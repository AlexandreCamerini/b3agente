#!/usr/bin/env bash
# Por que a LEITURA DO ATIVO tem campos vazios? (achado ao vivo, 2026-09-11)
#
# Imprime o `behavior` CRU que o serviço MCP devolve, o frescor medido e a
# inferência de quantos pregões a série tem. Não escreve nada, não publica
# nada, não grava segredo: as credenciais vêm do Railway para variáveis deste
# processo e morrem com ele. Custa 2 chamadas do teto de 2.000/dia.
#
#   bash scripts/diagnostico-leitura-opcoes.sh [TICKER]
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
VARS=""

[ -n "$MCP_CLIENT_ID" ] && [ -n "$MCP_CLIENT_SECRET" ] || { echo "credenciais MCP ausentes em production" >&2; exit 1; }

PYTHONPATH="$PWD/server" server/.venv/bin/python - "$TICKER" <<'PY'
import asyncio, json, sys
from app import mcp_client

ticker = sys.argv[1]

async def main():
    prop, _ = await mcp_client.call_tool("propose_option_setups", {"ticker": ticker})
    fres, _ = await mcp_client.call_tool("check_data_freshness", {})
    return prop, fres

prop, fres = asyncio.run(main())
b = prop.get("behavior") or {}

print(f"\n=== behavior CRU de {ticker} ===")
print(json.dumps(b, indent=2, ensure_ascii=False, default=str))

print("\n=== o que veio e o que faltou ===")
for campo in ("close", "rsi14", "sma21", "sma63", "distance_from_sma21_pct",
              "distance_from_sma63_pct", "trend", "hv21", "hv63",
              "range_63_sessions", "change_21_sessions_pct"):
    v = b.get(campo)
    vazio = v is None or (isinstance(v, dict) and all(x is None for x in v.values()))
    print(f"  {'FALTOU ' if vazio else 'veio   '} {campo}: {v!r}")

print("\n=== inferência sobre a série de candles ===")
tem21 = b.get("sma21") is not None
tem63 = b.get("sma63") is not None
if tem21 and not tem63:
    print("  entre 22 e 62 pregões: fecha a janela de 21 e NÃO fecha a de 63.")
    print("  => sma63, distance_from_sma63_pct, trend e range_63_sessions não")
    print("     têm de onde sair. Não é defeito do Boris nem do MCP: é o")
    print("     tamanho da série que o MyData entrega.")
elif tem63:
    print("  63+ pregões. Se algum campo de 63 faltou mesmo assim, o problema")
    print("  é do cálculo no serviço, não do tamanho da série.")
else:
    print("  menos de 22 pregões — série curta demais para quase tudo.")

if b.get("hv21") is None:
    print("\n  hv21/hv63 são colunas DIRETAS do candle do MyData (o MCP não as")
    print("  calcula: `DIRETOS` em setups.py mapeia hv21->hv21). Nulas aqui")
    print("  significa que o MyData não as populou para este ativo.")

print(f"\n=== pregão e frescor ===")
print(f"  trading_date do behavior: {b.get('trading_date')}")
print(f"  underlying_price: {prop.get('underlying_price')}")
# Frescor INTEIRO: o corte de 1200 chars escondia justamente a classe
# `negociacao_b3`, que e a que decide se a cotacao esta velha (2026-09-11).
classes = fres.get("classes") or []
print(f"  warning global: {fres.get('warning')!r}")
for c in classes:
    nome = c.get("class") or c.get("classe")
    idade, sla = c.get("age_hours"), c.get("sla_hours")
    marca = "  <<< a que manda na cotacao" if nome == "negociacao_b3" else ""
    print(f"  - {nome}: {c.get('status')} | idade {idade}h | SLA {sla}h{marca}")
    if c.get("last_failure"):
        print(f"      ultima falha: {str(c['last_failure'])[:300]}")
PY
