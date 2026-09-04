"""
ProjectMemory (item 29 da especificação).

Armazena decisões, arquitetura, estilo visual, mecânicas, arquivos,
tarefas, erros, soluções e preferências do projeto via SQLAlchemy
(SQLite), conforme sugerido no item 29/30.
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Decision, ErrorRecord, LogEntry, Project


class ProjectMemory:
    def __init__(self, db: AsyncSession, project_id: str) -> None:
        self.db = db
        self.project_id = project_id

    async def record_decision(self, category: str, decision: str, reasoning: str = "") -> None:
        self.db.add(
            Decision(
                project_id=self.project_id,
                category=category,
                decision=decision,
                reasoning=reasoning,
            )
        )
        await self.db.commit()

    async def record_error(
        self,
        error_type: str,
        message: str,
        file_path: Optional[str] = None,
        hypothesis: Optional[str] = None,
    ) -> ErrorRecord:
        error = ErrorRecord(
            project_id=self.project_id,
            error_type=error_type,
            message=message,
            file_path=file_path,
            hypothesis=hypothesis,
        )
        self.db.add(error)
        await self.db.commit()
        await self.db.refresh(error)
        return error

    async def mark_error_resolved(self, error_id: str, patch_applied: str) -> None:
        from datetime import datetime, timezone

        result = await self.db.execute(select(ErrorRecord).where(ErrorRecord.id == error_id))
        error = result.scalar_one_or_none()
        if error:
            error.resolved = True
            error.patch_applied = patch_applied
            error.resolved_at = datetime.now(timezone.utc)
            await self.db.commit()

    async def log_event(
        self,
        task: str,
        action: str,
        status: str = "info",
        provider: Optional[str] = None,
        duration_ms: Optional[float] = None,
        file_path: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        self.db.add(
            LogEntry(
                project_id=self.project_id,
                task=task,
                action=action,
                status=status,
                provider=provider,
                duration_ms=duration_ms,
                file_path=file_path,
                error=error,
                log_metadata=metadata or {},
            )
        )
        await self.db.commit()

    async def get_decisions(self) -> list[Decision]:
        result = await self.db.execute(
            select(Decision).where(Decision.project_id == self.project_id).order_by(Decision.created_at)
        )
        return list(result.scalars().all())

    async def get_unresolved_errors(self) -> list[ErrorRecord]:
        result = await self.db.execute(
            select(ErrorRecord).where(
                ErrorRecord.project_id == self.project_id,
                ErrorRecord.resolved == False,  # noqa: E712
            )
        )
        return list(result.scalars().all())