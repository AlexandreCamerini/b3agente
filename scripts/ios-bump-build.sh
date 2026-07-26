#!/usr/bin/env bash
# Incrementa o BUILD NUMBER (CURRENT_PROJECT_VERSION) do app iOS — cada upload ao
# TestFlight/App Store exige um build number ÚNICO e maior que o anterior.
# A MARKETING_VERSION (1.0, 1.1…) você sobe à mão quando muda a versão pública.
#
#   bash scripts/ios-bump-build.sh          # +1
#   bash scripts/ios-bump-build.sh 42       # define exatamente 42
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PBX="$REPO/web/ios/App/App.xcodeproj/project.pbxproj"
[[ -f "$PBX" ]] || { echo "[X] Não achei $PBX. Rode antes: bash scripts/setup-ios.sh && cap sync"; exit 1; }

CUR="$(grep -m1 -oE 'CURRENT_PROJECT_VERSION = [0-9]+' "$PBX" | grep -oE '[0-9]+' || echo 0)"
if [[ "${1:-}" =~ ^[0-9]+$ ]]; then NEW="$1"; else NEW="$((CUR + 1))"; fi
[[ "$NEW" -gt "$CUR" ]] || { echo "[X] novo build ($NEW) precisa ser > atual ($CUR)."; exit 1; }

# Substitui em TODAS as configs (Debug + Release).
sed -i '' "s/CURRENT_PROJECT_VERSION = [0-9]*;/CURRENT_PROJECT_VERSION = $NEW;/g" "$PBX"
MKT="$(grep -m1 -oE 'MARKETING_VERSION = [0-9.]+' "$PBX" | grep -oE '[0-9.]+' || echo '?')"
echo "[OK] build number: $CUR -> $NEW   (versão pública MARKETING_VERSION=$MKT)"
echo "    Agora no Xcode: Product > Archive > Distribute App > App Store Connect."
