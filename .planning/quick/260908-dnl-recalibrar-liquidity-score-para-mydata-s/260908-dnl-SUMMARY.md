---
quick_id: 260908-dnl
status: complete
date: 2026-09-08
files_modified:
  - server/app/options_quant.py
  - server/app/options_provider_mock.py
  - server/tests/test_liquidity_score_mydata.py (novo)
  - server/tests/test_options_provider_mydata.py
  - server/tests/test_opcoes_collar.py
  - docs/MEDICAO-gate-liquidez-mydata-2026-09-08.md
  - docs/adr/020-centralizacao-de-dados-no-mydata.md
  - .planning/STATE.md
---

# Summary — 260908-dnl

## O que foi entregue

`liquidity_score` recalibrado para uma fonte que não publica open interest.
Dois commits atômicos:

1. `fix(opcoes): recalibra liquidity_score para fonte sem open interest` —
   fórmula + dois guardiões atualizados com nota datada + guardião novo.
2. `chore(mock): cadeia mock espelha o mydata` — `MOCK_OPEN_INTEREST = None`,
   `MOCK_VOLUME = 5000`.

## A fórmula

```
atividade = max(curva(volume), curva(open_interest))
curva(x)  = clamp((log10(x + 1) − 1) × 20, 0, 75)
score     = clamp(atividade + 25 − spread_penalty, 0, 100)
```

Livro (`25 − spread_penalty`) byte-idêntico ao anterior. Corte 40 inalterado.
Piso sem livro: 1.000 unidades — onde a curva original saturava.

## Como se chegou nela (o que vale registrar)

A primeira candidata — curva até 75 **e** penalidade de livro desconhecido
reduzida de 25 para 10 — passava nos critérios olhando só PETR4 e VALE3. Nas
20 cadeias reais do catálogo era um pass-through: 15/15, 66/66, 69/69. Um
contrato com volume 100 e livro vazio passava a 51,1; um com spread **medido**
de 147% reprovava a 39,6. Ter dado piorava a nota.

Foi descartada porque falhou o critério fixado **antes** de olhar os dados
("volume 500 com um lado zerado reprova"). A variante que ficou muda uma coisa
só: a atividade pode ser carregada por volume sozinho. O piso de 1.000 não foi
escolhido — é onde a curva original considerava volume "cheio".

## Prova contra dado real (código real, 20 cadeias de produção de 2026-09-08)

| | antes | depois |
|---|---|---|
| gate aprovado | 2/18 | 18/18 |
| contratos aprovados | 3/592 | 461/592 (78%) |
| contratos reprovados | 589 | 131 |
| PETR4 | 0/60 | 50/60 |
| RADL3 (o mais fino) | 0/10 | 3/10 |

Continua sendo gate: 131 contratos reprovam, volume mínimo aprovado entre
1.000 e 2.000 por ticker.

## Validação

- `bash scripts/executar.sh --testes` — as duas suítes: **2064 passed, 1
  skipped**, exit 0. Eram 2049; os 15 a mais são o guardião novo.
- Sem mudança de front → `vite build` não se aplica.
- Diff restrito a 4 arquivos + 1 teste novo; nada em `web/src`, `main.py`,
  `store.py` ou `web_dist`.

## Guardiões

- `test_options_provider_mydata.py`: literal 52,0 → 71,0, docstring reescrita
  (a antiga documentava o teto de 60 e deixava o resto "para o checkpoint de
  virada", que não aconteceu). Renomeado para refletir o valor novo.
- `test_opcoes_collar.py`: put `volume=100` reprovava e o motor nem a
  selecionava — o teste morreria em `r["proposta"]["liquidez"]` sem testar o
  que se propõe. Fixture vira call 10.000 / put 2.000, preservando o
  propósito (put < call, ambas líquidas).
- `test_liquidity_score_mydata.py` (novo, 15 testes): critérios sintéticos
  fixados antes dos dados, linhas reais congeladas (PETRI478W2 88.100 passa;
  ABEVU147W2 100 reprova; PETRU441W2 300 com spread 66% reprova), fronteira
  explícita (1.000 passa, 900 reprova), OI substitui volume sem somar,
  monotonicidade, "desconhecido" não é pior que "péssimo medido".

## Fora de escopo, deliberadamente

- Corte (40) e `opcoes_motor.LIQUIDEZ_MINIMA` intocados.
- `educational_score` consome o score e herda a escala sem edição.
- Open interest de verdade (opção 3) é ingestão do MyData. A fórmula já o
  consome quando existir.
- A mensagem "nenhuma posição com opção líquida hoje" continua atribuindo ao
  mercado o que é da medição nos casos residuais. Menor agora; não zero.

## Pendência

**Deploy.** Está em `v2/interacao-estrutural`. Em produção as Fases
14/16/17/18/19 seguem dark até a promoção — que é clique manual no painel do
Railway (auto-deploy desligado desde 2026-09-07).
