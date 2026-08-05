# ADR-005: Fechamento por expiração — o terceiro motivo de saída

**Status:** Aceito
**Data:** 2026-08-04
**Decisor:** Alex
**Base:** [`docs/v2-opcoes-proposta.md`](../v2-opcoes-proposta.md) §3, mapeamento
de código (5 caminhos de fechamento de posição).

---

## Contexto

Hoje `history.type` só conhece `"COMPRA"`/`"VENDA"` (`store.py:372,402`), e
`sell()` sempre exige `priceOf(t)` — uma cotação. Opção introduz um terceiro
motivo de saída que não existe em ação: **expiração**. No vencimento, o
contrato é liquidado pelo intrínseco (`max(0, S−K)` para call,
`max(0, K−S)` para put), que **pode ser zero** — perda total do prêmio, sem
que nenhum "stop" tenha sido rompido no sentido em que o produto usa a
palavra hoje.

Não existe hoje um campo estruturado de **motivo de fechamento**. O texto
`"stop atingido"`/`"alvo atingido"` em `agent.py` (`_run_cycle_inner`,
linha ~315) é uma string local, interpolada direto no texto do evento e
descartada — o registro de VENDA no `history` não guarda motivo nenhum, só
`type: "VENDA"`. A mesma lógica está **duplicada** em
`web/src/persistence.js:729-741` (ciclo foreground iOS), com o mesmo
descarte.

**Achado do mapeamento de código, relevante para esta decisão:** fechar uma
posição hoje não tem um caminho único — são **5**: venda manual (UI), laço
do agente server-side (`agent.py`), ciclo foreground web (`POST
/api/cycle`, reusa o mesmo `agent.py`), ciclo foreground **iOS** (segunda
implementação independente em `persistence.js`, que **já diverge** do
server-side hoje — ignora `maxOpsDia`/`maxValorOp` e não tem nenhuma das
proteções de F2/F3), e `reset_portfolio`. Qualquer novo ramo de fechamento
(vencimento) que entre só do lado server-side **piora** essa divergência: o
usuário que só abre o app pelo iOS nunca teria a posição de opção liquidada
automaticamente no vencimento.

---

## Decisão

**1) Motivo de fechamento vira campo estruturado desde o início, para
opção.** `history` ganha `motivo: "stop" | "alvo" | "vencimento" | "manual"`
nas entradas de fechamento de `optionPositions`. Custa pouco a mais que a
string descartável atual e evita repetir a mesma dívida que `positions` já
tem — não se estende retroativamente a `positions` (fora do escopo desta
ADR; ver "A revisitar").

**2) Fechamento por vencimento roda nos dois caminhos que hoje avaliam
posições — server (`agent.py`) e foreground iOS (`persistence.js`) — não só
no server.** A divergência entre os dois caminhos já é um bug pré-existente
(fora do escopo desta v2, sinalizado como chip separado), mas **adicionar
opção sem replicar o ramo de vencimento nos dois pioraria ativamente** essa
divergência: um usuário majoritariamente-iOS teria contratos expirando sem
liquidação automática, acumulando posições "mortas" na carteira. Este ADR
não resolve a duplicação de lógica entre os dois arquivos — só recusa
piorá-la introduzindo um ramo nôvo que existe só de um lado.

**Regra do ramo de vencimento**, igual nos dois lugares: antes do loop de
stop/alvo, fora do gate de "sem cotação"; se `hoje >= expiration`, liquida
pelo intrínseco e grava `motivo: "vencimento"`. Aviso ao usuário em D-3
(três dias antes do vencimento) via evento/push, mesmo padrão de
`push_events` já usado para stop/alvo.

### Opções consideradas

| | Replicar nos 2 caminhos (escolhida) | Só no server, documentar a lacuna do iOS | Resolver a duplicação primeiro (unificar os 2 caminhos), depois adicionar vencimento |
|---|---|---|---|
| Risco para usuário majoritariamente-iOS | Nenhum novo | Posições de opção "mortas" na carteira sem liquidar | Nenhum, mas depende de trabalho fora do escopo da v2 |
| Escopo desta v2 | +1 função replicada (pequeno) | Menor, mas cria dívida nova sobre dívida existente | Maior — puxa uma refatoração não pedida pelo checkout |
| Trade-off | Custo pequeno agora, sem piorar o bug conhecido | Mais barato agora, mais caro para o usuário depois | Correto a longo prazo, mas atrasa a v2 por um problema pré-existente |

A terceira opção foi descartada porque o checkout desta rodada é
explicitamente sobre opções, não sobre unificar os caminhos de fechamento —
puxar essa refatoração aqui violaria a disciplina de escopo ("decida o
rotineiro sozinho, sinalize discordância em uma frase"). Fica registrada
como dependência a considerar em paralelo, fora da v2.

---

## Consequências

**Fica mais fácil**
- Relatórios futuros de "por que a posição fechou" (stop vs. alvo vs.
  vencimento) — o dado já nasce estruturado.
- O usuário iOS não é surpreendido por contrato expirado sem liquidação.

**Fica mais difícil**
- Duas implementações do ramo de vencimento para manter em paralelo — mesmo
  custo que qualquer mudança em `agent.py` já paga hoje ao tocar
  `persistence.js` (regra "método novo entra nos dois stores").
- `analysis_outcomes.py` não mede opção (decisão já registrada na proposta,
  §3) — o campo `motivo` não alimenta essa métrica na v2.

**A revisitar**
- Se a divergência dos 5 caminhos de fechamento virar trabalho próprio
  (chip já sinalizado, `task_cf7c8fed`), este ADR é a referência de que
  "vencimento" precisa ser um dos motivos contemplados na unificação.
- Estender `motivo` estruturado para `positions` (ação) fica de fora — put
  desta ADR não decide isso, mas nota que a mesma dívida existe lá.

## Action items

1. [ ] `history` de `optionPositions`: campo `motivo` estruturado
   (`stop`/`alvo`/`vencimento`/`manual`).
2. [ ] Ramo de liquidação por vencimento em `agent.py` (`_run_cycle_inner`),
   antes do loop de stop/alvo.
3. [ ] Mesmo ramo replicado em `persistence.js` (ciclo foreground iOS) —
   sem isso, este ADR não está implementado, só metade dele.
4. [ ] Aviso D-3 antes do vencimento (evento + push), mesmo padrão dos
   avisos de stop/alvo.
5. [ ] Teste de guardião: nenhuma posição de opção passa de `expiration` sem
   gerar entrada de `history` com `motivo: "vencimento"`.
