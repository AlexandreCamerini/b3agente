#!/usr/bin/env bash
# ios-patch-appdelegate.sh — BolsIA · reaplica o bloco APNs→Capacitor no
# AppDelegate.swift. IDEMPOTENTE (rodar 2× não duplica).
#
# POR QUE EXISTE: web/ios/ é gitignorado e é REGENERADO por setup-ios.sh /
# atualizações do Capacitor — quando isso acontece, o AppDelegate volta ao
# template e PERDE os callbacks do push (o register() do JS passa a dar
# timeout). Já aconteceu em produção; o guardião test_push_wiring.mjs acusa e
# ESTE script conserta. O entregar.sh o roda automaticamente após o cap sync.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.."
F="web/ios/App/App/AppDelegate.swift"
[ -f "$F" ] || { echo "[X] $F não existe — rode 'bash scripts/setup-ios.sh' antes."; exit 1; }

if grep -q "capacitorDidRegisterForRemoteNotifications" "$F"; then
  echo "[OK] AppDelegate já tem os callbacks do APNs (nada a fazer)"
  exit 0
fi

# insere o bloco imediatamente antes do marker do UIScene (sempre presente no
# template do projeto) ou, na falta dele, antes da última chave do arquivo.
python3 - "$F" << 'PY'
import sys

path = sys.argv[1]
src = open(path, encoding="utf-8").read()

BLOCO = """
    // MARK: - Push (APNs) -> Capacitor (FASE 6/9 - NAO REMOVER)
    // O plugin @capacitor/push-notifications SO resolve o register() do JS
    // quando o AppDelegate reencaminha estes dois callbacks via
    // NotificationCenter. Este bloco e reaplicado automaticamente por
    // scripts/ios-patch-appdelegate.sh (web/ios/ e gitignorado e regeneravel).
    func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        NotificationCenter.default.post(name: .capacitorDidRegisterForRemoteNotifications, object: deviceToken)
    }

    func application(_ application: UIApplication, didFailToRegisterForRemoteNotificationsWithError error: Error) {
        NotificationCenter.default.post(name: .capacitorDidFailToRegisterForRemoteNotifications, object: error)
    }
"""

marker = "    // MARK: - UIScene lifecycle"
if marker in src:
    src = src.replace(marker, BLOCO + "\n" + marker, 1)
else:
    # fallback: antes do fechamento da classe AppDelegate (última "}" dupla)
    idx = src.rstrip().rfind("\n}")
    src = src[:idx] + BLOCO + src[idx:]

open(path, "w", encoding="utf-8").write(src)
print("[OK] callbacks do APNs reaplicados no AppDelegate")
PY
