"""
Endpoints de projetos: criar, listar, obter, deletar, e disparar o
pipeline de geração completo (IterationEngine).
"""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.iteration_engine import IterationEngine
from app.api.schemas import ProjectCreateRequest, ProjectOut
from app.auth.dependencies import get_current_plan, get_current_user
from app.core.logging import get_logger
from app.core.plans import PlanContext
from app.database.models import Message, Project, User
from app.database.session import AsyncSessionLocal, get_db
from app.projects.project_manager import ProjectManager

router = APIRouter(prefix="/api/projects", tags=["projects"])
logger = get_logger("projects_router")


@router.get("", response_model=list[ProjectOut])
async def list_projects(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Project).where(Project.owner_id == user.id).order_by(Project.updated_at.desc())
    )
    return list(result.scalars().all())


@router.post("", response_model=ProjectOut)
async def create_project(
    payload: ProjectCreateRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    plan: PlanContext = Depends(get_current_plan),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.owner_id == user.id))
    existing_count = len(list(result.scalars().all()))
    if existing_count >= plan.projects_limit():
        raise HTTPException(
            status_code=402,
            detail=(
                f"Limite de {plan.projects_limit()} projetos atingido no plano "
                f"{plan.plan.value}. Faça upgrade para PRO para criar mais projetos."
            ),
        )

    project = Project(owner_id=user.id, name=payload.name, description=payload.description, status="draft")
    db.add(project)
    await db.commit()
    await db.refresh(project)

    pm = ProjectManager()
    workspace_path = pm.create_project_dir(project.id)
    project.workspace_path = workspace_path
    await db.commit()
    await db.refresh(project)

    if payload.description:
        db.add(Message(project_id=project.id, role="user", content=payload.description, message_type="text"))
        await db.commit()
        background_tasks.add_task(_run_pipeline_background, project.id, payload.description)

    return project


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    project = await _get_owned_project(project_id, user, db)
    return project


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    confirmed: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_owned_project(project_id, user, db)
    if not confirmed:
        raise HTTPException(status_code=400, detail="Exclusão requer confirmed=true.")

    pm = ProjectManager()
    try:
        pm.delete_project(project_id, confirmed=True)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Falha ao remover diretório do projeto %s: %s", project_id, exc)

    await db.delete(project)
    await db.commit()
    return {"deleted": True}


@router.post("/{project_id}/generate")
async def trigger_generation(
    project_id: str,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_owned_project(project_id, user, db)
    if project.status in ("planning", "building", "testing"):
        raise HTTPException(status_code=409, detail="O projeto já está em processamento.")

    last_user_msg_result = await db.execute(
        select(Message)
        .where(Message.project_id == project_id, Message.role == "user")
        .order_by(Message.created_at.desc())
        .limit(1)
    )
    last_msg = last_user_msg_result.scalar_one_or_none()
    prompt = last_msg.content if last_msg else project.description

    background_tasks.add_task(_run_pipeline_background, project_id, prompt)
    return {"status": "started"}


async def _get_owned_project(project_id: str, user: User, db: AsyncSession) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")
    if project.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Você não tem acesso a este projeto.")
    return project


async def _run_pipeline_background(project_id: str, prompt: str) -> None:
    """Executa o pipeline em uma sessão de banco própria (background task
    roda fora do ciclo de vida da requisição HTTP original)."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if project is None:
            logger.error("Projeto %s não encontrado para pipeline em background.", project_id)
            return
        engine = IterationEngine(db, project)
        await engine.run_full_pipeline(prompt)