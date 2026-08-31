---
phase: 14-opcoes-lastreadas
plan: 02
subsystem: api
tags: [options, portfolio-engine, pytest, position-lock, covered-call, protective-put]

# Dependency graph
requires: ["14-01"]
provides:
  - "store.abrir_call_coberta — vender para abrir uma CALL coberta: credita prêmio, cria posição side=\"vendida\" com lastro, incrementa qtyTravada da ação"
  - "store.fechar_call_coberta — recomprar para fechar: debita recompra, realiza pnl=(avg-price)*qty, destrava qtyTravada (parcial ou total)"
  - "store.comprar_put_protecao — compra de PUT vinculada a posição real do lastro, debita caixa, nunca trava ações"
  - "Formato aditivo de optionPositions: side (\"vendida\"|\"comprada\"|ausente=modelo antigo) + lastro ({t,qty})"
affects: [14-03, 14-04, 14-05, 14-06, 14-07, 14-08]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Leitura+validação+escrita das três operações inteiras dentro de UMA aquisição de store.ORDER_LOCK — diferente de buy/sell (onde a trava vive na rota chamadora em main.py), aqui a trava vive na função porque ainda não existe rota (plano 14-04)"
    - "Discriminador side ausente = posição do modelo antigo (long-only, buy_option/sell_option) — mantém a fase 14 não-retroativa sem migração/backfill, mesmo padrão de qtyTravada ausente=0 do plano 14-01"

key-files:
  created: []
  modified:
    - server/app/store.py
    - server/tests/test_opcoes_lastreadas_store.py

key-decisions:
  - "Retroatividade (14-CONTEXT.md, Claude's Discretion): decidida como NÃO — a chave `side` ausente identifica posições pré-existentes do modelo antigo, que seguem sob as regras antigas sem tocar em lastro/trava"
  - "`meta` nos parâmetros de abrir_call_coberta/comprar_put_protecao existe só por paridade de assinatura com buy_option — não fiado a `_sanitize_trade_meta`/`setupEntrada`, porque o plano não lista esse campo entre os gravados nesta posição (evita funcionalidade fora do escopo pedido)"
  - "fechar_call_coberta sem posição (ou posição não side=\"vendida\") devolve None em vez de levantar erro — mesma convenção de sell_option: fechar algo que não existe é no-op do chamador, não uma tentativa recusada registrável"
  - "comprar_put_protecao reusa sell_option para fechamento antecipado (nenhuma função nova) — a put comprada tem aritmética idêntica a uma posição long-only comum"

requirements-completed: []

# Metrics
duration: ~30min
completed: 2026-08-31
---

# Phase 14 Plan 02: Vender CALL coberta, recomprar para fechar, comprar PUT de proteção Summary

**Três funções novas em `server/app/store.py` (`abrir_call_coberta`, `fechar_call_coberta`, `comprar_put_protecao`) que tornam a venda coberta e a put de proteção aritmética verificável no motor determinístico — greenfield, `sell_option` só sabia "vender para fechar".**

## Performance

- **Duration:** ~30 min
- **Completed:** 2026-08-31T03:34:00Z
- **Tasks:** 2/2
- **Files modified:** 2 (0 criados, 2 modificados — o arquivo de teste foi criado na Task 1 e estendido na Task 2)

## Accomplishments
- `abrir_call_coberta`: "vender para abrir" uma CALL coberta — credita `qty*price` no caixa, cria/soma a posição de opção com `side="vendida"` e `lastro={"t","qty"}`, incrementa `qtyTravada` da ação lastro na mesma escrita. Recusa (optionType errado, sem posição no ativo, lastro livre insuficiente) grava rejeição e levanta `ValueError` sem tocar caixa/posições.
- `fechar_call_coberta`: recompra ("comprar para fechar") — debita a recompra, realiza `pnl=(avg-price)*qty`, destrava a mesma quantidade fechada (parcial mantém `avg` e reduz `qty`/`lastro["qty"]`; total remove a posição). Sem posição devolve `None`, mesma convenção de `sell_option`.
- `comprar_put_protecao`: compra vinculada a posição real do lastro, debita caixa, **nunca** trava ações (D-3 só se aplica à call). Recusa por tipo errado, ausência de posição, lastro insuficiente ou caixa insuficiente. Fechamento antecipado reusa `sell_option` — nenhuma função nova.
- As três operações mutam `cash`+`positions`+`optionPositions` dentro de UMA aquisição de `ORDER_LOCK` cobrindo leitura+validação+escrita (não só a escrita) — fecha o mesmo TOCTOU que T-14-06 do threat_model exige mitigar.
- Suíte canônica inteira verde: `1771 passed, 1 skipped` (pytest, suíte completa) + `107/107` `web/tests/*.mjs` `[OK]` — nenhum arquivo web foi tocado (backend-only), rodado mesmo assim por disciplina da suíte canônica do CLAUDE.md.

## Task Commits

Each task was committed atomically:

1. **Task 1: Formato da posição lastreada + abrir CALL coberta (vender para abrir)** - `eccbd92` (feat)
2. **Task 2: Fechar CALL coberta (recomprar) e comprar PUT de proteção** - `e23b9c0` (feat)

_Note: nenhuma task era TDD — plano `autonomous: true`, sem checkpoints._

## Files Created/Modified
- `server/app/store.py` - `abrir_call_coberta`/`fechar_call_coberta`/`comprar_put_protecao` (~200 linhas novas), formato aditivo de `optionPositions` documentado em comentário de módulo (`side`, `lastro`)
- `server/tests/test_opcoes_lastreadas_store.py` - guardião das três operações: abertura (credita/trava/recusa/reabre-pondera), fechamento (total/parcial/pnl negativo/sem posição), put de proteção (debita/não trava/recusa por lastro ou caixa/fechamento via sell_option)

## Decisions Made
- Retroatividade deixada em aberto no 14-CONTEXT.md resolvida como "não" — o discriminador `side` ausente é o que mantém posições de opção pré-existentes (modelo antigo, `buy_option`/`sell_option`) intocadas por este código novo, sem migração.
- `meta` nos parâmetros de `abrir_call_coberta`/`comprar_put_protecao` existe só por paridade de assinatura com `buy_option` — deliberadamente não fiado a `setupEntrada`, porque o plano não lista esse campo entre os gravados nestas posições (linha de decisão registrada em comentário de código também).
- `fechar_call_coberta` sem posição correspondente devolve `None`, não levanta erro nem registra rejeição — replica exatamente a convenção já estabelecida por `sell_option` para o mesmo caso.

## Deviations from Plan

None - plan executed exatamente conforme escrito. Todas as funções, formato de posição, mensagens de recusa, disciplina de `ORDER_LOCK` e os testes descritos em `<action>` foram implementados conforme especificado.

## Issues Encountered
- Mesma correção de base de worktree do plano 14-01: o worktree foi recriado a partir da tip do checkout principal em vez da branch de feature — corrigido com `git reset --hard` (fast-forward confirmado via `merge-base`, working tree limpo, sem perda de trabalho) antes de começar a executar o plano.
- `web/node_modules` ausente no worktree (mesmo padrão do backend/.venv já documentado no plano 14-01) — resolvido temporariamente com um symlink para `web/node_modules` do clone principal só para rodar a suíte `web/tests/*.mjs` de validação; o symlink foi removido antes do commit final (não aparece no `git status`, `node_modules/` já é ignorado pelo `.gitignore` da raiz).

## User Setup Required

None - nenhuma configuração de serviço externo necessária. As três funções são puramente do motor determinístico (`store.py`), sem rota HTTP ainda (rotas ficam para o plano 14-04) e sem dependência nova.

## Next Phase Readiness
- `abrir_call_coberta`/`fechar_call_coberta`/`comprar_put_protecao` estão prontas para o plano 14-04 expor rotas HTTP que as chamem (a trava de `ORDER_LOCK` já vive na função, então a rota não precisa envolver a chamada numa trava própria — só precisa resolver `contract`/`user_id`/`price` e tratar o `ValueError`, mesmo padrão de `HTTPException` já usado no resto de `main.py`).
- Formato `side`/`lastro` de `optionPositions` está pronto para o plano 14-03 tratar o estado derivado de "put sem lastro" (quando o usuário vende as ações depois de comprar a put) mencionado no comentário de `comprar_put_protecao`.
- Nenhum bloqueio conhecido para os próximos planos da fase.

---
*Phase: 14-opcoes-lastreadas*
*Completed: 2026-08-31*

## Self-Check: PASSED

- FOUND: server/app/store.py
- FOUND: server/tests/test_opcoes_lastreadas_store.py
- FOUND commit eccbd92 (Task 1)
- FOUND commit e23b9c0 (Task 2)
