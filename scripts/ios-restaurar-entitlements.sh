#!/usr/bin/env bash
# ios-restaurar-entitlements.sh — recria `App.entitlements` quando o projeto
# iOS nasce do zero.
#
# POR QUE EXISTE (2026-09-07, achado ao vivo): `web/ios/` está no .gitignore,
# então um clone/worktree novo não o tem. O `instalar-iphone.sh` roda
# `npx cap add ios`, que gera o projeto JÁ apontando para
# `CODE_SIGN_ENTITLEMENTS = App/App.entitlements` no pbxproj — mas NÃO cria o
# arquivo. Resultado: build passa, app instala, e o Sign in with Apple falha
# no aparelho com "Login não pode ser completado" (authorization error), sem
# nenhuma chamada chegar ao servidor. O push morre pela mesma ausência
# (`aps-environment`), só que mais silenciosamente.
#
# O `instalar-iphone.sh` já reaplicava UM ajuste nativo após recriar o projeto
# (`ios-adopt-uiscene.sh`); faltava este. Mesmo padrão, mesma razão.
#
# Conteúdo canônico conferido contra o clone que gerou o app de produção
# (`~/dev/bolsia/b3-agente/web/ios/App/App/App.entitlements`, projeto de
# 2026-07-08).
#
# Uso:
#   bash scripts/ios-restaurar-entitlements.sh                 # aps-environment=development
#   bash scripts/ios-restaurar-entitlements.sh --producao      # aps-environment=production
#
# `development` serve para rodar pelo cabo/Xcode. TestFlight e App Store
# exigem `production` — é o que o `ios-testflight.sh` precisa. Errar isso faz
# o push parar de chegar sem erro visível no build.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.."

APS="development"
[ "${1:-}" = "--producao" ] && APS="production"

PLIST="web/ios/App/App/App.entitlements"
PBX="web/ios/App/App.xcodeproj/project.pbxproj"

ok(){ printf "  \033[32m[OK]\033[0m %s\n" "$*"; }
warn(){ printf "  \033[33m[!]\033[0m %s\n" "$*"; }
die(){ printf "  \033[31m[X]\033[0m %s\n" "$*" >&2; exit 1; }

[ -d web/ios ] || die "web/ios não existe — rode o instalar-iphone.sh primeiro"

# Idempotente: se já existe com o applesignin, só ajusta o aps-environment se
# preciso. Nunca sobrescreve um arquivo que o usuário tenha estendido à mão
# com outras capabilities (iCloud, Associated Domains, etc.) — perder isso em
# silêncio seria pior que o bug original.
if [ -f "$PLIST" ]; then
  if grep -q "com.apple.developer.applesignin" "$PLIST"; then
    ATUAL="$(sed -n 's/.*<key>aps-environment<\/key>[[:space:]]*<string>\([^<]*\)<\/string>.*/\1/p' \
             "$(printf '%s' "$PLIST")" 2>/dev/null | head -1)"
    if [ -z "$ATUAL" ]; then
      ATUAL="$(tr -d '\n' < "$PLIST" | sed -n 's/.*aps-environment<\/key>[[:space:]]*<string>\([^<]*\)<\/string>.*/\1/p')"
    fi
    if [ "$ATUAL" = "$APS" ]; then
      ok "entitlements já corretos (applesignin + aps-environment=$APS)"
      exit 0
    fi
    warn "entitlements existem com aps-environment='$ATUAL', esperado '$APS'"
    warn "NÃO vou sobrescrever — pode conter capabilities adicionadas à mão."
    warn "Ajuste manualmente em $PLIST, ou apague o arquivo e rode de novo."
    exit 1
  fi
  warn "$PLIST existe mas SEM com.apple.developer.applesignin"
  warn "NÃO vou sobrescrever — revise o arquivo à mão (ou apague e rode de novo)."
  exit 1
fi

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>aps-environment</key>
	<string>$APS</string>
	<key>com.apple.developer.applesignin</key>
	<array>
		<string>Default</string>
	</array>
</dict>
</plist>
EOF
ok "App.entitlements criado (applesignin + aps-environment=$APS)"

# O pbxproj do Capacitor já referencia o arquivo; se não referenciar, o Xcode
# ignora o entitlements em silêncio e o bug volta idêntico.
if [ -f "$PBX" ] && grep -q "CODE_SIGN_ENTITLEMENTS = App/App.entitlements" "$PBX"; then
  ok "pbxproj já aponta para App/App.entitlements"
else
  warn "pbxproj NÃO referencia App/App.entitlements — o arquivo será ignorado."
  warn "No Xcode: target App → Build Settings → Code Signing Entitlements"
  warn "  = App/App.entitlements"
fi
