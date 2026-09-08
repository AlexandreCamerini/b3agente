# Phase 23: Motion com propósito e ilustração unificada - Context

**Gathered:** 2026-09-06
**Status:** Ready for planning
**Mode:** Smart discuss, autonomizada — mesma autorização das Fases 20/21/22.

<domain>
## Phase Boundary

O movimento no app hoje ou não existe (um card novo de setup aparece sem
nenhum aviso visual) ou é só decorativo. Esta fase adiciona DOIS movimentos
com significado (card novo entra com transição; confirmação de ordem pulsa
antes de virar sucesso) — ambos sob o gate de `prefers-reduced-motion` que a
Fase 20 já colocou em `GlobalStyle()` (MOTION-03, regra ampla
`.b3, .b3 *, .b3 *::before, .b3 *::after {transition-duration:0.01ms!important;
animation-duration:0.01ms!important; animation-iteration-count:1!important;}`).
Não reabrir essa regra — os dois motions novos DEVEM cair dentro dela
automaticamente (usar `transition`/`animation` normais, nunca JS puro tipo
`requestAnimationFrame` com duração hardcoded que ignora a media query).

Em paralelo, corrige a única inconsistência visual do mascote: a arte do
modal "Este é o Boris" (`web/src/pet/BorisIntro.jsx`, hoje `<Boris size={110}/>`)
usa o MESMO PNG semi-realista (`web/src/assets/boris.png`, 490×655,
sombreado/textura de pena) que o `PetFab` usa em 40px — no tamanho do modal
(110px) o detalhe do sombreado fica visível o bastante para ler como
"quase-fotorrealista", destoando do restante da marca (`LogoMark`, ícone do
app já publicado), que é flat/vetorial. `PetFab` continua com o PNG atual —
decisão de escopo já fechada no kickoff do milestone (ver `<decisions>`
abaixo), não é para reabrir.

</domain>

<decisions>
## Implementation Decisions

### MOTION-01 — Card novo entra com transição
- Onde: lista de resultados renderizada em `resultsFiltrados.map(...)` →
  `<AtivoCard key={r.ticker} .../>` (`web/src/App.jsx`, por volta da linha
  6855-6913 antes desta fase — localizar por conteúdo, não por número de
  linha) — usada tanto na Watchlist quanto no Radar/Mesa (`contexto="watchlist"`
  vs `"radar"`).
  "Setup inédito" = um `ticker` que não estava presente na renderização
  anterior da MESMA lista (comparar contra um `Set`/`Map` de tickers já
  vistos, guardado em `useRef`, atualizado a cada render — não persistido,
  reseta ao trocar de tela ou recarregar, o que é o comportamento correto:
  "inédito" é relativo à sessão de visualização atual, não ao histórico
  eterno do ativo).
- Transição: fade (`opacity 0→1`) + `translateY` curto (ex.: `8px→0`),
  `~200ms`, `ease-out` — aplicar via classe CSS com `@keyframes` (cai sob a
  regra ampla de `prefers-reduced-motion` da Fase 20 automaticamente) ou via
  `style` inline com `animation` (mesmo efeito, escolha de organização do
  planner). NÃO usar uma biblioteca nova (`framer-motion` etc.) — o projeto
  não tem essa dependência hoje e não deve ganhar uma só para isto.
- Cards já vistos (não "inéditos" nesta sessão de visualização) NÃO animam
  ao re-renderizar por causa de outra mudança de estado (ex.: preço mudou) —
  a transição é estritamente de ENTRADA de um item novo na lista, não um
  re-mount geral.

### MOTION-02 — Pulso na confirmação de ordem
- Onde: fluxo de confirmação de compra/venda (`store.buy`/`store.sell`,
  chamados a partir do modal/sheet aberto por `A.openBuy`/equivalente de
  venda — `web/src/App.jsx`, por volta da linha 8140-8253 antes desta fase,
  localizar por conteúdo `openBuy`/`store.buy(`/`store.sell(`). O motor
  determinístico (`store.buy`/`store.sell`) NÃO muda — este motion é
  puramente de apresentação, disparado DEPOIS que a resposta do motor já
  chegou (tudo-ou-nada: sucesso ou rejeição, nunca parcial — guardrail do
  CLAUDE.md do repo, `store.buy`/`sell` já garantem isso).
- Pulso: `~120ms`, no valor exibido (preço/total da ordem confirmada) —
  ex.: um `scale(1→1.08→1)` curto ou destaque de cor momentâneo, ANTES de a
  UI trocar para o estado de sucesso definitivo (o card/toast/mensagem que já
  existe hoje). Não inventar um novo componente de sucesso — o pulso é uma
  transição QUE PRECEDE o estado de sucesso já existente, não o substitui.
- Ordem rejeitada (motor recusou) NÃO pulsa — o pulso é reservado para
  confirmação bem-sucedida, nunca para erro/rejeição (não comunicar sucesso
  visual sobre uma operação que falhou).

### Ambos MOTION-01/MOTION-02 sob o gate de `prefers-reduced-motion`
- Critério de aceite explícito (ROADMAP Fase 23, item 3): com "reduzir
  movimento" ligado, NENHUM dos dois anima — o estado final aparece direto,
  sem perda de informação. Isso já é automático se a implementação usar
  `transition`/`animation` CSS padrão (a regra ampla da Fase 20 zera duração
  para qualquer seletor dentro de `.b3`) — não escrever uma exceção nem uma
  segunda regra `prefers-reduced-motion` local; reusar a existente.
- Verificação: mesma limitação de ferramenta já documentada em
  `20-HUMAN-UAT.md` (nenhuma ferramenta expõe `Emulation.setEmulatedMedia`
  para alternar o media feature via CDP neste ambiente) — o novo item de
  motion desta fase entra no MESMO `HUMAN-UAT.md` pendente, não cria um novo
  documento de pendência separado.

### ILUS-01 — Ilustração unificada do Boris no modal de introdução
- Problema exato: `web/src/pet/BorisIntro.jsx` usa `<Boris size={110}/>`
  (`web/src/pet/Boris.jsx`, que renderiza `web/src/assets/boris.png` — PNG
  490×655 com sombreado/textura de pena, estilo 3D semi-realista). No
  tamanho do modal (110px) esse sombreado fica visível o bastante para
  destoar do resto da marca.
- Solução: criar um NOVO componente de ilustração flat/cartoon, reusando o
  MESMO vocabulário visual já estabelecido em `LogoMark` (`web/src/App.jsx`,
  ~linha 201-231 antes desta fase) — corpo/rosto azul-marinho fixo (`#2a3a6b`
  ou o token de marca equivalente), óculos redondos âmbar (`BRAND.amber`),
  bico âmbar, olhos brancos — como um SVG inline novo, maior e mais
  "personagem" que o badge de 64×64 do `LogoMark` (o modal precisa de uma
  ilustração de corpo inteiro ou meio-corpo reconhecível como o Boris, não
  só o rosto em miniatura), mas na MESMA linguagem flat/vetorial, zero
  sombreado fotorrealista, zero gradiente complexo.
  Regra de marca já travada (comentário em `LogoMark`): "nunca recolorir os
  óculos fora do âmbar da marca" — óculos SEMPRE âmbar, independente de tema
  ou modo (Estudo/Operador). Rosto/corpo seguem a cor fixa de marca (não o
  accent do modo).
- `BorisIntro.jsx` troca `<Boris size={110}/>` por este novo componente.
  `PetFab` e qualquer outro uso de `<Boris .../>` (`web/src/pet/Boris.jsx`,
  `boris.png`) NÃO mudam — decisão de escopo já fechada no
  `ROADMAP.md`/kickoff do milestone: "a troca de arte se limita ao modal de
  introdução". Não reabrir essa fronteira.
- Ícone do app (TestFlight/App Store, `resources/ios/`, `server/ios_dist`)
  NÃO muda — fora de escopo, guardrail explícito do kickoff.
- Critério de aceite (ROADMAP item 4): lado a lado com o ícone do app, a
  nova ilustração é reconhecível como o MESMO personagem (mesma cor de
  corpo, mesmos óculos âmbar redondos, mesmo bico) — não precisa ser
  pixel-idêntica ao ícone, precisa ser inequivocamente "o mesmo Boris".

### Claude's Discretion
- Mecanismo exato de rastrear "ticker inédito nesta sessão de visualização"
  (nome da variável/ref, se é um `Set` ou `Map`, onde inicializar).
- Nome/organização do novo componente de ilustração flat (arquivo novo em
  `web/src/pet/` vs. função local em `App.jsx` — mas se for arquivo novo,
  seguir o padrão de import já usado por `BorisIntro`/`Boris`).
- Detalhes exatos da ilustração flat nova além dos elementos já travados
  acima (proporção do corpo, se tem "gravata" como o PNG atual, se tem pés
  visíveis) — desde que fique inequivocamente reconhecível como o mesmo
  personagem do `LogoMark`.
- Easing/keyframe exato do fade+translateY (MOTION-01) e do pulso
  (MOTION-02), desde que respeitem as durações-alvo (~200ms / ~120ms) e
  cascateiem sob a regra de `prefers-reduced-motion` já existente.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `LogoMark` (`web/src/App.jsx`, ~linha 201) — fonte do vocabulário visual
  flat/cartoon (cores, geometria dos óculos/bico) para a nova ilustração de
  ILUS-01.
- Regra `prefers-reduced-motion` já ampla em `GlobalStyle()` (Fase 20) — todo
  motion novo cai sob ela automaticamente, desde que use
  `transition`/`animation` CSS.
- `AtivoCard` (`web/src/App.jsx`, ~linha 3294) — componente já existente que
  recebe a transição de entrada de MOTION-01; não precisa mudar sua lógica
  de dados, só ganhar uma classe/estilo de entrada condicional.

### Established Patterns
- Zero dependência de animação externa (`framer-motion`, etc.) — motion
  sempre via CSS puro (`transition`/`@keyframes`), mesmo padrão já usado em
  `.tt-track`/`.spin`/`.b3-mode-switch`.
- Estilo 100% inline + `GlobalStyle()` para regras que não dá pra fazer só
  com `style={{}}` (keyframes, seletores compostos) — sem CSS Modules/Tailwind.
- `T.*`/`BRAND.*` tokens para toda cor — nunca hex solto fora de `PALETTE`/
  `BRAND` (única exceção já registrada no projeto: `TIER_FILL` da Fase 22,
  aprovada por serem cores semanticamente distintas de status).

### Integration Points
- `web/src/pet/BorisIntro.jsx` — troca de asset (ILUS-01).
- `web/src/pet/Boris.jsx`/`boris.png` — NÃO tocar (fora de escopo).
- `resultsFiltrados.map(...)` → `AtivoCard` (Watchlist e Radar/Mesa,
  `web/src/App.jsx`) — MOTION-01.
- Fluxo `openBuy`/`store.buy`/`store.sell` e a UI de confirmação que já
  existe (`web/src/App.jsx`) — MOTION-02.
- `GlobalStyle()` — nenhuma mudança na regra de `prefers-reduced-motion` em
  si, só os novos `@keyframes`/classes que caem sob ela.

</code_context>

<specifics>
## Specific Ideas

Nenhuma referência visual nova além do que já existe no app (`LogoMark`
como molde de cor/geometria da nova ilustração; o padrão de
`@keyframes`/`prefers-reduced-motion` da Fase 20 como molde de motion).
Fase de acabamento, não de criação de novo padrão visual.

</specifics>

<deferred>
## Deferred Ideas

- Unificar TODOS os usos de `<Boris .../>` (incluindo `PetFab`) para a nova
  arte flat — explicitamente fora de escopo desta fase e do milestone
  (decisão do kickoff, registrada no `ROADMAP.md`).
- Motion em outras transições do app (troca de tela, abertura de
  modal/sheet) — fora do escopo de MOTION-01/02, que são pontuais e
  específicos (card novo, confirmação de ordem).
- Resolver a limitação de ferramenta de `prefers-reduced-motion` real (CDP
  `Emulation.setEmulatedMedia`) — mesma pendência já documentada em
  `20-HUMAN-UAT.md`, não é desta fase resolver a ferramenta em si.

</deferred>
