#!/usr/bin/env bash
# =============================================================================
# aplicar_modelo.sh — valida o Boris+ e aplica o modelo default.
# Rode na RAIZ do b3-agente.
#
#   ./aplicar_modelo.sh              # VALIDA e mostra o que faria (não altera)
#   ./aplicar_modelo.sh --aplicar    # aplica (com backup)
#   ./aplicar_modelo.sh --reverter   # desfaz usando o backup
#
# O QUE FAZ
#   1. valida ambiente (git, branch, árvore, arquivos)
#   2. tira os scripts do Claude de dentro do repo (move, não apaga)
#   3. troca "model": "" por "model": "claude-sonnet-5" em defaults.py
#   4. verifica se o backfill cobre usuários ANTIGOS (só reporta)
#   5. valida sintaxe e mostra o diff para você revisar
#
# O QUE NÃO FAZ (de propósito)
#   Não faz commit. Não faz push. Não mexe no store.py. Você revisa e decide.
# =============================================================================
set -uo pipefail

MODO="check"
case "${1:-}" in
  ""|--check) MODO="check" ;;
  --aplicar)  MODO="aplicar" ;;
  --reverter) MODO="reverter" ;;
  -h|--help)  sed -n '2,20p' "$0"; exit 0 ;;
  *) echo "opção inválida: $1 (use --check, --aplicar, --reverter)"; exit 1 ;;
esac

if [ -t 1 ]; then
  B=$'\033[1m'; G=$'\033[32m'; Y=$'\033[33m'; R=$'\033[31m'; C=$'\033[36m'; N=$'\033[0m'
else B=""; G=""; Y=""; R=""; C=""; N=""; fi
ok()   { printf '%s✓%s %s\n' "$G" "$N" "$*"; }
warn() { printf '%s!%s %s\n' "$Y" "$N" "$*"; }
err()  { printf '%s✗%s %s\n' "$R" "$N" "$*" >&2; }
hd()   { printf '\n%s%s%s\n' "$B" "$*" "$N"; }
die()  { err "$*"; exit 1; }

DEF="server/app/defaults.py"
MODELO="claude-sonnet-5"
FALHAS=0

# ---------------------------------------------------------------------------
if [ "$MODO" = "reverter" ]; then
  hd "Revertendo"
  if [ -f "${DEF}.bak" ]; then
    mv "${DEF}.bak" "$DEF" && ok "$DEF restaurado do backup"
  else
    warn "sem ${DEF}.bak — use: git checkout -- $DEF"
    git checkout -- "$DEF" 2>/dev/null && ok "restaurado via git" || err "não consegui reverter"
  fi
  git diff --stat 2>/dev/null | sed 's/^/    /'
  exit 0
fi

# ---------------------------------------------------------------------------
hd "1 — Ambiente"
command -v git >/dev/null 2>&1 || die "git não encontrado"
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || die "não é repo git — rode dentro do b3-agente"
[ "$(pwd)" = "$ROOT" ] || { cd "$ROOT" || die "falhou cd"; warn "movi para a raiz: $ROOT"; }
ok "repo: ${C}${ROOT}${N}"

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
  warn "você está em '${BRANCH}'. Recomendado: git checkout -b modelo-default"
  FALHAS=$((FALHAS+1))
else
  ok "branch: ${C}${BRANCH}${N} (isolado — rollback é 'git checkout main')"
fi

[ -f "$DEF" ] || die "não achei $DEF"
ok "$DEF encontrado"

# ---------------------------------------------------------------------------
hd "2 — Scripts do Claude dentro do repo"
EXTERNOS=""
for f in medir_cache.py modelos.py reset_bolsia.sh setup.sh integrar_gateway.sh \
         corrigir.sh restaurar.sh achar_llm.sh aplicar_modelo.sh gateway_template.py.txt; do
  [ -f "$f" ] && EXTERNOS="${EXTERNOS} $f"
done
if [ -n "$EXTERNOS" ]; then
  warn "presentes no repo (não pertencem ao Boris+):"
  for f in $EXTERNOS; do echo "      $f"; done
  if [ "$MODO" = "aplicar" ]; then
    mkdir -p "${HOME}/Downloads/claude-scripts"
    for f in $EXTERNOS; do
      [ "$f" = "aplicar_modelo.sh" ] && continue   # não move a si mesmo agora
      mv "$f" "${HOME}/Downloads/claude-scripts/" 2>/dev/null && echo "      movido: $f"
    done
    ok "movidos para ~/Downloads/claude-scripts/ (nada apagado)"
  else
    echo "      -> --aplicar move para ~/Downloads/claude-scripts/"
  fi
else
  ok "repo limpo de scripts externos"
fi

# ---------------------------------------------------------------------------
hd "3 — Estado do arquivo a alterar"
ATUAL="$(grep -n '"model":' "$DEF" | head -5)"
echo "$ATUAL" | sed 's/^/    /'
N_VAZIO="$(grep -c '"model": ""' "$DEF" || true)"
N_JA="$(grep -c "\"model\": \"${MODELO}\"" "$DEF" || true)"

if [ "$N_JA" -gt 0 ]; then
  ok "já está em ${MODELO} — nada a fazer"
  APLICAR_EDIT=0
elif [ "$N_VAZIO" -eq 1 ]; then
  ok "encontrado exatamente 1 \"model\": \"\" — seguro alterar"
  APLICAR_EDIT=1
elif [ "$N_VAZIO" -eq 0 ]; then
  err "não achei \"model\": \"\" — o arquivo mudou? Edite à mão."
  APLICAR_EDIT=0; FALHAS=$((FALHAS+1))
else
  err "achei ${N_VAZIO} ocorrências de \"model\": \"\" — ambíguo. Edite à mão."
  APLICAR_EDIT=0; FALHAS=$((FALHAS+1))
fi

# ---------------------------------------------------------------------------
hd "4 — Usuários ANTIGOS pegam o novo default?"
echo "    default_state() vale só para conta NOVA. Quem já existe tem a config"
echo "    gravada no SQLite com model vazio."
BF="$(grep -nE 'backfill|setdefault|\.get\("model"|"model"' server/app/store.py 2>/dev/null | head -8 || true)"
if [ -n "$BF" ]; then
  echo "$BF" | sed 's/^/      /'
  if echo "$BF" | grep -q '"model"'; then
    ok "store.py menciona 'model' — confira se o merge preenche quando vazio"
  else
    warn "store.py NÃO menciona 'model' no merge/backfill"
    echo "      -> usuários antigos continuarão com model vazio (erro missing_model)"
    echo "      -> conserto: no merge de config, se cfg.get('model') estiver vazio,"
    echo "         preencher com o default. Isso é lógica sua — não altero."
  fi
else
  warn "não consegui inspecionar server/app/store.py"
fi

# ---------------------------------------------------------------------------
hd "5 — Confirmações de arquitetura (só leitura)"
if grep -q "sqlite3" server/app/db.py 2>/dev/null; then
  ok "SQLite em arquivo confirmado"
  echo "      -> Boris+ fica no Railway (volume persistente)."
  echo "      -> Cloud Run apagaria os dados a cada scale-to-zero. NÃO migrar."
fi
[ -f requirements.txt ] && warn "existe requirements.txt na raiz (o app usa server/)" \
  || ok "sem requirements.txt na raiz — contexto de build é server/"
grep -qE 'claude-gateway|^asyncpg' server/requirements.txt 2>/dev/null \
  && { warn "server/requirements.txt ainda tem dependências do gateway:"; \
       grep -nE 'claude-gateway|^asyncpg' server/requirements.txt | sed 's/^/      /'; \
       FALHAS=$((FALHAS+1)); } \
  || ok "server/requirements.txt sem dependências do gateway"

# ---------------------------------------------------------------------------
if [ "$MODO" = "check" ]; then
  hd "MODO CHECK — nada foi alterado"
  [ "$APLICAR_EDIT" -eq 1 ] && echo "    Alteração pendente: \"model\": \"\" -> \"model\": \"${MODELO}\""
  [ "$FALHAS" -gt 0 ] && warn "${FALHAS} ponto(s) de atenção acima" || ok "tudo validado"
  echo ""
  echo "    Para aplicar: ${C}./aplicar_modelo.sh --aplicar${N}"
  exit 0
fi

# ---------------------------------------------------------------------------
hd "6 — Aplicando"
if [ "$APLICAR_EDIT" -eq 1 ]; then
  cp "$DEF" "${DEF}.bak" && ok "backup: ${DEF}.bak"
  python3 - "$DEF" "$MODELO" <<'PY'
import sys
p, modelo = sys.argv[1], sys.argv[2]
src = open(p, encoding="utf-8").read()
alvo = '"model": ""'
if src.count(alvo) != 1:
    print("ABORT"); sys.exit(1)
open(p, "w", encoding="utf-8").write(src.replace(alvo, f'"model": "{modelo}"'))
print("OK")
PY
  if [ $? -ne 0 ]; then
    mv "${DEF}.bak" "$DEF"; die "edição abortada — arquivo restaurado"
  fi
  if python3 -c "import ast;ast.parse(open('$DEF',encoding='utf-8').read())" 2>/dev/null; then
    ok "sintaxe válida após a alteração"
  else
    mv "${DEF}.bak" "$DEF"; die "SINTAXE INVÁLIDA — revertido automaticamente"
  fi
else
  warn "nenhuma edição aplicada (veja o item 3)"
fi

hd "7 — Revise o diff"
git diff --stat | sed 's/^/    /'
echo ""
git diff "$DEF" | sed 's/^/    /'

hd "Próximos passos (você decide)"
cat <<EOF
  Se o diff acima mostra SÓ a linha do model:

    ${C}git add -A${N}
    ${C}git commit -m "default: ${MODELO} (cacheia >=1024, menor custo acima do piso)"${N}
    ${C}git checkout main && git merge ${BRANCH} && git push${N}

  Rollback a qualquer momento:
    ${C}./aplicar_modelo.sh --reverter${N}     (desfaz o arquivo)
    ${C}git checkout main${N}                   (descarta o branch inteiro)
EOF
