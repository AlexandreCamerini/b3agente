#!/usr/bin/env bash
# executar.sh — BolsIA (b3-agente) · execução em UM comando.
#
#   bash executar.sh              # DEV: backend :8787 + Vite :5173 (auto-instala se faltar)
#   bash executar.sh --prod       # PROD local: build do web + 1 servidor único :8787
#   bash executar.sh --stop       # encerra e libera as portas
#   bash executar.sh --status     # o que está no ar
#   bash executar.sh --testes     # só roda as suítes (backend + web) e sai
#                                 (sem pytest: fallback offline com os mini-runners)
#
# Fachada fina sobre scripts/run.sh (que já cuida de venv, portas e modos) —
# adiciona apenas o modo --testes e o lembrete do endereço para o iPhone.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]:-$0}")"

say(){ printf "\n\033[1m== %s ==\033[0m\n" "$*"; }
die(){ printf "  \033[31m[X]\033[0m %s\n" "$*" >&2; exit 1; }

if [ "${1:-}" = "--testes" ]; then
  say "Suítes do backend"
  bash scripts/test.sh || die "backend com falhas"
  say "Suítes web"
  RC=0
  for t in web/tests/*.mjs; do
    [ -e "$t" ] || continue
    if (cd web && node "${t#web/}" >/dev/null 2>&1); then printf "  \033[32m[OK]\033[0m %s\n" "$t"; else printf "  \033[31m[X]\033[0m %s\n" "$t"; RC=1; fi
  done
  exit "$RC"
fi

[ -f scripts/run.sh ] || die "scripts/run.sh não encontrado — rode na raiz do projeto"
if [ -z "${1:-}" ]; then
  IP="$(ipconfig getifaddr en0 2>/dev/null || hostname -I 2>/dev/null | awk '{print $1}')"
  [ -n "${IP:-}" ] && echo "Dica (iPhone na mesma rede): Config → endereço do servidor → http://$IP:8787"
fi
exec bash scripts/run.sh "$@"
