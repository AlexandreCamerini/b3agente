# Requirements: Boris+ (b3-agente) — Milestone v1.7

**Defined:** 2026-09-20
**Core Value:** O usuário leigo sai do Modo Estudo entendendo de verdade como o mercado funciona — não decorou uma resposta, aprendeu o raciocínio — e só então tem acesso a automações do Modo Operador.

Base: uso real em produção do milestone v1.6 (navegação hub+workspace) pelo
Alex em 2026-09-20, especificação técnica do motor/gráfico de payoff já
fechada por ele, screenshot de produção confirmando 3 bugs reais no gráfico
atual. Confirmado via AskUserQuestion na mesma sessão (resumo do milestone,
decisão de pular pesquisa, lista de requisitos).

## v1 Requirements

Corrigir a jornada de montar/analisar uma estrutura de opções dentro do
workspace (v1.6) e tornar o gráfico de payoff — e sua explicação —
matematicamente correto e genérico para qualquer estrutura, sem promover
recomendação.

### Jornada do Workspace (JORN)

- [ ] **JORN-01**: Usuário vê indicação clara de progresso/etapas ao montar uma estrutura em Analisar, do ticker escolhido até "ver possibilidades"
- [ ] **JORN-02**: O botão que revela as estruturas possíveis é visualmente proeminente e seu propósito é evidente sem explicação externa
- [ ] **JORN-03**: Comparar e Setups salvos recebem a mesma clareza de passos que Analisar

### Motor de Payoff (PAYOFF)

- [ ] **PAYOFF-01**: Motor genérico calcula resultado/breakevens/ganho-perda máxima/domínio X-Y para qualquer combinação de legs (`kind`/`side`/`strike`/`premium`/`qty`/`expiry`), sem lógica por nome de estratégia — proibido switch/case ou dicionário de textos por estratégia
- [ ] **PAYOFF-02**: Motor cobre os casos-limite: compra/venda seca (1 perna), venda descoberta/ratio spread (perda ilimitada), travas de alta/baixa com calls/puts, borboleta/condor (2 breakevens + platô central), straddle/strangle, covered call/collar (perna de ação sem strike), box (curva plana não-zero), calendário/diagonal (vencimentos diferentes — degrada com honestidade, nunca aproxima linearmente), lotSize/quantidades assimétricas, entrada degenerada (prêmio zero/strikes iguais — recusa com mensagem clara, nunca NaN)
- [ ] **PAYOFF-03**: Caso golden (trava de alta com calls, strikes 49,17/49,67, débito 0,25, lote 100 → breakeven 49,42, ganho/perda máx R$ 25,00, 3 segmentos, nenhum ilimitado) é teste de regressão nomeado

### Gráfico de Payoff (CHART)

- [ ] **CHART-01**: Linha do zero tracejada rotulada "R$ 0"; eixo vertical com escala visível (resultado por ação, legenda "multiplique por lotSize para o lote")
- [ ] **CHART-02**: Todo strike e todo breakeven marcado e rotulado no eixo; spot marcado "hoje {preço}"
- [ ] **CHART-03**: Segmento ilimitado termina em seta aberta na borda + rótulo "sem teto"/"sem piso" — nunca desenha platô falso onde o risco é ilimitado
- [ ] **CHART-04**: Domínio X (min/max strike + margem `max(12% do span, 4% do spot)`, spot sempre dentro) e domínio Y (inclui zero, +15% do extremo finito) nunca cortam um platô real
- [ ] **CHART-05**: Valor de marcação a mercado ("hoje · valor de mercado da estrutura") aparece separado e rotulado, distinto do resultado "no vencimento · {data}" — regressão confirmada em produção (screenshot 2026-09-20)

### Camada Explicativa (EXPL)

- [ ] **EXPL-01**: Texto explicativo é derivado dos segmentos da curva calculada, percorrida da esquerda para a direita com a frase do segmento onde o spot está vindo primeiro — nunca por nome de estratégia
- [ ] **EXPL-02**: Vocabulário do corpo explicativo livre de jargão técnico banido (strike, prêmio, delta, theta, volatilidade implícita, exercício, rolagem, ITM/OTM/ATM, "perna")
- [ ] **EXPL-03**: Razão G/P no texto usa o mesmo número exibido em tela — regressão confirmada em produção (screenshot mostra "1:1,00" exibido vs. "1:0,67" no texto)

## v2 Requirements

Deferido, decidido em conversa antes deste milestone — fora do roadmap atual.

### Personalização (PERS)

- **PERS-02**: Modelo de progresso do aprendiz, escopado a conceitos de opções (venda coberta, put de proteção, collar, razão prêmio/perda)
- **PERS-03**: Desafio personalizado por padrão observado no comportamento do usuário — risco regulatório de soar recomendação, precisa de desenho cuidadoso de texto antes de virar requisito v1

## Out of Scope

| Feature | Reason |
|---------|--------|
| Reorganização estrutural das sub-abas | v1.6, já entregue (Fases 33-34) |
| Migração do motor de opções para um MCP único | `revisao-arquitetura-mcp-ecossistema-b3.md`, revisão de arquitetura maior e separada, prioridade alta mas tratada à parte por decisão do Alex |
| Modelo de progresso do aprendiz / desafio personalizado (PERS-02/03) | Mesma decisão do v1.6: não personalizar antes de a explicação básica estar correta |
| Precificação de opções com vencimentos diferentes (calendário/diagonal) | O motor degrada com honestidade (estado explícito, sem gráfico) em vez de aproximar — precificação real fica fora de escopo até haver modelo disponível |
| Biblioteca de charting de terceiros | Gráfico é SVG próprio por decisão do Alex — proibido puxar dependência nova para isso |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| JORN-01 | Phase 35 | Pending |
| JORN-02 | Phase 35 | Pending |
| JORN-03 | Phase 35 | Pending |
| PAYOFF-01 | Phase 36 | Pending |
| PAYOFF-02 | Phase 36 | Pending |
| PAYOFF-03 | Phase 36 | Pending |
| CHART-01 | Phase 37 | Pending |
| CHART-02 | Phase 37 | Pending |
| CHART-03 | Phase 37 | Pending |
| CHART-04 | Phase 37 | Pending |
| CHART-05 | Phase 37 | Pending |
| EXPL-01 | Phase 37 | Pending |
| EXPL-02 | Phase 37 | Pending |
| EXPL-03 | Phase 37 | Pending |

**Coverage:**
- v1 requirements: 14 total
- Mapped to phases: 14 (Phase 35: JORN-01..03; Phase 36: PAYOFF-01..03; Phase 37: CHART-01..05, EXPL-01..03)
- Unmapped: 0

---
*Requirements defined: 2026-09-20*
*Last updated: 2026-09-20 — Roadmap gerado (`/gsd-roadmapper`): 14/14 requirements mapeados às Fases 35-37 (100% coverage), traceability atualizada de TBD para os números de fase reais.*
