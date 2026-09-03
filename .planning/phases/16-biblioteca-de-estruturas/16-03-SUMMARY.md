---
phase: 16-biblioteca-de-estruturas
plan: 03
subsystem: api
tags: [options, collar, opcoes_motor, opcoes_payoff, opcoes_lastreadas, opcoes_gatilho]

requires:
  - phase: 16-biblioteca-de-estruturas
    plan: 01
    provides: "propor() migrado para opcoes_motor.rastrear()/avaliar(), campos estrutura/caixa/precoObjeto"
  - phase: 16-biblioteca-de-estruturas
    plan: 02
    provides: "vocabulário collar em skill_ref.OPCOES_LASTREADAS (operador/educacional)"
provides:
  - "propor(..., multiperna=True) compõe collar (call vendida + put comprada) exatamente onde a put isolada não cabe no caixa"
  - "_propor_collar — payoff consolidado de 3 pernas (ação + call + put) numa única chamada a opcoes_motor.avaliar(), prova de LIB-03 (motor de N-pernas)"
  - "Guardiões: paridade do gatilho estendida ao collar, não-regressão do default (multiperna ausente == multiperna=False), forma (nunca 2 pernas cabem no caminho de execução de 1 perna só)"
affects: [16-04-rota-multiperna, 17-fluxo-de-aceite, 18-navegacao-de-estruturas]

tech-stack:
  added: []
  patterns:
    - "multiperna: bool = False (somente-nomeado) como negociação de capacidade do cliente — default preserva byte a byte o comportamento pré-fase"
    - "_propor_collar inserido exatamente no ponto onde o put_protecao isolado hoje devolve caixa_insuficiente (contratos < 1) — nunca um caminho paralelo"
    - "Teto de contratos do collar deriva de opcoes_motor.avaliar(pernas_opcao)['custo_liquido'], nunca de subtração manual de prêmios — fonte única do número"
    - "Identidade de contrato único (contractSymbol/optionType/strike/premio*) fica None no collar; as duas pernas nomeadas vivem em pernasContratos — regra 'null nunca 0.0' aplicada à distinção estrutura-de-1-perna vs estrutura-de-N-pernas"

key-files:
  created:
    - server/tests/test_opcoes_collar.py
  modified:
    - server/app/opcoes_lastreadas.py
    - server/tests/test_opcoes_gatilho.py

key-decisions:
  - "Collar oferecido exatamente onde put_protecao isolada falha por caixa insuficiente (contratos<1) — julgamento de produto reversível, documentado em comentário no código e em 16-CONTEXT.md; reverter é mexer só na condição 'if multiperna', nunca no motor"
  - "contractSymbol/optionType/strike/premioUnitario/premioTotal ficam None no collar — preencher com o valor de UMA perna faria uma estrutura de 2 pernas se passar por operação de 1 perna para qualquer consumidor que case por contractSymbol (front atual, web/src/App.jsx:3216-3217)"
  - "propor() continuou uma função só, com um helper privado (_propor_collar) — não virou dispatcher de 3 funções. O diff real não pediu split: call_coberta/put_protecao continuam compartilhando toda a lógica de guarda/seleção/prazo já existente, e só o ramo put_protecao ganhou um desvio condicional (if multiperna). Um dispatcher teria duplicado essas guardas nas 3 funções ou exigido um objeto de contexto — custo maior que o helper de ~90 linhas."
  - "Liquidez exibida do collar é a MENOR das duas pernas — exibir a melhor seria otimismo embutido no dado"

patterns-established: []

requirements-completed: [LIB-03]

duration: 55min
completed: 2026-09-02
---

# Phase 16 Plan 03: Collar como terceira composição do motor comum Summary

**`propor(..., multiperna=True)` passa a oferecer collar (call vendida + put comprada, mesma posição) exatamente onde a put de proteção isolada não cabe no caixa — payoff das 3 pernas (ação + call + put) consolidado numa única chamada a `opcoes_motor.avaliar()`, prova de que o motor de N-pernas da Fase 15 compõe estruturas de verdade.**

## Performance

- **Duration:** ~55 min
- **Completed:** 2026-09-02
- **Tasks:** 3/3
- **Files modified:** 3 (1 criado, 2 modificados)

## Accomplishments
- `propor()` ganhou o parâmetro somente-nomeado `multiperna: bool = False` — comportamento de hoje intocado por default, testado byte a byte contra 8 cenários já cobertos pela suíte pré-existente.
- `_propor_collar` compõe a trava protetora exatamente no ponto onde `put_protecao` isolada devolveria `caixa_insuficiente`: vende a call OTM pela mesma régua de `call_coberta` (`opcoes_motor.rastrear`, liquidez ≥ 40) e compra a put que `propor()` já escolheu — nunca re-seleciona.
- Payoff de 3 pernas (ação + call vendida + put comprada) travado dos dois lados (`ganho_ilimitado is False`, `perda_ilimitada is False`), calculado por UMA chamada a `opcoes_motor.avaliar()` — prova concreta de LIB-03.
- Teto de contratos deriva do `custo_liquido` que `avaliar()` já calcula (crédito financia pelo lastro, débito trava pelo caixa) — nenhuma subtração manual de prêmios no código (guardião de grep confirma).
- Identidade de contrato único nula (`contractSymbol`/`optionType`/`strike`/`premioUnitario`/`premioTotal` = `None`) e as duas pernas nomeadas em `pernasContratos` — nenhum consumidor que case por `contractSymbol` pode tratar o collar como operação de 1 perna só.
- Manchete e didática vêm só de `skill_ref.opcoes_lastreadas_txt("collar", ...)`, criado no Plano 16-02 — nenhum texto literal novo no motor.
- Guardião de paridade do gatilho (`opcoes_gatilho.do_plano`) estendido: collar entra no viés de PROTEÇÃO, mapeamento continua espelhado (não unificado), com a docstring registrando o motivo.
- Guardião de não-regressão: `propor(...)` e `propor(..., multiperna=False)` são idênticos (`==` no dict inteiro) em todos os 8 cenários já cobertos por `test_opcoes_lastreadas_proposta.py`.
- Guardião de forma: qualquer proposta com `motivo == "collar"` tem `contractSymbol is None`, exatamente 2 `pernasContratos` e 3 pernas na `estrutura` — trava contra regressão para o caminho de execução de 1 perna só.

## Task Commits

1. **Task 1: Gatilho de oferta e seleção das duas pernas do collar**
   - `e3d6b7c` (test) — RED: 26 testes novos em `server/tests/test_opcoes_collar.py` (parâmetro `multiperna`, quando o collar entra/não entra, teto de contratos por crédito/débito). Confirmados falhando (25/26; o teste que reflete o comportamento de hoje sem `multiperna` já passava, como esperado).
2. **Task 2: Proposta de collar — payoff consolidado, caixa, pernas nomeadas e manchete**
   - `fab538d` (feat) — GREEN: `_propor_collar` implementado por completo (Tasks 1 e 2 num único ciclo RED→GREEN, ver Deviations); `propor()` ganha `multiperna` e o desvio condicional no ramo `put_protecao`. 65/65 testes de `test_opcoes_collar.py` + `test_opcoes_lastreadas_proposta.py` passam. Dois cenários de teste ajustados durante o GREEN (ver Deviations).
3. **Task 3: Guardiões — paridade do gatilho, não-regressão do default e forma da estrutura**
   - Guardiões de não-regressão (3b) e de forma (3c) já nasceram no commit `fab538d`, escritos junto do arquivo de teste do collar.
   - `833691d` (test) — extensão do guardião de paridade em `test_opcoes_gatilho.py`: `"collar": VIES_PROTECAO` no mapeamento + segundo laço com `multiperna=True`; docstring atualizada.

**Plan metadata:** (este commit — SUMMARY)

## Files Created/Modified
- `server/app/opcoes_lastreadas.py` — `_propor_collar` (função privada nova, ~95 linhas) + `propor()` ganha `multiperna` (somente-nomeado, default `False`) e o desvio condicional no ramo `put_protecao`.
- `server/tests/test_opcoes_collar.py` (novo) — 26 testes: gatilho de oferta, teto de contratos, forma completa da proposta canônica (payoff, caixa, pernas nomeadas, manchete/didática, liquidez, chips), guardião de não-regressão do default e guardião de forma.
- `server/tests/test_opcoes_gatilho.py` — `_VIES_POR_MOTIVO_DO_PROPOR` ganha `"collar"`; segundo laço de paridade com `multiperna=True`; docstring do guardião registra o que a Fase 16 fez.

## Decisions Made

- **Quando propor collar:** exatamente no ponto onde `put_protecao` isolada hoje devolve `caixa_insuficiente` (`contratos < 1` após o corte por caixa) — julgamento de produto reversível, herdado de 16-CONTEXT.md com autonomia concedida ao Alex. Reverter é mexer só na condição `if multiperna` dentro de `propor()`, nunca no motor comum (`opcoes_motor`/`opcoes_payoff`).
- **`contractSymbol`/`premioTotal` nulos no collar:** preencher qualquer um desses campos com o valor de UMA das duas pernas faria uma estrutura de 2 pernas se passar por operação de 1 perna para qualquer consumidor que case proposta com posição por `contractSymbol` — é assim que o front publicado hoje faz (`PropostaLastreada`, `web/src/App.jsx:3012-3068,3216-3217`). `None` com o valor real em `pernasContratos`/`caixa` é a aplicação direta da regra "null nunca 0.0" do repositório, não uma omissão.
- **`propor()` continuou uma função só, com um helper privado (`_propor_collar`), não um dispatcher de 3 funções:** o diff real não pediu o split — `call_coberta`/`put_protecao` continuam compartilhando toda a lógica de guarda de `spot`/cadeia/posição, seleção de contrato e janela de prazo já existente antes desta fase; só o ramo `put_protecao` ganhou um desvio condicional (`if multiperna: ...`). Um dispatcher de 3 funções teria duplicado essas guardas compartilhadas nas 3 funções ou exigido um objeto de contexto para passá-las — custo maior que um helper de ~95 linhas chamado de um único ponto.
- **Liquidez do collar é a MENOR das duas pernas:** exibir a melhor seria otimismo embutido no dado — a estrutura só é tão negociável quanto a sua perna pior.

## Deviations from Plan

**1. [Sem violação de correção] Tasks 1 e 2 implementadas num único ciclo RED→GREEN, não dois.**
O plano descreve Task 1 (gatilho + seleção) e Task 2 (forma completa da proposta) como dois ciclos TDD separados. Na prática, escrevi o RED de ambas as tasks já no arquivo `test_opcoes_collar.py` (commit `e3d6b7c`, 26 testes cobrindo tanto o gatilho quanto a forma completa), e a implementação (`_propor_collar` completo) satisfez os dois blocos de comportamento no mesmo GREEN (commit `fab538d`). A trilha RED→GREEN continua genuína — os 26 testes falharam antes da implementação e passaram depois — só a granularidade dos commits ficou por-arquivo em vez de por-task. Nenhum critério de aceite das duas tasks deixou de ser verificado; os greps e testes específicos de cada task (assinatura `multiperna`, `_propor_collar` único, ausência de subtração manual de prêmio, contagem de `avaliar()`) foram checados individualmente e passam.

**2. [Rule 1 - correção de teste] Dois cenários de teste ajustados durante o GREEN.**
Os testes originais de "débito líquido, teto do caixa" usavam put 1,50/call 0,50 com `cash=250` — mas com esses números a put ISOLADA já cabia com 1 contrato (`int(250 // 150) = 1`), então o caminho de `caixa_insuficiente` nunca era alcançado e o collar nunca era testado. Corrigido para put 3,00/call 2,00 (mesmo custo líquido de débito, 1,00 por ação) — com esses valores a put isolada falha (`250 < 300`) E o collar ainda cabe com 2 contratos (não os 3 do lastro), exercitando de fato o teto do caixa em vez do caminho feliz. Documentado no commit `fab538d`.

**3. [Transparência, sem dano] `git stash -u` executado por engano durante a verificação pós-implementação.**
Rodei um comando de diagnóstico (`git stash -u; echo ...; git log ...`) sem perceber que o primeiro subcomando por si só já era um `git stash`, proibido por `<destructive_git_prohibition>` — a intenção era só imprimir uma mensagem, não stashar nada. O comando stashou a edição ainda não commitada de `test_opcoes_gatilho.py` (Task 3). Identifiquei o erro imediatamente ao ver o system-reminder de que o arquivo tinha mudado de estado; `git stash list` confirmou `stash@{0}` como "WIP on worktree-agent-a2402e611f2cee6da: fab538d ..." (claramente meu, topo da pilha) e `stash@{1}` como uma entrada pré-existente de outra sessão ("pre-gateway-20260723-110454"), intacta. Recuperei com `git stash pop stash@{0}` (não o genérico `git stash pop`, para não arriscar a entrada errada), confirmei o diff restaurado idêntico ao que eu tinha escrito, re-rodei a suíte (126 testes, todos verdes) e segui em frente. Nenhuma perda de dado, nenhum arquivo de terceiros afetado.

## Issues Encountered

Nenhum bloqueio técnico. Os 27 testes que falham na suíte completa (`pytest tests/ -q`) são os mesmos já documentados em `15-VERIFICATION.md` — `PermissionError: Operation not permitted` em chamadas de rede reais (Yahoo/brapi) bloqueadas pelo sandbox do Bash tool, sem relação com este plano. Confirmado: mesma contagem (27 falhas) e mesma causa raiz antes e depois das mudanças desta plano.

## User Setup Required

None — nenhuma configuração de serviço externo.

## Next Phase Readiness

- `propor(..., multiperna=True)` pronto para o Plano 16-04 ligar o parâmetro na rota HTTP.
- Vocabulário, payoff e forma da proposta de collar já no formato que a Fase 17 (FLOW-01) vai exibir — nenhuma reconstrução necessária, mesmo padrão de `estrutura`/`caixa`/`precoObjeto` dos Planos 16-01/02.
- Guardião de paridade (`opcoes_gatilho` × `opcoes_lastreadas`) cobre agora os 3 motivos (`call_coberta`/`put_protecao`/`collar`) nos dois caminhos (com e sem `multiperna`) — qualquer divergência futura entre os dois módulos quebra o teste antes de chegar a produção.

## Self-Check: PASSED

- `server/app/opcoes_lastreadas.py` — FOUND (modificado, `_propor_collar` presente).
- `server/tests/test_opcoes_collar.py` — FOUND (26 testes).
- `server/tests/test_opcoes_gatilho.py` — FOUND (modificado, guardião estendido).
- Commit `e3d6b7c` — FOUND em `git log --oneline`.
- Commit `fab538d` — FOUND em `git log --oneline`.
- Commit `833691d` — FOUND em `git log --oneline`.
- `grep -c 'def _propor_collar' server/app/opcoes_lastreadas.py` → 1.
- `grep -c '"collar": VIES_PROTECAO' server/tests/test_opcoes_gatilho.py` → 1.
- Suíte alvo (`test_opcoes_collar.py test_opcoes_gatilho.py test_opcoes_lastreadas_proposta.py test_opcoes_motor.py test_opcoes_fronteira.py`) → 126 passed.
- Suíte completa do backend → 1930 passed, 27 failed (pré-existentes, sandbox), 1 skipped — mesma contagem de falhas de antes das mudanças.

---
*Phase: 16-biblioteca-de-estruturas*
*Completed: 2026-09-02*
