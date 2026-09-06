---
phase: 23-motion-com-proposito-e-ilustracao-unificada
verified: 2026-09-06T00:00:00Z
status: human_needed
score: 4/5 success criteria verified in code + bundle; 1 (reduced-motion behavioral) and one sub-case of criterion 2 (real success pulse) require live human verification with real OS settings / open market
overrides_applied: 0
human_verification:
  - test: "Com 'Reduzir Movimento' ligado no SO (macOS: Ajustes → Acessibilidade → Movimento → Reduzir Movimento), abrir a Watchlist/Radar e confirmar uma ordem, no build F10-20260906-02."
    expected: "Cards de setup inédito aparecem no estado final DIRETO (sem fade, sem translateY 8px). Ao confirmar uma ordem, o modal fecha NA HORA — sem pulso no valor e SEM os ~120ms de espera do setTimeout (o portão é REDUCE_MOTION em JS, não só a regra CSS)."
    why_human: "Nenhuma ferramenta disponível neste ambiente expõe Emulation.setEmulatedMedia via CDP para alternar prefers-reduced-motion programaticamente — mesma limitação de ferramenta já documentada e aceita nas Fases 20-22 (20-HUMAN-UAT.md, Test 1). A prova estática é completa e independentemente reconfirmada nesta sessão: exatamente 2 blocos @media (prefers-reduced-motion: reduce) em GlobalStyle() (nenhum novo), REDUCE_MOTION declarado 1x e consumido nos dois portões (if (s.pendente || REDUCE_MOTION) / if (st.pendente || REDUCE_MOTION)) antes do setTimeout(finalizar, 120). Itens 4 e 5 já registrados em 20-HUMAN-UAT.md, pendentes, aguardando o Alex."
  - test: "Com o mercado ABERTO (pregão em andamento), confirmar uma compra e uma VENDA TOTAL de uma posição, e observar o valor ('Custo estimado'/'Valor estimado') pulsar (~120ms, scale(1→1.08→1)) antes do modal fechar e do toast de sucesso aparecer."
    expected: "O pulso pinta e é visível antes do fechamento do modal, inclusive na venda TOTAL (caso de risco: SellModal desmonta via `if (!pos) return null` se setData rodasse antes do pulso — o código já move setData para dentro de finalizar(), mas a confirmação visual ao vivo com mercado aberto não foi feita)."
    why_human: "Depende de horário de pregão — em toda a janela de execução e verificação desta fase (domingo, 2026-09-06) o mercado esteve fechado, então só os ramos pendente/rejeitada/duplo-toque puderam ser exercitados ao vivo (confirmados, zero pulsos indevidos, zero ordem duplicada, inclusive sob teste adversarial de 3 cliques síncronos). Já registrado em 20-HUMAN-UAT.md Test 3, pendente."
---

# Phase 23: Motion com propósito e ilustração unificada Verification Report

**Phase Goal:** O movimento passa a comunicar mudança de estado (card novo,
confirmação de ordem) em vez de existir por decoração, e o Boris tem um único
rosto em todo o produto.

**Verified:** 2026-09-06
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | MOTION-01: setup inédito na Watchlist/Radar entra com transição curta (fade+subida ~200ms), em vez de surgir sem aviso | ✓ VERIFIED | `@keyframes b3cardEnter{ from{ opacity:0; transform:translateY(8px); } to{ opacity:1; transform:translateY(0); } }` + `.b3 .card-enter{ animation:b3cardEnter 200ms ease-out; }` confirmados literais em `App.jsx:365-366` (grep direto nesta sessão). Mecanismo de "visto nesta sessão" (`useRef(new Set())`/`isNovo`) presente e correto em `MercadoScreen` (L3781-3800) e `RadarScreen` (L6711-6791), commitado em `useEffect` sem array de deps (StrictMode-safe), consumido no `vm`/`radarVm` dos dois call sites (L3914, L6941) e na raiz do `AtivoCard` (L3445). Guardião `test_fase23_motion.mjs` Seção A: 22 asserções, todas `ok`, exit 0 (rodado nesta sessão, independente). Assinaturas presentes no bundle publicado (`server/web_dist`): `b3cardEnter`, `card-enter`, `translateY(8px)` — todas confirmadas por `grep -rlI` nesta sessão. |
| 2 | MOTION-02: ao confirmar compra/venda, o valor pulsa (~120ms) antes de virar estado de sucesso | ✓ VERIFIED no código/estrutura; ⚠ sub-caso "sucesso real com mercado aberto" não exercitado ao vivo | `@keyframes b3valuePulse` + `.b3 .value-pulse{ display:inline-block; animation:b3valuePulse 120ms ease-out; }` confirmados literais em `App.jsx:367-368`. `confirmBuy`/`confirmSell` reescritos com wrapper `const finalizar = () => {...}` que move `setData`/`track`/`flash` para depois do portão `if (s.pendente \|\| REDUCE_MOTION)` / `if (st.pendente \|\| REDUCE_MOTION)` (confirmado por grep direto, L8205-8330), corrigindo a armadilha do SellModal (`if (!pos) return null`). Guarda de duplo envio em duas camadas: handler (`if (!bm \|\| bm.confirmado) return;`) e botão (`disabled={!ok \|\| !!buyModal.confirmado}`), confirmados. Guardião Seção B: 22 asserções novas, todas `ok`. Confirmado AO VIVO (dev bundle, 23-03-SUMMARY.md, reconferido nesta sessão contra o código): caminho pendente e rejeitado nunca pulsam, inclusive sob 3 cliques síncronos adversariais — resultado financeiro correto (1 ordem real, 2 rejeições, zero duplicação). O caminho de sucesso real (mercado aberto) não foi exercitado em nenhuma das sessões — mercado esteve fechado (domingo) durante toda a janela de execução e verificação desta fase. Ver Human Verification. |
| 3 | Com "reduzir movimento" ligado, nem a entrada de card nem o pulso animam — estado final aparece direto | ✓ VERIFIED o mecanismo; ⚠ comportamento real no SO não medido | Contagem de blocos `@media (prefers-reduced-motion: reduce)` = exatamente 2 (confirmado nesta sessão por `grep -v '^\s*//' web/src/App.jsx \| grep -c ...`), reusados sem alteração desde a Fase 20 — nenhum bloco novo. `REDUCE_MOTION` (`App.jsx:1443`) declarado 1x e consumido nos dois portões de MOTION-02 antes do `setTimeout`, prevenindo "não anima mas ainda espera 120ms". Guardião `test_fase20_fundacao_visual.mjs` (contagem exata) e a Seção B do guardião da Fase 23 (asserção de `REDUCE_MOTION` único) ambos verdes nesta sessão. Comportamento real com a preferência ligada no SO não é medível neste ambiente (sem CDP `Emulation.setEmulatedMedia`) — itens 4/5 já registrados em `20-HUMAN-UAT.md`, pendentes. Ver Human Verification. |
| 4 | ILUS-01: arte do modal "Este é o Boris" é flat/cartoon no vocabulário do LogoMark; lado a lado com o ícone do app é reconhecível como o mesmo personagem | ✓ VERIFIED | `web/src/pet/BorisFlat.jsx` existe, `export default function BorisFlat({ size = 110 })`, rosto copiado verbatim do `LogoMark` (mesmos `cx`/`cy`/`r`/`d`), corpo novo em `#2a3a6b`, óculos/bico/gravata em `#f2a93b` hardcoded (sem `var(--`, sem import de `App.jsx` — confirmado por leitura direta). `BorisIntro.jsx` importa e renderiza `<BorisFlat size={110} />`; import de `Boris`/PNG removido do arquivo. Guardião `test_boris_intro.mjs` (32 asserções, incluindo trava de ausência do import antigo e trava de fronteira de escopo) verde nesta sessão. **Confirmado AO VIVO contra o bundle de PRODUÇÃO** (23-04-SUMMARY.md, "Orchestrator Live Re-Verification"): modal reaberto via `PUT /api/config {borisIntroVisto:false}`, `<svg viewBox="0 0 64 92">` com 11 elementos path/circle presente nos temas claro E escuro, em Modo Operador com óculos/bico permanecendo âmbar (estruturalmente garantido — hex hardcoded, sem `var(--accent)`), `PetFab` confirmado intocado (ainda `boris-root`/PNG). O literal exclusivo do corpo (`M32 30 C48 30 54 44 54 60...`) confirmado presente no bundle publicado via grep nesta sessão. |
| 5 | Ícone do app já publicado (TestFlight/App Store) permanece inalterado | ✓ VERIFIED | `git status --porcelain resources/ios server/ios_dist` vazio (confirmado nesta sessão). `git show` dos commits da Fase 23 (`6143c4b`) confirma que o único arquivo tocado em `server/app/` foi a linha de `SERVER_BUILD_ID` em `main.py` — nenhum artefato de ícone/App Store alterado. |

**Score:** 5/5 critérios com evidência de código+bundle; 2 sub-itens (comportamento real de reduced-motion no SO, e pulso de sucesso real com mercado aberto) dependem de condições que nenhum agente neste ambiente controla — corretamente registrados como pendentes, não forjados.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `web/src/App.jsx` | keyframes b3cardEnter/b3valuePulse, `isNovo`/`vistosRef`, `finalizar()`/portões de 3 saídas, guarda de duplo envio, className condicional nos 2 modais | ✓ VERIFIED | Todos os símbolos confirmados por leitura direta e grep nesta sessão. |
| `web/tests/test_fase23_motion.mjs` | Guardião único da fase, Seção A (MOTION-01) + Seção B (MOTION-02) | ✓ VERIFIED | Executado nesta sessão: 44 asserções (22+22), todas `ok`, exit 0. |
| `web/src/pet/BorisFlat.jsx` | Ilustração flat SVG, sem import de App.jsx, sem tema | ✓ VERIFIED | Lido integralmente; hex literais, sem `var(--`, sem `import`. |
| `web/src/pet/BorisIntro.jsx` | Consome `BorisFlat`, import antigo removido | ✓ VERIFIED | Lido integralmente; `import BorisFlat from "./BorisFlat.jsx"`, `<BorisFlat size={110} />`. |
| `web/tests/test_boris_intro.mjs` | Guardião atualizado (não apagado), com nota de reversão deliberada | ✓ VERIFIED | 32 asserções, exit 0, comentário datado presente. |
| `server/web_dist` | Bundle publicado com os dois motions e a ilustração, carimbo novo, carimbo anterior ausente | ✓ VERIFIED | Todas as 10 assinaturas de presença (`b3cardEnter`, `card-enter`, `translateY(8px)`, `b3valuePulse`, `value-pulse`, `scale(1.08)`, `120ms ease-out`, `prefers-reduced-motion`, `#2a3a6b`, literal do corpo do BorisFlat) confirmadas por `grep -rlI` nesta sessão, cada uma em exatamente 1 arquivo. Carimbo `F10-20260906-02` presente nos 3 elos (`web/src/version.js`, `server/app/main.py:SERVER_BUILD_ID`, bundle); carimbo anterior (`F10-20260906-01`) ausente do bundle (`grep -rlI` vazio). `diff web/dist/assets/index-qMPKadI_.js server/web_dist/assets/index-qMPKadI_.js` — idêntico (build local reproduzido nesta sessão bate byte a byte com o publicado). |
| `.planning/phases/20-.../20-HUMAN-UAT.md` | Itens 4/5 de reduced-motion anexados, Test 1 e Gaps preservados | ✓ VERIFIED | `git show c0f10d8` confirma diff estritamente aditivo (só as linhas dos itens 4/5 e os contadores do Summary); nenhuma linha do Test 1 ou do bloco Gaps alterada. Nenhum `23-HUMAN-UAT.md` criado (`ls .planning/phases/23-*/` confirma). |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `MercadoScreen`/`RadarScreen` (`vistosRef`) | `AtivoCard` (raiz) | `vm.isNovo`/`radarVm.isNovo` → `className: isNovo ? "card-enter" : undefined` | ✓ WIRED | Confirmado por grep nos dois call sites e no destructuring/raiz do `AtivoCard`. |
| `GlobalStyle()` | Regra ampla de `prefers-reduced-motion` (Fase 20) | Cascata CSS — `animation` dentro de `.b3` | ✓ WIRED | Contagem exata de 2 blocos `@media` (nenhum novo) confirmada nesta sessão; os 2 keyframes novos ficam dentro do escopo `.b3`. |
| `confirmBuy`/`confirmSell` | `BuyModal`/`SellModal` (`<span>` do valor) | Flag `confirmado` no estado do modal → `className "value-pulse"` | ✓ WIRED | Confirmado: `className={buyModal.confirmado ? "value-pulse" : undefined}` na mesma linha que `{money(cost)}`; idem para `sellModal`/`{money(valor)}`. |
| Gate `pendente`/`REDUCE_MOTION` | Fechamento do modal + toast existente | `finalizar()` imediato ou `setTimeout(finalizar, 120)` | ✓ WIRED | Confirmado nos dois handlers, ordem de portão `pendente` antes de `REDUCE_MOTION`. |
| `BorisIntro.jsx` | `BorisFlat.jsx` | `import BorisFlat from "./BorisFlat.jsx"` | ✓ WIRED | Confirmado; import de `Boris`/PNG removido do arquivo. |
| `web/src/version.js` | `server/web_dist` | `scripts/bump.sh` → `scripts/publicar-web.sh` | ✓ WIRED | Carimbo idêntico nos 3 elos, bundle reproduzido byte a byte nesta sessão. |

### Data-Flow Trace (Level 4)

Não aplicável de forma extensa — fase é motion/ilustração puramente de
apresentação, sem novo fetch/estado assíncrono de dado de mercado. O único
"dado" relevante ao motion (`s.pendente`/`st.pendente`) já vem do motor
determinístico (`store.buy`/`store.sell`), inalterado por esta fase — confirmado
por leitura: nenhuma linha dentro do `try`/`catch` calcula pendência ou preço,
só consome o retorno do motor.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Guardião de motion da Fase 23 roda e passa (Seções A+B) | `node web/tests/test_fase23_motion.mjs` | 44 asserções `ok`, exit 0 | ✓ PASS |
| Guardião de ILUS-01 roda e passa | `node web/tests/test_boris_intro.mjs` | 32 asserções `ok`, exit 0 | ✓ PASS |
| Guardião da Fase 20 (reduced-motion) roda isolado e passa | `node web/tests/test_fase20_fundacao_visual.mjs` | 22 asserções `ok`, exit 0 | ✓ PASS |
| Build de produção compila | `cd web && npx vite build` | exit 0, chunk `index-qMPKadI_.js` idêntico byte a byte ao publicado em `server/web_dist` | ✓ PASS |
| Suíte canônica completa (pytest + `web/tests/*.mjs`) | `bash scripts/executar.sh --testes` (fora do sandbox — dentro dele, `mktemp`/SSL cert loading falham por restrição de escrita, artefato de ambiente já documentado nos SUMMARYs) | pytest `2021 passed, 1 skipped`; 118/118 `.mjs` `[OK]`; exit 0 | ✓ PASS |
| Bundle de produção: 10 assinaturas presentes + carimbo anterior ausente | `grep -rlI ... server/web_dist` | Todas as presenças com exatamente 1 arquivo; ausência do carimbo anterior confirmada (vazio) | ✓ PASS |
| Nenhum processo órfão desta fase/repo rodando | `ps aux \| grep -i "uvicorn\|vite"` (fora do sandbox) | Nenhum processo do `borisv2`/`b3-agente`; servidor de verificação foi parado ao final (`--stop`), conforme 23-04-SUMMARY.md | ✓ PASS |

### Probe Execution

Não aplicável — fase de UI sem `scripts/*/tests/probe-*.sh` declarado nem
convencional para este tipo de mudança.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| MOTION-01 | 23-01, 23-04 | Card inédito entra com fade+subida ~200ms, sem re-animar em re-render | ✓ SATISFIED | Ver truths 1; guardião + bundle confirmados nesta sessão. |
| MOTION-02 | 23-03, 23-04 | Valor pulsa ~120ms no caso executado; pendente/rejeitada nunca pulsam; sem duplo envio | ✓ SATISFIED no código; caso de sucesso real (mercado aberto) **NEEDS HUMAN** | Ver truths 2; caminhos negativos confirmados ao vivo, caminho de sucesso aberto por horário de pregão. |
| ILUS-01 | 23-02, 23-04 | Ilustração flat unificada, mesmo personagem do LogoMark/ícone, PetFab intocado | ✓ SATISFIED | Ver truths 4; confirmado ao vivo contra bundle de produção, 2 temas + Modo Operador. |

Nenhuma requirement órfã: `MOTION-01`/`MOTION-02`/`ILUS-01` são exatamente os 3
requirements do ROADMAP para esta fase e todos aparecem no frontmatter dos
planos 23-01/02/03.

### Anti-Patterns Found

Buscas por `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` nos arquivos
tocados pela fase (`web/src/App.jsx`, `web/src/pet/BorisFlat.jsx`,
`web/src/pet/BorisIntro.jsx`, `web/tests/test_fase23_motion.mjs`) não
retornaram ocorrências. Nenhum debt marker sem referência de issue/PR.

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | nenhum encontrado | — | — |

### Human Verification Required

#### 1. Comportamento real de `prefers-reduced-motion: reduce` para MOTION-01/02 (critério 3 do ROADMAP)

**Test:** Com "Reduzir Movimento" ligado no SO (macOS: Ajustes do Sistema →
Acessibilidade → Movimento → Reduzir Movimento), abrir a Watchlist/Radar no
build `F10-20260906-02` e confirmar que os cards de setup inédito aparecem no
estado final DIRETO (sem fade, sem translateY 8px). Confirmar uma ordem e
verificar que o modal fecha NA HORA — sem pulso e SEM os ~120ms de espera do
`setTimeout` (o portão `REDUCE_MOTION` existe em JS exatamente para isso).
Desligar a preferência e confirmar que as duas transições voltam.

**Expected:** Nenhuma animação visível, nenhum atraso perceptível, com a
preferência ligada; comportamento normal restaurado ao desligar.

**Why human:** Nenhuma ferramenta disponível neste ambiente expõe
`Emulation.setEmulatedMedia` via CDP para alternar o media feature
programaticamente — mesma limitação de ferramenta já documentada e aceita nas
Fases 20-22 (`20-HUMAN-UAT.md`, Test 1). Já anexado como itens 4 e 5 nesse
mesmo documento (aditivo, não um documento novo), pendentes.

#### 2. Pulso de sucesso real na confirmação de ordem, com mercado aberto (critério 2 do ROADMAP)

**Test:** Com o mercado ABERTO, confirmar uma compra e uma VENDA TOTAL de uma
posição e observar o valor pulsar (~120ms, `scale(1→1.08→1)`) antes do modal
fechar e do toast de sucesso aparecer. A venda TOTAL é o caso de risco
identificado no plano (`SellModal` desmonta via `if (!pos) return null` se o
estado fosse comitado antes do pulso).

**Expected:** O pulso pinta visivelmente antes do fechamento do modal em
ambos os casos (compra e venda total), sem regressão no fluxo de sucesso
existente (toast, oferta de stop/alvo na compra).

**Why human:** Depende de horário de pregão. Em toda a janela de execução e
verificação desta fase (2026-09-06, domingo) o mercado esteve fechado — só os
ramos pendente/rejeitada/duplo-toque puderam ser exercitados ao vivo
(confirmados sem regressão, inclusive sob teste adversarial). A prova estática
(guardião + inspeção de código, confirmada nesta sessão) mostra que o
mecanismo estrutural — `setData` dentro de `finalizar()`, portão
`pendente`-antes-de-`REDUCE_MOTION`, className condicional — está correto, mas
isso não substitui a confirmação visual do pulso em produção com mercado
aberto. Já registrado como Test 3 em `20-HUMAN-UAT.md`, pendente.

### Gaps Summary

Nenhum gap bloqueador no código. Os três requirements da fase (MOTION-01,
MOTION-02, ILUS-01) estão implementados, travados por guardião estático (44 +
32 asserções, todas verdes nesta sessão, independentemente da narrativa dos
SUMMARYs), publicados no bundle de produção com prova de build novo (carimbo
anterior ausente, chunk reproduzido byte a byte), e a suíte canônica completa
está verde (2021 backend + 118 web, confirmado fora do sandbox nesta sessão —
as 27 falhas observadas dentro do sandbox padrão são artefatos de permissão de
SSL/`mktemp`, não regressões de código, confirmado por reprodução isolada de
uma delas mostrando `PermissionError: [Errno 1] Operation not permitted` no
carregamento de certificado). ILUS-01 tem a evidência mais forte da fase:
confirmado ao vivo contra o bundle de produção real, nos dois temas e em Modo
Operador, com `PetFab` confirmado intocado. O ícone do app publicado não foi
tocado (evidência estática direta).

Os dois itens pendentes (comportamento real de reduced-motion no SO; pulso de
sucesso real com mercado aberto) são dependências de ambiente que nenhum
agente neste setup controla — a mesma classe de limitação já aceita e
documentada nas Fases 20-22 — e estão corretamente registrados como abertos em
`20-HUMAN-UAT.md` (itens 3, 4 e 5), não forjados nem aproximados por nenhum dos
quatro SUMMARYs da fase.

**Incidente operacional verificado, não é regressão de código:** o
`23-04-SUMMARY.md` registra que o orquestrador encontrou um processo `uvicorn`
órfão (PID 55990) servindo `:8787` a partir do `cwd` de um worktree já removido
(`git worktree remove --force`), causando um `404` transitório em `/`.
Confirmado nesta sessão: (1) o diff de `server/app/` na Fase 23 inteira está
limitado a uma única linha (`SERVER_BUILD_ID` em `main.py`, commit `6143c4b`)
— nenhuma mudança de rota, mount ou lógica de servidor; (2) nenhum processo
`uvicorn`/`vite` deste repositório está rodando atualmente (a busca por
processo mostrou apenas processos de um projeto não relacionado); (3) o bundle
publicado é reproduzível byte a byte a partir do código-fonte atual (`vite
build` local = `server/web_dist` commitado). A causa (processo apontando para
um diretório de worktree deletado) é puramente operacional/de ambiente de
execução, não uma falha introduzida pelo código desta fase.

---

*Verified: 2026-09-06*
*Verifier: Claude (gsd-verifier)*
