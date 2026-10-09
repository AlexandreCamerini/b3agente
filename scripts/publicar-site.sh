#!/usr/bin/env bash
# publicar-site.sh — copia site/ (site de marketing estático, quick 261009-mvb)
# para server/site_dist, a árvore que o Railway serve em /site/* no MESMO
# serviço do Boris (rootDirectory=/server — ../site fica fora do build context,
# mesmo motivo do web_dist/admin_dist). Sem build: o site é HTML/CSS/JS puro.
#
# Passo MANUAL, como publicar-web.sh/publicar-admin.sh:
#
#   bash scripts/publicar-site.sh
#
# Depois: revise o diff, rode `bash scripts/executar.sh --testes`, bump manual
# de SERVER_BUILD_ID (deploy só-backend), commit + push (Railway redeploya).
# NUNCA edite server/site_dist direto: a fonte é site/.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

say(){ printf "\n\033[1m== %s ==\033[0m\n" "$*"; }
ok(){ printf "  \033[32m[OK]\033[0m %s\n" "$*"; }
die(){ printf "  \033[31m[X]\033[0m %s\n" "$*" >&2; exit 1; }

say "Verificando site/"
[ -f site/index.html ] || die "site/index.html ausente"
if grep -rEn 'https?://' site --include='*.html' --include='*.css' --include='*.js' | grep -v 'www.w3.org' | grep -q .; then
  die "site/ referencia URL externa — o site deve ser autocontido (sem CDN)"
fi
ok "autocontido, sem URL externa"

say "Copiando para server/site_dist"
rm -rf server/site_dist
mkdir -p server/site_dist
# README.md é documentação do repo, não conteúdo publicado.
rsync -a --exclude 'README.md' --exclude '.DS_Store' site/ server/site_dist/
ok "$(find server/site_dist -type f | wc -l | tr -d ' ') arquivos em server/site_dist ($(du -sh server/site_dist | cut -f1))"

echo
echo "Próximo: git diff --stat server/site_dist · suíte canônica · bump de SERVER_BUILD_ID · commit + push."
