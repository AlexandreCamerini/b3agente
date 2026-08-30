#!/usr/bin/env bash
# Boris+ — backup do banco SQLite (FASE 2, decisão E).
#
# Faz um backup CONSISTENTE mesmo com o servidor rodando (usa a API de backup
# online do SQLite via Python — checkpoint do WAL incluído). Respeita B3_DB_PATH;
# senão usa server/data/b3_agente.db. Mantém os 14 backups mais recentes.
#
# Uso:
#   bash scripts/backup-db.sh                 # backup para server/backups/
#   B3_DB_PATH=/data/b3_agente.db bash scripts/backup-db.sh
#   BACKUP_DIR=/data/backups bash scripts/backup-db.sh   # ex.: no volume Railway
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVER_DIR="$ROOT/server"; [ -d "$SERVER_DIR" ] || SERVER_DIR="$ROOT"

DB="${B3_DB_PATH:-$SERVER_DIR/data/b3_agente.db}"
OUT="${BACKUP_DIR:-$SERVER_DIR/backups}"
KEEP="${BACKUP_KEEP:-14}"
PY="${PYTHON:-python3}"

[ -f "$DB" ] || { echo "ERRO: banco não encontrado em '$DB' (defina B3_DB_PATH)."; exit 1; }
mkdir -p "$OUT"
STAMP="$(date +%Y%m%d-%H%M%S)"
DEST="$OUT/b3_agente-$STAMP.db"

"$PY" - "$DB" "$DEST" <<'PY'
import sqlite3, sys
src, dest = sys.argv[1], sys.argv[2]
s = sqlite3.connect(src)
try:
    s.execute("PRAGMA wal_checkpoint(TRUNCATE)")  # consolida o WAL antes de copiar
    d = sqlite3.connect(dest)
    with d:
        s.backup(d)            # backup online consistente
    d.close()
finally:
    s.close()
print("backup ->", dest)
PY
[ $? -eq 0 ] || { echo "ERRO no backup."; exit 1; }

# retém só os KEEP mais recentes
ls -1t "$OUT"/b3_agente-*.db 2>/dev/null | tail -n +$((KEEP+1)) | while read -r old; do rm -f "$old"; done
echo "OK. Backups em: $OUT (retendo $KEEP)."
