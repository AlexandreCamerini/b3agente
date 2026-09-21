---
phase: 36-motor-de-payoff-gen-rico
plan: 02
subsystem: api
tags: [opcoes, payoff, motor-determinístico, pytest]

# Dependency graph
requires:
  - phase: 36
    plan: "01"
    provides: "opcoes_payoff.py com vencimento por perna, guarda de entrada degenerada e _breakevens sem S=0 espúrio"
provides:
  - "dominio_da_curva(perfil, spot=None) — domínio X/Y do gráfico de payoff (D-05)"
  - "segmentos_da_curva(perfil) — leitura da curva segmento a segmento, cortando só nos strikes (D-06)"
  - "caso golden nomeado test_golden_trava_de_alta_49_17_49_67_debito_025 travando as 5 propriedades de PAYOFF-03"
  - "auditoria de independência de nome de estratégia (PAYOFF-01), por teste e por leitura"
affects: [37-grafico-de-payoff-e-explicacao-confiaveis]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Funções de renderização (domínio/segmentos) recebem o dicionário JÁ calculado por perfil_da_estrutura + spot — nunca remontam pernas/curva, mesmo idioma de 'não recalcular o que a função já sabe'"
    - "Segmentos cortam só nos strikes (onde curva.resultado muda de inclinação aritmética); breakeven é frase de PONTO separada, nunca fronteira de segmento"
    - "Lado ilimitado do domínio Y sinaliza None (nunca 0.0/teto inventado) — mesmo guardrail de _delta_total/ganho_maximo"

key-files:
  created: []
  modified:
    - server/app/opcoes_payoff.py
    - server/tests/test_opcoes_payoff.py

key-decisions:
  - "Leitura do D-06 confirmada como PATTERNS.md-reading-1 (constant-slope segments): boundary nos strikes (49.17/49.67), não no breakeven (49.42) — 36-CONTEXT.md já tinha corrigido o exemplo literal após o pattern-map (achado próprio da Fase 36-01/planejamento, não desta execução); esta execução só implementou e travou a leitura já fechada"
  - "vencimentos.divergentes tratado como guarda de topo nas duas funções novas (dominio_da_curva/segmentos_da_curva): x/y tudo None com motivo, curva vazia -> segmentos [], nunca aproxima nem lê ganho/perda máxima nulos da degradação como 'ilimitado'"

requirements-completed: [PAYOFF-01, PAYOFF-03]

# Metrics
duration: ~15min (commits 19:34-19:40, mais leitura/planejamento antes)
completed: 2026-09-21
---

# Phase 36 Plan 02: Domínio X/Y, segmentos da curva e caso golden nomeado Summary

**`opcoes_payoff.py` ganhou `dominio_da_curva()` (domínio X/Y do gráfico, D-05) e `segmentos_da_curva()` (leitura segmento a segmento cortando só nos strikes, D-06), e a fase fecha com o caso golden do Alex travado como regressão NOMEADA cobrindo as 5 propriedades de PAYOFF-03 e a independência de nome de estratégia provada por teste e por auditoria de leitura (PAYOFF-01).**

## Performance

- **Duration:** ~15 min de commits (19:34–19:40), mais leitura de contexto/planejamento antes
- **Completed:** 2026-09-21
- **Tasks:** 3/3
- **Files modified:** 2 (`server/app/opcoes_payoff.py`, `server/tests/test_opcoes_payoff.py`) — nenhum arquivo novo (D-01)

## Accomplishments

- **D-05 (`dominio_da_curva`):** domínio X = `[min(strike)-margem, max(strike)+margem]` limitado em baixo por 0.0, com `margem = max(12% do span, 4% do spot)` para 2+ strikes de opção, `10% do strike` para strike único, e âncora no spot/preço do papel quando não há strike de opção nenhum (perna ACAO ignorada no cálculo de span — strike 0.0 é constante de cálculo, não strike de verdade). Spot sempre dentro: expande só o lado que falta até incluí-lo, sem margem extra. Domínio Y inclui zero sempre, estende 15% além do extremo finito, e vira `None` (nunca `0.0`) no lado ilimitado. Guarda de vencimentos divergentes primeiro: devolve tudo `None` com `motivo`.
- **D-06 (`segmentos_da_curva`):** percorre `curva` aos pares (mesmo formato de `_breakevens`), classifica cada trecho por sinal de `resultado` (`positiva`/`negativa`/`zero`), e fecha com um segmento de cauda (`ate=None`) cuja inclinação vem de `ganho_ilimitado`/`perda_ilimitada` — sem recalcular soma de sinais nem expor `inclinacao_direita`. Corta SÓ nos strikes: o golden dá 3 segmentos com fronteira em 49,17 (não 49,42) — o breakeven cai dentro do 2º segmento, continua sendo frase de PONTO via `breakevens`. Curva de 1 ponto só (estrutura ACAO isolada) produz 1 segmento sem par, exatamente pela ausência de pares em `zip(curva, curva[1:])`.
- **PAYOFF-03 (caso golden nomeado):** `test_golden_trava_de_alta_49_17_49_67_debito_025` trava num só lugar breakeven 49,42, ganho/perda máximos 0,25, nenhum lado ilimitado, 3 segmentos com fronteiras 49,17/49,67, e as duas metades de D-02 (ganho/perda máximos × 100 = R$ 25,00 calculado DENTRO do teste; breakeven nunca multiplicado, continua 49,42).
- **PAYOFF-01 (independência de nome):** `test_motor_nao_decide_pelo_nome_da_estrutura` monta a mesma trava de alta com `contrato` neutro (`PETR4C4917`/`PETR4C4967`) vs. nomes de estratégia (`BORBOLETA`/`STRADDLE`) e asserta que perfil, segmentos e domínio são idênticos, campo a campo, exceto o passthrough `contrato`. Auditoria de leitura complementar: `grep -in "estrategia\|strategy\|borboleta\|straddle\|condor" server/app/opcoes_payoff.py` devolve **zero linhas** — nem em código, nem em comentário, nem em docstring (não há nada a listar aqui).

## Task Commits

Each task was committed atomically:

1. **Task 1: `dominio_da_curva()` — domínio X e Y para o gráfico (D-05)** - `31e7db7` (feat)
2. **Task 2: `segmentos_da_curva()` — leitura da curva segmento a segmento (D-06)** - `6317698` (feat)
3. **Task 3: caso golden nomeado (PAYOFF-03), auditoria de PAYOFF-01, suíte canônica** - `0c0c27f` (test)

_TDD real em Task 1 e Task 2: testes escritos primeiro (8 para domínio, 7 para segmentos), confirmados falhando com `AttributeError: module 'app.opcoes_payoff' has no attribute '...'` (RED), só então implementados (GREEN). Task 3 não é TDD (`tdd` não declarado no frontmatter da task) — testes de auditoria escritos e confirmados verdes contra a implementação já entregue nas Tasks 1-2._

## Files Created/Modified

- `server/app/opcoes_payoff.py` — `dominio_da_curva(perfil, spot=None)` e `segmentos_da_curva(perfil)` inseridas entre `perfil_da_estrutura` e `_breakevens` (mesmo bloco, ao lado da função que consomem); nenhuma outra função tocada, nenhum import novo (`grep -n "^from\|^import"` continua só `__future__`/`typing`)
- `server/tests/test_opcoes_payoff.py` — Parte 4 (8 testes de domínio), Parte 5 (7 testes de segmentos), Parte 6 (2 testes: golden nomeado + auditoria de nome). 65 testes nomeados no total no arquivo (48 pré-existentes da 36-01 + 17 novos)

## Decisions Made

Nenhuma decisão de produto nova — a leitura do D-06 (segmentos cortam só nos strikes, boundary 49,17 não 49,42) já vinha travada em `36-CONTEXT.md` como corrigida-após-pattern-map antes desta execução começar; esta sessão confirmou a leitura contra o `<behavior>`/`<specifics>` do `36-02-PLAN.md` (idênticos entre si) antes do primeiro `Edit`, sem reabrir a pergunta.

Uma escolha de implementação dentro do espaço aberto pelo PLAN (Claude's Discretion, nomes exatos de campo/mensagens): mensagens de `motivo` em `dominio_da_curva` seguem o registro direto já usado no resto do módulo (`_delta_total`, guarda de vencimentos divergentes de `perfil_da_estrutura`).

## Deviations from Plan

None (Rule 1/2/3) — plano executado como escrito. Um achado de ambiente, não de produto, registrado abaixo (não é deviation de código).

## Issues Encountered

**`bash scripts/executar.sh --testes` não travou desta vez — falhou imediatamente dentro do sandbox** com `nice(5) failed: operation not permitted` (o wrapper chama `nice` para baixar prioridade do processo de teste, syscall negado pelo sandbox), saindo com exit 0 sem rodar nenhum teste — uma variação do mesmo achado ambiental já documentado em `STATE.md`/`36-01-SUMMARY.md` (sandbox nega uma syscall que o wrapper depende, em vez de travar em `lsof`/`ps`). Contorno aplicado conforme instruído no PLAN.md: suíte completa rodada `dangerouslyDisableSandbox: true`. Resultado fora do sandbox: **2960 pytest passed / 5 skipped / 3 xfailed / 0 failed** em 77,47s (baseline pós-36-01 documentada 2943 + exatamente os 17 testes novos desta onda — 8+7+2) e **154/154 `web/tests/*.mjs` OK** (idêntico à baseline da 36-01, incluindo `test_ios_assets.mjs` passando — `web/ios/` já existe neste worktree, diferente da observação de outras sessões onde estava ausente). `git diff --stat -- web/` mostra só `web/package-lock.json` (2 linhas, modificação PRÉ-EXISTENTE ao início desta sessão — confirmada no `git status` do system-reminder inicial da conversa, não tocada por nenhuma das 3 tasks desta onda). `git status --porcelain` não lista arquivo novo fora do já modificado `web/package-lock.json`.

## Prova negativa real (D-06, executada e registrada — não descrita)

1. **Injeção do defeito:** logo após `return segmentos` em `segmentos_da_curva`, inserido bloco temporário (comentado "NÃO COMMITAR") que corta cada segmento em cada ponto de `perfil["breakevens"]` contido nele.
2. **Rodada com o defeito:** `pytest tests/test_opcoes_payoff.py -q` → **3 failed, 60 passed**, nomeando exatamente os 3 testes que a leitura-só-nos-strikes protege:
   - `test_segmentos_golden_tres_segmentos_fronteira_nos_strikes_nao_no_breakeven` — diff mostrou `{'de': 49.17, 'ate': 49.42, ...}` no lugar de `{'de': 49.17, 'ate': 49.67, ...}`, com item extra sobrando (4 segmentos, não 3)
   - `test_segmentos_condor_cinco_segmentos_com_plato_central` — `assert len(segs) == 5` falhou com `7 == 5` (2 breakevens cortando 2 segmentos a mais)
   - `test_segmentos_straddle_dois_segmentos_apesar_de_dois_breakevens` — mesma classe de falha, segmento extra a partir do breakeven 48.0
   - Execução isolada do golden confirmou por impressão direta: **4 segmentos**, com a fronteira espúria exatamente em `49.42` (`{'de': 49.17, 'ate': 49.42, ...}` seguido de `{'de': 49.42, 'ate': 49.67, ...}`)
3. **Restauração:** bloco temporário removido, `return segmentos` volta a ser a última linha da função.
4. **Rodada de confirmação:** `pytest tests/test_opcoes_payoff.py -q` → **63 passed** (verde de novo, todos os testes até aquele ponto da execução, antes da Task 3 acrescentar mais 2).

## User Setup Required

None — módulo puro, sem configuração externa, sem env var, sem secret.

## Publicação (Task 3.4)

**Nada publicado nesta onda, por desenho.** Esta fase é backend puro, sem rota nova e sem consumidor de front — nenhum `bump.sh`, nenhum `publicar-web.sh`, nenhum push para `origin/main`. `SERVER_BUILD_ID`/`BUILD_ID` intocados. Publicação fica para a Fase 37, quando o gráfico/explicação consumirem `dominio_da_curva()`/`segmentos_da_curva()` de verdade.

## Next Phase Readiness

- `perfil_da_estrutura()` continua exatamente como a Fase 37 vai encontrar (nenhuma mudança nesta onda) mais dois dados novos prontos para consumo direto: `dominio_da_curva(perfil, spot)` (domínio do gráfico) e `segmentos_da_curva(perfil)` (uma frase por segmento, na ordem esquerda-para-direita).
- Fase 36 fecha com PAYOFF-01/02/03 cobertos: motor genérico sem lógica por nome (PAYOFF-01, provado por teste e auditoria), casos-limite (PAYOFF-02, coberto na 36-01), caso golden como regressão nomeada com as 5 propriedades mais segmentos (PAYOFF-03).
- Os 4 consumidores atuais (`opcoes_motor.py`, `opcoes_lastreadas.py`, `opcoes_curadoria.py`, `options_mcp_api.py`) seguem intocados — nenhum chama `dominio_da_curva`/`segmentos_da_curva` hoje; são funções novas, sem call site ainda, aguardando a Fase 37.

## Self-Check

FOUND: server/app/opcoes_payoff.py
FOUND: server/tests/test_opcoes_payoff.py
FOUND commit 31e7db7
FOUND commit 6317698
FOUND commit 0c0c27f

## Self-Check: PASSED

---
*Phase: 36-motor-de-payoff-gen-rico*
*Completed: 2026-09-21*
