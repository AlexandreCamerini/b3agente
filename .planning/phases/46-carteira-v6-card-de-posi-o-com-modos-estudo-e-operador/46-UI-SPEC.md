---
phase: 46
slug: carteira-v6-card-de-posi-o-com-modos-estudo-e-operador
status: draft
shadcn_initialized: false
preset: none
created: 2026-09-30
---

# Phase 46 — UI Design Contract

> Contrato visual e de interação do card de posição v6 (fechado: 1 visual / 1 estado; aberto: flip Ação | Opções; camadas Estudo e Operador). Gerado por gsd-ui-researcher, verificado por gsd-ui-checker. Herda o design system e as regras medidas da Fase 45 (`45-UI-SPEC.md`). Todo número, zona, conta e frase de caso vem do backend; o front só lê, formata e posiciona.

## Premissas e ressalvas (ler primeiro)

Sem usuário para perguntar; as lacunas abaixo foram resolvidas assumindo o razoável. Itens que dependem do Alex estão em "Perguntas em aberto" no fim; nenhum bloqueia.

1. **Regra de precedência (igual à 45):** o protótipo vence em **layout, hierarquia, ordem dos blocos e comportamento**; os tokens `T.*`, o contraste medido, a escala `SP` e a política de cópia deste spec vencem em **cor, tipografia, espaçamento e texto**. O protótipo é dark-only, com hex literal e paleta própria (`#55CFBE`/`#E4BE60`, fundos `#070b12..#111B29`): **nada disso é portado**. O modo Estudo/Operador já troca `T.accent` e neutros por override de variáveis (`MODE_OPERADOR`); o card só lê `T.*`. Sem hex literal no componente novo.
2. **O que NÃO é portado do protótipo (demonstrativo):** painel "Controles da demonstração" (largura/texto/movimento), cabeçalho "Boris+ / MODO ESTUDO", rodapé "Demonstrativo…", toasts, as folhas de plano/saída/histórico/termo/bloqueio (os fluxos existentes ficam: `ctx.A.openSell`, painéis `editFor`/`histFor`, Stop/alvo (IA)), emoji 🔒, o `calc()` e o `learnVals()` (aritmética e frases de caso são do backend, D-01/D-11), `Math.round(K*109)/100` e toda comparação preço×BE/K.
3. **Substituições deliberadas de guardião/regra (D-15, atualizar com nota, nunca apagar):**

   | # | Protótipo | Regra anterior | Resolução |
   |---|-----------|----------------|-----------|
   | S1 | Régua do card fechado com gradiente vermelho→verde (`#5a2f3a→#1f4a42`) | 45 COR-01: trilho neutro, sem gradiente | **45 vence**: trilho neutro `T.knob`; stop/alvo como traços `T.negative`/`T.positive`. Registrado como supersessão do protótipo (D-08 só trava vermelho/verde no **payoff**) |
   | S2 | Faixa no vencimento com 3 segmentos sólidos vermelho/verde-escuro | 45: faixa em `T.borderDashed` | **Protótipo vence na forma** (segmentos antes do BE / entre BE e K / acima de K), **cor com opacidade**: `T.negative` a 0.5, `T.positive` a 0.35 e 0.5 (elementos gráficos, sem texto; a zona também é dita por texto e por marcadores de forma ◆ e traço K) |
   | S3 | Status em caixa colorida com texto colorido (`#FFB3BA` sobre `#2A1E28`, etc.) | 45: negative sobre tint reprova no claro (4.18); positive/negative texto só sobre `bgCard` | **45 vence**: texto sempre `T.textSecondary`/`T.textPrimary`; o tom vai na **borda 1px + glifo** (ver "Bloco de estado") |
   | S4 | Caixa de zona do simulador com texto colorido sobre tint | idem | texto neutro, borda e glifo por zona (ver Simulador) |
   | S5 | Grade de métricas com célula selecionada em `accSurf` e valores coloridos | accent sobre tint reprova (4.33/4.36 claro); positive/negative sobre `bgBase` reprova | células sobre `T.bgCard`, separador 1px `T.borderSubtle`, selecionada = anel interno 2px `T.accent` + `aria-expanded` (sem tint) |
   | S6 | Kicker "TOQUE NOS TERMOS" / "✦ BÓRIS IA" em accent sobre painel `#0E1726` (mais escuro que o card) | accent só sobre `bgCard` liso | painéis internos **sem fundo próprio** (`transparent` sobre `bgCard`) com borda `T.borderSubtle` |
   | S7 | Chips/abas/botão "Atualizar" selecionados com texto accent sobre `accSurf` | idem | selecionado = fundo `T.accentTint10`**só como reforço**, texto `T.textPrimary`, borda 1px `T.accent`; "↻ Atualizar" = texto accent, fundo transparente, borda `T.accent` |
   | S8 | Cabeçalho do card clicável (`div onClick`) | D-17: teclado/leitor de tela | **só o botão do rodapé** abre/fecha (`aria-expanded`, `aria-controls`); o corpo do card não é interativo |
   | S9 | Valor da grade com `ellipsis` (trunca número) | princípio 4/legibilidade | valor **quebra linha** (`overflowWrap:anywhere`), nunca trunca; célula cresce |
   | S10 | `cur == null` posiciona o disco "agora" em 50% (`: 50`) | princípio 4: nunca inventar | **sem cotação → sem disco/linha "hoje"**, rótulo `agora —`; chip "Hoje" do simulador omitido; régua mostra só stop/alvo |
   | S11 | Sheet de saída diz "Registre a saída que você fez" (sugere operação real) | princípios 1–2 (dinheiro virtual; nenhuma ordem) | o fluxo existente `openSell` é reaproveitado; texto de apoio usa o vocabulário simulado (ver Copy) |
   | S12 | Estados do protótipo empilham "travadas" + "sem stop" no mesmo card | CONTEXT D-13: um estado por prioridade | **D-13 vence** (ver "Bloco de estado") |
   | S13 | `btnEncerrarEstrutura` hoje = "Ver encerramento em Opções…" (copy.js:760/1661) | — | passa a "Encerrar opção em Opções" (rótulo do protótipo); atualizar `test_estrutura_card_espelho.mjs`/`test_estrutura_card_vocab.py` com nota |

4. **Face padrão ao abrir:** posição com opções abre na face **Opções**; posição só-ação não mostra seletor (só a face Ação). Assumido do protótipo (estado inicial `back`). O estado de face é local por posição e sobrevive ao fechar/abrir na sessão; não é persistido.
5. **Estados do motor da 45 (vencida, exercício provável, prêmio indisponível, ≤ 5 dias, carregando, falha)** continuam valendo e entram na mesma "linha de estado" do v6 (ver precedência). A 45 não é reescrita (D-13).
6. **Sem shadcn/Tailwind.** React 18 hand-rolled, estilo inline com `T.*` e `SP`. `Tool: none`; gate de registry não se aplica.
7. Fixtures de aceite (UGPA3, CXSE3, ITSA4 sintético, B3SA3, PETR4, BBAS3) são **exemplos de comportamento, não literais de código**. Nenhum valor numérico do protótipo entra no componente ou em copy.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none (React 18 hand-rolled, estilo inline) |
| Preset | not applicable |
| Component library | none; componentes locais em `web/src/App.jsx` (novos **antes de `LinhaChamadaOpcoes`**, D-14) e `web/src/opcoes/*` |
| Icon library | glifos Unicode inline (`⚠ ⓘ ✓ ▴ ▾ ◆ ↻ ✦ ┆`), sem emoji; sem lib nova |
| Font | corpo `SANS` (Nunito, fallback sistema); números `SANS` + `font-variant-numeric: tabular-nums`; `MONO` só na linha da "conta" (`ui-monospace,'SF Mono',Menlo,Consolas,monospace`) |
| Tokens | `T.*` (`var(--x)` de `PALETTE`) + override `MODE_OPERADOR`: 4 combinações (Estudo-escuro, Estudo-claro, Operador-escuro, Operador-claro). Mapa protótipo→token abaixo |
| Componentes | evolui `CardPosicaoEstruturada` (App.jsx:4535) e `estruturaCard.js` (D-13); novos: `CartaoPosicao` (casca fechado/aberto), `ReguaPlano`, `FaixaVencimento`, `SeletorFace`, `SimuladorEstudo`, `PayoffOperador`, `GradeConta`, `TermosTocaveis`; reutiliza `PayoffChart.jsx` ou SVG novo (D-08, decisão do planner; ver "Gráfico") |

### Mapa de cor protótipo → token

| Protótipo | Token | Observação |
|-----------|-------|------------|
| `#070b12` fundo de tela | `T.bgBase` | tela |
| `#111B29` card | `T.bgCard` | superfície do card |
| `#1B2A3D`/`#0B111B`/`#0E1726` caixas internas | `T.bgBase` (só texto neutro) ou `transparent` sobre `bgCard` | S5/S6 |
| `#465D7B`/`#3a4d68`/`#243449` bordas | `T.borderSubtle` (padrão), `T.borderDashed` (tracejado/vazio) | |
| `#EDF2FA` texto | `T.textPrimary` | |
| `#D6DEEB`/`#C1CDE0` texto secundário | `T.textSecondary` | meta, legendas, fonte também `textSecondary` (não `textFaint`: sobe contraste e o texto passa a 12px) |
| `#62DFB5` / `#FF929C` | `T.positive` / `T.negative` | só P&L, preço de stop/alvo, traços de stop/alvo/K, glifo de zona; sempre sobre `bgCard` |
| `#FFE3A0`/`#FFB3BA` texto de estado | `T.textPrimary` + borda `T.warn`/`T.borderDashed` | S3 |
| `--acc` / `--accSurf` / `--accBorder` / `--accInk` | `T.accent` / `T.accentTint10` / `T.accent` / `T.onAccent` | muda por modo sozinho |
| `#f2a93b` "+" da marca | fora do card | |

---

## Spacing Scale

Só `SP` de `App.jsx:1310` (`{1:4, 2:8, 3:12, 4:16, 5:20, 6:24, 8:32}`). O protótipo usa 6/10/13/14 px, fora da escala: **arredondar**, sem exceção óptica nova.

| Token | Value | Usage neste card |
|-------|-------|------------------|
| SP[1] | 4px | glifo-texto; gap rótulo↔valor na célula; gap dentro de chips |
| SP[2] | 8px | gap entre chips/botões (protótipo 6), padding vertical de caixa de estado (protótipo 8–9), margem acima de blocos secundários |
| SP[3] | 12px | gap entre blocos da face (protótipo 12), padding horizontal de caixa (protótipo 10–11), gap entre cards (protótipo 10) |
| SP[4] | 16px | padding do card e do corpo aberto (protótipo 13–14); diâmetro do disco "hoje" na régua (protótipo 14: sobe a 16) |
| SP[5] | 20px | altura útil entre rótulo e trilho em régua com rótulo "agora" (**uso novo**; antes "não usado") |
| SP[6] | 24px | espaço acima da régua para o rótulo "agora/hoje" (protótipo 22) |
| SP[8] | 32px | respiro abaixo da última seção do corpo aberto |

Regras: tap target **mínimo 44px** de altura (protótipo usa 36–40 em abas, chips, "Entendi", link de histórico: todos sobem a 44). Largura mínima 320px; texto a 130% sem rolagem horizontal (flexWrap em todo `flex` de linha; grade 3×2 vira 2 colunas × 3 linhas com texto a 130% ou largura < 340px; ver "Grade"). **Exceções:** (a) termos inline do parágrafo "TOQUE NOS TERMOS" têm `minHeight 28px` com `lineHeight 2` (D-17 isenta termos inline; botão real, foco visível); (b) trilho/barras gráficas têm altura própria (listada abaixo), não são alvo de toque; (c) `padding: 0 2px` horizontal do termo inline.

---

## Typography

O protótipo usa ~12 tamanhos (11, 11.5, 12, 12.5, 13, 13.5, 14, 17, 19, 20, 21, 26) e pesos 650/700/750/800. **Os blocos novos do v6 declaram 3 tamanhos e 2 pesos**; a tabela substitui a da 45 para o card (a 45 usava 16/13/11.5/10.5 + exceção 24; o v6 sobe a legibilidade e elimina a exceção). Elementos herdados e não redesenhados (AvisoLiquidacao, painéis `editFor`/`histFor`, modal de saída) ficam como estão.

| Role | Size | Weight | Line Height | Onde |
|------|------|--------|-------------|------|
| Display | 20px | 700 | 1.2 | ticker; resultado total; preço do simulador; resultado do simulador |
| Body | 14px | 400 (700 em ênfase) | 1.5 | frases do motor, termos, valores de fato, linhas de perna, botões (700), título de perna (700), valor da célula (700), "Bóris explica", painel de termo, "conta" (MONO) |
| Label | 12px | 400 (700 em kicker/legenda ativa) | 1.35 | nome da empresa, meta (`1.000 ações · PM …`), kickers caixa alta (`letterSpacing: .06em`), rótulo de célula, legendas de régua, fonte, chips de vencimento |

Pesos: **400 e 700** (nada de 600/650/750/800 nos blocos novos). Tamanhos 13, 13.5, 12.5, 11, 11.5, 17, 19, 21, 26 do protótipo mapeiam assim: 11/11.5/12.5→12; 13/13.5→14; 17/19/21/26→20. Parágrafo de termos tocáveis: `lineHeight: 2` (exceção de linha, para o alvo de 28px dos termos), 14px. Números sempre `tabular-nums`; sinal explícito via `moneySigned` e `−` (U+2212). Sem `textFaint` em frase nem em texto novo.

---

## Color

Base = tokens vigentes. 60% `T.bgBase` (tela e caixas internas neutras), 30% `T.bgCard` (card), 10% acento do modo.

| Role | Token | Usage |
|------|-------|-------|
| Dominant (60%) | `T.bgBase` | tela; caixa de estado; caixa do gráfico; célula não selecionada **sem** número colorido |
| Secondary (30%) | `T.bgCard` + `T.borderSubtle` | card, painéis de face, grade de métricas |
| Accent (10%) | `T.accent` (azul-esverdeado Estudo / dourado Operador) | lista fechada abaixo |
| Destructive | `T.negative` | **nenhuma ação destrutiva nova.** "Simular venda/Registrar saída" herdam o modal atual |

**Accent reservado para:** (1) texto do botão de rodapé "Ver detalhes e aprender ▾ / Detalhes e ações ▾ / Fechar ▴" (accent sobre `bgCard`); (2) kickers "TOQUE NOS TERMOS", "✦ BÓRIS IA" e prefixo "Bóris explica ·"; (3) borda e anel interno de **estados selecionados** (aba Ação/Opções, chip do simulador, célula da grade, termo aberto) — texto permanece `textPrimary`; (4) o marcador do usuário: polegar do slider (`accent-color`), disco "hoje" da faixa, linha tracejada "hoje" do payoff e disco do simulador; (5) botão primário preenchido "Definir/Completar/Ajustar plano · IA" (fundo `T.accent`, texto `T.onAccent`; **um por card**); (6) botão "↻ Atualizar" (texto + borda); (7) sublinhado pontilhado dos termos (decorativo) e do rótulo de célula; (8) anel de foco `:focus-visible` (já global em `.b3 :focus-visible`, 2px offset 2px). **Nada mais.** Chips de vencimento, status, régua, "Encerrar opção em Opções" e "Reanalisar" são neutros (a 45 manteve "Reanalisar" neutro; o protótipo o pinta de accent com `accSurf`, que reprova no claro, então fica neutro: borda `T.borderSubtle`, texto `T.textPrimary`).

Verde/vermelho (`T.positive`/`T.negative`) **só** em: resultado total e parciais, P&L de perna, preços de stop/alvo, "Ganho máx."/"Perda máx.", traços de stop/alvo/K, glifos e bordas de zona/gráfico, preenchimento de zonas do gráfico. Nunca em chip, rótulo, texto de estado ou fundo de texto.

### Contraste (herda 45 medido; pares novos a medir no guardião)

Valem os 7 pares da tabela da 45 (`textSecondary/bgCard`, `textMuted/*`, `warn/warnTint10`, `positive|negative/bgCard`, `accent/bgCard`) e as regras derivadas (positive/negative texto só em `bgCard`; textFaint nunca em tint). **Pares novos que `test_estrutura_card_contraste.mjs` deve cobrir nas 4 combinações (≥ 4,5:1 texto, ≥ 3:1 gráfico/borda de estado):**

| Par | Mín. |
|-----|------|
| `onAccent` sobre `accent` (botão primário) | 4,5 |
| `textPrimary` sobre `bgBase` (caixas de estado, grade, zona) | 4,5 |
| `textSecondary` sobre `bgBase` (meta, legendas dentro de caixa) | 4,5 |
| `accent` sobre `bgCard` (kicker, rodapé, Atualizar) | 4,5 |
| `T.warn` e `T.negative` como **borda** de caixa sobre `bgBase` | 3,0 |
| `T.positive` (K, zona) e `T.negative` (zona) a 0.5 de opacidade sobre `bgBase` do gráfico | 3,0 (medir; se reprovar, subir opacidade) |
| `accent` como linha "hoje" sobre fundo do gráfico (`bgBase`) | 3,0 |

Se qualquer par reprovar no claro, ajusta-se a opacidade/borda, **não** o texto para cor de tom (regra da 45).

---

## Card fechado — um visual, um estado (igual em Estudo e Operador)

Ordem de cima para baixo, `SP[3]` entre blocos, padding `SP[4]`, raio herdado do card atual (premissa: manter o raio vigente de `CardPosicaoEstruturada`; o protótipo usa 18px). Largura de conteúdo 320px mínimo.

1. **Cabeçalho (sem toque).** Esquerda: ticker (Display), nome da empresa (Label, `textSecondary`). Direita (alinhada à direita, `flexWrap`, `marginLeft:auto`): resultado total Display colorido por sinal via `moneySigned(estrutura.resultado.total)`; embaixo, para posição com opções: `Ações {valor} · Opções {valor}` (Label, rótulo neutro, valor 700 colorido; `null` → "indisp." neutro); para posição simples: variação % (valor do backend, não calculada). Resultado `null` → "Parcial" em `textMuted` + linha extra "Resultado parcial" (abaixo).
2. **Meta.** Label: `{qty} ações · PM {R$}` e, com opções, ` · {estratégia ou "estratégia não classificada"} · vence {dd/mm} ({n}d)`. O chip âmbar da 45 (`vence … · N dias` com `0 ≤ dias ≤ 5`) continua no cabeçalho; neste v6 a data/dias da meta e o chip **não se duplicam**: com chip âmbar, a meta omite `vence …`.
3. **Régua (ação com plano completo) OU Faixa no vencimento (composta com BE do backend).** Nunca as duas. Nenhuma das duas sem dado do backend (ver estados).
4. **Linha de estado** (uma principal + linhas extras; ver abaixo).
5. **"Bóris explica ·"** (só Estudo): 1 linha determinística do caso (D-12), 14px, `textSecondary`, prefixo accent 700.
6. **Rodapé:** botão de largura total, `minHeight 44`, borda superior `T.borderSubtle`, texto accent 700 14px: Estudo `Ver detalhes e aprender ▾`, Operador `Detalhes e ações ▾`; aberto: `Fechar ▴`. `aria-expanded`, `aria-controls={id do corpo}`.

### Régua stop ← agora → alvo (ação com plano; D-14 vale para qualquer posição com stop e alvo)

- Container 40px de altura (rótulo 24 + trilho): rótulo `agora {preço}` Label 700 acima do disco; âncora com `anchor()` do protótipo (x<22%: alinha à esquerda; x>78%: alinha à direita; senão centro) como função pura em `estruturaCard.js` (testada).
- Trilho 8px (`SP[2]`), cantos 999px, `T.knob` (neutro, S1). Traço stop à esquerda (3px × 16px, `T.negative`) e traço alvo à direita (`T.positive`), mais traço PM 2px `T.textSecondary`. Disco "agora" 16px (`SP[4]`) `T.textPrimary` com anel 2px `T.bgCard`.
- Domínio = [stop, alvo]; posição = `posRegua` existente (clamp 0–100%). Preço fora do intervalo fica preso à ponta; o texto de estado diz "Abaixo do stop do plano / Acima do alvo do plano" (enum do backend, ver Contrato de dados).
- Legenda sob o trilho: `Stop {valor} {dist%}` à esquerda, `Alvo {valor} {dist%}` à direita (valor 700 colorido sobre `bgCard`; `dist%` Label `textSecondary`, **campo do backend**, não calculado). Cotação null: sem disco, `agora —`, sem `dist%`.
- `role="img"`, `aria-label` = frase do backend/`cp` com stop, alvo, PM e agora (só números do backend). Trilho e traços decorativos.

### Faixa no vencimento (composta com `faixa` e BE do backend)

- Título Label 700 `No vencimento ({dd/mm})` (neutro). Rótulo `hoje {preço}` acima do marcador (mesma âncora).
- Trilho 6px → **3 segmentos** (antes do BE / BE→K / acima de K) com S2; marcadores: ◆ no BE (losango 10px `textPrimary`), traço K 3px × 18px `T.positive`, disco "hoje" 16px `T.accent` anel `bgCard` (ausente se hoje `null`).
- Abaixo, 3 colunas (`grid 3×minmax(0,1fr)`, gap `SP[2]`): `Piso` (esq.) · `◆ Equilíbrio` (centro) · `Teto` (dir.). Rótulo Label `textSecondary`; valor Body 700 `textPrimary` **neutro** (o protótipo pinta piso de `#FFE3A0` e teto de verde: sem tom; teto positivo só no traço K). Piso `null` → "sem piso" (sem número). Em 320px a 130% as 3 colunas passam a empilhar (`1fr`) via `flex-wrap`, não por media query de largura fixa.
- Posicionamento: domínio = {BE, K, hoje, piso se houver} com margem; **os 3 limites são valores do backend**; o front só mapeia para %. Sem BE (ex.: ITSA4 sintético) → **sem faixa**: linha "aguardando o cálculo do app" (copy) e nada desenhado.

### Bloco de estado — um principal, extras à parte (D-13)

Um único **estado principal** por prioridade; depois, linhas extras. Estados de risco do motor (45) precedem a trava: primeiro a lista, depois D-13.

| Prio | Estado principal | Condição (enum do backend) | Glifo/borda |
|------|------------------|----------------------------|-------------|
| 0 | vencida · exercício provável (45) | `estrutura.estado` | borda `T.textMuted` / `T.warn`; textos da 45 (`estadoTexto`) |
| 1 | Ações travadas | `qtyLivre == 0` → "Ações travadas pela CALL — saída só após encerrar a opção"; `0 < qtyLivre < qty` → "{n} de {m} ações travadas · {k} livres" | `ⓘ` + `T.borderDashed` |
| 2 | Sem plano / plano incompleto | sem stop e alvo → "Sem stop e alvo — defina o plano"; só um → "Falta o alvo/stop — plano incompleto" | `⚠` + `T.warn` |
| 3 | Fora do plano | enum `abaixo_stop`/`acima_alvo` → "Abaixo do stop do plano" / "Acima do alvo do plano" | `⚠` + `T.warn` |
| 4 | Dentro do plano | enum `dentro` (**só posição sem opções**; composta não mostra) | `✓` + `T.borderSubtle` |

**Extras** (cada uma uma linha, após o principal, sem tom de alerta salvo pendência): pendência do backend (ex.: "Nota de corretagem pendente"; `⚠` + `T.warn`), "Resultado parcial: um prêmio atual indisponível" (`ⓘ`), "Cotação atual indisponível nesta fonte" (`ⓘ`, posição simples sem cotação), `estrutura.estado` ≤ 5 dias (chip âmbar da 45, não linha) e prêmio indisponível (45: `ⓘ` + `T.borderDashed`).

Quando prio 1 (trava) é o principal e há "sem plano", o aviso CARD-05 "Posição sem stop definido" **não** é mostrado no card fechado (evita 2 estados); o próximo passo "defina o plano" continua disponível no corpo aberto no botão `Definir plano · IA` e no painel `Plano da ação`. CARD-05 mantém a regra da 45 (só com `stopTexto == null` e estrutura carregada) **no corpo aberto**.

Caixa: fundo `T.bgBase`, borda 1px do tom, raio 10px, padding `SP[2]` `SP[3]`, glifo `aria-hidden` 14px + texto Body 14px 400 `textSecondary`. Sem texto colorido (S3). Tom nunca é o único portador: o glifo e a frase dizem o estado.

---

## Card aberto

Corpo `id` referenciado por `aria-controls`; padding `SP[4]`, borda superior `T.borderSubtle`, coluna com gap `SP[3]`.

### Seletor Ação | Opções (n) — só com opções

- `role="group" aria-label="Face do card {TICKER}"`; grade 1fr 1fr, gap `SP[1]`, padding `SP[1]`, borda `T.borderSubtle`, raio 11px, fundo `bgBase`. Dois botões `minHeight 44`, Body 700, `aria-pressed`. Selecionado: fundo `accentTint10`, borda 1px `T.accent`, texto `textPrimary`; não selecionado: transparente, borda transparente, texto `textSecondary`. Rótulos: `Ação` · `Opções ({n})` (n = nº de pernas do motor).

### Flip 3D (só a área abaixo do seletor)

- Container `perspective: 1100px`; uma face de cada vez no DOM (a face inativa **não** fica em `display:none`+escondida: ela é desmontada; assim leitor de tela e tab só veem a ativa).
- Sequência: `rotateY(0→90deg)` 170ms `ease-in` → troca o conteúdo no ponto médio → `rotateY(-90→0deg)` 170ms `ease-out`. `backface-visibility:hidden`. Trava `busy` durante os ~370ms (cliques repetidos ignorados; o último alvo vence ao terminar).
- **`prefers-reduced-motion`:** a checagem é feita **no momento do clique** com `window.matchMedia("(prefers-reduced-motion: reduce)").matches` (não usar a constante `REDUCE_MOTION` do `App.jsx:1708`, lida uma vez no carregamento, nem confiar na regra global de CSS `transition-duration: .01ms`, que não afeta `setTimeout`). Reduzido: troca imediata, sem timers.
- Foco permanece no botão acionado; ao trocar de face, o painel da face anunciado por `aria-live="polite"` vazio (sem anunciar o conteúdo inteiro). Esc/Tab seguem o fluxo normal.
- Testável: `flipDuracaoMs(reduzido)` pura (0 ou 170+170) em `estruturaCard.js`.

### Face "Ação"

1. **Plano da ação** (só quando a face existe junto com opções e plano completo): caixa `bgBase`, só texto neutro; `Stop {valor}` e `Alvo {valor}` com valores coloridos **fora** da caixa (regra 45: números coloridos sobre `bgCard`). Label 12 700 "Plano da ação".
2. **Fatos** (lista de linhas `rótulo … valor`, divisor 1px `T.borderSubtle`, linha mínima 44): `R:R atual` (só com stop **e** alvo), `Stop`/`Alvo` (parcial: valor ou `Falta definir`), `Em operação` ({n} dia(s)), `Do capital` ({%}), `Cotação atual` (simples), `Setup de entrada` (+ gatilho e status), `Origem` (só se o backend entregar). Valores do backend.
3. **Compras ({n})**: botão expansor `minHeight 44`, `aria-expanded`; aberto lista `data · ▲ qtd × preço · total`; **nota de PM** é texto do backend (`PM {R$} = {total} ÷ {qtd} ações (média ponderada).`), não somada no front. Fonte sem detalhe: `Compras: indisponível nesta fonte` / `Detalhes das compras não vieram nesta fonte — nada foi inferido.`

### Face "Opções"

1. **Pernas** (`ul/li`): título `{código ou "CALL s/ TICKER"} · CALL vendida`, P&L da perna à direita colorido por sinal (ou `indisponível` neutro); linha `{qtd} × strike {x} · prêmio {entrada} → {atual|indisponível}`; nota Label `Prêmio atual: {qualidade}.` quando o backend entregar `origemTexto`. Caixa `bgBase`, só texto neutro; P&L colorido **fora** da caixa (S3/regra 45) — a caixa de perna usa `bgCard` com borda `borderSubtle`.
2. **Estudo → Simulador "e se?"**; **Operador → Payoff + grade 3×2**; sem `faixa`/curva → caixa tracejada (D-16): `Cenários não calculados para esta combinação. Os limites dependem do cálculo do app.`
3. **Linha de fonte** (Label `textSecondary`: `{fonte} · {data hora}` ou `Origem da cotação não informada`) + botão `↻ Atualizar` (44px; desabilitado com requisição em voo).
4. Botão `Encerrar opção em Opções` (largura total, 44px, borda `borderSubtle`, texto `textPrimary`, fundo transparente). Bloqueios e reasons da 45 (`encerrar.texto`, `aria-disabled`/`aria-describedby`) mantidos. Dívida da 45 mantida (só recompra a call).

### Simulador "e se?" (Estudo)

- Painel `bgCard` + borda `borderSubtle`, padding `SP[3]`. Linha de lead (Label `textSecondary`): `Se em {dd/mm} {TICKER} fechar a`. Preço do slider em Display; à direita `resultado da estrutura` (Label) + resultado Display colorido (`moneySigned`, valor da grade).
- **Caixa de zona** (`role="status"`): fundo `T.bgBase`, borda 1px: zona 1 `T.negative`, zona 2 `T.borderDashed`, zona 3 `T.positive`; glifo `▾`/`▬`/`▴` (aria-hidden) + texto do backend em `textPrimary` 14px 400. A zona e o texto são **do ponto da grade** (D-06), o front não compara preço com BE/K.
- **Trilho** (altura 70px): barra 10px com 3 segmentos (S2), rótulos `◆ equilíbrio {x}` (acima) e `teto {x}` / `hoje {x} │` (abaixo), 12px Label; anti-colisão: se dois rótulos da mesma linha ficam a < 30% de distância, o segundo desce uma linha de 16px (função pura `rotulosSemColisao`, testada); âncora com `anchor()`. Disco do slider 18px `T.accent` anel 3px `bgCard`; linha "hoje" 2px `textPrimary`.
- **Slider** `input type="range"`: altura 44px, `min`/`max`/`step` da grade do backend (D-04), valor por **índice** na grade; `aria-label` "Preço de {TICKER} no vencimento", `aria-valuetext` = `{R$ preço}; {resultado com sinal}; {rótulo da zona}`. Setas = 1 passo; PageUp/Down = ver planner (múltiplos de passo, valor da grade). Arrastar não faz rede.
- **Chips** (pontos nomeados do backend: `hoje`, `equilibrio`, `teto`, `alta_forte`): rótulos `Hoje`, `Equilíbrio`, `Teto`, `Alta forte`; `minHeight 44`, pill, `aria-pressed` = índice igual ao do slider (igualdade de índice, sem tolerância numérica). Chip sem ponto (ex.: sem cotação → sem "Hoje") não é desenhado.
- Rodapé do painel: `Sem custos. É o resultado no vencimento, não o de hoje.` (Label; ver Pergunta 3).

### Payoff + grade (Operador)

- Painel como acima. Título `Payoff no vencimento · {dd/mm}` (Body 700) e `sem custos` à direita (Label).
- **Gráfico** (D-08): altura 140px, fundo `bgBase`, borda `borderSubtle`, raio 10px, `role="img"` + `aria-label` descritivo (do backend/`cp`: prejuízo abaixo de BE, ganho travado acima de K, com os números). Elementos: linha da curva `T.textPrimary` 2.5px; linha do zero `T.textMuted`; K tracejado `T.positive`; "hoje" tracejado `T.accent`; ◆ BE sobre a linha do zero (`textPrimary`, 9px); fundo vermelho antes do BE (`T.negative` a 0.12) e verde depois (`T.positive` a 0.10). **Sem texto dentro do desenho.** Sem curva → nada desenhado.
- **Legenda** abaixo (Label `textSecondary`, glifos coloridos só como marcador): `┆ hoje {x}` · `◆ BE {x}` · `┆ K {x}` · `eixo x: {lo} → {hi}`.
- **Grade 3×2:** `grid repeat(3, minmax(0,1fr))`, gap 1px sobre `borderSubtle`, células `bgCard`, botão `minHeight 48` com `aria-expanded`. Célula: rótulo Label com sublinhado pontilhado accent, valor Body 700 (Ganho máx. `positive` e Perda máx. `negative` sobre `bgCard`; demais `textPrimary`); sem `ellipsis` (S9). Ordem: `BE · Até BE · Até K · Ganho máx. · Perda máx. · Lastro`. Abaixo de 340px de largura útil **ou** texto ≥ 130%: 2 colunas × 3 linhas.
- **Conta** (`role="status"`) ao tocar: painel `bgBase`, borda `T.accent`, `Label` com a fórmula (`BE = PM − prêmio`) e linha MONO 14px/700 com os números (`39,50 − 1,49 = 38,01`) — **células `{rotulo, valor, conta}` do backend (D-07)**. `conta: null` → "Calculado pela camada de opções do app". Um aberto por vez; tocar de novo fecha. Sem ⓘ e sem card de termos no Operador.

### Camada Estudo: "TOQUE NOS TERMOS" e painel de termo

- Painel sem fundo próprio, borda `borderSubtle`, padding `SP[3]`, fora da área do flip (aparece nas duas faces). Kicker Label 700 accent `TOQUE NOS TERMOS`. Parágrafo de 14px `lineHeight 2` com **texto + termos**: cada termo é `<button>` `minHeight 28px`, 700, `textPrimary`, sublinhado pontilhado `T.accent`, `aria-expanded`; só é botão se houver verbete **válido** (D-09/princípio 4); sem verbete, vira texto simples (sem sublinhado). Texto e termos vêm prontos do backend (mapa por tipo de posição, D-11).
- Painel do termo (`role="status"`), abre abaixo do parágrafo: borda 1px `T.accent`, fundo transparente; título Body 700 `textPrimary`; definição (KB via `verbeteDoCatalogo`); divisor; `No seu caso:` (700) + frase do backend; botão `Entendi` (`minHeight 44`, borda `T.accent`, texto accent). Um termo por vez; tocar de novo fecha; `Entendi` fecha e devolve o foco ao termo.
- Termos por tipo de posição (backend): **call coberta** — lastro, call coberta, teto, equilíbrio, piso; **composta não classificada** — lastro, piso, teto (com "aguardando o cálculo do app" quando não há cálculo); **ação com plano completo** — preço médio, stop, alvo, R:R; **sem plano / incompleto** — preço médio, stop, alvo.

### Bloco "BÓRIS IA" (ambos os modos)

Painel sem fundo próprio, borda `borderSubtle`. Cabeçalho: kicker `✦ BÓRIS IA` (accent) + link `Histórico de análises ({n})` (44px, `textPrimary`, sublinhado). Dois botões em `repeat(auto-fit, minmax(120px,1fr))`, `minHeight 44`: primário preenchido `{Definir|Completar|Ajustar} plano · IA` (fundo `accent`, texto `onAccent`) e neutro `Reanalisar`. Em seguida o botão de saída (largura total, 44px): Estudo `Simular venda`, Operador `Registrar saída`; sem ações livres: `aria-disabled="true"`, sufixo `· 0 ações livres`, `aria-describedby` apontando para o texto de motivo visível ("Todas as ações estão travadas como lastro. Para sair do ativo, encerre a CALL vendida em Opções.") e o toque **não** abre o modal. Os handlers são os herdados (`ctx.A.openSell`, Stop/alvo (IA), reanálise, histórico); nenhum fluxo novo.

---

## Estados (princípio 9) no layout v6

| Estado | Tratamento |
|--------|------------|
| carregando (1ª leitura da estrutura) | linha `role="status"` "Lendo a estrutura de opções…" (chave `lendo` da 45); sem spinner animado; o card atual aparece completo abaixo (P&L das ações) |
| vazio | **não há estado vazio novo**: carteira sem posições mantém o vazio vigente da tela; posição sem opções = card sem face Opções |
| erro / falha | linha `role="status"` com `indisponivel` + `↻ Atualizar`; nenhum valor estimado (45) |
| mercado fechado | sem banner novo; a perna mostra a origem do prêmio (`origemTexto`: "pelo último negócio"); a `fonte`/`at` aparece na linha de fonte |
| dado atrasado | **lacuna herdada da 45** (a `estrutura` não traz flag de atraso): mostra só fonte e hora; ver Pergunta 2 |
| cotação indisponível | posição simples: extra "Cotação atual indisponível nesta fonte"; sem disco "agora" (S10); composta: faixa sem "hoje" |
| resultado parcial | resultado "Parcial" + sublinhas "indisp." + extra de resultado parcial |
| vencida / exercício provável / prêmio indisponível / ≤ 5 dias | tratamentos da 45 mantidos (chip âmbar, callout, `Encerrar` desabilitado com `encerrar.texto`); mapeados na prioridade 0 e nos extras |
| ordem rejeitada / operação concluída | fluxo herdado do modal de saída; este spec não os altera |
| sem cenário calculado (`faixa`/curva ausente) | caixa tracejada `Cenários não calculados…`; termos "aguardando o cálculo do app"; **nunca** gráfico sem dado |

---

## Copywriting Contract

Regra: **todo texto novo nasce em `server/app/skill_ref.py` e ganha espelho byte a byte em `web/src/copy.js`** (guardião). Frases com números e "No seu caso" vêm montadas do backend (D-11). Modo muda **só**: cor, rótulo de botão/saída e a camada didática; números/estados/ações idênticos.

| Element | Estudo | Operador |
|---------|--------|----------|
| Primary CTA (card) | `Ver detalhes e aprender ▾` | `Detalhes e ações ▾` |
| Fechar | `Fechar ▴` | `Fechar ▴` |
| Saída | `Simular venda` | `Registrar saída` |
| Saída sem lote livre | `Simular venda · 0 ações livres` | `Registrar saída · 0 ações livres` |
| Apoio ao abrir a saída (modal herdado) | `Treino com dinheiro virtual: nenhuma ordem é enviada.` | `Saída simulada com dinheiro virtual. Nenhuma ordem é enviada à corretora.` |
| Camada didática | kicker `TOQUE NOS TERMOS`; `No seu caso:`; `Entendi`; `Bóris explica ·` + 1 linha | ausente (sem ⓘ, sem card de termos, sem Bóris explica) |
| Simulador / payoff | `Se em {dd/mm} {T} fechar a` / `resultado da estrutura` | `Payoff no vencimento · {dd/mm}` / grade BE, Até BE, Até K, Ganho máx., Perda máx., Lastro |
| Aviso de método | `Sem custos. É o resultado no vencimento, não o de hoje.` | `sem custos` (título do payoff) |

Neutras (idênticas nos dois modos, só `copy.js` + guardião de igualdade Estudo=Operador): `Ação`, `Opções ({n})`, `Plano da ação`, `Compras ({n})`, `Ver ▾`/`Ocultar ▴`, `Compras: indisponível nesta fonte`, `Detalhes das compras não vieram nesta fonte — nada foi inferido.`, `Falta definir`, `Sem stop e alvo — defina o plano`, `Falta o alvo — plano incompleto`, `Falta o stop — plano incompleto`, `Abaixo do stop do plano`, `Acima do alvo do plano`, `Dentro do plano`, `Ações travadas pela CALL — saída só após encerrar a opção`, `{n} de {m} ações travadas · {k} livres`, `Resultado parcial: um prêmio atual indisponível`, `Cotação atual indisponível nesta fonte`, `Definir plano · IA`, `Completar plano · IA`, `Ajustar plano · IA`, `Reanalisar`, `Histórico de análises ({n})`, `Encerrar opção em Opções`, `↻ Atualizar`, `Origem da cotação não informada`, `Cenários não calculados para esta combinação. Os limites dependem do cálculo do app.`, `Calculado pela camada de opções do app`, `aguardando o cálculo do app`, `Piso`, `◆ Equilíbrio`, `Teto`, `sem piso`, `sem teto`, `agora`, `hoje`, `No vencimento ({dd/mm})`, `Hoje`, `Equilíbrio`, `Alta forte`.

| Element | Copy |
|---------|------|
| Empty state | sem estado vazio novo (ver Estados) |
| Error state | `indisponivel` (45): `Estrutura indisponível agora. Pernas abertas seguem na carteira — nada estimado.` (Operador) / `Não foi possível ler a estrutura de opções agora. As pernas abertas continuam na sua carteira, e nenhum valor é estimado no lugar.` (Estudo) + `↻ Atualizar` |
| Destructive confirmation | nenhuma ação destrutiva nova; `Simular venda`/`Registrar saída` herdam o modal atual |

**Guardiões de texto:** `test_opcoes_collar_vocab.py` varre todo `web/src/*.js(x)`: não escrever as âncoras proibidas (`trava protetora`, `abate o custo`). O guardião da 45 proíbe `\bcomprar\b|\bvender\b` no vocabulário Estudo de `ESTRUTURA_CARD`: "Simular venda", "vendida", "vendeu" e "vendê-las" **passam** a regex, "vender" **não**. O planner deve reescrever qualquer definição que use "vender/comprar" (ex.: a de Call coberta do protótipo: "…aceita vender as ações pelo strike" → "…aceita entregar as ações ao preço do strike") ou registrar relaxamento com nota. Sem linguagem de lucro garantido: "Ganho máx." e "lucro travado" descrevem **teto de resultado de uma estrutura**, nunca promessa; a frase do backend não usa "garante", "certo", "sempre".

---

## Contrato de dados exigido do backend (o que a UI lê; D-01..D-07)

Contrato **aditivo** (não quebra a 45 em produção). Nomes são do planner; a coluna "dono" é o contrato.

| Item na UI | Origem | Estado |
|-----------|--------|--------|
| resultado total/ações/opções, estado, pernas, fonte/`at`, piso/teto/BE, ganho/perda máx., `qtyTravada` | `estrutura` da 44/45 | existe |
| `dist%` do stop e do alvo na régua (protótipo calcula `stop/cur−1`) | **backend** | **novo** (não estava no CONTEXT; sinalizado) |
| enum de posição no plano (`abaixo_stop` / `acima_alvo` / `dentro` / sem plano / incompleto) | **backend** | **novo** (o front não compara preço com stop/alvo) |
| "Até BE", "Até K", "Alta forte" (constante nomeada `K × 1,09`) | backend (D-03) | novo |
| grade do simulador `{min,max,passo,pontos[]}` + pontos nomeados + zona por ponto/intervalo + texto da zona | backend (D-04, D-06) | novo |
| curva do payoff | `perfil_da_estrutura().curva` exposta | exposição nova |
| células `{rotulo, valor, conta}` | backend (D-07) | novo |
| definição dos termos | KB `GET /api/kb/catalogo` via `verbeteDoCatalogo` (D-09) | **parcial**: existem `stop`, `alvo` (conceitos), `risco-rr`; **faltam** lastro, call coberta, teto, equilíbrio, piso, preço médio (D-10, a criar em `kb.py`/`conceitos.py`; o researcher da fase confirma contra o catálogo) |
| "No seu caso:", mapa de termos por tipo, "Bóris explica" | backend determinístico (D-11/12) | novo |
| nota de PM (`PM = total ÷ qtd`) | backend (texto pronto) | novo |
| compras (lista), setup/gatilho, origem da posição, pendência (nota de corretagem), dias em operação, % capital | 45/posição | **lacuna a mapear** (não renderizar o que o backend não entregar; sem inferir) |
| "sem custos" | confirmar que o resultado do backend exclui custos | **pergunta** |

Front que **pode** fazer: formatar (pt-BR, `R$`, `−`), mapear valor→% na régua/trilho/gráfico (`posRegua`), âncora/anti-colisão de rótulos, indexar a grade pelo slider. Front que **não** pode: qualquer aritmética de payoff, BE, K, distância %, soma de prêmios, comparação preço×BE/K×stop/alvo, definição de zona. O guardião `test_estrutura_para_payoff.mjs` permanece intacto.

---

## Interação e acessibilidade

- Alvos ≥ 44px (exceto termos inline, 28px, com `lineHeight 2`). Tab: rodapé do card → seletor → conteúdo da face (em ordem visual) → termos → `Entendi` → Bóris IA (histórico, plano, reanalisar, saída). Ordem de leitura = ordem visual.
- `aria-expanded` nos botões de expandir (rodapé, compras, células da grade, termos); `aria-pressed` nas abas Ação/Opções e nos chips; `aria-controls` no rodapé; `role="status"` na caixa de zona, na conta e no painel do termo (um por vez para não spammar); `role="img"` + `aria-label` na régua, faixa e gráfico (texto vindo do backend/`cp`, nunca reescrevendo valor).
- Slider por teclado com `aria-valuetext` (preço + resultado + zona). Sem animação além do flip e do foco; `prefers-reduced-motion` por checagem no clique (ver Flip).
- Cor nunca é único canal: glifo (`⚠ ⓘ ✓ ◆ ▾ ▬ ▴`), sinal `+/−`, texto de estado e forma dos marcadores (traço, losango, disco).
- Responsivo: 320–430px; texto 130% sem rolagem horizontal; `flexWrap` em linhas de meta/legenda; grade 3×2 → 2 colunas conforme regra; rótulos de gráfico com âncora e anti-colisão.
- Foco: `.b3 :focus-visible` já global (2px `T.accent`, offset 2px); botões do card não removem o outline.

---

## Fora de escopo (invariantes)

Sem mudança em método de cálculo; sem `optionsCalc` no cliente (testes UGPA3/CXSE3 viram pytest do backend, D-02); sem ordem nova, sem rota nova de execução, sem fill parcial, sem polling, sem LLM nos textos do card (D-12), sem reescrever o card da 45, sem tocar manchete do card de decisão. `Encerrar opção em Opções` continua só recomprando a call (dívida da 45). Folha/chips "Entenda os termos" **removidos** (substituídos pelo painel de termos); guardiões que os varriam atualizados com nota.

## Validação exigida

`npx vite build`; `npx cap copy ios` antes da suíte; `bash scripts/executar.sh --testes` 1× por onda (orquestrador). Guardiões a **atualizar com nota** (D-15): `test_estrutura_card_ui.mjs`, `test_estrutura_card_logica.mjs`, `test_estrutura_card_espelho.mjs`, `test_estrutura_card_contraste.mjs` (+ pares novos acima), `test_estrutura_card_vocab.py`, `test_opcoes_collar_vocab.py` (checar), `test_ritmo_sp.mjs` (incluir os componentes novos), `test_payoff_responsivo.mjs` (se reaproveitar `PayoffChart`), `test_carteira_lastro_ui.mjs` (sem `disabled=` em `CarteiraScreen`), `test_skill_ref.py`. **Guardiões novos sugeridos:** `anchor`/`rotulosSemColisao`/`flipDuracaoMs`/prioridade de estado (puros em `estruturaCard.js`); espelho `skill_ref`↔`copy.js` das chaves novas; slider lê grade por índice sem aritmética (`test_estrutura_para_payoff.mjs` ampliado); `cur == null` não desenha disco; termo sem verbete não é botão; face inativa desmontada; motion reduzido troca sem timer; pytest UGPA3/CXSE3/ITSA4 no backend; ausência de hex literal e de `+ - * /` sobre campos financeiros nos componentes novos.

---

## Perguntas em aberto (assumi o padrão indicado; nenhuma bloqueia)

1. **Prioridade 0 (estados de risco da 45) acima da trava:** assumi que `vencida`/`exercício provável` precedem "ações travadas". Se o Alex quiser a lista literal de D-13 (trava primeiro), inverte-se a linha sem custo.
2. **Dado atrasado / tempo real (princípio 3):** continua sem flag no motor (lacuna da 45). O card mostra só fonte e hora. Fase própria ou aceitar?
3. **"Sem custos":** o protótipo afirma "Sem custos. É o resultado no vencimento…". Confirmar que `resultado_no_vencimento` do backend realmente exclui corretagem/slippage; senão a frase muda (CLAUDE.md exige custos exibidos).
4. **Raio e sombra do card:** assumi manter o do `CardPosicaoEstruturada` atual (não os 18px do protótipo). Aceitar?
5. **Face padrão = Opções** em posição com opções (do protótipo). Aceitar ou abrir em Ação?
6. **IDs de requisito (propostos para o plano):** CART6-01 card fechado 1 visual/1 estado; CART6-02 flip Ação/Opções com `prefers-reduced-motion`; CART6-03 camada Estudo (simulador + termos); CART6-04 camada Operador (payoff + conta); CART6-05 campos de backend aditivos + pytest UGPA3/CXSE3; CART6-06 verbetes KB faltantes.
7. **Reutilizar `PayoffChart.jsx` vs SVG novo (D-08):** recomendação do pesquisador: **SVG novo e enxuto** para o v6 (a regra "sem texto no desenho" e o fundo em duas zonas divergem do componente atual de Opções), mantendo `PayoffChart` intacto na tela Opções. Decisão final é do planner.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | none | not applicable (sem shadcn) |
| third-party | none | not applicable |

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending
