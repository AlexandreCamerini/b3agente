---
phase: 37-gr-fico-de-payoff-e-explica-o-confi-veis
plan: 03
subsystem: api
tags: [fastapi, options-mcp, valor-de-mercado, payoff]

# Dependency graph
requires:
  - phase: 37-01
    provides: "_perfil_para_curva()/_dominio_e_segmentos() e dominio/segmentos anexados a proposta()/possibilidades() em options_mcp_api.py"
provides:
  - "_valor_hoje() — busca prêmio ATUAL de cada perna via get_option_chain, soma sinal×quantidade×prêmio"
  - "valorHoje no envelope de POST /api/options/mcp/proposta (sempre, com 1 estrutura + lote) e POST /api/options/mcp/possibilidades (só candidato de índice 0)"
  - "chamadasPrevistas corrigido para refletir o custo real (2×N+2 com candidato; 2×N+1 sem nenhum vencimento)"
affects: [37-04, 37-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Reserva de cap ANINHADA (with _cap_check aninhado) para uma busca opcional dentro de uma rota que já reservou cap — mesmo padrão de D-24.1"
    - "Reuso de _erro_http(e).detail para produzir o MESMO shape de erro num caminho que NÃO levanta HTTPException (falha isolada que não pode abortar a rota)"

key-files:
  created: []
  modified:
    - server/app/options_mcp_api.py
    - server/tests/test_options_mcp_api.py

key-decisions:
  - "_valor_hoje() nunca levanta — reusa _erro_http(e).detail para montar {erro: ...} no mesmo shape que o front (ErroDoMcp) já interpreta, em vez de inventar um segundo formato de erro"
  - "chamadasPrevistas usa 2×len(escolhidos)+(2 se houver candidato, senão +1) — quando escolhidos está vazio não existe índice 0 a tentar, e afirmar +2 aí previa uma chamada IMPOSSÍVEL (não incerta como o resto do fan-out), desvio de Rule 1 do texto literal do plano (que pedia +2 incondicional)"

patterns-established:
  - "Falha de uma busca OPCIONAL dentro de uma rota MCP nunca aborta o envelope inteiro — grava {erro:...} no campo específico, preserva o resto"

requirements-completed: [CHART-05]

# Metrics
duration: ~20min
completed: 2026-09-22
---

# Phase 37 Plan 03: valorHoje (valor de mercado atual) em proposta()/possibilidades() Summary

**`_valor_hoje()` soma o prêmio ATUAL de cada perna via `get_option_chain` (sinal×quantidade×prêmio), anexado como `valorHoje` no envelope de `proposta()` (sempre) e `possibilidades()` (só o candidato de índice 0), corrigindo a regressão de produção onde "hoje" e "no vencimento" se confundiam no mesmo número.**

## Performance

- **Duration:** ~20 min (commits entre 23:39 e 23:53 -03:00)
- **Tasks:** 2 (+ 1 correção de aresta descoberta durante a Task 2)
- **Files modified:** 2

## Accomplishments
- `_valor_hoje()` (nova, em `options_mcp_api.py`) busca `get_option_chain`, indexa por `contrato`, soma `sinal(buy=+1/sell=-1) × quantidade × prêmio_atual` por perna; contrato ausente da cadeia devolve erro explícito (`valor_hoje_incompleto`), nunca soma parcial calada
- `proposta()`: `valorHoje` sempre tentado quando há exatamente 1 estrutura E lote informado (mesma régua de ambiguidade de `emReais`/`dominio`)
- `possibilidades()`: `valorHoje` só tentado no candidato de índice 0 (`enumerate(escolhidos)`) — demais itens NÃO recebem a chave (estado "não tentado", distinto de "tentado e falhou")
- `chamadasPrevistas` atualizado para refletir o custo real da chamada extra

## Task Commits

1. **Task 1: `_valor_hoje()` + wiring em `proposta()`/`possibilidades()`** - `d4307ed` (feat)
2. **Task 2: testes de `valor_hoje` — sucesso, contrato ausente, falha do serviço, gate do 1º candidato** - `a1ff6ca` (test) — inclui o fix de Rule 1 do `chamadasPrevistas` na mesma commit (achado ao rodar a suíte pós-Task 1)
3. **Correção de aresta pós-revisão** - `c26f0c4` (test) — teste adicional travando o caso "índice 0 sem estrutura" (achado do `advisor`, verificado por leitura antes de escrever o teste)

_Nenhum plano metadata commit ainda — este é feito pelo orquestrador ao consolidar a onda._

## Files Created/Modified
- `server/app/options_mcp_api.py` - `_valor_hoje()` nova; `proposta()`/`possibilidades()` ganham `valorHoje` no envelope; fórmula de `chamadasPrevistas` corrigida
- `server/tests/test_options_mcp_api.py` - 5 testes novos de `valor_hoje` (soma por sinal, contrato ausente, serviço indisponível, gate do 1º candidato, índice 0 sem estrutura); `_roteador()` ganha parâmetro `cadeia`; 6 testes pré-existentes atualizados para o novo custo de chamadas

## Decisions Made
- `_valor_hoje()` recebe a `_Reserva` já aberta pelo chamador (mesmo padrão de `_chamada_com_cap` no resto do arquivo) — não abre seu próprio `with _cap_check`
- Falha do `get_option_chain` dentro de `_valor_hoje()` NUNCA propaga: `{"erro": _erro_http(e).detail}` reusa a tradução de erro existente em vez de duplicar shape
- `emReais` de `valorHoje` fica `None` dentro de `_valor_hoje()` — quem multiplica pelo lote é o chamador (`_vezes_lote`), mesma disciplina "lote multiplica fora" de `_em_reais`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `chamadasPrevistas` afirmava uma chamada impossível quando não havia vencimento nenhum**
- **Found during:** Task 2, ao rodar a suíte completa do arquivo (`test_sem_vencimento_aberto_e_200_sem_segunda_etapa` continuou passando, mas só porque a fórmula literal do plano (`2×len(escolhidos)+2` incondicional) coincidia por acaso de ainda precisar de ajuste nos outros 5 testes — a leitura do caso `escolhidos=[]` mostrou que `+2` ali afirmaria uma chamada de `get_option_chain` que **não pode acontecer**, porque não existe candidato de índice 0 quando não há vencimento nenhum)
- **Issue:** o texto do plano (linha ~168-171 do `37-03-PLAN.md`) pedia a troca incondicional de `+1` para `+2`; aplicado ao pé da letra, o caso `escolhidos=[]` (rota `test_sem_vencimento_aberto_e_200_sem_segunda_etapa`) passaria a anunciar `chamadasPrevistas=2`, com a chamada real permanecendo em 1 — não é "previsão de pior caso" (aceito em todo o resto do arquivo, com precedente explícito em `test_vencimento_que_nao_monta_nao_gasta_a_avaliacao`), é afirmar algo estruturalmente impossível
- **Fix:** `"chamadasPrevistas": 2 * len(escolhidos) + (2 if escolhidos else 1)` — sem candidato nenhum, `+1` (só a chamada base); com pelo menos um candidato, `+2` (base + valor de hoje do índice 0, mesmo que ele acabe falhando em montar estrutura)
- **Files modified:** `server/app/options_mcp_api.py`
- **Verification:** `test_sem_vencimento_aberto_e_200_sem_segunda_etapa` passa SEM alteração (chamadasPrevistas continua 1, batendo com a chamada real); os demais 5 testes de custo atualizados para `+2`
- **Committed in:** `a1ff6ca` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug de previsão em edge case não coberto pelo texto literal do plano)
**Impact on plan:** Correção estritamente mais precisa que o texto literal do plano; nenhum teste do plano original precisou ser reescrito para acomodar o desvio (o caso afetado, ao contrário, ficou SEM mudança).

## Issues Encountered
- A aplicação da Task 1 quebrou 6 testes pré-existentes do arquivo (custo de chamadas mudou de `2×N+1` para `2×N+2`) — esperado e coberto pelo próprio Task 2 do plano; todos corrigidos e verificados individualmente antes de escrever os testes novos, não só re-executados até passar
- `advisor`, chamado antes deste SUMMARY, apontou 3 pontos de verificação não cobertos pela suíte verde: (1) `_erro_http(e).detail` nunca lança para nenhum subtipo de `McpErro`/`ValueError` que `_valor_hoje` captura — confirmado por leitura de `McpTetoAtingido.__init__`/`McpErroDeTool.__init__` (atributos sempre inicializados com default, nunca `AttributeError`); (2) `_lote(None)` em `possibilidades()` já levanta 422 ANTES do meu código rodar (linha pré-existente, `lote` nunca chega `None` na minha chamada de `_vezes_lote`) — comportamento herdado, não tocado; (3) índice 0 sem estrutura — trace confirmou que o `continue` do ramo `[R-15]` roda antes do bloco de `valorHoje`, e um teste novo (`test_possibilidades_indice_0_sem_estrutura_tambem_nao_recebe_a_chave`) travou isso explicitamente em vez de deixar só como leitura de código

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Backend do CHART-05 fechado: `valorHoje` está no envelope dos dois endpoints, pronto para o 37-04 (frontend `PayoffChart.jsx`) e o 37-05 (wiring + checkpoint humano) consumirem
- Suíte canônica completa verde fora do sandbox: 2973 pytest passed / 5 skipped / 3 xfailed + 156/156 `.mjs`, exit 0
- Nenhum código de front tocado nesta plan — a UI ainda não lê `valorHoje` (é o 37-05, conforme o CONTEXT.md)

---
*Phase: 37-gr-fico-de-payoff-e-explica-o-confi-veis*
*Completed: 2026-09-22*
