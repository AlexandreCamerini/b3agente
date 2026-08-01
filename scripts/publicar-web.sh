#!/usr/bin/env bash
# publicar-web.sh — F4 mínimo: builda o web e publica em server/web_dist, a
# ÚNICA árvore que o Railway enxerga (rootDirectory=/server — ver
# server/railway.json; ../web fica FORA do build context do serviço).
#
# NÃO é CI/CD automático de propósito: é um passo MANUAL, como o entregar.sh
# trata o iOS. Rode sempre que quiser que a versão web em produção reflita o
# front atual do repo:
#
#   bash scripts/publicar-web.sh              # builda, publica, sincroniza carimbo
#   bash scripts/publicar-web.sh --so-build    # só builda/copia, sem tocar carimbo/git
#
# Depois: revise o diff, rode a suíte, commit + push (Railway redeploya sozinho).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

say(){ printf "\n\033[1m== %s ==\033[0m\n" "$*"; }
ok(){ printf "  \033[32m[OK]\033[0m %s\n" "$*"; }
die(){ printf "  \033[31m[X]\033[0m %s\n" "$*" >&2; exit 1; }

SO_BUILD=0
[ "${1:-}" = "--so-build" ] && SO_BUILD=1

BUILD_LOCAL="$(sed -n 's/.*BUILD_ID = "\([^"]*\)".*/\1/p' web/src/version.js)"
[ -n "$BUILD_LOCAL" ] || die "web/src/version.js sem BUILD_ID"

say "1/3 · Build do web (npm ci + vite build)"
(cd web && npm ci --silent && npx vite build) || die "build falhou"
grep -rq "$BUILD_LOCAL" web/dist/assets/*.js 2>/dev/null \
  || die "dist buildado não contém o carimbo $BUILD_LOCAL — version.js divergente?"
ok "dist com o carimbo $BUILD_LOCAL"

say "2/3 · Publicar em server/web_dist (única árvore que o Railway enxerga)"
rm -rf server/web_dist
cp -r web/dist server/web_dist
ok "server/web_dist atualizado ($(du -sh server/web_dist | cut -f1))"

if [ "$SO_BUILD" = "1" ]; then
  ok "--so-build: parei aqui (carimbo do servidor e git intocados)"
  exit 0
fi

say "3/3 · Sincronizar carimbo do servidor (mesmo padrão do entregar.sh)"
SRV_ATUAL="$(sed -n 's/.*SERVER_BUILD_ID = "\([^"]*\)".*/\1/p' server/app/main.py)"
if [ "$SRV_ATUAL" != "$BUILD_LOCAL" ]; then
  sed -i '' "s/SERVER_BUILD_ID = \"[^\"]*\"/SERVER_BUILD_ID = \"$BUILD_LOCAL\"/" server/app/main.py 2>/dev/null \
    || sed -i "s/SERVER_BUILD_ID = \"[^\"]*\"/SERVER_BUILD_ID = \"$BUILD_LOCAL\"/" server/app/main.py
  ok "carimbo do servidor sincronizado: $SRV_ATUAL → $BUILD_LOCAL"
else
  ok "carimbo do servidor já era $BUILD_LOCAL"
fi

echo
echo "  Próximo passo (MANUAL, este script não commita/pushega):"
echo "    git add server/web_dist server/app/main.py web/src/version.js"
echo "    git commit -m \"...\" && git push"
echo "  O Railway redeploya sozinho; confira em /api/health e na URL raiz."
