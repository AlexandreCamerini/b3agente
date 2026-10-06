---
phase: 48-opcoes-caminho-b
plan: 04
subsystem: opcoes-motor
tags: [opcoes_escada, payoff, degraus, tdd]
requires: [48-01]
provides:
  - "server/app/opcoes_escada.py: OBJETIVOS, TIPO_DO_OBJETIVO, objetivos, escolher_degraus, pernas_do_candidato, leitura, degrau_do_candidato, celulas_da_cadeia, normalizar_barras"
affects: [48-05, 48-06, 48-07, 48-08, 48-09]
key-files:
  created: [server/app/opcoes_escada.py, server/tests/test_opcoes_escada.py]
  modified: [server/tests/test_opcoes_fronteira.py]
requirements-completed: [OPC-03, OPC-05]
metrics:
  completed: 2026-10-05
---

# Phase 48 Plan 04: Motor puro da escada Summary

Motor determinístico `opcoes_escada` que entrega, por degrau, pior/melhor caso, equilíbrio, piso/teto, prêmio e líquido (total e por ação), série do gráfico, marcadores, legenda, tabela e aria, tudo via `opcoes_payoff` e `skill_ref.opcoes_escada_txt`.

## Commits
- a2c327c7 test(48-04): RED (24 testes, ImportError)
- cab5c42e feat(48-04): GREEN (módulo + `opcoes_escada` na lista do guardião de fronteira)

## Entregue
- Contas de referência conferidas à mão: put protetora (perda 855,00; eq. 38,85), call coberta (ganho 780,00; perda 11.220,00; eq. 37,40) e collar (perda 675,00; ganho 525,00; líquido -75,00; eq. 38,25).
- `leitura` devolve números `None` + `motivo` quando prêmio é ausente/<=0 (nunca 0.0); gráfico `None` + `motivoSemGrafico` quando `cenarios_da_estrutura` devolve None, mantendo os números.
- Série <= 241 pontos, reamostrada de forma determinística preservando piso, equilíbrio, teto, spot, PM e extremos; `diferenca` em magnitude e `efeito` calculados no backend.
- Marcadores com numeração fixa 1-5; ausentes listados com texto (`ausente_*`); legenda com setor/kb.
- `celulas_da_cadeia`: mesma régua da escada (puts <= spot decrescente, calls > spot crescente, até 5, índices 0/meio/último), id via `id_candidato`, sem gráfico; faltantes viram célula com `id None` e motivo.

## Decisões / premissas
- `marcadores[i]` tem `y` (ponto plotado) e `valor` (número citado na legenda): na perda máxima sem piso o ponto fica em xMin, mas o valor é a perda real (ação a zero).
- `termos` (`opc_premio`/`opc_perda_maxima`) saem como números crus, só com chaves do allowlist do 48-02; chave sem valor é omitida. `estado` = pago/recebido pelo sinal do líquido; com_piso/sem_piso.
- `premioPago`/`premioRecebido` são `None` quando não há perna daquele lado (não 0.0). `perdaMaxima`/`ganhoMaximo` são magnitudes; `liquido` tem sinal (negativo = custa).
- Frase da legenda (`frase`) e `fraseRisco` usam sempre o total (nas N ações); `aria` tem as duas unidades.
- `escolher_degraus` devolve 1-3 candidatos; o chamador (48-06) atribui os rótulos por índice.

## Deviations from Plan
None - plano executado como escrito. Única adição: `opcoes_escada` acrescentado a `_MODULOS_NOVOS_FASE_15` em `test_opcoes_fronteira.py` (previsto na Task 2).

## Verificação
- `pytest tests/test_opcoes_escada.py tests/test_opcoes_fronteira.py tests/test_mcp_guardioes.py tests/test_cartao_cenarios.py tests/test_opcoes_payoff.py`: 207 passed.
- grep de rede/relógio/db no módulo: 0; referências a payoff/cenarios/texto: 6.
- Suíte canônica e `vite build` não rodados (plano só toca backend; suíte é do orquestrador).

## Known Stubs
Nenhum.

## Threat Flags
Nenhum (T-48-11..14 mitigados: prêmio inválido vira None; texto só de skill_ref; série <= 241; fronteira guardada).

## Self-Check: PASSED
- opcoes_escada.py e test_opcoes_escada.py presentes; commits a2c327c7 e cab5c42e existem; STATE.md/ROADMAP.md intocados.
