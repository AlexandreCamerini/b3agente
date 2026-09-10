---
quick_id: 260909-tmi
phase: quick-260909-tmi
plan: 01
type: quick
wave: 1
depends_on: []
files_modified: [STAGING.md, DEPLOY_RAILWAY.md, docs/ARQUITETURA.md, docs/adr/013-rbac-papeis-e-entitlements.md, docs/MEDICAO-gate-liquidez-mydata-2026-09-08.md, server/app/main.py, server/app/candle_provider.py, server/tests/test_gate_cadastro.py, server/tests/test_admin_summary.py, server/tests/test_ordens_pendentes_rotas.py, web/tests/test_api_parity.mjs]
autonomous: true
---

<objective>
Pedido do Alex (2026-09-09): "mude todos os domínios para boris.semente.dev". Fechar `boris.semente.dev` como ÚNICO domínio canônico de produção na documentação viva, nos comentários de código e nas fixtures de teste, eliminando os remanescentes `bolsia.semente.dev`, `acamerini.app` (plano F4 que nunca serviu HTTPS) e `b3-production-8fc0.up.railway.app` (morta, "Application not found").
</objective>

<context>
- Inventário antes: código/scripts JÁ usavam `boris.semente.dev` (70 ocorrências; `web/src/api.js` `PROD_BASE`, `ios_dist/manifest.plist`, scripts). Sobravam 3 `bolsia.*` em 2 docs, ~20 `acamerini.app` em docs vivos/comentários/testes, 3 `b3-production-8fc0` em fixture de teste.
- `boris.semente.dev` e `bolsia.semente.dev` respondem HOJE o mesmo serviço (`/api/health` = `F10-20260908-02`); `acamerini.app` resolve DNS sem HTTPS.
- **Histórico protegido NÃO se reescreve** (guardrail do CLAUDE.md): `qa/`, `CHECKOUT-*`, `RELEASES.md`, `ESTADO-*` mantêm os domínios da época.
- `mydata.acamerini.app` em docstring de `candle_provider.py` é OUTRO serviço (MyData); o nome atual é `mydata.semente.dev` (`mydata_client.BASE_DEFAULT`). Corrigido para o nome certo, não para boris.
- Fora do repo (não verificável daqui, sem comando Railway sem aprovação): valor real de `B3_GATED_HOSTS` em produção; return URLs de SIWA/Google nos consoles Apple/Google.
</context>

<tasks>
<task type="auto">
  <name>Task 1: trocar domínios remanescentes na doc viva, comentários e testes</name>
  <files>ver files_modified</files>
  <action>Substituição textual. Em `test_gate_cadastro.py`, o teste "host não listado passa" usava `boris.semente.dev` como exemplo de host LIVRE contra gate em `acamerini.app`; com o gate em `boris.semente.dev`, o host livre passa a ser a URL do Railway (`b3agente.up.railway.app`), como o docstring já descrevia.</action>
  <verify>grep sem resultado fora do histórico protegido; `pytest tests/test_gate_cadastro.py tests/test_admin_summary.py tests/test_ordens_pendentes_rotas.py` e `node web/tests/test_api_parity.mjs` verdes; suíte canônica `bash scripts/executar.sh --testes`.</verify>
  <done>Nenhuma referência a `bolsia.semente.dev`, `acamerini.app` (exceto `mydata.`) ou `b3-production-8fc0` em `server/`, `web/`, `scripts/`, `docs/`, `*.md` de raiz vivos.</done>
</task>
</tasks>

<success_criteria>
Um commit atômico; suíte canônica verde; SUMMARY lista o que ficou intocado (histórico) e o que é externo (env Railway, consoles Apple/Google).
</success_criteria>
