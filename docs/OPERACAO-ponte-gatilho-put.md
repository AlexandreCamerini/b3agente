# OPERAÇÃO — Ponte Gatilho→Put (Fase 10 v1.2)

Runbook do hook automático que cruza o Radar diário com as carteiras dos
usuários e grava uma sugestão de put de proteção quando um setup de baixa
dispara sobre um ticker que o usuário já tem comprado —
`server/app/put_bridge.py`. Este documento existe para que alguém
(inclusive o Alex, meses depois) entenda por que o log mostra `sugestoes: 0`
em produção sem precisar reabrir o ADR-021.

## 1. O que a ponte faz e quando roda

Dentro do `scheduler_loop` já existente de `server/app/agent.py` (nenhum
scheduler novo), uma vez por pregão útil, `put_bridge.maybe_run()`:

1. Lê o Radar diário já armazenado (`radar_daily.get_stored`, custo de rede
   zero — não dispara nenhuma consulta nova) e extrai, por ticker
   normalizado, o primeiro setup **ativo** de lado `"baixa"` (a mesma
   condição que já faz `setups.plano_operacional` dizer VENDER).
2. Cruza esse conjunto com as carteiras (`positions`) de **todos** os
   usuários com conta no servidor (o balde anônimo, chave `positions` sem
   prefixo `u:`, fica fora naturalmente — não casa com o filtro SQL).
3. Para os tickers na interseção (gatilho ∩ carteira), ordenados por
   confluência decrescente e cortados em `MAX_TICKERS_DIA=10`, consulta a
   cadeia de opções **sequencialmente** (nunca concorrente) via
   `options_provider.get_options(ticker)` — o mesmo seletor que
   `options_api.py` já usa.
4. Escolhe UM contrato de put candidata por ticker (`put_bridge.triar_put`)
   e grava uma linha por usuário em `put_suggestions`, com proveniência.

Horário default: **09:30** BRT, depois do Radar (08:45) e do
`signal_ledger_job` (09:15) — ordem provada com o laço real do agente
(`test_hook_roda_depois_do_ledger`, `10-02-SUMMARY.md`).

## 2. Variáveis de ambiente

| Variável | Efeito | Estado em produção |
|---|---|---|
| `B3_PUT_BRIDGE_HHMM` | Horário (BRT, `HH:MM`) em que a rodada diária dispara. Valor inválido cai no default `09:30`. | **Não definida.** A ponte roda no default. |
| `B3_PUT_BRIDGE_OFF` | Qualquer valor truthy desliga a ponte inteira (`enabled()` devolve `False`, `maybe_run` retorna sem fazer nada). | **Não definida.** A ponte está ligada por padrão desde que este milestone shipou. |

Nenhuma das duas foi definida em produção por este milestone — a ponte é
**inofensiva com as duas ausentes**: ela roda no horário default, mas
(ver §3) fecha sem gravar nenhuma linha enquanto `B3_OPTIONS_PROVIDER`
permanecer no default de produção.

## 3. Por que o resumo em produção fecha com `sugestoes: 0` hoje

Isto é o **desenho**, não um defeito (D-10-O do `10-03-PLAN.md`, formalizado
na Decisão 3 do ADR-021).

`put_bridge.run_diario` só acessa a cadeia de opções pelo seletor
`options_provider.get_options()` — a mesma alavanca de rollback manual por
env que o ADR-020 (D-02) já estabeleceu, nunca um provedor específico
hard-coded. Com `B3_OPTIONS_PROVIDER=yahoo` (o default de produção, que
**este milestone não muda** — guardrail explícito de v1.2), o contrato
devolvido pelo Yahoo não publica `exerciseStyle` para nenhum contrato de
opção. `triar_put()` pula todo contrato sem esse campo real
(`puladosSemEstilo`, nunca completado por default — parada dura do
contrato de autonomia) e, sem nenhum contrato elegível, devolve
`(None, "nenhuma put elegível")`. Nenhuma sugestão é gravada; a rodada
termina normalmente, sem erro, sem exceção.

No dia em que `B3_OPTIONS_PROVIDER` apontar para `mydata` (decisão de
arquitetura/negócio fora do escopo de v1.2 — ver o item "Retomar virada de
produção do mydata" em `.planning/STATE.md` e a nota de WR-01 em
`.planning/notes/decisoes-autonomas-v1.2.md`), a ponte passa a produzir
sugestões reais sem nenhuma mudança de código: o contrato do mydata já
publica `exerciseStyle`/`iv` reais (ADR-004/ADR-020).

## 4. Como inspecionar

**Query SQL** (mesma conexão/banco da aplicação, `B3_DB_PATH`):

```sql
SELECT ticker, data_pregao, contrato, strike, vencimento,
       estilo_exercicio, iv, estado, fonte, criado_em
  FROM put_suggestions
 ORDER BY criado_em DESC
 LIMIT 20;
```

Se a query devolver zero linhas em produção hoje, isso é esperado — ver §3.

**Log.** Toda rodada (com ou sem sugestão) é silenciosa no caminho de
sucesso; só o caminho de falha loga, com o prefixo `[put-bridge]`:

```
[put-bridge] rodada diária falhou: <mensagem>
```

Uma falha aqui **nunca** derruba o heartbeat, o kill-switch nem o ciclo de
stop/alvo — o hook tem try/except próprio dentro de `maybe_run`, e o
`scheduler_loop` tem um segundo try/except em volta da chamada (dois
cintos, mesmo padrão de `signal_ledger_job`). Se a rodada falhar, o
marcador `putBridgeLastRun` NÃO é gravado — a ponte tenta de novo no
próximo dia útil, nunca fica travada.

Telemetria em memória (`put_bridge.LAST_RUN`) existe para a Fase 11 poder
plugar num painel **se e quando** a exposição for aprovada — hoje ela não
está ligada a `agent.status_snapshot` nem a nenhuma rota, porque o portal
admin é superfície proibida por PUT-03 nesta fase (D-10-L do ADR-021).

## 5. Limites de consumo

- **2 requisições por ticker** consultado (1 `/vencimentos` + 1 página de
  `/opcoes/{ticker}`, mesmo custo unitário medido em
  `docs/MEDICAO-Mydata-2026-08-27.md`).
- **Teto duro de 10 tickers/dia** (`MAX_TICKERS_DIA`) — no pior caso, a
  ponte soma no máximo 20 requisições/dia ao consumo total do gate
  compartilhado (`mydata_budget`, 60/min · 2.000/dia), 1% do orçamento
  diário.
- Consulta **sempre sequencial** — nunca concorrente — mitigação de
  arquitetura para WR-01 (achado de gate de orçamento não-atômico,
  ver ADR-021 Decisão 4). A rodada roda 1x/dia útil, fora do pico do Radar
  (08:45)/ledger (09:15).

## 6. O que NÃO existe nesta fase

- **Nenhuma rota HTTP** expõe `put_suggestions` — provado por teste
  guardião que lê `app.main.app.routes` (`test_nenhuma_rota_serve_a_tabela`,
  `server/tests/test_put_bridge_sem_superficie.py`).
- **Nenhum push, card ou texto de vocabulário** menciona a ponte —
  `server/app/skill_ref.py` e o front (`web/src/`, `web-admin/src/`)
  seguem sem nenhuma referência, provado pelo mesmo guardião.
- **Nenhuma UI.** A sugestão fica só no banco; ver a nota final da §4 sobre
  telemetria em memória não-conectada.
- **Nenhuma execução simulada.** A Fase 11 (ciclo de vida e monitoramento)
  é quem vai evoluir o estado `armada` → `executada (simulada)` reusando os
  contratos de `optionPositions` já estabelecidos por ADR-003/004/005 — sem
  reimplementar preço médio, PnL ou proveniência de posição de opção.
- **Nenhuma opção vendida, a descoberto, com margem ou com atribuição.**
  Estruturalmente impossível pelo `CHECK(option_type = 'put')` e pela
  ausência de qualquer coluna de lado/margem no schema (ADR-021 Decisão 2).
