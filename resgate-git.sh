#!/usr/bin/env bash
# resgate-git.sh — BolsIA (b3-agente)
# Sai do rebase travado, protege o estado local completo (Blocos 1-3) numa
# branch de backup e publica esse estado como UM commit em cima da main do
# GitHub. Nada de replay de commits antigos, nada de resolver conflito à mão.
# Uso:  bash resgate-git.sh
set -euo pipefail

echo "== 1) Abortar o rebase travado (volta ao estado de antes dele) =="
git rebase --abort 2>/dev/null && echo "  rebase abortado" || echo "  sem rebase em andamento — ok"
git merge --abort  2>/dev/null && echo "  merge abortado"  || true

echo
echo "== 2) Sanidade: o estado local tem a entrega completa? =="
faltando=0
for f in server/app/scanner.py web/src/notify.js web/src/App.jsx server/app/main.py; do
  [ -f "$f" ] && echo "  ok  $f" || { echo "  FALTA $f"; faltando=1; }
done
grep -q '"/api/scan"' server/app/main.py 2>/dev/null && echo "  ok  rota /api/scan" || { echo "  FALTA rota /api/scan"; faltando=1; }
grep -q 'b3-notify-nid' web/src/notify.js 2>/dev/null && echo "  ok  notify.js (Bloco 1)" || { echo "  FALTA notify.js Bloco 1"; faltando=1; }
grep -q 'RadarScreen' web/src/App.jsx 2>/dev/null && echo "  ok  App.jsx (Radar)" || { echo "  FALTA Radar no App.jsx"; faltando=1; }
if [ "$faltando" = "1" ]; then
  echo
  echo "✗ O estado local NÃO está completo após o abort. NÃO SIGA."
  echo "  Extraia o b3-agente.zip (do files.zip) por cima desta pasta,"
  echo "  confirme que 'git status' funciona, e rode este script de novo."
  exit 1
fi

echo
echo "== 3) Congelar o estado local numa branch de backup =="
git add -A
git diff --cached --quiet || git commit -m "wip: estado local completo antes do resgate"
BK="backup-blocos-1-2-3-$(date +%Y%m%d-%H%M%S)"
git branch "$BK"
echo "  backup criado: $BK  (o estado atual está a salvo aqui, aconteça o que acontecer)"

echo
echo "== 4) Alinhar a main local com o GitHub =="
git fetch origin
git checkout -B main origin/main
echo "  main local = origin/main"

echo
echo "== 5) Trazer a árvore COMPLETA do backup por cima da main =="
# Snapshot: o conteúdo final vence; não reaplicamos commits antigos um a um.
git checkout "$BK" -- .
git add -A
if git diff --cached --quiet; then
  echo "  main já era idêntica ao estado final — nada a commitar"
else
  git commit -m "Blocos 1-3: notificacoes nativas confiaveis, welcome boot gate, radar de mercado (snapshot completo)"
fi

echo
echo "== 6) Push =="
git push origin main
echo "  ✓ push feito — o Railway inicia o deploy do b3agente-production"

echo
echo "== 7) Verificação do deploy (aguarda /api/scan responder) =="
RAILWAY_URL="https://b3agente-production.up.railway.app"
for i in $(seq 1 20); do
  code=$(curl -s -o /tmp/scan_check.json -w "%{http_code}" \
    "$RAILWAY_URL/api/scan?period=1mo&tickers=PETR4,VALE3" || echo "000")
  [ "$code" = "200" ] && { echo "  ✓ /api/scan no ar (tentativa $i)"; break; }
  echo "  tentativa $i/20 → HTTP $code (deploy subindo…)"
  [ "$i" = "20" ] && { echo "✗ sem 200 após ~5 min — veja Deployments no painel do Railway"; exit 1; }
  sleep 15
done
python3 -c "import json; d=json.load(open('/tmp/scan_check.json')); print('  ✓ radar ok:', d['scanned'], 'ativos,', 'período', d['period'])"

echo
echo "✓ Resgate concluído. Branches antigas (fase2-multiusuario, $BK) ficam"
echo "  como histórico local — pode apagar depois com 'git branch -D <nome>'."
echo "  Próximo passo: cd web && npm run build && npx cap sync ios → rebuild."
