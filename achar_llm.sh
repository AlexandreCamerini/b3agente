#!/usr/bin/env bash
# achar_llm.sh — encontra ONDE o BolsIA realmente chama o LLM.
# Rode na raiz do b3-agente.
set -uo pipefail

if [ -t 1 ]; then B=$'\033[1m'; C=$'\033[36m'; N=$'\033[0m'; else B=""; C=""; N=""; fi
hd() { printf '\n%s%s%s\n' "$B" "$*" "$N"; }

# produção apenas: sem worktrees, testes, venv, backups
F() { grep -rn --include='*.py' -E "$1" server/app 2>/dev/null \
      | grep -v '\.bak' | grep -v '/llm\.py:' | head -"${2:-10}"; }

hd "1 — Inventário de server/app (por tamanho)"
ls -lS server/app/*.py 2>/dev/null | awk '{printf "    %6s  %s\n", $5, $9}' | head -25

hd "2 — Endpoints HTTP de LLM (v1/messages, chat/completions)"
F 'v1/messages|chat/completions|/complete|anthropic-version|x-api-key' 12 | sed 's/^/    /'

hd "3 — Uso de baseUrl / apiKey vindos da config"
F 'baseUrl|base_url|apiKey|api_key' 15 | sed 's/^/    /'

hd "4 — record_usage / contabilização de tokens"
F 'record_usage|input_tokens|output_tokens|prompt_tokens|tokens_' 12 | sed 's/^/    /'

hd "5 — Onde o prompt do analista é montado"
F 'system|prompt|PROMPT' 15 | sed 's/^/    /'

hd "6 — Chamadas HTTP de saída (fora yahoo)"
grep -rn --include='*.py' -E 'httpx\.(post|AsyncClient)|requests\.post|\.post\(' server/app 2>/dev/null \
  | grep -v 'yahoo' | grep -v '\.bak' | head -12 | sed 's/^/    /'

hd "O que mandar para o Claude"
echo "    O arquivo que aparecer nos blocos 2/3/4 é o ponto de integração."
echo "    Cole o conteúdo dele (ou só as funções que fazem a chamada)."
