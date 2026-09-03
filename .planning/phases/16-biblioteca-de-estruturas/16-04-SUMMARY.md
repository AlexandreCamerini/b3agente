---
phase: 16-biblioteca-de-estruturas
plan: 04
subsystem: api
tags: [options, collar, multiperna, opcoes_lastreadas, fastapi]

# Dependency graph
requires:
  - phase: 16-biblioteca-de-estruturas
    plan: 01
    provides: "propor() migrado para opcoes_motor.rastrear()/avaliar(), campos estrutura/caixa/precoObjeto"
  - phase: 16-biblioteca-de-estruturas
    plan: 03
    provides: "propor(..., multiperna=True) compõe collar; contractSymbol/optionType/strike/premio* nulos no collar"
provides:
  - "GET /api/options/proposta/{ticker}?multiperna=1 devolve o collar completo (payoff travado, duas pernas, caixa)"
  - "Sem o parâmetro, a rota devolve exatamente o que devolvia antes da Fase 16 (mais os campos aditivos estrutura/caixa/precoObjeto do Plano 16-01)"
  - "POST /api/options/lastreada/abrir recusa com 400 nomeado qualquer corpo de mais de uma perna (tipo==collar OU pernasContratos/pernas com >1 item), sem efeito colateral no caixa/optionPositions"
  - "docs/adr/025-collar-e-estrutura-multiperna.md — as cinco decisões da Fase 16"
affects: [17-fluxo-de-aceite, 18-navegacao-de-estruturas]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Negociação de capacidade via query param tipado nativamente pelo FastAPI (multiperna: bool = False) — coerção inválida vira 422 sem parse manual, sem tocar o motor"
    - "Trava de execução server-side colocada ANTES da validação de campo único (contractSymbol), verificando tanto o rótulo declarado (tipo) quanto a forma do corpo (pernasContratos/pernas) — não confia no cliente ser honesto sobre o rótulo"

key-files:
  created:
    - docs/adr/025-collar-e-estrutura-multiperna.md
  modified:
    - server/app/main.py
    - server/tests/test_opcoes_lastreadas_rotas.py

key-decisions:
  - "multiperna é negociação de capacidade do CLIENTE, não feature flag de entrega parcial — o collar já está completo no motor e acessível pela rota desde este plano; o parâmetro descreve só o que o cliente sabe renderizar/executar"
  - "Trava de POST /api/options/lastreada/abrir checa tipo==collar OU pernasContratos/pernas>1 — cobre tanto o cliente honesto quanto o corpo que omite o rótulo mas ainda carrega duas pernas"
  - "Guarda de autoidentificação (confia em tipo/pernasContratos do próprio corpo, não re-deriva a partir da cadeia) é aceitável nesta fase porque nenhum front deste repo monta corpo multiperna — vira item de hardening real quando a Fase 17 ligar um cliente de verdade (documentado em ADR-025 e no prompt de execução deste plano)"

patterns-established: []

requirements-completed: [LIB-01, LIB-02, LIB-03]

# Metrics
duration: 55min
completed: 2026-09-02
---

# Phase 16 Plan 04: Rota multiperna + trava de execução Summary

**Collar exposto na rota de proposta via negociação de capacidade (`?multiperna=1`), com trava de servidor no `POST /api/options/lastreada/abrir` que recusa qualquer estrutura de mais de uma perna antes de qualquer escrita — o cliente publicado hoje (que casa proposta com posição por `contractSymbol` único e executa uma perna por vez) segue vendo exatamente a resposta de antes.**

## Performance

- **Duration:** ~55 min
- **Completed:** 2026-09-02
- **Tasks:** 3/3
- **Files modified:** 3 (1 criado, 2 modificados)

## Accomplishments
- `GET /api/options/proposta/{ticker}` ganhou o parâmetro de query tipado `multiperna: bool = False`, repassado a `opcoes_lastreadas.propor()`. Sem o parâmetro, a resposta é idêntica à de antes da Fase 16 (campos aditivos `estrutura`/`caixa`/`precoObjeto` do Plano 16-01 à parte). `?multiperna=1` no cenário onde a put isolada não cabe no caixa libera o collar completo (payoff travado dos dois lados, duas pernas nomeadas em `pernasContratos`, `contractSymbol is None`).
- `?multiperna=0`/`?multiperna=false` comportam-se como ausência do parâmetro (nenhum collar). `?multiperna=banana` devolve 422 via tipagem nativa do FastAPI — nunca 500, nunca collar por acidente.
- Caixa folgado + `?multiperna=1` continua devolvendo `put_protecao` — o gatilho do collar (Decisão 3 do ADR-025) só abre exatamente onde a put isolada falharia por caixa.
- `POST /api/options/lastreada/abrir` recusa com `HTTPException(400, "Estrutura de mais de uma perna não é executada por esta rota.")` qualquer corpo com `tipo == "collar"` OU `pernasContratos`/`pernas` de mais de um item — checagem posicionada logo após o 403 de Modo Estudo e antes da validação de `contractSymbol`, para nunca deixar a validação de campo único mascarar o motivo real da recusa.
- A trava não depende do cliente declarar `tipo` honestamente: um corpo com duas pernas em `pernasContratos` e sem `tipo` também é recusado. A trava não pega a operação legítima de uma perna (`pernasContratos` de 1 item continua abrindo normalmente) — nenhuma regressão nas duas estruturas em produção.
- Os dois casos de 400 têm teste afirmando, além do status code, que `optionPositions` continua vazio e o `cash` inalterado — recusa sem efeito colateral, não só código de status.
- `docs/adr/025-collar-e-estrutura-multiperna.md` registra as cinco decisões da Fase 16 (perna de lastro a preço de spot, régua única de seleção, quando propor collar, ausência de contrato único no collar, negociação de capacidade + trava), cada uma com a alternativa descartada nomeada, e documenta explicitamente a limitação da trava por autoidentificação como item de hardening da Fase 17.

## Task Commits

Tasks 1 e 2 tinham `tdd="true"`; cada uma virou um ciclo RED→GREEN (2 commits).

1. **Task 1: Negociação de capacidade na rota de proposta**
   - `ec1855f` (test) — RED: 6 testes novos em `test_opcoes_lastreadas_rotas.py` cobrindo os 6 itens do bloco `<behavior>` (campos aditivos, caixa_insuficiente sem regressão, collar liberado com multiperna=1, multiperna=0/false como ausência, multiperna=banana → 422, caixa folgado continua put_protecao). Confirmados falhando pela razão certa: o parâmetro ainda não era repassado a `propor()`.
   - `532d02c` (feat) — GREEN: parâmetro `multiperna: bool = False` acrescentado à assinatura da rota e repassado nomeado à chamada de `opcoes_lastreadas.propor()`. `motivoTexto` intocado.
2. **Task 2: Trava de servidor contra execução de meia estrutura**
   - `da97488` (test) — RED: 3 testes novos cobrindo os itens do bloco `<behavior>` (corpo `tipo=="collar"` → 400; corpo sem `tipo` mas com `pernasContratos` de 2 itens → 400; `pernasContratos` de 1 item continua abrindo). Confirmados falhando pela razão certa: sem a trava, o corpo caía na validação genérica de `contractSymbol` ausente, com a mensagem errada.
   - `fb3210d` (feat) — GREEN: trava inserida entre o 403 de Modo Estudo e a validação de `contractSymbol`, checando `tipo`/`pernasContratos`/`pernas`.
3. **Task 3: ADR-025**
   - `46b5bc9` (docs) — ADR-025 completo, 8 seções `## `, 5 decisões nomeadas com alternativa descartada cada.

**Plan metadata:** (este commit — SUMMARY)

## Files Created/Modified
- `server/app/main.py` — `options_proposta` ganha `multiperna: bool = False` + repasse nomeado a `propor()`; `options_lastreada_abrir` ganha a trava de mais de uma perna, comentada com o racional e com o registro explícito de que o collar segue sem caminho de execução até a Fase 17.
- `server/tests/test_opcoes_lastreadas_rotas.py` — 9 testes novos (6 da rota de proposta, 3 da rota de abertura), fixture `_plano_vender` e helper `_pernas_collar_da_cadeia` (lê a cadeia REAL do provider mock em vez de chutar prêmios).
- `docs/adr/025-collar-e-estrutura-multiperna.md` (novo) — as cinco decisões da fase + limitação conhecida da trava.

## Decisions Made
- **`multiperna` é negociação de capacidade, não feature flag de entrega parcial:** o collar está completo no motor (Plano 16-03) e acessível pela rota desde este plano; o parâmetro só descreve o que o cliente sabe renderizar/executar. Ver Decisão 5 do ADR-025.
- **Trava checa `tipo` OU forma do corpo (`pernasContratos`/`pernas`):** cobre tanto o cliente honesto sobre o rótulo quanto um corpo que omite `tipo` mas ainda carrega duas pernas — a trava não confia em nenhum campo isolado que o cliente poderia omitir ou errar.
- **Guarda por autoidentificação, não re-derivação server-side:** aceitável nesta fase porque nenhum front do repositório monta um corpo multiperna hoje (`PropostaLastreada`, `web/src/App.jsx:3010-3065`, não sabe renderizar `pernasContratos`) — a trava já recusa qualquer tentativa antes de qualquer escrita, independente do rótulo ser honesto. Vira item de hardening real quando a Fase 17 construir um cliente que declara `multiperna=1` de verdade; documentado explicitamente em ADR-025 e não expandido neste plano por instrução direta do escopo desta execução.

## Deviations from Plan

None — plano executado exatamente como escrito. As duas tasks TDD seguiram RED→GREEN com commits separados; a trava foi colocada na posição exata especificada (após o 403, antes da validação de `contractSymbol`); o ADR cobre as cinco decisões pedidas, cada uma com alternativa descartada nomeada.

## Issues Encountered

Durante a fixture de teste do collar, a fórmula de caixa do plano (`max(0.0, 100 * (premio_put - premio_call)) + 0.5`) produziu, para PETR4 no provider mock, `premio_put == premio_call == 0.65` (ambos os contratos escolhidos ficam equidistantes do spot por desenho do mock) — o que faz `custo_liquido` do collar ficar `<= 0` (financiado pelo lastro, sem checagem de caixa). As duas desigualdades exigidas pelo plano (`cash < 100*premio_put` e `cash >= custo_liquido_do_collar`) seguem verdadeiras mesmo nesse caso (a segunda trivialmente, já que o custo é `<= 0`), então o teste passa e continua útil como guardião — não foi necessário desviar da fórmula especificada. Registrado aqui para quem for reler o teste e estranhar os dois prêmios idênticos.

Suíte completa do backend (`pytest tests/ -q`) roda com `PermissionError`/network-block quando executada dentro do sandbox do Bash tool desta sessão (27 falhas, mesma causa raiz já documentada em `15-VERIFICATION.md` e nos summaries anteriores da fase) — **fora do sandbox** (`dangerouslyDisableSandbox: true`), a suíte inteira passa: `1965 passed, 1 skipped, 0 failed`. `bash scripts/executar.sh --testes` (suíte canônica: pytest + `web/tests/*.mjs`) também rodado fora do sandbox — backend `1965 passed, 1 skipped`, suíte web inteira `[OK]` em todos os arquivos, nenhuma falha.

## User Setup Required

None — nenhuma configuração de serviço externo.

## Next Phase Readiness

- Registrado para a Fase 17 (conforme pedido no `<output>` do plano): (1) ligar o collar no cliente é passar `multiperna=1` na chamada de `GET /api/options/proposta/{ticker}`; (2) executar o collar exige um caminho de N pernas em `server/app/store.py` que ainda não existe — hoje só há `abrir_call_coberta`/`comprar_put_protecao`, uma perna cada — e a trava de servidor deste plano (`options_lastreada_abrir`) é o que impede esse vácuo de virar execução parcial silenciosa enquanto esse caminho não existir; (3) resultado de `bash scripts/executar.sh --testes`: backend 1965 passed/1 skipped/0 failed, suíte web `web/tests/*.mjs` inteira `[OK]`.
- A guarda de execução por autoidentificação (`tipo`/`pernasContratos` do próprio corpo) é um item de hardening explícito para a Fase 17 assim que ela construir um cliente que declara `multiperna=1` — não bloqueante para esta fase (nenhum front atual pode disparar o cenário que a re-derivação cobriria), mas deve ser revisitado nesse momento (ADR-025, seção "Limitação conhecida").
- Nenhum bloqueio técnico conhecido. Fase 16 (LIB-01, LIB-02, LIB-03) fecha com este plano.

## Self-Check: PASSED

- `server/app/main.py` — FOUND (modificado; `multiperna` presente 5x).
- `server/tests/test_opcoes_lastreadas_rotas.py` — FOUND (modificado; 9 testes novos).
- `docs/adr/025-collar-e-estrutura-multiperna.md` — FOUND (8 seções `## `).
- Commit `ec1855f` — FOUND em `git log --oneline`.
- Commit `532d02c` — FOUND em `git log --oneline`.
- Commit `da97488` — FOUND em `git log --oneline`.
- Commit `fb3210d` — FOUND em `git log --oneline`.
- Commit `46b5bc9` — FOUND em `git log --oneline`.
- `grep -c 'multiperna' server/app/main.py` → 5 (≥2 exigido).
- `grep -c 'mais de uma perna' server/app/main.py` → 2 (≥1 exigido).
- `grep -c '^## ' docs/adr/025-collar-e-estrutura-multiperna.md` → 8 (≥5 exigido).
- `git status --porcelain web/` → vazio.
- `git diff --stat server/requirements.txt server/requirements-prod.txt` → vazio.

---
*Phase: 16-biblioteca-de-estruturas*
*Completed: 2026-09-02*
