#!/usr/bin/env bash
# atualizar.sh — BolsIA (b3-agente) · aplica a ENTREGA (files.zip) e atualiza o servidor.
#
#   bash atualizar.sh ~/Downloads/files.zip "feat: pipeline IA 3 niveis"
#   bash atualizar.sh ~/Downloads/files.zip --somente-aplicar   # aplica+valida, sem git/deploy
#   bash atualizar.sh --somente-deploy "msg"                    # sem zip: só commit+push+health
#
# O que faz com um files.zip da entrega:
#   1. exige working tree limpa (suas mudanças locais nunca são atropeladas);
#   2. extrai o b3-agente.zip de dentro do files.zip (ou aceita o b3-agente.zip direto);
#   3. aplica os arquivos POR CIMA do repo (overlay aditivo), protegendo
#      .git/ node_modules/ ios/ dist/ .venv/ data/ *.db;
#   4. validação local: py_compile no backend, node --check nos módulos web,
#      suítes do backend (se o venv existir);
#   5. delega o deploy ao scripts/atualizar-servidor.sh (commit+push+health do
#      /api/scan) e verifica os endpoints das entregas: /api/scan/deep/estimate
#      e, da FASE 1 (Revisão Total), o snapshotId em /api/technicals (STU).
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]:-$0}")"
ROOT="$(pwd)"
RAILWAY_URL="https://boris.semente.dev"

say(){ printf "\n\033[1m== %s ==\033[0m\n" "$*"; }
ok(){ printf "  \033[32m[OK]\033[0m %s\n" "$*"; }
die(){ printf "  \033[31m[X]\033[0m %s\n" "$*" >&2; exit 1; }

ZIP=""; MSG="atualizacao"; SOMENTE_APLICAR=0; SOMENTE_DEPLOY=0
for arg in "$@"; do
  case "$arg" in
    --somente-aplicar) SOMENTE_APLICAR=1 ;;
    --somente-deploy)  SOMENTE_DEPLOY=1 ;;
    *.zip) ZIP="$arg" ;;
    *) MSG="$arg" ;;
  esac
done
[ "$SOMENTE_DEPLOY" = "1" ] && [ -n "$ZIP" ] && die "--somente-deploy não aceita zip"
[ "$SOMENTE_DEPLOY" = "0" ] && [ -z "$ZIP" ] && die "informe o files.zip da entrega (ou use --somente-deploy)"

# ---------- 1) aplicar a entrega ----------
if [ -n "$ZIP" ]; then
  [ -f "$ZIP" ] || die "arquivo não encontrado: $ZIP"
  if command -v git >/dev/null 2>&1 && [ -d .git ]; then
    git diff --quiet && git diff --cached --quiet \
      || die "há mudanças locais não commitadas — commite/descarte antes de aplicar a entrega"
    ok "working tree limpa"
  elif [ "$SOMENTE_APLICAR" = "0" ]; then
    # Blindagem do erro recorrente: pasta extraída do zip NÃO tem .git — o
    # deploy no fim falharia com "'origin' does not appear to be a git repository".
    die "esta pasta não é o seu clone git (.git ausente) — rode este comando DENTRO do clone (ou use --somente-aplicar para só aplicar os arquivos aqui)"
  fi

  say "Extraindo a entrega"
  TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
  unzip -q "$ZIP" -d "$TMP/pkg" || die "falha ao abrir $ZIP"
  INNER="$TMP/pkg/b3-agente.zip"
  if [ -f "$INNER" ]; then
    unzip -q "$INNER" -d "$TMP/src" || die "falha ao abrir o b3-agente.zip interno"
    # documentos da entrega (ESTADO/PROPOSTA/ESPEC/ATUALIZAR) acompanham o overlay
    cp "$TMP"/pkg/*.md "$TMP/src/" 2>/dev/null || true
  elif [ -d "$TMP/pkg/server" ] || [ -d "$TMP/pkg/web" ]; then
    mv "$TMP/pkg" "$TMP/src"   # era o b3-agente.zip direto
  else
    die "zip não reconhecido: esperado files.zip (com b3-agente.zip dentro) ou b3-agente.zip"
  fi
  [ -f "$TMP/src/server/app/main.py" ] || die "conteúdo inesperado: server/app/main.py ausente no zip"

  say "Aplicando por cima do repo (overlay aditivo, com proteções)"
  EXCL=( ".git" "node_modules" "web/ios" "dist" ".venv" "__pycache__" "data" )
  if command -v rsync >/dev/null 2>&1; then
    RS_EX=(); for e in "${EXCL[@]}"; do RS_EX+=( --exclude "$e/" ); done
    rsync -a "${RS_EX[@]}" --exclude "*.db" "$TMP/src/" "$ROOT/" || die "rsync falhou"
  else
    TAR_EX=(); for e in "${EXCL[@]}"; do TAR_EX+=( --exclude "./$e" --exclude "$e" ); done
    ( cd "$TMP/src" && tar cf - "${TAR_EX[@]}" --exclude "*.db" . ) | ( cd "$ROOT" && tar xf - ) \
      || die "cópia via tar falhou"
  fi
  ok "arquivos aplicados"
  if command -v git >/dev/null 2>&1 && [ -d .git ]; then
    echo "  — resumo do que mudou —"
    git status --short | sed 's/^/    /' | head -40
  fi

  say "Validação local"
  if [ -f scripts/verificar-arquivos.sh ]; then
    bash scripts/verificar-arquivos.sh || die "manifesto incompleto — a entrega não trouxe tudo que o app precisa"
  fi
  PYBIN="server/.venv/bin/python"; [ -x "$PYBIN" ] || PYBIN="python3"
  "$PYBIN" -m py_compile server/app/*.py || die "py_compile falhou no backend"
  ok "py_compile backend"
  if command -v node >/dev/null 2>&1; then
    for f in web/src/*.js; do node --check "$f" || die "node --check falhou em $f"; done
    ok "node --check web/src"
  fi
  if [ -x "server/.venv/bin/python" ]; then
    ( cd server && ./.venv/bin/python -m pytest -q ) || die "suítes do backend falharam — entrega NÃO deployada"
    ok "suítes do backend verdes"
  else
    echo "  (venv ausente — pulei as suítes; rode 'bash instalar.sh' para tê-las aqui)"
  fi
fi

[ "$SOMENTE_APLICAR" = "1" ] && { say "Concluído (somente aplicar)"; echo "  deploy quando quiser:  bash atualizar.sh --somente-deploy \"$MSG\""; exit 0; }

# ---------- 2) deploy (delegado) + health estendido ----------
say "Deploy no Railway (scripts/atualizar-servidor.sh)"
[ -f scripts/atualizar-servidor.sh ] || die "scripts/atualizar-servidor.sh não encontrado"
bash scripts/atualizar-servidor.sh "$MSG" || die "deploy falhou"

say "Health dos endpoints da entrega atual"
code=$(curl -s -o /tmp/deep_est.json -w "%{http_code}" \
  "$RAILWAY_URL/api/scan/deep/estimate?period=1mo&topN=2&tickers=PETR4,VALE3" || echo 000)
if [ "$code" = "200" ]; then
  python3 -c "import json; d=json.load(open('/tmp/deep_est.json')); print('  ✓ /api/scan/deep/estimate → topN', d.get('topN'), '· chamadas novas:', d.get('chamadas'))" \
    || ok "/api/scan/deep/estimate 200"
else
  die "/api/scan/deep/estimate → HTTP $code (veja os logs no Railway)"
fi

# FASE 1 (Revisão Total): o STU está no ar? /api/technicals deve devolver snapshotId.
code=$(curl -s -o /tmp/tech_stu.json -w "%{http_code}" \
  "$RAILWAY_URL/api/technicals/PETR4?period=1mo" || echo 000)
if [ "$code" = "200" ]; then
  python3 - <<'PYSTU' || die "/api/technicals 200 mas SEM snapshotId — build antigo no ar (F1 não deployada)"
import json, sys
d = json.load(open('/tmp/tech_stu.json'))
sid = d.get('snapshotId')
if not sid:
    sys.exit(1)
print('  \u2713 STU no ar: PETR4 snapshot #%s \u00b7 %s' % (sid, d.get('snapshotAt')))
PYSTU
else
  die "/api/technicals/PETR4 → HTTP $code (veja os logs no Railway)"
fi

say "Atualização concluída"
echo "  iPhone (quando houver mudança de app/plugin):  bash instalar.sh --iphone"
