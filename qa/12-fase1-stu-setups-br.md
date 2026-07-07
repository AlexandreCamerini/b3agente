# 12 — FASE 1 (Revisão Total): Snapshot Técnico Único + Setups BR

*Prompt-mestre "Revisão Total BolsIA" · Fase 1 de 5 · data: 2026-07-06*

## Problema (1.1)
N1 (Radar) e N2 (análise completa) divergiam para o mesmo ativo no mesmo dia.
Causa raiz confirmada no código: **três caminhos de insumo independentes** —
o scanner montava (candle_cache → compute → slice → setups), o N2 refazia
fetch + `technical_models.build_context` com outro corte, o N3 montava um
terceiro contexto parcial; o deep (N1-IA) ainda refazia um `build_context`
próprio e cacheava por DIA (congelava leitura da manhã). Além disso, **nenhuma
chamada de LLM enviava `temperature`** — cada provedor usava o default
(~0.7–1.0), somando aleatoriedade à divergência de insumo.

## Solução implementada (1.2) — STU

`server/app/technical_snapshot.py` (novo):
- `build(ticker, raw_candles, period)`: sanitiza → `indicators.compute` →
  recorte da janela do usuário → condições+score (mesma função do scanner) →
  `setups.detect_setups` (clássicos + 7 BR) → `technical_models.build_context`
  → `snapshotId` = sha1(ticker, período, fingerprint da série)[:8];
- cache por `(ticker, período)` validado por **fingerprint do insumo** (mesma
  disciplina do candle_cache: sem mudança na série, nada é recalculado e o id
  não muda);
- **cotação ao vivo fica FORA do snapshot** (determinismo + invariante "motor
  de sinais separado dos preços ao vivo") — N2 anexa `quote` por fora.

Consumidores religados (todos leem o MESMO snapshot):
- **N1** `scanner.scan_one` → `technical_snapshot.build`; item do scan carrega
  `snapshotId`/`snapshotAt`;
- **N1-IA** `/api/scan/deep` → contexto E setups do prompt saem do snapshot;
  cache do deep re-chaveado por `snapshotId` (novo candle ⇒ nova leitura);
- **N2** `/api/technical/analyze/{t}` → contexto = `snap["context"]` (com
  `setupsRadar`: o LLM vê o mesmo veredito/setups do Radar) + `refocus()`
  (helper novo em `technical_models.py`) para o modelo escolhido;
- **N2 legado** `/api/analyze/{t}` → candles/janela do snapshot;
- **N3** `/api/carteira-stopalvo/{t}` → ATR/S&R/bandas/viés/setups do snapshot
  (N3 segue autorizado a divergir em CONCLUSÃO — responde gestão de risco —
  mas nunca em NÚMEROS);
- `/api/technicals/{t}` (gráfico) → payload do snapshot; o cache local de
  10 min foi removido (mascarava snapshot novo; o STU + candle_cache já
  protegem CPU/rede).

LLM (`llm.py`):
- `LLM_TEMPERATURE = 0.2` nos 3 provedores (Anthropic/OpenAI/Google); guarda
  de compatibilidade: modelos OpenAI de raciocínio que rejeitam `temperature`
  disparam UMA repetição sem o parâmetro (BYOK é livre);
- prompts do N1-deep e do N2 declaram o snapshot: *"Snapshot #id (data): todos
  os números vêm DELE — a direção de estudo deve ser coerente com
  `setupsRadar`"*.

UI (`App.jsx`):
- card do Radar: `· snapshot #id` no subtítulo;
- N2: pill "Modelo … · snapshot #id" (persistido no estado/seed da análise);
- N3: "Análise baseada no snapshot #id · data" no popup de stop/alvo.
- Mesmo id nas telas ⇒ mesmos dados, visível para o usuário.

## Setups BR (1.3)

7 famílias novas em `setups.py`, detectores puros com `gatilho`, `invalidacao`,
`alvoSugerido` (R:R 2:1 didático), `referencia` e `backtestavel: true` —
regras exatas e decisões de fidelidade em **`qa/SETUPS.md`**:
9.1/9.2/9.3 (Stormer) · IFR2 (Connors, só comprador, saída na máx. dos 2
anteriores) · PFR (Stormer) · 123 de fundo/topo · Ponto Contínuo (Dunnigan) ·
Inside Bar (com filtro de tendência obrigatório) · 9.4 Larry Williams.
Suporte novo em `indicators.py`: SMA200, EMA72, RSI2 (aditivo).
`MODEL_EXPLANATION` ("COMO O RADAR ANALISA") ganhou as 7 entradas.

## Validação

| Checagem | Resultado |
|---|---|
| `python3 -m py_compile` (todos os módulos tocados) | ok |
| Parse JSX completo do `App.jsx` (babel) + balance check | ok |
| Suítes puras existentes (indicators, setups, scanner, scan_deep, candles, candle_cache, kpi, tickers, technical_models) | **66/66** |
| `tests/test_setups_br.py` (novo) | **17/17** |
| `tests/test_snapshot_consistency.py` (novo — ACEITE F1) | **8/8** |
| Grep de wiring `snapshotId` (server + web) | ok |

Aceite do teste de consistência: N1 e N2 derivados do mesmo STU têm
`snapshotId`, `veredito`, `confluencia`, `melhorSetup` e `score` **idênticos
por construção**; insumo novo gera id novo; períodos diferentes geram ids
diferentes.

Suítes que exigem httpx/fastapi (`test_pipeline_n2_n3`, `test_guardrail_imperativo`,
`test_llm_errors`, `test_persistence` etc.) não rodam no sandbox offline —
**rodar `pytest` completo no seu ambiente** antes do deploy (nenhuma assinatura
usada por elas foi alterada; `build_context` e `parse_carteira` intactos).

## ✋ Hard stop (device) — roteiro

1. Deploy no Railway + rebuild web; abrir o Radar e anotar o `snapshot #id`
   de 5 tickers (ex.: PETR4, VALE3, ITUB4, WEGE3, PRIO3);
2. Para cada um: "Aprofundar com IA" (N1) e "Análise completa" (N2) —
   conferir que o **mesmo #id** aparece e que a direção de estudo do N2 é
   coerente com o veredito do Radar;
3. Num ativo em carteira: stop/alvo (N3) — conferir "baseado no snapshot #id"
   e que ATR/suportes citados batem com a análise;
4. Trocar o período (1M→6M) e confirmar que o id muda (janela nova = snapshot
   novo);
5. No dia seguinte (candle novo), confirmar que o id muda e que o deep refaz
   a leitura (não serve cache de ontem).
