#!/usr/bin/env bash
# =============================================================================
# corrigir.sh — conserta o estrago e diagnostica o que o BolsIA já tem.
# Rode na RAIZ do b3-agente.
#
#   ./corrigir.sh            # corrige + diagnostica
#   ./corrigir.sh --reverter # desfaz TUDO (volta aos .bak) e só diagnostica
# =============================================================================
set -uo pipefail

REVERTER=0
[ "${1:-}" = "--reverter" ] && REVERTER=1

if [ -t 1 ]; then
  B=$'\033[1m'; G=$'\033[32m'; Y=$'\033[33m'; R=$'\033[31m'; C=$'\033[36m'; N=$'\033[0m'
else B=""; G=""; Y=""; R=""; C=""; N=""; fi
ok()   { printf '%s✓%s %s\n' "$G" "$N" "$*"; }
warn() { printf '%s!%s %s\n' "$Y" "$N" "$*"; }
err()  { printf '%s✗%s %s\n' "$R" "$N" "$*" >&2; }
hd()   { printf '\n%s%s%s\n' "$B" "$*" "$N"; }

PKG="server/app"
MAIN="${PKG}/main.py"
[ -f "$MAIN" ] || { err "não achei ${MAIN} — rode na raiz do b3-agente"; exit 1; }

# ---------------------------------------------------------------------------
if [ "$REVERTER" -eq 1 ]; then
  hd "REVERTENDO tudo que os scripts alteraram"
  for f in "$MAIN" "${PKG}/llm.py"; do
    if [ -f "${f}.bak" ]; then
      mv "${f}.bak" "$f"; ok "restaurado: $f"
    fi
  done
  [ -f "${PKG}/llm.py" ] && [ ! -f "${PKG}/llm.py.bak" ] && {
    mv "${PKG}/llm.py" "${PKG}/llm.py.novo"
    ok "llm.py movido para llm.py.novo (não apaguei nada)"
  }
  warn "revise à mão: linha 'asyncpg' e 'claude-gateway' nos requirements."
else
  # -------------------------------------------------------------------------
  hd "1 — Corrigindo a posição do import em ${MAIN}"
  python3 - "$MAIN" <<'PY'
import re, sys
p = sys.argv[1]
src = open(p, encoding="utf-8").read()
lines = src.splitlines(keepends=True)

IMP = "from .llm import lifespan\n"

# remove o import onde quer que ele esteja hoje
lines = [l for l in lines if l.strip() != IMP.strip()]

# acha a linha do 'app = FastAPI('
idx = None
for i, l in enumerate(lines):
    if re.match(r'^\s*app\s*=\s*FastAPI\(', l):
        idx = i
        break

if idx is None:
    print("SEM_FASTAPI")
    sys.exit(0)

# insere IMEDIATAMENTE antes do uso -> definição sempre precede o uso
lines.insert(idx, IMP)
open(p, "w", encoding="utf-8").write("".join(lines))
print("OK")
PY
  RES=$?
  if [ $RES -eq 0 ]; then
    if python3 -c "import ast;ast.parse(open('$MAIN',encoding='utf-8').read())" 2>/dev/null; then
      ok "import reposicionado logo antes do uso"
      grep -n "from .llm import lifespan\|app = FastAPI" "$MAIN" | head -4 | sed 's/^/    /'
    else
      err "AST inválido após a correção — restaure: mv ${MAIN}.bak ${MAIN}"
    fi
  fi

  # -------------------------------------------------------------------------
  hd "2 — Alinhando as dependências"
  ROOT_REQ="requirements.txt"
  SRV_REQ="server/requirements.txt"
  DEP="$(grep -h 'claude-gateway' "$ROOT_REQ" "$SRV_REQ" 2>/dev/null | head -1)"
  if [ -z "$DEP" ]; then
    warn "claude-gateway não encontrado em nenhum requirements"
  elif grep -q 'claude-gateway' "$SRV_REQ" 2>/dev/null; then
    ok "claude-gateway já está em ${SRV_REQ} (o que o app usa)"
  else
    printf '%s\n' "$DEP" >> "$SRV_REQ"
    ok "claude-gateway copiado para ${SRV_REQ}"
    warn "existe cópia em ${ROOT_REQ} — decida qual é a fonte de verdade e remova a outra"
  fi
fi

# ---------------------------------------------------------------------------
hd "3 — DIAGNÓSTICO: o que o BolsIA já tem hoje"

# só código de produção: fora worktrees, testes, venv, node_modules
SCAN='--include=*.py'
EXCL="grep -v '/\.claude/' | grep -v '/tests\?/' | grep -v '/\.venv/' | grep -v '\.bak' | grep -v '/node_modules/'"

echo ""
echo "  ${B}a) Onde a API da Anthropic é REALMENTE chamada:${N}"
HITS="$(eval "grep -rn $SCAN -E 'Anthropic\(|messages\.create|api\.anthropic\.com' . 2>/dev/null | $EXCL" || true)"
if [ -n "$HITS" ]; then
  printf '%s\n' "$HITS" | sed 's/^/      /'
else
  echo "      (nada encontrado — a chamada pode estar via SDK genérico ou httpx)"
  eval "grep -rn $SCAN -E 'httpx\.(post|AsyncClient)|requests\.post' . 2>/dev/null | $EXCL" | head -8 | sed 's/^/      /'
fi

echo ""
echo "  ${B}b) Camada de abstração de provider (o ponto certo de integração):${N}"
eval "grep -rln $SCAN -E 'provider|managed' . 2>/dev/null | $EXCL" | head -10 | sed 's/^/      /'

echo ""
echo "  ${B}c) Controle de custo/uso que JÁ existe:${N}"
eval "grep -rn $SCAN -E 'record_usage|def .*usage|budget|finops|custo_usd|cost_usd' . 2>/dev/null | $EXCL" | head -12 | sed 's/^/      /'

echo ""
echo "  ${B}d) Cache de prompt já implementado?${N}"
eval "grep -rn $SCAN -E 'cache_control|ephemeral|prompt_cach' . 2>/dev/null | $EXCL" | head -8 | sed 's/^/      /' \
  || echo "      (nenhum)"

hd "Próximo passo"
cat <<EOF
  O BolsIA já tem camada de provider e registro de uso. Antes de plugar o
  gateway, precisamos decidir ONDE ele entra — e o candidato é a função que
  faz a chamada à Anthropic dentro da sua camada de provider, NÃO os call-sites.

  Mande para o Claude o conteúdo dos arquivos que apareceram em (a) e (b).
  Com eles, dá para dizer se o gateway:
    (i)  substitui a camada existente,
    (ii) entra por baixo dela (só o provider "anthropic"), ou
    (iii) é desnecessário porque você já tem o equivalente.
EOF
