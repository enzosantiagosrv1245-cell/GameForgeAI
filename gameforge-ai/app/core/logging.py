"""
Logging estruturado para observabilidade (item 55 da especificação).

Cada evento relevante do sistema (tarefa, ação, provider usado, erro,
duração) é registrado em formato estruturado (JSON-friendly dict) para
que o dashboard de logs no frontend possa consumi-lo via API/DB.
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    stream=sys.stdout,
)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


class StructuredEvent:
    """Representa um evento estruturado que pode ser persistido no banco
    (tabela `logs`) e exibido no dashboard de observabilidade."""

    def __init__(
        self,
        task: str,
        action: str,
        project_id: Optional[str] = None,
        provider: Optional[str] = None,
        status: str = "info",
        duration_ms: Optional[float] = None,
        file_path: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.task = task
        self.action = action
        self.project_id = project_id
        self.provider = provider
        self.status = status
        self.duration_ms = duration_ms
        self.file_path = file_path
        self.error = error
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "task": self.task,
            "action": self.action,
            "project_id": self.project_id,
            "provider": self.provider,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "file_path": self.file_path,
            "error": self.error,
            "metadata": self.metadata,
        }