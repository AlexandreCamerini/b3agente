# Phase 3: Correção Crítico + Alto - Context

**Gathered:** 2026-08-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Corrigir os 2 achados Crítico (C-11, C-30) e 8 Alto (C-12, C-19, C-20, C-31,
C-32, C-35, C-36, C-37) do `REPORT-01.md`, seguindo a própria "Sugestão de
sequenciamento" do relatório (dependência técnica: C11→C30, C12→C36, C20
antes de C19, C31 antes de C32, C35 antes de C37).

</domain>

<decisions>
## Implementation Decisions

Cada achado já tem evidência (arquivo:linha) e recomendação completas em
`.planning/milestones/v1.0-phases/01-auditoria-diagn-stica-consolidada/
REPORT-01.md` — os planos desta fase devem LER esse arquivo diretamente para
cada `C-NN`, não redescobrir. As decisões abaixo fecham só os pontos de
fronteira/escopo que o relatório deixava em aberto.

### Fronteira C-30 × C-34 (orçamento brapi)
- **D-01:** Fase 3 corrige SÓ o alerta do estado `degradado` (Crítico) —
  visível a usuário e admin quando o TTL triplicar. O medidor completo de
  consumo×limite (C-34, Médio) fica pra fase 5; não construir agora pra
  evitar acoplar o Crítico a um escopo maior.

### Fronteira C-19 × C-21 (appMode)
- **D-02:** Fase 3 fecha C-19 com um TESTE ESTRUTURAL genérico que falha se
  `data.config.appMode` for lido fora de `App()`/`ctx.operador` (regex sobre
  `App.jsx`, no padrão dos guardiões de paridade existentes) — não faz a
  migração dos 8 pontos de leitura redundante. Essa migração mecânica é
  C-21, Médio, fase 5.

### Gating comercial — corrigir arquitetura, não ativar
- **D-03:** C-31/C-32 corrigem a ARQUITETURA (hooks passam a resolver o
  plano REAL do usuário via `current_plan(user)`, gate concorrente
  unificado) SEM ativar nenhum limite comercial — `PLAN_FREE` continua com
  todos os limites `None` (ilimitado). Comportamento visível ao usuário NÃO
  muda nesta fase. Decisão dos números comerciais continua Out of Scope
  (ADR-010, depende do Alex).
- Fato técnico relevante: `users.plan` já existe na tabela e já é lido por
  `current_plan(user)` — só nunca é passado. `set_user_plan()` já existe mas
  nunca é chamada (sem fluxo de recibo de loja) — não implementar esse fluxo
  nesta fase, é ativação comercial, fora de escopo.

### Canal de alerta C-37 (kill-switch ligado há N horas)
- **D-04:** Usar push via `push.py` (infra existente) — decisão do Alex:
  "o admin também é um usuário, pode usar o push". NÃO existe hoje uma
  função que liste todos os `user_id` com papel admin — precisa ser
  adicionada (`db.py`, query `SELECT user_id FROM user_roles WHERE role =
  'role_admin'` ou equivalente).
- **Limitação técnica a declarar, não a resolver nesta fase:** não existe
  hoje nenhum registro confiável de "quando o kill-switch ligou" que cubra
  TODOS os caminhos de ativação — `admin_audit_log` cobre só a rota admin
  (`PUT /api/admin/agent/kill-switch`), não a ativação via env var
  `B3_AGENT_KILL` (lida ao vivo, sem registro). A duração calculada pela
  fase 3 é best-effort a partir do audit log; se o kill-switch foi ligado
  por env var, a duração não é rastreável — declarar essa limitação na UI/
  alerta, não silenciar.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Relatório fonte (evidência + recomendação de cada achado)
- `.planning/milestones/v1.0-phases/01-auditoria-diagn-stica-consolidada/
  REPORT-01.md` — seções C-11, C-12, C-19, C-20, C-30, C-31, C-32, C-35,
  C-36, C-37 (busca por `#### C-NN` no arquivo)

### Gating (C-31, C-32)
- `server/app/plan.py` — `current_plan()` (linhas 41-49, nunca chamada),
  `can_add_ticker`/`can_analyze` (linhas 63-80, fallback `ACTIVE_PLAN`),
  `ACTIVE_PLAN = PLAN_FREE` (linha 35)
- Call sites reais (nenhum passa `plan=`/`user=`): `server/app/main.py:870`
  (`can_add_ticker`), `:1223` e `:1370` (`can_analyze`)
- `server/app/db.py:315,490` — `users.plan` já existe e é lido no dict do
  usuário; `db.py:409-413` — `set_user_plan()` existe, nunca chamada
- `docs/adr/010-planos-e-cap-gratuito.md` — decisão 5: os 3 passos técnicos
  de ativação já documentados

### appMode (C-19)
- `web/src/App.jsx:7214-7220` — definição de `ctx.operador`, comentário
  "Novo código deve ler `ctx.operador`"
- `web/src/App.jsx:1624,1828,2018,3188,4224,5606,5756,6319,6501,6862,7411`
  — os 10 pontos de leitura hoje (para o teste estrutural identificar)

### Kill-switch e push (C-35, C-37)
- `server/app/push.py:171-249` — `send_to_user(conn, user_id, ...)`, sempre
  por `user_id` específico, sem broadcast/admin nativo
- `server/app/rbac.py:73-75` — `roles_for_user()` (um usuário por vez); não
  existe função de listar todos os admins — precisa ser criada
- `server/app/agent.py:173-204` (`kill_switch_on`), `:154-170`
  (`set_kill_switch`) — sem timestamp de ativação
- `server/app/db.py:532-542` (`admin_config_set`, grava `updated_at`
  internamente mas não exposto), `:522-529` (`admin_config_get`, descarta
  `updated_by`/`updated_at`)
- `server/app/main.py:668-675` — rota admin que liga/desliga e grava audit
  log via `audit.record` (`server/app/audit.py:12-16`)
- `server/app/timing_watch.py:58-59` — segundo kill-switch (C-35), mesmo
  padrão de ausência de visibilidade

### Fonte de dado / rótulo (C-11, C-12)
- ADR-008, decisão 5: "payload carrega `source` e idade" — o campo já
  existe na resposta da API, só não é lido corretamente no front
- `web/src/App.jsx:1511-1513` — `TechnicalModal`, rótulo hardcoded (C-11)

### Princípios do produto
- `CLAUDE.md` — princípio 3 (transparência de fonte/horário do dado,
  violado por C-11 e C-30), princípio 5 (cálculo determinístico — gating
  não pode virar decisão de IA)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `push.py:send_to_user` já pronto para reuso — só falta a função de listar
  admins.
- Padrão de teste estrutural via regex sobre `App.jsx` já existe (guardiões
  de paridade de prompts/stores) — reusar o mesmo padrão pro teste de C-19.
- `admin_audit_log` já registra transições do kill-switch pela rota admin —
  reusar para calcular duração, com a limitação declarada acima.

### Established Patterns
- `plan.py` foi desenhado desde o início para aceitar `user=`/`plan=`
  explícitos — a "correção" de C-31/C-32 é majoritariamente conectar
  parâmetros já suportados, não inventar mecanismo novo.

### Integration Points
- `main.py:870,1223,1370` — os 3 pontos exatos onde `current_plan(user)`
  precisa ser conectado.

</code_context>

<specifics>
## Specific Ideas

Nenhuma referência visual/exemplo externo.

</specifics>

<deferred>
## Deferred Ideas

- C-34 (medidor completo de orçamento) — já mapeado para fase 5, confirmado
  nesta discussão, não duplicar aqui
- C-21 (migração dos 8 pontos de `appMode`) — já mapeado para fase 5,
  confirmado nesta discussão
- Fluxo de validação de recibo de loja / ativação real do cap comercial —
  fora de escopo da milestone inteira (PROJECT.md Out of Scope)

</deferred>

---

*Phase: 3-Correção Crítico + Alto*
*Context gathered: 2026-08-18*
