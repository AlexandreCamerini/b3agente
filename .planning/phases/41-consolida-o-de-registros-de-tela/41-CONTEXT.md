# Phase 41: Consolidação de registros de tela - Context

**Gathered:** 2026-09-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Hoje o front decompõe "as telas do app" em 4 listas/switches paralelos no
`App.jsx`, sem teste amarrando uns aos outros, mais uma cópia no backend:

| Consumidor | Onde | Telas que cobre |
|---|---|---|
| `BottomNav.defs` | `web/src/App.jsx:1035` | 5 abas da barra: evolucao, radar, mercado, carteira, opcoes |
| `tourPassos(cp)` | `web/src/App.jsx:2569` | 6 passos (2 de introdução que NÃO são tela + 4 do funil) |
| `ajudaSecoes(cp, operador)` | `web/src/App.jsx:2492` | seções "Como funciona" por área |
| `petSnapshot` (useMemo/switch) | `web/src/App.jsx:9138` | switch por `petTela`, snapshot calculado em runtime |
| `PET_TELAS` (backend) | `server/app/conceitos.py:565` | 8: mercado, carteira, evolucao, radar, agente, historico, perfil, opcoes |

Esta fase entrega TELAS-01: um único registro de telas no front do qual os
4 consumidores leem a LISTA de telas, com teste de paridade front ↔
`PET_TELAS`. Origem: achado C3 da Fase 26 — "opcoes" entrou na barra mas
ficou fora de `petSnapshot`/`PET_TELAS` (achado A1), e o mesmo defeito pode
se repetir em qualquer tela nova.

</domain>

<decisions>
## Implementation Decisions

### Quais telas entram no registro
- **D-01:** O registro contém as **8** telas que o assistente conhece
  (`evolucao`, `radar`, `mercado`, `carteira`, `opcoes`, `agente`,
  `historico`, `perfil`) — não só as 5 da barra. Cada entrada declara se
  aparece na barra inferior (e em que ordem). O teste de paridade compara o
  conjunto de ids do registro com `PET_TELAS` **8 com 8, sem exceção** —
  é isso que impede repetir o defeito "tela na barra, fora do assistente".

### Onde mora o conteúdo
- **D-02:** O registro guarda só a ESTRUTURA por tela (id, rótulo/ícone da
  barra quando aplicável, flag "na barra" + ordem, posição no tour quando
  aplicável). Os TEXTOS do tour e da ajuda continuam onde estão
  (`tourPassos`, `ajudaSecoes`, `copy.js`), indexados/iterados pelos ids do
  registro. Os 2 passos de introdução do tour (que não são tela) ficam como
  estão, fora do registro. Motivo: mexe menos em strings e preserva a
  separação de vocabulário por modo (Estudo × Operador) que vive em
  `copy.js`.
- **D-03 (consequência de D-02, aplicada ao `petSnapshot`):** o snapshot é
  calculado em runtime com dados/hooks (`portfolioMetrics`, `quotes`,
  `wlScan`…), então NÃO vira dado estático no registro. O switch continua
  existindo; o que muda é que os ids que ele cobre passam a ser os do
  registro (a forma de garantir isso — teste estático que cruza os `case`
  do switch com o registro, ou mapa id→função — fica a critério do
  planner, desde que a divergência reprove em teste).

### Tolerância a mudança visível
- **D-04:** **Refactor puro, zero mudança visível.** Rótulos, textos,
  ordem das abas, passos do tour, seções da ajuda, snapshot do assistente
  e comportamento por modo saem idênticos. Qualquer inconsistência
  encontrada durante o trabalho (ex. mesma tela com rótulos diferentes em
  lugares diferentes) vira ACHADO REGISTRADO para depois, NÃO é corrigida
  nesta fase. Critério prático: `git diff web/src/copy.js` vazio; qualquer
  diff visível ao usuário é bug.

### Verificação e publicação
- **D-05:** Checkpoint humano CURTO e bloqueante antes de publicar (mesmo
  padrão das Fases 39/40): navegar pelas 5 abas nos dois modos, rodar o
  tour inteiro, abrir a Ajuda, e perguntar ao assistente (pet) em 2–3 telas
  (incluindo uma subtela: agente ou histórico). Depois, bump +
  publicar-web.sh + fechamento dos docs à mão.

### Claude's Discretion
- Nome e local do registro (ex. módulo novo em `web/src/` vs. constante no
  `App.jsx`), forma do mapeamento id→snapshot (D-03), e como a barra lê
  rótulo por modo (hoje `cp.tabRadar`/`cp.tituloWatchlist`/… com fallback
  literal) — desde que D-04 (zero mudança visível) se mantenha.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Origem e escopo
- `.planning/milestones/v1.4-phases/26-otimizacao-ux-ia/26-CONTEXT.md`
  linhas ~152-170 — definição original do achado C3 (5 listas paralelas,
  proposta do Alex, por que foi adiado como fase própria de arquitetura).
- `.planning/ROADMAP.md` §"Phase 41" — Success Criteria #1-#4.
- `.planning/REQUIREMENTS.md` — TELAS-01.

### Padrão de paridade a reproduzir
- `./CLAUDE.md` §"Guardrails do repositório" — paridade
  `server/app/defaults.py` ↔ `web/src/catalog.js` (dois pontos testados,
  não um cruzando JS/Python). Testes existentes que leem `catalog.js`
  (candidatos a analog): `server/tests/test_kb_ancoras.py`,
  `server/tests/test_auditoria_prompts.py`, `web/tests/test_copy_theme.mjs`.

### Código
- `web/src/App.jsx:1024-1050` — `BottomNav` e `defs` (rótulos por modo via
  `cp.*` com fallback literal; ícone via `NavIcon`).
- `web/src/App.jsx:2492` — `ajudaSecoes`.
- `web/src/App.jsx:2550-2582` — `tourPassos` e o comentário histórico sobre
  a ordem/rótulos dos passos.
- `web/src/App.jsx:~9125-9200` — `petTela` (derivação de subtelas
  agente/historico a partir de `carteiraView`) e o `switch` do
  `petSnapshot`.
- `server/app/conceitos.py:565` — `PET_TELAS`; `server/app/main.py:4521,
  4617-4622, 4741-4745` — consumidores backend (allowlist e fallback para
  "mercado").

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `NavIcon` (`App.jsx`) já é indexado por id de tela — o registro pode
  apontar para ele sem mudar ícones.
- Padrão de paridade testada `defaults.py`×`catalog.js` — mesmo formato
  para registro-front×`PET_TELAS`.

### Established Patterns
- Rótulos da barra variam por modo via `cp.*` (copy por modo) com fallback
  literal — o registro precisa preservar isso sem mover strings (D-02/D-04).
- `petTela` deriva subtela (agente/historico) de `tab === "carteira"` +
  `carteiraView` — `agente`/`historico`/`perfil` não são abas da barra,
  mas são telas para o assistente (por isso D-01 inclui as 8).

### Integration Points
- Os 4 consumidores estão todos em `App.jsx`; o backend só precisa do teste
  de paridade (nenhuma mudança de comportamento no servidor esperada).

</code_context>

<specifics>
## Specific Ideas

Critério de sucesso #4 do ROADMAP ("adicionar uma tela nova exige editar um
único ponto do front, mais o espelho no backend") deve ser demonstrável —
ex.: o planner descreve, no SUMMARY, o passo-a-passo de adicionar uma tela
hipotética e quantos arquivos ele toca.

</specifics>

<deferred>
## Deferred Ideas

- Qualquer inconsistência de rótulo/texto entre barra, tour, ajuda e
  assistente descoberta durante o refactor — registrar como achado, não
  corrigir (D-04).
- Mover textos do tour/ajuda para dentro do registro (opção rejeitada em
  D-02) — só se no futuro o custo de manter os textos separados aparecer.

### Reviewed Todos (not folded)
- `revisao-arquitetura-mcp-ecossistema-b3.md` — casou por palavra-chave
  genérica, não é sobre registro de telas; não dobrado.

</deferred>

---

*Phase: 41-consolida-o-de-registros-de-tela*
*Context gathered: 2026-09-25*
