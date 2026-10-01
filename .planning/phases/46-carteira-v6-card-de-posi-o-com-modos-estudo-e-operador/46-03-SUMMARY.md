---
phase: 46-carteira-v6-card-de-posi-o-com-modos-estudo-e-operador
plan: 03
subsystem: motor puro do card v6
tags: [cartao_posicao, opcoes_payoff, simulador, grade, didatica, tdd]
requires: ["46-01"]
provides:
  - "server/app/cartao_posicao.py: leitura_plano, cenarios_da_estrutura, didatica_estrutura, ALTA_FORTE_FATOR, TICK, MAX_PONTOS_GRADE, TERMO_KB"
affects: [46-04]
key-files:
  created:
    - server/app/cartao_posicao.py
    - server/tests/test_cartao_posicao.py
    - server/tests/test_cartao_cenarios.py
decisions:
  - "Grade em ticks inteiros (sem deriva de float); passo cresce até len(pontos) <= 1200 incluindo os 4 pontos nomeados inseridos"
  - "Conta (fórmula fechada) só para call coberta simples com qtd(ação) == qtd(CALL); demais estruturas: conta None"
  - "Termo sem caso ou fora de TERMO_KB vira texto simples (D-09), p.ex. 'teto' na put de proteção"
  - "Dado ausente que alimenta uma frase troca a frase por 'aguardando o cálculo do app' (nunca '0,00')"
metrics:
  tasks: 2
  completed: 2026-10-01
---

# Phase 46 Plan 03: Motor puro do card v6 Summary

`cartao_posicao.py` (494 linhas, sem rede/banco/LLM/relógio) reexpõe o plano da posição e os cenários de uma estrutura sobre `opcoes_payoff.resultado_no_vencimento`, com a mesma `entrada` que `estrutura_posicao._faixa` monta; toda frase vem de `skill_ref`.

## Tarefas

| # | Tarefa | Commits |
|---|--------|---------|
| 1 | leitura_plano + didática de posição simples | c14fb388 (RED), 5c8ca1b4 (GREEN) |
| 2 | cenarios_da_estrutura + didatica_estrutura | 704c88c5 (RED), b9776766 (GREEN) |

## Verificação

- `pytest tests/test_cartao_posicao.py tests/test_cartao_cenarios.py tests/test_skill_ref.py`: 69 ok.
- UGPA3: be 38,01, K 42,25, alta forte 46,05, até BE −5,2%, até K +5,4%, ganho 4.240, perda 38.010. CXSE3: be 19,81, ganho 1.210, perda 19.810.
- Todo `resultado` da grade/simulador/payoff é igual a `round(resultado_no_vencimento(entrada, preco), 2)` (teste de D-01).
- Greps de aceite: 3 constantes nomeadas, `1.09` só na constante, 0 imports de I/O.
- Teto de 1.200 pontos testado com K 500 / spot 480.

## Deviations from Plan

Nenhuma de regra. Notas: (a) `distStopPct`/`distAlvoPct` são calculados também em plano parcial (só stop/só alvo) quando há preço; (b) `acoes`/`pernas` de `didatica_estrutura` aceitam `premioEntrada` ou `premio`.

## Known Stubs

Nenhum.

## Notas para o orquestrador

`git status` mostrava `web/src/App.jsx` modificado e `.planning/quick/261001-0or-identidade-modo-opcao-c/` não rastreado antes/durante a execução; não são deste plano e não foram tocados nem commitados. STATE.md/ROADMAP.md intocados.

## Self-Check: PASSED
