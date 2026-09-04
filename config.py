"""
Configuração central da aplicação GameForge AI.

Todas as variáveis sensíveis (client secrets, chaves de API) devem vir
exclusivamente de variáveis de ambiente / arquivo .env. Nunca hardcode
segredos neste arquivo.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Aplicação ---
    APP_NAME: str = "GameForge AI"
    ENV: str = "development"  # development | production | test
    DEBUG: bool = True

    # --- Servidor ---
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"

    # --- Banco de dados ---
    DATABASE_URL: str = "sqlite+aiosqlite:///./workspace/gameforge.db"

    # --- Segurança / JWT ---
    SECRET_KEY: str = "dev-insecure-secret-change-me-in-env"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 dias
    SESSION_SECRET: str = "dev-insecure-session-secret-change-me"

    # --- OAuth: Google ---
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None

    # --- OAuth: GitHub ---
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None

    # --- OAuth: Discord ---
    DISCORD_CLIENT_ID: Optional[str] = None
    DISCORD_CLIENT_SECRET: Optional[str] = None

    # --- Planos / feature flags ---
    # E-mails que sempre recebem plano PRO automaticamente, separados por
    # vírgula (ex: "voce@exemplo.com,socio@exemplo.com"). Configurado por
    # VOCÊ (o operador) diretamente no .env do servidor - nunca por um
    # código digitado no chat. Armazenado como string simples (não JSON)
    # para ser fácil de editar manualmente; use `admin_emails_list` para
    # obter a lista já processada.
    ADMIN_EMAILS: str = ""

    @property
    def admin_emails_list(self) -> List[str]:
        return [e.strip() for e in self.ADMIN_EMAILS.split(",") if e.strip()]
    # Quando true, todo usuário autenticado localmente recebe PRO (uso em dev/demo).
    DEMO_UNLOCK_ALL_FEATURES: bool = False

    # --- Limites de plano ---
    FREE_CHAT_MESSAGES_PER_DAY: int = 30
    FREE_PROJECTS_LIMIT: int = 3
    PRO_PROJECTS_LIMIT: int = 50  # PRO tem limite alto, não infinito por padrão

    # --- Workspace / execução de agentes ---
    WORKSPACE_ROOT: str = "./workspace"
    GENERATED_ASSETS_ROOT: str = "./generated-assets"
    MAX_ITERATIONS: int = 10

    # --- Providers ---
    REASONING_PROVIDER: str = "demo"  # demo | local | remote
    ANTHROPIC_API_KEY: Optional[str] = None
    IMAGE_PROVIDER: str = "demo"  # demo | local | remote

    @property
    def is_production(self) -> bool:
        return self.ENV == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()