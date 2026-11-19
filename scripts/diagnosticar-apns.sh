#!/usr/bin/env bash
# diagnosticar-apns.sh — Boris+ · confere a credencial do push (APNs) de ponta a ponta.
#
#   bash scripts/diagnosticar-apns.sh                       # lê as variáveis do Railway (serviço linkado)
#   bash scripts/diagnosticar-apns.sh --environment staging # outro ambiente do Railway
#   bash scripts/diagnosticar-apns.sh --testar-locais         # qual .p8 de P8_DIR a Apple aceita (sem Railway)
#   P8_DIR=/outra/pasta bash scripts/diagnosticar-apns.sh   # .p8 locais fora de /Users/acamerini/p8
#
# Lê APNS_* (e SIWA_* para comparação) via `railway variables --json` e entrega
# por PIPE ao scripts/diagnosticar_apns.py: nada de segredo em argumento, arquivo
# ou tela. Não altera nada no Railway nem no portal Apple; a prova na Apple usa
# um token de aparelho falso, então nenhum push é entregue.
#
# Precisa: Railway CLI logado e linkado ao serviço do backend (`railway link`),
# server/.venv com as requirements (PyJWT[crypto], httpx[http2]) e rede.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.."
die(){ printf "  \033[31m[X]\033[0m %s\n" "$*" >&2; exit 1; }

PY="server/.venv/bin/python"
[ -x "$PY" ] || die "server/.venv ausente — crie com: python3.12 -m venv server/.venv && server/.venv/bin/python -m pip install -r server/requirements.txt"
"$PY" -c "import jwt, httpx, h2, cryptography" 2>/dev/null \
  || die "faltam dependências no server/.venv — rode: server/.venv/bin/python -m pip install -r server/requirements.txt"
# --testar-locais: testa cada AuthKey_*.p8 de P8_DIR direto na Apple, sem Railway.
if [ "${1:-}" = "--testar-locais" ]; then
  export P8_DIR="${P8_DIR:-/Users/acamerini/p8}"
  exec "$PY" scripts/diagnosticar_apns.py --testar-locais
fi
command -v railway >/dev/null 2>&1 || die "Railway CLI ausente (npm i -g @railway/cli) — ou exporte as APNS_* e rode: $PY scripts/diagnosticar_apns.py --from-env"
railway status >/dev/null 2>&1 || die "Railway CLI não está linkado a este diretório — rode: railway link (projeto bolsIA, serviço do backend)"

# Pasta dos AuthKey_*.p8 que o diagnóstico cruza com a chave do Railway.
export P8_DIR="${P8_DIR:-/Users/acamerini/p8}"
if [ -d "$P8_DIR" ]; then
  printf "  .p8 locais lidos de %s (%s arquivo(s) AuthKey_*.p8)\n" "$P8_DIR" "$(ls "$P8_DIR" | grep -cE '^AuthKey_[A-Z0-9]{10}\.p8$' || true)"
else
  printf "  \033[33m[!]\033[0m pasta %s não existe — o cruzamento com arquivos locais vai ser pulado\n" "$P8_DIR"
fi

railway variables --json "$@" | "$PY" scripts/diagnosticar_apns.py
