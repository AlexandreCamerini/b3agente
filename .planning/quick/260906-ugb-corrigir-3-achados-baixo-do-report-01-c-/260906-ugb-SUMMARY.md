---
phase: quick-260906-ugb
plan: 01
subsystem: ui, kb
tags: [accessibility, aria, react, kb, didatica, boris]

# Dependency graph
requires: []
provides:
  - "aria-describedby condicional ligando o botão \"Executar (vende no stop/alvo)\" desabilitado ao parágrafo que explica o gate (AgenteScreen)"
  - "verbete setup-ifr2 da KB nomeando o princípio de reversão à média no texto educacional, buscável pelo termo"
  - "reverificação documentada de C-28 (achado já resolvido antes desta sessão, sem mudança de código)"
affects: [backlog-achados-baixo-report-01, kb-didatica]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "aria-describedby condicional via ternário (desabilitado ? id : undefined) para não vazar o atributo no botão que nunca fica desabilitado"

key-files:
  created: []
  modified:
    - web/src/App.jsx
    - web/tests/test_agente_modo_estudo_ui.mjs
    - server/app/kb.py
    - .planning/STATE.md
    - .planning/PROJECT.md

key-decisions:
  - "Desvio deliberado do pedido literal: adicionado só o termo acentuado \"reversão à média\" à tupla de busca do setup-ifr2, NÃO a variante sem acento — kb._pontuar normaliza (remove acento) antes de casar, então as duas formas colidiriam no mesmo match e dobrariam a pontuação (17+17=34 em vez de 17), inflando artificialmente o rank de setup-ifr2 em kb.buscar(). Reversível em uma linha se preferir a forma literal."
  - "C-28 não gerou nenhuma mudança de código: reverificação de 2026-09-06 confirmou que os 2 pontos de `appMode || \"estudo\"` cru citados no achado original já não existem — sumiram como efeito colateral do refactor FIX-C21, anterior a esta sessão. Documentado como achado fechado, não como item pulado."

requirements-completed: [REPORT-01-C18, REPORT-01-C08, REPORT-01-C28]

# Metrics
duration: ~50min
completed: 2026-09-07
---

# Quick Task 260906-ugb: Corrigir 3 achados Baixo do REPORT-01 Summary

**aria-describedby liga o botão "Executar" desabilitado à sua explicação (C-18); verbete setup-ifr2 da KB nomeia reversão à média (C-08); C-28 reverificado e confirmado já resolvido, sem mudança de código.**

## Performance

- **Duration:** ~50min
- **Started:** 2026-09-07T00:35:00Z (aprox.)
- **Completed:** 2026-09-07T01:23:32Z
- **Tasks:** 3/3 completed
- **Files modified:** 5 (2 código de produto, 1 teste, 2 planejamento)

## Accomplishments
- Leitor de tela que aterrissa no botão "Executar (vende no stop/alvo)" desabilitado agora ouve, via `aria-describedby`, a explicação de que o recurso é do Modo Operador — sem depender de varrer o resto do card.
- Verbete `setup-ifr2` da KB nomeia explicitamente o princípio geral de reversão à média antes de detalhar a mecânica do RSI(2)/SMA200, e passa a ser encontrável pelo termo "reversão à média" em `kb.buscar()`.
- C-28 reverificado contra o código atual e confirmado como já resolvido antes desta sessão — nenhuma linha mudou por causa dele.
- Suíte canônica completa (`bash scripts/executar.sh --testes`) verde: 2021 passed/1 skipped no pytest + todos os `web/tests/*.mjs` OK. `npx vite build` em `web/` sem erro.

## Task Commits

Cada task foi commitada atomicamente:

1. **Task 1: C-18 — ligar o botão "Executar" desabilitado à sua explicação (aria-describedby)** - `c0c1e2e` (fix)
2. **Task 2: C-08 — nomear o princípio de reversão à média no verbete setup-ifr2** - `1e75cc5` (fix)
3. **Task 3: suíte canônica completa + fechar as 3 pendências em STATE.md e PROJECT.md** - `d92cadd` (docs)

**Plan metadata:** commit final feito pelo orquestrador (fora deste executor).

## Files Created/Modified
- `web/src/App.jsx` - `AgenteScreen`: `id="executar-gate-hint"` no `<p>` de explicação + `aria-describedby={desabilitado ? "executar-gate-hint" : undefined}` no botão "Executar", comentário `FIX-C18 (2026-09-06)` datado
- `web/tests/test_agente_modo_estudo_ui.mjs` - 2 asserções novas (`id="executar-gate-hint"`, forma ternária exata do `aria-describedby`), nenhuma assercão existente alterada
- `server/app/kb.py` - verbete `setup-ifr2`: termo `"reversão à média"` adicionado à tupla `termos` (só a forma acentuada), 2 frases novas no início do texto `"educacional"` nomeando o princípio; texto `"operador"` intocado (byte-idêntico)
- `.planning/STATE.md` - tabela "Deferred Items" atualizada (9→6 achados Baixo restantes, C-08/C-18/C-28 documentados); linha nova na tabela "Quick Tasks Completed"
- `.planning/PROJECT.md` - item da seção `### Active` reduzido aos 6 achados restantes; nova entrada na seção `### Validated` cobrindo os 3 achados desta task

## Decisions Made

1. **Só o termo acentuado, não os dois.** A instrução original pedia `"reversão à média"` E `"reversao a media"` na tupla `termos`. `kb._pontuar` roda `_normalizar()` (NFD + descarta categoria Unicode `Mn`, remove acento, baixa caixa) em cada termo antes de casar contra a query — as duas formas normalizam para a mesma string. Adicionar as duas faria `_pontuar` somar `len(t)` duas vezes pelo mesmo match (17+17=34 em vez de 17), inflando o rank de `setup-ifr2` contra outros verbetes em `kb.buscar()` e barateando artificialmente o corte `_CONFIANCA_MIN` de `kb.resolver()`. Pontuação determinística inflada é o tipo de efeito colateral silencioso que o Princípio 5 do CLAUDE.md do projeto rejeita (cálculo determinístico, sem distorção). **Reversível em uma linha** se o Alex preferir a forma literal: basta adicionar `"reversao a media"` à tupla, aceitando o double-count.
2. **C-28 documentado como achado fechado por reverificação, não como item pulado.** `grep -n 'appMode || ' web/src/App.jsx` retorna vazio — os 2 pontos citados no REPORT-01 original (linhas 7989 e 9071, hoje) já leem a variável canônica `appMode`, normalizada pelo ternário seguro, ambos com comentário `FIX-C21: lê a fonte única`. O passthrough cru morreu como efeito colateral do refactor FIX-C21, antes desta sessão. Nenhuma linha de código mudou por causa de C-28 — só a documentação em STATE.md/PROJECT.md registra o achado como resolvido.

## Deviations from Plan

**Um desvio deliberado, já declarado no próprio plano (`<deviation_declared>`) e não uma descoberta de execução:**

### Desvio declarado (não é um Rule 1-4 — é uma decisão de planejamento já registrada)

**Termo de busca "reversão à média": só a forma acentuada, não as duas**
- **Onde:** Task 2 (`server/app/kb.py`, tupla `termos` do verbete `setup-ifr2`)
- **Instrução original:** adicionar tanto `"reversão à média"` quanto `"reversao a media"`.
- **O que foi feito:** só `"reversão à média"` foi adicionado.
- **Motivo:** ver "Decisions Made" item 1 acima — double-count de pontuação em `kb._pontuar` por causa da normalização Unicode que já remove o acento antes de casar.
- **Reversão:** adicionar `"reversao a media"` à tupla é suficiente se o Alex preferir a forma literal.
- **Commit:** `1e75cc5`

---

**Total deviations:** 1 (desvio de planejamento pré-declarado, não uma descoberta de execução via Rules 1-4)
**Impact on plan:** Nenhum scope creep — o desvio é uma restrição técnica documentada no próprio PLAN.md antes da execução, seguida à risca pelo executor.

## Issues Encountered

Nenhum bloqueio real. Uma nota operacional: o sandbox padrão do ambiente de execução bloqueia `mktemp -d` (usado internamente por `scripts/executar.sh --testes` para capturar logs por teste), retornando "Operation not permitted" porque o diretório default do `mktemp` fica fora do allowlist de escrita do sandbox. A suíte foi re-executada com o sandbox desabilitado para este comando específico (evidência clara de restrição de sandbox, não de falha de teste) e passou integralmente: 2021 passed/1 skipped (pytest) + todos os `web/tests/*.mjs` OK, exit code 0.

## User Setup Required

None - nenhuma configuração de serviço externo necessária. Sem deploy, sem bump de build, sem `publicar-web.sh` (fix de fonte simples, conforme escopo do plano).

## Next Phase Readiness

- Backlog de achados Baixo do REPORT-01 reduzido de 9 para 6 (C-06, C-07, C-09, C-10, C-17, C-29 restantes, ainda sem fase mapeada).
- As linhas citadas no REPORT-01 original (18/08/2026) estavam defasadas para os 3 achados desta task; as linhas reais foram reverificadas em 2026-09-06 (registradas em `<pre_verified_facts>` do plano) antes de qualquer edição.
- Nenhum bloqueio para as próximas quick tasks ou fases — mudanças são pontuais e sem dependência de infraestrutura nova.

---
*Phase: quick-260906-ugb*
*Completed: 2026-09-07*

## Self-Check: PASSED

Todos os arquivos citados foram confirmados no disco (`web/src/App.jsx`,
`web/tests/test_agente_modo_estudo_ui.mjs`, `server/app/kb.py`,
`.planning/STATE.md`, `.planning/PROJECT.md`, este SUMMARY.md). Os 3 commits
de task (`c0c1e2e`, `1e75cc5`, `d92cadd`) foram confirmados em
`git log --oneline`, em ordem, em cima do commit de plano `a1e2cfe`.
