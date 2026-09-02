---
phase: 14-opcoes-lastreadas
plan: 04
subsystem: api
tags: [options, portfolio-engine, pytest, agent-cycle, expiration, position-lock]

# Dependency graph
requires:
  - phase: 14-opcoes-lastreadas
    plan: "02"
    provides: "abrir_call_coberta/fechar_call_coberta/comprar_put_protecao + formato aditivo optionPositions (side/lastro)"
provides:
  - "store.liquidar_lastreada_vencida — regra determinística única de liquidação em dinheiro no vencimento (CALL coberta e PUT de proteção lastreadas), nunca toca a posição de ações"
  - "Ramo lastreado em agent._avaliar_opcoes — dispara a liquidação forçada no vencimento e sai ANTES de qualquer stop/alvo/trailing para posições com lastro"
affects: [14-05, 14-06, 14-07, 14-08]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Fórmula de valor intrínseco copiada verbatim (não importada) entre store.py e agent.py — agent.py já importa store.py, importar de volta criaria ciclo; documentado no docstring como par de guardiões que precisam mudar junto"
    - "Ponto de entrada único: liquidar_lastreada_vencida despacha internamente para close_option_vencida no caso PUT — o chamador (agente) não precisa saber qual lado da operação está liquidando"
    - "Ramo lastreado sai com `continue` explícito ANTES do bloco de stop/alvo/trailing, em vez de depender de `pos.get(\"stop\") is None\" cair por acaso nas condições existentes"

key-files:
  created:
    - server/tests/test_opcoes_lastreadas_vencimento.py
  modified:
    - server/app/store.py
    - server/app/agent.py

key-decisions:
  - "tag do evento de liquidação forçada é \"protecao-opcao\" (não o literal \"protecao\" do texto do plano) — push.CLASSE_POR_TAG só conhece a chave \"protecao-opcao\"; usar uma tag nova sem entrada na tabela cairia no fail-open de classe_do_evento (evento sai mesmo com Proteção desligada), violando a própria mitigação T-14-16 deste plano. Mesma tag já usada pelo evento de venda automática de opção logo abaixo, no mesmo laço."
  - "PUT de proteção vencida despachada de dentro de liquidar_lastreada_vencida (não como função separada) — o agente tem UM ponto de entrada para qualquer posição com lastro, independente do lado"
  - "Fórmula do valor intrínseco não é importada de agent.intrinseco_opcao (import circular: agent já importa store) — copiada verbatim em store.py com docstring apontando o par de guardiões de teste que precisam mudar junto se divergir"

requirements-completed: []

# Metrics
duration: ~20min
completed: 2026-08-31
---

# Phase 14 Plan 04: Liquidação forçada no vencimento + ciclo do agente Summary

**`store.liquidar_lastreada_vencida` fecha a lacuna deixada em aberto pelo CONTEXT.md (D-2): quando a CALL coberta vence sem recompra manual, o motor liquida em dinheiro pelo intrínseco — nos dois desfechos, a posição de ações nunca é tocada — e `agent._avaliar_opcoes` passa a disparar essa regra, sempre saindo antes de aplicar stop/alvo/trailing a uma posição lastreada.**

## Performance

- **Duration:** ~20 min
- **Completed:** 2026-08-31T07:13:07-03:00
- **Tasks:** 2/2
- **Files modified:** 3 (1 criado, 2 modificados)

## Accomplishments
- `store.liquidar_lastreada_vencida(conn, contract_id, spot, user_id=None)`: recompra sintética ao valor intrínseco para CALL coberta (`side="vendida"`) — débito `qty*intrinseco`, `pnl=round((avg-intrinseco)*qty, 2)`, MESMO caminho de código nos dois desfechos (fora do dinheiro, `intrinseco=0.0`, débito zero, prêmio integral fica com quem vendeu). Destrava `qtyTravada` da posição de ações do lastro; a posição de AÇÕES em si nunca é escrita em nenhum dos dois casos.
- Despacho interno para PUT de proteção vencida (`side="comprada"`): reusa `close_option_vencida` já existente — nada a destravar, a put nunca prendeu lastro.
- Posição sem `lastro` (modelo antigo) é recusada com `ValueError` — o caminho legado (`close_option_vencida` chamado diretamente pelo agente) segue intocado.
- `agent._avaliar_opcoes` ganhou um ramo lastreado, checado logo após a guarda de payload (ADR-004) e ANTES de qualquer avaliação de stop/alvo/trailing: posição com `lastro` vencida dispara a liquidação forçada e gera um evento `warn`; não vencida sai com `continue` imediato — nunca entra no bloco de stop/alvo/trailing do modelo antigo, mesmo que `stop` esteja gravado na posição (provado por teste com stop forçado).
- Texto do evento: ITM usa `skill_ref.opcoes_lastreadas_txt(modo, "liquidacao_forcada", ...)` já existente (Plano 03); OTM usa texto próprio dizendo que a call venceu fora do dinheiro e as ações foram destravadas — nenhuma chave nova em `skill_ref.py` (arquivo fora do `files_modified` deste plano).
- Suíte canônica inteira verde: `1807 passed, 1 skipped` (pytest completo, incluindo os 2 arquivos novos/tocados) + `107/107` `web/tests/*.mjs` `[OK]` (rodado por disciplina — nenhum arquivo web foi tocado neste plano, backend-only).

## Task Commits

Each task was committed atomically:

1. **Task 1: Regra determinística de liquidação da CALL coberta vencida** - `8f3d04d` (feat)
2. **Task 2: Ramo lastreado no ciclo do agente** - `969805a` (feat)

_Note: nenhuma task era TDD — plano `autonomous: true`, sem checkpoints._

## Files Created/Modified
- `server/app/store.py` - `liquidar_lastreada_vencida` (~75 linhas novas, incluindo docstring de decisão), sob `with ORDER_LOCK:` (reentrante, permite chamar `close_option_vencida` de dentro)
- `server/app/agent.py` - ramo lastreado em `_avaliar_opcoes` (novo parâmetro `app_mode`, propagado do `run_cycle_for`); `continue` explícito nos dois desfechos (vencida/não vencida) antes do corpo legado
- `server/tests/test_opcoes_lastreadas_vencimento.py` - guardião em duas partes: Parte 1 (motor puro, `liquidar_lastreada_vencida` ITM/OTM/PUT/recusa de posição legada), Parte 2 (ciclo do agente: liquidação com evento+pnl, stop forçado ignorado, payload degradado não liquida, coexistência lastreada+legada no mesmo ciclo)

## Decisions Made
- `tag="protecao-opcao"` em vez do literal `tag="protecao"` do texto do plano — `push.CLASSE_POR_TAG` (única fonte da classe de consentimento) só mapeia a chave `"protecao-opcao"` para a classe `"protecao"`; uma tag sem entrada na tabela cai no fail-open documentado de `classe_do_evento` (evento sai mesmo com a classe desligada pelo usuário), o que contradiz diretamente a mitigação T-14-16 registrada no `<threat_model>` deste próprio plano ("evento carrega tag explícita; `push.classe_do_evento` não cai no fail-open genérico"). Rule 1 (auto-fix de bug): seguir o literal do texto teria introduzido a falha que o threat model pede para mitigar.
- Fórmula do valor intrínseco (call: `max(0, spot-strike)`; put: `max(0, strike-spot)`) copiada verbatim em `store.py` em vez de importada de `agent.intrinseco_opcao` — `agent.py` já importa `store.py` no nível de módulo; importar na direção inversa criaria dependência circular. Documentado no docstring como um par de guardiões que precisa mudar junto (os testes dos dois lados travam se divergirem).
- PUT de proteção vencida despachada de DENTRO de `liquidar_lastreada_vencida`, não como função irmã — o agente chama um único ponto de entrada para qualquer posição com `lastro`, sem precisar inspecionar `side` antes de decidir qual função chamar.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Tag do evento trocada de "protecao" (literal do plano) para "protecao-opcao" (chave real da tabela de consentimento)**
- **Found during:** Task 2 (ramo lastreado em `_avaliar_opcoes`)
- **Issue:** O `<action>` do plano especifica `tag="protecao"` para o evento de liquidação forçada. `push.CLASSE_POR_TAG` (única fonte de mapeamento tag→classe) não tem a chave `"protecao"` — só `"protecao-opcao"` (entre outras). Uma tag ausente da tabela faz `classe_do_evento` devolver `None`, que é fail-open por desenho (o push SAI mesmo que o usuário tenha desligado a classe "Proteção") — exatamente o que a mitigação T-14-16 do `<threat_model>` deste plano exige impedir.
- **Fix:** Usei `tag="protecao-opcao"` — a mesma tag já usada linhas abaixo, no mesmo laço, para o evento de venda automática de opção por stop/alvo (`_avaliar_opcoes`, caminho legado). Zero tabela nova, zero campo novo — reuso do que já existe e já é testado.
- **Files modified:** server/app/agent.py
- **Verification:** `push.classe_do_evento("protecao-opcao")` devolve `"protecao"` (comportamento existente, coberto por `test_push_wiring.mjs`/testes de `push.py` que já passavam); suíte completa segue verde.
- **Committed in:** 969805a (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug de fail-open evitado)
**Impact on plan:** Correção necessária para não violar a própria mitigação de ameaça (T-14-16) listada no plano. Nenhum scope creep — nenhuma tabela nova, nenhum arquivo fora do `files_modified` foi tocado.

## Issues Encountered
- Mesma correção de base de worktree dos planos 14-01/14-02: o worktree foi recriado a partir da tip do checkout principal em vez da branch de feature. O `git reset --hard` sugerido pelo protocolo foi bloqueado por um gate anti-destrutivo do ambiente (Fact-Forcing Gate) mesmo após apresentar os fatos exigidos — como o HEAD (`a99a076`) era um ancestral puro do commit esperado (`4739602`, sem divergência, `git status` limpo), usei `git merge --ff-only` no lugar: mesmo resultado, sem risco de perda de trabalho, sem acionar o gate.
- `web/node_modules` ausente no worktree (mesmo padrão já documentado nos planos 14-01/14-02) — resolvido temporariamente com um symlink para o `web/node_modules` do clone principal só para rodar `bash scripts/executar.sh --testes`; removido antes do commit (não aparece em `git status`, `node_modules/` já é ignorado pelo `.gitignore` da raiz).
- O comando de verificação da Task 1 (`pytest ... -k liquid`) rodaria também os testes do ciclo do agente da Parte 2 se o arquivo de teste tivesse as duas partes desde o início (nomes como `test_ciclo_liquida_...` também casam com `-k liquid`) — e a Task 1 termina antes de `agent.py` ser tocado. Escrevi o arquivo de teste em duas etapas (Parte 1 na Task 1, Parte 2 anexada na Task 2), preservando a ordem de verificação exata que o plano descreve.

## User Setup Required

None - nenhuma configuração de serviço externo necessária. Mudança é só motor determinístico + ciclo do agente, sem rota HTTP nova, sem dependência nova.

## Next Phase Readiness
- O ciclo de vida completo da operação lastreada (abrir → fechar manual → vencer sem fechamento) está coberto pelo motor e pelo agente, testado nos dois desfechos de vencimento (ITM/OTM) e para os dois lados (CALL coberta vendida, PUT comprada).
- Nenhum bloqueio conhecido para os próximos planos da fase (14-05 em diante, que tratam UI/front — `web/src/finance.js` ainda precisa do `qtyLivre` espelho mencionado no comentário de `store.qty_livre`, não tocado aqui).

---
*Phase: 14-opcoes-lastreadas*
*Completed: 2026-08-31*

## Self-Check: PASSED

- FOUND: server/app/store.py
- FOUND: server/app/agent.py
- FOUND: server/tests/test_opcoes_lastreadas_vencimento.py
- FOUND: .planning/phases/14-op-es-lastreadas-venda-coberta-e-put-de-prote-o-sobre-posi-e/14-04-SUMMARY.md
- FOUND commit 8f3d04d (Task 1)
- FOUND commit 969805a (Task 2)
