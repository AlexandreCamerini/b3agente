#!/usr/bin/env bash
# =============================================================================
# integrar_gateway.sh — rode na RAIZ do repositório do BolsIA.
#
#   ./integrar_gateway.sh            # aplica
#   ./integrar_gateway.sh --dry-run  # só mostra o que faria
#   ./integrar_gateway.sh --force    # sobrescreve o llm.py já existente
#
# O QUE FAZ (mecânico e seguro):
#   1. detecta o layout do projeto (app/, src/, raiz)
#   2. escreve o módulo llm.py (ponto único de acesso ao Claude)
#   3. pluga o lifespan no FastAPI (com backup) ou mostra o patch a aplicar
#   4. confere a dependência claude-gateway no requirements.txt
#   5. MAPEIA as chamadas diretas à API que faltam migrar (arquivo:linha)
#
# O QUE NÃO FAZ (de propósito):
#   Não reescreve suas chamadas automaticamente. Trocar call-site de Python
#   com sed quebra código em silêncio. O passo 5 te dá a lista exata; você
#   (ou o Claude Code) aplica com contexto.
#
# GARANTIAS: idempotente, não-destrutivo, backup .bak antes de tocar em arquivo.
# =============================================================================
set -uo pipefail

DRY=0; FORCE=0; PKG_ARG=""
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run|-n) DRY=1 ;;
    --force|-f)   FORCE=1 ;;
    --pkg)        shift; PKG_ARG="${1:-}" ;;
    --pkg=*)      PKG_ARG="${1#--pkg=}" ;;
    -h|--help)    sed -n '2,25p' "$0"; exit 0 ;;
    *) echo "opção desconhecida: $1"; exit 1 ;;
  esac
  shift
done

if [ -t 1 ]; then
  B=$'\033[1m'; G=$'\033[32m'; Y=$'\033[33m'; R=$'\033[31m'; C=$'\033[36m'; N=$'\033[0m'
else B=""; G=""; Y=""; R=""; C=""; N=""; fi
ok()   { printf '%s✓%s %s\n' "$G" "$N" "$*"; }
warn() { printf '%s!%s %s\n' "$Y" "$N" "$*"; }
err()  { printf '%s✗%s %s\n' "$R" "$N" "$*" >&2; }
hd()   { printf '\n%s%s%s\n' "$B" "$*" "$N"; }
die()  { err "$*"; exit 1; }
run()  { if [ "$DRY" -eq 1 ]; then echo "    [dry-run] $*"; else eval "$@"; fi; }

[ "$DRY" -eq 1 ] && warn "MODO DRY-RUN — nada será alterado."

# ---------------------------------------------------------------------------
# 1. Sanidade + detecção de layout
# ---------------------------------------------------------------------------
hd "1/5 — Reconhecendo o projeto"
[ -d .git ] || warn "não parece um repositório git (sem .git). Seguindo mesmo assim."

# lixo que nunca é o pacote da app
PRUNE='-not -path "*/.*" -not -path "*/node_modules/*" -not -path "*/venv/*" \
       -not -path "*/.venv/*" -not -path "*/site-packages/*" -not -path "*/build/*" \
       -not -path "*/dist/*" -not -path "*/__pycache__/*" -not -path "*/migrations/*"'

MAIN=""
if [ -n "$PKG_ARG" ]; then
  PKG="${PKG_ARG%/}"
  [ -d "$PKG" ] || die "pasta não existe: $PKG"
else
  PKG=""
  # (a) preferir a pasta que tem o entrypoint FastAPI — funciona em qualquer profundidade
  for f in $(eval "find . -maxdepth 5 \( -name main.py -o -name app.py -o -name api.py \) $PRUNE" 2>/dev/null); do
    if grep -qE 'FastAPI\(|from fastapi' "$f" 2>/dev/null; then
      MAIN="$f"; PKG="$(dirname "$f")"; break
    fi
  done
  # (b) senão, a pasta com mais arquivos .py
  if [ -z "$PKG" ]; then
    PKG="$(eval "find . -maxdepth 5 -name '*.py' $PRUNE" 2>/dev/null \
           | sed 's#/[^/]*$##' | sort | uniq -c | sort -rn | head -1 \
           | awk '{$1=""; sub(/^ /,""); print}')"
  fi
fi
[ -n "$PKG" ] && [ -d "$PKG" ] || die "não encontrei o pacote Python.
  Informe manualmente:  $0 --pkg caminho/do/pacote
  Ex.:                  $0 --pkg server/app"
PKG="${PKG#./}"
ok "pacote detectado: ${C}${PKG}/${N}"

if [ -z "$MAIN" ]; then
  for m in "$PKG/main.py" "$PKG/app.py" "$PKG/api.py"; do
    [ -f "$m" ] && { MAIN="$m"; break; }
  done
fi
MAIN="${MAIN#./}"
[ -n "$MAIN" ] && ok "entrypoint: ${C}${MAIN}${N}" || warn "não achei main.py/app.py — passo 3 será manual"

# requirements/pyproject: sobe a partir do pacote até a raiz do repo
REQ_FILE=""; d="$PKG"
while : ; do
  [ -f "$d/requirements.txt" ] && { REQ_FILE="$d/requirements.txt"; break; }
  [ -f "$d/pyproject.toml" ]   && { REQ_FILE="$d/requirements.txt"; break; }
  [ "$d" = "." ] || [ "$d" = "/" ] || [ -z "$d" ] && break
  d="$(dirname "$d")"
done
if [ -z "$REQ_FILE" ]; then
  REQ_FILE="$(dirname "$PKG")/requirements.txt"
  [ "$(dirname "$PKG")" = "." ] && REQ_FILE="requirements.txt"
  warn "sem requirements.txt/pyproject.toml — usarei ${REQ_FILE}"
else
  ok "dependências em: ${C}${REQ_FILE}${N}"
fi

# ---------------------------------------------------------------------------
# 2. Escrever o módulo llm.py
# ---------------------------------------------------------------------------
hd "2/5 — Instalando o módulo llm.py"
LLM="${PKG}/llm.py"
if [ -f "$LLM" ] && [ "$FORCE" -eq 0 ]; then
  ok "$LLM já existe (use --force para sobrescrever)"
else
  if [ "$DRY" -eq 1 ]; then
    echo "    [dry-run] escreveria $LLM"
  else
    [ -f "$LLM" ] && cp "$LLM" "${LLM}.bak" && warn "backup: ${LLM}.bak"
    cat > "$LLM" <<'PYEOF'
"""
llm.py — ponto único de acesso ao Claude no BolsIA.

Depois deste arquivo, NENHUM outro módulo deve importar anthropic/httpx nem
montar payload da API na mão. Todo mundo chama `ask()` daqui. É o que faz o
teto de gasto e o cache valerem para a app inteira.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Any

import asyncpg
from fastapi import FastAPI, HTTPException

from claude_gateway import (
    AgentProfile,
    AppBudget,
    BudgetExceeded,
    CircuitOpen,
    ClaudeGateway,
    GovernedGateway,
    IterationCapExceeded,
    PostgresBudgetStore,
    TurnResult,
)

logger = logging.getLogger("bolsia.llm")

APP_ID = "bolsia"

# ---------------------------------------------------------------------------
# PREFIXO ESTÁVEL = o que fica em cache e corta a maior parte da conta.
# Regra: não muda entre requests -> vai no `system`.
#        muda a cada request (ticker, período, pergunta) -> vai na mensagem.
#
# GOTCHA SILENCIOSO: o mínimo de cache do claude-opus-4-8 é ~1024 tokens.
# Prompt menor NÃO é cacheado e a API não avisa. O gateway loga um WARNING.
# ---------------------------------------------------------------------------
ANALISTA = AgentProfile(
    name="analista-b3",
    model="claude-opus-4-8",
    system=(
        "Você é um operador sênior de análise técnica do mercado brasileiro (B3).\n"
        # >>> COLE AQUI todo o prompt fixo do BolsIA: metodologia, formato de
        # >>> saída, regras de risco, disclaimers, exemplos.
    ),
    default_ttl="5m",
)

# Tarefa simples não precisa de Opus. Haiku custa ~1/5.
TRIAGEM = AgentProfile(
    name="triagem",
    model="claude-haiku-4-5",
    system="Você classifica e roteia pedidos do BolsIA. Responda curto e objetivo.",
    default_ttl="5m",
)

_gw: ClaudeGateway | None = None
_gov: GovernedGateway | None = None
_pool: asyncpg.Pool | None = None


async def startup() -> None:
    global _gw, _gov, _pool
    database_url = os.environ["DATABASE_URL"]   # use a string POOLED do Neon
    os.environ["ANTHROPIC_API_KEY"]             # falha cedo se faltar

    _pool = await asyncpg.create_pool(database_url, min_size=1, max_size=5,
                                      command_timeout=30)
    _gw = ClaudeGateway(on_telemetry=_log_cost)
    _gov = GovernedGateway(_gw, PostgresBudgetStore(_pool))
    _gov.register_app(AppBudget(
        app_id=APP_ID,
        monthly_cap_usd=float(os.getenv("BOLSIA_MONTHLY_CAP_USD", "10")),
        daily_cap_usd=float(os.getenv("BOLSIA_DAILY_CAP_USD", "1")),
        hard=True,
        max_concurrency=3,
    ))
    logger.info("llm: gateway pronto (app=%s)", APP_ID)


async def shutdown() -> None:
    if _gw:
        await _gw.aclose()
    if _pool:
        await _pool.close()
    logger.info("llm: encerrado")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup()
    try:
        yield
    finally:
        await shutdown()


def _log_cost(model: str, t) -> None:
    logger.info("claude[%s] cache_hit=%.0f%% in=%d out=%d custo=$%.5f",
                model, t.cache_hit_ratio * 100, t.total_input_tokens,
                t.output_tokens, t.cost_usd)


async def ask(
    prompt: str,
    *,
    agent: AgentProfile = ANALISTA,
    max_tokens: int = 1024,
    context: list[dict[str, Any]] | None = None,
) -> TurnResult:
    """Uma pergunta ao Claude, com teto, cache e disjuntor aplicados."""
    if _gov is None:
        raise RuntimeError("llm.startup() não chamado — registre o lifespan no FastAPI.")
    try:
        return await _gov.complete(APP_ID, agent, prompt,
                                   max_tokens=max_tokens, context=context)
    except BudgetExceeded as e:
        logger.warning("teto estourado: %s", e)
        raise HTTPException(402, "Limite de uso do período atingido.") from e
    except CircuitOpen as e:
        logger.error("circuito aberto: %s", e)
        raise HTTPException(503, "Serviço de análise temporariamente indisponível.",
                            headers={"Retry-After": str(int(e.reopen_in) + 1)}) from e
    except IterationCapExceeded as e:
        logger.error("loop de agente: %s", e)
        raise HTTPException(500, "A análise não convergiu.") from e


async def ask_text(prompt: str, **kw) -> str:
    return (await ask(prompt, **kw)).text
PYEOF
    ok "escrito: ${C}${LLM}${N}"
  fi
fi

# ---------------------------------------------------------------------------
# 3. Plugar o lifespan no FastAPI
# ---------------------------------------------------------------------------
hd "3/5 — Conectando o lifespan ao FastAPI"
# llm.py fica AO LADO do main.py. Com __init__.py, o import relativo é o único
# que funciona independentemente de onde está a raiz de execução (o pacote pode
# ser server/app mas rodar com WORKDIR em server/ -> "server.app.llm" quebraria).
IMPORT_PATH="$(echo "${PKG}" | sed 's#^\./##; s#/#.#g')"
[ "$IMPORT_PATH" = "." ] && IMPORT_PATH=""
LLM_IMPORT="${IMPORT_PATH:+${IMPORT_PATH}.}llm"     # caminho absoluto (referência)
if [ -f "$PKG/__init__.py" ]; then
  IMPORT_STMT="from .llm import lifespan"
  ASK_IMPORT="from .llm import ask_text"
else
  IMPORT_STMT="from llm import lifespan"
  ASK_IMPORT="from llm import ask_text"
  warn "sem __init__.py em ${PKG}/ — usando import simples; confira se resolve no seu runtime"
fi

if [ -z "$MAIN" ]; then
  warn "sem entrypoint detectado. Adicione à mão onde o FastAPI é criado:"
  echo "    ${IMPORT_STMT}"
  echo "    app = FastAPI(lifespan=lifespan)"
elif grep -q "lifespan" "$MAIN"; then
  ok "$MAIN já menciona 'lifespan' — revise se aponta para o do llm.py:"
  grep -n "lifespan" "$MAIN" | head -5 | sed 's/^/    /'
  warn "se você já tem um lifespan próprio, chame llm.startup()/llm.shutdown() dentro dele."
elif grep -qE '^\s*app\s*=\s*FastAPI\(' "$MAIN"; then
  if [ "$DRY" -eq 1 ]; then
    echo "    [dry-run] adicionaria import e lifespan em $MAIN"
  else
    cp "$MAIN" "${MAIN}.bak"
    python3 - "$MAIN" "$IMPORT_STMT" <<'PY'
import re, sys
path, stmt = sys.argv[1], sys.argv[2]
src = open(path, encoding="utf-8").read()
imp = stmt + "\n"
if imp not in src:
    lines = src.splitlines(keepends=True)
    idx = 0
    for i, l in enumerate(lines):
        if l.startswith(("import ", "from ")):
            idx = i + 1
    lines.insert(idx, imp)
    src = "".join(lines)
src = re.sub(r'(^\s*app\s*=\s*FastAPI\()\s*\)', r'\1lifespan=lifespan)', src, count=1, flags=re.M)
src = re.sub(r'(^\s*app\s*=\s*FastAPI\()(?!lifespan)(\s*\w)', r'\1lifespan=lifespan, \2', src, count=1, flags=re.M)
open(path, "w", encoding="utf-8").write(src)
PY
    if python3 -c "import ast,sys; ast.parse(open('$MAIN',encoding='utf-8').read())" 2>/dev/null; then
      ok "lifespan conectado em $MAIN (backup: ${MAIN}.bak)"
      grep -n "lifespan" "$MAIN" | head -3 | sed 's/^/    /'
    else
      mv "${MAIN}.bak" "$MAIN"
      warn "patch geraria código inválido — revertido. Faça à mão:"
      echo "    ${IMPORT_STMT}"
      echo "    app = FastAPI(lifespan=lifespan)"
    fi
  fi
else
  warn "não achei 'app = FastAPI(' em $MAIN. Adicione à mão:"
  echo "    ${IMPORT_STMT}"
  echo "    app = FastAPI(lifespan=lifespan)"
fi

# ---------------------------------------------------------------------------
# 4. Dependências
# ---------------------------------------------------------------------------
hd "4/5 — Conferindo dependências"
[ "$DRY" -eq 1 ] || touch "$REQ_FILE"
grep -q "claude-gateway" "$REQ_FILE" 2>/dev/null \
  && ok "claude-gateway presente" \
  || warn "claude-gateway AUSENTE em ${REQ_FILE} — rode o setup.sh (passo 2) ou adicione a linha git pinada"
grep -qi "^asyncpg" "$REQ_FILE" 2>/dev/null \
  && ok "asyncpg presente" \
  || { run "printf 'asyncpg>=0.29\n' >> '$REQ_FILE'"; ok "asyncpg adicionado a ${REQ_FILE}"; }

# ---------------------------------------------------------------------------
# 5. Mapear chamadas diretas que faltam migrar
# ---------------------------------------------------------------------------
hd "5/5 — Chamadas diretas à API (migrar para ask())"
PAT='anthropic|messages\.create|api\.anthropic\.com|ANTHROPIC_API_KEY'
HITS="$(grep -rnE "$PAT" --include='*.py' . 2>/dev/null \
        | grep -v "/llm.py:" | grep -v '\.bak:' | grep -v '/\.venv/' || true)"

if [ -z "$HITS" ]; then
  ok "nenhuma chamada direta encontrada — ou já migrou, ou o padrão é outro."
else
  COUNT="$(printf '%s\n' "$HITS" | wc -l | tr -d ' ')"
  warn "${COUNT} ponto(s) para migrar:"
  printf '%s\n' "$HITS" | sed 's/^/    /'
  cat <<EOF

  ${B}Como migrar cada um:${N}
    ANTES:  resp = client.messages.create(model=..., system=PROMPT, messages=[...])
            texto = resp.content[0].text
    DEPOIS: ${ASK_IMPORT}
            texto = await ask_text(f"Analise {ticker} no diário")

  O ${B}system/modelo saem do call-site${N} e vão para o AgentProfile em ${LLM}.
  Isso não é estética: prompt remontado a cada chamada tem prefixo diferente
  toda vez e ${B}o cache nunca acerta${N}.
EOF
fi

# ---------------------------------------------------------------------------
hd "Próximos passos"
cat <<EOF
  1. Abra ${C}${LLM}${N} e cole o prompt fixo do BolsIA em ANALISTA.system
  2. Migre os pontos listados acima (ou peça ao Claude Code)
  3. Teste local com ANTHROPIC_API_KEY e DATABASE_URL setados:

     python -c "
import asyncio, ${LLM_IMPORT} as llm
async def t():
    await llm.startup()
    r = await llm.ask('ping')
    print(r.text[:60], '| custo:', r.telemetry.cost_usd, '| cache:', r.telemetry.cache_hit_ratio)
    await llm.shutdown()
asyncio.run(t())"

     ${B}2ª chamada em até 5 min deve mostrar cache alto.${N} Se ficar 0 nas duas,
     o system está abaixo do mínimo — procure o WARNING no log.
  4. Commit e deploy: ${C}./setup.sh 4${N}
EOF
[ "$DRY" -eq 1 ] && warn "DRY-RUN: nada foi alterado. Rode sem --dry-run para aplicar."
exit 0
