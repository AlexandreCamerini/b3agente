# ADR-024: Limite interno rastrear()/avaliar() — o motor de opções sem dependência de runtime do b-mcp

**Status:** Aceito
**Data:** 2026-09-02
**Decisor:** Alex (via `/gsd-explore` + discussão de arquitetura, 2026-09-02)
**Base:** ROADMAP v1.4 Fase 15; `15-CONTEXT.md`; `.planning/notes/opcoes-v2-b-mcp-exploracao.md`;
ADR-004 (contrato de cadeia de opções); ADR-020 (centralização de dados no
mydata); ADR-023 (opções lastreadas).

---

## Contexto

O b-mcp existe como repositório separado (`~/dev/MCP`), com um serviço MCP
próprio em avaliação (`~/dev/MCP/docs/plano-mcp-servico.md`, datado
2026-09-02, aguardando aprovação do Alex) e uma biblioteca de aritmética de
payoff (`~/dev/MCP/servers/mydata/calculos.py`) e de DSL de setups
(`~/dev/MCP/servers/mydata/setups.py`, `estruturas.py`) próprias. Em
produção, o portal público `b-mcp.semente.dev` serve dado **sintético/
fixture** (`MYDATA_MODO` vira `"meta"` na nuvem) — consumi-lo em runtime
violaria o princípio 4 do CLAUDE.md (nunca inventar valor de mercado).
Subir um client MCP stdio dentro do processo único do Railway (uvicorn
com pool de threads/anyio) traria, além disso, risco operacional
concreto sem necessidade.

A exploração de arquitetura de 2026-09-02 avaliou 5 estratégias para o
motor de proposta desta fase (Phase 15). A **Estratégia B** — estender o
motor próprio do Boris, usando o b-mcp só como especificação de referência,
com o refinamento de reaproveitar `calculos.py` (a parte de A que é
matemática pura, sem o critério de seleção por delta que vem junto) — foi a
escolhida:

- **Estratégia A** (portar `estruturas.py` por cópia): descartada — traz
  junto o critério de seleção por delta, incompatível com a régua de
  liquidez já em produção (`opcoes_lastreadas.py`).
- **Estratégia B** (motor próprio, b-mcp como referência): **ESCOLHIDA**.
- **Estratégia C** (integrar via MCP autenticado, `mcp.semente.dev`):
  descartada por ora — depende de `plano-mcp-servico.md`, ainda não
  aprovado.
- **Estratégia D** (empurrar a conta para o hub REST, `mydata.semente.dev`):
  descartada — empurraria para o hub uma conta que é pura e não precisa de
  rede.
- **Estratégia E** (núcleo compartilhado versionado entre os dois repos):
  descartada — cria acoplamento de versionamento entre dois repositórios
  independentes.

## Decisão 1 — o limite

Duas funções puras em `server/app/opcoes_motor.py` formam a fronteira que
separa "como o Boris calcula hoje" de "o que o b-mcp faria pela rede
amanhã":

- `rastrear(cadeia, filtros) -> list[dict]` — equivalente interno de
  `find_tradable_options` do b-mcp. Hoje: filtra candidatos por
  `_candidato_valido` (liquidez, reusando `options_quant.liquidity_score`)
  e escolhe por strike extremo (`min` para venda coberta, `max` para put de
  proteção), a MESMA régua que `opcoes_lastreadas.py` já roda em produção
  desde a Fase 14 — não um critério novo.
- `avaliar(pernas) -> dict` — equivalente interno de
  `evaluate_option_structure` do b-mcp. Hoje: delegação direta a
  `opcoes_payoff.perfil_da_estrutura` (custo líquido, ganho/perda máximos,
  breakevens, delta somado de uma estrutura de N pernas).

O vocabulário usado nos dois é o do contrato ADR-004/`mydata_client.py` já
em uso no repositório — prêmio, strike, delta, tipo (`CALL`/`PUT`) — sem
inventar vocabulário novo, para que a leitura por quem já conhece o
contrato de cadeia não precise reaprender nada.

## Decisão 2 — o que foi portado e o que não foi

**Portado:** a aritmética de payoff de `~/dev/MCP/servers/mydata/
calculos.py` — Python puro, sem I/O, sem dependência de MCP, funções de
identidade aritmética (custo líquido, ganho/perda máximos, breakevens,
delta somado, dado um conjunto de pernas com contrato/lado/quantidade).
Adaptada ao vocabulário e à suíte de testes do Boris em
`server/app/opcoes_payoff.py` (Plano 15-01), não copiada 1:1 sem revisão —
mas a matemática em si não precisou ser reinventada.

**NÃO portado — a DSL de setups** (`~/dev/MCP/servers/mydata/setups.py`).
O sinal ingênuo de confluência daquele motor já foi medido perdendo
dinheiro e corrigido uma vez em produção (ADR-016/ADR-017, ver
PROJECT.md). Reintroduzi-lo sem passar pelo mesmo processo de validação
(`scripts/backtest_sinal.py`) traria de volta um defeito de produto já
fechado. O gatilho técnico desta fase (`server/app/opcoes_gatilho.py`,
Plano 15-02, ENG-06) consome exclusivamente o plano que o Radar/`setups.py`/
`indicators.py` já produzem em produção — nunca a DSL do b-mcp.

**NÃO adotado — o critério de seleção por delta** de
`~/dev/MCP/servers/mydata/estruturas.py` (montagem de pernas por delta,
0,25 asa / 0,5 ATM, sem filtro de liquidez). A régua do Boris é
`liquidity_score >= 40` (`opcoes_motor.LIQUIDEZ_MINIMA`) mais strike
extremo, já em produção desde a Fase 14 e validada com dado real da B3 —
não substituída por um critério novo sem passar por decisão de produto.

## Decisão 3 — o canal de dado

Leitura de cadeia de opções exclusivamente via `server/app/mydata_client.py`
(já existe, em produção desde a Fase 9/14), sempre atrás do lock de
orçamento `mydata_budget.reservar()` (WR-01, PR #28, commit `c014c88`) —
nunca um canal paralelo. O guardião estrutural de ENG-05
(`test_opcoes_fronteira.py`, Guardião C) mantém essa allowlist fechada em
`{candle_provider, options_provider_mydata, mydata_budget}`: qualquer
módulo novo que passe a importar `mydata_client` reprova a suíte e obriga
uma decisão consciente, porque o orçamento combinado (60/min · 2.000/dia)
só é defensável enquanto houver um caminho só até o hub.

## Procedimento de troca

Quando `~/dev/MCP/docs/plano-mcp-servico.md` for aprovado pelo Alex, a
troca é do **CORPO** das duas funções — nunca do chamador:

1. Trocar o corpo de `rastrear(cadeia, filtros)` por uma chamada
   autenticada a `find_tradable_options` no serviço MCP (`mcp.semente.dev`,
   bearer de máquina), mantendo a assinatura `(cadeia, filtros)` e o
   formato de retorno (`list[dict]` de contratos no vocabulário ADR-004)
   inalterados.
2. Trocar o corpo de `avaliar(pernas)` por uma chamada a
   `evaluate_option_structure`, mantendo a assinatura `(pernas)` e as
   chaves do dicionário devolvido (`custo`, `ganho_max`, `perda_max`,
   `breakevens`, `delta`) inalteradas — a Fase 16 e a Fase 17 consomem esse
   dicionário direto, sem remapeamento.
3. A nova chamada de rede passa a existir fora do módulo `opcoes_motor.py`
   propriamente dito (que continua puro) ou o módulo deixa de ser puro por
   desenho — decisão de implementação a tomar no momento da troca, mas em
   qualquer dos dois casos o novo caminho de rede tem que passar pelo MESMO
   princípio de orçamento/lock que rege `mydata_client.py` hoje (Decisão 3
   deste ADR permanece válida para o MCP: canal único, nunca paralelo).

**Guardiões de `test_opcoes_fronteira.py` que precisam ser REESCRITOS** no
dia da troca (porque deixam de ser verdade por desenho):
- Guardião A (ENG-03, proibição de rede/httpx/mcp/string b-mcp em
  `opcoes_motor.py`) — a troca introduz exatamente o que este guardião
  proíbe hoje; ele precisa ser removido ou movido para outro módulo se a
  chamada de rede for isolada num adaptador novo.
- Guardião ENG-04 "sem relógio" e allowlist de imports de `opcoes_motor.py`
  — se o cliente MCP exigir estado adicional (sessão de conexão, timeout),
  a allowlist precisa crescer deliberadamente, não silenciosamente.

**Guardiões que CONTINUAM valendo** sem alteração:
- Guardião de assinatura congelada (`rastrear(cadeia, filtros)` /
  `avaliar(pernas)`) — é exatamente o que garante que a troca seja
  transparente para todo chamador.
- Guardião B (ausência de `mcp` em `requirements.txt`/`requirements-prod.txt`)
  — passa a falhar de propósito no dia da troca, como sinal de que a
  dependência nova precisa ser adicionada conscientemente (não é guardião a
  reescrever, é guardião que vai ACUSAR a mudança de dependência, o que é o
  comportamento correto).
- Guardião C (canal único com orçamento, ENG-05) — o princípio de "um
  caminho só, sob lock" continua válido; só o nome do módulo autorizado
  muda (de `mydata_client` para o cliente MCP novo).

## Consequências

**Fica mais fácil:**
- O motor de N pernas próprio é testável offline, sem depender da
  disponibilidade do serviço MCP nem do hub mydata — a suíte inteira de
  `opcoes_payoff`/`opcoes_gatilho`/`opcoes_motor` roda sem rede.
- A Fase 16 (biblioteca de 3 estruturas) e a Fase 17 (fluxo de aceite)
  podem ser construídas e testadas sem esperar `plano-mcp-servico.md` ser
  aprovado — o produto não fica bloqueado por uma decisão de terceiro
  repositório.

**Fica mais difícil / o que se paga:**
- A matemática de payoff vive em dois repositórios (`~/dev/MCP/servers/
  mydata/calculos.py` e `server/app/opcoes_payoff.py`) e pode divergir com
  o tempo se um dos dois evoluir sem o outro. Mitigação: `opcoes_payoff.py`
  tem suíte própria (`test_opcoes_payoff.py`) que testa a aritmética
  isoladamente, e a fonte externa (`~/dev/MCP`) é tratada como read-only
  para esta fase — nenhuma edição no repo externo, só leitura de
  referência.
- A régua de seleção (liquidez + strike extremo) e a régua do b-mcp (delta)
  são deliberadamente diferentes — se o Alex decidir um dia unificar os
  dois critérios, isso é decisão de produto nova, não consequência
  automática desta troca.

**A revisitar:**
- No dia em que `plano-mcp-servico.md` for aprovado, revisitar se o corpo
  de `rastrear`/`avaliar` deve chamar o MCP diretamente ou se um adaptador
  intermediário (mantendo os dois módulos puros) é preferível — decisão de
  implementação, não de arquitetura, deixada para esse momento.
