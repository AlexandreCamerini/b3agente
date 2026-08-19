# qa/48 — Fase 2 (Realismo de Mercado): verificação ponta-a-ponta contra servidor real

> Data real do exercício: **2026-08-19, madrugada (agora BRT ~01:15–01:31)**.
> Plano: `02-07` (última wave da Fase 2, MERC-01..04). Objetivo: fechar a fase
> com evidência AO VIVO — servidor `uvicorn` real, banco SQLite descartável,
> rotas batidas via `curl`, nunca `TestClient`. Teste verde não é evidência
> suficiente (histórico do repo: defeitos de UI/sync só a verificação ao vivo
> pegou).

## Veredito: as DUAS suítes + o build do front passaram; o ciclo completo
## (pendente → execução → histórico) fechou a conta do caixa em todo passo

---

## 1. Suíte canônica completa

Comando executado literalmente: `bash scripts/executar.sh --testes`.

```
$ bash scripts/executar.sh --testes
...
1100 passed, 217 warnings in 17.96s

== Suítes web ==
  [OK] web/tests/test_admin_ui.mjs
  ... (82 arquivos, todos [OK]) ...
  [OK] web/tests/test_wiring_deps.mjs
```

- **Saída: exit 0** (confirmado via `$?` após rodar de novo separadamente).
- Backend: **1100 passed**, 0 falhas (inclui `test_ordens_pendentes.py`,
  `test_ordens_pendentes_rotas.py`, `test_ordens_pendentes_scheduler.py` —
  os 3 arquivos de guardiões unitários das Fases 02-01/02-03).
- Web: **82/82 arquivos `.mjs` `[OK]`** (inclui `test_status_mercado_ui.mjs`,
  `test_ordens_pendentes_ui.mjs`, `test_ordens_pendentes_client.mjs`,
  `test_api_parity.mjs`).
- Nenhum substituto usado — `scripts/test.sh` sozinho NÃO foi tratado como
  suficiente (regra do CLAUDE.md), a suíte web completa (todos os
  `web/tests/*.mjs`) rodou junto na mesma invocação.

## 2. Build do front

Comando: `cd web && npx vite build`.

```
vite v6.4.3 building for production...
✓ 89 modules transformed.
...
✓ built in 1.10s
PWA v0.21.2 — mode generateSW — precache 23 entries (794.91 KiB)
```

- **Saída: exit 0.** Pipeline completo (Vite + Rollup + plugin PWA), sem
  substituto de `esbuild`.
- Aviso de chunk >500kB (`index-m2fN9L2A.js`, 742kB) é pré-existente, não
  bloqueante — fora do escopo desta verificação (nenhum arquivo tocado por
  este plano).

## 3. Setup do exercício ao vivo (T-02-32: banco descartável)

- `B3_DB_PATH` apontado para
  `/private/tmp/claude-501/.../scratchpad/0207-e2e.db` — arquivo NOVO,
  fora de qualquer diretório do repositório ou de dado real. Confirmado
  antes de subir o servidor (`rm -f` do arquivo se existisse; não existia).
- Servidor real: `uvicorn app.main:app --host 127.0.0.1 --port 8787` a
  partir de `server/`, processo em background, log capturado em
  `0207-server.log` (sem tracebacks nem erro em nenhuma requisição — todas
  `200 OK`, conferido por `grep -iE "error|traceback|exception"` no log).
- Todas as chamadas abaixo foram `curl` reais contra `http://127.0.0.1:8787`,
  **nunca `TestClient`**.
- Cotação real (`PETR4`) veio do provedor Yahoo (backup/default sem
  `BRAPI_TOKEN` configurado neste ambiente — `B3_CANDLE_PROVIDER` não
  setado, default é `yahoo`), preço `42.60` na hora do exercício.

## 4. `GET /api/market/status` sem `Authorization` (rota pública)

```json
{
    "aberto": false,
    "diaDePregao": true,
    "abertura": "10:00",
    "fechamento": "16:55",
    "agoraBRT": "19/08 01:28",
    "afterMarket": false
}
```

- As 6 chaves esperadas estão presentes.
- `agoraBRT` = "19/08 01:28" e `aberto: false` batem com a realidade — é
  madrugada, muito antes das 10:00 (abertura do pregão), 19/08/2026 é
  quarta-feira (`diaDePregao: true`, dia útil, sem feriado).
- Rota chamada **sem header `Authorization`** — nenhum 401, nenhuma
  exigência de sessão, confirmando que é pública por desenho (T-02-08).

## 5. Conta registrada e estado inicial

`POST /api/auth/register` com `qa-0207-e2e@local.test` devolveu token +
estado limpo:

```
cash: 10000.0
caixaReservado: 0
pendingOrders: []
positions: []
history len: 0
```

(Este foi o PRIMEIRO usuário do banco descartável, então recebeu o
bootstrap aditivo de `role_admin` — ADR-013, comportamento esperado e
irrelevante para o exercício de carteira/ordens.)

## 6. `POST /api/buy` com mercado fechado → ordem pendente

Requisição: `{"t":"PETR4","qty":100}`, com o mercado já fechado no relógio
real (nenhum monkeypatch necessário nesta etapa).

Resposta (campos relevantes):

```json
{
  "pendente": true,
  "order": {
    "id": "po_ef67bd12",
    "tipo": "COMPRA",
    "t": "PETR4",
    "qty": 100,
    "precoReferencia": 42.6,
    "caixaReservado": 4260.0,
    "avgReservado": null
  },
  "priceUsed": null,
  "precoReferencia": 42.6,
  "cash": 5740.0,
  "caixaReservado": 4260.0,
  "history": []
}
```

**Conta do caixa (criação):** `cash 5740.0 + caixaReservado 4260.0 = 10000.0`
— igual ao saldo inicial. `pendente: true`, `priceUsed: null` (não
executou), `history` com o mesmo tamanho de antes (0 → 0).

## 7. `DELETE /api/orders/pending/{id}` → cancelamento

```
cash: 10000.0
caixaReservado: 0
pendingOrders: []
history: []
```

**Conta do caixa (cancelamento):** volta a `10000.0` exato, `caixaReservado`
zera. `history` continua vazio (cancelamento não gera linha de operação —
comportamento consistente com "não houve execução").

## 8. Nova ordem pendente + execução forçada pela passada do laço

Criada uma segunda ordem pendente idêntica (`po_314bb511`,
`caixaReservado: 4260.0`, `cash: 5740.0` — mesma conservação do passo 6).

**Como o gate de horário foi satisfeito** (documentação exigida pelo plano):
`POST /api/agent/run-now` **não serve** para isto — ele dispara
`run_cycle_for` (ciclo por usuário do Operador), que nunca toca
`pending_orders.executar_pendentes`; só o bloco novo dentro de
`agent.scheduler_loop` (plano 02-03) executa pendentes. Como agora (madrugada)
está fora do pregão, rodei `agent.scheduler_loop(conn, quotes_getter,
once=True)` **num processo Python separado**, conectado ao MESMO arquivo
SQLite do servidor real (`B3_DB_PATH` idêntico; WAL + `busy_timeout=5000`
já configurados em `db.connect()`, garantindo visibilidade entre processos),
com **monkeypatch documentado**: `agent.in_market_hours = lambda *a, **k:
True` — só neste processo efêmero, nunca no processo do servidor real, que
manteve o relógio real o tempo todo. `quotes_getter` devolveu o preço fixo
`42.60` (mesmo `precoReferencia` da ordem, sem rede) para a execução ser
determinística.

Saída do script: `LAST_PENDING: {'at': '19/08 01:30', 'escopos': 2,
'executadas': 1, 'canceladas': 0, 'erro': None}`.

**Verificação via rota real do servidor** (`GET /api/state`, mesmo
processo do `uvicorn`, mesmo token):

```json
{
  "cash": 5740.0,
  "caixaReservado": 0,
  "positions": [
    {"t": "PETR4", "qty": 100, "avg": 42.6, "stop": null, "alvo": null}
  ],
  "pendingOrders": [],
  "history": [
    {"date": "19/08/2026 01:30", "type": "COMPRA", "t": "PETR4",
     "qty": 100, "price": 42.6, "pnl": null, "origem": "pendente"}
  ]
}
```

- `pendingOrders` esvaziou, posição `PETR4` criada com `avg: 42.6`
  (idêntico ao `precoReferencia` reservado), `history` ganhou 1 linha com
  `origem: "pendente"` — exatamente o rastro que o plano pede.
- **Conta do caixa (execução):** `cash 5740.0` não volta a `10000.0` — a
  reserva (`4260.0`) virou POSIÇÃO, não caixa. Patrimônio total
  (`cash + valor da posição ao preço do motor`) = `5740 + 100×42.6 = 10000`,
  conservado — exatamente a exceção que o próprio plano antecipa ("exceto
  na execução, onde vira posição pelo preço do motor").

`GET /api/agent/status` (mesmo processo do servidor real, token da conta):

```
"ordensPendentes": {
    "total": 0,
    "escopos": 2,
    "ultimoCiclo": {"at": null, "escopos": 0, "executadas": 0, ...}
}
```

- `total: 0` — correto, lido AO VIVO do banco (`store.scopes_com_pendentes`
  + `pending_orders.listar`), reflete a execução real feita pelo script.
- **Limitação conhecida, documentada explicitamente (não é defeito):**
  `ultimoCiclo` (o contador `LAST_PENDING`) fica em branco no processo do
  servidor real, porque é um dict **em memória do processo** — o script que
  forçou a passada rodou num processo Python separado; sua cópia de
  `LAST_PENDING` foi atualizada (visto no print acima), mas nunca chega ao
  processo do `uvicorn`, que é quem responde `/api/agent/status`. Isto é
  esperado dado o método (processo externo) e não indica bug em
  `status_snapshot`/`scheduler_loop` — o dado que TEM que vir do banco
  (`total`) veio certo; o dado que É memória de processo (`ultimoCiclo`) só
  seria populado rodando a passada DENTRO do próprio processo do servidor
  (por exemplo, aguardando o próximo tick real do `scheduler_loop` do
  servidor em produção, algo que este exercício não tenta simular).
  Achado registrado aqui para não ser re-litigado como falha numa
  verificação futura.
- `escopos: 2` (antes e depois) — não é bug: `store.scopes_com_pendentes`
  inclui por desenho o "escopo legado" (`user_id=None`), que tem uma linha
  `pendingOrders -> []` gravada no kv (bucket anônimo histórico, hoje vazio
  mas presente). Confirmado lendo o kv diretamente: só 1 escopo (o usuário
  de teste) tinha ordens de fato; o outro é o balde legado vazio. Documentado
  no próprio docstring de `scopes_com_pendentes` ("+ escopo legado, `None`").

## 9. Fluxo de VENDA pendente (criação → cancelamento, mesmo `avg`)

Com a posição `PETR4 100@42.6` recém-criada, `POST /api/sell` com
`{"t":"PETR4","qty":40}` e mercado fechado:

```json
{
  "pendente": true,
  "positions": [],
  "order": {
    "id": "po_4d46ecf0", "tipo": "VENDA", "t": "PETR4", "qty": 100,
    "precoReferencia": null, "caixaReservado": null, "avgReservado": 42.6
  },
  "cash": 5740.0,
  "caixaReservado": 0
}
```

**Nota sobre `qty`:** pedi `40`, a ordem foi criada com `qty: 100`. **Não é
bug** — `pending_orders.criar_venda` normaliza para lote de 100
(`qty = max(100, round(qty/100)*100)`), a MESMA normalização que
`store.sell` já usa na venda imediata (lote redondo B3). Como a posição
inteira era 100, o pedido de 40 arredondou para o lote mínimo (100) e
reservou a posição inteira. Comportamento herdado e consistente, não
introduzido por este plano — registrado aqui porque não é óbvio à primeira
leitura da resposta.

- **Quantidade reservada sai da posição na criação:** `positions: []`
  (a posição de 100 zerou, coerente com a reserva de 100).
- `avgReservado: 42.6` — preço médio da posição preservado na ordem.

`DELETE /api/orders/pending/po_4d46ecf0`:

```json
{
  "positions": [
    {"t": "PETR4", "qty": 100, "avg": 42.6, "stop": null, "alvo": null}
  ],
  "pendingOrders": [],
  "cash": 5740.0
}
```

- **Volta no cancelamento com o mesmo preço médio:** posição restaurada
  `qty: 100, avg: 42.6` — idêntico ao estado antes da venda pendente.

## 10. Conta do caixa — tabela consolidada

| Passo | cash | caixaReservado | cash+caixaReservado | Observação |
|---|---:|---:|---:|---|
| Estado inicial | 10000.0 | 0 | **10000.0** | conta nova |
| Compra pendente criada (#1) | 5740.0 | 4260.0 | **10000.0** | conservado |
| Compra pendente #1 cancelada | 10000.0 | 0 | **10000.0** | conservado, volta exato |
| Compra pendente criada (#2) | 5740.0 | 4260.0 | **10000.0** | conservado |
| Compra pendente #2 EXECUTADA | 5740.0 | 0 | 5740.0 (+ posição 4260,0) | vira posição — exceção documentada pelo plano |
| Venda pendente criada | 5740.0 | 0 | — | reserva é de QUANTIDADE, não de caixa; posição zera |
| Venda pendente cancelada | 5740.0 | 0 | — | posição volta 100@42,6 |

Patrimônio (`cash + valor a mercado das posições`) permanece `10000.0` do
início ao fim do exercício, em todos os passos.

## 11. Erros/defeitos encontrados

**Nenhum.** Todas as respostas bateram com o contrato documentado nos
SUMMARYs de 02-01/02-03/02-04/02-05/02-06. As duas notas acima (contador
`ultimoCiclo` em memória de processo; normalização de lote em venda
pendente) são comportamento esperado/documentado, não bugs — registradas
para não serem re-litigadas.

## 12. Limitações conhecidas deste exercício

- A execução forçada da passada do scheduler rodou num **processo Python
  separado** do servidor `uvicorn` (mesmo banco, via WAL) — necessário
  porque o horário real (madrugada) está fora do pregão e
  `POST /api/agent/run-now` não toca `pending_orders`. Efeito colateral:
  o contador `ultimoCiclo` (memória do processo) não aparece no
  `/api/agent/status` do servidor real, só o `total` (lido do banco) — ver
  seção 8.
- Não foi exercitado o AUTO-CANCELAMENTO na abertura (preço subiu além do
  caixa reservado) — fora do escopo explícito do `<action>` deste plano
  (que pede reserva → execução → cancelamento manual, não o cenário de
  falha de execução). Coberto por guardiões unitários em
  `test_ordens_pendentes_scheduler.py` (02-03-SUMMARY).
- Verificação visual (badge, seção Pendentes, iPhone) é a Task 2 deste
  mesmo plano — checkpoint humano separado, não coberta por este relatório.

## 13. Ambiente

- `server/.venv` recriado neste worktree (`python3 -m venv .venv && pip
  install -r requirements.txt`) — não versionado, mesmo padrão já
  documentado em 02-01/02-03-SUMMARY.
- `web/node_modules` linkado por symlink ao worktree `peaceful-swanson-e9e462`
  (lockfile `package-lock.json` confirmado byte-idêntico via `diff` antes
  do link) — usado só para rodar a suíte web e o build; removido antes do
  commit deste relatório (symlinks não batem no padrão `node_modules/` do
  `.gitignore`, apareceriam como `??` no `git status`).
- Worktree nasceu de uma base desatualizada (`403432f`, sem `.planning/` e
  sem o trabalho de 02-01..02-06) — auto-recuperado por
  `git merge claude/gsd-revisao-aplicacao-b9b4ef` (fast-forward limpo,
  confirmado `git merge-base --is-ancestor` antes de agir, sem commits
  locais divergentes a perder).
