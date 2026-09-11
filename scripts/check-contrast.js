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

/**
 * Pares (frente, fundo, alvo) conferidos em todos os temas.
 * Foco é obrigatório (WCAG 2.4.7); regras decorativas não comunicam informação
 * necessária para identificar um componente, logo não são verificadas.
 */
const PAIRS = [
  ["--text", "--surface", AA_NORMAL],
  ["--text-muted", "--surface", AA_NORMAL],
  ["--text", "--surface-raised", AA_NORMAL],
  ["--text-muted", "--surface-raised", AA_NORMAL],
  ["--accent-text", "--surface", AA_NORMAL],
  ["--on-accent", "--accent-surface", AA_NORMAL],
  ["--focus", "--surface", AA_LARGE],
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
 * Reconhece três formatos de bloco de tema:
 * - `:root` vira o tema "dark" (canônico)
 * - `[data-theme="x"]` vira o tema "x"
 * - `:root:not([data-theme="dark"])` vira o tema "light-system"
 */
function parseThemes(css) {
  const themes = {};
  // A alternativa mais longa vem primeiro: com :root antes, o motor casaria
  // :root e falharia em \s*\{ contra :not(, abandonando o bloco inteiro.
  const blockRe =
    /(:root:not\(\[data-theme=["']dark["']\]\)|:root|\[data-theme=["']([a-z-]+)["']\])\s*\{([^}]*)\}/g;
  let block;
  while ((block = blockRe.exec(css)) !== null) {
    const selector = block[1];
    const name = block[2]
      ? block[2]
      : selector.indexOf(":not(") !== -1
        ? "light-system"
        : "dark";
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
