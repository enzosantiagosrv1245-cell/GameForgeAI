"""
ProjectManager (item 31 da especificação).

Responsável por criar/abrir/listar projetos, criar/editar/mover arquivos
dentro do workspace, verificar integridade e evitar acesso fora da área
autorizada (item 38: segurança - o agente só opera dentro do workspace).
"""
from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path
from typing import Any

from app.core.config import get_settings

settings = get_settings()

# Comandos/operações destrutivas que exigem bloqueio ou confirmação explícita.
BLOCKED_PATH_SEGMENTS = {"..", "~"}


class WorkspaceSecurityError(Exception):
    """Levantada quando uma operação tenta escapar do workspace autorizado."""


class ProjectManager:
    def __init__(self, workspace_root: str | None = None) -> None:
        self.workspace_root = Path(workspace_root or settings.WORKSPACE_ROOT).resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def project_dir(self, project_id: str) -> Path:
        path = (self.workspace_root / "projects" / project_id).resolve()
        self._assert_within_workspace(path)
        return path

    def _assert_within_workspace(self, path: Path) -> None:
        try:
            path.relative_to(self.workspace_root)
        except ValueError as exc:
            raise WorkspaceSecurityError(
                f"Operação bloqueada: caminho '{path}' está fora do workspace autorizado."
            ) from exc
        for segment in BLOCKED_PATH_SEGMENTS:
            if segment in str(path):
                raise WorkspaceSecurityError(f"Segmento de caminho bloqueado detectado: {segment}")

    def create_project_dir(self, project_id: str) -> str:
        p_dir = self.project_dir(project_id)
        p_dir.mkdir(parents=True, exist_ok=True)
        (p_dir / "assets").mkdir(exist_ok=True)
        (p_dir / "src").mkdir(exist_ok=True)
        return str(p_dir)

    def write_file(self, project_id: str, relative_path: str, content: str) -> dict[str, Any]:
        p_dir = self.project_dir(project_id)
        full_path = (p_dir / relative_path).resolve()
        self._assert_within_workspace(full_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")

        checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()
        return {
            "path": relative_path,
            "size_bytes": len(content.encode("utf-8")),
            "checksum": checksum,
        }

    def read_file(self, project_id: str, relative_path: str) -> str:
        p_dir = self.project_dir(project_id)
        full_path = (p_dir / relative_path).resolve()
        self._assert_within_workspace(full_path)
        if not full_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {relative_path}")
        return full_path.read_text(encoding="utf-8")

    def list_files(self, project_id: str) -> list[str]:
        p_dir = self.project_dir(project_id)
        if not p_dir.exists():
            return []
        files = []
        for root, _dirs, filenames in os.walk(p_dir):
            for fname in filenames:
                full = Path(root) / fname
                files.append(str(full.relative_to(p_dir)))
        return sorted(files)

    def delete_file(self, project_id: str, relative_path: str, confirmed: bool = False) -> None:
        if not confirmed:
            raise PermissionError(
                "Exclusão de arquivo requer confirmação explícita (confirmed=True)."
            )
        p_dir = self.project_dir(project_id)
        full_path = (p_dir / relative_path).resolve()
        self._assert_within_workspace(full_path)
        if full_path.exists():
            full_path.unlink()

    def delete_project(self, project_id: str, confirmed: bool = False) -> None:
        if not confirmed:
            raise PermissionError(
                "Exclusão de projeto requer confirmação explícita (confirmed=True)."
            )
        p_dir = self.project_dir(project_id)
        if p_dir.exists():
            shutil.rmtree(p_dir)

    def check_integrity(self, project_id: str, expected_files: list[str]) -> dict[str, Any]:
        existing = set(self.list_files(project_id))
        expected = set(expected_files)
        missing = expected - existing
        extra = existing - expected
        return {
            "missing_files": sorted(missing),
            "unexpected_files": sorted(extra),
            "ok": len(missing) == 0,
        }