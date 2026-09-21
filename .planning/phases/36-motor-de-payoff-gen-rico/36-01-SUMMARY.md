---
phase: 36-motor-de-payoff-gen-rico
plan: 01
subsystem: api
tags: [opcoes, payoff, motor-determinístico, pytest]

# Dependency graph
requires:
  - phase: 15
    provides: "opcoes_payoff.py original (perfil_da_estrutura, ENG-02) e os 4 consumidores (opcoes_motor/opcoes_lastreadas/opcoes_curadoria/options_mcp_api)"
provides:
  - "campo `vencimento` opcional por perna, opaco, com degradação honesta em vencimentos divergentes (D-03)"
  - "guarda de entrada degenerada (custo+curva+inclinação todos zero) recusada com ValueError (D-04.1)"
  - "_breakevens corrigido — não relata mais S=0 espúrio em CALL de prêmio zero, ratio spread de custo zero e box travado em zero (D-04.2)"
  - "20 testes nomeados novos travando D-03/D-04/PAYOFF-02 (48 no total no arquivo)"
affects: [37-grafico-de-payoff-e-explicacao-confiaveis, 36-02]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Guarda de divergência de entrada (D-03) roda ANTES da guarda de resultado degenerado (D-04.1) na mesma função — fato sobre a entrada precede fato sobre o resultado calculado"
    - "Campo opcional passthrough opaco (vencimento) segue o mesmo idiom de `delta`: nunca parseado, nunca validado, só comparado por igualdade"
    - "'Nulo sempre tem motivo' estendido a `vencimentos` (dict com divergentes/distintos/motivo, nunca ausente)"

key-files:
  created: []
  modified:
    - server/app/opcoes_payoff.py
    - server/tests/test_opcoes_payoff.py

key-decisions:
  - "D-03/D-04/D-07 implementados exatamente como travado em 36-CONTEXT.md; nenhuma decisão nova tomada nesta execução"
  - "Campo `vencimentos.distintos` reportado vazio no caminho não-divergente (mesmo quando ambas as pernas compartilham um vencimento explícito) — mantém o resultado byte-a-byte idêntico ao caso sem vencimento nenhum, exceto pelo campo `vencimentos` em si, que também fica idêntico; só o caminho divergente popula `distintos`"

requirements-completed: [PAYOFF-02]

# Metrics
duration: ~25min
completed: 2026-09-21
---

# Phase 36 Plan 01: Motor de Payoff — vencimento, entrada degenerada e S=0 espúrio Summary

**`opcoes_payoff.py` ganhou campo `vencimento` opcional por perna com degradação honesta em vencimentos divergentes (D-03), guarda de entrada degenerada (D-04.1) e correção do breakeven espúrio em S=0 que afetava CALL de prêmio zero, ratio spread de custo zero e box travado em zero (D-04.2), com 20 testes novos nomeados travando os casos-limite de PAYOFF-02.**

## Performance

- **Duration:** ~25 min (commits 19:22–19:28, mais leitura/planejamento antes)
- **Completed:** 2026-09-21
- **Tasks:** 3/3
- **Files modified:** 2 (`server/app/opcoes_payoff.py`, `server/tests/test_opcoes_payoff.py`) — nenhum arquivo novo (D-01)

## Accomplishments

- **D-03 (calendário/diagonal):** `_validar_perna` aceita `vencimento` opcional, passthrough opaco (nunca parseado, nunca comparado ao relógio). `perfil_da_estrutura` detecta vencimentos divergentes entre pernas (valores não-`None` distintos, ordem de primeira aparição) e devolve estado explícito — `vencimentos.divergentes=True`, `motivo` citando "vencimentos diferentes", `curva=[]`, `breakevens=[]`, `ganho_maximo`/`perda_maxima`=`None`, sem aproximar linearmente. Estruturas sem vencimento ou com o mesmo vencimento em todas as pernas calculam idêntico a antes.
- **D-04.1 (entrada degenerada):** guarda de três condições obrigatórias (`custo==0` E curva inteira em zero E `inclinacao_direita==0`) recusa com `ValueError("estrutura sem exposição: ...")`. Confirmado que box travado em zero (custo≠0) e ratio spread de custo zero (curva não é toda zero) continuam aceitos — a guarda de duas condições teria recusado o box por engano.
- **D-04.2 (`_breakevens` bugfix):** um ponto de resultado zero só conta como breakeven quando a curva sai do zero (`y1 != 0`); a cauda só soma o último strike quando `inclinacao_direita != 0`. Corrige `CALL comprada premio 0` (breakevens `[0.0, 50.0]` → `[50.0]`), ratio 1x2 (`[0.0, 50.0, 60.0]` → `[50.0, 60.0]`) e box travado em zero (`[0.0, 50.0, 55.0]` → `[]`), sem alterar nenhum breakeven legítimo (venda coberta `[28.5]`, call seca `[42.0]`, borboleta `[46.5, 53.5]`, condor `[47.0, 58.0]`, straddle `[48.0, 52.0]`).
- **D-07 (cobertura de PAYOFF-02):** 8 testes nomeados novos na "Parte 3" cobrindo trava de alta com calls (caso golden), trava de baixa com puts, straddle/strangle, borboleta/condor (platô central provado ponto a ponto), box de resultado constante não-zero (distinto do degenerado), quantidades assimétricas — com cabeçalho mapeando todo o checklist de PAYOFF-02 a um teste (nomeado nesta fase ou pré-existente citado).

## Task Commits

Each task was committed atomically:

1. **Task 1: `vencimento` por perna e degradação honesta de calendário/diagonal (D-03)** - `30e6d1c` (feat)
2. **Task 2: recusar entrada degenerada e parar de inventar breakeven em S=0 (D-04)** - `736a2ce` (fix)
3. **Task 3: travar em teste os casos-limite de PAYOFF-02 e rodar a suíte canônica** - `0fbc52d` (test)

_TDD real em Task 1 e Task 2: testes escritos primeiro, confirmados falhando (RED), só então implementados (GREEN). Task 3 não é TDD (`tdd` não declarado no frontmatter da task) — testes escritos e confirmados verdes contra a implementação já entregue nas Tasks 1-2._

## Files Created/Modified

- `server/app/opcoes_payoff.py` — campo `vencimento` em `_validar_perna`; `perfil_da_estrutura` refatorada com `pernas_out`/`fluxo` extraídos, guarda de divergência de vencimento, guarda de entrada degenerada, chave `vencimentos` nos dois retornos; `_breakevens` com as duas condições corrigidas (loop e cauda), docstring atualizado
- `server/tests/test_opcoes_payoff.py` — 20 testes novos (Parte 2b: 6 para D-03; Parte 2c: 6 para D-04; Parte 3: 8 para D-07/PAYOFF-02), 48 testes nomeados no total

## Decisions Made

Nenhuma decisão de produto nova — toda a implementação seguiu D-01 a D-07 de `36-CONTEXT.md` e os analogs de `36-PATTERNS.md` ao pé da letra. Uma escolha de implementação (Claude's Discretion, dentro do espaço que o CONTEXT.md deixou aberto): `vencimentos.distintos` fica vazio (`[]`) no caminho não-divergente mesmo quando há um vencimento único compartilhado por todas as pernas — só é populado quando há divergência de fato. Isso é o que torna a estrutura "mesmo vencimento nas duas pernas" byte-a-byte idêntica à mesma estrutura sem vencimento nenhum (comportamento exigido pelo `<behavior>` da Task 1), incluindo o campo `vencimentos` em si.

## Deviations from Plan

None (Rule 1/2/3) — plano executado como escrito, sem bug a corrigir, sem funcionalidade crítica faltando, sem bloqueio. Uma observação de acurácia do próprio PLAN.md, sem impacto:

**Contagem de testes pré-existentes divergiu da declarada no PLAN.md.** O bloco `<interfaces>` do plano afirmava "25 testes existentes" (medido em sessão de planejamento anterior); a contagem real no HEAD antes desta execução era 28 (`git show HEAD:server/tests/test_opcoes_payoff.py | grep -c "^def test_"` → 28). Não muda nenhum critério de aceite — os critérios pedem "os testes antigos intactos + N novos", que está satisfeito (28+6=34 após Task 1, 34+6=40 após Task 2, 40+8=48 após Task 3). Não é um deviation de código, só uma nota para quem for reconferir números do PLAN.md contra o repositório.

## Issues Encountered

**Erro de sequenciamento próprio, corrigido antes de qualquer commit.** Na primeira tentativa de implementar a Task 1, escrevi num único `Edit` tanto a guarda de vencimento divergente (D-03, Task 1) quanto a guarda de entrada degenerada (D-04.1, Task 2) na mesma função — quebrando a exigência de commit atômico por task. Revertido com `git checkout -- server/app/opcoes_payoff.py` (arquivo único, não histórico) antes de qualquer commit ter sido feito, e reimplementado em duas passadas TDD separadas (Task 1 primeiro, testes RED→GREEN→commit; Task 2 depois, mesmo ciclo). Nenhum código ou teste chegou a ser commitado na ordem errada.

**`bash scripts/executar.sh --testes` travou neste host**, confirmando o achado ambiental já documentado em `STATE.md` (Fase 35): `ps`/`lsof` bloqueados pelo sandbox do host fazem o wrapper pendurar (o pytest chegou a rodar e mostrar progresso — 2%, 4%, 7%, 9%… — antes de travar). Contorno aplicado conforme instruído no PLAN.md: as duas suítes rodadas manualmente, fora do sandbox (`dangerouslyDisableSandbox: true`, necessário porque testes de rede/subprocesso do backend davam 27 falsas-falhas dentro do sandbox — mesmo padrão "sandbox mente" já registrado na memória do projeto). Resultado fora do sandbox: **pytest 2943 passed/5 skipped/3 xfailed/0 failed** em 78,6s (baseline documentada 2923 + exatamente os 20 testes novos desta onda) e **154/154 `web/tests/*.mjs` passando** (replicando a invocação `node "${t#web/}"` do próprio `executar.sh`, arquivo por arquivo). `git diff --stat -- web/` para esta onda é vazio (o único item em `web/` é `web/package-lock.json`, já modificado antes desta sessão começar, não tocado por nenhuma das 3 tasks).

## Prova negativa real (D-04.2, executada e registrada — não descrita)

1. **Reversão:** condição `if y0 == 0 and y1 != 0:` revertida para `if y0 == 0:` (só essa linha, à mão).
2. **Rodada com o defeito reintroduzido:** `pytest tests/test_opcoes_payoff.py -q` → **3 failed, 37 passed**, nomeando exatamente os 3 casos que a correção protege:
   - `test_perfil_call_premio_zero_nao_e_degenerada_breakeven_so_no_strike` — `assert [0.0, 50.0] == [50.0]` falhou (0.0 espúrio reapareceu)
   - `test_perfil_box_travado_em_zero_custo_nao_zero_nao_e_degenerada_sem_breakevens` — `assert [0.0, 50.0] == []` falhou
   - `test_perfil_ratio_1x2_custo_zero_breakevens_sem_zero_espurio` — `assert [0.0, 50.0, 60.0] == [50.0, 60.0]` falhou
3. **Restauração:** condição devolvida a `if y0 == 0 and y1 != 0:`.
4. **Rodada de confirmação:** `pytest tests/test_opcoes_payoff.py -q` → **40 passed** (verde de novo, todos os 40 testes existentes até aquele ponto da execução).

## User Setup Required

None — módulo puro, sem configuração externa, sem env var, sem secret.

## Next Phase Readiness

- `perfil_da_estrutura()` agora aceita `vencimento` por perna, degrada com honestidade em calendário/diagonal, recusa entrada sem exposição, e `_breakevens` não inventa mais cruzamento espúrio em `S=0` — base pronta para a Fase 37 (gráfico + explicação) consumir sem herdar o defeito.
- Este plano (36-01) **não implementa D-05 (domínio X/Y) nem D-06 (segmentos)** — ambos ficam para 36-02 (`36-PATTERNS.md` já sinalizou uma ambiguidade real não resolvida em D-06: se os segmentos quebram só nos strikes ou também em cada breakeven; o exemplo literal de `36-CONTEXT.md` não sobrevive à verificação aritmética direta e precisa de confirmação do Alex antes de codificar).
- Os 4 consumidores (`opcoes_motor.py`, `opcoes_lastreadas.py`, `opcoes_curadoria.py`, `options_mcp_api.py`) seguem funcionando sem nenhuma linha alterada — nenhum passa `vencimento` hoje, confirmado por `grep` e pela suíte `-k "opcoes"` (560 passed, 1 skipped).

## Self-Check

FOUND: server/app/opcoes_payoff.py
FOUND: server/tests/test_opcoes_payoff.py
FOUND commit 30e6d1c
FOUND commit 736a2ce
FOUND commit 0fbc52d

## Self-Check: PASSED

---
*Phase: 36-motor-de-payoff-gen-rico*
*Completed: 2026-09-21*
