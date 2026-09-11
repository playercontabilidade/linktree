#!/usr/bin/env python3
"""
Gera a imagem de compartilhamento 1200x630 da Player.

Ferramenta de desenvolvimento — NAO faz parte do build do site.

    pip install pillow
    python scripts/build-og-image.py

Depende de scripts/fonts-src/Fraunces-Italic[SOFT,WONK,opsz,wght].ttf, o mesmo
arquivo que build-fonts.py usa (baixe conforme o cabecalho daquele script).

Sobre o upscale do lockup: a arte de origem tem 225px de largura e aqui ela
vai para 420px. O numero e maior que o nativo, mas a carta e autorada a
1200x630 e exibida por volta de 500-600px de largura nas previews, o que
devolve o logo para ~175-210px — ou seja, na pratica ele e exibido no
tamanho nativo ou abaixo dele.
"""
import pathlib
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("pip install pillow")

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "companies" / "player" / "assets"
LOGO = ASSETS / "logo_player_on_dark.png"
FONT = ROOT / "scripts" / "fonts-src" / "Fraunces-Italic[SOFT,WONK,opsz,wght].ttf"
OUT = ASSETS / "og-image.png"

W, H = 1200, 630
SURFACE = (20, 26, 41)      # --surface do tema escuro
TEXT = (236, 224, 212)      # --text
ACCENT = (255, 170, 0)      # --accent-surface
TAGLINE = "Somos cientistas da riqueza e da prosperidade."
MARGEM = 90


def assinatura(tamanho):
    """Fraunces no peso 500 — o mesmo da pagina.

    A instancia padrao do arquivo variavel e Black (wght 900); sem fixar os
    eixos a carta sairia muito mais pesada que a assinatura no site.
    """
    f = ImageFont.truetype(str(FONT), tamanho)
    try:
        # Ordem do fvar: opsz, wght, SOFT, WONK. opsz acompanha o corpo.
        f.set_variation_by_axes([float(tamanho), 500.0, 0.0, 1.0])
    except (OSError, AttributeError):
        print("  aviso: FreeType sem suporte a eixos; usando a instancia padrao")
    return f


def main():
    for path in (LOGO, FONT):
        if not path.is_file():
            sys.exit(f"arquivo necessario ausente: {path}")

    canvas = Image.new("RGB", (W, H), SURFACE)
    draw = ImageDraw.Draw(canvas)

    logo = Image.open(LOGO).convert("RGBA")
    alvo = 420
    logo = logo.resize((alvo, round(logo.height * alvo / logo.width)), Image.LANCZOS)
    canvas.paste(logo, ((W - logo.width) // 2, 196), logo)

    # Encolhe ate caber numa linha, em vez de confiar num numero fixo.
    tamanho = 44
    while tamanho > 24:
        fonte = assinatura(tamanho)
        caixa = draw.textbbox((0, 0), TAGLINE, font=fonte)
        largura = caixa[2] - caixa[0]
        if largura <= W - 2 * MARGEM:
            break
        tamanho -= 2
    draw.text(((W - largura) // 2 - caixa[0], 392), TAGLINE, font=fonte, fill=TEXT)

    # Regua ambar na base — o unico acento de cor, como na pagina.
    draw.rectangle([(0, H - 6), (W, H)], fill=ACCENT)

    canvas.save(OUT, "PNG", optimize=True)
    print(f"  {OUT.name}: {canvas.size[0]}x{canvas.size[1]}, "
          f"{OUT.stat().st_size / 1024:.1f} KB, assinatura em {tamanho}px")


if __name__ == "__main__":
    main()
