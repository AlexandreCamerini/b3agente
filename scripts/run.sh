#!/usr/bin/env bash
# Boris+ - lancador com auto-instalacao.
#   bash scripts/run.sh           # DEV:  cria o ambiente se faltar, sobe backend (8787) + Vite (5174)
#   bash scripts/run.sh --prod    # PROD: build web + 1 servidor (8787)
#   bash scripts/run.sh --stop    # encerra e libera as portas
#   bash scripts/run.sh --status  # mostra o que esta no ar
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVER_DIR=""
for cand in "$ROOT/server" "$ROOT" "$SCRIPT_DIR/../server" "$ROOT/../server"; do
  if [ -f "$cand/app/main.py" ]; then SERVER_DIR="$(cd "$cand" && pwd)"; break; fi
done
if [ -z "$SERVER_DIR" ]; then
  echo "ERRO: nao encontrei o backend (app/main.py) a partir de $ROOT"
  echo "      Rode de dentro da pasta do projeto (a que contem server/ e scripts/)."
  exit 1
fi
WEB_DIR="$ROOT/web"; [ -d "$WEB_DIR" ] || WEB_DIR="$SERVER_DIR/../web"

PORT="${PORT:-8787}"; VITE_PORT="${VITE_PORT:-5174}"
MODE="dev"
case "${1:-}" in
  --prod) MODE="prod";; --stop) MODE="stop";; --status) MODE="status";; --dev|"") MODE="dev";;
  -h|--help) sed -n '2,6p' "$0" | sed 's/^# \{0,1\}//'; exit 0;;
  *) echo "Opcao desconhecida: $1 (use --help)"; exit 1;;
esac

VENV="$SERVER_DIR/.venv"
venv_py(){ if [ -x "$VENV/bin/python" ]; then echo "$VENV/bin/python"; else echo "$VENV/Scripts/python.exe"; fi; }

# Mata SÓ o que é NOSSO na porta (cwd == $ROOT ou $SERVER_DIR) — nunca um
# processo de outro projeto que por acaso esteja na mesma porta. Regra do
# ~/.claude/CLAUDE.md: "Nunca matar processo que não é seu."
free_port(){
  local p="$1"; command -v lsof >/dev/null 2>&1 || return 0
  local pid cwd
  for pid in $(lsof -ti tcp:"$p" 2>/dev/null || true); do
    cwd="$(lsof -a -p "$pid" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p')"
    case "$cwd" in
      "$ROOT"|"$ROOT"/*|"$SERVER_DIR"|"$SERVER_DIR"/*) kill "$pid" 2>/dev/null || true ;;
      *) echo "  [!] porta $p ocupada por PID $pid de OUTRO projeto (cwd=$cwd) — não vou matar. Libere manualmente ou rode noutra porta." >&2 ;;
    esac
  done
}
lan_ip(){ (command -v ipconfig >/dev/null 2>&1 && ipconfig getifaddr en0 2>/dev/null) || (hostname -I 2>/dev/null | awk '{print $1}') || echo "127.0.0.1"; }

# cria o venv + instala dependencias se ainda nao existir
ensure_backend(){
  local py; py="$(venv_py)"
  if [ -x "$py" ] && "$py" -c "import fastapi" >/dev/null 2>&1; then return 0; fi
  echo "==> Preparando o ambiente Python (primeira vez)"
  local PY="${PYTHON:-python3}"
  if ! command -v "$PY" >/dev/null 2>&1; then
    echo "ERRO: 'python3' nao encontrado."
    echo "      Instale o Python 3 em https://www.python.org/downloads/macos/ e rode de novo."
    exit 1
  fi
  echo "    python do sistema: $("$PY" -V 2>&1)"
  if [ ! -x "$(venv_py)" ]; then
    rm -rf "$VENV"
    "$PY" -m venv "$VENV" || { echo "ERRO: falha ao criar o venv. Instale o Python do python.org."; exit 1; }
  fi
  py="$(venv_py)"
  echo "    instalando fastapi/uvicorn/httpx/pytest (pode demorar)..."
  "$py" -m pip install --upgrade pip >/dev/null 2>&1 || true
  if ! "$py" -m pip install -r "$SERVER_DIR/requirements.txt"; then
    echo
    echo "ERRO no 'pip install' acima (rede/proxy/firewall?)."
    echo "      Tente manualmente para ver a mensagem completa:"
    echo "        $py -m pip install -r \"$SERVER_DIR/requirements.txt\""
    exit 1
  fi
  echo "    ambiente pronto: $VENV"
}

if [ "$MODE" = "status" ]; then
  for p in "$PORT" "$VITE_PORT"; do
    if command -v lsof >/dev/null 2>&1 && lsof -ti tcp:"$p" >/dev/null 2>&1; then echo "porta $p: EM USO"; else echo "porta $p: livre"; fi
  done; exit 0
fi
if [ "$MODE" = "stop" ]; then free_port "$PORT"; free_port "$VITE_PORT"; echo "Encerrado."; exit 0; fi

ensure_backend
PYBIN="$(venv_py)"
echo "raiz:    $ROOT"
echo "backend: $SERVER_DIR"
echo "python:  $PYBIN"

free_port "$PORT"
IP="$(lan_ip)"
export B3_DB_PATH="${B3_DB_PATH:-$SERVER_DIR/data/b3_agente.db}"

if [ "$MODE" = "prod" ]; then
  command -v npm >/dev/null 2>&1 || { echo "npm nao encontrado (Node 22+). Necessario para o build do app web."; exit 1; }
  echo "==> Build do app web"
  ( cd "$WEB_DIR" && npm install && npm run build ) || { echo "ERRO no build do web."; exit 1; }
  echo "==> Servidor unico em http://0.0.0.0:$PORT (app + API)"
  echo "    Local: http://localhost:$PORT   |   LAN: http://$IP:$PORT  (use no iPhone, mesma Wi-Fi)"
  cd "$SERVER_DIR" && exec "$PYBIN" -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
fi

# DEV
free_port "$VITE_PORT"
echo "==> Backend FastAPI (reload) em http://0.0.0.0:$PORT"
( cd "$SERVER_DIR" && exec "$PYBIN" -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --reload ) &
BACK=$!
for i in $(seq 1 40); do
  if curl -fsS "http://localhost:$PORT/api/health" >/dev/null 2>&1; then echo "    backend OK (/api/health)"; break; fi
  sleep 0.3
done
if command -v npm >/dev/null 2>&1 && [ -d "$WEB_DIR" ]; then
  echo "==> Vite (web) em http://localhost:$VITE_PORT"
  ( cd "$WEB_DIR" && ([ -d node_modules ] || npm install) && exec npm run dev -- --host ) &
  FRONT=$!
  echo; echo "  Web: http://localhost:$VITE_PORT   |   LAN: http://$IP:$VITE_PORT"
else
  FRONT=""
  echo "  (npm/web ausente: rodando so o backend em http://localhost:$PORT)"
fi
echo "  Ctrl+C encerra."
trap 'kill $BACK $FRONT 2>/dev/null || true; free_port "$PORT"; free_port "$VITE_PORT"' INT TERM
wait
