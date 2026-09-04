"""
Endpoints de autenticação.

- GET  /api/auth/providers            -> lista quais provedores OAuth estão configurados
- GET  /api/auth/{provider}/login     -> inicia fluxo OAuth (google|github|discord)
- GET  /api/auth/{provider}/callback  -> callback OAuth, cria/atualiza usuário, retorna JWT
- POST /api/auth/register             -> login próprio do site (cria conta com senha)
- POST /api/auth/login                -> login próprio do site (autentica com senha)
- GET  /api/auth/me                   -> retorna usuário autenticado + plano efetivo
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.oauth_providers import is_provider_configured, oauth
from app.auth.security import create_access_token, hash_password, verify_password
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.plans import PlanContext
from app.database.models import OAuthAccount, User
from app.database.session import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = get_logger("auth")
settings = get_settings()

SUPPORTED_PROVIDERS = {"google", "github", "discord"}


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


def _user_to_public_dict(user: User) -> dict:
    plan_ctx = PlanContext.for_user(user)
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "avatar_url": user.avatar_url,
        "plan": plan_ctx.plan.value,
        "is_admin": user.is_admin,
        "limits": {
            "can_generate_3d": plan_ctx.can_generate_3d(),
            "chat_messages_per_day": plan_ctx.chat_messages_per_day(),
            "projects_limit": plan_ctx.projects_limit(),
            "unlimited_chat": plan_ctx.is_unlimited_chat(),
        },
    }


@router.get("/providers")
async def list_providers():
    return {
        "google": is_provider_configured("google"),
        "github": is_provider_configured("github"),
        "discord": is_provider_configured("discord"),
        "site_login": True,
    }


@router.get("/{provider}/login")
async def oauth_login(provider: str, request: Request):
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=404, detail="Provedor não suportado.")
    if not is_provider_configured(provider):
        raise HTTPException(
            status_code=503,
            detail=(
                f"O provedor '{provider}' ainda não foi configurado. "
                f"Defina {provider.upper()}_CLIENT_ID e {provider.upper()}_CLIENT_SECRET "
                "no arquivo .env."
            ),
        )
    client = oauth.create_client(provider)
    redirect_uri = f"{settings.BACKEND_URL}/api/auth/{provider}/callback"
    return await client.authorize_redirect(request, redirect_uri)


@router.get("/{provider}/callback")
async def oauth_callback(provider: str, request: Request, db: AsyncSession = Depends(get_db)):
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=404, detail="Provedor não suportado.")
    if not is_provider_configured(provider):
        raise HTTPException(status_code=503, detail=f"Provedor '{provider}' não configurado.")

    client = oauth.create_client(provider)
    try:
        token = await client.authorize_access_token(request)
    except Exception as exc:  # OAuthError e variantes
        logger.warning("Falha no callback OAuth (%s): %s", provider, exc)
        raise HTTPException(status_code=400, detail="Falha na autenticação OAuth.") from exc

    email: str | None = None
    name: str = ""
    avatar_url: str | None = None
    provider_account_id: str = ""

    if provider == "google":
        userinfo = token.get("userinfo") or await client.parse_id_token(request, token)
        email = userinfo.get("email")
        name = userinfo.get("name", email or "Usuário Google")
        avatar_url = userinfo.get("picture")
        provider_account_id = userinfo.get("sub", "")

    elif provider == "github":
        resp = await client.get("user", token=token)
        profile = resp.json()
        provider_account_id = str(profile.get("id", ""))
        name = profile.get("name") or profile.get("login", "Usuário GitHub")
        avatar_url = profile.get("avatar_url")
        email = profile.get("email")
        if not email:
            emails_resp = await client.get("user/emails", token=token)
            emails = emails_resp.json()
            primary = next((e for e in emails if e.get("primary")), None)
            email = (primary or (emails[0] if emails else {})).get("email")

    elif provider == "discord":
        resp = await client.get("users/@me", token=token)
        profile = resp.json()
        provider_account_id = str(profile.get("id", ""))
        name = profile.get("username", "Usuário Discord")
        email = profile.get("email")
        avatar_hash = profile.get("avatar")
        if avatar_hash:
            avatar_url = (
                f"https://cdn.discordapp.com/avatars/{provider_account_id}/{avatar_hash}.png"
            )

    if not email:
        raise HTTPException(
            status_code=400,
            detail=(
                "Não foi possível obter um e-mail da sua conta "
                f"{provider}. Verifique as permissões concedidas."
            ),
        )

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(email=email, name=name, avatar_url=avatar_url, plan="FREE")
        db.add(user)
        await db.flush()

    oauth_result = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.user_id == user.id,
            OAuthAccount.provider == provider,
        )
    )
    oauth_account = oauth_result.scalar_one_or_none()
    if oauth_account is None:
        db.add(
            OAuthAccount(
                user_id=user.id,
                provider=provider,
                provider_account_id=provider_account_id,
            )
        )

    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(subject=user.id)
    logger.info("Login OAuth bem-sucedido: provider=%s user=%s", provider, user.email)

    # Redireciona para o frontend com o token (fluxo padrão SPA + OAuth redirect)
    redirect_url = f"{settings.FRONTEND_URL}/auth/callback?token={access_token}"
    return RedirectResponse(url=redirect_url)


@router.post("/register", response_model=AuthResponse)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Já existe uma conta com este e-mail.")

    user = User(
        email=payload.email,
        name=payload.name,
        password_hash=hash_password(payload.password),
        plan="FREE",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(subject=user.id)
    logger.info("Novo registro via site: %s", user.email)
    return AuthResponse(access_token=access_token, user=_user_to_public_dict(user))


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if user is None or not user.password_hash:
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos.")
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos.")

    access_token = create_access_token(subject=user.id)
    return AuthResponse(access_token=access_token, user=_user_to_public_dict(user))


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return _user_to_public_dict(user)