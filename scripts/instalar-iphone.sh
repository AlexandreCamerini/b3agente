#!/usr/bin/env bash
# instalar-iphone.sh — Boris+ (b3-agente)
# Cadeia COMPLETA de atualização do app no iPhone, com verificação em cada elo.
# É este script que garante que o plugin de notificações entra no binário —
# a causa do app nem aparecer em Ajustes -> Notificacoes era build sem sync.
#
# Uso (na raiz do repo):
#   bash scripts/instalar-iphone.sh                  # aponta para PRODUÇÃO (default)
#   bash scripts/instalar-iphone.sh --staging        # aponta para o backend de STAGING
#   bash scripts/instalar-iphone.sh --api-base URL   # aponta para uma URL qualquer
#   (--recriar-ios continua valendo, combinável com os acima)
#
# POR QUE O ALVO DA API IMPORTA AQUI (2026-09-07): o bundle web fica EMBUTIDO
# no binário, e `web/src/api.js` resolve o endereço na ordem
# `override manual > VITE_API_BASE do build > PROD_BASE`. Buildar sem
# VITE_API_BASE produz um app que fala com PRODUÇÃO — instalar uma UI de
# staging assim escreveria no banco real. O alvo agora é impresso antes e
# CONFERIDO no dist depois do build, não é só um comentário.
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"

STAGING_API="https://b3agente-staging.up.railway.app"
PROD_API="https://boris.semente.dev"

RECRIAR=0
API_BASE=""          # vazio = default do app (PROD_BASE, ver api.js)
ALVO_ROTULO="PRODUÇÃO (default do app)"
while [ $# -gt 0 ]; do
  case "$1" in
    --recriar-ios) RECRIAR=1; shift;;
    --staging)     API_BASE="$STAGING_API"; ALVO_ROTULO="STAGING"; shift;;
    --api-base)    [ -n "${2:-}" ] || { echo "--api-base exige uma URL" >&2; exit 1; }
                   API_BASE="$2"; ALVO_ROTULO="CUSTOM"; shift 2;;
    *) echo "opção desconhecida: $1" >&2; exit 1;;
  esac
done
API_EFETIVA="${API_BASE:-$PROD_API}"

say(){ printf "\n\033[1m== %s ==\033[0m\n" "$*"; }
ok(){ printf "  \033[32m[OK]\033[0m %s\n" "$*"; }
die(){ printf "  \033[31m[X]\033[0m %s\n" "$*" >&2; exit 1; }

say "1) Pré-requisitos"
command -v node >/dev/null || die "node não encontrado"
command -v npm  >/dev/null || die "npm não encontrado"
command -v xcodebuild >/dev/null || die "Xcode não encontrado (instale pela App Store)"
ok "node $(node -v) · npm $(npm -v)"

say "2) Dependências web (inclui @capacitor/local-notifications)"
cd "$ROOT/web"
npm install --no-audit --no-fund
node -e "require.resolve('@capacitor/local-notifications/package.json')" \
  && ok "@capacitor/local-notifications presente no node_modules" \
  || die "plugin de notificações ausente — confira o package.json"

say "3) Ícone e splash (fonte única: resources/icon-1024.png)"
if [ -f "$ROOT/resources/icon-1024.png" ]; then
  bash "$ROOT/scripts/gen-assets.sh" || die "geração de assets falhou"
else
  echo "  [!] resources/icon-1024.png não encontrado — pulando assets"
fi

say "4) Build web"
printf "\n  \033[1m>>> BACKEND ALVO: %s\033[0m\n" "$ALVO_ROTULO"
printf "      %s\n\n" "$API_EFETIVA"
if [ -n "$API_BASE" ]; then
  VITE_API_BASE="$API_BASE" npm run build
else
  npm run build
fi
ok "dist/ gerado"

# Conferência real, não confiança: o endereço tem que estar DENTRO do bundle.
# Pega o erro clássico de esquecer a flag e instalar UI nova contra o banco
# de produção.
if [ -n "$API_BASE" ]; then
  grep -rqF "$API_BASE" dist/assets/*.js \
    || die "o dist NÃO contém $API_BASE — o build ignorou VITE_API_BASE; NÃO instale, o app falaria com produção"
  ok "confirmado no bundle: $API_BASE"
else
  grep -rqF "$STAGING_API" dist/assets/*.js \
    && die "o dist contém a URL de STAGING sem a flag --staging — build sujo, rode 'rm -rf web/dist' e repita" \
    || ok "build sem VITE_API_BASE (o app usará $PROD_API)"
fi

if [ "$RECRIAR" = "1" ] && [ -d ios ]; then
  say "4b) --recriar-ios: removendo a pasta ios/ (plano C do erro de SPM)"
  rm -rf ios
fi

say "5) Projeto iOS"
if [ ! -d ios ]; then
  npx cap add ios
  ok "ios/ criado"
  # Reaplicar ajustes nativos que a recriação apaga. `web/ios/` está no
  # .gitignore, então TODO clone/worktree novo passa por aqui.
  [ -f "$ROOT/scripts/ios-adopt-uiscene.sh" ] && bash "$ROOT/scripts/ios-adopt-uiscene.sh" || true
  # 2026-09-07: sem isto o Sign in with Apple falha no aparelho com
  # "Login não pode ser completado", e o push morre calado — `cap add ios`
  # referencia App.entitlements no pbxproj mas não cria o arquivo.
  bash "$ROOT/scripts/ios-restaurar-entitlements.sh" \
    || die "não consegui restaurar os entitlements — sem eles o login Apple e o push falham no aparelho"
fi

# Rede de segurança: vale também para um web/ios/ que já existia mas nasceu
# sem entitlements (exatamente o caso que originou este guard).
# Caminho ABSOLUTO de propósito: neste ponto o cwd é $ROOT/web, não $ROOT.
if [ ! -f "$ROOT/web/ios/App/App/App.entitlements" ]; then
  bash "$ROOT/scripts/ios-restaurar-entitlements.sh" \
    || die "entitlements ausentes e não foi possível criá-los"
fi

say "6) cap sync ios (é AQUI que o plugin entra no binário)"
npx cap sync ios | tee /tmp/capsync.log
grep -q "local-notifications" /tmp/capsync.log \
  && ok "plugin de notificações SINCRONIZADO no projeto nativo" \
  || die "cap sync não listou o local-notifications — o problema das notificações continuaria. Confira o package.json e rode de novo."

say "7) Identidade: nome sob o ícone = Boris+"
PLIST="ios/App/App/Info.plist"
if [ -f "$PLIST" ]; then
  /usr/libexec/PlistBuddy -c "Set :CFBundleDisplayName Boris+" "$PLIST" 2>/dev/null \
    || /usr/libexec/PlistBuddy -c "Add :CFBundleDisplayName string Boris+" "$PLIST"
  ok "CFBundleDisplayName = Boris+"
fi

say "8) Abrindo o Xcode"
# Projeto é 100% SPM (sem CocoaPods) — o arquivo certo é o .xcodeproj.
if ! npx cap open ios; then
  if [ -d ios/App/App.xcworkspace ]; then open ios/App/App.xcworkspace
  elif [ -d ios/App/App.xcodeproj ]; then open ios/App/App.xcodeproj
  fi
fi
cat << 'FIM'

  PASSOS FINAIS (no Xcode):
   1. Selecione o SEU IPHONE no topo (não o simulador).
   2. Product -> Run (▶). Aguarde instalar no aparelho.
   3. No app: Perfil -> Config -> Notificações -> botão DIAGNÓSTICO.
      Esperado: plugin carregado = true. Toque "Pedir permissão" ->
      o Boris+ passa a aparecer em Ajustes -> Notificações.
   4. Teste agendado (30s) -> feche o app -> o banner deve chegar.

  Se o SPM reclamar de capacitor-swift-pm (rede/credenciais):
   a) File -> Packages -> Reset Package Caches
   b) rm -rf ~/Library/Caches/org.swift.swiftpm ~/Library/Developer/Xcode/DerivedData
   c) Xcode -> Settings -> Accounts: remova a conta GitHub com erro
   d) Último recurso: bash scripts/instalar-iphone.sh --recriar-ios
FIM
