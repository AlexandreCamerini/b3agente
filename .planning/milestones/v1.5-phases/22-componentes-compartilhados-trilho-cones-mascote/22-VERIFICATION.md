---
phase: 22-componentes-compartilhados-trilho-cones-mascote
verified: 2026-09-06T00:00:00Z
status: human_needed
score: 15/15 must-haves verified in code; 1 item requires live human verification with real market/account data
overrides_applied: 0
human_verification:
  - test: "Rolar a tira 'Oportunidades de opções' (Posições) e a linha de candidatos de PropostaDaPosicao com uma conta que tenha proposta de opção ativa; medir no DOM getComputedStyle(container).scrollSnapType (esperado 'x proximity' ou serialização equivalente do navegador) e getComputedStyle(primeiroItem).scrollSnapAlign (esperado 'start')."
    expected: "Ambos os trilhos assentam em item ao parar de rolar, sem ganhar a largura de 84% do HERO-CARROSSEL (minWidth 210px preservado, comparação lado a lado intacta)."
    why_human: "Depende de dado real de mercado/conta (proposta de opção ativa). Na sessão de verificação do orquestrador (22-04-SUMMARY.md) a conta de teste estava com portfólio vazio e mercado fechado — os dois trilhos não tinham item para medir ao vivo. A prova estática (guardião test_fase22_componentes_compartilhados.mjs, Seção A) confirma que o JSX-fonte desses dois sites chama carouselTrackStyle()/carouselItemStyle('start') corretamente, mas isso não substitui a medição de scroll-snap computado no navegador contra dado real."
---

# Phase 22: Componentes compartilhados (trilho, ícones, mascote) Verification Report

**Phase Goal:** Os padrões que hoje divergem de tela para tela passam a ser um
só: um único comportamento de rolagem horizontal (scroll-snap + espiada do
próximo item), ícones SVG no traço do app no lugar de emoji do sistema, e o
mascote flutuante (`PetFab`) com separação visual suficiente para nunca
parecer cortado pela borda de um card atrás dele.

**Verified:** 2026-09-06
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Existe UM único padrão de rolagem horizontal — todos os 4 trilhos passam pelo mesmo helper, nenhum define `overflowX`/scroll-snap por conta própria | ✓ VERIFIED | `grep -n overflowX web/src/App.jsx` → só a definição do helper (L303) e o `<main>` (L9056, fora de escopo por FIX-01/Fase 20). `carouselTrackStyle(` e `carouselItemStyle(` aparecem 4× cada (confirmado por grep independente). |
| 2 | Os 3 trilhos que rolavam solto (filtro MODELO DE ANÁLISE, tira de oportunidades, linha de candidatos) assentam em item ao parar | ✓ VERIFIED | Guardião `test_fase22_componentes_compartilhados.mjs` Seção A (12 asserções) confirma `carouselItemStyle("start")` nos 3 sites, isolado por assinatura textual (função/`.map()`). Rodado independentemente: 111/111 asserções OK, exit 0. |
| 3 | Nenhum dos 3 ganhou 84% de largura — filtro segue escaneável (~3 chips), candidatos seguem comparáveis lado a lado | ✓ VERIFIED | `grep -c 'flex: "0 0 84%"'` → 1 (só HERO, linha 1993). `minWidth: "118px"` → 1 (chip intacto); `minWidth: "210px"` → 2 (tira + CandidatoOpcao intactos). |
| 4 | Guardião estático trava o padrão único (trilho novo que redefina `overflowX` inline quebra a suíte) | ✓ VERIFIED | Asserção central do guardião: `overflowX: "auto"` conta exatamente 1× em `App.jsx`; passou. |
| 5 | Seletor de Modo, chips de ação, botão Stop/alvo, aviso de chave configurada mostram SVG no traço do `NavIcon` — zero emoji do SO | ✓ VERIFIED | `grep -noP "[\x{1F300}-\x{1FAFF}]" web/src/App.jsx` → vazio (checado nesta sessão, independente do guardião). `⚪` também ausente. |
| 6 | Todos os ícones novos saem do MESMO registro do `NavIcon`; um único ícone de gráfico serve os 5 sites de 📈; nenhuma lib de ícone entrou | ✓ VERIFIED | `NavIcon` generalizado (`function NavIcon({ id, active, size = 23, color })`, L920); mapa `paths` com `graduacao`/`brilho`/`checado` novos + 7 antigos preservados (`radar:` único). `web/package.json` sem `lucide-react`/`react-icons`/etc (guardião Seção B, asserção 11, passou). |
| 7 | Ícones herdam cor do texto ao lado (nunca hex fixo) — legíveis nos dois temas | ✓ VERIFIED | Verificação direta: `grep -n 'color="currentColor"' web/src/App.jsx` mostra 7 usos reais (L2197 Estudo, L2198 Operador, L3745 brilho/Reanalisar, L3747 Indicadores, L4576 Stop/alvo (IA), L5661 checado/chave configurada, L6799 radar/Varredura automática de hoje) — exatamente os 7 sites do plano 22-02/22-03 que deveriam usar `currentColor` (o 8º hit do grep é o comentário de documentação em L917, não um call site). `NavIcon` propaga isso para `stroke: c` no SVG (`c = color || ...`), então o ícone herda de fato a cor CSS computada do elemento pai — mecanismo real do navegador, não um token. A exceção documentada (fallback do sparkline, L3503) usa `color={T.textMuted}` explicitamente, conforme o próprio `22-PATTERNS.md` prescreve para aquele site — não é uma omissão. |
| 8 | Nenhum rótulo visível perdido; nenhum nome acessível mudou | ✓ VERIFIED | `grep -c aria-label web/src/App.jsx` → 34 (mesmo valor registrado antes/depois no 22-02-SUMMARY.md). Rótulos "Indicadores", "Stop/alvo (IA)", "chave configurada", "Reanalisar", "Estudo"/"Operador" confirmados presentes por grep e pelo guardião. |
| 9 | Os 2 guardiões que travavam emoji como literal (`test_copy_theme.mjs`, `test_carteira_lastro_ui.mjs`) foram ATUALIZADOS com nota, não apagados | ✓ VERIFIED | Ambos presentes na suíte canônica e passando (confirmado na execução completa desta sessão); comentários datados "Fase 22 (SYS-02, 2026-09-06)" presentes no código-fonte. |
| 10 | Ponto de tier do Radar é SVG com paleta própria, separada do verde/vermelho de sinal de mercado | ✓ VERIFIED | `TierDot`/`TIER_FILL` com 4 literais hex (`#22c55e`/`#f59e0b`/`#9ca3af`/`#ef4444`), confirmado que o recorte NÃO cita `T.positive`/`T.negative`/`T.warn` (guardião, asserção C8, passou). Confirmado ao vivo em produção: `<circle fill="#22c55e">` adjacente a "Forte" (22-04-SUMMARY.md). |
| 11 | Ícone de varredura do Radar reusa a geometria `radar` do `NavIcon` — nenhuma segunda versão | ✓ VERIFIED | `grep -c "^\s*radar:" web/src/App.jsx` → 1; `<NavIcon id="radar"` presente dentro de `RadarScreen`. |
| 12 | Sombra do PetFab vem de token por tema (`T.shadowFab`), não de rgba fixo | ✓ VERIFIED | `PALETTE.dark.shadowFab = "rgba(0,0,0,0.45)"`, `PALETTE.light.shadowFab = "rgba(15,20,28,0.22)"` (valores DIFERENTES); `PetFab` consome `` `drop-shadow(0 3px 6px ${T.shadowFab})` ``; zero `rgba(0,0,0,0.45)` literal restante no `PetFab`. |
| 13 | Tema escuro mantém exatamente a sombra de hoje — mudança é só no tema claro | ✓ VERIFIED | `shadowFab` dark = `rgba(0,0,0,0.45)`, idêntico ao valor hardcoded pré-fase (confirmado por diff/leitura do código). |
| 14 | Sombra do PetFab conferida a olho nos dois temas antes de fechar SYS-03 | ✓ VERIFIED | 22-03-SUMMARY.md mediu contra o dev server; 22-04-SUMMARY.md (Task 2, "Orchestrator Live Re-Verification") mediu 4 combinações tema×modo contra o **bundle de produção** (`:8787`), valores computados batendo com os literais de `PALETTE` (`rgba(0, 0, 0, 0.45)` escuro; `rgba(15, 20, 28, 0.22)` claro), com veredito visual "sem virar disco/badge" registrado. |
| 15 | Fase publicada — carimbo novo coerente em `web/src/version.js`, `server/app/main.py`, `server/web_dist`; remoção dos 9 emojis chegou ao bundle | ✓ VERIFIED | `BUILD_ID`/`SERVER_BUILD_ID` = `F10-20260906-01` nos dois arquivos; bundle contém o carimbo (`index-Btka_lGt.js`). Checagem independente nesta sessão: as 6 assinaturas de presença (`x proximity`, `#f59e0b`, `Varredura automática de hoje`, `Stop/alvo (IA)`, `chave configurada`, `shadowFab`) presentes; os 9 glifos (`🎓 📈 ✨ ✅ 📡 🟢 🟡 ⚪ 🔴`) **ausentes** do bundle. `--shadow-fab` de fato não existe como string literal em lugar nenhum (achado do 22-04-SUMMARY.md confirmado: `VARKEY` gera o nome do custom property em runtime) — prova alternativa (`shadowFab` + os 2 valores rgba) aceita como equivalente. |

**Score:** 15/15 truths verificadas no código; 1 critério (trilho único, SYS-01) tem 2 dos 4 sites sem medição DINÂMICA em produção por falta de dado real de mercado/conta na sessão de verificação — ver Human Verification abaixo.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `web/src/App.jsx` | `carouselTrackStyle`/`carouselItemStyle`, `NavIcon` generalizado, `TierDot`/`TIER_FILL`, `PALETTE.{dark,light}.shadowFab` | ✓ VERIFIED | Todos os símbolos confirmados por leitura direta e grep nesta sessão (ver truths acima). |
| `web/tests/test_fase22_componentes_compartilhados.mjs` | Guardião único da fase, 4 seções (A/B/C/D) | ✓ VERIFIED | Executado nesta sessão: 111 asserções, todas `ok`, exit 0. |
| `server/web_dist` | Bundle publicado com as 3 mudanças e sem os 9 emojis | ✓ VERIFIED | Confirmado por grep direto nesta sessão (presença das 6 assinaturas + ausência dos 9 glifos). |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| 4 containers de trilho | `carouselTrackStyle`/`carouselItemStyle` | chamada com overrides de call site | ✓ WIRED | 4 chamadas de cada, confirmadas por grep e pelo guardião isolando cada função/site por nome. |
| 7 sites de ícone inline (onda 2 + Radar) | `NavIcon` (L920) | `<NavIcon id=... size=... color="currentColor" />` | ✓ WIRED | Confirmado por grep direto: 7 usos reais de `color="currentColor"` nos sites corretos (L2197/2198/3745/3747/4576/5661/6799), mais o fallback do sparkline (L3503) usando `color={T.textMuted}` por design. `NavIcon` propaga `color` para `stroke` no SVG. |
| `PetFab` | `PALETTE.{dark,light}.shadowFab` | `T.shadowFab` via mecanismo `VARKEY`/`T` existente | ✓ WIRED | `drop-shadow(0 3px 6px ${T.shadowFab})` presente; nenhum plumbing extra necessário, confirmado pela ausência de mudança em `VARKEY`/`T`. |
| `web/src/version.js` | `server/web_dist` | `bump.sh` + `publicar-web.sh` | ✓ WIRED | Carimbo idêntico nos 3 elos, bundle contém o carimbo, verificado nesta sessão. |

### Data-Flow Trace (Level 4)

Não aplicável de forma extensa — esta fase é estrutural/visual (estilo inline,
sem novo fetch/estado assíncrono). O único "dado" relevante é `r.confluencia`
alimentando `tierOf`/`TierDot`, que já é consumido de estado existente
(inalterado por esta fase) e confirmado renderizando de fato em produção
(`<circle fill="#22c55e">` ao lado de "Forte", 22-04-SUMMARY.md).

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Guardião estático da Fase 22 roda e passa | `node web/tests/test_fase22_componentes_compartilhados.mjs` | 111 asserções `ok`, exit 0 | ✓ PASS |
| Varredura Unicode pictográfica independente | `node -e "...match(/[\u{1F300}-\u{1FAFF}]/gu)..."` sobre `App.jsx` | `null` (zero matches) | ✓ PASS |
| `color="currentColor"` nos call sites corretos | `grep -n 'color="currentColor"' web/src/App.jsx` | 7 usos reais nos 7 sites esperados (1 hit adicional é comentário de doc, não call site) | ✓ PASS |
| Build de produção compila | `cd web && npx vite build` | exit 0, chunk `index-Btka_lGt.js` idêntico ao publicado em `server/web_dist` | ✓ PASS |
| Suíte canônica completa (pytest + `web/tests/*.mjs`) | `bash scripts/executar.sh --testes` | pytest `2021 passed, 1 skipped`; 117/117 `.mjs` `[OK]`; exit 0 | ✓ PASS |
| Bundle de produção: 6 assinaturas presentes + 9 glifos ausentes | `grep -rlI ... server/web_dist` (x8 sinais + x9 glifos) | Todas as presenças com ≥1 arquivo; todas as ausências vazias | ✓ PASS |

### Probe Execution

Não aplicável — fase de UI sem `scripts/*/tests/probe-*.sh` declarado nem
convencional para este tipo de mudança.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| SYS-01 | 22-01, 22-04 | Um único padrão de carrossel horizontal em todo lugar | ✓ SATISFIED no código/guardião; **parcialmente medido ao vivo** (2 de 4 trilhos sem dado real na sessão) | Ver truths 1-4, 15; human_verification abaixo |
| SYS-02 | 22-02, 22-03 | Zero emoji do SO; ícone SVG no traço do NavIcon; legível nos 2 temas | ✓ SATISFIED | Ver truths 5-9, 10-11; varredura Unicode independente confirmou zero; `currentColor` confirmado por grep nos 7 sites corretos |
| SYS-03 | 22-03, 22-04 | Mascote flutuante separado do fundo nos 2 temas | ✓ SATISFIED | Ver truths 12-14; medição ao vivo contra bundle de produção registrada e consistente com o código |

Nota: `.planning/REQUIREMENTS.md` (linhas 30-41) e `.planning/STATE.md` ainda
marcam SYS-01/02/03 como `[ ]`/"Pending" e `stopped_at: Phase 22 UI-SPEC
approved` — isso é **defasagem de documento de tracking**, não um problema de
código: o ROADMAP.md já marca os 4 planos como `[x]` e todas as evidências de
código/teste/bundle confirmam a implementação. Recomenda-se atualizar esses
dois arquivos ao fechar a fase, mas isso não bloqueia a verificação.

### Anti-Patterns Found

Nenhum bloqueador. Buscas por `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER`
nos arquivos tocados pela fase (`web/src/App.jsx`, os 3 arquivos de teste
editados) não retornaram ocorrências novas desta fase — os comentários
extensos são explicações de decisão de design, não marcadores de dívida.

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | nenhum encontrado | — | — |

### Human Verification Required

#### 1. Scroll-snap dinâmico nos 2 trilhos dependentes de dado real (SYS-01)

**Test:** Com uma conta que tenha ao menos uma posição com proposta de opção
ativa (ex.: put isolada ou collar da Fase 19), abrir Posições e medir no
console do navegador, contra o bundle de produção (`server/web_dist`, não o
dev server):
```js
getComputedStyle(document.querySelector(/* container da tira Oportunidades de opções */)).scrollSnapType
getComputedStyle(document.querySelector(/* container de candidatos da PropostaDaPosicao */)).scrollSnapType
```
e o `scrollSnapAlign` do primeiro item de cada um.

**Expected:** `x proximity` (ou a serialização equivalente que o Chromium usa
quando a força é implícita — já observado no HERO/Watchlist: `"x"` sozinho é
uma serialização válida de `"x proximity"`) no container, `"start"` no
primeiro item, largura do item inalterada (`minWidth: 210px`), permitindo ver
mais de um candidato/oportunidade por vez.

**Why human:** Depende de mercado aberto e/ou uma conta com proposta de opção
ativa — na sessão de verificação (orquestrador, 22-04-SUMMARY.md) a conta de
teste estava vazia e o mercado fechado, então os dois trilhos não tinham item
renderizado para medir. A prova estática (código-fonte + guardião,
confirmada nesta verificação) mostra que os call sites corretos chamam
`carouselTrackStyle`/`carouselItemStyle("start")`, o que é forte evidência —
mas não substitui a medição de `scrollSnapType` computado pelo navegador
contra o bundle real com item renderizado.

### Gaps Summary

Nenhum gap bloqueador no código. A fase entrega, de forma verificável e
travada por guardião estático + suíte canônica completa + inspeção direta do
bundle de produção, os três critérios de sucesso do ROADMAP (SYS-01/02/03),
incluindo a wiring de cor (`color="currentColor"`) confirmada por grep direto
nos 7 sites corretos — não apenas inferida da narrativa do SUMMARY. O único
item pendente é uma confirmação dinâmica (DOM real, não estática) de
scroll-snap em 2 dos 4 trilhos, que depende de estado de mercado/conta que não
estava disponível durante a sessão de verificação do orquestrador — está
corretamente registrado como aberto (não forjado) nos próprios artefatos da
fase, e esta verificação concorda com esse registro.

---

*Verified: 2026-09-06*
*Verifier: Claude (gsd-verifier)*
