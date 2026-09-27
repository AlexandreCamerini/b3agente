---
phase: 42-cr-tico-cor-chip-nico-e-ordem-de-leitura
plan: 03
subsystem: ui
tags: [react, sinal-chip, aria, component-contract, design-system]

# Dependency graph
requires: ["42-01", "42-02"]
provides:
  - "function SinalChip({ peso, ... }) em web/src/App.jsx — dois pesos fixos (primario/contexto), sem prop de cor livre (D-14)"
  - "HistoricoPill migrado para <SinalChip peso=\"contexto\" estado={estado}>, zero receita de pill paralela (CHIP-01)"
  - "ConfluenceRing com prop opcional ariaLabel (default preservado)"
  - "function LinhaContexto({ regime, fundamento, alinhamento, ... }) — regime + marca de alinhamento neutra + fundamento + disclaimer"
  - "function PlanoOperacionalBloco({ operador, plano, motivo, setup, close, config }) — plano por modo, transportado do Radar"
  - "web/tests/test_sinal_chip_ui.mjs — guardião do contrato (Parte A: SinalChip; Parte B: LinhaContexto/PlanoOperacionalBloco)"
affects: ["42-04", "42-05", "42-06"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "SinalChip resolve cor internamente via REC_STYLE[decision]/HISTORICO_PILL_STYLE[estado] — chamador nunca passa cor livre (guardrail 'manchete só do motor')"
    - "Componentes definidos sem call site real ainda (LinhaContexto/PlanoOperacionalBloco) — guardião de contrato roda sobre o corpo da função, não sobre wiring, permitindo separar DEFINIÇÃO de FIAÇÃO entre planos"

key-files:
  created:
    - web/tests/test_sinal_chip_ui.mjs
  modified:
    - web/src/App.jsx
    - web/tests/test_historico_ui.mjs

key-decisions:
  - "Ordem de renderização em SinalChip peso=contexto: label span primeiro (forma literal exigida por test_setor_toque.mjs), depois espaço condicional, depois <b>{value}</b> — preserva a convenção SUBLINHADO no rótulo para quando o 42-04/42-05 substituir chip()/FundamentoChip/RegimeChip por este componente"
  - "PlanoOperacionalBloco usa 4 flags booleanas explícitas (temCaixa/temMotivoOperador/temMotivoEstudo/temReguaEstudo) em vez de replicar o encadeamento condicional JSX original — mais legível para o guardião isolar o ramo Operador (ausência de <PlanRuler>, D-12) sem depender de posição de string frágil"

requirements-completed: [CHIP-01, CHIP-02, HIER-01, HIER-02]

# Metrics
duration: ~55min
completed: 2026-09-27
---

# Phase 42 Plan 03: Componente único de sinal (SinalChip) e blocos compostos Summary

**`SinalChip` (dois pesos, sem prop de cor) substitui a receita de pill do `HistoricoPill`; `LinhaContexto` e `PlanoOperacionalBloco` definidos e travados por guardião, prontos para a fiação do 42-04 — nenhuma tela do app mudou de comportamento ainda.**

## Performance

- **Duration:** ~55 min
- **Started:** 2026-09-27 (após leitura de contexto/UI-SPEC/PATTERNS/summaries anteriores)
- **Completed:** 2026-09-27
- **Tasks:** 2/2 completos
- **Files modified:** 3 (2 modificados, 1 criado)

## Accomplishments

- `SinalChip` criado em `web/src/App.jsx` (imediatamente antes de `SCORE_COLOR`), com os dois pesos do contrato:
  - `peso="primario"`: resolve `REC_STYLE[decision]` internamente (nunca recebe `[cor,fundo]` por prop), embute `ConfluenceRing` 36px via prop `ring`, rótulo do anel aria-hidden (texto vem pronto de `rotuloAnel`, 42-01), `role="group"` no container lendo kicker+decisão numa fonte só.
  - `peso="contexto"`: `estado` é a única exceção de cor (via `HISTORICO_PILL_STYLE`); `null`/`""` em `value` nunca renderiza (D-16); glifo `✓` decorativo `aria-hidden`; borda tracejada só no estado `aposentado`.
- `ConfluenceRing` ganhou prop opcional `ariaLabel` (default `Confluência {c}%` preservado — nenhum call site existente muda de comportamento).
- `HistoricoPill` migrado: removidas as linhas de `pillStyle`/borda condicional; o `<span role="img">` virou `<SinalChip peso="contexto" estado={estado} value={rotulo} ariaLabel={ariaLabel} />` — zero receita de pill paralela (CHIP-01).
- `LinhaContexto` e `PlanoOperacionalBloco` definidos (sem call site — a fiação é do 42-04), seguindo literalmente a ordem/gates do UI-SPEC e transportando o bloco de plano do Radar byte-a-byte nas partes de cor/preço.
- `web/tests/test_sinal_chip_ui.mjs` criado (2 partes, 29 asserções) — ban list de cor, contrato de aria, ordem de leitura, ausência de `<PlanRuler` no ramo Operador.
- `web/tests/test_historico_ui.mjs` reancorado (§3 glifo, §5 borda tracejada, §7 aria-label) para o corpo de `SinalChip` — nota de reversão deliberada no próprio teste.

## Task Commits

Each task was committed atomically:

1. **Task 1: SinalChip (primario+contexto), HistoricoPill via SinalChip, ConfluenceRing.ariaLabel** - `5a50774` (feat)
2. **Task 2: LinhaContexto e PlanoOperacionalBloco (definição) + guardião dos blocos** - `ad9fdfc` (feat)

**Plan metadata:** (este commit) — docs: complete plan

## Files Created/Modified

- `web/src/App.jsx` — import de `sinal.js`; `ConfluenceRing` com prop `ariaLabel`; `function SinalChip`, `function LinhaContexto`, `function PlanoOperacionalBloco` novos; `HistoricoPill` migrado
- `web/tests/test_historico_ui.mjs` — helper `functionBody`, recorte `sinalChip`, §3/§5/§7 reancorados, nota de reversão deliberada
- `web/tests/test_sinal_chip_ui.mjs` — guardião novo (criado), Parte A (SinalChip) + Parte B (LinhaContexto/PlanoOperacionalBloco)

## Validação

```
node web/tests/test_sinal_chip_ui.mjs              → TUDO OK (29 asserções)
node web/tests/test_historico_ui.mjs               → TUDO OK (41 asserções)
node web/tests/test_historico_setup_card_ui.mjs    → todos os testes passaram
node web/tests/test_setor_toque.mjs                → todos os testes passaram
cd web && npx vite build --logLevel error          → exit 0, build limpo
web/tests/*.mjs (suíte completa, 168 arquivos)      → 1 falha conhecida: test_ios_assets.mjs
```

Acceptance criteria (greps literais do plano) confirmados:
- `grep -c "^function SinalChip(" web/src/App.jsx` → 1
- ban list de `SinalChip` (sem comentário) → 0 ocorrências de `T.positive|T.negative|T.accent`
- `grep -c '<SinalChip peso="contexto" estado={estado}' web/src/App.jsx` → 1
- `grep -c "^function LinhaContexto(\|^function PlanoOperacionalBloco("` → 2
- ban list de `LinhaContexto` (sem comentário) → 0 ocorrências de `T.positive|T.negative|T.warn|T.accent`

`test_ios_assets.mjs` falha por drift de build local (mesmo achado documentado em 42-01/42-02-SUMMARY.md): `npx vite build` regenera `web/dist` com hashes novos que não batem com `web/ios/App/App/public` (bundle nativo local não resincronizado via `cap sync`). Ambos gitignored, artefato de ambiente, não regressão de código — nenhum arquivo iOS de produção foi tocado por este plano.

Suíte pytest do backend não foi executada — este plano não toca nenhum arquivo `server/app/*.py` (confirmado: `files_modified` do frontmatter e o diff real cobrem só `web/src/App.jsx` e `web/tests/*.mjs`); motor intocado.

## Deviations from Plan

None. O `<action>` de cada task foi seguido literalmente (nomes de função, assinatura de props, forma exata dos JSX exigidos pelos guardiões existentes — `test_setor_toque.mjs`, `test_historico_ui.mjs`). Os dois desvios possíveis identificados durante a leitura (variáveis `cor`/`fundo` órfãs em `HistoricoPill` após a migração; nome das flags booleanas de `PlanoOperacionalBloco`) são detalhes de implementação dentro do escopo do `<action>`, documentados em "Decisões autônomas" abaixo — não mudam contrato, arquivo ou comportamento visível.

## Decisões autônomas

Execução autorizada pelo Alex sem pausa para confirmação (autonomia concedida no prompt de execução). Decisões tomadas sem consulta:

1. **Remoção das variáveis `[cor, fundo] = HISTORICO_PILL_STYLE[estado] || ...` e `pillStyle` dentro de `HistoricoPill`** — o `<action>` da Task 1 pedia "remover pillStyle e as linhas de borda", mas não mencionava explicitamente a destructuring de `cor`/`fundo` que ficava sem uso após a migração para `SinalChip`. Removi por limpeza (variável morta, sem efeito de comportamento) — `HISTORICO_PILL_STYLE` continua exportado/usado, só não mais dentro de `HistoricoPill` diretamente. Risco: nenhum, confirmado por `npx vite build` limpo e pelos 41 guardiões de `test_historico_ui.mjs` verdes.
2. **Nomes das 4 flags booleanas em `PlanoOperacionalBloco`** (`temCaixa`/`temMotivoOperador`/`temMotivoEstudo`/`temReguaEstudo`) — o `<action>` descrevia a lógica em prosa (if/else encadeado), não deu nomes de variável. Escolhi flags explícitas em vez de replicar o if/else do Radar porque (a) o guardião da Task 2 precisa isolar "o ramo Operador" por string-slice para verificar ausência de `<PlanRuler` — nomear a fronteira (`temCaixa &&` ... `!operador && motivo &&`) deixa esse recorte robusto a reordenação futura de JSX dentro do mesmo ramo; (b) o `<done>` do plano não especifica a implementação interna, só o contrato observável (guardião roda verde, `npx vite build` limpo). Documentado também em `key-decisions` do frontmatter.
3. **Não toquei `web/dist`/`web/ios`/`cap sync`** ao confirmar a falha conhecida de `test_ios_assets.mjs` — mesma decisão dos executores de 42-01/42-02 (artefato gitignored, fora do escopo de um plano que só define componentes de apresentação).
4. **Rodei a suíte completa `web/tests/*.mjs` (168 arquivos)** além dos arquivos exigidos pela `<verify>` explícita de cada task, para confirmar ausência de regressão antes de fechar o plano — mesma prática dos dois executores anteriores desta fase. Achei só a falha já conhecida de `test_ios_assets.mjs`.

## User Setup Required

None — nenhuma configuração externa necessária.

## Next Phase Readiness

- `SinalChip`, `LinhaContexto` e `PlanoOperacionalBloco` estão prontos, com contrato travado por guardião, para o 42-04 (fiação no `AtivoCard`/Radar: substituir `chip()`/`FundamentoChip`/`RegimeChip`/pill de confiança pelo `SinalChip`, mover o rodapé do anel para dentro da manchete via prop `ring`, religar `LinhaContexto`/`PlanoOperacionalBloco` na ordem de leitura HIER-02).
- Nenhuma tela mudou de comportamento visível nesta plan (por desenho — DEFINIÇÃO separada de FIAÇÃO) exceto o pill de elegibilidade, que já passou pelo componente novo sem mudança de contrato de cor/aria (confirmado pelos 41 guardiões de `test_historico_ui.mjs`, incluindo os 4 recolhidos deste plano).
- Nenhum bloqueio. Nota de ambiente (repetida de 42-01/42-02): se o próximo executor rodar `npx vite build`, considerar `cd web && npx cap sync ios` antes de rodar a suíte completa para não repetir a falha local de `test_ios_assets.mjs`.

---
*Phase: 42-cr-tico-cor-chip-nico-e-ordem-de-leitura*
*Completed: 2026-09-27*

## Self-Check: PASSED

- `web/src/App.jsx` — FOUND (modificado, existe)
- `web/tests/test_historico_ui.mjs` — FOUND (modificado, existe)
- `web/tests/test_sinal_chip_ui.mjs` — FOUND (criado, existe)
- Commit `5a50774` — FOUND em `git log --oneline --all`
- Commit `ad9fdfc` — FOUND em `git log --oneline --all`
