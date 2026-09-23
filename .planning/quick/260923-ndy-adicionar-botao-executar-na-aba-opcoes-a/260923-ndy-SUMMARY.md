---
phase: quick-260923-ndy
plan: 01
subsystem: options-trading-ui
tags: [fastapi, react, options, mcp, execucao-simulada]

requires:
  - phase: quick-260915-j5l
    provides: executarCandidato.js (despacho puro candidato -> store), padrão de estado busy/erro/ok em CuradoriaEstruturas.jsx
provides:
  - "server/app/options_mcp_api.py: _execucao_da_proposta(estruturas, lote) + campo `execucao` em POST /api/options/mcp/proposta"
  - "web/src/opcoes/ExecutarProposta.jsx: bloco de execução manual da estrutura montada em Analisar"
affects: [aba-opcoes, fase-39-continuidade-workspace]

tech-stack:
  added: []
  patterns:
    - "Derivação de tamanho/tipo de ordem SEMPRE no backend (princípio 5 CLAUDE.md) — _execucao_da_proposta é o segundo lugar do código (depois de _em_reais) que fecha essa disciplina para a rota /proposta"
    - "Estado de execução amarrado à IDENTIDADE do objeto de dados (st.ref === dados), não a um id explícito — reseta sozinho quando a estrutura muda, sem useEffect"

key-files:
  created:
    - server/tests/test_options_mcp_proposta_execucao.py
    - web/src/opcoes/ExecutarProposta.jsx
    - web/tests/test_opcoes_analisar_executar_ui.mjs
  modified:
    - server/app/options_mcp_api.py
    - server/tests/test_options_mcp_api.py
    - web/src/opcoes/SecaoAnalisar.jsx
    - web/src/opcoes/OpcoesScreen.jsx
    - web/src/App.jsx
    - web/src/copy.js

key-decisions:
  - "Task 3 (bump/publicar-web.sh/push/produção) foi DELIBERADAMENTE NÃO executada nesta rodada — fica para o orquestrador, que pede confirmação explícita do Alex antes de publicar (guardrail de ação irreversível)."
  - "Mutadores de estado do gsd-sdk NÃO foram chamados (decisão do Alex, 2026-09-11) — STATE.md não foi tocado; este SUMMARY.md também não foi commitado, por instrução explícita da tarefa."

requirements-completed: []  # requirements: [QUICK-260923-ndy] do PLAN.md — Task 3 (publicação) segue pendente; a quick não fecha sem ela.

duration: ~35min (RED Task 1 a GREEN Task 2, sem contar exploração de contexto)
completed: 2026-09-23
---

# Quick 260923-ndy: Botão de execução em Opções -> Analisar (Task 1 + Task 2) Summary

**Bloco `execucao` derivado no backend (`_execucao_da_proposta`) e componente `ExecutarProposta.jsx` ligado em Analisar, reusando `ctx.A.executarCandidatoCurado` — Task 3 (publicação) fica para o orquestrador.**

## Performance

- **Duração:** ~35 min entre o primeiro commit RED (Task 1) e o último commit GREEN (Task 2), sem contar a leitura de contexto anterior (plano, CLAUDE.md, arquivos-fonte).
- **Iniciado:** 2026-09-23T17:04:42-03:00 (commit RED Task 1)
- **Concluído:** 2026-09-23T17:10:14-03:00 (commit GREEN Task 2)
- **Tasks:** 2 de 3 (Task 1 e Task 2 completas; Task 3 deliberadamente não executada)
- **Arquivos modificados/criados:** 9 (3 criados, 6 modificados)

## Accomplishments

- `POST /api/options/mcp/proposta` devolve um bloco `execucao` derivado no backend: candidato pronto para execução manual (`tipo`/`contractSymbol`/`expiration`/`contratos`/`qtyAcoes`) quando a estrutura tem 1 perna válida e lote múltiplo de 100; motivo nomeado e verbatim em todos os outros casos (2+ estruturas, 2+ pernas, venda de put, campos incompletos, proporção ≠ 1, lote ausente/fora de centena).
- Em Opções -> Analisar, Modo Operador, uma estrutura de 1 perna montada pelo usuário agora mostra um botão de execução (`ExecutarProposta.jsx`) que despacha pelo MESMO caminho já em produção no bloco de curadoria (`ctx.A.executarCandidatoCurado` -> `executarCandidato.js` -> `store`).
- Modo Estudo continua sem nenhum botão de execução (mesmo gate de `CuradoriaEstruturas.jsx`); estruturas não executáveis mostram o motivo do backend, verbatim, sem botão.
- Recusa de liquidez DIFÍCIL do servidor vira, ela mesma, o texto do checkbox de consentimento; só reenvia com `aceitaLiquidezDificil === true`.
- Zero conta de tamanho de ordem no front — `contratos`/`qtyAcoes` chegam prontos do backend (guardião estático confirma ausência de `* 100`/`/ 100`/`* lote` em `ExecutarProposta.jsx`).

## Task Commits

1. **Task 1 — RED: casos de `_execucao_da_proposta`** - `0bfec03` (test)
2. **Task 1 — GREEN: bloco `execucao` na rota de proposta** - `d92a829` (feat)
3. **Task 2 — RED: guardião de `ExecutarProposta.jsx`** - `a0f5888` (test)
4. **Task 2 — GREEN: `ExecutarProposta.jsx` ligado em Analisar** - `e7566bf` (feat)

**Task 3 (bump, publicar-web.sh, push, confirmação HTTP em produção): NÃO executada nesta rodada** — ver "Próximos passos" abaixo.

_Nenhum commit de metadados (SUMMARY.md/STATE.md) foi feito — por instrução explícita da tarefa, esse fechamento fica com o orquestrador._

## Files Created/Modified

- `server/app/options_mcp_api.py` - `_execucao_da_proposta(estruturas, lote)` + 7 constantes `MOTIVO_EXEC_*` + campo `execucao` no retorno de `proposta()`
- `server/tests/test_options_mcp_proposta_execucao.py` - 14 testes da função pura (todos os casos do `<behavior>` da Task 1)
- `server/tests/test_options_mcp_api.py` - 2 testes de rota novos/estendidos (`execucao` executável e `execucao` não-executável por multiperna)
- `web/src/opcoes/ExecutarProposta.jsx` - componente novo: gate Estudo, motivo/erro verbatim, consentimento de liquidez, botão contornado
- `web/tests/test_opcoes_analisar_executar_ui.mjs` - guardião novo (35 asserções): render SSR + inspeção estática
- `web/src/opcoes/SecaoAnalisar.jsx` - importa e renderiza `<ExecutarProposta>` depois de `<Pernas>`, dentro do ramo `proposta.dados ?`
- `web/src/opcoes/OpcoesScreen.jsx` - passa `operador=`/`onExecutarProposta=` a `<SecaoAnalisar>`
- `web/src/App.jsx` - `executarCandidatoCurado`: só o rótulo do `track` muda (`analisar_<tipo>` vs `curadoria_<tipo>`)
- `web/src/copy.js` - chave `opcoesExecucaoSimulada` nos dois modos

## Decisions Made

- **Task 3 explicitamente NÃO executada.** O plano original previa bump/publicação na mesma rodada, mas a instrução desta execução foi clara: só Task 1 e Task 2, parar antes da Task 3, que fica com o orquestrador (guardrail de ação irreversível — o Alex confirma explicitamente antes de publicar).
- **Mutadores de estado do `gsd-sdk` não foram chamados** (decisão do Alex, 2026-09-11, documentada em CLAUDE.md e MEMORY.md) — `STATE.md` não foi tocado.
- **Este SUMMARY.md não foi commitado** — instrução explícita da tarefa (`<constraints>`: "NÃO commite STATE.md/PLAN.md/SUMMARY.md"). Fica em disco, não staged, para o orquestrador decidir o que fazer no fechamento.
- Nenhuma decisão de arquitetura nova: a implementação seguiu as premissas já resolvidas no `260923-ndy-PLAN.md` (mapa perna->tipo, derivação no backend, estado por identidade em vez de `useEffect`).

## Deviations from Plan

None - plano executado exatamente como escrito nas Tasks 1 e 2, com um nível de prova diferente em cada RED:
- **Task 1 (backend):** RED por falha de import (`ImportError: cannot import name '_execucao_da_proposta'`) — prova real de que a função não existia, mas não prova que a ORDEM das checagens internas importa (com 14 testes cobrindo cada ramo do `<behavior>`, a cobertura por caso compensa, mas não houve prova por mutação/defeito injetado nesta task).
- **Task 2 (frontend):** RED por `ERR_MODULE_NOT_FOUND` (arquivo não existe) MAIS prova por defeito injetado depois do GREEN — o gate `!operador` foi removido temporariamente, 3 asserções falharam nomeando o caso Estudo, revertido, guardião voltou a passar. Prova de RED em ambas as tasks via `git stash push -u -m <tag única>` + `git stash apply <sha>` + `git stash drop`, evitando `git stash pop` bare por causa da stash compartilhada do worktree.

Task 3 não é uma "não execução acidental" — é omissão deliberada por instrução explícita desta rodada de execução (ver `<constraints>` do prompt do orquestrador).

## Issues Encountered

- Achado de ambiente (ferramental, não do produto): `timeout` não existe neste shell (zsh/macOS sem coreutils GNU) — comando falhou com "command not found", contornado sem o `timeout`. `/tmp` está fora do allowlist de escrita do sandbox (`operation not permitted`) — a variável `$TMPDIR` é o caminho certo, mas ela resolve para diretórios DIFERENTES dentro do sandbox (`/tmp/claude-501`) e fora dele via `dangerouslyDisableSandbox` (`/var/folders/.../T/`), o que custou algumas idas e vindas de `grep`/`ls` até localizar o log da suíte rodada fora do sandbox. Nenhum dos dois bloqueou o trabalho.
- A suíte canônica rodou TRÊS vezes ao todo: (1) dentro do sandbox, pós-mudança — `2980 passed, 27 failed` (falhas de rede/TLS conhecidas); (2) fora do sandbox via `dangerouslyDisableSandbox`, pós-mudança — backend `3007 passed, 0 failed`, frontend só com a falha ambiental conhecida `test_ios_assets.mjs` (`web/ios/` gitignored, `CLAUDE.md:236`); (3) dentro do sandbox, PRÉ-mudança (os 2 arquivos do backend trocados temporariamente pela versão do commit `926ce10`, o novo arquivo de teste posto de lado, depois restaurados e o `git diff HEAD` conferido vazio) — `2964 passed, 27 failed`, medida NESTA sessão para confirmar a reconciliação, não citada de memória de um STATE.md de outra fase. Aritmética batendo nas três: `2980 - 2964 = 16` testes novos (14 em `test_options_mcp_proposta_execucao.py` + 2 em `test_options_mcp_api.py`); `3007 - 27 = 2980`. Nenhuma regressão introduzida por esta quick.

## User Setup Required

None - nenhuma configuração de serviço externo.

## Next Phase Readiness

**Pendente: Task 3 (bump, `publicar-web.sh`, push nas duas branches, confirmação HTTP em produção).** O orquestrador deve pedir confirmação explícita ao Alex antes de rodar essa etapa — é publicação em produção (Railway, `boris.semente.dev`), ação irreversível/observável por terceiros.

**Seis itens que o `<output>` do plano exige declarar, sem resolver:**

1. **Risco já existente e correto (não é bug novo):** a estrutura devolvida pelo serviço MCP pode não coincidir mais com a cadeia real da Yahoo no momento do clique (prêmio/contrato podem ter mudado entre a montagem e a execução). A rota de execução (`optionsAbrirLastreada`/`optionsBuy`) RE-BUSCA a cadeia e revalida no servidor — se o contrato sumiu ou a liquidez piorou, ela recusa com mensagem clara. O front não confia no que já tinha na tela.
2. **Premissa 5 do plano — risco de produto para o Alex decidir:** a fixture real do serviço MCP tende a propor travas de 2 pernas para teses direcionais. Se esse padrão se confirmar em produção, a MAIORIA das estruturas montadas em Analisar vai cair no ramo "não executável aqui" (`MOTIVO_EXEC_MULTIPERNA`) — o achado original do Alex fica só parcialmente fechado por esta quick. Executar trava/collar a partir do Analisar exigiria uma rota multi-perna nova no motor (`store.py` hoje só executa 1 perna por chamada), o que é decisão de produto fora do escopo desta quick.
3. **Premissa 3 do plano — pré-existente, não corrigido aqui:** `/api/options/buy` (usado pelo tipo `opcao_a_descoberto`, ou seja, buy+CALL) NÃO tem o 403 de bloqueio de Modo Estudo — só `/api/options/lastreada/abrir` tem esse gate explícito. Na prática o front já bloqueia o botão em `!operador`, mas a defesa de servidor desse caminho específico é mais fraca que a dos outros dois tipos. Mesmo comportamento pré-existente que a curadoria (Fase 31) já tem — não é uma regressão desta quick.
4. **Premissa 6 do plano:** buy+PUT vira `put_protecao`, que EXIGE lastro (posição no ativo) — sem posição, o servidor recusa, verbatim, na hora de executar (o front não checa isso antes). Put a seco (compra de put sem lastro, com a flag de "opção a descoberto" ligada) NÃO é oferecido por este caminho — o mapa perna->tipo desta quick não cobre esse caso.
5. **iOS:** o app nativo carrega o bundle local (Capacitor, sem `server.url`) — o botão de execução só chega ao iPhone num build novo de TestFlight, decisão separada do Alex (`scripts/ios-bump-build.sh` + distribuição). O campo `execucao` do backend já vale para qualquer cliente que chamar a rota, incluindo o app atual instalado (é o front que precisa do build novo para MOSTRAR o botão).
6. **Guardrail do repositório:** mutadores de estado do `gsd-sdk` não foram chamados nesta execução; `STATE.md`, quando for atualizado, deve ser editado à mão pelo orquestrador (decisão do Alex, 2026-09-11).

---
*Quick: 260923-ndy*
*Tasks 1+2 completed: 2026-09-23*
*Task 3 pending explicit publish confirmation*

## Self-Check: PASSED

Todos os 9 arquivos criados/modificados desta rodada foram confirmados em
disco (`[ -f ... ]`) e os 4 commits (`0bfec03`, `d92a829`, `a0f5888`,
`e7566bf`) foram confirmados em `git log --oneline --all`. Depois da medição
de baseline pré-mudança (troca temporária de 2 arquivos do backend pela
versão do commit `926ce10` + arquivo de teste novo posto de lado, restaurados
em seguida), `git diff --stat HEAD -- server/ web/src web/tests` voltou
vazio — nenhuma divergência residual contra os commits desta quick. `git
status --short` final mostra só `web/package-lock.json` modificado
(pré-existente, fora do escopo — ver `<constraints>`/Task 3 do plano) e o
diretório `.planning/quick/260923-ndy-.../` untracked (PLAN.md + este
SUMMARY.md), nenhum dos dois commitado, conforme instrução explícita.
