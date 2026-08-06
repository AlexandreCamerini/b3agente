#!/usr/bin/env bash
# bump.sh — avança o BUILD_ID da entrega (web/src/version.js).
#
# O BUILD_ID é o carimbo que prova QUAL ENTREGA está no ar: ele viaja de
# version.js → web/dist → server/web_dist → bundle do iPhone, e o entregar.sh
# aborta se algum elo divergir. O SERVER_BUILD_ID (/api/health) é derivado
# dele automaticamente, então este é o ÚNICO carimbo que se edita à mão.
#
#   bash scripts/bump.sh                    # próximo do dia (hoje-01, ou +1 se já houver hoje)
#   bash scripts/bump.sh F10-20260806-07    # define exatamente (rollback, correção)
#
# Por que continua sendo um comando SEU e não um passo automático do
# entregar.sh: o carimbo marca ENTREGA, não build. Você builda dez vezes
# testando e entrega uma — gerar por timestamp faria cada build local virar
# "versão" e o número perderia o sentido de marco.
#
# Esquecer o bump não é inofensivo: o dist novo sai com o carimbo do dia
# anterior, igual ao do bundle iOS antigo, e "mesmo carimbo com chunks
# diferentes" é a assinatura de bundle amputado que o test_ios_assets.mjs
# pega (aconteceu em 2026-08-06).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
V="$REPO/web/src/version.js"
[ -f "$V" ] || { echo "[X] não achei $V"; exit 1; }

CUR="$(sed -n 's/.*BUILD_ID = "\([^"]*\)".*/\1/p' "$V")"
[ -n "$CUR" ] || { echo "[X] $V sem BUILD_ID — o carimbo é obrigatório"; exit 1; }

# O padrão que o resto da cadeia reconhece (build_no_bundle no entregar.sh):
# prefixo de fase, data de 8 dígitos, sequencial de 1 a 3.
PADRAO='^[A-Za-z][0-9A-Za-z]{0,5}-[0-9]{8}-[0-9]{1,3}$'
HOJE="$(date +%Y%m%d)"

if [ -n "${1:-}" ]; then
  NEW="$1"
  # Formato conferido AQUI porque carimbo torto só apareceria lá na frente,
  # disfarçado de "dist contém nada" na verificação do entregar.sh.
  echo "$NEW" | grep -qE "$PADRAO" \
    || { echo "[X] '$NEW' não é um carimbo válido (padrão: F10-AAAAMMDD-NN)"; exit 1; }
else
  echo "$CUR" | grep -qE "$PADRAO" \
    || { echo "[X] carimbo atual '$CUR' fora do padrão — passe o novo à mão: bash scripts/bump.sh F10-$HOJE-01"; exit 1; }
  PREFIXO="${CUR%%-*}"                       # preserva a fase (F10, F11…)
  DIA="$(echo "$CUR" | cut -d- -f2)"
  SEQ="$(echo "$CUR" | cut -d- -f3)"
  if [ "$DIA" = "$HOJE" ]; then
    # 10# força base decimal: sem isso, "08" e "09" viram octal inválido e o
    # bump quebraria só na oitava entrega do dia.
    NEW="$PREFIXO-$HOJE-$(printf '%02d' "$((10#$SEQ + 1))")"
  else
    NEW="$PREFIXO-$HOJE-01"                  # dia novo recomeça a contagem
  fi
fi

[ "$NEW" != "$CUR" ] || { echo "[X] o carimbo já é $CUR"; exit 1; }

sed -i '' "s/BUILD_ID = \"[^\"]*\"/BUILD_ID = \"$NEW\"/" "$V" 2>/dev/null \
  || sed -i "s/BUILD_ID = \"[^\"]*\"/BUILD_ID = \"$NEW\"/" "$V"

CONFIRMA="$(sed -n 's/.*BUILD_ID = "\([^"]*\)".*/\1/p' "$V")"
[ "$CONFIRMA" = "$NEW" ] || { echo "[X] a escrita não pegou ($V ainda em '$CONFIRMA')"; exit 1; }

echo "[OK] BUILD_ID: $CUR -> $NEW"
echo "    Próximo: bash entregar.sh \"mensagem da entrega\""
echo "    (ele sincroniza o SERVER_BUILD_ID e confere o carimbo em cada elo)"
