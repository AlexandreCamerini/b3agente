#!/usr/bin/env bash
# promover-staging-para-producao.sh — quando a versão em staging já foi
# validada e está pronta pra virar produção de verdade: mescla a branch de
# staging em `main`, roda a suíte de novo JÁ com o merge, e (só com
# confirmação explícita, digitada) empurra `main` pra origin — o único
# comando deste par de scripts que efetivamente dispara o deploy de
# PRODUÇÃO no Railway.
#
# `publicar-staging.sh` nunca chega perto de `main`; este script é o único
# lugar onde a promoção acontece, de propósito — histórico de decisão fica
# num commit só, fácil de apontar depois.
#
# Uso:
#   bash scripts/promover-staging-para-producao.sh
#   STAGING_BRANCH=outro-nome bash scripts/promover-staging-para-producao.sh
#
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.."

STAGING_BRANCH="${STAGING_BRANCH:-staging}"
RAILWAY_URL="https://boris.semente.dev"

say(){ printf "\n\033[1m== %s ==\033[0m\n" "$*"; }
ok(){ printf "  \033[32m[OK]\033[0m %s\n" "$*"; }
die(){ printf "  \033[31m[X]\033[0m %s\n" "$*" >&2; exit 1; }

git diff --quiet && git diff --cached --quiet \
  || die "há mudanças não commitadas na sua branch atual — commite ou descarte antes de trocar de branch"

say "0/6 · Buscando estado atual de origin"
git fetch origin
git rev-parse --verify -q "origin/$STAGING_BRANCH" >/dev/null \
  || die "origin/$STAGING_BRANCH não existe — publique em staging primeiro (scripts/publicar-staging.sh)"
echo "  origin/main:            $(git rev-parse origin/main)"
echo "  origin/$STAGING_BRANCH: $(git rev-parse "origin/$STAGING_BRANCH")"

say "1/6 · Checkout de main, alinhado com origin/main"
git checkout main
git merge --ff-only origin/main \
  || die "main local diverge de origin/main — resolva manualmente (git status) antes de continuar"
ok "main local == origin/main"

say "2/6 · Merge de origin/$STAGING_BRANCH em main (local, SEM push ainda)"
if git merge --no-ff "origin/$STAGING_BRANCH" -m "chore: promove $STAGING_BRANCH para produção"; then
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
git diff --cached --quiet || git commit -m "chore: publica front da promoção de $STAGING_BRANCH"

say "5/6 · Revisão final antes do push"
echo "  Commits que vão para produção (origin/main..HEAD):"
git log --oneline origin/main..HEAD
echo
echo "  Isto vai rodar:  git push origin main"
echo "  Este comando DISPARA O DEPLOY DE PRODUÇÃO no Railway."
printf "  Digite exatamente PRODUCAO para confirmar (qualquer outra coisa cancela): "
read -r CONFIRM
[ "$CONFIRM" = "PRODUCAO" ] || die "cancelado — nada foi enviado a origin/main. O merge continua só local (git reset --hard origin/main pra desfazer)."

say "6/6 · Push para origin/main"
git push origin main
ok "produção atualizada"

echo
echo "  Aguardando o Railway subir produção…"
for i in $(seq 1 20); do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$RAILWAY_URL/api/health" || echo 000)
  [ "$code" = "200" ] && { ok "/api/health de produção respondeu 200 (tentativa $i)"; break; }
  echo "  tentativa $i/20 -> HTTP $code"
  [ "$i" = "20" ] && { echo "  ✗ sem 200 após ~5 min — veja Deployments no painel do Railway (produção)"; exit 1; }
  sleep 15
done
echo
echo "  Promoção concluída: $STAGING_BRANCH -> main -> produção ($RAILWAY_URL)."
