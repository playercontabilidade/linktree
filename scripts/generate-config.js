#!/usr/bin/env node
/**
 * Gera shared/js/config.js a partir de variáveis de ambiente ou arquivo .env
 */
const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const envPath = path.join(root, ".env");
const outPath = path.join(root, "shared", "js", "config.js");

function loadDotEnv(filePath) {
  const values = {};
  if (!fs.existsSync(filePath)) {
    return values;
  }

  const lines = fs.readFileSync(filePath, "utf8").split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eq = trimmed.indexOf("=");
    if (eq === -1) continue;
    const key = trimmed.slice(0, eq).trim();
    let value = trimmed.slice(eq + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    values[key] = value;
  }
  return values;
}

const fileEnv = loadDotEnv(envPath);

const ENV = process.env.ENV || fileEnv.ENV || "development";
const BASE_PATH =
  process.env.BASE_PATH !== undefined
    ? process.env.BASE_PATH
    : fileEnv.BASE_PATH !== undefined
      ? fileEnv.BASE_PATH
      : "";
const SITE_URL =
  process.env.SITE_URL ||
  fileEnv.SITE_URL ||
  (ENV === "production"
    ? "https://playercontabilidade.github.io/linktree"
    : "http://localhost:5500");

const config = {
  ENV,
  BASE_PATH,
  SITE_URL,
};

const banner =
  "/* Gerado por scripts/generate-config.js - nao edite em producao */\n";
const body =
  "window.APP_CONFIG = " + JSON.stringify(config, null, 2) + ";\n";

fs.mkdirSync(path.dirname(outPath), { recursive: true });
fs.writeFileSync(outPath, banner + body, "utf8");

console.log("config.js gerado:", config);
