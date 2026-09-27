# Phase 42: Crítico — cor, chip único e ordem de leitura - Context

**Gathered:** 2026-09-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Camada de apresentação do card único de ativo (`AtivoCard`, `web/src/App.jsx:3368`)
e do cabeçalho/corpo do Radar que o reaproveita como `children`
(`App.jsx:~6840-6990`). O usuário lê o card como uma HISTÓRIA coerente —
decisão → quando → plano → contexto (com alinhamento dito) → elegibilidade — e
distingue em <3s o veredito do que é contexto e do que é ressalva estatística.

Entrega: COR-01, HIER-01, HIER-02, CHIP-01, CHIP-02.
Não entrega (Fase 43): microtexto de reconciliação por modo (HIER-03),
`KpiBlock` → `SinalChip` (CHIP-03), escala 4/8pt (RITMO-01).

Motor intocado: nenhum teste de `setups.py`/`kpi.py`/`signal_ledger.py`/
`regime.py` muda. Separação decisão × elegibilidade (ADR-017) fica mais
legível, nunca fundida.

### Correções factuais ao ROADMAP/REQUIREMENTS (medidas em 2026-09-26)

- **"8 combinações tema×modo" → são 4.** `PALETTE` tem 2 temas (`dark`/`light`,
  `App.jsx:105`) e `MODE_OPERADOR` 2 overrides (`App.jsx:175`). O critério de
  contraste AA vale nas 4 combinações.
- **"4 contextos do AtivoCard (Acompanhar/Mesa/Posições/home)" → são 2.** Só há
  dois call sites: `contexto="watchlist"` (`App.jsx:3955`) e `contexto="radar"`
  (`App.jsx:6891`). Posições/home não renderizam `AtivoCard` hoje. O critério
  de ordem vale para Watchlist + Radar. Se Posições/Portfólio tiver composição
  própria de chips, é achado registrado na fase, não escopo (já em Out of Scope).

</domain>

<decisions>
## Implementation Decisions

### Storyline e coerência dos indicadores
Gatilho do Alex nesta discussão: "não posso ter todos os indicadores apontando
alta, fundamento A, confluência 100% e estarmos indicando a venda". Diagnóstico
confrontado com o motor: é quase todo narrativa, não dado errado — confluência é
aderência ao MELHOR setup direcional (`setups.detect_setups`, `setups.py:535`),
que pode ser de venda; fundamento é qualidade, não direção; regime contra a
decisão já é calculado (`regime._gatilho_alinhado`, `regime.py:193`) mas só é
dito quando alinhado. A exceção real é o chip de direção da IA (duas fontes).

- **D-01: Narrar o alinhamento, de forma determinística, sem tocar no motor.**
  Cada indicador de contexto declara sua relação com a decisão:
  - confluência diz o LADO e o setup (ver D-09);
  - regime diz "a favor" ou "contra a tendência" a partir de `gatilhoAlinhado`
    (já no payload do scan — no Radar vem em `r.gatilhoAlinhado`; para a
    Watchlist o planejador verifica se o campo chega em `sc`, e se não chegar
    NÃO recalcula no front com lógica nova — ou repassa o campo existente do
    payload ou omite a marca; nunca inventa);
  - fundamento é rotulado como qualidade da empresa, "não indica direção".
  Sem decisão direcional (AGUARDAR/NÃO OPERAR/sem leitura) não há marca de
  alinhamento — não existe lado para estar a favor ou contra.
- **D-02: Chips da IA saem do card.** `kp.direcao`/`kp.conviccao`/`kp.qualidade`
  (vêm da análise da IA, `App.jsx:1062` "KPIs executivos vindos da análise da
  IA") deixam de renderizar no `AtivoCard`. O card mostra só o que o motor
  calcula. A leitura da IA continua no detalhe técnico (`KpiBlock`, migrado na
  Fase 43). Elimina a segunda fonte de direção na mesma tela (guardrail "manchete
  só do motor; IA explica").

### Canal de cor
- **D-03: Inelegível ("sem vantagem estatística medida") usa `T.warn`.**
  Âmbar já significa "honestidade de dado" no app (cota, dado degradado —
  racional em `App.jsx:497-522`). Criar par de tint `warnTint10` nos 2 temas;
  `MODE_OPERADOR` herda da base, a menos que o contraste AA falhe em alguma das
  4 combinações — aí o override entra no modo. Sem hex solto fora de `PALETTE`.
- **D-04: Elegível vira neutro com ✓.** Texto forte neutro (`T.textPrimary`/
  `T.textSecondary`) + glifo ✓, sem verde. `HISTORICO_PILL_STYLE` não referencia
  `T.positive` nem `T.negative` (grep guardião do COR-01). Má notícia continua
  com cor (âmbar), nunca apagada — o "nunca dim" original segue respeitado.
  Estados `insuficiente`/`nunca_medido`/`aposentado` mantêm o contrato atual.
- **D-05: Verde/vermelho ficam reservados a manchete (decisão), preço/variação
  e P&L.** Nenhum chip de contexto usa `T.positive`/`T.negative`.
- **D-06: Chips de contexto são neutros.** REGIME ALTA/BAIXA e FUNDAMENTO A/B/C
  perdem a cor semântica; o valor vai em texto forte neutro. (Decisão derivada
  de D-05, confirmada pelo Alex.) `SCORE_COLOR`/`REGIME_STYLE` deixam de dirigir
  cor dentro do card.
- **D-07: Marcas de alinhamento são neutras: texto + glifo** (ex. "↗ a favor",
  "↘ contra a tendência") em texto secundário. Âmbar NÃO é usado para "contra" —
  seria reusar o canal de confiabilidade para outro significado.

### ConfluenceRing (tier único)
- **D-08: Anel pequeno (~36px) DENTRO do bloco da manchete**, à direita de
  COMPRAR/VENDER, no mesmo fundo (`decBg`). Igual em Watchlist e Radar. Remove:
  o pill "confiança X" (`App.jsx:6896`), o bloco `ConfluenceRing` 54px + rótulo
  do rodapé do Radar (`App.jsx:~6940-6947`) e o chip "confluência X%" da linha
  de chips da Watchlist. Tier aparece uma vez por card.
- **D-09: Rótulo = % + tier + lado + setup**, ex. "100% · Forte — padrão de
  venda: Reversão de sobrecompra". Absorve o chip/texto de `melhorSetup` e o
  "x/y critérios" do Radar. O termo "confiança" sai do card para este dado; o
  nome é "confluência". Lado vem do `lado` do setup/plano (motor), nunca do texto.
- **D-10: Sem setup (confluência 0 / sem `melhorSetup` / sem leitura do motor)
  o anel não renderiza** — a manchete e o `motivo` já dizem a ausência.

### Ordem de leitura (HIER-02)
Ordem final do card, nos dois contextos:
0. identidade + preço + **resumo da posição** (D-13)
1. **manchete** (peso `primario`) com o anel de confluência dentro (D-08)
2. **TimingBadge** colado à manchete (D-11)
3. **plano operacional** por modo (D-12), quando existir
4. **uma linha de contexto** (peso `contexto`): regime + fundamento, com marcas
   de alinhamento (D-01/D-07)
5. **elegibilidade estatística** (`HistoricoPill` reestilizado, D-03/D-04) —
   última, em linha própria, fora da linha de contexto
6. cauda do contexto (Watchlist: posição no risco/histórico/CTAs; Radar:
   aprofundar/monitorar/critérios) — inalterada

- **D-11: TimingBadge fica logo abaixo da manchete, antes do plano** (é o
  "quando" da mesma decisão; posição F1 mantida).
- **D-12: Plano por modo, um bloco só.** Operador = caixa entrada/stop/alvo/
  R:R/sizing. Estudo = `motivo` determinístico + `PlanRuler` didática. A régua
  sai do Operador (hoje o Radar no Operador mostra caixa + régua duplicadas).
  Na Watchlist o bloco aparece só se o dado de plano já chegar no `vm`; trazer
  plano para a Watchlist por plumbing novo de API NÃO é escopo.
- **D-13: Resumo da posição ("em carteira · cotas · PM · resultado") fica acima
  da manchete, como hoje** — é situação do usuário, não sinal.

### SinalChip (CHIP-01/02)
- **D-14: Um componente `SinalChip` com `peso` ∈ {`primario`, `contexto`}**,
  visual fixo por peso, não escolhido por chamada (sem prop de cor livre).
  `primario` = só a manchete/decisão; `contexto` = regime, fundamento, marcas,
  elegibilidade. Substitui `chip()` interno do `AtivoCard`, `FundamentoChip`,
  `RegimeChip` e o pill de confiança. A exceção de cor dentro do `contexto` é o
  estado de elegibilidade (âmbar para inelegível), expressa como variante de
  ESTADO do contrato, não como cor por chamada.
- **D-15: Todo `SinalChip` tem `aria-label` descritivo** no padrão do
  `HistoricoPill` (`App.jsx:~6606`), incluindo a marca de alinhamento no texto
  acessível.
- **D-16: Posturas herdadas preservadas:** regime `indefinido` não vira chip;
  fundamento sem score não vira chip; base degradada do regime (`·SMA50`)
  continua declarada; `null` nunca vira 0.

### Claude's Discretion
- Forma visual exata de cada peso (borda × fundo × tamanho), respeitando: peso
  `primario` claramente dominante; `contexto` sem cor de direção.
- Onde a âncora didática do setor `analise` (`SetorAlvo`, hoje envolvendo a
  linha de chips com a confluência) passa a viver — provável: no anel. Setor
  `fundamento` continua no chip do fundamento. Não perder nenhum setor tocável.
- Anel quando há setup mas decisão NÃO OPERAR (esticado, R:R baixo): mostrar o
  anel (o setup existe) com o rótulo de lado — D-10 só suprime sem setup.
- Onde mora a string das marcas de alinhamento e do rótulo do anel: se for
  texto por modo, `web/src/copy.js` (e `skill_ref.py` se o backend já tiver a
  frase); nenhuma string solta nova no componente.
- Nome do token de tint (`warnTint10` ou equivalente) e se o Operador precisa
  de override.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Auditoria e requisitos
- `qa/AUDITORIA-Jornada-Decisao-v1.md` — fonte da milestone: diagnóstico 1.1-1.4, o que não mexer (§2), plano de fases (§3), critério de aceite (§4). Linhas citadas estão ~25 abaixo do código atual (drift).
- `.planning/REQUIREMENTS.md` — COR-01, HIER-01/02, CHIP-01/02 + invariantes transversais.
- `.planning/ROADMAP.md` §"Phase 42" — success criteria (com as 2 correções factuais deste CONTEXT).
- `qa/AUDITORIA-Design-System-v1.md` — tokens por modo, `ConfluenceRing`, `chipModo` (contexto da auditoria anterior; §3.2 é da Fase 43).

### Decisões de produto que não se reabrem
- `docs/adr/017-revisao-de-setups-e-selecao-dinamica.md` — decisão × elegibilidade separadas; secundariedade do `HistoricoPill`.
- `docs/adr/009-eixo-de-selecao.md` — regime como eixo do Radar; origem do `RegimeChip`/`gatilhoAlinhado`.
- `docs/adr/016-qualidade-do-sinal-do-motor-de-setups.md` — contexto do motor de setups.
- `.planning/milestones/v1.1-phases/08-interface-e-ia-da-sele-o-din-mica-vocabul-rio-novo-skill-ref/08-UI-SPEC.md` — contrato de cor/foco do `HistoricoPill` que esta fase REVISA deliberadamente (COR-01/D-04). Registrar a revisão.

### Motor (ler, não alterar)
- `server/app/setups.py` — `detect_setups` (:535, melhor setup/lado/confluência), `plano_operacional` (:639).
- `server/app/regime.py` — `_gatilho_alinhado` (:193), `ranquear` (`gatilhoAlinhado` no payload, :293).
- `server/app/signal_ledger.py` — semântica de elegível/inelegível (:~188).

### Guardiões de teste que esta fase muda DELIBERADAMENTE (atualizar com nota, nunca apagar)
- `web/tests/test_historico_ui.mjs` — trava `elegivel→[T.positive…]` / `inelegivel→[T.negative…]` (linhas 53-58): reversão deliberada por COR-01/D-03/D-04.
- `web/tests/test_radar_leitura_rapida.mjs` — P3b trava o pill "confiança {tierLabel}" (linhas 57-59): substituído pelo anel (HIER-01/D-08).
- `web/tests/test_radar_regime_chip.mjs` — trava existência/wiring/ordem de `RegimeChip` após `FundamentoChip`: migra para `SinalChip`, preservando "indefinido nunca vira chip".
- `web/tests/test_historico_setup_card_ui.mjs`, `web/tests/test_mode_operador_light_palette.mjs` — conferir; podem assentar em estrutura/cor tocada.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ConfluenceRing({conf,size,label})` (`App.jsx:6553`) — já tem `role="img"`/`aria-label`; cor do arco hoje usa `P.positive` para ≥75 — revisar à luz de D-05 (arco verde ao lado de VENDER reintroduz a colisão; tier já tem paleta própria `TIER_FILL`, `App.jsx:1098`).
- `tierOf(conf)` (`App.jsx:1085`) — índice [1] (rótulo) travado por teste; não mudar.
- `HistoricoPill` + `historicoEstado`/`historicoTxt`/`copyFor(...).historicoRotulo` — padrão de `aria-label` e copy por modo a replicar no `SinalChip`.
- `T.warn` (`PALETTE.dark` `#fbbf24`, `PALETTE.light` `#a16207`) + padrão `color-mix(in srgb, T.warn 12%, transparent)` já usado em `App.jsx:538` — referência para o tint.
- `decisaoDoModo`/`REC_STYLE` (`App.jsx:1286`) — cor da manchete (peso `primario`); intocado.
- `PlanRuler`, `TimingBadge`, `SetorAlvo` — reposicionados, não reescritos.

### Established Patterns
- Tokens via `T.x` → CSS vars por tema/modo (`THEME_CSS`, `App.jsx:~229`); nada de hex solto (exceção documentada: `TIER_FILL`).
- Comentários carregam histórico de decisão (qa/NN, ADR, Fase) — mudanças devem anotar "Fase 42 (COR-01/…)".
- Copy por modo em `web/src/copy.js` (`COPY.estudo`/`COPY.operador`), espelhando `skill_ref.py` quando a frase existe no backend.

### Integration Points
- `AtivoCard` corpo: `App.jsx:~3560-3625` (posição, manchete, timing, linha de chips `SetorAlvo analise`).
- Radar `children`: `App.jsx:~6891-6950` (pill confiança, `FundamentoChip`, `RegimeChip`, texto melhorSetup, `HistoricoPill`, motivo, caixa de plano, anel do rodapé, `PlanRuler`).
- `radarVm.sc` (`App.jsx:~6889`) é subconjunto explícito de `r` — adicionar `lado`/`gatilhoAlinhado` se D-01/D-09 precisarem, sem passar `r` inteiro.
- O Radar hoje passa `kp: {}`; a Watchlist passa `kp` da IA — D-02 remove o uso de `kp` no card.

</code_context>

<specifics>
## Specific Ideas

- Caso de teste humano: card de UGPA3 (ou equivalente) com manchete VENDER e contexto "de alta" — o leitor precisa entender em <3s que é um padrão de VENDA a 100% contra a tendência, com empresa de boa qualidade (que não diz direção), e se há ou não vantagem estatística medida.
- Rótulo alvo do anel: "100% · Forte — padrão de venda: Reversão de sobrecompra".
- Marca alvo: "↘ contra a tendência" / "↗ a favor".

</specifics>

<deferred>
## Deferred Ideas

- **Motor: decisão contra o regime.** Se VENDER/COMPRAR contra a tendência deve virar AGUARDAR ou exigir confirmação é lógica de decisão (`setups.py`/`regime.py`) — fora da v1.9 por invariante. Candidato a milestone futuro; o Alex escolheu só narrar nesta fase.
- Motion no `ConfluenceRing` ao trocar de tier (Future Requirements da v1.9).
- Tokens `--sp-*` globais (Future Requirements; RITMO-01 da Fase 43 cobre só o card).

### Reviewed Todos (not folded)
- `revisao-arquitetura-mcp-ecossistema-b3.md`, `opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp.md`, `medir-rate-limit-mydata.md` — casados por palavra-chave pelo SDK, sem relação com apresentação do card.

</deferred>

---

*Phase: 42-cr-tico-cor-chip-nico-e-ordem-de-leitura*
*Context gathered: 2026-09-26*
