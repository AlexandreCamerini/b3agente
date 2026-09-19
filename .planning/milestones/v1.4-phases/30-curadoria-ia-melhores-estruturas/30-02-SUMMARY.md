---
phase: 30-curadoria-ia-melhores-estruturas
plan: 02
subsystem: opcoes-curadoria
tags: [opcoes, venda-coberta, ranking-deterministico, rota-http, custo-zero]
dependency-graph:
  requires: [opcoes_curadoria.candidatos_da_posicao, opcoes_curadoria.rankear, options_provider.get_options, candle_provider.get_quote, store.qty_livre, _spot_from_chain_or_quote]
  provides: [main._curadoria_top, "GET /api/options/curadoria"]
  affects: [30-03 (rota de narração reusará _curadoria_top para narrar exatamente a mesma lista), 30-04 (bloco de UI consumirá esta rota)]
tech-stack:
  added: []
  patterns: [partição elegível/ignorada ANTES de qualquer rede (contagem verificável por teste, não por comentário), best-effort ADR-004 por posição (try/except vira degradados, nunca 500), helper não-exposto reusável entre planos]
key-files:
  created:
    - server/tests/test_opcoes_curadoria_rota.py
  modified:
    - server/app/main.py
decisions:
  - "avaliadas (meta) lista os tickers ELEGÍVEIS (partição), não só os que tiveram fetch bem-sucedido — degradados é informação adicional, pode se sobrepor a avaliadas"
  - "docstrings evitam os literais _gate_analise/LLM/metering dentro do corpo das funções guardadas por grep — mesmo ajuste textual já registrado no 30-01-SUMMARY, para não autoinvalidar os guardiões estáticos"
  - "posição inelegível em teste é simulada travando qtyTravada (não comprando <100 ações) — store.buy arredonda qty para o lote mínimo de 100 (store.py:671), então nunca nasce uma posição com menos de 1 lote"
metrics:
  duration: "~40min"
  completed: 2026-09-13
---

# Fase 30 Plano 02: Varredura cross-posição — GET /api/options/curadoria Summary

Rota `GET /api/options/curadoria` que varre a carteira inteira, busca a cadeia
de opções UMA vez por posição elegível (comprada, lote livre >= 100) e devolve
o top-4 de venda coberta do motor puro do Plano 01 — custo zero de IA e de
MCP, propriedade provada por contagem exata de chamadas, não por comentário.

## O que foi construído

`server/app/main.py` (+98 linhas, família `/api/options/*`, logo após
`options_vigias`):

- **`_curadoria_top(scope, modo)`** — helper `async` não exposto como rota
  (reusável pelo Plano 03, que narrará exatamente esta lista). Lê
  `positions`, particiona `elegiveis`/`ignoradas` ANTES de qualquer rede
  (`store.qty_livre(p) >= 100`), e para cada posição elegível faz **uma**
  chamada `options_provider.get_options(t)` (sem `expiration` — D3, cadeia
  de um vencimento só) dentro de `try/except`: exceção ou
  `providerStatus != "ok"` manda o ticker para `degradados` e o laço
  continua. Cotação vem de `candle_provider.get_quote` (best-effort, `None`
  em falha) combinada com `_spot_from_chain_or_quote`. Cada posição
  contribui candidatos via `opcoes_curadoria.candidatos_da_posicao` (n
  default do módulo); o pool inteiro passa por `opcoes_curadoria.rankear`.
  Não busca `technical_snapshot`/`setups`/candles (D1: elegibilidade só por
  lastro).
- **`GET /api/options/curadoria`** — lê `appMode` do config do escopo, chama
  o helper, devolve `{top, modo, fonte: "deterministico", at, avaliadas,
  ignoradas, degradados, candidatosAvaliados, source}`. Um `except` de
  última instância cobre falha inesperada fora do laço (ex.: `store` fora do
  ar) sem nunca cair em 500. Docstring declara que a rota não passa pelo
  gate de análise (D6 — só a etapa de narração, plano separado, entra nesse
  gate).
- Import `opcoes_curadoria` acrescentado ao grupo de imports de opções (ao
  lado de `opcoes_lastreadas`).

`server/tests/test_opcoes_curadoria_rota.py` (novo, 10 testes via
`TestClient`):

- **Contagem exata (coração do arquivo)**: `test_uma_chamada_por_posicao_
  elegivel` (2 posições elegíveis + 1 inelegível → `len(chamados) == 2`
  EXATO) e `test_nenhuma_chamada_extra_por_strike` (8 calls líquidas por
  ticker, mais que os 5 strikes pedidos → ainda `== 2`, prova que a
  enumeração de strikes é em memória). `test_carteira_sem_posicao_elegivel_
  zero_chamadas` prova zero chamadas quando não há posição elegível.
- **Ordem e teto**: `test_ordem_e_do_motor` (razão vencedora de um ticker
  específico aparece em `top[0]`, razões não-crescentes, `posicaoNoRanking`
  1..N) e `test_teto_de_quatro` (3 posições × 5 candidatos = 15 no pool,
  `len(top) == 4`, `candidatosAvaliados == 15`).
- **Degradação (ADR-004)**: `test_degradado_nao_derruba` (exceção num
  ticker) e `test_cadeia_degradada_reduz_lista_sem_500` (`providerStatus`
  degradado) — ambos 200, o outro ticker segue no `top`.
- **Ausência de IA/MCP**: `test_sem_ia_na_rota` (sem `texto`/`narrativa`/
  `markdown` na resposta; guardião estático recorta o corpo textual de
  `options_curadoria` e confirma ausência de `llm`/`_gate_analise`/
  `metering`) e `test_sem_mcp_na_curadoria` (mesmo recorte para
  `_curadoria_top` + `options_curadoria`, mais o arquivo inteiro de
  `opcoes_curadoria.py`, sem `mcp_client`/`options_mcp_api`/
  `mcp.semente.dev`, comentários filtrados).
- **Carteira vazia**: `test_carteira_vazia_200_com_listas_vazias`.

**Prova negativa real, exercitada e revertida**: dupliquei a chamada
`options_provider.get_options(t)` dentro do laço de `_curadoria_top` (mesma
técnica de regressão que o 30-01-SUMMARY registrou para o motor puro) e rodei
os dois testes de contagem — ambos falharam de verdade
(`assert 4 == 2`, `chamados == ['PETR4', 'PETR4', 'VALE3', 'VALE3']`).
Revertido; `git diff server/app/main.py` voltou vazio e a suíte de 10 testes
voltou a verde.

## Deviations from Plan

**1. [Rule 1 - bug de teste, não de produção] `store.buy` arredonda para o
lote mínimo de 100** (`store.py:671`) — a primeira versão do teste tentava
criar uma posição "inelegível" comprando 50 ações, mas `buy()` arredondava
para 100, tornando-a elegível por acidente (o guardião de contagem falhou
capturando isso: 3 chamadas em vez de 2). Corrigido simulando lote livre <
100 via `qtyTravada` direto no store (`_trava_parcial`), o mesmo campo que
uma CALL coberta aberta usaria — sem tocar `store.py`.

**2. [Rule 1 - ajuste textual] Docstrings reescritas para não conter os
literais `_gate_analise`/`LLM` dentro do corpo das duas funções** — os
próprios guardiões estáticos desta fase (`test_sem_ia_na_rota`, e o
acceptance criteria de grep do plano) contam menções sem filtrar
comentário/docstring dentro do recorte da função; a docstring explicando por
que a rota não passa pelo gate citava literalmente esses termos, o que
autoinvalidaria a checagem. Reescrito sem o literal, preservando a intenção
documental (mesmo padrão já registrado no 30-01-SUMMARY para
`options_provider`/`"tipo": "put"`).

## Auth Gates

Nenhum.

## Threat Flags

Nenhuma superfície nova fora do `<threat_model>` do plano — os 7 threats
(T-30-06 a T-30-11, T-30-SC) foram cobertos pelo desenho já descrito: nenhuma
dependência nova, a rota lê carteira só do próprio `scope` (via
`current_scope`), não aceita parâmetro de ticker/ordenação/peso, e a
degradação por posição segue o padrão best-effort ADR-004 já em produção nas
demais rotas de `/api/options/*`.

## Known Stubs

Nenhum. A rota é funcional ponta a ponta (verificada com servidor real
rodando, ver "Verificação" abaixo); a narração de IA (Plano 03) e o bloco de
UI (Plano 04) são planos separados que ainda não consomem esta rota.

## Verificação

- `bash scripts/executar.sh --testes` → **exit 0** (2838 passed, 5 skipped,
  3 xfailed no pytest — 10 a mais que o baseline de 2828 do 30-01; todos os
  `web/tests/*.mjs` OK) — rodado uma vez ao fim de cada task.
- `server/.venv/bin/python -m pytest server/tests/test_opcoes_curadoria_rota.py -q`
  → 10 passed.
- `grep -c '/api/options/curadoria'` = 1; `grep -n 'async def _curadoria_top'`
  = 1 definição; exatamente 1 ocorrência de `get_options` dentro do corpo do
  helper, sem `expiration`.
- `grep -v '^ *#' ... | grep -n curadoria | grep -ci mcp` = 0.
- `grep -A40 'def options_curadoria' ... | grep -c _gate_analise` = 0.
- `grep -c '== 2'` no arquivo de teste = 11 (>= 2 exigido); `grep -c 'SC-'`
  = 15 (>= 7 exigido).
- Regressão real exercitada e revertida (ver acima) — os dois testes de
  contagem capturam a quebra que D3/SC-2 existem para impedir.
- Servidor local exercitado de verdade: `POST /api/auth/register` → 200,
  `GET /api/options/curadoria` (autenticado, `B3_OPTIONS_PROVIDER=mock`) →
  200 com as chaves `top`, `avaliadas`, `ignoradas`, `degradados`, `fonte`,
  `at` (carteira vazia no momento do teste — a compra ficou pendente por
  mercado fechado, sem afetar a validação do contrato HTTP da rota).

## Instruções para validar localmente

```bash
server/.venv/bin/python -m pytest server/tests/test_opcoes_curadoria_rota.py -v
bash scripts/executar.sh --testes
```

## Limitações conhecidas

- Esta rota ainda não é consumida por nenhuma UI — o Plano 03 (rota de
  narração com gate de análise, reusando `_curadoria_top`) e o Plano 04
  (bloco em Posições, D4) são planos separados.
- Nenhum bump/publicação de front é necessário neste plano (só backend).

## Self-Check

```
FOUND: server/app/main.py (grep confirma _curadoria_top e /api/options/curadoria)
FOUND: server/tests/test_opcoes_curadoria_rota.py
FOUND commit 2d21387 (feat: _curadoria_top + rota)
FOUND commit 1f17bb6 (test: guardião de contagem + contrato)
```

## Self-Check: PASSED
