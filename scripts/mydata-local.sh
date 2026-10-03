#!/usr/bin/env bash
# Boris+ - backend local com o provedor de opcoes de producao (mydata), SEM expor o token.
#
#   bash scripts/mydata-local.sh --salvar                  # pede o token (digitacao oculta), valida no hub e guarda no Keychain
#   bash scripts/mydata-local.sh --salvar-railway [SERVICO]# le SO a variavel MYDATA_TOKEN via CLI do Railway e guarda no Keychain
#   bash scripts/mydata-local.sh --validar                 # testa o token guardado no hub (so imprime o resultado)
#   bash scripts/mydata-local.sh                           # valida e sobe o backend (scripts/run.sh) com mydata
#   bash scripts/mydata-local.sh --remover                 # apaga o token do Keychain
#   bash scripts/mydata-local.sh --mercado-aberto          # igual ao padrao, forcando o pregao ABERTO (so dev; ver abaixo)
#
# Regras (nao mudar sem motivo):
#  - A UNICA fonte do token e o Keychain do macOS (item abaixo). Variavel de ambiente da shell
#    e ignorada de proposito: foi assim que uma chave da Anthropic foi parar em MYDATA_TOKEN.
#  - O valor nunca e impresso, nunca vai para argv de comando nem para arquivo. Para o hub ele
#    viaja por stdin do curl (-H @-); para o Keychain, por stdin do `security -i`.
#  - Recusa qualquer valor que comece com "sk-ant-" (chave da Anthropic) ANTES de ir a rede.
#  - Nao usar `set -x` / `bash -x` neste script: vazaria o token no trace.
#  - --mercado-aberto liga B3_DEV_MERCADO_ABERTO=1 (pregao.dev_mercado_aberto_forcado): so forca
#    in_market_hours(). Cotacao/candle/opcoes continuam da fonte real (mydata e COTAHIST, publicado
#    apos o fechamento: pode estar parado). NAO destrava o agente autonomo (exige tambem B3_AGENT_KILL=0).
#    So para dev local/staging; nunca em producao (ver docstring em server/app/pregao.py).
#  - Nao muda o default de B3_OPTIONS_PROVIDER no codigo (ADR-020): mydata e so env desta sessao.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
KC_SERVICE="boris-mydata-token"
HUB_URL="${MYDATA_URL:-https://mydata.semente.dev}"
PROVA_PATH="/v1/cotacoes/PETR4?limite=1"

[[ "$(uname -s)" == "Darwin" ]] || { echo "ERRO: usa o Keychain do macOS (security); sistema nao suportado."; exit 1; }

# Mesma regra do cliente Python (mydata_client.base_url): so https, ou http em localhost.
case "$HUB_URL" in
  https://*|http://localhost*|http://127.0.0.1*) ;;
  *) echo "ERRO: MYDATA_URL precisa ser https:// (ou http://localhost). A chave so trafega por TLS."; exit 1;;
esac

kc_ler()   { security find-generic-password -a "$USER" -s "$KC_SERVICE" -w 2>/dev/null; }
kc_apagar(){ security delete-generic-password -a "$USER" -s "$KC_SERVICE" >/dev/null 2>&1; }
kc_gravar() {  # $1 = token; vai por stdin do `security -i`, nunca por argv
  local t="$1"; t="${t//\\/\\\\}"; t="${t//\"/\\\"}"
  printf 'add-generic-password -U -a "%s" -s "%s" -w "%s"\n' "$USER" "$KC_SERVICE" "$t" | security -i >/dev/null 2>&1
}

# Formato: devolve 0 se plausivel; escreve o motivo em stderr (nunca o valor).
formato_ok() {
  local t="$1"
  [[ -n "$t" ]] || { echo "token vazio." >&2; return 1; }
  [[ "$t" != sk-ant-* ]] || { echo "BLOQUEADO: esse valor e uma chave da Anthropic, nao o token do mydata. Nao foi enviado a lugar nenhum." >&2; return 1; }
  [[ "$t" != *[[:space:]]* ]] || { echo "token com espaco/quebra de linha (colagem errada)." >&2; return 1; }
  [[ "$t" != \<* && "$t" != *\> ]] || { echo "parece o placeholder <...> colado literalmente." >&2; return 1; }
  [[ ${#t} -ge 16 ]] || { echo "token curto demais (${#t} caracteres) para ser uma chave real." >&2; return 1; }
  return 0
}

# Testa no hub. Imprime so o veredito. Retorna 0 apenas em HTTP 200.
validar_no_hub() {
  local t="$1" code
  code="$(printf 'X-API-Key: %s' "$t" | curl -s -o /dev/null -m 15 -w '%{http_code}' -H @- "${HUB_URL}${PROVA_PATH}" 2>/dev/null)"
  case "$code" in
    200) echo "hub: HTTP 200 - token valido."; return 0;;
    401|403) echo "hub: HTTP $code - token RECUSADO (chave invalida)."; return 1;;
    429) echo "hub: HTTP 429 - cota excedida (token pode ser valido; espere e tente de novo)."; return 1;;
    000|"") echo "hub: sem resposta (rede/DNS/timeout)."; return 1;;
    *) echo "hub: HTTP $code inesperado."; return 1;;
  esac
}

cmd_salvar() {
  local t
  read -rs -p "Cole o token do mydata (nao aparece na tela): " t; echo
  formato_ok "$t" || exit 1
  validar_no_hub "$t" || { echo "Nao salvei: o hub nao aceitou."; exit 1; }
  kc_gravar "$t" || { echo "ERRO ao gravar no Keychain."; exit 1; }
  unset t
  echo "Token guardado no Keychain (item '$KC_SERVICE'). Agora: bash scripts/mydata-local.sh"
}

cmd_salvar_railway() {
  command -v railway >/dev/null || { echo "ERRO: CLI do Railway nao encontrada."; exit 1; }
  local svc="${1:-}" ambiente t
  ambiente="$(railway status 2>/dev/null | sed -n 's/^Environment:[[:space:]]*//p' | head -1)"
  echo "Railway - ambiente linkado: ${ambiente:-desconhecido}${svc:+ | servico: $svc}"
  echo "Atencao: se for producao, o teste local gasta a cota REAL do app (60/min, 2.000/dia)."
  read -r -p "Ler SOMENTE a variavel MYDATA_TOKEN deste ambiente? [s/N] " r
  [[ "$r" == [sS] ]] || { echo "Cancelado."; exit 1; }
  # Le so a linha MYDATA_TOKEN; as demais variaveis passam pelo pipe e sao descartadas pelo sed.
  t="$(railway variables --kv ${svc:+--service "$svc"} 2>/dev/null | sed -n 's/^MYDATA_TOKEN=//p' | head -1)"
  formato_ok "$t" || { echo "Nao achei um MYDATA_TOKEN utilizavel nesse ambiente/servico."; exit 1; }
  validar_no_hub "$t" || { echo "Nao salvei: o hub nao aceitou."; exit 1; }
  kc_gravar "$t" || { echo "ERRO ao gravar no Keychain."; exit 1; }
  unset t
  echo "Token do Railway guardado no Keychain. Agora: bash scripts/mydata-local.sh"
}

token_guardado() {
  local t; t="$(kc_ler)" || true
  [[ -n "$t" ]] || { echo "Nenhum token no Keychain. Rode: bash scripts/mydata-local.sh --salvar  (ou --salvar-railway)" >&2; return 1; }
  formato_ok "$t" || { echo "O item do Keychain esta invalido. Refaça com --salvar." >&2; return 1; }
  printf '%s' "$t"
}

MERCADO_ABERTO=0; ARGS=()
for a in "$@"; do if [[ "$a" == "--mercado-aberto" ]]; then MERCADO_ABERTO=1; else ARGS+=("$a"); fi; done
set -- ${ARGS[@]+"${ARGS[@]}"}

case "${1:-}" in
  --salvar)          cmd_salvar;;
  --salvar-railway)  shift; cmd_salvar_railway "${1:-}";;
  --remover)         kc_apagar && echo "Removido do Keychain." || echo "Nada para remover.";;
  --validar)         t="$(token_guardado)" || exit 1; validar_no_hub "$t";;
  -h|--help)         sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//';;
  "")
    t="$(token_guardado)" || exit 1
    validar_no_hub "$t" || { echo "Backend NAO iniciado."; exit 1; }
    bash "$SCRIPT_DIR/run.sh" --stop >/dev/null 2>&1 || true
    echo "Subindo backend (8787) com B3_OPTIONS_PROVIDER=mydata..."
    if [[ "$MERCADO_ABERTO" == 1 ]]; then
      export B3_DEV_MERCADO_ABERTO=1
      echo "ATENCAO: pregao FORCADO ABERTO (B3_DEV_MERCADO_ABERTO=1). Cotacao e opcoes continuam da fonte real e podem estar paradas fora do horario. So dev local."
    fi
    # O token entra so no ambiente do processo filho; nada e impresso.
    MYDATA_TOKEN="$t" B3_OPTIONS_PROVIDER=mydata exec bash "$SCRIPT_DIR/run.sh";;
  *) echo "Opcao desconhecida: $1 (use --help)"; exit 1;;
esac
