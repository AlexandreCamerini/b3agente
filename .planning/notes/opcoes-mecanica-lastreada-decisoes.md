---
title: Opções lastreadas — decisões de exploração (venda coberta + put de proteção)
date: 2026-08-30
context: /gsd-explore sobre funcionalidades de opções (incluindo UI/UX)
---

# Opções lastreadas — decisões de exploração

Exploração Socrática com o Alex sobre o futuro da mecânica de opções do
Boris+. Fecha um pivô de escopo: de "compra especulativa de qualquer
contrato líquido" para "operação lastreada por posição real da carteira,
guiada por análise técnica do próprio ativo".

## Escopo da mecânica

- **Só duas operações, ambas lastreadas por posição real na carteira:**
  venda de CALL coberta (gera prêmio, trava upside) e compra de PUT de
  proteção (paga prêmio, protege downside). Nenhuma perna especulativa
  desvinculada de uma posição existente.
- Setups/propostas de operação vêm da análise técnica do ativo-lastro que já
  está na carteira — não de uma varredura de qualquer ticker líquido.

## O que já existe hoje (auditado em código, 2026-08-30)

Três peças distintas, nenhuma delas implementa o que foi decidido acima:

1. **Motor real de opções** (`store.py buy_option/sell_option`, UI
   `OpcoesCamada` em `App.jsx`) — long-only (compra CALL ou PUT), sem
   nenhum vínculo com a carteira de ações. `sell_option` é só "vender pra
   fechar" — não existe "vender pra abrir" (lançar/escrever opção), então
   venda coberta não tem fundação nenhuma hoje.
2. **Motor de sugestão de put** (`put_bridge.py`/`put_lifecycle.py`,
   tabela `put_suggestions`, ADR-021/022) — vinculado a um ticker da
   carteira e a um gatilho técnico de baixa, mas é deliberadamente uma
   simulação-sombra: nunca mexe na carteira real, nunca aparece pro
   usuário, estruturalmente incapaz de virar posição real (sem campo de
   quantidade, ADR-021 Decisão 2).
3. `setOptionStop`/`setOptionAlvo` (`App.jsx:7512-13` + backend) — **código
   morto**: existem completos, mas nenhuma UI os invoca. Stop/alvo de
   posição de opção hoje são só leitura (`OpcoesCamada`).

## Decisões fechadas nesta exploração

- **D-1 — Redesenho do zero.** O motor de sugestão de put existente
  (put_bridge/put_lifecycle) **não é aproveitado** como base — a decisão de
  mantê-lo como sombra invisível (ADR-021) não é herdada pela mecânica
  nova. `setOptionStop`/`setOptionAlvo` também não são "consertados"
  isoladamente — o redesenho os substitui.
- **D-2 — Sem simulação de atribuição/exercício.** Quando a CALL coberta
  vence ITM, o motor **nunca** simula exercício (nunca vende as ações
  lastro pelo strike). O produto assume que a call sempre é fechada
  (recomprada) antes do vencimento. Implicação de implementação: se o
  usuário não fechar manualmente e a call vencer ITM, o motor precisa de
  uma regra determinística de liquidação em dinheiro (equivalente ao valor
  intrínseco) que nunca toque a posição de ações — não foi especificada em
  detalhe, fica para o planejamento da fase.
- **D-3 — Trava de lastro.** Enquanto a CALL coberta está aberta, o lote de
  ações que a lastreia fica **bloqueado para venda** na Carteira. Implica
  mudança de modelo de dados: posição de ação precisa de um campo de
  quantidade travada/reservada, distinto da quantidade livre — mexe em
  `store.py`, `finance.js` e nos dois stores (`deviceStore`/`serverStore`,
  paridade obrigatória).
- **D-4 — UX: proposta + cadeia expansível.** O motor escolhe um contrato
  com base no técnico + lastro disponível e propõe pronto ("vender N calls
  strike Y por Z"), no mesmo estilo de linguagem de decisão que o card de
  ação já usa (manchete única). A cadeia completa continua disponível,
  expansível, para quem quiser escolher outro strike/vencimento
  manualmente. Não é só navegador de cadeia (estado atual) nem só proposta
  fechada — os dois convivem.
- **D-5 — Modo.** Estudo explica a proposta como conteúdo didático ("se
  você tivesse feito isso...") sem CTA de executar; Operador ganha os CTAs
  reais de vender CALL / comprar PUT. Mesmo padrão do storyline
  Estudo-ensina/Operador-executa já estabelecido no produto.
- **D-6 — Patrimônio Total.** Diferente do estado atual (`portfolioMetrics()`
  em `finance.js` exclui `optionPositions` do Patrimônio Total/P&L da
  Carteira), a mecânica lastreada **entra** no cálculo agregado — prêmio e
  P&L da operação de opção passam a compor o total, não só aparecer
  isolado dentro do card do ativo.
- **D-7 — Fonte de dados: sem mudança de ADR.** mydata confirmado como
  única fonte de opções B3 (ADR-004/ADR-020 intactos, não reabertos). Ação
  diário/spot continua brapi master (ADR-008 intacto). Intraday continua
  Yahoo primário (ADR-001 intacto) — o Alex cogitou inverter pra brapi
  primário, mas voltou atrás ao saber que isso exigiria upgrade pago pra
  brapi Pro (R$116,66/mês, revertendo o orçamento US$0 travado no ADR-001);
  decisão de manter Yahoo primário foi confirmada explicitamente.
- **D-8 — Timing: fase agora, dormente.** Entra no roadmap já — motor+UI
  ficam prontos e testados contra payload mock/degradado, mas a execução
  real só libera de fato quando a virada de produção `B3_OPTIONS_PROVIDER=
  mydata` acontecer. Mesmo padrão que outras peças do produto já usam
  (constrói pronto, ativa quando a fonte virar).

## Dependências e bloqueios (não resolvidos aqui)

- **Virada de produção do mydata** (`B3_OPTIONS_PROVIDER=mydata`) está
  represada por dois motivos medidos, não achismo (ADR-020 §Medição):
  pico de requisições por minuto projetado em 148 contra o teto de 60/min
  da chave (mitigação de espaçamento já feita em código, 2026-08-28, falta
  confirmar a perna ao vivo com `MYDATA_TOKEN` real); e **WR-01** — race
  condition check-then-debit em `mydata_budget.pode_gastar()`/`debita()`,
  até 3 consumidores concorrentes possíveis, decisão de arquitetura
  pendente desde o fechamento do v1.2 (2026-08-28). Ver todo
  `decidir-wr01-mydata-budget.md`.
- Enquanto a cadeia de opções real não responde (Yahoo hoje devolve vazio
  pra B3; mydata ainda não está ligado em produção), a fase inteira só pode
  ser testada contra payload mock/degradado — não há ambiente real pra
  validar contra até a virada acontecer.

## Não decidido / fora desta exploração

- Fórmula exata de liquidação forçada quando a call coberta vence ITM sem
  fechamento manual (ver D-2) — fica para o planejamento da fase.
- Proventos via mydata (escopo `provento_b3` já liberado na chave, nenhum
  consumidor no código ainda) — mencionado, não aprofundado, não faz parte
  do escopo desta mecânica.
