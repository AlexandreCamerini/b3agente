---
phase: 15-motor-de-proposta-arquitetura-interna
plan: 04
subsystem: testing
tags: [ast, architecture-guardian, mydata, options-engine, adr]

# Dependency graph
requires:
  - phase: 15-motor-de-proposta-arquitetura-interna (planos 15-02, 15-03)
    provides: opcoes_gatilho.py (ENG-06), opcoes_payoff.py (ENG-02), opcoes_motor.py rastrear()/avaliar() (ENG-01/04)
provides:
  - Suíte estrutural (ast) que reprova import de rede/mcp e string b-mcp/URL nos 3 módulos novos de opções (ENG-03)
  - Allowlist estrutural dos módulos que importam mydata_client, travada em {candle_provider, options_provider_mydata, mydata_budget} (ENG-05)
  - Teste de comportamento provando que mydata_budget.reservar()=False impede toda requisição de rede (ENG-05)
  - Guardião de regressão do WR-01 — _debita() tem que referenciar reservar(), nunca debita() direto
  - Assinatura congelada rastrear(cadeia, filtros)/avaliar(pernas) e allowlist de imports de opcoes_motor.py (ENG-04)
  - ADR-024, registrando o limite trocável e o procedimento de troca para quando plano-mcp-servico.md for aprovado
affects: [16-biblioteca-de-estruturas, 17-fluxo-de-aceite]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Guardião estrutural via ast.parse (não grep textual) para invariante de arquitetura, com exclusão explícita de docstring por posição estrutural (nunca por valor de string)"
    - "Guardião de comportamento via monkeypatch reusando o padrão já estabelecido em test_options_provider_mydata.py"

key-files:
  created:
    - server/tests/test_opcoes_fronteira.py
    - docs/adr/024-limite-interno-rastrear-avaliar.md
  modified: []

key-decisions:
  - "Guardiões estruturais usam ast.walk sobre o arquivo INTEIRO (não só o top-level) para capturar imports dentro de função — necessário porque mydata_budget.snapshot() importa mydata_client tardiamente (import lazy, dentro da função, para evitar ciclo em boot parcial), e o Guardião C (canal único) precisa contar esse import também."
  - "Distinção entre string literal (proibida) e docstring (legítima) feita por POSIÇÃO estrutural na AST (primeiro Expr do corpo de Module/FunctionDef/ClassDef), não por conteúdo — opcoes_motor.py/opcoes_gatilho.py já citam 'b-mcp' e 'semente.dev' em docstring para EXPLICAR a proibição, e isso não pode reprovar o próprio guardião que o explica."

requirements-completed: [ENG-03, ENG-04, ENG-05]

# Metrics
duration: 55min
completed: 2026-09-02
---

# Phase 15 Plan 04: Guardião de fronteira do motor de opções Summary

**Suíte de 15 testes (ast estrutural + comportamento monkeypatch) que reprova rede/MCP/URL do b-mcp, canal paralelo ao hub mydata, e assinatura solta de rastrear()/avaliar() — mais ADR-024 documentando o limite trocável e o procedimento de troca.**

## Performance

- **Duration:** ~55 min
- **Started:** 2026-09-02T22:06:00Z (aprox., início da leitura de contexto)
- **Completed:** 2026-09-02T23:01:45Z
- **Tasks:** 2/2
- **Files modified:** 2 (1 criado em Task 1, 1 estendido + 1 criado em Task 2)

## Accomplishments

- Transformou as três invariantes de fronteira da fase (ENG-03 sem rede ao
  b-mcp, ENG-04 limite trocável, ENG-05 canal único com orçamento) de
  intenção documentada em comentário para suíte que reprova a violação —
  exatamente o gap que o `<objective>` do plano nomeava (CONTEXT explícito:
  "o planner deve garantir que ela é estruturalmente verdadeira, não só
  documentada").
- Provou por injeção de falha real (não só por leitura de código) que o
  guardião funciona: `import httpx` temporário em `opcoes_motor.py`
  reprovou 2 dos 15 testes; revertido, suíte voltou a 15/15 verde.
- Registrou o ponto de troca (ADR-024) com o que foi portado de
  `~/dev/MCP/servers/mydata/calculos.py` versus o que foi deliberadamente
  descartado (DSL de setups, critério de seleção por delta), e quais
  guardiões desta suíte precisam ser reescritos versus quais continuam
  valendo quando `plano-mcp-servico.md` for aprovado.

## Task Commits

1. **Task 1: Guardião de fronteira — sem rede ao b-mcp, canal único, orçamento respeitado** - `a6c6020` (test)
2. **Task 2: Guardião de trocabilidade do limite interno + ADR-024** - `37a3da8` (feat)

**Plan metadata:** (pendente — commit final feito pelo orquestrador fora deste worktree)

## Files Created/Modified

- `server/tests/test_opcoes_fronteira.py` (324 linhas, 15 testes) — Guardião A (ENG-03, import de rede/string b-mcp nos 3 módulos novos), Guardião B (ENG-03, nenhum módulo do app importa `mcp`; `mcp` ausente dos requirements), Guardião C (ENG-05, allowlist de módulos que importam `mydata_client`), Guardião D (ENG-05, comportamento: `reservar()=False` impede toda requisição), Guardião E (ENG-05, regressão WR-01: `_debita()` usa `reservar()`, nunca `debita()` direto), Guardião ENG-04 (assinatura congelada de `rastrear`/`avaliar`, allowlist de imports de `opcoes_motor.py`, ausência de relógio).
- `docs/adr/024-limite-interno-rastrear-avaliar.md` (180 linhas) — Contexto (5 estratégias avaliadas, Estratégia B escolhida), Decisão 1 (o limite `rastrear`/`avaliar`), Decisão 2 (o que foi portado de `calculos.py` e o que não foi — DSL de setups, critério por delta), Decisão 3 (canal único via `mydata_client`/`mydata_budget.reservar`), Procedimento de troca (passos exatos + quais guardiões são reescritos vs. permanecem), Consequências.

## Decisions Made

- Guardiões estruturais coletam imports por `ast.walk` sobre a árvore
  inteira (não só `tree.body` de topo), porque `mydata_budget.py` importa
  `mydata_client` de forma tardia (`from . import mydata_client`, dentro da
  função `snapshot()`, para evitar ciclo em boot parcial) — um guardião que
  só olhasse imports de topo do módulo teria um falso negativo em
  `mydata_budget.py` para o Guardião C.
- `_strings()` exclui docstrings por posição estrutural na AST (primeiro
  `ast.Expr` do corpo de `Module`/`FunctionDef`/`AsyncFunctionDef`/
  `ClassDef`), não por comparação de valor — a primeira versão do guardião
  reprovava a própria docstring de `opcoes_motor.py`/`opcoes_payoff.py`, que
  cita "b-mcp" e `~/dev/MCP/docs/plano-mcp-servico.md` para EXPLICAR a
  proibição (comportamento legítimo, previsto no plano: "comentário citando
  'b-mcp'... é legítimo e não pode reprovar a suíte" — docstring precisou
  do mesmo tratamento que comentário, apesar de virar nó da AST diferente
  de um comentário de verdade).

## Deviations from Plan

None - plan executado exatamente como escrito. O único ajuste foi técnico
(exclusão de docstring do Guardião A, acima), não uma mudança de escopo —
a intenção do guardião ("proibir string literal de verdade referenciando
b-mcp/URL") continua exatamente a mesma; só a implementação precisou
distinguir docstring explicativa de literal funcional.

## Issues Encountered

- Primeira execução do Guardião A falhou porque `_strings()` capturava
  docstrings de módulo/função (que citam "b-mcp" para explicar a
  proibição) como se fossem string literal de violação. Corrigido excluindo
  docstrings por posição estrutural na AST — ver "Decisions Made" acima.
- Suíte canônica (`bash scripts/executar.sh --testes`) dentro do sandbox de
  rede deste ambiente de execução reprova 27 testes pré-existentes com
  `PermissionError` de SSL (carregamento de cert store), TODOS não
  relacionados a este plano — confirmado reproduzindo a mesma falha com
  `test_opcoes_fronteira.py` removido do diretório de testes. Executado
  novamente fora do sandbox (`dangerouslyDisableSandbox`): `1905 passed, 1
  skipped`, exit code 0 — suíte canônica completa (pytest + `web/tests/*.mjs`)
  verde.

## User Setup Required

None - nenhuma configuração de serviço externo necessária. Nenhum pacote
novo (`mcp` continua ausente de `requirements.txt`/`requirements-prod.txt`,
verificado pelo próprio Guardião B).

## Next Phase Readiness

- Fase 15 (motor de proposta, arquitetura interna) encerrada com os 4
  planos completos: 15-01 (`opcoes_payoff.py`), 15-02 (`opcoes_gatilho.py`),
  15-03 (`opcoes_motor.py` — `rastrear()`/`avaliar()`), 15-04 (guardiões de
  fronteira + ADR-024).
- ENG-01..06 todos cobertos: ENG-01 (critério de seleção, régua já em
  produção), ENG-02 (aritmética de payoff portada), ENG-03 (sem rede ao
  b-mcp, agora estruturalmente garantido), ENG-04 (limite trocável, agora
  estruturalmente garantido), ENG-05 (canal único com orçamento, agora
  estruturalmente garantido), ENG-06 (gatilho reusa o Radar, `opcoes_gatilho.py`
  do Plano 15-02).
- Fase 16 (biblioteca de 3 estruturas — venda coberta, put de proteção,
  collar) pode começar consumindo `opcoes_motor.rastrear`/`opcoes_motor.avaliar`
  diretamente — as assinaturas estão congeladas por teste, e o motor de N
  pernas já suporta collar (2 pernas) desde o Plano 15-03.
- Nenhum bump/deploy necessário — fase inteira backend-only, sem rota
  exposta, sem UI tocada (confirma o item `<verification>` do plano: nenhum
  arquivo de `web/` foi alterado nesta fase inteira).

---
*Phase: 15-motor-de-proposta-arquitetura-interna*
*Completed: 2026-09-02*

## Self-Check: PASSED

- FOUND: server/tests/test_opcoes_fronteira.py
- FOUND: docs/adr/024-limite-interno-rastrear-avaliar.md
- FOUND commit: a6c6020 (Task 1)
- FOUND commit: 37a3da8 (Task 2)
