#!/usr/bin/env bash
# Boris+ - instalacao (robusto a cwd/layout; nao ativa o venv).
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVER_DIR=""
for cand in "$ROOT/server" "$ROOT" "$SCRIPT_DIR/../server" "$ROOT/../server"; do
  if [ -f "$cand/app/main.py" ]; then SERVER_DIR="$(cd "$cand" && pwd)"; break; fi
done
[ -n "$SERVER_DIR" ] || { echo "ERRO: nao encontrei o backend (app/main.py) a partir de $ROOT"; exit 1; }
WEB_DIR="$ROOT/web"; [ -d "$WEB_DIR" ] || WEB_DIR="$SERVER_DIR/../web"

PY="${PYTHON:-python3}"
echo "==> Backend (FastAPI / Python)   [$SERVER_DIR]"
command -v "$PY" >/dev/null 2>&1 || { echo "ERRO: '$PY' nao encontrado. Instale Python 3.10+ (python.org ou 'brew install python')."; exit 1; }
echo "    usando: $("$PY" -V 2>&1)  ($(command -v "$PY"))"
"$PY" -c 'import sys; raise SystemExit(0 if sys.version_info>=(3,10) else 1)' || echo "    AVISO: recomendado Python 3.10+ (tambem roda em 3.9)."

rm -rf "$SERVER_DIR/.venv"
"$PY" -m venv "$SERVER_DIR/.venv" || { echo "ERRO ao criar o venv. No macOS: instale o Python do python.org ou 'brew install python'."; exit 1; }
VENV_PY="$SERVER_DIR/.venv/bin/python"; [ -x "$VENV_PY" ] || VENV_PY="$SERVER_DIR/.venv/Scripts/python.exe"
echo "    atualizando pip..."
"$VENV_PY" -m pip install --upgrade pip >/dev/null 2>&1 || true
echo "    instalando dependencias (fastapi, uvicorn, httpx, pytest)..."
"$VENV_PY" -m pip install -r "$SERVER_DIR/requirements.txt" || { echo "ERRO no 'pip install' (veja acima: rede/proxy/firewall?)."; exit 1; }
echo "    backend OK -> $SERVER_DIR/.venv  (interpretador para o PyCharm)"

echo "==> App web (React / Vite / Capacitor)   [$WEB_DIR]"
if command -v npm >/dev/null 2>&1 && [ -d "$WEB_DIR" ]; then
  ( cd "$WEB_DIR" && npm install ) && echo "    web OK" || echo "    AVISO: 'npm install' falhou (precisa de Node 22+). O backend funciona mesmo assim."
else
  echo "    npm/web ausente. Instale Node 22+ se for usar o app web/iOS."
fi

cat <<'TXT'

Pronto. Proximos passos:
  bash scripts/run.sh         # DEV: backend (8787) + Vite (5173)
  bash scripts/run.sh --prod  # PROD: 1 servidor servindo tudo
  bash scripts/test.sh        # testes (pytest)
TXT
