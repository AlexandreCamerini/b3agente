#!/usr/bin/env bash
# atualizar-identidade.sh — Boris+ · migra a identidade de produção em 1 comando.
#
#   bash scripts/atualizar-identidade.sh            # aplica + verifica
#   bash scripts/atualizar-identidade.sh --verificar # só verifica (não muda nada)
#
# DECISÃO (10/08/2026 — aposentadoria do nome BolsIA):
#   appId   = com.alexandrecamerini.bolsia   ← MANTIDO de propósito. O bundle id
#             é a identidade do app na Apple: trocá-lo publica OUTRO app, quebra
#             todo login Sign in with Apple (o `sub` é emitido por bundle id) e
#             deixa órfã cada instalação existente. O usuário nunca o vê.
#   appName = Boris+
#
# O que este script cobre (idempotente — rodar 2x não muda nada):
#   web/capacitor.config.ts        appId + appName
#   web/index.html                 <title> + metas iOS/PWA de nome
#   web/vite.config.js             manifest name/short_name (PWA)
#   web/src/disclaimers.js         banner "B3 Agente é..." → "BolsIA é..."
#   scripts/configurar-apns.sh     TOPIC (default do APNS_TOPIC)
#   scripts/setup-ios.sh           exemplo do aviso de appId + título do cabeçalho
#   scripts/ios-allow-http.sh      descrição ATS exibida no Info.plist
#   server/app/main.py             docstring + title do FastAPI (/docs)
#   server/tests/test_fase3_operador.py  APNS_TOPIC do ambiente de teste
#   server/app/mydata_budget.py    comentário "chave de produção do BolsIA"
#   README.md, OPTIONS-MODELS.md, OPTIONS-SMOKE-TEST.md,
#   TECHNICAL-ANALYSIS-MODELS.md, scripts/setup.sh, scripts/run.sh,
#   scripts/backup-db.sh           título/cabeçalho "B3 Agente" (nome ANTERIOR
#                                   ao BolsIA) → Boris+, cauda medida 2026-08-30
#
# O que NÃO muda (codinome interno permanece — decisão do projeto):
#   pastas b3-agente/, package.json "b3-agente-web", env vars B3_*, chaves de
#   armazenamento b3-* (dado de usuário!), o bundle id acima, e registros
#   históricos (qa/, ESTADO-*, CHECKOUT-*, RELEASES.md, PROPOSTA-*, .planning/,
#   docs/MEDICAO-*) — reescrever o nome da época falsificaria o que foi
#   decidido nela. scripts/gerar-adhoc.sh SCHEME é identificador de scheme do
#   Xcode, não texto — nunca trocado no escuro (ver detecção no próprio script).
#
# Depois de rodar, os passos MANUAIS (uma vez) estão no
# ATUALIZAR-Git-Railway-iOS.md, seção "Migração de identidade":
#   portal Apple (App ID) → Railway (APNS_TOPIC) → setup-ios/cap sync →
#   clean build no Xcode → remover app antigo do iPhone → reinstalar.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.."

APP_ID="com.alexandrecamerini.bolsia"
APP_NAME="Boris+"
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

  perl -0777 -pi -e "s{B3 Agente é um simulador}{$APP_NAME é um simulador}; s{BolsIA é um simulador}{$APP_NAME é um simulador}" web/src/disclaimers.js
  ok "disclaimers.js (banner)"

  perl -0777 -pi -e "s{\Q$OLD_ID\E}{$APP_ID}g" scripts/configurar-apns.sh
  ok "configurar-apns.sh (TOPIC)"

  perl -0777 -pi -e "s{com\.seunome\.b3agente}{$APP_ID}g" scripts/setup-ios.sh
  ok "setup-ios.sh (exemplo do aviso)"

  perl -0777 -pi -e "s{backend do B3 Agente}{backend do $APP_NAME}; s{backend do BolsIA}{backend do $APP_NAME}" scripts/ios-allow-http.sh
  ok "ios-allow-http.sh (descrição ATS)"

  perl -0777 -pi -e "s{\"\"\"B3 Agente - backend}{\"\"\"$APP_NAME - backend}; s{\"\"\"BolsIA - backend}{\"\"\"$APP_NAME - backend}; s{title=\"B3 Agente API\"}{title=\"$APP_NAME API\"}; s{title=\"BolsIA API\"}{title=\"$APP_NAME API\"}" server/app/main.py
  ok "main.py (docstring + título do /docs)"

  perl -0777 -pi -e "s{\Q$OLD_ID\E}{$APP_ID}g" server/tests/test_fase3_operador.py
  ok "test_fase3_operador.py (APNS_TOPIC de teste)"

  perl -0777 -pi -e "s{chave de produção do BolsIA}{chave de produção do $APP_NAME}" server/app/mydata_budget.py
  ok "mydata_budget.py (comentário: código vivo, não histórico)"

  # Cauda medida em 2026-08-30 (quick task 260830-eqm): nome ANTERIOR ao
  # BolsIA ("B3 Agente") ainda em título/cabeçalho de documentação
  # operacional viva. Cada linha aqui é o título exato medido — sem `g`,
  # de propósito: um match por arquivo, sem risco de pegar outra ocorrência
  # legítima mais abaixo no mesmo arquivo.
  perl -0777 -pi -e "s{^# B3 Agente — mesa de operações educacional}{# $APP_NAME — mesa de operações educacional}m" README.md
  ok "README.md (título)"
  perl -0777 -pi -e "s{^# B3 Agente Opções}{# $APP_NAME Opções}m" OPTIONS-MODELS.md
  ok "OPTIONS-MODELS.md (título)"
  perl -0777 -pi -e "s{^# Smoke Test — B3 Agente Opções}{# Smoke Test — $APP_NAME Opções}m" OPTIONS-SMOKE-TEST.md
  ok "OPTIONS-SMOKE-TEST.md (título)"
  perl -0777 -pi -e "s{^# B3 Agente — Modelos de análise técnica}{# $APP_NAME — Modelos de análise técnica}m" TECHNICAL-ANALYSIS-MODELS.md
  ok "TECHNICAL-ANALYSIS-MODELS.md (título)"
  perl -0777 -pi -e "s{^# B3 Agente - instalacao}{# $APP_NAME - instalacao}m" scripts/setup.sh
  ok "setup.sh (cabeçalho)"
  perl -0777 -pi -e "s{^# B3 Agente - bootstrap do app iOS}{# $APP_NAME - bootstrap do app iOS}m" scripts/setup-ios.sh
  ok "setup-ios.sh (cabeçalho)"
  perl -0777 -pi -e "s{^# B3 Agente - lancador}{# $APP_NAME - lancador}m" scripts/run.sh
  ok "run.sh (cabeçalho)"
  perl -0777 -pi -e "s{^# B3 Agente — backup do banco SQLite}{# $APP_NAME — backup do banco SQLite}m" scripts/backup-db.sh
  ok "backup-db.sh (cabeçalho)"
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

  # Marca aposentada: "BolsIA" (case-sensitive — o bundle id é minúsculo e
  # escapa por natureza) não pode sobrar em arquivo VIVO. Histórico fica.
  #   ':!.planning' e ':!docs/MEDICAO-*' (medido 2026-08-30, quick task
  #     260830-eqm): registro histórico de decisão/medição de uma data
  #     específica — mesma classe que qa/ e ESTADO-*. Também cobre
  #     este PLAN/SPEC da própria quick task, que citam "BolsIA" verbatim
  #     ao transcrever o contexto da época.
  #   ':!*POLITICA-PRIVACIDADE.md' — SEM magic, pathspec relativo à raiz não
  #     casava "server/POLITICA-PRIVACIDADE.md" (defeito do verificador, não
  #     sobra de rename: o "(anteriormente BolsIA)" ali é mantido de
  #     propósito, o texto do arquivo não muda).
  say "Grep final — marca aposentada (BolsIA) fora do histórico"
  local MARCA
  MARCA="$(git grep -l "BolsIA" -- \
      ':!qa' ':!ESTADO-*' ':!CHECKOUT-*' ':!RELEASES.md' ':!PROPOSTA-*' \
      ':!AUDITORIA-PROMPTS-LLM.md' ':!09-*' ':!10-*' ':!11-*' \
      ':!RENOMEAR-*' ':!server/ios_dist' ':!scripts/atualizar-identidade.sh' \
      ':!*POLITICA-PRIVACIDADE.md' ':!.planning' ':!docs/MEDICAO-*' 2>/dev/null || true)"
  if [[ -n "$MARCA" ]]; then
    warn "BolsIA ainda vivo em:"; echo "$MARCA" | sed 's/^/      /'
    FALHAS=1
  else
    ok "zero BolsIA fora do histórico (POLITICA mantém o '(anteriormente BolsIA)' de propósito)"
  fi

  # Marca ANTERIOR ao BolsIA: "B3 Agente" (mesmo raciocínio acima, mesmas
  # exceções de histórico + o placeholder OLD_ID que citaria "b3agente" em
  # minúsculo mas não "B3 Agente" — sem colisão). Cauda medida 2026-08-30.
  say "Grep final — marca anterior (B3 Agente) fora do histórico"
  local MARCA_ANTIGA
  MARCA_ANTIGA="$(git grep -l "B3 Agente" -- \
      ':!qa' ':!ESTADO-*' ':!CHECKOUT-*' ':!RELEASES.md' ':!PROPOSTA-*' \
      ':!AUDITORIA-PROMPTS-LLM.md' ':!09-*' ':!10-*' ':!11-*' \
      ':!RENOMEAR-*' ':!server/ios_dist' ':!scripts/atualizar-identidade.sh' \
      ':!*POLITICA-PRIVACIDADE.md' ':!.planning' ':!docs/MEDICAO-*' 2>/dev/null || true)"
  if [[ -n "$MARCA_ANTIGA" ]]; then
    warn "B3 Agente ainda vivo em:"; echo "$MARCA_ANTIGA" | sed 's/^/      /'
    FALHAS=1
  else
    ok "zero B3 Agente fora do histórico"
  fi

  [[ "$FALHAS" -eq 0 ]] && say "IDENTIDADE OK ✅" || die "identidade INCOMPLETA — veja avisos acima"
}

[[ -z "$VERIFICAR" ]] && aplicar
verificar
