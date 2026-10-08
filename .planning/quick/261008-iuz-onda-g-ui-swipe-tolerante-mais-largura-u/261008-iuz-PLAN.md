---
phase: quick-261008-iuz
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - web/tests/test_ui_onda_g.mjs
  - web/tests/test_ui_onda_b.mjs
  - web/tests/test_cartao_v6_aberto.mjs
  - web/src/navStack.js
  - web/src/App.jsx
  - web/src/opcoes/CuradoriaEstruturas.jsx
  - web/src/opcoes/OpcoesScreen.jsx
  - web/src/opcoes/OportunidadesOpcoes.jsx
  - web/src/opcoes/SecaoAnalisar.jsx
  - web/src/opcoes/AnatomiaPerna.jsx
  - web/src/opcoes/GraficoResultado.jsx
  - web/src/opcoes/PosicaoTotal.jsx
autonomous: true
requirements: [ONDA-G-1, ONDA-G-2, ONDA-G-3]

must_haves:
  truths:
    - "No iPhone, o swipe-back de borda dispara com toque inicial até x=32, deslocamento horizontal > 50 e vertical < 60"
    - "Arrastar carrossel, tabela rolável ou slider (input range) colado à borda esquerda NÃO volta a tela"
    - "Em 375–430pt, o container de conteúdo ocupa >= 92% da largura da tela (gutter 12px por lado); em >= 732px o gutter segue 18px e o max-width 720px não muda"
    - "Em landscape com notch, o conteúdo não fica sob a safe area (padding = max(gutter, env(safe-area-inset-*)))"
    - "Cartões das telas principais (Resumo/Evolução, Carteira, Mesa/Radar, Agente, Perfil/config) têm padding lateral 16px (SP[4]) em vez de 17/18/20"
    - "Com 0 ações livres, 'Registrar saída · 0 ações livres' é disabled, aria-disabled, opacidade 0.6, cursor not-allowed, cor T.textFaint, altura >= 44, mesmo texto"
  artifacts:
    - path: "web/tests/test_ui_onda_g.mjs"
      provides: "Guardião da Onda G (3 partes)"
    - path: "web/src/navStack.js"
      provides: "BORDA_PX=32, DX_MIN=50, DY_MAX=60"
      contains: "export const BORDA_PX = 32;"
    - path: "web/src/App.jsx"
      provides: "GUTTER_X, CARD_PAD_X, container com safe-area, botão de saída desabilitado"
      contains: "const CARD_PAD_X = SP[4];"
  key_links:
    - from: "web/src/App.jsx (useEffect do swipe iOS)"
      to: "web/src/navStack.js ehGestoVoltarBorda"
      via: "closest(\"canvas, input[type=\\\"range\\\"], [data-sem-gesto-voltar]\") exclui o alvo antes de registrar o toque"
    - from: "web/src/App.jsx hero-carrossel (scrollSnapType x mandatory)"
      to: "GUTTER_X"
      via: "margin/padding de sangria igual ao gutter do container (antes -18px/18px fixos)"
---

<objective>
Onda G de UI (decisões do Alex, fechadas): (1) swipe-back de borda mais tolerante no iPhone sem roubar gestos de rolagem horizontal; (2) mais largura útil no iPhone (gutter 12px + padding lateral de cartão 16px), sem mudar tablet/desktop; (3) botão de saída com 0 ações livres efetivamente desabilitado.

Purpose: o gesto falha no aparelho real; o conteúdo desperdiça largura no 375pt; o botão parece clicável sem ser.
Output: guardião `web/tests/test_ui_onda_g.mjs` + edições em navStack.js, App.jsx, 7 arquivos de opcoes/ (só atributo), 2 guardiões reconciliados com NOTA DATADA 2026-10-08.

Fora de escopo: motor, dados financeiros, copy.js (texto não muda), persistence.js, modais/sheets (AboutModal, OnboardingModal, AuthModal, WelcomeAuthScreen, TermoOperadorModal, TermoDescobertoModal, BuyModal, SellModal, VigiasSheet), suíte completa, `cap copy ios`, push, publicação. Branch atual `ui/diagnostico-ondas-a-d` (não trocar).
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@./CLAUDE.md
@.planning/quick/261008-1ar-onda-b-ui-voltar-do-sistema-estado-e-scr/261008-1ar-SUMMARY.md
@.planning/quick/261008-1qw-onda-c1-ui-escala-tipografica-sem-meios-/261008-1qw-SUMMARY.md
@.planning/quick/261008-e9w-onda-f-ui-mesa-nao-operar-sem-anel-e-cta/261008-e9w-SUMMARY.md
@web/tests/test_ui_onda_f.mjs (modelo de guardião: helpers `ler`, `ok`, `falhas`, exit code)
@web/tests/test_ui_onda_b.mjs (linhas 56-60: asserção "gesto")

App.jsx (~10.750 linhas) NUNCA inteiro: Grep + Read offset/limit. Números de linha abaixo são do HEAD 0dc57526 e podem deslocar ±; localize sempre pelo trecho citado.

<interfaces>
web/src/navStack.js (linhas 9-11 e 89-92, puro, sem DOM):
  export const BORDA_PX = 20; export const DX_MIN = 60; export const DY_MAX = 40;
  export function ehGestoVoltarBorda({ x0, y0, x1, y1 } = {}) -> x0 <= BORDA_PX && (x1 - x0) > DX_MIN && Math.abs(y1 - y0) < DY_MAX

App.jsx ~10311 (useEffect swipe iOS, onStart):
  if (e.target && e.target.closest && e.target.closest("canvas, [data-sem-gesto-voltar]")) return;

App.jsx 1370: const SP = { 1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24, 8: 32 };   (linha travada byte a byte por test_ritmo_sp — não tocar)
App.jsx 1377/1380: const SP_OPTICO_CHIP_PRIMARIO / const SP_OPTICO_ANEL  (lista fechada de `const SP_OPTICO_*` — não criar outro SP_OPTICO_)
App.jsx 397: const card = { background: T.bgCard, border: `1px solid ${T.borderSubtle}`, borderRadius: "12px" };  (sem padding — padding é por uso)
App.jsx ~10740 (wrapper de conteúdo dentro de <main>):
  <div style={{ maxWidth: CONTENT_MAX_WIDTH, margin: "0 auto", padding: "24px 18px 34px", transform: pullY ? ... }}>
App.jsx ~2386 (hero-carrossel do Resumo, "SETUPS NA SUA WATCHLIST"):
  <div style={carouselTrackStyle({ gap: "12px", scrollSnapType: "x mandatory", margin: "0 -18px", padding: "2px 18px 6px" })}>
App.jsx ~4184 (MercadoScreen, filtro MODELO DE ANÁLISE; a linha imediatamente anterior a `TECH_MODELS.map(`, test_fase22 recorta a partir dela):
  <div style={carouselTrackStyle({ gap: "8px", paddingBottom: "2px" })}>
App.jsx ~5286-5313 (function BlocoBorisIA): const semLivres = qtyLivre(p) === 0; botão:
  onClick={semLivres ? undefined : () => ctx.A.openSell(p.t)}
  aria-disabled={semLivres ? "true" : undefined}
  aria-describedby={semLivres ? idMotivo : undefined}
  style={{ width: "100%", minHeight: 44, borderRadius: "10px", border: `1px solid ${semLivres ? T.borderSubtle : T.negative}`, background: semLivres ? "transparent" : T.negativeTint10, color: semLivres ? T.textSecondary : T.negative, fontSize: TIPO_CARD.corpo, fontWeight: 700 }}
  texto: {cartaoPosicaoTxt(modo, semLivres ? "saida_sem_livres" : "saida")}   (test_copy_theme trava esta expressão)
Convenção de desabilitado já usada (App.jsx ~512): opacity: disabled ? 0.6 : 1, cursor: disabled ? "not-allowed" : "pointer"; T.textFaint existe.

Guardiões que tocam nesta área (achados por grep):
- test_ui_onda_b.mjs:57 `!N.ehGestoVoltarBorda({ x0: 30, y0: 100, x1: 120, y1: 100 })` — com BORDA_PX=32 vira true -> reconciliar.
- test_cartao_v6_aberto.mjs:68 `ok("BlocoBorisIA: sem disabled= na fatia", !/(?<![-\w])disabled=/.test(bloco));` — conflita com o item 3 -> reconciliar.
- test_cartao_v6_aberto.mjs:64/66/67 — plano sem disabled, aria-disabled/aria-describedby/onClick undefined: continuam valendo (não mexer).
- test_fase20_fundacao_visual.mjs:76-80 — exatamente 1 `const CONTENT_MAX_WIDTH = "720px";` e exatamente 2 `maxWidth: CONTENT_MAX_WIDTH`; :59 `<main[^>]*overflowX: "hidden"` (não tocar a linha do <main>).
- test_fase22_componentes_compartilhados.mjs — `carouselTrackStyle` intacto; overflowX solto em App.jsx proibido fora do helper; recorte TECH_MODELS precisa conter `carouselTrackStyle(` (manter na mesma linha).
- test_ritmo_sp.mjs — varre só SinalChip, LinhaContexto, PlanoOperacionalBloco, HistoricoPill, CardPosicaoEstruturada, ReguaFaixa, recorte do AtivoCard e componentes v6 (ReguaPlano…GradeConta). Nenhuma linha editada aqui está nesses escopos; se tocar algum, só `${SP[N]}px`.
- test_opcoes_analisar_ui.mjs:470 `/const ROLAGEM = \{ overflowX: "auto"/` — não mexer na declaração de ROLAGEM.
- Nenhum guardião trava literais de padding de cartão (grep de "17px 18px", "16px 18px", "24px 18px 34px" em web/tests: zero).
</interfaces>
</context>

<decisions>
Decisões do planejador (discricionárias, registradas; ver também "Pendências para o Alex" no fim):
- G-D1 Exclusão de gesto: além de marcar cada trilho horizontal com `data-sem-gesto-voltar`, o seletor do closest vira o SUPERCONJUNTO `canvas, input[type="range"], [data-sem-gesto-voltar]` (mantém a exclusão pedida e cobre os 4 sliders — SimuladorEstudo ~5448, alocação ~6225, PosicaoTotal:136, GraficoResultado:230 — e qualquer slider futuro sem depender de marcação manual). O Ticker do topo é marquee animado sem rolagem do usuário: NÃO marcar.
- G-D2 Gutter: `const GUTTER_X = \`clamp(${SP[3]}px, calc(100vw - 714px), 18px)\`;` — 12px (token SP[3]) até 726px de viewport, 18px (valor histórico) a partir de 732px. Assim tablet/desktop (>720) mantêm exatamente o gutter atual e o max-width 720, como pedido; o 714 é 720 − 6 para a rampa terminar logo acima do max-width. Safe-area: `max(GUTTER_X, env(safe-area-inset-left|right))` (viewport-fit=cover já está no index.html).
- G-D3 Padding lateral de cartão = 16px (SP[4]), não 12. Justificativa: (a) o cartão de posição v6 (CarteiraScreen ~5809/5820) já usa `${SP[4]}px` e os cartões de Opções já usam "16px" — 16 unifica sem tocar ~30 cartões de opcoes/; (b) 12 dentro de gutter 12 cola o texto na borda arredondada (radius 12) e nos sub-blocos aninhados (BlocoBorisIA já tem padding SP[3] interno); (c) 16 é a margem de leitura padrão do iOS. Centralizado em `const CARD_PAD_X = SP[4];` — se o Alex preferir 12, é UMA linha.
- G-D4 Só se REDUZ: cartões com lateral <= 16 (14px 15px do AtivoCard, 14px 16px, 13px 16px, "16px" de Opções) ficam como estão. Vertical não muda (fora de escopo). Modais/sheets ficam fora (são largura de sheet, não da coluna).
- G-D5 Item 3: `disabled={semLivres}` entra (decisão do Alex) mesmo com o guardião antigo proibindo `disabled=` na fatia (aquela escolha mantinha o botão focável para o VoiceOver ler o motivo via aria-describedby). O motivo segue visível logo abaixo e lido na navegação linear; trade-off registrado na NOTA do guardião.
</decisions>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Guardião test_ui_onda_g.mjs (RED)</name>
  <files>web/tests/test_ui_onda_g.mjs</files>
  <behavior>
    Parte 1 — swipe (import dinâmico/estático de ../src/navStack.js, como test_ui_onda_b faz):
    - BORDA_PX === 32 && DX_MIN === 50 && DY_MAX === 60
    - ehGestoVoltarBorda({x0:30,y0:100,x1:85,y1:150}) === true (antes falhava em 3 critérios)
    - ehGestoVoltarBorda({x0:33,y0:100,x1:200,y1:100}) === false (fora da borda)
    - ehGestoVoltarBorda({x0:10,y0:100,x1:60,y1:100}) === false (dx 50 não é > 50) e ({x0:10,…,x1:61}) === true
    - ehGestoVoltarBorda({x0:10,y0:100,x1:120,y1:160}) === false (dy 60 não é < 60)
    - App.jsx contém `e.target.closest("canvas, input[type=\"range\"], [data-sem-gesto-voltar]")`
    - Para App.jsx e cada arquivo de web/src/opcoes/*.jsx: toda LINHA que contém `<div` E (`carouselTrackStyle(` OU `style={trilho}` OU `style={ROLAGEM}` OU `overflowX: "auto"`) contém também `data-sem-gesto-voltar` (logar arquivo:linha de cada violação); e o total de linhas assim é >= 12 (App 2, CuradoriaEstruturas 1, OpcoesScreen 1, OportunidadesOpcoes 2, SecaoAnalisar 2, AnatomiaPerna 1, GraficoResultado 1, PosicaoTotal 1) — total vazio é falha, nunca pass silencioso.
    Parte 2 — largura (App.jsx lido cru; para recortes use slice de `function Nome(` até o próximo `\nfunction `):
    - contém `const GUTTER_X = \`clamp(${SP[3]}px, calc(100vw - 714px), 18px)\`;` e `const CARD_PAD_X = SP[4];`, e o índice de ambas é MAIOR que o índice de `const SP = {` (ordem de avaliação de módulo)
    - não contém mais `padding: "24px 18px 34px"`; o wrapper com `maxWidth: CONTENT_MAX_WIDTH, margin: "0 auto"` contém `paddingLeft: \`max(${GUTTER_X}, env(safe-area-inset-left))\`` e `paddingRight: \`max(${GUTTER_X}, env(safe-area-inset-right))\``, `paddingTop: "24px"`, `paddingBottom: "34px"`
    - `const CONTENT_MAX_WIDTH = "720px";` aparece 1x e `maxWidth: CONTENT_MAX_WIDTH` 2x (paridade com test_fase20)
    - hero-carrossel: a linha com `scrollSnapType: "x mandatory"` contém `margin: \`0 calc(-1 * ${GUTTER_X})\`` e `padding: \`2px ${GUTTER_X} 6px\`` e não contém `-18px`
    - Nos recortes CapitalCurve, EvolucaoScreen, CarteiraScreen, AgenteScreen, NotifSection, SkillSection, PromptsSection, BorisConfigSection, PlanoScreen, AiConfigScreen, LogsDebugScreen, FonteDadosScreen, RadarScreen, OpcaoDescobertoCard, ConfigScreen: nenhum match de `/\.\.\.card[^}]{0,80}padding: "\d+px (\d+)px/` com grupo 1 > 16; cada recorte não vazio (> 200 chars)
    - contagem de `${CARD_PAD_X}px` em App.jsx === 30
    Parte 3 — botão de saída (recorte `function BlocoBorisIA(`):
    - contém `disabled={semLivres}`, `aria-disabled={semLivres ? "true" : undefined}`, `opacity: semLivres ? 0.6 : 1`, `cursor: semLivres ? "not-allowed" : "pointer"`, `color: semLivres ? T.textFaint : T.negative`
    - o `<button` que contém `ctx.A.openSell(p.t)` contém `minHeight: 44` e `onClick={semLivres ? undefined : () => ctx.A.openSell(p.t)}`
    - contém `cartaoPosicaoTxt(modo, semLivres ? "saida_sem_livres" : "saida")` (texto inalterado) e `"saida_motivo_lastro"`
    - o botão de plano (`ctx.openStopAlvo(p.t)`) NÃO tem `disabled` (stop/alvo nunca vetados)
  </behavior>
  <action>Criar web/tests/test_ui_onda_g.mjs seguindo a estrutura de web/tests/test_ui_onda_f.mjs (cabeçalho "// Onda G (2026-10-08) — quick 261008-iuz." com as 3 partes; helpers `ler`, `ok`, contador `falhas`; no fim `if (falhas) { console.error(...); process.exit(1); }` igual ao modelo). Implementar exatamente as asserções do bloco behavior. Para a varredura de opcoes/ usar readdirSync de web/src/opcoes filtrando `.jsx`. Ao checar strings que contêm `${...}`, usar strings JS normais com aspas duplas (ex.: "const CARD_PAD_X = SP[4];", "${CARD_PAD_X}px") para não interpolar. Rodar e confirmar que FALHA (RED) — esperado: todas as partes falham no HEAD. Commit: `test(261008-iuz): guardião test_ui_onda_g (RED)`.</action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2/web && node tests/test_ui_onda_g.mjs; test $? -ne 0 && echo RED-OK</automated>
  </verify>
  <done>Arquivo existe, roda sem erro de sintaxe, sai com código != 0 listando FALHOU nas 3 partes; commit feito.</done>
</task>

<task type="auto">
  <name>Task 2: Swipe tolerante + exclusão de trilhos e sliders (itens 1)</name>
  <files>web/src/navStack.js, web/src/App.jsx, web/src/opcoes/CuradoriaEstruturas.jsx, web/src/opcoes/OpcoesScreen.jsx, web/src/opcoes/OportunidadesOpcoes.jsx, web/src/opcoes/SecaoAnalisar.jsx, web/src/opcoes/AnatomiaPerna.jsx, web/src/opcoes/GraficoResultado.jsx, web/src/opcoes/PosicaoTotal.jsx, web/tests/test_ui_onda_b.mjs</files>
  <action>
(a) navStack.js linhas 9-11: `BORDA_PX = 32`, `DX_MIN = 50`, `DY_MAX = 60`. Acrescentar acima delas um comentário de 2 linhas: "Onda G (2026-10-08, quick 261008-iuz): 20/60/40 falhava no iPhone real (simulador aceitava x=8); ampliado para 32/50/60. Zona maior => trilhos/sliders na borda precisam de exclusão (App.jsx closest)." Não tocar `ehGestoVoltarBorda` (continua pura; test_ui_onda_b "navStack puro" proíbe window/document/history/import).
(b) App.jsx, useEffect do swipe iOS (~10311, onStart): trocar o seletor do closest por `"canvas, input[type=\"range\"], [data-sem-gesto-voltar]"` (G-D1; superconjunto — a exclusão original fica). Comentário de 1 linha acima citando Onda G.
(c) Marcar com o atributo JSX `data-sem-gesto-voltar` (sem valor) cada `<div` de rolagem horizontal, NA MESMA LINHA do `<div`, inserido logo após `<div` (ex.: `<div data-sem-gesto-voltar style={carouselTrackStyle({...})}>`). Lista (confirme com `grep -rn 'carouselTrackStyle(\|style={trilho}\|style={ROLAGEM}\|overflowX: "auto"' web/src | grep '<div'`):
   App.jsx ~2386 hero-carrossel (NÃO mude margin/padding aqui — isso é da Task 3); App.jsx ~4184 trilho TECH_MODELS (manter `carouselTrackStyle(` na mesma linha — test_fase22 recorta essa linha);
   opcoes/CuradoriaEstruturas.jsx:189; opcoes/OpcoesScreen.jsx:1358; opcoes/OportunidadesOpcoes.jsx:105 e :124 (`<div style={trilho}>`); opcoes/SecaoAnalisar.jsx:178 e :214 (`<div style={ROLAGEM}>` — não mexer na declaração `const ROLAGEM` da linha 130, travada por test_opcoes_analisar_ui); opcoes/AnatomiaPerna.jsx:217, opcoes/GraficoResultado.jsx:244, opcoes/PosicaoTotal.jsx:154 (`<div style={{ overflowX: "auto" }}>`).
   As declarações locais `carouselTrackStyle`/objetos com `overflowX: "auto"` (CuradoriaEstruturas:53, OpcoesScreen:170, OportunidadesOpcoes:38, App.jsx:406) NÃO são `<div` — não tocar.
(d) Reconciliar web/tests/test_ui_onda_b.mjs linha 57: trocar `x0: 30` por `x0: 40` e inserir imediatamente acima da linha 56 o comentário: "// NOTA 2026-10-08 (quick 261008-iuz, Onda G): BORDA_PX subiu 20->32, DX_MIN 60->50, DY_MAX 40->60 (gesto falhava no iPhone real). O caso 'fora da borda' passou de x0:30 para x0:40 (30 agora é borda). Demais casos seguem válidos sem mudança." Não apagar nenhuma asserção.
Commit: `fix(261008-iuz): swipe-back de borda tolerante (32/50/60) com trilhos e sliders excluídos`.
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2/web && node tests/test_ui_onda_b.mjs && node tests/test_fase22_componentes_compartilhados.mjs && node tests/test_opcoes_analisar_ui.mjs && node tests/test_ui_onda_g.mjs 2>&1 | grep -E "FALHOU" | grep -ivE "GUTTER|CARD_PAD|24px|safe-area|mandatory|BlocoBorisIA|disabled|opacity|cursor|textFaint|minHeight|CONTENT_MAX|recorte|> 16" ; npx vite build 2>&1 | tail -3</automated>
  </verify>
  <done>test_ui_onda_b, test_fase22 e test_opcoes_analisar_ui passam; parte 1 do test_ui_onda_g passa (nenhum FALHOU de swipe/trilho restante); vite build ok; commit feito.</done>
</task>

<task type="auto">
  <name>Task 3: Largura útil (gutter 12 + cartão 16) e botão de saída desabilitado (itens 2 e 3)</name>
  <files>web/src/App.jsx, web/tests/test_cartao_v6_aberto.mjs</files>
  <action>
(a) Tokens (G-D2/G-D3). Em App.jsx, logo DEPOIS da linha `const SP_OPTICO_ANEL = 36;` (~1380; não criar outro `const SP_OPTICO_*`, não tocar a linha `const SP = {...}`), inserir:
   comentário "Onda G (2026-10-08, quick 261008-iuz): gutter da coluna = SP[3] (12px) no iPhone; rampa até 18px (histórico) a partir de 732px de viewport, então tablet/desktop não mudam. CARD_PAD_X = padding lateral dos cartões das telas principais (16 = margem do cartão v6 e de Opções; trocar para SP[3] aqui se o Alex quiser mais largura)."
   `const GUTTER_X = \`clamp(${SP[3]}px, calc(100vw - 714px), 18px)\`;`
   `const CARD_PAD_X = SP[4];`
(b) Wrapper de conteúdo (~10740): substituir `padding: "24px 18px 34px"` por `paddingTop: "24px", paddingRight: \`max(${GUTTER_X}, env(safe-area-inset-right))\`, paddingBottom: "34px", paddingLeft: \`max(${GUTTER_X}, env(safe-area-inset-left))\``. Não tocar `maxWidth: CONTENT_MAX_WIDTH`, `margin: "0 auto"`, transform/transition, nem a linha do `<main>` (test_fase20 regex `<main[^>]*overflowX`).
(c) Hero-carrossel (~2386, linha com `scrollSnapType: "x mandatory"`): `margin: "0 -18px"` -> `margin: \`0 calc(-1 * ${GUTTER_X})\``; `padding: "2px 18px 6px"` -> `padding: \`2px ${GUTTER_X} 6px\``. Mantém o `data-sem-gesto-voltar` da Task 2.
(d) Padding lateral dos cartões (G-D4: só reduzir; só vertical literal preservado). Nas 30 ocorrências abaixo de `...card` com `padding: "<old>"`, trocar a componente HORIZONTAL por `${CARD_PAD_X}px` (template literal com crase). Recomendado: script node descartável em $TMPDIR que, para cada (linha, old, new), ASSERTA que a linha contém `...card` e `padding: "<old>"` e aborta sem gravar se qualquer uma não bater (linhas podem ter deslocado após a Task 2 — se deslocou, localize por componente+old via grep e ajuste a lista; nunca substituição global por regex). Mapa (linha HEAD, componente, old -> new):
   2190 CapitalCurve "18px 18px 14px" -> `18px ${CARD_PAD_X}px 14px`
   2408 EvolucaoScreen "20px 18px" -> `20px ${CARD_PAD_X}px`
   2421, 2448, 2479, 2488, 2495 EvolucaoScreen "16px 18px" -> `16px ${CARD_PAD_X}px`
   5718 CarteiraScreen "16px 18px" -> `16px ${CARD_PAD_X}px`
   6038 AgenteScreen "18px 17px" -> `18px ${CARD_PAD_X}px`
   6088, 6196, 6241 AgenteScreen "16px 17px" -> `16px ${CARD_PAD_X}px`
   6454 NotifSection, 6587 SkillSection, 6626 PromptsSection, 6690 BorisConfigSection, 6785 PlanoScreen, 6836 AiConfigScreen "17px 18px" -> `17px ${CARD_PAD_X}px`
   7443, 7458 LogsDebugScreen, 7740, 7759 FonteDadosScreen "17px 18px" -> `17px ${CARD_PAD_X}px`
   8160 RadarScreen (Mesa) "18px 20px" -> `18px ${CARD_PAD_X}px`
   8168, 8176 RadarScreen "16px 18px" -> `16px ${CARD_PAD_X}px`
   8509 OpcaoDescobertoCard, 8540, 8560, 8575, 8615 ConfigScreen "17px 18px" -> `17px ${CARD_PAD_X}px`
   Total = 30 (o guardião conta exatamente 30 `${CARD_PAD_X}px`). NÃO tocar: modais/sheets (linhas 600, 629, 795, 874, 2652, 2718, 2921, 8783, 8878, 10702), AtivoCard 3755 "14px 15px", MercadoScreen 4175 "12px", nenhum "14px 16px"/"13px 16px"/"15px 16px"/"12px 14px", CartaoPosicao (já `${SP[4]}px`), nada em web/src/opcoes (cartões de Opções já são "16px" — conforme G-D3). Não mexer em fontSize (só inteiros, test_ui_onda_c1) nem em minHeight.
(e) Botão de saída em `function BlocoBorisIA` (~5303-5313), item 3 / G-D5: acrescentar o atributo `disabled={semLivres}` (entre `type="button"` e `onClick`); manter `onClick={semLivres ? undefined : () => ctx.A.openSell(p.t)}`, `aria-disabled={semLivres ? "true" : undefined}`, `aria-describedby` e o texto. No style: `color: semLivres ? T.textSecondary : T.negative` -> `color: semLivres ? T.textFaint : T.negative`; acrescentar `opacity: semLivres ? 0.6 : 1, cursor: semLivres ? "not-allowed" : "pointer"` ao final do objeto. `minHeight: 44` intacto. Não tocar o botão de plano (openStopAlvo) nem o de reanalisar.
(f) Reconciliar web/tests/test_cartao_v6_aberto.mjs linha 68 (sem apagar a asserção): substituir por `ok("BlocoBorisIA: único disabled= da fatia é o da saída (disabled={semLivres})", (bloco.match(/(?<![-\w])disabled=/g) || []).length === 1 && bloco.includes("disabled={semLivres}"));` precedido do comentário "// NOTA 2026-10-08 (quick 261008-iuz, Onda G): o Alex decidiu que a saída com 0 ações livres é disabled de fato (antes só aria-disabled, para manter foco e o VoiceOver ler o motivo). O motivo segue visível logo abaixo e aria-describedby fica. A asserção passa a exigir exatamente UM disabled= (o da saída); plano/stop-alvo continua sem disabled (linha 64)."
Commit: `fix(261008-iuz): gutter 12px no iPhone, cartões com lateral 16px e saída sem livres desabilitada`.
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2/web && npx vite build 2>&1 | tail -3 && for t in test_ui_onda_g test_ui_onda_a test_ui_onda_b test_ui_onda_c1 test_ui_onda_e test_ui_onda_f test_ritmo_sp test_cartao_v6_transversal test_cartao_v6_aberto test_fase20_fundacao_visual test_fase22_componentes_compartilhados test_copy_theme test_opcoes_analisar_ui; do node tests/$t.mjs >/dev/null 2>&1 && echo "PASS $t" || echo "FAIL $t"; done; grep -c '\${CARD_PAD_X}px' src/App.jsx; grep -c '@media (prefers-reduced-motion: reduce){' src/App.jsx</automated>
  </verify>
  <done>vite build ok; todos os 13 guardiões listados imprimem PASS; contagem de `${CARD_PAD_X}px` = 30; contagem de `@media (prefers-reduced-motion: reduce){` em App.jsx = 2 (igual ao HEAD); `git diff --stat` mostra só os arquivos de files_modified; commit feito.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| toque do usuário -> history.back() | gesto de borda dispara navegação local; nenhum dado financeiro ou ordem cruza esta fronteira |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-iuz-01 | Tampering (ação não intencional) | swipe de borda ampliado (App.jsx useEffect iOS) | mitigate | seletor `canvas, input[type="range"], [data-sem-gesto-voltar]` + marcação de todo trilho horizontal; guardião test_ui_onda_g varre App.jsx e opcoes/*.jsx e reprova `<div` rolável sem o atributo |
| T-iuz-02 | Elevation (ação sem pré-condição) | botão "Registrar saída" com 0 livres (BlocoBorisIA) | mitigate | `disabled` nativo + `onClick` undefined (duas barreiras); motor (store.sell/qtyLivre) não é tocado e segue rejeitando venda de lastro |
| T-iuz-03 | Information disclosure | mudanças só de layout | accept | sem dado novo, sem rede, sem segredo |
</threat_model>

<verification>
- `cd web && npx vite build` sem erro.
- Guardiões: test_ui_onda_g, test_ui_onda_a, test_ui_onda_b, test_ui_onda_c1, test_ui_onda_e, test_ui_onda_f, test_ritmo_sp, test_cartao_v6_transversal, test_cartao_v6_aberto, test_fase20_fundacao_visual, test_fase22_componentes_compartilhados, test_copy_theme, test_opcoes_analisar_ui — todos PASS.
- Conta de largura (documentar no SUMMARY): 375pt -> container 351px = 93,6% (antes 339 = 90,4%); 430pt -> 406 = 94,4% (antes 394 = 91,6%). Área de texto dentro do cartão (borda 1 + CARD_PAD_X 16 por lado): 375 -> 317 = 84,5% (antes 301 = 80,3%); 430 -> 372 = 86,5% (antes 356 = 82,8%).
- NÃO rodar a suíte completa, NÃO `npx cap copy ios`, NÃO push, NÃO publicar. Não editar STATE.md com mutadores do gsd-sdk.
- Validação manual sugerida no SUMMARY (para o Alex, no aparelho): swipe a partir de ~25pt da borda em Carteira->posição volta; arrastar o carrossel "SETUPS NA SUA WATCHLIST" a partir da borda rola sem voltar; slider do simulador idem; posição com toda a quantidade em lastro mostra o botão de saída esmaecido e inerte.
</verification>

<success_criteria>
- Constantes 32/50/60 em navStack.js; ehGestoVoltarBorda pura; exclusão original preservada como subconjunto.
- 12 `<div` de rolagem horizontal marcados com `data-sem-gesto-voltar`; sliders excluídos pelo seletor.
- Gutter 12px (SP[3]) no iPhone, 18px a partir de 732px, max-width 720 intacto, safe-area respeitada; hero-carrossel sangra exatamente o gutter.
- 30 cartões das telas principais com lateral `${CARD_PAD_X}px` (16); modais e Opções intocados.
- Botão de saída com 0 livres: disabled + aria-disabled + opacity 0.6 + not-allowed + T.textFaint, texto e minHeight 44 inalterados.
- Guardiões antigos reconciliados só com NOTA DATADA 2026-10-08 (test_ui_onda_b:57, test_cartao_v6_aberto:68), nenhuma asserção apagada.
</success_criteria>

<output>
Criar `.planning/quick/261008-iuz-onda-g-ui-swipe-tolerante-mais-largura-u/261008-iuz-SUMMARY.md` com: o que mudou, arquivos, guardiões rodados e resultado, a conta de largura acima, decisões G-D1..G-D5 e as pendências abaixo.
</output>

## Pendências para o Alex (não bloqueiam a execução)

1. Métrica dos 92%: atingida para o container de conteúdo (93,6–94,4%). Para o TEXTO dentro do cartão, 92% em 375pt exigiria <= 15px de cromo por lado somando gutter + borda + padding — inviável sem colar texto na borda. Entregue: 80,3% -> 84,5%. Se quiser mais, `CARD_PAD_X = SP[3]` (uma linha) leva a 86,7% — o guardião de contagem continua válido.
2. Saída com 0 livres agora é `disabled` nativo: sai da ordem de foco do VoiceOver (antes era focável e lia o motivo via aria-describedby). O motivo segue visível e lido na leitura linear. Confirmar que o trade-off de a11y é aceitável.
3. Rampa do gutter (12px até 726px, 18px a partir de 732px): faixa 721–731px tem gutter intermediário; nenhum dispositivo real relevante cai aí.
