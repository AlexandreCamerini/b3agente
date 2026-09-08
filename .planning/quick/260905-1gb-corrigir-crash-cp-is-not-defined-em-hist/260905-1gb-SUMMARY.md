---
phase: quick-260905-1gb
plan: 01
subsystem: front-web
tags: [bugfix, crash, historico, guardiao]

requires: []
provides:
  - "web/src/App.jsx:4617 — HistoricoScreen usa ctx.cp.vazioHistorico (antes: variável livre cp.vazioHistorico, ReferenceError)"
  - "web/tests/test_historico_cp_escopo.mjs — guardião estático que assevera ausência de referência livre a cp. dentro do recorte de HistoricoScreen"
affects: [historico-de-operacoes, portfolio]

tech-stack:
  added: []
  patterns:
    - "Guardião estático (varredura de fonte via regex sobre o recorte da função, comentários removidos antes do regex) no padrão dos demais web/tests/*.mjs deste repo — sem DOM, sem runtime"

key-files:
  created:
    - web/tests/test_historico_cp_escopo.mjs
  modified:
    - web/src/App.jsx
    - web/src/version.js
    - server/app/main.py
    - server/web_dist/**

key-decisions:
  - "Fix mínimo de 1 linha (cp.vazioHistorico → ctx.cp.vazioHistorico), sem tocar em mais nada do componente — já era o único ponto do arquivo com referência livre a cp; as ~40 outras ocorrências no arquivo são parâmetro desestruturado ou ctx.cp corretos."
  - "Guardião roda RED antes do fix (falha comprovada) para não virar teste decorativo — hábito já registrado em memória deste projeto (fewer-permission-prompts/tdd)."
  - "Publicação incluída no mesmo quick task (bump.sh → publicar-web.sh → suíte de novo) — guardrail do repo: mudança em web/src/ sem publicação fica testada e nunca vai ao ar."
  - "Checkpoint humano bloqueante (roteiro de repro ao vivo) executado pelo orquestrador da sessão, não pelo executor: o cenário (mercado fechado + 1 ordem pendente + histórico vazio) não depende de horário de pregão real, diferente dos checkpoints pendentes das Fases 17/18/19 — não havia razão para adiar."
  - "Nenhum git push para origin em nenhum momento — branch v2/interacao-estrutural segue com os checkpoints humanos das Fases 17/18/19 intocados e não aprovados."

requirements-completed: []

duration: ~25min (planner + executor + verificação ao vivo do orquestrador)
completed: 2026-09-05
status: complete
---

# Quick Task 260905-1gb: Corrigir crash cp is not defined em HistoricoScreen, Summary

## O que foi feito

`HistoricoScreen` (`web/src/App.jsx`) quebrava com `ReferenceError: cp is not
defined` sempre que a conta tinha ≥1 ordem pendente e zero operações
executadas no histórico — exatamente o estado de quem compra com o mercado
fechado. Achado ao vivo durante uma auditoria de design nesta mesma sessão.

Causa: linha 4617 usava a expressão livre `cp.vazioHistorico` — `cp` nunca é
desestruturado no componente (só `const { data, A } = ctx;`); todas as outras
~40 referências ao vocabulário no arquivo usam corretamente `ctx.cp.*` ou
recebem `cp` como parâmetro/prop desestruturado.

## Como foi corrigido

1. **RED**: `web/tests/test_historico_cp_escopo.mjs` criado primeiro — varre
   o recorte de `HistoricoScreen` (com comentários removidos) e falha se
   houver qualquer `cp.` sem o prefixo `ctx.` antes, mais um assert de
   sanidade (`ctx.cp.ordemPendentePill` precisa estar presente, para o
   recorte nunca vir vazio e o guardião virar decorativo). Confirmado falhando
   contra o código com o bug.
2. **GREEN**: troca de `cp.vazioHistorico` por `ctx.cp.vazioHistorico` na
   linha 4617. Guardião passa a verde; nenhuma outra linha tocada.
3. **Publicação**: `scripts/bump.sh` (BUILD_ID `F10-20260904-01` →
   `F10-20260905-01`) → `scripts/publicar-web.sh` (republica
   `server/web_dist`, sincroniza `SERVER_BUILD_ID` em `server/app/main.py`).
4. **Suíte canônica** rodada duas vezes (antes e depois da publicação):
   `bash scripts/executar.sh --testes` → **2021 passed, 1 skipped** (backend)
   + todos os `web/tests/*.mjs` verdes, incluindo o guardião novo.

## Verificação ao vivo (checkpoint humano)

Reproduzido o cenário exato que antes quebrava:
1. Conta existente com 1 ordem pendente (B3SA3, 100 cotas, `COMPRA`,
   `PENDENTE`, R$ 1.737,00 reservado) e zero operações no histórico.
2. Portfólio → "Ver histórico de operações".
3. **Antes do fix**: ErrorBoundary "Algo saiu do lugar" /
   `ReferenceError: cp is not defined` (confirmado nesta mesma sessão, antes
   de abrir o quick task).
4. **Depois do fix**: tela abre normalmente — seção "Pendentes" com a ordem
   e o pill âmbar `PENDENTE`, seguida do estado vazio "Nenhuma operação
   ainda" / "Suas compras e vendas simuladas aparecerão aqui." (texto do
   Modo Estudo, via `ctx.cp.vazioHistorico`). Console sem
   `ReferenceError`/erro de render — só ruído de reconexão do HMR do Vite
   (`ws://localhost:5174/`), não relacionado ao bug.

**Aprovado.**

## Known Gaps

- Nenhum. Escopo era estritamente a linha 4617; nenhum outro defeito
  correlato foi tocado ou descoberto durante a correção.

## Nenhum push para origin

Confirmado por grep em `bump.sh`/`publicar-web.sh` que nenhum dos dois
scripts executa `git push`. Os checkpoints humanos bloqueantes das Fases
17/18/19 (registrados em `.planning/STATE.md` e
`.planning/notes/checkpoints-pendentes-fase-17-18-19.md`) seguem intocados e
não aprovados — este fix não os destrava.
