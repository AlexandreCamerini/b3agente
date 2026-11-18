#!/usr/bin/env bash
# diagnosticar-apns.sh — Boris+ · confere a credencial do push (APNs) de ponta a ponta.
#
#   bash scripts/diagnosticar-apns.sh                       # lê as variáveis do Railway (serviço linkado)
#   bash scripts/diagnosticar-apns.sh --environment staging # outro ambiente do Railway
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
command -v railway >/dev/null 2>&1 || die "Railway CLI ausente (npm i -g @railway/cli) — ou exporte as APNS_* e rode: $PY scripts/diagnosticar_apns.py --from-env"
railway status >/dev/null 2>&1 || die "Railway CLI não está linkado a este diretório — rode: railway link (projeto bolsIA, serviço do backend)"

railway variables --json "$@" | "$PY" scripts/diagnosticar_apns.py
