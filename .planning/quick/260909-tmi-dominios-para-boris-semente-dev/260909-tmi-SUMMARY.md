---
quick_id: 260909-tmi
phase: quick-260909-tmi
plan: 01
status: complete
subsystem: docs
tags: [dominio, producao, gate-cadastro, fixtures]
requires: []
provides:
  - "boris.semente.dev como único domínio canônico na doc viva, comentários e fixtures de teste"
affects: [STAGING.md, DEPLOY_RAILWAY.md, docs/ARQUITETURA.md, adr-013, main.py (comentário), candle_provider.py (docstring), testes de gate/admin/pendentes, test_api_parity.mjs]
---

# Quick 260909-tmi: domínios remanescentes → boris.semente.dev

## Commits
- `abfa21c` — docs+test: boris.semente.dev como único domínio canônico (260909-tmi). 11 arquivos, 28/28 linhas.

## O que mudou
| Antes | Depois | Onde |
|---|---|---|
| `bolsia.semente.dev` | `boris.semente.dev` | `STAGING.md` (tabela), `docs/MEDICAO-gate-liquidez-mydata-2026-09-08.md` (fonte + comando curl) |
| `acamerini.app` | `boris.semente.dev` | `DEPLOY_RAILWAY.md` (exemplo `B3_GATED_HOSTS`), `docs/ARQUITETURA.md`, `docs/adr/013` (tabela de permissões), comentários em `main.py:395-398`, fixtures em `test_gate_cadastro.py`/`test_admin_summary.py`/`test_ordens_pendentes_rotas.py` |
| `b3-production-8fc0.up.railway.app` | `boris.semente.dev` | `web/tests/test_api_parity.mjs` (fixture de normalização de URL) |
| `mydata.acamerini.app` | `mydata.semente.dev` | docstring `candle_provider.py:193` — OUTRO serviço, nome atual em `mydata_client.BASE_DEFAULT` |

Ajuste semântico num teste: `test_host_nao_listado_passa_mesmo_com_gate_ativo` usava `boris.semente.dev` como exemplo de host LIVRE contra gate em `acamerini.app`. Com o gate agora em `boris.semente.dev`, o host livre passou a ser `b3agente.up.railway.app` — exatamente o que o docstring ("a URL do Railway e o app iOS continuam livres") já descrevia.

## Sem mudança de comportamento
`web/src/api.js` `PROD_BASE`, `ios_dist/manifest.plist` e todos os scripts JÁ apontavam para `boris.semente.dev` (70 ocorrências antes desta task). Nada de runtime mudou; `bolsia.semente.dev` continua respondendo o mesmo serviço como alias.

## Intocado de propósito (guardrail "histórico não se reescreve")
`qa/*`, `CHECKOUT-*.md`, `RELEASES.md`, `ESTADO-*` mantêm `acamerini.app` e `b3-production-8fc0` como estavam na época.

## Fora do repo — não verificado (sem comando Railway sem aprovação)
- Valor real de `B3_GATED_HOSTS` em produção: se ainda estiver `acamerini.app` (ou vazio), o cadastro obrigatório NÃO está ativo em `boris.semente.dev`. Confirmar no painel do Railway.
- Return URLs / domínios autorizados de Sign in with Apple (Services ID) e Google OAuth nos consoles Apple/Google.

## Verificação
- `pytest tests/test_gate_cadastro.py tests/test_admin_summary.py tests/test_ordens_pendentes_rotas.py`: 37 passed.
- `node web/tests/test_api_parity.mjs`: 6/6.
- Suíte canônica `bash scripts/executar.sh --testes`: 2114 passed / 1 skipped (pytest) + 124 OK / 0 X (web/tests), exit 0.
- grep final: nenhuma referência aos domínios antigos fora do histórico protegido (exceto `mydata.*`, que é outro serviço).
