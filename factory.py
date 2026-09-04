"""
Fábrica de providers (item 54: não depender de um único fornecedor).

Seleciona a implementação concreta baseada em REASONING_PROVIDER /
IMAGE_PROVIDER no .env, com fallback automático e transparente para o
DemoReasoningProvider quando o provider remoto não estiver disponível
(sem chave configurada). Isso garante que a plataforma sempre funcione
em modo local, conforme exigido no item 43.
"""
from __future__ import annotations

from app.core.config import get_settings
from app.core.logging import get_logger
from app.providers.base import ReasoningProvider
from app.providers.demo_reasoning import DemoReasoningProvider
from app.providers.remote_reasoning import RemoteReasoningProvider

logger = get_logger("providers.factory")
settings = get_settings()

_demo_provider = DemoReasoningProvider()
_remote_provider = RemoteReasoningProvider()


def get_reasoning_provider() -> ReasoningProvider:
    if settings.REASONING_PROVIDER == "remote":
        if _remote_provider.is_available():
            return _remote_provider
        logger.warning(
            "REASONING_PROVIDER=remote mas ANTHROPIC_API_KEY não configurada. "
            "Usando DemoReasoningProvider como fallback."
        )
    return _demo_provider