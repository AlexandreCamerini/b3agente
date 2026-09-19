---
phase: 29-opcao-a-descoberto-flag-opt-in
plan: 01
subsystem: backend — carteira de opções (ADR-003)
tags: [gate, flag-opt-in, opcoes, backend]
dependency-graph:
  requires: []
  provides:
    - "config.permitirOpcaoADescoberto (bool, default False)"
    - "config.descobertoTermo ({aceitoEm, versao} | None)"
    - "store.MOTIVO_DESCOBERTO_DESLIGADO (mensagem única do gate)"
    - "gate em store.buy_option, fail-closed"
  affects:
    - "server/app/store.py (buy_option, sell_option, set_config, ensure_defaults)"
    - "server/app/main.py (POST /api/options/buy)"
tech-stack:
  added: []
  patterns:
    - "espelho estrutural de appMode/operadorTermo para o novo par permitirOpcaoADescoberto/descobertoTermo"
    - "gate dentro do motor (store.buy_option), não na rota — nenhum atalho de cliente passa por cima"
key-files:
  created:
    - server/tests/test_opcao_descoberto_gate.py
  modified:
    - server/app/defaults.py
    - server/app/store.py
    - server/app/main.py
    - server/tests/test_agent_options.py
    - server/tests/test_automacao.py
    - server/tests/test_opcoes_lastreadas_vencimento.py
    - server/tests/test_fase5_rejeicao_rotas.py
decisions:
  - "Nomes finais dos dois campos: permitirOpcaoADescoberto (bool) e descobertoTermo ({aceitoEm, versao} | None) — decisão D3 do 29-CONTEXT.md, fechada na execução."
  - "Mensagem única do gate (fonte de verdade a espelhar byte a byte pelo plano 29-02): ver MOTIVO_DESCOBERTO_DESLIGADO abaixo."
metrics:
  duration: "~1h"
  completed: "2026-09-13"
---

# Fase 29 Plano 01: Flag de opção a descoberto — campos de config + gate no motor Summary

Construído o par `permitirOpcaoADescoberto`/`descobertoTermo` em `config` e o
gate determinístico dentro de `store.buy_option` que recusa abrir posição de
opção sem lastro quando o flag está desligado — fail-closed por ausência,
sem migração silenciosa de conta nenhuma para ligado.

## O que foi feito

**Task 1 — Campos de config (`server/app/defaults.py`, `server/app/store.py`)**
- `permitirOpcaoADescoberto: False` e `descobertoTermo: None` no dict
  `config` de `defaults.py`, logo depois de `operadorTermo`.
- Backfill em `ensure_defaults`: conta legada ganha os dois campos
  DESLIGADOS, nunca ligados.
- `set_config` recusa ligar `permitirOpcaoADescoberto` sem `descobertoTermo`
  (aceitoEm+versao) já registrado ou vindo no mesmo patch — espelho
  estrutural exato da regra de `appMode`/`operadorTermo`. Desligar é sempre
  livre e não apaga `descobertoTermo`.

**Task 2 — Gate em `buy_option`, tradução 400, reparo dos testes a seco**
- Constante única `MOTIVO_DESCOBERTO_DESLIGADO` em `store.py` (fonte de
  verdade — ver texto exato abaixo).
- Gate inserido em `buy_option` ANTES de qualquer escrita em
  `opts`/`cash`/`history`: fail-closed por ausência da chave, sem
  `ORDER_LOCK` (flag não é recurso consumível), `registrar_rejeicao` também
  para `user_id=None` (espelha `abrir_call_coberta`).
- `sell_option` recebeu só um comentário declarando a decisão — nenhuma
  linha de código mudou nela.
- `POST /api/options/buy` (`main.py`) ganhou `except ValueError as e: raise
  HTTPException(400, str(e))` em volta da chamada a `store.buy_option`,
  fechando a mesma classe de vazamento (500 com texto cru) que a auditoria
  A-00b já fechou em `/api/buy`.
- Reparados os 8 call-sites de teste que compravam a seco direto no motor
  (`test_agent_options.py`, `test_automacao.py`,
  `test_opcoes_lastreadas_vencimento.py`) com um helper local
  `_liberar_descoberto` por arquivo — nenhuma asserção pré-existente mudou
  de valor.

**Task 3 — Guardião (`server/tests/test_opcao_descoberto_gate.py`, novo)**
- 13 testes cobrindo os quatro grupos do plano (A: default/fail-closed: 5
  testes; B: gate na compra: 2; C: fechar nunca barrado, comportamento +
  source assertion: 4; D: superfície HTTP: 2).

## Deviação do plano (Rule 1 — bug direto do próprio Task 2)

`server/tests/test_fase5_rejeicao_rotas.py` **não estava** em
`files_modified` do plano, mas 7 dos seus testes (`test_options_sell_*`,
`test_options_sell_qty_*`) compram uma opção a seco via
`POST /api/options/buy` só para montar a posição antes de testar a rota de
**venda**/rejeição — o gate novo os quebrava com 400 no lugar do 200
esperado na etapa de setup (a suíte foi rodada com `EXIT=1`, 7 failed, antes
do reparo). Corrigidos com o mesmo padrão dos outros três arquivos: um
helper `_liberar_descoberto(m, uid)` que liga o flag direto no motor antes
da chamada HTTP — o próprio arquivo já tinha esse precedente em
`_monta_lastreada` (bypassa a rota de config quando o alvo do teste é
outro). Nenhuma asserção pré-existente mudou de valor; o `git diff --stat`
final da fase inclui esse arquivo a mais além dos 7 do plano, sem tocar
`web/`, `server/app/agent.py`, nem `web/src/opcoes/` (fence D2 preservada).

## Mensagem exata de `MOTIVO_DESCOBERTO_DESLIGADO`

(o plano 29-02 vai espelhá-la byte a byte em `web/src/persistence.js`)

```
Operar opções a descoberto está desligado — ligue o flag em Preferências → Operar opções a descoberto. Lastro obrigatório é o padrão desta conta.
```

## Prova negativa (Task 3, executada de verdade)

1. Comentadas as 5 linhas do gate em `store.buy_option` (bloco
   `cfg = get(conn, "config", ...)` até `raise ValueError(...)`).
2. Rodado:
   `cd server && .venv/bin/python -m pytest tests/test_opcao_descoberto_gate.py -q -k "test_config_sem_a_chave_e_tratado_como_desligado or test_buy_option_com_flag_desligado_levanta_e_nao_move_nada or test_rota_options_buy_flag_desligado_400_com_a_mensagem_do_motor"`
   → **resultado real observado**: `3 failed, 10 deselected` — os testes 2,
   6 e 12 caíram exatamente como o plano exigia (`DID NOT RAISE ValueError`
   no teste 6; `assert 200 == 400` no teste 12; teste 2 falhou pela mesma
   ausência de `ValueError`).
3. Restaurado o gate (removidos os comentários, texto idêntico ao
   original).
4. Confirmado com `git diff --stat server/app/store.py` → saída vazia
   (arquivo idêntico ao commit da Task 2 antes da prova negativa).
5. Re-executado `pytest tests/test_opcao_descoberto_gate.py -q` → `13
   passed`.

## Números da suíte canônica (antes/depois)

- Baseline medida no início da fase (29-CONTEXT/29-01-PLAN, 2026-09-13):
  **2780 passed, 5 skipped, 3 xfailed**, exit 0; 144 `.mjs` `[OK]`.
- Após Task 1: `2780 passed, 5 skipped, 3 xfailed`, exit 0 (sem regressão).
- Após Task 2 (1ª rodada, ANTES do reparo de `test_fase5_rejeicao_rotas.py`):
  `EXIT=1`, `7 failed, 2773 passed` — regressão real detectada.
- Após Task 2 (2ª rodada, reparo aplicado): `2780 passed, 5 skipped, 3
  xfailed`, exit 0.
- Após Task 3 (guardião novo): **2793 passed** (2780 + 13 novos), `5
  skipped, 3 xfailed`, exit 0; 144 `.mjs` `[OK]`.

Suíte rodada 4 vezes ao todo (uma por task, mais uma repetição na Task 2
por causa da regressão real encontrada e corrigida) — dentro do orçamento
"uma vez por task, duas se houver correção" do plano.

## Verificação — comandos e resultados

```
$ bash scripts/executar.sh --testes
2793 passed, 5 skipped, 3 xfailed, 990 warnings in 63.23s — EXIT=0
144 arquivos web/tests/*.mjs — todos [OK]

$ python -m pytest server/tests/test_opcao_descoberto_gate.py -q
13 passed

$ git diff --stat ddbfe80~1..5a01b52
8 files changed, 391 insertions(+), 14 deletions(-)
```

`git diff --stat` mostra os 7 arquivos do `files_modified` do plano mais
`server/tests/test_fase5_rejeicao_rotas.py` (deviation documentada acima).
Nenhuma linha em `web/`, `server/app/agent.py` ou `web/src/opcoes/`.

## Limitações conhecidas

- Nenhuma. `sell_option`/`close_option_vencida` seguem intactos e
  comprovadamente livres do gate (comportamento + source assertion).
- A publicação (bump/deploy) não faz parte deste plano — backend-only,
  sem rebuild de front.

## Instruções para validar localmente

```bash
cd /Users/acamerini/dev/bolsia/b3-agente
bash scripts/executar.sh --testes
python -m pytest server/tests/test_opcao_descoberto_gate.py -q
```

## Self-Check: PASSED

- `server/app/defaults.py` — FOUND (permitirOpcaoADescoberto, descobertoTermo)
- `server/app/store.py` — FOUND (MOTIVO_DESCOBERTO_DESLIGADO, gate, comentário em sell_option)
- `server/app/main.py` — FOUND (except ValueError em /api/options/buy)
- `server/tests/test_opcao_descoberto_gate.py` — FOUND (13 testes)
- commit ddbfe80 — FOUND (`git log --oneline | grep ddbfe80`)
- commit d001d10 — FOUND
- commit 5a01b52 — FOUND
