#!/usr/bin/env python3
"""Regenera os assets de marca da Player a partir dos SVGs originais.

Os SVGs entregues pela agência são híbridos: parte vetor, parte PNG embutido em
base64. Este script extrai o raster, recompõe o canal alfa e gera versões
enxutas para a web.

Não faz parte do build do site — o site é estático e não tem dependências.
Rode apenas quando os arquivos de marca originais mudarem.

    pip install Pillow
    python scripts/build-brand-assets.py

Entradas  (companies/player/assets/):
    logo_grupo_player.svg   lockup para fundo claro (wordmark navy + símbolo)
    favicon.svg             símbolo "play" isolado   [removido do repo; pegue
                            no histórico do Git se precisar regerar os ícones]

Saídas    (companies/player/assets/):
    logo_grupo_player_dark.svg   wordmark branco, rasters reduzidos
    favicon.ico / -32.png / -180.png
"""

from __future__ import annotations

import base64
import io
import re
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow não encontrado. Rode: pip install Pillow")

ASSETS = Path(__file__).resolve().parent.parent / "companies" / "player" / "assets"

DATA_URI = re.compile(r"data:image/png;base64,([A-Za-z0-9+/=]+)")

# Cor do wordmark no SVG original e a cor equivalente para fundo escuro.
WORDMARK_FROM = 'fill="#0e1c2c"'
WORDMARK_TO = 'fill="#ffffff"'

# O símbolo aparece a ~60 px na tela; 400 px cobre telas 3x com folga.
SYMBOL_RASTER_WIDTH = 400


def _embedded_pngs(svg: str) -> list[Image.Image]:
    """Decodifica os PNGs embutidos, na ordem em que aparecem no SVG."""
    return [
        Image.open(io.BytesIO(base64.b64decode(m)))
        for m in DATA_URI.findall(svg)
    ]


def build_dark_logo() -> None:
    """Wordmark branco + rasters do símbolo reduzidos."""
    src_path = ASSETS / "logo_grupo_player.svg"
    if not src_path.exists():
        print(f"  pulando: {src_path.name} não encontrado")
        return

    svg = src_path.read_text(encoding="utf-8", errors="replace")
    before = len(svg)

    def shrink(match: re.Match[str]) -> str:
        img = Image.open(io.BytesIO(base64.b64decode(match.group(1))))
        height = round(img.height * SYMBOL_RASTER_WIDTH / img.width)
        buf = io.BytesIO()
        img.resize((SYMBOL_RASTER_WIDTH, height), Image.LANCZOS).save(
            buf, format="PNG", optimize=True
        )
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

    out = DATA_URI.sub(shrink, svg)
    out, recolored = re.subn(re.escape(WORDMARK_FROM), WORDMARK_TO, out)

    (ASSETS / "logo_grupo_player_dark.svg").write_text(out, encoding="utf-8")
    print(
        f"  logo_grupo_player_dark.svg: {before:,} -> {len(out):,} bytes"
        f" ({recolored} fills recoloridos)"
    )


def build_favicons() -> None:
    """Recompõe o símbolo em RGBA e exporta o jogo de ícones."""
    src_path = ASSETS / "favicon.svg"
    if not src_path.exists():
        print("  pulando favicons: favicon.svg não está no repo (veja o histórico)")
        return

    svg = src_path.read_text(encoding="utf-8", errors="replace")
    images = _embedded_pngs(svg)
    if len(images) != 2:
        sys.exit(f"esperava 2 PNGs embutidos em favicon.svg, achei {len(images)}")

    # O SVG usa o primeiro PNG como máscara de luminância do segundo.
    mask, art = images[0].convert("L"), images[1].convert("RGB")
    rgba = art.copy()
    rgba.putalpha(mask)

    # Desfaz o transform do SVG para chegar na região visível do viewBox.
    match = re.search(
        r"matrix\(([\d.]+),\s*0,\s*0,\s*([\d.]+),\s*(-?[\d.]+),\s*(-?[\d.]+)\)", svg
    )
    view = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
    if not (match and view):
        sys.exit("não consegui ler o transform/viewBox de favicon.svg")

    sx, sy, tx, ty = (float(g) for g in match.groups())
    vw, vh = float(view.group(1)), float(view.group(2))
    visible = rgba.crop(
        (round(-tx / sx), round(-ty / sy), round((vw - tx) / sx), round((vh - ty) / sy))
    )

    # Apara pelo alfa e centraliza num quadrado com 4% de respiro.
    tight = visible.crop(visible.split()[3].getbbox())
    side = int(max(tight.size) * 1.08)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(tight, ((side - tight.width) // 2, (side - tight.height) // 2))

    square.resize((180, 180), Image.LANCZOS).save(
        ASSETS / "favicon-180.png", optimize=True
    )
    square.resize((32, 32), Image.LANCZOS).save(
        ASSETS / "favicon-32.png", optimize=True
    )
    square.resize((256, 256), Image.LANCZOS).save(
        ASSETS / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)]
    )
    print("  favicon.ico, favicon-32.png, favicon-180.png")


if __name__ == "__main__":
    print(f"assets em {ASSETS}")
    build_dark_logo()
    build_favicons()
    print("pronto.")
