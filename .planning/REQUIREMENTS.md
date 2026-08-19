# Requirements: Boris+ (b3-agente) — v1.1 Realismo de Mercado + Correções

**Defined:** 2026-08-18
**Core Value:** O usuário leigo sai do Modo Estudo entendendo de verdade como o mercado funciona — não decorou uma resposta, aprendeu o raciocínio — e só então tem acesso a automações do Modo Operador.

## v1.1 Requirements

### Realismo de Mercado (funcionalidade nova)

- [x] **MERC-01**: Usuário vê o status real do mercado (aberto/fechado) na tela
      de entrada/home, calculado por `pregao.py` (fonte única já existente:
      `is_trading_day()` + `in_market_hours()`) — hoje esse status só aparece
      pós-login, na aba Operador
- [x] **MERC-02**: Ordem colocada fora do horário de pregão fica com status
      "pendente" e executa ao preço de abertura do pregão seguinte (não ao
      preço do momento do pedido)
- [x] **MERC-03**: Caixa da ordem pendente é reservado no momento do pedido
      (fica indisponível para outras ordens) — só é debitado de fato na
      execução
- [x] **MERC-04**: Usuário pode cancelar uma ordem pendente a qualquer momento
      antes da execução (abertura do pregão seguinte)

### Correção — Crítico (REPORT-01)

- [x] **FIX-C11**: Rótulo de fonte de dado no painel técnico (`TechnicalModal`)
      deixa de ser fixo/hardcoded e passa a refletir a fonte real que serviu
      o dado (UX, viola princípio 3)
- [x] **FIX-C30**: Estado `degradado` da cota brapi (TTL triplicado) passa a
      ser visível a usuário e admin, não só inferível (GATE, viola princípio 3)

### Correção — Alto (REPORT-01)

- [x] **FIX-C12**: Erro de fonte de dado não vaza detalhe técnico interno —
      sai como 502 limpo, não 500 cru (UX)
- [x] **FIX-C19**: Card de status único no topo da tela "Operador IA",
      resumindo os 3 interruptores que decidem se uma ordem dispara (Modo
      do app · Operador no servidor · Executar/sinalizar) com estado atual
      de cada um e link direto pra trocar — mecanismo estrutural que
      REPORT-01/docs/auditoria-controle-ordens-parametros.md recomendam
      para o padrão-classe "estado que muda num lugar que outro não vê"
      (dos 3 bugs históricos, só o de paridade de stores tem cobertura de
      classe, via C-20; os outros 2 seguem só com guardião de sintoma —
      este card não substitui teste, é a mitigação de visibilidade que o
      próprio relatório aponta como pendente) (CODE) — comportamento reativo
      testado ao vivo e aprovado por Alex (03-HUMAN-UAT.md)
- [x] **FIX-C20**: Teste genérico de paridade `deviceStore`×`serverStore` —
      falha em qualquer assimetria de método não documentada como
      intencional (CODE)
- [x] **FIX-C31**: Hooks de gate (`can_add_ticker`/`can_analyze`) passam a
      resolver o plano REAL do usuário, não o `ACTIVE_PLAN` global; código
      órfão `current_plan` é conectado ou removido (GATE)
- [x] **FIX-C32**: `can_analyze` e `metering.check` deixam de ser gates
      concorrentes na mesma requisição — lógica de contagem unificada (GATE)
- [x] **FIX-C35**: Segundo kill-switch (`timing_watch`) ganha visibilidade e
      toggle em runtime no portal admin (ADMIN) — fallback de permissão não
      testável ao vivo pelo fluxo real do produto (RBAC agrupa `.ver` e
      `.controlar`); Alex aceitou a garantia de código (03-HUMAN-UAT.md)
- [x] **FIX-C36**: Painel de custos do admin passa a mostrar `vazios`/
      `alerta`/`taxaFalha`, não só `erros` (ADMIN)
- [x] **FIX-C37**: Alerta de "kill-switch ligado há N horas em horário de
      pregão" implementado (ADMIN)

### Correção — Médio (REPORT-01)

- [ ] **FIX-C01**: Passo 7 (explicação educacional) ganha fallback
      determinístico quando a IA não está disponível (STORY)
- [ ] **FIX-C02**: Ordem rejeitada passa a registrar `status` e `motivo de
      rejeição` (STORY)
- [ ] **FIX-C03**: Passo 8 ("comparar com o benchmark") ganha comparação real
      com um índice (STORY)
- [ ] **FIX-C04**: Transição Estudo→Operador ganha critério pedagógico de
      prontidão, além do critério legal (aceite de termo) (STORY)
- [ ] **FIX-C05**: Conceito "Diversificação" passa a ser ensinado no produto
      (STORY)
- [ ] **FIX-C13**: Disclaimer de operação simulada passa a renderizar no
      momento da decisão, não só existir definido (UX)
- [ ] **FIX-C14**: "Ordem parcialmente executada" passa a existir no modelo
      de dados (UX)
- [ ] **FIX-C15**: Toggle "acordeão" responde a teclado (UX, acessibilidade)
- [ ] **FIX-C16**: `textFaint` ajustado para contraste mínimo WCAG AA em texto
      pequeno, nos dois temas (UX, acessibilidade)
- [ ] **FIX-C21**: Migrar os pontos de recomputação redundante de `appMode`
      em `App.jsx` para ler `ctx.operador` (CODE)
- [ ] **FIX-C22**: `default_skill_text()`/`defaultSkillText()` ganha guardião
      de paridade, no padrão do par `carteiraStopAlvo*` (CODE)
- [ ] **FIX-C23**: Toggle mestre de "Entrada automática" ganha atributo HTML
      `disabled` e feedback próprio (CODE)
- [ ] **FIX-C24**: Suíte web roda de forma confiável em checkout/worktree novo
      (documentar/automatizar `npm install` antes da suíte canônica) (CODE)
- [ ] **FIX-C25**: Rejeição de ordem em `/api/buy`/`/api/sell` (caixa
      insuficiente, sem cotação, ticker inválido) ganha teste de rota HTTP
      (CODE)
- [ ] **FIX-C26**: Recompra após venda parcial (preço médio reponderado)
      ganha teste (CODE)
- [ ] **FIX-C27**: Avaliar cobertura E2E/browser automation mínima para os
      fluxos financeiros críticos (CODE)
- [ ] **FIX-C33**: `can_add_ticker`/`can_analyze` passam a ser chamados com o
      estado real do usuário, não dado hardcoded (GATE)
- [ ] **FIX-C34**: Medidor de orçamento brapi (consumo × limite) ganha
      visibilidade para o usuário final, deixando claro que é consumo do app
      inteiro, não cota pessoal (GATE)
- [ ] **FIX-C38**: Alerta preventivo antes do teto global de gasto de IA, não
      só hard stop (ADMIN)
- [ ] **FIX-C39**: Aba "Auditoria" do portal admin ganha campo `perm`,
      alinhando com o padrão visual das outras 9 abas (ADMIN)

## Future Requirements (backlog — não mapeado a fase ainda)

### Correção — Baixo (REPORT-01, 9 achados)

- **C-06**: "Diário" vira jornada de aprendizado, não só log operacional (STORY)
- **C-07**: "Dois nomes Operador" — unificar narrativa (STORY)
- **C-08**: "Reversão à média" nomeada explicitamente como conceito (STORY)
- **C-09**: Drawdown sobe de "definição" para "decisão" (STORY)
- **C-10**: Frase literal "Não há dados suficientes para concluir" passa a
  aparecer verbatim (STORY + UX)
- **C-17**: Troca de modo sem reload completo do app (UX)
- **C-18**: Gate "Executar" ganha `aria-describedby` (UX, acessibilidade)
- **C-28**: Normalização "passthrough" de `appMode` alinhada ao padrão
  ternário (CODE)
- **C-29**: Medição numérica de cobertura de testes (CODE)

## Out of Scope

| Item | Reason |
|------|--------|
| Decisão dos números comerciais do plano gratuito/pago | Depende do Alex, ADR-010 — fora do alcance técnico |
| Modo Operador de trades reais | Fora do produto por princípio — só carteira simulada |
| Posição vendida/short | Não existe no modelo de dados |
| Fonte dupla por finalidade (brapi carteira / Yahoo Radar) | Descartada no checkpoint da v1.0 — ganho modesto, Radar já usa Yahoo |
| Escolha de fonte/frequência na UI do usuário | Já rejeitada no ADR-008 (duas vezes) e esbarra no orçamento ser por-app (ADR-010) |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| MERC-01 | Phase 2 | Complete |
| MERC-02 | Phase 2 | Complete |
| MERC-03 | Phase 2 | Complete |
| MERC-04 | Phase 2 | Complete |
| FIX-C11 | Phase 3 | Complete |
| FIX-C30 | Phase 3 | Complete |
| FIX-C12 | Phase 3 | Complete |
| FIX-C19 | Phase 3 | Complete |
| FIX-C20 | Phase 3 | Complete |
| FIX-C31 | Phase 3 | Complete |
| FIX-C32 | Phase 3 | Complete |
| FIX-C35 | Phase 3 | Complete (fallback de permissão: garantia de código aceita, não testável ao vivo — ver 03-HUMAN-UAT.md) |
| FIX-C36 | Phase 3 | Complete |
| FIX-C37 | Phase 3 | Complete |
| FIX-C01 | Phase 4 | Pending |
| FIX-C02 | Phase 4 | Pending |
| FIX-C03 | Phase 4 | Pending |
| FIX-C04 | Phase 4 | Pending |
| FIX-C05 | Phase 4 | Pending |
| FIX-C13 | Phase 4 | Pending |
| FIX-C14 | Phase 4 | Pending |
| FIX-C15 | Phase 4 | Pending |
| FIX-C16 | Phase 4 | Pending |
| FIX-C21 | Phase 5 | Pending |
| FIX-C22 | Phase 5 | Pending |
| FIX-C23 | Phase 5 | Pending |
| FIX-C24 | Phase 5 | Pending |
| FIX-C25 | Phase 5 | Pending |
| FIX-C26 | Phase 5 | Pending |
| FIX-C27 | Phase 5 | Pending |
| FIX-C33 | Phase 5 | Pending |
| FIX-C34 | Phase 5 | Pending |
| FIX-C38 | Phase 5 | Pending |
| FIX-C39 | Phase 5 | Pending |

**Coverage:**
- v1.1 requirements: 34 total (4 MERC + 30 FIX)
- Mapped to phases: 34/34 ✓
- Unmapped: 0

**Phase summary:**
- Phase 2 (Realismo de Mercado): MERC-01..04 (4 requirements)
- Phase 3 (Correção Crítico + Alto): FIX-C11, FIX-C30, FIX-C12, FIX-C19, FIX-C20, FIX-C31, FIX-C32, FIX-C35, FIX-C36, FIX-C37 (10 requirements)
- Phase 4 (Correção Médio — Storyline & UX): FIX-C01..C05, FIX-C13..C16 (9 requirements)
- Phase 5 (Correção Médio — Código, Gate & Admin): FIX-C21..C27, FIX-C33, FIX-C34, FIX-C38, FIX-C39 (11 requirements)

---
*Requirements defined: 2026-08-18*
*Last updated: 2026-08-18 after roadmap creation (v1.1, Phases 2-5)*
