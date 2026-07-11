# qa/35 — FASE 10: P1 snapshotId + P2 eficiência analítica + P3 spike de fundamentos

> Build: **F9-20260710-3**. Decisões do Alex nesta rodada (AskUserQuestion):
> **P2 MVP = camadas (a) expectância + (c) calibração de confiança** — (d) e
> (b)/(e) ficaram fora. P3 é spike + proposta + mock com **gate**: nada
> integrado antes do OK.

## P1 — snapshotId fora das telas de consumo (bug de produto)

O hash do STU era renderizado cru em 5 superfícies: destaque da home
(`#hex`), chip da análise N2 ("· snapshot #hex"), popup de stop/alvo
("Análise baseada no snapshot #hex"), cards de posição (setupEntrada
"· #hex") e card do Radar ("N candles no período · snapshot #hex").

- **Removido de todas.** No stop/alvo, a linha virou "Análise baseada nos
  dados de {data}" — a DATA é o que serve ao usuário; o hash não.
- **Rastreabilidade preservada**: payloads/estado intactos
  (`snapshotId: a.snapshotId`/`r.snapshotId` seguem fluindo); nova seção
  **"SNAPSHOTS DAS ANÁLISES"** em Perfil → Logs & debug lista uma linha
  `ticker · tipo · snapshot #hex · data` por análise recente (fonte:
  `ctx.analysis` + `ctx.stopAlvo`, até 20 linhas).
- Guardião: `web/tests/test_snapshotid_debug_only.mjs` — varre o App.jsx
  por padrões de render do hash e falha se aparecer FORA do corpo de
  `LogsDebugScreen` (aponta a linha do vazamento).

## P2 — eficiência da IA analítica (camadas a + c)

Tudo calculado em **Python** (`analysis_outcomes.py`); a LLM não calcula
nada. Regra de amostra: `MIN_N = 10` — célula com n menor mostra
**"n insuficiente"**, nunca porcentagem enganosa.

**Backend:**
- `normalizar_confianca()` — escala única da confiança declarada: N1 usa
  `confianca` (baixa|moderada), N2 usa `conviccao` (Muito Alto→alta,
  Alto→alta, Médio→moderada, Baixo→baixa). `registrar()` ganhou o campo
  `confianca` e os 2 call sites (`main.py` N1/N2) passam o valor declarado.
- `compute_stats()` estendido: `expectancia` (R médio por análise),
  `profitFactor` (Σ R⁺ / |Σ R⁻|; sem perdas → `"inf"`, serializável),
  `expectanciaInsuficiente` (n < 10), `minN`, `porConfianca` e `porDecisao`
  (células via `_celula`, cada uma com a régua do n mínimo).
- `to_csv()` + endpoint `GET /api/analysis-outcomes/export.csv`
  (PlainTextResponse; célula vazia = sem dado, nunca inferência).

**Cliente:** `api.analysisOutcomesCsv()` (texto puro, fora do parse JSON) +
paridade nos 2 stores (`persistence.js`). Painel "Eficiência da IA" ganhou
os cards **EXPECTÂNCIA** (expectância/análise + profit factor, com aviso de
n insuficiente), **CALIBRAÇÃO DA CONFIANÇA** (acerto real × confiança
declarada + recorte POR DECISÃO) e botão **Exportar CSV** (share sheet do
iOS com fallback de clipboard).

Guardiões: +8 casos em `server/tests/test_analysis_outcomes.py` (21 no
total: normalização, registro com confiança, expectância, n insuficiente,
profit factor infinito, calibração, bucket "—", CSV com escape) e +4 blocos
em `web/tests/test_analysis_outcomes_ui.mjs` (8 no total).

**Nota de leitura:** as análises registradas ANTES desta rodada não têm
`confianca` — caem no bucket "sem declaração" da calibração. A estatística
de calibração começa a valer ~10 pregões depois deste deploy.

## P3 — spike de fundamentos (GATE — nada integrado)

**Módulo:** `server/app/fundamentals.py` — brapi.dev (httpx, mesma pilha do
yahoo.py), cache SQLite no kv global (dado público), **TTL 7 dias**
(1 fetch/ticker/semana), `parse_brapi()` e `score_fundamento()` puros.
Fonte fora do ar → devolve cache velho; ticker sem cache → `None` (sem
dado, nunca inferência).

**Prova ao vivo (10/07/2026, 4 tickers irrestritos, sem token):**

| Ticker | Score | P/L | ROE | DY | Margem | Dívida/EBITDA |
|---|---|---|---|---|---|---|
| PETR4 | **A** | 4,8 | 24,3% | 6% | 21,7% | 2,93 |
| VALE3 | **C** | 20,4 | 7,2% | 7% | 6,4% | 3,79 |
| ITUB4 | **A** | 11,2 | 22,4% | 8% | 12,1% | sem dado (banco) |
| MGLU3 | **C** | 30,4 | 1,2% | 2% | 0,4% | 3,37 |

Cache validado: 2ª chamada não vai à rede (fetch injetado que explode se
chamado — não explodiu).

**Achados da pesquisa (relatório completo do agente, resumo):**
- **A pegadinha central:** o free da brapi entrega os módulos completos
  (`financialData`/`defaultKeyStatistics`/dividendos) **SÓ nos 4 tickers de
  teste**. Com token free (15k req/mês), o resto do universo recebe só
  quote + P/L + LPA. O plano Startup pago (R$ 99,99/mês) **também não**
  inclui esses módulos — só o Pro (R$ 116,66/mês).
- **"bolsai" existe e é melhor que o esperado:** usebolsai.com — free
  **200 req/dia**, `GET /fundamentals/{ticker}` com pl/pvp/ev_ebitda/roe/
  roa/roic/net_margin/net_debt_ebitda/cagr_5y **já calculados**, ~350
  ações. O refresh semanal do universo (~100 tickers) cabe em 1 dia de
  cota. Lacuna: dividendos/DY é recurso PRO (R$ 49/mês).
- **Recomendação da pesquisa (a decidir no gate): INVERTER os papéis —
  bolsai free como fonte primária do universo; brapi como complemento**
  (4 tickers completos + proventos desses 4). Requer criar conta/chave na
  bolsai (ação do Alex).
- **Opções B3:** gratuito = COTAHIST oficial (EOD D-1, calls/puts com
  strike/vencimento, sem IV/gregas; parsers prontos: `b3fileparser` etc.).
  Pagos documentados sem compromisso: **brapi Pro** (chain + gregas + IV,
  R$ 116,66/mês — mesmo fornecedor dos fundamentos), **OpLab PRO**
  (R$ 154–185/mês, mas API "somente uso pessoal e não comercial" — exigiria
  autorização expressa), **B3 UP2DATA** (institucional, sob consulta).
- Capacidade nunca é o gargalo (433 req/mês ≈ 3% do free brapi;
  100 req ≤ 200/dia bolsai) — **profundidade** é.

**Proposta (desenhada no mock `qa/mocks/fundamento-tecnica-v1.html`):**
1. **Chip de score** A/B/C no card (Radar/watchlist) — única mudança no card.
2. **Seção "Fundamento" no N2** — tabela P/L/ROE/DY/margem/dívida/
   crescimento + referência do trimestre; "sem dado" explícito.
3. **Regra objetiva de rebaixamento**: decisão técnica operável + score C ⇒
   confiança declarada desce 1 degrau, com linha explicando. Score B: sem
   efeito. Score A: **não promove** (fundamento só filtra pra baixo — nunca
   é gatilho). Plano técnico (gatilho/stop/alvo/R:R) intocado.
4. Score em 3 pilares (1 ponto cada, pilar sem dado é neutro): valuation
   P/L ∈ (0,20] · rentabilidade ROE ≥ 10% e margem > 0 · solidez
   dívida/EBITDA ≤ 3. A/B/C = ≥2/1/0 pontos.

**Guardião do gate:** `server/tests/test_fundamentals.py` (7 casos, sem
rede — fixture do payload real) inclui `test_spike_nao_esta_integrado`, que
FALHA se scanner/llm/scan_deep/setups importarem `fundamentals` antes do OK.

**Decisões pendentes do gate (F10.2):** (i) aprovar o desenho do mock;
(ii) fonte primária: bolsai free (recomendado — exige conta) × só brapi
(4 tickers) × brapi Pro pago; (iii) opções: fica fora por ora (COTAHIST é
EOD e sem IV) ou entra como fase própria.

## Validação

- Backend: **240 passed** (232 + 8 novos) · Web: **31/33** (2 ambientais do
  worktree: `test_ios_assets`/`test_push_wiring` exigem web/ios). Parse OK.
- **Hard stop pendente no aparelho** (build F9-20260710-3):
  1. Radar/N2/stop-alvo/posições/home SEM hash hexa; Logs & debug COM a
     seção "Snapshots das análises".
  2. Eficiência da IA: cards Expectância e Calibração aparecem (com
     "n insuficiente" enquanto a amostra < 10) + Exportar CSV compartilha.
  3. Regressão rápida da qa/34 (leitura do Radar, card-herói, ⓘ).
