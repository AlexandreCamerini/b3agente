---
phase: 30-curadoria-ia-melhores-estruturas
plan: 01
subsystem: opcoes-curadoria
tags: [opcoes, venda-coberta, ranking-deterministico, motor-puro]
dependency-graph:
  requires: [opcoes_motor.rastrear, opcoes_motor.avaliar, opcoes_lastreadas._dias_ate/_bloco_liquidez, options_quant.LIQUIDEZ_NEGOCIAVEL, store.qty_livre, skill_ref.opcoes_lastreadas_txt]
  provides: [opcoes_curadoria.candidatos_da_posicao, opcoes_curadoria.rankear, opcoes_curadoria.exigir_ranking, opcoes_curadoria.narrativa_system, opcoes_curadoria.narrativa_user]
  affects: [30-02 (varredura cross-posição consumirá candidatos_da_posicao), 30-03 (rota de narração consumirá rankear/exigir_ranking/narrativa_*), 30-04 (bloco de UI consumirá o top rankeado)]
tech-stack:
  added: []
  patterns: [motor puro sem rede/banco/LLM/relógio interno, guardrail estrutural via exigir_ranking (código, não convenção), chave de ordenação total e determinística]
key-files:
  created:
    - server/app/opcoes_curadoria.py
    - server/tests/test_opcoes_curadoria.py
  modified: []
decisions:
  - "Ranking 100% aritmético via opcoes_motor.rastrear()/avaliar() — nenhuma LLM decide ou reordena as 4 melhores (CLAUDE.md princípio 5, D2)"
  - "Universo restrito a venda coberta (D1) — nenhum filtro de put/collar entra no arquivo"
  - "Vários strikes dentro do vencimento único já buscado (D3) — zero chamada de rede nova"
  - "Piso de liquidez NEGOCIAVEL explícito via liquidez_minima (D5) — nunca herda o fallback DIFÍCIL de duas passadas de rastrear()"
  - "exigir_ranking() torna o guardrail 'IA nunca recebe pool não rankeado' comportamento do código, chamado como primeira linha de narrativa_user"
metrics:
  duration: "~50min"
  completed: 2026-09-13
---

# Fase 30 Plano 01: Motor puro da curadoria — candidatos, ranking e narração Summary

Motor puro que enumera candidatos de venda coberta sobre uma cadeia de opções
já em memória, ordena os 4 melhores por razão prêmio/perda máxima com
desempate total e determinístico, e recusa estruturalmente qualquer pool não
rankeado antes de virar prompt de IA.

## O que foi construído

`server/app/opcoes_curadoria.py` (novo, 299 linhas):

- **`candidatos_da_posicao`** — dada uma posição elegível (comprada, lote
  livre >= 100 ações) e uma cadeia ADR-004 já buscada, enumera até `n`
  (default `STRIKES_POR_POSICAO=5`) candidatos de venda coberta via UMA
  chamada a `opcoes_motor.rastrear(..., liquidez_minima=LIQUIDEZ_NEGOCIAVEL)`
  — piso explícito, nunca o fallback de duas passadas. Cada candidato passa
  por `opcoes_motor.avaliar()` (delega a `perfil_da_estrutura`); candidatos
  com `perda_maxima` `None`/`<=0` são descartados (razão indefinida, nunca
  publicada como infinita). Portas fechadas espelham `opcoes_lastreadas.propor`
  byte a byte no motivo e na ordem de checagem, mas SEM a porta de
  setup/plano técnico — D1 define elegibilidade só por lastro, decisão de
  produto documentada em comentário no código.
- **`rankear`** — corta em `TOPO=4`, ordenando por
  `(-razao, -premioUnitario, contractSymbol)`. Chave total: nenhum campo de
  usuário, peso configurável ou saída de LLM participa da ordem.
- **`exigir_ranking`** — validação que `narrativa_user` chama como primeira
  linha; levanta `ValueError` para lista não rankeada (>TOPO itens, `razao`
  fora de ordem, `posicaoNoRanking` incorreto, item sem `razao`, entrada que
  não é lista).
- **`narrativa_system`/`narrativa_user`** — prompts da futura etapa de
  narração (Plano 03 consumirá): prefixo estável por modo com
  `skill_ref.PRINCIPIOS`/`DISCLAIMER`; corpo serializa só os campos
  necessários (T-30-03: sem `curva`, sem dado de conta) na ordem já decidida.

`server/tests/test_opcoes_curadoria.py` (novo, 34 testes): cobre todos os
casos do `<behavior>` das duas tasks, incluindo os dois pontos de rigor
adversarial pedidos (provados por quebra real, não só por leitura de código):

- **Determinismo**: `test_rankear_permuta_entrada_nao_muda_saida` roda 20
  permutações (seed fixa `20260913`) e compara a sequência de
  `contractSymbol` — idêntica em todas. Prova negativa real: removi o
  terceiro critério de desempate (`contractSymbol`) do `sorted()` e rodei a
  suíte — `test_rankear_empate_desempata_por_premio_depois_contractsymbol`
  falhou de verdade (`['MMM','ZZZ','AAA'] != ['MMM','AAA','ZZZ']`),
  confirmando que o teste captura a regressão. Revertido e suíte voltou a
  verde (diff byte-idêntico ao original, confirmado com `diff`).
- **Piso de liquidez explícito**: prova negativa real — removi
  `"liquidez_minima": PISO_LIQUIDEZ` da chamada a `rastrear()` e rodei
  `test_piso_liquidez_explicito_nao_cai_para_dificil`; o teste falhou de
  verdade (um contrato DIFÍCIL de score 45 apareceu no resultado). Revertido
  e suíte voltou a verde.

## Deviations from Plan

None — plano executado exatamente como escrito, com um ajuste textual: as
menções literais a `options_provider` e a `"tipo": "put"` no docstring do
módulo foram reescritas sem o literal exato, porque o acceptance criteria do
próprio plano usa um grep de string crua (`assert 'options_provider' not in
src`) que não distingue código de comentário/docstring — mantendo a menção
literal, o teste de pureza por inspeção falharia mesmo com o módulo
comportando-se corretamente. A intenção documental (por que `options_provider`
não é usado, por que "put" não entra) foi preservada em prosa sem o literal.

## Auth Gates

Nenhum.

## Threat Flags

Nenhuma superfície nova fora do `<threat_model>` do plano — todos os 5
threats (T-30-01 a T-30-05) e o guardião de supply chain (T-30-SC) foram
cobertos pelo desenho já descrito no plano; nenhuma dependência nova, nenhuma
rota HTTP nova, nenhum acesso a dado de conta além do que já circulava em
`opcoes_lastreadas.propor`.

## Known Stubs

Nenhum. Este plano é motor puro consumido por planos futuros (30-02 varredura
cross-posição, 30-03 rota de narração, 30-04 bloco de UI) — não há UI nem rota
HTTP neste plano por desenho (ver `<source_audit>` do 30-01-PLAN.md).

## Verificação

- `bash scripts/executar.sh --testes` → **exit 0** (2828 passed, 5 skipped, 3
  xfailed no pytest; todos os `web/tests/*.mjs` OK) — rodado uma vez ao fim
  de cada task e uma vez final após o split dos commits.
- `server/.venv/bin/python -m pytest server/tests/test_opcoes_curadoria.py -q`
  → 34 passed.
- Pureza por inspeção: `options_provider`, `httpx`, `candle_provider` ausentes
  do arquivo (checado programaticamente).
- `grep -c 'LIQUIDEZ_NEGOCIAVEL'` = 2, `grep -c '"liquidez_minima"'` = 1.
- `grep -c '"tipo": "put"'` (fora de comentário) = 0.
- `-k permuta` → 1 passed; `-k exigir_ranking` → 6 passed (>= 4 exigidos).
- `def exigir_ranking` aparece 1x; `narrativa_user` chama `exigir_ranking`
  na primeira linha do corpo (confirmado por grep e por leitura).

## Instruções para validar localmente

```bash
server/.venv/bin/python -m pytest server/tests/test_opcoes_curadoria.py -v
bash scripts/executar.sh --testes
```

## Limitações conhecidas

- Este módulo não é chamado por nenhuma rota HTTP ainda — a varredura
  cross-posição (30-02), a rota de narração com gate de cota (30-03) e o
  bloco de UI (30-04) são planos separados que consomem esta base.
- `narrativa_system`/`narrativa_user` ainda não foram exercitados contra um
  LLM real (isso pertence ao 30-03, que fará a chamada de fato).

## Self-Check

```
FOUND: server/app/opcoes_curadoria.py
FOUND: server/tests/test_opcoes_curadoria.py
FOUND commit 4ae5864 (candidatos_da_posicao)
FOUND commit 4fe6e59 (rankear + exigir_ranking)
```

## Self-Check: PASSED
