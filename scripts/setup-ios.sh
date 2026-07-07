#!/usr/bin/env bash
#
# B3 Agente - bootstrap do app iOS (Capacitor + Xcode), ciente do monorepo.
# ASCII puro e expansoes defensivas (${VAR:-}) para funcionar tambem no bash 3.2
# do macOS. Opera na pasta web/.
#
# Uso:
#   ./scripts/setup-ios.sh [--api-base http://SEU_IP_LAN:8787]
#                          [--app-id com.seu.id] [--app-name "Nome"]
#                          [--reset] [--no-open] [--verbose]
#
# IMPORTANTE: o app nativo precisa falar com o backend pela rede. Passe
# --api-base com o IP do Mac na sua LAN (ex.: http://192.168.0.10:8787).
#
set -euo pipefail

API_BASE=""; APP_ID=""; APP_NAME=""; OPEN_XCODE=1; RESET=0; VERBOSE=""
while [[ $# -gt 0 ]]; do
  case "${1:-}" in
    --api-base) API_BASE="${2:-}"; shift 2;;
    --app-id)   APP_ID="${2:-}"; shift 2;;
    --app-name) APP_NAME="${2:-}"; shift 2;;
    --no-open)  OPEN_XCODE=0; shift;;
    --reset)    RESET=1; shift;;
    --verbose)  VERBOSE="--verbose"; shift;;
    -h|--help)  awk 'NR==1&&/^#!/{next} /^#/{sub(/^# ?/,"");print;next}{exit}' "$0"; exit 0;;
    *) echo "Opcao desconhecida: ${1:-} (use --help)"; exit 1;;
  esac
done

if [[ -t 1 ]]; then BOLD=$'\033[1m'; RED=$'\033[31m'; GRN=$'\033[32m'; YLW=$'\033[33m'; RST=$'\033[0m'
else BOLD=""; RED=""; GRN=""; YLW=""; RST=""; fi
say(){ printf "%s\n" "${BOLD}> $*${RST}"; }
ok(){ printf "%s\n" "${GRN}[OK] $*${RST}"; }
warn(){ printf "%s\n" "${YLW}[!] $*${RST}"; }
die(){ printf "%s\n" "${RED}[X] $*${RST}" >&2; exit 1; }

normalize_api_base(){
  local u="${1:-}"
  [[ -z "$u" ]] && { printf "%s" ""; return; }
  if [[ ! "$u" =~ ^https?:// ]]; then
    if [[ "$u" =~ ^(localhost|127\.|0\.0\.0\.0|10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[0-1])\.) ]]; then
      u="http://$u"
    else
      u="https://$u"
    fi
  fi
  u="${u%/}"
  u="${u%/api}"
  printf "%s" "$u"
}
trap 'printf "%s\n" "${RED}[X] Falhou na linha $LINENO - veja o erro acima.${RST}" >&2' ERR

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
WEB="$REPO/web"
[[ -f "$WEB/capacitor.config.ts" ]] || die "Nao achei web/capacitor.config.ts. Extraia o zip inteiro e rode de dentro do b3-agente."

say "Verificando ambiente..."
[[ "$(uname)" == "Darwin" ]] || die "Precisa de macOS (a compilacao iOS exige Mac + Xcode)."
if [[ "${NODE_ENV:-}" == "production" ]]; then warn "NODE_ENV=production - desativando nesta sessao."; unset NODE_ENV; fi
command -v node >/dev/null 2>&1 || die "Node.js nao encontrado. Instale o Node 22+ (https://nodejs.org)."
NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
[[ "$NODE_MAJOR" -ge 22 ]] || die "Node $(node -v) - o Capacitor 8 exige Node 22+."
ok "Node $(node -v)"
command -v xcodebuild >/dev/null 2>&1 || die "Xcode nao encontrado. Instale pela App Store e rode: xcode-select --install"
xcodebuild -version >/dev/null 2>&1 || die "xcodebuild inativo. Rode: sudo xcode-select -s /Applications/Xcode.app/Contents/Developer"
ok "$(xcodebuild -version | head -1)"

cd "$WEB"

if [[ "$RESET" -eq 1 ]]; then warn "Reset: removendo node_modules, dist, ios, package-lock.json."; rm -rf node_modules dist ios package-lock.json; fi

# appId / appName antes do 'add ios'
if [[ -n "${APP_ID:-}" ]]; then perl -0777 -pi -e "s{appId:\s*\"[^\"]*\"}{appId: \"$APP_ID\"}" capacitor.config.ts; ok "appId = $APP_ID"; fi
if [[ -n "${APP_NAME:-}" ]]; then perl -0777 -pi -e "s{appName:\s*\"[^\"]*\"}{appName: \"$APP_NAME\"}" capacitor.config.ts; ok "appName = $APP_NAME"; fi
CUR_ID="$(perl -ne 'print $1 if /appId:\s*"([^"]*)"/' capacitor.config.ts 2>/dev/null || true)"
if [[ "$CUR_ID" == "com.exemplo.b3agente" || -z "$CUR_ID" ]]; then
  warn "appId atual: '${CUR_ID:-?}'. Defina o seu: ./scripts/setup-ios.sh --app-id com.alexandrecamerini.bolsia"
fi

# dependencias (garante CLI + plataforma do Capacitor)
CAP="$WEB/node_modules/.bin/cap"
need=0; [[ -d node_modules ]] || need=1; [[ -x "$CAP" ]] || need=1; [[ -x "$WEB/node_modules/.bin/vite" ]] || need=1
if [[ "$need" -eq 1 ]]; then say "Instalando dependencias do web (npm install)..."; npm install; fi
if [[ ! -x "$CAP" || ! -d "$WEB/node_modules/@capacitor/ios" ]]; then
  warn "CLI/plataforma do Capacitor ausente - instalando."
  npm install -D @capacitor/cli @capacitor/ios; npm install @capacitor/core @capacitor/app @capacitor/status-bar
fi
[[ -x "$CAP" ]] || die "Nao consegui instalar o @capacitor/cli. Rode 'npm install' dentro de web/ manualmente."
ok "Capacitor CLI ok ($("$CAP" --version 2>/dev/null || echo presente))"

# build web (embute a URL do backend, se fornecida)
if [[ -n "${API_BASE:-}" ]]; then
  API_BASE="$(normalize_api_base "$API_BASE")"
  say "Build de producao com VITE_API_BASE=${API_BASE} ..."
  VITE_API_BASE="${API_BASE}" npm run build
  ok "App nativo apontara para ${API_BASE}"
else
  warn "Sem --api-base: o app nativo nao sabera onde esta o backend."
  warn "O app web (mesma origem) funciona, mas no iPhone passe --api-base http://SEU_IP_LAN:8787"
  npm run build
fi

# plataforma iOS (trata pasta parcial)
ios_ok(){ [[ -d ios/App && ( -e ios/App/App.xcodeproj || -e ios/App/App.xcworkspace ) ]]; }
if ios_ok; then
  say "Sincronizando iOS..."; "$CAP" sync ios ${VERBOSE:-}
else
  [[ -d ios ]] && { warn "Pasta ios/ incompleta - recriando."; rm -rf ios; }
  say "Adicionando plataforma iOS..."; "$CAP" add ios ${VERBOSE:-}; "$CAP" sync ios ${VERBOSE:-}
fi
ok "iOS pronto."
bash "$SCRIPT_DIR/ios-allow-http.sh" || warn "Nao consegui ajustar o Info.plist (ATS) automaticamente; rode: bash scripts/ios-allow-http.sh"
bash "$SCRIPT_DIR/ios-adopt-uiscene.sh" || warn "Nao consegui adotar o UIScene automaticamente; rode: bash scripts/ios-adopt-uiscene.sh"

# FASE 4 (Bloco 2) — URL scheme do Google Sign-In (client id iOS invertido).
# So roda se VITE_GOOGLE_IOS_CLIENT_ID estiver no ambiente do build; sem ele
# o login Google mostra o aviso de nao configurado (Apple e e-mail seguem ok).
PLIST="ios/App/App/Info.plist"
if [[ -n "${VITE_GOOGLE_IOS_CLIENT_ID:-}" && -f "$PLIST" ]]; then
  REV="$(echo "$VITE_GOOGLE_IOS_CLIENT_ID" | awk -F. '{ for (i=NF; i>0; i--) printf "%s%s", $i, (i>1 ? "." : "") }')"
  if ! /usr/libexec/PlistBuddy -c "Print :CFBundleURLTypes" "$PLIST" >/dev/null 2>&1; then
    /usr/libexec/PlistBuddy -c "Add :CFBundleURLTypes array" "$PLIST"
  fi
  if ! grep -q "$REV" "$PLIST"; then
    N="$(/usr/libexec/PlistBuddy -c "Print :CFBundleURLTypes" "$PLIST" 2>/dev/null | grep -c "Dict" || echo 0)"
    /usr/libexec/PlistBuddy -c "Add :CFBundleURLTypes:$N dict" "$PLIST"
    /usr/libexec/PlistBuddy -c "Add :CFBundleURLTypes:$N:CFBundleURLSchemes array" "$PLIST"
    /usr/libexec/PlistBuddy -c "Add :CFBundleURLTypes:$N:CFBundleURLSchemes:0 string $REV" "$PLIST"
    ok "URL scheme do Google Sign-In adicionado ao Info.plist ($REV)"
  else
    ok "URL scheme do Google Sign-In ja presente"
  fi
fi

if [[ "$OPEN_XCODE" -eq 1 ]]; then say "Abrindo no Xcode..."; "$CAP" open ios || warn "Nao consegui abrir o Xcode. Abra web/ios/App/App.xcworkspace."; fi

cat <<EOF

${GRN}${BOLD}Tudo pronto.${RST}
No Xcode: selecione seu Time (Signing & Capabilities), escolha seu iPhone e clique Run.
Lembre de iniciar o backend (no Mac): ${BOLD}bash scripts/start.sh${RST} ou ${BOLD}(cd server && npm start)${RST}.
Para Railway, use --api-base https://SEU_APP.up.railway.app. Para backend local, o iPhone e o Mac precisam estar na mesma rede, e o --api-base deve apontar para o IP do Mac.
EOF
