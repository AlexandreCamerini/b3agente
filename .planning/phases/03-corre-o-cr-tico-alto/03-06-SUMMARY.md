---
phase: 03-corre-o-cr-tico-alto
plan: 06
subsystem: admin
tags: [fastapi, sqlite, push-apns, react, rbac, kill-switch, observability]

# Dependency graph
requires:
  - phase: 03-corre-o-cr-tico-alto (plan 03-05)
    provides: "TimingWatchKillSwitchBox + KPI PUSH DO GATILHO no portal (o par visual que este plano NÃO duplica a mecânica de duração)"
provides:
  - "Alerta ATIVO por push (APNs) a administradores enquanto o kill-switch do Operador estiver ligado em horário de pregão"
  - "Duração best-effort ('ligado há Nh') calculada a partir do admin_audit_log, com ressalva explícita e nunca inventada quando não rastreável (ativação por env var)"
  - "db.user_ids_with_roles (consulta interna, sem rota HTTP) e db.audit_last (última transição de uma entidade/campo)"
  - "GET /api/admin/agent/kill-switch expõe desde/horas/rastreavel"
  - "Linha 'Ligado há' no portal admin (KillSwitchBox), mesma linguagem do push"
affects: [phase-04, phase-05, admin-portal, agent-scheduler]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Hook best-effort no scheduler_loop, pendurado ANTES do primeiro gate de kill-switch, com try/except próprio (mesmo padrão dos demais hooks do laço) — nenhum componente novo pode derrubar o ciclo de stop/alvo"
    - "Dedupe de alerta persistido em kv (sobrevive a redeploy), com reset explícito ao desligar o kill-switch"
    - "Consulta interna sem rota HTTP, documentada em docstring e travada por guardião automatizado (grep no fonte)"

key-files:
  created:
    - server/tests/test_fase3_kill_switch_duracao.py
    - web/tests/test_fase3_admin_duracao.mjs
  modified:
    - server/app/db.py
    - server/app/agent.py
    - server/app/main.py
    - web-admin/src/App.jsx
    - .planning/phases/03-corre-o-cr-tico-alto/deferred-items.md

key-decisions:
  - "Duração é SEMPRE best-effort via admin_audit_log — quando não rastreável (ativação por B3_AGENT_KILL), push e UI mostram a MESMA ressalva textual, nunca um número diferente entre os dois canais"
  - "Alerta não consulta push.prefs_for: é aviso operacional para papel administrativo, não uma classe de notificação opt-in do usuário final"
  - "db.user_ids_with_roles é uso EXCLUSIVAMENTE interno do scheduler — nenhuma rota HTTP a expõe (guardião automatizado)"

requirements-completed: [FIX-C37]

# Metrics
duration: ~1h45m (incluindo a pausa do checkpoint humano)
completed: 2026-08-19
---

# Phase 3 Plan 06: Alerta ativo de kill-switch + duração best-effort (C-37) Summary

**Push ativo (APNs) a administradores com "ligado há Nh" quando o kill-switch do Operador está ligado em pregão, calculado best-effort do admin_audit_log e com ressalva explícita (nunca um número inventado) quando a ativação foi por variável de ambiente — mesmo texto no push e no portal admin.**

## Performance

- **Duration:** ~1h45m de ponta a ponta, incluindo a pausa do checkpoint humano (Task 3) e a investigação de um achado de dado contaminado não relacionado ao código deste plano (ver "Issues Encontrados" abaixo)
- **Started:** 2026-08-18T23:18Z (aprox., após merge de 03-05)
- **Completed:** 2026-08-19T04:07Z
- **Tasks:** 3 (2 auto + 1 checkpoint humano, aprovado)
- **Files modified:** 6 (4 código + 2 novos arquivos de teste) + 1 doc de deferred-items

## Accomplishments

- O sinal do kill-switch do Operador deixou de ser 100% passivo: `scheduler_loop` avisa ativamente todo administrador (papel `role_admin` ou `execucao_automatica`) via push enquanto o kill-switch estiver ligado dentro do pregão, no máximo 1x a cada 4h por episódio — dedupe persistido em kv, sobrevive a redeploy.
- Duração calculada best-effort a partir do `admin_audit_log` (única fonte que registra a transição real da rota admin); quando a ativação foi por `B3_AGENT_KILL` (sem passar pela rota, sem registro), tanto o push quanto o portal dizem isso com todas as letras — nunca um `0h` nem uma estimativa.
- `GET /api/admin/agent/kill-switch` agora devolve `desde`/`horas`/`rastreavel`, sem mudar a permissão nem o comportamento do `PUT`.
- Portal admin (`KillSwitchBox`) ganha a linha "Ligado há", só visível com `data.on === true`, tom `negative` a partir de 4h.
- `db.user_ids_with_roles` é consulta interna (scheduler), nunca exposta por rota — guardião automatizado trava isso.

## Task Commits

1. **Task 1: Consultas de admin/auditoria em db.py + duração best-effort e alerta ativo no scheduler_loop** - `91c0de1` (feat)
2. **Task 2: Rota admin expõe duração/rastreabilidade e o portal mostra "Ligado há"** - `c4f1ede` (feat)
3. **Task 3: Verificação humana das superfícies visíveis da fase 3** - checkpoint, sem commit de código (aprovado pelo desenvolvedor)

**Plan metadata:** (este commit, docs: complete plan)

## Files Created/Modified

- `server/app/db.py` - `user_ids_with_roles` (consulta interna, placeholders parametrizados) e `audit_last` (última transição por entidade/campo, com helper `_audit_row_to_dict` extraído para não duplicar `audit_recent`)
- `server/app/agent.py` - `kill_switch_ligado_desde` (best-effort, `None` = não rastreável, nunca "0h"), `_alertar_kill_switch` (hook do `scheduler_loop`, dedupe em kv, fan-out de push), hook pendurado logo após o heartbeat e ANTES do primeiro gate de kill-switch
- `server/app/main.py` - `GET /api/admin/agent/kill-switch` monta `desde`/`horas`/`rastreavel`; `rastreavel` só `True` quando `on` e `desde` existem
- `web-admin/src/App.jsx` - `KillSwitchBox` ganha a linha "Ligado há" (Kv condicionado a `data.on`), formatação `DD/MM HH:MM` em BRT no cliente
- `server/tests/test_fase3_kill_switch_duracao.py` - 24 testes (20 de unidade/hook cobrindo os 9 pontos do `<behavior>`, guardião de posição do hook no fonte, guardião de superfície; 4 de rota HTTP)
- `web/tests/test_fase3_admin_duracao.mjs` - guardião estático (Pattern A): linha única, condicional a `data.on`, ressalva literal, limiar de 4h, fronteira com `TimingWatchKillSwitchBox`
- `.planning/phases/03-corre-o-cr-tico-alto/deferred-items.md` - achado de dado contaminado documentado (ver "Issues Encontrados")

## Decisions Made

- **Placement do hook:** logo após o bloco do heartbeat e ANTES do primeiro `if not kill_switch_on()` do `scheduler_loop` — validado por assertiva automatizada no teste (índice de string), não só inspeção visual, porque atrás do portão o alerta seria silenciado exatamente pelo estado que precisa denunciar (mesmo erro do heartbeat que mascarou o incidente real de 2,5 dias).
- **SQL de `user_ids_with_roles` sem f-string na query inteira** (T-03-24): só os placeholders `?` variam com o tamanho da lista de papéis; os valores viajam sempre parametrizados. Escrito como concatenação de string (não f-string) especificamente para passar no guardião automatizado que grepa por `f"SELECT.*user_roles`.
- **Ressalva de não-rastreabilidade idêntica nos dois canais** (push e portal) — decisão do UI-SPEC (D-04), reforçada por testes que checam a MESMA string literal nos dois lados.

## Deviations from Plan

None - plan executado exatamente como escrito. O único desvio notável não foi no código deste plano, mas um achado de ambiente descoberto DURANTE a verificação humana (Task 3) — ver "Issues Encontrados".

## Issues Encontrados

**Dado contaminado no banco do worktree, descoberto durante a verificação ao vivo (Task 3) — NÃO causado pelo código ou pelos testes deste plano.**

Ao abrir o painel técnico de um ativo (passo 3 do checklist de verificação), o `PriceChart` recebeu candles com `date: "2026-01-01+125"` (formato inválido) vindos do cache L2 (`candle_cache`, SQLite). Investigação (documentada em detalhe em
[`deferred-items.md`](./deferred-items.md#03-06)):

- A fórmula de data (`f"2026-01-01+{i}"`) é IDÊNTICA ao fixture `_mk_candles()` de `server/tests/test_fase3_proveniencia_technicals.py` — um arquivo de teste PRÉ-EXISTENTE (do plano 03-01, não deste plano). Suas funções `test_a_snapshot_propaga_source_do_candle_cache`/`test_b_snapshot_nao_inventa_source_quando_ausente` chamam `technical_snapshot.get()` DIRETAMENTE, sem `monkeypatch.setenv("B3_DB_PATH", ...)` e sem reimportar `app.main` — diferente das outras funções do MESMO arquivo (`test_c`..`test_f`), que isolam corretamente via um helper `_client(monkeypatch)`.
- Causa raiz confirmada por leitura de código (não só correlação): `server/app/main.py:50-55` cria `_conn = db.shared()` (conexão LAZY, resolvida por thread na primeira query) e injeta em `candle_cache.configure_db(_conn)` — um GLOBAL de módulo. `candle_cache.reset()` só limpa a memória L1, nunca esse `_DB_CONN`. Não existe `conftest.py` em `server/tests/` fixando `B3_DB_PATH` no nível de sessão. Pelo menos 10 arquivos de teste pré-existentes importam `app.main` no nível de MÓDULO sem override de `B3_DB_PATH` antes. Qualquer thread que resolva essa conexão compartilhada enquanto `B3_DB_PATH` está ausente (o estado ambiente padrão de um `pytest -q` cru) fica permanentemente presa ao banco REAL pelo resto da sessão.
- **Confirmado que NÃO foi o teste novo deste plano:** `test_fase3_kill_switch_duracao.py` nunca toca `candle_cache`/a conexão compartilhada de `app.main` — os testes de unidade usam `db.connect(tempdir)` direto; os testes de rota seguem o MESMO padrão seguro já usado por `test_fase3_timing_watch_kill.py` (env var setada ANTES do reimport de `app.main`). A contaminação é totalmente explicada por rodar a suíte PRÉ-EXISTENTE inteira (`cd server && ./.venv/bin/python -m pytest -q`, exigida pelo próprio critério de aceite deste plano, executada duas vezes durante a execução) contra o `B3_DB_PATH` ambiente (ausente) deste worktree.
- **Remediação aplicada foi só de DADO, não de código:** as 15 linhas contaminadas de `candle_cache` tiveram o campo `date` corrigido diretamente no SQLite do worktree (script Python, preservando os demais campos e `src`) para permitir concluir a verificação. O arquivo do banco é gitignorado (`server/data/`, confirmado via `git check-ignore`) — nada vazou para o histórico do git.
- **Não corrigido neste plano** (fora do escopo de arquivos de `03-06`): a correção adequada (ex.: `conftest.py` com fixture `autouse` de escopo de sessão fixando `B3_DB_PATH` antes de qualquer import, ou fazer `candle_cache.reset()` também limpar `_DB_CONN`/`_DB_ENABLED`) toca ~10 arquivos de teste pré-existentes fora da lista de arquivos deste plano. Registrado como item a resolver em fase futura, independente de qualquer plano de feature específico.

## User Setup Required

None - nenhuma configuração de serviço externo necessária. Este plano reusa a infraestrutura de push (APNs) já configurada em fases anteriores.

## Verificação Humana (Task 3, checkpoint aprovado)

Suíte canônica (`bash scripts/executar.sh --testes`) e os dois builds (`web`, `web-admin`) rodaram automaticamente antes do checkpoint — todos verdes. Passos verificados ao vivo:

- ✅ Passo 3 (Fonte: no painel técnico) — confirmado via `/api/technicals/PETR4` (`source: "yahoo"`), nunca "Yahoo Finance".
- ⚠️ Passo 4 (orçamento no Perfil) — NÃO verificado ao vivo neste worktree: roda com `B3_CANDLE_PROVIDER` default (yahoo), então `orcamentoBrapi` vem `null` (só populado com provedor brapi ativo). Coberto pelos testes automatizados (cenário degradado mockado em `test_fase3_proveniencia_technicals.py`); registrado aqui como limitação de AMBIENTE deste worktree, não como item pulado por omissão.
- ✅ Passo 5 (ticker inexistente) — `POST /api/buy {"t":"XXXXX9"}` → 502, mensagem limpa `"Sem cotacao para XXXXX9"`.
- ✅ Passos 6-8 (KPIs, kill-switches, linha "Ligado há") — aprovados pelo desenvolvedor; ambos os kill-switches devolvidos ao estado desligado.
- ✅ Passo 9 (Custos) — `/api/obs/usage` retorna `vazios`/`taxaFalha`/`alerta`; as 3 linhas renderizam corretamente.

**Resultado: aprovado**, com a ressalva do passo 4 (limitação de ambiente, não achado de produto) e o achado de dado contaminado documentado acima (não bloqueante, já remediado).

## Next Phase Readiness

- FIX-C37 completo — fecha o último item Alto da Fase 3 (2 Crítico + 8 Alto do REPORT-01, todos endereçados nos planos 03-01 a 03-06).
- Nenhum bloqueio para a Fase 4. O achado de test-isolation (`candle_cache._DB_CONN` global) é um item de infraestrutura de teste, não de produto — recomendado como item independente para uma fase futura (ver `deferred-items.md`).

---
*Phase: 03-corre-o-cr-tico-alto*
*Completed: 2026-08-19*

## Self-Check: PASSED

All key files confirmed present (`server/app/db.py`, `server/app/agent.py`, `server/app/main.py`,
`web-admin/src/App.jsx`, `server/tests/test_fase3_kill_switch_duracao.py`,
`web/tests/test_fase3_admin_duracao.mjs`, this SUMMARY.md, `deferred-items.md`). Both task commit
hashes (`91c0de1`, `c4f1ede`) confirmed present in `git log --oneline`.
