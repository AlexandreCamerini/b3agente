#!/usr/bin/env bash
# medir-yahoo-na-railway.sh — roda a medição do Yahoo DE DENTRO do container.
#
# Por que existe: a Fase 1 mediu o Yahoo de IP residencial (1.300 requisições,
# zero 429). O Yahoo aperta IP de datacenter — e este repositório já tem a
# cicatriz disso (README_FIX_YAHOO_401.md). Com orçamento de US$ 0 e fonte
# única, saber como o IP da Railway é tratado é PRÉ-REQUISITO do ADR.
#
# Como funciona: envia scripts/medicao_railway_payload.py comprimido pela linha
# de comando do `railway ssh` e executa com o python do container. NÃO faz
# deploy, NÃO cria arquivo no container, NÃO reinicia o serviço, NÃO escreve
# em /data. Só GETs no Yahoo e texto no stdout.
#
# Uso:
#   bash scripts/medir-yahoo-na-railway.sh                  # modo bloqueio (pregão FECHADO)
#   bash scripts/medir-yahoo-na-railway.sh atraso           # modo atraso (pregão ABERTO)
#   bash scripts/medir-yahoo-na-railway.sh bloqueio --seco  # só imprime o comando, não executa
#
# O payload aborta sozinho no primeiro 429/401/403 e tem teto de 300 requisições.
set -euo pipefail
cd "$(dirname "$0")/.."

MODO="${1:-bloqueio}"
SECO="${2:-}"
PAYLOAD="scripts/medicao_railway_payload.py"
SAIDA="medicao-railway-${MODO}-$(date +%Y%m%d-%H%M).txt"

[ -f "$PAYLOAD" ] || { echo "✗ não achei $PAYLOAD (rode a partir da raiz do repo)"; exit 1; }
command -v railway >/dev/null || { echo "✗ CLI da Railway não instalada"; exit 1; }

case "$MODO" in
  bloqueio|atraso) ;;
  *) echo "✗ modo inválido: $MODO (use 'bloqueio' ou 'atraso')"; exit 1 ;;
esac

# Aviso de janela: o modo bloqueio pode fazer o Yahoo apertar o IP que serve o
# app ao vivo. Fora do pregão o estrago é invisível; durante, não é.
HORA_BRT=$(TZ=America/Sao_Paulo date +%H)
DIA_BRT=$(TZ=America/Sao_Paulo date +%u)
if [ "$MODO" = "bloqueio" ] && [ "$DIA_BRT" -le 5 ] && [ "$HORA_BRT" -ge 10 ] && [ "$HORA_BRT" -lt 18 ]; then
  echo "⚠  São ${HORA_BRT}h BRT — PREGÃO ABERTO."
  echo "   O modo 'bloqueio' usa o mesmo IP que serve o app. Se o Yahoo apertar,"
  echo "   quem toma o 429 é o app ao vivo. O ideal é rodar com o pregão fechado."
  printf "   Continuar mesmo assim? [s/N] "
  read -r resp
  [ "$resp" = "s" ] || [ "$resp" = "S" ] || { echo "cancelado."; exit 0; }
fi
if [ "$MODO" = "atraso" ] && { [ "$DIA_BRT" -gt 5 ] || [ "$HORA_BRT" -lt 10 ] || [ "$HORA_BRT" -ge 17 ]; }; then
  echo "⚠  São ${HORA_BRT}h BRT — pregão fechado. O modo 'atraso' só produz número"
  echo "   útil entre 10h e 17h BRT. (O payload avisa de novo lá dentro.)"
fi

echo "→ alvo do deploy:"
railway status 2>/dev/null | sed -n '1,20p' | sed 's/^/   /'
echo

# Empacota: zlib + base64 numa linha só. Nada é gravado no container.
B64=$(python3 -c "
import base64, zlib, sys
src = open('$PAYLOAD','rb').read()
sys.stdout.write(base64.b64encode(zlib.compress(src, 9)).decode())
")
# O `python` do PATH no container é o do perfil Nix e NÃO enxerga as libs do
# app (httpx). Quem tem as dependências é o venv do Nixpacks — daí o fallback
# explícito, em ordem de confiança.
PY='PY=/opt/venv/bin/python3; [ -x "$PY" ] || PY=$(command -v python3) || PY=python'
CMD="sh -lc '$PY; exec \$PY -c \"import base64,zlib,sys;sys.argv=[\\\"medicao\\\",\\\"$MODO\\\"];exec(zlib.decompress(base64.b64decode(\\\"$B64\\\")))\"'"

if [ "$SECO" = "--seco" ]; then
  echo "→ modo seco: comando que SERIA executado (${#B64} bytes de payload):"
  echo
  echo "railway ssh $CMD"
  exit 0
fi

echo "→ executando no container (saída também em $SAIDA)…"
echo
railway ssh "$CMD" 2>&1 | tee "$SAIDA"
echo
echo "✓ saída salva em $SAIDA"
