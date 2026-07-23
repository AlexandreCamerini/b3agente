#!/usr/bin/env bash
# 02 - Pluga o gateway no repo do BolsIA (idempotente).
# Rode DENTRO da raiz do repo do BolsIA.
#   - adiciona a dependência pinada no requirements.txt
#   - ajusta o entrypoint do Dockerfile para o módulo real do BolsIA
set -euo pipefail

GH_USER="${GH_USER:?defina GH_USER=seu_usuario_github}"
REPO="${REPO:-claude-gateway}"
TAG="${TAG:-v0.1.0}"
APP_ENTRYPOINT="${APP_ENTRYPOINT:?defina APP_ENTRYPOINT=modulo.arquivo:app do BolsIA, ex: app.main:app}"

DEP="claude-gateway[postgres] @ git+https://github.com/${GH_USER}/${REPO}.git@${TAG}"

# requirements.txt (cria se não existir; não duplica)
touch requirements.txt
if grep -q "claude-gateway" requirements.txt; then
  echo ">> requirements.txt já referencia claude-gateway (revise manualmente se a tag mudou)."
else
  printf '%s\n' "${DEP}" >> requirements.txt
  echo ">> dependência adicionada ao requirements.txt."
fi

# Dockerfile: troca o placeholder do entrypoint
if [ -f Dockerfile ]; then
  if grep -q "app.main:app" Dockerfile; then
    sed -i.bak "s#app.main:app#${APP_ENTRYPOINT}#g" Dockerfile && rm -f Dockerfile.bak
    echo ">> entrypoint do Dockerfile ajustado para ${APP_ENTRYPOINT}."
  else
    echo ">> Dockerfile não tem o placeholder app.main:app (já ajustado?). Revise à mão."
  fi
else
  echo "AVISO: sem Dockerfile aqui. Copie o template que o Claude entregou para a raiz do BolsIA."
fi
