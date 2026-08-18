# Requirements: Boris+ (b3-agente) — Revisão Geral

**Defined:** 2026-08-18
**Core Value:** O usuário leigo sai do Modo Estudo entendendo de verdade como o mercado funciona — não decorou uma resposta, aprendeu o raciocínio — e só então tem acesso a automações do Modo Operador.

## v1 Requirements

Requisitos desta revisão: cada item é um achado auditável, não uma feature nova.
"Done" = achado documentado com severidade, evidência (arquivo:linha quando
aplicável) e recomendação — não é correção de código (fora de escopo desta
fase, ver PROJECT.md).

### Storyline pedagógico (Modo Estudo → Operador)

- [ ] **STORY-01**: Documentar a jornada real do usuário do primeiro acesso
      até a primeira ordem simulada, comparando contra os 8 passos da
      Experiência Principal do CLAUDE.md (escolher ativo → visualizar dado →
      analisar contexto/risco → enviar ordem → acompanhar execução →
      visualizar resultado → explicação educacional → registrar aprendizado)
- [ ] **STORY-02**: Avaliar se a transição Estudo→Operador tem gatilho e
      narrativa claros (o que muda, por que, quando o usuário deveria migrar)
      ou é apenas um toggle sem contexto
- [ ] **STORY-03**: Avaliar cobertura real da camada educacional (tendência,
      momentum, valor, qualidade, volatilidade, suporte/resistência,
      rompimento, reversão à média, diversificação, risco-retorno, drawdown,
      expectativa matemática, taxa de acerto vs. rentabilidade) contra o que
      é efetivamente ensinado hoje na UI e nas respostas da IA
- [ ] **STORY-04**: Verificar que a IA nunca promete lucro, nunca afirma
      100% de confluência, e diz explicitamente "não há dados suficientes
      para concluir" quando aplicável — inventariar violações reais, não
      hipotéticas

### UX/UI

- [ ] **UX-01**: Auditar os 10 princípios obrigatórios do CLAUDE.md contra
      telas reais: saldo fictício sempre visível, fonte+horário do dado
      exibidos, sem invenção de valor quando a fonte falha, estados
      completos (carregamento, vazio, erro, mercado fechado, dado atrasado,
      ordem rejeitada, ordem parcial, operação concluída)
- [ ] **UX-02**: Auditar consistência visual/hierarquia entre Modo Estudo e
      Modo Operador — fica claro em qual modo o usuário está a qualquer
      momento na tela?
- [ ] **UX-03**: Auditar responsividade mobile e acessibilidade básica
      (contraste, alvo de toque, leitura de tela) nas telas principais
      (Ativo, Operador, Carteira, Perfil)
- [ ] **UX-04**: Auditar linguagem/copy contra as proibições do CLAUDE.md
      (sem enriquecimento rápido, sem garantia de acerto, sem promessa)

### Código

- [ ] **CODE-01**: Avaliar o risco do monólito `web/src/App.jsx` (7599
      linhas, `appMode` recalculado em 11+ lugares) — mapear pontos de
      divergência real ou potencial entre as recomputações
- [ ] **CODE-02**: Avaliar se os guardiões de teste de paridade
      (`deviceStore`/`serverStore`, `defaults.py`/`catalog.js`) cobrem o
      suficiente ou há lacunas conhecidas
- [ ] **CODE-03**: Avaliar o defeito já documentado do gate "Executar" (trava
      silenciosa sem feedback, `docs/auditoria-controle-ordens-parametros.md`,
      `App.jsx:3596-3610` e `:3745-3749`) e classificar severidade/blast
      radius
- [ ] **CODE-04**: Avaliar cobertura da suíte canônica
      (`scripts/executar.sh --testes`) contra os fluxos críticos (execução
      de ordem, cálculo de PnL/drawdown, falha de fonte de dados, dado
      atrasado, ordem rejeitada)

### Gating de monetização

- [ ] **GATE-01**: Avaliar se `plan.py`/`metering.py` aguentam escalonamento
      real (free → pago) sem reescrita estrutural, dado que hoje os hooks
      `can_add_ticker`/`can_analyze`/`requires_subscription` nunca checam
      limite real (comparam contra `None`)
- [ ] **GATE-02**: Avaliar a separação entre cota física da brapi
      (compartilhada, 15k/mês) e cap comercial (por conta) — a UI comunica
      essa distinção de forma transparente quando o cap disparar?
- [ ] **GATE-03**: Mapear tecnicamente quais features hoje são candidatas
      naturais a tier pago (IA gerenciada com cota maior, ajuste de
      intervalo, alvo dinâmico, recorte de eficiência) e o esforço de
      ligá-las — sem decidir preço/quantidade (fora de escopo)

### Portal de administração/observabilidade

- [ ] **ADMIN-01**: Avaliar cobertura do portal (`web-admin/`) contra RBAC
      (ADR-013) — os grupos/papéis cobrem os cenários reais de operação?
- [ ] **ADMIN-02**: Avaliar visibilidade operacional (kill-switch, orçamento
      brapi, métricas de IA) — o portal teria detectado e permitido agir
      rápido num incidente como o do kill-switch de 2,5 dias?
- [ ] **ADMIN-03**: Avaliar usabilidade do handoff mobile (ADR-014) e do
      fluxo geral de quem administra o produto

### Consolidação

- [ ] **REPORT-01**: Relatório único consolidando todos os achados acima,
      classificados por severidade (crítico/alto/médio/baixo) e dimensão,
      com evidência (arquivo:linha quando aplicável) e recomendação —
      alimenta o roadmap de fases de correção seguintes

## v2 Requirements

Correção dos achados desta revisão — vira roadmap só depois do relatório
consolidado (REPORT-01), priorizado pelo Alex.

## Out of Scope

| Item | Reason |
|------|--------|
| Corrigir achados nesta fase | Revisão é diagnóstico, não implementação — decisão explícita do usuário |
| Decidir números comerciais do plano (limites, preço, loja) | Depende do Alex, ADR-010 — fora do alcance técnico desta revisão |
| Modo Operador de trades reais | Fora do produto por princípio — só carteira simulada |
| Posição vendida/short | Não existe no modelo de dados — fora de escopo de produto |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| STORY-01 | Phase 1 | Pending |
| STORY-02 | Phase 1 | Pending |
| STORY-03 | Phase 1 | Pending |
| STORY-04 | Phase 1 | Pending |
| UX-01 | Phase 1 | Pending |
| UX-02 | Phase 1 | Pending |
| UX-03 | Phase 1 | Pending |
| UX-04 | Phase 1 | Pending |
| CODE-01 | Phase 1 | Pending |
| CODE-02 | Phase 1 | Pending |
| CODE-03 | Phase 1 | Pending |
| CODE-04 | Phase 1 | Pending |
| GATE-01 | Phase 1 | Pending |
| GATE-02 | Phase 1 | Pending |
| GATE-03 | Phase 1 | Pending |
| ADMIN-01 | Phase 1 | Pending |
| ADMIN-02 | Phase 1 | Pending |
| ADMIN-03 | Phase 1 | Pending |
| REPORT-01 | Phase 1 | Pending |

**Coverage:**
- v1 requirements: 19 total
- Mapped to phases: 19/19 ✓
- Unmapped: 0

---
*Requirements defined: 2026-08-18*
*Last updated: 2026-08-18 after roadmap creation*
