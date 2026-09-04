"""
Funções de segurança: hashing de senha (login próprio do site) e
criação/validação de tokens JWT de sessão.

Usa `bcrypt` diretamente (em vez de `passlib.CryptContext`) porque
passlib==1.7.4 é incompatível com bcrypt>=4.1 (tenta ler o atributo
removido `bcrypt.__about__.__version__` e quebra com
"password cannot be longer than 72 bytes" mesmo para senhas curtas -
bug conhecido da combinação dessas versões). bcrypt trunca em 72 bytes
por design do próprio algoritmo; truncamos explicitamente para evitar
o ValueError e documentar o comportamento.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()

_BCRYPT_MAX_BYTES = 72


def _truncate_for_bcrypt(plain_password: str) -> bytes:
    return plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(plain_password: str) -> str:
    hashed = bcrypt.hashpw(_truncate_for_bcrypt(plain_password), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(_truncate_for_bcrypt(plain_password), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str, extra_claims: Optional[dict[str, Any]] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None