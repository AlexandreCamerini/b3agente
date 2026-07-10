#!/usr/bin/env bash
# entregar.sh — BolsIA · ENTREGA COMPLETA em um comando, com verificação de
# carimbo em CADA elo da cadeia. Criado na FASE 9 porque "a fase não apareceu"
# quase sempre era um elo solto entre código → git → dist → bundle iOS → Xcode.
#
#   bash entregar.sh "mensagem do commit"     # cadeia completa
#   bash entregar.sh --so-verificar           # só confere os elos, sem mudar nada
#
# Cadeia (aborta no primeiro elo ruim, com instrução exata):
#   1. suítes (backend offline + web)            — nunca entrega com teste falhando
#   2. commit + push (Railway redeploya sozinho) — backend no ar
#   3. npm install + vite build                  — dist/ com o BUILD_ID atual
#   4. cap sync ios + LIMPEZA de assets órfãos   — bundle do iPhone íntegro
#   5. VERIFICAÇÃO: BUILD_ID igual em version.js, dist/ e ios/public/
#   6. abre o Xcode com o lembrete do Clean Build Folder
#
# Depois do Run no iPhone: Perfil → rodapé DEVE mostrar o mesmo build.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]:-$0}")"

say(){ printf "\n\033[1m== %s ==\033[0m\n" "$*"; }
ok(){ printf "  \033[32m[OK]\033[0m %s\n" "$*"; }
warn(){ printf "  \033[33m[!]\033[0m %s\n" "$*"; }
die(){ printf "  \033[31m[X]\033[0m %s\n" "$*" >&2; exit 1; }

BUILD_LOCAL="$(sed -n 's/.*BUILD_ID = "\([^"]*\)".*/\1/p' web/src/version.js)"
[ -n "$BUILD_LOCAL" ] || die "web/src/version.js sem BUILD_ID — o carimbo é obrigatório"

# FASE 9.2: o carimbo do SERVIDOR é sincronizado AUTOMATICAMENTE a partir do
# version.js — as entregas 5–13 esqueceram o passo manual e o servidor ficou
# preso na -4, gerando "servidor ≠ local" falso na verificação para sempre.
SRV_ATUAL="$(sed -n 's/.*SERVER_BUILD_ID = "\([^"]*\)".*/\1/p' server/app/main.py)"
if [ "$SRV_ATUAL" != "$BUILD_LOCAL" ] && [ "${1:-}" != "--so-verificar" ]; then
  sed -i '' "s/SERVER_BUILD_ID = \"[^\"]*\"/SERVER_BUILD_ID = \"$BUILD_LOCAL\"/" server/app/main.py 2>/dev/null \
    || sed -i "s/SERVER_BUILD_ID = \"[^\"]*\"/SERVER_BUILD_ID = \"$BUILD_LOCAL\"/" server/app/main.py
  ok "carimbo do servidor sincronizado: $SRV_ATUAL → $BUILD_LOCAL"
fi

build_no_bundle(){ # $1 = dir de assets
  grep -rho 'F[0-9A-Za-z]\{1,6\}-[0-9]\{8\}-[0-9]\{1,3\}' "$1" 2>/dev/null | sort -u | tail -1
}
verificar(){
  say "Verificação dos elos (BUILD_ID esperado: $BUILD_LOCAL)"
  local RC=0
  # git
  if [ -z "$(git status --porcelain)" ]; then ok "working tree limpa (tudo commitado)"; else warn "há mudanças NÃO commitadas"; RC=1; fi
  local AHEAD="$(git rev-list --count origin/main..HEAD 2>/dev/null || echo '?')"
  [ "$AHEAD" = "0" ] && ok "push feito (main == origin/main)" || { warn "há $AHEAD commit(s) sem push"; RC=1; }
  # dist
  if [ -d web/dist/assets ]; then
    local BD; BD="$(build_no_bundle web/dist/assets)"
    [ "$BD" = "$BUILD_LOCAL" ] && ok "dist/ contém $BD" || { warn "dist/ contém '${BD:-nada}' ≠ $BUILD_LOCAL — rode a cadeia completa"; RC=1; }
  else warn "web/dist ausente — nunca buildou aqui"; RC=1; fi
  # bundle do iOS
  if [ -d web/ios/App/App/public/assets ]; then
    local BI; BI="$(build_no_bundle web/ios/App/App/public/assets)"
    [ "$BI" = "$BUILD_LOCAL" ] && ok "bundle do iOS contém $BI" || { warn "bundle do iOS contém '${BI:-nada}' ≠ $BUILD_LOCAL — falta cap sync"; RC=1; }
  else warn "web/ios/App/App/public ausente — rode cap sync"; RC=1; fi
  # servidor
  local URL="${RAILWAY_URL:-https://b3agente-production.up.railway.app}"
  local SRV; SRV="$(curl -fsS --max-time 8 "$URL/api/health" 2>/dev/null | sed -n 's/.*"build"[": ]*\([^"]*\)".*/\1/p')"
  if [ -n "$SRV" ]; then
    [ "$SRV" = "$BUILD_LOCAL" ] && ok "servidor no ar com $SRV" || warn "servidor no ar com '$SRV' ≠ $BUILD_LOCAL (deploy em andamento? aguarde ~2min)"
  else warn "servidor não respondeu (rede/painel do Railway)"; fi
  echo
  echo "  ÚLTIMO ELO (manual): Xcode → Product → Clean Build Folder → Run."
  echo "  No iPhone: Perfil → rodapé deve mostrar: build $BUILD_LOCAL"
  return $RC
}

if [ "${1:-}" = "--so-verificar" ]; then verificar; exit $?; fi

MSG="${1:-entrega}"

say "1/6 · Suítes (backend + web)"
bash executar.sh --testes >/dev/null 2>&1 && ok "todas as suítes verdes" || die "teste falhando — rode 'bash operar.sh testes' para ver qual. NUNCA entregue vermelho."

say "2/6 · Git (commit + push → Railway redeploya)"
if [ -n "$(git status --porcelain)" ]; then
  git add -A && git commit -m "$MSG" >/dev/null || die "commit falhou"
  ok "commit: $(git log -1 --format='%h %s')"
else
  ok "nada novo para commitar"
fi
git push >/dev/null 2>&1 && ok "push feito" || die "push falhou — confira a rede/credenciais e rode de novo"

say "3/6 · Build do web (npm install + vite build)"
cd web
npm install --silent >/dev/null 2>&1 || die "npm install falhou (veja: cd web && npm install)"
npx vite build >/dev/null 2>&1 || die "vite build falhou (veja: cd web && npx vite build)"
BD="$(build_no_bundle dist/assets)"
[ "$BD" = "$BUILD_LOCAL" ] || die "dist buildado com '$BD' ≠ $BUILD_LOCAL — version.js divergente?"
ok "dist com o carimbo $BD"

say "4/6 · cap sync ios + limpeza de assets órfãos"
npx cap sync ios >/dev/null 2>&1 || die "cap sync falhou (veja: cd web && npx cap sync ios)"
# FASE 9: o AppDelegate PERDE os callbacks do APNs quando a pasta ios/ é
# regenerada (é gitignorada) — reaplica o patch idempotente SEMPRE.
cd .. && bash scripts/ios-patch-appdelegate.sh || die "patch do AppDelegate falhou"
cd web
# FASE 9.1 (correção de bug GRAVE meu): o Vite gera VÁRIOS index-*.js — são os
# chunks dos imports dinâmicos (plugin de notificações, push, app-launcher,
# gráficos). A limpeza antiga mantinha só o de entrada e AMPUTAVA o app
# ("plugin não instalado", nada funcionava). Regra correta: dist/ é a fonte da
# verdade — órfão é APENAS o que está no public/ e NÃO existe no dist/ atual.
ORFAOS=0
for f in ios/App/App/public/assets/*; do
  b="$(basename "$f")"
  [ -f "dist/assets/$b" ] || { rm -f "$f"; ORFAOS=$((ORFAOS+1)); }
done
# paridade obrigatória: TODO chunk do dist precisa estar no bundle do iPhone
for f in dist/assets/*; do
  b="$(basename "$f")"
  [ -f "ios/App/App/public/assets/$b" ] || die "chunk $b do dist NÃO chegou ao bundle do iOS — cap sync incompleto"
done
ok "bundle sincronizado ESPELHANDO o dist ($(ls dist/assets | wc -l | tr -d ' ') chunks; $ORFAOS órfão(s) de builds antigos removidos)"

say "5/6 · Verificação final dos elos"
cd ..
verificar || warn "algum elo acima pede atenção — resolva antes do Xcode"

say "6/6 · Xcode"
echo "  Abrindo o Xcode. NO XCODE: Product → Clean Build Folder (⇧⌘K) → Run no iPhone."
echo "  Depois confira no app: Perfil → rodapé = build $BUILD_LOCAL"
cd web && npx cap open ios >/dev/null 2>&1 || warn "não deu para abrir o Xcode automaticamente — abra web/ios/App/App.xcodeproj"
