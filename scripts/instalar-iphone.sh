#!/usr/bin/env bash
# instalar-iphone.sh — BolsIA (b3-agente)
# Cadeia COMPLETA de atualização do app no iPhone, com verificação em cada elo.
# É este script que garante que o plugin de notificações entra no binário —
# a causa do app nem aparecer em Ajustes -> Notificacoes era build sem sync.
#
# Uso (na raiz do repo):  bash scripts/instalar-iphone.sh [--recriar-ios]
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"

RECRIAR=0
[ "${1:-}" = "--recriar-ios" ] && RECRIAR=1

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
npm run build
ok "dist/ gerado"

if [ "$RECRIAR" = "1" ] && [ -d ios ]; then
  say "4b) --recriar-ios: removendo a pasta ios/ (plano C do erro de SPM)"
  rm -rf ios
fi

say "5) Projeto iOS"
if [ ! -d ios ]; then
  npx cap add ios
  ok "ios/ criado"
  # Reaplicar ajustes nativos que a recriação apaga:
  [ -f "$ROOT/scripts/ios-adopt-uiscene.sh" ] && bash "$ROOT/scripts/ios-adopt-uiscene.sh" || true
fi

say "6) cap sync ios (é AQUI que o plugin entra no binário)"
npx cap sync ios | tee /tmp/capsync.log
grep -q "local-notifications" /tmp/capsync.log \
  && ok "plugin de notificações SINCRONIZADO no projeto nativo" \
  || die "cap sync não listou o local-notifications — o problema das notificações continuaria. Confira o package.json e rode de novo."

say "7) Identidade: nome sob o ícone = BolsIA"
PLIST="ios/App/App/Info.plist"
if [ -f "$PLIST" ]; then
  /usr/libexec/PlistBuddy -c "Set :CFBundleDisplayName BolsIA" "$PLIST" 2>/dev/null \
    || /usr/libexec/PlistBuddy -c "Add :CFBundleDisplayName string BolsIA" "$PLIST"
  ok "CFBundleDisplayName = BolsIA"
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
      o BolsIA passa a aparecer em Ajustes -> Notificações.
   4. Teste agendado (30s) -> feche o app -> o banner deve chegar.

  Se o SPM reclamar de capacitor-swift-pm (rede/credenciais):
   a) File -> Packages -> Reset Package Caches
   b) rm -rf ~/Library/Caches/org.swift.swiftpm ~/Library/Developer/Xcode/DerivedData
   c) Xcode -> Settings -> Accounts: remova a conta GitHub com erro
   d) Último recurso: bash scripts/instalar-iphone.sh --recriar-ios
FIM
