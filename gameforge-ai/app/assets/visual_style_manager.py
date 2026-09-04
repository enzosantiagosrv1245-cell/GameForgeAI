"""
VisualStyleManager (item 15 da especificação).

Mantém e aplica as regras de consistência visual do projeto: paleta,
estilo de contorno, iluminação, perspectiva, escala de sprite,
proporções de personagem, estilo de ambiente e de UI. Todo asset gerado
para o projeto consulta este módulo antes de ser criado.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


PALETTES = {
    "dark": [(60, 20, 25), (90, 40, 45), (40, 40, 50), (150, 60, 40), (20, 20, 24)],
    "pixel_art": [(88, 130, 87), (172, 194, 132), (61, 61, 84), (215, 123, 78)],
    "cartoon": [(255, 195, 100), (100, 180, 255), (255, 120, 150), (140, 220, 140)],
    "realistic": [(90, 85, 75), (120, 110, 95), (60, 55, 50), (150, 140, 120)],
    "minimalist": [(230, 230, 235), (60, 60, 65), (140, 140, 150)],
}


@dataclass
class VisualStyleSpec:
    art_style: str = "minimalist"
    palette: list = field(default_factory=lambda: PALETTES["minimalist"])
    outline_style: str = "dark"  # dark | light | none
    lighting: str = "flat"  # flat | soft_shadow | dramatic
    perspective: str = "top_down"  # top_down | side | isometric
    sprite_scale: int = 64  # px
    character_proportions: str = "realistic"  # realistic | chibi | stylized
    environment_style: str = "match_character"
    ui_style: str = "flat_dark"

    def to_dict(self) -> dict[str, Any]:
        return {
            "art_style": self.art_style,
            "palette": self.palette,
            "outline_style": self.outline_style,
            "lighting": self.lighting,
            "perspective": self.perspective,
            "sprite_scale": self.sprite_scale,
            "character_proportions": self.character_proportions,
            "environment_style": self.environment_style,
            "ui_style": self.ui_style,
        }

    @classmethod
    def from_design_spec(cls, design_spec: dict[str, Any]) -> "VisualStyleSpec":
        visual_styles = design_spec.get("visual_style", ["minimalist"])
        art_style = visual_styles[0] if visual_styles else "minimalist"
        palette = PALETTES.get(art_style, PALETTES["minimalist"])
        camera = design_spec.get("camera", "top_down")

        return cls(
            art_style=art_style,
            palette=palette,
            outline_style="dark" if art_style == "dark" else "light",
            lighting="dramatic" if art_style == "dark" else "flat",
            perspective=camera,
            sprite_scale=32 if art_style == "pixel_art" else 64,
            character_proportions="chibi" if art_style == "cartoon" else "realistic",
        )


class VisualStyleManager:
    """Gerencia a especificação de estilo de um projeto e a aplica de
    forma consistente a todos os pedidos de geração de asset."""

    def __init__(self, style_spec: VisualStyleSpec) -> None:
        self.style_spec = style_spec

    def style_for_asset(self, asset_type: str) -> dict[str, Any]:
        """Retorna o dicionário de estilo a ser passado ao ImageGenerationProvider,
        já anotado com o tipo de asset para escolha de forma/silhueta."""
        base = self.style_spec.to_dict()
        base["asset_type"] = asset_type
        return base

    @classmethod
    def for_project(cls, design_spec: dict[str, Any]) -> "VisualStyleManager":
        return cls(VisualStyleSpec.from_design_spec(design_spec))