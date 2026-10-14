# Quick Task 261013-svo: Painel de evolução da carteira (opção C) — Context

**Gathered:** 2026-10-13
**Status:** Ready for planning
**Origem:** design critique de 2026-10-13 (opção C) após A (261013-29f) e B (261013-cqk, publicada em F10-20261013-03). Escopo REDUZIDO pelo Alex depois do inventário de dados (abaixo): nada de curva de patrimônio no Portfólio, nada de snapshot no servidor.

<domain>
## Task Boundary

1. **Painel no topo da aba Posições** (`CarteiraScreen`, `web/src/App.jsx` ~5864): resumo de atenção + "hoje", com link para a evolução do patrimônio no Acompanhar.
2. **Evolução por posição na folha de detalhe**: gráfico do resultado da posição de AÇÕES desde a entrada, reconstruído de forma determinística a partir do histórico de operações + fechamentos diários.

FORA de escopo (decisão do Alex): curva de patrimônio no Portfólio (DEDUP-01 da v1.5 continua valendo — `test_fase21_dedup_consolidacao` intocado); snapshot diário gravado pelo servidor; marcação histórica de opções; sparkline em cada linha da lista.
</domain>

<decisions>
## Implementation Decisions (LOCKED — Alex, 2026-10-13)

### D1. Painel do topo (Resumo + hoje)
- **Resumo de atenção**: contadores derivados SÓ de `prioridadeAtencao` (`web/src/listaPosicoes.js:27`) por posição — ex.: "1 perto do stop · 1 vence em até 5 dias · 2 sem plano". Mostrar só níveis com contagem > 0; nível RISCO (abaixo do stop/acima do alvo/exercício provável/vencida) primeiro. Sem nada em atenção: frase neutra ("Nenhuma posição pede atenção agora") — nunca vazio mudo. Leitura ainda carregando: estado "lendo", não zero.
- Contadores TOCÁVEIS: tocar filtra a lista àquele nível (estado local), com controle claro "Ver todas"; filtro some se o nível zerar. `aria-pressed`, alvos ≥44px. Helper puro novo testado para contar/filtrar (sem aritmética financeira em componente).
- **Hoje**: "Carteira no dia" = os MESMOS números do Acompanhar (`portfolioMetrics` → `m.dayVal`, `dayReturnPct`, finance.js:131-135/239), rotulado explicitamente como "só ações" (opções não têm variação do dia). Maiores variações do dia entre as posições (até 2 altas e 2 baixas, de `quotes[t].change`), ordenação em helper puro. Cada número de mercado com fonte + horário da cotação (`quotes` traz `source`/`at`; princípio 3). **Ajuste 2026-10-13 (orquestrador, após o plan-checker):** o payload de `/api/quotes` não tem horário por cotação (yahoo.py:139; `at` é do lote, main.py:2037). O painel mostra UMA linha "Fonte · cotações de HH:MM" do lote, mesma convenção da Watchlist (App.jsx:4050), sem sugerir horário por ativo. Horário por cotação = follow-up de backend. Texto original acima era redação do orquestrador, não decisão literal do Alex; a troca será informada a ele no fechamento. Sem cotação → "—" e o ativo fica de fora do ranking (princípio 4).
- **Link** "Ver evolução do patrimônio" → aba Acompanhar (rota/ação já existente, ex.: `A.go("evolucao")`), sem renderizar `CapitalCurve` no Portfólio.
- O hero atual (PATRIMÔNIO TOTAL, RESULTADO ABERTO, CAIXA, EM POSIÇÕES; travado por test_fase21) FICA. Planner decide a posição do painel (sugestão: logo abaixo do hero, antes da `LinhaChamadaOpcoes`/lista) e evita repetir número que o hero já mostra.

### D2. Evolução por posição (folha de detalhe)
- Função PURA nova (ex.: `serieResultadoPosicao({ ticker, history, candles, posicao })` em `web/src/finance.js` ou módulo novo) que reconstrói, por pregão desde a 1ª compra da posição aberta atual: qty vigente e PM vigente a partir de `data.history` (compras = média ponderada; venda parcial preserva PM — mesma regra de `store.py:726-729/795`), e resultado = (fechamento do dia − PM vigente) × qty vigente. Datas de operação são "dd/mm/yyyy HH:MM" BRT (store.py:193) — parse explícito testado.
- **Nunca inventar** (princípio 4): se a reconstrução não fecha com a posição atual (qty reconstruída ≠ `p.qty`, ou PM final ≠ `p.avg` além de tolerância de arredondamento de centavos), sem compra no histórico, ou candles insuficientes (< 2 pregões) → NÃO desenha; mostra "Não há dados suficientes para reconstruir a evolução desta posição." (texto por modo). Teste cobre cada caso.
- Gráfico na folha (dentro do card aberto, perto do bloco Evolução da opção A): linha do resultado em R$ por pregão, linha zero, marcas de compra/venda (padrão `OpsSparkline` App ~1195), stop/alvo NÃO viram linhas de resultado (são preço; fora do escopo). Rótulo com fonte e período: "Fechamentos diários · <fonte> · até <data do último candle>" (princípio 3). Reusar componente SVG existente (`Sparkline`/`OpsSparkline`) ou SVG próprio pequeno; NÃO usar `<CapitalCurve`.
- Posição com estrutura de opções: o gráfico mostra só as ações, com nota explícita "Opções não entram nesta curva (sem histórico de prêmio)."
- Candles: carregar SÓ ao abrir a folha, pelo mesmo caminho que o `OpsSparkline`/technicals já usa (sem método novo de store se possível; se precisar, entra nos DOIS stores — paridade). Período o menor que cubra desde a 1ª compra (brapi só até 3mo; acima vai ao Yahoo — ADR-008; não gastar orçamento à toa). Estados: carregando, falha (com "Tentar de novo"), sem dados.
- Cálculo 100% determinístico no front a partir de dados existentes; nenhuma IA perto disso.

### Claude's Discretion
- Nomes de helpers/componentes; layout exato do painel e do gráfico (seguir tokens do card v6 / `T`, sem hex, pesos 400/700, tipografia `TIPO_CARD`, botões ≥44px, `SP[n]`).
- Guardiões: componentes novos entram em `test_ritmo_sp` (lista componentesV6) e respeitam `test_cartao_v6_transversal` (sem aritmética financeira em componente de card; a conta fica no helper puro). Toda asserção alterada ganha substituta com nota `2026-10-13 (quick 261013-svo)`; nada apagado.
- Copy nova nos dois modos (Estudo = professor, Operador = mesa) e paridade `skill_ref.py` ↔ `copy.js` se a copy for do card (`cartaoPosicao`); skill `didatica-boris`.
</decisions>

<specifics>
## Inventário (Explore, 2026-10-13) — pontos-chave
- `equitySnapshots`: série diária só de totais, gravada quando o app abre (App ~10459-10473; store.py:1543 ↔ persistence.js:82/1036) — não usada nesta task.
- Não há série por posição; `positions[]` só estado atual (store.py:733-740). `data.history` com COMPRA/VENDA `{date "dd/mm/yyyy HH:MM", type, t, qty, price, pnl}` (store.py:743/801), opções com `kind:"opcao"` (ignorar), rejeitadas `status:"rejeitada"` (ignorar).
- Candles: `GET /api/history/{ticker}?period=` (main.py:2040) e `/api/technicals`; `candle_provider.get_history` (candle_provider.py:405); cache L1/L2 compartilhado; brapi ranges 1d/5d/1mo/3mo, acima → Yahoo (`_gate`).
- `OpsSparkline` App ~1195 (candles + ▲/▼ por data; regex dd/mm/yyyy), `Sparkline` App ~8095, `PriceChart` (lightweight-charts) App ~1827.
- `portfolioMetrics` finance.js:123 (dayVal só ações; 7 chamadores com 5 args). `quotes[t]` tem `price`, `change`, `previousClose`, `source`; `/api/quotes` devolve `at`.
- Guardião DEDUP: test_fase21_dedup_consolidacao:56-61 (`<CapitalCurve` exatamente 1×, só em EvolucaoScreen, nunca em CarteiraScreen).
- App.jsx ~164k tokens: NUNCA ler inteiro. Sem dependências novas, sem worktree, sem publicar/push. Executor roda guardiões tocados + testes novos + `npx vite build`; suíte canônica e `cap copy ios` com o orquestrador.
</specifics>

<canonical_refs>
- ./CLAUDE.md (princípios 3, 4, 5); .claude/skills/didatica-boris/SKILL.md
- docs/adr/008-fonte-de-cotacoes-selecionavel.md (orçamento brapi/Yahoo)
- .planning/quick/261013-cqk-lista-de-posicoes-com-folha/261013-cqk-SUMMARY.md (lista, folha, listaPosicoes.js)
- .planning/quick/261013-29f-card-de-posicao-enxuto/261013-29f-SUMMARY.md (corpo enxuto)
</canonical_refs>
