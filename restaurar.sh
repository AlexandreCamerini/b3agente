#!/usr/bin/env bash
# =============================================================================
# restaurar.sh — desfaz o estrago: devolve o llm.py e o main.py originais.
# Rode na RAIZ do b3-agente.  NADA é apagado — só renomeado.
#
#   ./restaurar.sh --check   # só mostra o que faria
#   ./restaurar.sh           # restaura
# =============================================================================
set -uo pipefail

CHECK=0
[ "${1:-}" = "--check" ] && CHECK=1

if [ -t 1 ]; then
  B=$'\033[1m'; G=$'\033[32m'; Y=$'\033[33m'; R=$'\033[31m'; C=$'\033[36m'; N=$'\033[0m'
else B=""; G=""; Y=""; R=""; C=""; N=""; fi
ok()   { printf '%s✓%s %s\n' "$G" "$N" "$*"; }
warn() { printf '%s!%s %s\n' "$Y" "$N" "$*"; }
err()  { printf '%s✗%s %s\n' "$R" "$N" "$*" >&2; }
hd()   { printf '\n%s%s%s\n' "$B" "$*" "$N"; }
act()  { if [ "$CHECK" -eq 1 ]; then echo "    [check] $*"; else eval "$@"; fi; }

P="server/app"
[ -d "$P" ] || { err "rode na raiz do b3-agente"; exit 1; }

[ "$CHECK" -eq 1 ] && warn "MODO CHECK — nada será alterado."

# ---------------------------------------------------------------------------
hd "1 — Conferindo os backups"
for f in "$P/llm.py.bak" "$P/main.py.bak"; do
  if [ -f "$f" ]; then
    ok "$f ($(wc -l < "$f" | tr -d ' ') linhas)"
  else
    err "$f NÃO existe"
  fi
done

# sanidade: o llm.py.bak é mesmo o original do BolsIA?
if [ -f "$P/llm.py.bak" ]; then
  if grep -q "DEEP_FORMAT\|def .*llm\|PROMPT" "$P/llm.py.bak" 2>/dev/null; then
    ok "llm.py.bak tem cara de módulo original do BolsIA (bom sinal)"
  else
    warn "llm.py.bak não tem os marcadores esperados — CONFIRA antes de seguir:"
    head -20 "$P/llm.py.bak" | sed 's/^/      /'
  fi
fi
# sanidade: o llm.py atual é o meu template?
if grep -q "claude_gateway\|GovernedGateway" "$P/llm.py" 2>/dev/null; then
  ok "llm.py atual é o template do gateway (será preservado com outro nome)"
else
  warn "llm.py atual NÃO parece o template do gateway — pare e confira à mão."
  [ "$CHECK" -eq 1 ] || exit 1
fi

# ---------------------------------------------------------------------------
hd "2 — Preservando o template do gateway"
if [ -f "$P/llm.py" ]; then
  act "mv '$P/llm.py' 'gateway_template.py.txt'"
  ok "template salvo em ./gateway_template.py.txt (fora do pacote, não é importado)"
fi

hd "3 — Restaurando o llm.py do BolsIA"
if [ -f "$P/llm.py.bak" ]; then
  act "mv '$P/llm.py.bak' '$P/llm.py'"
  ok "$P/llm.py restaurado"
else
  err "sem backup — recupere com: git checkout -- $P/llm.py"
fi

hd "4 — Restaurando o main.py do BolsIA"
if [ -f "$P/main.py.bak" ]; then
  act "mv '$P/main.py.bak' '$P/main.py'"
  ok "$P/main.py restaurado (sem o lifespan do gateway)"
else
  warn "sem main.py.bak — removendo só as linhas que injetei:"
  if [ "$CHECK" -eq 0 ]; then
    python3 - "$P/main.py" <<'PY'
import re, sys
p = sys.argv[1]
src = open(p, encoding="utf-8").read()
src = "".join(l for l in src.splitlines(keepends=True)
              if l.strip() != "from .llm import lifespan")
src = src.replace("FastAPI(lifespan=lifespan, ", "FastAPI(")
src = src.replace("FastAPI(lifespan=lifespan)", "FastAPI()")
open(p, "w", encoding="utf-8").write(src)
PY
    python3 -c "import ast;ast.parse(open('$P/main.py',encoding='utf-8').read())" \
      && ok "linhas do gateway removidas de main.py" \
      || err "main.py inválido — use: git checkout -- $P/main.py"
  fi
fi

# ---------------------------------------------------------------------------
hd "5 — Dependências que eu adicionei (decida se remove)"
for f in requirements.txt server/requirements.txt; do
  [ -f "$f" ] || continue
  if grep -qE 'claude-gateway|^asyncpg' "$f" 2>/dev/null; then
    warn "$f contém:"
    grep -nE 'claude-gateway|^asyncpg' "$f" | sed 's/^/      /'
  fi
done
echo "    (deixar não quebra nada; só instala pacote sem uso. Remova quando decidirmos.)"

# ---------------------------------------------------------------------------
hd "6 — Sanidade final"
if [ "$CHECK" -eq 0 ]; then
  for f in "$P/llm.py" "$P/main.py"; do
    python3 -c "import ast;ast.parse(open('$f',encoding='utf-8').read())" 2>/dev/null \
      && ok "$f: sintaxe OK" || err "$f: SINTAXE INVÁLIDA"
  done
  echo ""
  echo "    Confirme com git que voltou ao estado original:"
  echo "      ${C}git status${N}"
  echo "      ${C}git diff --stat${N}"
fi

hd "Agora sim: o que preciso ver"
cat <<'EOF'
  O server/app/llm.py restaurado é a camada de LLM do BolsIA — é ALI que o
  gateway pode (ou não) entrar. Mande para o Claude:

    - server/app/llm.py     (o arquivo inteiro, ou as funções que chamam a API)
    - server/app/managed.py (a lógica de chave gerenciada vs. BYOK)

  Sem esses dois, qualquer proposta minha é chute.
EOF
