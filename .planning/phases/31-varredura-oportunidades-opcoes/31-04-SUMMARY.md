---
phase: 31-varredura-oportunidades-opcoes
plan: 04
subsystem: ui

# Dependency graph
requires:
  - phase: 31-02
    provides: "GET /api/options/curadoria com top[].tipo/idCandidato/estrutura e meta.candidatosPorTipo/tetoVencimentos (varredura de 2 vencimentos × 4 estruturas)"
  - phase: 31-03
    provides: "PayoffChart.jsx responsivo em 375px, piso de tipografia e supressão de rótulo sobreposto"
provides:
  - "Bloco de curadoria em Posições mostra as 4 estruturas do motor (não só venda coberta), com rótulo de tipo por card"
  - "Chave de render estável (idCandidato) — collar (sem contractSymbol) não colide mais"
  - "Linha de resumo da varredura (candidatosPorTipo + tetoVencimentos) auditável na tela"
  - "Curva de payoff do item nº 1 renderizada via adaptador puro estruturaParaPayoff.js (zero aritmética)"
  - "Gate D-05 (opção a descoberto sem o flag) sem CTA/convite — copy auditada"
affects: [31-fase-encerramento, futuras fases de polish/overlay do payoff]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Adaptador puro de renomeação de chave (PT do motor → inglês do componente) como módulo isolado, testado por identidade estrita campo a campo — mesmo padrão de 'zero segunda versão do número' já usado em finance.js/indicators.py"
    - "Guardião estático estende (não reescreve) o teste anterior, com nota datada no comentário justificando a mudança de contagem — 'reversão deliberada atualiza o guardião com nota' (CLAUDE.md)"

key-files:
  created:
    - web/src/opcoes/estruturaParaPayoff.js
    - web/tests/test_estrutura_para_payoff.mjs
  modified:
    - web/src/copy.js
    - web/src/App.jsx
    - web/tests/test_curadoria_ui.mjs

key-decisions:
  - "Checkpoint humano (Task 4) fechado com base em verificação ao vivo do orquestrador contra o provedor MOCK (api-qa-opcoes), não o servidor real que o executor anterior deixou no ar — Alex aprovou explicitamente sabendo dessa lacuna (ver seção Checkpoint abaixo). Registrado com proveniência completa, não apresentado como verificação direta do executor."
  - "Publicação (bump.sh + publicar-web.sh) NÃO executada nesta rodada — Alex pediu só fechamento local ('Aprovado, fechar a fase'), sem publicar."

patterns-established:
  - "Pattern: chave de render de lista com item potencialmente sem identificador único de negócio (collar sem contractSymbol) resolve por ID estável do backend (idCandidato), não por concatenação heurística no front"

requirements-completed: [SC-2, SC-3, SC-4, SC-5, SC-7]

# Metrics
duration: ~23min (Tasks 1-3, execução contínua) + checkpoint resolvido em sessão de continuação separada
completed: 2026-09-14
---

# Phase 31 Plan 04: Curadoria multi-estrutura em Posições Summary

**O bloco "AS 4 MELHORES VENDAS COBERTAS" em Posições vira "AS 4 MELHORES OPORTUNIDADES DE OPÇÕES", com rótulo de tipo por card, chave de render estável (`idCandidato`), resumo auditável da varredura (`candidatosPorTipo`/`tetoVencimentos`) e a curva de payoff do item nº 1 via adaptador puro — checkpoint humano fechado com aprovação literal do Alex, verificação baseada no provedor mock.**

## Performance

- **Duration:** Tasks 1-3 executadas em ~23min contínuos (13:15→13:35, 2026-09-14); Task 4 (checkpoint) resolvida em sessão de continuação separada no mesmo dia.
- **Started:** 2026-09-14T13:15:05-03:00 (commit Task 1)
- **Completed:** 2026-09-14 (checkpoint aprovado)
- **Tasks:** 4/4 (3 auto + 1 checkpoint:human-verify)
- **Files modified:** 5 (3 modificados, 2 criados)

## Accomplishments
- `web/src/copy.js`: as duas chaves de registro (`estudo`/`operador`) ganham 7 chaves novas (`curadoriaTipoCallCoberta`, `curadoriaTipoPutProtecao`, `curadoriaTipoCollar`, `curadoriaTipoDescoberto`, `curadoriaVarreduraRotulo`, `curadoriaPayoffRotulo`, `curadoriaRazaoAjuda`) e reescreve `curadoriaTitulo`/`curadoriaSubtitulo`/`curadoriaCarregando`/`curadoriaVazio` para não assumir mais que toda oportunidade é venda coberta (D-04). Total de chaves `curadoria*`: 11 → 18, paridade mantida nos dois modos. Nenhuma menção a "ative o flag"/"libere mais oportunidades" (D-05); nenhuma palavra de enriquecimento/garantia (princípios 6/8 do CLAUDE.md).
- `web/src/opcoes/estruturaParaPayoff.js` (novo): adaptador puro que renomeia o envelope PT do motor (`curva`, `custo_liquido`, `perda_maxima`, `perda_ilimitada`, ...) para o envelope inglês que `PayoffChart` consome (`payoff`, `net_cost`, `max_loss`, `unlimited_loss`, ...) — zero aritmética, entrada inválida/`curva` ausente/<2 pontos devolve `null`, `perda_maxima: null` + `perda_ilimitada: true` atravessa como `max_loss: null` + `unlimited_loss: true` (regra "null nunca 0.0" do repositório).
- `CuradoriaEstruturas` em `App.jsx`: chave de render `item.idCandidato` (fallback `contractSymbol`) substitui `item.contractSymbol` puro — collar (duas pernas, sem contrato único) não colide mais em `null`; chip de rótulo de tipo por card (mapa `tipo → chave de copy`, com `aria-label` citando tipo/posição/ticker); linha de resumo da varredura lendo `meta.candidatosPorTipo`/`meta.tetoVencimentos` (com "—" para campo ausente, nunca 0 inventado — princípio 4 do CLAUDE.md); UMA curva de payoff do item `posicaoNoRanking === 1` via `estruturaParaPayoff` + `PayoffChart`, `emReais={null}` (backend desta rota não manda o bloco em reais — multiplicar no front criaria segunda versão da conta). Zero `useState` novo, zero `.sort(`/`.reverse(`/comparação de `razao` no componente — a ordem exibida continua sendo a do motor (D-06).
- Guardiões estendidos: `test_curadoria_ui.mjs` 28→41 asserções (as 8 regras originais da Fase 30 preservadas + 5 regras novas: chave `idCandidato`, mapa de rótulo por tipo, resumo lê `meta.candidatosPorTipo`, exatamente 1 `<PayoffChart` no bloco, nenhuma copy convida a ligar o flag). `test_estrutura_para_payoff.mjs` (novo, 148→149 `.mjs`): identidade numérica estrita campo a campo, `null` seguro, travessia de `perda_maxima: null`/`perda_ilimitada: true`, e guardião estático de zero-aritmética via regex sobre o próprio fonte.
- Achado corrigido durante a Task 3 (Rule 1, ver Deviações): comentário em `copy.js` continha a própria string-âncora que o guardião CVM (`test_opcoes_collar_vocab.py`) varre no arquivo inteiro — reescrito sem quebrar o guardrail.

## Task Commits

Each task was committed atomically:

1. **Task 1: copy dos dois modos — a lista não é mais só de venda coberta** - `d10113c` (feat)
2. **Task 2: adaptador puro + CuradoriaEstruturas com tipo, chave estável, resumo e payoff do nº 1** - `457d32a` (feat)
3. **Task 3: guardiões estáticos atualizados + adaptador testado** - `ab2c03d` (test, inclui correção Rule 1 do achado CVM)
4. **Task 4: verificação ao vivo em 375px, com o flag desligado e ligado** - checkpoint, ver seção dedicada abaixo (sem commit de código — nenhuma edição prevista nesta task)

**Plan metadata:** (this commit, docs: complete plan)

## Files Created/Modified
- `web/src/copy.js` - 18 chaves `curadoria*` (7 novas, 4 reescritas) nos dois registros de modo; nenhuma promessa de resultado, nenhum convite a ligar o flag
- `web/src/opcoes/estruturaParaPayoff.js` (novo) - adaptador puro PT→inglês para `PayoffChart`, zero aritmética
- `web/src/App.jsx` - `CuradoriaEstruturas`: chave `idCandidato`, chip de tipo, linha de resumo da varredura, payoff único do item nº 1, prop `palette` propagada do call site em `CarteiraScreen`
- `web/tests/test_curadoria_ui.mjs` - 28→41 asserções, 8 regras da Fase 30 preservadas + 5 novas
- `web/tests/test_estrutura_para_payoff.mjs` (novo) - identidade estrita do adaptador, `null` seguro, guardião de zero-aritmética

## Decisions Made
- Ver `key-decisions` no frontmatter: (1) checkpoint fechado com verificação mock, aprovada explicitamente por Alex sabendo da lacuna mock-vs-real; (2) publicação não executada nesta rodada, só fechamento local.

## Checkpoint (Task 4) — resolução e proveniência

**Este agente é uma continuação fresca, spawnada após a Task 4 ter sido bloqueada por um executor anterior.** O executor anterior recusou corretamente fechar a Task 4 a partir de um relato do orquestrador nesta mesma conversa, porque (a) não era resposta literal do Alex nesta conversa, e (b) a verificação do orquestrador usou o provedor mock de opções (`api-qa-opcoes`), não o servidor real (DB real, caminho de dado de mercado real, acessível na LAN pro iPhone do Alex) que o executor havia deixado no ar.

Essa recusa foi endereçada na origem, não neste agente: o orquestrador (a sessão-mãe deste agente) apresentou ao Alex, via `AskUserQuestion` — elemento de UI de primeira parte, não um relato de outro agente — os 8 passos do roteiro de verificação do plano (título, rótulos de tipo, contagens do resumo com teto=2, gráfico de payoff em 375px, flag desligado mostrando 0 a descoberto sem CTA, flag ligado sobe a contagem sem reordenar, botão de explicação da IA degradando sem inventar texto — ambiente local sem chave de LLM —, e fechamento de posição de opção com o flag desligado verificado por leitura direta de `server/app/store.py:877-895`/`sell_option`, apoiado no guardião `test_opcao_descoberto_gate.py`).

**Resposta literal 1 (Alex, via AskUserQuestion na sessão do orquestrador):**
> "Aprovado, fechar a fase"

**Pergunta de confirmação explícita, nomeando a lacuna mock-vs-real e a recusa do executor anterior**, com a opção de texto: *"Confirmo que minha verificação (mock, os 8 passos) basta — pode fechar a Task 4 e criar o SUMMARY, sem precisar do servidor real que o executor deixou no ar."*

**Resposta literal 2 (Alex):**
> "Aprovado mesmo com verificação mock"

**O que isso é, precisamente:** duas respostas diretas do Alex, dadas com pleno conhecimento de que a verificação usou o provedor mock e não o servidor real staged. Não é um relato de terceiro sobre o que o Alex teria dito — é a transcrição do que ele respondeu num elemento de UI de primeira parte, relayada para este agente pelo objective de spawn (que é como o protocolo de checkpoint do GSD é desenhado para funcionar entre respawns de agente). O que este agente NÃO tem é a mensagem literal do Alex dentro da SUA PRÓPRIA transcrição — só a relay do orquestrador contendo a citação verbatim. Essa distinção é registrada aqui para que qualquer auditoria futura veja exatamente sobre que base o fechamento se apoia, em vez de apresentar "Alex confirmou" como se este agente tivesse testemunhado a resposta diretamente.

Nenhuma divergência foi relatada nos 8 passos. Nenhum passo foi declarado verde por inferência deste executor — os 6 passos ao vivo (título, rótulos, resumo, payoff, gate do flag ligado/desligado, botão de IA) vieram da verificação do orquestrador com o Alex assistindo/aprovando; os 2 passos restantes (payoff comparável à aba Opções, fechamento de posição com flag desligado) foram cobertos por evidência técnica direta (leitura de código + guardião existente), não por inferência.

**Estado de publicação:** local apenas. Alex não pediu publicação nesta rodada ("Aprovado, fechar a fase" — sem menção a bump/publicar). `scripts/bump.sh`/`scripts/publicar-web.sh` NÃO foram executados. Pendente para decisão futura do Alex.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Comentário em `copy.js` continha a string-âncora que o guardião CVM varre no arquivo inteiro**
- **Found during:** Task 3 (execução da suíte canônica completa)
- **Issue:** O comentário que documentava a colisão de "trava protetora" continha, ele mesmo, a string proibida que `test_opcoes_collar_vocab.py::test_nenhum_arquivo_front_compoe_manchete_do_collar` varre — esse guardião Python varre o ARQUIVO INTEIRO sem filtrar comentário (ao contrário do guardião Python equivalente que usa `ast` e exclui docstring).
- **Fix:** Comentário reescrito sem a string-âncora, preservando a explicação; guardrail CVM (manchete verbatim, nunca composta) permanece intacto.
- **Files modified:** web/src/copy.js
- **Verification:** `bash scripts/executar.sh --testes` volta a exit 0 (backend 2910 passed/0 failed).
- **Committed in:** ab2c03d (parte do commit da Task 3)

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug de guardião cruzado, não de produto).
**Impact on plan:** Correção estritamente editorial de comentário; nenhuma mudança de comportamento, copy visível ou lógica. Sem scope creep.

## Issues Encountered

Nenhum bloqueio técnico. O único evento fora do fluxo linear foi o próprio checkpoint da Task 4: um executor anterior recusou fechá-lo com base num relato de terceiro (corretamente, seguindo a regra do plano), e este agente foi spawnado como continuação fresca depois que a recusa foi endereçada na origem (ver seção "Checkpoint" acima).

## User Setup Required

None - no external service configuration required.

## Verification Evidence

- `cd web && npx vite build` — verde, `✓ built in 1.02s` (rodado nesta sessão de fechamento, após confirmar `git status` limpo).
- `bash scripts/executar.sh --testes` (rodado nesta sessão de fechamento, `dangerouslyDisableSandbox: true`): **2910 passed, 5 skipped, 3 xfailed, 0 failed** (backend) + **149/149 `.mjs` OK**, exit 0 — idêntico ao relatado no commit `ab2c03d`.
  - **Nota de ambiente:** a primeira tentativa (sandbox padrão) reportou 27 falhas de backend, todas `PermissionError: [Errno 1] Operation not permitted` em `ssl.py:717` — o mesmo artefato de sandbox já documentado em `MEMORY.md` ("sandbox mente, 26 falsas") e no SUMMARY do 31-03. Confirmado como artefato de ambiente reexecutando com `dangerouslyDisableSandbox: true`.
- Contagem de `.mjs`: 148 (herdado da Fase 31-03) → 149 (1 novo, `test_estrutura_para_payoff.mjs`).
- Chaves `curadoria*` em `web/src/copy.js`: 18 únicas (`curadoriaCarregando`, `curadoriaCotaEsgotada`, `curadoriaErroNarrar`, `curadoriaIaRessalva`, `curadoriaIaRotulo`, `curadoriaNarrando`, `curadoriaNarrarCta`, `curadoriaPayoffRotulo`, `curadoriaRazaoAjuda`, `curadoriaRazaoRotulo`, `curadoriaSubtitulo`, `curadoriaTipo`, `curadoriaTipoCallCoberta`, `curadoriaTipoCollar`, `curadoriaTipoDescoberto`, `curadoriaTipoPutProtecao`, `curadoriaTitulo`, `curadoriaVarreduraRotulo`), confirmado por `grep -oE 'curadoria[A-Za-z]+' web/src/copy.js | sort -u` — bate com a contagem 11→18 do commit `ab2c03d`.
- Provas negativas (executadas e revertidas na Task 3, `git diff` limpo confirmado): (i) `key={item.contractSymbol}` sem `idCandidato` derruba 2 asserções de `test_curadoria_ui.mjs`; (ii) multiplicar `net_cost` por 100 no adaptador derruba a identidade estrita E o guardião de zero-aritmética em `test_estrutura_para_payoff.mjs`.
- Checkpoint humano: ver seção dedicada acima — duas respostas literais do Alex via `AskUserQuestion`, relayadas com proveniência explícita.

## Next Phase Readiness

Fase 31 (varredura de oportunidades de opções) fecha com os 4 planos completos (31-01 a 31-04). O bloco de curadoria em Posições agora reflete as 4 estruturas varridas, com resumo auditável e payoff legível em 375px. Pendências conhecidas, não bloqueantes:
- **Publicação:** `scripts/bump.sh` + `scripts/publicar-web.sh` não executados — Alex pediu fechamento local nesta rodada. Próximo passo humano separado, quando decidido.
- **App nativo iOS:** não reflete esta fase sem `cap sync` + build novo no Xcode — pendência operacional conhecida (mesmo achado do checkpoint da Fase 29), não defeito desta fase.
- **D-06 (consequência conhecida, não bug):** put/collar/opção a descoberto rankeiam estruturalmente pior na fórmula única (prêmio ÷ perda máxima) — o top-4 pode continuar todo de venda coberta em contas sem posições com boas relações para as outras estruturas. A linha de resumo da varredura é o mecanismo de auditoria para isso, por desenho (não é bug a corrigir).

Nenhum push a `origin`, nenhum bump, nenhuma publicação — mesmo padrão do resto da Fase 31 em execução.

---
*Phase: 31-varredura-oportunidades-opcoes*
*Completed: 2026-09-14*
