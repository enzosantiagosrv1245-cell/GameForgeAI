"""
GameArchitect (item 10 da especificação).

Decide engine, linguagem, estrutura de diretórios e arquitetura modular
com base na especificação de design produzida pelo GameDesigner.
Primeiro foco: 2D via HTML5/Canvas (roda no navegador, sem dependência
de instalação de engine externa) - ver item 20/34 sobre preview no
navegador para projetos web.
"""
from __future__ import annotations

from typing import Any


class GameArchitect:
    """Traduz a especificação de design em um plano de arquitetura técnica
    concreto: engine escolhida, estrutura de arquivos e módulos/sistemas
    que o CodeEngineer deverá implementar."""

    def decide_architecture(self, design_spec: dict[str, Any]) -> dict[str, Any]:
        engine = self._choose_engine(design_spec)
        file_structure = self._file_structure_for_engine(engine, design_spec)
        systems = self._systems_from_design(design_spec)

        return {
            "engine": engine,
            "language": "javascript" if engine == "html5" else "gdscript",
            "file_structure": file_structure,
            "systems": systems,
            "dependencies": [],  # HTML5/Canvas puro não requer dependências externas
            "communication_pattern": "event_bus",
            "decision_reasoning": (
                f"Engine '{engine}' escolhida por ser executável diretamente no "
                "navegador para preview imediato (item 34 da especificação), sem "
                "exigir instalação de software externo pelo usuário."
            ),
        }

    @staticmethod
    def _choose_engine(design_spec: dict[str, Any]) -> str:
        # Item 20/21: foco inicial 2D. HTML5/Canvas é o alvo padrão porque
        # permite execução e preview diretamente no navegador da própria
        # plataforma, sem exigir Godot instalado na máquina do usuário.
        return "html5"

    @staticmethod
    def _file_structure_for_engine(engine: str, design_spec: dict[str, Any]) -> list[str]:
        base = [
            "index.html",
            "src/main.js",
            "src/engine/GameLoop.js",
            "src/engine/InputManager.js",
            "src/engine/Renderer.js",
            "src/engine/Camera.js",
            "src/engine/CollisionSystem.js",
            "src/entities/Player.js",
            "src/entities/Enemy.js",
            "src/systems/HealthSystem.js",
            "src/ui/HUD.js",
            "src/ui/MainMenu.js",
            "src/ui/PauseMenu.js",
            "src/map/MapLoader.js",
            "src/state/GameState.js",
            "assets/manifest.json",
        ]
        systems = design_spec.get("systems", [])
        if "inventory" in systems:
            base.append("src/systems/InventorySystem.js")
        if "hunger" in systems:
            base.append("src/systems/HungerSystem.js")
        if "stamina" in systems:
            base.append("src/systems/StaminaSystem.js")
        if "combat" in systems:
            base.append("src/systems/CombatSystem.js")
        if "loot" in systems:
            base.append("src/systems/LootSystem.js")
        if "economy" in systems:
            base.append("src/systems/EconomySystem.js")
        return base

    @staticmethod
    def _systems_from_design(design_spec: dict[str, Any]) -> list[dict[str, str]]:
        systems = design_spec.get("systems", [])
        result = [
            {"name": "core_loop", "description": "Game loop principal e renderização"},
            {"name": "input", "description": "Captura de teclado/mouse"},
            {"name": "collision", "description": "Detecção de colisão AABB"},
            {"name": "player_movement", "description": "Movimentação do jogador"},
            {"name": "enemy_ai", "description": "Comportamento básico de inimigos"},
        ]
        system_descriptions = {
            "inventory": "Gerenciamento de itens coletados",
            "hunger": "Decaimento de fome ao longo do tempo",
            "stamina": "Consumo/regeneração de stamina em ações",
            "combat": "Sistema de dano e combate corpo-a-corpo/à distância",
            "loot": "Drop de itens ao derrotar inimigos",
            "economy": "Moeda e loja in-game",
            "main_menu": "Tela inicial do jogo",
        }
        for sys_key in systems:
            if sys_key in system_descriptions:
                result.append({"name": sys_key, "description": system_descriptions[sys_key]})
        return result