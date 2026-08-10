#!/usr/bin/env bash
# configurar-e-rodar.sh — Boris+ (b3-agente) · do zero ao app rodando, UM comando.
#
# Orquestra os scripts que já existem (instalar.sh → configura; executar.sh → roda),
# valida os pré-requisitos ANTES de tentar, e orienta a chave de IA. Não duplica
# lógica — é a porta de entrada para uma máquina nova.
#
#   bash configurar-e-rodar.sh            # pré-requisitos + instala (se preciso) + sobe DEV
#   bash configurar-e-rodar.sh --prod     # idem, mas sobe PROD local (1 servidor :8787)
#   bash configurar-e-rodar.sh --rapido   # pula a reinstalação; só valida e sobe
#   bash configurar-e-rodar.sh --reinstalar  # força reinstalar tudo, depois sobe
#   bash configurar-e-rodar.sh --parar    # encerra e libera as portas
#   bash configurar-e-rodar.sh --status   # o que está no ar
#   bash configurar-e-rodar.sh --testes   # só roda as suítes e sai
#
# Endereços (DEV): app web http://localhost:5173 · API http://localhost:8787
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]:-$0}")"
ROOT="$(pwd)"

if [ -t 1 ]; then B=$'\033[1m'; G=$'\033[32m'; Y=$'\033[33m'; R=$'\033[31m'; Z=$'\033[0m'; else B=""; G=""; Y=""; R=""; Z=""; fi
say(){ printf "\n%s== %s ==%s\n" "$B" "$*" "$Z"; }
ok(){ printf "  %s[OK]%s %s\n" "$G" "$Z" "$*"; }
warn(){ printf "  %s[!]%s %s\n" "$Y" "$Z" "$*"; }
die(){ printf "  %s[X]%s %s\n" "$R" "$Z" "$*" >&2; exit 1; }

MODO="dev"; INSTALAR="auto"
case "${1:-}" in
  ""|--dev)     MODO="dev" ;;
  --prod)       MODO="prod" ;;
  --rapido)     MODO="dev"; INSTALAR="nao" ;;
  --reinstalar) MODO="dev"; INSTALAR="forcar" ;;
  --parar)      exec bash executar.sh --stop ;;
  --status)     exec bash executar.sh --status ;;
  --testes)     exec bash executar.sh --testes ;;
  -h|--help)    sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
  *)            die "opção desconhecida: $1 (use --help)" ;;
esac

# ---------- 1) pré-requisitos (falha cedo, com o conserto) ----------
say "Pré-requisitos"
[ -f server/app/main.py ] || die "rode na RAIZ do projeto (não achei server/app/main.py)."

if command -v python3 >/dev/null 2>&1; then
  if python3 -c 'import sys; raise SystemExit(0 if sys.version_info>=(3,10) else 1)'; then
    ok "python3 $(python3 -V 2>&1 | awk '{print $2}')"
  else
    warn "python3 $(python3 -V 2>&1 | awk '{print $2}') — recomendado 3.10+ (ainda roda em 3.9)."
  fi
else
  die "python3 não encontrado. Instale em https://www.python.org/downloads/ (ou 'brew install python')."
fi

if command -v node >/dev/null 2>&1; then
  NODE_MAJ="$(node -v 2>/dev/null | sed 's/^v//; s/\..*//')"
  if [ "${NODE_MAJ:-0}" -ge 22 ] 2>/dev/null; then ok "node $(node -v)"; else warn "node $(node -v) — o app web pede Node 22+ (o backend roda sem ele)."; fi
else
  warn "node não encontrado — o backend roda, mas o app web (Vite) não sobe. Instale Node 22+ (https://nodejs.org)."
fi
command -v npm >/dev/null 2>&1 && ok "npm $(npm -v)" || warn "npm ausente (vem com o Node)."
command -v git >/dev/null 2>&1 && ok "git presente" || warn "git ausente (só necessário para deploy)."

# ---------- 2) chave de IA (orientação, não bloqueia) ----------
say "Chave de IA"
KEY_ENV=""
for v in ANTHROPIC_API_KEY OPENAI_API_KEY GEMINI_API_KEY B3_AGENTE_API_KEY; do
  [ -n "${!v:-}" ] && KEY_ENV="$v" && break
done
if [ -n "$KEY_ENV" ]; then
  ok "$KEY_ENV está no ambiente — dá para usar 'Variável de ambiente' na Config da IA do app."
else
  warn "Nenhuma chave no ambiente. Duas formas (o app SOBE sem chave, em modo simulado):"
  echo "     • No app: Config → Modelo de IA → 'Digitar aqui' e cole a chave (fica no dispositivo)."
  echo "     • Por env (keySource='env'):  export ANTHROPIC_API_KEY=sk-...   (ou OPENAI_/GEMINI_/B3_AGENTE_)"
  echo "       Dica p/ não vazar no histórico:  read -rs ANTHROPIC_API_KEY && export ANTHROPIC_API_KEY"
fi

# ---------- 3) configurar (instalar/rodar) ----------
JA_INSTALADO=0
[ -x server/.venv/bin/python ] && [ -d web/node_modules ] && JA_INSTALADO=1

if [ "$INSTALAR" = "forcar" ] || { [ "$INSTALAR" = "auto" ] && [ "$JA_INSTALADO" -eq 0 ]; }; then
  say "Configurar (instalar backend + web)"
  bash instalar.sh || die "instalação falhou (veja acima)."
elif [ "$INSTALAR" = "nao" ]; then
  warn "Modo --rapido: pulei a instalação."
else
  ok "Ambiente já instalado (server/.venv + web/node_modules). Use --reinstalar para refazer."
fi

# ---------- 4) rodar ----------
IP="$(ipconfig getifaddr en0 2>/dev/null || hostname -I 2>/dev/null | awk '{print $1}')"
say "Rodar ($MODO)"
echo "  App web:  http://localhost:5173     API:  http://localhost:8787"
[ -n "${IP:-}" ] && echo "  iPhone (mesma rede): Config → endereço do servidor → http://$IP:8787"
echo "  Encerrar:  bash configurar-e-rodar.sh --parar"
echo
if [ "$MODO" = "prod" ]; then
  exec bash executar.sh --prod
else
  exec bash executar.sh
fi
