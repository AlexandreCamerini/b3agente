---
phase: 51-seu-dia-na-bolsa
plan: 04
subsystem: server/conceitos + scripts
tags: [conceitos, calibracao, dia-na-bolsa, raridade]
requires: ["51-01"]
provides: ["CONCEITOS['amplitude']", "CONCEITOS['extremo-52-semanas']", "scripts/dia_na_bolsa_calibrar.py"]
affects: ["51-05", "51-11"]
key-files:
  created:
    - server/tests/test_dia_na_bolsa_conceitos.py
    - scripts/dia_na_bolsa_calibrar.py
  modified:
    - server/app/conceitos.py
requirements: [ENG-05, ENG-04]
metrics:
  completed: 2026-11-18
  tasks: 2
  tests: 8
---

# Fase 51 Plano 04: Conceitos novos e calibração de frequência Summary

Conceitos `amplitude` e `extremo-52-semanas` nos dois modos (o que é, o que acontece, o que NÃO acontece), e script que mede a frequência de cada regra de raridade em 252 pregões, sem tocar nos limiares travados.

## Commits
- `263f90b2` feat(51-04): conceitos amplitude e extremo-52-semanas (+ guardião de 8 testes)
- `bd0cff95` feat(51-04): script de calibração de frequência

## Decisões
- Formatador novo `_fracao_pct` (fração 0..1 -> "91%"); o `_pct` existente trata o número como percentual já multiplicado e daria "1%". Fora de 0..1 não formata (o parágrafo ancorado some, nunca vira número sem sentido). `preco` reusa `_num`; `n` reusa `_volume_milhar`.
- Gap e volatilidade não ganharam conceito: o card abre `estr-gap`, `ind-volatilidade-historica` e `ind-atr` da KB (existência travada em teste).
- Sem entrada em SETORES (o card abre o conceito direto por `abrirVerbete`).
- Script: núcleo `medir(ibov, universo, dias)` puro e injetável; fontes L2 local (`candle_cache.peek`) ou Yahoo com `--rede`; nunca o provedor pago (grep de aceite = 0). Janela: >= 252 pregões anteriores + o dia avaliado; ativo com menos de 253 barras sai da medição e é listado.

## Calibração

calibração pendente: rodar fora do sandbox com
`server/.venv/bin/python scripts/dia_na_bolsa_calibrar.py --rede`

- L2 local (`server/data/b3_agente.db`): `candle_cache` só tem a linha de teste `ZZZZ9@1d`; IBOV e ativos vazios.
- `--rede`: falha no sandbox com `PermissionError [Errno 1]` (certifi/.pem bloqueado), não é bug.
- Nenhuma constante foi alterada: `IBOV_PERCENTIL = 0.95`, `ATR_MULT_ATIVO = 2.0`, `AMPLITUDE_MIN`, `AMPLITUDE_MIN_ATIVOS`, `GAP_MIN_ATR` intactas. Nenhum número real foi inventado. O smoke com dados SINTÉTICOS (aleatório gaussiano) só validou o funcionamento do script e não é calibração.
- Para o checkpoint 51-11: levar a saída do comando acima e a tabela por regra (disparos 12m, média/semana, união de mercado, união pessoal).

## Achados para o Alex (não corrigidos pelo executor)
1. **Amplitude nunca dispara com o catálogo atual.** `server/app/catalog.py` tem 20 ativos e `AMPLITUDE_MIN_ATIVOS = 30` (51-01). Para a regra funcionar, é preciso ampliar o universo (ex.: lista de líquidos além do catálogo, via `--tickers` na calibração) ou baixar `AMPLITUDE_MIN_ATIVOS`. O script emite AVISO quando o universo é menor que o mínimo. Relevante para 51-05 (o job precisa de universo com >= 30 ativos com 253 barras).
2. p95 isolado do IBOV dá cerca de 5% dos pregões (~1 por mês). O alvo de ~1 por semana só é atingível pela UNIÃO das regras de mercado (ibov_raro, amplitude, extremos de 52 semanas do IBOV). Se a união medida ficar abaixo disso, é decisão do Alex.
3. O cache L2 guarda no máximo 600 candles diários (~2,4 anos); medir 252 dias exige >= 505 barras. Com `--rede` e range 2y (~500 barras) os primeiros dias ficam sem 252 anteriores e a medição cobre algo menos que 252 dias (o script reporta "Dias avaliados" real).

## Deviations from Plan
Nenhuma mudança de escopo. `server/app/dia_na_bolsa_regras.py` não foi modificado (frontmatter lista como possível, mas sem dado real não há ajuste). TDD do Task 1: testes e implementação no mesmo commit.

## Verificação
- `pytest -q tests/test_dia_na_bolsa_conceitos.py tests/test_conceitos.py tests/test_setores.py` -> 44 passed.
- `tests/test_dia_na_bolsa_regras.py` -> 21 passed.
- Greps: `"amplitude": {` = 1; `"extremo-52-semanas": {` = 1; vocabulário proibido 0 -> 0; brapi no script = 0; constantes travadas = 1 cada; `--help` sai 0.
- Não rodados (fora do escopo): suíte canônica, `vite build` (sem `web/src`).

## Known Stubs
Nenhum.

## Threat Flags
Nenhum. T-51-10 mitigado (script sem provedor pago).

## Self-Check: PASSED
- Arquivos existem; commits 263f90b2 e bd0cff95 presentes; STATE.md e ROADMAP.md intocados.
