#!/usr/bin/env bash
# 01 - Publica o gateway como repo git PÚBLICO e cria a tag.
# Rode DENTRO da pasta descompactada do skeleton (onde está o pyproject.toml).
# Pré-requisito: git e GitHub CLI (gh) autenticado -> `gh auth login`.
set -euo pipefail

GH_USER="${GH_USER:?defina GH_USER=seu_usuario_github}"
REPO="${REPO:-claude-gateway}"
TAG="${TAG:-v0.1.0}"

[ -f pyproject.toml ] || { echo "ERRO: rode na raiz do skeleton (não achei pyproject.toml)"; exit 1; }

# repo git local (idempotente)
if [ ! -d .git ]; then
  git init -q
  git add .
  git commit -q -m "gateway ${TAG}: core (cache) + controls (governança)"
fi

# cria o repo remoto público e faz push (se ainda não existir)
if ! gh repo view "${GH_USER}/${REPO}" >/dev/null 2>&1; then
  gh repo create "${GH_USER}/${REPO}" --public --source=. --remote=origin --push
else
  git remote get-url origin >/dev/null 2>&1 || \
    git remote add origin "https://github.com/${GH_USER}/${REPO}.git"
  git push -u origin HEAD
fi

# tag (idempotente)
if ! git rev-parse "${TAG}" >/dev/null 2>&1; then
  git tag "${TAG}"
  git push origin "${TAG}"
  echo ">> tag ${TAG} publicada."
else
  echo ">> tag ${TAG} já existe (nada a fazer)."
fi

echo ">> pronto: https://github.com/${GH_USER}/${REPO} @ ${TAG}"
echo ">> linha p/ requirements do BolsIA:"
echo "   claude-gateway[postgres] @ git+https://github.com/${GH_USER}/${REPO}.git@${TAG}"
