#!/usr/bin/env bash
# Incrementa o BUILD NUMBER (CURRENT_PROJECT_VERSION) do app iOS - cada upload ao
# TestFlight/App Store exige um build number UNICO e maior que o anterior.
# A fonte versionada e resources/ios/versao.env (web/ios/ e gitignored); este
# script incrementa la e aplica no projeto via ios-aplicar-projeto.sh.
# A MARKETING_VERSION (versao publica) se edita a mao em versao.env, na mesma
# cadencia do package.json.
#
#   bash scripts/ios-bump-build.sh          # +1
#   bash scripts/ios-bump-build.sh 42       # define exatamente 42
#   (opcoes de teste: --ios-dir DIR  --versao-file FILE  --sem-verificar)
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
IOS_DIR="$REPO/web/ios"
VERSAO_FILE="$REPO/resources/ios/versao.env"
EXTRA=()
N=""
die(){ echo "[X] $*" >&2; exit 1; }
while [ $# -gt 0 ]; do
  case "$1" in
    --ios-dir)      [ -n "${2:-}" ] || die "--ios-dir exige um diretorio"; IOS_DIR="$2"; shift 2;;
    --versao-file)  [ -n "${2:-}" ] || die "--versao-file exige um arquivo"; VERSAO_FILE="$2"; shift 2;;
    --sem-verificar) EXTRA+=("--sem-verificar"); shift;;
    [0-9]*)         N="$1"; shift;;
    *) die "argumento desconhecido: $1";;
  esac
done
PBX="$IOS_DIR/App/App.xcodeproj/project.pbxproj"

[ -f "$PBX" ] || die "Nao achei $PBX. Rode antes: bash scripts/instalar-iphone.sh"
grep -q 'isa = PBXNativeTarget;' "$PBX" \
  || die "projeto iOS corrompido (sem target nativo - mesmo sintoma de 2026-10-22). Nada foi alterado. Rode: bash scripts/instalar-iphone.sh --recriar-ios"
grep -q 'CURRENT_PROJECT_VERSION = ' "$PBX" \
  || die "o projeto esta sem a chave CURRENT_PROJECT_VERSION. Rode: bash scripts/ios-aplicar-projeto.sh (nao vou calcular o build a partir de zero)."
[ -f "$VERSAO_FILE" ] || die "Nao achei $VERSAO_FILE"

CUR="$(grep -E '^CURRENT_PROJECT_VERSION=' "$VERSAO_FILE" | tail -1 | cut -d= -f2- | tr -d ' \r' || true)"
printf '%s' "$CUR" | grep -Eq '^[1-9][0-9]*$' || die "CURRENT_PROJECT_VERSION invalido em $VERSAO_FILE: '$CUR'"
PBXMAX="$(grep -oE 'CURRENT_PROJECT_VERSION = [0-9]+' "$PBX" | grep -oE '[0-9]+' | sort -n | tail -1)"
BASE="$CUR"
if [ "$PBXMAX" -ne "$CUR" ]; then
  echo "[!] versao.env ($CUR) difere do projeto ($PBXMAX); usando o maior como base."
  [ "$PBXMAX" -gt "$CUR" ] && BASE="$PBXMAX"
fi
if [ -n "$N" ]; then NEW="$N"; else NEW="$((BASE + 1))"; fi
[ "$NEW" -gt "$BASE" ] || die "novo build ($NEW) precisa ser > atual ($BASE)."

TMP="$VERSAO_FILE.bump.$$"
trap 'rm -f "$TMP"' EXIT
sed "s/^CURRENT_PROJECT_VERSION=.*/CURRENT_PROJECT_VERSION=$NEW/" "$VERSAO_FILE" > "$TMP"
bash "$REPO/scripts/ios-aplicar-projeto.sh" --ios-dir "$IOS_DIR" --versao-file "$TMP" ${EXTRA[@]+"${EXTRA[@]}"} \
  || die "falha ao aplicar o build $NEW no projeto; versao.env NAO foi alterado."
mv "$TMP" "$VERSAO_FILE"

MKT="$(grep -E '^MARKETING_VERSION=' "$VERSAO_FILE" | tail -1 | cut -d= -f2- | tr -d ' \r')"
echo "[OK] build: $BASE -> $NEW   (versao publica MARKETING_VERSION=$MKT)"
echo "    Commite resources/ios/versao.env junto do upload. A versao publica se muda editando"
echo "    MARKETING_VERSION nesse arquivo (mesma cadencia do package.json)."
echo "    Agora no Xcode: Product > Archive > Distribute App > App Store Connect."
