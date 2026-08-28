# OPERAÇÃO — Ciclo de Vida da Sugestão de Put (Fase 11 v1.2)

Runbook da varredura diária que avança o estado de cada sugestão de put
gravada pela ponte (Fase 10) — `server/app/put_lifecycle.py`. Este documento
existe para que alguém (inclusive o Alex, meses depois) entenda por que a
tabela `put_suggestions` mostra `linhas: 0` na varredura de hoje sem
precisar reabrir o ADR-022.

## 1. O que o ciclo de vida faz e quando roda

Dentro do `scheduler_loop` já existente de `server/app/agent.py` (nenhum
scheduler novo), uma vez por pregão útil, `put_lifecycle.maybe_run()`:

1. Lê `put_suggestions.listar_abertas()` — toda sugestão cujo estado NÃO é
   terminal (`expirada_sem_uso`/`fechada`).
2. Para cada linha, lê `candle_cache.peek(ticker, "1d")` (custo zero de
   rede — o cache que o Radar diário já pagou) e resolve o fechamento mais
   recente/o fechamento de liquidação via `resolver_spots()`.
3. Aplica `decidir()` — a máquina de decisão pura que cobre as 5 transições
   do ROADMAP — e grava o resultado pela única porta de escrita,
   `put_suggestions.transicionar()`.
4. Linha sem preço confiável (candle ausente) não avança e não é
   descartada: `registrar_pendencia()` grava a data de HOJE em
   `pendente_desde` (só na primeira vez — a primeira data de pendência é a
   que vale) e a rodada segue para a próxima linha.

Horário default: **09:45** BRT, depois da ponte (09:30) e do Radar/ledger —
ordem provada com o laço real do agente
(`server/tests/test_put_lifecycle_scheduler.py`).

## 2. Variáveis de ambiente

| Variável | Efeito | Estado em produção |
|---|---|---|
| `B3_PUT_LIFECYCLE_HHMM` | Horário (BRT, `HH:MM`) em que a varredura diária dispara. Valor inválido cai no default `09:45`. | **Não definida.** A varredura roda no default. |
| `B3_PUT_LIFECYCLE_OFF` | Qualquer valor truthy desliga a varredura inteira (`enabled()` devolve `False`, `maybe_run` retorna sem fazer nada). | **Não definida.** A varredura está ligada por padrão desde que esta fase shipou. |

Nenhuma das duas foi definida em produção por este milestone — os dois
gates (ponte e ciclo de vida) são **independentes de propósito**: desligar
um não desliga o outro.

## 3. Por que `linhas: 0` em produção hoje é o desenho

Isto é o **desenho**, não um defeito (ADR-022, Decisão 4) — mesma postura
que o §3 de `docs/OPERACAO-ponte-gatilho-put.md` já documentou para a
ponte.

`put_lifecycle.run_diario` varre `put_suggestions.listar_abertas()`. Com
`B3_OPTIONS_PROVIDER=yahoo` (o default de produção, que **este milestone
não muda**), o contrato do Yahoo não publica `exerciseStyle`, então
`put_bridge` (Fase 10) nunca grava uma linha `armada` com proveniência
completa — `put_suggestions` fica **vazia**, e todo dia a varredura devolve
`{"linhas": 0, "avancos": 0, "pendentes": 0, "porEstado": {}, "erros": []}`,
sem erro, sem exceção.

No dia em que `B3_OPTIONS_PROVIDER` apontar para `mydata` (decisão de
arquitetura/negócio fora do escopo de v1.2), a ponte passa a gravar linhas
`armada` reais e o ciclo de vida passa a ter trabalho a fazer sem nenhuma
mudança de código — a máquina de decisão e a varredura já estão testadas
ponta a ponta.

## 4. Como inspecionar

**Query SQL** (mesma conexão/banco da aplicação, `B3_DB_PATH`):

```sql
SELECT estado, COUNT(*) FROM put_suggestions GROUP BY estado;
```

**Linhas pendentes** (falta preço confiável do ativo-objeto há mais de um
dia):

```sql
SELECT id, ticker, contrato, estado, pendente_desde
  FROM put_suggestions
 WHERE pendente_desde IS NOT NULL
 ORDER BY pendente_desde ASC;
```

Se as duas queries devolverem zero linhas em produção hoje, isso é
esperado — ver §3.

**Log.** Toda rodada (com ou sem avanço) loga um resumo:

```
[put-lifecycle] {'linhas': 0, 'avancos': 0, 'pendentes': 0, 'porEstado': {}, 'erros': []}
```

Falha da rodada inteira loga com o prefixo `[put-lifecycle]`:

```
[put-lifecycle] rodada diária falhou: <mensagem>
```

Uma falha aqui **nunca** derruba o heartbeat, o kill-switch nem o ciclo de
stop/alvo — try/except POR LINHA dentro de `run_diario` (uma linha
envenenada não aborta as demais) + try/except PRÓPRIO em `maybe_run` (dois
cintos, mesmo padrão de `put_bridge`/`signal_ledger_job`). Se a rodada
falhar, o marcador `putLifecycleLastRun` NÃO é gravado — a varredura tenta
de novo no próximo dia útil, nunca fica travada.

Telemetria em memória (`put_lifecycle.LAST_RUN`) existe pronta para um
painel futuro **se e quando** a exposição for aprovada — hoje não está
ligada a `agent.status_snapshot` nem a nenhuma rota (guardião estático
`grep -c putLifecycle` sobre `agent.py`, `server/tests/test_put_lifecycle_sem_carteira.py`).

## 5. Limites de consumo

**Zero requisição de rede.** `run_diario` só lê `candle_cache.peek()` — o
cache em memória/SQLite que o Radar diário já populou. Nenhuma chamada a
`options_provider`/`candle_provider`/`httpx` existe em `put_lifecycle.py`
(guardião estático que lê o próprio fonte, incluindo docstring). A
varredura roda 1x/dia útil sobre no máximo dezenas de linhas — custo de CPU
irrelevante, sem custo de orçamento de API algum.

## 6. O que explicitamente NÃO existe nesta fase

- **Nenhuma rota HTTP** expõe `put_suggestions` nem o estado do ciclo de
  vida — provado por teste guardião que lê `app.main.app.routes`.
- **Nenhum push, card ou texto de vocabulário** menciona o ciclo de vida —
  `server/app/skill_ref.py` e o front (`web/src/`, `web-admin/src/`) seguem
  sem nenhuma referência.
- **Nenhuma UI.** O estado fica só no banco.
- **Nenhum efeito na carteira real do usuário.** `cash`/`positions`/
  `history`/`optionPositions` ficam byte-idênticos ao longo de um ciclo de
  vida completo — provado por comportamento (não por afirmação), ver
  `server/tests/test_put_lifecycle_sem_carteira.py`.
- **Nenhuma opção vendida, a descoberto, com margem ou com atribuição.**
  Estruturalmente impossível (herdado do `CHECK(option_type = 'put')` e da
  ausência de coluna de lado/quantidade/margem, ADR-021 Decisão 2).
- **Nenhum preço de opção ao vivo, nenhum monitoramento intradiário.**
  Consequência direta da decisão de arquitetura travada "EOD de ponta a
  ponta" (ADR-021, Contexto) — o ciclo de vida também é EOD, uma rodada por
  pregão útil.
