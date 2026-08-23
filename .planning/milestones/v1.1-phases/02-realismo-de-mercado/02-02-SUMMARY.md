---
phase: 02-realismo-de-mercado
plan: 02
subsystem: backend / rotas HTTP
tags: [pending-orders, market-status, MERC-01, MERC-02, MERC-03, MERC-04, ORDER_LOCK]
dependency-graph:
  requires:
    - server/app/pending_orders.py (plano 02-01: criar_compra, criar_venda, cancelar)
    - store.ORDER_LOCK (plano 02-01)
  provides:
    - "GET /api/market/status (público, MERC-01)"
    - "ramo pendente em POST /api/buy e POST /api/sell (MERC-02/03)"
    - "DELETE /api/orders/pending/{order_id} (MERC-04)"
    - "pet:evolucao com caixaReservado somado ao patrimônio"
  affects:
    - server/app/main.py
    - server/tests/test_ciclo_imediato_apos_carteira.py
    - server/tests/test_adr013_cobertura_rotas.py
tech-stack:
  added: []
  patterns:
    - "store.ORDER_LOCK reusado (mesma trava do plano 02-01) em volta da seção crítica síncrona de /api/buy e /api/sell — cotação (I/O de rede) sempre FORA da trava"
    - "import local de pregao (from . import pregao dentro do handler), mesmo padrão de agent.py:216, evita ciclo"
key-files:
  created:
    - server/tests/test_ordens_pendentes_rotas.py
  modified:
    - server/app/main.py
    - server/tests/test_ciclo_imediato_apos_carteira.py
    - server/tests/test_adr013_cobertura_rotas.py
decisions:
  - "GET /api/market/status devolve exatamente 6 chaves de calendário público, sem Depends(current_scope)/require_user — ausência de dependency de sessão é a própria mitigação de T-02-08"
  - "/api/buy e /api/sell fazem a checagem de caixa/posição + store.buy/store.sell DENTRO de store.ORDER_LOCK — mesma trava que pending_orders.executar_pendentes usa no scheduler (T-02-35), fechando o lost-update entre requisição HTTP e execução automática"
  - "scope is None + mercado fechado responde 401 em vez de criar pendente no balde anônimo (T-02-07): o escopo anônimo é compartilhado entre todos os visitantes sem conta"
metrics:
  duration: "~1h10 (inclui provisionamento do venv ausente no worktree e um spike de validação de threading/TestClient/RLock)"
  completed: 2026-08-18
---

# Phase 2 Plan 02: Rotas de Mercado e Ordens Pendentes Summary

Expõe o motor de ordens pendentes (plano 02-01) e o status de pregão por
HTTP: `GET /api/market/status` público (pré-login), ramo "fora do pregão →
pendente" em `/api/buy`/`/api/sell` com a mesma `store.ORDER_LOCK` do
scheduler, `DELETE /api/orders/pending/{id}` escopado, e `pet:evolucao`
corrigido para somar o caixa reservado ao patrimônio.

## What Was Built

1. **`GET /api/market/status`** (`server/app/main.py`) — rota PÚBLICA, sem
   `Depends(current_scope)`/`require_user` e sem nenhum parâmetro de sessão
   (mitigação de T-02-08). Devolve exatamente `{aberto, diaDePregao,
   abertura, fechamento, agoraBRT, afterMarket}`, calculado inteiramente por
   `pregao.py` (fonte única, import local). Entrou na
   `_GATE_ALLOWLIST_PREFIXES` (`/api/market`) para funcionar mesmo em host
   gated — a tela de login precisa do status ANTES de autenticar (D-08).

2. **Ramo pendente em `/api/buy`/`/api/sell`** (MERC-02/03) — a cotação
   continua sendo buscada mesmo com o mercado fechado (dá o
   `precoReferencia` da reserva, D-02); a decisão "mercado fechado" vem SÓ
   de `pregao.in_market_hours()`, nunca do corpo da requisição (T-02-10,
   testado explicitamente enviando `{"pendente": true}` durante o pregão).
   Fechado + `scope is None` → 401 (T-02-07, balde anônimo compartilhado).
   Fechado + sessão → `pending_orders.criar_compra`/`criar_venda`, resposta
   com `pendente: True`, `order`, `priceUsed: None`, `precoReferencia`.

3. **Exclusão mútua (T-02-02/T-02-35)** — o caminho IMEDIATO de compra/venda
   passou a adquirir `store.ORDER_LOCK` (a MESMA trava de `pending_orders`)
   em volta da checagem de caixa/posição + `store.buy`/`store.sell`; a
   cotação (`await candle_provider.get_quote`) fica fora da trava. Em
   `/api/sell`, a leitura inicial de `pos` (400 "Sem posicao") fica fora,
   mas a posição é RELIDA e revalidada dentro da trava — uma venda pendente
   executada no meio-tempo não gera venda de posição inexistente.

4. **`DELETE /api/orders/pending/{order_id}`** (MERC-04) — 401 sem sessão,
   404 PT-BR limpo para id inexistente/de outra conta (`pending_orders.
   cancelar` só enxerga a lista do `user_id` do chamador — sem busca
   cross-escopo, mitigação de T-02-09/IDOR). Devolve `store.public_state`
   atualizado (caixa/posição já restaurados).

5. **`_pet_resumo_evolucao` com caixa reservado** — `patrimonio = cash +
   caixa_reservado + pos_val` (antes só `cash + pos_val`); quando
   `reservado > 0`, a `fala` menciona explicitamente o valor e que ele volta
   ao caixa se a ordem for cancelada. Fecha a classe de defeito "a tela está
   certa, só o Boris erra" (auditoria v1.0) para o caso de ordem pendente.

## Verification

- `cd server && ./.venv/bin/python -m pytest -q tests/test_ordens_pendentes_rotas.py tests/test_gate_cadastro.py` — 12 passed (Task 1).
- `cd server && ./.venv/bin/python -m pytest -q tests/test_ordens_pendentes_rotas.py tests/test_ciclo_imediato_apos_carteira.py` — 22 passed (Task 2).
- `cd server && ./.venv/bin/python -m pytest -q tests/test_ordens_pendentes_rotas.py` — 24 passed (arquivo completo, Task 3 + 1 reforço pós-revisão: ver "Deviations").
- `cd server && ./.venv/bin/python -m pytest -q tests/` (suíte backend inteira) — **1047 passed**.
- `bash scripts/executar.sh --testes` (suíte canônica) — backend 1047 passed
  (verde); 67/74 arquivos `web/tests/*.mjs` OK e **7 falhando com a MESMA
  causa raiz já documentada no SUMMARY do plano 02-01**:
  `Cannot find package '@capacitor/core'` — `web/node_modules/@capacitor/*`
  não instalado neste worktree isolado. Este plano não tocou NENHUM arquivo
  de `web/`. Ver "Known Issues" abaixo — mesmo gap ambiental, não uma
  regressão deste plano.
- Exercício do endpoint real (servidor local, `uvicorn` em `:8799`):
  `curl -s localhost:8799/api/market/status` devolveu JSON com as 6 chaves
  esperadas (`{"aberto":false,"diaDePregao":true,"abertura":"10:00",
  "fechamento":"16:55","agoraBRT":"18/08 22:33","afterMarket":false}`);
  `curl -s -X DELETE localhost:8799/api/orders/pending/po_inexistente` (sem
  token) devolveu 401, não 500.
- Todos os greps de `acceptance_criteria` do PLAN.md confirmados
  manualmente: rota `/api/market/status` sem `current_scope`/`require_user`
  na assinatura; `_GATE_ALLOWLIST_PREFIXES` com `/api/market`;
  `in_market_hours` presente nos dois handlers; `with store.ORDER_LOCK`
  aparece exatamente 2 vezes em `main.py`; `RLock()` continua aparecendo só
  uma vez no backend inteiro (`store.py`); nenhum handler lê `body.get(
  "pendente"|"aberto"|"mercado")`; `orders/pending` e `caixa_reservado`
  presentes em `main.py`.

## Deviations from Plan

### 1. [Ambiente] `.venv` do backend ausente no worktree isolado

O worktree em que este plano foi executado nasceu SEM `server/.venv`
(diferente do clone principal). Provisionado com `python3 -m venv .venv` +
`pip install -r requirements.txt` — as MESMAS dependências já pinadas e
versionadas no repositório (`fastapi`, `pytest`, `httpx`, `PyJWT[crypto]`,
`h2`), nenhum pacote novo. Isto não conta como instalação de pacote não
verificado (Regra 3, exclusão de package manager) porque as versões já
estavam declaradas no `requirements.txt` do commit herdado — é
provisionamento de ambiente, não introdução de dependência nova.
`.venv` está no `.gitignore`, então nada foi commitado por isto.

### 2. [Rule 1 - Bug causado por este task] Teste de ciclo imediato dependia do relógio real

`test_ciclo_imediato_apos_carteira.py::test_{buy,sell}_logado_dispara_ciclo_
imediato` não mockava `pregao.in_market_hours` — antes deste plano, `/api/buy`
e `/api/sell` sempre executavam imediatamente, então o teste passava em
qualquer horário. Com o ramo pendente introduzido por este plano, os dois
testes caíram no ramo pendente sempre que rodados fora do horário real de
pregão (ex.: execução às 22h), quebrando a asserção de disparo do ciclo
imediato — que é exatamente o que o teste queria provar, não o roteamento
por horário. Corrigido com `monkeypatch.setattr(pregao_mod,
"in_market_hours", lambda now=None: True)` no início de cada teste,
preservando o propósito original.

### 3. [Rule 1 - Bug causado por este task] Guardião ADR-013 de cobertura de rotas

`test_adr013_cobertura_rotas.py::test_toda_rota_de_api_tem_gate_reconhecido_
ou_esta_na_allowlist` falhou porque `GET /api/market/status` (nova, sem
`current_scope`/`require_user` por decisão de projeto) não estava na
allowlist explícita de rotas públicas conhecidas. Adicionada com nota
(MERC-01/T-02-08: dado público de calendário) e o contador do segundo teste
de sinal humano (`test_allowlist_publica_nao_cresce_sem_atualizar_este_
teste`) atualizado de 16 para 17. Este é exatamente o cenário que o guardião
foi desenhado para capturar — decisão consciente registrada, não bypass.

### 4. [Reforço pós-revisão] Cobertura real do 401 anônimo em `/api/sell` fechado

`test_sell_mercado_fechado_sem_sessao_responde_401` (Task 2) usava uma conta
SEM posição — a checagem inicial de `pos` (`400 "Sem posicao"`) já barrava
antes de chegar ao ramo `scope is None`, então o `assert status_code in
(400, 401)` deixava o 401 de T-02-07 em `/api/sell` verificado só por
inspeção de código, não por teste direto (o mesmo branch em `/api/buy` já
tinha teste dedicado). Adicionado
`test_sell_mercado_fechado_sem_sessao_com_posicao_no_balde_anonimo_
responde_401`, que planta uma posição no escopo anônimo via `store.buy`
direto e prova o 401 de fato, sem tocar a posição. Commit `ab6ca53`.

Nenhum outro desvio. Sequência de commits TDD RED→GREEN seguida
integralmente nas 3 tasks (6 commits: 3 pares RED/GREEN), mais 1 commit de
reforço de cobertura pós-autorrevisão.

## Known Issues (not blocking this plan)

- **Web test suite environment gap (mesmo gap do plano 02-01).**
  `bash scripts/executar.sh --testes` reporta 7 arquivos `web/tests/*.mjs`
  falhando (`test_appmode_sincroniza_servidor.mjs`, `test_carteira_nativa_
  sincroniza.mjs`, `test_fase2_portfolio.mjs`, `test_notif_central.mjs`,
  `test_notify.mjs`, `test_oauth_repassa_name_e_code.mjs`, `test_pet_resumo_
  modo_web.mjs`), todos com `Cannot find package '@capacitor/core'` —
  `web/node_modules/@capacitor/*` não instalado neste worktree. Nenhum
  arquivo de `web/` foi tocado por este plano. Por política (exclusão de
  instalação de pacote da Regra 3), este executor não roda `npm install`
  unilateralmente em `web/`. Mesmo sinalizado ao orquestrador que o SUMMARY
  do plano 02-01 já registrou — ainda não resolvido no worktree de destino.

## Known Stubs

Nenhum. Este plano é backend puro (rotas HTTP), sem UI — não há dado
renderizado vazio/placeholder a rastrear.

## Threat Flags

Nenhum achado fora do `<threat_model>` do plano. Toda a superfície nova
(rota pública de status, ramo pendente em buy/sell, exclusão mútua com o
scheduler, cancelamento escopado) já estava mapeada no STRIDE register
(T-02-07 a T-02-12, T-02-35) e implementada conforme a mitigação descrita
lá.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 (RED) | `36ee497` | test(02-02): guardiões de GET /api/market/status (RED) |
| 1 (GREEN) | `341ab59` | feat(02-02): GET /api/market/status público + allowlist do gate (GREEN) |
| 2 (RED) | `1154706` | test(02-02): guardiões do ramo pendente em /api/buy e /api/sell (RED) |
| 2 (GREEN) | `6ef4d29` | feat(02-02): ramo pendente em /api/buy e /api/sell + trava de exclusão mútua (GREEN) |
| 3 (RED) | `93e6faf` | test(02-02): guardiões de DELETE /api/orders/pending/{id} e pet:evolucao (RED) |
| 3 (GREEN) | `02d580b` | feat(02-02): DELETE /api/orders/pending/{id} (MERC-04) + patrimônio do Boris com caixa reservado (GREEN) |
| reforço (pós-revisão) | `ab6ca53` | test(02-02): exercita de fato o 401 de escopo anônimo em /api/sell fechado |

## TDD Gate Compliance

Todas as 3 tasks têm `tdd="true"`. Para cada uma: commit `test(...)` (RED,
falha confirmada rodando a suíte antes da implementação) seguido de commit
`feat(...)` (GREEN, suíte passando depois). Nenhum REFACTOR separado foi
necessário. Gate sequence íntegro nas 6 commits acima.

## Self-Check: PASSED

- FOUND: server/tests/test_ordens_pendentes_rotas.py (491 linhas, mínimo pedido: 120)
- FOUND: commit 36ee497
- FOUND: commit 341ab59
- FOUND: commit 1154706
- FOUND: commit 6ef4d29
- FOUND: commit 93e6faf
- FOUND: commit 02d580b
- FOUND: commit ab6ca53
