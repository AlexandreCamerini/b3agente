---
phase: 43-refinamento-copy-por-modo-kpiblock-e-ritmo
verified: 2026-09-27T00:00:00Z
status: passed
score: 5/5 truths de código verificados (43-01..04); 1 item de geometria (D-18) precisa de confirmação visual — checkpoint humano (SC#4) e fechamento de docs (D-06) ficam para 43-05, fora do escopo desta verificação
overrides_applied: 0
resolved: "2026-09-27 — item humano D-18 resolvido: medido no app local o chip irmão da mesma receita (SinalChip contexto 'REGIME LATERAL') com 24px de altura e padding 4/8; com o SetorAlvo 12/8 a caixa de toque fica em 48px de altura, e a largura passa de 100px porque o chip de fundamento da LinhaContexto mantém o rótulo 'FUNDAMENTO' + valor (a premissa de ~43px supunha só o glifo A/B/C). Checkpoint humano SC#4 aprovado pelo Alex (43-05-SUMMARY.md). Detalhe em 43-05-CHECKPOINT.md."
human_verification:
  - test: "Abrir devtools no `AtivoCard` (Watchlist ou Radar), localizar o `SetorAlvo setorId=\"fundamento\"` na `LinhaContexto` e medir a bounding box computada do elemento (a caixa de TOQUE, não a caixa visual do chip)."
    expected: "≥44×44px nas duas dimensões, para o valor típico (score de 1 caractere, A/B/C)."
    why_human: "O código usa as constantes corretas (`padding: ${SP[3]}px ${SP[2]}px` / `margin: -${SP[3]}px -${SP[2]}px`, SP[3]=12, SP[2]=8), mas nenhum guardião mede a caixa renderizada. Cálculo estático a partir do CSS (fonte 11px/700, line-height 1.3, padding do chip 4px/8px, borda 1px, + padding de toque 12px/8px) estima altura ≈48px (ok) e largura ≈43px (limítrofe, pode ficar abaixo de 44px dependendo do glifo real da fonte Nunito em negrito) — não é possível confirmar sem renderizar. O 43-02-SUMMARY.md registra que "o executor confirma no devtools" mas essa confirmação não está registrada com o número medido, e a verificação não pode aceitar a afirmação da SUMMARY como prova (mandato adversarial)."
---

# Phase 43 (parcial 43-01..04): Refinamento — copy por modo, KpiBlock e ritmo — Verificação

**Escopo desta verificação:** planos 43-01 a 43-04 (código). **43-05** (checkpoint humano ao vivo, publicação via `bump.sh`/`publicar-web.sh`, correção D-06 no ROADMAP/REQUIREMENTS) **não foi executado** e está fora do escopo — listado como "depende de 43-05", não como gap.

**Goal da fase:** reconciliação sinal técnico × histórico legível por modo; detalhe técnico da IA usa `SinalChip`; espaçamento do card na escala 4/8pt — sem abrir escopo de decisão/elegibilidade.

**Status:** human_needed. Todos os truths de HIER-03/CHIP-03/RITMO-01 verificados no código, com suíte canônica front (171 arquivos `.mjs`) e pytest de `test_skill_ref.py` verdes, `npx vite build` limpo, motor com diff vazio. Um item geométrico (D-18, fold-in da Fase 42, executado no plano 43-02) não pode ser confirmado por análise estática — precisa de medição visual no devtools antes de considerar a fase (código) 100% fechada.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidência |
|---|-------|--------|-----------|
| 1 | Guardrail CVM: `kpis.recomendacao` nunca vira chip; os 3 chips da IA só em `AnalysisView`, neutros, omitidos sem `an.kpis`; nada da IA no `AtivoCard` | ✓ VERIFIED | `web/src/App.jsx:1622-1646` (bloco `an.kpis && (...)`, sem `estado=`/cor de mercado, sem `kpis.recomendacao`); guardião `test_leitura_ia_chips.mjs` 20/20 ok; `test_sinal_chip_ui.mjs` confirma "AtivoCard não contém kp." e 3 call sites de `SinalChip contexto` em `AnalysisView`; confirmado independentemente que `server/app/scan_deep.py` não tem nenhuma ocorrência de `kpis` (grep próprio, zero linhas) — a nota do 43-03-SUMMARY sobre "Radar Aprofundar com IA sem kpis" está correta |
| 2 | Microtexto só de `reconciliacaoTxt`/`reconciliacaoPorQueImporta`; paridade `skill_ref.py`↔`copy.js` byte a byte; `null` nunca vira 0; só no call site do `AtivoCard`; Estudo com cláusula tocável, Operador sem | ✓ VERIFIED | `server/app/skill_ref.py:452-491` ↔ `web/src/copy.js:603-609`/`1396-1402`/`1649-1663` (comparação manual byte a byte confere, nos dois modos); `web/src/App.jsx:6790-6812` (gate `!operador` antes do `SetorAlvo`); único call site com `microtexto` é `App.jsx:3772` (`test_reconciliacao_elegibilidade.mjs` 41/41 ok, incl. asserção "exatamente 1 call site... contém microtexto") |
| 3 | RITMO-01: zero px solto de margin/padding/gap no escopo D-14; exceções ópticas só as nomeadas | ✓ VERIFIED (código) / ⚠️ ver item 3b | `const SP`/`SP_OPTICO_CHIP_PRIMARIO`/`SP_OPTICO_ANEL` em `App.jsx`; guardião `test_ritmo_sp.mjs` 26/26 ok (autoteste do detector + zero violação em `SinalChip`/`LinhaContexto`/`PlanoOperacionalBloco`/`HistoricoPill`/recorte do `AtivoCard`) |
| 3b | D-18 (fold-in Fase 42): alvo de toque do chip de fundamento tocável ≥44×44px | ? UNCERTAIN | Código usa as constantes certas (ver Human Verification abaixo), mas nenhum guardião mede a geometria renderizada; cálculo estático é limítrofe na largura (~43px). Precisa de medição no devtools. |
| 4 | Guardiões alterados com nota datada, nenhum apagado, sem perda líquida de cobertura | ✓ VERIFIED | `git diff 4b0b7c5 -- web/tests/ server/tests/`: só adições/edições localizadas (+614/−12 linhas), 3 arquivos novos (`test_leitura_ia_chips.mjs`, `test_reconciliacao_elegibilidade.mjs`, `test_ritmo_sp.mjs`), 2 asserções reconciliadas em `test_decisao_modo.mjs` com nota "REVERSÃO DELIBERADA (2026-09-27, Fase 43...)" — nenhum arquivo removido |
| 5 | Motor intocado | ✓ VERIFIED | `git diff --stat 4b0b7c5 -- server/app/setups.py server/app/kpi.py server/app/signal_ledger.py server/app/regime.py` — vazio |

**Score:** 5/5 truths de código; 1 item (3b) requer verificação humana antes de fechar RITMO-01/D-18 com confiança total.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `server/app/skill_ref.py` | `RECONCILIACAO_ELEGIBILIDADE`, `RECONCILIACAO_POR_QUE_IMPORTA`, `reconciliacao_elegibilidade_txt` | ✓ VERIFIED | linhas 452-491, verbatim conforme UI-SPEC |
| `web/src/copy.js` | `reconciliacaoElegibilidade` (2 modos), `reconciliacaoTxt`, `reconciliacaoPorQueImporta`, `sinal.leituraIa` | ✓ VERIFIED | linhas 603-609, 1396-1402, 1649-1663, 627-633/1420-1426 |
| `web/src/App.jsx` — `AnalysisView` | 3 `SinalChip contexto` neutros, `an.kpis` gate | ✓ VERIFIED | linhas 1579-1669 |
| `web/src/App.jsx` — `HistoricoPill` | forma `microtexto` mutuamente exclusiva | ✓ VERIFIED | linhas 6758-6828 |
| `web/src/App.jsx` — `KpiBlock`/`KpiCell`/`DIR_STYLE`/`SCALE_STYLE` | apagados | ✓ VERIFIED | grep zero ocorrências fora de comentário histórico (`qa/49`) |
| `web/tests/test_ritmo_sp.mjs` | guardião novo RITMO-01 | ✓ VERIFIED | criado, autotestado, 26/26 ok |
| `web/tests/test_leitura_ia_chips.mjs` | guardião novo CHIP-03/D-17 | ✓ VERIFIED | criado, 20/20 ok |
| `web/tests/test_reconciliacao_elegibilidade.mjs` | guardião novo HIER-03 (Parte A+B) | ✓ VERIFIED | criado, 41/41 ok |
| Área de toque do fundamento (D-18) | ≥44×44px | ⚠️ HOLLOW (não medido) | constantes corretas no código, geometria renderizada não confirmada — ver Human Verification |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `AtivoCard` | `AnalysisView` | `<AnalysisView an={an} operador={operador} />` (único call site, `App.jsx:3943`) | ✓ WIRED | mesmo componente único cobre Watchlist e Radar (`AtivoCard` é reusado nos dois, `App.jsx:4115`/`7066`) |
| `AtivoCard` (linha de elegibilidade) | `HistoricoPill microtexto` | `App.jsx:3772` | ✓ WIRED | único call site com `microtexto`; cauda do Radar (`App.jsx:7126`) mantém números crus sem `microtexto`, conforme D-09 |
| `HistoricoPill` | `reconciliacaoTxt`/`reconciliacaoPorQueImporta` | import de `./copy.js`, chamada em `App.jsx:6791` | ✓ WIRED | confirmado por `test_reconciliacao_elegibilidade.mjs` (Parte B) |
| `AnalysisView` | `copyFor(...).sinal.leituraIa` | `App.jsx:1581` | ✓ WIRED | rótulo/aria vêm de `copy.js`, nenhuma string literal nova em `App.jsx` |

### Requirements Coverage

Texto completo de HIER-03/CHIP-03/RITMO-01 lido em `.planning/REQUIREMENTS.md:45-74` (não só a linha truncada do grep inicial) — nenhuma cláusula de aceite adicional além do que CONTEXT/UI-SPEC já cobriam.

| Requirement | Source Plan | Status | Evidência |
|-------------|-------------|--------|-----------|
| HIER-03 | 43-01, 43-04 | ✓ SATISFIED (código) | vocabulário + fiação confirmados; REQUIREMENTS.md ainda marca `[ ]`/"Pending" — atualização de status é tarefa do fechamento (43-05), não um gap de implementação |
| CHIP-03 | 43-01, 43-03 | ✓ SATISFIED (código) | KpiBlock apagado, 3 chips neutros em AnalysisView; texto do requirement (`REQUIREMENTS.md:64-67`) repete a mesma premissa factualmente incorreta do SC#2 do ROADMAP ("aberta via gráfico de velas... grade de caixas cinzas") — já coberto pelo D-06 do CONTEXT, correção adiada para 43-05, não é gap novo |
| RITMO-01 | 43-02 | ✓ SATISFIED (código) / ⚠️ ver D-18 acima | escala SP aplicada, guardião ban-list ativo; mesma nota sobre status pendente |

### Anti-Patterns Found

Nenhum `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` introduzido nos arquivos tocados pela fase (`skill_ref.py`, `copy.js`, `App.jsx`, `sinal.js`) — confirmado por diff desde `4b0b7c5`.

**Ruído fora de escopo (não é gap desta fase):** commit `e90270cd` ("fix(deploy): startCommand sem parênteses") no mesmo branch alterou `server/railway.json`/`.railway/railway.ts`/`server/tests/test_backup_pre_deploy.py` — não relacionado a nenhum dos 4 planos executados (deploy/infra, não copy/ritmo/chip). Mencionado só para registro; não bloqueia esta fase.

### Achados que dependem do 43-05 (não são gaps — fora do escopo desta verificação)

1. **SC#2 do ROADMAP / texto do requirement CHIP-03** mantêm a premissa factualmente incorreta identificada pelo D-06 do CONTEXT ("`KpiBlock`/`KpiCell` (detalhe técnico aberto via gráfico de velas)... grade de caixas cinzas") — a correção do texto no ROADMAP/REQUIREMENTS é tarefa explícita do 43-05, não desta fase de código.
2. **REQUIREMENTS.md** ainda lista HIER-03/CHIP-03/RITMO-01 como pendentes (`[ ]`) — atualização de status de requirement é parte do fechamento de fase (padrão do repo), não um gap de implementação.
3. **Decisão autônoma pendente de confirmação do Alex** (registrada no `43-02-SUMMARY.md`): a caixa "Sem leitura do motor" migrou para `SP`/`SP_OPTICO_CHIP_PRIMARIO` por Claude's Discretion (ponto fora da tabela D-15 original) — sem regressão visual detectável no código (2px→4px, 11px→12px), mas aguarda confirmação visual ao vivo no checkpoint do 43-05.
4. **SC#4** (checkpoint humano ao vivo) e a publicação (`bump.sh`+`publicar-web.sh`) — não executados, como esperado (43-05 é plano separado, ainda `[ ]` no ROADMAP).

### Human Verification Required

### 1. Área de toque do chip de fundamento (D-18, fold-in Fase 42, executado no 43-02)

**Teste:** Abrir devtools no `AtivoCard` (Watchlist ou Radar) com um ativo que tenha fundamento com score, localizar o `SetorAlvo setorId="fundamento"` dentro de `LinhaContexto` e medir a bounding box computada (a caixa de TOQUE — `padding`/`margin` negativa aplicados, não a caixa visual do chip por dentro).
**Esperado:** ≥44×44px nas duas dimensões.
**Por que humano:** O código aplica as constantes corretas (`SetorAlvo` com `padding: ${SP[3]}px ${SP[2]}px` = `12px 8px` e `margin: -${SP[3]}px -${SP[2]}px`, ao redor de um `SinalChip peso="contexto"` com `padding: ${SP[1]}px ${SP[2]}px` = `4px 8px`, fonte 11px/700/line-height 1.3, borda 1px). Cálculo estático a partir desses valores estima altura ≈48px (chip ~24px + 2×12px de toque — ok) e largura ≈43px (chip ~27px + 2×8px de toque — abaixo de 44px, dependendo da largura real do glifo A/B/C em Nunito Bold 11px, que não pode ser medida sem renderizar). O `43-02-SUMMARY.md` afirma que "o executor confirma no devtools", mas essa confirmação não veio com o número medido nem foi verificada de forma independente aqui — o mandato adversarial exige não aceitar a alegação da SUMMARY como prova. Se a medição real ficar abaixo de 44px, o ajuste é simétrico nos dois números (padding/margin), conforme o próprio 43-UI-SPEC.md já antecipa.

### Validação executada nesta verificação

- `node web/tests/test_reconciliacao_elegibilidade.mjs` — 41/41 ok
- `node web/tests/test_leitura_ia_chips.mjs` — 20/20 ok
- `node web/tests/test_ritmo_sp.mjs` — 26/26 ok
- `node web/tests/test_decisao_modo.mjs` — 10/10 ok
- `node web/tests/test_sinal_chip_ui.mjs` — 48/48 ok
- `node web/tests/test_hero_reconciliado.mjs` — 12/12 ok
- `node web/tests/test_vocabulario_espelho.mjs` — todos ok
- Loop completo `for t in web/tests/*.mjs` (171 arquivos) — `TOTAL_FALHAS=0`
- `cd server && .venv/bin/python -m pytest tests/test_skill_ref.py -q` — 29 passed
- `npx vite build` (web/) — build limpo (só warning pré-existente de chunk >500kB)
- `git diff --stat 4b0b7c5 -- server/app/setups.py server/app/kpi.py server/app/signal_ledger.py server/app/regime.py` — vazio (motor intocado)
- `git diff --stat 4b0b7c5 -- web/tests/ server/tests/` — só adições/edições localizadas, nenhum arquivo apagado
- `grep -n "kpis" server/app/scan_deep.py` — zero ocorrências (confirma, de forma independente, a nota do 43-03-SUMMARY)
- Leitura completa de `REQUIREMENTS.md:45-74` (HIER-03/CHIP-03/RITMO-01) — sem cláusula nova além de CONTEXT/UI-SPEC

## Gaps Summary

Nenhum gap de fiação/conteúdo encontrado em HIER-03/CHIP-03/RITMO-01 — vocabulário, wiring e ban-list de espaçamento passam em todos os guardiões e na leitura direta do código. O único ponto que impede um veredito `passed` sem ressalva é geométrico (D-18, item 3b): o código usa as constantes certas, mas a caixa de toque resultante não foi medida de forma confiável (cálculo estático fica limítrofe na largura, ~43px contra o limiar de 44px) — precisa de uma medição no devtools antes do checkpoint 43-05. Os demais quatro pontos listados em "Achados que dependem do 43-05" são consequências esperadas de a fase estar parcialmente fechada (falta o plano de checkpoint/publicação/fechamento de docs) e não indicam trabalho de produto pendente.

---
*Verificado: 2026-09-27*
*Verifier: Claude (gsd-verifier)*
