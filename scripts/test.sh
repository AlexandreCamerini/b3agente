#!/usr/bin/env bash
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVER_DIR=""
for cand in "$ROOT/server" "$ROOT" "$SCRIPT_DIR/../server"; do
  [ -f "$cand/app/main.py" ] && { SERVER_DIR="$(cd "$cand" && pwd)"; break; }
done
[ -n "$SERVER_DIR" ] || { echo "backend nao encontrado"; exit 1; }

# O venv vive no CLONE PRINCIPAL. Rodando de um worktree (.claude/worktrees/...),
# `$SERVER_DIR/.venv` não existe e as suítes caíam fora sem explicação. O
# git-common-dir aponta para o .git do clone principal em qualquer worktree —
# dele derivamos o server/ de lá. Fora de um worktree, é o mesmo diretório.
CANDIDATOS=("$SERVER_DIR/.venv/bin/python" "$SERVER_DIR/.venv/Scripts/python.exe")
COMMON="$(git -C "$ROOT" rev-parse --git-common-dir 2>/dev/null || true)"
if [ -n "$COMMON" ]; then
  case "$COMMON" in /*) ;; *) COMMON="$ROOT/$COMMON" ;; esac
  PRINCIPAL="$(cd "$(dirname "$COMMON")" 2>/dev/null && pwd || true)"
  [ -n "$PRINCIPAL" ] && CANDIDATOS+=("$PRINCIPAL/server/.venv/bin/python" "$PRINCIPAL/server/.venv/Scripts/python.exe")
fi

# `command -v pytest` não basta: um pytest QUEBRADO no PATH (stub do
# python.org sem o pacote instalado) satisfazia o teste, o script fazia exec
# nele e morria com ModuleNotFoundError — sem nunca chegar ao fallback offline.
# A checagem agora é se o pytest IMPORTA de verdade.
usa_pytest(){ "$1" -c "import pytest" >/dev/null 2>&1; }

cd "$SERVER_DIR"
for PYBIN in "${CANDIDATOS[@]}"; do
  if [ -x "$PYBIN" ] && usa_pytest "$PYBIN"; then
    [ "$PYBIN" = "${CANDIDATOS[0]}" ] || echo "usando o venv do clone principal: $PYBIN"
    exec "$PYBIN" -m pytest -q
  fi
done
if command -v pytest >/dev/null 2>&1 && pytest --version >/dev/null 2>&1; then exec pytest -q; fi

# ---------------------------------------------------------------------------
# Fallback OFFLINE (sem pytest): roda os mini-runners `__main__` das suítes
# puras (padrão do projeto desde o Radar v2; FASE 1 exige o gate mesmo em
# sandbox sem rede). Cobertura PARCIAL — para a suíte completa:
#   bash scripts/setup.sh   (instala o venv com pytest)
# ---------------------------------------------------------------------------
echo "pytest nao instalado — modo OFFLINE: mini-runners das suites puras."
PY="python3"; command -v python3 >/dev/null 2>&1 || PY="python"
RAN=0; FAILS=0; SKIPS=0
for t in tests/test_*.py; do
  [ -e "$t" ] || continue
  grep -q '__main__' "$t" || continue
  OUT="$(PYTHONPATH=. "$PY" "$t" 2>&1)"; RC=$?
  if [ "$RC" = "0" ]; then
    RAN=$((RAN+1)); printf '  [OK] %s\n' "$t"
  elif printf '%s' "$OUT" | grep -q "ModuleNotFoundError"; then
    SKIPS=$((SKIPS+1)); printf '  [PULOU] %s (dependencia ausente neste ambiente)\n' "$t"
  else
    RAN=$((RAN+1)); FAILS=$((FAILS+1))
    printf '  [X] %s\n' "$t"
    printf '%s\n' "$OUT" | grep -E "FALHOU|ERRO" | head -5 | sed 's/^/      /'
  fi
done
[ "$RAN" -gt 0 ] || { echo "nenhuma suite com mini-runner rodou"; exit 1; }
echo "$RAN suite(s) offline · $FAILS falha(s) · $SKIPS pulada(s) — cobertura parcial; rode o pytest completo antes do deploy."
[ "$FAILS" = "0" ] && exit 0 || exit 1
