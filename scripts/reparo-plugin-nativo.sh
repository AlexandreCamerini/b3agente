#!/usr/bin/env bash
# reparo-plugin-nativo.sh — BolsIA · repara o caso "app sumiu de Ajustes ->
# Notificações + Diagnóstico trava + Ativar push travado (permissão nunca
# vira granted)".
#
# CONTEXTO (qa/27): todos os guardiões de CÓDIGO (test_push_wiring.mjs,
# test_ios_assets.mjs) e o carimbo de build passam — a FONTE está correta:
# Package.swift lista CapacitorLocalNotifications/PushNotifications, o
# capacitor.config.json sincronizado tem packageClassList com
# LocalNotificationsPlugin/PushNotificationsPlugin, o AppDelegate tem os
# callbacks do APNs. Isso prova que o REPOSITÓRIO está certo — mas o
# BINÁRIO instalado no iPhone pode não refletir isso, porque o Xcode
# resolve os pacotes SPM locais (node_modules/@capacitor/...) via cache
# (DerivedData + ~/Library/Caches/org.swift.swiftpm) e esse cache pode ficar
# preso a uma resolução antiga depois de um `cap sync` ou `npm install`.
# Sintoma clássico: o app "compila e roda", mas a classe do plugin nunca é
# linkada de verdade -> UNUserNotificationCenter nunca é solicitado -> o
# app nem aparece em Ajustes -> Notificações, e qualquer chamada nativa ao
# plugin (ex.: getPending() do Diagnóstico) FICA PENDURADA em vez de
# responder ou lançar erro.
#
# Este script limpa TODOS os caches conhecidos e deixa o projeto pronto
# para uma resolução de pacotes 100% do zero no Xcode.
#
# Uso (na raiz do repo, com o Xcode FECHADO):
#   bash scripts/reparo-plugin-nativo.sh
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.."
ROOT="$(pwd)"

say(){ printf "\n\033[1m== %s ==\033[0m\n" "$*"; }
ok(){ printf "  \033[32m[OK]\033[0m %s\n" "$*"; }
warn(){ printf "  \033[33m[!]\033[0m %s\n" "$*"; }
die(){ printf "  \033[31m[X]\033[0m %s\n" "$*" >&2; exit 1; }

if pgrep -x Xcode >/dev/null 2>&1; then
  die "Feche o Xcode primeiro (ele trava o cache de pacotes enquanto está aberto) e rode de novo."
fi

say "1/6 · Dependências web (garante @capacitor/local-notifications e push-notifications no node_modules)"
cd "$ROOT/web"
npm install --no-audit --no-fund || die "npm install falhou"
node -e "require.resolve('@capacitor/local-notifications/package.json')" \
  && ok "@capacitor/local-notifications presente" || die "plugin ausente no package.json"
node -e "require.resolve('@capacitor/push-notifications/package.json')" \
  && ok "@capacitor/push-notifications presente" || die "plugin ausente no package.json"

say "2/6 · Limpando o cache de pacotes Swift (a causa mais comum deste sintoma)"
rm -rf ~/Library/Caches/org.swift.swiftpm && ok "~/Library/Caches/org.swift.swiftpm removido" || warn "nada para remover em Caches/org.swift.swiftpm"
rm -rf ~/Library/org.swift.swiftpm && ok "~/Library/org.swift.swiftpm removido" || warn "nada para remover em org.swift.swiftpm"
if [ -d ios/App/App.xcodeproj/project.xcworkspace/xcshareddata/swiftpm ]; then
  rm -rf ios/App/App.xcodeproj/project.xcworkspace/xcshareddata/swiftpm
  ok "resolução local (Package.resolved) do projeto removida — Xcode vai recalcular do zero"
fi

say "3/6 · Limpando DerivedData deste projeto"
FOUND=0
for d in ~/Library/Developer/Xcode/DerivedData/App-*; do
  [ -d "$d" ] || continue
  rm -rf "$d" && { ok "removido: $d"; FOUND=1; }
done
[ "$FOUND" = "1" ] || warn "nenhum DerivedData de 'App-*' encontrado (pode já estar limpo, ou o nome do projeto é outro)"

say "4/6 · cap sync ios (relinca os plugins nativos) + patch do AppDelegate"
npx cap sync ios | tee /tmp/capsync.log
grep -qi "local-notifications" /tmp/capsync.log && ok "local-notifications sincronizado" || warn "cap sync não confirmou local-notifications no log — confira /tmp/capsync.log"
grep -qi "push-notifications" /tmp/capsync.log && ok "push-notifications sincronizado" || warn "cap sync não confirmou push-notifications no log — confira /tmp/capsync.log"
cd "$ROOT" && bash scripts/ios-patch-appdelegate.sh || die "patch do AppDelegate falhou"

say "5/6 · Conferindo o registro dos plugins no config sincronizado"
CFG="web/ios/App/App/capacitor.config.json"
if [ -f "$CFG" ]; then
  python3 - "$CFG" << 'PY'
import json, sys
cfg = json.load(open(sys.argv[1]))
classes = cfg.get("packageClassList", [])
faltando = [c for c in ("LocalNotificationsPlugin", "PushNotificationsPlugin") if c not in classes]
if faltando:
    print(f"  [X] faltando em packageClassList: {faltando}")
    sys.exit(1)
print("  [OK] packageClassList tem LocalNotificationsPlugin e PushNotificationsPlugin")
PY
  [ $? -eq 0 ] || die "packageClassList incompleto — o cap sync não registrou os plugins. Rode 'npx cap add ios' do zero (apague web/ios/ antes)."
else
  die "$CFG não existe — cap sync não rodou direito"
fi

say "6/6 · Abrindo o Xcode"
npx cap open ios >/dev/null 2>&1 || open ios/App/App.xcworkspace 2>/dev/null || warn "abra manualmente web/ios/App/App.xcworkspace"

cat << 'FIM'

  PASSOS MANUAIS NO XCODE (nesta ordem — nenhum pode ser pulado):
   1. File -> Packages -> Reset Package Caches. Espere a barra de progresso
      no topo terminar (pode levar 1-2min) ANTES de continuar.
   2. File -> Packages -> Resolve Package Versions. Espere terminar de novo.
   3. Product -> Clean Build Folder (Shift+Cmd+K).
   4. NO IPHONE: apague o app BolsIA da tela (toque e segure -> Remover App).
      Isso limpa o registro antigo do app em Ajustes -> Notificações.
   5. No Xcode: selecione o SEU IPHONE no topo (não o simulador) e Product -> Run.

  DEPOIS DE INSTALAR:
   1. Confira o carimbo no rodapé do Perfil = build local (bash entregar.sh --so-verificar mostra o esperado).
   2. Perfil -> Notificações -> DIAGNÓSTICO. Agora deve responder na hora
      (não travar) com "plugin nativo carregado: true".
   3. Se aparecer true e "permissão do sistema: default", toque em Pedir
      permissão -> o BolsIA deve aparecer em Ajustes -> Notificações.
   4. Reporte o texto exato do Diagnóstico se ainda travar ou der false —
      nesse caso o problema não é mais cache, precisa de outro diagnóstico.
FIM
