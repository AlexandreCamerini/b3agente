---
phase: 50-marcos-do-plano-stop-alvo-e-entrada-pelo-motor
plan: 06
subsystem: card-e-opcoes
tags: [cartao_posicao, opcoes_lastreadas, opcoes_motor, marcos, D-05, D-13, D-16]
requires: [50-01, 50-02]
provides:
  - cartao_posicao.leitura_plano com plano "invalido" (motivoInvalido, textoInvalido) e rrPlano
  - opcoes_motor.rastrear relacao "acima_ou_igual"
  - opcoes_lastreadas.propor/_propor_collar ancorados em alvo/stop com campo "ancora"
key-files:
  modified: [server/app/cartao_posicao.py, server/app/opcoes_motor.py, server/app/opcoes_lastreadas.py, server/tests/test_cartao_posicao.py, server/tests/test_cartao_proximidade.py]
  created: [server/tests/test_marcos_opcoes.py]
metrics:
  tasks: 2
  completed: 2026-10-22
---

# Phase 50 Plan 06: Card e opções leem os marcos do motor

Card v6 passa a devolver "plano inválido" com motivo (PM 23,01 / stop 23,36 / alvo 21,58) e R:R em dois rótulos (rr restante x rrPlano da entrada); as opções lastreadas ancoram call no alvo e put no stop, com fallback ao spot declarado em `ancora`.

## Commits
- f94465a9 feat(50-06): leitura_plano com plano invalido e rrPlano
- 9b24ab08 feat(50-06): strikes das opcoes lastreadas ancorados nos marcos do plano

## Testes
- test_cartao_posicao + test_cartao_proximidade + test_skill_ref: 98 passed
- test_marcos_opcoes.py: 11 passed
- tests/test_opcoes_*.py + test_options*.py: 889 passed, 1 skipped, 1 failed (test_options_provider_yahoo::...degrades_instead_of_raising_on_yahoo_401, rede/Yahoo no sandbox, fora do escopo; arquivos não tocados)

## Deviations from Plan

1. [Rule 1 - guardião] test_cartao_proximidade.py: 4 linhas da tabela (alvo <= PM, ex. PM 30 / stop 20 / alvo 28) esperavam perto_alvo/perto_stop pelo fallback na régua stop->alvo. Essa é exatamente a geometria que a fase declara inválida (plano "invalido", proximidade None). Linhas mantidas, expectativa atualizada para None, com nota "Fase 50" no arquivo.
2. [Rule 2 - segurança da âncora] `_marcos_validos` exige também alvo > spot e stop < spot para ancorar (senão o strike viraria ITM e deixaria de ser a perna OTM); caso contrário cai no spot declarado. Além de validar_marcos(avg=) do plano.
3. resultadoNoStop/resultadoNoAlvo também ficam None em plano inválido (consistente com "leituras dependentes do plano None"). distStopPct/distAlvoPct permanecem (são distâncias ao preço, não dependem da coerência).
4. Nenhum guardião de proposta positiva fazia igualdade de dict inteiro; test_opcoes_lastreadas_proposta.py não precisou mudar (arquivo não modificado). Retornos negativos intocados.

## Diferido (D-19)
put_bridge.py (COLCHAO_PCT) e opcoes_curadoria.py NÃO ancorados nos marcos nesta fase; não tocados.

## Known Stubs
Nenhum.

## Self-Check: PASSED
