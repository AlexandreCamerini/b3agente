#!/usr/bin/env bash
# 03 - Aplica o schema do budget no Neon.
# Pré-requisito: psql instalado e a connection string do Neon.
# Sem psql? Cole o conteúdo de schema.sql no SQL Editor do console do Neon.
set -euo pipefail

DATABASE_URL="${DATABASE_URL:?defina DATABASE_URL=postgresql://...neon.tech/...?sslmode=require}"
DIR="$(cd "$(dirname "$0")" && pwd)"

psql "${DATABASE_URL}" -f "${DIR}/schema.sql"
echo ">> tabela gateway_budget criada/confirmada no Neon."
