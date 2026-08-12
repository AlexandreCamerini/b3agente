#!/usr/bin/env bash
# gerar-adhoc.sh — automatiza os passos 4 do cabeçalho de publicar-ipa.sh
# (Product > Archive > Distribute App > Ad Hoc > exportar) via xcodebuild,
# e encadeia com publicar-ipa.sh pra hospedar + devolver a URL final.
#
# NÃO substitui os passos 1-3 daquele script (UDID de cada aparelho
# cadastrado no Apple Developer portal ANTES de rodar isto) — sem device
# cadastrado no perfil Ad Hoc, o export falha ou gera um .ipa que não
# instala em ninguém. Isso é manual, feito uma vez por testador novo.
#
# Assume que web/ios/App/App/public já reflete o bundle que você quer
# publicar (rode `npx cap sync ios` antes se mudou o front recentemente).
#
#   bash scripts/gerar-adhoc.sh [URL_BASE]
#   URL_BASE default: https://boris.semente.dev
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

say(){ printf "\n\033[1m== %s ==\033[0m\n" "$*"; }
ok(){ printf "  \033[32m[OK]\033[0m %s\n" "$*"; }
die(){ printf "  \033[31m[X]\033[0m %s\n" "$*" >&2; exit 1; }

BASE="${1:-https://boris.semente.dev}"
PROJ="web/ios/App/App.xcodeproj"
PBXPROJ="$PROJ/project.pbxproj"
SCHEME="BolsIA"
BUILD_DIR="build/adhoc"
ARCHIVE="$BUILD_DIR/App.xcarchive"
EXPORT_DIR="$BUILD_DIR/export"
EXPORT_PLIST="$BUILD_DIR/ExportOptions.plist"

[ -f "$PBXPROJ" ] || die "$PBXPROJ não encontrado — rode 'npx cap sync ios' primeiro"

say "0/4 · Pré-checagem: certificado de distribuição no keychain"
security find-identity -v -p codesigning | grep -q "Apple Distribution" \
  || die "Nenhum certificado 'Apple Distribution' no keychain — Xcode > Settings > Accounts > Manage Certificates."
ok "certificado encontrado"

say "1/4 · Arquivar (xcodebuild archive) — pode levar alguns minutos"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
if ! xcodebuild -project "$PROJ" -scheme "$SCHEME" -configuration Release \
     -archivePath "$ARCHIVE" -destination "generic/platform=iOS" \
     -allowProvisioningUpdates archive > "$BUILD_DIR/archive.log" 2>&1; then
  tail -80 "$BUILD_DIR/archive.log"
  die "xcodebuild archive falhou — log completo em $BUILD_DIR/archive.log"
fi
[ -d "$ARCHIVE" ] || die "arquivo .xcarchive não foi gerado (ver $BUILD_DIR/archive.log)"
ok "$ARCHIVE gerado"

say "2/4 · Exportar .ipa como Ad Hoc"
TEAM_ID="$(sed -n 's/.*DEVELOPMENT_TEAM = \([A-Z0-9]*\);.*/\1/p' "$PBXPROJ" | head -1)"
[ -n "$TEAM_ID" ] || die "DEVELOPMENT_TEAM não encontrado em $PBXPROJ"
cat > "$EXPORT_PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>method</key><string>ad-hoc</string>
	<key>teamID</key><string>$TEAM_ID</string>
	<key>signingStyle</key><string>automatic</string>
	<key>compileBitcode</key><false/>
</dict>
</plist>
PLIST
if ! xcodebuild -exportArchive -archivePath "$ARCHIVE" -exportPath "$EXPORT_DIR" \
     -exportOptionsPlist "$EXPORT_PLIST" -allowProvisioningUpdates \
     > "$BUILD_DIR/export.log" 2>&1; then
  tail -80 "$BUILD_DIR/export.log"
  die "xcodebuild -exportArchive falhou — log completo em $BUILD_DIR/export.log (causa comum: nenhum UDID de teste cadastrado no perfil Ad Hoc)"
fi
IPA="$(find "$EXPORT_DIR" -maxdepth 1 -name '*.ipa' | head -1)"
[ -n "$IPA" ] && [ -f "$IPA" ] || die ".ipa não apareceu em $EXPORT_DIR (ver $BUILD_DIR/export.log)"
ok "$IPA ($(du -h "$IPA" | cut -f1))"

say "3/4 · Publicar (server/ios_dist) via publicar-ipa.sh"
bash scripts/publicar-ipa.sh "$IPA" "$BASE"

say "4/4 · Commit + push (Railway redeploya sozinho)"
VERSION="$(sed -n 's/.*MARKETING_VERSION = \([^;]*\);.*/\1/p' "$PBXPROJ" | head -1)"
BUILD="$(sed -n 's/.*CURRENT_PROJECT_VERSION = \([^;]*\);.*/\1/p' "$PBXPROJ" | head -1)"
git add server/ios_dist
if git diff --cached --quiet; then
  echo "  nada novo em server/ios_dist (ipa idêntico ao publicado) — sem commit"
else
  git commit -m "Ad Hoc: publica boris.ipa v$VERSION build $BUILD em server/ios_dist"
  git push
fi

say "Aguardando o Railway servir o novo build"
# HTTP 200 sozinho não basta: o deploy ANTERIOR também responde 200 durante a
# janela de propagação do Railway — checa o CONTEÚDO (versão nova) até bater.
UP=0
for i in $(seq 1 30); do
  BODY="$(curl -sf "$BASE/ios/manifest.plist" || true)"
  if echo "$BODY" | grep -q "bundle-version" && echo "$BODY" | grep -q ">$VERSION<"; then
    UP=1; break
  fi
  sleep 6
done
[ "$UP" = "1" ] && ok "servidor já serve a versão $VERSION (não o deploy anterior)" \
  || echo "  aviso: ainda servindo versão anterior após ~3min — confira manualmente: $BASE/ios/manifest.plist"

echo
echo "  Abra no SAFARI DO IPHONE (obrigatório — outro navegador/app de mensagem não instala):"
echo "    $BASE/ios/"
