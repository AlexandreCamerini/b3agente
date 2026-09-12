---
phase: 24-opcoes-mcp-analise-e-setups
plan: 17
subsystem: admin
tags: [rbac, adr-013, adr-010, plano-comercial, auditoria, portal-admin, fastapi, react]

requires:
  - phase: 24-opcoes-mcp-analise-e-setups
    provides: "card Usuários e papéis (ADR-013) com rota gated, auditoria e confirmação já montados"
provides:
  - "POST /api/admin/users/{user_id}/plan — escrita do plano comercial da conta, sob usuarios.gerenciar, auditada"
  - "planosDisponiveis em GET /api/admin/users, derivado de plan.PLANOS_POR_ID"
  - "entidade user_plan em rbac.ENTIDADES_POR_PERMISSAO[usuarios.gerenciar]"
  - "controle de plano no card Usuários e papéis do portal admin"
  - "guardião de rota (23 casos) e guardião estático de portal (27 asserções)"
affects: [publicação do portal admin, deploy de backend, futura loja/IAP do ADR-010]

tech-stack:
  added: []
  patterns:
    - "eixo comercial e eixo de governança continuam em rotas separadas, por decisão, não por acaso"
    - "lista de ids servida pelo backend (planosDisponiveis), como gruposDisponiveis já fazia"

key-files:
  created:
    - server/tests/test_admin_plano_usuario.py
    - web/tests/test_admin_plano_ui.mjs
  modified:
    - server/app/main.py
    - server/app/rbac.py
    - server/app/db.py
    - server/app/plan.py
    - web-admin/src/App.jsx
    - web-admin/src/api.js

key-decisions:
  - "Mudar o próprio plano continua permitido e auditado — freio só aqui seria assimétrico com a rota de papéis ao lado"
  - "A lista de planos é servida pelo backend; nenhum id de plano escrito no fonte do portal (nem o fallback \"free\" que existia)"
  - "As TRÊS notas de \"sem override de plano nesta rodada\" foram atualizadas com a reversão datada, não apagadas"
  - "Botão do plano vigente marcado e desabilitado: reaplicar só produziria evento de auditoria sem mudança"

patterns-established:
  - "Reversão de decisão registrada no código: a nota antiga fica, a nova diz o que mudou e quando"
  - "404 de rota inexistente não conta como prova: o guardião exige o texto da rota, porque o catch-all também responde 404"

requirements-completed: ["pedido do Alex 2026-09-12 — mudar o plano do usuário pelo portal"]

duration: 45min
completed: 2026-09-12
---

# Phase 24 Plan 17: plano da conta pelo portal admin

**`POST /api/admin/users/{id}/plan` sob `usuarios.gerenciar`, com auditoria `user_plan`, e o controle no card "Usuários e papéis" — `pro` deixa de depender de edição direta no SQLite do container.**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-09-12T14:50:00Z (aprox.)
- **Completed:** 2026-09-12T15:35:00Z
- **Tasks:** 3
- **Files modified:** 8 (6 modificados + 2 criados)

## Accomplishments

- O plano de uma conta muda pelo portal, por rota gated e auditada. Antes a
  única porta era o SQLite do container (`scripts/plano-da-conta.sh`, criado
  nesta mesma sessão) — serve para a conta do dono e não para mais ninguém.
- A lista de planos tem fonte única: sai de `plan.PLANOS_POR_ID` na ordem de
  `_ORDEM_PLANO`, viaja em `planosDisponiveis` e a UI só a renderiza. Nenhum
  id de plano escrito no `main.py` nem no portal — inclusive o fallback
  `"free"` que a exibição tinha foi trocado por travessão.
- A reversão ficou **registrada**, em três lugares que afirmavam o contrário:
  a docstring de `POST .../roles`, `db.set_user_plan` e `plan.current_plan`.
  Nenhuma nota apagada; cada uma diz o que mudou e quando (2026-09-12).

## Task Commits

1. **Task 1: rota de escrita do plano, com auditoria** — `7099f0c` (feat)
2. **Task 2: o controle no card do portal** — `19a622b` (feat)
3. **Task 3: guardiões** — `4a9486f` (test)

## Files Created/Modified

- `server/app/main.py` — `_planos_disponiveis()` (fonte única, com fallback
  para plano que exista em `PLANOS_POR_ID` e falte em `_ORDEM_PLANO`);
  `planosDisponiveis` em `GET /api/admin/users`; rota nova
  `POST /api/admin/users/{user_id}/plan`; docstring da rota de papéis
  atualizada com a reversão datada.
- `server/app/rbac.py` — `ENTIDADES_POR_PERMISSAO["usuarios.gerenciar"]` ganha
  `"user_plan"`, com a nota de por que entrou.
- `server/app/db.py` — docstring de `set_user_plan` atualizada (a função ganhou
  chamador humano).
- `server/app/plan.py` — docstring de `current_plan` atualizada (o trecho "sem
  override manual nesta rodada" deixou de valer).
- `web-admin/src/api.js` — `userPlan(userId, plano)`.
- `web-admin/src/App.jsx` — `mudarPlano` com confirmação, fileira de botões de
  plano vinda de `data.planosDisponiveis`, rótulos nas duas fileiras, nota de
  topo com a reversão.
- `server/tests/test_admin_plano_usuario.py` — 23 casos pelo caminho HTTP.
- `web/tests/test_admin_plano_ui.mjs` — 27 asserções estáticas sobre o portal.

## Decisions Made

**1. Mudar o próprio plano é permitido, e há teste para isso.**
Não é descuido: quem tem `usuarios.gerenciar` já concede a si mesmo qualquer
papel de governança pela rota irmã, e o registro com o nome de quem clicou é a
mitigação que o ADR-013 escolheu para essa classe inteira. Um freio só aqui
seria regra inventada e assimétrica com o que existe ao lado. O teste carrega
a razão escrita, para que "consertar" isso exija apagar um teste que explica
por quê.

**2. Duas rotas, dois eixos.** Papel de governança (ADR-013) e plano comercial
(ADR-010) continuam separados — o motivo original de não juntá-los continua
valendo, e é justamente por isso que a reversão criou uma rota irmã em vez de
acrescentar um campo na rota de papéis.

**3. O 404 da conta inexistente precisa dizer o que é.** Descoberto na medição
RED: `test_usuario_inexistente_404` **passava antes da correção**, porque o
catch-all `_api_inexistente` também responde 404. Um guardião que aprova a
ausência da rota é pior que nenhum. A asserção passou a exigir o texto da rota
e a recusar `rota_inexistente`.

**4. Botão do plano vigente desabilitado.** Reaplicar o mesmo plano produziria
um evento de auditoria com `old == new` — ruído numa tabela que existe para ser
lida.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Duas notas a mais de "sem override de plano" atualizadas**
- **Found during:** Task 1
- **Issue:** O plano mandava atualizar DUAS notas (docstring da rota de papéis
  e comentário do card). Existiam mais duas, fora dos `files_modified`, que
  passariam a afirmar algo falso: `db.set_user_plan` ("Sem tela de override
  manual nesta rodada") e `plan.current_plan` ("sem override manual nesta
  rodada"). Registro de decisão que mente é pior que registro ausente — é
  exatamente a classe de problema que o objetivo do plano nomeia.
- **Fix:** As duas ganharam a reversão datada, no mesmo estilo das outras.
  `plan.py` foi editado sem acentos, como o resto do arquivo.
- **Files modified:** `server/app/db.py`, `server/app/plan.py`
- **Verification:** Suíte canônica verde; nenhum guardião lê esses textos
  (`test_fase3_gate_plano.py` só exige a palavra `metering` em `plan.py`).
- **Committed in:** `7099f0c` (Task 1)

**2. [Rule 2 - Missing Critical] Rótulo nas duas fileiras de botões**
- **Found during:** Task 2
- **Issue:** A fileira de plano entrou acima da de papéis, nas mesmas cores e
  no mesmo formato. Sem rótulo, um admin no celular não distingue "conceder
  papel" de "mudar plano" — dois efeitos diferentes com o mesmo gesto.
- **Fix:** `mudar plano:` e `papéis:` como rótulo de cada fileira.
- **Files modified:** `web-admin/src/App.jsx`
- **Verification:** `npx vite build` verde; guardião do card passa.
- **Committed in:** `19a622b` (Task 2)

**3. [Rule 1 - Bug] Guardião de 404 que passava com a rota inexistente**
- **Found during:** Task 3 (medição RED)
- **Issue:** `test_usuario_inexistente_404` foi um dos 2 casos que passaram
  ANTES da correção — o catch-all `_api_inexistente` também responde 404.
- **Fix:** A asserção passou a recusar `rota_inexistente` e a exigir "não
  encontrado" no corpo.
- **Files modified:** `server/tests/test_admin_plano_usuario.py`
- **Verification:** RED re-medido depois do endurecimento: `21 failed, 2 passed`.
- **Committed in:** `4a9486f` (Task 3)

---

**Total deviations:** 3 auto-fixed (2 missing critical, 1 bug em guardião).
**Impact on plan:** Nenhum desvio de escopo — os três estão dentro do que o
objetivo do plano pede (registro de reversão honesto, controle usável no
celular, guardião que não aprova o vazio).

## Verificação

**RED medido antes de cada correção** (a regra de ouro do repositório):

| Guardião | Antes da correção | Depois |
|----------|-------------------|--------|
| `server/tests/test_admin_plano_usuario.py` | `21 failed, 2 passed` | 23 passed |
| `web/tests/test_admin_plano_ui.mjs` | `12 falha(s)` de 27 | 27 ok |

Os 2 casos de backend que passavam antes são de não-regressão por natureza e
está certo que passassem: o editor de prompts não ver um evento que ainda não
existe, e o `main.py` ainda não ter lista literal de planos. (Um terceiro
passava por vacuidade e virou o desvio 3 acima.)

**Suíte canônica, fora do sandbox:**

```
bash scripts/executar.sh --testes
2565 passed, 5 skipped, 761 warnings in 82.69s
131 arquivos web/tests/*.mjs [OK]
exit=0
```

Baseline `2542 passed, 5 skipped` + 130 `.mjs`. Os `+23` de pytest são
exatamente os casos novos; o `+1` de `.mjs` é o guardião novo.

**Build do portal:** `cd web-admin && npx vite build` → `✓ built in 1.04s`.

**Allowlist pública do ADR-013 NÃO cresceu:** `test_adr013_cobertura_rotas.py`
passa sem nenhuma entrada nova (`git diff HEAD~3 -- server/tests/test_adr013_cobertura_rotas.py`
é vazio) — a rota nova é gated, como deve.

## Issues Encountered

Nenhum. O ambiente exigiu `dangerouslyDisableSandbox` em todo teste/build,
como o contexto de execução já previa.

## User Setup Required

None — nenhuma configuração externa.

## Known Stubs

Nenhum.

## Next Phase Readiness

**NÃO ESTÁ NO AR.** São duas superfícies e duas publicações, nesta ordem:

1. **Backend** — a rota nova exige deploy, com bump manual de
   `SERVER_BUILD_ID` (deploy só-backend). Sem ele o portal chama uma rota que
   o servidor não tem.
2. **Portal admin** — `publicar-admin.sh` depois do deploy do backend. Publicar
   o portal antes deixaria o controle na tela chamando uma rota inexistente
   (o catch-all responderia 404 com `rota_inexistente`, e o card mostraria
   isso como mensagem de erro).

Nada empurrado a `origin`, nenhum PR, nenhuma publicação, nenhum `bump.sh`.

**Não exercitado ao vivo:** nada foi testado contra o servidor real nem no
aparelho. O caminho de verificação humana é: promover uma conta de teste pelo
portal, conferir o evento `user_plan` na aba Auditoria e confirmar que a conta
promovida deixa de bater no cap de análises do `PLAN_FREE`.

---
*Phase: 24-opcoes-mcp-analise-e-setups*
*Completed: 2026-09-12*

## Self-Check: PASSED

Arquivos e commits conferidos por `[ -f ]` e `git log --oneline --all | grep`:

- FOUND `server/tests/test_admin_plano_usuario.py`
- FOUND `web/tests/test_admin_plano_ui.mjs`
- FOUND `.planning/phases/24-opcoes-mcp-analise-e-setups/24-17-SUMMARY.md`
- FOUND `7099f0c`, `19a622b`, `4a9486f`
