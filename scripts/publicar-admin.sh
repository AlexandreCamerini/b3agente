#!/usr/bin/env bash
# publicar-admin.sh — builda web-admin/ (portal de observabilidade, ADR-011)
# e publica em server/admin_dist, a árvore que o Railway serve em /admin/*
# (rootDirectory=/server — ver server/railway.json; ../web-admin fica FORA
# do build context do serviço, mesmo motivo do web_dist).
#
# NÃO é CI/CD automático de propósito, mesmo padrão de publicar-web.sh: passo
# MANUAL, roda sempre que quiser que o portal em produção reflita o front
# atual do repo.
#
#   bash scripts/publicar-admin.sh
#
# Sem carimbo de versão (BUILD_ID) — esta app não vai pro iOS/TestFlight, só
# é servida como bundle web; a verificação de "publicou certo" é o hash do
# arquivo mudar no diff do commit, não uma cadeia de elos como o entregar.sh.
#
# Depois: revise o diff, rode a suíte, commit + push (Railway redeploya sozinho).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

say(){ printf "\n\033[1m== %s ==\033[0m\n" "$*"; }
ok(){ printf "  \033[32m[OK]\033[0m %s\n" "$*"; }
die(){ printf "  \033[31m[X]\033[0m %s\n" "$*" >&2; exit 1; }

[ -d web-admin ] || die "web-admin/ não encontrado"

say "1/2 · Build do portal (npm ci + vite build)"
(cd web-admin && npm ci --silent && npx vite build) || die "build falhou"
[ -d web-admin/dist/assets ] || die "build não gerou web-admin/dist/assets"
ok "web-admin/dist gerado"

say "2/2 · Publicar em server/admin_dist (única árvore que o Railway enxerga)"
rm -rf server/admin_dist
cp -r web-admin/dist server/admin_dist
ok "server/admin_dist atualizado ($(du -sh server/admin_dist | cut -f1))"

echo
echo "  Próximo passo (MANUAL, este script não commita/pushega):"
echo "    git add server/admin_dist"
echo "    git commit -m \"...\" && git push"
echo "  O Railway redeploya sozinho; confira em /admin/ (login restrito ao administrador)."
