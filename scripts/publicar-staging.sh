#!/usr/bin/env bash
# publicar-staging.sh — publica a branch de trabalho ATUAL no environment de
# STAGING do Railway, sem tocar em `main`/produção.
#
# Pré-requisito (feito UMA VEZ, no dashboard do Railway, fora deste script):
#   1. criar um environment novo no projeto (ex.: nome "staging");
#   2. configurar esse environment para rastrear a branch $STAGING_BRANCH
#      (default abaixo: "staging") — Railway redeploya sozinho a cada push
#      nela, do mesmo jeito que main já faz para produção;
#   3. copiar as env vars necessárias pro environment novo (o Railway deixa
#      copiar de um environment existente); o banco (B3_DB_PATH) e os
#      volumes ficam automaticamente ISOLADOS por environment — dado de
#      staging nunca contamina produção, e vice-versa.
#
# Uso:
#   bash scripts/publicar-staging.sh                 # branch atual -> staging
#   STAGING_BRANCH=outro-nome bash scripts/publicar-staging.sh
#   STAGING_URL=https://boris-staging.up.railway.app bash scripts/publicar-staging.sh
#
# O que faz:
#   1. recusa rodar a partir de `main` (staging existe pra ISOLAR trabalho de
#      main, não pra ser um atalho dela);
#   2. suíte canônica completa (backend + web) — nunca publica vermelho;
#   3. builda e publica o front em server/web_dist (via publicar-web.sh);
#   4. commit local do dist + carimbo;
#   5. push da branch atual para origin/$STAGING_BRANCH (pede confirmação —
#      é a primeira vez que este fluxo manda algo pra `origin`);
#   6. se STAGING_URL estiver setada, espera o Railway subir e confere
#      /api/health.
#
# `main` nunca é lida nem tocada por este script.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.."
ROOT="$(pwd)"

STAGING_BRANCH="${STAGING_BRANCH:-staging}"
STAGING_URL="${STAGING_URL:-}"

say(){ printf "\n\033[1m== %s ==\033[0m\n" "$*"; }
ok(){ printf "  \033[32m[OK]\033[0m %s\n" "$*"; }
die(){ printf "  \033[31m[X]\033[0m %s\n" "$*" >&2; exit 1; }

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
[ "$CURRENT_BRANCH" != "HEAD" ] || die "HEAD destacado (detached) — faça checkout de uma branch antes"
[ "$CURRENT_BRANCH" != "main" ] || die "você está em 'main'. Staging existe pra publicar trabalho SEM tocar em main — troque para a branch que quer testar."

say "0/6 · Branch e destino"
echo "  branch local:    $CURRENT_BRANCH"
echo "  destino:         origin/$STAGING_BRANCH"
[ -n "$STAGING_URL" ] && echo "  URL de staging:  $STAGING_URL" || echo "  URL de staging:  (não informada — pulo a checagem de saúde no fim)"

say "1/6 · Working tree limpa"
git diff --quiet && git diff --cached --quiet \
  || die "há mudanças não commitadas — commite ou descarte antes de publicar em staging"
ok "sem pendências"

say "2/6 · Suíte canônica (backend + web)"
bash scripts/executar.sh --testes || die "suíte vermelha — corrija antes de publicar em staging (scripts/test.sh sozinho NÃO conta)"
ok "suíte verde"

say "3/6 · Build + publicação do front (server/web_dist)"
bash scripts/publicar-web.sh || die "publicar-web.sh falhou"

say "4/6 · Commit local"
git add server/web_dist server/app/main.py web/src/version.js
if git diff --cached --quiet; then
  ok "nada novo para commitar (dist já estava com o carimbo atual)"
else
  BUILD_LOCAL="$(sed -n 's/.*BUILD_ID = "\([^"]*\)".*/\1/p' web/src/version.js)"
  git commit -m "chore(staging): publica $BUILD_LOCAL"
  ok "commit criado ($BUILD_LOCAL)"
fi

say "5/6 · Push para origin/$STAGING_BRANCH"
echo "  Isto vai rodar:  git push origin $CURRENT_BRANCH:$STAGING_BRANCH"
echo "  'main' e produção NÃO são tocados por este comando."
printf "  Confirma? (s/N) "
read -r RESP
case "$RESP" in
  s|S) ;;
  *) die "cancelado — nada foi enviado a origin" ;;
esac
git push origin "$CURRENT_BRANCH:$STAGING_BRANCH"
ok "empurrado para origin/$STAGING_BRANCH"

if [ -z "$STAGING_URL" ]; then
  say "6/6 · Checagem de saúde pulada (STAGING_URL não informada)"
  echo "  Rode de novo com STAGING_URL=https://sua-url-de-staging bash scripts/publicar-staging.sh"
  echo "  para o script esperar o Railway subir e conferir /api/health sozinho."
  exit 0
fi

say "6/6 · Aguardando o Railway subir o environment de staging"
for i in $(seq 1 20); do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$STAGING_URL/api/health" || echo 000)
  [ "$code" = "200" ] && { ok "/api/health respondeu 200 (tentativa $i)"; break; }
  echo "  tentativa $i/20 -> HTTP $code"
  [ "$i" = "20" ] && die "sem 200 após ~5 min — veja Deployments no painel do Railway (environment de staging)"
  sleep 15
done
echo
echo "  Staging atualizado: $STAGING_URL"
echo "  Quando validar esta versão, promova com:"
echo "    STAGING_BRANCH=$STAGING_BRANCH bash scripts/promover-staging-para-producao.sh"
