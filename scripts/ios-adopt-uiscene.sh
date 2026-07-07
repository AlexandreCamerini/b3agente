#!/usr/bin/env bash
# Adota o ciclo de vida UIScene no app iOS gerado pelo Capacitor (idempotente).
#
# Por quê: a partir do SDK do iOS 27, um app UIKit sem scene manifest NAO abre
# (assert no launch). No iOS 26 e so aviso. Roda DEPOIS do `cap sync` e vai
# encaixado no setup-ios.sh, sobrevivendo a regeneracao da pasta ios/.
#
# IMPORTANTE (licao do bug da tela preta): um arquivo .swift novo NAO entra no
# build so por existir na pasta — ele precisa estar referenciado no
# project.pbxproj. Por isso a classe SceneDelegate e EMBUTIDA no AppDelegate.swift
# (que ja esta no target App). Assim `App.SceneDelegate` compila e carrega.
#
# E codigo NATIVO Swift/plist — valide com UM build no Xcode (Cmd+Shift+K, Cmd+R).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PB="/usr/libexec/PlistBuddy"
APPDIR="$REPO/web/ios/App/App"
APPD="$APPDIR/AppDelegate.swift"
INFO="$APPDIR/Info.plist"
SCENE="$APPDIR/SceneDelegate.swift"
PBXPROJ="$REPO/web/ios/App/App.xcodeproj/project.pbxproj"

[[ -x "$PB" ]] || { echo "[X] PlistBuddy nao encontrado (precisa de macOS)."; exit 1; }
[[ -d "$APPDIR" ]] || { echo "[X] Nao achei $APPDIR. Rode antes: bash scripts/setup-ios.sh"; exit 1; }
[[ -f "$APPD" ]] || { echo "[X] Nao achei o AppDelegate.swift em $APPDIR."; exit 1; }

# --- 0) arquivo SceneDelegate.swift solto: so vale se estiver NO target -------
INLINE=1
if [[ -f "$SCENE" ]]; then
  if [[ -f "$PBXPROJ" ]] && grep -q "SceneDelegate.swift" "$PBXPROJ"; then
    echo "[=] SceneDelegate.swift ja esta referenciado no target — usando o arquivo separado."
    INLINE=0
  else
    rm -f "$SCENE"
    echo "[i] Removi um SceneDelegate.swift solto (estava na pasta mas FORA do build — causava a tela preta)."
  fi
fi

# --- 1) AppDelegate: remove window + metodos de cena --------------------------
if ! grep -q "configurationForConnecting" "$APPD"; then
  sed -i '' '/var window: UIWindow?/d' "$APPD"
  TMP="$(mktemp)"
  cat > "$TMP" <<'SWIFT'

    // MARK: - UIScene lifecycle (adotado para o requisito do iOS 27 SDK)
    func application(_ application: UIApplication,
                     configurationForConnecting connectingSceneSession: UISceneSession,
                     options: UIScene.ConnectionOptions) -> UISceneConfiguration {
        return UISceneConfiguration(name: "Default Configuration", sessionRole: connectingSceneSession.role)
    }

    func application(_ application: UIApplication,
                     didDiscardSceneSessions sceneSessions: Set<UISceneSession>) {
    }
SWIFT
  awk -v ins="$TMP" '
    function dump(f,  l){ while ((getline l < f) > 0) print l; close(f) }
    { a[NR]=$0 }
    END { last=0; for(i=1;i<=NR;i++) if(a[i] ~ /^[[:space:]]*}[[:space:]]*$/) last=i;
          for(i=1;i<=NR;i++){ if(i==last) dump(ins); print a[i] } }
  ' "$APPD" > "$APPD.new" && mv "$APPD.new" "$APPD"
  rm -f "$TMP"
  echo "[OK] AppDelegate.swift: window removida + metodos de sessao de cena."
else
  echo "[=] AppDelegate ja tem os metodos de sessao de cena."
fi

# --- 2) classe SceneDelegate embutida no AppDelegate.swift --------------------
if [[ "$INLINE" -eq 1 ]] && ! grep -q "class SceneDelegate" "$APPD"; then
  cat >> "$APPD" <<'SWIFT'

// MARK: - SceneDelegate (embutido de proposito: compila no target App sem
// precisar referenciar um arquivo novo no project.pbxproj). O Main.storyboard
// e referenciado no Info.plist, entao o UIKit cria a window e a bridge do
// Capacitor automaticamente. Deep links (futuro OAuth) sao reencaminhados ao
// ApplicationDelegateProxy; o reenvio acontece em sceneDidBecomeActive para
// evitar o problema de cold launch do Capacitor (issue #6662).
class SceneDelegate: UIResponder, UIWindowSceneDelegate {
    var window: UIWindow?
    private var pendingURL: URL?
    private var pendingActivity: NSUserActivity?

    func scene(_ scene: UIScene,
               willConnectTo session: UISceneSession,
               options connectionOptions: UIScene.ConnectionOptions) {
        if let url = connectionOptions.urlContexts.first?.url {
            pendingURL = url
        } else if let activity = connectionOptions.userActivities.first {
            pendingActivity = activity
        }
    }

    func sceneDidBecomeActive(_ scene: UIScene) {
        if let url = pendingURL {
            pendingURL = nil
            _ = ApplicationDelegateProxy.shared.application(UIApplication.shared, open: url, options: [:])
        }
        if let activity = pendingActivity {
            pendingActivity = nil
            _ = ApplicationDelegateProxy.shared.application(UIApplication.shared, continue: activity, restorationHandler: { _ in })
        }
    }

    func scene(_ scene: UIScene, openURLContexts URLContexts: Set<UIOpenURLContext>) {
        guard let url = URLContexts.first?.url else { return }
        _ = ApplicationDelegateProxy.shared.application(UIApplication.shared, open: url, options: [:])
    }

    func scene(_ scene: UIScene, continue userActivity: NSUserActivity) {
        _ = ApplicationDelegateProxy.shared.application(UIApplication.shared, continue: userActivity, restorationHandler: { _ in })
    }
}
SWIFT
  echo "[OK] Classe SceneDelegate embutida no AppDelegate.swift."
elif [[ "$INLINE" -eq 1 ]]; then
  echo "[=] AppDelegate ja contem a classe SceneDelegate."
fi

# --- 3) Info.plist: reescreve o manifest do ZERO (mata o config "(no name)") --
"$PB" -c "Delete :UIApplicationSceneManifest" "$INFO" >/dev/null 2>&1 || true
M=":UIApplicationSceneManifest"
R="$M:UISceneConfigurations:UIWindowSceneSessionRoleApplication"
"$PB" \
  -c "Add $M dict" \
  -c "Add $M:UIApplicationSupportsMultipleScenes bool false" \
  -c "Add $M:UISceneConfigurations dict" \
  -c "Add $R array" \
  -c "Add $R:0 dict" \
  -c "Add $R:0:UISceneConfigurationName string 'Default Configuration'" \
  -c "Add $R:0:UISceneDelegateClassName string '\$(PRODUCT_MODULE_NAME).SceneDelegate'" \
  -c "Add $R:0:UISceneStoryboardFile string Main" \
  "$INFO"
echo "[OK] UIApplicationSceneManifest reescrito limpo (1 config 'Default Configuration')."

echo
echo "[OK] UIScene adotado. No Xcode: Limpe (Cmd+Shift+K) e rode (Cmd+R)."
echo "    Os erros 'could not load class App.SceneDelegate' e a tela preta devem sumir."
