#!/usr/bin/env bash
# distribuir-iphone.sh — Boris+ (b3-agente) · script MASTER de distribuição
# iOS: confere que o diretório atual está promovido (== origin/main), builda
# contra PRODUÇÃO, sincroniza o projeto nativo e, na hora de instalar, você
# escolhe o canal.
#
#   bash scripts/distribuir-iphone.sh                  # pergunta o canal (Xcode/TestFlight)
#   bash scripts/distribuir-iphone.sh --xcode           # Run direto no seu iPhone, sem perguntar
#   bash scripts/distribuir-iphone.sh --testflight       # arquiva pra App Store Connect, sem perguntar
#   bash scripts/distribuir-iphone.sh --skip-testes      # pula a suíte canônica (retry rápido)
#   bash scripts/distribuir-iphone.sh --no-update        # não toca em git; usa o diretório atual como está no disco
#   bash scripts/distribuir-iphone.sh --recriar-ios      # repassado ao instalar-iphone.sh
#
# Orquestra scripts EXISTENTES, não duplica lógica:
#   instalar-iphone.sh (build web + cap sync + entitlements/AppDelegate),
#   ios-testflight.sh (manifesto de privacidade + export compliance),
#   ios-bump-build.sh (build number).
#
# POR QUE OPERA NO DIRETÓRIO ATUAL, NÃO MAIS CAÇA WORKTREE DO MAIN
# (2026-09-22, revisão da regra de 2026-09-09): o que se distribui pra um
# aparelho real precisa ser o código já PROMOVIDO — isso não mudou. Mas
# "promovido" agora é verificado por CONTEÚDO (HEAD == origin/main), não por
# NOME de branch: até 2026-09-22 este script sempre redirecionava pro
# worktree que tivesse `main` checked out, o que gerou dois projetos Xcode
# físicos diferentes (`web/ios/`, gitignored, um por worktree) e um Archive
# fantasma apontado pro backend local — confusão real em produção. A partir
# desta revisão, `git worktree list` só é consultado como fallback SE o
# diretório atual estiver divergente de origin/main (nunca redireciona por
# nome de branch); o caso comum (branch de trabalho já mantida idêntica ao
# main, como `v2/interacao-estrutural` neste repo) segue direto sem trocar
# de diretório.
#
# NUNCA aponta pra staging: script de distribuição não deveria nem oferecer
# isso por acidente (--staging/--api-base do instalar-iphone.sh não são
# repassados). NUNCA flipa APNs pra produção — isso é coordenado com o
# Railway, ação separada e manual (ver TESTFLIGHT.md item 9-10).
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.."

say(){ printf "\n\033[1m== %s ==\033[0m\n" "$*"; }
ok(){ printf "  \033[32m[OK]\033[0m %s\n" "$*"; }
warn(){ printf "  \033[33m[!]\033[0m %s\n" "$*"; }
die(){ printf "  \033[31m[X]\033[0m %s\n" "$*" >&2; exit 1; }

CANAL=""          # "" = pergunta; "xcode" | "testflight"
SKIP_TESTES=0
NO_UPDATE=0
RECRIAR=0
for a in "$@"; do
  case "$a" in
    --xcode)       CANAL="xcode" ;;
    --testflight)  CANAL="testflight" ;;
    --skip-testes) SKIP_TESTES=1 ;;
    --no-update)   NO_UPDATE=1 ;;
    --recriar-ios) RECRIAR=1 ;;
    -h|--help)     awk 'NR>1 && /^#/{sub(/^# ?/,"");print;next}{if(NR>1)exit}' "$0"; exit 0 ;;
    *) die "opção desconhecida: $a (use --help)" ;;
  esac
done

say "1/6 · Diretório de trabalho"
ROOT="$(pwd)"
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")"
ok "operando aqui mesmo: $ROOT (branch $CURRENT_BRANCH)"

if [ "$NO_UPDATE" = "1" ]; then
  say "2/6 · Atualização PULADA (--no-update) — usando $ROOT como está"
else
  say "2/6 · Verificando se $CURRENT_BRANCH está promovido (== origin/main)"
  git diff --quiet && git diff --cached --quiet \
    || die "$ROOT tem mudanças não commitadas — commite/descarte antes (nunca faço isso por você)"
  git fetch origin --quiet || die "git fetch falhou — sem rede? confira e rode de novo"
  LOCAL="$(git rev-parse HEAD)"; REMOTO="$(git rev-parse origin/main)"
  if [ "$LOCAL" = "$REMOTO" ]; then
    ok "$CURRENT_BRANCH já está em dia com origin/main ($LOCAL)"
  else
    git merge --ff-only origin/main \
      || die "$CURRENT_BRANCH diverge de origin/main (não é fast-forward) — resolva manualmente em $ROOT, NUNCA force nada. Se preferir buildar de um worktree que já tem main promovido, rode de lá."
    ok "$CURRENT_BRANCH atualizado: $LOCAL -> $(git rev-parse HEAD)"
  fi
fi

if [ "$SKIP_TESTES" = "1" ]; then
  say "3/6 · Suíte canônica PULADA (--skip-testes)"
else
  say "3/6 · Suíte canônica (pega código quebrado ANTES de empacotar)"
  bash scripts/executar.sh --testes \
    || die "suíte falhou — NÃO distribua um build quebrado. Rode com --skip-testes só se souber exatamente por quê."
  ok "suíte verde"
fi

say "4/6 · Build web + sincronização do projeto iOS (contra PRODUÇÃO)"
ARGS_INSTALAR=(--no-open)
[ "$RECRIAR" = "1" ] && ARGS_INSTALAR+=(--recriar-ios)
bash "$ROOT/scripts/instalar-iphone.sh" "${ARGS_INSTALAR[@]}" \
  || die "instalar-iphone.sh falhou — veja a mensagem acima"

if [ -z "$CANAL" ]; then
  say "5/6 · Escolha do canal de distribuição"
  while true; do
    printf "  [1] Xcode — instala DIRETO no seu iPhone agora\n"
    printf "  [2] TestFlight — arquiva pra upload à App Store Connect\n"
    read -r -p "  Escolha (1/2): " RESP
    case "$RESP" in
      1) CANAL="xcode"; break ;;
      2) CANAL="testflight"; break ;;
      *) echo "  responda 1 ou 2" ;;
    esac
  done
else
  say "5/6 · Canal escolhido via flag: $CANAL"
fi

cd "$ROOT/web"
PB="/usr/libexec/PlistBuddy"
ENT="ios/App/App/App.entitlements"

if [ "$CANAL" = "testflight" ]; then
  say "6/6 · Preparando para TestFlight"
  bash "$ROOT/scripts/ios-testflight.sh" \
    || die "ios-testflight.sh falhou — veja a mensagem acima"
  bash "$ROOT/scripts/ios-bump-build.sh" \
    || die "ios-bump-build.sh falhou — veja a mensagem acima"
  say "Abrindo o Xcode"
  if ! npx cap open ios; then
    if [ -d ios/App/App.xcworkspace ]; then open ios/App/App.xcworkspace
    elif [ -d ios/App/App.xcodeproj ]; then open ios/App/App.xcodeproj
    fi
  fi
  cat << 'FIM'

  PASSOS FINAIS (no Xcode, TestFlight):
   1. Destino: "Any iOS Device (arm64)" — NÃO um simulador, NÃO o seu iPhone.
   2. Product -> Archive.
   3. Organizer -> Distribute App -> App Store Connect -> Upload.
      Assinatura Automatic cuida do provisioning.
   4. Aguarde o processamento em App Store Connect -> TestFlight (minutos).
   5. Adicione o build ao grupo de testers e convide.

  Uma vez só, se ainda não fez: arraste web/ios/App/App/PrivacyInfo.xcprivacy
  para o grupo "App" no Xcode e marque o target "App" — sem isso a Apple
  rejeita o processamento (ios-testflight.sh já avisou acima se faltar).
FIM
else
  say "6/6 · Pronto para Run direto no Xcode"
  if ! npx cap open ios; then
    if [ -d ios/App/App.xcworkspace ]; then open ios/App/App.xcworkspace
    elif [ -d ios/App/App.xcodeproj ]; then open ios/App/App.xcodeproj
    fi
  fi
  cat << 'FIM'

  PASSOS FINAIS (no Xcode, Run direto):
   1. Selecione o SEU IPHONE no topo (não o simulador).
   2. Product -> Run (▶). Aguarde instalar no aparelho.
FIM
fi

say "Resumo"
BASE_BUNDLE="$(grep -rhoE "https://[a-z0-9.-]*\.(semente\.dev|railway\.app)" ios/App/App/public/assets/*.js 2>/dev/null | sort -u | head -1)"
BUILD_ID_BUNDLE="$(grep -rhoE "F10-[0-9]{8}-[0-9]{2}" ios/App/App/public/assets/*.js 2>/dev/null | sort -u | head -1)"
MKT="$(grep -m1 -oE 'MARKETING_VERSION = [0-9.]+' ios/App/App.xcodeproj/project.pbxproj | grep -oE '[0-9.]+')"
BUILDNUM="$(grep -m1 -oE 'CURRENT_PROJECT_VERSION = [0-9]+' ios/App/App.xcodeproj/project.pbxproj | grep -oE '[0-9]+')"
APNS_ENV="$([ -f "$ENT" ] && "$PB" -c "Print aps-environment" "$ENT" 2>/dev/null || echo "ausente")"
echo "  backend embutido:  ${BASE_BUNDLE:-desconhecido}"
echo "  carimbo do bundle: ${BUILD_ID_BUNDLE:-desconhecido}"
echo "  versão / build:    ${MKT:-?} / ${BUILDNUM:-?}"
echo "  aps-environment:   $APNS_ENV"
if [ "$CANAL" = "testflight" ] && [ "$APNS_ENV" = "development" ]; then
  warn "push está em development — TestFlight/App Store usam APNs de PRODUÇÃO."
  warn "push NÃO vai chegar neste build até você rodar (coordenado com o Railway):"
  warn "  bash scripts/ios-testflight.sh --apns-prod   +   zerar APNS_SANDBOX no Railway"
fi
if [ ! -f "$ROOT/web/.env.local" ]; then
  warn "web/.env.local ausente — login Google falha no aparelho (Apple/SIWA e e-mail/senha OK)."
fi
