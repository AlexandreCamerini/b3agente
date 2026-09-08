#!/usr/bin/env bash
# publicar-staging.sh — publica a branch de trabalho ATUAL no environment de
# STAGING do Railway, sem tocar em `main`/produção.
#
# POR QUE `railway up` E NÃO `git push` (decisão de 2026-09-07, aprendida na
# marra): a abordagem original era empurrar para uma branch `staging` que o
# Railway rastrearia. Não funciona neste projeto — o campo de branch é
# COMPARTILHADO entre os environments no modelo de dados do Railway, e todo
# comando de CLI que tenta mudá-lo (`service source connect --branch`, e o
# `environment edit --service-config source.branch` depois do upgrade) muda a
# branch de PRODUÇÃO junto. Isso causou dois deploys indevidos em produção no
# mesmo dia, um deles servindo código não verificado por alguns minutos.
#
# `railway up` envia o diretório local direto para um serviço+environment
# nomeados explicitamente. Não lê branch, não escreve configuração, não tem
# como vazar para produção. O rastro commit↔deploy continua existindo no git
# (o script exige árvore limpa e commita antes de subir), só não no painel do
# Railway.
#
# Uso:
#   bash scripts/publicar-staging.sh
#   STAGING_URL=https://b3agente-staging.up.railway.app bash scripts/publicar-staging.sh
#
# Pré-requisitos (uma vez): `railway login` e o environment `staging` criado
# no projeto, com as variáveis degradadas (ver STAGING.md).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.."

ENV_ALVO="${STAGING_ENV:-staging}"
SERVICO="${STAGING_SERVICE:-b3agente}"
STAGING_URL="${STAGING_URL:-https://b3agente-staging.up.railway.app}"

say(){ printf "\n\033[1m== %s ==\033[0m\n" "$*"; }
ok(){ printf "  \033[32m[OK]\033[0m %s\n" "$*"; }
die(){ printf "  \033[31m[X]\033[0m %s\n" "$*" >&2; exit 1; }

# ---------------------------------------------------------------------------
# TRAVA DE SEGURANÇA. Não é cerimônia: em 2026-09-07 dois deploys foram parar
# em produção por engano. Nada neste script pode rodar contra `production`.
# ---------------------------------------------------------------------------
[ "$ENV_ALVO" != "production" ] || die "STAGING_ENV=production é proibido por este script. Produção se publica por scripts/promover-staging-para-producao.sh, com confirmação digitada."

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
[ "$CURRENT_BRANCH" != "HEAD" ] || die "HEAD destacado — faça checkout de uma branch"
[ "$CURRENT_BRANCH" != "main" ] || die "você está em 'main'. Staging existe pra publicar trabalho SEM tocar em main — troque para a branch que quer testar."

say "0/6 · Alvo"
echo "  branch local: $CURRENT_BRANCH  (não é lida pelo Railway — só entra no rastro do git)"
echo "  environment:  $ENV_ALVO"
echo "  serviço:      $SERVICO"
echo "  URL:          $STAGING_URL"

say "1/6 · Working tree limpa"
git diff --quiet && git diff --cached --quiet \
  || die "há mudanças não commitadas — commite ou descarte antes de publicar"
ok "sem pendências"

say "2/6 · Suíte canônica (backend + web)"
bash scripts/executar.sh --testes || die "suíte vermelha — corrija antes de publicar (scripts/test.sh sozinho NÃO conta)"
ok "suíte verde"

say "3/6 · Build + publicação do front (server/web_dist)"
bash scripts/publicar-web.sh || die "publicar-web.sh falhou"

say "4/6 · Commit local (rastro do que foi ao ar)"
git add server/web_dist server/app/main.py web/src/version.js
if git diff --cached --quiet; then
  ok "nada novo para commitar"
else
  BUILD_LOCAL="$(sed -n 's/.*BUILD_ID = "\([^"]*\)".*/\1/p' web/src/version.js)"
  git commit -m "chore(staging): publica $BUILD_LOCAL"
  ok "commit criado ($BUILD_LOCAL)"
fi
BUILD_LOCAL="$(sed -n 's/.*BUILD_ID = "\([^"]*\)".*/\1/p' web/src/version.js)"
SHA_LOCAL="$(git rev-parse --short HEAD)"

say "5/6 · Deploy para $ENV_ALVO (railway up)"
echo "  Envia o diretório local para o serviço '$SERVICO' no environment"
echo "  '$ENV_ALVO'. NÃO passa por GitHub e NÃO altera configuração nenhuma"
echo "  — produção é inalcançável por este comando."
printf "  Confirma? (s/N) "
read -r RESP
case "$RESP" in s|S) ;; *) die "cancelado — nada foi enviado" ;; esac

railway up --environment "$ENV_ALVO" --service "$SERVICO" --ci \
  || die "railway up falhou (veja o log acima; 'railway login' expirado é a causa comum)"
ok "upload concluído"

say "6/6 · Conferindo o que subiu"
for i in $(seq 1 20); do
  RESP_HEALTH="$(curl -s --max-time 10 "$STAGING_URL/api/health" || true)"
  if echo "$RESP_HEALTH" | grep -q "$BUILD_LOCAL"; then
    ok "staging servindo $BUILD_LOCAL (commit $SHA_LOCAL)"
    echo
    echo "  $STAGING_URL"
    echo "  Quando validar, promova com:"
    echo "    bash scripts/promover-staging-para-producao.sh"
    exit 0
  fi
  echo "  tentativa $i/20 -> ${RESP_HEALTH:-sem resposta}"
  sleep 15
done
die "staging não reportou o carimbo $BUILD_LOCAL após ~5 min — veja Deployments no painel (environment $ENV_ALVO)"
