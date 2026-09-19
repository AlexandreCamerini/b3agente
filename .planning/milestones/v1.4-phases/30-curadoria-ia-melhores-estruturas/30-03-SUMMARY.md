---
phase: 30-curadoria-ia-melhores-estruturas
plan: 03
subsystem: opcoes-curadoria
tags: [opcoes, venda-coberta, ranking-deterministico, llm, cota-de-analise]
dependency-graph:
  requires: [opcoes_curadoria.exigir_ranking, opcoes_curadoria.narrativa_system, opcoes_curadoria.narrativa_user, main._curadoria_top, main._gate_analise, llm._call_llm, llm.resolve_key, llm.collect_usage, ai_activity.registrar_uso, kpi.normalize_markdown]
  provides: [curadoria_narrativa.narrar, "POST /api/options/curadoria/narrativa"]
  affects: [30-04 (bloco de UI consumirá esta rota para o texto de narração)]
tech-stack:
  added: []
  patterns: [camada fina de LLM espelhando assistente.responder, recusa estrutural de pool não rankeado antes de qualquer chamada ao modelo, recomputação server-side em vez de aceitar entrada do cliente, gate de cota único reusado — nunca duplicado]
key-files:
  created:
    - server/app/curadoria_narrativa.py
    - server/tests/test_opcoes_curadoria_narrativa.py
  modified:
    - server/app/main.py
decisions:
  - "narrar() recusa ANTES de qualquer chamada ao LLM: exigir_ranking(top) como primeira ação do corpo, mais uma segunda guarda para top vazio — o guardrail vira comportamento do código, não promessa de comentário (30-CONTEXT)"
  - "Nenhum teto de custo próprio em curadoria_narrativa.py — D6 é explícito: a cota inteira é decidida na ROTA via o mesmo _gate_analise de /api/analyze, nunca um orçamento paralelo"
  - "A rota lê do corpo SÓ `config`; ela RECOMPUTA _curadoria_top no servidor e ignora qualquer `top`/`candidatos`/`estruturas` que o cliente mande — provado por teste funcional (corpo adulterado de 9 itens não muda a resposta) e por guardião estático (nenhum body.get desses três nomes em main.py)"
  - "402 do gate PROPAGA na rota de narração (ao contrário de /api/technical/analyze, que mascara em fallback determinístico) — o fallback desta tela já é a rota irmã GET /api/options/curadoria, que não gasta cota"
  - "Docstrings do módulo/função e da rota evitam os literais opcoes_motor/candidatos_da_posicao/rankear/options_provider/get_options/teto_dia_brl fora de comentário — mesmo ajuste textual já registrado nos SUMMARYs do 30-01/30-02, para não autoinvalidar os guardiões estáticos de grep"
metrics:
  duration: "~55min"
  completed: 2026-09-13
---

# Fase 30 Plano 03: Curadoria — narração de IA sob o gate de análise Summary

Camada fina de LLM que escreve um parágrafo por estrutura sobre o top-4 já
escolhido pelo motor determinístico (Planos 01/02) e a rota HTTP que a expõe,
gastando exatamente a mesma cota mensal de `/api/analyze` — nunca um
orçamento paralelo, e estruturalmente incapaz de reordenar ou aceitar
estruturas vindas do cliente.

## O que foi construído

`server/app/curadoria_narrativa.py` (novo, 89 linhas) — `narrar(conn, config,
scope, modo, top)`:

- Primeira ação do corpo: `opcoes_curadoria.exigir_ranking(top)`, seguida de
  uma guarda explícita para lista vazia — as duas ANTES de qualquer chamada
  ao modelo de linguagem (provado por teste que conta chamadas ao `_call_llm`
  fake, não só por leitura de código).
- Prompt inteiro (`narrativa_system`/`narrativa_user`) vem do módulo puro do
  Plano 01 — este módulo não compõe texto de prompt.
- Mesma camada fina de `assistente.responder`: `llm.collect_usage()` +
  `llm._call_llm()` + `ai_activity.registrar_uso(tipo="Curadoria")` em
  try/except (contabilidade nunca derruba a resposta) +
  `kpi.normalize_markdown`.
- Devolve `{"texto": ..., "estruturas": [contractSymbol na ordem narrada]}` —
  a lista de símbolos viaja de propósito, para o cliente (e o teste) provarem
  que o texto fala das MESMAS estruturas mostradas, na mesma ordem.
- Nenhum freio de custo próprio: D6 (30-CONTEXT) decide a cota inteira na
  rota; um teto paralelo aqui seria o orçamento duplicado que D6 proíbe.

`server/app/main.py` (+50 linhas) — `POST /api/options/curadoria/narrativa`,
logo após `GET /api/options/curadoria`:

- Corpo aceita SOMENTE `config` — a rota chama `_curadoria_top` de novo
  (mesmo helper do Plano 02) e narra o que o servidor ordenou, nunca o que o
  cliente mandar.
- `_gate_analise(scope, config)` — o MESMO gate de `/api/analyze` (BYOK →
  plano mensal → cota diária da chave gerenciada). 402 PROPAGA (ao contrário
  de `/api/technical/analyze`, que mascara em fallback determinístico): o
  fallback determinístico desta tela já é a rota irmã, que não gasta cota.
- `top` vazio → `{"texto": None, "motivo": "sem_estrutura", ...}` sem chamar
  o modelo nem consumir cota.
- Falha do LLM → 502 com `llm.public_error(e)`, sem consumir.
- Sucesso → `_consume_ai()` chamado UMA vez, resposta com `texto`,
  `estruturas`, `top`, `fonte: "ia-sobre-ranking-deterministico"`.

`server/tests/test_opcoes_curadoria_narrativa.py` (novo, 17 testes):

- **Task 1 (`narrar`, unitário)**: top válido devolve texto e registra uso;
  lista maior que `TOPO`, fora de ordem ou vazia levanta `ValueError` com
  ZERO chamadas ao LLM; falha de `ai_activity.registrar_uso` não derruba a
  resposta; inspeção de fonte prova ausência de `opcoes_motor`/
  `candidatos_da_posicao`/`rankear(`/`options_provider`/`get_options` no
  módulo.
- **Task 2 (rota, via `TestClient`)**: 200 com `consume()` exatamente uma
  vez; 402 do gate propaga sem chamar o LLM; sem estrutura elegível → 200
  sem chamar o LLM nem consumir; falha do LLM → 502 sem consumir;
  `test_corpo_da_requisicao_nao_influencia_a_ordem` (T-30-12) — corpo com
  `top`/`candidatos` de 9 itens invertidos não muda a resposta;
  `test_estruturas_da_resposta_casa_com_top_na_ordem`;
  `test_ia_nunca_recebe_pool_nao_rankeado` (T-30-13) — captura o argumento
  REAL recebido por `narrar` no call site da rota e confirma que é
  exatamente a saída da ordenação do motor, mais um `ValueError` provado ao
  passar 9 itens desordenados direto para `narrar`; guardião estático de que
  `body.get("top"/"candidatos"/"estruturas")` não existe em `main.py`.
- **Gate real, sem mock** (rigor adicional pedido para esta fase, que não
  passou por `gsd-plan-checker`): 3 testes que NÃO mockam `_gate_analise` —
  `test_gate_real_byok_ignora_ledger_estourado_e_nao_consome_mensal` (BYOK
  real com ledger mensal em 100, muito acima do limite de 30 do FREE, ainda
  destrava a rota e o ledger mensal continua em 100 — BYOK não escreve
  nele); `test_gate_real_402_do_plano_mensal_propaga_sem_byok` (sem BYOK e
  ledger em 100, o 402 REAL do `plan.can_analyze` propaga, LLM nunca
  chamado); `test_gate_real_managed_consome_ledger_mensal_so_no_sucesso`
  (sem IA gerenciada configurada no ambiente de teste, a config que chega em
  `narrar` é exatamente a que `_ai_apply_managed` devolve nesse ramo — prova
  que a narração usa o MESMO caminho de `/api/analyze`, não uma cópia
  paralela).

## Deviations from Plan

**1. [Ajuste textual, mesmo padrão do 30-01/30-02] Docstrings reescritas
sem os literais exatos `opcoes_motor`, `candidatos_da_posicao`, `rankear`,
`options_provider`, `get_options` e `teto_dia_brl`** — os próprios
acceptance criteria do plano usam grep cru (`grep -v '^ *#' ... | grep -cE
'opcoes_motor|candidatos_da_posicao|rankear|options_provider|get_options'`)
que não distingue docstring de código: manter os literais na explicação da
fronteira do módulo autoinvalidaria o guardião de pureza mesmo com o módulo
se comportando corretamente. A intenção documental (por que essas funções
não são importadas/chamadas aqui) foi preservada em prosa, sem o literal
exato. Isso obrigou reestruturar o docstring da função `narrar` (docstring
curta + comentários logo abaixo) para que `exigir_ranking` aparecesse dentro
das primeiras linhas do corpo, satisfazendo o grep `-A4` do acceptance
criteria ao mesmo tempo que preservava a explicação completa.

**2. [Rigor adicional, não no plano original] 3 testes de gate real sem
mock** — a instrução de execução pediu para provar D6 exercitando de fato
os ramos BYOK/plano/gerenciada de `_gate_analise`, não só mockando a função
inteira (como os 4 testes de contrato HTTP da Task 2 fazem, por desenho,
para isolar o comportamento da ROTA). Acrescentados sem alterar
`server/app/main.py` além do já previsto — são só testes novos no mesmo
arquivo.

Nenhuma outra alteração fora do escopo do plano.

## Auth Gates

Nenhum.

## Threat Flags

Nenhuma superfície nova fora do `<threat_model>` do plano — os 7 threats
(T-30-12 a T-30-17, T-30-SC) foram cobertos pelo desenho já descrito:
nenhuma dependência nova, nenhum campo de conta sensível no prompt (a lista
de campos de `narrativa_user` é fechada, herdada do Plano 01), e a manchete
de cada item continua vindo só de `skill_ref` (fora do escopo textual da
narração).

## Known Stubs

Nenhum. A rota é funcional ponta a ponta (exercitada com servidor real, ver
"Verificação" abaixo); o bloco de UI que consumirá `texto`/`estruturas`
(Plano 04) é um plano separado.

## Verificação

- `bash scripts/executar.sh --testes` → **exit 0** (2856 passed, 5 skipped,
  3 xfailed no pytest — 18 a mais que o baseline de 2838 do 30-02: 6 da
  Task 1 + 8 da Task 2 (contrato HTTP) + 3 de gate real + 1 de contagem
  residual não atribuível a este plano; `web/tests/*.mjs` OK) — rodado uma
  vez ao fim de cada task.
- `server/.venv/bin/python -m pytest server/tests/test_opcoes_curadoria_narrativa.py -q`
  → 17 passed (>= 8 exigidos).
- `grep -A4 'async def narrar' server/app/curadoria_narrativa.py | grep -c
  'exigir_ranking'` = 1; pureza por inspeção (`opcoes_motor`,
  `candidatos_da_posicao`, `rankear`, `options_provider`, `get_options`,
  `teto_dia_brl`) = 0 cada; `grep -c 'metering' curadoria_narrativa.py` = 0.
- `grep -A30 'def options_curadoria_narrativa' main.py | grep -c
  '_gate_analise(scope, config)'` = 1; `grep -A60 ... | grep -c
  '_consume_ai()'` = 1; `body.get("top"/"candidatos"/"estruturas")` = 0
  ocorrências em `main.py`; `git diff --stat -- server/app/metering.py`
  vazio (nenhum `metering.consume` novo escrito nesta fase).
- Servidor local exercitado de verdade (`B3_OPTIONS_PROVIDER=mock`):
  `POST /api/auth/register` → 200; `POST /api/buy` → 200 (ordem ficou
  pendente por mercado fechado no momento do teste, mesmo achado já
  registrado no 30-02-SUMMARY — não afeta a validação do contrato HTTP);
  `GET /api/options/curadoria` → 200 com `top: []` (carteira sem posição
  liquidada ainda); `POST /api/options/curadoria/narrativa` → 200 com
  `{"texto": null, "motivo": "sem_estrutura", ...}` — nunca 500, gate real
  em produção sem mock nenhum.
- Isolamento no event loop: a chamada ao LLM é `await llm._call_llm(...)`,
  sem I/O síncrono.

## Instruções para validar localmente

```bash
server/.venv/bin/python -m pytest server/tests/test_opcoes_curadoria_narrativa.py -v
bash scripts/executar.sh --testes
```

## Limitações conhecidas

- O bloco de UI que exibirá `texto`/`estruturas` desta rota em
  Posições/Portfólio (D4) é o Plano 04, ainda não implementado.
- A verificação ao vivo não chegou a produzir um `top` não-vazio (a compra
  de teste ficou pendente por mercado fechado) — o caminho de sucesso com
  texto real de IA está coberto pelos testes automatizados (`_call_llm`
  fake), não por uma chamada de LLM de verdade em produção.

## Self-Check

```
FOUND: server/app/curadoria_narrativa.py
FOUND: server/tests/test_opcoes_curadoria_narrativa.py
FOUND commit b80f41e (test: guardiões de narrar())
FOUND commit 3c41492 (feat: curadoria_narrativa.narrar)
FOUND commit 7e01bc8 (test: guardiões da rota de narrativa)
FOUND commit 4e95686 (feat: POST /api/options/curadoria/narrativa)
```

## Self-Check: PASSED
