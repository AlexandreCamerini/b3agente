# Requirements — Milestone v1.4 Opções v2

Base completa da decisão: `.planning/seeds/opcoes-v2-setups-propostos-via-b-mcp.md`
e `.planning/notes/opcoes-v2-b-mcp-exploracao.md`.

## v1.4 Requirements

### Navegação (NAV)

Revisado em 2026-09-03 após mockup + `navigation-specialist`: a barra
inferior real tem 5 abas (não 4, como presumido em 01/09); Candidato A
("aba própria") descartado. Ver `.planning/notes/opcoes-v2-b-mcp-exploracao.md`
seção "Navegação" pro histórico da decisão original, preservado.

- [ ] **NAV-01**: Usuário vê, no topo de Posições/Portfólio, uma tira
  horizontal "Oportunidades de opções" agregando todas as propostas ativas
  no momento — sem aba nova na navegação inferior.
- [ ] **NAV-02**: Cada item da tira abre o detalhe completo dentro da
  posição correspondente em Posições — nunca uma estrutura sobre ticker sem
  posição real na carteira do usuário.
- [ ] **NAV-03**: Quando não há nenhuma proposta ativa (sem cobertura
  elegível, ou cobertura elegível mas sem setup técnico ativo hoje), a tira
  comunica esse estado vazio claramente, com o motivo — nunca desaparece
  silenciosamente.

### Biblioteca de estruturas (LIB)

- [x] **LIB-01**: Usuário pode receber proposta de venda coberta (covered
  call) sobre uma posição comprada existente.
- [x] **LIB-02**: Usuário pode receber proposta de put de proteção
  (protective put) sobre uma posição comprada existente.
- [x] **LIB-03**: Usuário pode receber proposta de collar (trava protetora)
  combinando as duas pernas acima sobre uma posição comprada existente.

### Motor / arquitetura (ENG)

- [x] **ENG-01**: O motor de proposta seleciona o contrato pelo critério já
  em produção — `liquidity_score ≥ 40` + strike extremo, mesma régua de
  `server/app/opcoes_lastreadas.py` — nunca pelo critério por delta do
  `estruturas.py` do b-mcp.
- [x] **ENG-02**: O cálculo de payoff de N pernas (custo líquido, ganho/perda
  máximos, breakevens, delta somado) usa aritmética portada de `calculos.py`
  do b-mcp, adaptada e testada dentro do repo do Boris.
- [x] **ENG-03**: O motor não faz nenhuma chamada de rede ao processo/serviço
  b-mcp em runtime — toda fonte de dado passa por `mydata_client.py`
  existente.
- [x] **ENG-04**: A lógica de screening de cadeia e avaliação de estrutura
  fica atrás de duas funções de limite interno — `rastrear()` e `avaliar()`
  — desenhadas no vocabulário do contrato ADR-004/`mydata_client.py`
  (prêmio/strike/delta/tipo), permitindo trocar a implementação local pelas
  chamadas ao b-mcp (`find_tradable_options`/`evaluate_option_structure`) no
  futuro sem redesenho — troca de corpo de função.
- [x] **ENG-05**: Qualquer chamada nova ao hub mydata feita pelo motor de
  opções (screening, avaliação) passa pelo lock existente
  (`mydata_budget.reservar()`) — nunca um canal paralelo.
- [x] **ENG-06**: O gatilho técnico que dispara a avaliação de proposta
  reusa o motor de setups já existente do Boris (Radar/`setups.py`
  server-side, `indicators.py`) — não porta nem depende da DSL de setups
  técnicos do b-mcp.

### Fluxo de aceite (FLOW)

- [ ] **FLOW-01**: Usuário vê os dados da proposta (estrutura, pernas,
  prêmio, breakeven, ganho/perda máximos) antes de decidir.
- [ ] **FLOW-02**: Usuário aceita ou recusa a proposta explicitamente —
  nenhuma execução automática.
- [ ] **FLOW-03**: Ao aceitar, a execução usa o mesmo motor de ordens de
  opções lastreadas já em produção (Fase 14, `store.py`) — sem automação
  nova.
- [ ] **FLOW-04**: Toda proposta declara a fonte e o horário do dado usado
  (frescor) — princípio 3 do CLAUDE.md, nunca dado silenciosamente
  desatualizado.

### Motor multi-candidato (MULTI)

Registrado em 2026-09-03 como Fase 19 (nova fase, decisão explícita do
Alex — "no detalhamento da proposta deveriamos poder mostrar uma série de
setups de opções para a análise do ativo"). Estende ENG-01..06 (Fase 15,
já verificado, não reaberto) — motor hoje devolve UMA estrutura por
posição via regra fixa de `plano.decisao`; estes requirements pedem N.
Success criteria detalhados ficam para `/gsd-plan-phase 19`.

- [x] **MULTI-01**: O motor de proposta (`opcoes_lastreadas.propor()` e a
  camada `opcoes_motor.rastrear()`/`avaliar()`) pode devolver mais de um
  candidato de estrutura (venda coberta, put de proteção, collar) para a
  mesma posição, quando mais de um fizer sentido pela análise técnica
  atual — não mais uma escolha única e fixa.
- [ ] **MULTI-02**: O detalhe da posição em Posições mostra os N candidatos
  lado a lado (mesmo padrão visual da tira "Oportunidades" da Fase 18);
  usuário aceita exatamente um por avaliação — nunca mais de um executado
  simultaneamente para a mesma posição.

## Future Requirements (deferred)

- Setup customizado pelo usuário (fora do v1 — biblioteca fixa por
  enquanto).
- Integração MCP real com o b-mcp (Estratégia C) — condicionada à aprovação
  de `~/dev/MCP/docs/plano-mcp-servico.md` pelo Alex. Quando aprovado, troca
  o corpo de `rastrear()`/`avaliar()` (ENG-04), sem reabrir requirements.
- Estruturas adicionais além das 3 do v1 (ex.: mais combinações de pernas),
  se a demanda de produto justificar.

## Out of Scope

- **Straddle/strangle coberto** — liquidez de opções B3 fora dos blue-chips
  já é curta pra 1 perna, pior pra 2 pernas simultâneas de lados opostos.
- **Cash-secured put** — inicia posição em vez de proteger uma existente,
  contradiz a régua "só sobre cobertura real" que é o próprio enunciado da
  feature (questão de definição, não de liquidez).
- **DSL de setups técnicos do b-mcp (`setups.py`)** — o Boris já mediu
  (ADR-016) que sinal ingênuo de confluência perde dinheiro e reconstruiu
  seleção por peso histórico (ADR-017); portar a DSL sem passar pelo
  `scripts/backtest_sinal.py` reintroduziria um defeito já corrigido. O
  gatilho técnico já vem do Radar (ver ENG-06).
- **Plano comercial (gratuito vs. pago) desta feature** — mesmo padrão do
  v1.3, que ativou infraestrutura sem loja/IAP ainda; decisão comercial
  separada, fora deste milestone.

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| NAV-01 | Phase 18 | Pending |
| NAV-02 | Phase 18 | Pending |
| NAV-03 | Phase 18 | Pending |
| LIB-01 | Phase 16 | Complete |
| LIB-02 | Phase 16 | Complete |
| LIB-03 | Phase 16 | Complete |
| ENG-01 | Phase 15 | Complete |
| ENG-02 | Phase 15 | Complete |
| ENG-03 | Phase 15 | Complete |
| ENG-04 | Phase 15 | Complete |
| ENG-05 | Phase 15 | Complete |
| ENG-06 | Phase 15 | Complete |
| FLOW-01 | Phase 17 | Pending |
| FLOW-02 | Phase 17 | Pending |
| FLOW-03 | Phase 17 | Pending |
| FLOW-04 | Phase 17 | Pending |
| MULTI-01 | Phase 19 | Complete |
| MULTI-02 | Phase 19 | Pending |

Coverage: 18/18 v1.4 requirements mapped. No orphans.
