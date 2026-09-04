"""
Endpoints de leitura de dados do projeto: tasks, assets, files, tests, logs.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.projects_router import _get_owned_project
from app.api.schemas import AssetOut, TaskOut
from app.auth.dependencies import get_current_user
from app.database.models import LogEntry, Project, ProjectFile, Task, TestRun, User
from app.database.session import get_db
from app.projects.project_manager import ProjectManager

router = APIRouter(prefix="/api/projects/{project_id}", tags=["project-data"])


@router.get("/tasks", response_model=list[TaskOut])
async def list_tasks(project_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    project = await _get_owned_project(project_id, user, db)
    result = await db.execute(select(Task).where(Task.project_id == project.id).order_by(Task.priority, Task.created_at))
    return list(result.scalars().all())


@router.get("/assets", response_model=list[AssetOut])
async def list_assets(project_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    project = await _get_owned_project(project_id, user, db)
    from app.database.models import Asset

    result = await db.execute(select(Asset).where(Asset.project_id == project.id).order_by(Asset.created_at))
    return list(result.scalars().all())


@router.get("/files")
async def list_files(project_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    project = await _get_owned_project(project_id, user, db)
    pm = ProjectManager()
    files = pm.list_files(project.id)
    return {"files": files}


@router.get("/files/content")
async def get_file_content(
    project_id: str, path: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    project = await _get_owned_project(project_id, user, db)
    pm = ProjectManager()
    try:
        content = pm.read_file(project.id, path)
    except FileNotFoundError:
        return {"error": "Arquivo não encontrado."}
    return {"path": path, "content": content}


@router.get("/tests")
async def list_tests(project_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    project = await _get_owned_project(project_id, user, db)
    result = await db.execute(
        select(TestRun).where(TestRun.project_id == project.id).order_by(TestRun.created_at.desc()).limit(50)
    )
    runs = list(result.scalars().all())
    return [
        {
            "id": r.id,
            "test_type": r.test_type,
            "passed": r.passed,
            "total": r.total,
            "passed_count": r.passed_count,
            "failed_count": r.failed_count,
            "details": r.details,
            "created_at": r.created_at.isoformat(),
        }
        for r in runs
    ]


@router.get("/logs")
async def list_logs(project_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    project = await _get_owned_project(project_id, user, db)
    result = await db.execute(
        select(LogEntry).where(LogEntry.project_id == project.id).order_by(LogEntry.created_at.desc()).limit(200)
    )
    logs = list(result.scalars().all())
    return [
        {
            "id": l.id,
            "task": l.task,
            "action": l.action,
            "provider": l.provider,
            "status": l.status,
            "duration_ms": l.duration_ms,
            "file_path": l.file_path,
            "error": l.error,
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]