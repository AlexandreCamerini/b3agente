# Phase 20: Fundação estrutural e tipográfica - Context

**Gathered:** 2026-09-05
**Status:** Ready for planning
**Mode:** Smart discuss, autonomizada — o Alex autorizou a sessão a resolver as áreas cinzentas sozinha e seguir até o fim das 4 fases do v1.5 sem pausar para aprovação por área (instrução explícita nesta sessão). Cada decisão abaixo tem racional registrado para revisão posterior, não é arbitrária.

<domain>
## Phase Boundary

O esqueleto do app (`.b3-shell`, `GlobalStyle()`, tokens de fonte/número) para
de vazar horizontalmente, respeita um teto de largura em tela grande, exibe
número financeiro numa escala consistente e alinhada, e obedece à preferência
de movimento reduzido do sistema. Esta fase NÃO toca em conteúdo/lógica de
tela específica (isso é Fase 21/22/23) — é a camada global que as outras três
consomem.

</domain>

<decisions>
## Implementation Decisions

### Contenção horizontal (FIX-01, FIX-02)
- `overflow-x: hidden` na regra `.b3-shell` de `GlobalStyle()` (`App.jsx:290`)
  — a causa raiz medida (scrollWidth 504px vs. clientWidth 375px) é contenção
  ausente na raiz, não em um componente filho específico.
- `min-width: 0` explícito nos containers flex pai de `MarketStatusBadge` nos
  dois call sites (Topbar `App.jsx:795`, home `App.jsx:1871`) — o componente
  já declara `textOverflow:ellipsis`, só falta o pai permitir encolher.
- Alternativa descartada: `overflow-x:hidden` só em containers específicos
  (ticker, carrosséis) em vez da raiz — trataria sintoma por sintoma sem
  fechar a causa; o achado da auditoria foi no nível do `.b3-shell`.

### Teto de largura desktop (SYS-04)
- Um wrapper único com `maxWidth:720px; margin:"0 auto"` envolvendo a área de
  conteúdo principal (entre Topbar/Ticker e BottomNav, dentro do shell
  pós-login, próximo de `App.jsx:8958-8995`) — mesmo valor já hardcoded em
  `BottomNav` (`App.jsx:875`), extraído para reuso nos dois lugares.
- Alternativa descartada: aplicar `maxWidth` em cada `*Screen()` individualmente
  — duplicaria a regra em ~15 componentes de tela sem necessidade.

### Escala numérica nomeada (TYPO-01, TYPO-02)
- Três constantes de estilo (objetos JS, no padrão do arquivo — não classe
  CSS): `numHero` (34px/700), `numBody` (18px/700), `numMicro` (13px/600),
  declaradas perto de `MONO`/`DISPLAY` (`App.jsx:236-243`) para reuso via
  spread (`style={{...numHero, ...}}`).
- `font-variant-numeric: tabular-nums` entra direto no stack `MONO` existente
  (`App.jsx:236`) — afeta todo uso de `MONO` de uma vez, sem precisar tocar
  em cada call site individualmente.
- Escopo desta fase: DEFINIR as três constantes e aplicá-las nos números que
  esta própria fase já toca (nenhum número de tela específica migra à força
  aqui — telas específicas de Watchlist/Portfólio/Histórico são Fase 21/22,
  a migração ponto a ponto delas acontece quando essas fases tocarem cada
  tela). Esta fase entrega a fundação, não a migração de todo o app.

### Fredoka nos H1 de tela (TYPO-03)
- Aplicar `fontFamily: DISPLAY` no elemento `<h1>` de nível-tela de cada
  `function XScreen()` (Acompanhar/Evolucao, Radar, Watchlist/Mercado,
  Portfólio/Carteira, Operador IA/Agente, Perfil/Config, e as telas
  secundárias com H1 próprio: Histórico, Ajuda, etc.) — não em H2/H3 nem em
  texto de corpo, só o título que identifica a tela.
- O wordmark "Boris+" (Topbar, WelcomeAuthScreen) já usa Fredoka e não muda.

### Movimento reduzido (MOTION-03)
- Media query CSS pura em `GlobalStyle()`:
  `@media (prefers-reduced-motion: reduce) { .b3 *, .b3 *::before, .b3 *::after { transition-duration: 0.01ms !important; animation-duration: 0.01ms !important; } }`
  — cobre a transição de tema/modo já existente (`.b3{transition:...}`,
  `App.jsx:291`) e qualquer transição/animação que as Fases 22/23 adicionarem
  depois, sem precisar de estado React ou `matchMedia` em JS.
- Alternativa descartada: condicionar via JS (`useMediaQuery` + desligar
  handlers de animação um por um) — mais código, mais superfície de bug, sem
  ganho sobre a media query pura pra este caso (nenhuma animação aqui depende
  de JS para iniciar/parar).

### Claude's Discretion
- Nomenclatura exata das constantes de estilo (`numHero`/`numBody`/`numMicro`)
  segue a nomenclatura já usada na conversa de design (bencium-controlled-ux-designer);
  pode ajustar levemente para bater com a convenção `camelCase` de constantes
  do arquivo se necessário durante o plano.
- Ordem de aplicação dos 5 grupos de mudança dentro da fase fica a critério
  do planner/executor, desde que todas fechem antes do checkpoint de
  publicação.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `T` (tokens via `var(--x)`, `App.jsx:113`), `PALETTE`/`MODE_OPERADOR`
  (`App.jsx:61-172`) — nenhum token novo de cor necessário nesta fase.
- `MONO` (`App.jsx:236`) e `DISPLAY` (`App.jsx:243`) — pontos de extensão
  para tabular-nums e Fredoka, respectivamente.
- `BottomNav` (`App.jsx:861-889`) — já usa `maxWidth:"720px", margin:"0 auto"`
  (`App.jsx:875`), fonte do valor a extrair.
- `MarketStatusBadge` (`App.jsx:774-786`) — já declara `textOverflow:ellipsis`,
  só precisa do pai com `min-width:0`.

### Established Patterns
- Estilo 100% inline (`style={{...}}`), sem Tailwind/shadcn/CSS Modules —
  manter esse padrão; novas constantes viram objetos JS, não classes.
- `GlobalStyle()` (função que retorna `<style>{...}</style>` com CSS puro
  via template string) é o único lugar de regra CSS "de verdade" (não
  inline) — é onde `.b3-shell{overflow-x:hidden}` e a media query de
  `prefers-reduced-motion` entram.

### Integration Points
- `.b3-shell` — raiz do app, `App.jsx:290` (dentro de `GlobalStyle()`).
- Wrapper de conteúdo principal — perto de `App.jsx:8958-8995`, onde o shell
  pós-login monta Topbar/Ticker + tela ativa + BottomNav.
- Cada `function XScreen({ ctx })` — H1 de cada uma recebe `fontFamily: DISPLAY`.

</code_context>

<specifics>
## Specific Ideas

Valores exatos já especificados na proposta de design aprovada nesta sessão
(skill `bencium-controlled-ux-designer`): `numHero` 34px/700, `numBody`
18px/700, `numMicro` 13px/600; Fredoka nos H1; `prefers-reduced-motion`
cobrindo toda transição/animação existente e futura.

</specifics>

<deferred>
## Deferred Ideas

- Migração ponto-a-ponto de cada número de tela específica para
  `numHero`/`numBody`/`numMicro` — fica para as fases que tocam cada tela
  (21/22/23), não para esta fase de fundação.
- Placeholder do gráfico de patrimônio com poucos pontos (FIX-03) — pertence
  à Fase 21 (mesmo componente do DEDUP-01), não a esta fase.

</deferred>
