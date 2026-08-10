#!/usr/bin/env bash
# =============================================================================
# auditar.sh — inventário do repositório: o que está VALENDO e o que é RESTO.
# Rode na raiz do b3-agente.
#
#   ./auditar.sh            # SOMENTE LEITURA (default) — nada é alterado
#   ./auditar.sh --limpar   # move os restos para fora do repo (não apaga)
#
# FILOSOFIA
#   Não apaga nada, nunca. Não commita. Não faz push. Não edita código.
#   Coisas destrutivas (remover branch, worktree, stash) viram COMANDO IMPRESSO
#   para você rodar com contexto — não decisão minha.
# =============================================================================
set -uo pipefail

LIMPAR=0
case "${1:-}" in
  ""|--check) LIMPAR=0 ;;
  --limpar)   LIMPAR=1 ;;
  -h|--help)  sed -n '2,14p' "$0"; exit 0 ;;
  *) echo "opção inválida: $1"; exit 1 ;;
esac

if [ -t 1 ]; then
  B=$'\033[1m'; G=$'\033[32m'; Y=$'\033[33m'; R=$'\033[31m'; C=$'\033[36m'; D=$'\033[2m'; N=$'\033[0m'
else B=""; G=""; Y=""; R=""; C=""; D=""; N=""; fi
ok()   { printf '  %s✓%s %s\n' "$G" "$N" "$*"; }
warn() { printf '  %s!%s %s\n' "$Y" "$N" "$*"; }
bad()  { printf '  %s✗%s %s\n' "$R" "$N" "$*"; }
inf()  { printf '    %s%s%s\n' "$D" "$*" "$N"; }
hd()   { printf '\n%s══ %s%s\n' "$B" "$*" "$N"; }
cmd()  { printf '    %s%s%s\n' "$C" "$*" "$N"; }

command -v git >/dev/null 2>&1 || { echo "git não encontrado"; exit 1; }
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "não é repo git"; exit 1; }
cd "$ROOT" || exit 1

ATENCAO=0
nota() { ATENCAO=$((ATENCAO+1)); }

printf '%s╔══════════════════════════════════════════════════════╗%s\n' "$B" "$N"
printf '%s║  AUDITORIA DO REPOSITÓRIO                            ║%s\n' "$B" "$N"
printf '%s╚══════════════════════════════════════════════════════╝%s\n' "$B" "$N"
inf "$ROOT"
[ "$LIMPAR" -eq 0 ] && inf "modo: somente leitura"

# ===========================================================================
hd "1. GIT — branch e sincronia"
BR="$(git rev-parse --abbrev-ref HEAD)"
ok "branch atual: ${BR}   HEAD: $(git rev-parse --short HEAD)"
if git remote get-url origin >/dev/null 2>&1; then
  git fetch -q origin 2>/dev/null || warn "não consegui fazer fetch (offline?)"
  UP="origin/${BR}"
  if git rev-parse "$UP" >/dev/null 2>&1; then
    A="$(git rev-list --count "${UP}..HEAD" 2>/dev/null || true)"
    BH="$(git rev-list --count "HEAD..${UP}" 2>/dev/null || true)"
    [ "$A" -eq 0 ] && [ "$BH" -eq 0 ] && ok "em sincronia com ${UP}"
    [ "$A" -gt 0 ] && { warn "${A} commit(s) LOCAL não enviado(s)"; nota; cmd "git push"; }
    [ "$BH" -gt 0 ] && { warn "${BH} commit(s) no remoto não baixado(s)"; nota; cmd "git pull --ff-only"; }
  else
    warn "branch '${BR}' não existe no remoto (nunca foi enviado)"; nota
    cmd "git push -u origin ${BR}"
  fi
else
  warn "sem remoto configurado"
fi

# ===========================================================================
hd "2. GIT — branches: o que está vivo e o que já cumpriu função"
MAIN="main"; git show-ref -q --verify refs/heads/main 2>/dev/null || MAIN="master"
echo ""
printf '  %s%-38s %s%s\n' "$B" "branch" "situação" "$N"
git for-each-ref --format='%(refname:short)' refs/heads | while read -r b; do
  [ -z "$b" ] && continue
  if [ "$b" = "$MAIN" ]; then
    printf '  %-38s %s\n' "$b" "principal"
  elif git merge-base --is-ancestor "$b" "$MAIN" 2>/dev/null; then
    printf '  %-38s %sjá integrado ao %s — pode remover%s\n' "$b" "$G" "$MAIN" "$N"
  else
    N_C="$(git rev-list --count "${MAIN}..${b}" 2>/dev/null || echo '?')"
    printf '  %-38s %s%s commit(s) NÃO integrado(s)%s\n' "$b" "$Y" "$N_C" "$N"
  fi
done
echo ""
inf "remover um branch já integrado:"
cmd "git branch -d NOME"

# ===========================================================================
hd "3. GIT — worktrees (cópias paralelas do repo)"
WT="$(git worktree list 2>/dev/null)"
N_WT="$(printf "%s\n" "$WT" | grep -c . || true)"
if [ "$N_WT" -le 1 ]; then
  ok "só a árvore principal"
else
  warn "$((N_WT-1)) worktree(s) além da principal:"
  printf '%s\n' "$WT" | tail -n +2 | sed 's/^/      /'
  nota
  inf "worktrees são cópias completas do código — inflam qualquer busca"
  inf "e mantêm branches vivos. Foi o que poluiu diagnósticos anteriores."
  inf "remover entradas de worktrees que já não existem em disco:"
  cmd "git worktree prune"
  inf "remover uma worktree específica (confira antes que não tem trabalho):"
  cmd "git worktree remove CAMINHO"
fi

# ===========================================================================
hd "4. GIT — tags e stashes"
N_TAG="$(git tag --list 'pre-gateway-*' | grep -c . || true)"
[ "$N_TAG" -gt 0 ] && {
  warn "${N_TAG} tag(s) de snapshot 'pre-gateway-*':"
  git tag --list 'pre-gateway-*' | sed 's/^/      /'
  inf "são pontos de restauração; inofensivas. Remover quando não precisar:"
  cmd "git tag -d NOME"
} || ok "sem tags de snapshot"

N_ST="$(git stash list | grep -c . || true)"
[ "$N_ST" -gt 0 ] && {
  warn "${N_ST} stash(es) guardado(s):"
  git stash list | sed 's/^/      /'
  inf "ver conteúdo:"; cmd "git stash show -p stash@{0}"
  inf "descartar:";    cmd "git stash drop stash@{0}"
} || ok "sem stashes pendentes"

# ===========================================================================
hd "5. ARQUIVOS — o que não é do projeto"
EXT=""
for f in medir_cache.py modelos.py reset_bolsia.sh setup.sh integrar_gateway.sh \
         corrigir.sh restaurar.sh achar_llm.sh aplicar_modelo.sh auditar.sh \
         gateway_template.py.txt llm.py INTEGRACAO_BOLSIA.md Dockerfile; do
  if [ -f "$f" ] && ! git ls-files --error-unmatch "$f" >/dev/null 2>&1; then
    EXT="${EXT} $f"
  fi
done
if [ -n "$EXT" ]; then
  warn "scripts/arquivos externos soltos no repo (não rastreados pelo git):"
  for f in $EXT; do echo "      $f"; done
  nota
  if [ "$LIMPAR" -eq 1 ]; then
    mkdir -p "${HOME}/Downloads/claude-scripts"
    for f in $EXT; do
      [ "$f" = "auditar.sh" ] && continue
      mv "$f" "${HOME}/Downloads/claude-scripts/" 2>/dev/null && echo "      → movido: $f"
    done
    ok "movidos para ~/Downloads/claude-scripts/ (nada apagado)"
  else
    inf "--limpar move para ~/Downloads/claude-scripts/"
  fi
else
  ok "nenhum arquivo externo solto"
fi

BAKS="$(find . -name '*.bak' -not -path './.git/*' -not -path './.claude/*' 2>/dev/null)"
if [ -n "$BAKS" ]; then
  warn "arquivos .bak (sobras de edição):"
  printf '%s\n' "$BAKS" | sed 's/^/      /'
  nota
  inf "com o git funcionando, .bak é redundante. Conferir e remover:"
  cmd "find . -name '*.bak' -not -path './.git/*' -delete"
else
  ok "sem arquivos .bak"
fi

# ===========================================================================
hd "6. ARQUIVOS — árvore de trabalho"
DIRTY="$(git status --porcelain)"
if [ -z "$DIRTY" ]; then
  ok "árvore limpa (tudo commitado)"
else
  N_M="$(printf '%s\n' "$DIRTY" | grep -c '^ *M' || true)"
  N_U="$(printf '%s\n' "$DIRTY" | grep -c '^??' || true)"
  warn "${N_M} modificado(s), ${N_U} não rastreado(s):"
  printf '%s\n' "$DIRTY" | head -15 | sed 's/^/      /'
  nota
fi

# ===========================================================================
hd "7. PYTHON — módulos possivelmente órfãos"
inf "heurística: módulo cujo nome não aparece em nenhum import do pacote."
inf "NÃO é veredito — imports dinâmicos e entrypoints dão falso positivo."
echo ""
ORF=""
for f in server/app/*.py; do
  [ -f "$f" ] || continue
  base="$(basename "$f" .py)"
  case "$base" in __init__|main) continue ;; esac
  USOS="$(grep -rlE "(from +\.?${base} +import|import +\.?${base}\b)" \
          server --include='*.py' 2>/dev/null | grep -v "^${f}$" | grep -c . || true)"
  if [ "$USOS" -eq 0 ]; then
    ORF="${ORF} ${base}"
    printf '      %-28s %ssem import encontrado%s\n' "$(basename "$f")" "$Y" "$N"
  fi
done
[ -z "$ORF" ] && ok "todos os módulos são importados em algum lugar" || nota

# ===========================================================================
hd "8. CONFIGURAÇÃO — decisões desta sessão"
# 8a. requirements
[ -f requirements.txt ] && { warn "requirements.txt na RAIZ (o app usa server/) — divergência"; nota; } \
                        || ok "sem requirements.txt na raiz"
if [ -f server/requirements.txt ]; then
  ok "server/requirements.txt é a fonte de verdade ($(grep -c . server/requirements.txt) linhas)"
  grep -qE 'claude-gateway|^asyncpg' server/requirements.txt 2>/dev/null && {
    bad "ainda contém dependências do gateway (não usadas):"
    grep -nE 'claude-gateway|^asyncpg' server/requirements.txt | sed 's/^/        /'; nota; }
fi

# 8b. modelo default
if [ -f server/app/defaults.py ]; then
  MOD="$(grep -o '"model": "[^"]*"' server/app/defaults.py | head -1)"
  case "$MOD" in
    *'"model": ""'*) bad "modelo default VAZIO — usuário novo quebra com missing_model"; nota ;;
    *claude*)        ok "modelo default: ${MOD}" ;;
    *)               warn "modelo default: ${MOD:-não encontrado}" ;;
  esac
fi

# 8c. llm.py íntegro
if [ -f server/app/llm.py ]; then
  if grep -q "claude_gateway\|GovernedGateway" server/app/llm.py 2>/dev/null; then
    bad "server/app/llm.py contém o TEMPLATE do gateway, não o módulo do Boris+"; nota
    cmd "git checkout -- server/app/llm.py"
  elif grep -q "DEEP_FORMAT" server/app/llm.py 2>/dev/null; then
    ok "server/app/llm.py é o módulo original do Boris+"
  fi
fi

# 8d. main.py sem enxerto
grep -q "from .llm import lifespan" server/app/main.py 2>/dev/null && {
  bad "main.py ainda importa o lifespan do gateway (código morto)"; nota
  cmd "git checkout -- server/app/main.py"; } || ok "main.py sem enxerto do gateway"

# 8e. persistência
grep -q "sqlite3" server/app/db.py 2>/dev/null && {
  ok "persistência: SQLite em arquivo"
  inf "→ fica no Railway (volume persistente). Cloud Run apagaria os dados."; }

# 8f. pendência conhecida
grep -qE '"model"' server/app/store.py 2>/dev/null && \
  inf "store.py trata 'model' no merge — confira se preenche quando vier vazio" || \
  { warn "store.py não trata 'model' no merge — usuário ANTIGO segue com model vazio"; nota; }

# ===========================================================================
hd "9. TAMANHO — onde está o peso"
du -sh .git 2>/dev/null | sed 's/^/      /'
[ -d .claude ] && du -sh .claude 2>/dev/null | sed 's/^/      /'
for d in server mobile web client app; do
  [ -d "$d" ] && du -sh "$d" 2>/dev/null | sed 's/^/      /'
done

# ===========================================================================
hd "RESUMO"
if [ "$ATENCAO" -eq 0 ]; then
  ok "nada pendente — repositório organizado"
else
  warn "${ATENCAO} ponto(s) de atenção acima"
fi
echo ""
inf "Este script não apagou, não commitou e não editou nada."
[ "$LIMPAR" -eq 0 ] && inf "Para mover os arquivos externos: ./auditar.sh --limpar"
echo ""
