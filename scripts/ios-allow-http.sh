#!/usr/bin/env bash
# Libera HTTP para a REDE LOCAL no app iOS (ATS NSAllowsLocalNetworking) e
# define o texto da permissao de rede local. Rode DEPOIS do setup-ios.sh
# (precisa do projeto web/ios/ ja gerado). Recompile no Xcode em seguida.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PB="/usr/libexec/PlistBuddy"
INFO="$REPO/web/ios/App/App/Info.plist"
DESC="O app acessa o backend do Boris+ na sua rede local."

[[ -x "$PB" ]] || { echo "[X] PlistBuddy nao encontrado (precisa de macOS)."; exit 1; }
[[ -f "$INFO" ]] || { echo "[X] Nao achei $INFO. Rode antes: bash scripts/setup-ios.sh --api-base http://SEU_IP:8787"; exit 1; }

"$PB" -c "Print :NSAppTransportSecurity" "$INFO" >/dev/null 2>&1 || "$PB" -c "Add :NSAppTransportSecurity dict" "$INFO"
"$PB" -c "Set :NSAppTransportSecurity:NSAllowsLocalNetworking true" "$INFO" 2>/dev/null \
  || "$PB" -c "Add :NSAppTransportSecurity:NSAllowsLocalNetworking bool true" "$INFO"
"$PB" -c "Set :NSLocalNetworkUsageDescription $DESC" "$INFO" 2>/dev/null \
  || "$PB" -c "Add :NSLocalNetworkUsageDescription string $DESC" "$INFO"

echo "[OK] ATS liberado para rede local em: $INFO"
echo "    Agora no Xcode: pare o app e clique Run de novo (Cmd+R)."
echo "    Na primeira conexao, aceite o aviso 'permitir rede local' no iPhone."
