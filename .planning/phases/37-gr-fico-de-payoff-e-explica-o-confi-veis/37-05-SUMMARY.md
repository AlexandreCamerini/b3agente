---
phase: 37-gr-fico-de-payoff-e-explica-o-confi-veis
plan: 05
subsystem: web/opcoes (SecaoAnalisar.jsx, SecaoComparar.jsx)
tags: [payoff, wiring, opcoes, checkpoint-humano, publicacao]

# Dependency graph
requires:
  - phase: 37-01
    provides: "dominio/segmentos anexados a proposta()/possibilidades() em options_mcp_api.py"
  - phase: 37-02
    provides: "ExplicacaoPayoff.jsx (componente puro, EXPL-01/02/03) e chaves de copy"
  - phase: 37-03
    provides: "valorHoje no envelope de proposta()/possibilidades(), gate do 1o candidato"
  - phase: 37-04
    provides: "PayoffChart.jsx aceita dominio/segmentos/valorHoje, geometria corrigida (CHART-01/02/03)"
provides:
  - "SecaoAnalisar.jsx e SecaoComparar.jsx passam dominio/segmentos/valorHoje ao PayoffChart e renderizam ExplicacaoPayoff — CHART-01..05/EXPL-01..03 observáveis de ponta a ponta num app rodando (Task 1)"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Passthrough puro de props já validadas pelos planos 37-01/37-02/37-03/37-04 — zero lógica de índice/gate reimplementada no front (T-37-10: item.valorHoje repassado como está, o backend já decide quem recebe a chave)"

key-files:
  created: []
  modified:
    - web/src/opcoes/SecaoAnalisar.jsx
    - web/src/opcoes/SecaoComparar.jsx

key-decisions:
  - "SecaoComparar.jsx não reintroduz gate por índice (i === 0) para o bloco Hoje — a fonte única do gate é o backend (chave item.valorHoje ausente vs. presente), conforme D-09/T-37-10 do 37-05-PLAN.md"
  - "CuradoriaEstruturas.jsx não foi tocado nesta task (D-09) — confirmado por git diff --stat, recebe a correção de geometria do 37-04 de graça via fallback local em PayoffChart.jsx, sem os blocos novos"

requirements-completed: []
# Nota: CHART-01..05/EXPL-01..03 estão implementados e observáveis num app
# rodando após a Task 1 (ver evidência abaixo), mas a marcação formal em
# REQUIREMENTS.md fica pendente da aprovação humana da Task 2 e da publicação
# da Task 3 — este SUMMARY é PARCIAL (ver "Status desta entrega").

# Metrics
duration: "~35min (Task 1) + tempo do checkpoint (Task 2, em aberto)"
completed: null
---

# Phase 37 Plan 05: Wiring do gráfico/explicação em Analisar e Comparar + checkpoint humano Summary

**`SecaoAnalisar.jsx`/`SecaoComparar.jsx` passam a passar `dominio`/`segmentos`/`valorHoje` ao `PayoffChart` corrigido (Plano 37-04) e a renderizar `<ExplicacaoPayoff/>` (Plano 37-02) — a onda de fechamento que torna CHART-01..05/EXPL-01..03 observáveis de ponta a ponta nos dois consumidores reais que um usuário vê.**

## Status desta entrega

**PARCIAL — Task 1 completa e commitada. Task 2 (checkpoint humano bloqueante) foi alcançada, com toda a evidência automatizada colhida e o roteiro apresentado, mas AINDA NÃO tem o "aprovado" explícito do Alex nesta conversa. Task 3 (bump + publicação) NÃO rodou — por desenho, só pode rodar depois da aprovação, e não nesta mesma invocação do executor (checkpoint bloqueante represa a publicação da FASE INTEIRA).**

Este SUMMARY documenta o que foi feito e serve de ponto de partida para a continuação (fresh agent) depois que o Alex responder ao checkpoint.

## Performance

- **Duration:** ~35min (Task 1)
- **Tasks:** 1/3 completa (Task 1); Task 2 alcançada e aguardando resposta humana; Task 3 não iniciada
- **Files modified:** 2

## Accomplishments (Task 1)

- `SecaoAnalisar.jsx`: `import ExplicacaoPayoff from "./ExplicacaoPayoff.jsx"`; `<PayoffChart>` ganha `dominio={proposta.dados.dominio}`, `segmentos={proposta.dados.segmentos}`, `valorHoje={proposta.dados.valorHoje}`; `<ExplicacaoPayoff segmentos=... spot=... razao=... cp={cp} />` renderizado logo após `<RazaoGanhoPerda>`, antes de `<Pernas>`
- `SecaoComparar.jsx`: mesmo import; dentro do `.map((item) => ...)`, `<PayoffChart>` ganha as mesmas 3 props lendo de `item.*`; `<ExplicacaoPayoff>` renderizado após `<RazaoGanhoPerda>`, antes de `<Cenarios>` — sem nenhuma lógica de índice própria (o backend já decide, via presença/ausência de `item.valorHoje`, quem recebe o bloco Hoje)
- `CuradoriaEstruturas.jsx` confirmado intocado por `git diff --stat` (D-09)

## Task Commits

1. **Task 1: wiring de dominio/segmentos/valorHoje + ExplicacaoPayoff** - `e62e231` (feat)

## Files Created/Modified

- `web/src/opcoes/SecaoAnalisar.jsx` — import de `ExplicacaoPayoff`; props novas no `PayoffChart`; `<ExplicacaoPayoff>` renderizado
- `web/src/opcoes/SecaoComparar.jsx` — idem, por item da lista de possibilidades

## Decisions Made

Ver `key-decisions` no frontmatter.

## Deviations from Plan

Nenhuma — Task 1 executada exatamente como especificada (passthrough puro de props, sem transformação, sem gate por índice reintroduzido).

## Issues Encountered

- **Falsos-positivos de sandbox na primeira rodada da suíte canônica**: `bash scripts/executar.sh --testes` dentro do sandbox padrão reportou 27 falhas de backend (`test_benchmark_ibov.py`, `test_yahoo_*`, `test_fase3_kill_switch_duracao.py`, etc.), todas com `PermissionError` — padrão já documentado no projeto ("sandbox mente", memória `worktree-test-setup.md`). Rerodada fora do sandbox (`dangerouslyDisableSandbox: true`) confirmou **2973 pytest passed, 0 failed** + **156/156 `.mjs`**, idêntico à baseline do Plano 37-04. Nenhuma das 27 falhas tem relação com os 2 arquivos desta task (ambos puramente frontend/JSX).
- **Backend/Vite não sobem com bind em `0.0.0.0` dentro do sandbox padrão** (`EPERM`/`operation not permitted` ao dar `listen`) — mesma classe de restrição de rede do sandbox, não falha de configuração do projeto. Resolvido subindo os dois com `dangerouslyDisableSandbox: true`, confirmado por HTTP antes de apresentar o roteiro da Task 2 (ver seção Verificação abaixo).

## User Setup Required

Nenhum novo — o checkpoint da Task 2 pede só a leitura visual do Alex, sem nenhuma configuração.

## Known Stubs

Nenhum. As props novas (`dominio`/`segmentos`/`valorHoje`) são passthrough puro de dados já produzidos pelo backend (37-01/37-03); `ExplicacaoPayoff` é componente puro já testado isoladamente (37-02).

## Threat Flags

Nenhum achado de superfície nova. T-37-10 (gate de índice divergente em `SecaoComparar.jsx`) mitigado por desenho: nenhuma lógica de índice foi adicionada, `item.valorHoje` é repassado como está.

## Verificação (Task 1 + precondição automatizada da Task 2)

- `git diff --stat` (contra o HEAD anterior a este plano): `CuradoriaEstruturas.jsx` NÃO aparece — confirmado
- `grep -n "import ExplicacaoPayoff"` / `grep -n "dominio={"` / `grep -n "<ExplicacaoPayoff"` — presentes nos dois arquivos
- `cd web && npx vite build` — exit 0, 113 módulos, sem erro de sintaxe
- `bash scripts/executar.sh --testes` fora do sandbox — **2973 pytest passed / 5 skipped / 3 xfailed / 0 failed** + **156/156 `.mjs`**, exit 0
- Backend (`uvicorn app.main:app --host 0.0.0.0 --port 8787`) e Vite (`npm run dev -- --host --port 5174`) subidos DIRETAMENTE (não pelo launcher `scripts/executar.sh` sem argumentos, que trava neste host — achado de ambiente já registrado em STATE.md), confirmados por HTTP:
  - `curl http://localhost:8787/api/health` → `{"ok":true,"build":"F10-20260921-01"}` (carimbo ANTERIOR ao bump — esperado, bump só na Task 3)
  - `curl http://localhost:5174/` → HTTP 200
  - `curl http://localhost:5174/api/health` → `{"ok":true,"build":"F10-20260921-01"}` (proxy dev do Vite para o backend confirmado funcionando)
- Servidores deixados NO AR (não encerrados) para o Alex poder rodar o roteiro imediatamente: **app em `http://localhost:5174`**, backend proxiado através dele.

## Next Phase Readiness

- **Task 2 (checkpoint humano bloqueante) alcançada e ainda ABERTA** — ver mensagem de checkpoint devolvida ao orquestrador nesta mesma resposta, com o roteiro de 7 passos na íntegra.
- **Task 3 (bump + publicação) NÃO deve rodar nesta mesma invocação do executor** — só numa continuação fresca, depois do "aprovado" explícito do Alex confirmado pelo orquestrador.
- Nenhum push a `origin` foi feito. Commit `e62e231` é local, na branch `v2/interacao-estrutural`.

---
*Phase: 37-gr-fico-de-payoff-e-explica-o-confi-veis*
*Status: PARCIAL — aguardando checkpoint humano da Task 2*

## Self-Check: PASSED

- FOUND: `.planning/phases/37-gr-fico-de-payoff-e-explica-o-confi-veis/37-05-SUMMARY.md`
- FOUND: `e62e231` (Task 1)
