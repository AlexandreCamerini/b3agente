# Boris+ (b3-agente)

## What This Is

Simulador educacional de ações da B3 com dados reais de mercado e dinheiro
exclusivamente virtual. Ensina a mecânica da bolsa brasileira — setups,
indicadores, gestão de risco — através de um Modo Estudo (a IA orienta, nunca
executa) que evolui para um Modo Operador (ferramentas automáticas e análises
mais profundas, com execução simulada, agora **gated pela seleção dinâmica**:
entrada automática só dispara em setup com vantagem estatística medida na
janela anterior fechada, não mais em qualquer padrão detectado). Web/PWA +
app iOS nativo (mesmo bundle via Capacitor), backend Python/FastAPI, portal
de administração separado. **Comercializado desde v1.3**: plano gratuito com
teto real (10 ativos na watchlist, 30 análises de IA/mês, motivo exato na
recusa), plano pago (`PLAN_PRO`) ilimitado — ainda sem loja/IAP nem preço
definido, essa ativação foi só a preparação técnica pro upgrade pago.

## Core Value

O usuário leigo sai do Modo Estudo entendendo de verdade como o mercado
funciona — não decorou uma resposta, aprendeu o raciocínio — e só então tem
acesso a automações do Modo Operador. Se o storyline pedagógico não convencer,
nada mais no produto importa.

## Milestone v1.7 Confiabilidade explicativa da aba Opções — SHIPPED 2026-09-22

**Goal:** corrigir a jornada de montar/analisar uma estrutura de opções
dentro do workspace (v1.6) e tornar o gráfico de payoff — e sua explicação —
matematicamente correto e genérico para qualquer estrutura, sem promover
recomendação.

**Origem:** pedido direto do Alex ao usar a navegação nova do v1.6 em
produção (2026-09-20). Dois problemas concretos, não hipotéticos: (1) a
jornada de montar/ver uma estrutura dentro do workspace (Analisar/Comparar/
Setups salvos) continua sem passos visíveis; (2) o gráfico de payoff mistura
valor de hoje com resultado no vencimento, eixo Y sem escala, platô cortado,
e a razão G/P no texto usa um número diferente do exibido — confirmado por
screenshot de produção. Mapeia para PERS-01 (v1.6), que a milestone anterior
já havia identificado e deferido deliberadamente até a reorganização
estrutural estar pronta.

**Entregue:** 3 fases (35-37), 10 plans, 14/14 requirements Done. Jornada
guiada do workspace com passos nomeados e CTAs com hierarquia visual real
(Fase 35). Motor de payoff genérico estendido — não recriado — com correção
de um bug real de breakeven espúrio, domínio X/Y e segmentação calculados no
backend (Fase 36). Gráfico SVG corrigido (eixo Y com escala real, strikes/
spot marcados, setas de risco ilimitado rotuladas, "hoje" separado de "no
vencimento") e explicação por segmento 100% determinística, fechando a
divergência real de razão G/P confirmada em produção (Fase 37). Publicado em
dois carimbos: `F10-20260921-01` (Fase 35) e `F10-20260922-01` (Fase 37).
Pendência não-bloqueante: verificação visual em produção com dado real do
gráfico corrigido (o checkpoint da Fase 37 fechou com evidência automática,
sem essa confirmação visual — credenciais ausentes no backend local usado na
tentativa).

**Fora de escopo desta milestone (decidido, não esquecido):** PERS-02
(modelo de progresso do aprendiz) e PERS-03 (desafio personalizado por
padrão observado) — mesma decisão do v1.6 de não personalizar antes da
explicação básica estar correta; migração do motor de opções para um MCP
único (`revisao-arquitetura-mcp-ecossistema-b3.md`, revisão de arquitetura
maior e separada).

## Milestone v1.6 Simplificação da aba Opções — SHIPPED 2026-09-20

**Entregue:** reorganização da sub-aba "Setups" por job-to-be-done em duas
fases de risco crescente — Fase 33 extraiu os 5 jobs (descobrir cross-
carteira, vigias, analisar ticker, comparar vencimentos, setups salvos) em
componentes próprios sem mudar comportamento; Fase 34 substituiu a rolagem
única por navegação hub (sem ticker) + workspace (ticker selecionado, 3
pills compartilhando uma única leitura paga). 13/13 requirements v1
(REORG-01..07, NAV-01..06) Done, publicado em produção (`F10-20260920-01`),
checkpoint humano aprovado ao vivo com medição real de rede confirmando
NAV-05. Detalhe completo: `.planning/milestones/v1.6-ROADMAP.md` e
`v1.6-REQUIREMENTS.md`.

**Achado que virou a próxima milestone:** a reorganização não tocou
qualidade de explicação por desenho (PERS-01 deferido desde o kickoff). Ao
usar a navegação nova em produção, o Alex confirmou que isso ainda dói —
jornada do workspace confusa e gráfico de payoff pouco confiável — origem
do v1.7.

## Milestone v1.4 Opções v2 — SHIPPED 2026-09-19

**Goal:** nova experiência de Opções no Boris+ — do motor de proposta
interno (venda coberta, put de proteção, collar) sobre posições reais da
carteira, com aceite manual, até a integração real com o serviço MCP
externo (`mcp.semente.dev`), planos comerciais e a consolidação de toda
operação de opções numa única aba com dois motores lado a lado.

**Entregue (14 fases — 15-19, 24-32 — 63 planos, ~211 tasks, 2026-09-02 a
2026-09-16, arquivado em 2026-09-19):**
- Fases 15-19: motor interno de N-pernas (`rastrear()`/`avaliar()`),
  biblioteca de estruturas (venda coberta, put de proteção, collar), fluxo
  de aceite reusando o motor de ordens da Fase 14, tira "Oportunidades de
  opções" em Posições, motor multi-candidato.
- Fase 24: aba Opções passa a ler o serviço MCP externo de verdade (cadeia,
  possibilidades, custo em reais) + criação de setups por linguagem
  natural com ensaio.
- Fase 25: planos comerciais como eixo de produto — papel `owner`, RBAC×
  plano como eixos independentes, limites de IA configuráveis por plano.
- Fase 26: **parcial** — só a "Fase A" (sete correções baratas de UX/IA)
  shippou; B2/B3/C1/C2/C3 nunca executados.
- Fases 27-29: universo da aba Opções vira a carteira; sub-aba "Operar"
  extrai `PropostaLastreada` para módulo compartilhado; opção a descoberto
  exige flag opt-in default OFF.
- Fases 30-32: curadoria de IA (top-4 determinístico), varredura de
  oportunidades (4 estruturas × 2 vencimentos), consolidação final — os
  dois motores (interno grátis + MCP com custo declarado) lado a lado sob
  frase-ponte permanente, Posições reduzida a uma linha de chamada.

**Fora de escopo (mantido, não reaberto):** setup customizado pelo usuário;
straddle/strangle coberto e cash-secured put (liquidez/definição); DSL de
setups técnicos do `b-mcp` local (nunca portada — a criação de setups da
Fase 24 usa o PRÓPRIO serviço MCP externo compilando linguagem natural, um
mecanismo estruturalmente diferente).

**Ressalvas carregadas explicitamente (não escondidas):** o roteiro de
verificação humana das Fases 17/18/19 (`checkpoints-pendentes-fase-17-18-
19.md`, registrado 2026-09-04) nunca fechou 100% ao vivo — a única
tentativa caiu com o mercado fechado; o item específico de multi-candidato
lado a lado (Fase 19) seguia sem confirmação em navegador real mesmo na
verificação da ÚLTIMA fase da milestone (`32-VERIFICATION.md`, 2026-09-16).
O plano de publicação dedicado da Fase 24 (`24-05`) nunca rodou como plano
próprio — a função foi cumprida por publicações conjuntas posteriores. A
Fase 26 é a única com escopo genuinamente parcial (backlog B2/B3/C1/C2/C3
carregado adiante). Nenhuma fase foi reprovada ou revertida.

Ver `.planning/milestones/v1.4-ROADMAP.md`, `.planning/milestones/
v1.4-REQUIREMENTS.md` e `.planning/MILESTONES.md`.

## Milestone v1.5 Redesenho de UI — simplificação e acessibilidade — SHIPPED 2026-09-06

**Goal:** eliminar a duplicação e as inconsistências visuais achadas numa
auditoria de design ao vivo (mobile 375px, dark/light, Estudo/Operador,
conta nova + conta com ordem pendente) e aplicar uma direção visual mais
coerente — sem tocar no motor determinístico, sem reabrir a navegação de 5
abas, sem sair do Brand Book v2 já aprovado.

**Contexto de abertura:** este milestone abriu com o v1.4 (Opções v2) ainda
EM EXECUÇÃO — Fases 17/18/19 com checkpoint humano bloqueante pendente. Por
decisão explícita do Alex, o v1.5 foi planejado e executado sem esperar
esse checkpoint fechar (diretórios de fase 15-19 intocados, nenhum push a
`origin` em nenhum dos dois fluxos) e evoluiu de ponta a ponta sem pausa
para aprovação humana intermediária — segunda vez que esse modo de operação
é usado no projeto (a primeira foi o v1.2, execução autônoma noturna).

**Entregue (4 fases, 16 planos, 123 commits, 2 dias — 2026-09-05 a
2026-09-06):**
- Fase 20 — fundação: fim do vazamento horizontal do shell, teto de 720px
  em desktop, escala tipográfica numérica nomeada (`numHero`/`numBody`/
  `numMicro`) com `tabular-nums`, H1 em Fredoka, gate de
  `prefers-reduced-motion` em `GlobalStyle()`
- Fase 21 — deduplicação: `CapitalCurve` (patrimônio simulado) unificado em
  uma única tela, card 2×2 do Portfólio consolidado, status do Operador IA
  sem repetição, placeholder dedicado para "1-2 pontos de dado"
- Fase 22 — componentes compartilhados: um único padrão de trilho
  horizontal (scroll-snap+peek) nos 4 usos do app, zero emoji nativo
  (`NavIcon` SVG), sombra/halo do `PetFab` por tema
- Fase 23 — motion com propósito: entrada de card novo (fade+translateY
  ~200ms) e pulso de confirmação de ordem (~120ms), ambos sob o gate de
  reduced-motion; nova ilustração flat unificada do Boris (`BorisFlat.jsx`)
  substituindo o PNG semi-realista do modal de introdução — ícone do app já
  publicado permanece intocado

**Resultado da auditoria (`.planning/milestones/v1.5-MILESTONE-AUDIT.md`):** 17/17
requirements satisfeitos, 16/17 pontos de integração cruzada `WIRED`
(2 fluxos E2E traçados ponta a ponta), status `tech_debt` (não bloqueante).
Débito técnico: `numHero` (34px) declarado mas sem consumidor real —
decisão deliberada documentada em 3 fases sucessivas, não um silêncio
acidental; candidato a backlog de polish visual futuro. 4 itens de
verificação humana consolidados num único documento
(`.planning/milestones/v1.5-phases/20-funda-o-estrutural-e-tipogr-fica/20-HUMAN-UAT.md`,
nunca fragmentados por fase): comportamento real de `prefers-reduced-motion`
(limitação de ferramenta — sem CDP `Emulation.setEmulatedMedia` neste
ambiente), pulso de sucesso com mercado aberto, 2 dos 4 trilhos SYS-01 sem
proposta de opção ativa durante a verificação.

**Decisões de arquitetura travadas (mantidas, não reabertas):**
1. Navegação de 5 abas permanece — Nível 1 "toque leve" escolhido sobre
   fusão/reordenação de abas
2. Sem migração de stack: estilo inline + tokens `var(--x)`, nada de
   Tailwind/shadcn
3. Ilustração do Boris = flat/cartoon (não o quase-fotorrealista do modal
   de intro antigo) — ícone do app publicado no TestFlight/App Store
   permanece intocado

**Fora de escopo (confirmado no fechamento):** fusão/reordenação de abas,
migração de biblioteca de UI, mudança de paleta/tokens do Brand Book v2,
qualquer alteração no motor determinístico ou nas rotas de backend — nada
disso foi tocado, confirmado pela auditoria.

Ver `.planning/milestones/v1.5-ROADMAP.md`,
`.planning/milestones/v1.5-REQUIREMENTS.md` e
`.planning/milestones/v1.5-MILESTONE-AUDIT.md`.

## Milestone v1.3 Cap comercial (plano gratuito) — SHIPPED 2026-08-31

**Goal:** ativar de verdade os limites do plano gratuito que o ADR-010 já
desenhou tecnicamente (watchlist e análises/mês) — sem loja/IAP neste
milestone. `PLAN_PRO` continua ilimitado por enquanto; isso é preparação
pro upgrade pago, não a venda em si.

**Target features:**
- `PLAN_FREE.max_watchlist = 10` (hoje `None` = ilimitado)
- `PLAN_FREE.max_analyses_per_month = 30` (hoje `None` = ilimitado)
- `can_add_ticker`/`can_analyze` (`server/app/plan.py`) passam a bloquear de
  verdade quando o limite bate, com o motivo exato já pronto nos hooks
- `used_this_month` do gate mensal vem do ledger real de `metering.py`
  (contrato C-33 já exige isso — nunca um contador paralelo)
- UI mostra o número real de uso/limite (ex.: "análises deste mês: 30/30"),
  nunca estimado nem escondido (princípio 3/8 do CLAUDE.md)

**Decisões de arquitetura travadas (não reabrir):**
1. Cap comercial (por conta) e cota física da brapi (por app inteiro) são
   camadas independentes — um usuário pago consome da mesma cota física,
   só sem limite comercial próprio (ADR-010, decisão 2)
2. Fonte de cotação (brapi/Yahoo) não é diferencial de plano — infra igual
   pra todo mundo (ADR-010, decisão 3)

**Fora de escopo (decidido no kickoff):** loja/IAP e validação de recibo
server-side; IA gerenciada sem BYOK como feature paga; alvo dinâmico (F3)
virar exclusivo do pago; preço/moeda. Tudo isso fica pra um milestone
futuro, quando a decisão de venda em si vier.

Ver `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md` e
`docs/adr/010-planos-e-cap-gratuito.md` (decisão técnica já fechada, só
faltavam os números).

## Requirements

### Validated

- ✓ Motor de simulação determinístico (ordens, preço médio, PnL, drawdown)
  server-side em `server/app/store.py`, mirror client-side em
  `web/src/finance.js`/`persistence.js` para uso offline — existing
- ✓ Camada de dados de mercado com fonte declarada e fallback (brapi master,
  Yahoo backup/intraday, ADR-001/ADR-008) — existing
- ✓ Separação Modo Estudo/Modo Operador via flag `appMode`, com vocabulário
  próprio por modo (`skill_ref.py` ↔ `copy.js`) — existing, fonte única
  reforçada em v1.1 (`ctx.operador`, FIX-C21)
- ✓ IA multi-provider (Anthropic/OpenAI/Google, BYOK + gerenciada com cota),
  camada didática que explica indicador→correlação→decisão — existing
- ✓ Autenticação multi-método unificada numa única conta (Sign in with Apple,
  Google, e-mail/senha) — existing
- ✓ RBAC/entitlements (ADR-013) e portal de administração/observabilidade
  separado (`web-admin/`, ADR-014, handoff mobile) — existing
- ✓ Estrutura técnica de planos (`plan.py`, `metering.py`) pronta para ligar
  cap comercial — v1.1 fechou o último buraco estrutural (FIX-C33, contagem
  real do mês); só falta a decisão de negócio (ADR-010) pra ativar de vez
- ✓ Cap comercial ativado de ponta a ponta (v1.3, Fases 12-13): `PLAN_FREE`
  com `max_watchlist=10`/`max_analyses_per_month=30` reais (eram `None`),
  gates `can_add_ticker`/`can_analyze` bloqueando de verdade com motivo
  exato (CAP-01..05, CAP-07), uso/limite real visível na UI nos dois stores
  — web e iOS (CAP-06), e o bypass do cap no app iOS nativo fechado
  (CAP-12/CR-01) — achado próprio: o code review pós-fase pegou o gate
  fail-closed comparando a contagem do SERVIDOR em vez da do APARELHO
  (iOS é local-first, nunca sincroniza watchlist pro servidor), corrigido e
  mutation-tested (`101335e`). CAP-12 já vale para builds NOVOS; instalações
  existentes via TestFlight só recebem o fix num build novo distribuído
  pelo Alex (pendência nomeada, não escondida, `13-05-SUMMARY.md`)
- ✓ REVIEW-01..06 / `REPORT-01.md` (39 achados, 2 Crítico + 8 Alto + 20 Médio
  + 9 Baixo) — v1.0
- ✓ MERC-01..04: status real de mercado na tela de entrada + fila de
  execução de ordens fora do horário de pregão — v1.1 Fase 2
- ✓ FIX-C11, FIX-C30 (2 Crítico) + FIX-C12, C19, C20, C31, C32, C35, C36, C37
  (8 Alto) — v1.1 Fase 3
- ✓ FIX-C01..C05, C13..C16 (9 Médio — STORY/UX: fallback determinístico do
  Passo 7, rastro de rejeição, benchmark Ibovespa, prontidão pedagógica,
  diversificação, disclaimer no modal, tudo-ou-nada declarado, acordeão por
  teclado, contraste WCAG AA) — v1.1 Fase 4
- ✓ FIX-C21..C27, C33, C34, C38, C39 (11 Médio — CODE/GATE/ADMIN: fonte
  única de `appMode`, paridade byte-exata de skill text — achou e corrigiu
  divergência REAL de persona entre iPhone e web —, Toggle disabled real,
  suíte autossuficiente, testes de rejeição/reponderação, avaliação de E2E
  via ADR-018, contagem mensal real do gate, alerta preventivo de gasto de
  IA, regra de acesso explícita da aba Auditoria) — v1.1 Fase 5
- ✓ ADR-015 (instrumentação de assertividade): âncora no gatilho real (não
  mais no close), dedup por `snapshotId`, `motivo` em `store.sell()`, R:R
  mínimo consolidado numa fonte única — v1.1 Fase 6 (nasceu de pesquisa
  ad-hoc, não do REPORT-01)
- ✓ ADR-016 (diagnóstico, sem código): motor de setups tinha expectância
  negativa (−0,105R/operação, 15 anos, 125.938 sinais) — achado que motivou
  as Fases 6-8
- ✓ ADR-017 Bloco 0+1 (seleção dinâmica): 6 setups catastróficos aposentados
  (estático, piso de segurança), ledger de sinais resolvidos + bootstrap +
  hook diário + `regime.ranquear()` pesando por elegibilidade medida na
  janela anterior — v1.1 Fase 7
- ✓ ADR-017 Bloco 3+4 (interface): vocabulário canônico do histórico medido,
  Radar/Watchlist/card de setup mostrando elegibilidade, `entradaAuto`
  religado mas GATED pela elegibilidade (nunca mais suspensão cega nem
  "qualquer padrão detectado") — v1.1 Fase 8
- ✓ ADR-020 (centralização de dados no mydata): `mydata_client.py` +
  `mydata_budget.py` (cota 60/min·2.000/dia), fatia diária de candle
  atrás de cadeia mydata→brapi→Yahoo, opções/IV atrás de
  `options_provider_mydata.py` (D-04, sem fallback pro Yahoo), ingestão
  paralela de COTAHIST (`b3_historical.py`) aposentada (commit `b3fdf02`
  recuperável). Rate-limit MEDIDO (não estimado): pico projetado NÃO CABE
  (148/60 por minuto), volume diário CABE com folga — virada de
  `B3_CANDLE_PROVIDER`/`B3_OPTIONS_PROVIDER` para mydata em produção
  **adiada** por decisão do Alex no checkpoint da fase, código pronto
  atrás das env vars — Fase 9 (standalone, fora de v1.0/v1.1)
- ✓ LEDGER-01/OPTGATE-01 (precondições do v1.2): 9 tickers 404 do bootstrap
  do ledger resolvidos com evidência (2 `ALIASES` por renomeação real, 5
  `EXCLUIR` por fusão/deslistagem, 2 `INDETERMINADO` documentados sem
  esconder); gate de orçamento (`_gate`/`_debita`) adicionado ao caminho de
  opções do mydata, refusal hard (nunca soft-pass, decisão A-05) — Fase 0
  do v1.2, execução autônoma noturna, 1 Crítico achado e corrigido em
  code review (CR-01, chave do ledger não-normalizada)
- ✓ PUT-01/02/03 (ponte gatilho→put, v1.2): hook diário no `scheduler_loop`
  (mesmo padrão de `signal_ledger_job`) cruza gatilho de setup × `positions`
  do usuário, triagem determinística da put de proteção com dados reais do
  hub (`estilo_exercicio`/strike/IV nunca assumidos), grava em tabela nova
  `put_suggestions` (long-only por CHECK constraint, isolada de
  `signal_ledger`/ADR-017 por desenho) com proveniência. **Dormente em
  produção por desenho**: `B3_OPTIONS_PROVIDER=yahoo` (default, intocado)
  não expõe `estilo_exercicio`, então a triagem sempre zera até a virada da
  Fase 9 acontecer — ver `docs/adr/021-ponte-gatilho-put.md`. Zero
  superfície visível (guardião dedicado). 2 Warnings achados e corrigidos
  em code review (WR-01 ticker malformado abortava o dia inteiro; WR-02
  strike não-positivo) — Fase 10 do v1.2, execução autônoma noturna
- ✓ PUTLIFE-01/02/03/04 (ciclo de vida, v1.2): máquina de 5 estados
  (`armada`/`expirada_sem_uso`/`executada_simulada`/`monitorada`/`fechada`)
  vivendo inteiramente em colunas novas de `put_suggestions` — nunca toca
  `optionPositions`/`cash`/`history` reais (provado por teste comportamental
  que monta carteira real e compara JSON byte a byte antes/depois de um
  ciclo completo). `intrinseco()` delega pra `agent.intrinseco_opcao`
  (ADR-005 real, sem fórmula paralela). Hook diário roda mesmo com
  kill-switch ligado — é medição, nunca execução de ordem (decisão do
  executor, override do desenho literal do ROADMAP, ver ADR-022). 0
  Crítico, 2 Warnings de baixo impacto deixados para sua decisão (ver UAT
  abaixo) — Fase 11 do v1.2, execução autônoma noturna, ÚLTIMA fase do
  milestone

- ✓ Opções v2 — v1.4 (Fases 15-19, 24-32): motor de proposta interno
  (`rastrear()`/`avaliar()`) com biblioteca de 3 estruturas (venda coberta,
  put de proteção, collar) sobre posições reais, fluxo de aceite e motor
  multi-candidato; integração real com o serviço MCP externo para cadeia/
  possibilidades/criação de setups; plano comercial como eixo de produto
  (`owner`, limites de IA por plano); consolidação final na aba Opções com
  os dois motores (interno grátis + MCP com custo declarado) lado a lado.
  18/18 requirements formais mapeados Complete, com duas ressalvas de
  verificação humana carregadas explicitamente (não fechadas 100% ao vivo)
  — ver `.planning/milestones/v1.4-ROADMAP.md` Milestone Summary. Fase 26 é
  parcial (backlog B2/B3/C1/C2/C3 carregado adiante, ver Active) — v1.4
- ✓ Redesenho de UI v1.5 (Fases 20-23): shell sem vazamento horizontal,
  teto de 720px em desktop, escala tipográfica numérica nomeada com
  `tabular-nums`, gate de `prefers-reduced-motion`, deduplicação de
  `CapitalCurve`/status do Operador/cards do Portfólio, trilho horizontal
  único, zero emoji nativo, motion com propósito (entrada de card + pulso
  de confirmação) e ilustração flat unificada do Boris no modal de
  introdução — 17/17 requirements, ver `.planning/milestones/v1.5-MILESTONE-AUDIT.md`
- ✓ `PALETTE.light.textDim` (Modo Estudo, tema claro) corrigido de `#6b7288`
  para `#646b7f` — contraste contra `bgPanel` (pior superfície) subiu de
  4,20:1 (reprovava AA) para 4,67:1, com `bgBase` 4,51→5,01 e `bgCard`
  4,79→5,32 subindo junto. Achado COLATERAL da Fase 4, fora do escopo do
  C-16 original (que corrigiu `textFaint` nesta mesma paleta mas não
  `textDim`). O guardião `test_brand_book_v2_tokens.mjs` seção 5 foi
  estendido de `textFaint` para `textFaint`+`textDim` nas 3 superfícies,
  fechando a lacuna que deixou o bug sobreviver à Fase 4 e ao v1.5 —
  corrigido em 2026-09-06
- ✓ 3 achados Baixo do REPORT-01 reverificados e fechados (quick task
  260906-ugb, 2026-09-06): C-18 — `aria-describedby` condicional liga o
  botão "Executar (vende no stop/alvo)" desabilitado ao parágrafo
  `id="executar-gate-hint"` que explica o gate, em `web/src/App.jsx`
  (`AgenteScreen`), com guardião novo em
  `web/tests/test_agente_modo_estudo_ui.mjs`; C-08 — verbete `setup-ifr2`
  de `server/app/kb.py` passa a nomear o princípio de reversão à média no
  texto educacional e a ser buscável pelo termo, com o texto `"operador"`
  intocado de propósito; C-28 — encontrado JÁ RESOLVIDO na reverificação: os
  2 pontos de `appMode || "estudo"` cru citados no achado original sumiram
  no refactor FIX-C21, antes desta sessão — nenhuma mudança de código foi
  necessária
- ✓ 3 achados de PRODUTO do REPORT-01 fechados (quick task 260906-vf9,
  2026-09-06): C-07 — `ModoTrabalhoCard` nomeia explicitamente a aba
  "Operador IA" nos dois ramos do ternário (Estudo/Operador), dizendo que o
  agente pode vender sozinho conforme as regras configuradas — antes o link
  causal entre ligar o Modo Operador e habilitar essa automação não existia
  na tela; C-09 — card de aviso não-bloqueante em `CapitalCurve` quando
  `drawdown > LIMIAR_DRAWDOWN_ALERTA` (limiar de **15%** decidido pelo
  orquestrador), texto vindo de `cp.drawdownAlertaTitulo`/
  `drawdownAlertaCorpo` nos dois modos, mesma gramática visual do card de
  concentração (T.warn nos estilos CSS, P.warn no ícone SVG); C-06 — escopo
  **reduzido** por decisão do orquestrador: `resumoOperacao(h)` (função pura
  nova em `web/src/finance.js`) gera uma frase em português simples por
  operação EXECUTADA já dentro do `HistoricoScreen` existente (não criou
  tela/aba/endpoint novo) — rejeitadas continuam só com "Rejeitada: ...".
  3 guardiões novos, nenhum guardião pré-existente quebrado

- ✓ Simplificação da aba Opções — v1.6 (Fases 33-34): sub-aba "Setups"
  reorganizada por job-to-be-done — 5 jobs extraídos em componentes próprios
  (Fase 33) e navegação hub+workspace substituindo a rolagem única (Fase
  34), com 3 pills do workspace compartilhando uma única leitura paga
  (NAV-05, verificado ao vivo por medição de rede). 13/13 requirements v1
  Done — ver `.planning/milestones/v1.6-ROADMAP.md`.
- ✓ Confiabilidade explicativa da aba Opções — v1.7 (Fases 35-37): jornada
  guiada do workspace com passos nomeados e CTAs com hierarquia visual real
  (Fase 35); motor de payoff genérico estendido com correção de um bug real
  de breakeven espúrio (Fase 36); gráfico SVG corrigido (eixo Y com escala,
  strikes/spot marcados, "hoje" separado de "no vencimento") e explicação
  por segmento 100% determinística, fechando a divergência real de razão
  G/P confirmada em produção (Fase 37). 14/14 requirements v1 Done — ver
  `.planning/milestones/v1.7-ROADMAP.md`. Pendência não-bloqueante:
  verificação visual em produção com dado real (checkpoint fechou com
  evidência automática, sem confirmação visual — ver STATE.md).

### Active

- [ ] Backlog da Fase 26 (v1.4), nunca executado: B2 (preservar estado ao
  trocar de aba, sem decisão de abordagem), B3 (ligar a aba Opções às rotas
  de execução com flag opt-in a descoberto, pesquisa concluída/decisão de
  escopo pendente), C1 (busca nos 83 verbetes da KB), C2 (ancorar verbete
  nas quatro abas sem cobertura), C3 (consolidar os cinco registros
  paralelos de tela do front) — ver `26-CONTEXT.md`
- [ ] Multi-candidato lado a lado (MULTI-02, Fase 19 → sub-aba Operar na
  Fase 32) nunca foi visto renderizando em navegador real com dado real —
  só sob provider mock, reconfirmado como dívida de verificação herdada até
  a última verificação da milestone v1.4 (`32-VERIFICATION.md`,
  2026-09-16); código implementado e coberto por guardião com injeção de
  defeito real
- [ ] Item 8 do checkpoint 08-05: verificação ao vivo da entrada automática
  gated por um pregão inteiro (`entradaAuto` ligado, confirmar que só
  dispara nos setups elegíveis do momento) — depende do Alex ligar a
  feature numa conta de teste
- [ ] 2 human-check da Fase 3 nunca confirmados ao vivo (card de status 3
  badges reativo; mensagem de "sem permissão" no kill-switch pra conta sem
  `execucao_automatica.controlar`) — ver `03-VERIFICATION.md`
- [ ] Backlog (não mapeado a fase ainda): 3 achados Baixo do REPORT-01 sem
  correção (C-10, C-17, C-29) — C-08/C-18 corrigidos e C-28 reverificado na
  quick task 260906-ugb (2026-09-06); C-06/C-07/C-09 (achados de produto,
  não Baixo) corrigidos na quick task 260906-vf9 (2026-09-06)
- [ ] CLAUDE.md exige "drawdown" como conceito didático obrigatório (lista
  de conceitos da camada educacional), mas não existe nenhum verbete para
  ele em `conceitos.py`/`kb.py` — só "diversificação" tem link "saiba mais"
  funcional hoje (achado colateral da quick task 260906-vf9, ao implementar
  o card de aviso de C-09 sem link de verbete por decisão de escopo). Não
  corrigido nesta task — o mecanismo de `conceitos.py` é maior que o de
  `kb.py`/`_SETUPS`, fora de escopo
- [ ] `numHero` (34px, token da escala tipográfica do v1.5/TYPO-02) sem
  nenhum consumidor real — o número mais "hero" do app (patrimônio simulado
  em `CapitalCurve`, `App.jsx:1865`) segue hardcoded em 27px. Decisão
  deliberada documentada em 3 fases sucessivas (20/21/22), não bloqueia
  nada; candidato a uma fase futura de polish visual
- [ ] 4 itens de verificação humana do v1.5 pendentes do Alex, consolidados
  em `.planning/milestones/v1.5-phases/20-funda-o-estrutural-e-tipogr-fica/20-HUMAN-UAT.md`:
  comportamento real de `prefers-reduced-motion` (2 casos), pulso de
  sucesso de ordem com mercado aberto, 2 dos 4 trilhos SYS-01 sem proposta
  de opção ativa durante a verificação
- [ ] CAP-12 (bypass do cap de watchlist no iOS) está fechado em código e
  testado desde a Fase 13, mas só passa a valer nos aparelhos que já têm o
  app instalado depois de um build novo distribuído via TestFlight — ação
  sua (`scripts/ios-bump-build.sh` → `scripts/ios-testflight.sh` →
  archive/upload no Xcode, ver `TESTFLIGHT.md`). Você também sinalizou
  interesse em liberar pra testers externos (amigos) antes de qualquer
  submissão à App Store pública — passos documentados em `TESTFLIGHT.md`
  §6 (grupo externo, Beta App Review, Public Link)

### Out of Scope

- Decisão dos números comerciais do plano gratuito/pago (quantos ativos,
  quantas análises/mês, preço, loja) — depende do Alex, ADR-010; a revisão
  avaliou só se a arquitetura aguenta quando a decisão vier (confirmado:
  aguenta, ver FIX-C31/C32/C33)
- Modo Operador de trades reais — fora do produto por princípio (só carteira
  simulada)
- Posição vendida/short — não existe no modelo de dados, fora de escopo de
  produto
- Fill parcial de ordem — reafirmado em v1.1 (FIX-C14): simulação é
  tudo-ou-nada por desenho, defensável pelo princípio 5 (determinismo);
  declarado explicitamente em copy/doc, não é lacuna
- Fonte dupla por finalidade (brapi só carteira/watchlist, Yahoo só Radar) —
  descartada no checkpoint da fase 1: o Radar intraday (15m) já usa Yahoo
  automaticamente, ganho real seria modesto
- Escolha de fonte de dado (brapi/Yahoo) e frequência de atualização na UI
  do usuário — rejeitada explicitamente no `docs/adr/008-...md`
- Suíte E2E/Playwright completa — avaliada em v1.1 (FIX-C27/ADR-018) e
  decidido NÃO adotar agora: os 3 defeitos históricos mais caros do produto
  ocorreram no lado nativo/Capacitor, superfície que Playwright-em-PWA não
  alcançaria; 4 gatilhos objetivos de reavaliação documentados no ADR-018
- Medidor de orçamento brapi visível ao usuário final — avaliado em v1.1
  (FIX-C34) e decidido que NÃO é necessário: o fix de FIX-C30 (Fase 3) já
  cobre o efeito prático (aviso de dado degradado, sem vazar número);
  construir um medidor nesse ponto contradiria essa decisão de produto já
  shippada

## Context

- Produto maduro, agora com o motor de recomendação revisado com evidência
  medida (não mais intuição): 15 anos de replay determinístico (ADR-016)
  mostraram que o motor de setups tinha expectância negativa; a seleção
  dinâmica por desempenho histórico (ADR-017) é o mecanismo corretivo, em
  produção desde 2026-08-21/22.
- CLAUDE.md da raiz do repo é a fonte normativa de produto: 10 princípios
  obrigatórios (saldo fictício, sem ordem real, transparência de dado, sem
  invenção de valor, cálculo determinístico, sem promessa de lucro,
  disclosure de dado histórico/atrasado, sem enriquecimento rápido, estados
  completos, acessibilidade).
- ADRs relevantes: 001/008 (fonte de dados), 006/007 (camada de entendimento
  e assistente), 010 (planos e cap gratuito — pendente comercial), 013
  (RBAC), 014 (admin mobile), 015 (assertividade da instrumentação), 016
  (diagnóstico do motor de setups), 017 (seleção dinâmica), 018 (avaliação
  de cobertura E2E — decisão de não adotar agora).
- **v1.1 entregou**: Fases 2-5 (REPORT-01: realismo de mercado + os 30
  achados Crítico/Alto/Médio) + Fases 6-8 (nascidas de pesquisa ad-hoc sobre
  o motor de recomendação: instrumentação de assertividade, seleção
  dinâmica por desempenho histórico, interface do histórico medido).
  7 fases, 44 planos, 343 commits, ~5 dias (2026-08-18 a 2026-08-23).
- **v1.3 entregou**: Fases 12-13 (cap comercial ponta a ponta — limites reais
  do plano gratuito, gates bloqueando de verdade, UI de uso/limite nos dois
  stores, bypass do iOS fechado). 2 fases, 8 planos, ~82 commits no range
  (inclui 1 merge de trabalho concorrente não relacionado, PR #27/ADR-23),
  ~2 dias (2026-08-29 a 2026-08-31, incluindo checkpoints humanos ao vivo).
- **v1.5 entregou**: Fases 20-23 (redesenho de UI — fundação estrutural,
  deduplicação, componentes compartilhados, motion+ilustração). 4 fases, 16
  planos, 123 commits, 2 dias (2026-09-05 a 2026-09-06), executado de ponta
  a ponta em modo autônomo (sem pausa para aprovação humana intermediária)
  por decisão explícita do Alex, convivendo com o v1.4 ainda em execução
  sem tocá-lo (invariante técnico: só `web/src/`, zero mudança em
  `server/app/*.py` ou contrato de API). 17/17 requirements, ver
  `.planning/milestones/v1.5-MILESTONE-AUDIT.md`.
- **v1.4 entregou**: Fases 15-19 (motor de proposta, biblioteca de
  estruturas, fluxo de aceite, tira de Posições, motor multi-candidato) +
  Fases 24-32 (integração real com o serviço MCP, planos comerciais,
  otimização parcial de UX/IA, e a consolidação final de toda operação de
  opções numa única aba). 14 fases, 63 planos, ~211 tasks, 2026-09-02 a
  2026-09-16 (arquivado 2026-09-19). Fase 26 parcial (só "Fase A" das 6
  fatias previstas). 18/18 requirements formais (Fases 15-19) mapeados
  Complete, com ressalvas de verificação humana carregadas explicitamente
  — ver `.planning/milestones/v1.4-ROADMAP.md` e
  `.planning/milestones/v1.4-REQUIREMENTS.md`.
- Suíte canônica de teste: `bash scripts/executar.sh --testes` (pytest +
  web/tests/*.mjs); `scripts/test.sh` sozinho é meia baseline. Desde a Fase
  5 (FIX-C24), o próprio `executar.sh` resolve `web/node_modules` ausente
  sozinho (antes precisava de `npm install` manual em checkout/worktree
  novo) e mostra a causa real de falha web em vez de engolir o erro.
- `web-admin/` (portal admin) não tem framework de teste — verificação é
  `npx vite build` + guardiões estáticos em `web/tests/*.mjs` que leem o
  código-fonte do portal (precedente confirmado, `test_fase3_custos_falha_
  brapi.mjs` e outros).
- Deploy: Railway serve só `server/web_dist` (app consumidor) e
  `server/admin_dist` (portal) — publicação é sempre passo manual
  (`scripts/publicar-web.sh`/`publicar-admin.sh`), nunca automático no CI.

## Constraints

- **Produto**: bundle id `com.alexandrecamerini.bolsia` não muda (login SIWA
  depende disso) — qualquer achado sobre branding/nome não pode sugerir isso
- **Financeiro**: cotações, posições, ordens, saldo, custos, lucro/prejuízo e
  drawdown são sempre calculados por regra determinística, nunca pela IA —
  qualquer achado que aproxime IA de cálculo financeiro é severidade alta
- **Dado de mercado**: brapi é master gratuita com orçamento de requisições
  (15k/mês para o app inteiro), Yahoo é backup/intraday — não é diferencial
  de plano pago (ADR-010, decisão 3)
- **Regulatório**: manchete do card de decisão vem só do motor determinístico
  (guardrail CVM); IA explica, nunca substitui
- **Deploy**: Railway com `rootDirectory=/server`; só `server/` é publicado,
  por isso `web_dist`/`admin_dist`/`ios_dist` ficam versionados no git
- **Seleção de setups**: toda elegibilidade/ranking é regra determinística
  sobre o ledger medido (ADR-017) — se algum dia a proposta for deixar a IA
  escolher setup, ordenar o Radar ou decidir entrada, isso é mudança de
  natureza e exige aprovação separada (guardrail explícito do ADR-017)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| D-01 emendado na Fase 34: hub usa SecaoVigias em vez de listar "setups salvos" | A leitura literal original era impossível — `setups` deriva só de `leitura.dados` (leitura paga, ticker-scoped), sempre vazio com `ticker=""`; achado do planner, verificado pelo orquestrador por leitura direta do código antes de aceitar | ✓ Good — evitou implementar um recurso que nunca funcionaria; SecaoVigias já era a listagem cross-ticker real que o critério original pedia |
| Bootstrap do GSD via `/gsd:new-project` num produto brownfield maduro | Usuário pediu revisão geral estruturada; GSD dá rastreabilidade de achado→fase de correção | ✓ Good — todos os 50 requirements de v1.1 rastreados até o REPORT-01/ADR-015/016/017, 44/44 planos com SUMMARY |
| Fase 1 é só diagnóstico, sem correção inline | Usuário escolheu explicitamente — quer priorizar antes de mexer em código | ✓ Good — checkpoint humano confirmou a régua de severidade antes de qualquer código mudar |
| 5 plans paralelos (wave 1) + 1 de consolidação (wave 2) | Mesmo padrão do map-codebase — reduz wall-clock | ✓ Good, causa raiz resolvida — o worktree isolado clona de `origin/main`, não do HEAD local; a partir da Fase 6, `git push` sempre roda antes de spawnar a wave seguinte (nunca mais o problema reapareceu) |
| Fonte dupla por finalidade e listbox de escolha de fonte (propostas do Alex no checkpoint) | Ganho de orçamento pareceu grande à primeira vista | ⚠️ Revisit se re-proposto — ambas descartadas com evidência: Radar intraday já usa Yahoo de graça; listbox já rejeitada no ADR-008 duas vezes |
| Critério de aposentadoria de setup: magnitude econômica em faixas, não \|t\| | Alex rejeitou a proposta original (\|t\| conflacia efeito com tamanho de amostra — provado com Setup 9.1 baixa vs alta, dano quase idêntico, veredito oposto só por 426 observações a mais) | ✓ Good — critério revisado incorporado no ADR-017 Decisão 1 antes de qualquer código, evitou aposentar setup errado por artefato estatístico |
| Checkpoint humano bloqueante represa o push da FASE INTEIRA, não só da task do checkpoint | Fase 8: push de wave 1 (hábito herdado das Fases 6/7) colocou o gate de `entradaAuto` em produção horas antes da aprovação do Alex — exposição real avaliada como zero (feature desligada em todas as contas), mas foi sorte, não desenho | ✓ Good — regra aplicada corretamente na Fase 5 (checkpoint do 05-08), nenhuma wave deu push antes da aprovação |
| Plano que toca `web/src/` precisa de task explícita de bump+publicar-web.sh | Fase 4: os 7 planos fecharam os 9 achados com suíte verde, mas nenhum publicou o front — ficou testado, mergeado e invisível em produção até eu notar manualmente | ✓ Good — corrigido antes de fechar a Fase 4 (commit `f2ef08e`); Fase 5 já nasceu com plano de publicação (05-08) desde o planejamento |
| Consultar design specialists dedicados (navigation/typography) antes do UI-SPEC, quando a fase tem decisão de UI real em aberto | Fase 13 tinha 2 perguntas de design não travadas no CONTEXT.md (validar o placement dual, decidir o tratamento tipográfico do "X/Y") — consulta directa aos specialists deu input mais concreto (achou a distinção `data.watchlist.length`×`catalogSel.length` que evita os 2 contadores divergirem) do que deixar o gsd-ui-researcher inferir sozinho | ✓ Good — UI-SPEC nasceu quase pronto, só 1 bloqueio de checker (3º peso de fonte), resolvido em 1 iteração |
| Code review obrigatório pós-fase (`code_review_gate`) não é cerimônia — achou um Critical real na Fase 13 | Gate fail-closed do CAP-12/CR-01 no iOS comparava a contagem do servidor (sempre desconectada, iOS é local-first) em vez da do aparelho; guardião existente só checava ORDEM das chamadas, não qual valor alimentava a decisão — o próprio objetivo da fase (fechar CR-01) não estava de fato fechado até esse achado | ✓ Good — corrigido, guardião reforçado (mutation-tested), e o mesmo padrão replicado preventivamente no caminho irmão (`putWatchlist`) antes mesmo de virar bug lá |
| Consolidar toda pendência de verificação humana de um milestone num ÚNICO documento (`20-HUMAN-UAT.md`), nunca fragmentar por fase | v1.5 gerou 4 itens humanos em 3 fases diferentes (limitação de ferramenta de emulação de `prefers-reduced-motion`, dependência de horário de pregão); decisão explícita do orquestrador de não criar `21-HUMAN-UAT.md`/`22-HUMAN-UAT.md`/`23-HUMAN-UAT.md` separados | ✓ Good — Alex recebe uma lista só pra revisar no fim, em vez de garimpar N arquivos de fase |
| Executar um milestone inteiro (4 fases) de ponta a ponta sem pausa para aprovação humana intermediária, sob autorização explícita | Alex pediu evolução autônoma completa do v1.5 e configurou o ambiente pra não exigir permissão de tool; v1.4 seguia em paralelo com checkpoints bloqueados, sem interferência entre os dois fluxos | ✓ Good — 4 fases, 16 planos, 123 commits, 17/17 requirements, zero push a `origin` (mesma disciplina do v1.4 pendente), único gap real foi tooling (sem CDP `Emulation.setEmulatedMedia` neste ambiente para testar `prefers-reduced-motion` de verdade) |
| Fase 36: estender `opcoes_payoff.py` em vez de criar um motor de payoff novo | Comparação explícita das duas opções pro Alex; risco de duas fontes de verdade divergentes já aconteceu 2x no repo (`RR_MIN`, CTA de collar) | ✓ Good — motor genérico já existia desde a Fase 15, esta fase só estendeu (domínio/segmentos/correção de bug), zero duplicação |
| Fallback pontual pro Sonnet quando o planner (Opus) da Fase 37 falhou 4x seguidas (500→529, capacidade esgotada) | Autorizado explicitamente pelo Alex após o sinal mudar de erro transiente pra overload real; mesmo prompt/contexto, só o modelo trocou | ✓ Good — 5 planos de qualidade equivalente, checker aprovou (1 ciclo de revisão, motivo não relacionado ao modelo) |
| Checkpoint humano da Fase 37 aprovado com evidência automática, não visual, quando a verificação ao vivo esbarrou em credenciais ausentes no backend local | O Alex escolheu explicitamente não esperar; ressalva registrada com precisão no SUMMARY, no comentário do `SERVER_BUILD_ID` e aqui — nunca apresentada como se tivesse sido uma confirmação visual real | ⚠️ Revisit — pendência não-bloqueante de verificação visual em produção, recomendada mas não forçada |
| `gsd-sdk query milestone.complete` não é confiável sem diff — corrompeu STATE.md na primeira tentativa (fechamento da v1.7) | Mesma classe de bug já documentada para os mutadores `state.*` (texto/contagem de sessão antiga sobrescrevendo o atual), mas num verbo NÃO listado no guardrail original — `progress.percent` caiu de 100% pra 60% contando fases standalone (9, 14) como parte da milestone | ✓ Good, causa raiz contida — revertido via `git checkout`, refeito à mão; guardrail expandido na prática para "qualquer mutador de STATE.md do gsd-sdk", não só os 4 nomeados originalmente |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-09-22 — Milestone v1.7 (Confiabilidade explicativa da
aba Opções, Fases 35-37) fechado e arquivado (14/14 requirements,
`F10-20260921-01`/`F10-20260922-01`). Nenhum milestone aberto no momento —
próximo passo é `/gsd-new-milestone`. Ver `.planning/milestones/v1.7-ROADMAP.md`/
`v1.7-REQUIREMENTS.md` para o detalhe completo do v1.7.*
