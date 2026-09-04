"""
Endpoints de chat dentro de um projeto.

Aplica o limite diário de mensagens do plano FREE (item mencionado pelo
usuário: "para o limite de chat, é apenas para o pro que é ilimitado").
O PRO tem `chat_messages_per_day = None`, ou seja, sem limite.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.iteration_engine import IterationEngine
from app.api.projects_router import _get_owned_project, _run_pipeline_background
from app.api.schemas import ChatMessageRequest, MessageOut
from app.auth.dependencies import get_current_plan, get_current_user
from app.core.plans import PlanContext
from app.database.models import ChatUsage, Message, User
from app.database.session import get_db

router = APIRouter(prefix="/api/projects/{project_id}/chat", tags=["chat"])


async def _check_and_increment_chat_usage(user: User, plan: PlanContext, db: AsyncSession) -> None:
    limit = plan.chat_messages_per_day()
    if limit is None:
        return  # PRO: chat ilimitado

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    result = await db.execute(
        select(ChatUsage).where(ChatUsage.user_id == user.id, ChatUsage.date == today)
    )
    usage = result.scalar_one_or_none()

    if usage is None:
        usage = ChatUsage(user_id=user.id, date=today, message_count=0)
        db.add(usage)

    if usage.message_count >= limit:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Você atingiu o limite de {limit} mensagens hoje no plano Free. "
                "Faça upgrade para o plano PRO para chat ilimitado."
            ),
        )

    usage.message_count += 1
    await db.commit()


@router.get("", response_model=list[MessageOut])
async def list_messages(
    project_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    project = await _get_owned_project(project_id, user, db)
    result = await db.execute(
        select(Message).where(Message.project_id == project.id).order_by(Message.created_at)
    )
    return list(result.scalars().all())


@router.post("", response_model=MessageOut)
async def send_message(
    project_id: str,
    payload: ChatMessageRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    plan: PlanContext = Depends(get_current_plan),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_owned_project(project_id, user, db)
    await _check_and_increment_chat_usage(user, plan, db)

    message = Message(project_id=project.id, role="user", content=payload.content, message_type="text")
    db.add(message)
    await db.commit()
    await db.refresh(message)

    if project.status not in ("planning", "building", "testing"):
        background_tasks.add_task(_run_pipeline_background, project.id, payload.content)

    return message