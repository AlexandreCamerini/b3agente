#!/usr/bin/env bash
# atualizar-identidade.sh — BolsIA · migra a identidade de produção em 1 comando.
#
#   bash scripts/atualizar-identidade.sh            # aplica + verifica
#   bash scripts/atualizar-identidade.sh --verificar # só verifica (não muda nada)
#
# DECISÃO TRAVADA (Fase 4 "Fechamento"):
#   appId   = com.alexandrecamerini.bolsia
#   appName = BolsIA
#
# O que este script cobre (idempotente — rodar 2x não muda nada):
#   web/capacitor.config.ts        appId + appName
#   web/index.html                 <title> + metas iOS/PWA de nome
#   web/vite.config.js             manifest name/short_name (PWA)
#   web/src/disclaimers.js         banner "B3 Agente é..." → "BolsIA é..."
#   scripts/configurar-apns.sh     TOPIC (default do APNS_TOPIC)
#   scripts/setup-ios.sh           exemplo do aviso de appId
#   scripts/ios-allow-http.sh      descrição ATS exibida no Info.plist
#   server/app/main.py             docstring + title do FastAPI (/docs)
#   server/tests/test_fase3_operador.py  APNS_TOPIC do ambiente de teste
#
# O que NÃO muda (codinome interno permanece — decisão do projeto):
#   pastas b3-agente/, package.json "b3-agente-web", env vars B3_*,
#   registros históricos em qa/ (diário e auditorias antigas são HISTÓRICO).
#
# Depois de rodar, os passos MANUAIS (uma vez) estão no
# ATUALIZAR-Git-Railway-iOS.md, seção "Migração de identidade":
#   portal Apple (App ID) → Railway (APNS_TOPIC) → setup-ios/cap sync →
#   clean build no Xcode → remover app antigo do iPhone → reinstalar.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.."

APP_ID="com.alexandrecamerini.bolsia"
APP_NAME="BolsIA"
OLD_ID="com.exemplo.b3agente"

say(){ printf "\n\033[1m== %s ==\033[0m\n" "$*"; }
ok(){ printf "  \033[32m[OK]\033[0m %s\n" "$*"; }
warn(){ printf "  \033[33m[!]\033[0m %s\n" "$*"; }
die(){ printf "  \033[31m[X]\033[0m %s\n" "$*" >&2; exit 1; }

VERIFICAR=""
[[ "${1:-}" == "--verificar" ]] && VERIFICAR="1"

# --- aplicação (perl -pi: substituição in-place, no-op se já aplicado) -------
aplicar(){
  say "Aplicando identidade: $APP_ID / $APP_NAME"

  perl -0777 -pi -e "s{appId:\s*\"[^\"]*\"}{appId: \"$APP_ID\"}" web/capacitor.config.ts
  perl -0777 -pi -e "s{appName:\s*\"[^\"]*\"}{appName: \"$APP_NAME\"}" web/capacitor.config.ts
  ok "capacitor.config.ts"

  perl -0777 -pi -e "s{<title>[^<]*</title>}{<title>$APP_NAME</title>}" web/index.html
  ok "index.html <title>"

  perl -0777 -pi -e "s{name:\s*\"B3 Agente\"}{name: \"$APP_NAME\"}g; s{short_name:\s*\"B3 Agente\"}{short_name: \"$APP_NAME\"}g" web/vite.config.js
  ok "vite.config.js (manifest PWA)"

  perl -0777 -pi -e "s{B3 Agente é um simulador}{$APP_NAME é um simulador}" web/src/disclaimers.js
  ok "disclaimers.js (banner)"

  perl -0777 -pi -e "s{\Q$OLD_ID\E}{$APP_ID}g" scripts/configurar-apns.sh
  ok "configurar-apns.sh (TOPIC)"

  perl -0777 -pi -e "s{com\.seunome\.b3agente}{$APP_ID}g" scripts/setup-ios.sh
  ok "setup-ios.sh (exemplo do aviso)"

  perl -0777 -pi -e "s{backend do B3 Agente}{backend do $APP_NAME}" scripts/ios-allow-http.sh
  ok "ios-allow-http.sh (descrição ATS)"

  perl -0777 -pi -e "s{\"\"\"B3 Agente - backend}{\"\"\"$APP_NAME - backend}; s{title=\"B3 Agente API\"}{title=\"$APP_NAME API\"}" server/app/main.py
  ok "main.py (docstring + título do /docs)"

  perl -0777 -pi -e "s{\Q$OLD_ID\E}{$APP_ID}g" server/tests/test_fase3_operador.py
  ok "test_fase3_operador.py (APNS_TOPIC de teste)"
}

# --- verificação -------------------------------------------------------------
verificar(){
  say "Verificando identidade"
  local FALHAS=0

  grep -q "appId: \"$APP_ID\"" web/capacitor.config.ts \
    && ok "appId = $APP_ID" || { warn "appId errado em capacitor.config.ts"; FALHAS=1; }
  grep -q "appName: \"$APP_NAME\"" web/capacitor.config.ts \
    && ok "appName = $APP_NAME" || { warn "appName errado em capacitor.config.ts"; FALHAS=1; }
  grep -q "<title>$APP_NAME</title>" web/index.html \
    && ok "title do index.html" || { warn "title do index.html não é $APP_NAME"; FALHAS=1; }
  grep -q "name: \"$APP_NAME\"" web/vite.config.js \
    && ok "manifest PWA" || { warn "manifest PWA não é $APP_NAME"; FALHAS=1; }
  grep -q "TOPIC=\"$APP_ID\"" scripts/configurar-apns.sh \
    && ok "TOPIC do configurar-apns.sh" || { warn "TOPIC do configurar-apns.sh não é $APP_ID"; FALHAS=1; }

  # nenhuma sobra do placeholder fora de histórico (qa/) e docs antigos
  say "Grep final — sobras do placeholder ($OLD_ID)"
  # Exceções LEGÍTIMAS (não são identidade viva):
  #   setup-ios.sh — guard que DETECTA checkout antigo com placeholder;
  #   atualizar-identidade.sh — este script (contém OLD_ID por definição);
  #   09/10/11-*.md — snapshots históricos de fases anteriores (como qa/).
  local SOBRAS
  SOBRAS="$(grep -rln "$OLD_ID" \
      --exclude-dir=node_modules --exclude-dir=ios --exclude-dir=dist \
      --exclude-dir=.venv --exclude-dir=__pycache__ --exclude-dir=qa \
      --exclude-dir=files-entrega --exclude="*.pyc" \
      web server scripts *.md *.sh 2>/dev/null \
      | grep -v "atualizar-identidade.sh" \
      | grep -v "scripts/setup-ios.sh" \
      | grep -v -E "^(09|10|11)-.*\.md$" || true)"
  if [[ -n "$SOBRAS" ]]; then
    warn "placeholder ainda presente em:"; echo "$SOBRAS" | sed 's/^/      /'
    FALHAS=1
  else
    ok "zero referência ao placeholder (fora do histórico em qa/)"
  fi

  [[ "$FALHAS" -eq 0 ]] && say "IDENTIDADE OK ✅" || die "identidade INCOMPLETA — veja avisos acima"
}

[[ -z "$VERIFICAR" ]] && aplicar
verificar
