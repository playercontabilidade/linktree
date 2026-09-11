# Redesign premium — Linktree Grupo Player

**Data:** 2026-09-10
**Branch:** `feat/player-linktree`
**Status:** aguardando revisão

---

## Objetivo

Elevar a página de links da Player de "dark-glass bem executado" para um artefato
com padrão de agência, sem trocar a stack e sem introduzir dependência de runtime.
Três frentes: identidade visual (direção editorial escura, com tema claro
institucional alternativo), sistema de design compartilhável entre as empresas do
Grupo, e uma camada de movimento guiada por scroll.

## Restrições herdadas

- **Zero dependência de runtime.** Sem framework, sem bundler, sem `node_modules`
  no caminho crítico. Node e Python continuam sendo ferramenta de
  desenvolvimento, nunca requisito para abrir e editar um arquivo.
- **GitHub Pages** como destino, com `BASE_PATH` injetado no CI.
- **Português brasileiro** no conteúdo, commits em inglês.

## Decisões travadas nesta sessão

| Decisão | Escolha |
|---|---|
| Stack | Estático + upgrade técnico real. Sem framework. |
| Escopo do design system | Sistema do Grupo desde já: primitivos em `shared/`, semânticos por empresa. |
| Direção estética canônica | **A — Editorial escuro.** Premium por contenção. |
| Tema alternativo | **B — Claro institucional**, via toggle. Mesma estrutura, outra paleta. |
| Conteúdo | Hero de links (primeira tela intacta) + 3 seções curtas abaixo. |
| Movimento | Scroll-driven nativo, um único momento pinado, parallax medido. |

---

## 1 · Arquitetura de arquivos

```
shared/
  css/
    layers.css      declaração da ordem de camadas (carregado primeiro)
    tokens.css      primitivos do Grupo — sem semântica de marca
    base.css        reset, tipografia base, utilidades
  js/
    config.js       GERADO (existente)
    theme.js        lógica do toggle (o set anti-flash é inline no <head>, ver §3)
companies/player/
  index.html
  css/
    brand.css       tokens semânticos da Player (mapeia primitivos → papéis)
    styles.css      componentes e layout da página
  js/main.js
  assets/
    fonts/          woff2 subsetados
scripts/
  build-fonts.py    subsetting das fontes (dev-only, precedente: build-brand-assets.py)
```

**Carregamento:** múltiplas tags `<link rel="stylesheet">`, não `@import`. `@import`
serializa requisições; `<link>` paraleliza. O total comprimido fica em ~6 KB, então
o custo de várias folhas é irrelevante e o ganho de editabilidade é real.

**Ordem da cascata:** `layers.css` declara `@layer reset, tokens, base, components,
motion, utilities;` numa linha única, antes de qualquer regra, e **precisa preceder
toda folha que participe dessa ordem** — `tokens.css`, `base.css`, `brand.css` e
`styles.css`. Folhas são aplicadas em ordem de documento, então é essa posição
relativa que garante a declaração antes de qualquer uso.

Não precisa ser a primeira tag `<link>` do `<head>`: `rel="icon"` e
`rel="preconnect"` não carregam CSS, e a folha do Google Fonts não declara camada
alguma — conteúdo sem camada ordena por último pela própria especificação,
independente de onde apareça (e essa folha sai do documento na etapa de fontes
self-hosted). Com a ordem estabelecida na frente, a ordem das demais folhas deixa
de importar para a precedência — que é exatamente o motivo de usar `@layer` aqui,
e não estética.

## 2 · Camada de tokens

Dois níveis, com uma regra dura: **primitivo não conhece marca, componente não
conhece primitivo.** Componente só consome token semântico.

**Primitivos (`shared/css/tokens.css`)** — escala tipográfica fluida com `clamp()`,
escala de espaço com base 4 px (4/8/12/16/24/32/48/64/96/128), raios, elevações,
durações e curvas de movimento. Nenhum valor de marca.

**Semânticos (`companies/player/css/brand.css`)** — papéis, não cores:
`--surface`, `--surface-raised`, `--text`, `--text-muted`, `--rule`,
`--accent-surface`, `--accent-text`, `--focus`.

A separação entre `--accent-surface` e `--accent-text` não é purismo: o âmbar da
marca (`#FFAA00`) sobre o fundo osso do tema claro dá **~1,8:1** de contraste, e
mesmo o `--amber-deep` (`#F88805`) fica em ~2,4:1. Ambos reprovam em AA para texto.
No tema claro o âmbar continua servindo como **superfície e acento**, mas texto de
destaque usa um âmbar profundo (alvo `#8A4B02`, ~7:1 sobre osso — a medir na
implementação). No tema escuro os dois papéis podem apontar para o mesmo âmbar.
Essa é a primeira dívida que o token layer paga.

## 3 · Sistema de temas

- `<html data-theme="dark|light">`. Sem atributo, vale `prefers-color-scheme`.
- Toggle discreto no topo do shell — ícone, sem rótulo, alvo de 44 px.
- Persistência em `localStorage`.
- **Script inline anti-flash no `<head>`**, antes de qualquer pintura, lendo
  `localStorage` e aplicando `data-theme`. O repositório já corrigiu flash branco
  uma vez (`91fd22a`); a mesma disciplina se aplica aqui.
- A propriedade CSS `color-scheme` acompanha o tema, para que scrollbar e controles
  nativos sigam junto.
- `<meta name="theme-color">` duplicada com `media="(prefers-color-scheme: …)"`.
- **A estrutura não muda entre temas.** Mesmo layout editorial, duas paletas. Trocar
  estrutura por tema significaria manter dois designs; o tema troca token, não DOM.

Ambos os temas devem passar AA. O escuro herda o piso já medido no projeto
(mínimo atual 6,15:1); o claro precisa de medição nova.

## 4 · Linguagem de movimento

**Princípio:** contenção nas superfícies, sofisticação no movimento. Lento, escasso
e motivado — um único momento pinado na página inteira, parallax em dezenas de
pixels, nunca sobre texto.

| Momento | Técnica | Suporte |
|---|---|---|
| Entrada do hero | Cascata escalonada, curva `--ease` existente | Universal |
| Fundo desloca ao rolar | `animation-timeline: scroll()`, ~40 px de diferencial | Enhancement |
| Hero → conteúdo | Único pin: bloco de marca prende, a seção sobe por baixo, solta | `sticky` universal; progressão é enhancement |
| Seção "O que a Player faz" | Reveal escalonado com `view()` | Enhancement |
| Fecho | CTA assenta na posição | Enhancement |

**Duração do pin.** Com apenas duas seções abaixo do hero, um pin de viewport
inteiro vira enchimento. Alvo inicial: ~0,6 viewport, ajustado no protótipo. A
página fecha em torno de 3,3 viewports no mobile — folga suficiente para a
coreografia sem inventar scroll.

**Degradação.** `position: sticky` é Baseline e funciona em todo lugar, Firefox
incluído — o *pin* é estrutura universal. Só a progressão animada durante o pin
depende de `animation-timeline`, que o MDN marca como *Limited availability, not
Baseline*. Todo bloco de scroll-driven fica dentro de
`@supports (animation-timeline: view())`, e o estado padrão de todo elemento é
**visível**. Sem suporte: layout correto, conteúdo legível, sem progressão. Nada
preso em `opacity: 0`.

**Parallax por `animation-timeline: scroll()`, não por `perspective` + `translateZ`.**
Ancestrais com `perspective`/`transform` alteram containing block e comportamento de
contêiner de rolagem, o que briga com `position: sticky`. Manter o sticky limpo vale
mais do que ter parallax no Firefox. **Risco a validar em protótipo antes do CSS
final.**

`prefers-reduced-motion: reduce` derruba parallax, progressão e reveals. O sticky
permanece — é layout, não movimento.

## 5 · Estrutura de conteúdo

A primeira tela continua sendo **só os links**. A decisão de três segundos não
atrasa. Abaixo, duas seções curtas:

1. **O que a Player faz** — uma frase forte e duas ou três linhas de apoio.
2. **Fecho** — endereço em Palmas/TO, mapa e CTA final de WhatsApp.

A seção de credibilidade com números foi **cortada por decisão do cliente**: sem
dado real do Grupo em mãos, preencher com número inventado ou com texto genérico
sairia pior do que não ter a seção. Se os números aparecerem depois, ela entra
entre as duas atuais sem refatorar nada — a coreografia de scroll já prevê um
terceiro bloco.

## 6 · Upgrades técnicos

- **Fontes self-hosted.** Inter e Fraunces subsetadas (latin + latin-ext), woff2,
  `font-display: swap`, `preload` só nas faces críticas. Elimina dois `preconnect`,
  duas viagens ao Google e o terceiro na cadeia crítica — além de melhorar a postura
  de LGPD. Subsetting via `scripts/build-fonts.py`, dev-only, seguindo o precedente
  de `build-brand-assets.py`.
- **JSON-LD** `LocalBusiness` com endereço e geo (a latitude/longitude já existem no
  link do Maps).
- **OG image 1200×630 de verdade.** Hoje o `og:image` aponta para um PNG de logo,
  que renderiza mal em compartilhamento.
- **`.gitattributes`** com `shared/js/config.js text eol=lf`, corrigindo o falso
  "modified" que `npm run config` produz no Windows (`core.autocrlf=true`).
- **`npm start`**, ativando o `prestart` que hoje é código morto.
- **CI:** checagem de acessibilidade e performance no workflow do Pages, com
  orçamento que falha o build. Dependência de CI, não do site.

## 7 · Orçamentos

| Métrica | Alvo |
|---|---|
| CLS | 0 |
| LCP (4G móvel) | < 1,5 s |
| Peso da primeira visita | ≤ 150 KB |
| Contraste de texto | AA (4,5:1); grandes 3:1 |
| Lighthouse — acessibilidade | 100 |

## 8 · Fora de escopo

Migração para framework; segunda empresa em `companies/`; conteúdo dinâmico
(vagas por API, simulador tributário); pipeline JSON→CSS de tokens — entra quando
houver um segundo consumidor além do CSS.

## 9 · Questões abertas

1. **Texto da seção "O que a Player faz".** Vou redigir uma proposta a partir do tom
   já presente ("Somos cientistas da riqueza e da prosperidade"), marcada como
   rascunho para você editar. Nenhuma afirmação verificável sobre o negócio —
   posicionamento e tom, não fato.
2. **Endereço completo** da sede para o JSON-LD e para o fecho. Hoje só existem as
   coordenadas, extraídas do link do Google Maps. Sem o endereço, o JSON-LD sai como
   `Organization` em vez de `LocalBusiness` e o fecho mostra só "Palmas · Tocantins".
