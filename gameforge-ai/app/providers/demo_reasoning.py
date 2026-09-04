"""
DemoReasoningProvider (item 43 da especificação).

Implementação 100% local, baseada em regras + heurísticas de palavras-chave,
que permite validar toda a infraestrutura da plataforma sem precisar de
nenhuma API paga configurada. Não é um LLM real - é um RuleBasedProvider
funcional e honesto sobre suas limitações.

Quando ANTHROPIC_API_KEY estiver configurada, o RemoteReasoningProvider
(app/providers/remote_reasoning.py) pode ser usado no lugar deste,
trocando o provider via configuração (REASONING_PROVIDER=remote), sem
alterar nenhum código que consome a interface ReasoningProvider.
"""
from __future__ import annotations

import re
from typing import Any, Optional

from app.providers.base import ReasoningProvider, ReasoningResult

GENRE_KEYWORDS = {
    "survival": ["sobrevivência", "survival", "zumbi", "zombie", "fome", "sede"],
    "platformer": ["plataforma", "platformer", "pular", "fases"],
    "shooter": ["tiro", "shooter", "atirador", "space shooter", "nave"],
    "rpg": ["rpg", "role playing", "personagem evolui", "level up", "quest"],
    "puzzle": ["puzzle", "quebra-cabeça", "enigma"],
    "farming": ["fazenda", "farm", "colheita", "plantar"],
    "adventure": ["aventura", "adventure", "exploração"],
}

CAMERA_KEYWORDS = {
    "top_down": ["visão de cima", "top down", "top-down", "vista superior"],
    "side_scroll": ["lateral", "side scroll", "2d lateral", "plataforma"],
    "first_person": ["primeira pessoa", "fps"],
    "isometric": ["isométrico", "isometric"],
}

SYSTEM_KEYWORDS = {
    "inventory": ["inventário", "inventory", "itens", "mochila"],
    "health": ["vida", "health", "hp", "saúde"],
    "hunger": ["fome", "hunger"],
    "stamina": ["stamina", "energia", "fôlego"],
    "combat": ["ataque", "combate", "combat", "arma", "luta"],
    "loot": ["loot", "saque", "recompensa"],
    "crafting": ["crafting", "criação de itens", "fabricar"],
    "main_menu": ["menu principal", "menu"],
    "progression": ["progressão", "níveis", "level up", "experiência"],
    "economy": ["economia", "moeda", "dinheiro", "loja"],
}

STYLE_KEYWORDS = {
    "dark": ["sombria", "sombrio", "dark", "escura"],
    "pixel_art": ["pixel art", "pixelado", "8-bit", "16-bit"],
    "cartoon": ["cartoon", "desenho animado", "fofo"],
    "realistic": ["realista", "realistic"],
    "minimalist": ["minimalista", "minimal"],
}


def _match_keywords(text: str, keyword_map: dict[str, list[str]]) -> list[str]:
    text_lower = text.lower()
    matches = []
    for key, keywords in keyword_map.items():
        if any(kw in text_lower for kw in keywords):
            matches.append(key)
    return matches


class DemoReasoningProvider(ReasoningProvider):
    """RuleBasedProvider funcional. Extrai gênero, câmera, sistemas e
    estilo visual da descrição em linguagem natural do usuário usando
    correspondência de palavras-chave determinística (sem chamada de rede,
    sem custo, sem chave de API)."""

    name = "demo-rule-based"

    async def complete(
        self, prompt: str, context: Optional[dict[str, Any]] = None
    ) -> ReasoningResult:
        text = f"Analisei sua descrição: '{prompt[:200]}'. "
        genres = _match_keywords(prompt, GENRE_KEYWORDS)
        if genres:
            text += f"Identifiquei o gênero '{genres[0]}'. "
        systems = _match_keywords(prompt, SYSTEM_KEYWORDS)
        if systems:
            text += f"Sistemas detectados: {', '.join(systems)}."
        return ReasoningResult(text=text, provider_name=self.name)

    async def complete_json(
        self, prompt: str, context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        genres = _match_keywords(prompt, GENRE_KEYWORDS)
        cameras = _match_keywords(prompt, CAMERA_KEYWORDS)
        systems = _match_keywords(prompt, SYSTEM_KEYWORDS)
        styles = _match_keywords(prompt, STYLE_KEYWORDS)

        title_match = re.search(r"jogo (?:de |sobre )?([a-zA-ZÀ-ÿ\s]{3,40})", prompt.lower())
        suggested_name = (
            title_match.group(1).strip().title() if title_match else "Novo Jogo"
        )

        return {
            "genre": genres[0] if genres else "adventure",
            "secondary_genres": genres[1:],
            "dimension": "2d",
            "camera": cameras[0] if cameras else "top_down",
            "systems": systems or ["health", "main_menu"],
            "visual_style": styles or ["minimalist"],
            "suggested_name": suggested_name,
            "confidence": "heuristic" if genres else "low_confidence_fallback",
        }

    def is_available(self) -> bool:
        return True