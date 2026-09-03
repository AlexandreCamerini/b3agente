# Phase 18: Seção de Opções em Posições - Context

**Gathered:** 2026-09-03
**Status:** Ready for planning
**Source:** Síntese manual, autonomia concedida pelo Alex — mesmo padrão da
Fase 17 (sem `discuss-phase` interativo). O desenho já foi validado nesta
sessão via mockup (2 iterações) + revisão com o agente
`design-with-claude:navigation-specialist`; não há decisão de produto em
aberto, só tradução pra plano executável.

<domain>
## Phase Boundary

Cobre NAV-01..03: uma tira "Oportunidades de opções" no topo de
Posições/Portfólio agregando as propostas ativas de todas as posições, e o
detalhe completo (payoff, aceite) dentro de cada posição específica. Nada de
aba nova na navegação inferior — decisão revertida nesta sessão depois de
descobrir (leitura de código + screenshot ao vivo) que a barra real já tem 5
abas, não 4 como presumido no kickoff de 01/09.

</domain>

<decisions>
## Implementation Decisions

### Estado real do código a estender

`web/src/App.jsx:3905` — `CarteiraScreen({ ctx })`: tela real de
Posições/Portfólio. Renderiza KPIs (patrimônio/resultado/caixa/em posições),
aviso de concentração, estado vazio, e o loop `data.positions.map((p) => ...)`
(linha 3983) que desenha um card por posição (ticker/qty/PM, PnL, badges).
**`PropostaLastreada` NÃO é renderizada aqui hoje** — o único ponto de
renderização confirmado é dentro de `AtivoCard`
(`web/src/App.jsx:3492`, contexto Watchlist/Radar), condicionado a
`opGate && opGate.liquida`.

`web/src/App.jsx:3203-3234` — padrão da busca da proposta, hoje só dentro de
`AtivoCard`:
```
store.optionsGate(t)                    // gate leve, best-effort
  → se opGate.liquida: store.optionsProposta(t, true)   // proposta completa
```
Ambas as chamadas já existem em `web/src/api.js:278` e
`web/src/persistence.js:1130` (paridade `deviceStore`/`serverStore` já
garantida, Fase 14) — **esta fase NÃO cria rota nova nem método novo de
store**, só reusa as duas chamadas já existentes, disparadas por ticker.

### NAV-01 — tira "Oportunidades de opções"

Decisão de arquitetura (sem endpoint bulk): o front itera
`data.positions` (a mesma lista que `CarteiraScreen` já usa) e dispara
`optionsGate`/`optionsProposta` por ticker, o MESMO padrão de custo já
aceito no ADR-004 ("1 chamada leve por card, best-effort") — carteiras deste
produto são de poucas posições (simulador educacional), então N chamadas
paralelas por ticker não é um problema de orçamento novo. **Não criar rota
`/api/options/propostas` (bulk) nesta fase** — se o número de posições típico
crescer a ponto de justificar, é decisão de escopo futuro, não desta fase.

A tira renderiza um item por posição com proposta ativa (`opGate.liquida &&
opProposta.proposta` truthy) — ticker + resumo curto (ex.: tipo de estrutura,
mesma manchete que `PropostaLastreada` já usa, nunca uma manchete nova
gerada por outro lugar — guardrail CVM, a manchete vem só de
`skill_ref.opcoes_lastreadas_txt()`). Clique no item rola/expande até o card
da posição correspondente na lista abaixo (mesmo padrão de "abrir detalhe"
já usado em outros pontos do app — ex. `histFor`/`editFor` em
`CarteiraScreen`, `useState` + scroll ou expand local).

### NAV-02 — detalhe dentro da posição

`PropostaLastreada` passa a ser renderizada TAMBÉM dentro do card de posição
em `CarteiraScreen` (loop de `data.positions.map`, ~linha 3991-4060) — não
substitui a renderização existente em `AtivoCard` (Watchlist/Radar continua
mostrando a proposta lá, ela é uma superfície de descoberta diferente,
comportamento intocado). A busca de gate/proposta por ticker dentro do card
de posição usa o MESMO hook/padrão de `useEffect` de `AtivoCard`
(`web/src/App.jsx:3203-3234`) — extrair pra um hook compartilhado se o
planner considerar mais limpo, ou duplicar o padrão local ao componente; a
regra que não pode quebrar é "nunca uma estrutura sobre ticker sem posição
real" — como `CarteiraScreen` só itera `data.positions` (posições reais por
definição), essa regra já é estrutural aqui, não precisa de guarda extra.

### NAV-03 — estado vazio explícito

Diferente do padrão de `AtivoCard` (que fica em silêncio quando
`opGate.liquida` é falso — ver comentário `web/src/App.jsx:3484-3489`,
decisão deliberada do ADR-004 pra não virar "seis avisos idênticos por
tela"), a tira de Posições É a superfície de descoberta agregada — aqui o
requirement NAV-03 pede o oposto do silêncio: quando NENHUMA posição tem
proposta ativa, mostrar uma mensagem curta e explícita (nunca sumir sem
explicação). Motivo a comunicar: sem cobertura elegível (posições existem
mas nenhuma passa no gate de liquidez) vs. cobertura elegível mas sem setup
técnico ativo hoje — reusar o texto que a `didatica`/`skill_ref` já produz
pro card individual, se existir um equivalente; senão, texto novo em
`web/src/copy.js`, nunca hardcoded no componente (convenção do projeto).
Se não houver NENHUMA posição na carteira (`data.positions.length === 0`),
a tira não aparece — esse caso já tem o próprio estado vazio de portfólio
(`web/src/App.jsx:3974-3980`), não duplicar mensagem.

### Claude's Discretion

- Nome exato do componente novo (`OportunidadesOpcoes` ou equivalente) e se
  fica em arquivo próprio ou inline em `App.jsx` (App.jsx já é um arquivo
  único de ~7600+ linhas — seguir o padrão existente, não iniciar split de
  arquivo nesta fase).
- Mecanismo exato de "clique no item rola até o card" (scroll com `ref` +
  `scrollIntoView`, ou expandir um estado local `focusedTicker`) — decisão de
  UI, seguir o estilo visual já usado nos mockups aprovados.
- Extrair hook compartilhado de gate+proposta (`useOpcoesProposta(t)`) vs.
  duplicar o efeito local — decisão de implementação, sem impacto de produto.
- Texto exato da tira/estados — copy nova em `web/src/copy.js`, revisar com
  `didatica-boris` skill se tocar vocabulário por modo (Estudo × Operador).
- Cobertura de teste do front — `web/tests/*.mjs`
  (`scripts/executar.sh --testes` roda as DUAS suítes); qualquer mudança em
  `web/src/App.jsx` PRECISA rodar `npx vite build` antes de declarar pronto
  (guardrail do CLAUDE.md do projeto — grep/teste estático não pega erro de
  sintaxe JS).

</decisions>

<specifics>
## Specific Ideas

Mockup de referência (2 iterações, aprovado pelo Alex nesta sessão, visual
apenas — não é fonte de verdade de dado, é direção de UI):
`https://claude.ai/code/artifact/16ae7543-c58e-4b7f-b164-f8923efa431b`.
Arquivo local (não versionado no repo, ephemeral):
`/private/tmp/claude-501/-Users-acamerini-dev-bolsia-b3-agente/aebe3980-e8b2-4252-8847-61f1d0bc34c8/scratchpad/opcoes-dentro-de-posicoes.html`.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Frontend a estender
- `web/src/App.jsx:3905-4060` — `CarteiraScreen`, tela de Posições real
  (KPIs, loop de cards de posição).
- `web/src/App.jsx:3006-3062` — `PropostaLastreada` (componente já existe,
  Fase 14/16/17), reusar sem alterar a assinatura.
- `web/src/App.jsx:3138-3234` — padrão `opGate`/`opProposta` dentro de
  `AtivoCard` (gate leve → proposta completa, best-effort, `useEffect`).
- `web/src/copy.js` — vocabulário de UI por modo, qualquer texto novo (não
  manchete) segue esse padrão.

### Backend (sem mudança nova esperada)
- `server/app/main.py:2348-2422` — `GET /api/options/proposta/{ticker}`
  (parâmetro `multiperna`), já retorna `source`/`at` (Fase 17).
- `web/src/api.js:278` — `optionsGate`; `web/src/persistence.js:1130` —
  `store.optionsGate`/`optionsProposta`, já existem nos DOIS stores.

### Decisão de escopo e requirements
- `.planning/REQUIREMENTS.md` — NAV-01..03 (reescritos em 2026-09-03).
- `.planning/ROADMAP.md` — seção Phase 18 (reescopada em 2026-09-03).
- `.planning/STATE.md` — Roadmap Evolution, decisão da revisão de navegação.
- `.planning/notes/opcoes-v2-b-mcp-exploracao.md` — histórico completo da
  decisão original (Candidato A) e da reversão, preservado.
- Ler o código-fonte comentado em `web/src/App.jsx:3484-3489` antes de
  decidir o texto do estado vazio da tira, pra não contradizer a razão de
  design já registrada lá sobre o silêncio deliberado do card individual.

</canonical_refs>

<deferred>
## Deferred Ideas

- Endpoint bulk de propostas (`/api/options/propostas`) — só se o volume de
  chamadas paralelas por ticker virar problema real de orçamento/latência;
  não há evidência disso hoje.
- Motor multi-candidato (N estruturas por posição, não 1) — Fase 19,
  registrada nesta sessão, depende desta fase estar fechada primeiro.

</deferred>

---

*Phase: 18-aba-opcoes*
*Context gathered: 2026-09-03 via síntese manual (mockup + navigation-specialist já validados nesta sessão, sem discuss-phase)*
