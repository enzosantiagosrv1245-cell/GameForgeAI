"""
AssetGenerator (item 12 da especificação) com submódulos de geração por
categoria (CharacterGenerator, EnemyGenerator, ItemGenerator, etc. -
item 12 lista). Implementados aqui como métodos especializados que
delegam ao ImageGenerationProvider configurado, sempre respeitando o
VisualStyleManager do projeto (item 15 - consistência visual
obrigatória).
"""
from __future__ import annotations

import os
from typing import Any

from app.assets.visual_style_manager import VisualStyleManager
from app.providers.base import ImageGenerationProvider


class AssetGenerator:
    def __init__(
        self,
        image_provider: ImageGenerationProvider,
        style_manager: VisualStyleManager,
        output_dir: str,
    ) -> None:
        self.image_provider = image_provider
        self.style_manager = style_manager
        self.output_dir = output_dir

    async def generate_character(self, name: str) -> dict[str, Any]:
        return await self._generate("character", name)

    async def generate_enemy(self, name: str) -> dict[str, Any]:
        return await self._generate("enemy", name)

    async def generate_item(self, name: str) -> dict[str, Any]:
        return await self._generate("item", name)

    async def generate_weapon(self, name: str) -> dict[str, Any]:
        return await self._generate("weapon", name)

    async def generate_environment_object(self, name: str) -> dict[str, Any]:
        return await self._generate("environment", name)

    async def generate_tile(self, name: str) -> dict[str, Any]:
        return await self._generate("tile", name, size=32)

    async def generate_ui_asset(self, name: str) -> dict[str, Any]:
        return await self._generate("ui", name, size=(96, 32))

    async def generate_icon(self, name: str) -> dict[str, Any]:
        return await self._generate("icon", name, size=24)

    async def generate_vfx(self, name: str) -> dict[str, Any]:
        return await self._generate("vfx", name)

    async def _generate(
        self, asset_type: str, name: str, size: int | tuple[int, int] = 64
    ) -> dict[str, Any]:
        if isinstance(size, tuple):
            width, height = size
        else:
            width = height = size

        safe_name = name.lower().replace(" ", "_")
        filename = f"{asset_type}_{safe_name}.png"
        output_path = os.path.join(self.output_dir, filename)

        style_spec = self.style_manager.style_for_asset(asset_type)
        result = await self.image_provider.generate(
            prompt=name,
            output_path=output_path,
            width=width,
            height=height,
            style_spec=style_spec,
        )

        return {
            "name": name,
            "asset_type": asset_type,
            "file_path": result.file_path,
            "width": result.width,
            "height": result.height,
            "provider_used": result.provider_name,
            "is_placeholder": result.is_placeholder,
            "style_spec": style_spec,
        }

    async def generate_full_manifest(self, design_spec: dict[str, Any]) -> list[dict[str, Any]]:
        """Gera o conjunto completo de assets necessários para o design_spec
        (player, inimigos, itens, tiles) de uma vez, retornando a lista de
        resultados para persistência no banco (tabela `assets`)."""
        results: list[dict[str, Any]] = []

        results.append(await self.generate_character("Player"))

        for enemy in design_spec.get("enemies", []):
            results.append(await self.generate_enemy(enemy["name"]))

        for item in design_spec.get("items", []):
            results.append(await self.generate_item(item["name"]))

        results.append(await self.generate_tile("Chao"))
        results.append(await self.generate_tile("Obstaculo"))

        return results