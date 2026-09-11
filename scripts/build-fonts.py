#!/usr/bin/env python3
"""
Subseta Inter e Fraunces para o repertorio que a pagina realmente usa.

Ferramenta de desenvolvimento — NAO faz parte do build do site. Rode so
quando as fontes de origem ou o conteudo mudarem.

    pip install fonttools brotli
    python scripts/build-fonts.py

Baixe os TTF de origem antes, do repositorio oficial do Google Fonts:
    https://github.com/google/fonts/tree/main/ofl/inter
    https://github.com/google/fonts/tree/main/ofl/fraunces
e coloque em scripts/fonts-src/ (ignorado pelo git).

Por que variavel, e nao instancias estaticas por peso: o CSS usa 400, 450,
500 e 600. Tres estaticos custam 54,8 KB e ainda assim nao tem o 450 — o
browser cairia no 400 e a meta das linhas perderia o peso que o design pede.
Um Inter variavel com o eixo wght inteiro custa 41,0 KB e cobre qualquer
peso. Medido, nao presumido: rode o script e confira a saida.

Os dois tem o eixo opsz fixado, e nos dois casos a razao e a mesma: medida.
O Inter vai em 16 porque o texto da pagina vive entre 13 e 19px. O Fraunces
vai em 28 porque a assinatura renderiza entre 24 e 32px — uma faixa de 1,33x,
onde a diferenca optica e sutil. Manter o eixo ali custava 18,3 KB (39,7 contra
21,4), ou 12% do orcamento de 150 KB da pagina inteira, para um ganho que nao
se ve. font-optical-sizing: auto vira no-op e saiu do CSS junto.
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "scripts" / "fonts-src"
OUT = ROOT / "companies" / "player" / "assets" / "fonts"
TMP = ROOT / "scripts" / ".fonts-tmp"

# latin + latin-ext cobre pt-BR (ç, ã, õ, á, é, í, ó, ú, â, ê, ô)
UNICODES = (
    "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,"
    "U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,"
    "U+FEFF,U+FFFD"
)

# (origem, saida, eixos fixados — os nao citados permanecem variaveis)
JOBS = [
    ("Inter[opsz,wght].ttf", "inter.woff2", ["opsz=16"]),
    (
        "Fraunces-Italic[SOFT,WONK,opsz,wght].ttf",
        "fraunces-italic.woff2",
        ["wght=500", "SOFT=0", "WONK=1", "opsz=28"],
    ),
]


def main():
    if not SRC.is_dir():
        sys.exit(f"coloque os TTF de origem em {SRC}")
    OUT.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(exist_ok=True)

    total = 0
    for src_name, out_name, axes in JOBS:
        src = SRC / src_name
        if not src.is_file():
            sys.exit(f"fonte de origem ausente: {src}")

        # 1. Fixar os eixos que nao variam, preservando os demais.
        #    Separado do subset de proposito: fontTools.subset sozinho nao
        #    instancia eixo, e a flag para isso mudou entre versoes.
        parcial = TMP / out_name.replace(".woff2", ".ttf")
        subprocess.run(
            [sys.executable, "-m", "fontTools.varLib.instancer",
             str(src), *axes, "-o", str(parcial)],
            check=True, stdout=subprocess.DEVNULL,
        )

        # 2. Subsetar e converter para woff2. Sem --desubroutinize: ele so
        #    vale para CFF, e estas duas sao glyf/gvar.
        subprocess.run(
            [sys.executable, "-m", "fontTools.subset", str(parcial),
             f"--unicodes={UNICODES}",
             "--layout-features=kern,liga,calt,tnum",
             "--flavor=woff2",
             "--no-hinting",
             f"--output-file={OUT / out_name}"],
            check=True,
        )

        tamanho = (OUT / out_name).stat().st_size
        total += tamanho
        print(f"  {out_name}: {tamanho / 1024:.1f} KB")
        parcial.unlink()

    TMP.rmdir()
    print(f"  total: {total / 1024:.1f} KB")


if __name__ == "__main__":
    main()
