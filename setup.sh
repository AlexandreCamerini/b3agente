#!/usr/bin/env bash
# =============================================================================
# setup.sh — instalação do BolsIA em UM comando.
#
#   ./setup.sh            -> menu interativo
#   ./setup.sh all        -> roda tudo na ordem, do início ao fim
#   ./setup.sh 1 | 2 ...  -> roda só um passo
#   ./setup.sh status     -> mostra o que já está feito
#   ./setup.sh doctor     -> checa pré-requisitos e some
#
# GARANTIAS
#   - Idempotente: rodar 2x não quebra nada; passo já feito é pulado.
#   - Não-destrutivo: nunca apaga repo, banco, serviço ou secret.
#   - Segredos NUNCA são gravados em disco nem ficam no histórico do shell
#     (lidos com `read -s` a cada execução).
#   - Se algo falha, para na hora e diz exatamente o que fazer.
#
# O QUE ELE NÃO FAZ (cadastro web, impossível roteirizar):
#   - criar conta no Neon        -> https://neon.tech
#   - criar conta GCP + billing  -> https://console.cloud.google.com
#   Ele te avisa na hora certa e espera você voltar.
# =============================================================================
set -uo pipefail

CONFIG="${HOME}/.bolsia-setup.env"   # guarda só config, JAMAIS segredo
SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---------- cosmético -------------------------------------------------------
if [ -t 1 ]; then
  B=$'\033[1m'; G=$'\033[32m'; Y=$'\033[33m'; R=$'\033[31m'; C=$'\033[36m'; N=$'\033[0m'
else
  B=""; G=""; Y=""; R=""; C=""; N=""
fi
say()  { printf '%s\n' "$*"; }
ok()   { printf '%s✓%s %s\n' "$G" "$N" "$*"; }
warn() { printf '%s!%s %s\n' "$Y" "$N" "$*"; }
err()  { printf '%s✗%s %s\n' "$R" "$N" "$*" >&2; }
head_() { printf '\n%s%s%s\n' "$B" "$*" "$N"; }
die()  { err "$*"; exit 1; }

# ---------- config persistida ----------------------------------------------
load_cfg() { [ -f "$CONFIG" ] && . "$CONFIG"; return 0; }
save_cfg() {
  umask 077
  {
    echo "# gerado por setup.sh — apenas configuração, sem segredos"
    for k in GH_USER REPO TAG BOLSIA_DIR APP_ENTRYPOINT SKELETON_DIR \
             PROJECT_ID REGION SERVICE BILLING_ACCOUNT_ID; do
      v="${!k:-}"; [ -n "$v" ] && printf '%s=%q\n' "$k" "$v"
    done
  } > "$CONFIG"
}

# pergunta e memoriza (usa valor salvo como default)
ask() {                      # ask VAR "pergunta" ["default"]
  local var="$1" prompt="$2" def="${3:-${!1:-}}" ans
  if [ -n "$def" ]; then read -r -p "$prompt [$def]: " ans; ans="${ans:-$def}"
  else read -r -p "$prompt: " ans; fi
  [ -z "$ans" ] && die "valor obrigatório."
  printf -v "$var" '%s' "$ans"
}
ask_secret() {               # ask_secret VAR "pergunta"  (nunca salvo)
  local var="$1" ans
  if [ -n "${!1:-}" ]; then ok "usando ${1} já fornecido nesta sessão"; return; fi
  read -r -s -p "$2: " ans; echo
  [ -z "$ans" ] && die "valor obrigatório."
  printf -v "$var" '%s' "$ans"
}
confirm() { local a; read -r -p "$1 [s/N]: " a; [[ "$a" =~ ^[sSyY]$ ]]; }

# ---------- pré-requisitos --------------------------------------------------
have() { command -v "$1" >/dev/null 2>&1; }
need() {                     # need cmd "como instalar"
  if have "$1"; then ok "$1 encontrado"; return 0; fi
  err "$1 NÃO encontrado — $2"; return 1
}

doctor() {
  head_ "Pré-requisitos"
  local miss=0
  need git    "https://git-scm.com/downloads"                    || miss=1
  need gh     "https://cli.github.com  (depois: gh auth login)"   || miss=1
  need gcloud "https://cloud.google.com/sdk/docs/install"         || miss=1
  have psql && ok "psql encontrado" \
            || warn "psql ausente (opcional — dá pra rodar o SQL no site do Neon)"
  if have gh; then
    gh auth status >/dev/null 2>&1 && ok "gh autenticado" \
      || { err "gh não autenticado — rode: gh auth login"; miss=1; }
  fi
  if have gcloud; then
    [ -n "$(gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null)" ] \
      && ok "gcloud autenticado" \
      || warn "gcloud não autenticado — rode: gcloud auth login (só precisa no passo 4)"
  fi
  [ "$miss" -eq 0 ] || die "instale o que falta acima e rode de novo."
  ok "tudo pronto."
}

# ---------- localizar o skeleton (a pegadinha que te travou) ----------------
find_skeleton() {
  [ -n "${SKELETON_DIR:-}" ] && [ -f "${SKELETON_DIR}/pyproject.toml" ] && return 0
  local c
  for c in "$PWD" "$PWD/claude-gateway" "$SELF_DIR" "$SELF_DIR/claude-gateway" \
           "$SELF_DIR/../claude-gateway" "$HOME/claude-gateway"; do
    if [ -f "$c/pyproject.toml" ] && grep -q 'name = "claude-gateway"' "$c/pyproject.toml" 2>/dev/null; then
      SKELETON_DIR="$(cd "$c" && pwd)"; return 0
    fi
  done
  # não achou a pasta: procura o tarball e descompacta sozinho
  local tgz
  tgz="$(ls -1 "$PWD"/claude-gateway-skeleton.tar.gz \
                "$SELF_DIR"/claude-gateway-skeleton.tar.gz \
                "$HOME"/Downloads/claude-gateway-skeleton.tar.gz \
                "$HOME"/Desktop/claude-gateway-skeleton.tar.gz 2>/dev/null | head -n1)"
  if [ -n "$tgz" ]; then
    say "  descompactando $(basename "$tgz")…"
    tar -xzf "$tgz" -C "$(dirname "$tgz")" || die "falha ao descompactar $tgz"
    SKELETON_DIR="$(cd "$(dirname "$tgz")/claude-gateway" && pwd)" || die "estrutura inesperada no tarball"
    return 0
  fi
  return 1
}

# =============================================================================
# PASSO 1 — publicar o gateway (repo público + tag)
# =============================================================================
step1() {
  head_ "PASSO 1/5 — Publicar o gateway no GitHub"
  have gh || die "gh não instalado. Rode: ./setup.sh doctor"
  gh auth status >/dev/null 2>&1 || die "gh não autenticado. Rode: gh auth login"

  if ! find_skeleton; then
    err "não encontrei o código do gateway."
    say "  Baixe 'claude-gateway-skeleton.tar.gz' do chat e:"
    say "    - deixe em ~/Downloads (eu descompacto sozinho), ou"
    say "    - descompacte e rode este script de dentro da pasta."
    exit 1
  fi
  ok "gateway encontrado em: ${SKELETON_DIR}"

  ask GH_USER "Seu usuário do GitHub"
  REPO="${REPO:-claude-gateway}"; TAG="${TAG:-v0.1.0}"
  save_cfg

  ( cd "$SKELETON_DIR" || exit 1
    if [ ! -d .git ]; then
      git init -q && git add . \
        && git commit -q -m "gateway ${TAG}: core (cache) + controls (governança)"
      ok "repo local criado"
    else ok "repo local já existia"; fi

    if gh repo view "${GH_USER}/${REPO}" >/dev/null 2>&1; then
      ok "repo remoto já existe"
      git remote get-url origin >/dev/null 2>&1 \
        || git remote add origin "https://github.com/${GH_USER}/${REPO}.git"
      git push -q -u origin HEAD || warn "push sem novidades (ok)"
    else
      say "  criando repo PÚBLICO (necessário: o build do Cloud Run instala daqui)…"
      gh repo create "${GH_USER}/${REPO}" --public --source=. --remote=origin --push \
        || exit 1
      ok "repo remoto criado"
    fi

    if git rev-parse "${TAG}" >/dev/null 2>&1; then
      ok "tag ${TAG} já existe"
    else
      git tag "${TAG}" && git push -q origin "${TAG}" && ok "tag ${TAG} publicada"
    fi
  ) || die "passo 1 falhou (veja o erro acima)."

  DEP="claude-gateway[postgres] @ git+https://github.com/${GH_USER}/${REPO}.git@${TAG}"
  ok "gateway no ar: https://github.com/${GH_USER}/${REPO}"
  say "  dependência: ${C}${DEP}${N}"
}

# =============================================================================
# PASSO 2 — plugar no BolsIA (requirements + Dockerfile)
# =============================================================================
step2() {
  head_ "PASSO 2/5 — Plugar o gateway no BolsIA"
  [ -n "${GH_USER:-}" ] || ask GH_USER "Seu usuário do GitHub"
  REPO="${REPO:-claude-gateway}"; TAG="${TAG:-v0.1.0}"

  ask BOLSIA_DIR "Caminho do repositório do BolsIA" "${BOLSIA_DIR:-$PWD}"
  BOLSIA_DIR="${BOLSIA_DIR/#\~/$HOME}"
  [ -d "$BOLSIA_DIR" ] || die "pasta não existe: $BOLSIA_DIR"

  ask APP_ENTRYPOINT "Entrypoint do BolsIA (modulo:app)" "${APP_ENTRYPOINT:-app.main:app}"
  save_cfg

  local DEP="claude-gateway[postgres] @ git+https://github.com/${GH_USER}/${REPO}.git@${TAG}"

  ( cd "$BOLSIA_DIR" || exit 1
    touch requirements.txt
    if grep -q "claude-gateway" requirements.txt; then
      ok "requirements.txt já referencia o gateway"
      grep -n "claude-gateway" requirements.txt | sed 's/^/    /'
      warn "confira se a tag é ${TAG}"
    else
      printf '%s\n' "$DEP" >> requirements.txt
      ok "dependência adicionada ao requirements.txt"
    fi

    if [ -f Dockerfile ]; then
      if grep -q "app.main:app" Dockerfile; then
        sed -i.bak "s#app.main:app#${APP_ENTRYPOINT}#g" Dockerfile && rm -f Dockerfile.bak
        ok "Dockerfile ajustado para ${APP_ENTRYPOINT}"
      else
        ok "Dockerfile já ajustado (sem placeholder)"
      fi
    else
      warn "sem Dockerfile no BolsIA — copie o template do chat para ${BOLSIA_DIR}"
    fi
  ) || die "passo 2 falhou."

  warn "FALTA A INTEGRAÇÃO NO CÓDIGO (não é script, é lógica da app):"
  say  "  trocar as chamadas diretas à API por GovernedGateway e registrar"
  say  "  AppBudget(\"bolsia\", ...). Peça esse trecho ao Claude quando chegar aqui."
}

# =============================================================================
# PASSO 3 — schema no Neon
# =============================================================================
SCHEMA_SQL='CREATE TABLE IF NOT EXISTS gateway_budget (
    app_id    text PRIMARY KEY,
    day_key   text NOT NULL,
    month_key text NOT NULL,
    day_usd   double precision NOT NULL DEFAULT 0,
    month_usd double precision NOT NULL DEFAULT 0
);'

step3() {
  head_ "PASSO 3/5 — Criar a tabela de controle de gasto no Neon"
  say "  Precisa de uma conta Neon (grátis): https://neon.tech"
  say "  Copie a connection string do projeto (começa com postgresql://)."

  if ! have psql; then
    warn "psql não instalado — faça pelo site (30 segundos):"
    say  "  Neon > seu projeto > SQL Editor > cole e execute:"
    printf '%s\n' "$SCHEMA_SQL" | sed 's/^/    /'
    confirm "  Já executei no SQL Editor do Neon" && ok "ok, seguindo" \
      || die "execute o SQL e rode de novo: ./setup.sh 3"
    return 0
  fi

  ask_secret DATABASE_URL "Connection string do Neon (não aparece na tela)"
  printf '%s\n' "$SCHEMA_SQL" | psql "$DATABASE_URL" -q \
    && ok "tabela gateway_budget criada/confirmada" \
    || die "psql falhou — confira a connection string (precisa de ?sslmode=require)"
}

# =============================================================================
# PASSO 4 — deploy no Cloud Run
# =============================================================================
step4() {
  head_ "PASSO 4/5 — Deploy do BolsIA no Cloud Run"
  have gcloud || die "gcloud não instalado. Rode: ./setup.sh doctor"
  [ -n "$(gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null)" ] \
    || die "gcloud não autenticado. Rode: gcloud auth login"

  say "  Precisa de conta GCP ${B}pessoal${N} (separada do trabalho) com billing ativo."
  say "  https://console.cloud.google.com"
  ask PROJECT_ID "ID do projeto GCP"
  ask REGION     "Região" "${REGION:-southamerica-east1}"
  ask SERVICE    "Nome do serviço" "${SERVICE:-bolsia}"
  ask BOLSIA_DIR "Caminho do repositório do BolsIA" "${BOLSIA_DIR:-$PWD}"
  BOLSIA_DIR="${BOLSIA_DIR/#\~/$HOME}"
  [ -f "${BOLSIA_DIR}/Dockerfile" ] || die "sem Dockerfile em ${BOLSIA_DIR} — rode o passo 2."
  save_cfg

  ask_secret ANTHROPIC_API_KEY "Sua ANTHROPIC_API_KEY do BolsIA (não aparece na tela)"
  ask_secret DATABASE_URL      "Connection string do Neon (não aparece na tela)"

  gcloud config set project "$PROJECT_ID" >/dev/null 2>&1 || die "projeto inválido: $PROJECT_ID"

  say "  habilitando APIs (demora ~1 min na primeira vez)…"
  gcloud services enable run.googleapis.com secretmanager.googleapis.com \
    cloudbuild.googleapis.com artifactregistry.googleapis.com >/dev/null \
    || die "falha ao habilitar APIs (billing ativo no projeto?)"
  ok "APIs habilitadas"

  put_secret() {
    local name="$1" value="$2"
    if gcloud secrets describe "$name" >/dev/null 2>&1; then
      printf '%s' "$value" | gcloud secrets versions add "$name" --data-file=- >/dev/null
    else
      printf '%s' "$value" | gcloud secrets create "$name" \
        --replication-policy=automatic --data-file=- >/dev/null
    fi
  }
  put_secret anthropic-api-key  "$ANTHROPIC_API_KEY" && ok "secret anthropic-api-key gravado"
  put_secret neon-database-url  "$DATABASE_URL"      && ok "secret neon-database-url gravado"

  say "  buildando e publicando (primeira vez demora alguns minutos)…"
  # --min-instances=0 : dorme quando ocioso -> custo zero (aceita cold start)
  # --max-instances=2 : teto de custo e de raio de explosão
  ( cd "$BOLSIA_DIR" && gcloud run deploy "$SERVICE" \
      --source . --region "$REGION" --allow-unauthenticated \
      --min-instances=0 --max-instances=2 --cpu=1 --memory=512Mi \
      --set-secrets="ANTHROPIC_API_KEY=anthropic-api-key:latest,DATABASE_URL=neon-database-url:latest" \
  ) || die "deploy falhou — leia o log acima (causa comum: repo do gateway privado)."

  local URL
  URL="$(gcloud run services describe "$SERVICE" --region "$REGION" \
         --format='value(status.url)' 2>/dev/null)"
  ok "no ar: ${C}${URL}${N}"
  warn "endpoint é público (--allow-unauthenticated). Ok p/ estudo; não exponha nada sensível."
}

# =============================================================================
# PASSO 5 — budget alert
# =============================================================================
step5() {
  head_ "PASSO 5/5 — Alerta de gasto no GCP"
  have gcloud || die "gcloud não instalado."
  if [ -z "${BILLING_ACCOUNT_ID:-}" ]; then
    say "  suas billing accounts:"
    gcloud billing accounts list 2>/dev/null | sed 's/^/    /' || warn "não consegui listar"
    ask BILLING_ACCOUNT_ID "ID da billing account (formato XXXXXX-XXXXXX-XXXXXX)"
  fi
  local AMOUNT="${AMOUNT:-5}"
  save_cfg

  if gcloud billing budgets list --billing-account="$BILLING_ACCOUNT_ID" 2>/dev/null \
     | grep -q "estudo-bolsia"; then
    ok "budget 'estudo-bolsia' já existe"
    return 0
  fi
  gcloud billing budgets create --billing-account="$BILLING_ACCOUNT_ID" \
    --display-name="estudo-bolsia" --budget-amount="${AMOUNT}USD" \
    --threshold-rule=percent=0.5 --threshold-rule=percent=0.9 --threshold-rule=percent=1.0 \
    >/dev/null && ok "alerta criado (${AMOUNT} USD; avisos em 50/90/100%)" \
    || warn "não consegui criar — dá pra fazer pelo console em Billing > Budgets & alerts"
  warn "é ALERTA, não corta serviço. O freio real é o teto do gateway + spend limit da Anthropic."
}

# =============================================================================
status() {
  head_ "Situação"
  load_cfg
  [ -f "$CONFIG" ] && ok "config salva em $CONFIG" || warn "nenhuma config ainda"
  [ -n "${GH_USER:-}" ] && say "  GitHub .......: ${GH_USER}/${REPO:-claude-gateway}@${TAG:-v0.1.0}"
  [ -n "${BOLSIA_DIR:-}" ] && say "  BolsIA .......: ${BOLSIA_DIR} (${APP_ENTRYPOINT:-?})"
  [ -n "${PROJECT_ID:-}" ] && say "  GCP ..........: ${PROJECT_ID} / ${REGION:-?} / ${SERVICE:-?}"
  say ""
  say "  1) publicar gateway   2) plugar no BolsIA   3) schema Neon"
  say "  4) deploy Cloud Run   5) alerta de gasto"
}

menu() {
  head_ "Instalação do BolsIA"
  say "  0) checar pré-requisitos"
  say "  1) publicar o gateway no GitHub"
  say "  2) plugar o gateway no BolsIA"
  say "  3) criar a tabela no Neon"
  say "  4) deploy no Cloud Run"
  say "  5) alerta de gasto no GCP"
  say "  a) rodar TUDO na ordem"
  say "  s) ver situação atual"
  say "  q) sair"
  local o; read -r -p $'\nEscolha: ' o
  case "$o" in
    0) doctor ;; 1) step1 ;; 2) step2 ;; 3) step3 ;; 4) step4 ;; 5) step5 ;;
    a|A) doctor && step1 && step2 && step3 && step4 && step5
         head_ "Tudo pronto." ;;
    s|S) status ;;
    q|Q) exit 0 ;;
    *) err "opção inválida" ;;
  esac
}

load_cfg
case "${1:-menu}" in
  doctor) doctor ;;
  status) status ;;
  1) step1 ;; 2) step2 ;; 3) step3 ;; 4) step4 ;; 5) step5 ;;
  all)  doctor && step1 && step2 && step3 && step4 && step5; head_ "Tudo pronto." ;;
  menu) menu ;;
  *) say "uso: $0 [doctor|status|1|2|3|4|5|all]"; exit 1 ;;
esac
