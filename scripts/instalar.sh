#!/usr/bin/env bash
# instalar.sh — BolsIA (b3-agente) · instalação em UM comando.
#
#   bash scripts/instalar.sh              # ambiente local: backend (venv+deps) + web (npm)
#   bash scripts/instalar.sh --iphone     # cadeia completa do iPhone (build+sync+pod+Xcode)
#   bash scripts/instalar.sh --tudo       # local + iPhone
#
# Orquestra os scripts existentes (scripts/setup.sh, scripts/instalar-iphone.sh)
# — não duplica lógica. Ao final roda as suítes como prova de instalação sã.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.."
ROOT="$(pwd)"

say(){ printf "\n\033[1m== %s ==\033[0m\n" "$*"; }
ok(){ printf "  \033[32m[OK]\033[0m %s\n" "$*"; }
die(){ printf "  \033[31m[X]\033[0m %s\n" "$*" >&2; exit 1; }

MODO="local"
case "${1:-}" in
  --iphone) MODO="iphone" ;;
  --tudo)   MODO="tudo" ;;
  "") ;;
  *) die "opção desconhecida: $1 (use --iphone ou --tudo)" ;;
esac

if [ "$MODO" != "iphone" ]; then
  say "Instalação local (backend + web)"
  [ -f scripts/setup.sh ] || die "scripts/setup.sh não encontrado — rode na raiz do projeto"
  bash scripts/setup.sh || die "setup.sh falhou (veja acima)"
  ok "ambiente local instalado"

  say "Prova de instalação: suítes do backend"
  if bash scripts/test.sh; then ok "suítes verdes"; else die "suítes falharam — instalação inconsistente"; fi

  say "Prova de instalação: suítes web (node)"
  FALHAS=0
  for t in web/tests/*.mjs; do
    [ -e "$t" ] || continue
    if (cd web && node "${t#web/}" >/dev/null 2>&1); then ok "$t"; else printf "  \033[31m[X]\033[0m %s\n" "$t"; FALHAS=1; fi
  done
  [ "$FALHAS" = "0" ] || die "suítes web falharam — confira 'npm install' em web/"
fi

if [ "$MODO" = "iphone" ] || [ "$MODO" = "tudo" ]; then
  say "Instalação no iPhone (cadeia completa)"
  [ -f scripts/instalar-iphone.sh ] || die "scripts/instalar-iphone.sh não encontrado"
  bash scripts/instalar-iphone.sh || die "instalar-iphone.sh falhou"
  ok "app pronto no Xcode — rode no aparelho físico (▶) e aceite a permissão de notificações"
fi

say "Instalação concluída"
echo "  próximo passo:  bash scripts/executar.sh        (rodar local)"
echo "                  bash scripts/atualizar.sh ...   (aplicar entrega e/ou deploy)"
