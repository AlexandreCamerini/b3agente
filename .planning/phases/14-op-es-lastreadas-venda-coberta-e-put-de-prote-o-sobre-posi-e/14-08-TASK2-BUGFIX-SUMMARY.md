---
phase: 14-opcoes-lastreadas
plan: 08
subsystem: api
tags: [options, covered-call, protective-put, bugfix, deterministic-proposal]

# IMPORTANT — scope note
# This SUMMARY covers the targeted bugfix found by the developer (Alex)
# during Task 2 (checkpoint:human-verify) of plan 14-08 — the live UI
# verification step. It is NOT a new plan; it is a single atomic bugfix
# commit against the same phase, executed outside the plan's task
# structure per explicit executor instructions (STATE.md/ROADMAP.md are
# NOT updated by this executor — the orchestrator owns those writes).

# Dependency graph
requires:
  - phase: 14-opcoes-lastreadas
    plan: "03"
    provides: "opcoes_lastreadas.propor() — motor puro de proposta (mantido intocado)"
  - phase: 14-opcoes-lastreadas
    plan: "04"
    provides: "rotas HTTP lastreada/abrir e lastreada/fechar — padrão de fetch de cadeia keyed ao underlying+expiration da posição, reusado aqui"
  - phase: 14-opcoes-lastreadas
    plan: "08"
    provides: "achado ao vivo do bug (Task 2, checkpoint humano) — este commit é o fix"
provides:
  - "opcoes_lastreadas.proposta_fechar(pos_opcao, chain, modo, hoje): função pura irmã de propor(), localiza o MESMO contrato já aberto por contractSymbol em vez de re-escolher"
  - "GET /api/options/proposta/{ticker} detecta posição lastreada já aberta ANTES de chamar propor()/pipeline técnico e usa proposta_fechar() nesse caso — contractSymbol estável entre chamadas"
affects: [14-08-task-2-checkpoint]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Função 'irmã' pura ao lado de um motor stateless existente, em vez de adicionar estado/memória ao motor original — propor() continua 100% puro e inalterado; proposta_fechar() cobre o caso 'já existe posição' com a MESMA leitura do dado já persistido, nunca uma nova escolha"

key-files:
  created: []
  modified:
    - server/app/opcoes_lastreadas.py
    - server/app/main.py
    - server/tests/test_opcoes_lastreadas_proposta.py
    - server/tests/test_opcoes_lastreadas_rotas.py
    - .planning/phases/14-op-es-lastreadas-venda-coberta-e-put-de-prote-o-sobre-posi-e/deferred-items.md

key-decisions:
  - "opcoes_lastreadas.propor() ficou byte-a-byte intocado — é módulo puro documentado como tal; o caso 'posição já aberta' ganhou uma função nova (proposta_fechar), não um parâmetro extra em propor() que forçaria I/O ou estado dentro de um motor que hoje não tem nenhum."
  - "A rota GET /api/options/proposta/{ticker} decide qual caminho seguir (fechar vs propor) usando o MESMO discriminador que o front já usa para separar posições lastreadas de legado (p.lastro truthy) — nenhum campo novo, nenhuma superfície nova."
  - "Quando existe posição aberta, o pipeline técnico (candle_provider.get_quote + technical_snapshot.get + setups.plano_do_resultado) NUNCA é chamado — não só corrige o bug, é uma otimização real: o plano técnico não influencia mais a proposta de fechamento."
  - "tipo em proposta_fechar() é um binário seguro (side=='vendida' → call_coberta, senão put_protecao) porque o schema de optionPositions só grava 'vendida' (abrir_call_coberta) ou 'comprada' (comprar_put_protecao) — nunca um terceiro valor; não há branch de erro para side desconhecido porque o dado de entrada é uma leitura de posição já validada na escrita."
  - "Manchete de fechamento reusa o texto de ABERTURA de propor() ('Vender N calls...'/'Comprar N puts...') — intencional para esta correção pontual (consistente com o que o Plano 06 já publicou e o Alex já aprovou); flagrado como observação de copy não corrigida, registrado em deferred-items.md."

requirements-completed: []

# Metrics
duration: ~35min
completed: 2026-08-31
---

# Phase 14 Plan 08 (Task 2 bugfix): proposta de fechamento estável para posições lastreadas

**`opcoes_lastreadas.proposta_fechar()` (função pura nova) faz `GET /api/options/proposta/{ticker}` devolver sempre o MESMO `contractSymbol` da posição já aberta, em vez de deixar `propor()` (stateless) re-escolher um contrato diferente a cada chamada — o bug que fazia o CTA "Recomprar/fechar" desaparecer do front depois da primeira operação.**

## Performance

- **Duration:** ~35min
- **Completed:** 2026-08-31
- **Tasks:** 1 (bugfix atômico, fora da estrutura de tasks do plano — ver nota de escopo no topo)
- **Files modified:** 5 (2 código, 2 testes, 1 registro de deferred-item)

## Accomplishments

- **Bug reproduzido e confirmado por leitura de código**: `GET /api/options/proposta/{ticker}` sempre chamava `opcoes_lastreadas.propor()`, que é STATELESS e re-deriva qual contrato propor do zero a cada chamada (strike mais próximo do spot atual + leitura técnica atual). O front (`PropostaLastreada`, `web/src/App.jsx:3010-3065`) casa uma posição já aberta com a proposta atual SÓ por `contractSymbol` idêntico (`posAberta`, `App.jsx:3216-3217`) para decidir se mostra o CTA "Recomprar/fechar". Como `propor()` podia escolher um contrato DIFERENTE numa chamada posterior (spot moveu → outro "strike mais próximo"; veredito técnico mudou → outro `tipo`), o CTA de fechar sumia silenciosamente depois da primeira operação — exatamente o que o Alex reproduziu ao vivo na verificação da Task 2.
- **Fix**: nova função pura `opcoes_lastreadas.proposta_fechar(pos_opcao, chain, modo, hoje)`, irmã de `propor()` (que fica intocada — reusa `_dias_ate`, `_label_liquidez`, `liquidity_score`, `skill_ref.num_br`/`opcoes_lastreadas_txt`). Dado uma posição lastreada JÁ ABERTA e uma cadeia já buscada (pelo chamador, keyed ao `underlying`+`expiration` da posição — mesmo padrão da rota irmã `options_lastreada_fechar`), localiza o MESMO contrato por `contractSymbol == pos_opcao["id"]` e monta a proposta com os campos da PRÓPRIA posição (contratos, strike, lastro), só atualizando o prêmio pelo `lastPrice` atual do mesmo contrato. Nunca re-escolhe. Cadeia degradada, contrato sumido da cadeia atual, ou sem `lastPrice` válido → sempre `{"proposta": None, "motivo": "degradado"}` (CLAUDE.md princípio 4: nunca inventar prêmio).
- **Rota `options_proposta` (`server/app/main.py`) reorganizada**: busca `optionPositions` mais cedo e detecta `pos_op_aberta` (mesmo discriminador `lastro` truthy que o front já usa) ANTES de qualquer chamada a `propor()`/pipeline técnico. Com posição aberta: busca a cadeia TARGETED (`get_options(t, pos_op_aberta.get("expiration"))`) e chama `proposta_fechar()` — o pipeline técnico (`candle_provider.get_quote`, `technical_snapshot.get`, `setups.plano_do_resultado`) nem é executado nesse ramo, uma otimização real além do fix. Sem posição aberta: comportamento 100% preservado (gate de `providerStatus` → gate de `qty_livre` → snapshot técnico → `propor()`).
- **Testes**: 6 unit tests novos para `proposta_fechar()` isolado (degradado, contrato sumido, sem `lastPrice`, sucesso call/put, estabilidade quando `propor()` divergiria) + 2 regression tests HTTP novos (`test_opcoes_lastreadas_rotas.py`) que abrem uma call coberta de verdade e provam que uma segunda chamada à rota de proposta devolve o MESMO `contractSymbol`, inclusive com o plano técnico mockado para o que faria `propor()` divergir para `sem_setup`.

## Task Commits

1. **Fix: proposta_fechar() + rota + testes** - `869fe07` (fix)
2. **Registro do achado de copy (manchete de fechamento) + este SUMMARY** - (commit seguinte, ver abaixo)

## Files Created/Modified

- `server/app/opcoes_lastreadas.py` - `proposta_fechar()` nova (função pura, irmã de `propor()`, que fica intocada)
- `server/app/main.py` - `options_proposta` detecta posição aberta antes de chamar `propor()`, usa `proposta_fechar()` + fetch de cadeia targeted nesse caso
- `server/tests/test_opcoes_lastreadas_proposta.py` - 6 unit tests novos (Parte 3: `proposta_fechar`)
- `server/tests/test_opcoes_lastreadas_rotas.py` - 2 regression tests HTTP novos (proposta estável após abrir, inclusive com plano técnico divergente)
- `.planning/phases/14-op-es-lastreadas-venda-coberta-e-put-de-prote-o-sobre-posi-e/deferred-items.md` - achado de copy (manchete de fechamento reusa texto de abertura), não corrigido, flagrado

## Decisions Made

Ver `key-decisions` no frontmatter — resumo: `propor()` fica puro/intocado; `proposta_fechar()` cobre o caso "já existe posição" lendo o dado já persistido (nunca re-escolhendo); a rota decide o caminho pelo mesmo discriminador (`lastro` truthy) que o front já usa; pipeline técnico é pulado quando há posição aberta (otimização real).

## Deviations from Plan

Este NÃO é um plano formal (é um bugfix de checkpoint), então "Deviations from Plan" não se aplica no sentido usual. A única decisão de escopo tomada durante a execução:

**1. [Rule 4-adjacente, mas resolvida por spec] Manchete de fechamento reusa texto de abertura**
- **Found during:** implementação de `proposta_fechar()` — o texto de `OPCOES_LASTREADAS["operador"]["call_coberta"]` diz "Vender N call(s)...", verbo de ABERTURA, mesmo quando a proposta é de FECHAMENTO de uma posição já aberta.
- **Decisão:** a especificação da task pediu explicitamente reusar as MESMAS chaves de vocabulário que `propor()` já usa para o `tipo` (não inventar copy nova) — decisão de produto já fechada no Plano 06/aprovada pelo Alex. Seguido à risca; a estranheza da frase no estado já-aberto foi FLAGRADA, não corrigida (registrado em `deferred-items.md`, Plano 08/Task 2, com fix sugerido para quem pegar).
- **Files modified:** nenhum além do já commitado (é uma decisão de não-mudança).
- **Committed in:** `869fe07` (a decisão de reuso é parte do fix; o registro do flag está no commit seguinte).

**Total deviations:** 0 auto-fixes de Rule 1-3 (nenhum bug novo encontrado fora do escopo do próprio fix); 1 observação de copy flagrada e deliberadamente não corrigida (fora do escopo literal deste bugfix, decisão de produto já fechada).
**Impact on plan:** Nenhum — a correção resolve exatamente o bug relatado (CTA de fechar sumindo) sem tocar em texto/copy que já foi aprovado.

## Issues Encountered

- **`server/.venv` ausente neste worktree** (mesmo padrão de planos anteriores da Fase 14 — worktrees não copiam diretórios não versionados). Resolvido rodando os testes com o interpretador do venv do clone principal (`/Users/acamerini/dev/bolsia/b3-agente/server/.venv/bin/python`) a partir do `cwd` do worktree (`server/`), garantindo que o pacote `app` resolvido fosse o do worktree (editado), não o do clone principal (que nem tem `opcoes_lastreadas.py` — Fase 14 ainda não está mergeada em `main`). `bash scripts/executar.sh --testes` (suíte canônica completa) rodou normalmente via `scripts/test.sh`, que já resolve esse mesmo caso (comentário no próprio script: "O venv vive no CLONE PRINCIPAL... rodando de um worktree, `$SERVER_DIR/.venv` não existe").
- Nenhum bloqueio de teste, nenhuma dependência nova instalada.

## User Setup Required

None — nenhuma configuração de serviço externo necessária. Fix é puramente de código de servidor (Python), sem novo env var, sem nova rota, sem mudança de schema.

## Next Phase Readiness

- **O fix resolve o achado da Task 2 (checkpoint humano) do plano 14-08.** A sessão orquestradora com canal ao vivo com o Alex deve re-verificar o cenário específico (abrir call coberta, pedir a proposta de novo, confirmar que o CTA "Recomprar/fechar" continua aparecendo) antes de considerar a Task 2 aprovada.
- **Nenhuma publicação de front foi feita nesta correção** — é 100% backend (`server/app/*.py`). O front já publicado em `F10-20260831-01` (Task 1 do 14-08) não precisa de rebuild para este fix funcionar; `web/src/App.jsx` não foi tocado (a lógica de `posAberta` do front já estava correta, só recebia um `contractSymbol` instável do backend).
- **`bash scripts/executar.sh --testes` verde**: 1814 passed, 1 skipped (backend, +8 vs. os 1806 anteriores — os 8 testes novos deste fix), 108/108 `.mjs` (web, sem regressão, sem mudança de front esperada).
- `npx vite build` NÃO foi rodado — nenhum arquivo `web/src/*` foi tocado por este fix (instrução explícita da task: pular quando claramente não se aplica).
- STATE.md e ROADMAP.md NÃO foram atualizados por este executor — por instrução explícita, o orquestrador que fez o merge deste worktree é quem faz essas escritas.

---
*Phase: 14-opcoes-lastreadas*
*Bugfix completed: 2026-08-31*
