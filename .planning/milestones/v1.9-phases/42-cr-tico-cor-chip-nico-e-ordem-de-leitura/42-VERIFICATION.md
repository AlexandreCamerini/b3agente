---
phase: 42-cr-tico-cor-chip-nico-e-ordem-de-leitura
verified: 2026-09-27T05:27:32Z
status: passed
score: 5/5 must-haves verified (planos 42-01..42-05; 42-06 fora do escopo desta verificação, por decisão do Alex)
overrides_applied: 0
scope_note: >
  Verificação parcial e deliberada: cobre só os planos 42-01..42-05 (implementação).
  42-06 (checkpoint humano ao vivo DP-1..DP-4, publicação com carimbo próprio,
  fechamento de REQUIREMENTS.md/ROADMAP.md/STATE.md) NÃO foi executado de
  propósito e está fora do escopo desta rodada — não contado como gap. Itens
  que dependem dele estão listados em "Dependências de 42-06" abaixo, não em
  "gaps".
gaps: []
---

# Phase 42 (planos 01-05): Crítico — cor, chip único e ordem de leitura — Verificação

**Goal da fase:** o usuário distingue em <3s decisão × contexto × ressalva de
confiabilidade estatística no `AtivoCard` e no cabeçalho do Radar, sem tocar
manchete determinística nem fundir decisão × elegibilidade (ADR-017).

**Verificado:** 2026-09-27T05:27:32Z
**Status:** passed (para o que estava em escopo: 42-01 a 42-05)
**Re-verificação:** Não — verificação inicial, independente, goal-backward.

## Veredito por requisito

### COR-01 — inelegível fora do canal positive/negative — VERIFIED

Evidência:
- `web/src/App.jsx:6742-6749`: `HISTORICO_PILL_STYLE = { elegivel: [T.textPrimary, "transparent"], inelegivel: [T.warn, T.warnTint10], insuficiente: [T.textFaint, T.bgBase], nunca_medido: [T.textFaint, T.bgBase], aposentado: [T.textMuted, T.bgCard] }` — zero referência a `T.positive`/`T.negative`.
- `PALETTE.dark.warnTint10` (`App.jsx:132`) e `PALETTE.light.warnTint10` (`App.jsx:168`) declarados nos dois temas, sem hex solto fora de `PALETTE`.
- `ConfluenceRing.col` (`App.jsx:6710-6726`) usa `TIER_FILL[tierOf(c)[0]]`, não mais `P.positive`/`P.accent` — arco não colide com o canal de direção.
- Guardião `web/tests/test_cor_confiabilidade.mjs` roda contraste WCAG calculado (blend rgba sobre `bgCard`) nas 4 combinações tema×modo: 7,98:1 / 8,64:1 / 4,68:1 / 4,68:1 — todas ≥ AA 4,5:1. Executado (`node web/tests/test_cor_confiabilidade.mjs`) → TUDO OK, 28 asserções.
- Guardião `web/tests/test_historico_ui.mjs` reconciliado com nota "REVERSÃO DELIBERADA (2026-09-26, Fase 42, COR-01/D-03/D-04)" e ban-list explícita contra `T.positive`/`T.negative` no objeto `HISTORICO_PILL_STYLE`. Executado → TUDO OK, 37+ asserções.

Nota: a "meta interna de 4,7:1" (4,68:1 medido no tema claro) é a DP-1 nomeada para o checkpoint 42-06 — ainda dentro do critério formal (AA 4,5:1), não é gap.

### HIER-01 — tier de confluência uma única vez, como `ConfluenceRing` junto da manchete — VERIFIED

Evidência:
- `SinalChip` peso `primario` (`App.jsx:1383-1414`) embute `<ConfluenceRing conf={ring.pct} size={36} .../>` dentro do próprio bloco da manchete (mesmo `decBg`/fundo da decisão).
- Grep de produção confirma pill solta apagada: `test_radar_leitura_rapida.mjs` roda "RadarScreen NÃO contém mais a pill solta 'confiança {tierLabel'" → PASS; "NÃO contém mais a contagem 'x/y critérios'" → PASS.
- Rodapé duplicado do anel 54px + `TierDot` + rótulo "CONFLUÊNCIA DO SETUP" apagados do Radar (confirmado por `git diff` do 42-05 e pelo teste `test_fase22_componentes_compartilhados.mjs`: "`TierDot` foi apagado (D-08...)" → PASS; "`<ConfluenceRing` NÃO aparece dentro do bloco do Radar (...)" → PASS).
- Inspeção direta do bloco `<AtivoCard key={r.ticker} ...>...</AtivoCard>` do Radar (`App.jsx:7035-7130`) confirma que só resta a cauda (aprofundar/monitorar/critérios/condições) — nenhum anel, pill ou chip de tier duplicado.

### HIER-02 — ordem manchete → plano → contexto → elegibilidade, Watchlist e Radar — VERIFIED (nos 2 contextos existentes)

Evidência:
- `AtivoCard` (único componente, `App.jsx:3521`) renderiza, na ordem: identidade+preço → resumo da posição (`pos &&`) → manchete `<SinalChip peso="primario" .../>` com anel → `<TimingBadge>` → `<PlanoOperacionalBloco>` → `<LinhaContexto>` → elegibilidade (`<HistoricoPill>` em bloco próprio, só com `sc.melhorSetup`) → `{anVencida && (...)}` → cauda (`children`). Ordem confirmada por leitura direta de `App.jsx:3818-3866`.
- Watchlist (`contexto="watchlist"`, `App.jsx:4112`) e Radar (`contexto="radar"`, `App.jsx:7035`) chamam o MESMO `AtivoCard` — não há dois componentes/duas ordens.
- `radarVm.sc` (`App.jsx:7033`) foi ampliado campo a campo (`close, plano, setups, regime, gatilhoAlinhado, fundamento`) para alimentar o mesmo card que a Watchlist — confirmado por leitura do backend (`server/app/main.py:2172` `_enrich_fundamentos_sync`, `server/app/regime.py:293` `gatilhoAlinhado`) mostrando que ambos os payloads de `/api/scan` carregam esses campos, não é dado inventado no front.
- Guardião novo `test_sinal_chip_ui.mjs` Parte C valida a ordem estritamente crescente das posições de string no JSX (`{pos && (` < manchete < timing < plano < contexto < elegibilidade < `anVencida`) → executado, TUDO OK.
- **Correção factual herdada do 42-CONTEXT.md, não um gap**: o ROADMAP fala em "4 contextos do AtivoCard (Acompanhar/Mesa/Posições/home)"; medido pelo Context Gatherer que só existem 2 call sites reais (`watchlist`, `radar`) — Posições/home não renderizam `AtivoCard` hoje. Ambos os 2 contextos existentes foram verificados.

### CHIP-01 — um único `SinalChip`, dois pesos fixos, zero receita paralela — VERIFIED

Evidência:
- `function SinalChip({ peso, ... })` existe uma única vez (`App.jsx:1383`), resolve cor internamente (`REC_STYLE[decision]` para `primario`; `HISTORICO_PILL_STYLE[estado]` para `contexto`) — sem prop de cor livre por chamada (D-14 confirmado por leitura do corpo da função).
- `FundamentoChip`/`SCORE_COLOR`, `RegimeChip`/`REGIME_STYLE` e `TierDot` apagados de `App.jsx` (comentário datado em `App.jsx:1551-1552`; `grep -c "^function FundamentoChip\|^function RegimeChip\|^function TierDot"` → 0).
- `HistoricoPill` migrado para `<SinalChip peso="contexto" estado={estado} .../>` (zero `pillStyle` paralelo).
- `LinhaContexto` (regime+fundamento) e `FundamentoTabela` também usam `<SinalChip peso="contexto">` — confirmado por `test_sinal_chip_ui.mjs`: "LinhaContexto usa `<SinalChip peso=\"contexto\"` 2 vezes", "FundamentoTabela usa ... 1 vez", "HistoricoPill usa ... 1 vez" → todos PASS.
- Os 3 "falsos-positivos" documentados no 42-05-SUMMARY (HistoricoPill por-setup na cauda do Radar, 2 badges "condições detectadas" com `borderRadius 999px`) foram inspecionados: nenhum é receita de pill de confiança/tier — são, respectivamente, o mesmo `HistoricoPill`/`SinalChip` já migrado (não uma receita paralela) e badges de texto livre sem relação com tier/confiabilidade. Não são gap.

### CHIP-02 — `aria-label` descritivo em todo `SinalChip` — VERIFIED

Evidência:
- Peso `primario`: `role="group" aria-label={ariaManchete(...)}` no container (`App.jsx:1389-1390`); o `ConfluenceRing` interno recebe `ariaLabel={copyFor(modo).sinal.ariaAnel(ring.texto)}` (`App.jsx:1401`).
- Peso `contexto`: `<span role="img" aria-label={ariaLabel}>` (`App.jsx:1417`), padrão idêntico ao antigo `HistoricoPill`.
- `web/src/sinal.js` fornece as funções que compõem esses aria-labels a partir da MESMA fonte do texto visível (`ariaRegime`, `ariaFundamento`, `ariaManchete`, `rotuloAnel`) — nunca uma segunda string divergente.
- `test_sinal_helpers.mjs` (43 asserções) e `test_historico_ui.mjs` §7 confirmam paridade estudo/operador e presença do `aria-label`.

## Guardrail CVM (ataque #1 do escopo pedido) — VERIFICADO, sem violação

- `web/src/sinal.js:ladoDoMotor` lê exclusivamente `setup.lado`/`plano.lado` (campos do motor, `setups.py:707`) — nunca faz `String(setup.nome).includes(...)` ou qualquer inferência textual. Confirmado por leitura integral do arquivo (78 linhas).
- `kp.direcao`/`kp.conviccao`/`kp.qualidade` (chips da IA) NÃO aparecem no corpo de `AtivoCard` (`App.jsx:3521-3963`, grep confirma zero ocorrência de `kp\.` nesse range) nem no `vm` da Watchlist (`MercadoScreen`, `App.jsx:3963-4126`, zero `kp\b`/`const chip =`) nem no `radarVm` do Radar (`App.jsx:7033`, objeto literal sem chave `kp`).
- `DIR_STYLE`/`kpis.direcao` só existem em `KpiBlock` (`App.jsx:1072`, `1338-1356`) — a tela de detalhe técnico aberta pelo gráfico de velas, explicitamente fora do escopo da Fase 42 (CHIP-03, Fase 43). O card único (`AtivoCard`) não os usa.
- `server/` intocado: `git diff --stat cf7c36d -- server/` vazio — o motor determinístico (`setups.py`, `regime.py`, `signal_ledger.py`) não foi tocado.

## Canal de cor (ataque #2) — VERIFICADO, sem violação

- `T.positive`/`T.negative` continuam usados em: manchete (`REC_STYLE`, cor da decisão — intocado), preço/variação (`chColor`, `App.jsx` linha da cotação), P&L (`pnl >= 0 ? T.positive : T.negative`, `App.jsx:3~3712` resumo da posição), e o veredito na espinha de opções — todos dentro do escopo permitido por D-05.
- Nenhuma ocorrência de `T.positive`/`T.negative`/`T.accent` dentro do corpo de `SinalChip` nem `LinhaContexto` (confirmado pelos 2 ban-lists explícitos do `test_sinal_chip_ui.mjs`, ambos PASS).
- `HISTORICO_PILL_STYLE.inelegivel` usa `T.warn`/`T.warnTint10`; `elegivel` usa `T.textPrimary` neutro + glifo `✓` decorativo (`aria-hidden`), sem verde.

## Guardiões reconciliados (ataque #3) — VERIFICADO, sem perda líquida de cobertura

| Guardião | Nota datada de reversão | Executado | Resultado |
|---|---|---|---|
| `test_historico_ui.mjs` | Sim, 3 pontos (2026-09-26, Fase 42, CHIP-01/COR-01/D-03/D-04) | `node` | TUDO OK |
| `test_hero_reconciliado.mjs` | Sim (2026-09-26, Fase 42, HIER-01/CHIP-01/D-02) | `node` | todos passaram |
| `test_setor_toque.mjs` | Sim (2026-09-26, Fase 42, D-08) | `node` | todos passaram |
| `test_radar_leitura_rapida.mjs` | Sim, 2 pontos | `node` | todos passaram |
| `test_radar_regime_chip.mjs` | Sim (reescrito para `sinal.js`) | `node` | TUDO OK |
| `test_fundamento_ui.mjs` | Sim, 3 pontos | `node` | todos passaram |
| `test_fase22_componentes_compartilhados.mjs` | Sim, 2 pontos (D-08) | `node` | exit 0, todas asserções ok |
| `test_modo_operador.mjs` | Sim (fora da lista original, achado pela suíte) | `node` | todos passaram |
| `test_radar.mjs` | Sim (idem) | `node` | TODOS PASSARAM |
| `test_setup_operavel_adr017.mjs` | Sim (idem) | `node` | todos passaram |
| `test_sinal_helpers.mjs` (novo, 42-01) | — (guardião novo) | `node` | TUDO OK |
| `test_sinal_chip_ui.mjs` (novo, 42-03/04/05) | — (guardião novo) | `node` | TUDO OK |
| `test_cor_confiabilidade.mjs` (novo, 42-02) | — (guardião novo) | `node` | TUDO OK |

`git diff --stat cf7c36d` nos 11 arquivos de teste tocados: **508 inserções / 98 remoções** — net positivo de asserções, nenhum arquivo zerado ou esvaziado. Todas as reversões inspecionadas preservam a GARANTIA original em prosa (ex.: `test_radar.mjs` — "confluência rotulada na tela" migrou de âncora textual exata para regex case-insensitive, mas a garantia semântica permanece testada) — nenhuma suavização de garantia encontrada, só realocação de onde/como o contrato é verificado.

Nenhum guardião foi apagado (confirmado por comparação de nomes de arquivo entre `cf7c36d` e `HEAD` em `web/tests/`).

## Motor intocado (ataque #4) — VERIFIED

`git diff --stat cf7c36d -- server/` → **vazio**. Nenhum arquivo de `server/app/*.py` foi tocado por nenhum dos 5 planos.

## Paridade (ataque #5) — VERIFIED, não afetada

- `git diff --stat cf7c36d -- server/app/defaults.py web/src/catalog.js web/src/persistence.js` → vazio — nenhum dos três arquivos de paridade foi tocado.
- `node web/tests/test_didatica_parity.mjs`, `node web/tests/test_copy_theme.mjs`, `node web/tests/test_api_parity.mjs` → todos passaram (paridade estudo/operador do bloco `sinal` novo em `copy.js`, e paridade cliente HTTP, intactas).

## Build e testes executados nesta verificação

```
node web/tests/test_historico_ui.mjs                        → TUDO OK
node web/tests/test_hero_reconciliado.mjs                   → todos os testes passaram
node web/tests/test_setor_toque.mjs                          → todos os testes passaram
node web/tests/test_radar_leitura_rapida.mjs                 → todos os testes passaram
node web/tests/test_radar_regime_chip.mjs                    → TUDO OK
node web/tests/test_fundamento_ui.mjs                        → todos os testes passaram
node web/tests/test_fase22_componentes_compartilhados.mjs    → exit 0
node web/tests/test_modo_operador.mjs                        → todos os testes passaram
node web/tests/test_radar.mjs                                → TODOS OS TESTES DO RADAR (WIRING) PASSARAM
node web/tests/test_setup_operavel_adr017.mjs                → todos os testes passaram
node web/tests/test_sinal_helpers.mjs                        → TUDO OK
node web/tests/test_sinal_chip_ui.mjs                        → TUDO OK
node web/tests/test_cor_confiabilidade.mjs                   → TUDO OK
node web/tests/test_didatica_parity.mjs                       → todos os testes passaram
node web/tests/test_copy_theme.mjs                            → todos os testes passaram
node web/tests/test_api_parity.mjs                             → TODOS PASSARAM
cd web && npx vite build --logLevel error                     → exit 0 (build limpo; ruído "failed to copy trust settings of system certificate" é do sandbox de TLS local, não do código)
```

Suíte pytest do backend **não foi executada** nesta verificação, por instrução explícita da tarefa (sandbox quebra TLS; o orquestrador roda fora do sandbox). O motor intocado (`git diff` vazio em `server/`) elimina a necessidade prática de rodá-la para este veredito — nenhum código Python foi alterado pelos planos 42-01..05.

## Requirements Coverage

| Requisito | Status | Evidência |
|---|---|---|
| COR-01 | ✓ SATISFIED | Ver seção acima |
| HIER-01 | ✓ SATISFIED | Ver seção acima |
| HIER-02 | ✓ SATISFIED | Ver seção acima (nos 2 contextos existentes) |
| CHIP-01 | ✓ SATISFIED | Ver seção acima |
| CHIP-02 | ✓ SATISFIED | Ver seção acima |

`.planning/REQUIREMENTS.md` continua com as 5 linhas em `Pending`/`- [ ]` — **isso é esperado e correto**: fechar essas linhas (`- [x]`, `Pending → Done`) é tarefa explícita do 42-06-PLAN.md (Task de fechamento de docs), não das plans 42-01..05. Não é gap desta verificação.

## Anti-Patterns

Nenhum `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` novo introduzido nos arquivos tocados (`web/src/App.jsx`, `web/src/sinal.js`, `web/src/copy.js`) — grep no diff completo (`cf7c36d..HEAD`) não encontrou nenhum marcador de dívida nas linhas adicionadas.

Falha ambiental conhecida e documentada em todos os 5 SUMMARYs: `test_ios_assets.mjs` falha após `npx vite build` porque `web/dist`/`web/ios` (ambos gitignored) ficam com hashes de chunk dessincronizados sem `cap sync`. Não é regressão de código — nenhum arquivo iOS de produção foi tocado por esta fase. Não impacta o veredito.

## Dependências de 42-06 (não são gaps desta verificação, mas bloqueiam fechamento da fase)

1. **Checkpoint humano ao vivo** — Alex precisa confirmar em <3s o veredito do card de UGPA3 (ou equivalente) e responder DP-1..DP-4 por nome (alpha do `warnTint10` no tema claro: 4% vs 3,6%; alinhamento só em regime de tendência; ausência do "x/y critérios" no cabeçalho do Radar; Watchlist agora mostra regime+plano e o novo formato de chip de elegibilidade em todas as telas, inclusive lista de setups do Operador IA). Isto é verificação humana — não pode ser feito por grep, é o próprio propósito do 42-06.
2. **Publicação** (`scripts/bump.sh` + `publicar-web.sh`, carimbo próprio do `SERVER_BUILD_ID`) — nada foi publicado; o app em produção ainda roda o build anterior (`F10-20260925-02` citado no 42-06-PLAN). Enquanto isso não roda, os ganhos desta fase existem só no código, não na experiência do usuário real.
3. **Fechamento de documentos** (`REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`) — as 5 linhas de requisito continuam `Pending` até o 42-06 rodar; isso é esperado neste ponto, não uma inconsistência a corrigir agora.

## Human Verification Required

Nenhum item de verificação humana é necessário desta rodada de verificação — a verificação humana ao vivo (leitura <3s + DP-1..DP-4) é o próprio conteúdo do plano 42-06, deliberadamente não executado, e não faz parte do escopo desta chamada de verificação (que cobre só 42-01..05).

## Gaps Summary

Nenhum gap real encontrado nos planos 42-01 a 42-05. Todos os 5 must-haves do ROADMAP (Success Criteria 1-3 mapeados a COR-01/HIER-01/CHIP-01/CHIP-02; Success Criteria 4 mapeado a HIER-02) estão implementados, testados por guardião próprio, e o motor/paridade permanecem intocados. O Success Criteria 5 do ROADMAP ("suíte canônica verde... publicação... checkpoint humano") mistura verificação automatizável (suíte + build, ambos verdes) com verificação humana e publicação — ambas deliberadamente reservadas ao 42-06, não gaps desta fase parcial.

---

*Verificado: 2026-09-27T05:27:32Z*
*Verificador: Claude (gsd-verifier) — verificação independente goal-backward, planos 42-01..42-05*
