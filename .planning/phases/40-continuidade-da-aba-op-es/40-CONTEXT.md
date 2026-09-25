# Phase 40: Continuidade da aba Opções - Context

**Gathered:** 2026-09-25
**Status:** Ready for planning

<domain>
## Phase Boundary

O estado da aba Opções (ticker selecionado e aba ativa —
Oportunidades/Destacadas/Montar) hoje se perde sempre que o usuário troca
para outra aba principal e volta, porque `OpcoesScreen` é desmontado
(`{tab === "opcoes" && <OpcoesScreen ctx={ctx} />}`, `App.jsx:9279`) e todo
`useState` interno morre com ele. Esta fase entrega ESTADO-01: esse estado
sobrevive à troca de aba dentro da MESMA sessão do app/página (não é
persistência entre reloads/restarts — ver D-01).

</domain>

<decisions>
## Implementation Decisions

### Mecanismo de sobrevivência
- **D-01:** Levantar o estado (ticker + aba ativa) para `App.jsx` — MESMO
  padrão já existente do `opcoesAbaInicial` (deep-link one-shot da Fase
  39-02, `App.jsx:7675`, lido como estado inicial pelo `OpcoesScreen` no
  mount). Estado fica em memória no componente pai, que nunca desmonta —
  sobrevive à troca de aba dentro da sessão atual. NÃO entra nos stores
  (`deviceStore`/`serverStore`) — decisão explícita de NÃO buscar
  persistência entre reload/restart do app nesta fase, para não acionar o
  guardrail de paridade obrigatória dos dois stores por um ganho que o
  requirement não pediu. Se persistência real vier a ser pedida no futuro,
  é fase própria (mecanismo muda de raiz).

### Escopo do que é lembrado
- **D-02:** Só o mínimo do requirement — ticker selecionado + aba ativa.
  NADA MAIS é lembrado: sheet de Vigias sempre volta fechado, expansões
  internas (ex. "ver mais vencimentos" em Comparar) sempre voltam no
  estado default, filtros de Comparar não são preservados. Motivo
  explícito do Alex: menos estado pra sincronizar, menos risco de "estado
  zumbi" (ex. sheet lembrado aberto sem o dado vivo por trás).

### Interação com o deep-link one-shot
- **D-03:** `opcoesAbaInicial` (deep-link vindo de Posições, força abrir em
  Destacadas) SEMPRE vence o estado lembrado, incondicionalmente — mesmo
  que já exista ticker/aba lembrados de uma visita anterior na mesma
  sessão. Intenção explícita do toque em Posições > estado lembrado
  passivamente. Implica: o gate de prioridade no `useState` inicial do
  `OpcoesScreen` precisa checar `opcoesAbaInicial` ANTES do estado
  lembrado, não depois.

### Expiração da memória
- **D-04:** Nenhuma lógica de expiração adicional. Como o mecanismo (D-01)
  é em memória no `App.jsx`, a sessão inteira já é o limite natural —
  fechar o app ou recarregar a página já zera tudo sozinho. Não escrever
  código de expiração/TTL.
  - **Nota para o planner:** troca de conta/logout NO MEIO da mesma sessão
    do app não foi discutida explicitamente como gatilho — o Alex aceitou
    "vale a sessão inteira" como a resposta recomendada. Se o fluxo de
    logout já limpa/reseta outro estado semelhante do `App.jsx` hoje,
    replicar o mesmo tratamento aqui por consistência; se não limpa nada
    parecido, não inventar tratamento novo só para este campo.

### Comportamento pós-restauração
- **D-05:** Restauração é SILENCIOSA — sem toast, sem microtexto, sem
  salto visual perceptível. O usuário só vê a tela do jeito que deixou,
  como se nunca tivesse saído. Nenhum elemento novo de UI para desenhar
  ou testar.

### Fora de escopo (esclarecido durante a discussão)
- "Rever UX/UI da aba Opções" (pedido inicial ambíguo do Alex) foi
  restringido, depois de pergunta direta, a D-05 acima (comportamento da
  restauração) — NÃO é uma revisão visual geral da aba Opções. Uma
  auditoria completa da aba Opções, se vier a ser pedida, é fase própria
  (mesmo tratamento dado à auditoria "Jornada de Decisão" da Mesa/
  Acompanhar, registrada como v1.9 na fila).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirement e histórico da fase
- `.planning/REQUIREMENTS.md` §"Continuidade UX" — texto original de
  ESTADO-01, inclusive a dependência explícita de NAV-01 (Fase 39, já
  fechada) por mudar a forma da navegação a preservar.
- `.planning/phases/39-reestrutura-o-de-navega-o-da-aba-op-es/39-CONTEXT.md`
  linhas 176-178 — decisão prévia registrada: "qualquer novo campo de
  estado de navegação [persistido] precisa entrar nos DOIS stores" — o
  motivo direto por trás de D-01 escolher NÃO persistir.
- `.planning/STATE.md` — nota da Fase 39 sobre o deep-link
  `opcoesAbaInicial` ("a Fase 40/ESTADO-01 precisa conviver com ele").

### Padrão de código a reaproveitar
- `web/src/App.jsx:7675` (`const [opcoesAbaInicial, setOpcoesAbaInicial] = useState(null)`)
  e `App.jsx:8973-8978` — o padrão exato de estado levantado ao pai que
  D-01 estende.
- `web/src/opcoes/OpcoesScreen.jsx:314-323` — onde o `OpcoesScreen` lê
  `ctx.opcoesAbaInicial` como estado inicial e limpa via
  `ctx.limparOpcoesAbaInicial()` (one-shot) — o ponto de integração para
  D-03 (ordem de prioridade deep-link > estado lembrado).
- `web/src/App.jsx:9279` (`{tab === "opcoes" && <OpcoesScreen ctx={ctx} />}`)
  — o unmount/remount que causa a perda de estado hoje.

No external specs beyond the above — requirements fully captured in
decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `opcoesAbaInicial`/`setOpcoesAbaInicial`/`limparOpcoesAbaInicial`
  (`App.jsx`): infraestrutura de estado-levantado-ao-pai já existe e já é
  passada via `ctx` para `OpcoesScreen` — o padrão para o novo campo de
  ticker/aba lembrados é literalmente copiar essa forma, não inventar
  mecanismo novo.

### Established Patterns
- Paridade obrigatória entre `deviceStore`/`serverStore`
  (`web/src/persistence.js`) — qualquer campo que ENTRE nos stores exige
  espelhamento nos dois. D-01 evita esse guardrail deliberadamente ao
  ficar só em memória no `App.jsx`.
- `ABAS_OPCOES` (constantes das 3 abas fixas, `OpcoesScreen.jsx`) — fonte
  única de validação de valor de aba, usada tanto pelo `opcoesAbaInicial`
  quanto pelo novo estado lembrado (D-01/D-03).

### Integration Points
- `ctx` (objeto de contexto passado de `App.jsx` para `OpcoesScreen`) é o
  canal existente — o novo estado lembrado entra em `ctx` do mesmo jeito
  que `opcoesAbaInicial` já entra.

</code_context>

<specifics>
## Specific Ideas

Nenhuma referência específica externa — as decisões acima (D-01 a D-05)
cobrem a implementação completamente.

</specifics>

<deferred>
## Deferred Ideas

- **Auditoria/revisão de UX-UI geral da aba Opções** — pedido inicial
  ambíguo do Alex, esclarecido como fora de escopo desta fase (ver seção
  "Fora de escopo" em `<decisions>`). Se vier a ser priorizado, tratar como
  fase própria, no mesmo padrão da auditoria "Jornada de Decisão"
  (`qa/AUDITORIA-Jornada-Decisao-v1.md`, registrada como v1.9 na fila em
  `PROJECT.md`).
- **Persistência real (deviceStore/serverStore)** do estado da aba
  Opções — descartada nesta fase (D-01), mas fica registrada como upgrade
  possível futuro se o Alex quiser que o estado sobreviva a reload/restart
  do app, não só à troca de aba na mesma sessão.

### Reviewed Todos (not folded)
- `opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp.md`,
  `revisao-arquitetura-mcp-ecossistema-b3.md`,
  `medir-rate-limit-mydata.md` — combinaram por palavra-chave genérica
  ("opções"/"fase"/"trocar") na busca de todos pendentes, mas nenhum é
  sobre continuidade de estado de navegação; revisados e não dobrados
  nesta fase.

</deferred>

---

*Phase: 40-continuidade-da-aba-op-es*
*Context gathered: 2026-09-25*
