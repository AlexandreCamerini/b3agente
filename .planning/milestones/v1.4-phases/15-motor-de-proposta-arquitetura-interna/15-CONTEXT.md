# Phase 15: Motor de proposta (arquitetura interna) - Context

**Gathered:** 2026-09-02
**Status:** Ready for planning
**Source:** Síntese manual de uma exploração `/gsd-explore` + discussão socrática com
agente de arquitetura (ecc:architect) nesta mesma sessão. Não passou por
`/gsd-discuss-phase` porque a decisão já estava exaustivamente fechada.

<domain>
## Phase Boundary

Motor determinístico que decide QUAL estrutura de opções (venda coberta, put
de proteção, collar) propor sobre uma posição real da carteira, a partir de
um gatilho técnico. Cobre ENG-01..06 do REQUIREMENTS.md. Sem UI (Fase 18) e
sem fluxo de aceite/execução (Fase 17) — este é só o motor que produz a
proposta como dado, pronto pra ser exibido e aceito depois.

</domain>

<decisions>
## Implementation Decisions

### ENG-01 — Critério de seleção do contrato

Mantém a régua que JÁ ESTÁ em produção em `server/app/opcoes_lastreadas.py`
— não adota o critério por delta do `estruturas.py` do b-mcp.

Código real já existente (ler antes de planejar):
- `server/app/options_quant.py` — função `liquidity_score(volume,
  openInterest, bid, ask)`.
- `server/app/opcoes_lastreadas.py:20` — `_LIQUIDEZ_MINIMA = 40`.
- `server/app/opcoes_lastreadas.py:42-47` — `_candidato_valido(c)`: filtra
  candidatos por `liq["score"] >= _LIQUIDEZ_MINIMA`.
- `server/app/opcoes_lastreadas.py:50-56` — `_escolher_contrato(candidatos,
  melhor)`: escolhe pelo strike extremo — `min` (menor strike = call OTM
  mais próxima) para venda coberta, `max` (maior strike = put mais próxima
  do spot) para put de proteção.
- `server/app/opcoes_lastreadas.py:59-149` — `propor(underlying, chain,
  spot, plano, posicao, cash, modo, hoje)`: a função de proposta SINGLE-LEG
  que já existe e já roda em produção (Fase 14).

Este é o algoritmo de seleção a generalizar pra N pernas, não a substituir
por um critério novo.

### ENG-02 — Aritmética de payoff portada de calculos.py

Fonte a portar: `~/dev/MCP/servers/mydata/calculos.py` (repo separado,
`~/dev/MCP/`). É Python puro, sem I/O, sem dependência de MCP — funções de
identidade aritmética (custo líquido, ganho/perda máximos, breakevens,
delta somado, dado um conjunto de pernas com contrato/lado/quantidade).
Adaptar pro vocabulário e testes do Boris, não copiar 1:1 sem revisão —
mas a matemática em si não precisa ser reinventada.

### ENG-03 — Zero chamada de rede ao b-mcp em runtime

O motor consome dado de opções exclusivamente via
`server/app/mydata_client.py` (já existe, já em produção desde Fase 9/14).
Função relevante já existente: `mydata_client.get_options_chain(ticker,
vencimento=None, pregao=None)` (linha 248). Não subir client MCP stdio, não
chamar `b-mcp.semente.dev` (serve dado sintético/fixture em produção —
chamá-lo violaria o princípio 4 do CLAUDE.md, nunca inventar valor).

### ENG-04 — Limite/interface interno: `rastrear()` / `avaliar()`

Duas funções formam a fronteira que separa "como o Boris calcula hoje" de
"o que o b-mcp faria pela rede amanhã":

- `rastrear(cadeia, filtros) -> [contratos]` — equivalente a
  `find_tradable_options` do b-mcp. Hoje: filtra por `_candidato_valido`
  (liquidez) e escolhe por `_escolher_contrato` (strike extremo).
- `avaliar(pernas) -> {custo, ganho_max, perda_max, breakevens, delta}` —
  equivalente a `evaluate_option_structure` do b-mcp. Hoje: aritmética
  portada de `calculos.py` (ENG-02).

Vocabulário: o do contrato ADR-004/`mydata_client.py` já em uso — prêmio,
strike, delta, tipo (CALL/PUT) — NÃO inventar um vocabulário novo. Quando
`~/dev/MCP/docs/plano-mcp-servico.md` for aprovado pelo Alex (está em
avaliação, sem data), trocar o CORPO dessas duas funções pelas chamadas
reais ao b-mcp deve ser possível sem mudar quem as chama. Isso é a
restrição de design mais importante desta fase — o planner deve garantir
que ela é estruturalmente verdadeira, não só documentada.

### ENG-05 — Reuso do lock de orçamento

Qualquer chamada nova ao hub mydata feita por `rastrear()`/`avaliar()` (via
`mydata_client.py`) passa pelo `mydata_budget.reservar()` já existente
(lock do WR-01, PR #28) — nunca um canal de chamada paralelo que fure o
orçamento.

### ENG-06 — Gatilho técnico reusa o Radar

O que decide QUANDO avaliar uma proposta (não QUAL propor) vem do motor de
setups técnicos já existente do Boris — Radar, `setups.py` server-side,
`indicators.py`. NÃO portar nem depender da DSL de setups do b-mcp
(`~/dev/MCP/servers/mydata/setups.py`) — risco de sinal já medido e
corrigido uma vez (ADR-016/017, sinal ingênuo de confluência perdia
dinheiro). Esta fase não precisa reimplementar o gatilho — só consumir o
que o Radar já produz como entrada pro motor de proposta.

### Estruturas do v1 (contexto da Fase 16, não desta fase)

Esta fase constrói o motor GENÉRICO de N pernas. As 3 estruturas concretas
(venda coberta, put de proteção, collar) são escopo da Fase 16 — mas o
motor desta fase precisa suportar N pernas desde o início (não só 1),
porque collar é 2 pernas (venda de call + compra de put) sobre a mesma
posição.

### Claude's Discretion

- Nome exato dos módulos/arquivos novos em `server/app/` (ex.:
  `opcoes_motor.py`, `opcoes_estruturas_calc.py` — o planner decide,
  seguindo a convenção `snake_case.py` já usada no projeto).
- Estrutura interna de dados pra representar uma "perna" (dict vs.
  TypedDict vs. dataclass) — seguir o estilo já predominante no módulo
  `opcoes_lastreadas.py`/`store.py` (esses usam dict simples).
- Cobertura de teste exata — seguir o padrão `server/tests/test_<feature>.py`
  já estabelecido no projeto.

</decisions>

<specifics>
## Specific Ideas

Nenhuma além do que já está em `<decisions>` — a decisão já foi fechada em
detalhe nesta sessão, não há exemplo solto adicional a registrar.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Decisão e racional completos
- `.planning/notes/opcoes-v2-b-mcp-exploracao.md` — exploração completa,
  seção "Arquitetura decidida (2026-09-02)" tem o racional das 5 estratégias
  avaliadas e por que a B foi escolhida.
- `.planning/seeds/opcoes-v2-setups-propostos-via-b-mcp.md` — resumo das
  decisões de produto e arquitetura fechadas.
- `.planning/REQUIREMENTS.md` — ENG-01..06, texto oficial dos requirements
  desta fase.

### Código existente a estender, não substituir
- `server/app/opcoes_lastreadas.py` — motor single-leg em produção (Fase
  14); `_LIQUIDEZ_MINIMA`, `_candidato_valido`, `_escolher_contrato`,
  `propor()`.
- `server/app/options_quant.py` — `liquidity_score()`.
- `server/app/mydata_client.py` — cliente REST já em produção,
  `get_options_chain()`.
- `server/app/mydata_budget.py` — lock `reservar()` (WR-01, PR #28).

### Fonte a portar (repo externo, só leitura — não editar)
- `~/dev/MCP/servers/mydata/calculos.py` — aritmética de payoff pura a
  adaptar (ENG-02).

</canonical_refs>

<deferred>
## Deferred Ideas

- Integração MCP real via `rastrear()`/`avaliar()` chamando o b-mcp —
  Future Requirement, condicionado à aprovação do `plano-mcp-servico.md`.
- As 3 estruturas concretas (venda coberta, put, collar) usando este motor
  — Fase 16.
- Exibição da proposta e fluxo de aceite — Fase 17.
- Aba de navegação — Fase 18.

</deferred>

---

*Phase: 15-motor-de-proposta-arquitetura-interna*
*Context gathered: 2026-09-02 via síntese manual (sem discuss-phase)*
