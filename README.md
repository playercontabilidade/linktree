# Linktree — Grupo Player

Site estático de links das empresas do Grupo Player, publicado no GitHub Pages.

**Produção:** https://playercontabilidade.github.io/linktree

## Estrutura

```
index.html                 # redireciona para /home/
home/                      # hub (hoje redireciona para Player)
companies/<slug>/          # página de cada empresa
shared/js/config.js        # gerado — não editar à mão
scripts/generate-config.js # gera config a partir do .env / CI
.github/workflows/         # deploy no GitHub Pages
```

## Configuração local

Pré-requisito: Node.js 20+.

1. Clone o repositório e entre na pasta do projeto.
2. Copie o ambiente de exemplo:

```bash
cp .env.example .env
```

3. Ajuste o `.env` se precisar (valores padrão para local):

| Variável    | Local                         | Produção (CI)                                      |
|-------------|-------------------------------|----------------------------------------------------|
| `ENV`       | `development`                 | `production`                                       |
| `BASE_PATH` | *(vazio)*                     | `/linktree`                                        |
| `SITE_URL`  | `http://localhost:5500`       | `https://playercontabilidade.github.io/linktree`   |

4. Gere o `shared/js/config.js`:

```bash
npm run config
```

5. Sirva a raiz do projeto com qualquer servidor estático (Live Server, `npx serve`, etc.) na porta que estiver em `SITE_URL`.

O arquivo `.env` não vai para o Git (está no `.gitignore`). Em produção as variáveis vêm do workflow, não do `.env`.

## Deploy (GitHub Pages)

O deploy é automático via [`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml):

- **Gatilho:** push na branch `main`, ou execução manual (**Actions → Deploy GitHub Pages → Run workflow**)
- **Build:** gera o config de produção (`BASE_PATH=/linktree`) e publica a raiz do repositório

### Configurar o repositório (uma vez)

1. No GitHub: **Settings → Pages**
2. Em **Build and deployment → Source**, escolha **GitHub Actions** (não “Deploy from a branch”)
3. Confirme que a branch padrão de deploy do workflow é `main`

> Se a Source for “branch”, o `config.js` de desenvolvimento sobe sem `BASE_PATH` e redirects absolutos quebram (ex.: `/home/` em vez de `/linktree/home/`). Os redirects internos usam paths relativos; mesmo assim o deploy correto é via Actions.

### Publicar mudanças

1. Faça merge (ou push) das alterações em `main`
2. Acompanhe em **Actions → Deploy GitHub Pages**
3. Abra https://playercontabilidade.github.io/linktree

Se o nome do repositório ou a URL do Pages mudar, atualize `BASE_PATH` e `SITE_URL` no workflow e no `.env.example`.

## Nova empresa

Crie `companies/<slug>/` com `index.html`, `css/`, `js/` e `assets/`. Detalhes em [`companies/README.md`](companies/README.md).
