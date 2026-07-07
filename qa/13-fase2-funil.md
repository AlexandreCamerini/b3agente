# QA 13 — FASE 2 (Revisão Total): funil de navegação + Watchlist + Portfólio + Acompanhar

**Data:** 06/07/2026 · **Escopo:** prompt-mestre "Revisão Total BolsIA", Fase 2 (itens 2.1–2.4)

---

## O que mudou

### 2.1 Navegação (funil canônico)
- Nova ordem de abas: **Acompanhar · Radar · Watchlist · Portfólio · Operador IA**.
- Renomes: "Avaliar" → **Watchlist**; "Operar" → **Portfólio**. "Avaliar" deixa de
  ser conceito de aba: a análise N2 abre como detalhe a partir dos cards.
- **Ids internos preservados** (`evolucao/radar/mercado/carteira/agente`) — zero
  mudança de estado, deep-links e `openAvaliar()` continuam funcionando
  (redirecionam para a Watchlist com a análise aberta).
- Aba inicial já era `evolucao` (Acompanhar) — mantida.

### 2.2 Acompanhar (nova home)
- **Resumo do dia** 100% determinístico (decisão: LLM não redige o resumo para
  não gastar cota; `finance.js` segue fonte única): carteira no dia + acumulado
  (`portfolioMetrics`/`dayReturnPct`/`equityCurve`), operações de hoje
  (`history`), e **setups na watchlist** (scan restrito do STU).
- **Destaque de oportunidade**: melhor confluência do scan diário FORA da
  watchlist + leitura N1 automática (1×/sessão; o cache do deep por
  `snapshotId` garante no máx. 1 gasto de cota por ativo/dia — autorizado).
  Botões: "Ver leitura completa" (DeepModal) e "Levar para a watchlist".
- **Estado vazio elegante** para usuário novo (CTA "Começar pelo Radar").
- Disclaimers educacionais em ambos os cards.

### 2.3 Watchlist (ex-Avaliar/Mercado)
- **Ordenação permanente por oportunidade** (confluência do STU; desempate por
  score técnico e alfabético) + **filtro por direção** (chips).
- Card ganha: badge de tier (🟢 Forte ≥75 · 🟡 Moderada ≥50 · ⚪ Neutra · 🔴 Fraca)
  com % de confluência, veredito, melhor setup e badge **"em carteira"**.
- **Histórico por ativo** no formato aprovado: (a) linha-resumo "N ops · ±X% acum."
  no card → expande para (b) sparkline do preço com marcadores ▲compra/▼venda
  + (c) tabela de operações. Fonte única: seção `history` dos stores.
- Compra a partir do card envia **meta de entrada** (setup/veredito/confluência/
  gatilho/invalidação/snapshotId do scan).

### 2.4 Portfólio (ex-Operar/Carteira)
- STOP/ALVO agora mostram **distância %** até o preço atual.
- Bloco de leitura de risco por posição: **dias em operação** (`abertaEm`, com
  fallback pela COMPRA mais antiga do histórico), **R:R atual**, **% do capital**,
  **setup de entrada com status do gatilho** (válido/invalidado vs. `invalidacao`
  por lado) e **alerta de posição sem stop**.
- **Simular venda** abre modal com **venda total ou parcial** (lotes de 100,
  prévia de valor/resultado, confirmação). Parcial preserva o preço médio.

### Stores e backend (interface idêntica nos DOIS stores — invariante)
- `store.py`: `buy(..., meta=)` com `_sanitize_trade_meta` (posição ganha
  `setupEntrada` + `abertaEm`; histórico ganha `setup`/`snapshotId`);
  `sell(..., qty=)` parcial. `main.py`: `/api/buy` aceita `meta`, `/api/sell`
  aceita `qty`. `persistence.js`: espelho exato (serverStore e deviceStore);
  `sanitizeTradeMeta` idêntico. `api.scan(period, tickers)` para scan restrito.
- Compatibilidade: chamadas antigas (`buy(t, qty)` / `sell(t)`) intocadas;
  `agent.py` e ciclo do deviceStore seguem vendendo total.

## Testes novos
- `server/tests/test_fase2_portfolio.py` (7/7): meta sanitizada, venda
  parcial/total/lotes, escopo por usuário, persistência pós-reinício.
- `web/tests/test_fase2_portfolio.mjs` (13/13): mesmos cenários no
  **deviceStore real** (Capacitor simulado via `CapacitorCustomPlatform`,
  localStorage + fetch mockados) — prova a paridade de semântica.
- `web/tests/test_radar.mjs` atualizado para a assinatura `scan(period, tickers)`.

## Validação desta entrega (sandbox)
- `py_compile` ✓ · `node --check` ✓ · parse JSX (babel) ✓ · balance ✓
- Backend: 20/24 mini-runners OK (4 puladas por `httpx` ausente no sandbox —
  passam no pytest completo; nenhuma toca a F2).
- Web: **9/9 suítes OK** (incluindo a nova F2).

---

## ✋ HARD STOP — roteiro no iPhone (antes da Fase 3)

1. **Build**: `bash instalar.sh --iphone` (labels de aba mudaram → rebuild obrigatório).
2. **Navegação**: app abre no **Acompanhar**; ordem das abas =
   Acompanhar · Radar · Watchlist · Portfólio · Operador IA; Perfil no avatar.
3. **Fluxo completo do funil**:
   Radar → escolher um ativo → "Análise completa" (deve cair na **Watchlist**
   com a análise abrindo no card) → **Simular compra** → conferir no
   **Portfólio**: setup de entrada + status do gatilho + dias + R:R + % capital
   + distâncias de stop/alvo → definir stop/alvo → **Simular venda parcial**
   (metade) → conferir preço médio intacto e histórico → **venda total** →
   resultado aparece no **Acompanhar** (resumo do dia) e no histórico do ativo
   na Watchlist (linha "N ops · ±X%", sparkline com ▲/▼ e tabela).
4. **Watchlist**: ordenação por confluência (melhor primeiro), chips de filtro,
   badge "em carteira" enquanto houver posição.
5. **Acompanhar**: card DESTAQUE carrega (gauge → ticker fora da watchlist);
   "Levar para a watchlist" funciona; disclaimers visíveis.
6. **Regressões**: Operador IA, Opções (via Watchlist), Perfil, stop/alvo por IA
   (N3) e histórico de análises seguem funcionando.
7. **Persistência**: fechar e reabrir o app — posições/histórico/meta intactos;
   no servidor, `test_kpi`/`test_persistence`/`test_fase2_portfolio` verdes.
