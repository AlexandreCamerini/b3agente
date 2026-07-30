#!/usr/bin/env bash
# Teste MÍNIMO do agente LLM: 1 análise (PETR4/estudo) = 1 chamada.
# Sem flags para colar — evita o "merge de paste" do terminal.
# Usa BOLSIA_API_KEY do ambiente; provider/model têm default (Anthropic/opus-4-8).
set -euo pipefail
cd "$(dirname "$0")/.."
: "${BOLSIA_API_KEY:?exporte a chave antes:  read -rs BOLSIA_API_KEY && export BOLSIA_API_KEY}"
export BOLSIA_PROVIDER="${BOLSIA_PROVIDER:-anthropic}"
export BOLSIA_MODEL="${BOLSIA_MODEL:-claude-sonnet-5}"
exec python3 scripts/masstest-agentes-llm.py PETR4 --modes estudo --limit 1
