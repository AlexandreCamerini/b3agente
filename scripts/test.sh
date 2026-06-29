#!/usr/bin/env bash
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVER_DIR=""
for cand in "$ROOT/server" "$ROOT" "$SCRIPT_DIR/../server"; do
  [ -f "$cand/app/main.py" ] && { SERVER_DIR="$(cd "$cand" && pwd)"; break; }
done
[ -n "$SERVER_DIR" ] || { echo "backend nao encontrado"; exit 1; }
PYBIN="$SERVER_DIR/.venv/bin/python"; [ -x "$PYBIN" ] || PYBIN="$SERVER_DIR/.venv/Scripts/python.exe"
cd "$SERVER_DIR"
if [ -x "$PYBIN" ]; then exec "$PYBIN" -m pytest -q
elif command -v pytest >/dev/null 2>&1; then exec pytest -q
else echo "pytest nao instalado. Rode: bash scripts/setup.sh"; exit 1; fi
