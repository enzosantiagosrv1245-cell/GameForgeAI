"""
GameDesigner (item 9 da especificação).

Transforma a descrição em linguagem natural do usuário em um documento
estruturado de design de jogo (gênero, câmera, mecânicas, sistemas,
personagens, inimigos, mapas, UI, etc.), usando o ReasoningProvider
configurado (demo ou remoto).
"""
from __future__ import annotations

from typing import Any

from app.providers.base import ReasoningProvider

DEFAULT_ENEMY_TEMPLATES = {
    "survival": [{"name": "Zumbi Comum", "health": 30, "damage": 5, "speed": "slow"}],
    "shooter": [{"name": "Nave Inimiga", "health": 20, "damage": 10, "speed": "fast"}],
    "platformer": [{"name": "Inimigo Rastejante", "health": 15, "damage": 5, "speed": "slow"}],
    "rpg": [{"name": "Monstro Selvagem", "health": 40, "damage": 8, "speed": "medium"}],
}

DEFAULT_ITEM_TEMPLATES = {
    "survival": [
        {"name": "Comida Enlatada", "type": "consumable", "effect": "restore_hunger"},
        {"name": "Kit Médico", "type": "consumable", "effect": "restore_health"},
    ],
    "rpg": [{"name": "Poção de Vida", "type": "consumable", "effect": "restore_health"}],
}


class GameDesigner:
    """Módulo responsável por converter a ideia do usuário em uma
    especificação de design estruturada e reproduzível."""

    def __init__(self, reasoning_provider: ReasoningProvider) -> None:
        self.provider = reasoning_provider

    async def design_from_prompt(self, user_prompt: str) -> dict[str, Any]:
        extraction = await self.provider.complete_json(user_prompt)

        genre = extraction.get("genre", "adventure")
        systems = extraction.get("systems", ["health", "main_menu"])
        camera = extraction.get("camera", "top_down")
        visual_style = extraction.get("visual_style", ["minimalist"])
        suggested_name = extraction.get("suggested_name", "Novo Jogo")

        design_spec: dict[str, Any] = {
            "genre": genre,
            "dimension": "2d",
            "camera": camera,
            "name": suggested_name,
            "player": {
                "health": 100,
                "speed": 200,
                "has_inventory": "inventory" in systems,
                "has_stamina": "stamina" in systems,
                "has_hunger": "hunger" in systems,
            },
            "enemies": DEFAULT_ENEMY_TEMPLATES.get(genre, []),
            "items": DEFAULT_ITEM_TEMPLATES.get(genre, []),
            "systems": systems,
            "maps": [{"name": "Mapa Principal", "size": "large", "biome": "default"}],
            "ui": {
                "hud_elements": self._hud_for_systems(systems),
                "menus": ["main_menu", "pause_menu"] + (
                    ["game_over_menu"] if "health" in systems else []
                ),
            },
            "progression": {
                "type": "level_based" if "progression" in systems else "linear",
            },
            "economy": {"enabled": "economy" in systems},
            "audio": {"music": True, "sfx": True},
            "visual_style": visual_style,
            "objectives": self._default_objectives(genre),
            "win_condition": self._default_win_condition(genre),
            "lose_condition": "player_health <= 0" if "health" in systems else "none",
            "raw_prompt": user_prompt,
            "reasoning_provider": self.provider.name,
        }
        return design_spec

    @staticmethod
    def _hud_for_systems(systems: list[str]) -> list[str]:
        hud = []
        if "health" in systems:
            hud.append("health_bar")
        if "stamina" in systems:
            hud.append("stamina_bar")
        if "hunger" in systems:
            hud.append("hunger_bar")
        if "inventory" in systems:
            hud.append("inventory_slots")
        if "economy" in systems:
            hud.append("currency_counter")
        return hud or ["health_bar"]

    @staticmethod
    def _default_objectives(genre: str) -> list[str]:
        mapping = {
            "survival": ["Sobreviver o maior tempo possível", "Coletar recursos"],
            "platformer": ["Chegar ao final da fase", "Coletar itens"],
            "shooter": ["Destruir inimigos", "Sobreviver às ondas"],
            "rpg": ["Completar missões", "Evoluir o personagem"],
        }
        return mapping.get(genre, ["Explorar o mundo do jogo"])

    @staticmethod
    def _default_win_condition(genre: str) -> str:
        mapping = {
            "survival": "survive_duration_reached",
            "platformer": "level_completed",
            "shooter": "all_waves_cleared",
            "rpg": "main_quest_completed",
        }
        return mapping.get(genre, "no_explicit_win_condition")