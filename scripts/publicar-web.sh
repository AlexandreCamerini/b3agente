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
#   bash scripts/publicar-web.sh --so-publicar # só copia um dist JÁ buildado
#
# Depois: revise o diff, rode a suíte, commit + push (Railway redeploya sozinho).
#
# `--so-publicar` existe para o entregar.sh: ele já builda com o próprio npm
# install e só precisa da PUBLICAÇÃO. Assim o "o que vai para onde" continua
# definido em UM lugar só (aqui), sem o entregar.sh duplicar o rm -rf/cp nem
# rebuildar o que acabou de buildar.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

say(){ printf "\n\033[1m== %s ==\033[0m\n" "$*"; }
ok(){ printf "  \033[32m[OK]\033[0m %s\n" "$*"; }
die(){ printf "  \033[31m[X]\033[0m %s\n" "$*" >&2; exit 1; }

SO_BUILD=0; SO_PUBLICAR=0
case "${1:-}" in
  --so-build) SO_BUILD=1 ;;
  --so-publicar) SO_PUBLICAR=1 ;;
  "") ;;
  *) die "opção desconhecida: $1 (use --so-build ou --so-publicar)" ;;
esac

BUILD_LOCAL="$(sed -n 's/.*BUILD_ID = "\([^"]*\)".*/\1/p' web/src/version.js)"
[ -n "$BUILD_LOCAL" ] || die "web/src/version.js sem BUILD_ID"

say "1/3 · Build do web (npm ci + vite build)"
if [ "$SO_PUBLICAR" = "1" ]; then
  # Quem chama já buildou (entregar.sh). Ainda assim o carimbo é conferido:
  # publicar um dist velho em server/web_dist é exatamente o erro que este
  # script existe para não deixar acontecer.
  [ -d web/dist/assets ] || die "--so-publicar exige web/dist já buildado"
  grep -rq "$BUILD_LOCAL" web/dist/assets/*.js 2>/dev/null \
    || die "o dist existente não contém o carimbo $BUILD_LOCAL — builde antes de publicar"
  ok "--so-publicar: reusando o dist já buildado ($BUILD_LOCAL)"
else
  (cd web && npm ci --silent && npx vite build) || die "build falhou"
  grep -rq "$BUILD_LOCAL" web/dist/assets/*.js 2>/dev/null \
    || die "dist buildado não contém o carimbo $BUILD_LOCAL — version.js divergente?"
  ok "dist com o carimbo $BUILD_LOCAL"
fi

say "2/3 · Publicar em server/web_dist (única árvore que o Railway enxerga)"
rm -rf server/web_dist
cp -r web/dist server/web_dist
ok "server/web_dist atualizado ($(du -sh server/web_dist | cut -f1))"

if [ "$SO_BUILD" = "1" ] || [ "$SO_PUBLICAR" = "1" ]; then
  # O entregar.sh já sincronizou o SERVER_BUILD_ID no início da cadeia dele;
  # refazer aqui não muda nada, mas dizer que fez mentiria sobre o que rodou.
  ok "parei aqui (carimbo do servidor e git intocados)"
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
