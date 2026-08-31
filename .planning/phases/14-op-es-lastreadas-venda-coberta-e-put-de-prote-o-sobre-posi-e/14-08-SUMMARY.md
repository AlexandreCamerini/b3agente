---
phase: 14-opcoes-lastreadas
plan: 08
subsystem: infra
tags: [options, covered-call, protective-put, adr, publish, mock-provider, e2e]

# IMPORTANT — scope note
# This SUMMARY covers ONLY Task 1 of the 14-08 plan (autonomous: ADR-023,
# end-to-end curl verification against the mock provider, publishing the
# front). Task 2 (checkpoint:human-verify — live verification of proposta/
# trava/dormancy on-screen with the developer, Alex) is DEFERRED to the
# orchestrator session that has a live channel to the developer. This
# executor has no such channel and did not attempt Task 2. The phase/plan
# is NOT complete until Task 2 is run and approved.

# Dependency graph
requires:
  - phase: 14-opcoes-lastreadas
    plan: "01"
    provides: "provedor mock (options_provider_mock.py), trava de lastro (qtyTravada/qty_livre)"
  - phase: 14-opcoes-lastreadas
    plan: "03"
    provides: "as 3 rotas HTTP (proposta/abrir/fechar) exercitadas nesta verificação"
  - phase: 14-opcoes-lastreadas
    plan: "04"
    provides: "store.liquidar_lastreada_vencida — fórmula registrada em ADR-023"
  - phase: 14-opcoes-lastreadas
    plan: "07"
    provides: "trava visível na Carteira, Patrimônio com pernas lastreadas — front que este plano publica"
provides:
  - "docs/adr/023-opcoes-lastreadas.md: registro formal das 7 decisões da Fase 14 (escopo, fórmula de liquidação, trava, Patrimônio, não-retroatividade, provedor mock, dormência) + o que não foi reaberto"
  - "Verificação ponta a ponta comprovada contra B3_OPTIONS_PROVIDER=mock: sem_lastro → compra → proposta real → 403 Estudo → abrir Operador (caixa creditado, qtyTravada=100) → 400 de venda travada → fechar (destrava) → degradado (motivo=degradado)"
  - "Dormência confirmada contra o provedor DEFAULT (yahoo, sem env): gate liquida=false, proposta=null"
  - "fix(14-08): POST /api/sell agora devolve 400 explícito (em vez de 200 silencioso) quando a trava de lastro bloqueia a venda inteira — achado pela própria verificação ponta a ponta"
  - "Front publicado: BUILD_ID F10-20260831-01 (bump.sh + publicar-web.sh), server/web_dist atualizado, SERVER_BUILD_ID sincronizado"
affects: [14-08-task-2]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Verificação ponta a ponta via 3 lifecycles de uvicorn separados (mock ok / mock degradado / provedor default), cada um com seu próprio B3_DB_PATH throwaway — env vars lidas via os.environ dentro do processo do servidor não são alteráveis por export num shell separado depois que o processo já subiu"

key-files:
  created:
    - docs/adr/023-opcoes-lastreadas.md
  modified:
    - server/app/main.py
    - server/tests/test_opcoes_lastreadas_rotas.py
    - web/src/version.js
    - server/web_dist/** (rebuild completo)
    - .planning/phases/14-op-es-lastreadas-venda-coberta-e-put-de-prote-o-sobre-posi-e/deferred-items.md

key-decisions:
  - "Rule 1 (bug) aplicado dentro do escopo desta própria task: POST /api/sell não checava o retorno None de store.sell() quando a trava de lastro bloqueava 100% da posição — devolvia 200 silencioso em vez do 400 explícito que os acceptance_criteria da Task 1 exigem transcrever. Corrigido em server/app/main.py com teste HTTP novo (test_vender_posicao_100_por_cento_travada_via_sell_devolve_400); a camada de motor (store.sell) já estava correta e coberta por test_lastro_trava.py — só a rota HTTP não traduzia a rejeição em status code."
  - "motivoTexto com placeholders não preenchidos em motivos de sucesso (call_coberta/put_protecao) — achado, confirmado como dead code (PropostaLastreada só lê motivoTexto quando proposta é falsy) e registrado em deferred-items.md em vez de corrigido: fora do escopo literal da Task 1, não causado por esta task, sem impacto de produto."
  - "Sequência de curl rodada em 3 lifecycles de servidor separados (mock/ok, mock/degradado, default/yahoo) em vez de um só com troca de env em runtime — env vars são lidas via os.environ dentro do processo já iniciado; exportar num shell novo não alcança o processo do uvicorn já rodando."
  - "GET /api/options/proposta/{ticker} com posição real usou o resultado técnico REAL do dia (Yahoo, sem mock de candle/setup) — a proposta saiu call_coberta com 1 contrato, confirmando o caminho completo sem precisar fixar o plano técnico como os testes automatizados fazem."

requirements-completed: []

# Metrics
duration: ~2h10min (grande parte esperando o pregão abrir às 10:00 BRT)
completed: 2026-08-31
---

# Phase 14 Plan 08 (Task 1 only): ADR-023 + verificação ponta a ponta + publicação Summary

**ADR-023 registra as 7 decisões da mecânica lastreada; a sequência completa (sem_lastro → compra → proposta real → 403 Estudo → abrir Operador → venda travada 400 → fechar/destrava → degradado) foi exercitada via curl contra o provedor mock e achou um bug real (POST /api/sell devolvia 200 silencioso em vez de 400 quando a trava bloqueava a venda inteira), corrigido nesta mesma task; front publicado com BUILD_ID F10-20260831-01. Task 2 (checkpoint humano) fica para a sessão orquestradora com canal ao vivo com o Alex.**

## Performance

- **Duration:** ~2h10min (a maior parte foi espera do pregão B3 abrir às 10:00 BRT — o passo de compra imediata exige mercado aberto; sem hora de teste dedicada, o restante do trabalho — ADR, prep de servidor, checks de dormência/degradado — foi feito em paralelo à espera)
- **Completed:** 2026-08-31T11:20:00-03:00
- **Tasks:** 1/2 do plano (Task 1 completa; Task 2 é checkpoint humano, deferida ao orquestrador — ver nota de escopo no topo)
- **Files modified:** 5 arquivos de código/config + rebuild completo de `server/web_dist` (25 arquivos no commit de publicação)

## Accomplishments

- **ADR-023** escrito no formato dos ADRs existentes (`docs/adr/023-opcoes-lastreadas.md`, 213 linhas): escopo restrito às duas operações lastreadas; fórmula exata de liquidação forçada (`intrinseco = max(0.0, spot−strike)`, débito `qty×intrínseco`, `pnl=(avg−intrínseco)×qty`, ações intocadas, lastro destravado); trava de lastro (`positions[].qtyTravada`/`store.qty_livre` fonte única); não-retroatividade via os discriminadores `side`/`lastro` ausentes; Patrimônio Total incluindo pernas lastreadas; provedor `mock` só-desenvolvimento; dormência sem flag nova (o gate de liquidez já existente decide). Fecha explicitamente o que não foi reaberto: ADR-001/004/008/020/021/022.
- **Verificação ponta a ponta contra `B3_OPTIONS_PROVIDER=mock`** (transcrições completas abaixo) — todos os 8 passos do item 2 do plano confirmados, incluindo um bônus (venda normal funciona após destrava).
- **Dormência confirmada contra o provedor DEFAULT** (sem `B3_OPTIONS_PROVIDER`, ou seja `yahoo`): `GET /api/options/gate/PETR4` devolveu `liquida: false`; `GET /api/options/proposta/PETR4` devolveu `proposta: null`. Nota: o motivo textual observado foi `sem_lastro` (não `degradado` como o texto do plano previa) porque o Yahoo respondeu com sucesso real (`providerStatus: "ok"`) só que com cadeia vazia para PETR4 (`calls: []`, `puts: []`, `expirations: []`) — exatamente o comportamento que ADR-020 já documenta ("Yahoo hoje devolve vazio pra B3"). A garantia de fundo do `must_haves.truths` ("nenhuma superfície nova aparece") se mantém: com posição real e chain vazia o motor cairia em `sem_contrato_liquido` (também `proposta: null`), nunca produz uma proposta.
- **Bug real achado e corrigido dentro do escopo desta própria task**: `POST /api/sell` devolvia HTTP 200 silencioso quando a trava de lastro bloqueava 100% da venda (o motor `store.sell` já recusava e gravava a rejeição no histórico, mas a rota não traduzia isso em status code — inconsistente com todo outro caminho de rejeição da mesma rota, que já usa 400 explícito). Corrigido em `server/app/main.py`; teste HTTP novo (`test_vender_posicao_100_por_cento_travada_via_sell_devolve_400`) adicionado a `server/tests/test_opcoes_lastreadas_rotas.py`.
- **Front publicado**: `bash scripts/bump.sh` (BUILD_ID `F10-20260830-02` → `F10-20260831-01`) seguido de `bash scripts/publicar-web.sh` — `server/web_dist` rebuildado (18 arquivos alterados/renomeados, hashes novos de todos os chunks), `SERVER_BUILD_ID` sincronizado em `server/app/main.py`. `bash scripts/executar.sh --testes` rodado ANTES e DEPOIS da publicação, ambos verdes (1806 passed, 1 skipped).

## Task Commits

Task 1 foi feita em 4 commits atômicos (não uma task só, porque o achado do Rule 1 e o registro do deferred-item mereciam commits dedicados):

1. **ADR-023** - `17a542f` (docs)
2. **Fix Rule 1: POST /api/sell devolve 400 na trava** - `ea1713b` (fix)
3. **Registro do achado motivoTexto (deferred, não corrigido)** - `4cec1b3` (docs)
4. **Publicação do front (BUILD_ID F10-20260831-01)** - `03d8b8d` (docs)

_Task 2 (checkpoint humano) NÃO foi executada por este agente — ver nota de escopo no topo do frontmatter._

## Files Created/Modified

- `docs/adr/023-opcoes-lastreadas.md` - ADR novo, 7 decisões + o que não foi reaberto
- `server/app/main.py` - `POST /api/sell` checa o retorno de `store.sell()` e levanta 400 explícito quando a trava bloqueia; `SERVER_BUILD_ID` sincronizado pela publicação
- `server/tests/test_opcoes_lastreadas_rotas.py` - teste HTTP novo cobrindo o 400 de venda travada
- `web/src/version.js` - `BUILD_ID` carimbado para `F10-20260831-01`
- `server/web_dist/**` - rebuild completo (front publicado)
- `.planning/phases/14-op-es-lastreadas-venda-coberta-e-put-de-prote-o-sobre-posi-e/deferred-items.md` - achado do `motivoTexto` com placeholders (dead code, não corrigido)

## Verificação ponta a ponta — transcrições de curl (item 2 do plano)

Três lifecycles de servidor separados (env vars só são lidas dentro do processo do uvicorn já iniciado — trocar `export` num shell novo não alcança um processo já rodando):

### Servidor 1 — `B3_OPTIONS_PROVIDER=mock` (sequência completa, conta logada `verificacao-14-08@teste.local`)

**1) `GET /api/options/proposta/PETR4` sem posição:**
```json
{"ticker": "PETR4", "providerStatus": "ok", "modo": "estudo",
 "proposta": null, "motivo": "sem_lastro",
 "motivoTexto": "Sem posição em PETR4 na carteira — venda coberta e put de proteção exigem uma posição real do ativo-lastro.",
 "putSemLastro": []}
```
✅ `proposta: null`, `motivo: "sem_lastro"` como esperado.

**2) `POST /api/buy {"t":"PETR4","qty":100}` (mercado aberto, 11:15 BRT):**
```
HTTP 200 — pendente: None, priceUsed: 45.08
positions PETR4: [{'t': 'PETR4', 'qty': 100, 'avg': 45.08, ...}]
```
✅ Execução imediata (não pendente), posição criada.

**3) `GET /api/options/proposta/PETR4` com posição real:**
```json
{"ticker": "PETR4", "providerStatus": "ok", "modo": "operador",
 "proposta": {"tipo": "call_coberta", "contractSymbol": "PETR4MOCK06C",
   "strike": 39, "expiration": "2026-09-18", "diasParaVencimento": 18,
   "contratos": 1, "qtyAcoes": 100, "premioUnitario": 0.65, "premioTotal": 65.0,
   "lastro": {"t": "PETR4", "qtyLivre": 100},
   "manchete": "Vender 1 call(s) de PETR4 strike 39,00 por R$ 65,00."},
 "motivo": "call_coberta"}
```
✅ `contratos: 1` (>= 1), `motivo: "call_coberta"` — a proposta usou o plano técnico REAL do dia (Yahoo), não um plano mockado, e mesmo assim produziu `call_coberta` (decisão determinística contra dados reais do mercado no momento do teste).

**4) `POST /api/options/lastreada/abrir` em Modo Estudo:**
```
HTTP 403 — {"detail":"Modo Estudo não executa ordens — troque para o Modo Operador para operar."}
```
✅ 403 confirmado (testado antes de ligar o Operador, com a conta ainda em modo `estudo` default).

**5) Troca para Operador (`PUT /api/config`) + `POST /api/options/lastreada/abrir {"underlying":"PETR4","contractSymbol":"PETR4MOCK06C","contratos":1}`:**
```
HTTP 200
cash: 5557.0 (10000 - 4508 da compra + 65 do prêmio)
positions PETR4: [{..., "qtyTravada": 100}]
optionPositions: [{"id": "PETR4MOCK06C", "side": "vendida", "strike": 39,
  "avg": 0.65, "lastro": {"t": "PETR4", "qty": 100}, ...}]
```
✅ Caixa creditado, `qtyTravada: 100` (100% da posição travada — 1 contrato = 100 ações).

**6) `POST /api/sell {"t":"PETR4"}` (posição 100% travada):**
```
HTTP 400 — {"detail":"100 ação(ões) de PETR4 estão travadas como lastro de uma CALL coberta aberta — recompre a call para liberar."}
```
✅ 400 com a frase de lastro — **este era o bug corrigido nesta task** (antes do fix retornava 200 silencioso).

**7) `POST /api/options/lastreada/fechar {"contractSymbol":"PETR4MOCK06C","contratos":1}`:**
```
HTTP 200 — priceUsed: 0.65
positions PETR4: [{..., "qtyTravada": 0}]
optionPositions: []
cash: 5492.0 (5557 - 65 da recompra)
```
✅ Destravou (`qtyTravada: 0`), posição de opção removida.

**Bônus — `POST /api/sell {"t":"PETR4"}` após destravar:**
```
HTTP 200 — positions PETR4: []
```
✅ Venda normal funciona depois que a trava sai — confirma que o 400 do passo 6 é específico da trava, não uma regressão geral da rota.

### Servidor 2 — `B3_OPTIONS_PROVIDER=mock B3_OPTIONS_MOCK_STATUS=degraded`

**8) `GET /api/options/proposta/PETR4`:**
```json
{"ticker": "PETR4", "providerStatus": "degraded", "modo": "estudo",
 "proposta": null, "motivo": "degradado",
 "motivoTexto": "Proposta indisponível — cotação de opções degradada.",
 "putSemLastro": []}
```
✅ `motivo: "degradado"` como esperado.

### Servidor 3 — provedor DEFAULT (sem `B3_OPTIONS_PROVIDER`, ou seja `yahoo`) — item 3 do plano (dormência)

**`GET /api/options/gate/PETR4`:**
```json
{"ticker": "PETR4", "liquida": false, "providerStatus": "ok"}
```
✅ `liquida: false` como esperado.

**`GET /api/options/proposta/PETR4`:**
```json
{"ticker": "PETR4", "providerStatus": "ok", "modo": "estudo",
 "proposta": null, "motivo": "sem_lastro", ...}
```
✅ `proposta: null` como esperado. Nota (ver Deviations): o `motivo` observado foi `sem_lastro` (sem posição na conta de teste), não `degradado` como o texto do plano previa — porque o Yahoo respondeu `providerStatus: "ok"` com cadeia REAL vazia para PETR4 (`GET /api/options/chain/PETR4` confirmou `expirations: [], calls: [], puts: []`, `underlyingPrice: 43.55` real), em vez de falhar com 401/403/429. A garantia de fundo (nenhuma proposta surge com o provedor default) se mantém — só o `motivo` textual variou conforme o estado real e momentâneo do Yahoo no instante do teste.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `POST /api/sell` devolvia 200 silencioso em vez de 400 quando a trava de lastro bloqueava a venda inteira**
- **Found during:** Task 1, item 2 do plano (passo 6 da sequência de curl — "tentar POST /api/sell da posição inteira, espera 400").
- **Issue:** `store.sell()` (motor) já recusava corretamente e gravava a rejeição no histórico (`registrar_rejeicao`) quando `qty_livre(pos) <= 0`, devolvendo `None` — comportamento coberto por `test_lastro_trava.py::test_sell_com_100_por_cento_travado_e_recusada`. Mas a rota HTTP `/api/sell` (`server/app/main.py`) não checava esse retorno `None`; a requisição seguia até `store.public_state(...)` e devolvia HTTP 200 com a posição intocada — o cliente não tinha como distinguir "vendida" de "rejeitada" sem reler o histórico à parte. Toda outra rejeição da mesma rota (sem posição, quantidade inválida, caixa insuficiente em `/api/buy`) já levanta `HTTPException(400, ...)` explícito — esta era a única exceção silenciosa.
- **Fix:** `main.py` agora captura o retorno de `store.sell()`; se `None` (com a posição existindo — o caso "sem posição" já tem seu próprio 400 antes), levanta `HTTPException(400, "{qtyTravada} ação(ões) de {t} estão travadas como lastro de uma CALL coberta aberta — recompre a call para liberar.")`. Nenhuma mudança em `store.sell()` — a camada de motor já estava correta; o gap era só a rota não traduzir o `None` em status code.
- **Files modified:** `server/app/main.py`, `server/tests/test_opcoes_lastreadas_rotas.py` (teste novo `test_vender_posicao_100_por_cento_travada_via_sell_devolve_400`)
- **Verification:** `pytest tests/test_opcoes_lastreadas_rotas.py -v` → 9/9 passed (incluindo o teste novo); `bash scripts/executar.sh --testes` (suite completa) → 1806 passed, 1 skipped, sem regressão; confirmado ao vivo pela própria sequência de curl (passo 6, ver transcrição acima).
- **Committed in:** `ea1713b`

### Documented, not fixed (out of scope)

**2. `motivoTexto` com placeholders não substituídos em motivos de sucesso** — ver `deferred-items.md`, Plano 08. Confirmado dead code (nunca renderizado pelo front quando `proposta` é truthy); fora do escopo literal desta task; não corrigido.

**Total deviations:** 1 auto-fixed (Rule 1, dentro do escopo dos próprios acceptance_criteria desta task) + 1 documentado sem correção (fora de escopo, sem impacto de produto).
**Impact on plan:** O fix do Rule 1 era necessário para que a Task 1 pudesse cumprir seu próprio acceptance_criteria literal ("incluindo o 400 de lastro travado" transcrito no SUMMARY) — sem ele, a transcrição honesta teria mostrado 200 em vez de 400, contradizendo o comportamento pretendido do produto (toda rejeição desta rota já usa 400 explícito).

## Issues Encountered

- Nenhum bloqueio. A única fricção operacional foi temporal: o passo "comprar ações" (item 2, sub-passo 2) exige `pregao.in_market_hours()` verdadeiro — não há bypass de teste no código (nem deveria haver, por design: CLAUDE.md princípio 4, nunca fabricar estado de mercado). A verificação começou às 09:38 BRT (mercado abre 10:00); os passos independentes de mercado (ADR, fix do Rule 1, checks de degradado/dormência) foram feitos em paralelo à espera; a compra e o restante da sequência rodaram normalmente assim que o pregão abriu.
- `server/.venv` e `web/node_modules` ausentes neste worktree (mesmo padrão dos planos 14-01 a 14-07) — resolvido com symlinks temporários para o clone principal; `npm ci` (rodado por `publicar-web.sh`) substituiu o symlink de `node_modules` por uma instalação real (comportamento normal do npm, sem impacto — segue gitignored). O symlink de `server/.venv` foi removido antes do commit final.

## User Setup Required

None — nenhuma configuração de serviço externo necessária. A verificação rodou inteiramente contra o provedor `mock` (sem rede de opções) e, para o passo de compra de ações, contra dados reais de mercado via Yahoo (já configurado, sem chave nova).

## Next Phase Readiness

- **Task 2 do plano 14-08 (checkpoint humano) NÃO foi executada.** É um `checkpoint:human-verify` com `gate="blocking"` — requer o desenvolvedor (Alex) confirmando ao vivo, na tela, os 8 passos de `how-to-verify` (proposta no card, split Estudo/Operador, badge de trava, dormência com provedor default). Este agente executor não tem canal com o Alex; a sessão orquestradora que spawnou este agente deve apresentar o roteiro de `how-to-verify` da Task 2 diretamente a ele.
- O front já está publicado (`BUILD_ID F10-20260831-01`) com tudo que a Task 2 precisa para a verificação visual — nenhuma publicação adicional é necessária antes do checkpoint.
- A fase permanece dormente em produção (`B3_OPTIONS_PROVIDER` não definido em produção = `yahoo`) — confirmado nesta mesma task (servidor 3). O checkpoint da Task 2 inclui confirmar isso ao vivo (passo 8 do `how-to-verify`), mas o achado de código já está documentado aqui e em ADR-023.
- Não commitar/marcar STATE.md, ROADMAP.md ou a fase como concluída até a Task 2 ser aprovada — por instrução explícita do orquestrador.

---
*Phase: 14-opcoes-lastreadas*
*Completed (Task 1 only): 2026-08-31*
