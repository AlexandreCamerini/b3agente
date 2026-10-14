---
phase: quick-261013-svo
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - web/src/evolucaoPosicao.js
  - web/tests/test_evolucao_posicao_logica.mjs
  - web/src/finance.js
  - web/src/painelPosicoes.js
  - web/tests/test_painel_posicoes_logica.mjs
  - server/app/skill_ref.py
  - web/src/copy.js
  - web/tests/test_cartao_posicao_espelho.mjs
  - web/src/App.jsx
  - web/tests/test_painel_evolucao_ui.mjs
  - web/tests/test_ritmo_sp.mjs
autonomous: true
requirements: [D1, D2]

must_haves:
  truths:
    - "Ordem da aba Posições: título/subtítulo → hero 2x2 (inalterado) → aviso de opções sem marcação (só se houver) → PainelPosicoes → alerta de concentração (só se houver) → LinhaChamadaOpcoes → estado vazio → linha 'Mostrando só' (só com filtro) → chips de ordenação → lista"
    - "O PainelPosicoes traz contadores de atenção (só níveis com contagem > 0, RISCO primeiro), derivados SÓ de prioridadeAtencao das linhas já montadas"
    - "Tocar um contador filtra a lista àquele nível (aria-pressed); 'Ver todas' limpa; se o nível zerar, o filtro some sozinho (filtro vigente é derivado, sem efeito)"
    - "Sem nada em atenção o painel diz 'Nenhuma posição pede atenção agora.' (Estudo); com leitura ainda carregando mostra 'Lendo o plano das posições…', nunca zero"
    - "'Carteira no dia · só ações' mostra os MESMOS números do Resumo do dia do Acompanhar (m.dayVal + dayReturnPct), com UMA linha de fonte e horário do LOTE de cotações ('Fonte: Yahoo · cotações de <quotesAt>' ou 'Fontes: brapi, Yahoo · cotações de <quotesAt>'), nunca horário por ativo; sem nenhuma cotação válida mostra '—' e o texto de sem dado, nunca R$ 0,00"
    - "Maiores altas/baixas do dia (até 2 de cada) vêm de helper puro; ativo sem cotação válida (mesmo predicado de portfolioMetrics) fica fora do ranking e é listado em 'Sem cotação'"
    - "O link 'Ver evolução do patrimônio' leva à aba Acompanhar (A.go(\"evolucao\")); nenhum <CapitalCurve novo"
    - "Na folha de detalhe de uma posição de ações aparece o gráfico 'Resultado em aberto por pregão', reconstruído do histórico + fechamentos diários, com linha zero, marcas ▲ compra / ▼ venda e rótulo 'Fechamentos diários · <fonte> · até <data>'"
    - "Se a reconstrução não fecha com a posição atual, não há compra, ou há menos de 2 pregões fechados, ou o período de candles não pode ser definido, o gráfico NÃO é desenhado e aparece 'Não há dados suficientes para reconstruir a evolução desta posição.' + o motivo explícito (não existe estado 'idle' visível)"
    - "Posição com estrutura de opções: a curva é só das ações, com a nota 'Opções não entram nesta curva (sem histórico de prêmio).'"
    - "Candles só são pedidos ao abrir a folha, por store.technicals (mesmo caminho do OpsSparkline/Indicadores), uma vez por abertura; falha mostra 'Tentar de novo'"
  artifacts:
    - path: "web/src/evolucaoPosicao.js"
      provides: "parseDataOperacao, hojeBRT, ymdParaBr, reconstruirPosicao, serieResultadoPosicao, periodoCandles, PERIODOS_CANDLES, geometriaSerie (puros)"
      exports: ["parseDataOperacao", "hojeBRT", "ymdParaBr", "reconstruirPosicao", "serieResultadoPosicao", "periodoCandles", "PERIODOS_CANDLES", "geometriaSerie"]
    - path: "web/src/finance.js"
      provides: "cotacaoDoDiaValida exportada e usada pelo próprio portfolioMetrics (predicado único do dia)"
      exports: ["cotacaoDoDiaValida"]
    - path: "web/src/painelPosicoes.js"
      provides: "CHAVE_NIVEL, NIVEIS_PAINEL, resumoAtencao, filtroVigente, filtrarPorNivel, painelHoje (puros)"
      exports: ["CHAVE_NIVEL", "NIVEIS_PAINEL", "resumoAtencao", "filtroVigente", "filtrarPorNivel", "painelHoje"]
    - path: "web/src/App.jsx"
      provides: "PainelPosicoes, ContadoresAtencao, BlocoHoje, EvolucaoResultadoPosicao, GraficoResultadoPosicao; filtro em CarteiraScreen; gráfico em CartaoPosicao (só naFolha)"
    - path: "web/tests/test_evolucao_posicao_logica.mjs"
      provides: "tabela de casos da reconstrução, parse de data, período e geometria"
    - path: "web/tests/test_painel_posicoes_logica.mjs"
      provides: "tabela de contagem/filtro/ranking do dia"
    - path: "web/tests/test_painel_evolucao_ui.mjs"
      provides: "guardião estático do painel, do filtro e do gráfico da folha"
  key_links:
    - from: "web/src/App.jsx:CarteiraScreen"
      to: "web/src/painelPosicoes.js"
      via: "resumoAtencao(linhas...) + filtroVigente + filtrarPorNivel + painelHoje(m.dayVal)"
      pattern: "filtrarPorNivel\\("
    - from: "web/src/painelPosicoes.js:painelHoje"
      to: "web/src/finance.js:cotacaoDoDiaValida"
      via: "mesmo predicado de portfolioMetrics para dia e ranking"
      pattern: "cotacaoDoDiaValida\\("
    - from: "web/src/App.jsx:EvolucaoResultadoPosicao"
      to: "store.technicals"
      via: "useEffect com deps [p.t, periodo, tentativa] — carrega só quando a folha monta"
      pattern: "store\\.technicals\\(p\\.t, periodo\\)"
    - from: "web/src/App.jsx:EvolucaoResultadoPosicao"
      to: "web/src/evolucaoPosicao.js"
      via: "reconstruirPosicao → periodoCandles → serieResultadoPosicao → geometriaSerie"
      pattern: "serieResultadoPosicao\\("
    - from: "web/src/App.jsx:CartaoPosicao"
      to: "EvolucaoResultadoPosicao"
      via: "{naFolha && <EvolucaoResultadoPosicao ...>} no corpo aberto, depois da face"
      pattern: "naFolha && <EvolucaoResultadoPosicao"
    - from: "server/app/skill_ref.py:CARTAO_POSICAO"
      to: "web/src/copy.js:cartaoPosicao"
      via: "chaves atn_*/hoje_*/evo_* byte a byte (test_cartao_posicao_espelho)"
      pattern: "evo_sem_dados"
---

<objective>
Opção C reduzida (CONTEXT LOCKED, Alex 2026-10-13): (D1) painel no topo da aba Posições com contadores de atenção tocáveis que filtram a lista + bloco "Hoje" (carteira no dia só ações, maiores variações com fonte/horário, link para o Acompanhar); (D2) gráfico do resultado em aberto da posição de ações na folha de detalhe, reconstruído de forma determinística a partir de `data.history` + fechamentos diários, sem desenhar quando não fecha.

Purpose: dar o "como estou hoje / o que pede atenção" sem repetir o hero e sem curva de patrimônio no Portfólio (DEDUP-01 intocado), e mostrar a trajetória da posição com números que o motor consegue provar.
Output: 2 módulos puros novos com testes de tabela, predicado de cotação do dia exportado de finance.js, copy nos dois modos com paridade, componentes em App.jsx e guardião estático novo.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/quick/261013-svo-painel-de-evolucao-da-carteira/261013-svo-CONTEXT.md
@./CLAUDE.md
@.claude/skills/didatica-boris/SKILL.md
@.planning/quick/261013-cqk-lista-de-posicoes-com-folha/261013-cqk-SUMMARY.md

App.jsx (~164k tokens) NUNCA é lido inteiro: Grep + Read com offset/limit nas âncoras abaixo (linhas de 2026-10-13, conferir por grep antes de editar).

<interfaces>
Regra de PM/qty (fonte: server/app/store.py, espelho em web/src/persistence.js deviceStore):
- buy (store.py:719-729): qty normalizada a lotes de 100 ANTES de gravar; se existe posição, `avg = round((avg*qty + price*q)/(qty+q), 2)`, `qty += q`; senão `avg = round(price, 2)`. Histórico grava `price: round(price, 2)` (o avg usa o price NÃO arredondado → divergência de até ~1 centavo por compra, daí a tolerância).
- sell (store.py:790-801): `sold` já normalizado e limitado a qty livre; se `sold >= pos.qty` a posição some; senão `qty -= sold` e avg PRESERVADO. Histórico grava `qty: sold`.
- Formato de data do histórico: `now_str()` = `"%d/%m/%Y %H:%M"` em BRT (store.py:193). Histórico é newest-first (`history.insert(0, ...)` / `doc.history.unshift(...)`): ordem cronológica = array invertido (não ordenar por data — operações no mesmo minuto mantêm a ordem de gravação).
- Entradas a IGNORAR: `status === "rejeitada"` (registrar_rejeicao, store.py:825), qualquer `status` presente e diferente de "executada"; `kind === "opcao"`; entradas com `underlying` (compra/venda de contrato de opção, store.py:903/958); `t !== ticker`; `type` fora de COMPRA/VENDA. Entrada legada SEM `status` conta como executada.
- Exercício/atribuição de opção NUNCA mexe na posição de ações (store.py:1372).

Caminho de candles (conferido 2026-10-13):
- Front: `store.technicals(t, period)` — serverStore `technicals: (t, period) => api.technicals(t, period)` (persistence.js:200); deviceStore `async technicals(t, period)` → `api.technicals` + `cacheTech(t, r, period)` (persistence.js:1139-1143). Já existe nos DOIS stores → NENHUM método novo. `api.history` não existe no front; NÃO criar.
- É o mesmo caminho do OpsSparkline da Watchlist (`toggleOps`, App.jsx:4028: `store.technicals(t, candlePeriod)` → `r.candles`) e do painel de Indicadores (App.jsx:2002).
- Rota: `GET /api/technicals/{ticker}?period=` (main.py:2113) → `technical_snapshot.get` → `candle_cache.load` (rede: FULL_RANGE "2y" no cache miss, delta RECENT_RANGE depois; fresh < 45 s; cache L2 compartilhado com Radar/Watchlist/Indicadores; brapi master, Yahoo backup/>3mo por ADR-008). O `period` SÓ recorta a cauda (`resolve_keep` = PERIOD_BARS: 1mo 22, 3mo 66, 6mo 126, 1y 252, 2y 504 — candles.py:14); a busca de rede é a do candle_cache (2y no miss, delta depois), independente do período. Escolher o período NÃO economiza brapi — e nenhum comentário/copy/SUMMARY deve afirmar economia de orçamento (W5, revisão 2026-10-13).
- Payload usado: `r.candles` = `[{ date: "AAAA-MM-DD", open, high, low, close, ... }]` (diário, yahoo.py:_candle_key) e `r.source` (proveniência real, pode ser null). Rótulo da fonte via `FONTE_LABEL(source)` (App.jsx:1416).
- Período escolhido (só para o recorte cobrir a 1ª compra com payload menor): `periodoCandles(inicioYmd, hojeYmd)` = o MENOR de 1mo/3mo/6mo/1y/2y cujo PERIOD_BARS cobre os pregões estimados desde a 1ª compra do episódio atual (+5 de folga); acima disso "2y" e a série começa no 1º candle disponível (marcada `parcial`).

Existentes que o executor usa (não recriar):
- `web/src/listaPosicoes.js`: `NIVEIS_ATENCAO = { RISCO:0, PERTO_STOP:1, VENCE_5_DIAS:2, SEM_PLANO:3, PERTO_ALVO:4, LEITURA_INDISPONIVEL:5, DEMAIS:6 }`, `prioridadeAtencao`, `ordenarLinhas(linhas, criterio)`.
- `web/src/finance.js`: `portfolioMetrics(...)` → `{ posVal, patr, dayVal, ... }`; dayVal só ações, predicado em finance.js:135 `typeof quote.price === "number" && quote.price > 0 && typeof quote.change === "number"`; `dayReturnPct(patr, dayVal)` (finance.js:239).
- `web/src/estruturaCard.js`: `rsNbsp(v)`, `rsSinalNbsp(v)` (formatadores do card v6). App.jsx: `pct(n)`, `FONTE_LABEL`, `SP`, `T`, `TIPO_CARD` (App.jsx:4720), `MONO`.
- `web/src/copy.js:2726` `cartaoPosicaoTxt(mode, chave, vals)` (interpola `{k}`); chave existente `tentar_de_novo` (reusar).
- CarteiraScreen (App.jsx:5864): `const m = portfolioMetrics(...)` (5905) já existe — REUSAR `m`, não chamar portfolioMetrics de novo (guardiões test_status_mercado_ui e test_patrimonio_opcao_avulsa travam exatamente 7 chamadas). `linhas` (5916) = `{ p, t, nivel, resultado, dias, modoLeitura, vig, e, res, atencao, ... }`; `modeloAvulsa(t)` (5928) → `{ t, modoLeitura, e, atencao, ... }`; `ordenarLinhas(linhas, ordem).map(...)` (6052); `avulsas.map(...)` (6068). `ctx.quotesAt` (horário do último /api/quotes, um só para o LOTE — App.jsx:9476 `setQuotesAt(r.at)`) está no ctx (App.jsx:10692). O payload de /api/quotes NÃO tem horário por cotação (yahoo.py:139 devolve t/price/change/previousClose/currency; brapi idem + source): o painel segue a convenção da Watchlist (App.jsx:4050, `"cotações " + quotesAt`) e mostra UMA linha de fonte + horário do lote. Horário por cotação exigiria mudança de backend — follow-up, fora desta task. Hero 2x2 (5973-5992) intocado.
- CartaoPosicao (App.jsx:4939): props incluem `naFolha`, `data`, `ctx`; `e` (estrutura) e `modo` locais; corpo aberto (≈5036-5050): `nPernas > 0 ? (<SeletorFace/> <AreaFlip/>) : faceAcao`, depois `{!mostraResumo && explicaBoris}`.
- Âncoras de fatia: transversal = `function ReguaPlano(` (4722) → `function LinhaChamadaOpcoes(` (5797). Os componentes novos entram DENTRO dessa fatia, inseridos IMEDIATAMENTE ANTES de `function SeletorFace(` (App.jsx:5207, logo depois do fim de `LinhaPernaAvulsa`), então obedecem: zero hex, fontWeight só 400/700, fontSize só `TIPO_CARD.*`, todo `<button>` com `minHeight: 44`, zero `disabled=`, nenhuma aritmética `+ - * /` sobre preco|resultado|be|k|stop|alvo|avg|valor (nomes de layout `xDoGrafico`/`yDoGrafico` são liberados, mas aqui a geometria vem pronta do helper).
- Precedente de SVG: `OpsSparkline` (App.jsx:1195; marcas ▲/▼ por data, `preserveAspectRatio="none"`); `PayoffOperador` (App.jsx:5646; cores por `style={{ stroke: T.x }}`, não atributo `stroke=` com var()).
</interfaces>
</context>

## Especificação dos helpers puros

### web/src/evolucaoPosicao.js (novo, puro, sem import de React/App)

- `parseDataOperacao(s)` → `"AAAA-MM-DD"` | `null`. Regex ancorada `^(\d{2})\/(\d{2})\/(\d{4})(?:\s+\d{2}:\d{2})?$`; mês 1-12, dia 1-31; qualquer outra coisa (ISO, número, null) → null.
- `hojeBRT(agora = new Date())` → `"AAAA-MM-DD"` do dia na B3: `new Intl.DateTimeFormat("en-CA", { timeZone: "America/Sao_Paulo", year: "numeric", month: "2-digit", day: "2-digit" }).format(agora)`; `agora` inválido → null. Único lugar do front desta task que lê relógio/fuso (W6).
- `ymdParaBr(ymd)` → `"dd/mm/aaaa"` | `null` (W7: toda manipulação de data fica aqui, nunca no componente).
- `PERIODOS_CANDLES = Object.freeze([["1mo",22],["3mo",66],["6mo",126],["1y",252],["2y",504]])` — espelho de `PERIOD_BARS` (server/app/candles.py:14), travado por teste que lê o .py.
- `periodoCandles(inicioYmd, hojeYmd)` → string | null. dias = diferença em dias corridos via `Date.UTC`; estimado = `Math.ceil(dias * 5 / 7) + 5`; devolve o 1º período com barras ≥ estimado; acima de 504 → "2y"; entrada inválida ou inicio > hoje → null.
- `reconstruirPosicao({ ticker, history, posicao })` → `{ ok: true, inicioYmd, ops: [{ ymd, tipo: "compra"|"venda", qtyDepois, pmDepois }], nCompras }` | `{ ok: false, motivo }`. Motivos: `"sem_posicao"` (posicao nula ou qty ≤ 0), `"sem_compra"` (nenhuma COMPRA válida do ticker), `"nao_fecha"`.
  - Percorre o histórico FILTRADO (regras de ignorar acima) do mais antigo ao mais novo (array invertido). Estado `qty = 0, pm = null`.
  - COMPRA (qty > 0 e price > 0 numéricos, data parseável; senão → `nao_fecha`): se `qty === 0` inicia episódio novo (zera `ops`, `nCompras = 0`, `inicioYmd = ymd`) e `pm = arred2(price)`; senão `pm = arred2((pm*qty + price*q)/(qty+q))`; `qty += q`; `nCompras++`.
  - VENDA: com `qty === 0` → `nao_fecha`; `q >= qty` → `qty = 0, pm = null` (episódio termina; o próximo COMPRA abre outro); senão `qty -= q` (pm preservado).
  - `arred2(x) = Math.round(x * 100) / 100`.
  - Fecha se, ao fim, `qty === posicao.qty` E `Math.abs(pm - posicao.avg) <= 0.01 * nCompras + 1e-9`. Senão `nao_fecha`. Sem nenhum COMPRA válido → `sem_compra`.
- `serieResultadoPosicao({ ticker, history, candles, posicao, hojeYmd })` → `{ ok: true, pontos: [{ data, resultado }], marcas: [{ data, tipo }], inicio, ate, parcial, desde, inicioBr, ateBr, desdeBr, min, max, ultimo }` (`*Br` via `ymdParaBr`, prontos para a copy) | `{ ok: false, motivo }`.
  - Chama `reconstruirPosicao`; propaga falha.
  - Candles válidos: `date` string com `AAAA-MM-DD` nos 10 primeiros chars, `close` número finito > 0, data ≥ `inicioYmd` e data < `hojeYmd` (o candle de HOJE é sempre excluído: não é fechamento enquanto o pregão roda; decisão de discretion registrada). Ordenados por data.
  - Para cada candle: aplica todas as ops do episódio com `ymd <= data` (ponteiro), e se `qty > 0` emite `{ data, resultado: arred2((close - pm) * qty) }`.
  - Marcas: cada op do episódio mapeada para o 1º candle válido com data ≥ op.ymd; só entra se esse candle existir.
  - `parcial = true` só quando o candle MAIS ANTIGO recebido (antes de filtrar por `inicioYmd`) tem data > `inicioYmd` — a janela de candles não alcança a 1ª compra; `desde` = data do 1º ponto. Dia da compra sem candle (lacuna) com candles anteriores presentes NÃO é parcial (caso 12).
  - `< 2` pontos → `{ ok: false, motivo: "candles_insuficientes" }`. `min`/`max`/`ultimo` dos resultados (para eixo e aria).
- `geometriaSerie({ pontos, marcas, largura = 280, altura = 72, margem = 4 })` → `{ d, yZero, marcas: [{ x, y, tipo }], W, H }`. Domínio Y = `[min(min,0), max(max,0)]` (zero sempre visível; se degenerado, ±1). `x(i) = margem + i/(n-1)*(largura-2*margem)`; `y(v) = margem + (yMax - v)/(yMax - yMin)*(altura-2*margem)`; `d = "M x y L x y ..."` com `toFixed(1)`; marca usa o índice do ponto com a mesma data.

Tabela de casos (ticker PETR4, `hojeYmd = "2026-10-13"`, fixtures de histórico SEMPRE newest-first):

| # | Caso | Histórico (cronológico) | posicao | Candles (data:close) | Esperado |
|---|------|-------------------------|---------|----------------------|----------|
| 1 | compra única | COMPRA 100 @30,00 01/10/2026 10:15 | {qty:100, avg:30} | 10-01:31, 10-02:29.5, 10-05:32 | pontos [100, -50, 200]; marcas [compra 10-01]; inicio 10-01; ate 10-05; parcial false; min -50; max 200; ultimo 200 |
| 2 | compras múltiplas | COMPRA 100 @30 01/10; COMPRA 100 @32 05/10 | {200, 31} | 10-01:31, 10-02:29.5, 10-05:32, 10-06:30 | pontos [100, -50, 200, -200]; marcas compra 10-01 e 10-05 |
| 3 | venda parcial | COMPRA 200 @30 01/10; VENDA 100 @33 02/10 | {100, 30} | 10-01:31, 10-02:33, 10-05:32 | pontos [200, 300, 200]; marcas compra 10-01, venda 10-02 (PM preservado) |
| 4 | venda total + recompra | COMPRA 100 @20 01/09; VENDA 100 @22 10/09; COMPRA 100 @30 01/10 | {100, 30} | 09-01:20 … 10-05 (inclui setembro) | igual ao caso 1: só o episódio atual; inicio 10-01; nenhuma marca de setembro |
| 5a | histórico incompleto (qty) | COMPRA 100 @30 01/10 | {200, 30} | caso 1 | `{ ok:false, motivo:"nao_fecha" }` |
| 5b | PM não fecha | COMPRA 100 @30 01/10 | {100, 30.5} | caso 1 | `nao_fecha` |
| 5c | PM dentro da tolerância | COMPRA 100 @30 01/10 | {100, 30.01} | caso 1 | ok (pontos calculados com o PM reconstruído 30) |
| 5d | venda sem compra antes | VENDA 100 @30 01/10 | {100, 30} | caso 1 | `nao_fecha` |
| 6 | sem compra | [] (ou só outro ticker) | {100, 30} | caso 1 | `sem_compra` |
| 7a | candles insuficientes | caso 1 | {100, 30} | só 10-01:31 | `candles_insuficientes` |
| 7b | só o candle de hoje depois da compra | COMPRA 100 @30 12/10/2026 | {100, 30} | 10-12:31, 10-13:32 | `candles_insuficientes` (hoje excluído) |
| 7c | candles vazios/nulos | caso 1 | {100, 30} | [] e null | `candles_insuficientes` |
| 8 | rejeitada ignorada | caso 1 + COMPRA 100 @31 02/10 status:"rejeitada" | {100, 30} | caso 1 | idêntico ao caso 1 |
| 9 | opção ignorada | caso 1 + COMPRA t:"PETRJ300" underlying:"PETR4" kind:"opcao" + VENDA t:"PETR4" kind:"opcao" | {100, 30} | caso 1 | idêntico ao caso 1 |
| 10 | candle de hoje excluído | caso 1 | {100, 30} | caso 1 + 10-13:40 | ate 10-05; sem ponto 10-13 |
| 11 | janela parcial | caso 1 | {100, 30} | 10-02:29.5, 10-05:32 | pontos [-50, 200]; parcial true; desde 10-02; marcas [] |
| 12 | compra em dia sem candle | COMPRA 100 @30 02/10 | {100, 30} | 10-01:31, 10-05:32, 10-06:33 | pontos [200, 300]; marca compra em 10-05; parcial false (há candle anterior à compra) |
| 13 | close inválido | caso 1 | {100, 30} | caso 1 + 10-03 close null + 10-04 close 0 | idêntico ao caso 1 |
| 14 | legado sem status | caso 1 sem a chave status | {100, 30} | caso 1 | idêntico ao caso 1 |
| 15 | mesmo dia compra+venda | COMPRA 200 @30 01/10 10:00; VENDA 100 @31 01/10 11:00 | {100, 30} | caso 1 | 1º ponto = (31-30)×100 = 100 (estado depois das duas) |
| 16 | sem posição | caso 1 | null / {qty:0} | caso 1 | `sem_posicao` |

hojeBRT (W6): `new Date("2026-10-14T01:30:00Z")` → "2026-10-13" (22h30 em BRT, já é dia 14 em UTC); `new Date("2026-10-13T12:00:00Z")` → "2026-10-13"; `new Date("2026-10-14T03:00:00Z")` → "2026-10-14" (meia-noite BRT); `new Date(NaN)` → null.
ymdParaBr: "2026-10-05" → "05/10/2026"; "x"/null → null. Caso 1 da tabela também confere `inicioBr === "01/10/2026"` e `ateBr === "05/10/2026"`.
parseDataOperacao: "01/10/2026 10:15"→"2026-10-01"; "01/10/2026"→"2026-10-01"; "2026-10-01"→null; "32/10/2026 10:00"→null; "01/13/2026 10:00"→null; null/undefined/123→null.
periodoCandles (hoje "2026-10-13"): inicio = hoje → "1mo"; −20 d → "1mo"; −30 d → "3mo"; −80 d → "3mo"; −100 d → "6mo"; −300 d → "1y"; −400 d → "2y"; −1000 d → "2y"; inválido / futuro → null. Mais: `PERIODOS_CANDLES` bate com o dict PERIOD_BARS lido de server/app/candles.py.
geometriaSerie: pontos [0, 100], largura 100, altura 50, margem 0 → `d === "M0.0 50.0 L100.0 0.0"`, `yZero === 50`; todos negativos [-100, -50] → `yZero === 0` (topo); todos zero → sem NaN; marca no índice da data.

### web/src/painelPosicoes.js (novo, puro)

- `NIVEIS_PAINEL = [0,1,2,3,4,5]` (RISCO..LEITURA_INDISPONIVEL; DEMAIS nunca é contado).
- `CHAVE_NIVEL = { 0:"atn_risco", 1:"atn_perto_stop", 2:"atn_vence", 3:"atn_sem_plano", 4:"atn_perto_alvo", 5:"atn_sem_leitura" }`.
- `resumoAtencao(linhas)` — linhas `[{ t, nivel, lendo }]` → `{ estado: "lendo" }` se QUALQUER linha `lendo`; `{ estado: "nenhum" }` se nenhuma linha em NIVEIS_PAINEL; senão `{ estado: "ok", grupos: [{ nivel, n }] }` só n > 0, em ordem crescente de nível (RISCO primeiro). Entrada não-array → `{ estado: "nenhum" }`.
- `filtroVigente(filtro, resumo)` → `filtro` se `resumo.estado === "ok"` e há grupo com esse nível; senão `null` (o filtro some sozinho quando o nível zera ou a leitura volta a carregar — derivado, sem useEffect).
- `filtrarPorNivel(linhas, nivel)` → novo array; `nivel == null` devolve cópia inteira.
- `painelHoje({ positions, quotes, patr, dayVal, rotuloFonte, n = 2 })` → `{ dia: { valor, pct } | null, altas: [{ t, change }], baixas: [...], semCotacao: [t], semCotacaoTxt, fontes: [source], tipoFonte: "uma"|"varias"|"nenhuma", fontesTxt }`. Válida = `cotacaoDoDiaValida(quotes[p.t])`, importada de finance.js (W1: EXATAMENTE o predicado de portfolioMetrics, sem filtros extras, para dia e ranking nunca divergirem). `rotuloFonte` é injetado pelo componente (`FONTE_LABEL`, que vive em App.jsx); `fontesTxt` = rótulos distintos unidos por ", "; `semCotacaoTxt` = tickers unidos por ", " (W7: junção de texto no helper, não no componente). `dia = null` se nenhuma válida; senão `{ valor: dayVal, pct: dayReturnPct(patr, dayVal) }` (importa de finance.js — mesmos números do Acompanhar). Altas: change > 0, desc, empate por ticker, até n; baixas: change < 0, asc, até n; change 0 não entra. `fontes` = sources distintos não-vazios das cotações VÁLIDAS na ordem de aparição; `tipoFonte` = "uma" (1), "varias" (≥2), "nenhuma" (0); `semCotacao` = tickers inválidos na ordem das posições.
- Em finance.js: `export function cotacaoDoDiaValida(quote)` = `!!quote && typeof quote.price === "number" && quote.price > 0 && typeof quote.change === "number"`, e `portfolioMetrics` passa a usá-la no lugar da condição inline (finance.js:135) — refatoração sem mudança de comportamento.

Casos (test_painel_posicoes_logica.mjs): contagem com níveis 0,0,3,6 → grupos [{0,2},{3,1}]; só DEMAIS → "nenhum"; uma linha `lendo` → "lendo"; vazio → "nenhum"; filtroVigente(3, resumo com 3) = 3; filtroVigente(1, resumo sem 1) = null; filtroVigente(0, {estado:"lendo"}) = null; filtrarPorNivel não muta e respeita null; painelHoje com 5 posições (+3,+1,−2,0, sem cotação) → altas [+3,+1], baixas [−2], semCotacao [o sem cotação], dia.pct === dayReturnPct(patr, dayVal); paridade W1: para um conjunto misto (price 0, price ausente, change string, change ok) o conjunto de tickers válidos de painelHoje é exatamente o que contribui para `portfolioMetrics(...).dayVal` (conferido comparando dayVal com e sem cada posição) e `cotacaoDoDiaValida` é a função exportada usada pelos dois; nenhuma cotação → dia null e tipoFonte "nenhuma"; fontes ["yahoo","yahoo"] → "uma"; ["brapi","yahoo"] → "varias" com fontesTxt "brapi, Yahoo" (rotuloFonte de teste); n=1 corta.

## Corte de execução (2 levas, mesmo padrão da 261013-cqk)

PLAN único, executado em DUAS levas de executor, cada uma com o próprio verify:
- **Leva 1 = Tarefas 1 e 2** (helpers puros + testes de tabela; copy nos dois modos + paridade). Fecha com os verifies das Tarefas 1 e 2 verdes, commit por tarefa e SUMMARY parcial (seção "Leva 1") com as assinaturas finais exportadas e a lista de chaves de copy.
- **Leva 2 = Tarefas 3 e 4** (App.jsx: painel, filtro, gráfico na folha; guardiões). SÓ dispara depois que o orquestrador re-rodar os verifies da leva 1. Executor novo lê este PLAN + SUMMARY da leva 1; NÃO relê os testes da leva 1. Fecha com os verifies das Tarefas 3 e 4 e completa o SUMMARY ("Leva 2").
- Falha na leva 1 → leva 2 não dispara.

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: evolucaoPosicao.js — reconstrução determinística da série por posição (D2)</name>
  <files>web/src/evolucaoPosicao.js, web/tests/test_evolucao_posicao_logica.mjs</files>
  <behavior>
    - Os 16 casos da tabela "Tabela de casos" acima, cada um com asserção exata de `ok`/`motivo`, `pontos` (data e resultado), `marcas`, `inicio`, `ate`, `parcial`, `desde`, `min`, `max`, `ultimo` quando aplicável.
    - Casos de `parseDataOperacao`, `periodoCandles` (incluindo paridade de `PERIODOS_CANDLES` com o PERIOD_BARS lido por regex de `server/app/candles.py`) e `geometriaSerie` listados acima.
    - `reconstruirPosicao` e `serieResultadoPosicao` não mutam `history`, `candles` nem `posicao` (deep-equal antes/depois).
  </behavior>
  <action>Per D2: criar o módulo puro `web/src/evolucaoPosicao.js` exatamente com as funções e regras da seção "Especificação dos helpers puros" (regra de PM/qty igual a store.py:726-729/795 com arredondamento a 2 casas a cada compra, venda parcial preserva PM, venda total encerra o episódio e a recompra abre outro; histórico newest-first invertido; filtros de rejeitada/opção/underlying/status; tolerância 0,01 × nº de compras do episódio; candle de hoje excluído; menos de 2 pontos não desenha). Cabeçalho de comentário com a data `2026-10-13 (quick 261013-svo)`, citando princípio 4 (não inventar) e princípio 5 (cálculo determinístico, nunca IA), e que `PERIODOS_CANDLES` espelha candles.py. Sem dependência nova, sem import de App/React. Escrever o teste primeiro (RED: módulo ausente falha), depois a implementação (GREEN). Teste no formato da casa (`ok(nome, cond)` + `process.exit(fails ? 1 : 0)`, ver web/tests/test_lista_posicoes_logica.mjs).</action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2/web && node tests/test_evolucao_posicao_logica.mjs</automated>
  </verify>
  <done>Os 16 casos + parse + período + geometria passam; módulo exporta parseDataOperacao, reconstruirPosicao, serieResultadoPosicao, periodoCandles, PERIODOS_CANDLES, geometriaSerie; zero dependência nova.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: painelPosicoes.js + copy do painel e do gráfico nos dois modos (D1, D2)</name>
  <files>web/src/finance.js, web/src/painelPosicoes.js, web/tests/test_painel_posicoes_logica.mjs, server/app/skill_ref.py, web/src/copy.js, web/tests/test_cartao_posicao_espelho.mjs</files>
  <behavior>
    - Casos de painelPosicoes listados na especificação (contagem, lendo, nenhum, filtroVigente, filtrarPorNivel sem mutação, painelHoje com ranking/semCotacao/fontes/dia null/`dia.pct === dayReturnPct(patr, dayVal)`).
    - Paridade CARTAO_POSICAO ↔ COPY[modo].cartaoPosicao continua byte a byte com as chaves novas; neutras idênticas nos dois modos; específicas diferentes.
  </behavior>
  <action>Per D1 + W1: em web/src/finance.js exportar `cotacaoDoDiaValida(quote)` e trocar a condição inline do loop de `portfolioMetrics` por ela (comentário `2026-10-13 (quick 261013-svo)`: predicado único do dia). Criar `web/src/painelPosicoes.js` puro conforme a especificação (importa só `dayReturnPct` e `cotacaoDoDiaValida` de ./finance.js; comparadores só `<`/`>`; nenhuma outra conta financeira). Teste `web/tests/test_painel_posicoes_logica.mjs` primeiro (RED), depois o módulo.
Copy (per D1/D2 + discretion "copy nos dois modos"): acrescentar em `CARTAO_POSICAO["educacional"]` e `["operador"]` de server/app/skill_ref.py E em `COPY.estudo.cartaoPosicao`/`COPY.operador.cartaoPosicao` de web/src/copy.js, byte a byte, as chaves:
NEUTRAS (mesmo texto nos dois modos): `atn_grupo_aria` "Filtrar posições por atenção"; `atn_risco` "Em risco"; `atn_perto_stop` "Perto do stop"; `atn_vence` "Vence em até 5 dias"; `atn_sem_plano` "Sem plano completo"; `atn_perto_alvo` "Perto do alvo"; `atn_sem_leitura` "Sem leitura do plano"; `atn_contador_aria` "{rotulo}: {n}. Filtrar a lista."; `atn_lendo` "Lendo o plano das posições…"; `atn_ver_todas` "Ver todas"; `atn_mostrando` "Mostrando só: {rotulo} ({n})"; `hoje_titulo` "Hoje"; `hoje_carteira_dia` "Carteira no dia · só ações"; `hoje_altas` "Maiores altas"; `hoje_baixas` "Maiores baixas"; `hoje_item` "{ticker} {pct}"; `hoje_sem_cotacao` "Sem cotação: {tickers}"; `hoje_sem_dado` "Sem variação do dia disponível agora."; `hoje_fonte_uma` "Fonte: {fonte} · {lote}"; `hoje_fontes` "Fontes: {fontes} · {lote}"; `hoje_sem_fonte` "Fonte não informada · {lote}"; `hoje_lote_hora` "cotações de {hora}"; `hoje_sem_hora` "horário das cotações não informado"; `hoje_link_evolucao` "Ver evolução do patrimônio"; `evo_titulo` "Resultado em aberto por pregão"; `evo_fonte` "Fechamentos diários · {fonte} · até {data}"; `evo_fonte_desconhecida` "fonte não informada"; `evo_desde_janela` "Desde {data} (início dos fechamentos disponíveis)"; `evo_opcoes_fora` "Opções não entram nesta curva (sem histórico de prêmio)."; `evo_carregando` "Carregando fechamentos…"; `evo_falha` "Não foi possível carregar os fechamentos."; `evo_motivo_sem_compra` "Nenhuma compra desta posição no histórico."; `evo_motivo_nao_fecha` "O histórico de operações não fecha com a posição atual."; `evo_motivo_candles` "Menos de 2 pregões fechados desde a compra."; `evo_motivo_periodo` "Não foi possível definir o período de fechamentos a partir da data da compra."; `evo_leg_compra` "▲ compra"; `evo_leg_venda` "▼ venda"; `evo_aria` "Resultado em aberto de {ticker} de {inicio} a {fim}: mínimo {min}, máximo {max}, último {ultimo}.".
ESPECÍFICAS (Estudo / Operador; cabeçalhos de comentário e copy não afirmam economia de brapi — W5): `atn_nenhuma` "Nenhuma posição pede atenção agora." / "Nada pede atenção agora."; `evo_sem_dados` "Não há dados suficientes para reconstruir a evolução desta posição." / "Sem dados suficientes para reconstruir a evolução."; `evo_explica` "Cada ponto é o fechamento do dia menos o preço médio da época, vezes a quantidade da época. O lucro de venda parcial já realizado sai da curva." / "(Fechamento − PM vigente) × qtd vigente. Realizado fica fora.".
Nenhum texto pode casar o PROIBIDO do espelho (comprar/vender/garante/certo/sempre). Reusar `tentar_de_novo` (não criar chave de retry). Em test_cartao_posicao_espelho.mjs: acrescentar as neutras ao array `NEUTRAS` e `atn_nenhuma`, `evo_sem_dados`, `evo_explica` ao `ESPECIFICAS`, cada extensão com comentário `// 2026-10-13 (quick 261013-svo): + chaves do painel de atenção/hoje e da evolução por posição.` — nada removido. Rodar test_skill_ref.py (mexeu em skill_ref.py).</action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2/web && f=0; for t in test_painel_posicoes_logica test_cartao_posicao_espelho test_copy_theme test_finance test_status_mercado_ui test_patrimonio_opcao_avulsa; do node tests/$t.mjs >/dev/null || { echo "FALHOU: $t"; f=$((f+1)); }; done; cd ../server && .venv/bin/python -m pytest tests/test_skill_ref.py -q || f=$((f+1)); echo "falhas=$f"; [ $f -eq 0 ]</automated>
  </verify>
  <done>finance.js exporta cotacaoDoDiaValida e portfolioMetrics a usa (test_finance/status_mercado/patrimonio verdes, comportamento igual); painelPosicoes.js exporta CHAVE_NIVEL, NIVEIS_PAINEL, resumoAtencao, filtroVigente, filtrarPorNivel, painelHoje e seu teste passa; as 41 chaves novas (38 neutras + 3 específicas) existem nos dois lados com paridade byte a byte; espelho e test_skill_ref verdes.</done>
</task>

<task type="auto">
  <name>Task 3: App.jsx — painel no topo, filtro da lista e gráfico da evolução na folha (D1, D2)</name>
  <files>web/src/App.jsx</files>
  <action>ANTES de escrever componente (W7): ler `web/tests/test_cartao_v6_transversal.mjs` inteiro (regex de aritmética `FIN`, tipografia, alvos de toque) e o grupo 8 da Tarefa 4. Ler App.jsx só por Grep + Read com offset/limit nas âncoras de `<interfaces>`. Imports: `import { NIVEIS_PAINEL, CHAVE_NIVEL, resumoAtencao, filtroVigente, filtrarPorNivel, painelHoje } from "./painelPosicoes.js";` e `import { hojeBRT, reconstruirPosicao, periodoCandles, serieResultadoPosicao, geometriaSerie } from "./evolucaoPosicao.js";` com comentário `quick 261013-svo (2026-10-13)`.

Componentes novos (function declarations), inseridos IMEDIATAMENTE ANTES de `function SeletorFace(` (W2; fica dentro da fatia do transversal, logo depois de `LinhaPernaAvulsa`), sob um cabeçalho de comentário `quick 261013-svo (2026-10-13)`:
(a) `ContadoresAtencao({ resumo, filtro, onFiltro, modo })` — `role="group"` com `aria-label` = `atn_grupo_aria`; estado "lendo" → texto `atn_lendo` com `role="status"`; "nenhum" → `atn_nenhuma`; "ok" → um `<button type="button">` por grupo (rótulo `cartaoPosicaoTxt(modo, CHAVE_NIVEL[g.nivel])` + contagem em MONO), `aria-pressed={filtro === g.nivel}`, `aria-label` = `atn_contador_aria`, `minHeight: 44`, toque alterna (mesmo nível → `onFiltro(null)`); com filtro ativo, botão `atn_ver_todas` (`minHeight: 44`). Tom por nível via tokens `T.*` (0/1 = T.warn, 2 = T.warn, 3 = T.textSecondary, 4 = T.accent, 5 = T.textMuted) — discretion.
(b) `BlocoHoje({ hoje, quotesAt, modo, onEvolucao })` — título `hoje_titulo`; linha `hoje_carteira_dia` com `rsSinalNbsp(hoje.dia.valor)` + `pct(hoje.dia.pct)` (cor positiva/negativa pelo sinal só por comparação `> 0`/`< 0`, sem conta), ou "—" + `hoje_sem_dado` quando `hoje.dia == null`; UMA linha de fonte e horário do lote (B1): `lote = quotesAt ? cartaoPosicaoTxt(modo, "hoje_lote_hora", { hora: quotesAt }) : cartaoPosicaoTxt(modo, "hoje_sem_hora")`, e a chave conforme `hoje.tipoFonte` ("uma" → `hoje_fonte_uma` com `{ fonte: hoje.fontesTxt, lote }`; "varias" → `hoje_fontes` com `{ fontes: hoje.fontesTxt, lote }`; "nenhuma" → `hoje_sem_fonte` com `{ lote }`); listas `hoje_altas`/`hoje_baixas` com `hoje_item` ({ticker, pct: pct(change)}) SEM fonte nem horário por item (não sugerir horário próprio por ativo); `hoje_sem_cotacao` com `{ tickers: hoje.semCotacaoTxt }` quando `semCotacao.length > 0`; botão `hoje_link_evolucao` → `onEvolucao` (`minHeight: 44`). NÃO mostra patrimônio, resultado aberto, caixa nem em posições (o hero já mostra).
(c) `PainelPosicoes({ resumo, filtro, onFiltro, hoje, quotesAt, modo, onEvolucao })` — card (`T.bgCard`, borda `T.borderSubtle`, padding/gap só `SP[n]`) com ContadoresAtencao em cima e BlocoHoje embaixo.
(d) `GraficoResultadoPosicao({ serie, ticker, modo })` — `const g = geometriaSerie({ pontos: serie.pontos, marcas: serie.marcas })`; `<svg role="img" aria-label={evo_aria com rsSinalNbsp(serie.min/max/ultimo) e serie.inicioBr/ateBr}>` com `viewBox={"0 0 " + g.W + " " + g.H}`, `preserveAspectRatio="none"`, linha zero tracejada (`y1={g.yZero}`, `style={{ stroke: T.borderSubtle }}`), path `d={g.d}` (`style={{ stroke: T.textSecondary }}`, `vectorEffect="non-scaling-stroke"`), marcas ▲ (T.positive) / ▼ (T.negative) nas coordenadas de `g.marcas` (padrão OpsSparkline); rótulos HTML do eixo com `rsSinalNbsp(serie.max)` e `rsSinalNbsp(serie.min)`; legenda `evo_leg_compra`/`evo_leg_venda`. Nenhuma conta: toda coordenada vem de `g`.
(e) `EvolucaoResultadoPosicao({ p, data, modo, comEstrutura })` — hooks no topo: `const [tentativa, setTentativa] = useState(0)`, `const [carga, setCarga] = useState({ status: "carregando", r: null })` (W4: não existe status "idle"; o estado inicial já é carregando e o único caso sem busca é período nulo, tratado abaixo). `const rec = reconstruirPosicao({ ticker: p.t, history: data.history, posicao: p })`; `const hojeYmd = hojeBRT();` (W6: fuso da B3 resolvido no helper; o componente não toca em Date); `const periodo = rec.ok ? periodoCandles(rec.inicioYmd, hojeYmd) : null`. `useEffect(() => { if (!periodo) return; let vivo = true; setCarga({ status: "carregando", r: null }); store.technicals(p.t, periodo).then((r) => { if (vivo) setCarga({ status: "ok", r }); }).catch(() => { if (vivo) setCarga({ status: "falha", r: null }); }); return () => { vivo = false; }; }, [p.t, periodo, tentativa]);` — deps primitivas, sem loop; sem reconstrução que feche ou sem período NÃO busca candles (não há o que desenhar). Render: título `evo_titulo`; `comEstrutura` → nota `evo_opcoes_fora`; `!rec.ok` → `evo_sem_dados` + motivo (`evo_motivo_sem_compra` | `evo_motivo_nao_fecha`; `sem_posicao` usa `evo_motivo_nao_fecha`); `rec.ok && !periodo` → `evo_sem_dados` + `evo_motivo_periodo` (W4; ex.: data da compra depois de hoje no relógio); carregando → `evo_carregando` (`role="status"`); falha → `evo_falha` + botão `tentar_de_novo` (`minHeight: 44`, `onClick={() => setTentativa((n) => n + 1)}`); ok → `const serie = serieResultadoPosicao({ ticker: p.t, history: data.history, candles: carga.r && carga.r.candles, posicao: p, hojeYmd })`; `!serie.ok` → `evo_sem_dados` + `evo_motivo_candles`/`evo_motivo_nao_fecha`; senão `<GraficoResultadoPosicao>` + `evo_fonte` ({ fonte: carga.r.source ? FONTE_LABEL(carga.r.source) : evo_fonte_desconhecida, data: serie.ateBr }) + `evo_desde_janela` ({ data: serie.desdeBr }) se `serie.parcial` + `evo_explica` (rótulo). W7: nenhum componente novo manipula data/texto (sem `new Date`, `Intl.`, `.slice(`, `.split(`, `padStart`, `toFixed(`, `Math.`, `.join(`): datas e junções chegam prontas dos helpers; o componente só chama `cartaoPosicaoTxt`, `rsSinalNbsp`, `pct` e `FONTE_LABEL`.

Fiação:
- CarteiraScreen: novo `const [filtroNivel, setFiltroNivel] = useState(null);` logo depois de `const [abertaT, setAbertaT] = useState(null);` (ANTES de qualquer `return (`, inclusive o da IIFE `folha`). Depois de `linhas`/`modeloAvulsa` (antes do `folha`): `const modelosAvulsas = avulsas.map(modeloAvulsa);` `const resumo = resumoAtencao([...linhas.map((l) => ({ t: l.t, nivel: l.nivel, lendo: l.vig.situacao === "carregando" || l.modoLeitura === "carregando" })), ...modelosAvulsas.map((a) => ({ t: a.t, nivel: a.atencao.nivel, lendo: a.modoLeitura === "carregando" }))]);` `const filtro = filtroVigente(filtroNivel, resumo);` `const hoje = painelHoje({ positions: data.positions, quotes, patr: m.patr, dayVal: m.dayVal, rotuloFonte: FONTE_LABEL });` — REUSA o `m` existente (NÃO chamar portfolioMetrics de novo: contagem travada em 7). Ordem exata do JSX (W3): título/subtítulo → hero 2x2 → aviso `m.opcoesSemMarcacao > 0` (se houver) → PainelPosicoes → bloco de concentração (se houver) → `LinhaChamadaOpcoes` → estado vazio → linha `atn_mostrando` (só com filtro) → `ChipsOrdenacaoPosicoes` → lista → `{folha}`. Inserir, depois do aviso de opções e antes do bloco de concentração: `{data.positions.length + avulsas.length > 0 && <PainelPosicoes resumo={resumo} filtro={filtro} onFiltro={setFiltroNivel} hoje={hoje} quotesAt={ctx.quotesAt} modo={modo} onEvolucao={() => A.go("evolucao")} />}`. A lista passa a `ordenarLinhas(filtrarPorNivel(linhas, filtro), ordem).map(...)` e as avulsas mantêm EXATAMENTE o laço `avulsas.map((t) => {` (test_carteira_perna_avulsa ancora em `app.indexOf("avulsas.map((t) =>")` e exige `<LinhaPernaAvulsa` nos 900 chars seguintes; por isso `modelosAvulsas` usa `avulsas.map(modeloAvulsa)`, nunca `avulsas.map((t) =>`): antes do JSX, `const avulsasVisiveis = new Set(filtrarPorNivel(modelosAvulsas.map((a) => ({ ...a, nivel: a.atencao.nivel })), filtro).map((a) => a.t));` e, na 1ª linha do laço, `if (!avulsasVisiveis.has(t)) return null;`. Com filtro ativo, entre o estado vazio e os chips de ordenação, uma linha `atn_mostrando` (`role="status"`, `{ rotulo, n }` do grupo vigente) — o "Ver todas" já está no painel. Hero, aviso de opções, concentração, `LinhaChamadaOpcoes`, estado vazio, chips de ordenação, `id={"posicao-" + p.t}` e a folha ficam como estão. Nenhum `<CapitalCurve`, nenhum `CONTENT_MAX_WIDTH` novo, nenhum `varsCartaoV6(` em forma nova.
- CartaoPosicao: no corpo aberto, logo DEPOIS do bloco `{nPernas > 0 ? (...) : faceAcao}` e antes de `{!mostraResumo && explicaBoris}`, inserir `{naFolha && <EvolucaoResultadoPosicao p={p} data={data} modo={modo} comEstrutura={!!e} />}` (o card fora da folha não busca nada). Ordem BlocoBorisIA → DetalheCompras → histórico preservada (test_cartao_posicao_enxuto).
- Todos os componentes novos: só tokens `T.*`, `fontSize: TIPO_CARD.*`, `fontWeight` 400/700, margin/padding/gap via `SP[n]` (sem px solto — test_ritmo_sp), todo `<button>` com `minHeight: 44`, nada de `disabled=`, nada de `+ - * /` sobre valores financeiros (contas só nos helpers).</action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2/web && npx vite build >/dev/null 2>&1 || { echo "FALHOU: vite build"; exit 1; }; f=0; for t in test_cartao_v6_transversal test_cartao_v6_fechado test_cartao_v6_aberto test_cartao_posicao_enxuto test_lista_posicoes_ui test_fase21_dedup_consolidacao test_status_mercado_ui test_patrimonio_opcao_avulsa test_carteira_lastro_ui test_estrutura_card_contraste test_fase20_fundacao_visual test_ui_onda_g test_carteira_perna_avulsa test_hero_reconciliado; do node tests/$t.mjs >/dev/null || { echo "FALHOU: $t"; f=$((f+1)); }; done; echo "falhas=$f"; [ $f -eq 0 ]</automated>
  </verify>
  <done>Build ok; os 14 guardiões listados verdes SEM alteração (se algum travar uma mudança intencional, ele é tratado na Tarefa 4 com substituta datada, nunca apagado); `grep -c "<CapitalCurve" src/App.jsx` = 1; `grep -c "portfolioMetrics(" src/App.jsx` = 7.</done>
</task>

<task type="auto">
  <name>Task 4: Guardiões — novo test_painel_evolucao_ui e extensão do test_ritmo_sp</name>
  <files>web/tests/test_painel_evolucao_ui.mjs, web/tests/test_ritmo_sp.mjs</files>
  <action>Criar `web/tests/test_painel_evolucao_ui.mjs` (estático, mesmo estilo de test_lista_posicoes_ui.mjs: `functionBody(nome)` + `semComentarios`), cabeçalho com nota `2026-10-13 (quick 261013-svo)`, travando (grupos 1-8):
1. CarteiraScreen contém `<PainelPosicoes`, `resumoAtencao(`, `filtroVigente(`, `filtrarPorNivel(`, `painelHoje(`, `A.go("evolucao")`, `m.dayVal`; `useState(null)` do `filtroNivel` antes do primeiro `"  return (\n"`; ordem W3 por índice: `PATRIMÔNIO TOTAL` < `m.opcoesSemMarcacao > 0` < `<PainelPosicoes` < `concentracaoMaxima(` < `<LinhaChamadaOpcoes` < `<ChipsOrdenacaoPosicoes`; NÃO contém `<CapitalCurve` nem `portfolioMetrics(` mais de 1×.
2. App.jsx inteiro: `<CapitalCurve` exatamente 1× (reforço DEDUP-01); `portfolioMetrics(` exatamente 7×.
3. PainelPosicoes/ContadoresAtencao/BlocoHoje: `aria-pressed=`, `role="group"`, `minHeight: 44`, `quotesAt`, `hoje_lote_hora`, `tipoFonte`; CarteiraScreen passa `rotuloFonte: FONTE_LABEL`; BlocoHoje NÃO contém `source` (B1: nada de fonte/horário por item); e nenhuma conta nem ordenação de mercado no componente: `!/\.change\s*[-+*/]|sort\(|\.dayVal\s*[-+*/]|dayReturnPct\(/` sobre os corpos (ranking e % vêm do helper).
4. EvolucaoResultadoPosicao: contém `store.technicals(p.t, periodo)`, `hojeBRT()`, `reconstruirPosicao(`, `periodoCandles(`, `serieResultadoPosicao(`, `evo_sem_dados`, `evo_motivo_periodo`, `!periodo`, `evo_opcoes_fora`, `tentar_de_novo`, deps `[p.t, periodo, tentativa]`, `useState({ status: "carregando"`; NÃO contém `"idle"` (W4), `api.history`, `/api/history`, `<CapitalCurve`. GraficoResultadoPosicao contém `geometriaSerie(` e `role="img"` e não contém `Math.` nem `toFixed(` (geometria vem pronta).
5. CartaoPosicao contém `naFolha && <EvolucaoResultadoPosicao` e ele vem depois de `faceAcao}` e antes de `<BlocoBorisIA`.
6. Paridade de store por construção: `technicals` existe no serverStore e no deviceStore de persistence.js (contagem de `technicals` ≥ 2) e persistence.js não ganhou método `history(`/`candles(` novo.
7. Componentes novos dentro da fatia do transversal e na âncora W2: os 5 `function <Nome>(` têm índice entre `function LinhaPernaAvulsa(` e `function SeletorFace(` (e portanto entre `function ReguaPlano(` e `function LinhaChamadaOpcoes(`).
8. W6/W7, sobre os corpos sem comentários dos 5 componentes novos: nenhum `new Date`, `Date.`, `Intl.`, `toISOString`, `getFullYear`, `.slice(`, `.split(`, `padStart`, `toFixed(`, `Math.`, `.join(`, `.sort(`; e `evolucaoPosicao.js` contém `timeZone: "America/Sao_Paulo"`. Comentários das peças novas sem a palavra "econom" perto de "brapi" (W5).

Em `web/tests/test_ritmo_sp.mjs`, acrescentar à lista `componentesV6` (asserção atual: lista termina em `"CorpoLinhaLista"`; substituta: mesma lista + os 5 nomes) a linha `// 2026-10-13 (quick 261013-svo): + painel de atenção/hoje e evolução por posição.` e `"PainelPosicoes", "ContadoresAtencao", "BlocoHoje", "EvolucaoResultadoPosicao", "GraficoResultadoPosicao"`. Se algum recorte ficar < 200 chars (limite do guardião), não baixar o limite: enriquecer o componente ou registrar desvio no SUMMARY.

Guardiões afetados (asserção atual → substituta, nota `2026-10-13 (quick 261013-svo)`):
| Arquivo | Atual | Substituta |
|---|---|---|
| test_ritmo_sp.mjs | componentesV6 até `CorpoLinhaLista` | + 5 componentes novos |
| test_cartao_posicao_espelho.mjs (Tarefa 2) | NEUTRAS/ESPECIFICAS até as chaves da cqk | + 38 neutras e 3 específicas novas |
| test_painel_evolucao_ui.mjs | (novo) | grupos 1-8 acima |
Esperado SEM mudança (devem passar intactos): test_fase21_dedup_consolidacao, test_status_mercado_ui (7 chamadas), test_patrimonio_opcao_avulsa (7), test_carteira_lastro_ui, test_lista_posicoes_ui, test_cartao_v6_transversal/fechado/aberto, test_cartao_posicao_enxuto, test_estrutura_card_contraste, test_fase20_fundacao_visual, test_ui_onda_g. Se algum travar, NÃO apagar asserção: substituta datada + linha nesta tabela no SUMMARY.</action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2/web && f=0; for t in test_painel_evolucao_ui test_ritmo_sp test_evolucao_posicao_logica test_painel_posicoes_logica test_cartao_posicao_espelho test_cartao_v6_transversal test_cartao_v6_fechado test_cartao_v6_aberto test_cartao_posicao_enxuto test_lista_posicoes_ui test_lista_posicoes_logica test_fase21_dedup_consolidacao test_status_mercado_ui test_patrimonio_opcao_avulsa test_carteira_lastro_ui test_estrutura_card_contraste test_fase20_fundacao_visual test_ui_onda_g test_carteira_perna_avulsa test_hero_reconciliado test_api_parity; do node tests/$t.mjs >/dev/null || { echo "FALHOU: $t"; f=$((f+1)); }; done; echo "falhas=$f"; [ $f -eq 0 ] && npx vite build >/dev/null 2>&1</automated>
  </verify>
  <done>Os 21 arquivos passam, cada um rodado separado (o loop agrega falhas e imprime cada uma); test_painel_evolucao_ui existe com os 8 grupos de asserção; test_ritmo_sp lista os 5 componentes novos com nota datada; nada apagado; vite build ok.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| API de mercado → front | candles/cotações (brapi/Yahoo via servidor) entram na tela; podem faltar, atrasar ou vir incompletos |
| Store do usuário → helper | `data.history`/`positions` (deviceStore local no iOS, servidor no web) alimentam a reconstrução |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-svo-01 | Tampering (integridade do número) | serieResultadoPosicao | mitigate | Só desenha se qty reconstruída === p.qty e PM dentro de 0,01 × nº de compras; senão "Não há dados suficientes…" (princípio 4); casos 5a-5d testados |
| T-svo-02 | Tampering (dado de mercado inválido) | serieResultadoPosicao / painelHoje | mitigate | close não finito/≤0 ignorado; candle de hoje excluído; cotação com error/sem change fora do ranking e do dia (dia null → "—"), nunca R$ 0,00 inventado |
| T-svo-03 | Denial of Service (orçamento brapi 15k/mês) | EvolucaoResultadoPosicao | mitigate | Limita o NÚMERO de requisições: busca só ao montar a folha (`naFolha`), deps primitivas, sem polling, sem busca quando a reconstrução não fecha ou sem período, retry só por toque. O custo de cada requisição é o do candle_cache (2y no miss, delta depois) e o `period` não o reduz — nada aqui é apresentado como economia de orçamento |
| T-svo-04 | Information Disclosure | painel/gráfico | accept | Só dados do próprio usuário já presentes na tela; nada novo sai do aparelho |
| T-svo-05 | Repudiation / regulatório (IA perto de número) | todos | mitigate | Nenhuma chamada de IA; cálculos em módulos puros testados; copy sem promessa (filtro PROIBIDO do espelho) |
</threat_model>

<verification>
- Leva 1: verifies das Tarefas 1 e 2 (node + pytest test_skill_ref).
- Leva 2: verifies das Tarefas 3 e 4 (vite build + loop de guardiões, cada um separado).
- Orquestrador (fora do executor): suíte canônica `bash scripts/executar.sh --testes` uma vez ao final; `npx cap copy ios` só antes dela, se for o caso. Sem publicar, sem push, sem worktree.
- Conferência manual sugerida (preview local, 390x844, Estudo e Operador): painel com 0/1/vários níveis, tocar contador filtra e "Ver todas" volta; posição comprada há dias mostra a curva com ▲; posição com venda parcial mostra ▼ e o degrau; posição com opções mostra a nota; avião (offline) → "Tentar de novo".
</verification>

<success_criteria>
- D1: painel na ordem W3 com contadores tocáveis (aria-pressed, ≥44 px), estados lendo/nenhum, "Carteira no dia · só ações" idêntico ao Acompanhar (predicado único `cotacaoDoDiaValida`), maiores altas/baixas, UMA linha de fonte + horário do lote, link para o Acompanhar; hero inalterado; 7 chamadas de portfolioMetrics; 1 `<CapitalCurve`.
- D2: gráfico do resultado em aberto por pregão na folha, reconstruído de histórico + fechamentos, com marcas de compra/venda, fonte e "até <data>"; não desenha quando não fecha / sem compra / < 2 pregões; nota de opções; candles só ao abrir a folha via store.technicals.
- Toda conta em helper puro com tabela de casos; guardiões alterados com substituta datada; nenhuma dependência nova.
</success_criteria>

<output>
Follow-up a registrar no SUMMARY: horário por cotação (cada ativo com o próprio timestamp) exige mudança de backend em /api/quotes (yahoo.py:139/brapi) — fora desta task (B1).

Criar `.planning/quick/261013-svo-painel-de-evolucao-da-carteira/261013-svo-SUMMARY.md` (seções "Leva 1" e "Leva 2": commits, verifies, desvios, guardiões alterados, o que não foi verificado em runtime).
</output>
