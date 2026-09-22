# Phase 37: Gráfico de Payoff e Explicação Confiáveis - Context

**Gathered:** 2026-09-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Esta fase conserta e estende o `PayoffChart.jsx` já existente em produção
(SVG puro, 3 pontos de uso reais) para consumir `dominio_da_curva()` e
`segmentos_da_curva()`, entregues pela Fase 36, e adiciona uma camada de
explicação textual por segmento. Corrige 2 bugs reais confirmados em
produção por screenshot (CHART-05: "hoje" e "no vencimento" hoje se
confundem; EXPL-03: dois números diferentes lidos como se fossem a mesma
"razão") e completa lacunas de acessibilidade/rotulagem do gráfico (CHART-01
zero + escala; CHART-02 strike/spot marcados). Não é um motor novo — o
cálculo continua 100% em `server/app/opcoes_payoff.py` (Fase 36); esta fase
é renderização (SVG) + apresentação (texto determinístico), nunca cálculo
financeiro novo no front (princípio 5 do CLAUDE.md).

</domain>

<decisions>
## Implementation Decisions

### CHART-05 — fonte de "hoje · valor de mercado"
- **D-01:** Buscar o prêmio ATUAL de cada perna via `get_option_chain`
  (tool MCP que já existe e já é chamado em `options_mcp_api.py`) e o
  backend soma prêmio atual × lado × quantidade por perna — mesma
  disciplina de `net_cost`/`_em_reais` (determinístico, nunca no front).
  Devolve um campo novo (nome exato: Claude's Discretion, seguir
  `snake_case`, ex. `valor_hoje`). Decisão explícita do Alex: vale o custo
  de cota extra por ser um número real de marcação a mercado, não uma
  aproximação.
- **D-02:** Em `SecaoComparar` (que mostra N candidatos simultaneamente,
  cada um com seu próprio `PayoffChart`), a busca de valor de hoje NÃO é
  automática para todos — só para o 1º candidato da lista já ordenada pelo
  ranking de curadoria (`opcoes_curadoria.py`, mesma ordem que
  `CuradoriaEstruturas.jsx` já respeita como "ORDEM RECEBIDA"). Evita
  multiplicar chamadas ao serviço (e consumo de cota, ADR-013/`plan.py`)
  só por renderizar a lista de comparação. Nos demais candidatos, o gráfico
  mostra só a curva no vencimento (sem busca ao vivo) — zero mudança aí.
- **Nova chamada ao serviço, novo estado de erro:** `get_option_chain` pode
  falhar/degradar como qualquer chamada MCP (cascata já estabelecida em
  `ErroDoMcp`, `uiOpcoes.jsx`). Se a busca de valor de hoje falhar, a curva
  no vencimento continua aparecendo normalmente — só o bloco "hoje" mostra
  o estado de erro/indisponível (princípio 4 do CLAUDE.md: nunca inventar,
  mostrar o estado real). Não bloquear o gráfico inteiro por causa de um
  dado adicional que falhou.

### EXPL-03 — origem confirmada da divergência de razão G/P
- **D-03:** Confirmado pelo Alex: a confusão do screenshot ("1:1,00" vs.
  "1:0,67") é `CuradoriaEstruturas.jsx:194` (`cand.razao.toFixed(2)`, SCORE
  de ranking de `opcoes_curadoria.py`) sendo lido como se fosse a mesma
  coisa que `RazaoGanhoPerda` (`_razao_ganho_perda`, ganho máximo ÷ perda
  máxima) — dois números com nome parecido ("razão"), semântica
  completamente diferente, aparecendo perto um do outro na mesma tela.
- **D-04:** Rótulo `curadoriaRazaoRotulo` (hoje provavelmente "Razão" ou
  similar) passa a se chamar "Pontuação de curadoria" / "Score" — deixa
  explícito que é critério de RANKING (como o algoritmo ordenou os
  candidatos), nunca confundível com a métrica financeira do resultado da
  estrutura. Redação exata: Claude's Discretion, seguir o tom PT-BR direto
  já usado no módulo.
- **D-05 (guardrail travado, aplica-se também à explicação nova de
  EXPL-01):** Qualquer texto que mencione a razão ganho/perda — incluindo
  a camada explicativa nova desta fase — reusa LITERALMENTE a mesma
  variável já exibida por `RazaoGanhoPerda` (a partir de
  `_razao_ganho_perda`), nunca recalcula dentro do componente/função de
  texto. Mesmo padrão que `emReais` já segue (zero conta fora do backend).
  Precedente de duas-fontes-divergentes já citado na Fase 36 (`RR_MIN`,
  CTA de collar) — esta é a mesma classe de bug, prevenida da mesma forma.

### EXPL-01/02/03 — arquitetura da camada explicativa
- **D-06:** Texto 100% determinístico, função pura em JavaScript, ZERO
  I/O e zero LLM — mesma disciplina de `finance.js`/`plan.js`. Percorre
  `segmentos_da_curva()` (da Fase 36) e monta frase por template (mapa
  inclinação→verbo, `e_plato`→"resultado trava em"). Decisão explícita do
  Alex, motivada pelo guardrail CVM (manchete só do motor determinístico) e
  pelo princípio 5: um LLM parafraseando segmentos correria o risco exato
  de EXPL-03 (arredondar/reformular um número que já existe em outro
  lugar), além de adicionar latência e custo numa tela hoje só de cálculo.
- **D-07:** O texto descreve TODOS os segmentos de `segmentos_da_curva()`,
  não só o segmento onde o spot está — o segmento do spot vem PRIMEIRO
  ("hoje você está aqui, resultado X"), os demais seguem na ordem espacial
  esquerda→direita restante. Interpretação literal de EXPL-01 ("percorrida
  da esquerda para a direita com a frase do segmento onde o spot está
  vindo primeiro") — não é só "onde estou agora", é o quadro completo da
  estrutura em texto.
- **Vocabulário banido (já travado em REQUIREMENTS.md, EXPL-02, sem
  reabrir):** strike, prêmio, delta, theta, volatilidade implícita,
  exercício, rolagem, ITM/OTM/ATM, "perna". O texto por segmento precisa
  descrever inclinação/platô/direção em português direto sem essas
  palavras.

### Escopo dos consumidores do PayoffChart
- **D-08:** Correção de leitura desta discussão: `PayoffChart.jsx` tem
  **3 consumidores reais** (não 4 como o CONTEXT.md inicial supôs) —
  `SecaoComparar.jsx`, `SecaoAnalisar.jsx`/`OpcoesScreen.jsx`, e
  `CuradoriaEstruturas.jsx`. `CriarSetup.jsx` só CITA `PayoffChart` num
  comentário de código, não importa nem renderiza — não é um 4º consumidor.
- **D-09:** Como é o MESMO componente, as correções de eixo/domínio/
  segmento (CHART-01..04 — zero rotulado, escala Y, strike/spot marcados,
  domínio vindo de `dominio_da_curva()`) chegam automaticamente aos 3
  consumidores, sem trabalho extra por tela. Os blocos NOVOS — explicação
  por segmento (EXPL-01/02/03) e "hoje · valor de mercado" (CHART-05) —
  entram SÓ na jornada que a Fase 35 acabou de polir: `SecaoAnalisar`
  (Analisar) e `SecaoComparar` (Comparar). `CuradoriaEstruturas` (Modo
  Operador) fica só com o gráfico corrigido nesta fase, sem os blocos
  novos — não foi objeto de discussão de UX nem na Fase 35 nem aqui;
  decisão de trazer os blocos novos pra lá fica para fase futura.

### Claude's Discretion
- Nome exato do campo novo de valor de hoje (`valor_hoje` é só ponto de
  partida) e da função/endpoint que faz a busca via `get_option_chain`.
- Redação final do rótulo "Pontuação de curadoria"/"Score" e das frases de
  template da explicação por segmento (viram chaves `cp.*` em `copy.js`,
  mesmo padrão de vocabulário por modo já estabelecido nas Fases 33-35).
- Onde exatamente a função pura de explicação mora (`web/src/opcoes/`,
  módulo novo ou dentro de `uiOpcoes.jsx` — olhar o padrão real de
  duplicação antes de centralizar, mesmo critério usado na Fase 35).
- Tratamento visual exato do estado de erro/indisponível do bloco "hoje"
  quando `get_option_chain` falha (reusar `ErroDoMcp`/`Aviso` já
  existentes, mas o texto exato é decisão de quem planejar/executar).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Motor determinístico que esta fase consome (Fase 36, base obrigatória)
- `server/app/opcoes_payoff.py` — `perfil_da_estrutura()`,
  `dominio_da_curva()`, `segmentos_da_curva()` (as duas últimas são o
  produto novo da Fase 36 que esta fase renderiza)
- `.planning/phases/36-motor-de-payoff-gen-rico/36-CONTEXT.md` — decisões
  D-05 (fórmula de margem/domínio) e D-06 (formato de segmento, cortes só
  em strike) que o SVG desta fase precisa respeitar sem reabrir

### Componente a estender (não recriar)
- `web/src/opcoes/PayoffChart.jsx` — o gráfico SVG existente; ler INTEIRO
  antes de planejar, especialmente as linhas 100-160 (`desenho = useMemo`)
  onde o domínio X/Y é calculado LOCALMENTE hoje e precisa ser substituído
  pelo domínio vindo do backend (`dominio_da_curva()`)
- `web/src/opcoes/estruturaParaPayoff.js` — adaptador PT→EN puro que
  alimenta `PayoffChart` a partir do motor local (`opcoes_payoff.py`);
  precisa ganhar as chaves novas de domínio/segmentos/valor-hoje, sem
  nenhuma aritmética (guardião `test_estrutura_para_payoff.mjs` proíbe
  operador aritmético neste arquivo por regex)

### Consumidores reais (D-08/D-09)
- `web/src/opcoes/SecaoComparar.jsx:221` — recebe blocos novos
- `web/src/opcoes/SecaoAnalisar.jsx:390` (via `OpcoesScreen.jsx`) — recebe
  blocos novos
- `web/src/opcoes/CuradoriaEstruturas.jsx:194,291` — só gráfico corrigido,
  sem blocos novos nesta fase; linha 194 é o `cand.razao` a renomear (D-04)

### Razão ganho/perda (fonte única, D-05)
- `web/src/opcoes/uiOpcoes.jsx` — `RazaoGanhoPerda()`, a função/componente
  cuja variável a explicação nova DEVE reusar literalmente
- `server/app/options_mcp_api.py:1325` — `_razao_ganho_perda()`, cálculo
  determinístico de origem (ganho máximo ÷ perda máxima)

### Serviço MCP (CHART-05)
- `server/app/options_mcp_api.py` — `_chamada_com_cap()` (padrão de
  chamada com cota), tool `get_option_chain` já em uso (linha ~2084),
  `_em_reais()`/`_vezes_lote()` (padrão "lote multiplica fora", D-02 da
  Fase 36, D-01 desta fase segue o mesmo)
- `server/app/plan.py`, ADR-013 — teto de cota diário que a chamada nova
  consome

### Requisitos e roadmap
- `.planning/REQUIREMENTS.md` — CHART-01..05, EXPL-01..03 (esta fase)
- `.planning/ROADMAP.md` — seção "Phase 37: Gráfico de Payoff e Explicação
  Confiáveis"

### Guardrails do repositório
- `CLAUDE.md` (raiz) — princípio 4 (nunca inventar valor na falha de
  dado, D-01/erro de get_option_chain), princípio 5 (cálculo
  determinístico nunca pela IA/front, D-06), guardrail CVM (manchete só do
  motor determinístico)
- Precedentes de duas-fontes-divergentes: `RR_MIN` (Fase 6), CTA de collar
  (Fase 32/quick 260916-g6p), citados de novo em D-05 como a mesma classe
  de bug que EXPL-03 expôs

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `PayoffChart.jsx` já desenha: linha do zero tracejada (sem rótulo "R$ 0"
  ainda — lacuna CHART-01), setas ↑/↓ para lado ilimitado + legenda "sem
  teto"/"sem piso" (CHART-03 já quase completo), breakevens marcados no
  eixo com supressão de colisão de texto (padrão a REUSAR para marcar
  strikes/spot também, CHART-02)
- `RazaoGanhoPerda()` (`uiOpcoes.jsx`) — já pronta, backend-calculada; a
  explicação nova só precisa LER essa mesma variável (D-05)
- `ErroDoMcp`/`Aviso` (`uiOpcoes.jsx`) — cascata de erro já estabelecida,
  reusar para o estado de falha do bloco "hoje" (CHART-05)
- `get_option_chain` — tool MCP já integrado, já usado em outro fluxo
  (`options_mcp_api.py:2084`), não é I/O novo no sentido de "nunca visto
  no repo", só novo NESTE fluxo de avaliação de estrutura

### Established Patterns
- "Lote multiplica fora" (`_em_reais`, `_vezes_lote`) — o campo novo de
  valor de hoje segue a mesma disciplina, calculado uma vez no backend
- `color-mix()`/tokens de tema — zero cor literal nova, só os tokens já
  declarados em `PayoffChart.jsx` (`TOKENS`/`T`)
- Supressão de rótulo por colisão (breakevens hoje, strikes/spot amanhã)
  já implementada — reusar o mesmo algoritmo, não inventar um novo

### Integration Points
- `estruturaParaPayoff.js` é o único ponto de tradução PT→EN entre o motor
  local e `PayoffChart` — qualquer campo novo do backend (domínio,
  segmentos, valor de hoje) precisa passar por aqui sem nenhuma conta
- `opcoes_motor.avaliar()` delega direto a `perfil_da_estrutura()` sem
  acrescentar chave — `dominio_da_curva()`/`segmentos_da_curva()` (funções
  SEPARADAS por decisão da Fase 36, D-06/discretion) precisam ser
  explicitamente chamadas e mescladas em algum ponto da rota HTTP que serve
  o front; verificar qual rota é essa antes de planejar (research phase)

</code_context>

<specifics>
## Specific Ideas

Nenhuma referência visual/redação literal nova nesta discussão além do que
já está travado em REQUIREMENTS.md (CHART-01..05, EXPL-01..03) e no
`36-CONTEXT.md` (formato de segmento). O caso golden da Fase 36 (trava de
alta 49,17/49,67, breakeven 49,42, 3 segmentos) continua sendo o cenário de
referência natural para o SVG e o texto desta fase.

</specifics>

<deferred>
## Deferred Ideas

- Blocos novos (explicação por segmento, valor de hoje) em
  `CuradoriaEstruturas.jsx` (Modo Operador) — decisão explícita de deixar
  fora do escopo desta fase (D-09); candidato a fase futura se o Alex
  quiser levar a mesma experiência para lá.
- "Análise automática apresentando o melhor candidato" em Comparar (ideia
  que surgiu respondendo à pergunta de custo de cota) — resolvida NESTA
  fase apenas no sentido estrito de "buscar valor de hoje só do 1º
  candidato do ranking já existente" (D-02). Uma automação de análise/
  apresentação mais ampla do melhor candidato não foi especificada nem
  decidida — se o Alex quiser algo além disso (ex.: destaque visual
  especial, resumo automático comparando os candidatos), é uma capacidade
  nova, fora do escopo desta fase de gráfico+explicação.

### Reviewed Todos (not folded)
- `carimbo-frescor-blocos-cross-carteira.md`, `medir-rate-limit-mydata.md`,
  `revisao-arquitetura-mcp-ecossistema-b3.md` — mesmo padrão das Fases
  34/35/36: match fraco por palavra-chave genérica ("motor", "fase",
  "real", "produção"), nenhum é sobre gráfico de payoff ou explicação.
  `medir-rate-limit-mydata.md` tem alguma proximidade temática com D-01
  desta fase (nova chamada MCP consome cota) mas é sobre MEDIR rate-limit
  do serviço como um todo, não sobre esta feature específica — não dobrado.

</deferred>

---

*Phase: 37-gr-fico-de-payoff-e-explica-o-confi-veis*
*Context gathered: 2026-09-21*
