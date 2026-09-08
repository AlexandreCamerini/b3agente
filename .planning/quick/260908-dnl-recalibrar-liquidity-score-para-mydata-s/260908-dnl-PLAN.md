---
quick_id: 260908-dnl
description: recalibrar liquidity_score para mydata sem open interest
date: 2026-09-08
status: executing
depende_de: 260908-bzf (a medição que motivou)
---

# Quick 260908-dnl — recalibrar `liquidity_score` para uma fonte sem open interest

## Contexto

`260908-bzf` mediu em produção que o gate de liquidez ficou impossível de
cruzar com `B3_OPTIONS_PROVIDER=mydata`: o `oi_score` (até 40 pontos) some
porque o COTAHIST não publica open interest, e sobra um teto de 35 contra um
corte de 40. Os 60 contratos de PETR4 empatam em 35,0. O Alex escolheu, entre
quatro opções, **recalibrar o score** (opção 1).

## O que os dados reais mandaram (20 cadeias do catálogo, produção, 2026-09-08)

- Volume é quase o único sinal: livro com dois lados existe em ~15% dos
  contratos (0/28 no BPAC11, 1/69 no PRIO3). Só PETR4 (28/60) e VALE3 (31/67)
  têm cobertura decente.
- Volume vem em lotes: 592/592 valores são múltiplos de 100, mínimo 100.
  `volume=100` = negociou uma vez.
- Escala real: mediana de 400 (RADL3) a 28.800 (VALE3); máximos até 1,8 mi.
  A curva original saturava em 1.000 porque esperava que o OI discriminasse.

## A primeira candidata foi descartada (registro deliberado)

Curva de volume até 75 + penalidade de livro desconhecido reduzida para 10.
Resultado nas 20 cadeias: **pass-through** — 15/15, 66/66, 69/69; um contrato
com volume 100 e livro vazio passava a 51,1, e um com spread MEDIDO de 147%
reprovava a 39,6. Ter dado piorava a nota. Falhou o critério fixado antes de
olhar os dados ("volume 500 com um lado zerado reprova").

## Decisão: variante conservadora (penalidade de livro INALTERADA)

```
atividade = max(curva(volume), curva(open_interest))
curva(x)  = clamp((log10(x + 1) − 1) × 20, 0, 75)
score     = clamp(atividade + 25 − spread_penalty, 0, 100)
```

`spread_penalty` fica **byte-idêntica** à de produção: 0/8/18/30 quando
medido, 25 quando desconhecido. A ÚNICA mudança conceitual: a atividade pode
ser carregada por volume sozinho, e o open interest — quando a fonte o
publica — substitui o volume em vez de somar a ele (mantém o caminho Yahoo de
rollback sem inflar nada no mydata).

Piso sem livro: **1.000 unidades (10 lotes)** — exatamente onde a curva
original de volume saturava. Número derivado, não tunado.

Verificado contra as 20 cadeias reais: PETR4 50/60, VALE3 58/67, BPAC11
(zero livro) 23/28, RADL3 (fino) 3/10. Continua sendo gate.

## Tasks

1. **`server/app/options_quant.py`** — `liquidity_score`: a fórmula acima, com
   docstring que registra o porquê e o piso. Assinatura inalterada (6 call
   sites).

2. **Guardiões que travavam o valor antigo** (atualizar COM nota datada, nunca
   apagar):
   - `server/tests/test_options_provider_mydata.py:423-435` — literal `52.0`
     → `71.0`; docstring reescrita (a atual documenta o teto antigo de 60).
   - `server/tests/test_opcoes_collar.py:373-375` — put `volume=100` reprova
     agora e o motor nem a seleciona; fixture vira call 10.000 / put 2.000
     (preserva o propósito: put < call, ambas líquidas).

3. **Guardião novo** `server/tests/test_liquidity_score_mydata.py` — os
   critérios sintéticos fixados ANTES de olhar os dados, mais linhas reais
   congeladas da cadeia de produção (PETRI478W2 88.100 sem livro passa;
   ABEVU147W2 100 reprova; PETRU441W2 300 com spread 66% reprova), a
   fronteira explícita (1.000 passa, 900 reprova), OI substitui volume,
   monotonicidade.

4. **Commit separado — mock fiel ao mydata**
   `server/app/options_provider_mock.py`: `MOCK_OPEN_INTEREST = None`,
   `MOCK_VOLUME = 5000`. O mock tinha OI=2000, que salvava o volume 500 —
   a MESMA cegueira do ADR-020 (staging passava por um campo que o mydata
   nunca tem). Sem asserção literal sobre 500/2000 em teste algum (grep).

5. Docs: seção "Recalibração aplicada" em
   `docs/MEDICAO-gate-liquidez-mydata-2026-09-08.md`; linha no adendo do
   ADR-020; blocker do STATE.md atualizado (estava "adiada").

## Validação

- `bash scripts/executar.sh --testes` (as duas suítes).
- Sem mudança de front → `vite build` não se aplica.
- Prova contra dado real: o guardião novo carrega linhas congeladas de
  produção; a análise completa das 20 cadeias fica em scratchpad (não
  versionada — 576 KB de JSON de mercado não é fixture).

## Fora de escopo

O corte (40) e `LIQUIDEZ_MINIMA` não mudam. `educational_score` consome o
score e herda a escala nova sem edição. Buscar open interest na B3 (opção 3)
continua pendência do MyData.
