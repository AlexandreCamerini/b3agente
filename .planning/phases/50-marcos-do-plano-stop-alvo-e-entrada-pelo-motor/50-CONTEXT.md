# Phase 50: Marcos do plano — stop, alvo e entrada pelo motor - Context

**Gathered:** 2026-10-21
**Status:** Ready for planning
**Discussão:** Alex + orquestrador, com a régua técnica da skill `analise-tecnica-b3` (princípios 5, 6 e 8: R:R ≥ 1,5, stop na invalidação, não perseguir movimento esticado).

<domain>
## Phase Boundary

Toda posição comprada — aberta pela entrada automática do Operador ou pela compra manual a partir de um plano — passa a ter **entrada, stop e alvo calculados por UMA função determinística do motor**, com geometria validada antes de gravar. A IA (N2/N3) deixa de produzir os números gravados e passa a explicá-los. O Operador gerencia a posição com breakeven + trailing por padrão, não executa sobre marcos inválidos, e as opções lastreadas (call coberta / put de proteção) ancoram os strikes nesses marcos.

Gatilho da fase (2026-10-21): posição real no iPhone com preço médio 23,01, cotação 23,51, STOP 23,36 e **ALVO 21,58** (abaixo da cotação) — gravado via `PUT /api/position` sem validação; na abertura seguinte o Operador venderia por "alvo atingido".

Fora do escopo: lado vendido (short) de ação; realização parcial (o motor é tudo-ou-nada por decisão do ROADMAP v1.1, C-14); novos setups ou revisão da qualidade dos detectores (ADR-016/017 continuam valendo).
</domain>

<decisions>
## Implementation Decisions

### Fonte única dos marcos (motor)
- **D-01 Stop:** `stop = invalidação do setup − 0,1×ATR(14)` (folga contra ruído). Se a distância `entrada − stop` ficar **< 0,5×ATR**, o stop vai para `entrada − 1×ATR`. Se ficar **> 3×ATR**, o plano é recusado ("stop largo demais"), com motivo no Diário/card.
- **D-02 Alvo:** `alvo = primeira resistência relevante acima da entrada`, desde que o R:R a partir da entrada seja **≥ RR_MIN (1,5)**. Se a resistência estiver antes de 1,5R → **não opera** (teto próximo demais). Sem resistência no caminho → `alvo = entrada + 2R`. Um alvo só (sem parcial).
- **D-03 Entrada:** mantém a regra atual de `setups.plano_operacional`: entrada no gatilho; se o preço já passou, aceita até 0,5R acima (`ZONA_PERSEGUICAO`); além disso, "não persiga". Passa a valer em todos os caminhos que gravam marcos.
- **D-04 Uma função só:** as 4 fórmulas de hoje (invalidação do setup, `riskPlanReference`, `localProposal` do front, número da IA no N3) são reconciliadas numa função pura do motor (backend), com espelho no front só se for indispensável (paridade testada). `riskPlanReference` e `localProposal` deixam de ser fonte de número gravado (podem virar insumo ou ser removidos — decisão do planner, sem dois cálculos para o mesmo conceito).
- **D-05 R:R:** uma definição canônica para decidir (a partir da entrada/preço executado). O R:R "a partir do preço atual" do card (`cartao_posicao.rr`, `rrPos` do App) pode continuar como leitura de acompanhamento, mas rotulado de forma distinta — o planner decide nome/rótulo.

### Entrada automática e compra manual
- **D-06 Preço executado ≠ gatilho:** stop e alvo ficam nos **níveis técnicos** do plano (não deslocam com o preço). O R:R é recalculado a partir do preço executado; se cair **< 1,5**, a compra **não acontece** e o Diário diz por quê.
  - **Esclarecimento (Alex, 2026-10-21, após o plan-checker):** a recusa vale **só para a entrada automática**. Compra manual (imediata ou pendente) com R:R < 1,5 ou entrada além de 0,5R do gatilho no preço executado **executa sem marcos**; a resposta e o card dizem por que o motor não traçou plano e pedem para definir (parecer não é veto).
- **D-07 Tamanho da posição:** `qty = (risco por operação, ex. 1% do patrimônio) ÷ (entrada − stop)`, em lotes de 100 (arredonda para baixo), **limitado pelo `allocPct` do caixa**. Mesma conta de `sizingPlano` (`web/src/finance.js:415`) — uma fonte só. Se não couber 1 lote, não compra e avisa.
- **D-08 Entrada automática nasce com stop e alvo** do motor gravados no ato da compra (hoje `store.buy` cria `stop: None, alvo: None`).
- **D-09 Compra manual a partir de plano/setup** também nasce com os marcos do motor (o `buyMeta` já leva gatilho/invalidação); o usuário pode editar depois, sujeito a D-11. Compra sem plano nasce sem marcos e o card pede para definir. Ordem pendente (`pending_orders.py:196`) segue a mesma regra quando executar.

### IA e validação
- **D-10 IA só explica:** N2/N3 ("Ajustar plano · IA") recebem os marcos do motor e explicam racional, riscos e quando revisar. **Não devolvem números para gravar.** Os prompts default (`server/app/defaults.py` ↔ `web/src/catalog.js`, paridade byte a byte) e os formatos (`llm.py` FORMAT/`parse_carteira`/`kpi.parse_rich`) mudam de acordo; `applyStopAlvoFor`/`applyProposal` passam a aplicar os marcos do motor, não os da IA.
- **D-11 Validação de geometria no motor (recusa):** para posição comprada, `stop < preço atual < alvo` e `stop < alvo`, valores > 0. Geometria impossível é **recusada** com motivo em PT-BR — em `store.set_position`/`PUT /api/position` e no espelho do `deviceStore`, **inclusive na edição manual**. Parecer de qualidade (R:R baixo, `operar:false`) continua sendo **só aviso, nunca veto**.
- **D-12 Invariante atualizada:** a regra do CLAUDE.md "Stop/alvo nunca são vetados" ganha a nota: vale para parecer (`operar:false`, R:R baixo); geometria impossível é recusada (decisão do Alex, 2026-10-21). Guardiões que travam a invariante são atualizados com nota, não apagados.
- **D-13 Posições já inválidas:** marco com geometria inválida **não dispara venda** no ciclo (servidor e caminho sem conta do iPhone); card e Diário mostram "plano inválido — redefina", com os marcos do motor como sugestão. Nada é reescrito sozinho.

### Gestão e opções
- **D-14 Gestão padrão:** ao andar **1R a favor**, o stop sobe para o preço de entrada (breakeven); a partir daí, **trailing de 2×ATR**, sempre monotônico (só sobe — regra que já existe em `agent.py`). Ligado por padrão nas posições com plano; o usuário pode desligar.
- **D-15 Alvo dinâmico:** continua **opt-in** (fechar no alvo é a disciplina do Estudo). Regra atual mantida (+1,5×ATR, máx. 2 extensões, R:R ≥ 1,5), medida com o stop já em breakeven/trailing.
- **D-16 Opções ancoradas nos marcos:** call coberta com o strike disponível mais próximo **≥ alvo**; put de proteção com o strike mais próximo do **stop**. Sem marcos válidos, cai na regra atual (spot, ex. `put_bridge.COLCHAO_PCT`) e **diz que caiu**.

### Decisões após o plan-checker (Alex, 2026-10-21)
- **D-17 Botão Aplicar:** continua **habilitado** mesmo com marco inválido; se o motor recusar (D-11), a mensagem do 400 aparece no modal. A guardrail "a UI sempre permite Aplicar proteção" fica literal.
- **D-18 Fonte única também na exibição:** o "ALVO 2:1" do setup (`alvoSugerido`, bloco do plano) e o `riskPlanReference` deixam de ser número exibido ou enviado à IA; a tela e a IA mostram/recebem só os marcos da função do motor. `riskPlanReference` só segue como insumo interno se algo ainda o consumir.
- **D-19 Fora da D-16:** `put_bridge` (sugestão diária compartilhada) e a curadoria top-4 de opções **não** são ancoradas nos marcos nesta fase (diferido).

### Claude's Discretion
- Nome/assinatura da função pura de marcos e onde mora (provável `setups.py` ao lado de `plano_operacional`, ou módulo novo).
- O que é "resistência relevante" (ex.: primeira de `piv["resistances"]` acima da entrada, com distância mínima) — o planner define com base em `technical_models.py` e cobre com teste de valores conhecidos.
- Valor default do "risco por operação" (1% sugerido; já existe `pct` em `sizingPlano`, teto 5).
- Texto das mensagens (vocabulário por modo via `skill_ref` ↔ `copy.js`, regras da skill `didatica-boris`).
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Regras de produto e guardrails
- `CLAUDE.md` — princípios 4/5/9, guardrails "Manchete do card vem só do motor", "Stop/alvo nunca são vetados" (a atualizar por D-12), paridade `defaults.py` ↔ `catalog.js` e `deviceStore` ↔ `serverStore`.
- `.claude/skills/didatica-boris/SKILL.md` — vocabulário por modo e textos ao usuário.

### Decisões anteriores sobre setups e medição
- `docs/adr/015-assertividade-do-motor-de-recomendacao.md` — entrada = gatilho, alvo2 como barreira; desencontro alvo1 (1R) × alvo2.
- `docs/adr/016-qualidade-do-sinal-do-motor-de-setups.md` — setups saindo por stop (stop colado no ruído; motiva D-01).
- `docs/adr/017-revisao-de-setups-e-selecao-dinamica.md` — setups aposentados e gate de elegibilidade da entrada automática (continua valendo).
- `docs/adr/002-triade-temporal.md` — plano diário × barra 15 min × timing.
- `docs/adr/021-ponte-gatilho-put.md`, `docs/adr/023-opcoes-lastreadas.md`, `docs/adr/025-collar-e-estrutura-multiperna.md` — opções a partir do plano/lastro (D-16).

### Código — motor
- `server/app/setups.py` — detectores (`_mk` l.219, `_alvo_rr` l.209), `plano_operacional` l.639-718 (entrada, zona de perseguição, recusas de geometria, `RR_MINIMO`), `plano_do_resultado` l.721.
- `server/app/technical_models.py` l.254-267, 333-337 — `riskPlanReference`, suportes/resistências (`piv`).
- `server/app/skill_ref.py` l.32-33 — `RR_MIN`, `RR_IDEAL` (fonte única; `test_rr_min_fonte_unica.mjs`).
- `server/app/agent.py` — `nivel_trailing` l.428, `avaliar_alvo_dinamico` l.489, `_avaliar_entradas` l.702 (compra sem marcos, sizing por `allocPct`), laço de saída em `_run_cycle_inner`.
- `server/app/store.py` — `buy` l.840 (sem stop/alvo), `set_position` l.602 (sem validação), `_sanitize_trade_meta` l.826.
- `server/app/pending_orders.py` l.196 — posição criada sem marcos.
- `server/app/cartao_posicao.py` l.221-262 — `leitura_plano` (R:R a partir do preço, proximidade, gatilhoStatus).
- `server/app/timing.py` l.63-130 — armado/gatilho/esticado.
- `server/app/main.py` — `PUT /api/position` ~l.3010, `/api/carteira-stopalvo` ~l.2695, N1 `analyze_deep` ~l.2282 (registro em `analysis_outcomes`), N2 ~l.2462.

### Código — IA
- `server/app/llm.py` — FORMAT N2 (stopSugerido/alvoSugerido) ~l.236-266, `analyze_carteira` ~l.1170, `parse_carteira` ~l.1071.
- `server/app/kpi.py` l.265-310 — `parse_rich` (validação stop×alvo sem preço).
- `server/app/defaults.py` ~l.165-225 ↔ `web/src/catalog.js` — prompts `carteiraStopAlvo`/`carteiraStopAlvoOperador`.

### Código — front
- `web/src/finance.js` l.415-431 `sizingPlano`, l.517-547 `setupOperavel`/`metaDeEntrada`.
- `web/src/App.jsx` — `localProposal` l.396-407, `StopAlvoModal` ~l.4181-4202, `rrPos` ~l.4070, `applyProposal` ~l.10335, `applyStopAlvoFor` ~l.10430 (ler só com offset/limit).
- `web/src/persistence.js` — `deviceStore.putPosition` ~l.1952, ciclo local sem conta.

### Código — opções
- `server/app/opcoes_lastreadas.py` l.195-275 `propor`, `server/app/put_bridge.py` l.40,70 (`COLCHAO_PCT`), `server/app/opcoes_motor.py` (`rastrear`), `server/app/opcoes_gatilho.py`.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `setups.plano_operacional` já é determinístico e recusa geometria errada e R:R < mínimo — base natural da função de marcos (D-01..D-04).
- `sizingPlano` (front) já faz sizing por risco — portar/espelhar no backend para a entrada automática (D-07).
- `agent.nivel_trailing` (modo `atr`, monotonicidade aplicada no laço) e `avaliar_alvo_dinamico` — reaproveitar para D-14/D-15.
- `store.qty_livre` / `_avisar_lastro_travado` (quick 261021-spd) — padrão de aviso deduplicado por dia para D-13.

### Established Patterns
- Número de carteira só sai do motor; LLM recebe snapshot pronto (princípio 5).
- Nullable numérico é `null`, nunca `0.0` (`test_m3_format_pede_null_nunca_zero`).
- Paridade `deviceStore` ↔ `serverStore` com teste; prompts `defaults.py` ↔ `catalog.js` byte a byte.

### Integration Points
- `store.buy` / `pending_orders` (gravar marcos na criação), `store.set_position` + `PUT /api/position` + `deviceStore.putPosition` (validação D-11), `_run_cycle_inner` (D-13, D-14), `opcoes_lastreadas.propor` / `put_bridge` (D-16), prompts e parsers de N2/N3 (D-10).

### Testes que travam o comportamento atual (atualizar com nota, não apagar)
- Servidor: `test_plano_operacional.py`, `test_setups.py`, `test_setups_br.py`, `test_technical_models.py`, `test_timing.py`, `test_agent.py`, `test_entrada_automatica.py`, `test_entrada_automatica_suspensa_adr017.py`, `test_kpi.py`, `test_pipeline_n2_n3.py`, `test_carteira_stopalvo_502.py`, `test_cartao_posicao.py`, `test_cartao_proximidade.py`, `test_analysis_outcomes.py`, `test_opcoes_gatilho.py`, `test_opcoes_lastreadas_proposta.py`.
- Front: `test_finance.mjs`, `test_rr_min_fonte_unica.mjs`, `test_posicao_stop_alvo.mjs`, `test_trailing_dinamico_ui.mjs`, `test_alvo_dinamico_ui.mjs`, `test_plano_ui.mjs`.
</code_context>

<specifics>
## Specific Ideas

- Caso de regressão obrigatório: posição PM 23,01, cotação 23,51, stop 23,36, alvo 21,58 → `PUT` recusado; se já gravado (legado), o ciclo não vende e mostra "plano inválido".
- Mudança de comportamento observável que precisa de medição: D-01 (folga de ATR) e D-02 (alvo em resistência) alteram a taxa de stop/alvo medida pelo `signal_ledger`/ADR-015 — o planner deve prever recálculo do histórico ou nota de quebra de série.
</specifics>

<deferred>
## Deferred Ideas

- Realização parcial (alvo1 1R + alvo2) — exige fill parcial, fora do modelo tudo-ou-nada (C-14).
- Lado vendido (short) de ação no motor de marcos.
- Texto do toggle "Modo local (com o app aberto)" que ainda promete proteção local (quick 261021-spd) — pode entrar aqui se o planner tocar a tela do Operador; senão, quick própria.
- Item 3 da quick 261021-spd: PUT de proteção órfã quando o stop vende as ações.
- Ancorar `put_bridge` e a curadoria top-4 de opções nos marcos (D-19).
</deferred>

---

*Phase: 50-marcos-do-plano-stop-alvo-e-entrada-pelo-motor*
*Context gathered: 2026-10-21*
</content>
</invoke>
