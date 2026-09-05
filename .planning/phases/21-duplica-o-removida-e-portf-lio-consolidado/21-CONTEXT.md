# Phase 21: Duplicação removida e Portfólio consolidado - Context

**Gathered:** 2026-09-05
**Status:** Ready for planning
**Mode:** Smart discuss, autonomizada — mesma autorização da Fase 20 (o Alex
pediu para a sessão evoluir até o fim sem pausar por aprovação por área).

<domain>
## Phase Boundary

O usuário para de ver a mesma informação duas vezes: a curva de patrimônio
existe em uma única tela (Acompanhar), o status do Operador aparece uma vez
só em Operador IA, os números do Portfólio viram um card denso (padrão de
"Resumo do dia"), e o gráfico de patrimônio deixa de mostrar caixa vazia
quando ainda há pouco dado (1-2 pontos).

</domain>

<decisions>
## Implementation Decisions

### DEDUP-01 — Qual instância de `CapitalCurve` remove
- Remove a chamada de `App.jsx` (linha ~8974, dentro da rota "carteira" —
  `<CapitalCurve ctx={ctx} /><CarteiraScreen ctx={ctx} />`), mantendo a
  instância de `EvolucaoScreen`/Acompanhar (linha ~1976) como a única.
  Acompanhar é a tela dedicada a desempenho/curva por desenho (funil
  canônico "Acompanhar → Radar → Watchlist → Portfólio → Operador IA"); o
  Portfólio ganha o card consolidado de DEDUP-03 no lugar, que já cobre
  patrimônio/resultado sem repetir a curva completa.
- Alternativa descartada: manter a curva em Portfólio e remover de
  Acompanhar — rejeitada porque Acompanhar é a home/primeira tela, e a
  curva de performance é o gancho de engajamento diário (linguagem do
  próprio copy: "Sua curva começa amanhã. Volte para vê-la crescer").

### DEDUP-03 — Formato do card consolidado do Portfólio
- Um único card com grid de 2 colunas (`display:"grid", gridTemplateColumns:"1fr 1fr"`
  ou `repeat(2, 1fr)`), 4 células: Patrimônio total, Resultado aberto, Caixa
  disponível, Em posições — mesmo padrão visual/densidade de "RESUMO DO DIA"
  em `EvolucaoScreen` (rótulo pequeno uppercase + valor grande MONO logo
  abaixo, dentro do MESMO `card` style já usado no arquivo).
  Reaproveitar os tokens `numBody`/`numMicro` da Fase 20 para os valores
  (numBody pro valor principal de cada célula, numMicro pro rótulo — ou
  manter o rótulo no estilo `kicker` já existente se for mais consistente
  com "Resumo do dia": decisão de detalhe fica com o planner, usar o card
  de Resumo do Dia como referência byte a byte de espaçamento).
- Substitui os 4 cards separados hoje empilhados (Patrimônio total /
  Resultado aberto / Caixa disponível / Em posições) por 1 card só.

### DEDUP-02 — Card de status do Operador IA
- Remover inteiramente o card de texto "Modo do app: Estudo / Operador no
  servidor: Desligado / Executar/sinalizar: Apenas sinalizar / Trocar
  modo →" (topo de `AgenteScreen`) — é puramente redundante com o card
  funcional "OPERADOR NO SERVIDOR · 24×5 / INATIVO · Apenas sinalizar" com
  o toggle real, que já mostra a mesma informação de forma acionável logo
  abaixo.
- O link "Trocar modo →" que vivia no card removido precisa de um novo lar:
  mover para dentro do card funcional (ex.: um link textual abaixo do
  toggle) ou para o Perfil, que já tem o controle "Modo de trabalho"
  (Estudo/Operador) completo — preferir reusar o link do Perfil (evita
  duplicar o MESMO controle em dois lugares, e o Perfil já é a fonte única
  dessa troca desde a Fase 20 não tocar nisso). Decisão de destino exata
  fica com o planner, com a régua: "Trocar modo" não pode desaparecer sem
  substituto navegável.
- Alternativa descartada: fundir os dois cards num só (texto + toggle) —
  mais trabalho de redesenho para o mesmo resultado que remover o
  redundante; a informação do card de texto já está 100% coberta pelo card
  funcional.

### FIX-03 — Placeholder do gráfico com 1-2 pontos
- Quando `data.length` (histórico de patrimônio) for 1 ou 2, mostrar um
  placeholder dedicado — mesma família visual do placeholder de 0 pontos já
  existente ("Sua curva começa amanhã..."), mas com texto que reconhece que
  JÁ HÁ dado, só não o suficiente pra plotar uma curva com sentido (ex.:
  "Só 1 dia registrado ainda — a curva aparece a partir do 3º dia" ou
  redação equivalente, tom professor/mesa conforme o modo ativo via `cp.*`
  se já existir uma frase pronta no vocabulário do backend; senão, uma
  string nova em `copy.js`, nunca hardcoded só no front sem seguir o padrão
  Estudo/Operador do resto do app).
- Nunca renderizar a lib de gráfico (`lightweight-charts` ou o SVG/canvas
  que for) com 1-2 pontos — é a causa raiz da caixa vazia com escala
  degenerada.
- Limite exato (1-2 pontos = placeholder, 3+ = curva normal) fica com o
  planner decidir o valor de corte preciso lendo o código de
  `CapitalCurve`/`equityCurve`, mas a intenção é clara: qualquer quantidade
  de dado insuficiente pra uma escala de eixo Y com sentido usa o
  placeholder, não a lib.

### Claude's Discretion
- Nome exato da nova prop/variável de corte (`data.length < 3`, etc.) e se
  o placeholder de "pouco dado" é uma variação do componente de placeholder
  de "zero dado" ou um componente novo — decisão de implementação, não de
  produto.
- Ordem das 4 células do grid em DEDUP-03 (Patrimônio total / Resultado
  aberto / Caixa disponível / Em posições) — manter a ordem atual de leitura
  de cima pra baixo, a menos que o planner ache uma ordem mais natural em
  grid 2×2.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `CapitalCurve` (`App.jsx:~1670`) — componente único hoje chamado 2x
  (`App.jsx:~1976` em `EvolucaoScreen`, `App.jsx:~8974` antes de
  `CarteiraScreen`) — confirmado por `grep -n "<CapitalCurve"` na sessão de
  auditoria original.
- `card` (objeto de estilo compartilhado, `App.jsx:~287`) — usado em toda
  parte do arquivo para o card padrão (`background:T.bgCard, border:...,
  borderRadius:"12px"`); o card consolidado de DEDUP-03 deve usar este
  mesmo objeto via spread, não inventar um novo.
- `numHero`/`numBody`/`numMicro` (Fase 20, `App.jsx:~256-258`) — escala
  numérica nomeada já pronta para os valores do card consolidado.
- Padrão "RESUMO DO DIA" em `EvolucaoScreen` — referência direta de
  densidade/espaçamento pro card novo do Portfólio (rótulo uppercase
  pequeno `T.textFaint` + valor grande logo abaixo).

### Established Patterns
- Vocabulário por modo (Estudo/Operador) sempre vem do backend
  (`server/app/skill_ref.py` → `cp.*`) ou de `web/src/copy.js`
  (`COPY.estudo`/`COPY.operador`) — nunca string solta hardcoded no
  componente. Qualquer texto novo do placeholder de FIX-03 deve seguir essa
  convenção se depender do modo.
- Estilo 100% inline, sem CSS Modules/Tailwind — grid consolidado via
  `style={{display:"grid", ...}}` no mesmo padrão do resto do arquivo.

### Integration Points
- `EvolucaoScreen` (Acompanhar) — mantém `<CapitalCurve>` como está.
- Rota "carteira"/Portfólio (`App.jsx:~8974` antes da correção) — remove
  `<CapitalCurve>`, os 4 cards separados viram 1 card consolidado.
- `AgenteScreen` (Operador IA) — remove o card de texto duplicado, realoca
  "Trocar modo →".
- `CapitalCurve` internals — ganha o branch de "poucos pontos" antes do
  branch de "zero pontos"/"curva normal".

</code_context>

<specifics>
## Specific Ideas

Nenhuma referência visual nova além do que já está no código (card "Resumo
do dia" como molde de densidade). Não é uma fase de exploração de design —
é remoção de duplicação e consolidação dentro do vocabulário visual já
existente.

</specifics>

<deferred>
## Deferred Ideas

- Migração de números do Portfólio para `numHero`/`numBody`/`numMicro`
  além do card consolidado (ex.: linhas do histórico dentro da mesma tela)
  — fora do escopo desta fase, que só migra os 4 valores do card novo.
- Qualquer redesenho maior do `AgenteScreen` além de remover o card
  duplicado — fora de escopo (Nível 1 "toque leve" do milestone).

</deferred>
