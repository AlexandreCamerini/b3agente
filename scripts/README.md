# Scripts — subir o BolsIA (gateway + Neon + Cloud Run)

Idempotentes e não-destrutivos. Cada um lê variáveis do ambiente (falha cedo
se faltar). Inspecione antes de rodar — nenhum deve ser executado às cegas.

## Pré-requisitos manuais (não roteirizáveis)
- **GitHub CLI** logado: `gh auth login`
- **Conta Neon** criada + connection string em mãos
- **Conta GCP pessoal** + projeto + billing habilitado (cartão) — separada do trabalho
- **gcloud CLI** logado: `gcloud auth login`
- **psql** (só para o passo 03; alternativa: SQL Editor do Neon)

## Ordem

```bash


# A1+A2 — publicar o gateway (rode na pasta do skeleton descompactado)
GH_USER=seu_usuario ./scripts/01_publish_gateway.sh

# B + D — plugar no BolsIA (rode na raiz do repo do BolsIA)
GH_USER=seu_usuario APP_ENTRYPOINT=app.main:app ./scripts/02_wire_bolsia.sh

# C2 — schema no Neon
DATABASE_URL='postgresql://...neon.tech/db?sslmode=require' ./scripts/03_apply_neon_schema.sh

# E — deploy (rode na raiz do repo do BolsIA)
PROJECT_ID=seu-projeto-estudo \
ANTHROPIC_API_KEY=sk-ant-... \
DATABASE_URL='postgresql://...neon.tech/db?sslmode=require' \
  ./scripts/04_deploy_cloudrun.sh

# E5 — budget alert
BILLING_ACCOUNT_ID=XXXXXX-XXXXXX-XXXXXX ./scripts/05_budget_alert.sh
```

## O que fica por sua conta (código, não script)
- **Fase B (integração):** trocar as chamadas diretas à API no código do BolsIA
  por `GovernedGateway` + registrar `AppBudget("bolsia", ...)`. O Claude entrega
  esse trecho — é lógica da app, não infra.
- **Fase C (wiring do Neon):** instanciar `PostgresBudgetStore(pool)` no boot.

## Nota de segurança
Os scripts recebem segredos por variável de ambiente para não gravá-los em
arquivo. Evite deixá-los no histórico do shell (use um gerenciador ou `read -s`).
