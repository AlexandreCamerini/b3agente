#!/usr/bin/env bash
# 05 - Budget alert no billing do GCP (avisa por e-mail em 50/90/100%).
# NÃO corta serviço automaticamente — é alerta. É o cinto do lado infra.
set -euo pipefail

BILLING_ACCOUNT_ID="${BILLING_ACCOUNT_ID:?defina BILLING_ACCOUNT_ID (gcloud billing accounts list)}"
AMOUNT="${AMOUNT:-5}"                 # teto de referência em USD
NAME="${NAME:-estudo-bolsia}"

gcloud billing budgets create \
  --billing-account="${BILLING_ACCOUNT_ID}" \
  --display-name="${NAME}" \
  --budget-amount="${AMOUNT}USD" \
  --threshold-rule=percent=0.5 \
  --threshold-rule=percent=0.9 \
  --threshold-rule=percent=1.0

echo ">> budget alert '${NAME}' criado (${AMOUNT} USD, avisos em 50/90/100%)."
echo ">> dica: liste billing accounts com 'gcloud billing accounts list'."
