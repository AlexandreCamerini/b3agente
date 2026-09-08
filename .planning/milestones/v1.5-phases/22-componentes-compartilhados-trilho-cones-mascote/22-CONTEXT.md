# Phase 22: Componentes compartilhados (trilho, ícones, mascote) - Context

**Gathered:** 2026-09-06
**Status:** Ready for planning
**Mode:** Smart discuss, autonomizada — mesma autorização das Fases 20/21.

<domain>
## Phase Boundary

Os padrões que hoje divergem de tela para tela passam a ser um só: um único
comportamento de rolagem horizontal (scroll-snap + espiada do próximo item),
ícones SVG no traço do app no lugar de emoji do sistema, e o mascote
flutuante (`PetFab`) com separação visual suficiente para nunca parecer
cortado pela borda de um card atrás dele.

</domain>

<decisions>
## Implementation Decisions

### SYS-01 — Carrossel horizontal único
- Padrão de referência: o carrossel de setups da home (`App.jsx`, HERO-CARROSSEL,
  ~linha 1886 antes das Fases 20/21 — localizar por conteúdo
  `scrollSnapType`, não por número de linha) — `scrollSnapType:"x mandatory"`
  + cada item com `flex:"0 0 84%"` (ou `maxWidth` equivalente) pra deixar o
  próximo espiando.
- Aplicar o MESMO padrão ao(s) trilho(s) hoje sem snap/peek: o grupo
  `TECH_MODELS` ("MODELO DE ANÁLISE") na Watchlist, e qualquer outro trilho
  horizontal que a auditoria/leitura de código encontrar com
  `overflowX:"auto"` solto (sem `scrollSnapType`). Fazer um levantamento
  completo (`grep -n "overflowX" web/src/App.jsx`) antes de decidir quantos
  trilhos existem — não assumir que são só os dois já nomeados na auditoria
  original.
- Extrair a repetição num pequeno helper/constante compartilhada (ex.: um
  objeto de estilo `carouselTrackStyle` ou função `carouselItemStyle(pct)`)
  em vez de copiar os mesmos valores em cada call site — reduz a chance de
  o próximo trilho divergir de novo no futuro.
- Não mexer no marquee do ticker (`.tt-track`) — é uma animação contínua
  (`animation:b3tt 52s linear infinite`), não um carrossel de swipe do
  usuário; está fora do escopo de SYS-01 (esse é outro mecanismo,
  intencionalmente diferente).

### SYS-02 — Ícones SVG no lugar de emoji
- Localizar as 5 ocorrências já nomeadas na auditoria (🎓/📈/🚀/✨/📈 — seletor
  de Modo no Perfil, card do Operador IA, chips de ação da Watchlist) MAIS
  qualquer outra que uma varredura (`grep -n "🎓\|📈\|🚀\|✨\|⚡\|🔔\|⭐" web/src/App.jsx`
  ou busca mais ampla por emoji Unicode) encontrar — não travar no número 5
  se a varredura achar mais.
- Ícone novo: SVG inline no MESMO traço/peso visual do `NavIcon` já existente
  (componente usado no `BottomNav`) — reusar o padrão de `<svg viewBox=...
  stroke=... strokeWidth=...>` do `NavIcon`, nunca importar uma lib de ícone
  nova (`lucide-react`, `react-icons`, etc.) — o projeto não tem
  dependência de ícone hoje e não deve ganhar uma só para isso.
- Cada emoji removido ganha um `aria-label`/`aria-hidden` equivalente ao que
  o emoji comunicava — não perder informação de acessibilidade na troca.

### SYS-03 — Sombra/halo no PetFab
- Adicionar `boxShadow` (ou `filter:drop-shadow`) ao botão fixo `PetFab`
  (`position:"fixed", right:"14px", bottom:"92px"`) — valor exato fica com o
  planner calibrar visualmente (ex.: `0 4px 16px rgba(0,0,0,0.35)` no
  tema escuro), mas TEM que variar por tema (dark/light) via os tokens `T.*`
  já existentes (ex.: uma nova entrada em `PALETTE` tipo `shadowFab`, ou
  compor com `T.scrim`) — nunca um hex fixo que só funciona num tema.
- Verificar visualmente nos dois temas que o halo separa o mascote do card
  atrás dele sem criar um "disco" chapado ao redor da coruja (a arte já tem
  transparência/contorno próprio — a sombra deve ser sutil, não um badge).

### Claude's Discretion
- Nome exato do helper de carrossel compartilhado.
- Se o SVG novo de cada ícone é um componente `<IconGraduationCap/>` etc.
  separado, ou uma função `renderIcon(name)` — decisão de organização de
  código, não de produto.
- Valor exato do `boxShadow`/`drop-shadow` do PetFab — calibrar visualmente.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `NavIcon` (componente usado em `BottomNav`) — fonte do traço/peso pros
  ícones novos de SYS-02.
- O carrossel de setups da home (HERO-CARROSSEL) — fonte do padrão
  scroll-snap+peek pra SYS-01.
- `PALETTE`/`T` (tokens por tema) — onde a sombra do PetFab de SYS-03 deve
  se apoiar, nunca hex solto.

### Established Patterns
- Zero dependência de ícone/UI externa hoje — não introduzir uma só para
  este fix pontual.
- Estilo 100% inline, sem CSS Modules/Tailwind.

### Integration Points
- `PetFab` (componente já existente, botão flutuante).
- Grupo `TECH_MODELS` na Watchlist (trilho sem snap hoje).
- Qualquer outro trilho horizontal a ser confirmado por grep antes do plano.
- `AgenteScreen`/Perfil (emoji 🎓/📈/🚀) e chips de ação da Watchlist
  (✨/📈) — sites exatos a confirmar por grep no momento do plano (podem ter
  se deslocado após as Fases 20/21).

</code_context>

<specifics>
## Specific Ideas

Nenhuma referência visual nova além do que já existe no app (carrossel da
home como molde, `NavIcon` como traço de ícone). Fase de unificação, não de
criação de novo padrão visual.

</specifics>

<deferred>
## Deferred Ideas

- Extrair um design-system/token file separado para o carrossel — fora de
  escopo (o milestone não migra de stack nem introduz build step novo).
- Animação de entrada dos itens do carrossel — isso é MOTION-01, Fase 23,
  não aqui.

</deferred>
