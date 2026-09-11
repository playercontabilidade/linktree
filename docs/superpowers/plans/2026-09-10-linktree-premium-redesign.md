# Redesign Premium do Linktree — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Levar a página de links da Player de "dark-glass bem executado" para um artefato com padrão de agência — direção editorial escura com tema claro institucional, sistema de tokens compartilhável entre as empresas do Grupo, e movimento guiado por scroll — sem introduzir dependência de runtime.

**Architecture:** Três camadas de CSS carregadas em paralelo por `<link>`, com ordem de cascata fixada por `@layer` declarado na primeira folha. Tokens primitivos vivem em `shared/` e não conhecem marca; tokens semânticos vivem por empresa e mapeiam primitivos para papéis. Tema troca token, nunca estrutura. Movimento é enhancement puro sob `@supports (animation-timeline: view())`, com `position: sticky` (Baseline) carregando a estrutura em todo browser.

**Tech Stack:** HTML5, CSS puro (custom properties, `@layer`, `@supports`, scroll-driven animations), JavaScript ES5 em IIFE. Node 20+ e Python 3 apenas como ferramenta de desenvolvimento — nunca requisito de runtime.

**Spec:** [`docs/superpowers/specs/2026-09-10-linktree-premium-redesign-design.md`](../specs/2026-09-10-linktree-premium-redesign-design.md)

## Global Constraints

- **Zero dependência de runtime.** `package.json` continua sem `dependencies`. Nenhum `node_modules` no caminho crítico. Nenhum framework, bundler ou polyfill embarcado.
- **Node 20+** para scripts de desenvolvimento; **Python 3 + Pillow/fonttools** apenas para geração de assets, rodado sob demanda, nunca no build do site.
- **Conteúdo em pt-BR.** Mensagens de commit em inglês, formato Conventional Commits, escopo quando ajudar (`feat(player): ...`).
- **Todo texto passa AA:** 4,5:1 para corpo, 3:1 para texto grande. Piso do projeto: **6,15:1**.
- **`prefers-reduced-motion: reduce` derruba todo movimento.** `position: sticky` permanece — é layout, não movimento.
- **Tokens semânticos de cor devem ser hex literal**, nunca `rgba()` ou `color-mix()`. Variantes com alfa entram como hex já composto. Motivo: é o que torna a paleta verificável por máquina (Task 2).
- **Estado padrão de todo elemento animado é visível.** Nenhum `opacity: 0` fora de um bloco `@supports`.
- **`shared/js/config.js` é gerado.** Nunca editar à mão.
- **Não há test runner neste projeto e não vai haver.** O ciclo de teste de cada task é: (a) `node scripts/check-contrast.js` onde houver token de cor, (b) verificação no browser com asserção explícita via preview tools, (c) os orçamentos do CI (Task 12).

---

### Task 1: Higiene do repositório

Duas correções pequenas e independentes que limpam ruído antes do trabalho pesado. Sem elas, `git status` fica sujo durante o resto do plano e mascara mudanças reais.

**Files:**
- Create: `.gitattributes`
- Modify: `package.json`

**Interfaces:**
- Consumes: nada.
- Produces: `npm start` passa a existir e roda `npm run config` antes de servir (via o `prestart` que já existe).

- [ ] **Step 1: Reproduzir o bug de line-ending**

```bash
cd "D:/Projetos/projetos da player/linktree"
npm run config
git status --short
```

Esperado: `M shared/js/config.js`, mesmo o conteúdo sendo byte-idêntico ao commit. Causa: `core.autocrlf=true` espera CRLF na árvore de trabalho, e o Node escreve LF.

- [ ] **Step 2: Confirmar que o conteúdo é idêntico**

```bash
git diff shared/js/config.js
```

Esperado: saída vazia (só o warning de CRLF em stderr). Isso prova que é normalização, não mudança real.

- [ ] **Step 3: Criar `.gitattributes`**

```
# shared/js/config.js é gerado por scripts/generate-config.js, que escreve LF.
# Sem esta regra, core.autocrlf=true marca o arquivo como modificado no Windows
# a cada `npm run config`, mesmo sem mudança de conteúdo.
shared/js/config.js text eol=lf

# Normaliza o resto do texto para LF no repositório.
* text=auto eol=lf
```

- [ ] **Step 4: Verificar que o bug sumiu**

```bash
git checkout -- shared/js/config.js
npm run config
git status --short
```

Esperado: **saída vazia**. Se ainda aparecer `M`, rode `git add --renormalize .` e commite a renormalização como passo separado.

- [ ] **Step 5: Provar que `npm start` está quebrado hoje**

```bash
npm start
```

Esperado: `npm error Missing script: "start"`. O `prestart` no `package.json` nunca dispara porque não existe `start` para ele preceder.

- [ ] **Step 6: Adicionar o script `start`**

```bash
npm pkg set scripts.start="npx --yes serve --listen 5500 ."
```

Resultado esperado em `package.json`:

```json
{
  "name": "linktree-grupo-player",
  "private": true,
  "scripts": {
    "config": "node scripts/generate-config.js",
    "prestart": "npm run config",
    "start": "npx --yes serve --listen 5500 ."
  }
}
```

- [ ] **Step 7: Verificar que `prestart` agora dispara**

```bash
npm start
```

Esperado: a linha `config.js gerado: { ENV: 'development', ... }` aparece **antes** do servidor subir em `http://localhost:5500`. Encerre com Ctrl+C.

- [ ] **Step 8: Commit**

```bash
git add .gitattributes package.json
git commit -m "chore: pin config.js to LF and wire up npm start

scripts/generate-config.js writes LF, but core.autocrlf=true expects CRLF
in the working tree, so every `npm run config` on Windows marked the
generated file as modified with byte-identical content. A .gitattributes
rule settles it.

The prestart hook had no start script to precede, so it never ran."
```

---

### Task 2: Verificador de contraste

O arnês de teste do plano. Todo token de cor passa por aqui. Ele lê os hex direto do CSS — não de um manifesto paralelo — para que a paleta não possa divergir do que é verificado.

**Files:**
- Create: `scripts/check-contrast.js`
- Test: o próprio script, rodado contra um par deliberadamente reprovado

**Interfaces:**
- Consumes: nada ainda. A partir da Task 4 lê `companies/player/css/brand.css`.
- Produces: `node scripts/check-contrast.js [caminho-do-css]` — sai com código **0** se todos os pares passarem AA, **1** se algum reprovar. Imprime uma tabela com razão e veredito por par.

- [ ] **Step 1: Escrever o script**

```javascript
#!/usr/bin/env node
/**
 * Confere contraste WCAG dos tokens semânticos de cor.
 *
 * Lê os hex literais declarados em cada bloco de tema do CSS informado e
 * confere os pares (frente, fundo) que a página realmente usa. Os tokens
 * precisam ser hex literal — rgba() e color-mix() não são verificáveis aqui,
 * e é por isso que a spec exige hex composto para variantes com alfa.
 *
 * Uso: node scripts/check-contrast.js [caminho.css]
 * Sai 1 se qualquer par reprovar no alvo.
 */
const fs = require("fs");
const path = require("path");

const AA_NORMAL = 4.5;
const AA_LARGE = 3.0;

/** Pares (frente, fundo, alvo) conferidos em todos os temas. */
const PAIRS = [
  ["--text", "--surface", AA_NORMAL],
  ["--text-muted", "--surface", AA_NORMAL],
  ["--text", "--surface-raised", AA_NORMAL],
  ["--text-muted", "--surface-raised", AA_NORMAL],
  ["--accent-text", "--surface", AA_NORMAL],
  ["--on-accent", "--accent-surface", AA_NORMAL],
  ["--rule-strong", "--surface", AA_LARGE],
];

function channel(c) {
  const s = c / 255;
  return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
}

function luminance([r, g, b]) {
  return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
}

function parseHex(value) {
  let h = value.replace("#", "").trim();
  if (h.length === 3) h = h.split("").map((c) => c + c).join("");
  if (!/^[0-9a-fA-F]{6}$/.test(h)) return null;
  return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
}

function contrast(fg, bg) {
  const a = luminance(fg);
  const b = luminance(bg);
  const [hi, lo] = a > b ? [a, b] : [b, a];
  return (hi + 0.05) / (lo + 0.05);
}

/**
 * Extrai { nomeDoTema: { "--token": "#hex" } } do CSS.
 * `:root` vira o tema "dark" (canônico); [data-theme="x"] vira o tema "x".
 */
function parseThemes(css) {
  const themes = {};
  const blockRe = /(:root|\[data-theme=["']([a-z-]+)["']\])\s*\{([^}]*)\}/g;
  let block;
  while ((block = blockRe.exec(css)) !== null) {
    const name = block[2] || "dark";
    const body = block[3];
    themes[name] = themes[name] || {};
    const declRe = /(--[a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{3,8})\s*;/g;
    let decl;
    while ((decl = declRe.exec(body)) !== null) {
      themes[name][decl[1]] = decl[2];
    }
  }
  return themes;
}

function main() {
  const target = process.argv[2] ||
    path.resolve(__dirname, "..", "companies", "player", "css", "brand.css");

  if (!fs.existsSync(target)) {
    console.error("arquivo nao encontrado:", target);
    process.exit(1);
  }

  const themes = parseThemes(fs.readFileSync(target, "utf8"));
  const names = Object.keys(themes);

  if (names.length === 0) {
    console.error("nenhum bloco de tema encontrado em", target);
    process.exit(1);
  }

  let failed = 0;

  for (const name of names) {
    console.log("\n--- tema: " + name + " ---");
    for (const [fgName, bgName, target_] of PAIRS) {
      const fgRaw = themes[name][fgName];
      const bgRaw = themes[name][bgName];

      if (!fgRaw || !bgRaw) {
        console.log(
          (fgName + " sobre " + bgName).padEnd(42) +
            "     -   AUSENTE (" + (fgRaw ? bgName : fgName) + ")"
        );
        failed++;
        continue;
      }

      const fg = parseHex(fgRaw);
      const bg = parseHex(bgRaw);

      if (!fg || !bg) {
        console.log(
          (fgName + " sobre " + bgName).padEnd(42) + "     -   NAO-HEX"
        );
        failed++;
        continue;
      }

      const ratio = contrast(fg, bg);
      const ok = ratio >= target_;
      if (!ok) failed++;
      console.log(
        (fgName + " sobre " + bgName).padEnd(42) +
          ratio.toFixed(2).padStart(6) +
          "   " +
          (ok ? "OK" : "FALHA (alvo " + target_ + ")")
      );
    }
  }

  console.log("");
  if (failed > 0) {
    console.error(failed + " par(es) reprovado(s).");
    process.exit(1);
  }
  console.log("todos os pares passaram.");
}

main();
```

- [ ] **Step 2: Provar que o script detecta reprovação**

Crie um arquivo temporário fora do projeto com o par que a spec identificou como o pior caso — o âmbar da marca sobre o fundo osso:

```bash
mkdir -p /tmp/contrast-probe && cat > /tmp/contrast-probe/fail.css <<'CSS'
:root {
  --surface: #F7F3EC;
  --surface-raised: #FFFFFF;
  --text: #0E1C2C;
  --text-muted: #4A5765;
  --accent-text: #FFAA00;
  --accent-surface: #FFAA00;
  --on-accent: #131007;
  --rule-strong: #0E1C2C;
}
CSS
node scripts/check-contrast.js /tmp/contrast-probe/fail.css
echo "exit: $?"
```

Esperado: a linha `--accent-text sobre --surface` mostra **1.73 FALHA (alvo 4.5)** e `exit: 1`.

Isso é o teste falhando primeiro. Se sair `exit: 0`, o script está quebrado — conserte antes de seguir.

- [ ] **Step 3: Provar que o script aprova uma paleta válida**

```bash
sed 's/--accent-text: #FFAA00/--accent-text: #8A4B02/' /tmp/contrast-probe/fail.css > /tmp/contrast-probe/pass.css
node scripts/check-contrast.js /tmp/contrast-probe/pass.css
echo "exit: $?"
```

Esperado: `--accent-text sobre --surface` mostra **6.15 OK** e `exit: 0`.

- [ ] **Step 4: Limpar a sonda**

```bash
rm -rf /tmp/contrast-probe
```

- [ ] **Step 5: Commit**

```bash
git add scripts/check-contrast.js
git commit -m "test(tokens): add a WCAG contrast checker for semantic colour tokens

Reads the literal hex declared in each theme block of a stylesheet and
checks the pairs the page actually renders, so the palette cannot drift
from what is verified. Exits non-zero on any pair below its target."
```

---

### Task 3: Camadas de cascata e tokens primitivos

Primitivos não conhecem marca. Nenhum valor aqui é âmbar, navy ou creme — são escalas, curvas e medidas que qualquer empresa do Grupo herda.

**Files:**
- Create: `shared/css/layers.css`
- Create: `shared/css/tokens.css`
- Create: `shared/css/base.css`
- Modify: `companies/player/index.html` (tags `<link>`)

**Interfaces:**
- Consumes: nada.
- Produces: as camadas `reset, tokens, base, components, motion, utilities` nessa ordem de precedência, e os primitivos abaixo, disponíveis para todas as empresas.

- [ ] **Step 1: Criar `shared/css/layers.css`**

```css
/* Ordem de precedência da cascata para todas as páginas do Grupo.
   Precisa ser a PRIMEIRA tag <link> do documento: folhas são aplicadas em
   ordem de documento, e é essa posição que garante a declaração antes de
   qualquer uso. Com a ordem fixada aqui, a ordem das demais folhas deixa de
   importar para a precedência. */
@layer reset, tokens, base, components, motion, utilities;
```

- [ ] **Step 2: Criar `shared/css/tokens.css`**

```css
/* ==========================================================================
   Primitivos do Grupo Player
   Escalas, medidas e curvas. Nenhum valor de marca — cor de marca vive no
   brand.css de cada empresa. Nada aqui deve precisar mudar para uma empresa
   nova; se precisar, é semântico e está no lugar errado.
   ========================================================================== */

@layer tokens {
  :root {
    /* Escala tipográfica — fluida, base 16px.
       Os degraus de display usam clamp para respirar entre 360px e 1200px. */
    --text-2xs: 0.6875rem;   /* 11px — rótulos, legendas */
    --text-xs: 0.75rem;      /* 12px */
    --text-sm: 0.8125rem;    /* 13px — meta dos links */
    --text-base: 1rem;       /* 16px — corpo */
    --text-md: clamp(1.0625rem, 0.98rem + 0.4vw, 1.1875rem);
    --text-lg: clamp(1.25rem, 1.1rem + 0.7vw, 1.5rem);
    --text-xl: clamp(1.5rem, 1.25rem + 1.2vw, 2rem);
    --text-2xl: clamp(1.875rem, 1.4rem + 2.1vw, 2.75rem);
    --text-3xl: clamp(2.25rem, 1.5rem + 3.2vw, 3.75rem);

    /* Peso e tracking — tracking negativo cresce com o tamanho */
    --weight-normal: 400;
    --weight-book: 450;
    --weight-medium: 500;
    --weight-semibold: 600;
    --weight-bold: 700;
    --track-tight: -0.022em;
    --track-snug: -0.012em;
    --track-normal: 0em;
    --track-wide: 0.08em;
    --track-caps: 0.16em;

    /* Altura de linha */
    --leading-none: 1;
    --leading-tight: 1.12;
    --leading-snug: 1.28;
    --leading-normal: 1.5;
    --leading-relaxed: 1.65;

    /* Espaço — base 4px */
    --space-1: 0.25rem;
    --space-2: 0.5rem;
    --space-3: 0.75rem;
    --space-4: 1rem;
    --space-5: 1.25rem;
    --space-6: 1.5rem;
    --space-8: 2rem;
    --space-10: 2.5rem;
    --space-12: 3rem;
    --space-16: 4rem;
    --space-20: 5rem;
    --space-24: 6rem;
    --space-32: 8rem;

    /* Medidas */
    --measure-shell: 30rem;      /* largura da coluna de conteúdo */
    --measure-prose: 34ch;       /* largura confortável de leitura */
    --tap-min: 2.75rem;          /* 44px — alvo mínimo de toque */

    /* Raios */
    --radius-sm: 0.5rem;
    --radius-md: 0.75rem;
    --radius-lg: 1.125rem;
    --radius-pill: 999px;

    /* Movimento — poucas durações, poucas curvas, usadas com disciplina */
    --dur-instant: 120ms;
    --dur-fast: 200ms;
    --dur-base: 380ms;
    --dur-slow: 640ms;
    --dur-ambient: 20s;

    /* ease-exit: saída rápida, chegada macia — entradas e quedas.
       ease-soft: simétrica — hover e estados ociosos. */
    --ease-exit: cubic-bezier(0.22, 1, 0.36, 1);
    --ease-soft: cubic-bezier(0.4, 0, 0.2, 1);

    /* Escalonamento da cascata de entrada: índice --i inline por elemento */
    --stagger-step: 55ms;
    --stagger-base: 140ms;

    /* Camadas de profundidade */
    --z-backdrop: 0;
    --z-content: 1;
    --z-sticky: 2;
    --z-overlay: 10;
  }
}
```

- [ ] **Step 3: Criar `shared/css/base.css`**

O reset e as regras de documento que hoje moram no topo de `styles.css`. Saem de lá porque não são da Player — são de qualquer página do Grupo.

```css
/* ==========================================================================
   Base do Grupo Player — reset e regras de documento.
   Nada aqui é específico de empresa; cor vem de token semântico.
   ========================================================================== */

@layer reset {
  *,
  *::before,
  *::after {
    box-sizing: border-box;
  }

  body {
    margin: 0;
  }

  /* Só desliga a rolagem suave para quem não pediu redução de movimento. */
  @media (prefers-reduced-motion: no-preference) {
    html {
      scroll-behavior: smooth;
    }
  }
}

@layer base {
  body {
    min-height: 100dvh;
    display: flex;
    flex-direction: column;
    font-family: var(--font-sans);
    font-size: var(--text-base);
    line-height: var(--leading-normal);
    color: var(--text);
    background: var(--surface);
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
    transition:
      background-color var(--dur-base) var(--ease-soft),
      color var(--dur-base) var(--ease-soft);
  }

  /* A troca de tema não deve animar no primeiro paint. */
  @media (prefers-reduced-motion: reduce) {
    body {
      transition: none;
    }
  }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    margin: -1px;
    padding: 0;
    overflow: hidden;
    clip-path: inset(50%);
    white-space: nowrap;
  }
}
```

`--font-sans` só existe a partir da Task 7; até lá a família cai no fallback do sistema, o que é aceitável e visível.

- [ ] **Step 4: Ligar as folhas no HTML**

Em `companies/player/index.html`, substitua a linha única de stylesheet pelas cinco folhas, **nesta ordem**:

```html
<link rel="stylesheet" href="../../shared/css/layers.css" />
<link rel="stylesheet" href="../../shared/css/tokens.css" />
<link rel="stylesheet" href="../../shared/css/base.css" />
<link rel="stylesheet" href="css/brand.css" />
<link rel="stylesheet" href="css/styles.css" />
```

E remova de `styles.css` o bloco de reset e as regras de `body` que acabaram de migrar — deixar as duas cópias é a receita para elas divergirem.

`brand.css` ainda não existe — será criado na Task 4. O `<link>` para um arquivo ausente devolve 404 e é ignorado sem quebrar a página; a ordem já fica correta.

- [ ] **Step 5: Verificar a ordem de camadas no browser**

Suba o servidor (`npm start`) e confira que a declaração foi aceita:

```javascript
// no console da página, ou via preview tools
({ token: getComputedStyle(document.documentElement).getPropertyValue('--space-4'),
   reset: getComputedStyle(document.body).boxSizing })
```

Esperado: `{ token: " 1rem", reset: "border-box" }`. Token vazio significa que `tokens.css` não carregou — confira o caminho relativo `../../shared/css/`.

- [ ] **Step 6: Commit**

```bash
git add shared/css/layers.css shared/css/tokens.css shared/css/base.css companies/player/index.html companies/player/css/styles.css
git commit -m "feat(ds): add Group-level cascade layers, primitives and base

The reset and document rules move out of the Player's stylesheet: they were
never company-specific. Layer order is declared up front in its own sheet so
the loading order of the rest stops mattering.

Primitives carry no brand meaning either: scales, measures and motion curves
that any company in the Group inherits."
```

---

### Task 4: Tokens semânticos e os dois temas

O momento em que o verificador da Task 2 ganha o emprego. A paleta clara **vai reprovar** na primeira rodada — isso é esperado e é o ponto.

**Files:**
- Create: `companies/player/css/brand.css`

**Interfaces:**
- Consumes: primitivos de `shared/css/tokens.css`.
- Produces: os tokens semânticos abaixo, em dois temas. Componentes consomem **apenas** estes, nunca um primitivo de cor nem um hex solto.

Tokens produzidos: `--surface`, `--surface-raised`, `--surface-sunken`, `--text`, `--text-muted`, `--text-faint`, `--rule`, `--rule-strong`, `--accent-surface`, `--accent-text`, `--on-accent`, `--focus`, `--brand-whatsapp`, `--brand-youtube`, `--brand-spotify`.

- [ ] **Step 1: Escrever `brand.css` com o tema escuro e uma primeira tentativa do claro**

Escreva o âmbar da marca como `--accent-text` no tema claro **de propósito**. É a hipótese que o verificador vai derrubar.

```css
/* ==========================================================================
   Player Contabilidade — tokens semânticos
   Papéis, não cores. Componentes consomem daqui e nunca de um hex solto.
   Todo valor é hex literal para ser verificável por scripts/check-contrast.js;
   variantes com alfa entram já compostas sobre a superfície do tema.
   ========================================================================== */

@layer tokens {
  /* Tema escuro — canônico. A marca foi desenhada para ser vista assim. */
  :root {
    --surface: #060812;
    --surface-raised: #0f1428;
    --surface-sunken: #04050c;

    --text: #ffdbbf;
    --text-muted: #b39a83;   /* creme a 66% composto sobre --surface */
    --text-faint: #7a6a5c;   /* decorativo — nunca texto de conteúdo */

    --rule: #1c2033;
    --rule-strong: #2e3348;

    --accent-surface: #ffaa00;
    --accent-text: #ffaa00;
    --on-accent: #131007;

    --focus: #ffaa00;

    --brand-whatsapp: #25d366;
    --brand-youtube: #ff0000;
    --brand-spotify: #1db954;

    color-scheme: dark;
  }

  /* Tema claro — institucional. Mesma estrutura, outra paleta. */
  [data-theme="light"] {
    --surface: #f7f3ec;
    --surface-raised: #ffffff;
    --surface-sunken: #efe9df;

    --text: #0e1c2c;
    --text-muted: #4a5765;
    --text-faint: #8b95a1;

    --rule: #e0d8cb;
    --rule-strong: #0e1c2c;

    --accent-surface: #ffaa00;
    --accent-text: #ffaa00;
    --on-accent: #131007;

    --focus: #8a4b02;

    --brand-whatsapp: #128c4a;
    --brand-youtube: #cc0000;
    --brand-spotify: #17a64b;

    color-scheme: light;
  }
}
```

- [ ] **Step 2: Rodar o verificador e ver a reprovação**

```bash
node scripts/check-contrast.js
echo "exit: $?"
```

Esperado: o tema `dark` passa inteiro. O tema `light` mostra:

```
--accent-text sobre --surface                 1.73   FALHA (alvo 4.5)
```

e `exit: 1`.

Isso confirma o achado da spec: o âmbar da marca é inutilizável como cor de texto sobre fundo claro.

- [ ] **Step 3: Corrigir separando o papel de superfície do papel de texto**

Em `[data-theme="light"]`, troque só a linha do `--accent-text`:

```css
    --accent-surface: #ffaa00;
    --accent-text: #8a4b02;   /* 6,15:1 sobre --surface — o piso do projeto */
    --on-accent: #131007;
```

O âmbar continua sendo a cor da marca nas **superfícies** (o CTA preenchido, o fio de acento). Só o âmbar usado como **texto** vira a versão profunda.

- [ ] **Step 4: Verificar que passou**

```bash
node scripts/check-contrast.js
echo "exit: $?"
```

Esperado: todos os pares OK nos dois temas, `exit: 0`. Confira especificamente:

| Par | Escuro | Claro |
|---|---|---|
| `--text` sobre `--surface` | 15.35 | 15.55 |
| `--text-muted` sobre `--surface` | ~6.7 | ~6.5 |
| `--accent-text` sobre `--surface` | 10.47 | **6.15** |
| `--on-accent` sobre `--accent-surface` | 9.96 | 9.96 |

- [ ] **Step 5: Commit**

```bash
git add companies/player/css/brand.css
git commit -m "feat(player): add semantic colour tokens for both themes

Splits --accent-surface from --accent-text because the brand amber scores
1.73:1 as text on the light bone background and fails AA outright. Amber
stays the brand colour on surfaces; amber used as text becomes a deep
variant at 6.15:1, matching the floor the project already documents."
```

---

### Task 5: Toggle de tema e supressão do flash

**Files:**
- Create: `shared/js/theme.js`
- Modify: `companies/player/index.html` (script inline no `<head>`, botão de toggle)
- Modify: `companies/player/css/styles.css` (estilo do botão)

**Interfaces:**
- Consumes: `--surface`, `--text`, `--rule`, `--focus`, `--tap-min`.
- Produces: `window.__setTheme(name)` disponível a partir do `<head>`; atributo `data-theme` em `<html>`; chave `player-theme` em `localStorage` com valor `"dark"` ou `"light"`.

- [ ] **Step 1: Script inline anti-flash, como primeiro elemento do `<head>`**

Precisa vir **antes de qualquer `<link rel="stylesheet">`** e ser síncrono. Um `<script src>` aqui, mesmo local, permitiria uma pintura com o tema errado.

```html
<script>
  // Aplica o tema antes da primeira pintura. Sem isto, o browser pinta o
  // tema padrão e troca — o flash que o commit 91fd22a já corrigiu nos
  // redirects. Mantenha inline e síncrono.
  (function () {
    var KEY = "player-theme";
    window.__setTheme = function (name) {
      var t = name === "light" || name === "dark" ? name : null;
      if (t) {
        document.documentElement.setAttribute("data-theme", t);
        try { localStorage.setItem(KEY, t); } catch (e) {}
      }
      return t;
    };
    try {
      var saved = localStorage.getItem(KEY);
      if (saved === "light" || saved === "dark") {
        document.documentElement.setAttribute("data-theme", saved);
      }
    } catch (e) {}
    // Sem valor salvo, nenhum atributo é escrito e prefers-color-scheme decide.
  })();
</script>
```

- [ ] **Step 2: Fazer o tema escuro ser o padrão do sistema no CSS**

Em `brand.css`, o bloco `:root` já é o escuro. Adicione, no mesmo `@layer tokens`, a regra que faz o sistema claro valer quando o usuário não escolheu nada:

```css
  @media (prefers-color-scheme: light) {
    :root:not([data-theme="dark"]) {
      --surface: #f7f3ec;
      --surface-raised: #ffffff;
      --surface-sunken: #efe9df;
      --text: #0e1c2c;
      --text-muted: #4a5765;
      --text-faint: #8b95a1;
      --rule: #e0d8cb;
      --rule-strong: #0e1c2c;
      --accent-surface: #ffaa00;
      --accent-text: #8a4b02;
      --on-accent: #131007;
      --focus: #8a4b02;
      --brand-whatsapp: #128c4a;
      --brand-youtube: #cc0000;
      --brand-spotify: #17a64b;
      color-scheme: light;
    }
  }
```

Sim, os valores repetem o bloco `[data-theme="light"]`. É intencional: o verificador da Task 2 lê blocos por seletor, e um `@media` aninhado com os mesmos valores mantém a paleta clara conferível em ambos os caminhos. Se preferir DRY aqui, extraia para uma custom property de grupo — mas só depois que o verificador souber resolver indireção.

- [ ] **Step 3: Botão de toggle no HTML**

Dentro de `.shell`, antes de `<header class="brand">`:

```html
<button
  class="theme-toggle"
  type="button"
  data-theme-toggle
  aria-label="Alternar entre tema claro e escuro"
>
  <svg class="theme-toggle__icon" aria-hidden="true" focusable="false">
    <use href="#i-theme" />
  </svg>
</button>
```

E o símbolo no sprite, junto dos demais:

```html
<symbol id="i-theme" viewBox="0 0 24 24">
  <path
    fill="currentColor"
    d="M12 2a10 10 0 1 0 0 20zm0 1.7v16.6a8.3 8.3 0 0 1 0-16.6"
  />
</symbol>
```

- [ ] **Step 4: Criar `shared/js/theme.js`**

```javascript
(function () {
  var KEY = "player-theme";

  function current() {
    var attr = document.documentElement.getAttribute("data-theme");
    if (attr === "light" || attr === "dark") return attr;
    return window.matchMedia("(prefers-color-scheme: light)").matches
      ? "light"
      : "dark";
  }

  function sync(button) {
    button.setAttribute("aria-pressed", current() === "light" ? "true" : "false");
  }

  var button = document.querySelector("[data-theme-toggle]");
  if (!button) return;

  sync(button);

  button.addEventListener("click", function () {
    window.__setTheme(current() === "light" ? "dark" : "light");
    sync(button);
  });

  // Segue o sistema enquanto o usuário não tiver escolhido explicitamente.
  var query = window.matchMedia("(prefers-color-scheme: light)");
  var onChange = function () {
    var saved = null;
    try { saved = localStorage.getItem(KEY); } catch (e) {}
    if (!saved) sync(button);
  };
  if (query.addEventListener) query.addEventListener("change", onChange);
})();
```

Ligue no fim do `<body>`, antes de `js/main.js`:

```html
<script src="../../shared/js/theme.js"></script>
```

- [ ] **Step 5: Estilo do botão**

Em `styles.css`, dentro de `@layer components`:

```css
.theme-toggle {
  justify-self: end;
  display: grid;
  place-items: center;
  width: var(--tap-min);
  height: var(--tap-min);
  border-radius: var(--radius-pill);
  border: 1px solid var(--rule);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition:
    color var(--dur-fast) var(--ease-soft),
    border-color var(--dur-fast) var(--ease-soft);
}

.theme-toggle:hover {
  color: var(--text);
  border-color: var(--rule-strong);
}

.theme-toggle:focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: 3px;
}

.theme-toggle__icon {
  width: 1.1rem;
  height: 1.1rem;
  transition: transform var(--dur-base) var(--ease-exit);
}

[data-theme="light"] .theme-toggle__icon {
  transform: rotate(180deg);
}
```

- [ ] **Step 6: Verificar — sem flash, persistente, respeita o sistema**

Com o servidor no ar, confira as quatro condições:

```javascript
// 1. Alterna e persiste
document.querySelector('[data-theme-toggle]').click();
({ tema: document.documentElement.dataset.theme,
   salvo: localStorage.getItem('player-theme') })
// Esperado: { tema: 'light', salvo: 'light' }
```

Depois recarregue a página e confirme que abre em claro **sem piscar escuro**. Grave a verificação com um reload e uma captura imediata; se houver flash, o script inline não está antes dos `<link>`.

```javascript
// 2. Limpar a escolha devolve o controle ao sistema
localStorage.removeItem('player-theme');
document.documentElement.removeAttribute('data-theme');
getComputedStyle(document.documentElement).colorScheme
// Esperado: acompanha o prefers-color-scheme do SO
```

Teste também com `resize_window` e `colorScheme: 'light'` / `'dark'` emulados.

- [ ] **Step 7: Commit**

```bash
git add shared/js/theme.js companies/player/index.html companies/player/css/brand.css companies/player/css/styles.css
git commit -m "feat(player): add theme toggle with pre-paint application

The theme is applied by an inline synchronous script before any stylesheet
link, so the page never paints the wrong theme and swaps. Without an
explicit choice stored, prefers-color-scheme decides."
```

---

### Task 6: Redesign editorial do hero

A direção A: premium por contenção. Os cards de vidro saem, a lista vira linhas separadas por fio, o âmbar aparece **uma vez** — no CTA comercial.

**Files:**
- Modify: `companies/player/css/styles.css` (reescrita substancial)
- Modify: `companies/player/index.html` (estrutura dos links)

**Interfaces:**
- Consumes: todos os tokens semânticos da Task 4, primitivos da Task 3.
- Produces: as classes `.shell`, `.brand`, `.brand__logo`, `.brand__eyebrow`, `.links`, `.link`, `.link--cta`, `.link__label`, `.link__meta`, `.link__arrow`, `.links__social`, `.backdrop`, `.grain`. A Task 9 anexa movimento a `.link` e `.brand`, e **anima `.backdrop::after`** — esse seletor precisa sobreviver a esta task.

- [ ] **Step 0: Apagar a camada de tokens legada e destravar o tema**

Verificado em browser durante a Task 5: o sistema de temas funciona no nível de token
(`--surface` troca, `color-scheme` troca, o `body` repinta), **mas nada disso aparece** porque
`styles.css` ainda carrega o design antigo por cima.

Duas causas, ambas nesta folha:

1. Um bloco `:root` próprio declarando `--ink`, `--navy-950`, `--navy-900`, `--navy-500`,
   `--amber*`, `--cream*`, `--glass*`, `--hairline`, `--font`, `--r-*`, `--shell`, `--ease*`.
   São cegos a tema e sombreiam a camada semântica. **Apague o bloco inteiro.** Onde uma
   regra que você mantém usava um deles, troque pelo token semântico ou primitivo
   equivalente (`--ink` → `--surface`, `--cream` → `--text`, `--hairline` → `--rule`,
   `--shell` → `--measure-shell`, `--ease` → `--ease-exit`, `--r-card` → `--radius-lg`).
2. `.backdrop` é `position: fixed; inset: 0; z-index: 0` pintando um gradiente navy fixo —
   ele cobre o viewport inteiro e é o motivo real de o tema claro não aparecer.
   **Reescreva-o em tokens semânticos**, de forma que siga o tema. Mantenha o
   `.backdrop::after` como elemento: a Task 9 o usa como alvo do parallax.

`.grain` é textura de vocabulário da direção C. Se mantiver, torne-o consciente de tema
(no fundo claro um grain quente em `soft-light` some ou suja); se remover, tire também a
`<div class="grain">` do HTML. Decisão de design desta task — mas não deixe um terceiro
lugar declarando cor fora do sistema.

**Verificação deste passo:** com `data-theme="light"` aplicado, uma captura da página deve
mostrar fundo claro de verdade, não navy. É o teste que a Task 5 não conseguiu passar.

- [ ] **Step 1: Reestruturar a marcação dos links**

O CTA comercial deixa de ser um card entre iguais e vira elemento próprio:

```html
<a class="link link--cta" data-brand="whatsapp" href="https://api.whatsapp.com/send?phone=5511994453204" target="_blank" rel="noopener noreferrer">
  <span class="link__label">Falar com o comercial</span>
  <svg class="link__arrow" aria-hidden="true"><use href="#i-arrow" /></svg>
</a>
```

Os demais viram linhas, sem badge de vidro e sem ícone de plataforma no corpo — o ícone só permanece onde carrega reconhecimento de marca (YouTube, Spotify, no bloco social):

```html
<a class="link" style="--i: 1" data-brand="vagas" href="https://vagas.playercontabilidade.com" target="_blank" rel="noopener noreferrer">
  <span>
    <span class="link__label">Vagas de emprego em aberto</span>
    <span class="link__meta">Trabalhe no Grupo Player</span>
  </span>
  <svg class="link__arrow" aria-hidden="true"><use href="#i-arrow" /></svg>
</a>
```

Mantenha `--i` sequencial e `data-brand` — a spec exige que cor de plataforma venha do atributo, não da posição.

- [ ] **Step 2: Escrever o CSS do hero**

Valores concretos, dentro de `@layer components`:

- `.shell` — `width: min(100% - var(--space-8), var(--measure-shell))`, `margin-inline: auto`, `padding-block: clamp(var(--space-8), 7vh, var(--space-16))`, `display: grid`, `gap: var(--space-10)`.
- `.brand` — grid centrado, `gap: var(--space-6)`.
- `.brand__logo` — `width: min(70%, 224px)` (260px acima de 768px). **Remova os dois `drop-shadow`** do CSS atual: halo âmbar é vocabulário da direção C, não da A.
- `.brand__eyebrow` — Fraunces italic, `font-size: var(--text-2xl)`, `letter-spacing: var(--track-tight)`, `line-height: var(--leading-tight)`, `text-wrap: balance`, `max-width: 18ch`. **Cor sólida `var(--text)`, sem gradiente e sem `shimmer`.** Na direção A a assinatura é forte pela forma, não pelo brilho; o âmbar fica reservado ao CTA.
- `.link--cta` — `background: var(--accent-surface)`, `color: var(--on-accent)`, `border-radius: var(--radius-sm)`, `padding: var(--space-4) var(--space-5)`, `font-weight: var(--weight-semibold)`, `min-height: var(--tap-min)`, `display: flex`, `justify-content: space-between`, `align-items: center`.
- `.link` (linha) — `display: grid`, `grid-template-columns: 1fr auto`, `align-items: center`, `gap: var(--space-4)`, `padding-block: var(--space-4)`, `min-height: var(--tap-min)`, `border-bottom: 1px solid var(--rule)`, `color: var(--text)`, `text-decoration: none`. **Sem `background`, sem `border-radius`, sem `backdrop-filter`, sem `box-shadow`.**
- `.links` — `border-top: 1px solid var(--rule)` para fechar a lista em cima; o último `.link` perde o `border-bottom`.
- `.link__label` — `font-size: var(--text-md)`, `font-weight: var(--weight-medium)`, `letter-spacing: var(--track-snug)`.
- `.link__meta` — `font-size: var(--text-sm)`, `color: var(--text-muted)`, `margin-top: var(--space-1)`.
- `.link__arrow` — `width: 0.9rem`, `color: var(--text-faint)`.
- `.links__social` — duas colunas, `gap: var(--space-3)`, itens com `border: 1px solid var(--rule)` e `border-radius: var(--radius-sm)`.

- [ ] **Step 3: Hover premium — o efeito principal da lista**

Em `@layer components`, sob `@media (hover: hover)`. O gesto é **deslocamento e revelação**, não elevação:

```css
@media (hover: hover) {
  .link {
    /* O fio inferior vira a superfície animada: cresce da esquerda no hover */
    background-image: linear-gradient(var(--accent-surface), var(--accent-surface));
    background-repeat: no-repeat;
    background-position: 0 100%;
    background-size: 0% 1px;
    transition:
      background-size var(--dur-base) var(--ease-exit),
      padding-inline-start var(--dur-base) var(--ease-exit);
  }

  .link:hover {
    background-size: 100% 1px;
    padding-inline-start: var(--space-3);
  }

  .link:hover .link__label { color: var(--accent-text); }
  .link:hover .link__arrow {
    color: var(--accent-text);
    transform: translateX(var(--space-2));
  }

  .link--cta {
    transition:
      filter var(--dur-fast) var(--ease-soft),
      transform var(--dur-fast) var(--ease-soft);
  }
  .link--cta:hover { filter: brightness(1.06); transform: translateY(-1px); }
}
```

O fio âmbar que corre por baixo é o único momento de cor da lista, e ele é **temporário** — some quando o ponteiro sai. Coerente com "o âmbar aparece uma vez".

- [ ] **Step 4: Foco visível e estado ativo**

```css
.link:focus-visible,
.link--cta:focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: 3px;
  border-radius: var(--radius-sm);
}

.link:active { transform: translateY(0) scale(0.995); }
```

- [ ] **Step 5: Verificar contraste, alvo de toque e os dois temas**

```bash
node scripts/check-contrast.js
```

No browser, com o servidor no ar:

```javascript
// Nenhum alvo de toque abaixo de 44px
[...document.querySelectorAll('.link, .link--cta, .theme-toggle')]
  .map(el => ({ el: el.className, h: Math.round(el.getBoundingClientRect().height) }))
  .filter(x => x.h < 44)
// Esperado: []
```

Capture o hero nos dois temas em 375×812 e confirme: um único elemento âmbar preenchido, nenhum card de vidro, fios visíveis nos dois temas.

- [ ] **Step 6: Commit**

```bash
git add companies/player/index.html companies/player/css/styles.css
git commit -m "feat(player): restyle the hero as an editorial list

Glass cards give way to hairline rows, the signature drops its gradient
shimmer for a solid weight, and amber is spent once — on the commercial
CTA. Hover reveals an amber rule running under the row rather than
lifting a card, so colour stays temporary."
```

---

### Task 7: Fontes self-hosted

Tira o Google Fonts da cadeia crítica: dois `preconnect`, duas viagens de rede e um terceiro a menos, além de melhor postura de LGPD.

**Files:**
- Create: `scripts/build-fonts.py`
- Create: `companies/player/assets/fonts/*.woff2`
- Modify: `companies/player/index.html` (remove Google Fonts, adiciona `preload`)
- Modify: `companies/player/css/styles.css` (blocos `@font-face`)

**Interfaces:**
- Consumes: nada do projeto.
- Produces: as famílias `Inter` (400, 500, 600) e `Fraunces` (italic 500) disponíveis localmente, e o token `--font-sans` / `--font-serif` em `brand.css`.

- [ ] **Step 1: Escrever `scripts/build-fonts.py`**

Segue o precedente de `build-brand-assets.py`: ferramenta de desenvolvimento, rodada sob demanda, fora do build do site.

```python
#!/usr/bin/env python3
"""
Subseta Inter e Fraunces para o repertório que a página realmente usa.

Ferramenta de desenvolvimento — NÃO faz parte do build do site. Rode só
quando as fontes de origem ou o conteúdo mudarem.

    pip install fonttools brotli
    python scripts/build-fonts.py

Baixe os TTF de origem antes:
    https://github.com/rsms/inter/releases        -> Inter[opsz,wght].ttf
    https://github.com/googlefonts/fraunces       -> Fraunces-Italic[SOFT,WONK,opsz,wght].ttf
e coloque em scripts/fonts-src/.
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "scripts" / "fonts-src"
OUT = ROOT / "companies" / "player" / "assets" / "fonts"

# latin + latin-ext cobre pt-BR (ç, ã, õ, á, é, í, ó, ú, â, ê, ô)
UNICODES = "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"

# (arquivo de origem, saída, eixos fixados na instância estática)
JOBS = [
    ("Inter[opsz,wght].ttf", "inter-400.woff2", "wght=400"),
    ("Inter[opsz,wght].ttf", "inter-500.woff2", "wght=500"),
    ("Inter[opsz,wght].ttf", "inter-600.woff2", "wght=600"),
    ("Fraunces-Italic[SOFT,WONK,opsz,wght].ttf", "fraunces-italic-500.woff2", "wght=500"),
]


def main():
    if not SRC.is_dir():
        sys.exit(f"coloque os TTF de origem em {SRC}")
    OUT.mkdir(parents=True, exist_ok=True)

    tmp = ROOT / "scripts" / ".fonts-tmp"
    tmp.mkdir(exist_ok=True)

    for src_name, out_name, axes in JOBS:
        src = SRC / src_name
        if not src.is_file():
            sys.exit(f"fonte de origem ausente: {src}")

        # 1. Fixar os eixos variáveis, gerando um estático.
        static = tmp / (out_name.replace(".woff2", ".ttf"))
        subprocess.run(
            [sys.executable, "-m", "fontTools.varLib.instancer",
             str(src), axes, "-o", str(static)],
            check=True,
        )

        # 2. Subsetar o estático e converter para woff2.
        subprocess.run(
            [sys.executable, "-m", "fontTools.subset", str(static),
             f"--unicodes={UNICODES}",
             "--layout-features=kern,liga,calt,tnum",
             "--flavor=woff2",
             "--no-hinting",
             "--desubroutinize",
             f"--output-file={OUT / out_name}"],
            check=True,
        )

        size = (OUT / out_name).stat().st_size
        print(f"  {out_name}: {size / 1024:.1f} KB")
        static.unlink()

    tmp.rmdir()
    print("pronto.")


if __name__ == "__main__":
    main()
```

Os dois passos são separados de propósito: `fontTools.subset` sozinho não fixa eixo de fonte variável, e a flag para isso mudou entre versões. Instanciar antes com `varLib.instancer` funciona em qualquer versão recente e deixa explícito o que está acontecendo.

Adicione `scripts/.fonts-tmp/` e `scripts/fonts-src/` ao `.gitignore` — os TTF de origem pesam megabytes e não pertencem ao repositório.

- [ ] **Step 2: Rodar e conferir o orçamento**

```bash
pip install fonttools brotli
python scripts/build-fonts.py
ls -la companies/player/assets/fonts/
```

Esperado: quatro `.woff2`, cada um abaixo de **30 KB**, somando **menos de 90 KB**. Se estourar, reduza o repertório de `UNICODES` para `latin` puro e reavalie.

- [ ] **Step 3: Declarar as faces no CSS**

Em `styles.css`, no topo, fora de qualquer `@layer` (regras `@font-face` não pertencem a camada):

```css
@font-face {
  font-family: "Inter";
  src: url("../assets/fonts/inter-400.woff2") format("woff2");
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}
/* repita para 500 e 600 */

@font-face {
  font-family: "Fraunces";
  src: url("../assets/fonts/fraunces-italic-500.woff2") format("woff2");
  font-weight: 500;
  font-style: italic;
  font-display: swap;
}
```

Adicione os tokens de família em `brand.css`:

```css
    --font-sans: "Inter", ui-sans-serif, system-ui, "Segoe UI", sans-serif;
    --font-serif: "Fraunces", "Playfair Display", Georgia, serif;
```

- [ ] **Step 4: Trocar Google Fonts por preload**

Remova do `<head>` os dois `<link rel="preconnect">` e o `<link>` para `fonts.googleapis.com`. No lugar, pré-carregue apenas as duas faces do primeiro paint:

```html
<link rel="preload" href="assets/fonts/inter-500.woff2" as="font" type="font/woff2" crossorigin />
<link rel="preload" href="assets/fonts/fraunces-italic-500.woff2" as="font" type="font/woff2" crossorigin />
```

- [ ] **Step 5: Verificar que nada mais sai para o Google**

Com o servidor no ar, recarregue e inspecione a rede:

```
Esperado: nenhuma requisição para fonts.googleapis.com ou fonts.gstatic.com.
```

E confirme que as famílias carregaram de fato:

```javascript
({ inter: document.fonts.check('500 1rem Inter'),
   fraunces: document.fonts.check('italic 500 1rem Fraunces') })
// Esperado: { inter: true, fraunces: true }
```

- [ ] **Step 6: Commit**

```bash
git add scripts/build-fonts.py companies/player/assets/fonts companies/player/index.html companies/player/css/styles.css companies/player/css/brand.css
git commit -m "perf(player): self-host Inter and Fraunces as subset woff2

Drops two preconnects, two network round trips and a third party from the
critical path, and stops shipping visitor IPs to Google on every load. The
subsetting script is development tooling, following build-brand-assets.py."
```

---

### Tasks 8, 9 e 10: aposentadas

**Não executar.** O cliente decidiu, em 2026-09-11, que a página é de uma tela só —
sem barra de rolagem. As três tasks abaixo pressupõem o contrário e ficam sem
objeto:

- A **Task 8** mirava 2,4 a 3,5 viewports de conteúdo ("Se ficar abaixo de 2, a
  coreografia da Task 10 não terá curso").
- A **Task 9** anexava reveals ao scroll dessas seções.
- A **Task 10** era um `position: sticky` que só tem curso se houver rolagem.

O que se perde: o texto institucional não tem onde morar nesta página, e a
camada de movimento fica só com a animação de entrada que já existe em
`styles.css`. O que se ganha: a promessa de uma página de links — tudo à vista,
sem rolagem, o que foi verificado em 375×812 e 375×667 no commit 34a4622.

Se o texto institucional precisar existir, o lugar é o site, não este linktree.
A **Questão aberta 1** abaixo fica encerrada por consequência.

---

### Task 8: Seções de conteúdo

Duas seções abaixo do hero. A primeira tela continua sendo só os links.

**Files:**
- Modify: `companies/player/index.html`
- Modify: `companies/player/css/styles.css`

**Interfaces:**
- Consumes: tokens semânticos, `.shell`.
- Produces: `.section`, `.section__label`, `.section__lede`, `.section__body`, `.closing`, `.closing__address`. A Task 9 anexa reveals a `.section`; a Task 10 usa `#pin-sentinel`.

- [ ] **Step 1: Marcação das duas seções**

Depois de `</nav>` e antes do `<footer>`:

```html
<section class="section" id="sobre" aria-labelledby="sobre-titulo">
  <p class="section__label">O que fazemos</p>
  <h2 class="section__lede" id="sobre-titulo">
    Contabilidade que enxerga o próximo passo do seu negócio, não só o mês
    que passou.
  </h2>
  <p class="section__body">
    Cuidamos da rotina fiscal, contábil e trabalhista com a régua alta — e
    usamos o que ela revela para apontar onde a sua empresa perde dinheiro
    e onde pode crescer.
  </p>
</section>

<section class="closing" aria-labelledby="contato-titulo">
  <h2 class="section__lede" id="contato-titulo">Vamos conversar?</h2>
  <address class="closing__address">
    Palmas &middot; Tocantins
  </address>
  <a class="link link--cta" data-brand="whatsapp" href="https://api.whatsapp.com/send?phone=5511994453204" target="_blank" rel="noopener noreferrer">
    <span class="link__label">Falar com um contador</span>
    <svg class="link__arrow" aria-hidden="true"><use href="#i-arrow" /></svg>
  </a>
</section>
```

> **Texto marcado como rascunho.** O conteúdo acima é proposta de tom, derivada da assinatura existente. Nenhuma afirmação verificável sobre o negócio — sem número, sem prazo, sem superlativo. O cliente deve editar antes de publicar. Se o endereço completo chegar, substitua a linha do `<address>` e volte à Task 11 para promover o JSON-LD a `LocalBusiness`.

- [ ] **Step 2: Estilo das seções**

Em `@layer components`, com valores concretos:

- `.section`, `.closing` — `display: grid`, `gap: var(--space-4)`, `padding-block: var(--space-20)`, `border-top: 1px solid var(--rule)`.
- `.section__label` — `font-size: var(--text-2xs)`, `text-transform: uppercase`, `letter-spacing: var(--track-caps)`, `color: var(--text-faint)`, `margin: 0`.
- `.section__lede` — `font-family: var(--font-serif)`, `font-style: italic`, `font-size: var(--text-xl)`, `line-height: var(--leading-tight)`, `letter-spacing: var(--track-tight)`, `color: var(--text)`, `max-width: var(--measure-prose)`, `text-wrap: balance`, `margin: 0`.
- `.section__body` — `font-size: var(--text-base)`, `line-height: var(--leading-relaxed)`, `color: var(--text-muted)`, `max-width: var(--measure-prose)`, `text-wrap: pretty`, `margin: 0`.
- `.closing__address` — `font-style: normal`, `font-size: var(--text-sm)`, `letter-spacing: var(--track-wide)`, `text-transform: uppercase`, `color: var(--text-faint)`.
- `.closing .link--cta` — `justify-self: start`, `margin-top: var(--space-4)`.

- [ ] **Step 3: Verificar altura e contraste**

```bash
node scripts/check-contrast.js
```

```javascript
// Agora deve haver scroll de verdade
({ viewport: innerHeight,
   pagina: document.documentElement.scrollHeight,
   viewports: +(document.documentElement.scrollHeight / innerHeight).toFixed(2) })
// Em 375x812, esperado: viewports entre 2.4 e 3.5
```

Se ficar abaixo de 2, a coreografia da Task 10 não terá curso — aumente `padding-block` das seções antes de seguir.

- [ ] **Step 4: Commit**

```bash
git add companies/player/index.html companies/player/css/styles.css
git commit -m "feat(player): add the about and closing sections

The links keep the whole first screen; these two sections reward the
scroll and give the motion layer something real to animate against. Copy
is a draft in the existing voice and asserts nothing verifiable about the
business — the client edits before publishing."
```

---

### Task 9: Movimento — reveals e parallax

Enhancement puro. Estado padrão de tudo: visível.

**Files:**
- Create: `shared/css/motion.css`
- Modify: `companies/player/index.html` (`<link>`)

**Interfaces:**
- Consumes: `.link`, `.brand`, `.section`, `.closing`, `.backdrop`; tokens `--dur-*`, `--ease-*`, `--stagger-*`.
- Produces: as animações `rise`, `reveal`, `drift`. A Task 10 adiciona `pin-progress` no mesmo arquivo.

- [ ] **Step 1: Criar `shared/css/motion.css`**

```css
/* ==========================================================================
   Camada de movimento — Grupo Player
   Regra dura: o estado PADRÃO de todo elemento é visível. Animação só entra
   dentro de @supports. Um browser sem animation-timeline mostra a página
   inteira, estática e correta — nunca algo preso em opacity: 0.
   ========================================================================== */

@layer motion {
  /* Cascata de entrada — não depende de scroll, roda em todo browser. */
  @keyframes rise {
    from { opacity: 0; transform: translateY(14px); }
    to   { opacity: 1; transform: none; }
  }

  .brand {
    animation: rise var(--dur-slow) var(--ease-exit) both;
  }

  .link {
    animation: rise var(--dur-base) var(--ease-exit) both;
    animation-delay: calc(var(--i, 0) * var(--stagger-step) + var(--stagger-base));
  }

  /* --- Enhancement: guiado por scroll ---------------------------------- */
  @supports (animation-timeline: view()) {
    @keyframes reveal {
      from { opacity: 0; transform: translateY(28px); }
      to   { opacity: 1; transform: none; }
    }

    .section,
    .closing {
      animation: reveal auto var(--ease-exit) both;
      animation-timeline: view();
      /* Começa quando o topo do bloco entra 15% no viewport e termina a 45%.
         Curso curto de propósito: o conteúdo assenta cedo e fica legível. */
      animation-range: entry 15% entry 45%;
    }

    /* Parallax do fundo: 40px de diferencial no curso inteiro da página.
       Medido, não cinematográfico — e nunca sobre texto. */
    @keyframes drift {
      from { transform: translate3d(0, -20px, 0); }
      to   { transform: translate3d(0, 20px, 0); }
    }

    .backdrop::after {
      animation: drift auto linear both;
      animation-timeline: scroll(root block);
    }
  }

  /* --- Redução de movimento -------------------------------------------- */
  @media (prefers-reduced-motion: reduce) {
    .brand,
    .link,
    .section,
    .closing,
    .backdrop::after {
      animation: none !important;
    }

    .link,
    .link__arrow,
    .link--cta,
    .theme-toggle__icon {
      transition: none !important;
    }

    .link:hover,
    .link--cta:hover,
    .link:active {
      transform: none !important;
    }
  }
}
```

- [ ] **Step 2: Ligar a folha**

Em `index.html`, depois de `styles.css`:

```html
<link rel="stylesheet" href="../../shared/css/motion.css" />
```

- [ ] **Step 3: Verificar que o padrão é visível**

O teste que importa. Simule ausência de suporte inspecionando a opacidade computada com o scroll no topo:

```javascript
// Com a página no topo, as seções abaixo da dobra:
[...document.querySelectorAll('.section, .closing')].map(el => ({
  cls: el.className,
  opacity: getComputedStyle(el).opacity
}))
```

Em browser **com** suporte, as de fora da view podem estar em `0` — correto, é a animação. Em browser **sem** suporte, todas devem estar em `1`. Confirme a segunda condição desabilitando a feature ou conferindo que o bloco `@supports` é o único lugar com `opacity: 0`:

```bash
grep -n "opacity: 0" shared/css/motion.css
```

Esperado: toda ocorrência está dentro do bloco `@supports (animation-timeline: view())`. Se alguma estiver fora, é bug — corrija.

- [ ] **Step 4: Verificar redução de movimento**

Emule `prefers-reduced-motion: reduce` e confirme:

```javascript
[...document.querySelectorAll('.section, .link, .brand')]
  .map(el => getComputedStyle(el).animationName)
  .every(n => n === 'none')
// Esperado: true
```

- [ ] **Step 5: Commit**

```bash
git add shared/css/motion.css companies/player/index.html
git commit -m "feat(ds): add the scroll-driven motion layer

Reveals and background parallax ride animation-timeline, which MDN still
marks as limited availability. Every element defaults to visible and the
animation lives inside @supports, so a browser without it renders the page
correctly rather than leaving content stuck at opacity 0."
```

---

### Task 10: Movimento — o momento pinado

O único pin da página. `position: sticky` é Baseline, então a estrutura funciona em todo lugar; só a progressão é enhancement.

**Files:**
- Modify: `companies/player/index.html` (envelope do hero)
- Modify: `shared/css/motion.css`
- Modify: `companies/player/css/styles.css`

**Interfaces:**
- Consumes: `.brand`, `.section`; `--dur-*`, `--ease-*`.
- Produces: `.pin`, `.pin__stage`. Nenhuma task posterior depende disto.

- [ ] **Step 1: Validar o risco da spec antes de escrever o CSS final**

A spec registra um risco: `perspective`/`transform` em ancestrais brigam com `position: sticky`. Prove que o caminho escolhido está limpo:

```javascript
// Nenhum ancestral do elemento sticky pode ter transform, perspective,
// filter ou contain que crie containing block.
(() => {
  const el = document.querySelector('.pin__stage');
  const bad = [];
  for (let p = el?.parentElement; p; p = p.parentElement) {
    const s = getComputedStyle(p);
    if (s.transform !== 'none' || s.perspective !== 'none' ||
        s.filter !== 'none' || s.contain.includes('paint')) {
      bad.push({ tag: p.tagName, cls: p.className, transform: s.transform,
                 perspective: s.perspective, filter: s.filter });
    }
  }
  return bad;
})()
// Esperado: []
```

Se vier algo, mova a propriedade ofensora para um irmão do sticky em vez de um ancestral.

- [ ] **Step 2: Envelopar o hero**

```html
<div class="pin">
  <div class="pin__stage">
    <header class="brand"><!-- logo e assinatura, inalterados --></header>
  </div>
</div>
```

A `<nav class="links">` fica **fora** do `.pin` — os links não pinam, só a marca.

- [ ] **Step 3: Estrutura do pin (universal)**

Em `styles.css`, `@layer components`:

```css
.pin {
  /* Altura total = a tela do stage + o curso do pin.
     0,6vh de curso: com só duas seções abaixo, um viewport inteiro vira
     enchimento. Ajuste aqui se a página crescer. */
  min-height: 160vh;
}

.pin__stage {
  position: sticky;
  top: var(--space-8);
  z-index: var(--z-sticky);
}
```

- [ ] **Step 4: Progressão durante o pin (enhancement)**

Em `motion.css`, dentro do `@supports` existente:

```css
    /* Enquanto a marca está presa, ela recua: encolhe de leve e perde peso
       à medida que a primeira seção sobe por baixo. Sai de cena por
       vontade própria, em vez de ser empurrada. */
    @keyframes pin-progress {
      from { opacity: 1; transform: scale(1); }
      to   { opacity: 0.28; transform: scale(0.94); }
    }

    .pin__stage {
      animation: pin-progress auto linear both;
      animation-timeline: view(block);
      animation-range: exit 0% exit 100%;
    }
```

E acrescente `.pin__stage` à lista de `animation: none !important` do bloco `prefers-reduced-motion`.

- [ ] **Step 5: Verificar nos dois cenários**

```javascript
// 1. O sticky prende de fato (universal)
(() => {
  const el = document.querySelector('.pin__stage');
  window.scrollTo(0, 400);
  const top = el.getBoundingClientRect().top;
  return { position: getComputedStyle(el).position, topAposScroll: Math.round(top) };
})()
// Esperado: position 'sticky' e topAposScroll travado no valor de --space-8 (32)
```

```javascript
// 2. Sem suporte, nada fica invisível
getComputedStyle(document.querySelector('.pin__stage')).opacity
// Em browser sem animation-timeline: '1'
```

Depois role a página inteira e capture três momentos — topo, meio do pin, e depois da soltura — confirmando que a marca recua suavemente e a seção sobe por baixo sem sobreposição de texto.

- [ ] **Step 6: Commit**

```bash
git add companies/player/index.html shared/css/motion.css companies/player/css/styles.css
git commit -m "feat(player): pin the brand block through the hero handoff

The page spends its one pinned moment here. position: sticky carries the
structure everywhere, including Firefox; only the recede-while-pinned
progression rides animation-timeline. Parallax stays on scroll() rather
than the perspective trick, which would fight sticky from an ancestor."
```

---

### Task 11: Metadados

**Files:**
- Create: `scripts/build-og-image.py`
- Create: `companies/player/assets/og-image.png`
- Modify: `companies/player/index.html`

**Interfaces:**
- Consumes: `companies/player/assets/logo_grupo_player_dark.svg`.
- Produces: `og-image.png` em 1200×630 e o bloco JSON-LD.

- [ ] **Step 1: Escrever `scripts/build-og-image.py`**

Hoje o `og:image` aponta para um PNG de logo — proporção errada, que recorta mal em compartilhamento. Segue o padrão de `build-brand-assets.py`: Pillow, reproduzível, dev-only. Usa o PNG oficial de fundo escuro como fonte do logo (Pillow não lê SVG) e o TTF de origem da Task 7 para a assinatura.

```python
#!/usr/bin/env python3
"""
Gera a imagem de compartilhamento 1200x630 da Player.

Ferramenta de desenvolvimento — NÃO faz parte do build do site.

    pip install Pillow
    python scripts/build-og-image.py

Depende de scripts/fonts-src/Fraunces-Italic[SOFT,WONK,opsz,wght].ttf
(o mesmo arquivo que build-fonts.py usa).
"""
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "companies" / "player" / "assets"
LOGO = ASSETS / "logo_grupo_player_light.png"
FONT = ROOT / "scripts" / "fonts-src" / "Fraunces-Italic[SOFT,WONK,opsz,wght].ttf"
OUT = ASSETS / "og-image.png"

W, H = 1200, 630
SURFACE = (6, 8, 18)          # --surface do tema escuro
TEXT = (255, 219, 191)        # --text
AMBER = (255, 170, 0)         # --accent-surface
TAGLINE = "Somos cientistas da riqueza e da prosperidade."


def main():
    for path in (LOGO, FONT):
        if not path.is_file():
            sys.exit(f"arquivo necessário ausente: {path}")

    canvas = Image.new("RGB", (W, H), SURFACE)
    draw = ImageDraw.Draw(canvas)

    # Logo centralizado no terço superior, 420px de largura.
    logo = Image.open(LOGO).convert("RGBA")
    target_w = 420
    logo = logo.resize(
        (target_w, round(logo.height * target_w / logo.width)),
        Image.LANCZOS,
    )
    canvas.paste(logo, ((W - logo.width) // 2, 168), logo)

    # Assinatura em Fraunces italic, centralizada abaixo do logo.
    font = ImageFont.truetype(str(FONT), 44)
    box = draw.textbbox((0, 0), TAGLINE, font=font)
    draw.text(
        ((W - (box[2] - box[0])) // 2, 392),
        TAGLINE,
        font=font,
        fill=TEXT,
    )

    # Régua âmbar na base — o único acento de cor, como na página.
    draw.rectangle([(0, H - 6), (W, H)], fill=AMBER)

    canvas.save(OUT, "PNG", optimize=True)
    print(f"{OUT.name}: {canvas.size[0]}x{canvas.size[1]}, "
          f"{OUT.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Rodar e conferir**

```bash
pip install Pillow
python scripts/build-og-image.py
```

Esperado: `og-image.png: 1200x630` e peso **abaixo de 100 KB**. Abra o arquivo e confirme que o logo não está cortado e que a assinatura cabe numa linha — se estourar a largura, reduza o tamanho da fonte de 44 para 40.

- [ ] **Step 3: Apontar as metatags para ela**

```html
<meta property="og:image" content="https://playercontabilidade.github.io/linktree/companies/player/assets/og-image.png" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta name="twitter:card" content="summary_large_image" />
```

`twitter:card` sai de `summary` para `summary_large_image` — é o que usa uma imagem 1200×630.

- [ ] **Step 4: `theme-color` por tema**

Substitua a única metatag atual por duas:

```html
<meta name="theme-color" content="#F7F3EC" media="(prefers-color-scheme: light)" />
<meta name="theme-color" content="#060812" media="(prefers-color-scheme: dark)" />
```

- [ ] **Step 5: JSON-LD**

Antes de `</head>`. Sem o endereço completo (Questão aberta 2 da spec), o tipo é `Organization`, não `LocalBusiness` — declarar `LocalBusiness` sem `address` é marcação incompleta:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Player Contabilidade",
  "url": "https://playercontabilidade.com",
  "logo": "https://playercontabilidade.github.io/linktree/companies/player/assets/logo_grupo_player_light.png",
  "areaServed": "Palmas, Tocantins, Brasil",
  "sameAs": [
    "https://www.youtube.com/@playercontabilidade",
    "https://open.spotify.com/show/033DHcdDzl3xF7WrdSdjYD"
  ]
}
</script>
```

> Quando o endereço completo chegar, promova para `LocalBusiness` acrescentando `address` (`PostalAddress` com rua, número, bairro, CEP), `geo` (`-10.3037758`, `-48.3261666`, já extraídas do link do Maps) e `telephone`.

- [ ] **Step 6: Verificar**

```javascript
// JSON-LD é válido e parseável
JSON.parse(document.querySelector('script[type="application/ld+json"]').textContent)
```

```bash
# A OG image tem a dimensão declarada
python -c "from PIL import Image; im=Image.open('companies/player/assets/og-image.png'); print(im.size)"
# Esperado: (1200, 630)
```

- [ ] **Step 7: Commit**

```bash
git add scripts/build-og-image.py companies/player/assets/og-image.png companies/player/index.html
git commit -m "feat(player): add a real OG image, per-theme theme-color and JSON-LD

og:image pointed at a logo PNG, which crops badly at share aspect ratio.
The structured data stays Organization rather than LocalBusiness until we
have a full street address — declaring the latter without one is
incomplete markup."
```

---

### Task 12: Orçamentos no CI

Transforma os alvos da spec em algo que falha o build.

**Files:**
- Modify: `.github/workflows/deploy-pages.yml`
- Create: `.lighthouserc.json`

**Interfaces:**
- Consumes: `scripts/check-contrast.js`.
- Produces: um job `quality` que precede o deploy.

- [ ] **Step 1: Configuração do Lighthouse CI**

```json
{
  "ci": {
    "collect": {
      "staticDistDir": ".",
      "url": ["http://localhost/companies/player/index.html"],
      "numberOfRuns": 3,
      "settings": { "preset": "desktop" }
    },
    "assert": {
      "assertions": {
        "categories:accessibility": ["error", { "minScore": 1 }],
        "categories:performance": ["error", { "minScore": 0.95 }],
        "categories:seo": ["error", { "minScore": 0.95 }],
        "cumulative-layout-shift": ["error", { "maxNumericValue": 0 }],
        "total-byte-weight": ["error", { "maxNumericValue": 153600 }]
      }
    },
    "upload": { "target": "temporary-public-storage" }
  }
}
```

`total-byte-weight` em 153600 bytes é o orçamento de 150 KB da spec.

- [ ] **Step 2: Job de qualidade no workflow**

Insira **antes** do job `build`, e faça `build` depender dele:

```yaml
  quality:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Check colour token contrast
        run: node scripts/check-contrast.js

      - name: Lighthouse budgets
        run: npx --yes @lhci/cli@0.14.x autorun
```

E no job `build`:

```yaml
  build:
    needs: quality
    runs-on: ubuntu-latest
```

O `@lhci/cli` roda via `npx` no runner — é dependência de CI, nunca do site. `package.json` continua sem `dependencies`.

- [ ] **Step 3: Verificar localmente antes de empurrar**

```bash
node scripts/check-contrast.js && echo "contraste OK"
npx --yes @lhci/cli@0.14.x autorun
```

Se `total-byte-weight` estourar, o suspeito são as fontes — reduza o repertório em `build-fonts.py`. Se a acessibilidade cair de 100, rode `npx @lhci/cli collect` e leia o relatório antes de mexer em qualquer coisa.

- [ ] **Step 4: Verificar que o gate funciona de verdade**

Quebre um token de propósito e confirme que o CI falharia:

```bash
sed -i 's/--accent-text: #8a4b02/--accent-text: #ffaa00/' companies/player/css/brand.css
node scripts/check-contrast.js; echo "exit: $?"
# Esperado: FALHA e exit: 1
git checkout -- companies/player/css/brand.css
```

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/deploy-pages.yml .lighthouserc.json
git commit -m "ci: gate the deploy on contrast, accessibility and weight budgets

The spec's targets only mean something if a build can fail on them. Both
tools run through npx on the runner, so package.json still declares no
dependencies."
```

---

## Verificação final

Depois da última task, com o servidor no ar:

- [ ] `node scripts/check-contrast.js` sai 0 nos dois temas
- [ ] `git status` limpo após `npm run config`
- [ ] Nenhuma requisição para `fonts.googleapis.com` ou `fonts.gstatic.com`
- [ ] Página abre no tema salvo **sem flash**, em ambos os sentidos
- [ ] Em 375×812: nenhum alvo de toque abaixo de 44px
- [ ] Com `prefers-reduced-motion: reduce`: nenhuma animação, sticky preservado
- [ ] `grep -n "opacity: 0" shared/css/motion.css` — toda ocorrência dentro de `@supports`
- [ ] Console sem erros; todos os recursos em 200
- [ ] Capturas dos dois temas em mobile e desktop entregues ao cliente

## Questões que permanecem abertas

1. ~~**Texto das seções novas**~~ — encerrada: as Tasks 8–10 foram aposentadas (página de uma tela só).
2. **Endereço completo da sede** — sem ele o JSON-LD fica em `Organization` (Task 11). Quando chegar, promover para `LocalBusiness` com `address`, `geo` (`-10.3037758`, `-48.3261666`) e `telephone`.
