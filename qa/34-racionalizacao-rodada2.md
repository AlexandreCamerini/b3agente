# qa/34 — Racionalização de design, rodada 2 (leitura do Radar + fraseologia + Operador IA)

> Build: **F9-20260710-1**. Continuação direta da rodada do mock v2
> (`qa/AUDITORIA-Design-System-v1.md` + `qa/CHECKOUT-Racionalizacao-Design.md`).
> Decisões aprovadas pelo Alex via AskUserQuestion nesta sessão:
> **âmbar no Estudo confirmado** · **card-herói na aba Operador IA** ·
> **Radar P1+P3** · **mock v2 aprovado como um todo**.

## 0. Reconciliação de estado (importante p/ histórico)

A implementação principal do mock v2 (tokens âmbar, ConfluenceRing, Sparkline
na Watchlist, CapitalCurve com área, hero-carrossel, Perfil em tiles, linha de
modo + friso) **já estava commitada** (build F9-20260709-12). No clone
principal havia um **diff não commitado** (a "v13"): LogoMark seguindo o acento
do modo (gradiente por instância via `usePalette()`), `IA_GRAD` via
`var(--accent)` e o hero-carrossel filtrando `confluencia > 0` (ordenado) em
vez de só vereditos "Estudar". Esse diff foi **trazido para este branch**
(idêntico) — ao mesclar, descartar a cópia não commitada do clone principal
(`git checkout -- web/src/App.jsx web/src/version.js` lá) para não conflitar.

## 1. Radar — "análise inicial rápida" (P1 + P3, zero custo de LLM)

Diagnóstico: TODO o dado necessário já vinha no payload determinístico do scan
(`server/app/scanner.py`) — o problema era de exibição.

- **P1 — leitura em prosa no Estudo**: `plano.motivo` (frase pronta do
  `setups.py`: operável/aguardar/esticado/R:R baixo) era renderizado SÓ no
  Modo Operador (`plano = operador ? r.plano : null`). Agora o `motivo`
  aparece também no Estudo, logo sob o veredito. O plano OPERACIONAL completo
  (entrada/stop/alvo/sizing) continua exclusivo do Operador.
- **P3a — sparkline no card**: o campo `spark` (~32 fechamentos) vinha no
  payload do Radar e só era usado na Watchlist — agora renderiza sob o preço.
- **P3b — pill de confiança + critérios**: pill "confiança FORTE/MODERADA/…"
  (`tierOf`) ao lado do veredito (como no mock `modo-operador.html`) +
  contagem "N/M critérios" junto ao nome do setup.

Guardião novo: `web/tests/test_radar_leitura_rapida.mjs` (7 asserções, inclui
o contrato do `spark` no scanner).

**P2 (headline agregada do dia) NÃO foi implementada** — o Alex escolheu
apenas P1+P3 no AskUserQuestion.

## 2. Fraseologia — top 5 gaps da auditoria (item B da matriz, resto)

Auditoria completa (agente): infra correta (`copy.js` + `copyFor()` ligados),
núcleo das telas ok, mas superfícies secundárias hardcodadas na voz de Estudo
vazavam para o Operador. Corrigido:

1. **"O veredito é sempre de estudo, nunca uma ordem" na mesa** — o bloco
   "COMO O RADAR ANALISA" virou `comoAnalisaTitulo`/`comoAnalisaCorpo` por
   modo ("COMO A MESA DECIDE" + corpo de mesa no Operador).
2. **Onboarding da home** ("Bem-vindo ao seu simulador…") → `welcomeTitulo`/
   `welcomeCorpo`/`welcomeCta` por modo.
3. **Aba inferior "Radar" fixa** (tela = "Mesa de oportunidades") →
   `tabRadar` ("Radar" × "Mesa").
4. **Chaves órfãs ligadas**: `btnAnalise` (agora no botão "✨ Estudar este
   ativo" × "✨ Plano completo" da Watchlist — antes "✨ Analisar com IA"
   fixo) e `subtituloPortfolio` (renderizado sob o título do Portfólio).
   `marcaSufixo` REMOVIDA (órfã de verdade — a linha de modo a substituiu).
5. **Vocabulário de monitoramento**: subtítulo da Watchlist →
   `subtituloWatchlist` ("em estudo" × "monitorados"); CTAs do Radar →
   `btnAddMonitor`/`jaMonitorado` ("+ Watchlist"/"✓ Na watchlist" ×
   "+ Monitorar"/"✓ Monitorado").

Extra: `notifVarTitulo` era a ÚNICA chave idêntica nos dois modos — no
Operador virou "MOVIMENTO forte · {t}" (padrão caixa-alta dos irmãos STOP/ALVO).

Guardião: seção qa/34 em `test_copy_theme.mjs` (9 asserções novas);
`test_radar.mjs` atualizado para o novo contrato (design mudou → guardião
mudou).

## 3. Aba Operador IA — card-herói (§7 da auditoria, aprovado)

Reorganização SEM remover nada:
- **Card-herói**: kicker "OPERADOR NO SERVIDOR · 24×5" + estado dominante
  **ATIVO/INATIVO · Executar/Sinalizar** (21px) + toggle como único CTA de
  peso + segmentado Executar/Sinalizar.
- **Card "REGRAS & LIMITES"**: regras (stop/alvo/trailing), tetos (ops/dia,
  valor máx.) e intervalo do ciclo (5/15/30/60) — antes soltos no card do toggle.
- **Rodapé da aba**: link da central de notificações + disclaimer (antes no
  meio do card).
- Card "Modo local" e "EVENTOS E AVISOS RECENTES" intactos.

## 4. Disclaimer ⓘ por tela (mock v2 §10)

Novo `InfoDot` (ⓘ ao lado do título) nas 4 telas principais — Watchlist,
Portfólio, Radar, Operador IA — abrindo o `AboutModal` ("Sobre · Aviso legal",
ponto único do texto). Avisos de conteúdo obrigatórios (termo do Operador,
AiNote nos conteúdos de IA) preservados.

Guardião (3 e 4): `web/tests/test_agente_hero_infodot.mjs` (16 asserções).

## 5. Hex fora do token system (critério §6 da auditoria)

- **Candles do PriceChart** eram verde/rosa FIXOS (`#22c55e`/`#f43f5e`) — a
  única parte do gráfico que ignorava tema/modo após qa/29. Agora
  `P.positive`/`P.negative` (usePalette).
- **`#fbbf24` solto** (2×: diário do operador + logs) virou token
  `warn` do PALETTE (dark `#fbbf24` / light `#a16207`).
- **Critério de aceite: ZERO hex azul inline** fora do PALETTE/marca —
  confirmado por grep e agora TRANCADO por guardião.
- Mantidos de propósito: TEAL/ORANGE (SMA 20/50 — adiado, ver checkout),
  marcas Google/Apple, fundo escuro do LogoMark (identidade de ícone),
  theme-color meta, `#fff`/`#000` de contraste fixo sobre fundos fixos.

Guardião: seção qa/34 em `test_chart_colors_theme_aware.mjs` (4 asserções).

## 6. Validação

- **232/232** pytest backend · **30/30** suítes web de código (as 2 restantes,
  `test_ios_assets`/`test_push_wiring`, exigem `web/ios`+`web/dist`, que são
  gitignorados e não existem no worktree — validam na entrega no clone
  principal). Parse TS de `App.jsx` OK.
- **Hard stop pendente no aparelho** (build F9-20260710-1):
  1. Radar (Estudo): frase-leitura em todo card + sparkline + pill de confiança.
  2. Radar (Operador): aba inferior "Mesa"; bloco "COMO A MESA DECIDE".
  3. Home vazia (Operador): onboarding com voz de mesa.
  4. Watchlist: botão "✨ Estudar este ativo" × "✨ Plano completo".
  5. Operador IA: card-herói ATIVO/INATIVO; regras em "REGRAS & LIMITES";
     notificações no rodapé.
  6. ⓘ ao lado dos títulos abre "Sobre · Aviso legal".
  7. Gráfico do ativo: candles na cor do modo (verde-mercado na mesa).
  8. Perfil → rodapé mostra **F9-20260710-1**.

## 7. Pendências que SEGUEM abertas (fora desta rodada)

- Fase B da eficiência (trades reais, mock `modo-operador.html` tela 4).
- "Desenhar o prompt como especialista no Claude" (escopo não confirmado).
- Matriz qa/26: B no aparelho, C/D/E não testados.
- P2 do Radar (headline agregada do dia) — não aprovada, fica como opção futura.
- TEAL/ORANGE mode-aware (adiado, cosmético).
