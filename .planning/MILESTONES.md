# Milestones

## v1.0 Revisão Geral (Shipped: 2026-08-18)

**Phases completed:** 1 phases, 6 plans, 13 tasks

**Key accomplishments:**

- Jornada real dos 8 passos da Experiência Principal exercitada ao vivo via API (conta isolada, PETR4, compra real de 100 ações), produzindo 10 achados evidenciados (nenhum Crítico/Alto — 5 Médio, 5 Baixo) e confirmando ao vivo que o guardrail CVM da manchete determinística está conforme.
- Auditoria ao vivo dos 10 princípios obrigatórios do CLAUDE.md contra o Boris+ real (backend uvicorn + Vite, dados de mercado reais), com 9 achados evidenciados incluindo um rótulo de fonte de dado hardcoded e factualmente errado no painel técnico (violação direta do princípio 3).
- Dívida técnica auditada em profundidade (10 achados F-CODE-01..10, com 1 Alto: paridade `deviceStore`/`serverStore` sem guardião exaustivo — já causou 2 incidentes reais); a narrativa de causa-raiz dos 3 bugs históricos do `appMode` foi corrigida com evidência linha a linha.
- Achados evidenciados por grep real: `current_plan(user)` nunca é chamado (código órfão), `can_add_ticker`/`can_analyze` caem no `ACTIVE_PLAN` global em vez do plano do usuário, `can_analyze` e `metering.check` são gates concorrentes na mesma rota, e o estado `degradado` da cota brapi (TTL 3x) é invisível a usuário e admin — violação do princípio 3 do CLAUDE.md.
- 4 achados brutos (3 Alto, 1 Médio) na dimensão ADMIN: o segundo kill-switch (`timing_watch`) é invisível no portal e sem toggle em runtime, o painel de custos não mostra o modo de falha silenciosa do provedor de dados que já causou incidente real em produção (31/07/2026), a aba Auditoria diverge visualmente das outras 9 por não ter campo `perm` (mas o backend já gateia corretamente), e não existe alerta por duração do kill-switch ligado — o mecanismo que teria encurtado o incidente real de 2,5 dias.
- Relatório único de 39 achados (2 Crítico, 8 Alto, 20 Médio, 9 Baixo) consolidando as 5 dimensões da auditoria do Boris+, com severidade normalizada pela régua D-02..D-05, deduplicação evidence-based (só 1 de 5 fusões candidatas se confirmou) e validação humana do Alex no checkpoint.

---
