#!/usr/bin/env bash
# ios-aplicar-projeto.sh - reaplica, de forma IDEMPOTENTE, o que o projeto iOS
# precisa para ser arquivavel depois de `npx cap add ios`:
#   time de assinatura, CODE_SIGN_ENTITLEMENTS, MARKETING_VERSION e
#   CURRENT_PROJECT_VERSION (de resources/ios/versao.env), PrivacyInfo.xcprivacy
#   no grupo App + fase Resources, e o nome Boris+ no Info.plist.
#
# POR QUE EXISTE (incidente de 2026-10-22): web/ios/ e gitignored; o template do
# Capacitor 8 nasce sem time, sem entitlements e sem PrivacyInfo, com build 1 /
# versao 1.0 - tudo isso foi refeito a mao em python. Um pbxproj sem
# PBXNativeTarget (projeto corrompido) tambem passou em silencio pelo bump.
#
# Uso:
#   bash scripts/ios-aplicar-projeto.sh [--ios-dir DIR] [--versao-file FILE] [--sem-verificar]
#
# Nunca escreve PRODUCT_BUNDLE_IDENTIFIER (bundle id e invariante do repo).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"

IOS_DIR="$REPO/web/ios"
VERSAO_FILE="$REPO/resources/ios/versao.env"
VERIFICAR=1
TEAM="LC65399YC9"
ENTITLEMENTS="App/App.entitlements"
NOME="Boris+"
PRIV_SRC="$REPO/resources/ios/PrivacyInfo.xcprivacy"
PB="/usr/libexec/PlistBuddy"

ok(){ printf "  [OK] %s\n" "$*"; }
warn(){ printf "  [!] %s\n" "$*"; }
die(){ printf "  [X] %s\n" "$*" >&2; exit 1; }

while [ $# -gt 0 ]; do
  case "$1" in
    --ios-dir)      [ -n "${2:-}" ] || die "--ios-dir exige um diretorio"; IOS_DIR="$2"; shift 2;;
    --versao-file)  [ -n "${2:-}" ] || die "--versao-file exige um arquivo"; VERSAO_FILE="$2"; shift 2;;
    --sem-verificar) VERIFICAR=0; shift;;
    -h|--help) awk 'NR>1 && /^#/{sub(/^# ?/,"");print;next}{if(NR>1)exit}' "$0"; exit 0;;
    *) die "opcao desconhecida: $1 (use --help)";;
  esac
done

PBX="$IOS_DIR/App/App.xcodeproj/project.pbxproj"
PLIST="$IOS_DIR/App/App/Info.plist"

# ---- 1) validar entrada (nada escrito ainda) ----
[ -d "$IOS_DIR" ] || die "diretorio iOS nao existe: $IOS_DIR. Rode: bash scripts/instalar-iphone.sh"
[ -f "$PBX" ] || die "pbxproj nao encontrado: $PBX. Rode: bash scripts/instalar-iphone.sh --recriar-ios"
[ -f "$PLIST" ] || die "Info.plist nao encontrado: $PLIST. Rode: bash scripts/instalar-iphone.sh --recriar-ios"
[ -f "$VERSAO_FILE" ] || die "arquivo de versao nao encontrado: $VERSAO_FILE"
[ -x "$PB" ] || die "PlistBuddy nao encontrado (precisa de macOS)"
command -v perl >/dev/null 2>&1 || die "perl nao encontrado"
[ -f "$PRIV_SRC" ] || die "faltou $PRIV_SRC no repo"

# parse estrito, nunca `source`
MKT="$(grep -E '^MARKETING_VERSION=' "$VERSAO_FILE" | tail -1 | cut -d= -f2- | tr -d ' \r' || true)"
BLD="$(grep -E '^CURRENT_PROJECT_VERSION=' "$VERSAO_FILE" | tail -1 | cut -d= -f2- | tr -d ' \r' || true)"
printf '%s' "$MKT" | grep -Eq '^[0-9]+(\.[0-9]+){1,2}$' || die "MARKETING_VERSION invalido em $VERSAO_FILE: '$MKT' (esperado ex. 2.0)"
printf '%s' "$BLD" | grep -Eq '^[1-9][0-9]*$' || die "CURRENT_PROJECT_VERSION invalido em $VERSAO_FILE: '$BLD' (esperado inteiro >= 1)"

# ---- 2) guard do incidente de 2026-10-22 ----
MSG_CORROMPIDO="projeto iOS corrompido (sem target nativo - mesmo sintoma de 2026-10-22). Nada foi alterado. Rode: bash scripts/instalar-iphone.sh --recriar-ios"
grep -q 'isa = PBXNativeTarget;' "$PBX" || die "$MSG_CORROMPIDO"
grep -q 'INFOPLIST_FILE = App/Info.plist;' "$PBX" || die "$MSG_CORROMPIDO"

# ---- 3) pbxproj (perl, tmp + mv so se mudou) ----
PERL_PROG=$(cat <<'PERL'
use strict; use warnings;
my ($in, $out) = @ARGV;
open(my $fh, '<', $in) or die "nao abri $in\n"; local $/; my $c = <$fh>; close $fh;
my %want = (
  CODE_SIGN_ENTITLEMENTS  => $ENV{APR_ENT},
  CURRENT_PROJECT_VERSION => $ENV{APR_BLD},
  DEVELOPMENT_TEAM        => $ENV{APR_TEAM},
  MARKETING_VERSION       => $ENV{APR_MKT},
);
my $nconf = 0;
sub ajusta {
  my ($blk) = @_;
  return $blk unless $blk =~ /INFOPLIST_FILE = App\/Info\.plist;/;
  return $blk unless $blk =~ /buildSettings = \{\n((?:\t\t\t\t[^\n]*\n)*?)\t\t\t\};/;
  my $body = $1;
  $nconf++;
  for my $k (sort keys %want) {
    my $v = $want{$k};
    next if $body =~ s/^(\t\t\t\t\Q$k\E = )[^;\n]*;$/$1$v;/m;
    my @lines = split /^/, $body;
    my @res; my $done = 0;
    for my $l (@lines) {
      if (!$done && $l =~ /^\t\t\t\t([A-Za-z0-9_\[\]=*]+) = / && $1 gt $k) { push @res, "\t\t\t\t$k = $v;\n"; $done = 1; }
      push @res, $l;
    }
    push @res, "\t\t\t\t$k = $v;\n" unless $done;
    $body = join '', @res;
  }
  $blk =~ s/(buildSettings = \{\n)(?:\t\t\t\t[^\n]*\n)*?(\t\t\t\};)/$1$body$2/;
  return $blk;
}
$c =~ s{(\t\t[0-9A-F]{24} /\* \w+ \*/ = \{\n\t\t\tisa = XCBuildConfiguration;\n.*?\n\t\t\};\n)}{ajusta($1)}gse;
die "nenhuma config do target App encontrada\n" if $nconf == 0;

# PrivacyInfo
my $bf  = "\t\t465BE8AF305B68D80081DCF5 /* PrivacyInfo.xcprivacy in Resources */ = {isa = PBXBuildFile; fileRef = 465BE8AE305B68D80081DCF5 /* PrivacyInfo.xcprivacy */; };\n";
my $fr  = "\t\t465BE8AE305B68D80081DCF5 /* PrivacyInfo.xcprivacy */ = {isa = PBXFileReference; lastKnownFileType = text.xml; path = PrivacyInfo.xcprivacy; sourceTree = \"<group>\"; };\n";
my $ch  = "\t\t\t\t465BE8AE305B68D80081DCF5 /* PrivacyInfo.xcprivacy */,\n";
my $rs  = "\t\t\t\t465BE8AF305B68D80081DCF5 /* PrivacyInfo.xcprivacy in Resources */,\n";
my $res_has = ($c =~ /isa = PBXResourcesBuildPhase;.*?PrivacyInfo\.xcprivacy in Resources.*?\n\t\t\};/s) ? 1 : 0;
my $ref_has = ($c =~ /path = PrivacyInfo\.xcprivacy;/) ? 1 : 0;
if ($res_has && $ref_has) {
  # ja referenciado (inclusive por arrasto no Xcode com outros IDs): nao toca
} else {
  my $fixed = 0;
  for my $l ($bf, $fr, $ch, $rs) { $fixed++ if index($c, $l) >= 0; }
  my $mentions = () = $c =~ /PrivacyInfo\.xcprivacy/g;
  my $fixed_mentions = 0;
  for my $l ($bf, $fr, $ch, $rs) { $fixed_mentions += () = $l =~ /PrivacyInfo\.xcprivacy/g if index($c, $l) >= 0; }
  die "PrivacyInfo.xcprivacy referenciado parcialmente com outros IDs; revise o projeto manualmente\n" if $mentions != $fixed_mentions;
  # IDs fixos em uso por outro objeto?
  for my $id (qw(465BE8AE305B68D80081DCF5 465BE8AF305B68D80081DCF5)) {
    my $total = () = $c =~ /\Q$id\E/g;
    my $mine = 0;
    for my $l ($bf, $fr, $ch, $rs) { if (index($c, $l) >= 0) { $mine += () = $l =~ /\Q$id\E/g; } }
    die "ID $id ja em uso por outro objeto; revise o projeto manualmente\n" if $total != $mine;
  }
  if (index($c, $bf) < 0) { $c =~ s{(/\* End PBXBuildFile section \*/)}{$bf$1} or die "secao PBXBuildFile ausente\n"; }
  if (index($c, $fr) < 0) { $c =~ s{(/\* End PBXFileReference section \*/)}{$fr$1} or die "secao PBXFileReference ausente\n"; }
  if (index($c, $ch) < 0) {
    $c =~ s{(isa = PBXGroup;\n\t\t\tchildren = \(\n(?:\t\t\t\t[^\n]*\n)*)(\t\t\t\);\n(?:\t\t\t[^\n]*\n)*?\t\t\tpath = App;)}{$1$ch$2} or die "grupo App ausente\n";
  }
  if (index($c, $rs) < 0) {
    $c =~ s{(isa = PBXResourcesBuildPhase;\n\t\t\tbuildActionMask = [0-9]+;\n\t\t\tfiles = \(\n(?:\t\t\t\t[^\n]*\n)*)(\t\t\t\);)}{$1$rs$2} or die "fase Resources ausente\n";
  }
}
open(my $oh, '>', $out) or die "nao escrevi $out\n"; print $oh $c; close $oh;
PERL
)
TMP="$PBX.apr.$$"
trap 'rm -f "$TMP"' EXIT
APR_ENT="$ENTITLEMENTS" APR_BLD="$BLD" APR_TEAM="$TEAM" APR_MKT="$MKT" \
  perl -e "$PERL_PROG" "$PBX" "$TMP" || die "falha ao editar o pbxproj (nada alterado). Se persistir: bash scripts/instalar-iphone.sh --recriar-ios"
if cmp -s "$PBX" "$TMP"; then
  rm -f "$TMP"
else
  mv "$TMP" "$PBX"
fi

# ---- 4) arquivo do PrivacyInfo ----
if ! cmp -s "$PRIV_SRC" "$IOS_DIR/App/App/PrivacyInfo.xcprivacy" 2>/dev/null; then
  cp "$PRIV_SRC" "$IOS_DIR/App/App/PrivacyInfo.xcprivacy"
fi

# ---- 5) Info.plist: nome sob o icone ----
for K in CFBundleName CFBundleDisplayName; do
  ATUAL="$("$PB" -c "Print :$K" "$PLIST" 2>/dev/null || true)"
  if [ "$ATUAL" != "$NOME" ]; then
    "$PB" -c "Set :$K $NOME" "$PLIST" 2>/dev/null || "$PB" -c "Add :$K string $NOME" "$PLIST"
  fi
done

# ---- 6) entitlements ----
[ -f "$IOS_DIR/App/App/App.entitlements" ] || warn "App.entitlements ausente - o build vai falhar. Rode: bash scripts/ios-restaurar-entitlements.sh"

# ---- 7) verificacao ----
if [ "$VERIFICAR" = "1" ] && command -v xcodebuild >/dev/null 2>&1; then
  if BS="$(xcodebuild -project "$IOS_DIR/App/App.xcodeproj" -target App -configuration Release -showBuildSettings -disableAutomaticPackageResolution 2>/dev/null)"; then
    chk(){ printf '%s\n' "$BS" | grep -Eq "^[[:space:]]*$1 = $2\$" || die "verificacao falhou: $1 != $2 no projeto"; }
    chk DEVELOPMENT_TEAM "$TEAM"
    chk CODE_SIGN_ENTITLEMENTS "$ENTITLEMENTS"
    chk MARKETING_VERSION "$MKT"
    chk CURRENT_PROJECT_VERSION "$BLD"
    ok "xcodebuild -showBuildSettings confirma as 4 chaves"
  else
    warn "nao consegui verificar via xcodebuild (SPM/rede/sandbox); pbxproj editado sem conferencia"
  fi
fi
ok "time=$TEAM entitlements=$ENTITLEMENTS versao=$MKT build=$BLD PrivacyInfo=referenciado nome=$NOME"
