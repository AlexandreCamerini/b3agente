# Requirements

## v1.5 Redesenho de UI — simplificação e acessibilidade

Escopo derivado de uma auditoria de design ao vivo (mobile 375px, dark/light,
Modo Estudo/Operador, conta nova + conta com ordem pendente) e das decisões
de direção visual aprovadas na mesma sessão (skill `bencium-controlled-ux-designer`).
Ver o resumo completo da auditoria e das decisões em `.planning/PROJECT.md`
seção "Current Milestone: v1.5" (Key Decisions travadas, Fora de escopo).

Bug crítico encontrado durante a auditoria (`cp is not defined` em
`HistoricoScreen`) já foi corrigido fora deste milestone, via quick task
`260905-1gb` — não entra em nenhum requirement abaixo.

### Remoção de duplicação (DEDUP)

- [x] **DEDUP-01**: O card "Patrimônio simulado" (`CapitalCurve`) aparece em
  exatamente UMA tela — hoje está duplicado, idêntico, em Acompanhar E
  Portfólio (`web/src/App.jsx:1976` e `:8974`).
- [x] **DEDUP-02**: Na tela Operador IA, o status do modo/operador/execução
  aparece uma única vez — hoje um card de texto ("Modo do app: Estudo /
  Operador no servidor: Desligado / Executar/sinalizar: Apenas sinalizar")
  repete o que o card funcional de toggle logo abaixo já mostra.
- [x] **DEDUP-03**: Os cards "Patrimônio total", "Resultado aberto", "Caixa
  disponível" e "Em posições" do Portfólio viram um único card com colunas
  — mesmo padrão de densidade que "Resumo do dia" já usa em Acompanhar.

### Sistema de componente (SYS)

- [x] **SYS-01**: Existe um único padrão de carrossel horizontal
  (scroll-snap + espiada do próximo item) usado em todo lugar da interface
  que hoje rola horizontalmente — hoje há dois padrões divergentes (o
  carrossel de setups da home, com peek; o filtro "Modelo de análise" da
  Watchlist, sem peek e sem indicação de conteúdo cortado).
- [x] **SYS-02**: Nenhum emoji nativo do sistema operacional aparece na
  interface do app — os 5 usos hoje (🎓/📈/🚀/✨/📈, no seletor de Modo do
  Perfil, no card do Operador IA e nos chips de ação da Watchlist) viram
  ícones SVG no traço do `NavIcon` existente.
- [x] **SYS-03**: O mascote flutuante (`PetFab`) tem separação visual
  (sombra/halo) suficiente para nunca parecer cortado pela borda de um card
  atrás dele — reproduzido em pelo menos 5 telas na auditoria.
- [x] **SYS-04**: Em telas ≥768px de largura, o conteúdo principal respeita
  o mesmo teto de largura (720px) que o `BottomNav` já usa
  (`web/src/App.jsx:875`) — hoje só a barra de navegação tem esse limite;
  o resto do app estica edge-to-edge.

### Responsividade e estados (FIX)

- [x] **FIX-01**: A raiz do app (`.b3-shell`, `web/src/App.jsx:290`) nunca
  permite rolagem horizontal além do viewport — confirmado por medição DOM
  (`scrollWidth` 504px vs. `clientWidth` 375px) que um clique comum
  (foco/scrollIntoView) desloca a tela inteira (header, conteúdo e nav
  inferior) para o lado.
- [x] **FIX-02**: A mensagem de status de mercado (`MarketStatusBadge`,
  `web/src/App.jsx:774`) trunca com reticência visível quando não cabe, em
  vez de vazar texto para fora do viewport — o componente já declara
  `textOverflow:ellipsis`, mas um container pai sem `min-width:0` impede o
  efeito.
- [x] **FIX-03**: O gráfico de patrimônio (`CapitalCurve`) tem um
  placeholder dedicado para o caso de 1-2 pontos de dado registrados, em vez
  de renderizar uma caixa vazia com escala degenerada (achado ao vivo logo
  após a primeira operação de uma conta nova).

### Tipografia (TYPO)

- [x] **TYPO-01**: Todo número financeiro (preço, R$, quantidade) usa
  `font-variant-numeric: tabular-nums` no stack `MONO` existente
  (`web/src/App.jsx:236`) — hoje ausente, causa desalinhamento de dígitos em
  listas (Histórico, cards de Watchlist).
- [x] **TYPO-02**: Existe uma escala numérica nomeada de 3 níveis
  (`numHero` 34px/700, `numBody` 18px/700, `numMicro` 13px/600) aplicada
  consistentemente onde hoje há tamanhos de fonte soltos para valor
  financeiro.
- [x] **TYPO-03**: O título H1 de cada tela usa a fonte `DISPLAY` (Fredoka) —
  hoje restrita ao wordmark "Boris+" (`web/src/App.jsx:243`).

### Motion com propósito (MOTION)

- [x] **MOTION-01**: Um card novo (setup inédito na Watchlist/Radar) entra
  com uma transição sutil (fade + translateY, ~200ms) em vez de aparecer
  sem nenhum aviso visual.
- [x] **MOTION-02**: A confirmação de uma ordem (compra/venda) dá um
  feedback visual de pulso curto (~120ms) no valor antes de virar sucesso.
- [x] **MOTION-03**: O app respeita `prefers-reduced-motion` — hoje ausente
  em `GlobalStyle()` (`web/src/App.jsx`); todas as transições/animações se
  reduzem ou desligam quando o usuário pede no sistema operacional.

### Ilustração unificada (ILUS)

- [x] **ILUS-01**: Existe um único estilo de ilustração do Boris
  (flat/cartoon, o do `LogoMark`/`PetFab`/ícone do app já publicado) em
  todos os pontos onde o mascote aparece — a arte do modal "Este é o Boris"
  (introdução), hoje quase-fotorrealista, é refeita nesse estilo. Não mexe
  no ícone do app já publicado no TestFlight/App Store.

## Future Requirements (deferred)

- Consolidação de arquitetura de informação (fusão de abas Acompanhar↔Portfólio)
  — Nível 1 "toque leve" escolhido para este milestone; a alternativa mais
  radical (4 abas em vez de 5) fica registrada para reavaliação futura, caso
  a duplicação resolvida aqui não seja suficiente.
- Migração de estilo (Tailwind/shadcn) — fora de cogitação enquanto não
  houver ganho concreto declarado que justifique reescrever ~9k linhas.

## Out of Scope

- **Qualquer mudança na navegação de 5 abas** — decisão travada no kickoff
  (Nível 1 = "toque leve"); reabrir isso é um milestone à parte.
- **Qualquer alteração no motor determinístico ou em rotas de backend** —
  este milestone é inteiramente front-end visual/interação; nenhum cálculo
  de carteira, preço, ordem ou timing muda.
- **Mudança de paleta ou tokens do Brand Book v2** — cores/tema/modo já
  aprovados (v2, 2026-08-08); este milestone consome os tokens existentes,
  não os redesenha.
- **Fluxo de aceite de opções (Fases 17/18/19 do v1.4)** — esses checkpoints
  humanos seguem pendentes e são tratados dentro do próprio v1.4, não aqui.

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FIX-01 | Phase 20 | Complete |
| FIX-02 | Phase 20 | Complete |
| SYS-04 | Phase 20 | Complete |
| TYPO-01 | Phase 20 | Complete |
| TYPO-02 | Phase 20 | Complete |
| TYPO-03 | Phase 20 | Complete |
| MOTION-03 | Phase 20 | Complete |
| DEDUP-01 | Phase 21 | Complete |
| DEDUP-02 | Phase 21 | Complete |
| DEDUP-03 | Phase 21 | Complete |
| FIX-03 | Phase 21 | Complete |
| SYS-01 | Phase 22 | Complete |
| SYS-02 | Phase 22 | Complete |
| SYS-03 | Phase 22 | Complete |
| MOTION-01 | Phase 23 | Complete |
| MOTION-02 | Phase 23 | Complete |
| ILUS-01 | Phase 23 | Complete |

Cobertura: 17/17 requirements do v1.5 mapeados, cada um a exatamente uma
fase — nenhum órfão, nenhuma duplicata. Os requirements do v1.4
(NAV/LIB/ENG/FLOW/MULTI) têm tabela própria mais abaixo e não foram tocados.

---

## v1.4 Opções v2 (em execução — não shipped, requirements preservados abaixo)

Base completa da decisão: `.planning/seeds/opcoes-v2-setups-propostos-via-b-mcp.md`
e `.planning/notes/opcoes-v2-b-mcp-exploracao.md`.

### Navegação (NAV)

Revisado em 2026-09-03 após mockup + `navigation-specialist`: a barra
inferior real tem 5 abas (não 4, como presumido em 01/09); Candidato A
("aba própria") descartado. Ver `.planning/notes/opcoes-v2-b-mcp-exploracao.md`
seção "Navegação" pro histórico da decisão original, preservado.

- [ ] **NAV-01**: Usuário vê, no topo de Posições/Portfólio, uma tira
  horizontal "Oportunidades de opções" agregando todas as propostas ativas
  no momento — sem aba nova na navegação inferior.
- [ ] **NAV-02**: Cada item da tira abre o detalhe completo dentro da
  posição correspondente em Posições — nunca uma estrutura sobre ticker sem
  posição real na carteira do usuário.
- [ ] **NAV-03**: Quando não há nenhuma proposta ativa (sem cobertura
  elegível, ou cobertura elegível mas sem setup técnico ativo hoje), a tira
  comunica esse estado vazio claramente, com o motivo — nunca desaparece
  silenciosamente.

### Biblioteca de estruturas (LIB)

- [x] **LIB-01**: Usuário pode receber proposta de venda coberta (covered
  call) sobre uma posição comprada existente.
- [x] **LIB-02**: Usuário pode receber proposta de put de proteção
  (protective put) sobre uma posição comprada existente.
- [x] **LIB-03**: Usuário pode receber proposta de collar (trava protetora)
  combinando as duas pernas acima sobre uma posição comprada existente.

### Motor / arquitetura (ENG)

- [x] **ENG-01**: O motor de proposta seleciona o contrato pelo critério já
  em produção — `liquidity_score ≥ 40` + strike extremo, mesma régua de
  `server/app/opcoes_lastreadas.py` — nunca pelo critério por delta do
  `estruturas.py` do b-mcp.
- [x] **ENG-02**: O cálculo de payoff de N pernas (custo líquido, ganho/perda
  máximos, breakevens, delta somado) usa aritmética portada de `calculos.py`
  do b-mcp, adaptada e testada dentro do repo do Boris.
- [x] **ENG-03**: O motor não faz nenhuma chamada de rede ao processo/serviço
  b-mcp em runtime — toda fonte de dado passa por `mydata_client.py`
  existente.
- [x] **ENG-04**: A lógica de screening de cadeia e avaliação de estrutura
  fica atrás de duas funções de limite interno — `rastrear()` e `avaliar()`
  — desenhadas no vocabulário do contrato ADR-004/`mydata_client.py`
  (prêmio/strike/delta/tipo), permitindo trocar a implementação local pelas
  chamadas ao b-mcp (`find_tradable_options`/`evaluate_option_structure`) no
  futuro sem redesenho — troca de corpo de função.
- [x] **ENG-05**: Qualquer chamada nova ao hub mydata feita pelo motor de
  opções (screening, avaliação) passa pelo lock existente
  (`mydata_budget.reservar()`) — nunca um canal paralelo.
- [x] **ENG-06**: O gatilho técnico que dispara a avaliação de proposta
  reusa o motor de setups já existente do Boris (Radar/`setups.py`
  server-side, `indicators.py`) — não porta nem depende da DSL de setups
  técnicos do b-mcp.

### Fluxo de aceite (FLOW)

- [ ] **FLOW-01**: Usuário vê os dados da proposta (estrutura, pernas,
  prêmio, breakeven, ganho/perda máximos) antes de decidir.
- [ ] **FLOW-02**: Usuário aceita ou recusa a proposta explicitamente —
  nenhuma execução automática.
- [ ] **FLOW-03**: Ao aceitar, a execução usa o mesmo motor de ordens de
  opções lastreadas já em produção (Fase 14, `store.py`) — sem automação
  nova.
- [ ] **FLOW-04**: Toda proposta declara a fonte e o horário do dado usado
  (frescor) — princípio 3 do CLAUDE.md, nunca dado silenciosamente
  desatualizado.

### Motor multi-candidato (MULTI)

Registrado em 2026-09-03 como Fase 19 (nova fase, decisão explícita do
Alex — "no detalhamento da proposta deveriamos poder mostrar uma série de
setups de opções para a análise do ativo"). Estende ENG-01..06 (Fase 15,
já verificado, não reaberto) — motor hoje devolve UMA estrutura por
posição via regra fixa de `plano.decisao`; estes requirements pedem N.
Success criteria detalhados ficam para `/gsd-plan-phase 19`.

- [x] **MULTI-01**: O motor de proposta (`opcoes_lastreadas.propor()` e a
  camada `opcoes_motor.rastrear()`/`avaliar()`) pode devolver mais de um
  candidato de estrutura (venda coberta, put de proteção, collar) para a
  mesma posição, quando mais de um fizer sentido pela análise técnica
  atual — não mais uma escolha única e fixa.
- [ ] **MULTI-02**: O detalhe da posição em Posições mostra os N candidatos
  lado a lado (mesmo padrão visual da tira "Oportunidades" da Fase 18);
  usuário aceita exatamente um por avaliação — nunca mais de um executado
  simultaneamente para a mesma posição.

### v1.4 Future Requirements (deferred)

- Setup customizado pelo usuário (fora do v1 — biblioteca fixa por
  enquanto).
- Integração MCP real com o b-mcp (Estratégia C) — condicionada à aprovação
  de `~/dev/MCP/docs/plano-mcp-servico.md` pelo Alex. Quando aprovado, troca
  o corpo de `rastrear()`/`avaliar()` (ENG-04), sem reabrir requirements.
- Estruturas adicionais além das 3 do v1 (ex.: mais combinações de pernas),
  se a demanda de produto justificar.

### v1.4 Out of Scope

- **Straddle/strangle coberto** — liquidez de opções B3 fora dos blue-chips
  já é curta pra 1 perna, pior pra 2 pernas simultâneas de lados opostos.
- **Cash-secured put** — inicia posição em vez de proteger uma existente,
  contradiz a régua "só sobre cobertura real" que é o próprio enunciado da
  feature (questão de definição, não de liquidez).
- **DSL de setups técnicos do b-mcp (`setups.py`)** — o Boris já mediu
  (ADR-016) que sinal ingênuo de confluência perde dinheiro e reconstruiu
  seleção por peso histórico (ADR-017); portar a DSL sem passar pelo
  `scripts/backtest_sinal.py` reintroduziria um defeito já corrigido. O
  gatilho técnico já vem do Radar (ver ENG-06).
- **Plano comercial (gratuito vs. pago) desta feature** — mesmo padrão do
  v1.3, que ativou infraestrutura sem loja/IAP ainda; decisão comercial
  separada, fora deste milestone.

### v1.4 Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| NAV-01 | Phase 18 | Pending |
| NAV-02 | Phase 18 | Pending |
| NAV-03 | Phase 18 | Pending |
| LIB-01 | Phase 16 | Complete |
| LIB-02 | Phase 16 | Complete |
| LIB-03 | Phase 16 | Complete |
| ENG-01 | Phase 15 | Complete |
| ENG-02 | Phase 15 | Complete |
| ENG-03 | Phase 15 | Complete |
| ENG-04 | Phase 15 | Complete |
| ENG-05 | Phase 15 | Complete |
| ENG-06 | Phase 15 | Complete |
| FLOW-01 | Phase 17 | Pending |
| FLOW-02 | Phase 17 | Pending |
| FLOW-03 | Phase 17 | Pending |
| FLOW-04 | Phase 17 | Pending |
| MULTI-01 | Phase 19 | Complete |
| MULTI-02 | Phase 19 | Pending |

Coverage: 18/18 v1.4 requirements mapped. No orphans. Pendências de
verificação ao vivo (não de mapeamento) documentadas em
`.planning/notes/checkpoints-pendentes-fase-17-18-19.md`.
