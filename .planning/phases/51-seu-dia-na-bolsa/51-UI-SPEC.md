---
phase: 51
slug: seu-dia-na-bolsa
status: approved
reviewed_at: 2026-11-17
shadcn_initialized: false
preset: none
created: 2026-11-17
---

# Phase 51 — UI Design Contract

> Contrato visual e de interação do card "Seu dia na bolsa", do convite do push, do streak e do painel do portal. Gerado por gsd-ui-researcher, verificado por gsd-ui-checker. Fontes: `51-CONTEXT.md` (D-01..D-20, travadas), `.planning/engajamento/DECISIONS.md` (Q1-Q8), CLAUDE.md, skill `didatica-boris`, tokens lidos em `web/src/App.jsx` e `web-admin/src/App.jsx`.

Regra de ouro desta fase: o design não reabre decisão. Onde CONTEXT silencia, vale a seção "Premissas" no fim.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none (React 18, estilo inline com tokens próprios; sem shadcn, sem lib de componentes) |
| Preset | not applicable |
| Component library | none (componentes próprios: `card`, `kicker`, `SetorAlvo`, `ConceitoSheet`, `MarketStatusBadge`; portal: `Card`, `Kpi`, `Kv`, `Estado`, `ResumoExecutivo`, `EventoComSerie`) |
| Icon library | none (glifos de texto e SVG inline já usados no app; nenhuma dependência nova) |
| Font | App: `DISPLAY` Fredoka (título), `SANS` Nunito (corpo), `MONO` ui-monospace (números, tickers, R). Portal: mesmas três constantes |

Regras de reuso (não criar sistema novo):
- App consumidor: cores só via `T.*` (aponta para `var(--x)`, segue tema claro/escuro e modo Estudo/Operador). Nunca hex literal no card.
- Portal: cores só via `T` local de `web-admin/src/App.jsx` (dark-only, accent dourado).
- Superfície do card: o objeto `card` (`bgCard`, borda `borderSubtle` 1px, raio 12px), mesmo do carrossel de setups do Acompanhar.
- Teto de largura herdado (`CONTENT_MAX_WIDTH` 720px). O card não define largura própria.

Focal point: com o card presente, a âncora visual do Acompanhar é o heading 16px/700 do card (frase-chamada) sobre o filete accent de 3px, o único bloco com accent estrutural acima do carrossel; o h1 de saudação (23px) fica como contexto. Sem card, a âncora volta a ser o carrossel de setups.

Onde entra (Acompanhar = `EvolucaoScreen`, `web/src/App.jsx` ~2348): Ordem fixa na coluna flex: saudação+status do mercado (h1 existente) → **Card "Seu dia na bolsa"** → `OperadorIACard` → carrossel de setups. Motivo: a saudação e o `MarketStatusBadge` já dão o carimbo de mercado; o card é o primeiro conteúdo acionável e fica "no topo" do conteúdo, sem deslocar o h1.

---

## Spacing Scale

Escala do app (`SP` = 4, 8, 12, 16, 20, 24, 32), todos múltiplos de 4.

| Token | Value | Usage nesta fase |
|-------|-------|-------|
| xs (SP1) | 4px | gap glifo-texto, gap entre kicker e título |
| sm (SP2) | 8px | gap entre chips, entre linhas dentro de um bloco de família |
| md (SP3) | 12px | padding interno de linha-de-família, gap entre blocos de família |
| lg (SP4) | 16px | padding do card (todos os lados), gap card ↔ próximo bloco da tela |
| xl (SP6) | 24px | gap entre seções do painel do portal |
| 2xl (SP8) | 32px | reservado (não usado no card) |

Nota: 12px (SP3) e 20px (SP5) pertencem à escala `SP` existente do app (`App.jsx` L1377, padrão já em uso), e são múltiplos de 4.

Exceptions:
- Alvos de toque: toda linha explorável, botão do convite e chips de ação têm `minHeight: 44px` (padrão já usado em `App.jsx`: 1837, 2063, 2500). O visual da linha pode ser menor; a área tocável não.
- Dots da faixa de streak: 8px de diâmetro, gap 4px (a área tocável é do conjunto, não de cada dot; a faixa não é interativa).

---

## Typography

Quatro tamanhos, dois pesos, na escala já existente do app. Tamanhos fora desta tabela não entram no card.

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Label / kicker (CAIXA ALTA, `letterSpacing 0.05em`, `T.textFaint`) e carimbo de dado | 11px | 700 | 1.4 |
| Body (frases do card, pergunta do Estudo, linha de mesa do Operador) | 13px | 400 | 1.5 |
| Heading (título "Seu dia na bolsa", `DISPLAY`) | 16px | 700 | 1.2 |
| Número destaque (R, %, ATR, patrimônio do dia; `MONO`, = `numBody`) | 18px | 700 | 1.2 |

Pesos: 400 (regular) e 700 (bold). Nada de 600/800 no card. Ticker em `MONO` 13px/700 inline; percentuais inline no corpo usam `MONO` 13px/700. Termo de conceito = `SUBLINHADO` pontilhado (padrão da camada didática), sem mudar peso.

Portal: corpo 13px (padrão do `Kv`), rótulo 11px `T.faint` (escala da fase: 11/13/16/18, sem tamanhos extras), valor `MONO` 700; título de `Card` já definido.

---

## Color

Cores via `T.*`. 60/30/10:

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `T.bgBase` | fundo da tela |
| Secondary (30%) | `T.bgCard` (+ `T.bgPanel` para linhas internas/chips, `T.borderSubtle` bordas) | corpo do card, linhas de família |
| Accent (10%) | `T.accent` (Estudo azul-esverdeado `#2fa8a0`/`#1e7972`; Operador dourado `#d4af37`/`#84671b`) | ver lista abaixo |
| Destructive | n/a nesta fase (nenhuma ação destrutiva); `T.negative` só como sinal de valor de carteira (família 2) | ver restrição abaixo |

Accent reservado EXCLUSIVAMENTE para:
1. Filete esquerdo de 3px do card (`borderLeft: 3px solid T.accent`, igual ao carrossel).
2. Botão primário "Quero receber" do convite.
3. Sublinhado/foco do termo de conceito explorável e o texto de ação "Ver [conceito] →" (cor `T.accent`, 700).
4. Anel de foco (`outline 2px T.accent`, offset 2px) dos elementos tocáveis.

Não usar accent em: números, chips de desfecho, kicker, faixa de streak, linha de carteira.

Restrições de cor (honestidade visual, princípio 8 e D-04):
- **Desfecho do "e se": alvo e stop usam o MESMO tratamento neutro** (chip `T.bgPanel`, borda `T.borderSubtle`, texto `T.textPrimary`, mesmo tamanho, mesmo peso). A distinção é por texto e glifo (alvo: "▲ chegaria ao alvo"; stop: "■ stop atingido — não entrar foi o acerto"), nunca só por cor. Proibido pintar o stop de vermelho/`T.negative` ou o alvo de verde: isso criaria "perdeu/ganhou" visual. O R fica em `T.textPrimary` com sinal explícito (`+1,8R`, `-1,0R`).
- **Família 2 (carteira)** segue a convenção do app: variação do dia e carteira × IBOV em `T.positive`/`T.negative` (valor, sinal universal, igual ao P&L do resto do app); zero/`null` em `T.textMuted`. Resultado negativo tem o mesmo tamanho e posição que o positivo (D-02: não esconder placar negativo).
- Banner de dado atrasado: `T.warn` + `T.warnTint10`, padrão de `role="status"` da base (`App.jsx:586`).
- Tema claro: tokens já cobrem AA; não adicionar cor nova.

Portal: `T.card` / `T.border` / `T.text` / `T.muted` / `T.faint`; accent dourado só no título ativo e no foco; **sem `tone="positive"/"negative"` em nenhum KPI desta fase** (ver Portal).

---

## Anatomia do card "Seu dia na bolsa" (app)

Container: `card` + `borderLeft: 3px solid T.accent`, padding 16, `display:flex; flexDirection:column; gap:12`. `role="region"`, `aria-labelledby` apontando para o título.

### Cabeçalho
- Linha 1: kicker `SEU DIA NA BOLSA · {DD/MM}` (11px/700, `T.textFaint`).
- Linha 2: heading 16px/700 `DISPLAY`: frase-chamada determinística do template (Estudo: pergunta curta de curiosidade; Operador: manchete de mesa). Uma única frase, no máximo 2 linhas.
- Carimbo do dado (11px/700, `T.textFaint`): `Fechamento de {DD/MM} · calculado às {calculadoEm} · {fonte}`. `{fonte}` e `{calculadoEm}` vêm prontos do payload do endpoint (por família, quando diferem); o cliente nunca compõe nem hardcoda a fonte. Princípio 3 e D-11.
- Toque no cabeçalho **não** colapsa nada; "abrir" (`daily_card_opened`) = card entrou em tela por ≥1s com a aba ativa OU qualquer toque no card. Premissa P-3.

### Corpo: três blocos de família, ordem por modo (D-09)
- Estudo: Família 1 → 3 → 2. Operador: Família 2 → 1 → 3. A ordem vem do payload (`ordem: [...]`), calculada no servidor; o front só renderiza na ordem recebida.
- Cada bloco: `T.bgPanel`, raio 10px, padding 12, gap 8, separados por 12px. Bloco sem conteúdo no dia **não é renderizado** (sem placeholder, sem "nada hoje"). Mínimo 1 bloco (senão não há card, D-12).
- Cada bloco abre com label de família (11px/700, `T.textFaint`): `O "E SE" DO QUE VOCÊ VIU` / `O QUE O MOTOR FEZ NA SUA CARTEIRA` / `UM FATO RARO DO MERCADO`.

**Família 1 — o "e se"** (setups vistos e resolvidos no dia; D-03..D-05)
- Cada setup = 1 linha tocável (`minHeight 44`): `TICKER` (MONO 13/700) · nome do setup · chip de desfecho neutro · R em 18px MONO à direita. Máximo 3 linhas visíveis; excedente em "+N" que não é link (placar cobre).
- Chip de desfecho (mesmo estilo para todos): `▲ chegaria ao alvo` | `■ stop atingido — não entrar foi o acerto` | `○ expirou sem gatilho` | `○ sem gatilho no horizonte`. Alvo e stop: mesma altura, mesmo peso, mesma posição.
- Placar semanal ao pé do bloco, SEMPRE com os 4 contadores na mesma linha e mesmo estilo: `Semana: {X} vistos · {Y} chegariam ao alvo · {Z} ao stop · {W} abertos ou expirados` (13px/400, números em MONO 700). Com Y=0 ou Z=0 o contador aparece mesmo assim ("0"), nunca omitido.
- Linha tocável abre o plano do ativo (`daily_card_explored` `tipo:"plano"`, `familia:1`). O ticker é alvo próprio? Não: a linha inteira é um único alvo, evita dois alvos de 44px empilhados (premissa P-6).
- Preços de gatilho/stop/alvo/R exibidos vêm do arquivo do motor (T-50-13). Sem preço no payload → o campo não aparece (nunca `0`).

**Família 2 — o motor na carteira** (D-06)
- Linhas de evento, uma por fato, ordenadas por horário: `Stop de PETR4 subiu para R$ 38,20 (breakeven)` / `Alvo de VALE3 executado` / `Ordem pendente de ITUB4 executada` / `Carteira {+0,4%} × IBOV {-0,9%} no dia`.
- A linha carteira × IBOV é sempre a última e a única com 18px MONO nos dois números, lado a lado, mesmo tamanho. IBOV sem dado → `—` + `T.textMuted` + texto "IBOV indisponível hoje" (nunca 0%).
- Linha de evento tocável abre a posição (`tipo:"ativo"`, `familia:2`); linha carteira × IBOV não é tocável (informativa).

**Família 3 — fato raro** (D-07/D-08)
- 1 fato por dia (o de maior raridade; empate: ativo do usuário antes de mercado). Frase do template com número do dia em MONO 700 + 1 termo de conceito com `SUBLINHADO`.
- Estudo: a frase + uma pergunta de uma linha própria (13px/400, `T.textSecondary`, sem itálico).
- Operador: só a linha de mesa, sem pergunta.
- Ação: `Ver {conceito} →` (accent, 700, `minHeight 44`) abre `ConceitoSheet` via `abrirVerbeteKb`/conceito novo (`tipo:"conceito"`, `familia:3`). O próprio termo sublinhado abre a mesma folha (um clique em qualquer dos dois dispara 1 `explored`, deduplicado por card+tipo+id).
- Selo de raridade (opcional, só texto): `raro: percentil 95 em 12 meses` ou `acima de 2×ATR(14) do ativo` (11px/700 `T.textFaint`). Sai do payload; é o critério real da regra.

### Rodapé do card
- Linha de transparência fixa (11px, `T.textFaint`), texto de `skill_ref`/`copy.js`: `Simulação educacional com dinheiro virtual. Não é recomendação.` (reusar a string canônica de `disclaimers.js`, sem texto novo).
- Convite (quando aplicável) entra acima desta linha, ver abaixo.

### Remoção
D-15: o card do dia anterior some quando o próximo é gerado. Sem botão de dispensar/fechar na v1 (reduz estado; o card é curto e não bloqueia). Premissa P-5.

---

## Estados completos (princípio 9)

O slot do card no Acompanhar renderiza exatamente um destes estados. Fonte única: resposta de `GET /api/dia-na-bolsa` (nome sujeito ao planner) + `ctx.mercado`.

| Estado | Gatilho | Visual | Copy (chave em `copy.js`) |
|--------|---------|--------|------|
| Carregando | primeira busca da sessão | skeleton do card: 3 barras `T.bgPanel` (altura 16/48/48px), sem shimmer animado em `prefers-reduced-motion`; mantém altura mínima 148px para não saltar o layout | `aria-busy="true"`; texto sr-only "Carregando o resumo do dia" |
| Card do dia | payload com `data` = último pregão fechado e ≥1 bloco | card completo | templates |
| Vazio (sem nada relevante) | job rodou e não gerou card (D-12) | **nada é renderizado** (slot colapsa, 0px). Não existe card vazio | n/a |
| Vazio (conta nova, sem posição/watchlist/visto) | `novato` (já existe no `EvolucaoScreen`) | nada; o onboarding existente cobre | n/a |
| Erro | falha da requisição | linha compacta (`T.bgPanel`, borda `T.borderSubtle`, padding 12) com `role="status"` + botão texto "Tentar de novo" (44px). Não bloqueia o resto da tela | "Não consegui carregar o resumo do dia. Seus dados e saldo não mudaram." |
| Dado atrasado / card de pregão anterior | `data` do card < último pregão fechado E agora > 17:30 BRT (job falhou/atrasou) | card completo + banner `T.warnTint10`/`T.warn` no topo com `role="status"` | "Este é o resumo de {DD/MM}. O de hoje ainda não foi gerado." |
| Mercado fechado (após 17:15, fim de semana, feriado) | `ctx.mercado` fechado | card do último pregão permanece; carimbo diz o pregão de origem; sem banner extra (o `MarketStatusBadge` do h1 já informa) | carimbo "Fechamento de {DD/MM}" |
| Feriado/fim de semana | `pregao.is_holiday` | sem card novo; permanece o do último pregão até o próximo ser gerado (D-15) | idem |
| Fonte parcial | Yahoo/IBOV falhou, resto ok | card sem a parte do IBOV; linha "IBOV indisponível hoje"; nada estimado | "IBOV indisponível hoje" |
| Ordem rejeitada / parcial | n/a nesta fase (card não executa ordem; execução é tudo-ou-nada por desenho) | n/a | n/a |

Transição: sem animação de entrada além de `opacity` 150ms; respeitar `prefers-reduced-motion` (sem transição).

---

## Convite do push `fechamento` (D-13)

Aparece **dentro do card**, acima do rodapé de transparência, uma única vez por conta existente que ainda não decidiu (aceite OU recusa gravados; flag/estado vive no servidor, decisão de armazenamento do planner). Conta nova (push já ligado) nunca vê o convite.

Condições de exibição (todas): app nativo iOS com permissão de push concedida; `prefs.fechamento` não decidido; card do dia presente (D-13: o convite vive no próprio card). Na web/PWA o convite não existe (sem push na v1). Sem card no dia, o convite não aparece e espera o próximo card (P-4).

Visual: bloco `T.accentTint10`, raio 10px, padding 12, gap 8.
- Texto 13/400: pergunta.
- Dois botões lado a lado, mesma altura 44px, mesma largura (flex:1), mesmo peso:
  - Primário (accent preenchido, texto `T.onAccent`, 700): `Quero receber`
  - Secundário (transparente, borda `T.borderSubtle`, texto `T.textSecondary`, 700): `Agora não`
- Recusa é tão fácil e visível quanto aceite (sem dark pattern). Após qualquer escolha o bloco some e não volta; o usuário muda depois em Configurações (preferência `fechamento` já listada junto das outras de push; adicionar o rótulo `Resumo do fechamento (17:15)`).
- Confirmação: `role="status"` 3s: aceite "Combinado. Você recebe o resumo no fechamento de dias de pregão." / recusa "Tudo bem. Você ainda vê o resumo aqui no Acompanhar."

Copy do convite: Estudo e Operador usam o mesmo texto (convite é configuração, não conteúdo didático): "Quer receber este resumo às 17:15, nos dias de pregão?"

---

## Push "Seu dia na bolsa" e linha do Radar 08:45

Texto 100% de template (`skill_ref` ↔ `copy.js`, paridade byte a byte, 3-4 variantes por regra, escolha por hash(usuário+dia)). Sem emoji, sem urgência, sem "oportunidade".

- Título fixo: `Seu dia na bolsa`.
- Corpo (≤110 caracteres, 1 frase, termina em ponto): a manchete da família de maior prioridade **do modo**.
  - Estudo exemplo: "O IBOV oscilou 3,8% hoje, um dia raro. Quer ver o que isso significa?"
  - Operador exemplo: "Stop de PETR4 subiu para breakeven. IBOV -0,9%, carteira +0,4%."
- Toque no push abre o Acompanhar com o card visível (`notification_tapped` existente).
- Horário ~17:15 BRT; silêncio em dia sem pregão e sem card; teto 2 engajamento/dia.
- **Linha do Radar 08:45** (`PUSH_RADAR`): uma linha extra ao final do corpo: `Ontem: {TICKER} {chegaria ao alvo | teve o stop atingido}.` Alvo e stop com a mesma construção e o mesmo comprimento aproximado. Sem R no push. Se o "e se" de ontem não existir, a linha é omitida (sem "nada ontem").
- Web/PWA: sem push; só o card.

---

## Vocabulário e Copywriting Contract

Fonte: templates em `server/app/skill_ref.py`, espelhados em `web/src/copy.js`. O front nunca compõe frase. Guardião de vocabulário (D-02) reprova, em qualquer template de card/push/radar/convite, as formas: `perdeu`, `perdeste`, `oportunidade`, `imperdível`, `última chance`, `só hoje`, `agora!`, `entre agora`, `garantid*`, `lucro certo`, `não perca`, `fique rico`, `rápido`, contagem regressiva, e qualquer superlativo promocional. Estudo não usa verbo de ordem (`compre`, `venda`); Operador pode falar a linguagem de mesa já existente (`COMPRAR/VENDER` só se vierem do vocab), mas nunca como convite a operar no card de fechamento.

| Element | Copy |
|---------|------|
| Título do card | `Seu dia na bolsa` |
| Primary CTA (convite) | `Quero receber` (secundário: `Agora não`) |
| CTA de exploração | `Ver {conceito} →` / linha tocável de plano ou ativo (sem rótulo de botão) |
| Empty state heading | n/a: sem card, nada é renderizado (D-12). Não existe tela vazia |
| Empty state body | n/a |
| Error state | "Não consegui carregar o resumo do dia. Seus dados e saldo não mudaram." + ação `Tentar de novo` |
| Dado atrasado | "Este é o resumo de {DD/MM}. O de hoje ainda não foi gerado." |
| Destructive confirmation | n/a: nenhuma ação destrutiva nesta fase (aceitar/recusar convite é reversível em Configurações) |

Templates por regra (família 1, desfecho; estrutura obrigatória, 3-4 variantes por regra finalizadas pelo planner; abaixo a variante canônica por modo):

| Regra | Estudo | Operador |
|-------|--------|----------|
| alvo | "{T} chegou ao alvo do plano que você viu ({R}). O que fez o plano funcionar?" | "{T}: alvo atingido, {R}." |
| stop | "{T} atingiu o stop do plano que você viu ({R}). Não entrar foi o acerto aqui. Por quê?" | "{T}: stop atingido, {R}. Sem entrada, sem efeito no seu saldo virtual." |
| expirou / sem gatilho | "{T} não chegou ao gatilho dentro de {N} pregões. Sem entrada, sem resultado." | "{T}: sem gatilho em {N} pregões." |

(`{R}` sai do motor, formato `+1,8R`; nunca texto livre. Nenhum template usa "prejuízo", "perdeu" nem "perda".)

Família 2 e 3 seguem o mesmo mecanismo (placeholders do motor + conceito). Exemplos de CONTEXT ("O IBOV caiu 3,8%: dia mais forte em 14 meses." / "B3SA3 andou 3 ATRs hoje. O que isso diz do seu stop?" / "PETR4 abriu 4% abaixo de ontem e não voltou.") são ilustrativos e válidos como forma.

Mensagens com número: percentual com vírgula decimal pt-BR (`Intl.NumberFormat("pt-BR")`, já usado no app), `null` → `—`, nunca `0`. Moeda `R$ 38,20`.

---

## Streak: dias de decisão (D-16/D-17)

Substitui o rótulo do streak atual (hoje lê `config.streak.days`, conta abertura; `App.jsx` ~10938).

- Texto: `{X} dias de decisão nas últimas 4 semanas` (13px/400, `{X}` MONO 700). `X=0`: "Nenhum dia de decisão nas últimas 4 semanas ainda. Explorar o resumo do dia conta." Sem tom de cobrança, sem "sequência quebrada", sem zerar.
- Faixa opcional de 28 dots (4 linhas × 7; 8px; gap 4px): cheio `T.textSecondary` = dia de decisão; vazio `T.borderSubtle` (contorno) = sem decisão; fim de semana/feriado = ponto 4px central `T.borderFaint` (forma diferente, não "vazio"). Nenhum dot em vermelho. `aria-label` na faixa com o mesmo texto; os dots são `aria-hidden`.
- Data sempre `hojeBRT()` (D-17). Nada de `toISOString().slice(0,10)`.
- Nenhuma medalha, selo, confete, número recorde, ranking ou contagem de operações. Nenhum texto sugere que comprar/vender melhora o número.
- Evento `decision_day` (1× por dia BRT, com `modo` e `origem`: `card|plano|stop`) emitido no momento da decisão, não na abertura do app.
- Decidir "não entrar": Grep em `web/src/App.jsx` (não entrar, descartar, dispensar, pular) não achou controle de usuário para isso (só o veredito do motor, ~L1367). Este caminho do D-16 fica SEM origem de evento nesta fase, FORA da v1 por decisão do Alex em 2026-11-17 (P-7). Não há botão novo neste contrato. `decision_day` nesta fase cobre `card`, `plano` (revisar) e `stop` (ajustar).

---

## Interação e analytics (D-01, D-18)

- `daily_card_shown`: card visível ≥1s, 1× por card/dia/sessão.
- `daily_card_opened`: primeiro toque no card ou permanência ≥1s com aba ativa (P-3), 1× por card.
- `daily_card_explored`: toque em conceito, ativo ou plano; payload `{tipo: "conceito"|"ativo"|"plano", familia: 1|2|3, modo}`; 1× por (card, tipo, alvo). Sem ticker/preço/valor monetário no payload (chaves proibidas de `analytics.py:35`).
- `decision_day`: ver streak.
- Todos com `modo` ("estudo"|"operador"). Entram na lista `EVENTOS` de `web/tests/test_analytics_instrumentacao.mjs`.
- Abrir só o card **não** conta como sucesso (D-01); o front não exibe nenhuma métrica de exploração ao usuário.

Acessibilidade:
- Região nomeada; título é `h2` (o h1 da tela já existe).
- Cada linha tocável é um `<button>` com nome acessível completo ("PETR4, plano chegaria ao alvo, mais 1,8 R. Abrir plano"). Foco visível 2px accent.
- Desfecho nunca só por cor (texto + glifo). Contraste: tokens já medidos AA nos dois temas e modos.
- Termos de conceito: botão sr-only "O que é {conceito}?" conforme padrão `SetorAlvo`.
- Mobile 360px: texto quebra, sem rolagem horizontal; chips quebram para linha própria; alvo ≥44px.
- `prefers-reduced-motion`: sem animações.
- Declarar setores/ids novos de conceito em `conceitos.SETORES`/KB (amplitude/capitulação, máxima/mínima de 52 semanas), redação pela skill `didatica-boris`: o que é, o que acontece, o que NÃO acontece (o app não executa ordem).

---

## Portal admin (`web-admin`) — painel "Engajamento do fechamento"

Dark-only, tokens `T` locais, componentes existentes (`Card`, `Kpi`, `Kv`, `Estado`, `ResumoExecutivo`, `EventoComSerie`, `selectStyle`). Local: nova seção na aba de analytics, abaixo do funil (`web-admin/src/App.jsx` ~270-304), mesmo seletor de período (7/30/90 dias) e mesmo `Estado` (loading/erro/vazio). Dados: `GET /api/analytics/...` (RBAC como as demais, via backend).

Layout, de cima para baixo:
1. `ResumoExecutivo` com 4 `Kpi` iguais em tamanho e sem `tone`:
   - `WAU (7 DIAS)` = `COUNT(DISTINCT user_id)` de `session_start`, exato sobre eventos brutos.
   - `EXPLORAÇÃO DO CARD (4 SEM)` = explorou ÷ viu, em %, com `n` ao lado.
   - `DIAS DE DECISÃO / USUÁRIO (4 SEM)` = mediana (valor principal) e média no `Kv` abaixo.
   - `OPERAÇÕES / USUÁRIO ATIVO (4 SEM)` = `trade_simulated` ÷ WAU médio.
2. `Card` "Exploração × operações, lado a lado": duas séries `EventoComSerie` no mesmo eixo de tempo, mesma altura, mesma largura, mesma cor (`T.muted`), uma sobre a outra: (a) exploração do card por semana, (b) `trade_simulated` por usuário ativo por semana. O contrapeso tem peso visual idêntico ao de engajamento. É proibido destacar (a) e esmaecer (b).
3. `Card` "Exploração por família e modo": tabela 3 famílias × 2 modos (`Kv` ou tabela simples com `MONO`), cada célula `{explorou}/{viu} ({pct}%)`. Célula com `viu < 20`: sufixo `amostra pequena` em `T.faint` (limiar 20 = P-8).
4. `Card` "WAU": série semanal (`EventoComSerie`), persistida em `obs_daily_metrics` via `registrar_metricas_diarias`/`METRICAS_CONHECIDAS` para passar dos 90 dias; rótulo da fonte da série (bruta ≤90 dias; rollup além).

Regras do painel:
- **Sem meta, sem alvo, sem linha de 30%, sem semáforo, sem `tone`, sem alerta** (D-20). A hipótese existe só no documento de decisões (`DECISIONS.md`/D-20); nenhum número de referência aparece na tela, nem em rodapé. Se houver nota, é só: "Sem meta e sem alerta. Compare a tendência após 4 semanas de baseline." (11px, `T.faint`). Nenhum valor é colorido por estar acima/abaixo de referência.
- Estado vazio: "Ainda não há eventos do card de fechamento neste período." Erro: mensagem do `Estado`. Loading: `Estado`.
- Atenção a mobile (ADR-014): `minWidth:0`/`overflowWrap:anywhere` herdados de `Kv`; tabela com `overflowX` apenas pelo helper existente de rolagem, sem estourar a página.
- Eventos distinguem usuários únicos (`usuarios`) de total; sempre exibir o denominador.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | nenhum (shadcn não inicializado; gate do shadcn não aplicável: projeto sem `components.json`, stack própria já estabelecida em 50+ fases) | not applicable |
| third-party | nenhum | not applicable |

Nenhuma dependência nova de UI ou ícones.

---

## Premissas (onde CONTEXT silencia; revisar na verificação)

- P-1. Sem shadcn: o gate de inicialização foi dispensado por o projeto ter design system próprio consolidado (tokens `T`, `SP`, `MONO/SANS/DISPLAY`); introduzi-lo agora divergiria de 50 fases.
- P-2. Posição do card: abaixo do h1/status de mercado e acima do `OperadorIACard`. Reversível trocando a ordem dos filhos.
- P-3. "Aberto" = card visível ≥1s com aba ativa ou qualquer toque nele. Não é métrica de sucesso (a de sucesso é `explored`).
- P-4. Sem card no dia e conta existente elegível ao convite: alinhado ao D-13 (convite no próprio card): sem card no dia, o convite NÃO aparece e espera o próximo card gerado. Sem linha isolada.
- P-5. Sem botão de dispensar na v1; o card some quando o próximo é gerado (D-15).
- P-6. Linha de família 1 = um único alvo tocável (abre o plano), para evitar alvos de 44px aninhados; o ticker não é link próprio.
- P-7. Não existe no app controle de usuário para "decidir não entrar" (Grep em `App.jsx` por não entrar/descartar/dispensar/pular: nada além do veredito do motor). Esse caminho do D-16 fica FORA da v1 (decisão do Alex, 2026-11-17). Nenhum botão inventado.
- P-8. Limiar de "amostra pequena" no portal: 20 vistos por célula.
- P-9. Desfecho alvo/stop com o mesmo tratamento neutro de cor; carteira em P&L segue verde/vermelho como o resto do app (valor de carteira, não julgamento de decisão).
- P-10. Texto do convite é igual nos dois modos (configuração, não didática).
- P-11. Dado atrasado só é sinalizado quando o card exibido é de pregão anterior ao último fechado após 17:30 BRT; antes disso, o card de ontem é o estado normal.
- P-12. Nenhum ícone/ilustração novo; glifos de texto `▲ ■ ○` são suficientes e acessíveis (texto acompanha).
- P-13. Limite de 3 linhas na família 1 e 1 fato na família 3 mantêm o card ≤ cerca de 60% da altura útil em 390x844.

---

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS
- [x] Dimension 2 Visuals: PASS
- [x] Dimension 3 Color: PASS
- [x] Dimension 4 Typography: PASS
- [x] Dimension 5 Spacing: PASS
- [x] Dimension 6 Registry Safety: PASS

**Approval:** approved 2026-11-17 (gsd-ui-checker, revisão 1/2; FLAG D-16 "não entrar" resolvido: fora da v1, decisão do Alex 2026-11-17)
