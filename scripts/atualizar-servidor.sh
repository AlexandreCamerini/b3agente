#!/usr/bin/env bash
# atualizar-servidor.sh — commit + push + verificação do deploy no Railway.
# Uso (na raiz do repo):  bash scripts/atualizar-servidor.sh "mensagem do commit"
set -euo pipefail
cd "$(dirname "$0")/.."
MSG="${1:-atualizacao}"
RAILWAY_URL="https://b3agente-production.up.railway.app"

git add -A
git diff --cached --quiet && echo "nada novo para commitar" || git commit -m "$MSG"
git push origin main
echo "push feito — aguardando o deploy do Railway…"

for i in $(seq 1 20); do
  code=$(curl -s -o /tmp/health.json -w "%{http_code}" \
    "$RAILWAY_URL/api/scan?period=1mo&tickers=PETR4,VALE3" || echo 000)
  [ "$code" = "200" ] && { echo "✓ /api/scan no ar (tentativa $i)"; break; }
  echo "tentativa $i/20 → HTTP $code"
  [ "$i" = "20" ] && { echo "✗ sem 200 após ~5 min — veja Deployments no painel do Railway"; exit 1; }
  sleep 15
done
python3 -c "import json; d=json.load(open('/tmp/health.json')); r=d['results'][0]; print('✓ radar v2:', r['ticker'], '->', r.get('veredito'), str(r.get('confluencia'))+'%')"
echo "✓ servidor atualizado e verificado"
