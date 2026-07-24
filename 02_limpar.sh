#!/usr/bin/env bash
# =============================================================================
# 02_limpar.sh — limpeza na ORDEM CORRETA, com rollback.
#
#   ./02_limpar.sh            # mostra o plano (default, não altera)
#   ./02_limpar.sh --aplicar  # executa
#
# ORDEM IMPORTA: worktree segura o branch. Apagar o branch antes falha.
#   1) snapshot (tag)  2) worktrees  3) prune  4) branches  5) arquivos
#
# NUNCA remove worktree com alteração não commitada — verifica antes e pula.
# Stash e tag NÃO são descartados automaticamente (são sua rede de segurança).
# =============================================================================
set -uo pipefail

APLICAR=0
case "${1:-}" in
  ""|--check) APLICAR=0 ;;
  --aplicar)  APLICAR=1 ;;
  -h|--help)  sed -n '2,14p' "$0"; exit 0 ;;
  *) echo "opção inválida: $1"; exit 1 ;;
esac

if [ -t 1 ]; then
  B=$'\033[1m'; G=$'\033[32m'; Y=$'\033[33m'; R=$'\033[31m'; C=$'\033[36m'; D=$'\033[2m'; N=$'\033[0m'
else B=""; G=""; Y=""; R=""; C=""; D=""; N=""; fi
ok()  { printf '  %s✓%s %s\n' "$G" "$N" "$*"; }
warn(){ printf '  %s!%s %s\n' "$Y" "$N" "$*"; }
bad() { printf '  %s✗%s %s\n' "$R" "$N" "$*"; }
inf() { printf '    %s%s%s\n' "$D" "$*" "$N"; }
hd()  { printf '\n%s══ %s%s\n' "$B" "$*" "$N"; }
cmd() { printf '    %s%s%s\n' "$C" "$*" "$N"; }
faria(){ printf '    %s[plano]%s %s\n' "$Y" "$N" "$*"; }

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "não é repo git"; exit 1; }
cd "$ROOT" || exit 1
BR="$(git rev-parse --abbrev-ref HEAD)"
MAIN=main; git show-ref -q --verify refs/heads/main 2>/dev/null || MAIN=master

printf '%s LIMPEZA — %s%s\n' "$B" "$ROOT" "$N"
[ "$APLICAR" -eq 0 ] && inf "MODO PLANO — nada será alterado"

# ---------------------------------------------------------------------------
hd "0. Pré-condições"
if [ "$BR" != "$MAIN" ]; then
  bad "você está em '${BR}'. Vá para ${MAIN} antes (branches serão removidos)."
  cmd "git checkout ${MAIN}"
  exit 1
fi
ok "em ${MAIN}"
SUJO="$(git status --porcelain | grep -vE '^\?\? (0[12]_|03_|auditar)' | grep -c . || true)"
if [ "${SUJO:-0}" -gt 0 ]; then
  bad "há alterações não commitadas. Commite ou guarde antes."
  git status --short | head -10 | sed 's/^/      /'
  exit 1
fi
ok "árvore limpa"

# ---------------------------------------------------------------------------
hd "1. Snapshot (rede de segurança)"
TS="$(date +%Y%m%d-%H%M%S)"; TAG="pre-limpeza-${TS}"
if [ "$APLICAR" -eq 1 ]; then
  git tag "$TAG" && ok "tag: ${TAG} -> $(git rev-parse --short HEAD)"
else
  faria "criar tag ${TAG} no commit atual"
fi

# ---------------------------------------------------------------------------
hd "2. Worktrees (antes dos branches — elas seguram os branches)"
N=0
git worktree list 2>/dev/null | tail -n +2 > /tmp/_wt.$$ || true
while read -r caminho _resto; do
  [ -z "$caminho" ] && continue
  N=$((N+1))
  if [ -d "$caminho" ]; then
    S="$(git -C "$caminho" status --porcelain 2>/dev/null | grep -c . || true)"
    if [ "${S:-0}" -gt 0 ]; then
      bad "PULANDO (tem ${S} alteração não commitada): $caminho"
      inf "revise antes; nada é removido com trabalho dentro"
      continue
    fi
  fi
  if [ "$APLICAR" -eq 1 ]; then
    git worktree remove --force "$caminho" 2>/dev/null \
      && ok "removida: $(basename "$caminho")" \
      || warn "falhou: $caminho"
  else
    faria "remover worktree $(basename "$caminho")"
  fi
done < /tmp/_wt.$$
rm -f /tmp/_wt.$$
[ "$N" -eq 0 ] && ok "nenhuma worktree extra"

if [ "$APLICAR" -eq 1 ]; then
  git worktree prune && ok "entradas órfãs removidas"
else
  faria "git worktree prune"
fi

# ---------------------------------------------------------------------------
hd "3. Branches já integrados ao ${MAIN}"
git for-each-ref --format='%(refname:short)' refs/heads > /tmp/_br.$$
while read -r b; do
  [ -z "$b" ] && continue
  [ "$b" = "$MAIN" ] && continue
  if git merge-base --is-ancestor "$b" "$MAIN" 2>/dev/null; then
    if [ "$APLICAR" -eq 1 ]; then
      git branch -d "$b" >/dev/null 2>&1 && ok "removido: $b" || warn "não removido: $b (em uso?)"
    else
      faria "git branch -d $b"
    fi
  else
    warn "MANTIDO (tem commit não integrado): $b"
  fi
done < /tmp/_br.$$
rm -f /tmp/_br.$$

# ---------------------------------------------------------------------------
hd "4. Arquivos residuais"
BAKS="$(find . -name '*.bak' -not -path './.git/*' -not -path './.claude/*' 2>/dev/null)"
if [ -n "$BAKS" ]; then
  printf '%s\n' "$BAKS" | sed 's/^/      /'
  if [ "$APLICAR" -eq 1 ]; then
    printf '%s\n' "$BAKS" | while read -r f; do
      mv "$f" "${f}.removido" 2>/dev/null && ok "renomeado: $f -> .removido"
    done
    inf "renomeados, não apagados. Apague quando confirmar:"
    cmd "find . -name '*.removido' -delete"
  else
    faria "renomear .bak para .removido (não apaga)"
  fi
else
  ok "sem arquivos .bak"
fi

EXT=""
for f in auditar.sh 01_verificar.sh 02_limpar.sh 03_gateway_cache.py \
         medir_cache.py modelos.py reset_bolsia.sh setup.sh aplicar_modelo.sh; do
  [ -f "$f" ] && ! git ls-files --error-unmatch "$f" >/dev/null 2>&1 && EXT="${EXT} $f"
done
if [ -n "$EXT" ]; then
  inf "scripts externos no repo:${EXT}"
  inf "deixe-os até terminar; depois mova para fora:"
  cmd "mkdir -p ~/Downloads/claude-scripts && mv${EXT} ~/Downloads/claude-scripts/"
fi

# ---------------------------------------------------------------------------
hd "5. NÃO removidos de propósito"
inf "tag pre-gateway-* e stash: são sua rede de segurança. Só você decide."
git stash list 2>/dev/null | sed 's/^/      /' || true
git tag --list 'pre-*' 2>/dev/null | sed 's/^/      /' || true
inf "quando não precisar mais:"
cmd "git stash drop stash@{0}   # confira antes: git stash show -p stash@{0}"
cmd "git tag -d NOME"

# ---------------------------------------------------------------------------
hd "RESULTADO"
if [ "$APLICAR" -eq 1 ]; then
  ok "limpeza concluída"
  echo ""
  du -sh .claude 2>/dev/null | sed 's/^/      /' || true
  inf "rollback: git checkout ${TAG}"
else
  inf "para executar: ./02_limpar.sh --aplicar"
fi
echo ""
