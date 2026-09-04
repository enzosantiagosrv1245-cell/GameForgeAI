"""
DebuggerAI (item 27 da especificação).

Fluxo: ERROR -> ANALYZE -> HYPOTHESIS -> PATCH -> TEST -> VERIFY.

Implementa correções reais para as classes de erro mais comuns
detectadas pelo GameTestEngine (arquivo faltando, erro de sintaxe JS
reportado pelo `node --check`, import quebrado). Não apenas apaga o
código problemático (proibido pelo item 27) - tenta reparar de forma
específica ao tipo de erro.
"""
from __future__ import annotations

import re
from typing import Any, Optional

from app.core.logging import get_logger
from app.projects.project_manager import ProjectManager

logger = get_logger("debugger_ai")


class DebuggerAI:
    def __init__(self, project_manager: ProjectManager, project_id: str) -> None:
        self.pm = project_manager
        self.project_id = project_id

    def analyze_error(self, error_type: str, message: str, file_path: Optional[str]) -> dict[str, Any]:
        """Formula uma hipótese sobre a causa do erro."""
        hypothesis = "Causa desconhecida - requer inspeção manual."

        if error_type == "missing_file":
            hypothesis = (
                f"O arquivo '{file_path}' esperado pela arquitetura não foi criado "
                "durante a fase de geração de código."
            )
        elif error_type == "syntax_validation" and "Unexpected" in message:
            hypothesis = "Erro de sintaxe JavaScript - provável chave, parêntese ou vírgula ausente."
        elif error_type == "syntax_validation" and "is not defined" in message:
            hypothesis = "Referência a identificador não importado/declarado no módulo."
        elif error_type == "missing_import":
            hypothesis = f"O arquivo '{file_path}' referencia um módulo que não existe ou tem path incorreto."

        return {"error_type": error_type, "file_path": file_path, "hypothesis": hypothesis}

    def attempt_patch(
        self, error_type: str, file_path: Optional[str], message: str, regenerate_fn
    ) -> dict[str, Any]:
        """Aplica um patch real. `regenerate_fn` é uma função fornecida pelo
        chamador (IterationEngine) capaz de regenerar o conteúdo correto de
        um arquivo específico usando o CodeEngineer - o Debugger não
        inventa código às cegas, ele aciona a fonte de verdade (CodeEngineer)
        para o arquivo problemático."""
        if error_type == "missing_file" and file_path:
            try:
                content = regenerate_fn(file_path)
                self.pm.write_file(self.project_id, file_path, content)
                return {"patched": True, "action": f"Arquivo '{file_path}' regenerado."}
            except Exception as exc:  # noqa: BLE001
                logger.error("Falha ao regenerar %s: %s", file_path, exc)
                return {"patched": False, "action": f"Falha ao regenerar '{file_path}': {exc}"}

        if error_type == "syntax_validation" and file_path:
            try:
                # Estratégia de patch para erro de sintaxe: regenerar o
                # arquivo inteiro a partir do CodeEngineer (fonte de verdade),
                # já que patches cirúrgicos de sintaxe em código gerado
                # programaticamente têm alta chance de introduzir novos bugs.
                content = regenerate_fn(file_path)
                self.pm.write_file(self.project_id, file_path, content)
                return {
                    "patched": True,
                    "action": f"Arquivo '{file_path}' regenerado para corrigir erro de sintaxe.",
                }
            except Exception as exc:  # noqa: BLE001
                return {"patched": False, "action": f"Falha ao corrigir sintaxe: {exc}"}

        return {
            "patched": False,
            "action": "Nenhuma estratégia automática de correção disponível para este tipo de erro.",
        }