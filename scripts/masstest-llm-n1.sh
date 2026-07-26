#!/usr/bin/env bash
# Teste massivo do agente N1 (Radar deep): topN 3 × 2 modos. Sem flags para colar.
# Usa BOLSIA_API_KEY do ambiente; provider/model têm default (Anthropic/opus-4-8).
set -euo pipefail
cd "$(dirname "$0")/.."
: "${BOLSIA_API_KEY:?exporte a chave antes:  read -rs BOLSIA_API_KEY && export BOLSIA_API_KEY}"
export BOLSIA_PROVIDER="${BOLSIA_PROVIDER:-anthropic}"
export BOLSIA_MODEL="${BOLSIA_MODEL:-claude-opus-4-8}"
exec python3 scripts/masstest-agentes-llm-n1.py --topn 3
