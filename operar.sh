#!/usr/bin/env bash
# operar.sh — BolsIA (b3-agente) · operação do dia a dia em UM comando.
#
#   bash operar.sh status      # saúde do servidor (Railway) e do ambiente local
#   bash operar.sh testes      # roda TODAS as suítes (backend + web)
#   bash operar.sh backup      # backup consistente do banco local (SQLite)
#   bash operar.sh deploy "msg"  # commit + push + health check (Railway)
#   bash operar.sh ajuda       # este texto
#
# Fachada fina sobre os scripts existentes (test.sh, backup-db.sh,
# atualizar-servidor.sh) — não duplica lógica. Os LOGS DETALHADOS do servidor
# ficam no app: Perfil → Observabilidade → "Logs do servidor" (FASE 5), ou no
# painel do Railway (Deployments → View Logs).
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]:-$0}")"
RAILWAY_URL="${RAILWAY_URL:-https://boris.semente.dev}"

say(){ printf "\n\033[1m== %s ==\033[0m\n" "$*"; }
ok(){ printf "  \033[32m[OK]\033[0m %s\n" "$*"; }
warn(){ printf "  \033[33m[!]\033[0m %s\n" "$*"; }
die(){ printf "  \033[31m[X]\033[0m %s\n" "$*" >&2; exit 1; }

cmd="${1:-ajuda}"
case "$cmd" in
  status)
    say "Servidor no ar (Railway)"
    HEALTH="$(curl -fsS --max-time 10 "$RAILWAY_URL/api/health" 2>/dev/null || true)"
    if [ -n "$HEALTH" ]; then
      ok "responde em $RAILWAY_URL"
      SRV_BUILD="$(printf '%s' "$HEALTH" | sed -n 's/.*"build"[": ]*\([^"]*\)".*/\1/p')"
      LOCAL_BUILD="$(sed -n 's/.*BUILD_ID = "\([^"]*\)".*/\1/p' web/src/version.js 2>/dev/null)"
      if [ -n "$SRV_BUILD" ]; then
        if [ "$SRV_BUILD" = "$LOCAL_BUILD" ]; then ok "build no ar = build local ($SRV_BUILD)"; else warn "build no ar ($SRV_BUILD) ≠ local ($LOCAL_BUILD) — falta deploy"; fi
      else
        warn "servidor no ar é ANTIGO (sem carimbo de build) — rode: bash operar.sh deploy"
      fi
    else
      warn "NÃO respondeu em $RAILWAY_URL/api/health — veja os logs no painel do Railway"
    fi
    # FASE 9: comparação TRIPLA do carimbo — código × dist × bundle do iOS.
    # É o diagnóstico instantâneo do "a fase não apareceu".
    say "Carimbo de build nos 3 elos"
    LOCAL_B="$(sed -n 's/.*BUILD_ID = "\([^"]*\)".*/\1/p' web/src/version.js 2>/dev/null)"
    DIST_B="$(grep -rho 'F[0-9A-Za-z]\{1,6\}-[0-9]\{8\}-[0-9]\{1,3\}' web/dist/assets 2>/dev/null | sort -u | tail -1)"
    IOS_B="$(grep -rho 'F[0-9A-Za-z]\{1,6\}-[0-9]\{8\}-[0-9]\{1,3\}' web/ios/App/App/public/assets 2>/dev/null | sort -u | tail -1)"
    echo "  código (version.js): ${LOCAL_B:-?}"
    [ "${DIST_B:-}" = "$LOCAL_B" ] && ok "dist/: $DIST_B" || warn "dist/: ${DIST_B:-ausente} — rode: bash entregar.sh"
    [ "${IOS_B:-}" = "$LOCAL_B" ] && ok "bundle do iOS: $IOS_B" || warn "bundle do iOS: ${IOS_B:-ausente} — rode: bash entregar.sh"
    echo "  4º elo (manual): o RODAPÉ do Perfil no iPhone deve mostrar 'build $LOCAL_B'."
    echo "  Entrega completa em um comando: bash entregar.sh \"mensagem\""
    say "Ambiente local"
    [ -d server/.venv ] && ok "venv do backend instalado" || warn "venv ausente — rode: bash instalar.sh"
    [ -d web/node_modules ] && ok "dependências do web instaladas" || warn "node_modules ausente — rode: bash instalar.sh"
    if command -v git >/dev/null 2>&1; then
      DIRTY="$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
      [ "$DIRTY" = "0" ] && ok "working tree limpa" || warn "$DIRTY arquivo(s) alterado(s) sem commit"
      ok "último commit: $(git log -1 --format='%h %s (%cr)' 2>/dev/null)"
    fi
    echo
    echo "  Logs detalhados: app → Perfil → Observabilidade → 'Logs do servidor'"
    echo "  (restrito ao admin: B3_ADMIN_EMAILS no Railway, ou a 1ª conta criada)"
    ;;
  testes)
    exec bash executar.sh --testes
    ;;
  backup)
    exec bash scripts/backup-db.sh
    ;;
  deploy)
    MSG="${2:-atualizacao}"
    say "Deploy (commit + push + health)"
    exec bash scripts/atualizar-servidor.sh "$MSG"
    ;;
  ajuda|help|-h|--help)
    sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'
    ;;
  *)
    die "comando desconhecido: $cmd (use: status | testes | backup | deploy | ajuda)"
    ;;
esac
