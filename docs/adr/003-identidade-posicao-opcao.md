# ADR-003: Identidade da posição de opção

**Status:** Aceito
**Data:** 2026-08-04
**Decisor:** Alex
**Base:** [`docs/v2-opcoes-proposta.md`](../v2-opcoes-proposta.md) §3, painel de
4 especialistas (`CHECKOUT-V2-Opcoes-otimizado.md`) + mapeamento de código.

---

## Contexto

`positions` (`server/app/store.py`) é uma lista de dicts num blob JSON no
kv-store (`server/app/db.py`), sem schema e sem tabela relacional. `p["t"]`
cumpre três papéis ao mesmo tempo:

1. **Chave primária** — identifica a posição dentro da lista.
2. **Chave de cotação** — `priceOf(t)` chama `yahoo.get_quote(t)` direto.
3. **Rótulo de UI** — exibido como está.

Um contrato de opção não tem um "t" único e estável nesse sentido: o mesmo
ativo-objeto (PETR4) tem dezenas de contratos simultâneos (strikes ×
vencimentos × tipo), cada um com cotação própria, vencimento próprio e P&L
independente. Reusar `positions` faria os três papéis colidirem — e pior,
faria todo consumidor hoje (compra, venda, KPI de carteira, snapshot diário,
render de UI) tratar um contrato de opção como se fosse uma ação, em
silêncio, porque nenhum desses consumidores valida o shape que recebe.

**Achado do mapeamento de código, não estava previsto na entrada do
checkout:** 19 arquivos tocam a forma de `positions` hoje (13 de produção + 6
de teste), com **3 implementações independentes de cálculo de P&L**
(`store.sell`, o card de UI em `App.jsx`, e o espelho em
`web/src/persistence.js`). `persistence.js` mantém um `deviceStore`
(persistência nativa iOS) que é uma **réplica manual completa** da lógica de
`store.py`, não um adaptador fino sobre uma API — motivo pelo qual o F3
(alvo dinâmico) já exigiu tocar dois arquivos e por que a checklist
`campo-novo-em-agent-checklist` existe.

**Também não existe hoje nenhum ponto único de migração de schema de
posição.** `store.ensure_defaults` faz backfill de `config`/`agent`/
`llmPrompts` campo a campo, mas nunca de `positions` — campos novos
sobrevivem só por leitura defensiva (`pos.get("alvoExtensoes") or 0`). Não
há precedente de "adicionar uma coleção nova" neste código; a v2 cria esse
precedente.

---

## Decisão

**`optionPositions` é uma coleção separada, com identidade própria — não
campos opcionais em `positions`.**

Confirmada de forma independente pelas lentes de dados (`system-design`) e
de arquitetura (`architecture`) do painel: a alternativa de sobrecarregar
`positions` com campos `optionType`/`strike`/`expiration` nullable faria
todo código que itera `positions` (KPI, snapshot, render, P&L) precisar de
um `if` para não quebrar — e o primeiro esquecimento seria silencioso, não
um erro visível.

**Shape:**

```json
{
  "id": "PETRH340",          // contractSymbol do provider — chave primária, único por série
  "underlying": "PETR4",     // ativo-objeto — onde a camada aparece no card
  "optionType": "call",      // "call" | "put"
  "strike": 34.0,
  "expiration": "2026-08-15",
  "qty": 100,                 // ações-equivalente, mesma unidade de positions.qty
  "avg": 1.25,                 // PRÊMIO pago por ação — mesmo nome/semântica de positions.avg
  "stop": null, "alvo": null,  // em PRÊMIO (mesma unidade de avg), não no preço do ativo-objeto
  "abertaEm": "...", "setupEntrada": {...},  // idênticos ao padrão de positions
  "ivEntrada": null, "deltaEntrada": null, "hv21Entrada": null  // snapshot didático da entrada
}
```

`id` (não `t`) é a chave primária e a chave de cotação — resolve via a
cadeia `(underlying, expiration)`, nunca sozinho. `underlying` é o único
campo que aponta de volta para `positions`/`AtivoCard`; nada aqui reusa `t`
como identidade tripla.

**O que isso propaga**, listado para não ser descoberto em produção:

- **Catálogo/Radar** — não muda: a camada de opções entra por `children` do
  `AtivoCard` (`App.jsx:2128`), não por campo novo em `vm`.
- **STU** — não avalia contrato de opção; a análise técnica continua sendo a
  do ativo-objeto (Princípio 5/9: opção nunca contradiz a leitura do ativo).
- **P&L** — `optionPositions` tem sua própria função de venda (não reusa
  `store.sell`), porque a unidade (prêmio × 100) e o motivo de fechamento
  (venda antecipada vs. expiração) divergem do fluxo de ação.
- **`persistence.js` / `deviceStore`** — precisa da mesma coleção espelhada,
  no mesmo padrão de hoje (regra "método novo entra nos dois stores").

**Consciente e aceito:** `optionPositions` nasce **sem migração** também —
mesma dívida que `positions` já tem. Não é um problema resolvido por esta
ADR; é uma dívida que a v2 escolhe não pagar agora, registrada para não ser
"descoberta" depois como se fosse surpresa.

---

## Consequências

**Fica mais fácil**
- Nenhum consumidor de `positions` precisa mudar para não quebrar com opção.
- P&L de opção fica isolado — bug em um não vaza pro outro.
- `underlying` dá o caminho de volta pro card sem acoplar `t`.

**Fica mais difícil**
- Dois caminhos de compra/venda para manter em paridade (ação e opção), nos
  dois stores (server e iOS `deviceStore`) — 4 lugares no total.
- KPI de carteira (patrimônio total) precisa somar as duas coleções
  explicitamente; esquecer `optionPositions` na soma é o próximo bug óbvio
  desta linha — vira item de teste dedicado, não nota de rodapé.

**A revisitar**
- Se `positions` ganhar um mecanismo de migração de schema, `optionPositions`
  deveria herdar o mesmo mecanismo — não construir um segundo.
- Se a v3 trouxer multi-perna (travas/estruturas), a chave `id` única por
  contrato deixa de bastar para agrupar pernas da mesma estratégia — precisa
  de um campo de agrupamento (`estrategiaId`), fora do escopo desta ADR.

## Action items

1. [ ] `optionPositions` em `SECTIONS`/`USER_SECTIONS` (`store.py`), com
   `buy_option`/`sell_option`/`close_option_expirada`.
2. [ ] KPI de patrimônio soma `positions` + `optionPositions` — teste
   dedicado que falha se uma das duas for esquecida.
3. [ ] `persistence.js`: mesma coleção no `deviceStore`, mesmo padrão de
   compra/venda espelhado.
4. [ ] `public_state`/`export_sections` incluem `optionPositions`.
