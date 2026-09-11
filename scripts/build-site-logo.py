#!/usr/bin/env python3
"""
Deriva as variantes do lockup oficial do site (Player Contabilidade).

Ferramenta de desenvolvimento — NAO faz parte do build do site. Rode so
quando a arte de origem mudar.

    pip install pillow
    python scripts/build-site-logo.py

A origem e o PNG que playercontabilidade.com serve em
img/logo/logo-principal.png, ja versionado aqui. Nao existe SVG publicado:
o proprio site renderiza este PNG de 225x75. Tres saidas:

  logo_player_on_dark.png   lockup como veio (lettering claro)
  logo_player_on_light.png  lettering recolorido para a tinta do tema claro
  mark_player.png           so o simbolo, recortado, para uso como icone

O recorte por coluna (e nao por cor) e proposital: o simbolo ocupa as
colunas 0..57 e o lettering comeca na 59, entao a fronteira e geometrica e
nao depende de acertar um limiar de matiz nos pixels de antialiasing.
"""
import pathlib
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("pip install pillow")

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "companies" / "player" / "assets"
SRC = ASSETS / "logo_grupo_player_light.png"

# Fronteira entre simbolo e lettering, medida na arte de origem.
SYMBOL_END_X = 58

# --text do tema claro, em brand.css.
INK_LIGHT = (39, 49, 61)

# Acima disto o pixel e do lettering acromatico; o simbolo dourado fica
# muito abaixo. So vale na regiao do lettering, entao e uma rede de seguranca.
MAX_CHROMA = 60


def main():
    if not SRC.is_file():
        sys.exit(f"arte de origem ausente: {SRC}")

    src = Image.open(SRC).convert("RGBA")
    w, h = src.size

    # 1. Variante para fundo escuro: a arte original, sem tocar.
    src.save(ASSETS / "logo_player_on_dark.png")

    # 2. Variante para fundo claro: so o lettering troca de tinta. O alfa ja
    #    carrega a forma e o antialiasing, entao basta trocar o RGB e manter
    #    o alfa — as bordas continuam suaves contra qualquer fundo.
    light = src.copy()
    px = light.load()
    trocados = 0
    for y in range(h):
        for x in range(SYMBOL_END_X, w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if max(r, g, b) - min(r, g, b) <= MAX_CHROMA:
                px[x, y] = (*INK_LIGHT, a)
                trocados += 1
    light.save(ASSETS / "logo_player_on_light.png")

    # 3. Simbolo sozinho, aparado pelo proprio alfa, para servir de icone.
    mark = src.crop((0, 0, SYMBOL_END_X, h))
    caixa = mark.getbbox()
    if caixa:
        mark = mark.crop(caixa)
    mark.save(ASSETS / "mark_player.png")

    for nome in ("logo_player_on_dark.png", "logo_player_on_light.png", "mark_player.png"):
        p = ASSETS / nome
        print(f"  {nome}: {Image.open(p).size} {p.stat().st_size / 1024:.1f} KB")
    print(f"  ({trocados} px de lettering recoloridos)")


if __name__ == "__main__":
    main()
