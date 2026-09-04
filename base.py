"""
Interfaces de providers (item 53 da especificação).

Isso permite trocar fornecedores (OpenAI, Anthropic, modelos locais,
Stable Diffusion, etc.) sem acoplar o resto da aplicação a uma única API.
Cada provider concreto implementa uma dessas interfaces abstratas.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ReasoningResult:
    text: str
    provider_name: str
    structured: Optional[dict[str, Any]] = None


class ReasoningProvider(ABC):
    """Interface para módulos que interpretam intenção/contexto e geram
    respostas ou planos (item 23 da especificação)."""

    name: str = "base"

    @abstractmethod
    async def complete(
        self, prompt: str, context: Optional[dict[str, Any]] = None
    ) -> ReasoningResult:
        ...

    @abstractmethod
    async def complete_json(
        self, prompt: str, context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        ...

    def is_available(self) -> bool:
        return True


@dataclass
class ImageGenerationResult:
    file_path: str
    provider_name: str
    width: int
    height: int
    is_placeholder: bool = False


class ImageGenerationProvider(ABC):
    """Interface para geração de sprites/imagens (item 53)."""

    name: str = "base"

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        output_path: str,
        width: int = 64,
        height: int = 64,
        style_spec: Optional[dict[str, Any]] = None,
    ) -> ImageGenerationResult:
        ...

    def is_available(self) -> bool:
        return True


class AudioGenerationProvider(ABC):
    """Interface para geração de áudio (item 19/53). Nenhuma implementação
    real automática é fingida; sem provider configurado, retorna None e o
    sistema documenta que o asset precisa ser fornecido manualmente."""

    name: str = "base"

    @abstractmethod
    async def generate(self, prompt: str, output_path: str) -> Optional[str]:
        ...

    def is_available(self) -> bool:
        return False


class CodeGenerationProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def generate_code(self, spec: dict[str, Any], context: dict[str, Any]) -> str:
        ...


class VisionProvider(ABC):
    """Interface para análise visual de screenshots (VisualReviewer, item 28)."""

    name: str = "base"

    @abstractmethod
    async def analyze(self, image_path: str) -> dict[str, Any]:
        ...

    def is_available(self) -> bool:
        return True


class ThreeDGenerationProvider(ABC):
    """Interface para geração 3D (item 22/52). Sem provider real conectado,
    NUNCA finge gerar um modelo 3D - retorna indisponível explicitamente."""

    name: str = "base"

    @abstractmethod
    async def generate_model(self, spec: dict[str, Any], output_path: str) -> Optional[str]:
        ...

    def is_available(self) -> bool:
        return False