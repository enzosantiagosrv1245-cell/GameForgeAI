"""
TaskPlanner (item 24 da especificação).

Transforma a arquitetura decidida em uma lista de tarefas concretas,
com id, prioridade, dependências, status, arquivos relacionados,
descrição e critérios de aceitação.
"""
from __future__ import annotations

from typing import Any


class TaskPlanner:
    def plan_tasks(
        self, design_spec: dict[str, Any], architecture: dict[str, Any]
    ) -> list[dict[str, Any]]:
        tasks: list[dict[str, Any]] = []
        counter = 1

        def add_task(
            title: str,
            description: str,
            files: list[str],
            depends_on: list[str] | None = None,
            priority: int = 3,
            acceptance_criteria: list[str] | None = None,
        ) -> str:
            nonlocal counter
            code = f"TASK-{counter:03d}"
            counter += 1
            tasks.append(
                {
                    "code": code,
                    "title": title,
                    "description": description,
                    "priority": priority,
                    "status": "pending",
                    "depends_on": depends_on or [],
                    "related_files": files,
                    "acceptance_criteria": acceptance_criteria or [f"Arquivo(s) {files} criado(s) e sem erros de sintaxe"],
                }
            )
            return code

        t_scaffold = add_task(
            "Criar estrutura do projeto",
            "Criar diretórios e arquivos base do projeto de acordo com a arquitetura decidida.",
            ["index.html", "src/main.js"],
            priority=1,
            acceptance_criteria=["Diretório do projeto existe", "index.html abre sem erro 404"],
        )

        t_engine = add_task(
            "Implementar game loop e engine core",
            "Implementar GameLoop, Renderer, InputManager, Camera e CollisionSystem.",
            [
                "src/engine/GameLoop.js",
                "src/engine/Renderer.js",
                "src/engine/InputManager.js",
                "src/engine/Camera.js",
                "src/engine/CollisionSystem.js",
            ],
            depends_on=[t_scaffold],
            priority=1,
            acceptance_criteria=["Loop de jogo executa a 60fps sem exceções no console"],
        )

        t_player = add_task(
            "Criar player e movimentação",
            "Implementar entidade Player com movimentação via teclado (WASD/setas).",
            ["src/entities/Player.js"],
            depends_on=[t_engine],
            priority=1,
            acceptance_criteria=["Player se move na tela ao pressionar teclas direcionais"],
        )

        t_enemies = add_task(
            "Criar inimigos e IA básica",
            "Implementar entidade Enemy com comportamento de perseguição simples.",
            ["src/entities/Enemy.js"],
            depends_on=[t_player],
            priority=2,
            acceptance_criteria=["Inimigos aparecem no mapa e se movem em direção ao player"],
        )

        systems = design_spec.get("systems", [])
        last_system_task = t_enemies

        if "combat" in systems:
            last_system_task = add_task(
                "Criar sistema de combate",
                "Implementar CombatSystem com dano, cooldown de ataque e feedback visual.",
                ["src/systems/CombatSystem.js"],
                depends_on=[t_enemies],
                priority=2,
            )

        if "inventory" in systems:
            last_system_task = add_task(
                "Criar sistema de inventário",
                "Implementar InventorySystem com slots, adicionar/remover itens.",
                ["src/systems/InventorySystem.js"],
                depends_on=[t_player],
                priority=2,
            )

        if "hunger" in systems:
            add_task(
                "Criar sistema de fome",
                "Implementar HungerSystem com decaimento ao longo do tempo e dano quando zerado.",
                ["src/systems/HungerSystem.js"],
                depends_on=[t_player],
                priority=3,
            )

        if "stamina" in systems:
            add_task(
                "Criar sistema de stamina",
                "Implementar StaminaSystem com consumo em corrida/ataque e regeneração.",
                ["src/systems/StaminaSystem.js"],
                depends_on=[t_player],
                priority=3,
            )

        t_hud = add_task(
            "Criar HUD",
            "Implementar HUD com barras de vida/stamina/fome conforme sistemas ativos.",
            ["src/ui/HUD.js"],
            depends_on=[last_system_task],
            priority=2,
        )

        t_menu = add_task(
            "Criar menu principal e pausa",
            "Implementar MainMenu e PauseMenu com navegação funcional.",
            ["src/ui/MainMenu.js", "src/ui/PauseMenu.js"],
            depends_on=[t_scaffold],
            priority=3,
        )

        t_map = add_task(
            "Criar mapa e colisões",
            "Implementar MapLoader com tiles, limites de mapa e colisão com cenário.",
            ["src/map/MapLoader.js"],
            depends_on=[t_engine],
            priority=2,
        )

        t_assets = add_task(
            "Gerar assets visuais",
            "Gerar sprites de player, inimigos, itens e tiles via AssetGenerator, "
            "respeitando o VisualStyleManager do projeto.",
            ["assets/manifest.json"],
            depends_on=[t_player, t_enemies],
            priority=2,
        )

        add_task(
            "Testar e validar projeto",
            "Executar GameTestEngine: validação de arquivos, sintaxe, smoke test de carregamento.",
            ["*"],
            depends_on=[t_hud, t_menu, t_map, t_assets],
            priority=1,
            acceptance_criteria=["Todos os testes de validação de arquivo passam"],
        )

        return tasks