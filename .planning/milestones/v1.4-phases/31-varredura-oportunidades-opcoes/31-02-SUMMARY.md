---
phase: 31-varredura-oportunidades-opcoes
plan: 02
subsystem: api
tags: [python, pytest, fastapi, opcoes, mydata, orcamento-de-requisicoes, curadoria]

# Dependency graph
requires:
  - phase: 31-varredura-oportunidades-opcoes
    plan: "01"
    provides: candidatos_da_posicao(permitir_a_descoberto=...), proximos_vencimentos(), VENCIMENTOS_POR_POSICAO, TIPOS (motor puro das 4 estruturas)
provides:
  - "_curadoria_top varrendo até VENCIMENTOS_POR_POSICAO (2) cadeias por posição elegível, cotação uma vez por ticker, vencimento extra degradado não derruba o que já deu certo"
  - "meta.candidatosPorTipo/vencimentosPorTicker/tetoVencimentos — payload que o Plano 31-04 (bloco de Posições) vai consumir"
  - "GET /api/options/curadoria e POST .../narrativa lendo permitirOpcaoADescoberto exclusivamente de store.get(config) do servidor (T-31-01) — corpo do cliente nunca liga o flag"
  - "_vencimentos()/_venc_cache em options_provider_mydata.py — cache dedicado da lista de vencimentos, 1 get_vencimentos por ticker/dia"
affects: [31-04-bloco-posicoes-checkpoint]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pré-filtro de orçamento que PREVÊ o número de requisições restantes desta chamada (_gate(1) com cache de vencimentos fresco, _gate(2) sem) em vez de um número fixo — o commit atômico continua sendo _debita()/reservar() (WR-01), o pré-filtro só decide o TAMANHO do pedido"
    - "Cache dedicado por granularidade de dado (lista de vencimentos, barato e estável por dia) separado do cache de payload completo (cadeia, mais caro e específico por vencimento) — mesma chave-com-data que _cache já usa para 'first@'"
    - "Degradação por vencimento independente dentro do mesmo laço de posição: uma falha no vencimento extra nunca derruba o vencimento que já produziu candidatos, nunca faz `continue` no laço de posições"

key-files:
  created: []
  modified:
    - server/app/main.py
    - server/app/options_provider_mydata.py
    - server/tests/test_opcoes_curadoria_rota.py
    - server/tests/test_options_provider_mydata.py

key-decisions:
  - "degradados continua PER-POSIÇÃO, deduplicado — uma posição com 1 de 2 vencimentos degradados continua avaliada (produziu candidatos) e aparece só UMA vez em degradados, não uma entrada por vencimento falho"
  - "candidatosPorTipo é contado sobre o pool ANTES do corte de rankear (TOPO=4) — é essa contagem, não o top exibido, que torna SC-2/SC-3 verificáveis quando o top-4 fica todo de venda coberta (D-06: put/collar/descoberto rankeiam estruturalmente mal na fórmula única, consequência aceita, não bug)"
  - "POST /api/options/curadoria/narrativa ignora deliberadamente body['config']['permitirOpcaoADescoberto'] — lê cfg_servidor = store.get(_conn, 'config', user_id=scope) explicitamente, nunca o que o cliente mandar, para o mesmo campo específico (modo continua saindo do corpo, é preferência de exibição, não gate)"
  - "cache de vencimentos só grava quando a lista volta NÃO-vazia (mesma postura A-07 do _gate de orçamento) — erro ou lista vazia não pode 'travar' o cache pelos próximos 300s"

requirements-completed: [SC-1, SC-2, SC-3, SC-6]

# Metrics
duration: ~70min
completed: 2026-09-14
---

# Phase 31 Plan 02: Rota + cache de vencimentos Summary

**`_curadoria_top` varre até 2 vencimentos por posição elegível (custo declarado de até 3 requisições mydata via cache de vencimentos), publica `candidatosPorTipo`/`vencimentosPorTicker`/`tetoVencimentos` na meta, e as duas rotas de curadoria leem `permitirOpcaoADescoberto` exclusivamente da config do servidor — nunca do corpo da requisição.**

## Performance

- **Duration:** ~70 min
- **Started:** 2026-09-14 (após 31-01 completo, commit `82a9e03`)
- **Completed:** 2026-09-14
- **Tasks:** 3
- **Files modified:** 4 (`server/app/main.py`, `server/app/options_provider_mydata.py`, `server/tests/test_opcoes_curadoria_rota.py`, `server/tests/test_options_provider_mydata.py`)

## Contagem de chamadas por posição elegível — antes/depois

| Cenário | Antes (Fase 30) | Depois (Fase 31/D-01) |
|---|---|---|
| Cadeia com 1 vencimento futuro | 1 `get_options` | 1 `get_options` (teto não vira piso) |
| Cadeia com 2+ vencimentos futuros | 1 `get_options` (só o mais próximo) | 2 `get_options` (mais próximo + 2º) |
| Custo mydata por posição (rede real, provider layer) | 1 `get_vencimentos` + 1 `get_options_chain` = 2 | até 1 `get_vencimentos` (cacheado, Task 3) + 2 `get_options_chain` = até **3** (nunca 4) |

Custo declarado no plano (D-03): até 3 requisições mydata por posição elegível, contra o teto REAL enforçado `_teto_util_min() = int(60 * 0.9) = 54/min` (`mydata_budget.py`) — degradação graciosa por vencimento é esperada em carteiras realistas (>18 posições elegíveis simultâneas já excede o teto isolada), não caso raro; é exatamente por isso que a Task 3 (cache) existe: sem ela o custo seria 4/posição, não 3.

## Payload de `meta` (chaves exatas — contrato para o Plano 31-04)

```
{
  "avaliadas": [...tickers elegíveis...],
  "ignoradas": [...tickers com lote livre < 100...],
  "degradados": [...tickers com pelo menos 1 vencimento degradado, deduplicado...],
  "candidatosAvaliados": <int, len(pool) antes do corte de rankear>,
  "candidatosPorTipo": {
    "call_coberta": <int>, "put_protecao": <int>,
    "collar": <int>, "opcao_a_descoberto": <int>
  },
  "vencimentosPorTicker": { "<ticker>": ["<data ISO>", ...] },
  "tetoVencimentos": 2,
  "source": "<mydata|teste|None>"
}
```
As 4 chaves de `candidatosPorTipo` estão SEMPRE presentes, zero inclusive — nunca uma chave ausente quando um tipo não produziu candidato.

## Accomplishments

- `_curadoria_top` (Task 1): laço de vencimentos por posição elegível — primeira busca sem `expiration`, até `VENCIMENTOS_POR_POSICAO - 1` extras via `opcoes_curadoria.proximos_vencimentos`; cotação (`candle_provider.get_quote`) chamada UMA vez por ticker, fora do laço de vencimentos; vencimento extra degradado (exceção ou `providerStatus != "ok"`) não derruba o vencimento que já produziu candidatos, ticker entra UMA vez em `degradados`.
- As duas rotas (`GET /api/options/curadoria`, `POST /api/options/curadoria/narrativa`) leem `permitirOpcaoADescoberto` exclusivamente de `store.get(_conn, "config", user_id=scope)` — a rota de narrativa ignora explicitamente o mesmo campo se vier em `body["config"]` (T-31-01), com comentário nomeando o motivo.
- Cache de vencimentos (Task 3, `options_provider_mydata.py`): `_venc_cache`/`_vencimentos()` — 1 `get_vencimentos` por ticker/dia, não 1 por cadeia buscada. Pré-filtro `_gate()` passa a prever o número de requisições restantes (`_gate(1)` com cache fresco, `_gate(2)` sem), sem alterar o ponto de commit atômico (`_debita`/`mydata_budget.reservar`, WR-01 intacto).

## Task Commits

Cada task foi commitada atomicamente:

1. **Task 1: `_curadoria_top` varre até 2 vencimentos e recebe o flag de descoberto do servidor** - `0e9a713` (feat)
2. **Task 2: guardiões da contagem de vencimentos e do gate de descoberta na rota** - `19392f0` (test)
3. **Task 3: cache de vencimentos no provedor mydata (1 `get_vencimentos` por ticker/dia)** - `a71d1fa` (feat)

## Files Created/Modified

- `server/app/main.py` — `_curadoria_top` reescrita (laço de vencimentos, meta ampliada); as duas rotas de curadoria lendo o flag do servidor.
- `server/app/options_provider_mydata.py` — `_venc_cache`/`_VENC_TTL`/`_vencimentos()` novos; `get_options()` usando o helper e o pré-filtro previsível.
- `server/tests/test_opcoes_curadoria_rota.py` — `_cadeia`/`_contador` estendidos para multi-vencimento; 2 guardiões antigos com nota de reversão deliberada; 5 guardiões novos (10 → 15 `def test_`).
- `server/tests/test_options_provider_mydata.py` — fixture autouse limpando `_venc_cache`; 6 guardiões novos de cache de vencimentos (39 → 45 `def test_`).

## Provas negativas (comando + saída real)

**1. Teto de vencimentos (Task 2) — `VENCIMENTOS_POR_POSICAO` de 2 para 3:**
```
$ sed -i 's/^VENCIMENTOS_POR_POSICAO = 2$/VENCIMENTOS_POR_POSICAO = 3/' server/app/opcoes_curadoria.py
$ .venv/bin/python -m pytest tests/test_opcoes_curadoria_rota.py -k "teto_nao_vira_piso or duas_buscas" -q
1 failed, 1 passed, 13 deselected in 1.66s
FAILED tests/test_opcoes_curadoria_rota.py::test_duas_buscas_quando_cadeia_tem_dois_vencimentos
```
Revertido; `git diff --stat` limpo (confirmado por reexecução verde: 15 passed).

**2. Cache de vencimentos (Task 3) — cache forçado a MISS sempre (`hit = None`):**
```
$ .venv/bin/python -m pytest tests/test_options_provider_mydata.py -k test_duas_cadeias_mesmo_ticker_mesmo_dia_custam_3_requisicoes_nao_4 -q
1 failed, 44 deselected in 0.08s
FAILED ...
AssertionError: get_vencimentos deveria ser chamado 1 vez, veio ['PETR4', 'PETR4']
assert 2 == 1
```
Revertido; `git diff --stat` limpo (confirmado por reexecução verde: 58 passed em `test_options_provider_mydata.py` + `test_mydata_budget.py`).

## Números finais das duas suítes

```
cd server && .venv/bin/python -m pytest tests/test_opcoes_curadoria_rota.py tests/test_options_provider_mydata.py tests/test_opcoes_curadoria.py -q
129 passed, 3 warnings in 8.38s
```

```
bash scripts/executar.sh --testes  (dangerouslyDisableSandbox: sandbox local nega handshake TLS em ~27 testes não relacionados a este plano — mesma causa documentada em 31-01-SUMMARY.md e na memória do projeto, "sandbox mente")
2910 passed, 5 skipped, 3 xfailed, 0 failed, 991 warnings in 172.44s
147/147 .mjs OK
exit 0
```

Delta contra a baseline pós-31-01 (2899 passed): **+11 pytest** (5 em `test_opcoes_curadoria_rota.py` + 6 em `test_options_provider_mydata.py`), **+0 .mjs** (plano não toca `web/`). Nenhuma regressão. Sem sandbox (execução direta), a primeira passada mostrou os mesmos 27 falsos-positivos de TLS já catalogados — não relacionados a nenhum arquivo deste plano.

## Decisions Made

Ver `key-decisions` no frontmatter. Resumo em prosa:

- `degradados` continua per-posição e deduplicado — uma posição com 1 de 2 vencimentos degradados ainda é `avaliada` (produziu candidatos do vencimento que deu certo) e aparece só uma vez em `degradados`, nunca uma entrada por vencimento falho.
- `candidatosPorTipo` conta o `pool` inteiro, antes do corte de `rankear` (TOPO=4) — é essa contagem, não o `top` exibido, que prova SC-2/SC-3 mesmo quando o top-4 fica todo de venda coberta (D-06, consequência aceita).
- A rota de narrativa lê `permitirOpcaoADescoberto` explicitamente do servidor, ignorando o mesmo campo em `body["config"]` — única exceção ao padrão geral da rota (que aceita `config` do corpo para `modo`), documentada com o motivo (T-31-01) direto no código.
- O cache de vencimentos só grava lista NÃO-vazia — erro ou lista vazia não "trava" vazia pelos próximos 300s (mesma postura A-07 do gate de orçamento).

## Deviations from Plan

None - plano executado exatamente como escrito. As duas provas negativas exigidas pelos acceptance criteria foram executadas e revertidas sem deixar resíduo (`git diff --stat` limpo em ambos os casos, confirmado antes do commit de cada task).

## Issues Encountered

- Ao escrever os guardiões T-31-01 do plano (Task 2), a primeira tentativa de reusar `chamados` como lista de tickers simples quebrou com a mudança de `_contador` para pares `(ticker, expiration)` — ajustado inline nos dois guardiões antigos (`sorted(t for t, _e in chamados)` em vez de `sorted(chamados)`), sem mudar a garantia que eles protegem (contagem exata).
- No guardião negativo de cota do cache de vencimentos (Task 3), a primeira asserção (`len(chamadas_chain) == 0`) ignorava que a PRIMEIRA chamada do teste já havia gerado 1 chamada de `get_options_chain` — corrigido para comparar contra o valor capturado após a primeira chamada, não contra zero absoluto. Achado e corrigido antes do commit da Task 3, não é um desvio de regra (Rule 1/2/3) porque o bug estava só no teste em rascunho, nunca chegou a ser commitado.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Plano 31-04** (bloco de Posições + checkpoint humano) consome `meta.candidatosPorTipo`/`vencimentosPorTicker`/`tetoVencimentos` diretamente do payload de `GET /api/options/curadoria` — as 4 chaves de `candidatosPorTipo` sempre presentes (zero inclusive) simplificam a renderização condicional no front (não precisa checar `"opcao_a_descoberto" in meta`, só o valor).
- Nenhum bloqueio conhecido. `git status --short` mostra só os 4 arquivos declarados em `files_modified` do plano; `server/app/store.py` intocado (Fase 29 intacta).
- `bash scripts/executar.sh --testes` exit 0, 2910 passed / 0 failed, sem regressão contra a baseline do Plano 01.

---
*Phase: 31-varredura-oportunidades-opcoes*
*Completed: 2026-09-14*

## Self-Check: PASSED

- FOUND: `.planning/phases/31-varredura-oportunidades-opcoes/31-02-SUMMARY.md`
- FOUND: `0e9a713` (Task 1 commit)
- FOUND: `19392f0` (Task 2 commit)
- FOUND: `a71d1fa` (Task 3 commit)
