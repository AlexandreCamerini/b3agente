---
phase: 07-sele-o-din-mica-por-desempenho-hist-rico-ledger-de-sinais-re
plan: 05
subsystem: api
tags: [setups, regime, radar, adr-017, seleção-dinâmica, determinístico]

# Dependency graph
requires:
  - phase: 07-02
    provides: "signal_ledger.historico_snapshot(conn) — {nome do setup: {expR, n, medidoAte, elegivel, insuficiente, expRJanela, nJanela, janelaRef, calculadoEm}}"
provides:
  - "server/app/setups.py: set_historico_provider(fn) — ponto de injeção do histórico medido por setup, default None"
  - "detect_setups() anexa s[\"historico\"] por setup (inclusive aposentado) quando há provedor configurado; sem provedor, contrato antigo intacto (sem a chave)"
  - "server/app/regime.py: W_HISTORICO_ELEGIVEL/W_HISTORICO_INELEGIVEL, _elegibilidade(), ranquear() anexando setupHistorico/setupElegivel e usando o rank de elegibilidade na ordenação (entre momentum e gatilho)"
affects: [07-06-liga-provedor-em-producao]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ponto de injeção (Callable[[], dict] | None) em vez de import direto de banco em módulo puro do caminho síncrono quente — mesmo padrão de _SNAP_CACHE em technical_snapshot.py, mas para um provedor externo em vez de cache local"
    - "Provedor chamado UMA vez por chamada (não por setup/por resultado), sempre dentro de try/except que devolve None em vez de propagar — histórico é informativo, nunca pode derrubar a tela"
    - "Elegibilidade entra na tupla de ordenação como rank de 3 valores (0/1/2) posicionado ENTRE os critérios já validados (momentum) e os mais fracos (timing/desempate) — extensão da técnica já usada por gatilhoAlinhado/confluencia em regime.ranquear"

key-files:
  created:
    - server/tests/test_adr017_historico_setups.py
  modified:
    - server/app/setups.py
    - server/app/regime.py

key-decisions:
  - "_elegibilidade() reusa EXATAMENTE a seleção de melhor setup operável de _gatilho_alinhado (primeiro não-aposentado da lista já ordenada por confluência) — nenhuma segunda noção de \"melhor setup\" foi criada."
  - "insuficiente=True e elegivel=None colapsam para o MESMO resultado (historico, None) em _elegibilidade — ausência de evidência nunca vira penalidade, mesmo tratamento dado a 'nunca medido' (historico=None) no radarScore (peso 0.0)."
  - "Peso ±10.0 (metade do corpo do score, que é percentil 0–100) escolhido para desempatar no eixo de evidência sem jamais superar o eixo de regime/momentum do ADR-016 — gatilhoAlinhado (timing) vale metade disso (+5.0)."

patterns-established:
  - "Motor lê evidência medida via injeção, nunca via import de storage — quem liga a ponta em produção é o boot do main.py, plano separado (07-06)."

requirements-completed: [ADR17-B1-05, ADR17-B1-06]

duration: ~35min
completed: 2026-08-21
---

# Phase 07 Plan 05: detect_setups + regime.ranquear consomem a evidência medida Summary

**`detect_setups()` ganha campo informativo `historico` por setup via provedor injetado (default `None`, sem I/O no caminho quente) e `regime.ranquear()` passa a somar ±10 ao `radarScore` e usar a elegibilidade da janela anual fechada como novo termo de ordenação, entre momentum relativo e gatilho de timing — sem esconder nenhum setup e sem inverter o eixo de regime/momentum validado no ADR-016.**

## Performance

- **Duration:** ~35 min
- **Tasks:** 2/2 completos (TDD RED→GREEN cada)
- **Files modified:** 2 (`server/app/setups.py`, `server/app/regime.py`); 1 arquivo de teste criado (`server/tests/test_adr017_historico_setups.py`, 19 testes)

## Accomplishments
- `setups.set_historico_provider(fn)` — ponto de injeção puro (sem import de banco/`signal_ledger`), chamado UMA vez por `detect_setups` (não por setup), protegido por `try/except Exception` que nunca propaga e ignora retorno que não seja `dict`.
- Todo setup detectado (inclusive os aposentados do Bloco 0) recebe `s["historico"]` quando há provedor — "aposentado ≠ apagado" continua valendo também para o histórico: o número aparece justo ao lado do padrão retirado do motor.
- Sem provedor configurado (default), a chave `"historico"` nem é criada — contrato antigo de `detect_setups` fica byte-a-byte igual, nenhum teste pré-existente quebrou.
- `_vale`, `melhor`, `veredito` e `confluencia` não foram tocados — verificado por `git diff` (0 linhas removidas dentro de `_vale`) e por teste que compara os dois caminhos (com/sem provedor) e exige igualdade.
- `regime._elegibilidade(resultado)` lê o histórico do melhor setup OPERÁVEL (mesma seleção de `_gatilho_alinhado`) e devolve `(historico, None)` sempre que a amostra é insuficiente ou a elegibilidade é desconhecida — nunca `(historico, False)` por ausência de evidência.
- `ranquear()` anexa `setupHistorico`/`setupElegivel`, soma `W_HISTORICO_ELEGIVEL=+10.0`/`W_HISTORICO_INELEGIVEL=-10.0` ao `radarScore` (0.0 quando `None`) e insere o rank de elegibilidade na tupla de ordenação, entre `momentumRelPct` e `gatilhoAlinhado` — guardião de teste prova que um ativo com momentum maior continua à frente de um com setup elegível mas momentum menor (eixo do ADR-016/Adendo 7 preservado).
- Nenhum resultado é removido de `ranquear` por causa de elegibilidade — `len(saída) == len(entrada)` testado explicitamente.

## Task Commits

Cada task foi commitada em ciclo RED→GREEN (TDD):

1. **Task 1: detect_setups anexa o histórico medido (provedor injetado)** — `7a13066` (test, RED) → `5235aaf` (feat, GREEN)
2. **Task 2: regime.ranquear consome a elegibilidade da janela fechada** — `f54665c` (test, RED) → `0452be8` (feat, GREEN)

_Nenhuma task precisou de commit de REFACTOR._

**Nota sobre o RED da Task 2:** 2 das 10 novas asserções já passavam antes da implementação (`test_momentum_maior_vence_elegibilidade_eixo_adr016_preservado` e `test_nada_e_removido_len_preservado`) — ambas validam invariantes que JÁ existiam em `regime.ranquear` antes desta mudança (o eixo de momentum e a não-remoção de resultados), não comportamento novo. As 8 asserções restantes (novas de verdade — `setupHistorico`/`setupElegivel`/peso no `radarScore`/ordem por elegibilidade) falharam corretamente por `KeyError` até a implementação. Um teste de ordenação foi corrigido durante o RED (tickers em ordem alfabética coincidiam com a ordem de elegibilidade esperada, mascarando a ausência da lógica nova — trocados para ordem alfabética INVERSA da elegibilidade esperada, forçando o teste a depender de fato do rank novo).

## Files Created/Modified
- `server/app/setups.py` — `_HISTORICO_PROVIDER`/`set_historico_provider`/`_historico_map` (ponto de injeção); `s["historico"]` anexado no mesmo laço que já marca `s["aposentado"]`.
- `server/app/regime.py` — `W_HISTORICO_ELEGIVEL`/`W_HISTORICO_INELEGIVEL`; `_elegibilidade()`; `ranquear()` anexando `setupHistorico`/`setupElegivel`, somando ao `radarScore` e usando o rank de elegibilidade na tupla de ordenação; docstrings do módulo e da função atualizadas.
- `server/tests/test_adr017_historico_setups.py` (novo) — 19 testes: 9 para `detect_setups` (Task 1) + 10 para `regime.ranquear` (Task 2).

## Decisions Made
- `_elegibilidade()` não criou uma segunda lógica de "melhor setup" — reusa literalmente a mesma seleção (`[s for s in setups if not s.get("aposentado")][0]`) que `_gatilho_alinhado` já usa, evitando duas fontes de verdade sobre "qual é o setup que importa" no mesmo resultado.
- O peso `±10.0` foi calibrado contra o corpo do `radarScore` (percentil de momentum, 0–100): desloca cerca de um decil, o dobro do peso do `gatilhoAlinhado` (+5.0, timing) — a evidência medida pesa mais que o timing, mas nenhum dos dois domina o eixo de momentum validado no ADR-016.
- Comentários no código evitam as substrings literais que os greps de aceitação do plano proíbem (`signal_ledger`, `import db`, `datetime`, `os.environ`) mesmo em prosa explicativa — ajustado durante a Task 1 depois que o primeiro grep de verificação acusou falso positivo por um comentário que citava `server/app/signal_ledger.py` como referência.

## Deviations from Plan

None - plano executado exatamente como escrito. As duas tasks TDD (RED→GREEN) seguiram os comportamentos e critérios de aceite do `07-05-PLAN.md` sem necessidade de ajuste de escopo, arquitetura ou correção de bug. O único ajuste foi de qualidade de teste (ticker alfabético mascarando RED — corrigido antes do commit RED, documentado acima) e de fraseado de comentário (grep de aceitação — corrigido antes do commit GREEN da Task 1).

## Issues Encountered
- Nenhum bloqueio. A engenharia dos candles sintéticos para disparar "Setup 9.2 (alta)" (aposentado) ponta a ponta via `detect_setups` exigiu iteração manual (não havia teste ponta-a-ponta pré-existente para esse setup específico no repositório) — resolvido com uma série de tendência de alta + 1 candle de correção, validado por execução direta antes de fixar no teste.

## User Setup Required
None - nenhuma configuração de serviço externo. `set_historico_provider` continua desligado (`None`) em produção; ligar a ponta real é o Plano 06.

## Next Phase Readiness
- Interface pronta para o Plano 06 (liga o provedor em produção, no boot de `main.py`, chamando `setups.set_historico_provider(signal_ledger.historico_snapshot_cache_wrapper)` ou equivalente).
- `bash scripts/test.sh`: 1211 passed, 1 skipped (era 1201 antes desta plan, no fim da Task 1 — os 19 testes de `test_adr017_historico_setups.py` somam 9 da Task 1 + 10 da Task 2).
- `bash scripts/executar.sh --testes` (suíte canônica): pytest 100% verde (1211 passed, 1 skipped); 6 falhas pré-existentes em `web/tests/*.mjs` por `@capacitor/core` ausente (`web/node_modules` não instalado neste worktree) — confirmado por execução direta (`ERR_MODULE_NOT_FOUND` em `persistence.js`), fora do escopo desta plan (backend puro, nenhum arquivo em `web/`/`web-admin/` tocado — `git status --porcelain web/ web-admin/` retorna vazio). Mesmo padrão documentado em 07-02-SUMMARY.md e no achado da auditoria em PROJECT.md.
- Verificações do bloco `<verification>` do plano conferidas: `grep -c "signal_ledger\|import db" server/app/setups.py server/app/regime.py` == 0; `git diff server/app/setups.py` sem alteração dentro de `_vale`/`melhor`/`veredito`; `git status --porcelain web/ web-admin/` vazio.

---
*Phase: 07-sele-o-din-mica-por-desempenho-hist-rico-ledger-de-sinais-re*
*Completed: 2026-08-21*

## Self-Check: PASSED

- FOUND: server/app/setups.py, server/app/regime.py, server/tests/test_adr017_historico_setups.py
- FOUND commits: 7a13066, 5235aaf, f54665c, 0452be8 (todos em `git log --oneline`)
