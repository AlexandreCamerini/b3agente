# Phase 43: Refinamento — copy por modo, KpiBlock e ritmo - Context

**Gathered:** 2026-09-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Entrega três coisas sobre o card já religado na Fase 42, sem abrir escopo novo de decisão/elegibilidade e sem tocar no motor:

1. **HIER-03**: microtexto de reconciliação por modo na linha de elegibilidade do `AtivoCard`, reconciliando "o padrão bateu os critérios" com "o histórico medido mostra X". Texto vem do par `server/app/skill_ref.py` ↔ `web/src/copy.js`, e os números vêm do `signal_ledger`.
2. **CHIP-03 (premissa corrigida, ver D-01)**: direção, convicção e qualidade da IA voltam a ser visíveis como `SinalChip` peso `contexto`, dentro da leitura da IA (`AnalysisView`), nunca no card. O `KpiBlock`/`KpiCell` morto é apagado.
3. **RITMO-01**: escala 4/8pt no card inteiro, entre os blocos e dentro deles, via constante nomeada `SP`.

Mais dois fold-ins das pendências da Fase 42: "FUNDAMENTO" duplicado e alvo de toque < 44px.

Não entrega: tokens `--sp-*` globais nem migração de outras telas para `SP`, motion do `ConfluenceRing`, mudança de lógica de decisão.

</domain>

<decisions>
## Implementation Decisions

### Leitura da IA (CHIP-03)
- **Achado do scout (premissa da CHIP-03 errada):** o `KpiBlock`/`KpiCell` (`web/src/App.jsx:1327-1366`) é código morto desde a qa/49 (`App.jsx:3925`: "KpiBlock removido") — nenhuma tela o renderiza, não existe "detalhe técnico com grade de caixas cinzas". Com a D-02 da Fase 42 (chips da IA fora do card, 42-04), direção/convicção/qualidade da IA deixaram de aparecer em QUALQUER tela. A D-02 da 42 assumia "a leitura da IA continua no detalhe técnico" — falso.
- **D-01:** Os três voltam dentro da **leitura da IA — `AnalysisView`** (`App.jsx:1616`, a análise formatada dentro do card da Watchlist, com resumo/confirmações/invalidações), NÃO no detalhe de candles e NUNCA no card (D-02 da 42 mantida).
- **D-02:** Forma: 3 `SinalChip peso="contexto"` **neutros** (sem verde/vermelho — COR-01/D-14 da 42; direção com seta textual ↗/↘ no valor), numa linha sob o rótulo "Leitura da IA". Cada chip com aria-label descritivo (CHIP-02).
- **D-03:** A **recomendação da IA (`kpis.recomendacao`) NÃO vira chip** — decisão é só do motor (guardrail CVM, "manchete só do motor; IA explica").
- **D-04:** Aparece só quando `an.kpis` existe; no caminho determinístico (`an.fonte === "deterministico"`, sem kpis) a linha é omitida — nunca placeholder, nunca "—" inventado.
- **D-05:** `KpiBlock`, `KpiCell` e o que ficar órfão só por eles (verificar `DIR_STYLE`/`SCALE_STYLE`) são apagados. Guardiões que os citam são reconciliados com nota datada, nunca apagados.
- **D-06:** Texto de ROADMAP SC#2 / REQUIREMENTS CHIP-03 ("detalhe técnico aberto via gráfico de velas… grade de caixas cinzas") é corrigido no fechamento da fase como correção factual (ROADMAP no lugar; REQUIREMENTS com nota, texto original preservado — mesmo padrão da 42).

### Microtexto de reconciliação (HIER-03)
- **D-07:** O microtexto **substitui os números crus** (`+0,005R n=123 2024`) na linha de elegibilidade do card. Fica: chip de estado (âmbar/neutro, aprovado na 42) + uma frase. `n` e janela vão dentro da frase. O `expR` sai da linha no Estudo (continua no aria-label); no Operador volta dentro da frase (D-12).
- **D-08:** **Frase própria para cada estado**, nunca omitindo nem inventando `n`:
  - elegível / inelegível: "bateu os critérios; em {n} ocorrências na janela {janela} houve / não houve vantagem medida";
  - insuficiente (n<40): "bateu os critérios; só {n} ocorrências — pouco para medir";
  - nunca medido: "bateu os critérios; ainda sem histórico medido";
  - aposentado (ADR-016): "padrão identificado; sem vantagem medida em 15 anos (ADR-016)".
  Redação final é da UI-SPEC/planner, dentro deste conteúdo.
- **D-09:** **Só na linha de elegibilidade do `AtivoCard`** (Watchlist e Radar). As listas por setup (cauda do Radar, lista do Operador IA) e o modo `compacto` continuam com chip + números: ali o usuário compara setups lado a lado.
- **D-10:** Modificador `desatualizado` (⏱ {medidoAte}) segue como está, depois da frase.

### Tom por modo
- **D-11 (Estudo):** duas orações — o fato + o "por que importa" ("sinal técnico e histórico medido são coisas diferentes"). A oração do porquê é tocável e abre o conceito existente na camada de entendimento (sem texto de conceito novo inventado; se não existir verbete adequado, o planner aponta e usa o mais próximo existente).
- **D-12 (Operador):** fato curto com `n`, janela e `expR`: "Critérios ok · sem vantagem medida (n=123, 2024, +0,005R)". `expR` formatado como hoje (3 casas, vírgula, sinal explícito), `null` nunca vira 0 (regra de casa).
- **D-13:** Texto mora em dict novo em `server/app/skill_ref.py` (ao lado de `HISTORICO`/`HISTORICO_ROTULO`) com espelho em `web/src/copy.js` e função `…Txt(mode, estado, vals)` espelhada (mesmo padrão de `historico_txt`/`historicoTxt`). Paridade de chaves coberta pelo guardião cruzado existente.

### Escala 4/8pt (RITMO-01)
- **D-14:** Alcance: **card inteiro** — espaço entre os blocos (manchete → timing → plano → contexto → elegibilidade) **e** padding/gap internos dos blocos (`SinalChip` primário/contexto, `LinhaContexto`, `PlanoOperacionalBloco`, `HistoricoPill`, corpo do `AtivoCard`). Font-size, raio e line-height fora do escopo.
- **D-15:** Constante única nomeada **`SP`** em `web/src/App.jsx`: `{1:4, 2:8, 3:12, 4:16, 5:20, 6:24, 8:32}` (`qa/AUDITORIA-Design-System-v1.md §3.2`). O card usa agora; outras telas NÃO migram nesta fase (tokens globais seguem deferidos).
- **D-16:** Exceção de micro-ajuste óptico permitida **só como constante nomeada e comentada** (ex.: `SP_OPTICO_2`), numa lista fechada que o guardião aceita. Guardião novo: zero px solto de espaçamento (margin/padding/gap) no corpo do `AtivoCard` e dos blocos listados em D-14.

### Fold-in (pendências da Fase 42)
- **D-17:** "FUNDAMENTO" duplicado na `FundamentoTabela` (`App.jsx` ~1572/1576): sai o `label` do `SinalChip` (fica só o valor A/B/C) e o cabeçalho da tabela continua. Aria-label do chip continua descritivo.
- **D-18:** Alvo de toque do chip de fundamento tocável na `LinhaContexto` < 44px: corrigido pela **área de toque** (padding/hit-area), não pelo tamanho visual, junto com a D-14.

### Claude's Discretion
- Chave/nome do dict novo em `skill_ref.py` e da função espelhada.
- Formato exato da seta de direção no chip da IA e rótulo da linha ("Leitura da IA").
- Mapeamento de cada valor avulso atual (9px/11px/…) para o degrau da escala: o mais próximo, com a exceção óptica só onde o resultado visual quebrar.
- Radar "Aprofundar com IA" (`scan_deep`): se o payload trouxer `kpis`, aplicar a mesma linha da D-02; se não trouxer, não inventar.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requisitos e fase anterior
- `.planning/REQUIREMENTS.md` — HIER-03, CHIP-03, RITMO-01 + invariantes transversais da v1.9.
- `.planning/ROADMAP.md` §"Phase 43" — goal e success criteria (SC#2 com premissa errada, ver D-06).
- `.planning/phases/42-cr-tico-cor-chip-nico-e-ordem-de-leitura/42-CONTEXT.md` — D-02 (IA fora do card), D-03/D-04 (cor de elegibilidade), D-14 (SinalChip sem cor livre).
- `.planning/phases/42-cr-tico-cor-chip-nico-e-ordem-de-leitura/42-UI-SPEC.md` — contrato visual do card, ordem de leitura, `warnTint10`.
- `.planning/phases/42-cr-tico-cor-chip-nico-e-ordem-de-leitura/42-06-SUMMARY.md` — DP-1..DP-4 aprovadas, pendências.

### Vocabulário e didática
- `server/app/skill_ref.py` (seção "Vocabulário do histórico medido por setup", ~l.355-435) — `HISTORICO`, `HISTORICO_ROTULO`, `historico_txt`: padrão a seguir para o dict novo.
- `web/src/copy.js` (`historicoRotulo` ~l.593/1367, `historicoTxt` ~l.1600) — espelho.
- `.claude/skills/didatica-boris/SKILL.md` — vocabulário por modo, resultado negativo com o mesmo peso do positivo, "Não há dados suficientes para concluir".

### Design system
- `qa/AUDITORIA-Design-System-v1.md` §3.2 — escala 4/8pt (`--sp-1..8`), "exceções só em micro-ajuste óptico".

### Histórico medido (dado)
- `server/app/regime.py:231-312` — `_elegibilidade`, `setupHistorico`/`setupElegivel` (fonte dos estados e de n/janela/expR).
- `docs/adr/016-qualidade-do-sinal-do-motor-de-setups.md` e `docs/adr/017-revisao-de-setups-e-selecao-dinamica.md` — aposentadoria de setup e separação decisão × elegibilidade.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `SinalChip` (`App.jsx:1383`): pesos `primario`/`contexto`, `estado`, `ariaLabel`, `explicavel` — base de D-02, D-07, D-17.
- `HistoricoPill` (`App.jsx:6750`): já calcula `estado`, `expRJanela`, `nJanela`, `janelaRef`, `velho` — o microtexto nasce aqui (ou num irmão chamado só pelo `AtivoCard`, preservando as listas — D-09).
- `historicoEstado`, `historicoTxt`, `copyFor(modo)` — padrão de texto por modo.
- `AnalysisView` (`App.jsx:1616`) e `an.kpis` (`App.jsx:7987`/`8311`) — onde os chips da IA entram.
- Camada de entendimento (`web/src/entendimento.jsx`, `SetorAlvo`/`ConceitoSheet`) — para a oração tocável do Estudo (D-11).

### Established Patterns
- Guardiões de teste por invariante, com reconciliação datada ("REVERSÃO DELIBERADA (data, Fase N, ID)"), nunca apagados.
- Paridade `skill_ref.py` ↔ `copy.js` testada por guardião cruzado.
- `null` nunca vira `0` na UI (regra de casa).

### Integration Points
- `AtivoCard` (Watchlist `App.jsx:~4112`, Radar `~7035`): linha de elegibilidade (`<HistoricoPill>` em linha própria, 42-04).
- `LinhaContexto` / `PlanoOperacionalBloco` / `FundamentoTabela`: espaçamento (D-14) e fold-ins (D-17/D-18).

</code_context>

<specifics>
## Specific Ideas

- Exemplo aprovado de Operador: "Critérios ok · sem vantagem medida (n=123, 2024, +0,005R)".
- Exemplo aprovado de Estudo: "O padrão bateu os critérios, mas em 123 ocorrências na janela 2024 não houve vantagem medida — sinal técnico e histórico medido são coisas diferentes."
- Checkpoint humano da fase (SC#4): o Alex lê o card de UGPA3 (ou equivalente) em < 3 s nos dois modos, com o microtexto visível; e abre a leitura da IA na Watchlist para ver os 3 chips.

</specifics>

<deferred>
## Deferred Ideas

- Tokens `--sp-*` globais e migração das outras telas para `SP` (Future Requirements).
- Motion no `ConfluenceRing` ao trocar de tier (Future Requirements da v1.9).
- Motor: decisão contra o regime (herdado da 42, fora da v1.9 por invariante).
- Chips da IA no detalhe de candles (alternativa rejeitada na D-01).

### Reviewed Todos (not folded)
- `revisao-arquitetura-mcp-ecossistema-b3.md`, `medir-rate-limit-mydata.md` — casados por palavra-chave pelo SDK, sem relação com apresentação do card.

</deferred>
