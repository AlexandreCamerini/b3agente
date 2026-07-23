#!/usr/bin/env bash
# 04 - Deploy do BolsIA no Cloud Run (conta GCP PESSOAL).
# Rode DENTRO da raiz do repo do BolsIA (onde está o Dockerfile já ajustado).
# Pré-requisitos MANUAIS (não roteirizáveis):
#   - conta GCP pessoal + projeto criado + billing habilitado (cartão)
#   - gcloud CLI instalado e logado: `gcloud auth login`
#   - o repo do gateway PÚBLICO (senão o build falha ao pip install do git)
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?defina PROJECT_ID=seu-projeto-estudo}"
REGION="${REGION:-southamerica-east1}"          # São Paulo
SERVICE="${SERVICE:-bolsia}"
ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:?defina ANTHROPIC_API_KEY=sk-ant-...}"
DATABASE_URL="${DATABASE_URL:?defina DATABASE_URL=postgresql://...neon.tech/...}"

gcloud config set project "${PROJECT_ID}" >/dev/null

echo ">> habilitando APIs..."
gcloud services enable run.googleapis.com secretmanager.googleapis.com \
  cloudbuild.googleapis.com artifactregistry.googleapis.com >/dev/null

# cria ou versiona um secret (idempotente)
put_secret() {
  local name="$1" value="$2"
  if gcloud secrets describe "${name}" >/dev/null 2>&1; then
    printf '%s' "${value}" | gcloud secrets versions add "${name}" --data-file=- >/dev/null
  else
    printf '%s' "${value}" | gcloud secrets create "${name}" \
      --replication-policy=automatic --data-file=- >/dev/null
  fi
  echo "   secret ${name} ok"
}
echo ">> gravando secrets..."
put_secret anthropic-api-key "${ANTHROPIC_API_KEY}"
put_secret neon-database-url "${DATABASE_URL}"

echo ">> deploy (build via Dockerfile + push + deploy)..."
# --source .  -> Cloud Build detecta o Dockerfile, builda e sobe sozinho.
# --min-instances=0 -> custo-zero ocioso (aceita cold start).
# --max-instances=2 -> teto de raio de explosão e de custo.
# --allow-unauthenticated -> endpoint público (ok p/ estudo; ciente do trade-off).
gcloud run deploy "${SERVICE}" \
  --source . \
  --region "${REGION}" \
  --allow-unauthenticated \
  --min-instances=0 \
  --max-instances=2 \
  --cpu=1 --memory=512Mi \
  --set-secrets="ANTHROPIC_API_KEY=anthropic-api-key:latest,DATABASE_URL=neon-database-url:latest"

URL="$(gcloud run services describe "${SERVICE}" --region "${REGION}" --format='value(status.url)')"
echo ">> no ar: ${URL}"
