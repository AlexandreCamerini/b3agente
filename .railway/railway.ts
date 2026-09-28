// Boris+ — projeto Railway `bolsIA`, serviço `b3agente`, ambientes
// `production` e `staging`. Substitui `server/railway.json` (Config as Code,
// deprecado; a plataforma para de ler em 2026-12-01).
//
// Declarado = observado em 2026-09-27 (describe-service nos dois ambientes):
// - builder RAILPACK sem Dockerfile. O `NIXPACKS` do railway.json é vestigial:
//   o log de build de 2026-09-27 mostra o provider Python do Railpack
//   (`python -m venv /opt/venv && pip install -r requirements.txt`).
// - fonte GitHub `AlexandreCamerini/b3agente`, rootDirectory `/server`,
//   branch `main` em production e `staging` em staging. ATENÇÃO (STAGING.md):
//   mudar branch por CLI já vazou para produção duas vezes em 2026-09-07.
//   Este arquivo declara exatamente o que está no painel; o `plan` DEVE mostrar
//   zero mudança em `source` nos dois ambientes. Nunca use este arquivo para
//   trocar branch — publique staging por `scripts/publicar-staging.sh`.
// - volume `b3agente-volume` (50 GB, sfo) em /data, o MESMO id nos dois
//   ambientes segundo a API (STAGING.md descreve um banco por ambiente —
//   conferir no primeiro `plan`; se o plan propuser criar ou destruir volume,
//   pare).
// - start, healthcheck `/api/health` (120 s) e restart ON_FAILURE ×3 vêm do
//   railway.json e ficam explícitos aqui. O backup roda no INÍCIO do `start`
//   (não como `preDeploy`): o pré-deploy do Railway executa num container
//   separado, sem o volume montado (doc oficial), então nunca protegeria o
//   banco de verdade. A semântica de saída do backup está documentada em
//   `server/app/backup.py`.
// - domínios custom só em production: boris.semente.dev e bolsia.semente.dev
//   (o segundo é legado do nome bolsIA, mas está ativo). Os domínios gerados
//   `*.up.railway.app` não entram no IaC por regra da plataforma.
//
// Ordem de migração (ação do dono): `railway link` no projeto `bolsIA`,
// environment `staging` primeiro → `railway config plan` → `apply` → smoke
// (`/api/health`) → repetir em `production` → só então remover
// `server/railway.json` e limpar o "config file path" no painel.
// O pacote npm `railway` precisa resolver a partir da raiz do repo
// (`npm install --no-save railway`; `node_modules/` já é ignorado).
import { defineRailway, github, preserve, project, service, volume } from "railway/iac";

export default defineRailway((ctx) => {
  if (ctx.projectName && ctx.projectName !== "bolsIA") {
    throw new Error(`este arquivo descreve o projeto bolsIA; diretório linkado a "${ctx.projectName}".`);
  }
  const prod = ctx.environment === "production";

  const dados = volume("b3agente-volume", { region: "sfo", sizeMB: 50000 });

  const api = service("b3agente", {
    source: github("AlexandreCamerini/b3agente", {
      branch: prod ? "main" : "staging",
      rootDirectory: "/server",
      checkSuites: false,
    }),
    // `a || b && c` é, em POSIX sh, `((a || b) && c)`: `||` e `&&` têm a mesma
    // precedência e associam à esquerda. Sem parênteses de propósito — o parser
    // de startCommand do Railway rejeita `( ... )` ("Failed to parse start
    // command", deploy 03a3a97a, 2026-09-27). Se o backup falhar com o banco
    // presente, python e python3 saem 1 e o `&&` segura o uvicorn.
    start: "python -m app.backup --pre-start || python3 -m app.backup --pre-start && uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    healthcheck: "/api/health",
    healthcheckTimeout: 120,
    deploy: { restartPolicyType: "ON_FAILURE", restartPolicyMaxRetries: 3 },
    replicas: { sfo: 1 },
    domains: prod
      ? [
          { domain: "boris.semente.dev", port: 8080 },
          { domain: "bolsia.semente.dev", port: 8080 },
        ]
      : [],
    volumeMounts: { "/data": dados },
    env: {
      APNS_AUTH_KEY: preserve(),
      APNS_KEY_ID: preserve(),
      APNS_SANDBOX: preserve(),
      APNS_TEAM_ID: preserve(),
      APNS_TOPIC: preserve(),
      APPLE_CLIENT_ID: preserve(),
      B3_ADMIN_EMAILS: preserve(),
      B3_AGENTE_API_KEY: preserve(),
      B3_CANDLE_PROVIDER: preserve(),
      B3_DB_PATH: preserve(),
      B3_MANAGED_GLOBAL_DAILY_CAP: preserve(),
      B3_MANAGED_LLM_KEY: preserve(),
      B3_MANAGED_LLM_MODEL: preserve(),
      B3_MANAGED_LLM_PROVIDER: preserve(),
      B3_OBSERVABILIDADE_CHAVE: preserve(),
      B3_OPTIONS_PROVIDER: preserve(),
      B3_RADAR_DAILY_HHMM: preserve(),
      BOLSAI_API_KEY: preserve(),
      BRAPI_TOKEN: preserve(),
      GOOGLE_CLIENT_ID: preserve(),
      MCP_CLIENT_ID: preserve(),
      MCP_CLIENT_SECRET: preserve(),
      MYDATA_TOKEN: preserve(),
      PORTAL_ORIGENS: preserve(),
      SEMENTE_ID_CLIENT_ID: preserve(),
      SEMENTE_ID_CLIENT_SECRET: preserve(),
      SEMENTE_ID_EMAIL_DONO: preserve(),
      // Só em production (2026-09-27): endereço do serviço MCP.
      ...(prod ? { MCP_URL: preserve() } : {}),
      // Só em staging: kill-switch do agente e simulação de mercado aberto.
      ...(prod ? {} : { B3_AGENT_KILL: preserve(), B3_DEV_MERCADO_ABERTO: preserve() }),
    },
  });

  return project("bolsIA", { resources: [api, dados] });
});
