---
phase: 45
slug: card-de-posi-o-estruturada
status: draft
shadcn_initialized: false
preset: none
created: 2026-09-29
---

# Phase 45 — UI Design Contract

> Contrato visual e de interação do card de Posição estruturada (CARD-01..06). Gerado por gsd-ui-researcher, verificado por gsd-ui-checker. Só front (`web/src`) + vocabulário com paridade `skill_ref.py` <-> `copy.js`. Todo número vem do motor determinístico (`estrutura` da Fase 44); o front não calcula nem compõe frase de motor.

## Premissas e ressalvas (ler primeiro)

1. **Mock conferido pelo orquestrador (2026-09-29)** — o pesquisador não conseguiu lê-lo (403); o orquestrador leu `CardEstrutura.dc.html` e `Atual.dc.html` do canvas aprovado. Regra: **o mock vence em layout/hierarquia; tokens, contraste e copy seguem este spec.** Onde a seção "Layout do card" (marcada "conferir com o mock") divergir da tabela abaixo, vale a tabela. Estados e copy do mock (`vencida` com "Resultado final"/"viraram pó", "Ver em Opções", sufixo "(ação a zero)") NÃO valem: D-06 removeu "Ver em Opções" e o padrão conservador de vencida foi aprovado.

   | # | Mock | Este spec (rascunho) | Resolução |
   |---|------|----------------------|-----------|
   | M1 | Resultado é **bloco próprio** abaixo do banner: kicker (10/800, caixa alta) + total 24 MONO + linha `ações … · opções …` 12 MONO | Total 16/700 à direita do header | **Mock vence**: bloco próprio; tamanho 24 é exceção de tipografia a aprovar no plano (herdado do mock; o checker contou 4 tamanhos sem ele) |
   | M2 | Ordem: header → chips → banner → resultado → faixa → **limites (Piso/Teto/Stop + definir stop e alvo)** → pernas + fonte → ações | pernas antes de limites | **Mock vence**: limites antes de pernas |
   | M3 | Kicker do resultado muda: `RESULTADO DA ESTRUTURA`; `SÓ AS AÇÕES — PRÊMIOS INDISPONÍVEIS` (degradado) | não previsto | Adotar; texto vem do motor/`copy`, sem "resultado final" na vencida |
   | M4 | "Registrar saída…" desabilitado + frase ao lado (`0/1000 livres (lastro da call)`; put: "sem lastro") | só botão herdado | Adotar a frase como texto neutro descritivo, com `aria-describedby`; números vêm de `qtyTravada`/qty (nunca calculados por IA) |
   | M5 | Piso/Teto/Stop em 3 linhas rotuladas em caixa `bgBase`; "Sem piso"/"Sem teto" quando aberto | limites só stop/alvo | Adotar as 3 linhas (texto do motor: `faixa.textos`); valores coloridos seguem fora da caixa (contraste) |
   | M6 | Régua fina 2px + traço/rótulo por marcador; "← sem piso"/"sem teto →" nas pontas | trilho 8px + losango/disco + legenda | Manter a forma do mock (traços + rótulos) **com** forma distinta por marcador; trilho neutro (COR-01) |
   | M7 | Estado `vencida`: link `Ver no histórico de operações →` | omitido | Adotar (navegação, alvo 44px); sem "resultado final" |
   | M8 | Chip estudo `ESTUDO · COLLAR` / operador `ESTRUTURA · COLLAR` | chip de estrutura por modo | Igual — sem divergência |

   O planner trata M1–M7 como parte do contrato; conflito residual entre este quadro e "Layout do card" se resolve por este quadro.
2. **CONTEXT D-05 aponta para um lugar que não existe.** "Opções > Operar" foi dissolvida na Fase 39. `ABAS_OPCOES = ["oportunidades","recomendadas","montar"]` (rótulos "Oportunidades", "Destacadas", "Montar"). O fluxo de fechar (`PropostaDoAtivo` -> `fecharLastreada`) só renderiza dentro de **Oportunidades**, quando `oportunidadeAberta` (estado local de `OpcoesScreen`) == ticker. Ver §Navegação do Encerrar: exige um one-shot novo.
3. Sem shadcn/Tailwind: React hand-rolled, estilo inline com tokens `T.*` (CSS vars) e escala `SP`. `Tool: none`; gate de registry não se aplica.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none (React 18 hand-rolled, estilo inline) |
| Preset | not applicable |
| Component library | none (componentes locais em `web/src/App.jsx`, `web/src/opcoes/*`) |
| Icon library | glyphs Unicode inline (`⚠`, `▸`, `✎`, `↻`) + `NavIcon` do app; sem lib nova |
| Font | corpo `SANS` (Nunito, fallback sistema); números/tickers `MONO` (`ui-monospace,'SF Mono',Menlo,Consolas,monospace`) |
| Tokens | `T.*` = `var(--x)` de `PALETTE` (dark/light) + override `MODE_OPERADOR` — 4 combinações: Estudo-escuro, Estudo-claro, Operador-escuro, Operador-claro. **Proibido hex literal no componente novo.** |
| Componente | novo `CardPosicaoEstruturada` (extraído; o card atual segue para ativo sem `optionPositions`) |

---

## Spacing Scale

Só `SP` de `App.jsx:1302` (`{1:4, 2:8, 3:12, 4:16, 5:20, 6:24, 8:32}`); nenhuma exceção óptica nova (lista fechada D-16 do RITMO-01).

| Token | Value | Usage neste card |
|-------|-------|------------------|
| SP[1] | 4px | gap glifo-texto, entre linhas de legenda |
| SP[2] | 8px | gap entre chips, padding interno de callout vertical, altura do trilho da régua |
| SP[3] | 12px | gap entre blocos, padding horizontal de callout, gap entre cards |
| SP[4] | 16px | padding do card (era 14/15 -> 16: empate arredonda para cima, D-15), diâmetro do marcador "hoje", alvo mínimo lateral |
| SP[5] | 20px | — (não usado) |
| SP[6] | 24px | espaço acima da régua para o rótulo "hoje" |

Regras: tap target mínimo **44px de altura** (`minHeight: 44px`) em botão e link novos (o card atual usa 42 — o novo sobe para 44). `gap` entre cards de posição: `SP[3]`. Exceptions: none.

---

## Typography

Blocos novos declaram **4 tamanhos e 2 pesos**, todos já em uso no card. Elementos herdados (AvisoLiquidacao, links, painel de edição, histórico, botão Stop/alvo) ficam **inalterados**.

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Display (ticker; resultado total) | 16px | 700 | 1.2 |
| Body (linhas de perna, valores, texto do motor) | 13px MONO p/ números · 11.5px SANS p/ frases | 400 | 1.5 |
| Label (kicker de bloco, legenda da régua, chips, fonte) | 10.5px | 700 (kicker/legenda/chip) · 400 (linha de fonte) | 1.35 |
| Heading (rótulo de bloco) | usa Label 10.5px/700 com `letterSpacing: 0.06em` (mesmo `kicker`) | 700 | 1.2 |

Pesos: 400 e 700. Não introduzir 600/800 nos blocos novos (existem só nos herdados). Frases do motor: 11.5px/400, `T.textSecondary`. Sem `textFaint` em frase.

---

## Color

Base = tokens vigentes. 60% `T.bgBase` (tela), 30% `T.bgCard` (card) + `T.bgBase` (caixas internas), 10% acento.

| Role | Token | Usage |
|------|-------|-------|
| Dominant (60%) | `T.bgBase` | fundo de tela; caixas internas (callout, bloco de limites) |
| Secondary (30%) | `T.bgCard` (+ `T.borderSubtle`) | superfície do card |
| Accent (10%) | `T.accent` (azul-esverdeado Estudo / dourado Operador) | ver lista abaixo |
| Destructive | `T.negative` | **não há ação destrutiva nova nesta fase.** "Registrar saída…" herdado mantém seu estilo e o modal de confirmação atual |

Accent reserved for: (1) botão "Stop/alvo (IA)" (herdado); (2) link "definir ▸" / "✎ definir stop e alvo" (herdado); (3) link "↻ Atualizar" da estrutura; (4) anel de foco visível dos elementos novos. **Nada mais.** Chips, régua, callouts e "Encerrar estrutura…" são neutros.

Verde/vermelho (`T.positive`/`T.negative`) **só** em: resultado total, resultado de ações/opções/perna (P&L), preços, marcadores de stop/alvo na régua (D-10) e a pill "travada". Nunca em chip, callout, rótulo ou texto de estado (COR-01).

Âmbar `T.warn` / `T.warnTint10`: só no chip "vence …" quando `0 <= diasParaVencimento <= 5` (D-11) e na borda do callout de estado atenção (ate_5_dias / exercicio_provavel).

### Contraste AA medido (4.5:1 texto) — calculado dos hex de `PALETTE` + `MODE_OPERADOR`, com tint composto sobre a superfície

| Par | Est-escuro | Est-claro | Op-escuro | Op-claro |
|-----|-----------|-----------|-----------|----------|
| textSecondary / bgCard | 10.72 | 12.45 | 11.49 | 12.45 |
| textMuted / bgCard | 6.51 | 6.13 | 6.89 | 6.74 |
| textMuted / bgBase | 7.43 | 5.78 | 7.67 | 6.18 |
| textFaint / bgCard (só kicker/fonte) | 4.55 | 5.19 | 4.56 | 5.32 |
| warn / warnTint10 sobre bgCard (chip âmbar) | 7.98 | 4.68 | 8.64 | 4.68 |
| positive / bgCard | 8.52 | 4.77 | 9.13 | 4.77 |
| negative / bgCard (inclui pill sem tint) | 5.60 | 4.79 | 6.00 | 4.79 |

**Regras derivadas das reprovações medidas (o checker deve fazê-las valer):**
- `positive`/`negative` como **texto só sobre `bgCard`**. Sobre `bgBase` no Operador-claro medem 4.38/4.40 (reprova) e no Estudo-claro 4.50/4.52 (limite). Logo: **as caixas internas em `bgBase` levam só texto neutro** (`textSecondary`/`textMuted`); números coloridos (P&L, stop, alvo) ficam fora de caixa `bgBase`, direto no `bgCard`.
- `negative` sobre `negativeTint10` mede **4.18 no claro (reprova)**. `TravaPill` atual reprova AA no tema claro (dívida herdada). **Correção nesta fase:** pill = fundo transparente + borda 1px `T.negative` + texto `T.negative` (mín. 4.79). Aplicar em `TravaPill` inteiro (afeta também `App.jsx:3651`; mudança visual pequena, corrige AA). Atualizar guardião `test_carteira_lastro_ui.mjs` se checar o estilo.
- `accent` sobre `accentTint10` mede 4.33/4.36 no claro (reprova; botão "Stop/alvo (IA)" herdado já está nessa faixa — fora de escopo, registrar como dívida). **Elementos novos não usam accent sobre tint**; "↻ Atualizar" é accent sobre `bgCard` liso (4.94/4.95/5.64/8.34).
- `textFaint` **nunca** sobre tint (mede 3.84–3.93 no escuro). Só sobre `bgCard`/`bgBase` liso e só para kicker/linha de fonte, 10.5px.
- Chip neutro "ESTRUTURA · COLLAR" = `textMuted` sobre `bgBase`, borda `borderSubtle` (5.78 mín.).
- Régua: trilho **neutro** (`T.knob`, faixa piso–teto em `T.borderDashed`), sem gradiente vermelho-verde (o `PlanRuler` viola COR-01 aqui). Trilho/faixa são decorativos (valores repetidos em texto e em `aria-label`); marcadores usam `T.textSecondary` (>= 10:1).

---

## Layout do card [derivado do CONTEXT, conferir com o mock]

Mobile-first (coluna única, 360px como caso limite; `flexWrap` nos chips e no header). Ordem de cima para baixo, todos os blocos com `SP[3]` entre si:

1. **Header.** Esquerda: `TICKER` (16/700 MONO) + `{qty} cotas · PM R$ x` (11.5 `textMuted`); abaixo, fileira de chips (gap SP[2], wrap): chip de estrutura, chip de vencimento, pill "travada" (só com call). Direita (alinhada à direita, MONO): **resultado total** 16/700 colorido por sinal via `moneySigned(resultado.total)`; embaixo 11.5 neutro: `Ações {moneySigned(resultado.acoes)} · Opções {moneySigned(resultado.pernasCotadas)}` (números coloridos por sinal; `null` -> "—" neutro). `total == null` -> "—" em `textMuted` e, abaixo, `resultado.texto` (frase do motor). **Nunca** somar parcial no cliente.
2. `AvisoLiquidacao` — herdado, mesma posição (logo após o header).
3. **Estado.** `vigente` = uma linha 11.5 `textMuted` com `estadoTexto`. Demais estados = callout (ver matriz).
4. **Faixa no vencimento.** Kicker `FAIXA NO VENCIMENTO`; régua; legenda; frases `faixa.textos` (11.5 `textSecondary`, uma por linha); `descobertaTexto` se houver. `faixa == null` -> sem régua, só `motivoFaixaTexto` numa linha 11.5 `textMuted`.
5. **Pernas** (sempre visível, sem acordeão — CARD-03). Kicker `PERNAS`; lista `<ul>` sem marcador; uma `<li>` por perna: `CALL vendida · strike 42,00 · vence 16/10` (13 MONO), `qtd`; segunda linha `prêmio R$ 0,45 -> R$ 0,30` e resultado da perna colorido à direita; se `origemTexto`, 10.5 `textMuted` abaixo. Prêmio atual `null` -> "—" e `sem cotação`. Rótulos "vendida"/"comprada" são dado descritivo (adjetivo), idênticos nos dois modos.
6. **Limites e contexto** (caixa `bgBase`, só texto neutro; valores de stop/alvo coloridos ficam **fora** da caixa, em linha própria sobre `bgCard`):
   - Linha Stop/Alvo: `STOP` / `ALVO` (legenda 10.5) + valor real (13 MONO, `negative`/`positive`) ou `definir ▸` (accent, herdado). Com `estrutura.stopTexto != null`, `STOP` mostra `stopTexto` (proteção pela put) em `textSecondary`, sem número vermelho.
   - Linha de contexto: `N dias em operação · X% do capital` + `R:R atual …` **somente com stop E alvo** (D-08/D-10). `X%` usa `estrutura.acoes.preco * p.qty`, **não** `markPrice` (um só spot no card). Bloco "Entrada pelo setup …" herdado (mesmo `gatStatus`) — o `gatStatus` usa `estrutura.acoes.preco` quando carregada.
   - Aviso "sem stop": ver regra abaixo.
7. **Ações.** Linha 1: `Encerrar estrutura…` (largura total, `minHeight 44`, contorno neutro: borda `borderSubtle`, texto `textPrimary`, fundo transparente). Se bloqueado: `disabled` + `aria-disabled`, texto `textMuted`, e **abaixo** `encerrar.texto` (11.5 `textMuted`, `id` referenciado por `aria-describedby`). Linha 2: `Stop/alvo (IA)` | `{cp.btnVender}…` (herdados, 44px). Sem "Ver em Opções" (D-06).
8. **Links** herdados: `✎ Editar stop/alvo`, `Reanalisar`, `Histórico de análises (n)` + painéis `editFor`/`histFor` inalterados. "Compras desta posição" **não** aparece em posição estruturada (D-09).
9. **Rodapé de fonte.** 10.5 `textFaint`: `fonteEstruturaLinha(fonte, at)` à esquerda; `↻ Atualizar` (accent, alvo 44px) à direita.

### Régua de faixa (CARD-02, D-07, D-10)
- Trilho 8px (`SP[2]`), `T.knob`, cantos 999px. Faixa piso→teto preenchida `T.borderDashed`; extremidade aberta (`piso`/`teto` `null`) vai rente à borda do trilho.
- Domínio = min/max de {piso, teto, PM, hoje, stop?, alvo?}, mapeado em 8%–92% (mesmo `posOf` do `PlanRuler`), para que PM e hoje **fora** da faixa continuem visíveis. Menos de 2 valores numéricos -> sem régua.
- Marcadores (forma distinta, nunca só cor): piso e teto = traço vertical 2px altura 16 `textSecondary`; PM = losango vazado 10px acima do trilho `textSecondary`; **hoje** = disco 16px `textPrimary` com anel `bgCard`, rótulo `hoje R$ x` 24px acima (usa `estrutura.acoes.preco`); stop = traço `T.negative`, alvo = traço `T.positive` (extras, só se definidos).
- Legenda (fixa nesta ordem, 10.5): `PISO x` · `PM x` · `HOJE x` · `TETO x`; `null` -> `sem piso` / `sem teto`. Stop/alvo ficam na linha de limites, não na legenda.
- Acessibilidade: container `role="img"` com `aria-label` = `cp.estruturaFaixaAria(nomeTexto, faixa.textos.join(" "), hoje, pm)` (só texto do motor + números). Sem animação (respeita `prefers-reduced-motion` por ausência).

---

## Estados (princípio 9) — todos os tratamentos

Decisão do estado vem de `estrutura.estado`; o chip âmbar vem de `diasParaVencimento` (não do estado, porque `premio_indisponivel`/`exercicio_provavel` têm precedência sobre `ate_5_dias`).

| Estado | Chip vence | Bloco de estado | Resultado | Encerrar |
|--------|-----------|-----------------|-----------|----------|
| carregando (1ª leitura) | — | linha `role="status"` `lendo` sob o header; card ATUAL completo abaixo | P&L das ações (atual) | não exibido |
| falha (timeout 30s / 502 / `estrutura: null` com pernas locais) | — | linha `role="status"` `indisponivel` + `↻ Atualizar`; card ATUAL completo | P&L das ações (atual) | não exibido |
| vigente | neutro `vence DD/MM · N dias` | linha `textMuted` com `estadoTexto` | total | habilitado |
| <=5 dias | **âmbar** (`0<=dias<=5`) | callout borda `T.warn`, glifo `⚠` aria-hidden, texto `textSecondary` = `estadoTexto` | total | habilitado |
| exercício provável | âmbar se dias<=5, senão neutro | callout borda `T.warn` = `estadoTexto` | total | habilitado |
| prêmio indisponível | neutro | callout borda `T.borderDashed`, glifo `ⓘ` = `estadoTexto`; pernas mostram "—" | **só ações**; total "—" + `resultado.texto` | `disabled` + `encerrar.texto` |
| vencida | neutro `vencida em DD/MM` | callout borda `T.textMuted` = `estadoTexto`; `AvisoLiquidacao` permanece | total se o motor devolver, senão "—" + `resultado.texto`; **sem** "resultado final" nem "viraram pó" | `disabled` + `encerrar.texto` |
| aberta sem proposta (eixo à parte) | — | linha extra `motivoSemPropostaTexto` (11.5 `textMuted`) sob o botão Encerrar; **não** bloqueia | — | conforme `encerrar` |
| mercado fechado | — | sem banner novo: o motor marca a perna pelo último negócio e devolve `origemTexto` por perna (mostrado) | — | — |
| dado atrasado | — | **gap**: `estrutura` não carrega flag de atraso/tempo real. Rodapé mostra só a hora da leitura (ver Fonte). Registrado em Perguntas | — | — |

Regras transversais:
- **Aviso "Posição sem stop definido" (CARD-05):** aparece **só** se `p.stop == null` **e** `estrutura` carregada **e** `estrutura.stopTexto == null` (put cobrindo todas as ações é o único caso que gera `stopTexto`). Call coberta pura ou put parcial mantêm o aviso (é verdadeiro). **Suprimido** em carregando e em falha (D-03). Texto do aviso na variante estruturada: chave `aviso_sem_stop` (a régua acima agora é a de faixa, então a frase antiga "pela régua acima" fica errada).
- **`R:R`** nunca renderiza `—`: some quando não há stop E alvo.
- `estrutura: null` **não** significa "sem opções" (a rota engole exceção em `null`). Decidir por `data.optionPositions` local: pernas locais + `null` = falha; sem pernas locais = card atual (D-02).
- `fora_da_biblioteca` (`nome == null`): chip genérico `ESTRUTURA · OPÇÕES`, `nomeTexto` como linha 11.5 sob os chips, sem régua (`motivoFaixaTexto`).
- `put_protecao`/`call_coberta`: mesmo layout; chip com o nome; `Sem piso`/`Sem teto` conforme a legenda.

---

## Busca e recarga da estrutura (D-01..D-04, refinado)

- Tickers-alvo: `new Set(data.optionPositions.map(o => o.underlying))` ∩ `data.positions`. Sem chamada extra para descobrir — o front já sabe (mesma derivação de `App.jsx:3605`, `myOptionPositions`). Chamada: `store.optionsProposta(t, true)`, paralelas com teto de concorrência 3 (premissa; cada chamada calcula proposta e consome cota brapi). Guardar `resposta.estrutura`, `resposta.source`, `resposta.at`.
- **Chave do efeito = assinatura estável**, não a identidade do array: `sort( id:qty:side por perna do ticker )` + `ticker:qty:avg` da ação + `ctx.operador`. Recarrega quando: monta a tela, a assinatura muda (buy/sell/fechar), **troca Estudo<->Operador** (a rota devolve o texto no `appMode` do servidor; sem refetch a frase fica no modo errado) ou toque em `↻ Atualizar`. Sem polling.
- Ao mudar a assinatura de um ticker: descartar a estrutura antiga desse ticker (volta a "carregando"; nunca mostrar número de pernas antigas) e aplicar **last-response-wins** (token por requisição). Troca de conta/escopo limpa o mapa inteiro.
- `↻ Atualizar` desabilitado enquanto há requisição em voo para o ticker.

## Navegação do "Encerrar estrutura…" (D-05) — ponto de código para o planner

`ctx.goOpcoes(aba)` (App.jsx:9127) só leva **aba**; `tickerInicialOpcoes` só lê `ctx.opcoesMemoria` (`{ticker, aba}`) e só aceita ticker presente em `carteira`; `oportunidadeAberta` é estado local **sem deep-link**. Contrato novo (mínimo, one-shot, mesmo padrão de `opcoesAbaInicial`):
1. `ctx.goOpcoes("oportunidades", { abrirTicker: t })`: além de `setOpcoesAbaInicial`, grava `setOpcoesMemoria({ ticker: t, aba: "oportunidades" })` e um novo `opcoesAbrirTicker` (limpo por `ctx.limparOpcoesAbrirTicker`, junto do `limparOpcoesAbaInicial`).
2. `OpcoesScreen`: inicializador lazy de `oportunidadeAberta` = `abrirTicker` se estiver em `carteira`, senão `null` (sem salto, sem `useEffect` pós-paint, igual à Fase 40 D-05).
3. Guardião novo: `goOpcoes` com e sem 2º argumento; ticker fora da carteira -> `null`; one-shot limpo.
Risco a checar na implementação: `pos_op_aberta` (main.py) é só a **primeira perna com `lastro`**; para put de proteção isolada ou para a segunda perna do collar, o painel pode não oferecer "encerrar". O card **só promete navegar**; o destino mostra o estado honesto do motor (`PropostaDoAtivo`: sem liquidez / sem proposta). No Estudo, o destino explica que não executa (403 na rota). Não fechar duas pernas no card (sem atomicidade).

## Fonte e horário (princípio 3)

A rota devolve `source` (cadeia da proposta) e `at` (instante em que a **resposta foi montada**, não horário do pregão), mais `providerStatus` da proposta — que **não** descreve a cadeia que marcou as pernas (essa falha vira perna sem cotação). Contrato conservador: rodapé `fonteEstruturaLinha(FONTE_LABEL(source), at)` = "Opções lidas de {fonte} em {dd/mm/aaaa hh:mm}"; sem `source` -> `fonteEstruturaSemDado`. Nunca "cotação de", nunca hora inventada. Prêmio pelo último negócio: `origemTexto` da perna. Reusar `FONTE_LABEL` de `PropostaLastreada.jsx` (exportar se necessário).

---

## Copywriting Contract

### Chaves de voz por modo — nascem em `skill_ref.py` (novo dict `ESTRUTURA_CARD`, formato rígido: um par por linha, sem aspas internas) e ganham espelho byte a byte em `copy.js` `COPY[modo].estruturaCard`

Dict novo (e não novas chaves em `ESTRUTURA_POSICAO`) para **não** quebrar o guardião da Fase 44 (`test_estrutura_espelho.mjs` exige o conjunto exato de chaves). Guardião novo espelha `ESTRUTURA_CARD`, proíbe âncoras (`trava protetora`, `abate o custo`) e, no Estudo, `\bcomprar\b|\bvender\b`.

| Chave | Operador | Estudo |
|-------|----------|--------|
| `chip_estrutura` | `ESTRUTURA · {nome}` | `ESTUDO · {nome}` |
| `chip_estrutura_generica` | `ESTRUTURA · OPÇÕES` | `ESTUDO · OPÇÕES` |
| `lendo` | `Lendo a estrutura de opções…` | `Lendo a estrutura de opções desta posição…` |
| `indisponivel` | `Estrutura indisponível agora. Pernas abertas seguem na carteira — nada estimado.` | `Não foi possível ler a estrutura de opções agora. As pernas abertas continuam na sua carteira, e nenhum valor é estimado no lugar.` |
| `badge_travada_collar` | `{qty} travada(s) · lastro da CALL do collar` | `{qty} travada(s) · lastro da call do collar` |
| `aviso_sem_stop` | `Posição sem stop definido — defina em Editar stop/alvo ou peça a sugestão da IA.` | `Esta posição não tem stop definido. Defina em Editar stop/alvo ou peça a sugestão da IA.` |

`{nome}` = `estrutura.nomeTexto.toUpperCase()` (uppercase é formatação; o texto vem do motor). Pill "travada": `nome == collar` -> `badge_travada_collar`; `call_coberta` ou `fora_da_biblioteca` com `qtyTravada > 0` -> `cp.badgeTravada` existente; `put_protecao` **sem pill** (put comprada não soma em `qtyTravada`: `store.py:1018` só a call coberta incrementa). Condição de exibição: `p.qtyTravada > 0`.

### Chaves neutras (idênticas nos dois modos) — só em `copy.js` (`cp.*`), guardião de igualdade Estudo=Operador

`estruturaResultadoRotulo` "Resultado da estrutura" · `estruturaAcoesRotulo` "Ações" · `estruturaOpcoesRotulo` "Opções" · `estruturaFaixaTitulo` "FAIXA NO VENCIMENTO" · `estruturaPernasTitulo` "PERNAS" · legenda "PISO"/"PM"/"HOJE"/"TETO"/"STOP"/"ALVO" · `semPiso` "sem piso" · `semTeto` "sem teto" · lado "vendida"/"comprada" · `chipVence(ddmm, dias)` "vence {ddmm} · {dias} dia(s)" · `chipVenceHoje` "vence hoje" · `chipVencida(ddmm)` "vencida em {ddmm}" · `btnEncerrarEstrutura` "Encerrar estrutura…" · `btnAtualizarEstrutura` "Atualizar" · `fonteEstruturaLinha(fonte, quando)` "Opções lidas de {fonte} em {quando}" · `fonteEstruturaSemDado` "Fonte das opções não declarada." · `estruturaFaixaAria(nome, textos, hoje, pm)` "{nome}. {textos} Hoje R$ {hoje}. Preço médio R$ {pm}." · `encerrarAria(t)` "Encerrar estrutura de {t}: abre a aba Opções em {t}".

| Element | Copy |
|---------|------|
| Primary CTA | `Encerrar estrutura…` (igual nos dois modos, D-06) |
| Empty state | Não há estado vazio novo: sem `optionPositions` o card é o atual (D-02). Card estruturado sem dado -> estados carregando/falha acima |
| Error state | `indisponivel` (tabela) + `↻ Atualizar` — problema + caminho |
| Destructive confirmation | Nenhuma ação destrutiva nova. `Registrar saída…` / `Simular venda…` herdados mantêm o modal atual |

Tom: sem promessa de lucro, sem "resultado final", sem "opções viraram pó". Números do mock são ilustrativos; nenhum literal de valor no código.

### Reconciliação de "trava protetora" (item 2) — chave a chave

Verificado: `tiraOpcoesMotivo` (ambos os modos) **já usa "collar"** e não tem âncora — nada a reconciliar ali; `tiraOpcoesMotivo.aberta_sem_proposta` fica, o card usa `estrutura.motivoSemPropostaTexto`. Alterações em `copy.js` (o guardião `test_opcoes_collar_vocab.py` é case-sensitive e `trava(s) protetora(s)` escapa por causa do "(s)", então hoje só passa por acidente):

| Chave | Hoje | Passa a ser |
|-------|------|-------------|
| `eyebrowPropostaCollar` Estudo (l.728) | `ESTUDO · TRAVA PROTETORA` | `ESTUDO · COLLAR` |
| `eyebrowPropostaCollar` Operador (l.1583) | `PROPOSTA · TRAVA PROTETORA` | `PROPOSTA · COLLAR` |
| `collarPernasLinha` (l.729, 1584) | `{n}× TRAVA {t} · call … / put …` | `{n}× COLLAR {t} · call … / put …` |
| `ctaCollarDebito`/`ctaCollarCredito` Operador (l.1585-1586) | `Montar {n}× trava …` | `Montar {n}× collar …` |
| `confirmAbrirCollar` Operador (l.1587) | `Montar {n} trava(s) protetora(s) de {t} trava {qty} …` | `Montar {n} collar(s) de {t} — trava {qty} ação(ões) do seu lote-lastro (perna da call) …` (resto idêntico) |
| `badgeTravada` | `lastro de CALL` / `lastro da call coberta` | inalterado (collar usa `badge_travada_collar`) |
| `skill_ref.py` `OPCOES_LASTREADAS[*]["collar"]` (l.623, 670: manchete do motor com "trava protetora … abate o custo") | — | **NÃO tocar por padrão.** É manchete do card de decisão (guardrail CVM, âncora só em `skill_ref`). O comentário `skill_ref.py:743` atribui a troca à Fase 45, mas mexe em texto regulado -> Pergunta 1 |

Guardiões a atualizar **com nota de reversão deliberada** (nunca apagar): `web/tests/test_opcoes_collar_ui.mjs` (lê `eyebrowPropostaCollar`, `ctaCollar*`, `confirmAbrirCollar` — l.270-274), `web/tests/test_vocabulario_opcoes.mjs` se tocar essas chaves, `REQUIREMENTS.md` CARD-06 (nota D-11: pill só com call), e adicionar `CardPosicaoEstruturada` à lista de funções varridas por `web/tests/test_ritmo_sp.mjs` (hoje cobre só `SinalChip`/`LinhaContexto`/`PlanoOperacionalBloco`, não este card).

### CARD-06 — reversão deliberada (D-11)
"`badgeTravada` cobre collar e put de proteção" **não** vale: put comprada não trava ações. Pill vermelha só onde há call vendida; put de proteção é coberta pelo chip neutro. `REQUIREMENTS.md` CARD-06 ganha a nota; o planner registra.

---

## Interação e acessibilidade

- Foco: `:focus-visible` com anel `T.accent` 2px offset 2px em todo botão/link novo (herdar o padrão do app; se inexistente, definir no componente).
- Ordem de tab: Encerrar -> Stop/alvo (IA) -> Registrar saída -> Editar stop/alvo -> Reanalisar -> Histórico -> Atualizar.
- `disabled` do Encerrar: `aria-disabled="true"` + `aria-describedby` no motivo; o motivo é texto visível, não tooltip.
- Chips: `<span>` não interativos; fileira com `role="group" aria-label="Estrutura de opções"`. Pill travada: texto visível basta.
- Estados de carregamento/falha: `role="status"` `aria-live="polite"`; sem spinner animado.
- Lista de pernas semântica (`ul/li`); cada resultado numérico com sinal explícito (`moneySigned`), nunca só cor.
- Nenhum `aria-label` que reescreva valor do motor; só concatena texto do motor.
- `Registrar saída…`: continua `ctx.A.openSell(p.t)`, que já limita a `qtyLivre` (lastro); o aviso `avisoTravaNaVenda` existente é reusado, sem mudança.

---

## Fora de escopo (invariantes)
Sem ordem nova, sem rota nova, sem fill parcial, sem estrutura além das 3, sem tocar manchete/decisão do motor, sem cálculo financeiro no front, sem polling, sem "Encerrar" inline.

## Validação exigida
`npx vite build` (front editado); `bash scripts/executar.sh --testes` uma vez por onda (orquestrador); guardiões novos: espelho `ESTRUTURA_CARD`, `goOpcoes` one-shot, aviso "sem stop" só com `stopTexto == null` e estrutura carregada, contraste dos 7 pares da tabela nas 4 combinações, pill travada só com `qtyTravada > 0`, ausência de âncoras.

---

## Perguntas em aberto (assumi o padrão indicado; nenhuma bloqueia)

1. Mexer na manchete `collar` de `skill_ref.py:623/670` (texto regulado, guardrail CVM)? Padrão assumido: **não**; a exigência "âncora ausente" vale para todo texto visível **do card**. Se sim, exige texto aprovado pelo Alex.
2. ~~Mock não lido~~ — conferido pelo orquestrador; divergências M1–M7 em §Premissas. Pendente do Alex só: aceitar o tamanho 24 do total (M1).
3. Princípio 3: `estrutura` não traz flag de atraso/tempo real nem horário do dado. O card mostra só a hora da leitura. Quer campo aditivo no motor (quick/fase própria) ou aceita o gap?
4. O destino do "Encerrar" só oferece fechar a **perna com lastro** (`pos_op_aberta`). Put isolada e 2ª perna do collar podem não ter caminho de encerramento em Oportunidades. Verificar `A.fecharLastreada`/rota com `contractSymbol` de put antes de prometer o fluxo na copy do Estudo.
5. `↻ Atualizar` incluído por padrão (D-04 deixou opcional): só por toque, 1 chamada por ticker, sem polling. Remover se a cota brapi preocupar.
6. `TravaPill` global muda de tint para contorno (corrige AA 4.18 no claro; afeta também o AtivoCard). Aceitar ou restringir ao card novo e manter a dívida.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | none | not applicable (sem shadcn) |
| third-party | none | not applicable |

---

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS
- [x] Dimension 2 Visuals: PASS
- [x] Dimension 3 Color: PASS
- [x] Dimension 4 Typography: PASS
- [x] Dimension 5 Spacing: PASS
- [x] Dimension 6 Registry Safety: PASS

**Approval:** APPROVED (gsd-ui-checker, 2026-09-29; 6/6). Ressalva: M1–M7 (conferência com o mock) adicionados após a aprovação, por orquestrador — plan-checker deve verificá-los.
