# Phase 36: Motor de Payoff Genérico - Context

**Gathered:** 2026-09-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Esta fase entrega o motor determinístico que a Fase 37 (gráfico + explicação)
vai consumir: dado um conjunto de pernas (CALL/PUT/ACAO), calcular
resultado/breakevens/ganho-perda máxima/domínio X-Y/segmentos, sem nenhuma
lógica por nome de estratégia. **Achado central desta discussão, verificado
por leitura + execução direta, não suposição:** um motor genérico que já
satisfaz boa parte disso EXISTE e está em produção —
`server/app/opcoes_payoff.py` (`perfil_da_estrutura()`). Esta fase ESTENDE
esse módulo (domínio X/Y, segmentos estruturados, vencimento por perna,
correção de um defeito real de breakeven espúrio), não cria um motor
paralelo. Módulo puro (sem rede/banco/LLM), mesma disciplina de
`opcoes_lastreadas.py`/`setups.py`/`indicators.py` — cálculo determinístico,
nunca pela IA (princípio 5 do CLAUDE.md).

</domain>

<decisions>
## Implementation Decisions

### Arquitetura — estender, não recriar
- **D-01:** `server/app/opcoes_payoff.py` é o motor. Esta fase ESTENDE esse
  módulo (funções novas ao lado de `perfil_da_estrutura()`, não uma reescrita
  dela) — não cria motor paralelo em nenhuma linguagem/arquivo novo.
  Decisão do Alex após comparação explícita das duas opções (estender vs.
  motor novo): risco de duas fontes de verdade divergentes (já aconteceu 2x
  neste repo — `RR_MIN` na Fase 6, CTA de collar na Fase 32/quick
  260916-g6p) pesa mais que a liberdade de schema de um motor novo.
  **Verificado nesta discussão, não suposto:**
  - Caso golden do Alex (trava de alta 49,17/49,67, débito 0,25) rodado
    direto em `perfil_da_estrutura()`: `breakevens: [49.42]`,
    `ganho_maximo: 25.0`, `perda_maxima: 25.0` — bate exato, sem alteração.
  - Múltiplos breakevens já funcionam: straddle comprado (call+put strike 50,
    prêmio 1,0 cada) → `breakevens: [48.0, 52.0]`, correto.
  - 4 consumidores em produção hoje: `opcoes_motor.py` (`avaliar()`,
    delegação direta), `opcoes_lastreadas.py`, `opcoes_curadoria.py`,
    `options_mcp_api.py`. Qualquer extensão bem desenhada beneficia os 4 sem
    sincronizar nada manualmente.
- **D-02:** Convenção de quantidade PRESERVADA como está — `quantidade` é
  número de contratos (não lote); lote multiplica FORA da função (padrão já
  existe em `options_mcp_api.py:_em_reais(dados, lote)`); breakeven é PREÇO,
  nunca multiplicado pelo lote (comentário já existe em
  `options_mcp_api.py:1283-1289` citando exatamente esse motivo). Bate com
  a especificação original do Alex ("breakeven não se multiplica pelo
  lote"). Nenhuma mudança de contrato aqui — só confirmação.

### Calendário / diagonal (vencimentos diferentes)
- **D-03:** Cada perna ganha campo de vencimento (nome exato: Claude's
  Discretion, seguir convenção `snake_case` do módulo — ex.: `vencimento`,
  já usado nesse sentido em `opcoes_lastreadas.py`/`options_mcp_api.py`).
  Campo OPCIONAL com default `None` — os 4 consumidores atuais que não
  passam vencimento continuam funcionando sem mudança (retrocompatibilidade
  obrigatória, conferir os 4 call sites antes de fechar o plano).
  Se as pernas informadas tiverem vencimentos DIVERGENTES entre si, a
  função retorna um estado explícito ("vencimentos diferentes, resultado
  depende do valor restante da outra ponta") em vez de calcular ganho/perda
  máxima ou desenhar curva — nunca aproxima linearmente. Pernas com
  vencimento omitido (`None`) são tratadas como "mesmo vencimento implícito"
  entre si (comportamento atual, preservado).

### Defeito real achado nesta discussão (não do planejamento) — corrigir junto
- **D-04:** `_breakevens()` hoje relata `S=0` como "breakeven" sempre que o
  resultado nesse ponto é exatamente zero — mesmo quando não é um
  cruzamento real, é a curva inteira constante em zero. **Verificado por
  execução direta:** uma posição líquida zero (mesma perna comprada e
  vendida no mesmo strike/prêmio) devolve `breakevens: [0.0, 50.0]`, dois
  pontos espúrios para uma "estrutura" sem exposição real nenhuma. Esta
  fase corrige duas coisas juntas, porque são a mesma causa raiz:
  1. Detectar e recusar com mensagem clara a entrada degenerada real:
     custo líquido ZERO **e** curva constante em zero em toda a faixa
     avaliada (não é "sem breakeven calculável", é "não há estrutura aqui
     para analisar" — corresponde ao pedido original do Alex de "prêmio
     zero ou strikes iguais → recusar com mensagem clara").
  2. Fora do caso degenerado acima, corrigir `_breakevens` para não
     reportar `S=0` como cruzamento quando o resultado ali é zero só por
     coincidência de posição (ex.: uma CALL comprada com prêmio zero — caso
     2 testado nesta discussão — tem breakeven real só no strike, não em
     S=0).
  **Box / resultado constante NÃO-zero** (ex.: estrutura trava um resultado
  de R$50 em qualquer preço) é um caso DIFERENTE do degenerado acima — não
  tem custo líquido zero, então não cai na recusa; o texto desta fase deve
  dizer "o resultado é o mesmo em qualquer preço" (não é um bug, é um
  requisito explícito do Alex) — precisa de teste dedicado, hoje não
  coberto por `test_opcoes_payoff.py`.

### Dado novo para a Fase 37 consumir
- **D-05:** Domínio X: `min(strike) - margem` a `max(strike) + margem`, onde
  `margem = max(12% do span dos strikes, 4% do spot)`; com perna única
  (sem span, um strike só) usar `±10% do strike`. Spot sempre dentro do
  domínio — se `spot` cair fora do intervalo acima, expandir o lado que
  falta até incluí-lo. Domínio Y: inclui zero sempre; estende 15% além do
  extremo finito (ganho ou perda máxima, o que for finito); em perna
  ilimitada, sinalizar continuação em vez de desenhar um teto/piso falso —
  a função devolve o sinal (`ganho_ilimitado`/`perda_ilimitada`, já
  existem), quem desenha a seta é a Fase 37.
- **D-06:** Lista estruturada de segmentos, percorrendo a curva da esquerda
  para a direita — formato proposto (Claude's Discretion nos nomes exatos
  de campo, seguir `snake_case` do módulo):
  `[{"de": float, "ate": float | null (null = sem teto/piso, cauda
  ilimitada), "inclinacao": "negativa"|"zero"|"positiva", "e_plato": bool}]`.
  Derivado de `curva` (pontos existentes) + `breakevens` + a cauda além do
  último strike (`inclinacao_direita`, já calculada) — não recalcula nada
  que a função já sabe, só reorganiza em formato consumível segmento a
  segmento (a Fase 37 gera uma frase por segmento, nessa ordem).

### Cobertura de teste obrigatória (além do que já existe)
- **D-07:** `test_opcoes_payoff.py` ganha casos novos para: straddle/
  strangle (2 breakevens, já comprovado no código mas não testado),
  borboleta/condor (2 breakevens + platô central), box/resultado constante
  não-zero, calendário/diagonal (degradação explícita), entrada degenerada
  (recusa), o caso golden do Alex como teste NOMEADO (não é implícito em
  nenhum teste existente hoje), lotSize/quantidades assimétricas entre
  pernas, domínio X/Y (D-05) e segmentos (D-06) para pelo menos 3
  estruturas diferentes (unária ilimitada, travada dos dois lados, 2+
  breakevens).

### Claude's Discretion
- Nome exato do campo de vencimento por perna e da função nova de
  domínio/segmentos (seguir convenção já estabelecida no módulo).
- Se a função de domínio/segmentos fica dentro de `opcoes_payoff.py` (mesmo
  módulo, função separada de `perfil_da_estrutura`) ou em um módulo
  companheiro novo — decisão técnica sem impacto de produto, só not
  misturar conceito de renderização dentro da função de cálculo financeiro
  puro existente.
- Mensagem exata de recusa do caso degenerado e do caso calendário
  (conteúdo semântico já decidido acima — D-03/D-04 — só a redação exata
  fica a critério de quem planeja/executa, seguindo o tom PT-BR direto já
  usado nas mensagens de erro existentes do módulo).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Motor existente (base desta fase — ler INTEIRO antes de planejar)
- `server/app/opcoes_payoff.py` — o módulo que esta fase estende
- `server/tests/test_opcoes_payoff.py` — 25 testes existentes, cobertura
  atual (ver D-07 para o que falta)

### Consumidores atuais (retrocompatibilidade obrigatória — D-03)
- `server/app/opcoes_motor.py` — `avaliar()`, delegação direta a
  `perfil_da_estrutura()`, linha ~197 ("não acrescentar semântica própria")
- `server/app/opcoes_lastreadas.py`
- `server/app/opcoes_curadoria.py`
- `server/app/options_mcp_api.py` — `_em_reais(dados, lote)` (linha ~1289),
  o padrão de "lote multiplica fora" que D-02 preserva; comentário sobre
  breakeven ser preço não dinheiro (linhas 1283-1289)

### Requisitos e roadmap
- `.planning/REQUIREMENTS.md` — PAYOFF-01, PAYOFF-02, PAYOFF-03 (esta fase)
- `.planning/ROADMAP.md` — seção "Phase 36: Motor de Payoff Genérico"

### Guardrails do repositório
- `CLAUDE.md` (raiz) — princípio 5 (cálculo determinístico, nunca pela IA);
  nota de "Paridade dos dois stores" NÃO se aplica aqui (este motor não
  mexe em `persistence.js`/saldo/posição — é cálculo de exploração de
  estrutura, não execução de ordem)
- Precedentes de duas-fontes-divergentes citados em D-01: `f1-timing-entrada`
  /Fase 6 (`RR_MIN`), Fase 32/quick `260916-g6p` (CTA de collar)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `perfil_da_estrutura(pernas)` — já devolve `curva`, `breakevens`,
  `ganho_maximo`/`perda_maxima` (com `None` correto para ilimitado),
  `ganho_ilimitado`/`perda_ilimitada` (booleanos já existem — a Fase 37 não
  precisa reinventar um formato `{unbounded: 'up'|'down'}`, os booleanos já
  servem), `custo_liquido`, `delta_total`
- `_validar_perna()` — validação por perna já existe, com mensagens citando
  índice + campo; extensão de vencimento deve seguir o mesmo padrão
- `_breakevens(curva, inclinacao_direita)` — função a corrigir (D-04), não
  recriar

### Established Patterns
- Módulo puro sem I/O, mesma disciplina de `opcoes_lastreadas.py`/
  `setups.py`/`indicators.py`
- Nunca `0.0` no lugar de "desconhecido" — motivo sempre declarado quando
  soma é parcial (`_delta_total` já faz isso, seguir o mesmo padrão para
  qualquer estado novo)
- "Lote multiplica fora" — função de cálculo nunca embute o fator de lote

### Integration Points
- `opcoes_motor.avaliar()` é o único ponto de delegação direta hoje — se a
  Fase 37 (ou uma rota nova) precisar do domínio/segmentos, o caminho mais
  provável é estender `avaliar()` ou a rota que já chama `perfil_da_estrutura`
  para também devolver os campos novos, não criar uma segunda chamada

</code_context>

<specifics>
## Specific Ideas

Formato proposto de segmento (D-06), ponto de partida pro planner:
```python
{"de": 0.0, "ate": 49.42, "inclinacao": "zero", "e_plato": True}
{"de": 49.42, "ate": 49.67, "inclinacao": "positiva", "e_plato": False}
{"de": 49.67, "ate": None, "inclinacao": "zero", "e_plato": True}
```

Caso golden do Alex, para usar como teste nomeado (D-07):
trava de alta com calls, strikes 49,17/49,67, débito 0,25, lote 100 →
breakeven 49,42, ganho/perda máx R$ 25,00 (do lote), 3 segmentos, nenhum
ilimitado.

</specifics>

<deferred>
## Deferred Ideas

- Motor espelhado em JavaScript/client-side — não decidido nesta discussão
  como necessário; `PayoffChart.jsx` hoje já consome dados pré-calculados
  vindos do servidor via prop, e nada nesta fase muda esse padrão. Se a
  Fase 37 achar que precisa de cálculo client-side, é decisão da Fase 37,
  não desta.
- Centralizar/refatorar os 4 consumidores atuais de `opcoes_payoff.py` —
  fora de escopo, esta fase só estende o motor sem tocar em quem já o
  chama (além do necessário pra aceitar o campo novo opcional).

### Reviewed Todos (not folded)
- `carimbo-frescor-blocos-cross-carteira.md`,
  `opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp.md`,
  `revisao-arquitetura-mcp-ecossistema-b3.md`,
  `subaba-operar-fetch-redundante-gate-proposta.md` — mesmo motivo das
  Fases 34/35: match fraco por palavra-chave genérica, nenhum é sobre
  motor de payoff.

</deferred>

---

*Phase: 36-motor-de-payoff-gen-rico*
*Context gathered: 2026-09-21*
