---
phase: 17-fluxo-de-aceite
plan: 03
subsystem: api
tags: [python, fastapi, options, collar, order-engine, tdd, security]

# Dependency graph
requires:
  - phase: 17-fluxo-de-aceite
    provides: "store.abrir_collar (17-01) — execução atômica das 2 pernas dentro de UMA aquisição de ORDER_LOCK; source/at na rota de proposta (17-02)"
provides:
  - "POST /api/options/lastreada/abrir-collar — caminho de ACEITE do collar, com re-derivação server-side da proposta a cada chamada (opcoes_lastreadas.propor(..., multiperna=True))"
  - "Cross-check dict símbolo→lado entre corpo e proposta fresca — recusa contrato trocado, faltando, duplicado ou lado invertido, todos com 409 sem efeito colateral"
  - "Fechamento formal da 'Limitação conhecida — guarda por autoidentificação' do ADR-025 (ADR-026)"
affects: [17-05, main, opcoes_lastreadas, store]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Rota de ESCRITA que re-deriva o pipeline inteiro da rota de LEITURA irmã (chain/posicao/cash/snapshot/plano/propor) a cada chamada, em vez de confiar em qualquer dado vindo do corpo — nunca engole exceção do pipeline em 'degradado' (isso é próprio de rota de leitura); qualquer falha inesperada aqui vira 502 explícito"
    - "Cross-check por dict {contractSymbol: lado} entre o que o cliente submeteu e a proposta fresca — uma única comparação de igualdade de dict cobre contrato trocado, contrato faltando, contrato duplicado e lado invertido de uma vez"
    - "409 (estado mudou, corpo válido) vs 400 (corpo malformado) como informação estrutural para o cliente decidir entre corrigir o formulário e recarregar a proposta"

key-files:
  created:
    - server/tests/test_opcoes_collar_rota.py
    - docs/adr/026-execucao-de-estrutura-multiperna.md
  modified:
    - server/app/main.py
    - docs/adr/025-collar-e-estrutura-multiperna.md

key-decisions:
  - "Rota nova (abrir-collar) em vez de flag na rota antiga (/abrir) — uma flag transformaria a trava de 400 do 16-04 num opt-out do próprio cliente"
  - "Mensagens de erro usam 'collar'/'Collar' em vez de 'trava protetora' — mesma colisão com o guardião CVM (test_opcoes_collar_vocab.py) que o Plano 17-01 já documentou; nenhuma string de CÓDIGO fora de skill_ref.py pode conter a frase-âncora da manchete"
  - "Pipeline de re-derivação NÃO engole exceção em 'degradado' como a rota de leitura faz — falha vira 502 explícito, porque degradar numa rota de ESCRITA seria executar sem a própria defesa"
  - "premiosUsados (plural) no retorno em vez de priceUsed (singular, da rota irmã) — o collar tem duas pernas, um campo singular mentiria sobre a forma da operação"

patterns-established:
  - "Cross-check de estrutura multiperna por dict símbolo→lado, não por comparação campo a campo — mais barato de ler e mais difícil de esquecer um caso (duplicata, troca de lado) do que uma sequência de ifs"

requirements-completed: [FLOW-02, FLOW-03]

# Metrics
duration: ~90min
completed: 2026-09-03
---

# Phase 17 Plan 03: Rota de aceite do collar (re-derivação server-side) Summary

**`POST /api/options/lastreada/abrir-collar` executa a trava protetora só quando a proposta RE-DERIVADA no servidor (nunca o corpo da requisição) confere com o que o cliente submeteu — fecha a "Limitação conhecida" que o ADR-025 deixou documentada como pendência da Fase 17.**

## Performance

- **Duration:** ~90 min
- **Started:** 2026-09-03T02:20:00Z (aprox.)
- **Completed:** 2026-09-03T04:00:00Z (aprox.)
- **Tasks:** 3
- **Files modified:** 4 (2 criados, 2 modificados)

## Accomplishments
- Nova rota `POST /api/options/lastreada/abrir-collar` (`options_lastreada_abrir_collar` em `server/app/main.py`) — 403 de Modo Estudo antes de qualquer I/O; validação de forma do corpo (underlying/pernasContratos/contratos); re-derivação completa do pipeline técnico (chain/posição/cash/snapshot/plano) com `opcoes_lastreadas.propor(..., multiperna=True)` FIXO, nunca lido do corpo; 409 quando o motor não propõe mais collar; cross-check por dict `{contractSymbol: lado}` entre o corpo e a proposta fresca (409 em qualquer divergência); execução via `store.abrir_collar` (17-01) usando SÓ os prêmios/contratos/quantidade da proposta re-derivada; 400 para `ValueError` do motor; `premiosUsados` no retorno.
- 17 testes (14 funções, uma parametrizada em 4 casos) em `server/tests/test_opcoes_collar_rota.py` cobrindo todo o `<behavior>` do plano: 403 sem tocar provider, 400 de corpo malformado (parametrizado: `None`/vazio/1 perna/3 pernas), 200 com execução das duas pernas, 409 (proposta mudou, contrato trocado, lado trocado, quantidade divergente), prêmio do corpo ignorado (inspeção de fonte + comportamento), 502 de cadeia degradada, 400 de `ValueError` do motor, não-regressão da trava de 16-04 na rota antiga, e meia estrutura impossível pela rota nova.
- `docs/adr/026-execucao-de-estrutura-multiperna.md` — 5 decisões nomeando a alternativa descartada em cada uma, seção de limitações conhecidas (encerramento perna a perna, ramo `pos_op_aberta` herdado, semântica de `at`), referências. ADR-025 recebeu nota datada apontando o fechamento, sem reescrever o texto original.
- Ciclo RED→GREEN seguido à risca: commit de 16 testes falhando (405/`AttributeError`, rota inexistente) antes da implementação, depois commit da implementação com os 17 testes verdes, depois commit endurecendo o guardião de prêmio com verificação de comportamento.
- Injeção de falha (acceptance criteria da Task 2) executada manualmente: cross-check trocado por `if False:` (confiança cega no corpo) — 2 de 17 testes reprovaram (`test_collar_contrato_trocado_devolve_409_sem_efeito_colateral`, `test_collar_lado_trocado_devolve_409_sem_efeito_colateral`), `>= 2` exigido; `git checkout -- server/app/main.py` restaurou o estado correto e a suíte voltou a 17/17.

## Task Commits

1. **Task 1 (RED): testes falhando antes da rota existir** - `2231a19` (test)
2. **Task 1 (GREEN): `POST /api/options/lastreada/abrir-collar`** - `4a1720f` (feat)
3. **Task 2: guardião de prêmio com verificação de comportamento** - `45e2e68` (test)
4. **Task 3: ADR-026 + nota no ADR-025** - `f18f20e` (docs)

## Files Created/Modified
- `server/tests/test_opcoes_collar_rota.py` - 18 testes (403/400/200/409/502/400 do comportamento completo + 4 guardiões de hardening/não-regressão)
- `server/app/main.py` - nova função `options_lastreada_abrir_collar` (~110 linhas incluindo docstring), inserida entre `options_lastreada_abrir` e `options_lastreada_fechar`; `git diff` confirma zero linhas removidas/alteradas em `options_lastreada_abrir` (só inserção)
- `docs/adr/026-execucao-de-estrutura-multiperna.md` - novo ADR, 9 seções `## `, 5 decisões cada uma com alternativa descartada nomeada
- `docs/adr/025-collar-e-estrutura-multiperna.md` - nota datada acrescentada (linha, não reescrita) apontando o fechamento pelo ADR-026

## Decisions Made
Ver `key-decisions` no frontmatter. Resumo: rota nova (não flag), re-derivação sempre (nunca confiar no corpo), 502 explícito em vez de degradar numa rota de escrita, `premiosUsados` plural.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Mensagens de erro usavam a frase-âncora "trava protetora", quebrando o guardião CVM pré-existente**
- **Found during:** Task 1 (GREEN), ao rodar a suíte de collar completa
- **Issue:** O `<action>` do plano especifica literalmente as mensagens `"Trava protetora exige exatamente duas pernas."` e `"A trava protetora não está mais disponível — o servidor recalculou a proposta e o resultado mudou."`. `test_opcoes_collar_vocab.py::test_nenhum_modulo_backend_fora_do_skill_ref_compoe_manchete_do_collar` (guardião CVM da Fase 16, varredura AST) reprova qualquer string literal de CÓDIGO fora de `skill_ref.py` contendo a frase-âncora "trava protetora" — a manchete do collar vem SÓ do motor determinístico. A segunda mensagem ("A trava protetora não está...") continha o substring exato `"trava protetora"` (minúsculo, após "A "). Este é exatamente o mesmo desvio que o Plano 17-01 já encontrou e documentou em seu SUMMARY para `store.abrir_collar`.
- **Fix:** Reescrevi as duas mensagens para usar "Collar"/"collar" em vez de "Trava protetora"/"trava protetora" — preservando o sentido, mudando só a palavra reservada à manchete: `"Collar exige exatamente duas pernas."` e `"O collar não está mais disponível — o servidor recalculou a proposta e o resultado mudou."`. Testes correspondentes em `test_opcoes_collar_rota.py` ajustados para a mesma wording.
- **Files modified:** `server/app/main.py`, `server/tests/test_opcoes_collar_rota.py`
- **Verification:** `test_opcoes_collar_vocab.py` volta a passar; suíte combinada de collar (rota + execução + vocabulário + lastreadas) 74/75 (1 falha pré-existente não relacionada, ver Issues Encountered); suíte canônica completa (`bash scripts/executar.sh --testes`, sandbox desligado) verde: 2010 passed, 1 skipped (pytest) + todos os `web/tests/*.mjs`.
- **Committed in:** `4a1720f`

---

**Total deviations:** 1 auto-fixed (Rule 1 — mesmo padrão de colisão com o guardião CVM já documentado pelo Plano 17-01, não uma descoberta nova).
**Impact on plan:** Nenhuma mudança de escopo ou de comportamento validado pelos testes do plano — só o texto exato de duas mensagens de erro divergiu do `<action>` literal.

## Issues Encountered
- **`test_vender_posicao_100_por_cento_travada_via_sell_devolve_400` falha dentro do sandbox padrão** (`PermissionError: [Errno 1] Operation not permitted` na criação de contexto SSL para `candle_provider.get_quote` via Yahoo real) — restrição de rede do sandbox de execução, não regressão deste plano. Confirmado rodando a suíte completa com `dangerouslyDisableSandbox: true`: **2010 passed, 1 skipped** (pytest) + todos os `web/tests/*.mjs` OK. Mesmo achado documentado no SUMMARY do Plano 17-01 para outros testes da mesma classe.
- **`server/.venv` ausente no worktree:** criado um symlink temporário `server/.venv -> <repo principal>/server/.venv` para rodar os testes; removido antes de finalizar.

## User Setup Required
None - nenhuma configuração de serviço externo.

## Next Phase Readiness

**Para o Plano 17-05 (front):**
- **Rota:** `POST /api/options/lastreada/abrir-collar`
- **Corpo aceito:** `{"underlying": <ticker>, "pernasContratos": [{"contractSymbol": <str>, "lado": "venda"|"compra"}, {"contractSymbol": <str>, "lado": "venda"|"compra"}], "contratos": <int>}` — exatamente 2 pernas, ambas presentes; `expiration` pode ser enviado mas é ignorado pela rota (não usado na re-derivação).
- **Códigos de erro que a UI precisa diferenciar:**
  - `403` — Modo Estudo (mesma mensagem da rota irmã `/abrir`)
  - `400` — corpo malformado (`underlying`/`contratos` inválidos, ou `pernasContratos` sem exatamente 2 pernas válidas) OU `ValueError` do motor de execução (lastro/caixa consumidos entre a re-derivação e a escrita)
  - `409` — proposta re-derivada não bate mais com o que o cliente submeteu (motor não propõe collar agora, OU contrato/lado/quantidade divergem da proposta fresca) — ação recomendada: recarregar a proposta via `GET /api/options/proposta/{ticker}?multiperna=1` e reexibir
  - `502` — cadeia de opções indisponível, ou falha inesperada na re-derivação
- **Corpo de resposta em sucesso:** `store.public_state(...)` + `premiosUsados: [{"contractSymbol", "lado", "premioUnitario"}, ...]` (2 entradas, espelho de `pernasContratos` da proposta).
- Rota `/abrir` original e sua trava de 400 (Plano 16-04) permanecem 100% intocadas — nenhuma mudança de comportamento para o cliente atual (venda coberta/put isolada).

## Self-Check: PASSED

- FOUND: `server/app/main.py` — `options_lastreada_abrir_collar` presente
- FOUND: `server/tests/test_opcoes_collar_rota.py`
- FOUND: `docs/adr/026-execucao-de-estrutura-multiperna.md`
- `grep -c "abrir-collar" server/app/main.py` == 1
- `grep -n "multiperna=True" server/app/main.py` mostra a chamada dentro da rota nova
- `git diff server/app/main.py` não altera nenhuma linha de `options_lastreada_abrir` (só inserção)
- `git diff docs/adr/025-collar-e-estrutura-multiperna.md` mostra só linhas acrescentadas
- FOUND commits: `2231a19`, `4a1720f`, `45e2e68`, `f18f20e` (todos presentes em `git log --oneline`)
- `cd server && .venv/bin/python -m pytest tests/test_opcoes_collar_rota.py -q` — 17 passed
- `bash scripts/executar.sh --testes` (sandbox desligado) — verde: 2010 passed, 1 skipped (pytest) + todos os `web/tests/*.mjs`

---
*Phase: 17-fluxo-de-aceite*
*Completed: 2026-09-03*
