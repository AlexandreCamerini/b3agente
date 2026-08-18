# Phase 2: Realismo de Mercado - Context

**Gathered:** 2026-08-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Status real de mercado (aberto/fechado, via `pregao.py`) visível ao usuário, e
ordens colocadas fora do horário de pregão viram pendentes, executando ao
preço de abertura do pregão seguinte. Cobre MERC-01..04.

</domain>

<decisions>
## Implementation Decisions

### Regras de negócio (fechadas na abertura da milestone v1.1)
- **D-01:** Ordem fora do horário de pregão fica "pendente" e executa ao
  preço de ABERTURA REAL do pregão seguinte — não ao preço do momento do
  pedido.
- **D-02:** Caixa da ordem pendente é reservado no momento do PEDIDO, não só
  na execução.
- **D-03:** Usuário pode cancelar uma ordem pendente a qualquer momento antes
  da execução.

### Implementação — critério "mais simples sem prejuízo ao funcionamento
básico" (decisão do Alex: não precisamos de precisão total)
- **D-04 (precisão do horário):** A execução da ordem pendente acontece na
  PRIMEIRA passada do `scheduler_loop` após `pregao.ABERTURA` (10:00) —
  cadência default de 300s (`agent.py:31`), então pode executar até ~5min
  depois das 10:00:00. Não vale criar um gatilho mais preciso que isso.
- **D-05 (mecânica de reserva de caixa):** Reusa o caminho de débito que já
  existe para ordem imediata — debita `cash` na hora do PEDIDO (mesmo código
  de `store.py:549`), credita de volta se a ordem for cancelada antes de
  executar. Não criar um campo novo "caixaReservado"/"caixaDisponível" — é
  mais simples debitar e, se cancelar, devolver.
- **D-06 (mecânica de reserva de posição, ordem de venda pendente):** Mesma
  lógica do D-05 aplicada à posição: subtrai a quantidade da posição
  disponível no momento do PEDIDO da venda, devolve se cancelar. Evita vender
  a mesma ação duas vezes em ordens pendentes simultâneas.
- **D-07 (múltiplas ordens pendentes no mesmo ticker):** Permitido, sem
  bloqueio nem substituição — cada ordem pendente é independente, processada
  na ordem em que foi criada.
- **D-08 (onde exibir o status de mercado):** No `Topbar` (`App.jsx:707`,
  renderizado em toda aba, já mostra patrimônio/caixa/variação do dia) — mais
  visível que uma tela específica, e é o componente mais próximo de "o que o
  usuário vê ao entrar no app".
- **D-09 (onde exibir ordens pendentes):** Dentro da `HistoricoScreen`
  existente (`App.jsx:3647`), seção "Pendentes" no topo, reusando o
  componente de tabela já existente — não criar tela nova.

### Claude's Discretion
- Texto exato do badge de status de mercado (ex.: "Mercado aberto" /
  "Mercado fechado — abre 10:00" vs. variações) — seguir o vocabulário por
  modo já existente (`copy.js`), tom didático no Modo Estudo.
- Nome exato do novo status de ordem no modelo de dados (`"pendente"` é o
  termo natural, mas o nome do campo/enum fica a critério de quem planeja,
  desde que documentado).
- Se a ordem pendente cancelada devolve caixa/posição imediatamente ou no
  próximo tick — mais simples é devolver imediatamente na própria ação de
  cancelar (sem esperar o scheduler).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Fonte única de horário de pregão (reusar, não duplicar)
- `server/app/pregao.py` — `is_trading_day()` (linhas 106-112),
  `in_market_hours()` (linhas 124-136), `ABERTURA`/`FECHAMENTO` (linhas
  33-34) — fonte ÚNICA de "a bolsa está aberta agora?"
- `server/app/agent.py:208-217` — `in_market_hours()` local, delega para
  `pregao.py` (comentário explícito "fonte única")

### Scheduler / execução automática (ponto de integração)
- `server/app/agent.py:874` — `scheduler_loop`, roda a cada
  `INTERVAL_S_DEFAULT = 300` (`agent.py:31`)
- `server/app/agent.py:936` — gate `if not kill_switch_on() and
  in_market_hours():` — padrão a seguir pra disparar a execução de ordens
  pendentes
- `server/app/agent.py:920-935` — job do Radar diário roda FORA do gate de
  `in_market_hours`, padrão de referência pra "algo que roda perto da
  abertura"

### Motor de ordens (onde a ordem pendente se conecta)
- `server/app/store.py:530-563` (`buy`), `:566-590` (`sell`) — motor
  determinístico atual, débito de caixa em `:549`, `cash` como valor único
  sem distinção reservado/disponível (`SECTIONS` em `store.py:9`)
- `server/app/main.py:1501-1518` (`/api/buy`), `:1521-1535` (`/api/sell`) —
  rotas atuais, sem nenhuma checagem de horário

### Frontend — pontos de integração
- `web/src/App.jsx:707-753` — `Topbar`, onde entra o badge de status de
  mercado (D-08)
- `web/src/App.jsx:6144` (`BuyModal`), `:6192` (`SellModal`),
  `:6732-6745` (`confirmBuy`), `:6684-6694` (`confirmSell`) — fluxo de
  submissão de ordem, onde a lógica de "fora do pregão → pendente" entra
- `web/src/App.jsx:3647` (`HistoricoScreen`) — onde entra a seção
  "Pendentes" (D-09)
- `web/src/App.jsx:5052` — único lugar hoje que já lê `pregaoAberto`
  (tela de diagnóstico do Operador) — reusar o mesmo dado, não duplicar

### Princípios do produto
- `CLAUDE.md` — princípio 9 (estados completos, incluindo "mercado
  fechado"), princípio 5 (cálculo determinístico — o preço de execução da
  ordem pendente vem sempre do motor/candle_provider, nunca da IA)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `pregao.py` já é a fonte única de verdade de horário de pregão — não
  reimplementar calendário/horário em nenhum lugar novo.
- Padrão de "job que roda perto da abertura, fora do gate de
  `in_market_hours`" já existe no Radar diário (`agent.py:920-935`) — usar
  como referência estrutural pro job de execução de ordens pendentes.
- `HistoricoScreen` já renderiza uma tabela de operações — reusar o
  componente, adicionar uma seção "Pendentes".

### Established Patterns
- Débito de caixa é sempre síncrono e direto em `store.py` (`kv_set`
  imediato) — nenhuma fila/async hoje. A ordem pendente introduz o primeiro
  conceito de estado assíncrono no motor de ordens do produto — cuidado
  redobrado para não quebrar o guardrail de cálculo determinístico
  (CLAUDE.md princípio 5).
- `SECTIONS` em `store.py:9` lista as chaves KV por conta — um novo tipo de
  dado (ordens pendentes) provavelmente precisa de uma seção nova nessa
  lista.

### Integration Points
- `scheduler_loop` (`agent.py:874`) é o único loop de background já ativo —
  natural ponto de integração pra "checar e executar ordens pendentes a
  cada tick", em vez de criar um scheduler novo.

</code_context>

<specifics>
## Specific Ideas

Nenhuma referência visual/exemplo externo — o usuário delegou a decisão de
implementação ao critério "mais simples sem prejuízo ao funcionamento
básico, sem precisão total".

</specifics>

<deferred>
## Deferred Ideas

Nenhuma — discussão ficou dentro do escopo da fase (MERC-01..04).

</deferred>

---

*Phase: 2-Realismo de Mercado*
*Context gathered: 2026-08-18*
