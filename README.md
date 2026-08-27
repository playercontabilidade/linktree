# Linktree — Grupo Player

Site estático com as páginas de links das empresas do Grupo Player, publicado no
GitHub Pages.

**Produção:** https://playercontabilidade.github.io/linktree/

---

## Stack

Não há framework, bundler, nem dependência de runtime. O site é HTML, CSS e
JavaScript servidos como arquivos estáticos.

| Camada | O que é usado |
|---|---|
| Marcação | HTML5, uma pasta por empresa |
| Estilo | CSS puro com custom properties, grid, `@supports`, `prefers-reduced-motion` |
| Script | JavaScript ES5 em IIFE — sem módulos, sem transpilação |
| Tipografia | Inter, via Google Fonts |
| Configuração | Node.js 20+, só para gerar `shared/js/config.js` a partir do `.env` |
| Deploy | GitHub Actions → GitHub Pages |

O `package.json` não declara `dependencies` e o repositório não tem lockfile nem
`node_modules`. Isso é intencional: a página muda uma ou duas vezes por ano e não
tem estado, rota dinâmica nem dado remoto. Manter zero dependência significa que
daqui a três anos ainda dá para abrir o arquivo e editar, sem `npm install`
quebrado nem major version para resolver.

Se um dia surgir conteúdo dinâmico de verdade (vagas vindas de uma API, o
simulador tributário embutido), aí vale reavaliar — provavelmente com Astro, que
mantém tudo estático por padrão. Enquanto for "logo + lista de links", trocar a
stack seria trocar algo que funciona por algo que dá manutenção.

---

## Estrutura

```
index.html                     redireciona para /home/
home/index.html                hub — hoje redireciona para a Player
companies/<slug>/              uma pasta por empresa
  index.html
  css/styles.css
  js/main.js
  assets/
shared/js/config.js            GERADO — não editar à mão
scripts/generate-config.js     gera o config a partir do .env / CI
scripts/build-brand-assets.py  regenera os assets de marca (uso pontual)
.github/workflows/             deploy no GitHub Pages
.nojekyll                      impede o Pages de processar o conteúdo
```

Os redirects de `index.html` e `home/index.html` são JavaScript client-side. Eles
normalizam a barra final da URL e removem o `BASE_PATH` do Pages antes de montar
o destino, então funcionam tanto em `localhost` quanto em `/linktree/`.

---

## Rodando local

Pré-requisito: **Node.js 20+**.

**1.** Copie o ambiente de exemplo:

```bash
cp .env.example .env
```

**2.** Ajuste o `.env` se precisar. Os padrões já servem para desenvolvimento:

| Variável | Local | Produção (vem do CI) |
|---|---|---|
| `ENV` | `development` | `production` |
| `BASE_PATH` | *(vazio)* | `/linktree` |
| `SITE_URL` | `http://localhost:5500` | `https://playercontabilidade.github.io/linktree` |

**3.** Gere o `shared/js/config.js`:

```bash
npm run config
```

**4.** Sirva a raiz do projeto com qualquer servidor estático, na porta que estiver
em `SITE_URL`:

```bash
npx serve --listen 5500 .
```

**5.** Abra http://localhost:5500/companies/player/

O `.env` não vai para o Git (está no `.gitignore`). Em produção as variáveis vêm
do workflow, nunca do `.env`.

### Como a configuração funciona

`scripts/generate-config.js` lê as variáveis de ambiente (ou do `.env`, nessa
ordem de precedência) e escreve `shared/js/config.js`, que expõe:

```js
window.APP_CONFIG = { ENV, BASE_PATH, SITE_URL };
```

O `js/main.js` de cada empresa lê esse objeto para saber em que ambiente está.
Em `development` ele loga cada clique no console; em `production` não faz nada.

O arquivo gerado **é versionado** — o Pages precisa dele no artefato. O CI
sobrescreve com os valores de produção antes de publicar, então nunca edite à
mão: rode `npm run config`.

---

## Design system

Os tokens vêm do site institucional (playercontabilidade.com) e estão
declarados no `:root` de cada `css/styles.css`.

| Papel | Token | Valor |
|---|---|---|
| Fundo base | `--ink` | `#05070f` |
| Fundo gradiente | `--navy-900` / `--navy-500` | `#08122b` / `#1a2b5c` |
| Marca | `--amber` / `--amber-deep` | `#ffaa00` / `#f88805` |
| Texto | `--cream` | `#ffdbbf` |
| Texto secundário | `--cream-dim` / `--cream-mute` | creme a 70% / 66% |
| Vidro | `--glass` / `--hairline` | branco a 4,5% / 12% |
| Tipografia | `--font` | Inter, tracking negativo nos títulos |

Regras que a página segue e que convém não quebrar:

- **Hierarquia.** Um único CTA preenchido em âmbar (o comercial); todo o resto em
  cards de vidro. Se tudo virar destaque, nada é destaque.
- **Contraste.** Todo texto fica acima de 4,5:1 (AA). O menor hoje é 6,15:1. Ao
  mexer em `--cream-mute`, remeça.
- **Cores de plataforma** saem do atributo `data-brand` do link, não da posição.
  Reordenar links não troca as cores.
- **Animação de entrada** usa `--i` inline como índice: `calc(var(--i) * 55ms)`.
  Link novo, índice novo.
- **`prefers-reduced-motion`** desliga todo movimento. Mantenha assim.

Os ícones ficam num sprite `<symbol>` no topo do `index.html` e são usados via
`<use href="#i-...">`. Para adicionar um, crie um `<symbol>` com `viewBox` e
`fill="currentColor"`.

---

## Assets da Player

| Arquivo | Uso | Peso |
|---|---|---|
| `logo_grupo_player_dark.svg` | Lockup do topo. Wordmark branco, símbolo colorido — para fundo escuro. | 101 KB |
| `logo_grupo_player.svg` | Original para fundo claro (wordmark navy `#0e1c2c`). Não é carregado pela página; é a fonte para regerar o dark. | 141 KB |
| `logo_grupo_player_light.png` | Versão oficial do site para fundo escuro. Usada só como `og:image`. | 16 KB |
| `favicon.ico`, `favicon-32.png`, `favicon-180.png` | Ícone do navegador e da tela de início do iOS. | 43 KB |

### Por que os SVGs precisam de tratamento

Os SVGs entregues são **híbridos**: no `logo_grupo_player.svg` o wordmark são
paths vetoriais de verdade (11 elementos com `fill="#0e1c2c"`), mas o símbolo é
um par de PNGs embutidos em base64 — a arte em RGB mais uma máscara de
luminância que faz o papel de canal alfa.

Isso tem duas consequências:

1. **O wordmark é escuro por natureza.** Em fundo escuro ele some. A variante
   dark troca os 11 `fill` para branco e mantém o símbolo nas cores originais.
2. **O raster vinha superdimensionado.** Era 753 px de largura para aparecer a
   ~60 px na tela. Reduzir para 400 px (folga para telas 3x) levou o arquivo de
   144 KB para 101 KB sem perda visível.

O antigo `favicon.svg` tinha o mesmo problema em escala pior: 470 KB para um
ícone. A arte RGB recebeu a máscara como alfa, foi recortada pelo `viewBox`,
aparada pelo bounding box real e redimensionada — o jogo inteiro ficou em 43 KB.

### Regenerar

```bash
pip install Pillow
python scripts/build-brand-assets.py
```

O script é reproduzível (mesma entrada, mesmo byte de saída) e **não faz parte do
build do site** — Pillow é ferramenta de desenvolvimento, não dependência do
projeto. Rode só quando os arquivos de marca originais mudarem.

Para regerar os favicons é preciso recuperar o `favicon.svg` do histórico:

```bash
git show <commit>:companies/player/assets/favicon.svg > companies/player/assets/favicon.svg
```

### Removidos

`background_branco.png` (1,7 MB), `background_cinza_escuro.png` (1,5 MB),
`logo.svg` (248 KB) e `favicon.svg` (460 KB) foram removidos por não terem
referência nenhuma. O fundo da página é gradiente CSS, sem imagem. Todos seguem
recuperáveis pelo histórico do Git.

Resultado: a primeira visita baixa ~100 KB (antes eram ~1,8 MB) e a visita
repetida, ~49 KB.

---

## Deploy (GitHub Pages)

Automático via [`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml).

- **Gatilho:** push em `main` ou em `feat/player-linktree`, ou execução manual em
  **Actions → Deploy GitHub Pages → Run workflow**
- **Build:** roda `generate-config.js` com `ENV=production` e `BASE_PATH=/linktree`,
  confere com `grep` que os dois valores saíram certos, e publica a raiz do repo
- **Deploy:** `actions/deploy-pages@v4` no environment `github-pages`

> O branch padrão deste repositório é **`feat/player-linktree`** — é dele que sai
> o deploy hoje. Todo push nele publica em produção.

### Configurar o repositório (uma vez)

1. No GitHub: **Settings → Pages**
2. Em **Build and deployment → Source**, escolha **GitHub Actions**
   (não "Deploy from a branch")

Se a Source ficar em "Deploy from a branch", o `config.js` de desenvolvimento
sobe sem o `BASE_PATH` e os redirects quebram.

### Publicar

1. Push no branch de deploy
2. Acompanhe em **Actions → Deploy GitHub Pages**
3. Abra https://playercontabilidade.github.io/linktree/ — **com a barra no final**

Se o nome do repositório ou a URL do Pages mudar, atualize `BASE_PATH` e
`SITE_URL` no workflow e no `.env.example`.

### Problemas comuns

| Sintoma | Causa provável |
|---|---|
| 404 em `/home/` | Pages em "Deploy from a branch", ou URL aberta sem a barra final |
| Página sem estilo em produção | `config.js` gerado sem `BASE_PATH` |
| Logo invisível | Usando `logo_grupo_player.svg` (fundo claro) em vez da variante `_dark` |

---

## Nova empresa

Crie `companies/<slug>/` com `index.html`, `css/`, `js/` e `assets/`. Cada empresa
tem layout e identidade próprios — não há template compartilhado, e isso é
proposital. Detalhes em [`companies/README.md`](companies/README.md).

O que vale copiar da Player como ponto de partida: a estrutura de tokens no
`:root`, o sprite de ícones, o padrão `data-brand` e o piso de qualidade
(contraste AA, `prefers-reduced-motion`, foco visível no teclado, alvos de toque
de 44 px ou mais).

---

## Convenções

- **Mensagens de commit em inglês**, no formato *Conventional Commits*
  (`feat:`, `fix:`, `perf:`, `docs:`, `refactor:`, `chore:`), com escopo quando
  ajudar: `feat(player): ...`
- **Não versionar** `.env`, `node_modules/` nem configuração local de editor/IDE
- **`shared/js/config.js` é gerado.** Se precisar mudar, mexa no
  `scripts/generate-config.js` ou nas variáveis do workflow
