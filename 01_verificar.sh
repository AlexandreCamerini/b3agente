#!/usr/bin/env bash
# =============================================================================
# 01_verificar.sh — VERIFICAÇÃO PROFUNDA. Somente leitura, sempre.
# Rode na raiz do b3-agente. Não altera, não apaga, não commita.
#
# Responde: o que é código VIVO, o que é resto, e onde há risco de segurança.
# =============================================================================
set -uo pipefail

if [ -t 1 ]; then
  B=$'\033[1m'; G=$'\033[32m'; Y=$'\033[33m'; R=$'\033[31m'; C=$'\033[36m'; D=$'\033[2m'; N=$'\033[0m'
else B=""; G=""; Y=""; R=""; C=""; D=""; N=""; fi
ok()  { printf '  %s✓%s %s\n' "$G" "$N" "$*"; }
warn(){ printf '  %s!%s %s\n' "$Y" "$N" "$*"; }
bad() { printf '  %s✗%s %s\n' "$R" "$N" "$*"; }
inf() { printf '    %s%s%s\n' "$D" "$*" "$N"; }
hd()  { printf '\n%s══ %s%s\n' "$B" "$*" "$N"; }
cmd() { printf '    %s%s%s\n' "$C" "$*" "$N"; }

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "não é repo git"; exit 1; }
cd "$ROOT" || exit 1
RISCO=0

printf '%s VERIFICAÇÃO — %s%s\n' "$B" "$ROOT" "$N"

# ===========================================================================
hd "1. MÓDULOS PYTHON — vivo ou morto (detecção corrigida)"
inf "agora procura o nome do módulo em QUALQUER uso (store.get, defaults.x),"
inf "não só em 'from .modulo import' — que perdia imports com vírgula."
echo ""
MORTOS=""
for f in server/app/*.py; do
  [ -f "$f" ] || continue
  base="$(basename "$f" .py)"
  case "$base" in __init__|main) continue ;; esac
  USOS="$(grep -rlw "$base" server --include='*.py' 2>/dev/null \
          | grep -v "^${f}$" | grep -c . || true)"
  if [ "${USOS:-0}" -eq 0 ]; then
    MORTOS="${MORTOS} ${base}"
    printf '      %-26s %sNENHUM uso — candidato real%s\n' "$(basename "$f")" "$R" "$N"
  else
    printf '      %-26s %svivo (%s arquivo(s) usam)%s\n' "$(basename "$f")" "$G" "$USOS" "$N"
  fi
done
echo ""
if [ -z "$MORTOS" ]; then
  ok "nenhum módulo órfão — os 4 da auditoria anterior eram falso positivo"
else
  warn "candidatos:${MORTOS}"
  inf "confirme à mão antes de remover (imports dinâmicos existem)."
fi

# ===========================================================================
hd "2. SEGURANÇA — segredos versionados"
for p in ".env" ".env.local" "*.db" "*.sqlite" "*.sqlite3" "*.pem" "*.key"; do
  ACHOU="$(git ls-files "$p" 2>/dev/null | head -5)"
  if [ -n "$ACHOU" ]; then
    bad "RASTREADO pelo git (não deveria): $p"
    printf '%s\n' "$ACHOU" | sed 's/^/        /'
    RISCO=$((RISCO+1))
    inf "remover do índice sem apagar do disco:"
    cmd "git rm --cached ARQUIVO && echo ARQUIVO >> .gitignore"
  fi
done
[ "$RISCO" -eq 0 ] && ok "nenhum .env/.db/.key versionado"

hd "3. SEGURANÇA — chaves hardcoded no código versionado"
CHAVES="$(git grep -nE 'sk-ant-[A-Za-z0-9]|sk-[A-Za-z0-9]{20}|AIza[A-Za-z0-9]{20}' \
          -- '*.py' '*.js' '*.ts' '*.json' '*.yml' '*.yaml' 2>/dev/null | head -5 || true)"
if [ -n "$CHAVES" ]; then
  bad "possível chave de API no código:"
  printf '%s\n' "$CHAVES" | cut -c1-110 | sed 's/^/        /'
  RISCO=$((RISCO+1))
  inf "se for chave real: REVOGUE no console antes de qualquer outra coisa."
else
  ok "nenhuma chave aparente no código versionado"
fi

hd "4. SEGURANÇA — .gitignore"
[ -f .gitignore ] || { bad "sem .gitignore"; RISCO=$((RISCO+1)); }
for p in ".env" "*.db" ".claude" "node_modules" ".venv" "__pycache__" "*.bak"; do
  if [ -f .gitignore ] && grep -qF -- "$p" .gitignore 2>/dev/null; then
    ok "ignora: $p"
  else
    warn "NÃO ignora: $p"
    RISCO=$((RISCO+1))
  fi
done

# ===========================================================================
hd "5. PESO — o que está inflando o repositório"
inf "auditoria anterior: .claude=130M  web=122M  server=74M  .git=9.4M"
echo ""
for d in .claude .claude/worktrees web server mobile; do
  [ -d "$d" ] && du -sh "$d" 2>/dev/null | sed 's/^/      /'
done
echo ""
for d in web/node_modules server/.venv server/venv web/dist web/build; do
  if [ -d "$d" ]; then
    T="$(du -sh "$d" 2>/dev/null | cut -f1)"
    if git ls-files --error-unmatch "$d" >/dev/null 2>&1; then
      bad "${d} (${T}) está VERSIONADO — não deveria"; RISCO=$((RISCO+1))
    else
      ok "${d} (${T}) fora do git"
    fi
  fi
done

# ===========================================================================
hd "6. WORKTREES — o que há dentro"
git worktree list 2>/dev/null | tail -n +2 | while read -r caminho resto; do
  [ -z "$caminho" ] && continue
  printf '      %s\n' "$caminho"
  if [ -d "$caminho" ]; then
    SUJO="$(git -C "$caminho" status --porcelain 2>/dev/null | grep -c . || true)"
    if [ "${SUJO:-0}" -gt 0 ]; then
      printf '        %s%s alteração(ões) NÃO COMMITADA(S) — NÃO remova ainda%s\n' "$R" "$SUJO" "$N"
      git -C "$caminho" status --porcelain 2>/dev/null | head -5 | sed 's/^/          /'
    else
      printf '        %slimpa — seguro remover%s\n' "$G" "$N"
    fi
  else
    printf '        %spasta não existe — entrada órfã (git worktree prune resolve)%s\n' "$Y" "$N"
  fi
done

# ===========================================================================
hd "7. STASH — o que está guardado"
if git stash list | grep -q .; then
  git stash list | sed 's/^/      /'
  echo ""
  inf "conteúdo do mais recente:"
  git stash show --stat stash@{0} 2>/dev/null | sed 's/^/      /' || inf "(vazio)"
else
  ok "sem stashes"
fi

# ===========================================================================
hd "8. GATEWAY — o que falta implementar no llm.py"
L="server/app/llm.py"
if [ -f "$L" ]; then
  grep -q "cache_control" "$L" 2>/dev/null && ok "prompt caching JÁ implementado" \
    || { warn "prompt caching AUSENTE — é o que o gateway agrega"; }
  grep -q "cache_read_input_tokens" "$L" 2>/dev/null && ok "telemetria de cache presente" \
    || warn "telemetria não conta tokens lidos do cache (custo ficaria subestimado)"
  grep -q "record_usage" "$L" 2>/dev/null && ok "record_usage presente (FinOps já existe)"
fi

# ===========================================================================
hd "RESUMO"
[ "$RISCO" -eq 0 ] && ok "nenhum risco de segurança encontrado" \
                   || bad "${RISCO} ponto(s) de risco/atenção — resolva ANTES de limpar"
echo ""
inf "Nada foi alterado. Próximo: ./02_limpar.sh --check"
echo ""
