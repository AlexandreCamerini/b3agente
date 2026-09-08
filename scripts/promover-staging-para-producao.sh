#!/usr/bin/env bash
# promover-staging-para-producao.sh — quando a versão em staging já foi
# validada e está pronta pra virar produção: mescla a branch de trabalho em
# `main`, roda a suíte de novo JÁ com o merge, e (só com confirmação
# explícita, digitada) empurra `main` pra origin.
#
# O PUSH NÃO DEPLOYA. O auto-deploy de produção foi desligado de propósito
# em 2026-09-07 (ver STAGING.md): depois de dois deploys indevidos causados
# por mudança de CONFIGURAÇÃO no Railway — não por este script — produção
# passou a exigir um clique manual no painel. Este script prepara e publica
# o código; quem sobe é você, vendo o que está subindo.
#
# `publicar-staging.sh` nunca chega perto de `main`; este script é o único
# lugar onde a promoção acontece, de propósito — histórico de decisão fica
# num commit só, fácil de apontar depois.
#
# 2026-09-07: passou a promover a BRANCH LOCAL de trabalho, não `origin/staging`.
# O staging deixou de ser publicado por push de branch (ver o cabeçalho de
# publicar-staging.sh — a branch é compartilhada entre environments no Railway
# e mudá-la vazava para produção); agora sobe por `railway up`. Então o que se
# promove é o commit que você testou em staging, que é o HEAD da sua branch.
#
# Uso:
#   bash scripts/promover-staging-para-producao.sh            # branch atual
#   PROMOVER_BRANCH=v2/interacao-estrutural bash scripts/promover-staging-para-producao.sh
#
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.."

PROMOVER_BRANCH="${PROMOVER_BRANCH:-$(git rev-parse --abbrev-ref HEAD)}"
RAILWAY_URL="https://boris.semente.dev"

say(){ printf "\n\033[1m== %s ==\033[0m\n" "$*"; }
ok(){ printf "  \033[32m[OK]\033[0m %s\n" "$*"; }
die(){ printf "  \033[31m[X]\033[0m %s\n" "$*" >&2; exit 1; }

git diff --quiet && git diff --cached --quiet \
  || die "há mudanças não commitadas na sua branch atual — commite ou descarte antes de trocar de branch"

say "0/6 · Buscando estado atual de origin"
git fetch origin
[ "$PROMOVER_BRANCH" != "main" ] || die "PROMOVER_BRANCH não pode ser 'main' — não há o que promover"
git rev-parse --verify -q "$PROMOVER_BRANCH" >/dev/null \
  || die "branch '$PROMOVER_BRANCH' não existe localmente"
echo "  origin/main:            $(git rev-parse origin/main)"
echo "  $PROMOVER_BRANCH: $(git rev-parse "$PROMOVER_BRANCH")"

say "1/6 · Checkout de main, alinhado com origin/main"
git checkout main
git merge --ff-only origin/main \
  || die "main local diverge de origin/main — resolva manualmente (git status) antes de continuar"
ok "main local == origin/main"

say "2/6 · Merge de $PROMOVER_BRANCH em main (local, SEM push ainda)"
if git merge --no-ff "$PROMOVER_BRANCH" -m "chore: promove $PROMOVER_BRANCH para produção"; then
  ok "merge sem conflito"
else
  die "merge deu conflito — resolva manualmente e rode de novo, ou 'git merge --abort' pra cancelar. NÃO force nada."
fi

say "3/6 · Suíte canônica em main JÁ COM o merge"
if ! bash scripts/executar.sh --testes; then
  echo
  echo "  Suíte vermelha DEPOIS do merge. main NÃO foi empurrada."
  echo "  Pra desfazer o merge local:  git reset --hard origin/main"
  die "corrija o problema (na branch de staging) antes de promover de novo"
fi
ok "suíte verde em main pós-merge"

say "4/6 · Build final + publicação do front, já em main"
bash scripts/publicar-web.sh || die "publicar-web.sh falhou em main"
git add server/web_dist server/app/main.py web/src/version.js
git diff --cached --quiet || git commit -m "chore: publica front da promoção de $PROMOVER_BRANCH"

say "5/6 · Revisão final antes do push"
echo "  Commits que vão para produção (origin/main..HEAD):"
git log --oneline origin/main..HEAD
echo
BUILD_PROMO="$(sed -n 's/.*BUILD_ID = "\([^"]*\)".*/\1/p' web/src/version.js)"
echo "  Carimbo que vai ao ar: $BUILD_PROMO"
echo
echo "  Isto vai rodar:  git push origin main"
echo
echo "  ATENÇÃO: o auto-deploy de produção está DESLIGADO de propósito"
echo "  (decisão de 2026-09-07 — ver STAGING.md). O push NÃO sobe nada"
echo "  sozinho: ele só publica o código. O deploy é um clique seu, no"
echo "  painel, depois. Isso é a rede de segurança, não um defeito."
printf "  Digite exatamente PRODUCAO para confirmar o push (qualquer outra coisa cancela): "
read -r CONFIRM
[ "$CONFIRM" = "PRODUCAO" ] || die "cancelado — nada foi enviado a origin/main. O merge continua só local (git reset --hard origin/main pra desfazer)."

say "6/6 · Push para origin/main"
git push origin main
ok "código publicado em origin/main (produção ainda NÃO mudou)"

SHA_PROMO="$(git rev-parse --short HEAD)"
cat <<FIM

  ─────────────────────────────────────────────────────────────
   FALTA UM PASSO — o deploy de produção é MANUAL
  ─────────────────────────────────────────────────────────────

   1. Abra o Railway → projeto bolsIA
   2. Troque o environment para  production
   3. Serviço  b3agente  → botão  Deploy
      (ele sobe o commit mais recente de main: $SHA_PROMO)
   4. Acompanhe em Deployments; o build usa NIXPACKS
      e deve mostrar a linha do backup:  [backup] ok -> /data/backups/...

   Produção AGORA:   $(curl -s --max-time 10 "$RAILWAY_URL/api/health" 2>/dev/null || echo "sem resposta")
   Esperado depois:  build "$BUILD_PROMO"

   Para conferir quando terminar:
     curl -s $RAILWAY_URL/api/health

   Se precisar voltar atrás: no painel, Deployments → o deploy
   anterior → Redeploy. O banco não volta junto (ver STAGING.md,
   seção Rollback) — por isso o backup roda antes de cada deploy.

  ─────────────────────────────────────────────────────────────
FIM
