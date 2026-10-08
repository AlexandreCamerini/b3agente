---
phase: quick-261008-oos
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - web/tests/test_ui_onda_h.mjs
  - web/src/opcoes/payoffEixos.js
  - web/src/opcoes/PayoffPrimitivas.jsx
  - web/src/opcoes/GraficoResultado.jsx
  - web/src/opcoes/GraficoAnatomia.jsx
  - web/src/opcoes/PosicaoTotal.jsx
  - web/src/opcoes/AnatomiaPerna.jsx
  - web/src/App.jsx
  - web/src/copy.js
  - server/app/skill_ref.py
autonomous: true
requirements: [ONDA-H-UI]

must_haves:
  truths:
    - "Os três gráficos de payoff que aparecem nos screenshots (GraficoResultado da escada, GraficoAnatomia/PosicaoTotal da posição em Opções, PayoffOperador do card da carteira) têm eixo Y com até 3 ticks (máx/zero/mín) em R$ compacto, com rótulos inteiros dentro de uma coluna esquerda dimensionada pelo maior rótulo, e a linha do zero rotulada 'R$ 0'"
    - "Os três têm eixo X com 3 ticks (início/meio/fim) em fonte >= 11px reais"
    - "Nenhum marcador vertical (strike, PM, BE, hoje) escreve texto sobre a área do gráfico: cada um vira um círculo numerado no topo da sua linha; dois círculos a < 22px em X vão para linhas diferentes (nunca se sobrepõem) e a legenda abaixo do gráfico lista uma linha por marcador"
    - "A área plotada tem >= 220px de altura real em 375pt e usa a largura total do container (sem scroll horizontal)"
    - "Chips de perna mostram estado explícito (ligado = preenchido, desligado = contorno apagado), cabem em no máximo 2 linhas com até 6 itens, e a linha do total é cheia e mais grossa enquanto as pernas são finas e tracejadas (nenhuma perna em traço cheio)"
    - "A legenda da escada diz cada conceito uma vez só (fim de 'equilíbrio R$ 0,00 Equilíbrio R$ 22,69: …')"
    - "Nenhum número financeiro novo é calculado: ticks são geometria/formatação; null vira travessão; ausência de teto/piso declarada nunca vira tick de extremo"
  artifacts:
    - path: "web/tests/test_ui_onda_h.mjs"
      provides: "Guardião da Onda H (funções puras + varredura estática + SSR do GraficoAnatomia)"
    - path: "web/src/opcoes/payoffEixos.js"
      provides: "Geometria pura comum: rotuloEixoBRL, margemEsquerda, ticksY, ticksX, empilharMarcadores, alturaTopo, afastarPontos, montarGeometria + constantes"
      exports: ["FONTE_EIXO", "PLOT_H", "PLOT_H_COMPACTO", "MARC_R", "MARC_DIST", "MARC_LINHA_H", "MB_EIXO", "MR_EIXO", "rotuloEixoBRL", "margemEsquerda", "ticksY", "ticksX", "empilharMarcadores", "alturaTopo", "afastarPontos", "montarGeometria"]
    - path: "web/src/opcoes/PayoffPrimitivas.jsx"
      provides: "Primitivas visuais comuns: useLarguraMedida, EixoY, EixoX, MarcadoresVerticais, BadgeNumero, LegendaMarcadores"
      exports: ["useLarguraMedida", "EixoY", "EixoX", "MarcadoresVerticais", "BadgeNumero", "LegendaMarcadores"]
  key_links:
    - from: "web/src/opcoes/GraficoResultado.jsx"
      to: "web/src/opcoes/payoffEixos.js + PayoffPrimitivas.jsx"
      via: "montarGeometria + <EixoY/<EixoX/<MarcadoresVerticais"
      pattern: "montarGeometria\\("
    - from: "web/src/opcoes/GraficoAnatomia.jsx"
      to: "web/src/opcoes/payoffEixos.js + PayoffPrimitivas.jsx"
      via: "montarGeometria + <LegendaMarcadores"
      pattern: "<LegendaMarcadores"
    - from: "web/src/App.jsx (PayoffOperador)"
      to: "web/src/opcoes/payoffEixos.js + PayoffPrimitivas.jsx"
      via: "import { montarGeometria } / { LegendaMarcadores, useLarguraMedida }"
      pattern: "from \"\\./opcoes/payoffEixos\\.js\""
---

<objective>
Onda H de UI: tornar legíveis no iPhone os gráficos de payoff de opções, com UMA linguagem visual comum (eixo Y com 3 ticks em coluna dimensionada, eixo X com 3 ticks, marcadores verticais numerados com anti-colisão e legenda abaixo, chips de série com estado explícito, área plotada >= 220px), sem tocar em nenhum número do motor.

Purpose: os três screenshots do Alex mostram rótulos colidindo ("226,865", "K 53,67/54,17/55,17" sobrepostos), eixo Y cortado ("-4.998") ou ausente (card), chips dourados todos parecendo ligados e um gráfico de 720 de viewBox encolhido para ~5px de fonte. Princípio 5 do CLAUDE.md: o front só desenha.

Output: guardião `test_ui_onda_h.mjs`; módulo puro `payoffEixos.js`; primitivas `PayoffPrimitivas.jsx`; GraficoResultado, GraficoAnatomia (+PosicaoTotal/AnatomiaPerna) e PayoffOperador (App.jsx) migrados; templates de legenda sem redundância (copy.js ↔ skill_ref.py, byte a byte).

## Premissas e correção de escopo (leia antes de tudo)

- **Correção de rótulo do screenshot 2.** O orquestrador chamou de `PayoffChart` o gráfico "Posição em PETR4 / Payoff no vencimento (09/10)" com os 4 chips dourados. Ele é `PosicaoTotal.jsx` → `GraficoAnatomia.jsx` (os chips são o `Chip` de PosicaoTotal; a hachura, o slider "hipótese, não previsão" e "Ver em tabela" são de lá). A causa da fonte minúscula é `W = 720` no viewBox (não compacto) encolhido para ~317px → escala 0,44 → fonte 12 vira ~5px.
- **Corte feito (H2):** `web/src/opcoes/PayoffChart.jsx` NÃO entra nesta onda. Não aparece em nenhum screenshot, já tem eixo Y de 3 ticks com coluna (PAD_E=48) e supressão de colisão, e migrá-lo exige reconciliar as asserções 6 e 8 de `test_payoff_responsivo.mjs` (bloco `tipoMarca: "breakeven"` + `mostrarTexto ? (`). Em troca, GraficoAnatomia (que o orquestrador mandaria cortar) entra, porque é o gráfico do screenshot 2. Escopo final: GraficoResultado (screenshot 1), GraficoAnatomia/PosicaoTotal (screenshot 2), PayoffOperador (screenshot 3).
- **Medição em px reais.** Os SVGs passam a medir a própria largura (`useLarguraMedida`, ResizeObserver, mesmo padrão de `GradeConta` em App.jsx) e usam `viewBox="0 0 {largura} {altura}"` com largura medida — assim fonte 12 no SVG = 12px na tela e PLOT_H=244 = 244px, independente de quanto padding o container tenha. Fallback sem ResizeObserver (SSR/testes): largura 340.
- Nada de `cap copy ios`, suíte completa, push, publicação ou troca de branch (`ui/diagnostico-ondas-a-d`).
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@./CLAUDE.md
@.claude/skills/didatica-boris/SKILL.md
@.planning/quick/261008-iuz-onda-g-ui-swipe-tolerante-mais-largura-u/261008-iuz-SUMMARY.md
@web/src/opcoes/GraficoResultado.jsx
@web/src/opcoes/GraficoAnatomia.jsx
@web/src/opcoes/PosicaoTotal.jsx
@web/src/opcoes/fluxoEstilo.js

Evidência visual (Read nas imagens):
- /Users/acamerini/.claude/uploads/737e58a8-6131-40ca-8e4e-9a34026f925d/dfe8c825-image.png (GraficoResultado)
- /Users/acamerini/.claude/uploads/737e58a8-6131-40ca-8e4e-9a34026f925d/a29db3c0-image.png (PosicaoTotal/GraficoAnatomia — NÃO é PayoffChart)
- /Users/acamerini/.claude/uploads/737e58a8-6131-40ca-8e4e-9a34026f925d/98c88df5-image.png (PayoffOperador, App.jsx)

App.jsx (~10.700 linhas): NUNCA ler inteiro. `PayoffOperador` começa em `function PayoffOperador({ e, modo })` (~linha 5523, Grep para achar) e termina antes de `function GradeConta(`. Imports de React na linha 1. `SP = { 1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24, 8: 32 }` (~1370). `TIPO_CARD = { titulo: "20px", corpo: "14px", rotulo: "12px", ... }` (~4827). `MONO` em App é string de font-family (usado como `fontFamily: MONO`). `price(v)` é o formatador de preço do card.

<interfaces>
Payload do card (server/app/cartao_posicao.py:389, só leitura):
  e.cenarios = { vencimentoTexto, be, k, hoje, payoff: { pontos: [{preco, resultado}], xMin, xMax, yMin, yMax, aria }, grade }
  (yMin/yMax = min/max reais de resultado na janela; k == null => estrutura sem teto, mesma regra do aria "payoff_aria_sem_teto")

GraficoResultado (degrau.grafico do backend, opcoes_escada.py:472):
  g = { xMin, xMax, hoje, precoMedio, y, pontos: [{preco, soAcoes:{total,porAcao}, comEstrutura:{total,porAcao}, efeito, diferenca}],
        marcadores: [{n (1..5 FIXO), chave, preco, y, valor:{total,porAcao}}],
        legenda: [{n, chave, rotulo, setor, kb, valor:{total,porAcao}, frase}], ausentes: [{n, chave, texto}], tabela, aria:{total,porAcao} }
  chaves: piso(1) equilibrio(2) teto(3) perda_maxima(4) ganho_maximo(5). ausentes possíveis: piso, teto, ganho_maximo.

GraficoAnatomia props (inalteradas): { precos, series:[{id, valores, traco, tipo?, apagada?, destaque?}], area, marcadores:[{preco, rotulo, comPreco?}], cursorIdx, titulo, descricao, compacto }
  export const TRACOS (consumido por PosicaoTotal.Amostra)

fluxoEstilo.js: T (var(--x) de bgBase,bgPanel,borderSubtle,textPrimary,textSecondary,textMuted,textFaint,accent,accentTint10,positive,negative,warn,onAccent), TIPO.label {12px,700}, TIPO.corpo {14px}, MONO {fontFamily, tabular-nums}, ALVO_MIN=44, FOCO.

Contrato NOVO de payoffEixos.js (puro, sem React, sem import de App.jsx):
  FONTE_EIXO = 12; PLOT_H = 244; PLOT_H_COMPACTO = 132; MARC_R = 9; MARC_DIST = 22; MARC_LINHA_H = 22; MB_EIXO = 22; MR_EIXO = 12; PAD_INT = 8
  rotuloEixoBRL(v) -> string
  margemEsquerda(rotulos: string[], fonte = FONTE_EIXO) -> Math.ceil(maiorComprimento * fonte * 0.62) + 8
  ticksY({ yMin, yMax, sy, semTeto, semPiso }) -> [{chave:"max"|"zero"|"min", valor, rotulo, y}]
  ticksX(x0, x1) -> [{valor, ancora:"start"|"middle"|"end"}] (3 itens) ou []
  empilharMarcadores(itens:[{preco, rotulo, n?, comPreco?}], sx, { xMin, xMax, dist = MARC_DIST }) -> { itens:[{...item, n, x, cx, linha}], linhas }
  alturaTopo(linhas) -> 6 + Math.max(1, linhas) * MARC_LINHA_H
  afastarPontos(pts:[{x,y}], dist = 20) -> [{x, y, dy}]
  montarGeometria({ largura, x0, x1, yMin, yMax, marcadores, compacto, semTeto, semPiso }) ->
    { W, H, ML, MR, topo, plotH, sx, sy, yZero, ticksY, ticksX, marcadores, linhas }
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Guardião RED test_ui_onda_h.mjs</name>
  <files>web/tests/test_ui_onda_h.mjs</files>
  <behavior>
    Parte A — módulo puro (import dinâmico de ../src/opcoes/payoffEixos.js dentro de try/catch; se faltar, registra UMA falha "payoffEixos.js ausente" e pula a parte A sem derrubar o processo):
    - rotuloEixoBRL: 0 -> "R$ 0"; 841 -> "R$ 841"; -4998 -> "−R$ 4.998" (sinal U+2212 antes de "R$"); 0.83 -> "R$ 0,83"; -22.5 -> "−R$ 22,50"; 150000 -> "R$ 150 mil"; 1234567 -> "R$ 1,23 mi"; null, undefined, NaN -> "—".
    - margemEsquerda(["R$ 841","R$ 0","−R$ 4.998"], 12) === 75; margemEsquerda maior para rótulo maior (monotônica); margemEsquerda([], 12) === 8.
    - ticksY com sy linear (sy = v => 100 - v/50): yMin -4998, yMax 841 -> chaves ["max","zero","min"] e rotulo do zero "R$ 0"; semTeto:true -> sem "max"; semPiso:true -> sem "min"; yMax 0 -> sem "max"; yMin 5 -> sem "min"; extremo cujo |y - yZero| < FONTE_EIXO + 2 é suprimido (o zero sempre fica).
    - ticksX(45.35, 63.8) -> valores [45.35, 54.575, 63.8] (tolerância 1e-9) e âncoras start/middle/end; ticksX(null, 5) -> [].
    - empilharMarcadores com sx = p => p (identidade), xMin 0, xMax 400: preços [200,100,110] -> n por ordem de preço (100->1, 110->2, 200->3), linhas [0,1,0] respectivamente, linhas === 2; preços [100,105,110,115] -> 4 linhas distintas; para TODO par na mesma linha |cx_a - cx_b| >= 22 (varredura em 30 conjuntos pseudo-aleatórios com semente fixa); item com preco null é descartado; cx fica dentro de [xMin + MARC_R, xMax - MARC_R]; item com n inteiro preserva o n recebido.
    - alturaTopo(0) === 28, alturaTopo(1) === 28, alturaTopo(3) === 72.
    - afastarPontos([{x:100,y:100},{x:105,y:102}]) -> segundo com dy === -20; pontos distantes -> dy 0.
    - montarGeometria({largura:317, x0:45, x1:64, yMin:-4998, yMax:841, marcadores:[3 próximos]}) -> plotH >= 220, W === 317, ML === margemEsquerda dos rótulos dos ticks, H === topo + plotH + MB_EIXO, sx(45) === ML, sx(64) === W - MR; compacto:true -> plotH === PLOT_H_COMPACTO.
    - Constantes: FONTE_EIXO inteiro >= 11; PLOT_H >= 220; MARC_DIST === 22; MARC_R === 9.
    Parte B — varredura estática (sem comentários, mesma função semComentario de test_payoff_responsivo):
    - PayoffPrimitivas.jsx existe e exporta useLarguraMedida, EixoY, EixoX, MarcadoresVerticais, BadgeNumero, LegendaMarcadores; não contém /(?:fill|stroke)=\{T\./ nem transition/animation; importa de "./payoffEixos.js".
    - GraficoResultado.jsx: importa de "./PayoffPrimitivas.jsx" e "./payoffEixos.js"; usa montarGeometria(, <EixoY, <EixoX, <MarcadoresVerticais; NÃO tem `<text` contendo linha_preco_medio (texto do PM sobre o plot); NÃO tem o padrão /R\$ \{fmt\(v\)\}[\s\S]{0,300}it\.frase/ (redundância valor+frase); mantém `OPACIDADE = 0.2` com exatamente 2 `fillOpacity={OPACIDADE}`, `aria-label={ariaTxt}`, `<details`, `type="range"`.
    - GraficoAnatomia.jsx: usa montarGeometria( e <LegendaMarcadores; nenhum `{m.rotulo}` dentro de `<text`; TRACOS não contém "" (nenhuma perna em traço cheio); não há `W = compacto ? 340 : 720` (viewBox fixo de 720).
    - PosicaoTotal.jsx: Chip ligado usa `background: ligado ? T.accentTint10` e desligado usa `T.textMuted`; não há mais `2px solid ${T.accent}`; chips num grid de 3 colunas (`repeat(3, minmax(0, 1fr))`); `minHeight: ALVO_MIN` mantido.
    - App.jsx, recorte de `function PayoffOperador(` até `\nfunction GradeConta(`: importa (no topo do App) de "./opcoes/payoffEixos.js" e "./opcoes/PayoffPrimitivas.jsx"; o recorte usa montarGeometria(, useLarguraMedida(, <LegendaMarcadores; não contém "140px"; não contém /(?:fill|stroke)=\{T\./; mantém `<svg role="img" aria-label={pf.aria}` e zero `<text`.
    - copy.js e skill_ref.py: leg_hoje/leg_be/leg_k sem "┆" e sem "◆" (as 4 ocorrências de cada arquivo); legenda_equilibrio/legenda_piso/legenda_teto começam com "R$ {preco}" (2 modos, 2 arquivos); legenda_perda_maxima/legenda_ganho_maximo não contêm "{valor}" (2 modos, 2 arquivos).
    Parte C — SSR (register("./_jsx_loader.mjs", import.meta.url), padrão de test_opcoes_anatomia_render.mjs) de GraficoAnatomia com precos [44,46,48,50,52], area/serie [1,2,-3,2,4] e marcadores [{preco:48.0,rotulo:"K 48"},{preco:48.2,rotulo:"PM",comPreco:true},{preco:49,rotulo:"hoje",comPreco:true}]: o trecho entre `<svg` e `</svg>` NÃO contém "K 48"; a saída contém `<ol` com "K 48" e "PM"; contém 3 círculos de marcador numerados (texto "1","2","3" em `<text` dentro do svg); todo `font-size` dentro do svg é >= 11.
    Sanidade: cada regex nova ganha uma asserção-irmã provando que pega o caso ruim (ex.: a regex de redundância casa com `R$ {fmt(v)}</span> ... {it.frase}`).
  </behavior>
  <action>Criar web/tests/test_ui_onda_h.mjs no padrão dos guardiões da casa (cabeçalho "Onda H (2026-10-08) — quick 261008-oos" explicando o que cada parte tranca; `ok(nome, cond)` com contagem; `process.exit(falhas ? 1 : 0)`; leitura por readFileSync relativa a import.meta.url; roda com `node web/tests/test_ui_onda_h.mjs` da raiz). Implementar exatamente as asserções do bloco behavior; nada de asserção "por vacuidade" — cada regex tem a sanidade. Rodar e confirmar que FALHA (RED) por ausência dos módulos/mudanças; registrar o número de falhas na mensagem do commit `test(261008-oos): guardião test_ui_onda_h (RED)`.</action>
  <verify>
    <automated>node web/tests/test_ui_onda_h.mjs; test $? -ne 0 && echo RED-OK</automated>
  </verify>
  <done>Arquivo existe, executa sem exceção não tratada, sai com código 1 listando as falhas esperadas; commit RED feito.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Primitivas comuns (payoffEixos.js + PayoffPrimitivas.jsx) e GraficoResultado migrado</name>
  <files>web/src/opcoes/payoffEixos.js, web/src/opcoes/PayoffPrimitivas.jsx, web/src/opcoes/GraficoResultado.jsx</files>
  <behavior>
    - Parte A inteira de test_ui_onda_h passa; parte B de PayoffPrimitivas e GraficoResultado passa.
    - test_opcoes_caminho_b_ui, test_opcoes_jornada_ui, test_opcoes_nav_tres_abas_ui, test_ui_onda_c1, test_ui_onda_a seguem verdes.
  </behavior>
  <action>
    (a) payoffEixos.js — módulo PURO (zero React, zero import de App.jsx, zero leitura de tema), cabeçalho dizendo que é geometria/formatação de eixo e nunca resultado financeiro (princípio 5). Implementar o contrato da seção interfaces. Regras:
    rotuloEixoBRL: não-número finito -> "—"; 0 -> "R$ 0"; sinal negativo vira prefixo "−" (U+2212) antes de "R$ "; |v| < 100 -> 2 casas com vírgula ("0,83"); 100 <= |v| < 100000 -> inteiro arredondado com ponto de milhar pt-BR ("4.998"); 100000 <= |v| < 1e6 -> inteiro de milhares + " mil"; >= 1e6 -> 2 casas de milhões + " mi" ("1,23 mi"). Formatação com toLocaleString("pt-BR") — sem "|| 0"/"?? 0".
    ticksY: sempre inclui {chave:"zero", valor:0, rotulo:"R$ 0", y: sy(0)}; inclui "max" só se yMax > 0 e !semTeto e |sy(yMax) - sy(0)| >= FONTE_EIXO + 2; "min" só se yMin < 0 e !semPiso e mesma folga; ordem max, zero, min.
    ticksX: 3 itens (x0, média de x0 e x1, x1) com âncoras start/middle/end; qualquer extremo não-numérico -> [].
    empilharMarcadores: descarta preco não numérico; ordena por preço (estável); n = item.n se inteiro, senão posição 1-based; x = sx(preco); cx = x limitado a [xMin + MARC_R, xMax - MARC_R]; linha = primeira linha cujo último cx dista >= dist, senão abre linha nova (sem teto de linhas: nunca sobrepõe); retorna { itens, linhas } (linhas = 0 quando vazio).
    montarGeometria: força o domínio Y a conter 0 (yLo = min(yMin, 0), yHi = max(yMax, 0); yLo === yHi -> ±1) só para a ESCALA; os ticks usam yMin/yMax recebidos. Ordem: rótulos dos ticks candidatos (rotuloEixoBRL de yMax/0/yMin) -> ML = margemEsquerda -> MR = MR_EIXO -> sx linear [x0,x1] -> [ML, W - MR] -> empilharMarcadores com xMin ML, xMax W - MR -> topo = alturaTopo(linhas) -> plotH = compacto ? PLOT_H_COMPACTO : PLOT_H -> sy linear [yHi,yLo] -> [topo + PAD_INT, topo + plotH - PAD_INT] -> ticksY com essa sy -> ticksX com x = sx(valor) -> H = topo + plotH + MB_EIXO. W = largura (fallback 340 se não-número ou <= 0).
    (b) PayoffPrimitivas.jsx — componentes de desenho comuns; cores SEMPRE via style (nunca `fill={T.x}`/`stroke={T.x}` em atributo — trava de test_chart_colors_theme_aware), tokens de ./fluxoEstilo.js, sem transition/animation (Reduce Motion), fontSize só inteiro (test_ui_onda_c1).
    useLarguraMedida(ref, inicial = 340): useState(inicial) + useEffect com ResizeObserver (guard `typeof ResizeObserver === "undefined"`), atualiza com Math.round(el.clientWidth) quando > 0, desconecta no cleanup. Usar useEffect (não useLayoutEffect: os testes fazem SSR).
    EixoY({ geo }): `<g aria-hidden="true">` com, por tick, linha de 4px (de geo.ML - 4 a geo.ML) e `<text>` com textAnchor "end" em x = geo.ML - 6, dominantBaseline "central", style { fontSize: FONTE_EIXO + "px", fontFamily: MONO.fontFamily, fill: T.textSecondary }; a linha do zero atravessa o plot (geo.ML até geo.W - geo.MR) com style stroke T.textMuted, strokeWidth 1. Props opcionais semTeto/semPiso desenham "↑"/"↓" (aria-hidden, fontSize 14, style fill T.textSecondary) na coluna do eixo no topo/base do plot.
    EixoX({ geo }): 3 `<text>` em y = geo.H - 6 com as âncoras do tick, mesmo estilo de fonte, conteúdo via prop formatar (preço com 2 casas pt-BR).
    MarcadoresVerticais({ geo }): `<g aria-hidden="true">`; por marcador: linha tracejada ("3 3", style stroke T.textSecondary, strokeWidth 1) de cy + MARC_R até geo.topo + geo.plotH, na posição x REAL; se cx != x, uma perna curta de cx a x; círculo r=MARC_R em (cx, 4 + MARC_R + linha * MARC_LINHA_H) com style fill T.accent; número em `<text>` centralizado, fontSize 12, fontWeight 700, style fill T.onAccent.
    BadgeNumero({ n }): span aria-hidden 20px de diâmetro, background T.accent, color T.onAccent, TIPO.label, inline-flex centralizado.
    LegendaMarcadores({ itens, formatarPreco }): `<ol>` sem estilo de lista, coluna, gap 4px; um `<li>` por item: BadgeNumero + rótulo (color T.textPrimary) + quando item.comPreco for true, " " + formatarPreco(item.preco) em MONO; TIPO.corpo, color T.textSecondary. Itens vazios -> null.
    (c) GraficoResultado.jsx — trocar W/H fixos por largura medida: ref num div wrapper do svg + useLarguraMedida(ref, 340) declarados ANTES do early return (regra dos hooks). Escala Y continua sendo min/max dos valores plotados + 0 (geometria). Marcadores verticais = só o PM: se ehNum(g.precoMedio), um item { preco: g.precoMedio, rotulo: tx("linha_preco_medio"), n: 6, comPreco: true } (6 = depois da numeração FIXA 1-5 do backend — decisão H-D4). semTeto = ausentes tem chave "ganho_maximo"; semPiso = ausentes tem chave "piso" E não existe marcador perda_maxima. Chamar montarGeometria({ largura, x0: g.xMin, x1: g.xMax, yMin, yMax, marcadores, semTeto, semPiso }) e desenhar com <EixoY/<EixoX/<MarcadoresVerticais; remover o `<text>` "R$ 0" solto, o `<text>` do PM e os dois `<text>` de xMin/xMax. Clip-paths e área (OPACIDADE 0.2 nas DUAS, exatamente 2 `fillOpacity={OPACIDADE}`) mantidos, mas com ids únicos via useId (dois gráficos na mesma tela não podem compartilhar `opc-clip-pos`). Séries: desenhar PRIMEIRO comEstrutura (traço cheio, strokeWidth 3, style stroke T.accent) e POR CIMA soAcoes (strokeWidth 1.5, strokeDasharray "6 4", style stroke T.textSecondary) — a tracejada fica visível sobre a cheia onde coincidem. Marcadores do backend sobre a curva (n 1-5) continuam círculos numerados em `<g aria-hidden="true">`, agora com afastarPontos(dist 20): ponto deslocado ganha linha-guia curta até o ponto real. Legenda (spec 8, uma frase por conceito): para chaves piso/equilibrio/teto o `<li>` mostra BadgeNumero + TermoOpcoes(rotulo) + " " + it.frase (a frase nova já começa com "R$ {preco}", Task 4) e NÃO mostra mais `R$ {fmt(v)}`; para perda_maxima/ganho_maximo mostra BadgeNumero + TermoOpcoes(rotulo) + " R$ " + fmt(v) unitário (respeita total/por ação) + "(perde)" quando v < 0 + " — " + it.frase (frase nova sem número). O PM entra como último `<li>` da mesma `<ol>` (BadgeNumero 6 + tx("linha_preco_medio") + " R$ " + fmt(g.precoMedio)). Ausentes, slider "E se…", `<details>` com tabela e o estado sem gráfico (agora com altura fixa = alturaTopo(1) + PLOT_H + MB_EIXO em px, sem layout shift) permanecem. Nenhum `|| 0`/`?? 0`.
  </action>
  <verify>
    <automated>node web/tests/test_ui_onda_h.mjs 2>&1 | grep -E "FALHOU|FALHA" | grep -iE "payoffEixos|Primitivas|GraficoResultado|rotuloEixo|margem|ticks|empilhar|alturaTopo|afastar|montarGeometria" ; for t in test_opcoes_caminho_b_ui test_opcoes_jornada_ui test_opcoes_nav_tres_abas_ui test_ui_onda_c1 test_ui_onda_a; do node web/tests/$t.mjs >/dev/null 2>&1 || echo "FALHOU $t"; done; cd web && npx vite build 2>&1 | tail -3</automated>
  </verify>
  <done>Nenhuma falha de test_ui_onda_h nas partes A e B de primitivas/GraficoResultado; 5 guardiões listados verdes; vite build ok. Commit `feat(261008-oos): primitivas comuns de payoff e GraficoResultado legível`.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: GraficoAnatomia + PosicaoTotal + AnatomiaPerna na linguagem comum</name>
  <files>web/src/opcoes/GraficoAnatomia.jsx, web/src/opcoes/PosicaoTotal.jsx, web/src/opcoes/AnatomiaPerna.jsx</files>
  <behavior>
    - Partes B (GraficoAnatomia, PosicaoTotal) e C (SSR) de test_ui_onda_h passam.
    - test_opcoes_anatomia_render.mjs segue verde SEM edição (title/desc no svg, `<pattern`, "K 48" na saída, null quebra o traço, ids únicos, `=== ""` com < 2 preços, total com halo stroke-width 6 e 3 paths fill none, contagens de aria-pressed 3/4 em PosicaoTotal).
  </behavior>
  <action>
    GraficoAnatomia.jsx: remover `W = compacto ? 340 : 720` / `H` / ML/MR/MT/MB locais; usar ref + useLarguraMedida(ref, 340) (hooks antes do `return null` de < 2 preços — mover o early return para depois dos hooks) e montarGeometria({ largura, x0, x1, yMin: min dos valores plotados, yMax: max dos valores plotados, marcadores, compacto }). Retornar um `<div style={{ display: "flex", flexDirection: "column", gap: "8px", minWidth: 0 }} ref={ref}>` contendo o `<svg>` (viewBox `0 0 {geo.W} {geo.H}`, width 100%, height auto, role="img", aria-labelledby, `<title>`/`<desc>` como hoje, fundo/borda como hoje) e, abaixo, `<LegendaMarcadores itens={geo.marcadores} formatarPreco={fmt} />`. Dentro do svg: hachura de perda e área de ganho mantidas (mesmo pattern/clip com ids únicos), EixoY, EixoX (ticks início/meio/fim do domínio, substituindo os 3 `<text>` atuais e os 3 rótulos Y `fmt(…, 0)`), MarcadoresVerticais (substitui o bloco que escrevia `{m.rotulo}` sobre o plot com alternância i % 2) e o cursor do slider (linha + círculo accent, sem número — é a hipótese do usuário, não marcador). Séries: TRACOS passa a ["6 4", "2 3", "10 3 2 3", "1 3"] (nenhuma perna cheia — spec 4); pernas strokeWidth 1.5 (destaque 2.5); total cheio strokeWidth 3 com o halo de 6 mantido (WR-05). Comentário de decisão no topo citando Onda H e a troca de viewBox fixo por largura medida.
    AnatomiaPerna.jsx: no map de marcadores (~linha 95) adicionar `comPreco: m.chave !== "strike"` (o rótulo do strike já traz o preço via anat_marcador_strike; o de equilíbrio não). Nada mais muda.
    PosicaoTotal.jsx: no map de marcadores (~linha 101) adicionar `comPreco: m.chave !== "strike"`. Chip (spec 4): estado explícito — ligado: `background: ligado ? T.accentTint10 : "transparent"`, borda `1px solid ${T.accent}`, color T.textPrimary, Amostra opacidade 1; desligado: borda `1px solid ${T.borderSubtle}`, color T.textMuted, Amostra com opacity 0.4; remover `2px solid ${T.accent}` e o `opacity: ligado ? 1 : 0.85`; padding "4px 8px", gap "6px", minHeight ALVO_MIN mantido (test_ui_onda_a/caminho_b), justifyContent center, texto TIPO.label sem quebra (whiteSpace "nowrap", overflow hidden, textOverflow "ellipsis" no span). Amostra encolhe para width 16. Grupo de chips vira grid `gridTemplateColumns: "repeat(3, minmax(0, 1fr))"`, gap "6px" (até 6 itens = 2 linhas em 317px — decisão H-D5). A linha de legenda abaixo do gráfico passa a começar com uma amostra estática do total (svg 16x10, linha cheia strokeWidth 3, style stroke T.textPrimary, aria-hidden) + tx("anat_tabela_total") + " · " + anat_legenda_perda + " · " + anat_legenda_ganho (chaves existentes; nenhuma chave nova). Slider, leitura aria-live, `<details>` e tabela intactos.
  </action>
  <verify>
    <automated>node web/tests/test_ui_onda_h.mjs 2>&1 | grep -E "FALHOU|FALHA" | grep -iE "Anatomia|PosicaoTotal|SSR|TRACOS|Chip"; for t in test_opcoes_anatomia_render test_opcoes_caminho_b_ui test_ui_onda_a test_ui_onda_c1 test_ui_onda_g; do node web/tests/$t.mjs >/dev/null 2>&1 || echo "FALHOU $t"; done; cd web && npx vite build 2>&1 | tail -3</automated>
  </verify>
  <done>Nenhuma falha de test_ui_onda_h para GraficoAnatomia/PosicaoTotal/SSR; test_opcoes_anatomia_render verde sem edição; vite build ok. Commit `feat(261008-oos): anatomia com eixos, marcadores numerados e chips com estado`.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 4: PayoffOperador do card + templates de legenda (copy.js ↔ skill_ref.py) + verificação final</name>
  <files>web/src/App.jsx, web/src/copy.js, server/app/skill_ref.py</files>
  <behavior>
    - test_ui_onda_h.mjs 100% verde.
    - test_cartao_v6_camadas (svg role=img + aria-label={pf.aria}, zero `<text`, xDoGrafico/yDoGrafico, chaves leg_hoje/leg_be/leg_k/leg_eixo, sem comparação be/k/preco/resultado), test_cartao_posicao_espelho, test_opcoes_escada_espelho (byte a byte), test_ritmo_sp (padding/gap/margin só por SP), test_ui_onda_g ("30 usos de CARD_PAD_X" intacto), test_chart_colors_theme_aware verdes; pytest de skill_ref/opcoes_escada/cartao_posicao verde.
  </behavior>
  <action>
    (a) Copy (paridade byte a byte, 2 modos em cada arquivo; os dois arquivos mudam no mesmo commit; precedente de chave mista: aqui só VALORES mudam, nenhuma chave nova):
    cartaoPosicao — leg_hoje "hoje {v}", leg_be "BE {v}", leg_k "K {v}" (sai o glifo ┆/◆: o círculo numerado substitui o glifo), leg_eixo "eixo horizontal: preço no vencimento" (os números agora estão nos ticks; {lo}/{hi} seguem sendo passados e ignorados). faixa_rot_be/faixa_leg_hoje NÃO mudam (test_skill_ref.py:438 trava "◆ BE" em faixa_rot_be).
    opcoesEscada, educacional/estudo: legenda_piso "R$ {preco}: abaixo desse preço, a perda por ação para de crescer."; legenda_equilibrio "R$ {preco}: nesse preço, no vencimento, o resultado é zero."; legenda_teto "R$ {preco}: acima desse preço, o ganho por ação para de crescer."; legenda_perda_maxima "é o pior resultado possível no vencimento."; legenda_ganho_maximo "é o melhor resultado possível no vencimento."
    opcoesEscada, operador: legenda_piso "R$ {preco}: abaixo, a perda por ação para de crescer."; legenda_equilibrio "R$ {preco}: resultado zero no vencimento."; legenda_teto "R$ {preco}: acima, o ganho por ação para de crescer."; legenda_perda_maxima "pior resultado no vencimento."; legenda_ganho_maximo "melhor resultado no vencimento."
    opcoes_escada.py continua passando `valor=` (interpolação por str.replace ignora placeholder ausente) — NÃO editar o motor. Rodar o vocabulário (test_vocabulario_opcoes, PROIBIDO do espelho) para garantir que nada promete resultado.
    (b) App.jsx — linha 1: acrescentar useId ao import de "react". Junto dos imports de ./opcoes (perto da linha 23/39): `import { montarGeometria, rotuloEixoBRL, ticksX, PLOT_H } from "./opcoes/payoffEixos.js";` (só o que usar) e `import { useLarguraMedida, LegendaMarcadores } from "./opcoes/PayoffPrimitivas.jsx";`. Reescrever SÓ o corpo de PayoffOperador (Grep `function PayoffOperador(`, Read com offset/limit ~60 linhas):
    hooks no topo, ANTES do `return null` (ref do plot, useLarguraMedida(ref, 280), useId para o pattern da hachura); o `if (!pf || !Array.isArray(pf.pontos) || pf.pontos.length < 2) return null;` permanece com esse texto exato (guardião).
    Marcadores: itens [{ preco: c.hoje, rotulo: cartaoPosicaoTxt(modo, "leg_hoje", { v: price(c.hoje) }) }, { preco: c.be, rotulo: …"leg_be"… }, { preco: c.k, rotulo: …"leg_k"… }] filtrados por `!= null` (só `!=`/`==`: o guardião COMPARA reprova `<`/`>` com be/k/preco/resultado).
    geo = montarGeometria({ largura, x0: pf.xMin, x1: pf.xMax, yMin: pf.yMin, yMax: pf.yMax, marcadores, semTeto: c.k == null }) — decisão H-D6: k nulo = sem teto, mesma regra que já escolhe payoff_aria_sem_teto no backend. xDoGrafico/yDoGrafico continuam existindo (guardião) e passam a devolver px: xDoGrafico = geo.sx e yDoGrafico = (v) => geo.sy(v) - geo.topo.
    Layout HTML (o SVG continua SEM `<text>` — o guardião "zero <text no desenho" fica intacto; rótulos são HTML): wrapper como hoje (bgCard, borda, radius 10, padding SP[3], gap SP[2], SÓ tokens SP em padding/gap/margin — test_ritmo_sp; NÃO usar `${CARD_PAD_X}px` — test_ui_onda_g conta exatamente 30); cabeçalho (payoff_titulo + payoff_sem_custos) igual; depois um bloco `position: relative` com ref, height geo.H - MB_EIXO px, contendo: (1) faixa do topo (altura geo.topo) com um div aria-hidden por marcador — círculo de 18px (MARC_R*2), left cx px, top 4 + linha*MARC_LINHA_H px, transform translateX(-50%), background T.accent, color T.onAccent, fontSize TIPO_CARD.rotulo, fontWeight 700, número centralizado; (2) coluna de rótulos Y: um div absoluto por tick em left 0, width geo.ML - 6 px, top tick.y px, transform translateY(-50%), textAlign right, fontFamily MONO, fontSize TIPO_CARD.rotulo, color T.textSecondary, whiteSpace nowrap; "↑" no topo quando c.k == null; (3) `<svg role="img" aria-label={pf.aria}` (essa ordem exata) posicionado absoluto em top geo.topo, left 0, width 100%, height geo.plotH px, viewBox `0 0 ${geo.W} ${geo.plotH}`, sem preserveAspectRatio "none"; dentro: área entre curva e zero recortada em dois clipPaths (acima do zero: style fill T.positive, fillOpacity 0.1; abaixo: style fill T.negative, fillOpacity 0.12 + path com hachura `url(#…)` cujo pattern tem a linha com style stroke T.negative) — substitui os dois rects divididos no BE; linha do zero (style stroke T.textMuted); linhas verticais dos marcadores na x REAL (tracejado "4 3", style stroke T.textSecondary, vectorEffect non-scaling-stroke) do topo à base; polyline da curva (style stroke T.textPrimary, strokeWidth 2.5); NENHUM fill=/stroke= com T.* em atributo. O losango do BE em HTML pode ficar (posição em px: left xDoGrafico(c.be), top geo.topo + yDoGrafico(0)). (4) linha de ticks X: div flex justify space-between com os 3 ticksX formatados por price(), fontFamily MONO, fontSize TIPO_CARD.rotulo, color T.textSecondary, paddingLeft geo.ML px é proibido como literal solto — usar `marginLeft: geo.ML` numérico (React aplica px; o detector de ritmo só reprova literais "Npx"; se reprovar, posicionar os 3 rótulos absolutos em left sx(valor) com translate como na coluna Y). Abaixo: `<LegendaMarcadores itens={geo.marcadores} />` (rótulos já trazem o preço; comPreco ausente) e uma linha rotuloTxt com cartaoPosicaoTxt(modo, "leg_eixo", { lo: price(pf.xMin), hi: price(pf.xMax) }). Área plotada = PLOT_H (244px) — some o "140px".
    (c) Verificação final do executor (fora do sandbox se pytest precisar): rodar a bateria abaixo; qualquer guardião reprovado por mudança INTENCIONAL desta onda é reconciliado com NOTA DATADA 2026-10-08 ao lado da asserção (nunca apagar asserção; reversão atualiza o guardião com nota). Contagem `@media (prefers-reduced-motion: reduce){` em App.jsx deve seguir 2.
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2 && for t in test_ui_onda_h test_payoff_responsivo test_chart_colors_theme_aware test_ui_onda_a test_ui_onda_b test_ui_onda_c1 test_ui_onda_e test_ui_onda_f test_ui_onda_g test_opcoes_anatomia_render test_opcoes_caminho_b_ui test_opcoes_jornada_ui test_opcoes_nav_tres_abas_ui test_opcoes_escada_espelho test_opcoes_fluxo_render test_vocabulario_opcoes test_cartao_v6_camadas test_cartao_v6_fechado test_cartao_posicao_espelho test_ritmo_sp; do node web/tests/$t.mjs >/dev/null 2>&1 && echo "ok $t" || echo "FALHOU $t"; done; (cd server && .venv/bin/python -m pytest tests/test_skill_ref.py tests/test_opcoes_escada.py tests/test_cartao_posicao.py tests/test_conceitos_opcoes_escada.py -q 2>&1 | tail -2); grep -c "prefers-reduced-motion: reduce){" web/src/App.jsx; (cd web && npx vite build 2>&1 | tail -3)</automated>
  </verify>
  <done>Todos os 20 guardiões "ok", pytest verde, contagem reduced-motion = 2, vite build ok. Commit `feat(261008-oos): card da carteira com eixos e marcadores numerados; legendas sem redundância` + SUMMARY.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| backend → front (payload de gráfico) | números já calculados pelo motor; o front só posiciona |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-H-01 | Tampering (integridade do dado exibido) | payoffEixos.js / ticks | mitigate | ticks são formatação de extremos do domínio; nenhum `|| 0`/`?? 0`; null -> "—"; teto/piso ausente suprime o tick (semTeto/semPiso), guardião parte A |
| T-H-02 | Repudiation/Info (guardrail CVM) | legendas | accept | só textos de legenda mudam; manchete do card não é tocada |
| T-H-03 | Info disclosure | — | accept | sem segredo, sem rede nova, sem pacote novo (nenhum npm/pip install) |
</threat_model>

<verification>
- Guardião novo test_ui_onda_h verde; os 19 guardiões vizinhos verdes; pytest de skill_ref/opcoes_escada/cartao_posicao verde; `npx vite build` ok.
- Inspeção manual pelo Alex no aparelho (não bloqueante): Opções → escada → "Resultado no vencimento" (PM numerado 6, sem "226,865"); Opções → posição PETR4 (chips em 2 linhas, ligado/desligado distinguíveis, marcadores 1..N sem texto sobre o plot, "−R$ 4.998" inteiro); Posições → card com opções (eixo Y presente, plot alto).
</verification>

<success_criteria>
- Nenhum texto de marcador sobre a área plotada nos três gráficos; legenda numerada abaixo.
- Eixo Y com até 3 ticks, nunca cortado; eixo X com 3 ticks; plot >= 220px reais.
- Zero número novo calculado; null = travessão; paridade copy.js ↔ skill_ref.py byte a byte.
- Nenhuma asserção de guardião apagada; reconciliações com NOTA DATADA 2026-10-08.
</success_criteria>

<decisoes_pendentes_alex>
- H-D1 (corte): PayoffChart.jsx (Analisar/Comparar/Curadoria) fica para H2 — não está nos screenshots e já tem eixo Y; migrar exige reconciliar test_payoff_responsivo (asserções 6 e 8). GraficoAnatomia entrou no lugar (é o gráfico do screenshot 2).
- H-D2 (deploy): as frases da legenda vêm do backend (skill_ref.py). Front novo + backend antigo ainda mostra a redundância até o próximo deploy do servidor (bump de SERVER_BUILD_ID). Publicar os dois juntos.
- H-D3 (formato do tick Y): < 100 com 2 casas; 100–99.999 inteiro com milhar; >= 100 mil "mil"; >= 1 mi "mi". O tick é arredondado; o valor exato fica na tabela, no aria e na legenda.
- H-D4: o PM na escada leva o número 6 (o backend fixa 1–5 para piso/equilíbrio/teto/perda/ganho).
- H-D5: chips em grid de 3 colunas — até 6 itens cabem em 2 linhas em 375pt; estruturas com 7+ itens abrem a 3ª linha.
- H-D6: no card, `k == null` suprime o tick máximo e mostra "↑" (mesma regra do aria "sem teto"). GraficoAnatomia não recebe flag de ilimitado do motor, então mostra os 3 ticks da janela; uma seta de "sem limite" ali exigiria campo novo do backend (H2).
- Estudo: as frases didáticas da legenda da escada ficaram, só sem repetir o rótulo/valor; conferir o tom no aparelho.
</decisoes_pendentes_alex>

<output>
Criar `.planning/quick/261008-oos-onda-h-ui-graficos-de-payoff-legiveis/261008-oos-SUMMARY.md` ao terminar (commits, desvios, verificação, pendências H-D1..H-D6). Não editar STATE.md com mutadores do gsd-sdk.
</output>
