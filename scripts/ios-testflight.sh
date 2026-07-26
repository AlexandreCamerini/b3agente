#!/usr/bin/env bash
# Prepara o app iOS para TestFlight/App Store. IDEMPOTENTE. Rode DEPOIS do
# setup-ios.sh + cap sync (precisa de web/ios/ gerado). macOS (PlistBuddy).
#
#   bash scripts/ios-testflight.sh              # aplica manifesto + Info.plist
#   bash scripts/ios-testflight.sh --apns-prod  # + vira aps-environment=production
#   bash scripts/ios-testflight.sh --apns-dev   # volta aps-environment=development
#
# O flip de APNs (--apns-prod) é COORDENADO com o servidor: remova/zere
# APNS_SANDBOX no Railway ao mesmo tempo (TestFlight usa APNs de PRODUÇÃO).
# Sem argumento, o entitlement de push NÃO é tocado (mantém o dev de hoje).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PB="/usr/libexec/PlistBuddy"
APPDIR="$REPO/web/ios/App/App"
INFO="$APPDIR/Info.plist"
ENT="$APPDIR/App.entitlements"
PBXPROJ="$REPO/web/ios/App/App.xcodeproj/project.pbxproj"
SRC_PRIVACY="$REPO/resources/ios/PrivacyInfo.xcprivacy"

APNS=""   # "", "prod" ou "dev"
for a in "$@"; do
  case "$a" in
    --apns-prod) APNS="prod" ;;
    --apns-dev)  APNS="dev" ;;
    -h|--help)   awk 'NR>1 && /^#/{sub(/^# ?/,"");print;next}{if(NR>1)exit}' "$0"; exit 0 ;;
    *) echo "[X] opção desconhecida: $a (use --help)"; exit 1 ;;
  esac
done

[[ -x "$PB" ]] || { echo "[X] PlistBuddy não encontrado (precisa de macOS)."; exit 1; }
[[ -f "$INFO" ]] || { echo "[X] Não achei $INFO. Rode antes: bash scripts/setup-ios.sh && cap sync"; exit 1; }
[[ -f "$SRC_PRIVACY" ]] || { echo "[X] Faltou resources/ios/PrivacyInfo.xcprivacy no repo."; exit 1; }

# 1) Manifesto de privacidade (obrigatório). Copia a fonte versionada.
cp "$SRC_PRIVACY" "$APPDIR/PrivacyInfo.xcprivacy"
echo "[OK] PrivacyInfo.xcprivacy copiado para o app."
if [[ -f "$PBXPROJ" ]] && ! grep -q "PrivacyInfo.xcprivacy" "$PBXPROJ"; then
  echo "[!] AÇÃO ÚNICA no Xcode: arraste web/ios/App/App/PrivacyInfo.xcprivacy para o"
  echo "    grupo 'App' e MARQUE o target 'App' (Copy items if needed). Sem isso, o"
  echo "    manifesto NÃO vai no bundle. (Persiste depois; só precisa uma vez.)"
else
  echo "[OK] PrivacyInfo.xcprivacy já referenciado no projeto."
fi

# 2) Export compliance: só HTTPS => sem criptografia não-isenta => pula o prompt.
"$PB" -c "Set :ITSAppUsesNonExemptEncryption false" "$INFO" 2>/dev/null \
  || "$PB" -c "Add :ITSAppUsesNonExemptEncryption bool false" "$INFO"
echo "[OK] ITSAppUsesNonExemptEncryption=false (sem prompt de export a cada upload)."

# 3) APNs (opcional, coordenado com o servidor)
if [[ -n "$APNS" && -f "$ENT" ]]; then
  VAL="development"; [[ "$APNS" == "prod" ]] && VAL="production"
  "$PB" -c "Set :aps-environment $VAL" "$ENT" 2>/dev/null \
    || "$PB" -c "Add :aps-environment string $VAL" "$ENT"
  echo "[OK] aps-environment=$VAL"
  if [[ "$APNS" == "prod" ]]; then
    echo "[!] AGORA no Railway: remova/zere APNS_SANDBOX (TestFlight usa APNs de produção)."
  else
    echo "[!] AGORA no Railway: APNS_SANDBOX=1 (build de Xcode usa APNs de sandbox)."
  fi
elif [[ -n "$APNS" ]]; then
  echo "[X] Não achei $ENT — o entitlement de push não foi tocado."
fi

echo
echo "Próximos passos: veja TESTFLIGHT.md. Para incrementar o build: bash scripts/ios-bump-build.sh"
