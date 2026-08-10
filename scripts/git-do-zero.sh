#!/usr/bin/env bash
# git-do-zero.sh — Boris+ (b3-agente)
# Reconstrói o repositório Git DO ZERO e publica no GitHub em um comando.
#
#   bash scripts/git-do-zero.sh                       # usa o repo padrão (b3agente)
#   bash scripts/git-do-zero.sh https://github.com/USUARIO/REPO.git
#   bash scripts/git-do-zero.sh --sem-push            # tudo, menos o push (ensaio)
#   bash scripts/git-do-zero.sh --recriar [url]       # apaga o .git atual e refaz
#
# O que faz, na ordem:
#   1. verificar-arquivos.sh  → manifesto completo (aborta se faltar algo);
#   2. validação de código    → py_compile no backend, node --check no web;
#   3. git init + .gitignore  → só se não houver .git (ou com --recriar);
#   4. commit inicial com TUDO que o app precisa (o .gitignore protege
#      node_modules/ web/ios/ dist/ .venv/ data/ *.db .env);
#   5. remote origin + push -u origin main.
#
# AUTENTICAÇÃO GITHUB: a senha da conta NÃO funciona no push. Use um
# Personal Access Token (PAT): github.com → Settings → Developer settings →
# Personal access tokens → Generate new token (classic), escopo `repo`.
# No prompt do push: Username = seu usuário · Password = o TOKEN.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.."
ROOT="$(pwd)"

say(){ printf "\n\033[1m== %s ==\033[0m\n" "$*"; }
ok(){ printf "  \033[32m[OK]\033[0m %s\n" "$*"; }
die(){ printf "  \033[31m[X]\033[0m %s\n" "$*" >&2; exit 1; }

REPO_URL="https://github.com/AlexandreCamerini/b3agente.git"
SEM_PUSH=0; RECRIAR=0
for arg in "$@"; do
  case "$arg" in
    --sem-push) SEM_PUSH=1 ;;
    --recriar)  RECRIAR=1 ;;
    http*|git@*) REPO_URL="$arg" ;;
    *) die "argumento desconhecido: $arg" ;;
  esac
done

command -v git >/dev/null 2>&1 || die "git não encontrado (macOS: xcode-select --install)"

say "1/5 · Manifesto de arquivos"
bash scripts/verificar-arquivos.sh || die "manifesto incompleto — corrija antes de subir"

say "2/5 · Validação de código"
PYBIN="server/.venv/bin/python"; [ -x "$PYBIN" ] || PYBIN="python3"
"$PYBIN" -m py_compile server/app/*.py || die "py_compile falhou"
ok "py_compile backend"
if command -v node >/dev/null 2>&1; then
  for f in web/src/*.js; do node --check "$f" >/dev/null || die "node --check falhou em $f"; done
  ok "node --check web/src"
else
  echo "  (node ausente — pulei o check do web; instale Node 18+ para o app web)"
fi
if [ -x "server/.venv/bin/python" ]; then
  ( cd server && ./.venv/bin/python -m pytest -q ) || die "suítes falharam — não vou subir código quebrado"
  ok "suítes do backend verdes"
else
  echo "  (venv ausente — pulei as suítes; rode 'bash scripts/instalar.sh' antes, se quiser essa garantia)"
fi

say "3/5 · Repositório Git"
if [ -d .git ]; then
  if [ "$RECRIAR" = "1" ]; then
    echo "  .git existente será APAGADO em 5s (histórico local se perde; Ctrl+C para abortar)…"
    sleep 5
    rm -rf .git
    ok ".git anterior removido"
  else
    die "já existe um .git aqui. Para atualização use scripts/atualizar.sh; para refazer do zero use --recriar"
  fi
fi
git init -q -b main 2>/dev/null || { git init -q && git checkout -q -b main; }
ok "git init (branch main)"

say "4/5 · Commit inicial (tudo que o app precisa)"
git add -A
N_ARQ=$(git diff --cached --name-only | wc -l | tr -d ' ')
# sanidade: nada proibido pode ter entrado no commit
if git diff --cached --name-only | grep -qE "(^|/)(node_modules|\.venv|dist)/|^web/ios/|^server/data/|\.db$|\.p8$|^\.env"; then
  die "arquivo proibido no commit — confira o .gitignore (node_modules/ios/dist/venv/data/db/env)"
fi
ok "sem arquivos proibidos no commit"
git -c user.name="${GIT_NAME:-Alexandre Camerini}" -c user.email="${GIT_EMAIL:-alex@bolsia.local}" \
  commit -qm "Boris+ — bootstrap do repositório (app completo: backend FastAPI + web React/Capacitor + scripts + testes)"
ok "commit inicial com $N_ARQ arquivos"

say "5/5 · Remote e push"
git remote remove origin 2>/dev/null || true
git remote add origin "$REPO_URL"
ok "origin → $REPO_URL"
if [ "$SEM_PUSH" = "1" ]; then
  echo "  (--sem-push) Ensaio concluído. Quando quiser publicar:"
  echo "      git push -u origin main"
  echo "  Lembrete: no prompt, Password = Personal Access Token (não a senha)."
  exit 0
fi
echo "  Enviando ao GitHub… (Username = seu usuário · Password = seu PAT)"
git push -u origin main || die "push falhou — confira o PAT (escopo 'repo') e se o repositório existe no GitHub"
ok "publicado em $REPO_URL"

say "Pronto — próximos passos"
cat <<'FIM'
  Railway (primeira vez): siga o passo a passo do ATUALIZAR-Git-Railway-iOS.md
    (New Project → Deploy from GitHub → Root Directory=server → volume /data
     → variável B3_DB_PATH=/data/b3.db → Generate Domain → /api/health).
  Railway (repo já conectado): o push acima JÁ disparou o redeploy automático.
  Atualizações futuras: bash scripts/atualizar.sh files.zip "mensagem"
FIM
