"""
Configuração dos provedores OAuth: Google, GitHub, Discord (item "login com
Google, Discord, GitHub" solicitado pelo usuário).

Usa Authlib para o fluxo Authorization Code. As credenciais (client_id /
client_secret) vêm exclusivamente de variáveis de ambiente - nunca
hardcoded. Se um provider não estiver configurado (.env vazio), o
endpoint correspondente retorna erro 503 claro em vez de fingir sucesso.
"""
from __future__ import annotations

from authlib.integrations.starlette_client import OAuth

from app.core.config import get_settings

settings = get_settings()

oauth = OAuth()

oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

oauth.register(
    name="github",
    client_id=settings.GITHUB_CLIENT_ID,
    client_secret=settings.GITHUB_CLIENT_SECRET,
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "read:user user:email"},
)

oauth.register(
    name="discord",
    client_id=settings.DISCORD_CLIENT_ID,
    client_secret=settings.DISCORD_CLIENT_SECRET,
    access_token_url="https://discord.com/api/oauth2/token",
    authorize_url="https://discord.com/api/oauth2/authorize",
    api_base_url="https://discord.com/api/",
    client_kwargs={"scope": "identify email"},
)

PROVIDERS_CONFIGURED = {
    "google": bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET),
    "github": bool(settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET),
    "discord": bool(settings.DISCORD_CLIENT_ID and settings.DISCORD_CLIENT_SECRET),
}


def is_provider_configured(provider: str) -> bool:
    return PROVIDERS_CONFIGURED.get(provider, False)