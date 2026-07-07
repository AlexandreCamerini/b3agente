#!/usr/bin/env bash
# gen-assets.sh — gera TODOS os ícones (AppIcon.appiconset completo, incl.
# 1024 da App Store) e splash a partir da fonte única resources/icon-1024.png.
# Versionado porque recriar a pasta ios/ apaga assets colocados à mão.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f resources/icon-1024.png ] || { echo "resources/icon-1024.png não existe"; exit 1; }
cp resources/icon-1024.png resources/icon.png            # nome que a ferramenta espera
[ -f resources/splash.png ] || cp resources/icon-1024.png resources/splash.png
cd web
npx --yes @capacitor/assets generate --ios --assetPath ../resources
echo "[OK] AppIcon + splash gerados no projeto iOS"
# Paridade web/PWA: usa a mesma arte no favicon/apple-touch-icon
python3 - << 'PY' 2>/dev/null || true
from PIL import Image
img = Image.open("../resources/icon-1024.png")
img.resize((180,180)).save("public/apple-touch-icon.png")
img.resize((192,192)).save("public/icon-192.png")
img.resize((512,512)).save("public/icon-512.png")
print("[OK] ícones web atualizados com a mesma arte")
PY
