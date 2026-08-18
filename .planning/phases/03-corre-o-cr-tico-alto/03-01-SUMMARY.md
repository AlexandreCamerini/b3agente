---
phase: 03-corre-o-cr-tico-alto
plan: 01
subsystem: ui
tags: [fastapi, react, brapi, yahoo, transparencia-de-dado, technical-panel]

requires: []
provides:
  - "GET /api/technicals/{ticker} devolve `source` (propagado do candle_cache, nunca inventado) e `degradado` (bool, orçamento brapi da fatia spot)"
  - "TechnicalModal declara a fonte real do dado (brapi/Yahoo/—), nunca mais uma string fixa incorreta"
  - "Qualificador visual (T.warn) quando o dado pode estar mais desatualizado que o habitual (TTL 3x)"
  - "FonteDadosScreen (admin-gated) mostra 'estado do orçamento: degradado (TTL 3×)' / 'normal'"
affects: [phase-4, phase-5]

tech-stack:
  added: []
  patterns:
    - "helper de módulo `_degradado_spot()` em main.py: try/except Exception → False, para indicador de orçamento nunca derrubar rota de usuário final"

key-files:
  created:
    - server/tests/test_fase3_proveniencia_technicals.py
    - web/tests/test_fase3_fonte_technicals.mjs
  modified:
    - server/app/technical_snapshot.py
    - server/app/main.py
    - web/src/App.jsx

key-decisions:
  - "Task 1 (backend): technical_snapshot.get() propaga hist.get('source') no dict de retorno; main.py ganha helper _degradado_spot() (False quando provedor != brapi ou quando o cálculo lança exceção)."
  - "Task 2 (frontend): linha de fonte do TechnicalModal lê data.source via FONTE_LABEL, fallback honesto '—'; qualificador em T.warn quando data.degradado; FonteDadosScreen ganha span 'estado do orçamento'."
  - "Deviation (Rule 2): acceptance criteria do plano exige `grep -c \"Yahoo Finance\" web/src/App.jsx` == 0 para o arquivo INTEIRO, não só a linha do TechnicalModal. Havia mais 2 ocorrências fora do escopo nomeado pelo plano (AboutModal linha ~363, validação de ticker no CatalogModal linha ~6104) — mesma classe de violação (citavam só o backup Yahoo como se fosse a única fonte, quando brapi é master desde ADR-008). Reescritas para citar brapi (principal) + Yahoo (backup), sem mudança de lógica, para satisfazer a acceptance criteria e corrigir a mesma falsidade em princípio 3."

patterns-established:
  - "'não sei' sobre estado de orçamento é sempre False, nunca uma invenção — princípio 4 do CLAUDE.md aplicado a um indicador secundário que não pode derrubar rota principal."

requirements-completed: [FIX-C11, FIX-C30]

duration: 12min
completed: 2026-08-18
---

# Phase 3 Plan 01: Proveniência real do dado + estado do orçamento visível Summary

**`/api/technicals/{ticker}` para de mentir a fonte do dado (Yahoo Finance fixo) e passa a expor `source`/`degradado` reais; TechnicalModal e FonteDadosScreen leem esses campos, fechando os 2 achados Crítico (C-11, C-30) do REPORT-01 que violavam o princípio 3 do CLAUDE.md.**

## Performance

- **Duration:** ~12 min (commits 20:22:43 → 20:28:51, mais leitura de contexto)
- **Started:** 2026-08-18T20:19:00-03:00 (aprox.)
- **Completed:** 2026-08-18T20:28:51-03:00
- **Tasks:** 2 (ambas TDD)
- **Files modified:** 3 (technical_snapshot.py, main.py, App.jsx) + 2 arquivos de teste novos

## Accomplishments

- `GET /api/technicals/{ticker}` agora devolve `source` (propagado sem invenção do `candle_cache.load()`) e `degradado` (bool, calculado com blindagem total contra exceção).
- O painel técnico do usuário final (`TechnicalModal`) declara a fonte real ("Fonte: brapi" / "Fonte: Yahoo" / "Fonte: —"), nunca mais a string fixa "Yahoo Finance" que estava ativamente errada quando o dado vinha da brapi.
- Quando o orçamento brapi está degradado (TTL 3×), o usuário final lê um aviso em âmbar na mesma linha da fonte, sem exposição de detalhes de orçamento/cota/limite (contrato do UI-SPEC).
- `FonteDadosScreen` (tela admin-gated) ganha a linha "estado do orçamento: degradado (TTL 3×)" / "normal".
- Dois guardiões novos travando a regressão: 6 casos no backend, 9 asserções no front (static source inspection).

## Task Commits

Each task was committed atomically:

1. **Task 1: Propagar `source` e expor `degradado` no payload de /api/technicals** - `be997cf` (feat)
2. **Task 2: Linha de fonte real no TechnicalModal + estado do orçamento em FonteDadosScreen** - `833216c` (feat)

_Nenhuma commit de plan-metadata separada — SUMMARY.md e commit final ficam a cargo do orquestrador, conforme instrução da execução._

## Files Created/Modified

- `server/app/technical_snapshot.py` - `get()` propaga `hist.get("source")` no dict de retorno (nunca um default inventado)
- `server/app/main.py` - novo helper `_degradado_spot()`; payload de `/api/technicals` ganha `source` e `degradado`
- `server/tests/test_fase3_proveniencia_technicals.py` - guardião novo (6 testes: propagação, ausência honesta, payload de rota, bool condicionado ao provedor, resiliência a exceção, leg admin de C-30)
- `web/src/App.jsx` - linha de fonte do `TechnicalModal` reescrita; `FonteDadosScreen` ganha span "estado do orçamento"; 2 disclaimers adicionais corrigidos (ver Deviations)
- `web/tests/test_fase3_fonte_technicals.mjs` - guardião novo (9 asserções, static source inspection)

## Decisions Made

- `_degradado_spot()` inteiramente dentro de `try/except Exception` — decisão do plano, reforçada pelo threat model T-03-03 (o indicador de orçamento nunca pode derrubar o painel técnico).
- Fallback honesto `"—"` quando `data.source` está ausente — nunca um provedor presumido (contrato do UI-SPEC, mitiga T-03-04).
- Qualificador de degradado deliberadamente não menciona orçamento/cota/mês/limite ao usuário final — só o efeito (dado mais velho), nunca a causa, conforme D-01/UI-SPEC Copywriting Contract.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality / correctness] Duas ocorrências adicionais de "Yahoo Finance" fora da linha nomeada pelo plano**

- **Found during:** Task 2 (verificação da acceptance criteria `grep -c "Yahoo Finance" web/src/App.jsx` == 0)
- **Issue:** O plano nomeia explicitamente só `App.jsx:1511-1513` (TechnicalModal) como alvo de edição, mas a acceptance criteria do próprio Task 2 exige zero ocorrências da string no arquivo INTEIRO. Duas outras ocorrências pré-existiam, não rastreadas em nenhum achado do REPORT-01 (confirmado por busca no arquivo — nem `AboutModal` nem `CatalogModal` aparecem em C-11 nem em qualquer outro C-NN): (a) `AboutModal` (~linha 363), disclaimer geral "As cotações vêm do Yahoo Finance..."; (b) `CatalogModal` (~linha 6104), "a existência é confirmada no Yahoo Finance" na validação de ticker novo na watchlist. Ambas citavam só o backup Yahoo como se fosse a única fonte — mesma classe de violação do princípio 3 que C-11 corrige (proveniência desatualizada desde a ADR-008, que tornou a brapi a fonte MASTER).
- **Fix:** Reescritas para citar as duas fontes reais — "brapi (fonte principal) e do Yahoo (backup)" no AboutModal; "provedor de cotações (brapi/Yahoo)" no CatalogModal. Nenhuma mudança de lógica, só copy.
- **Files modified:** `web/src/App.jsx`
- **Verificação:** `grep -c "Yahoo Finance" web/src/App.jsx` retorna 0; suíte web completa (`bash scripts/executar.sh --testes`) permanece verde.
- **Committed in:** `833216c` (parte do commit da Task 2)

---

**Total deviations:** 1 auto-fixed (Rule 2, 2 ocorrências no mesmo arquivo)
**Impact on plan:** Correção de copy pré-existente e não rastreada, na mesma classe de violação do achado que este plano fecha. Nenhuma mudança de lógica/comportamento, nenhum novo componente, nenhuma expansão de escopo funcional — necessária para a acceptance criteria literal do próprio plano.

## Issues Encountered

Nenhum arquivo `.venv` estava presente no worktree isolado (comum a agentes de worktree neste milestone — ver PROJECT.md Key Decisions) — usado o `.venv` do repositório principal (`/Users/acamerini/dev/bolsia/b3-agente/server/.venv/bin/python`) para rodar pytest a partir do diretório `server/` do worktree. `web/node_modules` também ausente — `npm install` rodado em `web/` antes da suíte, conforme já documentado em PROJECT.md como achado conhecido de worktree novo.

## User Setup Required

None - nenhuma configuração de serviço externo necessária.

## Next Phase Readiness

- `/api/technicals/{ticker}` está pronto para qualquer consumidor futuro (iOS nativo, outros painéis) ler `source`/`degradado` com o mesmo contrato.
- Verificação humana ao vivo (abrir o painel técnico e conferir "Fonte: brapi"/"Fonte: Yahoo", forçar a fatia spot acima de 80% e conferir o aviso âmbar; conferir a linha "estado do orçamento" em Perfil → Fonte de dados) fica para `/gsd:verify-phase`, conforme o próprio plano já delimitava.
- Nenhum bloqueio conhecido para a Fase 4/5.

---
*Phase: 03-corre-o-cr-tico-alto*
*Completed: 2026-08-18*

## Self-Check: PASSED

- FOUND: server/tests/test_fase3_proveniencia_technicals.py
- FOUND: web/tests/test_fase3_fonte_technicals.mjs
- FOUND commit be997cf
- FOUND commit 833216c
- Canonical suite (`bash scripts/executar.sh --testes`) exit 0
- `cd web && npx vite build` succeeded
- `grep -c "Yahoo Finance" web/src/App.jsx` == 0
