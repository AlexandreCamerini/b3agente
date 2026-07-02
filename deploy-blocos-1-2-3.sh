#!/usr/bin/env bash
# deploy-blocos-1-2-3.sh — BolsIA (b3-agente)
# Commita os Blocos 1·2·3, faz push e VERIFICA o /api/scan no Railway.
# Uso:  bash deploy-blocos-1-2-3.sh
set -euo pipefail

RAILWAY_URL="https://b3agente-production.up.railway.app"

echo "== 0) Sanidade: os arquivos novos estão neste diretório de trabalho? =="
faltando=0
for f in server/app/scanner.py server/tests/test_scanner.py web/tests/test_radar.mjs; do
  if [ -f "$f" ]; then echo "  ok  $f"; else echo "  FALTA $f"; faltando=1; fi
done
grep -q '"/api/scan"' server/app/main.py && echo "  ok  rota /api/scan no main.py" || { echo "  FALTA rota /api/scan no main.py"; faltando=1; }
grep -q 'b3-notify-nid' web/src/notify.js && echo "  ok  notify.js (Bloco 1)" || { echo "  FALTA notify.js atualizado"; faltando=1; }
grep -q 'RadarScreen' web/src/App.jsx && echo "  ok  App.jsx (Radar)" || { echo "  FALTA App.jsx atualizado"; faltando=1; }
if [ "$faltando" = "1" ]; then
  echo
  echo "✗ Este diretório NÃO tem a entrega aplicada. Extraia o b3-agente.zip do"
  echo "  files.zip por cima do repo (preservando o .git) e rode de novo."
  exit 1
fi

echo
echo "== 1) Git: commit + push =="
git add -A
if git diff --cached --quiet; then
  echo "  nada novo para commitar (já commitado antes?) — seguindo para o push"
else
  git commit -m "Blocos 1-3: notificacoes nativas confiaveis, welcome boot gate, radar de mercado"
fi
git push origin main
echo "  push feito. O Railway inicia o deploy automaticamente."

echo
echo "== 2) Aguardando o deploy do Railway (health check a cada 15s) =="
# Espera a rota nova existir (novo deploy no ar). Timeout: ~5 min.
tentativas=20
for i in $(seq 1 $tentativas); do
  code=$(curl -s -o /tmp/scan_check.json -w "%{http_code}" \
    "$RAILWAY_URL/api/scan?period=1mo&tickers=PETR4,VALE3" || echo "000")
  if [ "$code" = "200" ]; then
    echo "  ✓ /api/scan respondeu 200 na tentativa $i"
    break
  fi
  echo "  tentativa $i/$tentativas → HTTP $code (deploy ainda subindo?)"
  if [ "$i" = "$tentativas" ]; then
    echo
    echo "✗ /api/scan não respondeu 200 após ~5 min."
    echo "  Abra o painel do Railway → Deployments e veja se o build falhou."
    echo "  Última resposta:"; cat /tmp/scan_check.json; echo
    exit 1
  fi
  sleep 15
done

echo
echo "== 3) Smoke test do Radar (2 tickers) =="
python3 - << 'PY'
import json
d = json.load(open("/tmp/scan_check.json"))
assert "results" in d and "disclaimer" in d, d
print("  ✓ payload ok: %d/%d ativos varridos, período=%s (%d pregões)" %
      (d["scanned"], d["universeSize"], d["period"], d["periodBars"]))
for r in d["results"]:
    print("    %-7s score=%-3d condições=%d" % (r["ticker"], r["score_tecnico"], len(r["condicoes_detectadas"])))
if d.get("errors"):
    print("  atenção — erros:", d["errors"])
PY

echo
echo "== 4) Próximos passos (manuais) =="
echo "  • Universo completo (1ª vez ~1 min): $RAILWAY_URL/api/scan?period=1y"
echo "  • iOS: cd web && npm install && npm run build && npx cap sync ios  → rebuild no Xcode"
echo "  • No iPHONE: Perfil → Conta & preferências → endereço do servidor ="
echo "      b3agente-production.up.railway.app  → Testar conexão"
echo "    (o simulador funcionar e o iPhone não = endereço salvo diferente no aparelho)"
echo
echo "✓ Deploy dos Blocos 1·2·3 concluído."
