#!/usr/bin/env bash
# Boris+ — backup do banco SQLite (FASE 2, decisão E).
#
# 2026-09-07: a IMPLEMENTAÇÃO saiu daqui e virou `server/app/backup.py`; este
# script agora é só o ponto de entrada local. Motivo: o `rootDirectory` do
# Railway é `/server`, então `scripts/` não existe dentro do container e um
# `preDeployCommand` apontando para cá falharia — justamente no deploy em que
# o backup mais importa. Com o código dentro de `server/app/`, o mesmo caminho
# serve o pre-deploy do Railway e o uso local, sem duas cópias para divergir.
#
# O comportamento local não mudou: mesmo backup online consistente (checkpoint
# do WAL + API `.backup()` do SQLite), mesmo destino padrão (`server/backups`),
# mesma retenção de 14.
#
# Uso:
#   bash scripts/backup-db.sh                 # backup para server/backups/
#   B3_DB_PATH=/data/b3_agente.db bash scripts/backup-db.sh
#   BACKUP_DIR=/data/backups bash scripts/backup-db.sh   # ex.: no volume Railway
#   BACKUP_KEEP=30 bash scripts/backup-db.sh
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVER_DIR="$ROOT/server"; [ -d "$SERVER_DIR" ] || SERVER_DIR="$ROOT"

# Destino padrão preservado (`server/backups`) — o default do módulo é
# `<pasta do banco>/backups`, que é o certo no Railway (mesmo volume do banco)
# mas mudaria silenciosamente onde os backups locais caem. Aqui é explícito.
OUT="${BACKUP_DIR:-$SERVER_DIR/backups}"
KEEP="${BACKUP_KEEP:-14}"

# Prioriza o venv do projeto; cai para o python do PATH.
PY="${PYTHON:-}"
if [ -z "$PY" ]; then
  if [ -x "$SERVER_DIR/.venv/bin/python3" ]; then PY="$SERVER_DIR/.venv/bin/python3"
  elif command -v python3 >/dev/null 2>&1; then PY="python3"
  else PY="python"; fi
fi

ARGS=(-m app.backup --out "$OUT" --keep "$KEEP")
[ -n "${B3_DB_PATH:-}" ] && ARGS+=(--db "$B3_DB_PATH")

cd "$SERVER_DIR" || { echo "ERRO: não achei o diretório server/ em $ROOT"; exit 1; }
"$PY" "${ARGS[@]}"
RC=$?

# O módulo trata banco ausente como sucesso (environment novo não tem o que
# proteger). No uso LOCAL isso quase sempre é engano de caminho, então aqui a
# ausência vira aviso visível — sem mudar o código de saída.
if [ "$RC" -eq 0 ]; then
  DB_ESPERADO="${B3_DB_PATH:-$SERVER_DIR/data/b3_agente.db}"
  [ -f "$DB_ESPERADO" ] || echo "AVISO: '$DB_ESPERADO' não existe — nada foi copiado (defina B3_DB_PATH?)."
fi
exit "$RC"
