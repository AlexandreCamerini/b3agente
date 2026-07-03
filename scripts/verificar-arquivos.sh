#!/usr/bin/env bash
# verificar-arquivos.sh — BolsIA (b3-agente)
# Fonte ÚNICA da verdade do manifesto: confere se TODOS os arquivos necessários
# para o app funcionar estão presentes, antes de qualquer git/deploy.
# Usado por git-do-zero.sh e atualizar.sh; pode ser rodado sozinho:
#   bash scripts/verificar-arquivos.sh
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.."

ok(){ printf "  \033[32m[OK]\033[0m %s\n" "$*"; }
falta(){ printf "  \033[31m[FALTA]\033[0m %s\n" "$*"; FALHAS=$((FALHAS+1)); }
FALHAS=0

echo "== Manifesto do backend (server/) =="
REQ_SERVER=(
  server/Procfile server/railway.json server/requirements.txt
  server/requirements-prod.txt server/pytest.ini
  server/app/__init__.py server/app/main.py server/app/db.py server/app/auth.py
  server/app/store.py server/app/llm.py server/app/managed.py server/app/metering.py
  server/app/yahoo.py server/app/tickers.py server/app/catalog.py server/app/plan.py
  server/app/kpi.py server/app/defaults.py server/app/indicators.py
  server/app/candles.py server/app/candle_cache.py server/app/scanner.py
  server/app/setups.py server/app/scan_deep.py server/app/technical_models.py
  server/app/options_api.py server/app/options_provider_yahoo.py server/app/options_quant.py
)
for f in "${REQ_SERVER[@]}"; do [ -f "$f" ] && ok "$f" || falta "$f"; done

echo "== Manifesto do web (web/) =="
REQ_WEB=(
  web/package.json web/package-lock.json web/vite.config.js web/index.html
  web/capacitor.config.ts
  web/src/main.jsx web/src/App.jsx web/src/api.js web/src/persistence.js
  web/src/sync.js web/src/notify.js web/src/finance.js web/src/migrate.js
  web/src/catalog.js web/src/plan.js web/src/demo.js web/src/disclaimers.js
  web/public/icon-192.png web/public/icon-512.png web/public/icon-512-maskable.png
  web/public/apple-touch-icon.png
)
for f in "${REQ_WEB[@]}"; do [ -f "$f" ] && ok "$f" || falta "$f"; done

echo "== Testes (garantia de qualidade versionada) =="
[ -d server/tests ] && [ -n "$(ls server/tests/test_*.py 2>/dev/null)" ] && ok "server/tests/ ($(ls server/tests/test_*.py | wc -l | tr -d ' ') suítes)" || falta "server/tests/"
[ -d web/tests ] && [ -n "$(ls web/tests/*.mjs 2>/dev/null)" ] && ok "web/tests/ ($(ls web/tests/*.mjs | wc -l | tr -d ' ') suítes)" || falta "web/tests/"

echo "== Scripts e raiz =="
REQ_MISC=( .gitignore scripts/setup.sh scripts/run.sh scripts/test.sh
  scripts/atualizar-servidor.sh scripts/instalar-iphone.sh )
for f in "${REQ_MISC[@]}"; do [ -f "$f" ] && ok "$f" || falta "$f"; done

echo "== Sanidade do .gitignore (o que NUNCA pode ser versionado) =="
for pat in "server/.venv/" "server/data/" "*.db" "node_modules/" "web/dist/" "web/ios/" ".env"; do
  grep -qF "$pat" .gitignore && ok "ignora $pat" || falta ".gitignore sem '$pat'"
done
# e o que NUNCA pode estar ignorado:
grep -qE "^package-lock" .gitignore && falta ".gitignore NÃO pode ignorar package-lock.json" || ok "package-lock.json versionável"

echo "== Sanidade do deploy (Railway) =="
grep -q 'app.main:app' server/Procfile && ok "Procfile → uvicorn app.main:app" || falta "Procfile sem o start do uvicorn"
grep -q '"healthcheckPath": "/api/health"' server/railway.json && ok "railway.json → healthcheck /api/health" || falta "railway.json sem healthcheck"
grep -q 'api/health' server/app/main.py && ok "endpoint /api/health presente" || falta "main.py sem /api/health"

if [ "$FALHAS" -gt 0 ]; then
  printf "\n\033[31m✗ %d item(ns) faltando — NÃO suba o git/deploy assim.\033[0m\n" "$FALHAS"
  exit 1
fi
printf "\n\033[32m✓ Manifesto completo: o repositório tem tudo que o app precisa.\033[0m\n"
