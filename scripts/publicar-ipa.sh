#!/usr/bin/env bash
# publicar-ipa.sh — hospeda um .ipa Ad Hoc no Railway (server/ios_dist), com
# link itms-services para instalar direto no iPhone SEM passar pelo TestFlight.
#
# NÃO é distribuição pública: só instala em aparelhos cujo UDID foi
# registrado no Apple Developer portal ANTES de gerar este build.
#
# PRÉ-REQUISITOS (fora deste script, manuais, com sua conta Apple):
#   1. Pegue o UDID de cada aparelho de teste: plugue o iPhone no Mac e abra
#      Xcode > Window > Devices and Simulators (ou Apple Configurator 2).
#      NÃO existe atalho remoto/web confiável para isto — é por USB mesmo.
#   2. developer.apple.com > Certificates, IDs & Profiles > Devices > cadastre
#      cada UDID.
#   3. Gere/confirme um provisioning profile "Ad Hoc" que INCLUA esses
#      aparelhos (Automatically manage signing cobre isso se os devices já
#      estiverem cadastrados antes do Archive).
#   4. No Xcode: Product > Archive > Distribute App > "Ad Hoc" (NUNCA
#      "App Store Connect" — é outro fluxo) > exporte o .ipa para um caminho
#      local.
#
#   bash scripts/publicar-ipa.sh /caminho/para/o-seu.ipa [URL_BASE]
#   URL_BASE default: https://boris.semente.dev
#
# Depois: revise, rode a suíte, commit + push (Railway redeploya sozinho).
# Cada novo testador = repita 1-4 (o app precisa ser reexportado incluindo o
# UDID dele) — isto NÃO é mais simples que o TestFlight a médio prazo; use
# quando quiser instalar num punhado de aparelhos já conhecidos, hoje.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

say(){ printf "\n\033[1m== %s ==\033[0m\n" "$*"; }
ok(){ printf "  \033[32m[OK]\033[0m %s\n" "$*"; }
die(){ printf "  \033[31m[X]\033[0m %s\n" "$*" >&2; exit 1; }

IPA="${1:-}"
BASE="${2:-https://boris.semente.dev}"
[ -n "$IPA" ] && [ -f "$IPA" ] || die "uso: bash scripts/publicar-ipa.sh /caminho/para/o-seu.ipa [URL_BASE]"

PBXPROJ="web/ios/App/App.xcodeproj/project.pbxproj"
[ -f "$PBXPROJ" ] || die "$PBXPROJ não encontrado — rode 'npx cap sync ios' primeiro"
VERSION="$(sed -n 's/.*MARKETING_VERSION = \([^;]*\);.*/\1/p' "$PBXPROJ" | head -1)"
BUILD="$(sed -n 's/.*CURRENT_PROJECT_VERSION = \([^;]*\);.*/\1/p' "$PBXPROJ" | head -1)"
[ -n "$VERSION" ] || die "MARKETING_VERSION não encontrada no pbxproj"

say "1/3 · Copiar o .ipa para server/ios_dist (única árvore que o Railway enxerga)"
mkdir -p server/ios_dist
cp "$IPA" server/ios_dist/boris.ipa
ok "server/ios_dist/boris.ipa ($(du -h server/ios_dist/boris.ipa | cut -f1)) — versão $VERSION build $BUILD"

say "2/3 · Gerar manifest.plist"
cat > server/ios_dist/manifest.plist <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>items</key>
	<array>
		<dict>
			<key>assets</key>
			<array>
				<dict>
					<key>kind</key>
					<string>software-package</string>
					<key>url</key>
					<string>$BASE/ios/boris.ipa</string>
				</dict>
			</array>
			<key>metadata</key>
			<dict>
				<key>bundle-identifier</key>
				<string>com.alexandrecamerini.bolsia</string>
				<key>bundle-version</key>
				<string>$VERSION</string>
				<key>kind</key>
				<string>software</string>
				<key>title</key>
				<string>Boris+</string>
			</dict>
		</dict>
	</array>
</plist>
PLIST
ok "manifest.plist gerado (versão $VERSION, ipa em $BASE/ios/boris.ipa)"

say "3/3 · Gerar página de instalação (server/ios_dist/index.html)"
cat > server/ios_dist/index.html <<HTML
<!doctype html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Instalar Boris+</title>
<style>
body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#0b0e14;
color:#eee;text-align:center;padding:3rem 1.5rem;margin:0}
h1{color:#eec96b}
a.btn{display:inline-block;margin-top:2rem;padding:1rem 2.2rem;background:#c9972c;
color:#151515;font-weight:700;border-radius:12px;text-decoration:none;font-size:1.1rem}
p.aviso{color:#999;font-size:.9rem;margin-top:2.5rem;max-width:32em;margin-left:auto;
margin-right:auto;line-height:1.5}
</style></head>
<body>
<h1>Boris+</h1>
<p>Instalação direta (Ad Hoc) — versão $VERSION.</p>
<p>Só funciona em aparelhos já cadastrados para este build.</p>
<a class="btn" href="itms-services://?action=download-manifest&url=$BASE/ios/manifest.plist">Instalar no iPhone</a>
<p class="aviso">Abra este link no <b>Safari do iPhone</b> — não funciona em outro
navegador nem em apps de mensagem que renderizam preview do link. Depois de tocar
em "Instalar", confirme em Ajustes se pedir para confiar no desenvolvedor.</p>
</body></html>
HTML
ok "index.html gerado"

echo
echo "  Próximo passo (MANUAL, este script não commita/pushega):"
echo "    git add server/ios_dist"
echo "    git commit -m \"...\" && git push"
echo "  Link para o testador abrir NO SAFARI DO IPHONE:"
echo "    $BASE/ios/"
