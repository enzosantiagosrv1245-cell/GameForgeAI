"""
RemoteReasoningProvider: usa a API da Anthropic quando ANTHROPIC_API_KEY
está configurada no .env. Implementação real via httpx, não simulada -
mas só é instanciada/usada quando há uma chave configurada; caso
contrário `is_available()` retorna False e o sistema cai no
DemoReasoningProvider automaticamente (ver providers/factory.py).
"""
from __future__ import annotations

import json
from typing import Any, Optional

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.providers.base import ReasoningProvider, ReasoningResult

logger = get_logger("remote_reasoning")
settings = get_settings()

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


class RemoteReasoningProvider(ReasoningProvider):
    name = "anthropic-remote"

    def __init__(self) -> None:
        self.api_key = settings.ANTHROPIC_API_KEY

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def _call(self, prompt: str, system: Optional[str] = None) -> str:
        if not self.api_key:
            raise RuntimeError(
                "RemoteReasoningProvider indisponível: ANTHROPIC_API_KEY não configurada."
            )
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        body: dict[str, Any] = {
            "model": "claude-sonnet-4-6",
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            body["system"] = system

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(ANTHROPIC_API_URL, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()

        text_parts = [block["text"] for block in data.get("content", []) if block.get("type") == "text"]
        return "\n".join(text_parts)

    async def complete(
        self, prompt: str, context: Optional[dict[str, Any]] = None
    ) -> ReasoningResult:
        text = await self._call(prompt)
        return ReasoningResult(text=text, provider_name=self.name)

    async def complete_json(
        self, prompt: str, context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        system = (
            "Responda EXCLUSIVAMENTE com um objeto JSON válido, sem markdown, "
            "sem texto adicional antes ou depois."
        )
        raw = await self._call(prompt, system=system)
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("RemoteReasoningProvider retornou JSON inválido, usando fallback vazio.")
            return {}