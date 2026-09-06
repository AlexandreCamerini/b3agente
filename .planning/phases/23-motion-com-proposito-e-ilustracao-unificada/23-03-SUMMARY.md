---
phase: 23-motion-com-proposito-e-ilustracao-unificada
plan: 03
subsystem: ui
tags: [react, css-keyframes, motion, accessibility, prefers-reduced-motion, trading, double-submit]

# Dependency graph
requires:
  - phase: 20-motion-fundacao-visual
    provides: "gate abrangente de prefers-reduced-motion em GlobalStyle() (MOTION-03), reusado verbatim sem @media novo"
  - phase: 23-motion-com-proposito-e-ilustracao-unificada (plano 01)
    provides: "guardião web/tests/test_fase23_motion.mjs (Seção A, MOTION-01) — estendido aqui com a Seção B"
provides:
  - "keyframe b3valuePulse + classe .b3 .value-pulse (display:inline-block, 120ms ease-out) em GlobalStyle()"
  - "sequenciamento de três saídas explícitas (executada/pendente/rejeitada) em confirmBuy/confirmSell via wrapper finalizar(), com portão pendente-primeiro/REDUCE_MOTION-depois"
  - "guarda de duplo envio em duas camadas: handler (if (!bm/sm || confirmado) return) + botão (disabled sob confirmado)"
  - "Seção B do guardião web/tests/test_fase23_motion.mjs (MOTION-02), 22 asserções novas"
  - "conserto do recorte por janela fixa de caracteres em test_historico_rejeitada.mjs (marcador, não offset)"
affects: [23-04]

tech-stack:
  added: []
  patterns:
    - "Wrapper finalizar() dentro do try: isola o commit de estado (setData/track/flash) do disparo do motor, permitindo um delay de apresentação (setTimeout) sem mexer no que o motor decidiu"
    - "Ordem de portão obrigatória documentada em comentário: condição de dado (pendente) SEMPRE antes de preferência de UI (REDUCE_MOTION) — pendente nunca pulsa, independente de motion"
    - "Guarda de duplo envio em duas camadas (handler + disabled) quando um modal deixa de desmontar imediatamente após a ação"

key-files:
  created: []
  modified:
    - web/src/App.jsx
    - web/tests/test_fase23_motion.mjs
    - web/tests/test_historico_rejeitada.mjs
    - web/tests/test_ordens_pendentes_ui.mjs
    - web/tests/test_carteira_lastro_ui.mjs

key-decisions:
  - "setData/track/flash movidos para dentro de finalizar(), disparado só depois do portão — corrige a armadilha do SellModal (if (!pos) return null desmontaria antes do pulso pintar numa venda TOTAL)"
  - "Cancelar e o toque no scrim ficam ativos durante a janela de 120ms: se o usuário fechar, finalizar() ainda roda e comita o estado — a ordem já executou no motor, só o pulso é truncado"
  - "setTimeout(finalizar, 120) sem cleanup: se o componente desmontar durante os 120ms, finalizar() precisa comitar o estado da ordem que já executou (perder o commit seria pior que um setState em componente desmontado)"
  - "Dois guardiões pré-existentes (test_ordens_pendentes_ui.mjs, test_carteira_lastro_ui.mjs) tinham asserções sobre a forma LITERAL de `disabled={...}` que o plano não mapeou — atualizados com nota datada, invariante preservado (ver Deviations)"

patterns-established:
  - "Guardião de MOTION-02 completo em test_fase23_motion.mjs, Seção B — isola handlers de objeto (nome: async () => {}) por par de marcadores início/fim, mesmo padrão dos guardiões vizinhos"

requirements-completed: [MOTION-02]

# Metrics
duration: ~90min
completed: 2026-09-06
---

# Phase 23 Plan 03: Pulso na confirmação de ordem (MOTION-02) Summary

**Confirmar uma compra/venda que EXECUTOU faz o valor pulsar (`scale(1→1.08→1)`, 120ms) antes do modal fechar; ordem pendente e rejeitada seguem sem pulso e sem atraso, via wrapper `finalizar()` com portão `pendente-primeiro / REDUCE_MOTION-depois` e guarda de duplo envio em duas camadas.**

## Performance

- **Duration:** ~90 min
- **Completed:** 2026-09-06
- **Tasks:** 3/3 completos
- **Files modified:** 5 (`web/src/App.jsx`, `web/tests/test_fase23_motion.mjs`, `web/tests/test_historico_rejeitada.mjs`, `web/tests/test_ordens_pendentes_ui.mjs`, `web/tests/test_carteira_lastro_ui.mjs`)

## Accomplishments

- `@keyframes b3valuePulse` + `.b3 .value-pulse{ display:inline-block; animation:b3valuePulse 120ms ease-out; }` em `GlobalStyle()`, imediatamente após o bloco de `card-enter` (plano 23-01) — nenhum `@media` novo, continuam existindo exatamente 2 blocos `prefers-reduced-motion`.
- `confirmBuy`/`confirmSell` reescritos com três saídas explícitas: **executada** (pulso 120ms → `finalizar()` → toast de sucesso + oferta de N3 na compra), **pendente** (`finalizar()` imediato, toast de pendente, sem pulso) e **rejeitada** (`catch` intocado, diff zero).
- `setData`/`track`/`flash` movidos para dentro de um wrapper `finalizar()`, disparado só depois do portão `if (s.pendente || REDUCE_MOTION)` — corrige a armadilha do `SellModal` (`if (!pos) return null` desmontaria o modal antes do pulso pintar, no caso mais comum: venda TOTAL).
- Guarda de duplo envio em duas camadas: handler (`if (!bm || bm.confirmado) return;` / `if (!sm || sm.confirmado) return;`) e botão (`disabled={!ok || !!buyModal.confirmado}` / `disabled={livre <= 0 || !!sellModal.confirmado}`) — o modal agora fica montado por ~120ms a mais, removendo o antídoto acidental que o desmonte imediato dava.
- `BuyModal`/`SellModal`: `className={.../* .confirmado */ ? "value-pulse" : undefined}` no valor da ordem (`{money(cost)}`/`{money(valor)}`), nunca no "Resultado estimado" (P&L) — `value-pulse` aparece em exatamente 3 lugares no arquivo (a regra CSS + os dois `className`).
- `catch` dos dois handlers com **diff zero** — ordem rejeitada não ganha nenhuma linha nova.
- Guardião `web/tests/test_fase23_motion.mjs` estendido com a Seção B (MOTION-02): 22 asserções novas, provadas com dentes (RED na Task 1 contra o `App.jsx` não modificado, GREEN na Task 3).
- Guardião `test_historico_rejeitada.mjs` consertado ANTES do refactor: janela fixa de caracteres (`+ 1200`/`+ 1700`) trocada por delimitação por marcador, com abort explícito se algum marcador sumir — provado verde contra o `App.jsx` ainda não modificado (conserto de ferramenta de recorte, não de contrato).
- Suíte canônica (`bash scripts/executar.sh --testes`) verde: 2021 testes de backend + 1 skip, **118/118** `web/tests/*.mjs`.

## Task Commits

1. **Task 1: Seção B do guardião (RED) e conserto do recorte do test_historico_rejeitada** - `b9bf303` (test)
2. **Task 2: Keyframe do pulso e o sequenciamento de três saídas em confirmBuy/confirmSell** - `78329a4` (feat)
3. **Task 3: O pulso nos dois modais e a suíte canônica verde** - `f47014a` (feat)

_Nenhum commit de metadados de plano separado — este SUMMARY é o registro final da execução (STATE.md/ROADMAP.md não são atualizados por esta task, conforme instrução do orquestrador)._

## Files Created/Modified

- `web/src/App.jsx` — keyframe/classe do pulso em `GlobalStyle()`; `confirmBuy`/`confirmSell` reescritos com `finalizar()`, portão de três saídas e guarda de duplo envio; `BuyModal`/`SellModal` com `className` condicional no valor e `disabled` reforçado no botão Confirmar.
- `web/tests/test_fase23_motion.mjs` — Seção B (MOTION-02), estendendo o arquivo do plano 23-01.
- `web/tests/test_historico_rejeitada.mjs` — recorte de `confirmBuy`/`confirmSell` trocado de janela fixa de caracteres para delimitação por marcador (Task 1, antes do refactor).
- `web/tests/test_ordens_pendentes_ui.mjs` — asserção do `disabled` do `BuyModal` atualizada para a nova forma literal (ver Deviations).
- `web/tests/test_carteira_lastro_ui.mjs` — asserção do `disabled` do `SellModal` atualizada para a nova forma literal (ver Deviations).

## Decisions Made

- **`setData` dentro de `finalizar()`, não antes:** com o estado comitado cedo, o `SellModal` desmontaria (`if (!pos) return null`) antes do pulso pintar numa venda TOTAL, e o `BuyModal` recalcularia `ok` com o caixa já debitado durante os 120ms de exibição. Consequência aceita: `track("trade_simulated", ...)` também atrasa 120ms no caso executado — a ordem relativa que os guardiões medem (`track` logo após `setData`) foi preservada, só o par inteiro atrasou.
- **Cancelar/scrim seguem ativos durante a janela de 120ms.** Se o usuário fechar o modal nesse intervalo, `finalizar()` ainda roda e ainda comita `setData`/toast — a ordem já executou no motor antes de qualquer coisa aqui; só o pulso visual é truncado. Não há como "cancelar" uma ordem que já foi aceita pelo `store.buy`/`store.sell`.
- **`setTimeout(finalizar, 120)` sem cleanup, deliberado.** Se o componente desmontar por qualquer outro motivo dentro dos 120ms (ex.: logout, troca de tela), `finalizar()` ainda precisa comitar o estado da ordem que já executou — perder esse commit seria pior que o warning inofensivo de `setState` em componente desmontado.
- **`value-pulse` nunca no "Resultado estimado" (P&L).** Pulsar um resultado de PnL daria destaque visual de sucesso a um número que pode ser prejuízo — violaria o princípio do `CLAUDE.md` de "resultados positivos e negativos apresentados sem manipulação visual".

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `web/node_modules` ausente + cache npm com permissão restrita no sandbox — instalado fora do sandbox, sem pacote novo**
- **Found during:** Task 2, ao rodar `cd web && npx vite build` (passo obrigatório do CLAUDE.md).
- **Issue:** `node_modules` ausente (isolamento de worktree). A primeira tentativa de `npm install` dentro do sandbox falhou com `EPERM` ao escrever em `/Users/acamerini/.npm/_cacache` e `ERROR: failed to copy trust settings of system certificate` — restrição de escrita do sandbox, não falha real de instalação.
- **Fix:** `npm install` executado com `dangerouslyDisableSandbox: true` (evidência de causa-sandbox: erro literal `EPERM`/`Operation not permitted` num diretório fora do allowlist de escrita). Reinstala exatamente as dependências já pinadas em `web/package-lock.json` — `git diff web/package.json web/package-lock.json` vazio depois.
- **Files modified:** nenhum arquivo versionado.
- **Verification:** `npx vite build` concluiu com código 0 (duas vezes, Task 2 e Task 3); `git diff web/package.json web/package-lock.json` vazio.
- **Committed in:** N/A (não gerou mudança versionada).

**2. [Rule 1 - Bug de guardião] `test_ordens_pendentes_ui.mjs` travava a forma literal `disabled={!ok}` do `BuyModal` — atualizado para a nova forma com nota datada**
- **Found during:** Task 3, ao rodar `bash scripts/executar.sh --testes` (varredura do plano não mapeou este consumidor).
- **Issue:** A asserção `/disabled=\{!ok\}/.test(buyModal)` (linha ~92-93) verificava a forma EXATA do atributo `disabled`. O Task 3 do próprio plano exige `disabled={!ok || !!buyModal.confirmado}` (segunda camada da guarda de duplo envio, item obrigatório do critério de aceite e do `<threat_model>` T-23-15) — a string exata deixou de existir, então o guardião falhava por medir a forma antiga, não por regressão de comportamento (o invariante que ele protegia — "status indisponível NÃO desabilita o Confirmar" — continua valendo, `statusIndisponivel` não entra em nenhum termo do `disabled`).
- **Fix:** Asserção atualizada para `/disabled=\{!ok \|\| !!buyModal\.confirmado\}/.test(buyModal) && !/disabled=\{[^}]*statusIndisponivel/.test(buyModal)` com comentário datado (2026-09-06) explicando a mudança — mesma classe de conserto que a Task 1 já aplicou em `test_historico_rejeitada.mjs` (regra do repositório: "guardião não se apaga, se atualiza com nota").
- **Files modified:** `web/tests/test_ordens_pendentes_ui.mjs`.
- **Verification:** `node web/tests/test_ordens_pendentes_ui.mjs` volta a passar (49 asserções); `bash scripts/executar.sh --testes` completo, verde.
- **Committed in:** `f47014a` (Task 3 commit).

**3. [Rule 1 - Bug de guardião] `test_carteira_lastro_ui.mjs` travava a forma literal `disabled={livre <= 0}` do `SellModal` — mesmo conserto**
- **Found during:** Task 3, mesma execução da suíte canônica que revelou o item 2.
- **Issue:** Mesma classe de problema: `/A\.confirmSell\}\s*disabled=\{livre\s*<=\s*0\}/` deixou de casar depois que o Task 3 acrescentou `|| !!sellModal.confirmado` ao `disabled` do botão de confirmar venda (item obrigatório do plano). Varredura de `<guardioes_existentes_que_este_plano_afeta>` também não mapeou este arquivo.
- **Fix:** Asserção atualizada para exigir `disabled={livre <= 0 || !!sellModal.confirmado}` com o mesmo comentário datado e a mesma justificativa (invariante "livre <= 0 desabilita" preservado, agora como um dos dois termos do `||`).
- **Files modified:** `web/tests/test_carteira_lastro_ui.mjs`.
- **Verification:** `node web/tests/test_carteira_lastro_ui.mjs` volta a passar (29 asserções); confirmado, antes de aplicar o conserto, que nenhum OUTRO consumidor de `disabled={!ok}`/`disabled={livre <= 0}` existia em `web/tests/*.mjs` ou `web/src/*.jsx` (sweep dedicado, ver nota abaixo).
- **Committed in:** `f47014a` (Task 3 commit).

---

**Total deviations:** 3 auto-fixed (1 bloqueio de ambiente — Rule 3, sem instalação de pacote novo; 2 guardiões desatualizados pela mudança literal do `disabled` — Rule 1, mesma classe já demonstrada e endorsada pelo próprio plano na Task 1)
**Impact on plan:** Os itens 2 e 3 são guardiões que o plano não mapeou em `<guardioes_existentes_que_este_plano_afeta>` — a varredura por `confirmBuy|confirmSell|setBuyModal|setSellModal|Custo estimado|Valor estimado` não cobria a forma literal `disabled={!ok}`/`disabled={livre <= 0}` isoladamente. Antes de aplicar o segundo conserto, foi feito um sweep dedicado (`grep -rn 'disabled={!ok}'` e `'disabled={livre <= 0}'` em todo `web/tests/` e `web/src/`) para garantir que nenhum terceiro consumidor sobrava — nenhum foi encontrado. Nenhum dos dois conserta afrouxa contrato: o invariante behavioral (status indisponível/qtyTravada não desabilitam; livre<=0/caixa insuficiente desabilita) foi reafirmado, só a literalidade da string mudou — mesma classe de "guardião não se apaga, se atualiza com nota" que o próprio plano demonstrou e prescreveu na Task 1 para `test_historico_rejeitada.mjs`. Sem scope creep: nenhuma linha de comportamento do produto foi alterada além do que o plano já mandava.

## Issues Encountered

Nenhum além dos três deviations acima (já documentados como Rule 1 ×2 / Rule 3 ×1). O comando `bash scripts/executar.sh --testes` também expôs um artefato de sandbox: `mktemp -d` falha silenciosamente sob o sandbox padrão, produzindo `TMPDIR_TESTES` vazio e tentativas de escrita em `/*.log` (raiz do filesystem) com `Operation not permitted` — corrigido rodando o comando com `dangerouslyDisableSandbox: true` (critério explícito de "evidência de falha causada pelo sandbox": erro literal de permissão numa escrita fora do allowlist). Não é um bug do produto nem do script — é o comportamento esperado do harness de sandbox quando `mktemp` não tem um diretório temporário writável disponível.

## User Setup Required

None - no external service configuration required.

## Pendente de verificação ao vivo (orquestrador)

Confirmado no `<environment_limitation_known_upfront>` deste plano e no do plano 23-01: subagentes executores não herdam ferramentas MCP de navegador (`mcp__computer-use__*`, `mcp__claude-in-chrome__*`) — bug upstream anthropics/claude-code#13898. Tudo o que é automatizável foi automatizado (guardião estático com 22 asserções novas provadas RED→GREEN, `vite build`, suíte canônica completa com 2021+118 testes). Dois dos três caminhos desta mudança dependem de ESTADO DE MERCADO que nenhum agente controla (pendente só ocorre com mercado fechado; executada só com mercado aberto). Roteiro numerado para o orquestrador, no formato de `21-04-SUMMARY.md`:

1. **Mercado ABERTO, compra que executa:** confirmar uma compra e observar o "Custo estimado" pulsar (crescer ~8% e voltar, `scale(1→1.08→1)`) antes de o modal fechar e o toast de compra aparecer. A oferta de stop/alvo (N3) deve continuar abrindo depois.
2. **Mercado ABERTO, venda que executa:** mesma conferência no "Valor estimado". Fazer especificamente uma **venda TOTAL** — é o caso da armadilha do `SellModal` (`if (!pos) return null`); se o modal sumir sem pulso, o `setData` ficou fora do `finalizar()`. (Guardião estático já prova que `setData` está DENTRO de `finalizar()` — este item confirma o comportamento ao vivo.)
3. **Mercado FECHADO (ou resposta com `pendente:true`):** o modal fecha na hora, com a pill/toast de PENDENTE, **sem nenhum pulso e sem atraso perceptível**. Este é o item que protege o princípio 9 do `CLAUDE.md` (ordem pendente ≠ ordem executada).
4. **Ordem rejeitada** (ex.: quantidade acima do caixa, ou provocar erro do servidor): nenhum pulso, toast de erro imediato, entrada de rejeição no histórico como antes. (`catch` com diff zero garante isso estaticamente; este item confirma ao vivo.)
5. **Duplo toque em Confirmar dentro da janela de 120ms:** **uma única ordem** no histórico e no caixa — conferir no histórico, não só na tela (a guarda de handler é a camada que realmente impede a segunda chamada a `store.buy`/`store.sell`; o `disabled` no botão é só a camada visível, um clique programático/muito rápido poderia contornar a UI mas não o handler). **Este item é o mais crítico da lista** — é o único T-23-15 (Elevation of privilege) do threat model que só um teste ao vivo confirma de verdade.
6. **`prefers-reduced-motion` ligado:** o modal fecha na hora, sem pulso e **sem os 120ms de espera** (o portão `REDUCE_MOTION` no JS existe exatamente para isso — animação zerada no CSS não zera o `setTimeout`). **Limitação de ferramenta já registrada em `20-HUMAN-UAT.md`**: nenhuma ferramenta deste ambiente expõe `Emulation.setEmulatedMedia` via CDP. Este item entra no MESMO `20-HUMAN-UAT.md` pendente — não foi criado documento de pendência novo, conforme decisão explícita do `23-CONTEXT.md`.

Item não medido é item registrado como ABERTO — nenhum dos seis itens acima foi declarado verificado neste plano.

## Next Phase Readiness

- `web/tests/test_fase23_motion.mjs` completo (Seções A + B) para o plano 23-04 (publicação) usar como gate de regressão.
- Nenhum bloqueio para o plano 23-04 — este plano não toca `web/src/pet/`, não publica (`bump` + `publicar-web.sh` são do 23-04) e não fez `git push`.
- Suíte canônica (`bash scripts/executar.sh --testes`) verde: 2021 testes de backend (1 skipped) + 118/118 `web/tests/*.mjs`.
- Ficam pendentes os 6 itens de verificação ao vivo listados acima — o item 5 (duplo toque) é o único que valida um mitigation de threat model (T-23-15) que a prova estática não alcança sozinha.

---
*Phase: 23-motion-com-proposito-e-ilustracao-unificada*
*Plan: 03*
*Completed: 2026-09-06*

## Self-Check: PASSED

- FOUND: web/src/App.jsx
- FOUND: web/tests/test_fase23_motion.mjs
- FOUND: web/tests/test_historico_rejeitada.mjs
- FOUND: web/tests/test_ordens_pendentes_ui.mjs
- FOUND: web/tests/test_carteira_lastro_ui.mjs
- FOUND: .planning/phases/23-motion-com-proposito-e-ilustracao-unificada/23-03-SUMMARY.md
- FOUND commit: b9bf303 (Task 1)
- FOUND commit: 78329a4 (Task 2)
- FOUND commit: f47014a (Task 3)
