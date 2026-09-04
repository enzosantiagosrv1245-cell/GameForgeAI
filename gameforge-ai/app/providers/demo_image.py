"""
DemoImageProvider (item 52 - "não inventar capacidades").

Este provider NÃO chama nenhuma API paga de geração de imagem. Em vez
disso, gera sprites reais e funcionais proceduralmente usando Pillow:
formas geométricas coloridas de acordo com o VisualStyleManager do
projeto (paleta, outline, etc). O arquivo PNG gerado é real, válido,
carregável por qualquer engine - não é um "fingimento".

Quando um provider real (Stable Diffusion local, API paga, etc.) for
conectado no futuro, basta implementar ImageGenerationProvider e trocar
IMAGE_PROVIDER no .env - nenhum código consumidor precisa mudar.
"""
from __future__ import annotations

import hashlib
import os
import random
from typing import Any, Optional

from PIL import Image, ImageDraw

from app.providers.base import ImageGenerationProvider, ImageGenerationResult

# Formas simples por tipo de asset - mantém coerência visual básica
ASSET_SHAPE_MAP = {
    "character": "humanoid",
    "enemy": "humanoid",
    "item": "diamond",
    "weapon": "blade",
    "environment": "blob",
    "tile": "square",
    "ui": "rounded_rect",
    "icon": "circle",
    "vfx": "burst",
}


def _seeded_random(seed_text: str) -> random.Random:
    seed_int = int(hashlib.sha256(seed_text.encode()).hexdigest(), 16) % (2**32)
    return random.Random(seed_int)


def _draw_humanoid(draw: ImageDraw.ImageDraw, w: int, h: int, primary, outline, rng):
    cx = w // 2
    head_r = w // 6
    draw.ellipse(
        [cx - head_r, h * 0.1, cx + head_r, h * 0.1 + head_r * 2],
        fill=primary,
        outline=outline,
        width=2,
    )
    body_top = h * 0.1 + head_r * 2
    draw.rectangle(
        [cx - w // 5, body_top, cx + w // 5, h * 0.75],
        fill=primary,
        outline=outline,
        width=2,
    )
    draw.rectangle([cx - w // 6, h * 0.75, cx - w // 16, h * 0.95], fill=primary, outline=outline)
    draw.rectangle([cx + w // 16, h * 0.75, cx + w // 6, h * 0.95], fill=primary, outline=outline)


def _draw_diamond(draw, w, h, primary, outline, rng):
    cx, cy = w // 2, h // 2
    size = min(w, h) // 3
    draw.polygon(
        [(cx, cy - size), (cx + size, cy), (cx, cy + size), (cx - size, cy)],
        fill=primary,
        outline=outline,
    )


def _draw_blade(draw, w, h, primary, outline, rng):
    draw.polygon(
        [(w * 0.5, h * 0.1), (w * 0.62, h * 0.55), (w * 0.5, h * 0.65), (w * 0.38, h * 0.55)],
        fill=primary,
        outline=outline,
    )
    draw.rectangle([w * 0.45, h * 0.65, w * 0.55, h * 0.9], fill=outline)


def _draw_blob(draw, w, h, primary, outline, rng):
    points = []
    cx, cy = w / 2, h / 2
    for i in range(10):
        angle = (i / 10) * 6.283
        r = min(w, h) / 3 * rng.uniform(0.7, 1.0)
        points.append((cx + r * __import__("math").cos(angle), cy + r * __import__("math").sin(angle)))
    draw.polygon(points, fill=primary, outline=outline)


def _draw_square(draw, w, h, primary, outline, rng):
    draw.rectangle([w * 0.05, h * 0.05, w * 0.95, h * 0.95], fill=primary, outline=outline, width=2)


def _draw_rounded_rect(draw, w, h, primary, outline, rng):
    draw.rounded_rectangle([w * 0.05, h * 0.15, w * 0.95, h * 0.85], radius=w // 8, fill=primary, outline=outline, width=2)


def _draw_circle(draw, w, h, primary, outline, rng):
    m = min(w, h) * 0.1
    draw.ellipse([m, m, w - m, h - m], fill=primary, outline=outline, width=2)


def _draw_burst(draw, w, h, primary, outline, rng):
    cx, cy = w / 2, h / 2
    for i in range(8):
        angle = (i / 8) * 6.283
        x2 = cx + (w / 2.2) * __import__("math").cos(angle)
        y2 = cy + (h / 2.2) * __import__("math").sin(angle)
        draw.line([(cx, cy), (x2, y2)], fill=primary, width=max(2, w // 20))


SHAPE_DRAWERS = {
    "humanoid": _draw_humanoid,
    "diamond": _draw_diamond,
    "blade": _draw_blade,
    "blob": _draw_blob,
    "square": _draw_square,
    "rounded_rect": _draw_rounded_rect,
    "circle": _draw_circle,
    "burst": _draw_burst,
}


class DemoImageProvider(ImageGenerationProvider):
    name = "demo-procedural"

    async def generate(
        self,
        prompt: str,
        output_path: str,
        width: int = 64,
        height: int = 64,
        style_spec: Optional[dict[str, Any]] = None,
    ) -> ImageGenerationResult:
        style_spec = style_spec or {}
        asset_type = style_spec.get("asset_type", "item")
        shape_name = ASSET_SHAPE_MAP.get(asset_type, "square")
        drawer = SHAPE_DRAWERS.get(shape_name, _draw_square)

        rng = _seeded_random(prompt + asset_type)

        palette = style_spec.get("palette") or [
            (rng.randint(40, 220), rng.randint(40, 220), rng.randint(40, 220))
        ]
        primary = tuple(palette[0]) if isinstance(palette[0], (list, tuple)) else palette[0]
        outline_style = style_spec.get("outline_style", "dark")
        outline = (20, 20, 24, 255) if outline_style == "dark" else (240, 240, 240, 255)

        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        rgba_primary = (*primary[:3], 255) if len(primary) >= 3 else (120, 160, 200, 255)
        drawer(draw, width, height, rgba_primary, outline, rng)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, "PNG")

        return ImageGenerationResult(
            file_path=output_path,
            provider_name=self.name,
            width=width,
            height=height,
            is_placeholder=True,
        )