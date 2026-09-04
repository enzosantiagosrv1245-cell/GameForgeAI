"""
IterationEngine (item 23/36 da especificação).

Orquestra o ciclo completo de geração de um jogo, conectando os agentes
já implementados nesta base de código:

    PLAN (GameDesigner -> GameArchitect -> TaskPlanner)
      -> IMPLEMENT (CodeEngineer -> AssetGenerator)
      -> TEST (GameTestEngine)
      -> ANALYZE/FIX (DebuggerAI, com CodeEngineer como fonte de verdade
         para regeneração de arquivos)
      -> RETEST
      -> VISUAL REVIEW (VisualReviewer)

Cada etapa é persistida no banco (Message, Task, ProjectFile, Asset,
TestRun, ErrorRecord, Decision, LogEntry) para que o frontend possa
acompanhar o progresso real - nunca progresso inventado. O loop de
correção respeita MAX_ITERATIONS (config) para evitar loops infinitos.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.code_engineer import CodeEngineer
from app.agents.debugger_ai import DebuggerAI
from app.agents.factory import get_image_provider, get_reasoning_provider
from app.agents.game_architect import GameArchitect
from app.agents.game_designer import GameDesigner
from app.agents.game_test_engine import GameTestEngine
from app.agents.task_planner import TaskPlanner
from app.agents.visual_reviewer import VisualReviewer
from app.assets.asset_generator import AssetGenerator
from app.assets.visual_style_manager import VisualStyleManager
from app.core.config import get_settings
from app.core.logging import get_logger
from app.database.models import (
    Asset,
    Decision,
    ErrorRecord,
    LogEntry,
    Message,
    Project,
    ProjectFile,
    Task,
    TestRun,
)
from app.projects.project_manager import ProjectManager

logger = get_logger("iteration_engine")
settings = get_settings()


class IterationEngine:
    """Orquestra o pipeline PLAN -> IMPLEMENT -> TEST -> FIX para um
    projeto específico, usando uma sessão de banco própria (a mesma que
    o chamador - ex: background task - já abriu)."""

    def __init__(self, db: AsyncSession, project: Project) -> None:
        self.db = db
        self.project = project
        self.pm = ProjectManager()
        self.max_iterations = settings.MAX_ITERATIONS

    # ------------------------------------------------------------------
    # Helpers de persistência - nunca inventam sucesso, sempre refletem
    # o resultado real de cada etapa.
    # ------------------------------------------------------------------
    async def _log(self, action: str, status: str = "info", **kwargs: Any) -> None:
        entry = LogEntry(
            project_id=self.project.id,
            task=kwargs.get("task", "pipeline"),
            action=action,
            provider=kwargs.get("provider"),
            status=status,
            duration_ms=kwargs.get("duration_ms"),
            file_path=kwargs.get("file_path"),
            error=kwargs.get("error"),
            log_metadata=kwargs.get("metadata", {}),
        )
        self.db.add(entry)
        await self.db.commit()

    async def _message(self, content: str, message_type: str = "status", extra: dict | None = None) -> None:
        msg = Message(
            project_id=self.project.id,
            role="assistant",
            content=content,
            message_type=message_type,
            extra_data=extra or {},
        )
        self.db.add(msg)
        await self.db.commit()

    async def _set_status(self, status: str, progress_pct: float | None = None) -> None:
        self.project.status = status
        if progress_pct is not None:
            self.project.progress_pct = progress_pct
        await self.db.commit()
        await self.db.refresh(self.project)

    async def _record_decision(self, category: str, decision: str, reasoning: str = "") -> None:
        self.db.add(
            Decision(project_id=self.project.id, category=category, decision=decision, reasoning=reasoning)
        )
        await self.db.commit()

    # ------------------------------------------------------------------
    # Pipeline principal
    # ------------------------------------------------------------------
    async def run_full_pipeline(self, user_prompt: str) -> dict[str, Any]:
        try:
            design_spec, architecture, tasks = await self._plan(user_prompt)
            await self._implement(design_spec, architecture, tasks)
            test_results = await self._test(design_spec, architecture)
            await self._fix_loop(design_spec, architecture, test_results)
            await self._visual_review(design_spec)
            await self._set_status("ready", 100.0)
            await self._message("Pipeline concluído. Projeto pronto para preview.", "status")
            return {"status": "ready"}
        except Exception as exc:  # noqa: BLE001
            logger.exception("Pipeline falhou para o projeto %s", self.project.id)
            await self._set_status("needs_attention")
            await self._message(f"O pipeline encontrou um erro não recuperável: {exc}", "error")
            await self._log("pipeline_failure", status="error", error=str(exc))
            return {"status": "needs_attention", "error": str(exc)}

    # --- PLAN ---------------------------------------------------------
    async def _plan(self, user_prompt: str) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
        await self._set_status("planning", 5.0)
        await self._message("Entendendo a ideia e definindo o game design...", "progress")

        reasoning_provider = get_reasoning_provider()
        designer = GameDesigner(reasoning_provider)
        design_spec = await designer.design_from_prompt(user_prompt)
        self.project.design_spec = design_spec
        self.project.genre = design_spec.get("genre")
        self.project.name = design_spec.get("name", self.project.name)
        await self.db.commit()
        await self._record_decision(
            "scope", f"Game design definido: gênero={design_spec.get('genre')}", "Extraído do prompt do usuário via ReasoningProvider."
        )

        await self._message("Criando arquitetura técnica...", "progress")
        architect = GameArchitect()
        architecture = architect.decide_architecture(design_spec)
        await self._record_decision(
            "architecture", f"Engine escolhida: {architecture.get('engine')}", architecture.get("decision_reasoning", "")
        )

        await self._message("Planejando tarefas...", "progress")
        planner = TaskPlanner()
        tasks = planner.plan_tasks(design_spec, architecture)
        for t in tasks:
            self.db.add(
                Task(
                    project_id=self.project.id,
                    code=t["code"],
                    title=t["title"],
                    description=t["description"],
                    priority=t["priority"],
                    status=t["status"],
                    depends_on=t["depends_on"],
                    related_files=t["related_files"],
                    acceptance_criteria=t["acceptance_criteria"],
                )
            )
        await self.db.commit()
        await self._log("plan_complete", metadata={"task_count": len(tasks)})
        return design_spec, architecture, tasks

    # --- IMPLEMENT ------------------------------------------------------
    async def _implement(
        self, design_spec: dict[str, Any], architecture: dict[str, Any], tasks: list[dict[str, Any]]
    ) -> None:
        await self._set_status("building", 30.0)
        self.pm.create_project_dir(self.project.id)

        await self._message("Gerando código-fonte do jogo...", "progress")
        engineer = CodeEngineer()
        files = engineer.generate_all_files(design_spec, architecture)
        for rel_path, content in files.items():
            result = self.pm.write_file(self.project.id, rel_path, content)
            self.db.add(
                ProjectFile(
                    project_id=self.project.id,
                    path=result["path"],
                    file_type="code",
                    size_bytes=result["size_bytes"],
                    checksum=result["checksum"],
                )
            )
        await self.db.commit()
        await self._log("code_generation_complete", metadata={"file_count": len(files)})

        await self._message("Gerando assets visuais...", "progress")
        style_manager = VisualStyleManager.for_project(design_spec)
        assets_dir = str(self.pm.project_dir(self.project.id) / "assets")
        asset_generator = AssetGenerator(get_image_provider(), style_manager, assets_dir)
        asset_results = await asset_generator.generate_full_manifest(design_spec)
        for a in asset_results:
            self.db.add(
                Asset(
                    project_id=self.project.id,
                    name=a["name"],
                    asset_type=a["asset_type"],
                    file_path=a["file_path"],
                    width=a["width"],
                    height=a["height"],
                    provider_used=a["provider_used"],
                    style_spec=a["style_spec"],
                )
            )
        await self.db.commit()
        await self._log("asset_generation_complete", metadata={"asset_count": len(asset_results)})

        await self._set_status("testing", 60.0)

    # --- TEST -----------------------------------------------------------
    async def _test(self, design_spec: dict[str, Any], architecture: dict[str, Any]) -> list[dict[str, Any]]:
        await self._message("Executando testes...", "progress")
        project_dir = str(self.pm.project_dir(self.project.id))
        test_engine = GameTestEngine(project_dir)
        expected_files = architecture.get("file_structure", [])
        results = test_engine.run_full_suite(expected_files, expected_asset_count=3)

        for r in results:
            self.db.add(
                TestRun(
                    project_id=self.project.id,
                    test_type=r["test_type"],
                    passed=bool(r["passed"]),
                    total=r["total"],
                    passed_count=r["passed_count"],
                    failed_count=r["failed_count"],
                    details=r["details"],
                )
            )
        await self.db.commit()

        failed = [r for r in results if r["passed"] is False]
        await self._message(
            f"Testes concluídos: {len(results) - len(failed)}/{len(results)} suites passaram.",
            "progress",
            extra={"results": results},
        )
        return results

    # --- FIX (DebuggerAI, com limite de iterações) -----------------------
    async def _fix_loop(
        self, design_spec: dict[str, Any], architecture: dict[str, Any], test_results: list[dict[str, Any]]
    ) -> None:
        engineer = CodeEngineer()
        debugger = DebuggerAI(self.pm, self.project.id)
        iteration = 0
        current_results = test_results

        while iteration < self.max_iterations:
            failed = [r for r in current_results if r["passed"] is False]
            if not failed:
                break

            await self._set_status("debugging")
            iteration += 1
            await self._message(f"Iteração de correção {iteration}/{self.max_iterations}...", "progress")

            for failure in failed:
                error_type = failure["test_type"]
                message = str(failure["details"])
                file_path = None
                missing_files = failure.get("details", {}).get("missing_files")
                if missing_files:
                    file_path = missing_files[0]
                    error_type = "missing_file"

                analysis = debugger.analyze_error(error_type, message, file_path)
                error_record = ErrorRecord(
                    project_id=self.project.id,
                    error_type=error_type,
                    message=message[:2000],
                    file_path=file_path,
                    hypothesis=analysis["hypothesis"],
                )
                self.db.add(error_record)
                await self.db.commit()

                def regenerate_fn(rel_path: str) -> str:
                    all_files = engineer.generate_all_files(design_spec, architecture)
                    if rel_path in all_files:
                        return all_files[rel_path]
                    raise KeyError(f"CodeEngineer não sabe gerar '{rel_path}'.")

                patch_result = debugger.attempt_patch(error_type, file_path, message, regenerate_fn)
                error_record.patch_applied = patch_result.get("action")
                error_record.resolved = bool(patch_result.get("patched"))
                await self.db.commit()
                await self._log(
                    "debug_patch_attempt",
                    status="info" if patch_result.get("patched") else "warning",
                    metadata=patch_result,
                )

            # RETEST
            project_dir = str(self.pm.project_dir(self.project.id))
            test_engine = GameTestEngine(project_dir)
            expected_files = architecture.get("file_structure", [])
            current_results = test_engine.run_full_suite(expected_files, expected_asset_count=3)
            for r in current_results:
                self.db.add(
                    TestRun(
                        project_id=self.project.id,
                        test_type=r["test_type"],
                        passed=bool(r["passed"]),
                        total=r["total"],
                        passed_count=r["passed_count"],
                        failed_count=r["failed_count"],
                        details=r["details"],
                    )
                )
            await self.db.commit()

        remaining_failures = [r for r in current_results if r["passed"] is False]
        if remaining_failures:
            await self._message(
                f"{len(remaining_failures)} suite(s) de teste ainda falham após "
                f"{iteration} iteração(ões) de correção (limite: {self.max_iterations}).",
                "warning",
            )

    # --- VISUAL REVIEW ----------------------------------------------------
    async def _visual_review(self, design_spec: dict[str, Any]) -> None:
        await self._message("Revisando estrutura visual do projeto...", "progress")
        project_dir = str(self.pm.project_dir(self.project.id))
        reviewer = VisualReviewer(project_dir)
        review = reviewer.review_structural(design_spec)
        await self._log(
            "visual_review_complete",
            status="info" if review["passed"] else "warning",
            metadata=review,
        )
        if review["issues_found"]:
            await self._message(
                "Revisão estrutural encontrou pontos de atenção: " + "; ".join(review["issues_found"]),
                "warning",
                extra=review,
            )
