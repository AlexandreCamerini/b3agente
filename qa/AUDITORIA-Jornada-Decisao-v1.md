# Auditoria — Jornada de Decisão (Acompanhar · Mesa · Monitoramento · Posições)

> Sessão: /design-audit, gatilho = achado ao vivo do Alex em TestFlight (screenshot da Mesa,
> ativo UGPA3: "muita informação e de forma confusa, não sei se é pra vender ou comprar").
> Estágio: **mapeamento do código real + achados + proposta de fases**. Nada aplicado ao
> código ainda — este documento é o artefato de aprovação, no mesmo formato que gerou a
> Fase 39/NAV-01 a partir de uma auditoria anterior da aba Opções.

## 0. Escopo real vs. escopo pedido

O pedido cobria 4 telas (Acompanhar, Mesa, Monitoramento, Posições). O código revela que isso
é **um só componente reaproveitado**, não quatro implementações:

> `AtivoCard` (`web/src/App.jsx:3343`) — comentário do próprio código: *"CARD ÚNICO DO ATIVO —
> fonte única de renderização em todas as abas (watchlist, radar, posições, home)."*

Ou seja: os achados abaixo, encontrados a partir do screenshot da Mesa, **se propagam
automaticamente** para as outras 3 telas — não é um bug isolado de uma tela, é um problema de
hierarquia visual na camada de indicadores que todo o app compartilha. Isso muda o cálculo de
esforço: corrigir o componente compartilhado corrige a jornada inteira de uma vez.

Não aprofundei código específico de Monitoramento/Posições além do que o AtivoCard/KpiBlock já
cobre — se essas telas tiverem composição própria de indicadores além do card único, é um
achado potencial da Fase 1 de implementação, a confirmar ao abrir cada tela no ambiente local.

## 1. Diagnóstico — por que "cada indicador parece falar uma coisa diferente"

O card não tem dado errado nem lógica contraditória (validei contra `setups.py`,
`signal_ledger.py`, `regime.py` — a decisão COMPRAR/VENDER e a elegibilidade estatística são
propositalmente duas trilhas independentes, e isso é correto por design). O problema é
**puramente de camada visual**: três falhas concretas, cada uma confirmada em código.

### 1.1 — CRÍTICO: colisão de canal de cor (vermelho carrega dois significados diferentes)

`HISTORICO_PILL_STYLE` (`App.jsx:6552-6558`):
```js
const HISTORICO_PILL_STYLE = {
  elegivel: [T.positive, T.positiveTint10],
  inelegivel: [T.negative, T.negativeTint10], // MESMO peso visual do positivo — nunca dim
  ...
};
```
`T.negative` é o **mesmo token** usado para: decisão VENDER (`REC_STYLE["VENDER"]`,
`App.jsx:1286`), direção "Baixa" (`DIR_STYLE`, `App.jsx:1063`), e P&L negativo. Ou seja, "×
NÃO ELEGÍVEL" (que significa **"não medimos vantagem estatística nesta janela"** — um aviso de
HONESTIDADE DE DADO, ver `signal_ledger.py:188`) usa a cor vermelha, exatamente a mesma que
"você está perdendo dinheiro" e "o mercado está caindo". Dois eixos semânticos completamente
diferentes (direção de mercado × confiabilidade estatística do padrão) competem pelo mesmo
canal de cor. Resultado: o usuário lê "mais um sinal vermelho" reforçando VENDER, quando na
verdade é um aviso ortogonal que poderia aparecer do mesmo jeito ao lado de um COMPRAR.

A intenção original (comentário "nunca dim") era correta — não esconder má notícia
(princípio 4 do CLAUDE.md). O erro foi reaproveitar o MESMO hue de mercado para fazer isso, em
vez de um canal de cor próprio (ex.: âmbar/neutro para "sem vantagem medida", reservando
vermelho/verde só para direção de preço e P&L).

### 1.2 — CRÍTICO: a mesma métrica aparece duas vezes, em dois idiomas visuais, em pontas opostas do card

`App.jsx:6842` (topo do corpo do card): `tierLabel = tierOf(r.confluencia)[1]`, renderizado como
```
confiança FORTE   ← pill cinza neutro, border, App.jsx:6871
```
`App.jsx:6919` (rodapé do mesmo card, ~80 linhas depois): o MESMO `tierOf(r.confluencia)`:
```
<ConfluenceRing conf={r.confluencia} .../>
"Forte · aderência ao padrão de estudo"   ← anel colorido, App.jsx:6917-6920
```
É o mesmo número, calculado da mesma variável, mostrado duas vezes com dois desenhos
diferentes (pill de texto vs. anel gráfico), sem nenhuma pista visual de que são a mesma coisa.
No screenshot do Alex isso aparece como "confiança FORTE" no topo e "100% · Forte" embaixo —
parecem dois indicadores concordando por coincidência, não o mesmo dado.

### 1.3 — CRÍTICO: três estilos de "chip de sinal" diferentes, sem contrato visual comum

| Componente | Estilo | Onde |
|---|---|---|
| `chip()` interno do AtivoCard | fundo cinza sólido (`T.bgBase`), sem borda | `App.jsx:3345-3349` |
| `FundamentoChip` / `RegimeChip` | sem fundo, borda colorida pela cor semântica | `App.jsx:1368-1399` |
| `HistoricoPill` | fundo colorido pela cor semântica, sem borda | `App.jsx:6552-6607` |
| pill de "confiança X" | sem fundo, borda cinza neutra (`T.borderSubtle`), texto sempre `T.textMuted` mesmo quando o valor é "FORTE" | `App.jsx:6871` |

Quatro receitas visuais para o mesmo conceito de UI ("aqui vai um chip de estado"). Como a
forma não carrega significado (não há uma gramática tipo "borda = contexto, fundo sólido =
veredito"), a única forma de saber o que é primário e o que é secundário é **ler cada palavra**
— exatamente o esforço cognitivo que o Alex descreveu.

### 1.4 — Achado de processo (não é regressão, é um teto que a correção anterior não alcançou)

Comentário do próprio código, `App.jsx:3571-3573` (qa/49, v11): *"indicadores unificados em
chips (mesmo peso); confluência e fundamento deixam de ser vereditos concorrentes."* Essa
correção anterior resolveu "os chips brigam entre si por serem tratados como veredito" —
nivelando tudo ao mesmo peso visual. Efeito colateral não previsto: nivelar tudo removeu
qualquer hierarquia entre "isto é o veredito", "isto é evidência de apoio" e "isto é uma
ressalva de confiabilidade". O pedido do Alex é exatamente o próximo degrau dessa correção:
não voltar a ter vereditos competindo, mas agora **diferenciar por peso visual real**
(tamanho, posição, presença/ausência de cor) o que é decisão do que é contexto.

## 2. O que NÃO mexer (validado no código, correto por design)

- A manchete (COMPRAR/VENDER/AGUARDAR/NÃO OPERAR) já vem só do motor determinístico
  (`setups.py:plano_operacional`, `kpi.py`) — nenhuma proposta abaixo toca nisso, só em COMO
  ela é apresentada.
- A separação entre decisão (geométrica, setup vs. preço) e elegibilidade (estatística,
  `signal_ledger.py`) é uma decisão de produto correta e deliberada (ADR-017) — o objetivo é
  tornar essa separação MAIS legível, nunca escondê-la ou fundir as duas trilhas numa síntese.
- `ConfluenceRing`, `chipModo`, tokens por modo — já implementados a partir da auditoria de
  design system anterior (`qa/AUDITORIA-Design-System-v1.md`, 2026-07) e funcionando.

## 3. Plano de fases

### Fase 1 — Crítico (resolve a confusão relatada)

1. **Token de cor próprio para o eixo "confiabilidade estatística"**, separado do eixo
   "direção de mercado/P&L". Proposta: `T.warnMuted` (âmbar dessaturado) para `inelegivel`,
   mantendo `T.positive` para `elegivel` (vantagem medida É boa notícia, esse lado pode
   continuar verde) — o que muda é só o lado negativo, que sai do vermelho de "venda/prejuízo"
   para um "atenção, sem dado" claramente diferente. Arquivo: `App.jsx:6552-6558`
   (`HISTORICO_PILL_STYLE`). Precisa de token novo em `PALETTE` (todos os 4 temas ×2 modos,
   `App.jsx:~115-220`) — não hardcodear hex solto.
2. **Eliminar a duplicidade confiança/confluência.** Escolher UM lugar para o tier de
   confluência — recomendo manter só o `ConfluenceRing` (mais informativo, já mostra %) e
   remover o pill "confiança X" solto (`App.jsx:6871`) OU inverter: mover o `ConfluenceRing`
   pra cima, perto da manchete, e remover a repetição embaixo. Qualquer uma resolve a
   duplicidade; a escolha é sobre ONDE o usuário deve olhar primeiro — recomendo perto da
   manchete, já que é a evidência mais direta de "o quão bem o padrão bateu".
3. **Um componente `SinalChip` único**, substituindo as 4 receitas (`chip()`, `FundamentoChip`,
   `RegimeChip`, pill de confiança solto) por um único componente parametrizado com 2 variantes
   claras por contrato: `peso="primario"` (usado só pela manchete/decisão) e
   `peso="contexto"` (todo o resto — fundamento, regime, elegibilidade, confiança). O visual de
   cada peso é fixo e não escolhido por chamada; hoje quem decide a "importância" é o
   desenvolvedor lendo o texto, deveria ser o componente.
4. **Reordenar por hierarquia de leitura**, não por ordem de implementação: (a) manchete/
   decisão, (b) plano operacional (entrada/stop/alvo) quando existir, (c) UMA linha de contexto
   agrupado (regime + fundamento + confluência, mesmo peso "contexto"), (d) elegibilidade
   estatística com rótulo textual explícito de reconciliação — ex. um microtexto fixo tipo "o
   padrão bateu os critérios; o histórico de {n} ocorrências mostra {elegível/sem vantagem
   medida}" em vez de dois pills soltos que o usuário tem que conciliar sozinho.

### Fase 2 — Refinamento

- Padronizar espaçamento entre os blocos do card (manchete → plano → contexto → elegibilidade)
  na escala 4/8pt já proposta em `qa/AUDITORIA-Design-System-v1.md §3.2` (ainda não
  formalizada como tokens `--sp-*` no código — hoje são valores soltos tipo `"11px"`,
  `"9px"`).
- Microtexto de reconciliação (item 4 da Fase 1) deve ter uma versão por modo (Estudo
  explicativo, Operador direto) — usar o par `server/app/skill_ref.py` / `web/src/copy.js`
  já existente, não inventar string nova solta no componente.
- Revisar `KpiBlock`/`KpiCell` (`App.jsx:1316-1356`, tela de detalhe técnico aberta via "abrir
  gráfico de velas") contra o mesmo componente `SinalChip` da Fase 1 — hoje usa uma 4ª receita
  visual (grid de caixas cinzas) para direção/convicção/qualidade, que são conceitualmente os
  mesmos "chips de contexto" do AtivoCard.

### Fase 3 — Polish

- Motion: ao trocar de tier de confluência (ex. reordenar Radar), considerar transição suave no
  `ConfluenceRing` em vez de salto abrupto do arco.
- Acessibilidade: `HistoricoPill` já tem `aria-label` bem escrito (`App.jsx:6592`) — replicar
  esse padrão pro `SinalChip` novo, hoje `chip()`/`FundamentoChip`/`RegimeChip` não têm
  `aria-label`, só o texto visual.
- Dark/light: os 4 temas já têm tokens próprios de `positive`/`negative`/`accent`
  (`App.jsx:115-220`) — o token novo do item 1 da Fase 1 precisa das 8 variações (4 temas × 2
  modos), conferir contraste AA em todas antes de fechar.

## 4. Critério de aceite

- Vermelho/verde nunca mais representam dois eixos semânticos diferentes no mesmo card
  (grep final: `HISTORICO_PILL_STYLE` não referencia `T.negative`/`T.positive` diretamente).
- Confluência aparece em UM lugar só por card.
- Um único componente de chip de contexto, dois pesos visuais fixos (primário/contexto), zero
  receita nova de pill fora dele.
- Manchete determinística intocada — nenhum teste de `setups.py`/`kpi.py`/`signal_ledger.py`
  muda.
- Verificação humana ao vivo (mesmo padrão das Fases 35-39): Alex olha o card de UGPA3 (ou
  equivalente) reconstruído e confirma que consegue dizer, em menos de 3 segundos, qual é o
  veredito e o que é só contexto.
