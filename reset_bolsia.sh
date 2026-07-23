#!/usr/bin/env bash
# =============================================================================
# reset_bolsia.sh — volta o BolsIA ao estado limpo do git, SEM perder nada.
#
#   ./reset_bolsia.sh --check    # só mostra o que seria feito (default seguro)
#   ./reset_bolsia.sh --reset    # snapshot + limpa a árvore de trabalho
#   ./reset_bolsia.sh --pull     # snapshot + limpa + traz o último do remoto
#   ./reset_bolsia.sh --undo     # restaura o snapshot mais recente
#   ./reset_bolsia.sh --list     # lista os snapshots existentes
#
# COMO O ROLLBACK FUNCIONA (dupla rede):
#   1. TAG git em HEAD  -> ponteiro para o commit atual, some nunca
#   2. STASH com -u     -> guarda TODAS as alterações não commitadas,
#                          inclusive arquivos novos (llm.py.bak, scripts etc.)
#   Nada é apagado: `git stash` é reversível com `git stash pop`.
#
# NÃO usa: reset --hard sem stash, git clean sem backup, rm.
# =============================================================================
set -uo pipefail

MODE="check"
case "${1:-}" in
  --check|"") MODE="check" ;;
  --reset)    MODE="reset" ;;
  --pull)     MODE="pull" ;;
  --undo)     MODE="undo" ;;
  --list)     MODE="list" ;;
  -h|--help)  sed -n '2,20p' "$0"; exit 0 ;;
  *) echo "opção inválida: $1 (use --check, --reset, --pull, --undo, --list)"; exit 1 ;;
esac

if [ -t 1 ]; then
  B=$'\033[1m'; G=$'\033[32m'; Y=$'\033[33m'; R=$'\033[31m'; C=$'\033[36m'; N=$'\033[0m'
else B=""; G=""; Y=""; R=""; C=""; N=""; fi
ok()   { printf '%s✓%s %s\n' "$G" "$N" "$*"; }
warn() { printf '%s!%s %s\n' "$Y" "$N" "$*"; }
err()  { printf '%s✗%s %s\n' "$R" "$N" "$*" >&2; }
hd()   { printf '\n%s%s%s\n' "$B" "$*" "$N"; }
die()  { err "$*"; exit 1; }

command -v git >/dev/null 2>&1 || die "git não encontrado."
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || die "não é um repositório git — rode dentro do b3-agente."
cd "$ROOT" || die "não consegui entrar em $ROOT"
ok "repo: ${C}${ROOT}${N}"

BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
PREFIX="pre-gateway"

# ---------------------------------------------------------------------------
if [ "$MODE" = "list" ]; then
  hd "Snapshots disponíveis"
  echo "  ${B}Tags:${N}"
  git tag --list "${PREFIX}-*" --sort=-creatordate | head -10 | sed 's/^/    /' || true
  echo ""
  echo "  ${B}Stashes:${N}"
  git stash list | grep "$PREFIX" | sed 's/^/    /' || echo "    (nenhum)"
  echo ""
  echo "  Restaurar o mais recente:  ${C}./reset_bolsia.sh --undo${N}"
  echo "  Restaurar um específico:   ${C}git stash apply stash@{N}${N}"
  exit 0
fi

# ---------------------------------------------------------------------------
if [ "$MODE" = "undo" ]; then
  hd "Desfazendo — restaurando o snapshot mais recente"
  ST="$(git stash list | grep "$PREFIX" | head -1 | cut -d: -f1)"
  [ -n "$ST" ] || die "nenhum snapshot '${PREFIX}' encontrado. Veja: ./reset_bolsia.sh --list"
  echo "  restaurando: $(git stash list | grep "$PREFIX" | head -1)"
  # 'apply' (não 'pop'): mantém o stash guardado mesmo após restaurar.
  if git stash apply "$ST"; then
    ok "alterações restauradas (o snapshot CONTINUA salvo em $ST)"
    echo "  para descartá-lo depois de conferir: ${C}git stash drop $ST${N}"
  else
    err "conflito ao restaurar. Nada foi perdido — resolva e rode: git stash apply $ST"
    exit 1
  fi
  git status --short | head -20 | sed 's/^/    /'
  exit 0
fi

# ---------------------------------------------------------------------------
hd "1 — Estado atual"
DIRTY="$(git status --porcelain)"
if [ -z "$DIRTY" ]; then
  ok "árvore de trabalho já está limpa (nada a salvar)"
else
  N_MOD="$(printf '%s\n' "$DIRTY" | grep -c '^ *M' || true)"
  N_NEW="$(printf '%s\n' "$DIRTY" | grep -c '^??' || true)"
  warn "${N_MOD} modificado(s), ${N_NEW} novo(s):"
  printf '%s\n' "$DIRTY" | head -20 | sed 's/^/    /'
  [ "$(printf '%s\n' "$DIRTY" | wc -l)" -gt 20 ] && echo "    ... e mais"
fi
echo "  branch: ${C}${BRANCH}${N}   HEAD: ${C}$(git rev-parse --short HEAD)${N}"

if [ "$MODE" = "check" ]; then
  hd "MODO CHECK — nada foi alterado"
  cat <<EOF
  Se rodar ${C}--reset${N}, eu faria, nesta ordem:
    1. tag ${PREFIX}-<timestamp> no commit atual  (ponteiro permanente)
    2. git stash push -u  (guarda TUDO acima, inclusive arquivos novos)
    3. árvore volta ao estado limpo do commit atual
  Se rodar ${C}--pull${N}: o acima + traz o último do remoto (merge ff-only).
  Tudo desfazível com ${C}--undo${N}.
EOF
  exit 0
fi

# ---------------------------------------------------------------------------
hd "2 — Criando o snapshot (rede de segurança)"
TS="$(date +%Y%m%d-%H%M%S)"
TAG="${PREFIX}-${TS}"

git tag "$TAG" && ok "tag criada: ${C}${TAG}${N} -> $(git rev-parse --short HEAD)" \
  || warn "não consegui criar a tag (seguindo — o stash é a rede principal)"

if [ -n "$DIRTY" ]; then
  if git stash push -u -m "${PREFIX}-${TS}" >/dev/null 2>&1; then
    ok "alterações guardadas no stash: ${C}${PREFIX}-${TS}${N}"
    ok "árvore de trabalho limpa"
  else
    die "falha ao criar o stash — NADA foi alterado. Verifique 'git status'."
  fi
else
  ok "nada para guardar"
fi

# ---------------------------------------------------------------------------
if [ "$MODE" = "pull" ]; then
  hd "3 — Trazendo a última versão do remoto"
  if git remote get-url origin >/dev/null 2>&1; then
    git fetch origin && ok "fetch ok"
    # merge ff-only: nunca cria merge nem reescreve histórico. Se divergiu,
    # falha e avisa — em vez de fazer algo irreversível por conta própria.
    if git merge --ff-only "origin/${BRANCH}" 2>/dev/null; then
      ok "atualizado para origin/${BRANCH} -> $(git rev-parse --short HEAD)"
    else
      warn "não deu fast-forward (branch local divergiu do remoto)."
      echo "    seu trabalho está seguro na tag ${TAG} e no stash."
      echo "    decida à mão:  ${C}git log --oneline HEAD..origin/${BRANCH}${N}"
    fi
  else
    warn "sem remoto 'origin' configurado — pulei o pull"
  fi
fi

# ---------------------------------------------------------------------------
hd "4 — Verificação"
git status --short | head -10 | sed 's/^/    /' || true
[ -z "$(git status --porcelain)" ] && ok "árvore limpa" || warn "ainda há alterações (veja acima)"
echo "  HEAD agora: ${C}$(git rev-parse --short HEAD)${N}"

hd "Rollback"
cat <<EOF
  Desfazer tudo:          ${C}./reset_bolsia.sh --undo${N}
  Ver snapshots:          ${C}./reset_bolsia.sh --list${N}
  Voltar ao commit antigo:${C}git checkout ${TAG}${N}
  Ver o que foi guardado: ${C}git stash show -p stash@{0}${N}

  Nada foi apagado. A tag e o stash permanecem até você removê-los.
EOF
