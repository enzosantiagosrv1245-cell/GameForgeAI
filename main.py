"""
GameForge AI - Backend principal.

Ponto de entrada da aplicação FastAPI. Registra routers, middlewares
(CORS, sessão para OAuth), monta o diretório de workspace para servir
os projetos gerados (preview no navegador - item 34) e inicializa o
banco de dados no startup.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.api.auth_router import router as auth_router
from app.api.chat_router import router as chat_router
from app.api.project_data_router import router as project_data_router
from app.api.projects_router import router as projects_router
from app.core.config import get_settings
from app.database.session import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(chat_router)
app.include_router(project_data_router)

import os

os.makedirs(settings.WORKSPACE_ROOT, exist_ok=True)
os.makedirs(f"{settings.WORKSPACE_ROOT}/projects", exist_ok=True)
app.mount(
    "/preview",
    StaticFiles(directory=f"{settings.WORKSPACE_ROOT}/projects", html=True),
    name="preview",
)


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/api/plans")
async def get_plans():
    from app.core.plans import PLAN_LIMITS

    return {
        plan.value: {
            "can_generate_3d": limits.can_generate_3d,
            "chat_messages_per_day": limits.chat_messages_per_day,
            "projects_limit": limits.projects_limit,
            "label": limits.label,
        }
        for plan, limits in PLAN_LIMITS.items()
    }