#!/usr/bin/env bash
# Etapa 5 do `fechar-fase-24.sh`, isolada: o compilador NL->DSL com LLM REAL.
#
# `llm._call_llm` está substituído em 100% dos testes automatizados. Nunca um
# modelo de verdade leu o `system` que se monta em runtime do `inputSchema` de
# `create_setup`. É isto que decide se MAX_TOKENS_COMPILADOR basta.
#
# NÃO grava setup nenhum: a rota chamada é o dry-run (`confirm=false`).
# Custa 1 chamada de LLM + 2 tools do teto de 2.000/dia.
# Nenhum segredo toca o disco: vem do Railway para variáveis deste processo.
#
#   bash scripts/testar-compilador-llm.sh [TICKER]
set -euo pipefail
cd "$(dirname "$0")/.."
TICKER="${1:-PETR4}"

command -v railway >/dev/null 2>&1 || { echo "railway CLI não encontrada" >&2; exit 1; }
railway whoami >/dev/null 2>&1 || { echo "railway CLI não autenticada (railway login)" >&2; exit 1; }

VARS=$(railway variables --json --environment production)
_v() { printf '%s' "$VARS" | python3 -c 'import json,sys;print(json.load(sys.stdin).get(sys.argv[1],""))' "$1"; }
export MCP_CLIENT_ID="$(_v MCP_CLIENT_ID)"
export MCP_CLIENT_SECRET="$(_v MCP_CLIENT_SECRET)"
export MCP_URL="$(_v MCP_URL)"
export B3_MANAGED_LLM_KEY="$(_v B3_MANAGED_LLM_KEY)"
export B3_MANAGED_LLM_MODEL="$(_v B3_MANAGED_LLM_MODEL)"
export B3_MANAGED_LLM_PROVIDER="$(_v B3_MANAGED_LLM_PROVIDER)"
VARS=""

[ -n "$MCP_CLIENT_SECRET" ] || { echo "MCP_CLIENT_SECRET ausente em production" >&2; exit 1; }
[ -n "$B3_MANAGED_LLM_KEY" ] || { echo "B3_MANAGED_LLM_KEY ausente em production" >&2; exit 1; }
echo "  IA gerenciada: ${B3_MANAGED_LLM_PROVIDER:-?}/${B3_MANAGED_LLM_MODEL:-?} (chave não exibida)"

TMPD=$(mktemp -d)
trap 'rm -rf "$TMPD"' EXIT
B3_DB_PATH="$TMPD/fase24.db" PYTHONPATH="$PWD/server" server/.venv/bin/python - "$TICKER" <<'PY'
import sys, time
from fastapi.testclient import TestClient
ticker = sys.argv[1]
from app import main

c = TestClient(main.app)
r = c.post("/api/auth/register", json={"email": "fase24@local.test", "password": "senhaboa123"})
r.raise_for_status()
h = {"authorization": "Bearer " + r.json()["token"]}

me = c.get("/api/auth/me", headers=h).json()
perms = (me.get("user") or me).get("permissions") or []
print(f"  permissões da conta de teste: {perms}")
if "opcoes.criar_setup" not in perms:
    print("  FALTA opcoes.criar_setup — a rota responderia 403"); sys.exit(2)

descricao = (f"Quero um setup para {ticker}: avisar quando o RSI de 14 ficar abaixo "
             f"de 30 e o fechamento estiver acima da média de 200, por dois pregões "
             f"seguidos.")
print(f"\n  descrição enviada:\n    {descricao}\n")

t0 = time.perf_counter()
r = c.post("/api/options/mcp/setups/compilar",
           json={"ticker": ticker, "descricao": descricao}, headers=h)
dt = time.perf_counter() - t0
print(f"  HTTP {r.status_code} em {dt:.1f}s")

try:
    d = r.json()
except Exception:
    print("  corpo não-JSON:", r.text[:400]); sys.exit(1)

if r.status_code != 200:
    det = d.get("detail") if isinstance(d, dict) else d
    print(f"\n  === NÃO COMPILOU ===")
    print(f"  {det if not isinstance(det, dict) else ''}")
    if isinstance(det, dict):
        for k in ("code", "message", "action", "faltando", "problems"):
            if det.get(k) is not None:
                print(f"    {k}: {det[k]}")
        if det.get("cru") is not None:
            print(f"    cru (o que a IA respondeu):\n{det['cru'][:1500]}")
        if det.get("code") == "compilacao_invalida":
            print("\n  LEITURA: `cru` truncado no meio do JSON = MAX_TOKENS_COMPILADOR curto.")
        if det.get("code") == "setup_invalido":
            print("\n  LEITURA: o modelo compilou; quem recusou foi a SEMÂNTICA do serviço.")
    sys.exit(1)

s = d.get("setup") or {}
print("\n  === COMPILOU ===")
print(f"    status: {d.get('status')}   (dry_run = NADA foi gravado)")
print(f"    name: {s.get('name')!r}")
print(f"    ticker: {s.get('ticker')!r}")
print(f"    logic: {s.get('logic')}   consecutive_days: {s.get('consecutive_days')}")
print(f"    conditions ({len(s.get('conditions') or [])}):")
for cond in (s.get("conditions") or []):
    print(f"      - {cond}")
orig = d.get("descricao")
print(f"\n    description preservada byte a byte: {s.get('description') == descricao}")
if s.get("description") != descricao:
    print(f"      ATENÇÃO — a IA reescreveu: {s.get('description')!r}")

b = d.get("backtest") or {}
print(f"\n    backtest:")
print(f"      período: {b.get('periodo')}")
print(f"      disparos: {b.get('disparos')}  por 100 pregões: {b.get('disparos_por_100_pregoes_avaliaveis')}")
for passo in ("d+5", "d+10"):
    print(f"      {passo}: {(b.get('retorno_apos_disparo') or {}).get(passo)}")
print(f"\n    pregão: {d.get('pregao')}   atraso: {d.get('atraso')}")
PY
