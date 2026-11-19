#!/usr/bin/env bash
# configurar-apns.sh — Boris+ · configura o push (APNs) no Railway em 1 comando.
#
#   bash scripts/configurar-apns.sh 42D5CDUT49             # lê $P8_DIR/AuthKey_42D5CDUT49.p8
#   bash scripts/configurar-apns.sh 42D5CDUT49 --sandbox   # build de desenvolvimento
#   bash scripts/configurar-apns.sh                        # lista as chaves em $P8_DIR
#   bash scripts/configurar-apns.sh /outro/AuthKey_XXXXXXXXXX.p8   # caminho explícito
#
# P8_DIR (padrão /Users/acamerini/p8) é a pasta dos AuthKey_*.p8 baixados do
# portal Apple — a mesma que o diagnosticar-apns.sh varre.
#
# Parâmetros JÁ preenchidos com os dados da conta do Alex (confira se mudar):
#   APNS_TEAM_ID = LC65399YC9   (Membership da conta Apple Developer)
#   APNS_KEY_ID  = 42D5CDUT49   (vale em produção E sandbox — 2026-11-18; a antiga
#                               22Y76F52NJ é só sandbox e dava BadEnvironmentKeyInToken)
#   APNS_TOPIC   = com.alexandrecamerini.bolsia  (appId do capacitor.config.ts)
#
# SEGURANÇA: a chave .p8 NUNCA entra no git (o .gitignore bloqueia *.p8 e o
# git-do-zero recusa commit com ela). Ela vai só para as Variables do Railway.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.."

say(){ printf "\n\033[1m== %s ==\033[0m\n" "$*"; }
ok(){ printf "  \033[32m[OK]\033[0m %s\n" "$*"; }
die(){ printf "  \033[31m[X]\033[0m %s\n" "$*" >&2; exit 1; }

TEAM_ID="LC65399YC9"
# FASE 7 (fix do BadEnvironmentKeyInToken): o Key ID NÃO é mais fixo — a Apple
# nomeia o arquivo como AuthKey_<KEYID>.p8, então o script DETECTA o ID do
# próprio arquivo (troca de chave nunca mais exige editar este script).
# Fallback: a última chave conhecida; override: KEY_ID=XXXX bash scripts/...
KEY_ID="${KEY_ID:-42D5CDUT49}"
TOPIC="com.alexandrecamerini.bolsia"
# Serviço do backend no Railway. Sem --service, o CLI usa o serviço linkado ao
# diretório — e com "Linked service: None" grava FORA do b3agente (achado
# 2026-11-18: chave nova aplicada e o servidor seguia com a velha).
RAILWAY_SERVICE="${RAILWAY_SERVICE:-b3agente}"
P8_DIR="${P8_DIR:-/Users/acamerini/p8}"

P8=""; SANDBOX=""
for arg in "$@"; do
  case "$arg" in
    --sandbox) SANDBOX="1" ;;
    *) P8="$arg" ;;
  esac
done
if [ -z "$P8" ]; then
  [ -d "$P8_DIR" ] || die "pasta $P8_DIR não existe — crie e mova os AuthKey_*.p8 para lá (ou P8_DIR=/outra/pasta)"
  printf "  chaves em %s:\n" "$P8_DIR"
  ls "$P8_DIR" | sed -n 's/^AuthKey_\([A-Z0-9]\{10\}\)\.p8$/    \1/p'
  die "informe o Key ID (ex.: bash scripts/configurar-apns.sh ${KEY_ID}) ou o caminho do .p8"
fi
# Só o Key ID (10 caracteres) → arquivo padrão da Apple dentro de P8_DIR.
if printf "%s" "$P8" | grep -qE '^[A-Z0-9]{10}$'; then
  P8="$P8_DIR/AuthKey_$P8.p8"
fi
P8="${P8/#\~/$HOME}"
[ -f "$P8" ] || die "arquivo não encontrado: $P8"

say "1/3 · Validando a chave"
head -c 40 "$P8" | grep -q "BEGIN PRIVATE KEY" || die "não parece um .p8 (PEM) válido"
if command -v openssl >/dev/null 2>&1; then
  openssl pkey -in "$P8" -noout >/dev/null 2>&1 || die "a chave não é parseável (arquivo corrompido?)"
  ok "chave PEM válida"
else
  ok "formato PEM ok (openssl ausente — validação profunda pulada)"
fi
# Detecta o Key ID pelo nome padrão da Apple (AuthKey_<10 chars>.p8). Se o
# nome foi alterado e não dá para detectar, mantém o fallback e avisa.
DETECTED="$(basename "$P8" | sed -n 's/^AuthKey_\([A-Z0-9]\{10\}\)\.p8$/\1/p')"
if [ -n "$DETECTED" ]; then
  if [ "$DETECTED" != "$KEY_ID" ]; then
    echo "  chave NOVA detectada pelo nome do arquivo: $DETECTED (substitui $KEY_ID)"
  fi
  KEY_ID="$DETECTED"
  ok "Key ID em uso: $KEY_ID (detectado do arquivo)"
else
  echo "  (aviso: nome fora do padrão AuthKey_XXXXXXXXXX.p8 — usando Key ID $KEY_ID;"
  echo "   se for outra chave, rode: KEY_ID=SEUKEYID bash scripts/configurar-apns.sh $P8)"
fi
KEY_CONTENT="$(cat "$P8")"

say "2/3 · Aplicando as variáveis no Railway"
if command -v railway >/dev/null 2>&1 && railway status >/dev/null 2>&1; then
  railway variables --service "$RAILWAY_SERVICE" --set "APNS_TEAM_ID=$TEAM_ID" --set "APNS_KEY_ID=$KEY_ID" \
    --set "APNS_TOPIC=$TOPIC" --set "APNS_AUTH_KEY=$KEY_CONTENT" \
    ${SANDBOX:+--set "APNS_SANDBOX=1"} || die "railway variables falhou — use o caminho manual abaixo"
  ok "variáveis aplicadas no serviço $RAILWAY_SERVICE via Railway CLI (redeploy automático)"
else
  echo "  Railway CLI ausente/não logado — caminho manual (2 minutos):"
  if command -v pbcopy >/dev/null 2>&1; then
    printf "%s" "$KEY_CONTENT" | pbcopy
    ok "conteúdo da chave COPIADO para o clipboard (⌘V no valor de APNS_AUTH_KEY)"
  fi
  cat <<FIM

  Railway → serviço do backend → Variables → + New Variable (4 vezes):
    APNS_TEAM_ID   = $TEAM_ID
    APNS_KEY_ID    = $KEY_ID
    APNS_TOPIC     = $TOPIC
    APNS_AUTH_KEY  = (cole o clipboard — o PEM inteiro, com BEGIN/END)
FIM
  [ -n "$SANDBOX" ] && echo "    APNS_SANDBOX   = 1   (build de desenvolvimento)"
  echo "  Salve — o Railway redeploya sozinho."
  read -r -p "  Pressione Enter quando tiver salvo as variáveis… " _ || true
fi

say "3/3 · Verificando no servidor"
URL="https://boris.semente.dev"
for i in 1 2 3 4 5 6; do
  ST=$(curl -s "$URL/api/agent/status" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); p=d.get('push') or {}; print('configurado' if p.get('configurado') else 'pendente')" 2>/dev/null || echo "erro")
  [ "$ST" = "configurado" ] && { ok "APNs CONFIGURADO no servidor ✓"; break; }
  [ "$i" = "6" ] && die "servidor ainda reporta push '$ST' — aguarde o redeploy terminar e rode de novo (só o passo 3 repete: este script é idempotente)"
  echo "  aguardando redeploy… ($i/6)"; sleep 20
done

cat <<'FIM'

Próximo (no iPhone): Operador IA → "Ativar push das ações" → aceitar a
permissão → "Testar push agora" deve chegar no aparelho. Guarde o backup do
.p8 em local seguro (a Apple não permite baixá-lo de novo).
FIM
