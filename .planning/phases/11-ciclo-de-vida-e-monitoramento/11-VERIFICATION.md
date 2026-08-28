---
phase: 11-ciclo-de-vida-e-monitoramento
verified: 2026-08-28T00:00:00Z
status: passed
score: 9/9 must-haves verified
overrides_applied: 2
suggested_overrides:
  - must_have: "ROADMAP SC #2 / PUTLIFE-02 (texto literal): 'A execução simulada de uma put usa optionPositions e os contratos de ADR-003/004/005'"
    reason: "ADR-022 Decisão 1 (docs/adr/022-ciclo-de-vida-da-sugestao-de-put.md), com duas evidências duras independentemente reconfirmadas por este verificador: (a) server/app/store.py:10 — SECTIONS inclui optionPositions/cash/history/positions, todas exportadas ao front — escrever ali seria, por definição, superfície visível, violando o guardrail de topo do milestone ('sem mostrar nada ao usuário'); (b) server/app/agent.py:531 — _avaliar_opcoes lê optionPositions e retorna imediatamente quando vazia, tornando a leitura literal do ROADMAP tecnicamente inerte (o ciclo de vida nunca rodaria sem uma posição real pré-existente). A interpretação adotada reusa os CONTRATOS (forma ADR-003 sem qty, cálculo de intrínseco de ADR-005 via import direto, vocabulário de motivo) sem escrever na coleção viva — provado por teste de comportamento (test_put_lifecycle_sem_carteira.py) e por leitura de fonte (nenhum import de store, nenhuma chamada a buy_option/sell_option/close_option_vencida/set_option_position em put_lifecycle.py/put_suggestions.py)."
    accepted_by: "Alex"
    accepted_at: "2026-08-28T18:00:00Z"
  - must_have: "ROADMAP SC #4 / PUTLIFE-04 (texto literal): 'roda dentro da segunda passada já existente do agent.py para optionPositions (linha ~527, _avaliar_opcoes/equivalente)'"
    reason: "ADR-022 Decisão 3 + D-EXEC-11-02-01 (.planning/notes/decisoes-autonomas-v1.2.md). A parte VINCULANTE do critério ('nenhum scheduler novo, nenhum cron externo') é cumprida literalmente — o hook vive dentro do scheduler_loop já existente. A parte literal ('dentro de _avaliar_opcoes') foi recusada porque _avaliar_opcoes é tecnicamente inerte sem posição real (mesma evidência do item acima) e porque pendurar ali acoplaria a medição ao gate de kill-switch/pregão (precedente do incidente de kill-switch de 2,5 dias). Implementação real: hook próprio, sibling do bloco 'if radar_fetch...', FORA do gate de kill-switch/pregão — confirmado por leitura direta de indentação em server/app/agent.py:1171 vs 1208-1214 por este verificador."
    accepted_by: "Alex"
    accepted_at: "2026-08-28T18:00:00Z"
re_verification: "Aceito por Alex em 11-HUMAN-UAT.md (status: resolved) — os 3 itens de UAT (ADR-022 Decisões 1/3, WR-01, WR-02) foram decididos: ADR-022 aceito como escrito; WR-01 aceito o estado atual (sem correção); WR-02 deixado documentado como código morto (sem correção). Ver .planning/phases/11-ciclo-de-vida-e-monitoramento/11-HUMAN-UAT.md."
gaps: []
human_verification:
  - test: "Ler e aceitar (ou rejeitar) formalmente ADR-022 Decisão 1 e Decisão 3 — a reinterpretação de 'reusar optionPositions' e de 'dentro da segunda passada' do texto literal do ROADMAP v1.2 Fase 11 (Success Criteria #2 e #4)"
    expected: "Alex concorda que a leitura literal seria tecnicamente inerte/violaria o guardrail de invisibilidade (evidência já reconfirmada por este verificador em store.py:10 e agent.py:531), e aceita a interpretação por CONTRATOS em vez de por COLEÇÃO — ou pede uma revisão de desenho"
    why_human: "É uma decisão de produto/arquitetura sobre o que o ROADMAP realmente pedia, tomada autonomamente pelo executor durante a madrugada sem pergunta prévia (A-11-01 documenta que o executor considerou a evidência dura o bastante para não reabrir a questão) — merece confirmação humana antes do milestone ser considerado 'shipped', mesmo com toda a evidência técnica apontando na mesma direção"
  - test: "Decidir se fecha WR-01 (11-REVIEW.md): sugestão `armada` sem `premio` (contrato ilíquido) fica sem carimbo de observabilidade — estado_em e pendente_desde ambos NULL — enquanto aguarda vencimento"
    expected: "Alex escolhe entre (a) estender a pendência de run_diario para cobrir o motivo 'sem prêmio de entrada', reusando pendente_desde, ou (b) um contador separado (ex. 'semPremio') no resumo de run_diario, ou (c) aceitar o estado atual (o resultado final continua correto — a linha se autorresolve em expirada_sem_uso no vencimento — só falta rastro de auditoria intermediário)"
    why_human: "Não é defeito de correção (o REVIEW confirma que o resultado final é sempre correto), é um buraco de observabilidade — decisão de produto sobre o nível de rastreabilidade desejado, já registrada para revisão matinal em decisoes-autonomas-v1.2.md"
  - test: "Decidir se fecha WR-02 (11-REVIEW.md): decidir() teria um fallback morto que fabricaria preco_entrada=0.0 se precoEntrada estivesse ausente/malformado ao entrar em executada_simulada/monitorada"
    expected: "Alex decide entre deixar o fallback morto documentado (não é alcançável pelo caminho atual — único produtor de executada_simulada é o próprio decidir(), que sempre grava preco_entrada válido) ou endurecê-lo agora para não virar risco se um segundo caminho de entrada for criado no futuro (ex. ferramenta de reparo manual)"
    why_human: "Risco de correção théorica, não realizado hoje — decisão de investimento de esforço (corrigir código morto vs. documentar e esperar), já registrada para revisão matinal em decisoes-autonomas-v1.2.md"
---

# Phase 11: Ciclo de vida e monitoramento Verification Report

**Phase Goal:** Toda sugestão de put armada tem um estado rastreável ao longo
do tempo (`armada` → `expirada sem uso` | `executada (simulada)` →
`monitorada` → `fechada`). Execução simulada e fechamento por expiração
reusam integralmente `optionPositions` e os contratos de ADR-003/004/005;
monitoramento é diário e roda dentro da segunda passada já existente do
`agent.py`. (ROADMAP.md, milestone v1.2, Phase 11 — última fase do
milestone.)

**Verified:** 2026-08-28
**Status:** passed (2 overrides aceitos por Alex em 2026-08-28 — ver `suggested_overrides` no frontmatter e `11-HUMAN-UAT.md`)
**Re-verification:** No — initial verification

**Contexto de execução:** esta fase rodou 100% desassistida, sob contrato de
autonomia noturna (`.planning/notes/decisoes-autonomas-v1.2.md`). O code
review (`11-REVIEW.md`) achou 0 Critical / 2 Warning / 1 Info; o orquestrador
decidiu deliberadamente NÃO corrigir os 2 Warnings (documentado, não
esquecido) e registrou os itens para revisão matinal do Alex. Esta
verificação NÃO trata WR-01/WR-02 como gaps de verificação (instrução
explícita da tarefa) — eles aparecem abaixo em `human_verification`, não em
`gaps`.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | Toda sugestão carrega um estado que só transiciona pelos 5 estados do ROADMAP, sem estado inválido/inatingível (ROADMAP SC #1, PUTLIFE-01) | ✓ VERIFIED | `put_suggestions.py:31-46` — `ESTADOS`/`ESTADOS_ROTULO`/`TERMINAIS`/`TRANSICOES`; `transicionar()` (linha 178) é a única porta, valida contra `ESTADOS` e `TRANSICOES[atual]`, devolve 0 para qualquer destino não declarado (nunca levanta). Confirmado por teste (`test_put_lifecycle_sem_carteira.py::test_b4_*`, produto cartesiano `ESTADOS × ESTADOS` completo) e por leitura direta do código |
| 2 | Execução simulada usa os CONTRATOS de ADR-003/004/005 sem função paralela de cálculo (ROADMAP SC #2, PUTLIFE-02) | ✓ VERIFIED — ver override sugerido | `put_lifecycle.forma_adr003()` produz shape ADR-003 sem `qty` (estruturalmente inaproveitável); `intrinseco()` importa `agent.intrinseco_opcao` e delega — CONFIRMADO por leitura direta (`put_lifecycle.py:115-121`: `from .agent import intrinseco_opcao; return intrinseco_opcao(...)`), nenhuma fórmula paralela. **Desvio do texto literal:** a sugestão NUNCA escreve em `optionPositions` (ver ADR-022 Decisão 1, evidência reconfirmada abaixo) — override sugerido no frontmatter |
| 3 | Fechamento por expiração reusa o mecanismo do ADR-005 (`motivo: "vencimento"`), sem lógica paralela (ROADMAP SC #3, PUTLIFE-03) | ✓ VERIFIED | `put_lifecycle.py`: `MOTIVO_VENCIMENTO = "vencimento"` (linha 33); ramo de fechamento em `decidir()` chama `intrinseco()` → `agent.intrinseco_opcao` real, nunca `max(0, strike-spot)` reimplementado. `grep -c intrinseco_opcao put_lifecycle.py` = 2 (import + docstring) |
| 4 | Monitoramento diário roda dentro do `scheduler_loop` já existente, nenhum scheduler novo (ROADMAP SC #4, PUTLIFE-04) | ✓ VERIFIED — ver override sugerido | `agent.py:1210-1214` — hook `put_lifecycle.maybe_run` pendurado no `scheduler_loop` real, confirmado por leitura direta de código e por teste com o laço REAL (`test_put_lifecycle_scheduler.py`, 8/8 passed). **Desvio do texto literal:** hook é SIBLING do `if radar_fetch...` (linha 1171), não dentro de `_avaliar_opcoes` — override sugerido no frontmatter |
| 5 | Nenhuma superfície visível ao usuário introduzida (ROADMAP SC #5) | ✓ VERIFIED | `git diff --stat "$FASE10" -- web/ web-admin/ server/app/skill_ref.py server/app/main.py server/app/defaults.py` → vazio (comando rodado por este verificador); `agent.py` não ganha chave `putLifecycle` em `status_snapshot` (`grep -v '^#' agent.py \| grep -c putLifecycle` = 0); nenhuma rota nova (`test_b5_nenhuma_rota_nova_de_ciclo_de_vida`) |
| 6 | Um ciclo de vida completo deixa `optionPositions`/`cash`/`history` byte-idênticos (must_have 11-01/11-03) | ✓ VERIFIED | Leitura direta de `put_lifecycle.py` e `put_suggestions.py` inteiros por este verificador: zero import de `store`, zero menção a `buy_option`/`sell_option`/`close_option_vencida`/`set_option_position`/`optionPositions` em qualquer linha (grep `-v '^#'` sobre o arquivo inteiro, incluindo docstring, `exit 1` = zero matches). `test_b1_carteira_intocada_em_ciclo_completo`/`test_b2_*` comparam `==` e `json.dumps(sort_keys=True)` de carteira real (montada via `db.kv_set` direto, bypass de `store.py`) antes/depois de 4 rodadas de `run_diario` — rodei localmente, 85/85 passed |
| 7 | Nenhuma sugestão fica em limbo silencioso (must_have 11-02/11-03) | ✓ VERIFIED, com ressalva WR-01 | `registrar_pendencia()`/`listar_abertas()` + tricotomia terminal/avançou-hoje/pendência-datada provada por `test_b3_nenhuma_linha_em_limbo_apos_rodada_mista`. **Ressalva (não rebaixa o veredito, ver human_verification):** o REVIEW (WR-01) encontrou um caso reachável que o próprio guardião de anti-limbo não exercita — `armada` sem `premio` e ainda não vencida fica com `estado_em`/`pendente_desde` ambos `NULL` até o vencimento (resultado final correto, rastro intermediário ausente) |
| 8 | Custo de rede zero na varredura diária (must_have 11-02) | ✓ VERIFIED | `grep -v '^#' put_lifecycle.py \| grep -cE "options_provider\|mydata_client\|candle_provider\|httpx\|B3_OPTIONS_PROVIDER"` = 0; `candle_cache.peek` é a única fonte (linha ~280); asserção negativa em teste (`test_custo_zero_de_rede_por_asserção_negativa`) |
| 9 | Uma exceção do ciclo de vida nunca derruba heartbeat/kill-switch/stop-alvo (must_have 11-02) | ✓ VERIFIED | `agent.py:1210-1214` — try/except PRÓPRIO em torno de `put_lifecycle.maybe_run`, dentro do try/except interno de `maybe_run` (duplo cinto); `test_excecao_do_hook_nao_impede_ponte_nem_vizinhos`/`test_excecao_do_hook_nao_derruba_a_passada` passam com o laço REAL |

**Score:** 9/9 truths verified (2 carregam override sugerido para o texto literal do ROADMAP, ambos com evidência dura reconfirmada por este verificador; 1 carrega ressalva WR-01, não-bloqueante)

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `server/app/put_lifecycle.py` | máquina de decisão pura + varredura diária + hook helpers | ✓ VERIFIED | 100% lido por este verificador; zero import de `store`; `intrinseco()` delega para `agent.intrinseco_opcao` via import local (linha 118-121) |
| `server/app/put_suggestions.py` | `transicionar()` como porta única + colunas de ciclo | ✓ VERIFIED | `ESTADOS`/`TRANSICOES`/`transicionar`/`registrar_pendencia`/`listar_abertas` confirmados presentes e substantivos |
| `server/app/db.py` | 11 colunas de ciclo de vida, `CREATE TABLE` + migração idempotente | ✓ VERIFIED | 11 colunas confirmadas em `CREATE TABLE` (linhas 332-342) E em `ALTER TABLE ... ADD COLUMN` idempotente (linhas 365-378), mesmo precedente de `candle_cache`/`users` |
| `server/app/agent.py` | hook `put_lifecycle.maybe_run` no `scheduler_loop` | ✓ VERIFIED | Linhas 1208-1214; `_avaliar_opcoes` (linha 526) comprovadamente NÃO editada nesta fase (`git diff "$FASE10" -- agent.py \| grep -c _avaliar_opcoes` = 0) |
| `server/tests/test_put_lifecycle_estados.py` | guardião de transições | ✓ VERIFIED | Existe, roda, passa |
| `server/tests/test_put_lifecycle_decisao.py` | guardião da decisão pura | ✓ VERIFIED | Existe, roda, passa |
| `server/tests/test_put_lifecycle_diario.py` | guardião da varredura diária | ✓ VERIFIED | Existe, roda, passa |
| `server/tests/test_put_lifecycle_scheduler.py` | guardião do hook com laço real | ✓ VERIFIED | Existe, roda, passa |
| `server/tests/test_put_lifecycle_sem_carteira.py` | guardião permanente carteira-intocada + anti-limbo + sem-superfície | ✓ VERIFIED | 439 linhas, 15 testes, todos passam; confere `min_lines: 120` do must_have (excede) |
| `docs/adr/022-ciclo-de-vida-da-sugestao-de-put.md` | registro permanente da decisão de desenho | ✓ VERIFIED | Existe, cita PUTLIFE-02 (2x), ADR-021 (7x), ADR-003/004/005 (10x), "expirada sem uso" (1x) — todos os greps do plano confirmados |
| `docs/OPERACAO-ciclo-de-vida-put.md` | runbook operacional | ✓ VERIFIED | Existe, cita as 2 env vars |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `put_lifecycle.py::intrinseco` | `agent.py::intrinseco_opcao` | import local dentro da função | ✓ WIRED | Confirmado por leitura direta: `from .agent import intrinseco_opcao` seguido de chamada direta — não há reimplementação da fórmula `max(0, strike-spot)` em `put_lifecycle.py` |
| `put_suggestions.py::transicionar` | `put_suggestions` (tabela) | UPDATE escopado por whitelist `COLUNAS_CICLO` | ✓ WIRED | Confirmado; proveniência da Fase 10 (premio/fonte/prov_*/iv/estilo_exercicio) fora da whitelist, comprovadamente imutável por essa porta |
| `agent.py::scheduler_loop` | `put_lifecycle.py::maybe_run` | hook com try/except próprio | ✓ WIRED | Confirmado com o laço REAL (`asyncio.run(agent.scheduler_loop(..., once=True))`), não mock |
| `put_lifecycle.py::run_diario` | `candle_cache.py::peek` | leitura sem rede | ✓ WIRED | Confirmado; `grep -c "candle_cache.peek"` ≥ 1, nenhuma chamada de rede alcançável |
| `put_lifecycle.py::run_diario` | `put_suggestions.py::transicionar` | única porta de escrita de estado | ✓ WIRED | Confirmado por leitura de `run_diario` (chama `transicionar`/`registrar_pendencia`, nunca UPDATE direto) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Nenhum literal proibido em `put_lifecycle.py`/`put_suggestions.py` | `grep -v '^#' <arquivo> \| grep -cE "buy_option\|sell_option\|close_option_vencida\|set_option_position\|optionPositions"` | 0 nos dois arquivos | ✓ PASS |
| `put_lifecycle.py` nunca importa `store` | `grep -n "import store\|from \.store\|from \. import store"` | vazio | ✓ PASS |
| Hook fora do gate de kill-switch/pregão | leitura de indentação `agent.py:1171` (12 espaços) vs `agent.py:1208-1214` (12 espaços, sibling) | mesmo nível de indentação — hook FORA do `if radar_fetch...` | ✓ PASS |
| `_avaliar_opcoes` não tocada nesta fase | `git diff "$FASE10" -- server/app/agent.py \| grep -c _avaliar_opcoes` | 0 | ✓ PASS |
| Suíte dos 5 arquivos de teste da fase + guardião Fase 10 | `pytest tests/test_put_lifecycle_*.py tests/test_put_bridge_sem_superficie.py -q` | 85 passed | ✓ PASS |
| Suíte canônica completa | `cd server && ./.venv/bin/python -m pytest -q` | 1674 passed, 1 skipped (bate com a contagem da SUMMARY) | ✓ PASS |
| Nenhum debt marker (TBD/FIXME/XXX/HACK/PLACEHOLDER) nos arquivos da fase | `grep -nE "TBD\|FIXME\|XXX\|HACK\|PLACEHOLDER"` em todos os 9 arquivos modificados/criados | nenhum match | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| PUTLIFE-01 | 11-01, 11-03 | Estado rastreável, 5 estados, transições declaradas | ✓ SATISFIED | `ESTADOS`/`TRANSICOES`/`transicionar()`, produto cartesiano testado |
| PUTLIFE-02 | 11-01, 11-03 | Reuso de `optionPositions`/ADR-003/004/005 sem cálculo paralelo | ✓ SATISFIED — via ADR-022 (reinterpretação documentada, override sugerido) | Contratos reusados por import direto; `optionPositions` nunca tocada por desenho |
| PUTLIFE-03 | 11-01, 11-03 | Fechamento por vencimento reusa ADR-005, sem lógica paralela | ✓ SATISFIED | `intrinseco()` delega a `agent.intrinseco_opcao`; `MOTIVO_VENCIMENTO` = vocabulário ADR-005 |
| PUTLIFE-04 | 11-02, 11-03 | Monitoramento diário sem scheduler novo | ✓ SATISFIED — via ADR-022 (reinterpretação documentada, override sugerido) | Hook no `scheduler_loop` existente; posição exata (dentro de `_avaliar_opcoes`) reinterpretada por ADR-022 Decisão 3 |

**Nota:** `.planning/REQUIREMENTS.md` ainda lista os 4 IDs como `[ ]`/"Pending" na tabela de status — isto é esperado neste ponto do fluxo (o passo "evolve PROJECT.md after phase completion" roda DEPOIS da verificação, mesmo padrão observado nas Fases 9/10) e não é tratado como gap desta verificação. `ROADMAP.md` já marca a Fase 11 como `[x]` completed 2026-08-28. `STATE.md` também está desatualizado ("Executing Phase 11", 0%) pelo mesmo motivo — bookkeeping pendente, não falha de goal.

Nenhum requisito órfão: os 4 IDs de `PUTLIFE-01..04` aparecem declarados em pelo menos um `requirements:` de PLAN, e todos os 4 aparecem em `.planning/REQUIREMENTS.md` na seção "Ciclo de vida e monitoramento (Fase 11)".

### Anti-Patterns Found

Nenhum. Scan de `TBD`/`FIXME`/`XXX`/`HACK`/`PLACEHOLDER`/"not yet implemented"/"coming soon" sobre os 9 arquivos criados/modificados pela fase (`put_lifecycle.py`, `put_suggestions.py`, `db.py`, `agent.py` + 5 arquivos de teste) não encontrou nenhum match.

Os dois achados do code review (WR-01, WR-02) não são anti-patterns de código morto/placeholder — são, respectivamente, um buraco de observabilidade num ramo alcançável (WR-01) e um fallback defensivo hoje inalcançável (WR-02), ambos documentados e deliberadamente deixados para decisão do Alex. Listados em `human_verification`, não aqui.

### Human Verification Required

#### 1. Aceitar formalmente ADR-022 Decisão 1 e Decisão 3 (reinterpretação de "reusar optionPositions"/"dentro da segunda passada")

**Test:** Ler `docs/adr/022-ciclo-de-vida-da-sugestao-de-put.md`, seções Decisão 1 e Decisão 3, e as duas entradas correspondentes em `.planning/notes/decisoes-autonomas-v1.2.md` (A-11-01 em `11-01-PLAN.md`, D-EXEC-11-02-01 no log de decisões)
**Expected:** Confirmar que a leitura literal do ROADMAP ("reusar `optionPositions`"/"dentro de `_avaliar_opcoes`") de fato produziria um recurso morto ou uma superfície visível indesejada — este verificador reconfirmou independentemente as duas evidências duras citadas (`store.py:10`, `agent.py:531`) e concorda com a conclusão técnica, mas a leitura de qual TEXTO do roadmap prevalece é uma chamada de produto, não só técnica
**Why human:** É uma decisão de arquitetura/produto tomada autonomamente pelo executor sem pergunta prévia (o contrato de autonomia permite isso quando a evidência é dura o bastante), mas o milestone ainda não foi "shipped" — este é o ponto correto do fluxo para o Alex validar ou reverter antes do merge para `main`/próximo milestone

#### 2. Decidir sobre WR-01 (observabilidade de `armada` sem prêmio)

**Test:** Ler `11-REVIEW.md` seção WR-01 e a entrada correspondente em `decisoes-autonomas-v1.2.md`
**Expected:** Escolher entre estender `pendente_desde` para cobrir "sem prêmio de entrada", criar um contador separado, ou aceitar o estado atual — nenhuma opção é urgente (resultado financeiro final já está correto)
**Why human:** Trade-off de rastreabilidade vs. escopo de mudança — decisão de produto, não bug de correção

#### 3. Decidir sobre WR-02 (fallback morto de `preco_entrada`)

**Test:** Ler `11-REVIEW.md` seção WR-02
**Expected:** Decidir se vale endurecer agora um caminho hoje inalcançável, ou documentar e esperar um segundo produtor de `executada_simulada` aparecer
**Why human:** Risco teórico, não realizado — decisão de investimento de esforço

### Gaps Summary

Nenhum gap bloqueante. Todas as 9 truths observáveis (mapeadas aos 5 Success Criteria do ROADMAP + aos must_haves consolidados dos 3 planos) foram verificadas por leitura direta de código, execução real da suíte de teste (85 testes da fase + 1674 da suíte canônica completa, ambos rodados por este verificador, não apenas citados da SUMMARY), e confirmação independente das duas evidências duras que sustentam o ADR-022.

O status é `human_needed`, não `passed`, porque:
1. Duas truths carregam desvio do texto LITERAL do ROADMAP (SC #2 e #4), resolvido por uma reinterpretação arquitetural bem fundamentada (ADR-022) mas ainda não formalmente aceita por um humano — sugestão de override incluída no frontmatter, pronta para o Alex assinar.
2. O próprio processo já identificou 2 itens (WR-01, WR-02) para decisão do Alex, e esta verificação os herda como itens de verificação humana, não como gaps técnicos — consistente com a instrução explícita da tarefa de não tratá-los como falha de verificação.

Nenhum BLOCKER. A propriedade mais crítica da fase — a simulação do ciclo de vida nunca toca `optionPositions`/`cash`/`history` — foi reconfirmada de forma independente por este verificador tanto por leitura de fonte (zero import de `store`, zero menção aos 4 nomes de função de escrita de opção) quanto por execução real do teste de comportamento que compara a carteira antes/depois de um ciclo completo.

---

*Verified: 2026-08-28*
*Verifier: Claude (gsd-verifier)*
