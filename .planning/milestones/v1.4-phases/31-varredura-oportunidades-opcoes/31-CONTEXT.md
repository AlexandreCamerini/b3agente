# Phase 31: Varredura de oportunidades de opções - Context

**Gathered:** 2026-09-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Estender a curadoria determinística de oportunidades de opções (Fase 30) de
"1 vencimento × 1 estrutura (venda coberta)" para "vários vencimentos ×
as 4 estruturas que o motor interno já executa (venda coberta, put de
proteção, collar, opção a descoberto)", sobre as posições que o usuário já
tem na carteira — mais um payoff visual (`PayoffChart.jsx`) responsivo no
bloco de curadoria. A seleção de quais oportunidades aparecem continua
100% determinística (`opcoes_motor.avaliar()`/`opcoes_curadoria.py`); a IA,
se aparecer, só narra.

</domain>

<decisions>
## Implementation Decisions

### D1 — Vencimentos: teto fixo de 2 por posição elegível
- **D-01:** Varrer até **2 vencimentos** por posição elegível (o mais
  próximo + o segundo mais próximo publicado por
  `mydata_client.get_vencimentos(ticker)`), não só o mais próximo como
  hoje. Custo de rede passa a ser **2× o de hoje**, previsível — nunca
  "todos os vencimentos que a cadeia trouxer" nem uma janela de dias sem
  teto.
- **D-02:** Isso substitui a decisão literal do Alex de horas atrás
  ("primeiro futuro, seja qual for") e a de ontem à noite ("todos os
  vencimentos") por um meio-termo com custo declarado — não é varredura
  ilimitada.
- **D-03 (achado técnico, não decisão de produto):** `get_vencimentos()` é
  1 chamada barata que já retorna a lista inteira; `get_options_chain(t,
  vencimento=X)` é 1 chamada cara POR vencimento. O teto de 2 significa
  até 2 chamadas de `get_options_chain` por posição elegível (vs. 1 hoje).
  Qualquer plano de execução precisa declarar esse número explicitamente
  contra o orçamento medido do mydata (60/min · 2.000/dia, ver
  `docs/MEDICAO-Mydata-2026-08-27.md`).

### D2 — Estruturas: as 4 do motor interno, oportunidade a descoberto só para quem já tem o flag ligado
- **D-04:** A varredura passa a cobrir as 4 estruturas do motor interno —
  venda coberta, put de proteção, collar e opção a descoberto — não só
  venda coberta como a Fase 30. Isso é uma ampliação explícita do universo
  D1 da Fase 30 (que excluiu put/collar de propósito).
- **D-05:** Oportunidade a descoberto só aparece na varredura para contas
  com `permitirOpcaoADescoberto = true` já ligado (Fase 29). Quem não
  ligou o flag não vê essas oportunidades — nem com aviso. A Fase 29 e seu
  gate de execução não mudam.
- **D-06:** Ranking usa **uma fórmula só (prêmio ÷ perda máxima) para as 4
  estruturas**, decisão explícita do Alex mesmo sabendo que put/collar de
  proteção rankeiam estruturalmente mal nessa fórmula (perda máxima baixa
  por design, prêmio líquido às vezes negativo) — aceito porque o objetivo
  declarado da varredura é "gerar receita com risco mínimo", não proteção.
  Não criar seções separadas por objetivo nesta fase.

### D3 — Payoff visual: responsivo mobile primeiro, sem overlay
- **D-07:** Prioridade única desta fase para `PayoffChart.jsx`: garantir
  que funciona bem em 375px (mobile), sem mudar a lógica de exibição —
  continua recebendo **uma estrutura por vez**, igual hoje.
- **D-08:** Overlay de múltiplos candidatos na mesma curva e
  interatividade (tocar/zoom) ficam **fora de escopo** desta fase — são
  trabalho novo real (o componente não suporta hoje), não reuso. Podem
  virar fase própria se o Alex pedir depois de ver o resultado desta.

### D4 — Universo de tickers: só posições já na carteira
- **D-09:** A varredura cobre só tickers com posição aberta na carteira do
  usuário — o mesmo universo da Fase 30. Não se estende a
  watchlist/catálogo sem posição. Isso vale inclusive para opção a
  descoberto: mesmo sem exigir lastro no motor, o escopo de BUSCA desta
  fase continua sendo a carteira do usuário, não o catálogo B3 inteiro.

### Claude's Discretion
- Layout exato do bloco de resultado na tela de Posições (extensão do
  bloco da Fase 30 vs. bloco novo ao lado) — decidir na pesquisa/plano com
  base no que já existe em `CuradoriaEstruturas`.
- Texto de narração da IA para put/collar/naked quando rankeados mal pela
  fórmula única (D-06) — desde que não avance a leitura do princípio 5
  (a IA explica o número, não o promove).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Fase 30 — base a estender (não jogar fora)
- `.planning/phases/30-curadoria-ia-melhores-estruturas/30-CONTEXT.md` — D1 (universo/fórmula), D3 (achado que 1 chamada = 1 vencimento, motivo do teto agora virar 2), D4 (onde a IA narra)
- `server/app/opcoes_curadoria.py` — `candidatos_da_posicao`, `rankear`, `exigir_ranking` (padrão de ranking determinístico a estender pras 4 estruturas)
- `server/app/curadoria_narrativa.py` — narração de IA sobre o ranking já pronto

### Fase 29 — gate de execução a descoberto (invariante, não mexer)
- `.planning/phases/29-opcao-a-descoberto-flag-opt-in/29-CONTEXT.md`
- `server/app/store.py:102,319-328,825` — `permitirOpcaoADescoberto`, gate de `sell_option`/`buy_option` a descoberto

### Correção de vencimento (base técnica do D1/D3)
- `.planning/quick/260914-b6p-corrigir-bug-de-selecao-de-vencimento-em/260914-b6p-SUMMARY.md`
- `server/app/options_provider_mydata.py:183-334` — `_primeiro_vencimento_futuro`, `get_options()` (1 chamada de `get_vencimentos` + 1 de `get_options_chain` por vencimento buscado)
- `docs/MEDICAO-Mydata-2026-08-27.md` — orçamento real medido (60/min · 2.000/dia) contra o qual o custo 2× de D1 precisa ser declarado

### Motor determinístico (guardrail principio 5)
- `docs/adr/023-opcoes-lastreadas.md` — mecânica lastreada (venda coberta/put/collar)
- `server/app/opcoes_motor.py` — `rastrear()`/`avaliar()`, já suporta N candidatos por chamada sobre cadeia em memória

### Payoff visual
- `web/src/opcoes/PayoffChart.jsx` — componente a tornar responsivo (recebe 1 `estrutura` por vez, sem overlay hoje)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `opcoes_motor.rastrear()`/`avaliar()`: já aceitam parâmetro `n` para retornar múltiplos candidatos de uma cadeia já em memória — nenhuma chamada de rede extra por candidato dentro do MESMO vencimento.
- `opcoes_curadoria.py` (`rankear`/`exigir_ranking`): molde de ranking determinístico que recusa estruturalmente pool não ordenado — estender para 4 estruturas em vez de reescrever.
- `buy_option`/`sell_option` + `permitirOpcaoADescoberto` (Fase 29): mecânica de execução a descoberto já existe e já está gateada — esta fase só decide como a DESCOBERTA de oportunidade interage com o gate de EXECUÇÃO (D-05), não reconstrói a execução.
- `PayoffChart.jsx`: componente de curva + números já em produção no caminho MCP — ponto de partida citado pelo próprio Alex, precisa só de ajuste de responsividade (D-07).

### Established Patterns
- 1 chamada de `get_options_chain` por vencimento buscado é o ponto de contenção de custo real (D-03) — qualquer expansão de escopo de varredura precisa declarar esse número explicitamente, igual a Fase 30 fez.
- `permitirOpcaoADescoberto` é lido no momento da EXECUÇÃO (`store.py`); esta fase introduz o primeiro lugar onde o flag também precisa ser checado no momento da DESCOBERTA/exibição (D-05) — não existe hoje esse ponto de checagem em `opcoes_curadoria.py`.

### Integration Points
- Bloco de resultado em Posições (extensão de `CuradoriaEstruturas`/`useCuradoria`, Fase 30) é o ponto de entrada mais provável — a decidir em detalhe na pesquisa/plano (Claude's Discretion).

</code_context>

<specifics>
## Specific Ideas

Pedido original do Alex, na íntegra: "sempre trazer as opções disponíveis
no futuro" + "uma análise AI ou determinística destas opções disponíveis
usando os principais setups de opções e os gráficos de payoff para trazer
para o usuário as oportunidades". A ambiguidade "IA ou determinística" foi
fechada por D-01/D-06/guardrail do CLAUDE.md: seleção é sempre
determinística, IA só narra — não foi reaberta pelo Alex nesta sessão de
discuss-phase.

</specifics>

<deferred>
## Deferred Ideas

- Varredura sobre watchlist/catálogo sem posição na carteira (D-09 recusa
  por ora) — poderia virar fase própria se o Alex pedir depois de ver o
  resultado desta.
- Overlay de múltiplos candidatos e interatividade no payoff (D-08) —
  candidato natural para uma fase de "polish" depois que o mobile
  responsivo estiver validado.
- Seções de ranking separadas por objetivo (receita vs. proteção),
  recusada em D-06 — revisitar se o Alex achar que put/collar rankeando
  mal na fórmula única está confundindo o usuário na prática.

### Reviewed Todos (not folded)
None — discussion stayed within phase scope.

</deferred>

---

*Phase: 31-varredura-oportunidades-opcoes*
*Context gathered: 2026-09-14*
