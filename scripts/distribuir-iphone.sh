#!/usr/bin/env bash
# distribuir-iphone.sh — Boris+ (b3-agente) · script MASTER de distribuição
# iOS: atualiza `main` para o que está publicado, builda contra PRODUÇÃO,
# sincroniza o projeto nativo e, na hora de instalar, você escolhe o canal.
#
#   bash scripts/distribuir-iphone.sh                  # pergunta o canal (Xcode/TestFlight)
#   bash scripts/distribuir-iphone.sh --xcode           # Run direto no seu iPhone, sem perguntar
#   bash scripts/distribuir-iphone.sh --testflight       # arquiva pra App Store Connect, sem perguntar
#   bash scripts/distribuir-iphone.sh --skip-testes      # pula a suíte canônica (retry rápido)
#   bash scripts/distribuir-iphone.sh --no-update        # não toca em git; usa main como está no disco
#   bash scripts/distribuir-iphone.sh --recriar-ios      # repassado ao instalar-iphone.sh
#
# Orquestra scripts EXISTENTES, não duplica lógica:
#   instalar-iphone.sh (build web + cap sync + entitlements/AppDelegate),
#   ios-testflight.sh (manifesto de privacidade + export compliance),
#   ios-bump-build.sh (build number).
#
# POR QUE ATUALIZAR `main` E NÃO A BRANCH ATUAL (2026-09-09): o que se
# distribui pra um aparelho real é sempre o código já PROMOVIDO — a branch de
# trabalho pode estar em qualquer estado intermediário. `main` costuma estar
# num checkout PERMANENTE noutro worktree deste repo (`git worktree list`);
# este script localiza esse worktree e opera de dentro dele, em vez de tentar
# `git checkout main` aqui (o git recusa: "already used by worktree").
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

say "1/6 · Localizando o worktree de main"
MAIN_DIR=""
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")"
if [ "$CURRENT_BRANCH" = "main" ]; then
  MAIN_DIR="$(pwd)"
  ok "já estamos em main, aqui mesmo: $MAIN_DIR"
else
  # `git worktree list --porcelain` imprime blocos "worktree <path>" seguidos
  # de "branch refs/heads/<nome>" — paramos no primeiro cujo branch é main.
  while IFS= read -r linha; do
    case "$linha" in
      worktree\ *) CAND="${linha#worktree }" ;;
      branch\ refs/heads/main) MAIN_DIR="$CAND"; break ;;
    esac
  done < <(git worktree list --porcelain)
  if [ -n "$MAIN_DIR" ]; then
    ok "main está em outro worktree: $MAIN_DIR"
  else
    warn "nenhum worktree tem main checked out — tentando aqui mesmo"
    MAIN_DIR="$(pwd)"
  fi
fi
cd "$MAIN_DIR" || die "não consegui entrar em $MAIN_DIR"
ROOT="$(pwd)"

if [ "$NO_UPDATE" = "1" ]; then
  say "2/6 · Atualização PULADA (--no-update) — usando main como está em $ROOT"
else
  say "2/6 · Atualizando main"
  [ "$(git rev-parse --abbrev-ref HEAD)" = "main" ] || {
    git diff --quiet && git diff --cached --quiet \
      || die "$ROOT tem mudanças não commitadas — commite/descarte antes (nunca faço isso por você)"
    git checkout main || die "não consegui trocar para main em $ROOT"
  }
  git diff --quiet && git diff --cached --quiet \
    || die "main em $ROOT tem mudanças não commitadas — commite/descarte antes de distribuir"
  git fetch origin --quiet || die "git fetch falhou — sem rede? confira e rode de novo"
  LOCAL="$(git rev-parse main)"; REMOTO="$(git rev-parse origin/main)"
  if [ "$LOCAL" = "$REMOTO" ]; then
    ok "main já está em dia com origin/main ($LOCAL)"
  else
    git merge --ff-only origin/main \
      || die "main diverge de origin/main (não é fast-forward) — resolva manualmente em $ROOT, NUNCA force nada"
    ok "main atualizado: $LOCAL -> $(git rev-parse main)"
  fi
fi

if [ "$SKIP_TESTES" = "1" ]; then
  say "3/6 · Suíte canônica PULADA (--skip-testes)"
else
  say "3/6 · Suíte canônica em main (pega código quebrado ANTES de empacotar)"
  bash scripts/executar.sh --testes \
    || die "suíte falhou em main — NÃO distribua um build quebrado. Rode com --skip-testes só se souber exatamente por quê."
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
