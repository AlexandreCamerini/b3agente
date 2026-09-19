# Requirements: Boris+ (b3-agente) — Milestone v1.6

**Defined:** 2026-09-19
**Core Value:** O usuário leigo sai do Modo Estudo entendendo de verdade como o mercado funciona — não decorou uma resposta, aprendeu o raciocínio — e só então tem acesso a automações do Modo Operador.

Base: pesquisa em `.planning/research/` (STACK/FEATURES/ARCHITECTURE/PITFALLS/SUMMARY), avaliação agentic UX escopada à aba Opções (sessão 2026-09-19), decisões confirmadas com o Alex via AskUserQuestion na mesma sessão.

## v1 Requirements

Reorganizar a sub-aba "Setups" da aba Opções por job-to-be-done. Duas fases de risco crescente, confirmadas pelo Alex: primeiro extrair (sem tocar navegação), depois redesenhar a navegação.

### Extração (REORG) — Fase A: separar os 5 jobs sem mudar comportamento

- [ ] **REORG-01**: Usuário vê os 5 jobs hoje misturados numa rolagem só — descobrir oportunidades cross-carteira (Blocos A+B), gerenciar vigias, analisar um ticker manualmente, comparar vencimentos, gerenciar/criar setups salvos — como seções fisicamente separadas em componentes próprios
- [ ] **REORG-02**: Cada seção extraída preserva exatamente o comportamento, os dados e a ordem atuais — nenhuma funcionalidade nova, nenhuma removida
- [ ] **REORG-03**: Nenhuma seção extraída instancia `useOpcoesMcp` de novo — todo dado chega por prop do orquestrador (`OpcoesScreen.jsx`)
- [ ] **REORG-04**: `curadoriaAtiva` continua gateado por `tab` em `App.jsx`, nunca promovido a gate por seção/job — não pode reintroduzir o bug que a Fase 32 corrigiu (fetch pago amarrado à visita de uma tela)
- [ ] **REORG-05**: Guardiões de teste que dependem de ordem/posição por arquivo (`test_opcoes_subabas_ui.mjs`, `test_opcoes_consolidacao_ui.mjs`, `test_opcoes_analisar_ui.mjs`, `test_opcoes_vigias_ui.mjs`, `test_opcoes_mcp_aba_ui.mjs`) são atualizados junto com a extração, sem afrouxar a garantia que cada um verifica
- [ ] **REORG-06**: O guardrail CVM de manchete (hoje escopado só a `SubAbaOperar`) passa a cobrir qualquer seção nova que renderize `.manchete` — nenhuma seção nova fica fora do guardião
- [ ] **REORG-07**: `top`/`meta` (seleção determinística do motor) permanecem imutáveis e passados por referência/índice a qualquer seção nova — nenhuma seção nova reordena ou filtra a curadoria por conveniência de exibição

### Navegação (NAV) — Fase B: hub + workspace

- [ ] **NAV-01**: Sub-aba "Setups" abre em modo hub (frase-ponte + Bloco A + Bloco B + vigias + setups salvos) quando nenhum ticker está selecionado
- [ ] **NAV-02**: Selecionar um ticker troca para modo workspace (análise manual do ticker + comparação de vencimentos), sem os blocos de descoberta cross-carteira
- [ ] **NAV-03**: Workspace tem um caminho de volta claro ao hub — um botão, sem breadcrumb nem histórico de navegação
- [ ] **NAV-04**: A frase-ponte (mitigação regulatória D-05) permanece fisicamente adjacente ao Bloco B em qualquer novo arranjo do hub — nunca separada por gate ou rolagem
- [ ] **NAV-05**: Os jobs "analisar ticker", "comparar vencimentos" e "gerenciar setups salvos" continuam compartilhando uma única leitura paga (3 chamadas MCP) — trocar entre eles dentro do workspace não paga de novo (decisão confirmada com o Alex: manter custo atual)
- [ ] **NAV-06**: Estados de erro/degradado hoje visíveis independente de posição na rolagem (ex.: MCP fora do ar) continuam visíveis independente de qual seção o usuário está olhando — nenhum aviso crítico fica isolado numa seção fechada

## v2 Requirements

Deferido, decidido em conversa antes deste milestone — fora do roadmap atual.

### Personalização (PERS)

- **PERS-01**: Explicação com profundidade adaptativa (progressive disclosure) — alvo inicial: a frase-ponte, que hoje nunca colapsa
- **PERS-02**: Modelo de progresso do aprendiz, escopado a conceitos de opções (venda coberta, put de proteção, collar, razão prêmio/perda)
- **PERS-03**: Desafio personalizado por padrão observado no comportamento do usuário — risco regulatório de soar recomendação, precisa de desenho cuidadoso de texto antes de virar requisito v1

## Out of Scope

| Feature | Reason |
|---------|--------|
| Router / URLs por job | App não usa router, decisão de arquitetura já travada na v1.5; navegação por estado (`ticker`) já resolve o drill-down sem precisar de rota |
| Terceiro nível de abas aninhadas dentro de "Setups" | App já está em 2 níveis (bottom nav → Setups/Operar); pesquisa (UX Planet, LogRocket, Design Monks) converge em não passar disso |
| Layout multi-painel estilo terminal profissional (Bloomberg-like) | Usuário do Boris+ é leigo aprendendo, não trader profissional — contradiz o Core Value |
| Busca universal "ir para qualquer coisa" | Não existe hoje, não é reorganização — seria feature nova |
| Auto-refresh contínuo do hub | Conflita com a disciplina de frescor/staleness já estabelecida (princípio 3 do CLAUDE.md) |
| Cada job pagando a própria leitura MCP (em vez de leitura compartilhada) | Decidido com o Alex: manter uma leitura só para os 3 jobs, custo atual não deve subir |
| Fechar o backlog B2 (estado não sobrevive à troca de aba) | Dívida pré-existente (Fase 26, v1.4), não causada por esta reorganização — a pesquisa recomenda aproveitar a fase pra fechar, mas isso é feature/correção nova, não reorganização; fica registrado aqui para decisão futura, não incluído sem pedido explícito |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| REORG-01 | Phase 33 | Pending |
| REORG-02 | Phase 33 | Pending |
| REORG-03 | Phase 33 | Pending |
| REORG-04 | Phase 33 | Pending |
| REORG-05 | Phase 33 | Pending |
| REORG-06 | Phase 33 | Pending |
| REORG-07 | Phase 33 | Pending |
| NAV-01 | Phase 34 | Pending |
| NAV-02 | Phase 34 | Pending |
| NAV-03 | Phase 34 | Pending |
| NAV-04 | Phase 34 | Pending |
| NAV-05 | Phase 34 | Pending |
| NAV-06 | Phase 34 | Pending |

**Coverage:**
- v1 requirements: 13 total
- Mapped to phases: 13
- Unmapped: 0 ✓

---
*Requirements defined: 2026-09-19*
*Last updated: 2026-09-19 after roadmap creation (Phase 33 + Phase 34, full coverage)*
