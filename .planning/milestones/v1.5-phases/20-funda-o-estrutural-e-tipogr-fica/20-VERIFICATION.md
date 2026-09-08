---
phase: 20-funda-o-estrutural-e-tipogr-fica
verified: 2026-09-05T00:00:00Z
status: human_needed
score: 7/7 must-haves verified at code/artifact level (1 requires human behavioral confirmation)
overrides_applied: 0
human_verification:
  - test: "Ligar 'reduzir movimento' no sistema operacional (ou emular prefers-reduced-motion:reduce via DevTools com um método que de fato alterna o media feature — resize_window/CDP básico não fizeram isso nas sessões anteriores), recarregar http://localhost:8787 (bundle de produção, BUILD_ID F10-20260905-02) ou o app publicado, e observar: (1) troca de tema/modo em Preferências é instantânea, sem fade; (2) o marquee do ticker (.tt-track) e o spinner (.spin) ficam PARADOS — comparar dois screenshots com ~1s de intervalo e confirmar mesma posição, não um flicker acelerado; (3) desligar a preferência e confirmar que o ticker volta a andar."
    expected: "Nenhuma transição/animação roda com a preferência ligada (troca de tema instantânea, ticker e spinner parados, sem strobe); ao desligar, o comportamento padrão volta."
    why_human: "A regra CSS (@media prefers-reduced-motion: reduce, seletores .b3/.b3-mode-switch, ordem de fonte correta) foi confirmada byte-idêntica no código-fonte E no bundle de produção servido (verificado por grep e pela leitura do <style> renderizado no DOM pelo orquestrador). Mas o EFEITO comportamental — o navegador de fato aplicando animation-duration:0.01ms/animation-iteration-count:1 e o resultado visual (ticker parado, sem strobe) — nunca foi observado ao vivo com a preferência realmente ativa. As três sessões de execução (20-01/02/03) e as duas reverificações do orquestrador (20-03, 20-04) documentaram, de forma consistente e não escondida, que nenhuma ferramenta disponível no ambiente expõe emulação de prefers-reduced-motion via CDP (Emulation.setEmulatedMedia) — resize_window só emula viewport/color-scheme. Presença de CSS correto não é evidência de comportamento correto (a mesma distinção que MOTION-01/02 na Fase 23 vão herdar deste gate) — por isso esta é uma checagem que só um humano com controle real do SO (macOS: Ajustes > Acessibilidade > Reduzir Movimento, ou Safari/Chrome com emulação real) pode fechar."
---

# Phase 20: Fundação estrutural e tipográfica Verification Report

**Phase Goal:** O esqueleto do app para de vazar horizontalmente, respeita um teto de largura em tela grande, exibe número financeiro numa escala consistente e alinhada, e obedece à preferência de movimento reduzido do sistema — a base que as três fases seguintes consomem.
**Verified:** 2026-09-05
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth (mapeada a requisito) | Status | Evidence |
|---|---|---|---|
| 1 | FIX-01 — `.b3-shell`/`<main>` não vazam horizontalmente em 375px | ✓ VERIFIED | `App.jsx:305` `.b3-shell{...overflow-x:hidden;}`; `<main>` com `overflowX:"hidden"` inline; guardião estático (`test_fase20_fundacao_visual.mjs`) 2 asserções verdes; medição ao vivo do orquestrador (20-01-SUMMARY, "Orchestrator Live Re-Verification"): `.b3-shell` scrollWidth=375=clientWidth, `main` 365=365, em 375×812; regressão em 820px (Acompanhar/Watchlist/Portfólio) sem quebra nova; remedido em produção (:8787) no 20-04-SUMMARY. |
| 2 | FIX-02 — badge de status de mercado trunca com reticência em vez de empurrar | ✓ VERIFIED | `App.jsx:834` span raiz do `MarketStatusBadge` com `maxWidth:"100%"` (causa raiz real, medida ao vivo — os ancestrais já tinham `minWidth:0`); `App.jsx:864/880/1924` com `marginTop:"4px", minWidth:0` (3 call sites); guardião 3 asserções verdes; live re-verification (20-01): span `scrollWidth=475` vs `clientWidth=136`, `textOverflow:ellipsis` computado, reticência visível, patrimônio intacto; remedido em produção (20-04): spans de 149px/185px contidos, truncamento visível no bundle publicado. |
| 3 | SYS-04 — conteúdo ≥768px contido em 720px, alinhado ao BottomNav, teto numa única constante | ✓ VERIFIED | `App.jsx:248` `const CONTENT_MAX_WIDTH = "720px"` (1 declaração); `grep -c 'maxWidth: CONTENT_MAX_WIDTH'` = 2 (BottomNav `App.jsx:928` + wrapper de conteúdo `App.jsx:9020`); `grep -c '"1060px"'` = 0; `grep -c 'maxWidth: "720px"'` = 0; guardião 4 asserções verdes; live re-verification 1280×900: wrapper=720px, BottomNav=720px, alinhados; remedido em produção. |
| 4 | TYPO-01 — todo número que já usa `MONO` ganha `tabular-nums` (dígitos de largura fixa) | ✓ VERIFIED | `App.jsx:322` `.b3 [style*="ui-monospace"]{ font-variant-numeric: tabular-nums; }`; `grep -c 'fontFamily: MONO'` continua 151 (zero call site editado); guardião 2 asserções verdes; live re-verification (20-02): amostra de 28+27 elementos em Acompanhar/Watchlist, 100% com `tabular-nums` computado; remedido em produção (20-04): 28 elementos em Acompanhar, 100%. |
| 5 | TYPO-02 — escala nomeada de 3 níveis declarada uma vez, com consumidor real | ✓ VERIFIED (com ressalva de escopo do próprio ROADMAP) | `App.jsx:256-258` `numHero`(34/700)/`numBody`(18/700)/`numMicro`(13/600); `App.jsx:886` `{...numBody, lineHeight:1.05, color:T.textPrimary}` no patrimônio do Topbar (consumidor real, diff visual zero confirmado por screenshot no 20-02); guardião 4 asserções verdes. **Ressalva textual do próprio ROADMAP.md (linha 328-332, sob a Fase 20)**: a metade "todo valor financeiro usa um dos três tamanhos" é deferimento explícito para as Fases 21/22 (migração tela a tela) — não é gap desta fase, é escopo pré-recortado no contrato do roadmap. |
| 6 | TYPO-03 — os 15 H1 de tela usam Fredoka (`DISPLAY`), sem mudar tamanho/peso/margem | ✓ VERIFIED | `grep -c '<h1'` = 15 = `grep '<h1' \| grep -c 'fontFamily: DISPLAY'`; os dois branches de `EficienciaIAScreen` confirmados; guardião trava por igualdade de contagem (pega H1 futuro sem a fonte); live re-verification (20-03): `document.fonts.check("600 22px Fredoka")` = true, 5 telas com `fontFamily` iniciando por `Fredoka`; remedido em produção (20-04). |
| 7 | MOTION-03 — sob "reduzir movimento", nenhuma transição roda (raiz + troca de modo) e ticker/spinner ficam PARADOS (não strobe) | ✓ VERIFIED no código/CSS — **UNCERTAIN no comportamento observado** | Regra ampla `App.jsx:367` cobre `.b3, .b3 *, .b3 *::before, .b3 *::after, .b3-mode-switch, .b3-mode-switch *` com `transition-duration/animation-duration:0.01ms !important` + `animation-iteration-count:1 !important`; bloco estreito pré-existente (`App.jsx:368`, `animation:none` para `.tt-track`/`.spin`) preservado intacto, com especificidade maior — evita o strobe que `0.01ms` produziria em animação `infinite`; ordem de fonte correta (306 < 337 < 367 < 368); guardião 5 asserções verdes; regra confirmada byte-idêntica no `<style>` servido pelo bundle de produção (20-03, 20-04). **Nunca observado ao vivo com a preferência realmente ativa** — nenhuma ferramenta do ambiente (nas 3 execuções + 2 reverificações do orquestrador) expõe emulação real de `prefers-reduced-motion` via CDP; ver Human Verification Required. |

**Score:** 7/7 truths verificadas no nível de código/artefato/bundle de produção; 1 (MOTION-03) tem a metade comportamental pendente de confirmação humana.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `web/src/App.jsx` | `CONTENT_MAX_WIDTH`, `overflow-x:hidden`, `maxWidth:"100%"` no badge, `tabular-nums`, `numHero/numBody/numMicro`, 15×`fontFamily: DISPLAY`, gate `prefers-reduced-motion` amplo | ✓ VERIFIED | Todas as strings/regras confirmadas por grep direto no arquivo; `npx vite build` sai com código 0 |
| `web/tests/test_fase20_fundacao_visual.mjs` | Guardião estático cobrindo os 7 requisitos | ✓ VERIFIED | 180 linhas, 22 asserções, `node tests/test_fase20_fundacao_visual.mjs` → EXIT 0, todas `ok` |
| `server/web_dist` (bundle de produção) | Fundação publicada, carimbo `F10-20260905-02`, 4 assinaturas de CSS presentes | ✓ VERIFIED | `web/src/version.js`, `server/app/main.py:SERVER_BUILD_ID` e `server/web_dist/assets/index-qgYCE9kb.js` com o mesmo carimbo; `grep -rl` confirma `tabular-nums`, `overflow-x:hidden`, `prefers-reduced-motion`, `720px` no bundle minificado |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `const CONTENT_MAX_WIDTH` | BottomNav + wrapper de conteúdo pós-login | `maxWidth: CONTENT_MAX_WIDTH` | ✓ WIRED | 2 ocorrências confirmadas (`App.jsx:928`, `App.jsx:9020`); zero literal residual |
| `web/tests/test_fase20_fundacao_visual.mjs` | `web/src/App.jsx` | `readFileSync` + asserção de substring | ✓ WIRED | Teste lê o arquivo real, roda isolado (`node tests/...mjs`) e integrado (`scripts/executar.sh --testes`) |
| `.b3 [style*="ui-monospace"]` (GlobalStyle) | ~151 call sites `fontFamily: MONO` | seletor de atributo sobre style inline serializado pelo React | ✓ WIRED | `grep -c 'fontFamily: MONO'` inalterado (151); confirmado por medição ao vivo (`fontVariantNumeric` computado = `tabular-nums` em dezenas de elementos reais, dev e produção) |
| `const numBody` | valor de patrimônio do Topbar | spread `{...numBody, ...}` | ✓ WIRED | `App.jsx:886`; diff visual zero confirmado por comparação de screenshot |
| `const DISPLAY` | 15 `<h1>` de tela | `fontFamily: DISPLAY` | ✓ WIRED | Igualdade de contagem 15=15; `document.fonts.check` confirma carregamento real da fonte, não só a cascata |
| Bloco `@media (prefers-reduced-motion: reduce)` amplo | Regras `.b3{transition}` e `.b3-mode-switch{transition!important}` | ordem de fonte (empate de especificidade resolvido por posição) | ✓ WIRED (estático) / ? UNCERTAIN (comportamento) | Ordem de linha confirmada (306 < 337 < 367); regra servida byte-idêntica em produção; efeito comportamental sob emulação real nunca observado (ver Human Verification) |

### Data-Flow Trace (Level 4)

Não aplicável no sentido tradicional (a fase é CSS/estilo estático, não dado dinâmico de servidor) — mas o equivalente é "o seletor casa com o DOM real servido":

| Artifact | "Dado" | Fonte | Produz efeito real | Status |
|----------|--------|-------|---------------------|--------|
| `.b3 [style*="ui-monospace"]` | Atributo `style` serializado pelo React em runtime | JSX inline `fontFamily: MONO` | Confirmado via `getComputedStyle().fontVariantNumeric` em dezenas de elementos reais, dev E produção | ✓ FLOWING |
| Bloco amplo `prefers-reduced-motion` | Media feature do SO/navegador | preferência de acessibilidade do usuário | Regra CSS presente e correta; efeito só inferido, nunca observado sob o media feature realmente ativo | ⚠️ NÃO CONFIRMADO COMPORTAMENTALMENTE |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Guardião estático (22 asserções, 7 requisitos) | `cd web && node tests/test_fase20_fundacao_visual.mjs` | EXIT 0, 22/22 `ok` | ✓ PASS |
| Build de produção do front | `cd web && npx vite build` | EXIT 0, `dist/` gerado, sem erro de sintaxe | ✓ PASS |
| Suíte canônica completa (pytest + `.mjs`) | `bash scripts/executar.sh --testes` | Com sandbox padrão: 27 falhas — diagnosticadas como `PermissionError: [Errno 1] Operation not permitted` ao carregar certificados SSL (`ssl.py:717`), causa de sandbox, não do código. Com sandbox desabilitado: **2021 passed + 1 skipped, 115/115 `.mjs` OK, EXIT 0** | ✓ PASS (após isolar o artefato de sandbox) |
| Publicação (3 elos do carimbo + 4 assinaturas de CSS no bundle) | `grep` direto em `web/src/version.js`, `server/app/main.py`, `server/web_dist/assets/*.js` | Carimbo `F10-20260905-02` idêntico nos 3 elos; `tabular-nums`/`overflow-x:hidden`/`prefers-reduced-motion`/`720px` presentes no bundle minificado | ✓ PASS |

### Probe Execution

Não aplicável — fase não declara nem usa `scripts/*/tests/probe-*.sh`; nenhum probe convencional encontrado para este escopo (CSS/shell visual).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| FIX-01 | 20-01 | `.b3-shell` nunca rola horizontal além do viewport | ✓ SATISFIED | Ver Truth #1 |
| FIX-02 | 20-01 | `MarketStatusBadge` trunca com reticência em vez de vazar | ✓ SATISFIED | Ver Truth #2 |
| SYS-04 | 20-01 | Conteúdo ≥768px respeita o mesmo 720px do BottomNav | ✓ SATISFIED | Ver Truth #3 |
| TYPO-01 | 20-02 | Todo número com `MONO` usa `tabular-nums` | ✓ SATISFIED | Ver Truth #4 |
| TYPO-02 | 20-02 | Escala numérica nomeada de 3 níveis existe e tem consumidor | ✓ SATISFIED (com ressalva de escopo documentada no ROADMAP) | Ver Truth #5 |
| TYPO-03 | 20-03 | H1 de cada tela usa `DISPLAY` (Fredoka) | ✓ SATISFIED | Ver Truth #6 |
| MOTION-03 | 20-03 | App respeita `prefers-reduced-motion` | ✓ SATISFIED no código; comportamento pendente de confirmação humana | Ver Truth #7 |

Nenhum requisito órfão: os 7 IDs declarados nos frontmatters dos planos (`20-01` a `20-04`) batem exatamente com os 7 IDs listados em `REQUIREMENTS.md` sob "Phase 20" e com os 7 requisitos citados no `ROADMAP.md`.

### Anti-Patterns Found

Nenhum. Varredura do diff da fase (`git diff e33566a..40e2d46 -- web/src/App.jsx web/tests/test_fase20_fundacao_visual.mjs`) não encontrou `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER`, nem handler vazio, nem retorno estático mascarando dado dinâmico. O escopo do diff está limitado aos arquivos declarados (`App.jsx`, o guardião novo, `version.js`, 1 linha de `main.py`, e a árvore `server/web_dist` regenerada pelo build) — sem pacote novo (`git diff` dos 4 manifests vazio) e sem `git push` executado.

### Human Verification Required

### 1. Comportamento real de `prefers-reduced-motion: reduce` (MOTION-03)

**Test:** Ligar "Reduzir movimento" no sistema operacional (macOS: Ajustes do Sistema → Acessibilidade → Movimento → Reduzir Movimento; ou usar uma ferramenta de emulação de navegador que realmente alterne o media feature, não apenas viewport/color-scheme), então abrir o app (dev `:5173` ou produção `:8787`, build `F10-20260905-02`), logar e observar: (1) trocar tema/modo em Preferências — a transição de cor deve ser instantânea, sem fade perceptível; (2) tirar dois screenshots do Topbar/home com ~1s de intervalo — o marquee do ticker e o spinner (se visível) devem estar exatamente na mesma posição, sem indicação de "strobe" (ciclo acelerado); (3) desligar a preferência e confirmar que o ticker volta a se mover normalmente.
**Expected:** Nenhuma transição/animação perceptível roda com a preferência ligada; ticker e spinner ficam parados (não em flicker); ao desligar, o comportamento padrão volta sem quebra.
**Why human:** A regra CSS que produz esse comportamento foi confirmada, byte a byte, correta e presente no código-fonte e no bundle de produção servido — mas o efeito real do navegador aplicando essa regra sob o media feature genuinamente ativo nunca foi observado em nenhuma das 3 sessões de execução nem nas 2 reverificações do orquestrador, porque nenhuma ferramenta disponível no ambiente (MCP de browser, CDP) expõe `Emulation.setEmulatedMedia` para alternar `prefers-reduced-motion` programaticamente. Presença de CSS correto não é prova de comportamento correto — só um humano com controle real do SO (ou uma ferramenta de emulação CDP genuína) pode fechar este item.

### Gaps Summary

Não há gaps de código, arquivo ou wiring: os 7 requisitos da Fase 20 (FIX-01, FIX-02, SYS-04, TYPO-01, TYPO-02, TYPO-03, MOTION-03) estão implementados, travados por um guardião estático de 22 asserções, e confirmados publicados no bundle de produção (carimbo `F10-20260905-02`, coerente nos 3 elos, com as 4 assinaturas de CSS presentes no bundle minificado). A suíte canônica está verde (2021 pytest + 115 `.mjs`) quando isolada do artefato de sandbox local (permissão de leitura de certificado SSL, não relacionado ao código da fase).

O único item pendente é comportamental, não estrutural: a metade "efeito visual sob `prefers-reduced-motion` realmente ativo" do MOTION-03 nunca foi observada ao vivo, por limitação de ferramenta consistentemente documentada (não por omissão) em três sessões de execução e duas reverificações do orquestrador. Isso não é evidência de que o código esteja errado — a regra é sintaticamente correta, na ordem certa, e é o mesmo mecanismo de navegador (CSS media query) que qualquer app usa para essa preferência — mas o framework de verificação não aceita "deveria funcionar" como prova de comportamento, e por isso este item vai para verificação humana em vez de ser marcado como fechado.

Adicionalmente, o critério de sucesso 4 do ROADMAP ("todo valor financeiro usa um dos três tamanhos nomeados") só está parcialmente fechado (a metade `tabular-nums`/TYPO-01 sim; a migração tela a tela para `numHero`/`numBody`/`numMicro`/TYPO-02 não) — mas isso NÃO é um gap desta verificação: o próprio `ROADMAP.md`, na seção da Fase 20, já carrega a ressalva textual de que essa segunda metade é deferimento explícito para as Fases 21/22. O contrato da fase já nasceu recortado dessa forma; a fase entrega exatamente o que prometeu.

---

*Verified: 2026-09-05*
*Verifier: Claude (gsd-verifier)*
