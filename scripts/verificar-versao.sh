#!/usr/bin/env bash
# verificar-versao.sh — confere se git local, backend Railway e bundle iOS
# estão na mesma versão.
#
# GARANTIA: somente leitura. Nenhum comando altera código, deploy ou build.
# O único efeito colateral é `git fetch` (atualiza refs remotos locais);
# desligue com --no-fetch.
#
# Uso:
#   ./scripts/verificar-versao.sh                 # verifica tudo
#   ./scripts/verificar-versao.sh --no-fetch      # não toca na rede do git
#   ./scripts/verificar-versao.sh --only git,ios  # frentes específicas
#   ./scripts/verificar-versao.sh --json          # saída para agente/CI
#
# Exit codes:
#   0  todas as frentes verificadas e sincronizadas
#   1  divergência confirmada (git sujo, deploy defasado, cap sync pendente)
#   2  indeterminado (faltou instrumentação/ferramenta para concluir)

set -uo pipefail

VERSION="2.2"   # bump a cada mudança de comportamento. A saída imprime isto:
                # rodar a versão errada por engano é a falha mais provável aqui.

API_URL="${BOLSIA_API_URL:-https://b3agente-production.up.railway.app}"
BRANCH="${BOLSIA_BRANCH:-main}"

DO_FETCH=1
JSON=0
FRENTES="git,railway,ios"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-fetch) DO_FETCH=0; shift ;;
    --json)     JSON=1; shift ;;
    --only)     FRENTES="${2:?--only exige lista: git,railway,ios}"; shift 2 ;;
    --api)      API_URL="${2:?--api exige URL}"; shift 2 ;;
    -h|--help)  sed -n '2,20p' "$0"; exit 0 ;;
    --version)  echo "verificar-versao.sh v$VERSION"; exit 0 ;;
    *) echo "argumento desconhecido: $1" >&2; exit 2 ;;
  esac
done

# ---------- saída ----------
if [[ -t 1 && $JSON -eq 0 ]]; then
  C_OK=$'\033[32m'; C_WARN=$'\033[33m'; C_ERR=$'\033[31m'; C_DIM=$'\033[2m'; C_N=$'\033[0m'
else
  C_OK=""; C_WARN=""; C_ERR=""; C_DIM=""; C_N=""
fi

RESULTS=()   # "frente|status|detalhe"
HAS_DIVERGE=0
HAS_INDET=0

reg() { # frente status detalhe
  RESULTS+=("$1|$2|$3")
  case "$2" in
    DIVERGE) HAS_DIVERGE=1 ;;
    INDET)   HAS_INDET=1 ;;
  esac
  [[ $JSON -eq 1 ]] && return 0
  local cor="$C_OK" tag="OK"
  case "$2" in
    DIVERGE) cor="$C_ERR";  tag="DIVERGE" ;;
    INDET)   cor="$C_WARN"; tag="INDET" ;;
  esac
  printf '  %s%-8s%s %s\n' "$cor" "$tag" "$C_N" "$3"
}

info() { [[ $JSON -eq 0 ]] && printf '%s  %s%s\n' "$C_DIM" "$1" "$C_N"; return 0; }
head_() { [[ $JSON -eq 0 ]] && printf '\n%s\n' "$1"; return 0; }

quer() { [[ ",$FRENTES," == *",$1,"* ]]; }

# mtime em epoch. BSD (macOS) usa -f %m; GNU (Linux/CI) usa -c %Y.
# Sanitiza para dígitos: saída não-numérica quebraria o [[ -gt ]] com set -u.
mtime() {
  local out
  out="$(stat -f %m "$1" 2>/dev/null)" || out="$(stat -c %Y "$1" 2>/dev/null)" || out=""
  out="$(printf '%s' "$out" | tr -cd '0-9')"
  printf '%s' "${out:-0}"
}

# ---------- pré-requisitos ----------
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "erro: rode dentro do repositório b3-agente" >&2; exit 2; }
cd "$REPO_ROOT"

[[ $JSON -eq 0 ]] && printf '%sverificar-versao.sh v%s%s\n' "$C_DIM" "$VERSION" "$C_N"

HEAD_SHA=""; HEAD_SHORT=""

# ---------- frente 1: git ----------
if quer git; then
  head_ "git"
  [[ $DO_FETCH -eq 1 ]] && git fetch origin --quiet 2>/dev/null

  HEAD_SHA="$(git rev-parse HEAD)"
  HEAD_SHORT="${HEAD_SHA:0:7}"
  REMOTE_SHA="$(git rev-parse --verify -q "origin/$BRANCH" 2>/dev/null || echo "")"
  SUJO="$(git status --porcelain | wc -l | tr -d ' ')"
  CUR_BRANCH="$(git rev-parse --abbrev-ref HEAD)"

  info "HEAD ....... $HEAD_SHORT ($CUR_BRANCH)"
  info "origin ..... ${REMOTE_SHA:0:7}"

  if [[ -z "$REMOTE_SHA" ]]; then
    reg git INDET "origin/$BRANCH não encontrado (fetch falhou ou branch não existe)"
  elif [[ "$HEAD_SHA" != "$REMOTE_SHA" ]]; then
    AHEAD="$(git rev-list --count "origin/$BRANCH..HEAD" 2>/dev/null || echo '?')"
    BEHIND="$(git rev-list --count "HEAD..origin/$BRANCH" 2>/dev/null || echo '?')"
    reg git DIVERGE "HEAD != origin/$BRANCH (ahead $AHEAD / behind $BEHIND)"
  elif [[ "$SUJO" -gt 0 ]]; then
    reg git DIVERGE "working tree com $SUJO arquivo(s) não commitado(s)"
  else
    reg git OK "HEAD == origin/$BRANCH == $HEAD_SHORT, tree limpo"
  fi

  # Worktrees (Claude Code cria em .claude/worktrees/) têm HEAD próprio:
  # `git status` no repo principal NÃO enxerga trabalho pendente neles.
  WT="$(git worktree list --porcelain 2>/dev/null | grep -c '^worktree ' || echo 1)"
  if [[ "${WT:-1}" -gt 1 ]]; then
    info "$(( WT - 1 )) worktree(s) ativo(s) — HEAD próprio, invisível ao status acima:"
    git worktree list 2>/dev/null | tail -n +2 | sed 's/^/           /'
    reg git INDET "$(( WT - 1 )) worktree(s) com trabalho possivelmente não mergeado em $BRANCH"
  fi
fi

# ---------- frente 2: railway ----------
if quer railway; then
  head_ "railway (backend)"

  if ! command -v curl >/dev/null 2>&1; then
    reg railway INDET "curl ausente"
  else
    HTTP="$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "$API_URL/health" 2>/dev/null)"
    info "GET $API_URL/health -> ${HTTP:-timeout}"

    if [[ "$HTTP" == "200" ]]; then
      BODY="$(curl -s --max-time 15 "$API_URL/health")"
      PROD_SHA="$(printf '%s' "$BODY" | python3 -c \
        'import sys,json;d=json.load(sys.stdin);print(d.get("commit") or "")' 2>/dev/null)"
      if [[ -z "$PROD_SHA" || "$PROD_SHA" == "unknown" ]]; then
        reg railway INDET "/health responde mas não expõe commit — ver §instrumentação"
      elif [[ -n "$HEAD_SHA" && "${PROD_SHA:0:7}" == "${HEAD_SHA:0:7}" ]]; then
        reg railway OK "produção em ${PROD_SHA:0:7} == HEAD"
      else
        reg railway DIVERGE "produção em ${PROD_SHA:0:7}, HEAD em ${HEAD_SHORT:-?}"
      fi

    elif [[ "$HTTP" == "404" ]]; then
      # backend vivo (FastAPI respondeu), mas sem rota de versão.
      # Fallback: comparar rotas do openapi.json vs. decoradores no código.
      ROTAS_PROD="$(curl -s --max-time 20 "$API_URL/openapi.json" 2>/dev/null | python3 -c \
        'import sys,json
try: print("\n".join(sorted(json.load(sys.stdin).get("paths",{}))))
except Exception: pass' 2>/dev/null)"

      if [[ -z "$ROTAS_PROD" ]]; then
        reg railway INDET "sem /health e sem /openapi.json — versão não verificável"
      else
        # Varre SÓ código de aplicação. Sem os excludes, .venv/site-packages
        # entrega os exemplos do tutorial do FastAPI (/items/, /uploadfile/,
        # /users/me...) como se fossem rotas do projeto.
        ROTAS_CODE="$(grep -rhoE '@(app|router)\.(get|post|put|patch|delete)\("([^"]+)"' \
          --include='*.py' \
          --exclude-dir=.venv --exclude-dir=venv --exclude-dir=env \
          --exclude-dir=site-packages --exclude-dir=node_modules \
          --exclude-dir=__pycache__ --exclude-dir=.git \
          --exclude-dir=.claude \
          --exclude-dir=tests --exclude-dir=test --exclude-dir=docs \
          --exclude-dir=migrations --exclude-dir=alembic \
          . 2>/dev/null | sed -E 's/.*\("([^"]+)".*/\1/' | sort -u)"

        # NÃO tentamos mais adivinhar o prefixo. Ele pode vir de
        # include_router(prefix=), APIRouter(prefix=) no construtor, ou da
        # composição dos dois — regex de linha não cobre isso, e cada
        # tentativa gerou falso positivo. Match por sufixo é indiferente ao
        # prefixo: /chain/{ticker} casa com /api/options/chain/{ticker}.
        # Custo: perde sensibilidade (colisão de sufixo). Aceito — o objetivo
        # aqui é só detectar ausência grosseira, nunca provar versão.
        N_CODE="$(printf '%s\n' "$ROTAS_CODE" | grep -c . || true)"
        N_PROD="$(printf '%s\n' "$ROTAS_PROD" | grep -c . || true)"
        info "rotas em produção: $N_PROD | no código (app only): $N_CODE"

        AUSENTES=""
        SUFIXADAS=0
        while IFS= read -r r; do
          [[ -z "$r" ]] && continue
          if printf '%s\n' "$ROTAS_PROD" | grep -qxF "$r"; then
            continue                                   # match exato
          elif printf '%s\n' "$ROTAS_PROD" | grep -qF -- "$r"; then
            SUFIXADAS=$((SUFIXADAS + 1))               # existe sob prefixo
          else
            AUSENTES+="$r"$'\n'
          fi
        done <<< "$ROTAS_CODE"

        N_AUS="$(printf '%s' "$AUSENTES" | grep -c . || true)"
        [[ $SUFIXADAS -gt 0 ]] && info "$SUFIXADAS rota(s) casaram sob prefixo de router"

        if [[ "${N_AUS:-0}" -eq 0 ]]; then
          reg railway INDET "as $N_CODE rotas do código existem em produção — mas rota não é commit; sem veredito"
        elif [[ "${N_AUS:-0}" -ge $(( N_CODE / 2 )) ]]; then
          reg railway INDET "$N_AUS de $N_CODE ausentes — proporção alta demais, suspeite do extrator antes do deploy"
          [[ $JSON -eq 0 ]] && printf '%s' "$AUSENTES" | sed 's/^/           ? /'
        else
          reg railway DIVERGE "$N_AUS rota(s) sem correspondência em produção — investigar"
          [[ $JSON -eq 0 ]] && printf '%s' "$AUSENTES" | sed 's/^/           ausente: /'
        fi
      fi

    elif [[ -z "$HTTP" || "$HTTP" == "000" ]]; then
      reg railway DIVERGE "backend não respondeu ($API_URL) — fora do ar ou URL errada"
    else
      reg railway INDET "/health retornou HTTP $HTTP"
    fi
  fi

  # railway CLI é bônus: confirma estado do último deployment
  if command -v railway >/dev/null 2>&1; then
    ST="$(railway status 2>&1)"
    if printf '%s' "$ST" | grep -qi 'no linked project'; then
      info "railway CLI presente mas não linkada (railway link) — estado do build não verificado"
    else
      info "railway status: $(printf '%s' "$ST" | head -n 3 | tr '\n' ' ')"
    fi
  fi
fi

# ---------- frente 3: ios ----------
if quer ios; then
  head_ "ios (bundle nativo)"

  DIST="web/dist"
  PUBLIC="$(find web/ios -type d -path '*/App/public' -not -path '*/node_modules/*' 2>/dev/null | head -n 1)"

  if [[ ! -d "$DIST" ]]; then
    reg ios INDET "web/dist ausente — nunca buildado nesta máquina (rode instalar-iphone.sh)"
  elif [[ -z "$PUBLIC" ]]; then
    reg ios INDET "projeto nativo não encontrado (web/ios git-ignored, ausente ou não gerado)"
  else
    info "dist ....... $DIST"
    info "nativo ..... $PUBLIC"

    DIFF="$(diff -rq "$DIST" "$PUBLIC" 2>/dev/null | grep -v -E '\.DS_Store|cordova|capacitor\.config' | head -n 20)"
    if [[ -n "$DIFF" ]]; then
      reg ios DIVERGE "bundle nativo != dist — cap sync pendente"
      [[ $JSON -eq 0 ]] && printf '%s\n' "$DIFF" | sed 's/^/           /'
    else
      # dist bate com o nativo, mas o dist é do HEAD atual?
      SRC_EPOCH="$(git log -1 --format=%ct -- web/src/ 2>/dev/null | tr -cd '0-9')"
      DIST_EPOCH="$(mtime "$DIST/index.html")"
      SRC_EPOCH="${SRC_EPOCH:-0}"; DIST_EPOCH="${DIST_EPOCH:-0}"
      if [[ "$SRC_EPOCH" -gt "$DIST_EPOCH" ]]; then
        reg ios DIVERGE "web/src/ commitado depois do último build do dist — rode instalar-iphone.sh"
      elif [[ "$DIST_EPOCH" -eq 0 ]]; then
        reg ios INDET "não foi possível datar o dist"
      else
        reg ios OK "dist == bundle nativo, e mais recente que o último commit em web/src/"
      fi
    fi
  fi
  info "obs: isto compara a MÁQUINA. O binário no iPhone/TestFlight só é"
  info "     garantido por build+deploy posterior a esta checagem."
fi

# ---------- resumo ----------
# DIVERGE (1) tem precedência sobre INDET (2): divergência confirmada é o
# achado mais forte e deve dominar o exit code.
if   [[ $HAS_DIVERGE -eq 1 ]]; then WORST=1
elif [[ $HAS_INDET   -eq 1 ]]; then WORST=2
else WORST=0; fi

if [[ $JSON -eq 1 ]]; then
  printf '{"head":"%s","frentes":[' "${HEAD_SHORT:-}"
  for i in "${!RESULTS[@]}"; do
    IFS='|' read -r f s d <<< "${RESULTS[$i]}"
    [[ $i -gt 0 ]] && printf ','
    printf '{"frente":"%s","status":"%s","detalhe":"%s"}' "$f" "$s" "${d//\"/\\\"}"
  done
  printf '],"exit":%d}\n' "$WORST"
else
  head_ "resumo"
  for r in "${RESULTS[@]}"; do
    IFS='|' read -r f s d <<< "$r"
    printf '  %-9s %s\n' "$f" "$s"
  done
  case $WORST in
    0) printf '\n%sTudo sincronizado em %s.%s\n' "$C_OK" "${HEAD_SHORT:-?}" "$C_N" ;;
    1) printf '\n%sDivergência confirmada — ver acima.%s\n' "$C_ERR" "$C_N" ;;
    2) printf '\n%sIndeterminado: falta instrumentação para concluir.%s\n' "$C_WARN" "$C_N"
       printf '%s  Adicione /health expondo RAILWAY_GIT_COMMIT_SHA e rode de novo.%s\n' "$C_DIM" "$C_N" ;;
  esac
fi

exit $WORST
