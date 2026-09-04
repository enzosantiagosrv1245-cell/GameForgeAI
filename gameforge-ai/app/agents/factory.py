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
from app.providers.base import ImageGenerationProvider, ReasoningProvider
from app.providers.demo_image import DemoImageProvider
from app.providers.demo_reasoning import DemoReasoningProvider
from app.providers.remote_reasoning import RemoteReasoningProvider

logger = get_logger("providers.factory")
settings = get_settings()

_demo_provider = DemoReasoningProvider()
_remote_provider = RemoteReasoningProvider()
_demo_image_provider = DemoImageProvider()


def get_reasoning_provider() -> ReasoningProvider:
    if settings.REASONING_PROVIDER == "remote":
        if _remote_provider.is_available():
            return _remote_provider
        logger.warning(
            "REASONING_PROVIDER=remote mas ANTHROPIC_API_KEY não configurada. "
            "Usando DemoReasoningProvider como fallback."
        )
    return _demo_provider


def get_image_provider() -> ImageGenerationProvider:
    """Seleciona o ImageGenerationProvider configurado (IMAGE_PROVIDER no
    .env). Nenhum provider remoto real está implementado nesta versão -
    quando IMAGE_PROVIDER=remote for solicitado sem uma implementação
    concreta conectada, cai para o DemoImageProvider (procedural via
    Pillow) e registra isso explicitamente, nunca fingindo geração real."""
    if settings.IMAGE_PROVIDER == "remote":
        logger.warning(
            "IMAGE_PROVIDER=remote solicitado, mas nenhum ImageGenerationProvider "
            "remoto está implementado nesta versão. Usando DemoImageProvider "
            "(geração procedural real via Pillow) como fallback honesto."
        )
    return _demo_image_provider