# ESPEC-A — Inversão do eixo de seleção do Radar (regime + momentum relativo)

**Escopo:** N1 (Radar / `/api/scan`). Não toca N2/N3, guardrails CVM, contrato da UI.
**Arquivos:** `+ server/app/regime.py` (novo, puro), `~ server/app/scanner.py` (3 hunks), `+ server/tests/test_regime.py`, `+ docs/adr/009-eixo-de-selecao.md`.
**Status:** patch aplicável, testes passando (10/10).

---

## 1. Problema (o que o código faz hoje)

`scanner.run_scan` ordena o universo inteiro por:

```python
results.sort(key=lambda r: (-r["confluencia"], -r["score_tecnico"], r["ticker"]))
```

`confluencia` é, pela definição do próprio `setups.py`, *"aderência do ativo ao padrão em dados PASSADOS, nunca probabilidade de resultado"*. Ou seja, **o eixo primário de ranking mede aderência a um padrão, não vantagem estatística** — a confusão taxa-de-acerto ≠ expectância que o `CLAUDE.md` proíbe.

Agrava:

- O roster que domina esse ranking (`_setups_br`: 9.1/9.2/9.3, IFR2, PFR, 123, ponto contínuo, inside bar, 9.4 LW) é **price action de curto prazo** — a família de evidência acadêmica mais fraca (Lund; Savin-Weller-Zvingelis; Park-Irwin sobre data snooping).
- **Tendência e momentum** (as famílias com melhor evidência OOS reproduzível — Hurst-Ooi-Pedersen; NBER; AQR) só entram como insumo do `score_tecnico`, que é mero **desempate** ("intensidade de atividade técnica, não direção").
- O **momentum implementado é intra-ativo** (RSI/MACD). O momentum com melhor evidência é o **relativo / cross-sectional** (força relativa *entre* ativos) — que **não existe** como eixo.

Resultado: a hierarquia está invertida — a família mais frágil ordena o mercado; as mais defensáveis desempatam.

## 2. Correção

Novo eixo primário: **regime (tendência/lateral) + momentum relativo cross-sectional**. Os setups de price action deixam de ordenar o mercado e viram **gatilho de timing** dentro de um ativo já selecionado pelo regime — só pontuam quando **alinhados** à direção do regime. Reversão à média só conta como gatilho em **regime lateral** (respeitando a evidência condicional).

Ordenação final (`regime.ranquear`):

```
(tier do regime ↓, momentum relativo ↓, gatilho alinhado ↓, confluência ↓, ticker ↑)
                                                              └ agora é só desempate FINAL
```

### Insumos — tudo já existe no Snapshot Técnico Único

| Sinal | Origem no snapshot | Observação |
|---|---|---|
| Direção do regime | `summary.sma200` (fallback `summary.sma50`) vs `close` | filtro de 200 (Hurst) quando a janela ≥200 candles; senão degrada e declara |
| Força do regime | `summary.adx14` | ≥25 forte, <20 fraca/lateral, 20–25 transição→lateral (conservador) |
| Momentum absoluto | `context.historyStats.change63dPct` + `change252dPct` | proxy 3–12m (a literatura usa 12-1) |
| Momentum **relativo** | percentil de `change` **entre** os ativos do universo | só calculável após o `gather` — é onde todos os snapshots coexistem |

Nenhum número novo nasce na LLM: regime e momentum são cálculo determinístico puro. A `confluencia` **continua no payload** — a UI não muda de contrato, só deixa de ser a chave de ordenação.

## 3. Módulo `regime.py` (API)

```python
classificar(snap) -> {
    "regime": "tendencia_alta|tendencia_baixa|lateral|indefinido",
    "direcao": "alta|baixa|None",
    "forca":   "forte|transicao|fraca|None",
    "adx14":   float|None,
    "base":    "sma200|sma50|None",   # em que média o filtro se apoiou
    "confiavel": bool,                # SMA200 disponível E n>=200
}

ranquear(resultados, snaps_por_ticker) -> resultados  # ordena in-place e anexa:
    r["regime"]          # saída de classificar()
    r["momentumRelPct"]  # percentil cross-sectional 0–100
    r["momentumParcial"] # True se faltou 252 (janela curta)
    r["gatilhoAlinhado"] # melhor setup direcional coincide com o regime?
    r["radarScore"]      # chave de ordenação
```

## 4. Patch de `scanner.run_scan` (3 hunks — ver `scanner.run_scan.patch`)

1. `from . import regime`
2. `results, errors, snaps = [], [], {}` + `snaps[symbol] = snap` logo após o build do snapshot.
3. Substitui o `results.sort(...)` por `regime.ranquear(results, snaps)`.

## 5. Degradação (contrato da skill preservado)

- Janela sem 200 candles → `base="sma50"`, `confiavel=False`. A UI/LLM deve dizer "filtro de regime em SMA50 (janela sem 200 candles)".
- Sem `change252` → `momentumParcial=True`, ranqueia por `change63` só. Declarar "momentum de janela curta".
- Regime `indefinido` (sem média nem ADX) → tier 0, vai para o fim. Nunca é promovido para compensar dado ausente.

## 6. Guardrail adicional no prompt (mesma-família não empilha confiança)

Independente do ranking, inserir no system prompt do N2 (`server/app/defaults.py`) e **espelhar byte-a-byte em `web/src/catalog.js`** (invariante de paridade do `CLAUDE.md` — o teste trava se divergir):

> *"Setups da MESMA família (ex.: RSI, estocástico e MACD derivam de preço/tempo) NÃO somam confirmações independentes. Ao ler confluência, conte FAMÍLIAS distintas alinhadas (tendência, momentum, volume, volatilidade, price action), não indicadores. Vários indicadores da mesma família concordando é UM sinal repetido, não vários."*

Isso fecha o risco de "confluência = certeza" que o `CLAUDE.md` já proíbe, mas que o roster atual facilita.

## 7. Critérios de aceite

- `bash scripts/executar.sh --testes` verde (pytest backend + `web/tests/*.mjs`).
- `test_regime.py`: 10/10 (validado aqui).
- Radar não regride contrato: todo resultado mantém `confluencia`, `veredito`, `plano`, `spark`.
- Um ativo em forte tendência de alta com momentum relativo alto e `confluencia` baixa **sobe** acima de um ativo lateral com `confluencia` 90 (era o inverso).
- **Interlock com B:** `r["regime"]["regime"]` é o campo que o B (validação) passa a persistir e segmentar. A ordem A→B é obrigatória por isso.

## 8. Risco residual / dívida assumida

- `change252` exige 252 candles; nas janelas curtas do produto (1M/3M) o momentum é parcial por design — declarado, não mascarado.
- O percentil é **relativo ao universo escaneado**: universo pequeno/enviesado → ranking enviesado. Documentar que o eixo pressupõe universo amplo (IBOV+). É a mesma premissa da força relativa clássica.
- `radarScore` ainda **não** incorpora expectância medida — isso é o B. Até o B fechar, o eixo é evidência estrutural (regime+momentum), não resultado histórico do ativo.
