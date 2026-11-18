---
phase: 51-seu-dia-na-bolsa
plan: 11
status: checkpoint
subsystem: verificacao-final
tags: [checkpoint, roteiro, emenda-D-16]
requirements: [ENG-01, ENG-02, ENG-03, ENG-04, ENG-05, ENG-06, ENG-07, ENG-08, ENG-09, ENG-10, ENG-11, ENG-12]
key-files:
  modified:
    - .planning/ROADMAP.md
    - .planning/REQUIREMENTS.md
metrics:
  tasks_done: 2
  tasks_total: 3
---

# Fase 51 Plano 11: Verificação final e checkpoint do Alex (status: checkpoint)

Tarefas 1 e 2 concluídas; Tarefa 3 (checkpoint humano web + iPhone) PENDENTE.

## Tarefa 1 — Verificação objetiva

- Testes da fase (`server/tests/test_dia_na_bolsa_*.py`): 105 passed.
- Suíte canônica (rodada pelo orquestrador após a onda 6, commit 99a43a2e): backend 3886 passed / 31 failed (todas pré-existentes no sandbox: leitura de `*.pem` do certifi bloqueada, PermissionError, idêntico à baseline 289f8d27); `web/tests/*.mjs` 237/237 ok; `npx vite build` ok. Não reexecutada aqui.
- Calibração (51-04): PENDENTE. Sem rede/TLS e L2 vazio no sandbox. Alex roda fora do sandbox:
  `server/.venv/bin/python scripts/dia_na_bolsa_calibrar.py --rede`
  Atenção (51-04): o catálogo tem 20 ativos e `AMPLITUDE_MIN_ATIVOS = 30` — a regra de amplitude nunca dispara com o catálogo atual; decidir ampliar o universo (`--tickers`) ou baixar o mínimo.

### Roteiro de disparo local do job

1. Backend local: `cd server && ./.venv/bin/uvicorn app.main:app --port 8787` (B3_DB_PATH apontando para um banco de teste, conta de teste).
2. Num REPL do `server/.venv` (mesmo B3_DB_PATH), forçar o relógio via `_agora` e rodar o job:
   ```python
   from datetime import datetime
   from app import db, dia_na_bolsa as d
   conn = db.connect()
   d._agora = lambda: datetime(2026, 11, 18, 17, 25, tzinfo=d.BRT)   # dia útil, após o horário
   import asyncio; print(asyncio.run(d.maybe_run(conn)))
   print(db.ler_job(conn, "diaNaBolsa"))   # yahooChamadas, cacheHits, semDado
   ```
   (alternativa: `B3_DIA_NA_BOLSA_HHMM=HH:MM` muda o horário-alvo; `B3_DIA_NA_BOLSA_OFF=1` desliga; `B3_DIA_NA_BOLSA_MAX_YAHOO` ajusta o teto.)
3. Consultar autenticado: `GET /api/dia-na-bolsa?modo=estudo|operador` com o Bearer da conta de teste.
4. Sábado/feriado: trocar `_agora` para uma data de fim de semana/feriado B3 e confirmar que `maybe_run` não gera card nem push.
5. Nada de deploy/publicação nesta fase (`scripts/bump.sh` + `publicar-web.sh` são etapa separada).

## Tarefa 2 — Emenda D-16 (commit 1edec3ad)

- ROADMAP.md: nota acrescentada ao FINAL da linha ENG-11 da Fase 51 (1 linha estendida, nada removido).
- REQUIREMENTS.md não tinha ENG-01..12: criada a seção "Fase 51 — Seu dia na bolsa" (antes de "Future Requirements") com as 12 linhas copiadas do ROADMAP, ENG-11 já com a emenda.

## Tarefa 3 — Checkpoint (pendente, aguardando o Alex)

Resposta do Alex item a item (1-10): _a registrar_.

## Desvios conhecidos para decisão do Alex

- Botão de retry com texto "Tentar novamente" (51-02).
- Rodapé do card usa `DISCLAIMERS.short`, não a frase literal do UI-SPEC (51-08).
- Rótulos dos KPIs mostram o período do seletor, não "(4 SEM)" fixo (51-09).
- Gate diário de "vistos" removido do localStorage pelo orquestrador (o servidor deduplica) — fix 99a43a2e.
- 51-04: amplitude inoperante com 20 ativos no catálogo (ver acima).

## Deviations from Plan

None nas Tarefas 1-2 (a Tarefa 1 não gera arquivo de produto; seu produto é este roteiro).

## Self-Check: PASSED
