---
phase: quick-261013-svo
plan: 01
status: complete
---

# Quick 261013-svo: Painel de evolução da carteira — Summary

Completa: Leva 1 (Tarefas 1 e 2, helpers puros e copy) e Leva 2 (Tarefas 3 e 4, App.jsx e guardiões).

## Leva 1

### Commits
- `e1919b60` feat(quick-261013-svo): reconstrução determinística do resultado em aberto por posição (Tarefa 1: `web/src/evolucaoPosicao.js`, `web/tests/test_evolucao_posicao_logica.mjs`)
- `8e2ba92d` feat(quick-261013-svo): painelPosicoes puro, predicado único do dia e copy do painel/evolução nos dois modos (Tarefa 2: `web/src/finance.js`, `web/src/painelPosicoes.js`, `web/tests/test_painel_posicoes_logica.mjs`, `server/app/skill_ref.py`, `web/src/copy.js`, `web/tests/test_cartao_posicao_espelho.mjs`)

### Verifies (todos verdes)
- Tarefa 1: `node tests/test_evolucao_posicao_logica.mjs` — 56 asserções ok, exit 0 (RED confirmado antes: módulo ausente).
- Tarefa 2: `test_painel_posicoes_logica`, `test_cartao_posicao_espelho`, `test_copy_theme`, `test_finance`, `test_status_mercado_ui`, `test_patrimonio_opcao_avulsa` — falhas=0; `server/tests/test_skill_ref.py` — 49 passed. RED do painel confirmado (import falhava antes do export de `cotacaoDoDiaValida`).
- `grep -c "portfolioMetrics(" web/src/App.jsx` = 7 (App.jsx não foi tocado). Suíte canônica, `vite build` e `cap copy ios` NÃO rodados (fora desta leva).

### Desvios
- Nenhum de regra. Duas decisões de detalhe nos helpers, registradas:
  1. `serieResultadoPosicao`: com `parcial`, marcas de operações com `ymd < desde` são descartadas (necessário para o caso 11 da tabela, marcas `[]`); sem `parcial`, a marca vai para o 1º ponto com data >= `op.ymd` (casos 1 e 12).
  2. `painelHoje`: ordenação de altas/baixas usa só comparadores `<`/`>` (sem subtração sobre `change`), para respeitar a regra "sem aritmética" também no helper.
- Candle de `hojeYmd` inválido/ausente em `serieResultadoPosicao` devolve `candles_insuficientes` (a spec não cobre; comportamento conservador, nada é desenhado).

### Interfaces exatas para a leva 2

`web/src/evolucaoPosicao.js` (puro)
- `parseDataOperacao(s) -> "AAAA-MM-DD" | null`
- `hojeBRT(agora = new Date()) -> "AAAA-MM-DD" | null` (único lugar com Intl/fuso, `timeZone: "America/Sao_Paulo"`)
- `ymdParaBr(ymd) -> "dd/mm/aaaa" | null`
- `PERIODOS_CANDLES` congelado `[["1mo",22],["3mo",66],["6mo",126],["1y",252],["2y",504]]`
- `periodoCandles(inicioYmd, hojeYmd) -> "1mo"|"3mo"|"6mo"|"1y"|"2y"|null`
- `reconstruirPosicao({ ticker, history, posicao }) -> { ok:true, inicioYmd, ops:[{ymd,tipo,qtyDepois,pmDepois}], nCompras } | { ok:false, motivo: "sem_posicao"|"sem_compra"|"nao_fecha" }`
- `serieResultadoPosicao({ ticker, history, candles, posicao, hojeYmd }) -> { ok:true, pontos:[{data,resultado}], marcas:[{data,tipo:"compra"|"venda"}], inicio, ate, parcial, desde, inicioBr, ateBr, desdeBr, min, max, ultimo } | { ok:false, motivo }` com motivo em `sem_posicao | sem_compra | nao_fecha | candles_insuficientes` (propaga os da reconstrução). Mapeamento de motivo para copy: `sem_compra` -> `evo_motivo_sem_compra`; `nao_fecha` e `sem_posicao` -> `evo_motivo_nao_fecha`; `candles_insuficientes` -> `evo_motivo_candles`; período nulo (rec.ok sem `periodoCandles`) -> `evo_motivo_periodo`.
- `geometriaSerie({ pontos, marcas, largura = 280, altura = 72, margem = 4 }) -> { d, yZero, marcas:[{x,y,tipo}], W, H }` (números crus em x/y/yZero; `d` já com toFixed(1)).

`web/src/painelPosicoes.js` (puro; importa só `dayReturnPct` e `cotacaoDoDiaValida` de finance.js)
- `NIVEIS_PAINEL` = `[0..5]`; `CHAVE_NIVEL` = `{0:"atn_risco",1:"atn_perto_stop",2:"atn_vence",3:"atn_sem_plano",4:"atn_perto_alvo",5:"atn_sem_leitura"}`
- `resumoAtencao([{ t, nivel, lendo }]) -> { estado:"lendo" } | { estado:"nenhum" } | { estado:"ok", grupos:[{nivel,n}] }` (RISCO primeiro)
- `filtroVigente(filtro, resumo) -> nivel | null` (nível 0 é válido; use comparação com `null`, não truthiness)
- `filtrarPorNivel(linhas, nivel)` -> novo array (nivel null/undefined = cópia inteira); lê `linha.nivel`
- `painelHoje({ positions, quotes, patr, dayVal, rotuloFonte, n = 2 }) -> { dia:{valor,pct}|null, altas:[{t,change}], baixas:[{t,change}], semCotacao:[t], semCotacaoTxt, fontes:[source], tipoFonte:"uma"|"varias"|"nenhuma", fontesTxt }`. Atenção: itens de altas/baixas usam a chave `t` (não `ticker`) e `change` em %; `hoje_item` recebe `{ ticker: item.t, pct: pct(item.change) }`. `dia` é `null` só quando nenhuma posição tem cotação válida.

`web/src/finance.js`
- `export function cotacaoDoDiaValida(quote) -> boolean` (predicado único de `portfolioMetrics`); `dayReturnPct(patr, dayVal)` inalterado.

Copy (`cartaoPosicaoTxt(modo, chave, vals)`; 41 chaves em `skill_ref.CARTAO_POSICAO` e `COPY.{estudo,operador}.cartaoPosicao`, inseridas depois de `folha_aria`)
- Neutras (38): `atn_grupo_aria`, `atn_risco`, `atn_perto_stop`, `atn_vence`, `atn_sem_plano`, `atn_perto_alvo`, `atn_sem_leitura`, `atn_contador_aria` ({rotulo},{n}), `atn_lendo`, `atn_ver_todas`, `atn_mostrando` ({rotulo},{n}), `hoje_titulo`, `hoje_carteira_dia`, `hoje_altas`, `hoje_baixas`, `hoje_item` ({ticker},{pct}), `hoje_sem_cotacao` ({tickers}), `hoje_sem_dado`, `hoje_fonte_uma` ({fonte},{lote}), `hoje_fontes` ({fontes},{lote}), `hoje_sem_fonte` ({lote}), `hoje_lote_hora` ({hora}), `hoje_sem_hora`, `hoje_link_evolucao`, `evo_titulo`, `evo_fonte` ({fonte},{data}), `evo_fonte_desconhecida`, `evo_desde_janela` ({data}), `evo_opcoes_fora`, `evo_carregando`, `evo_falha`, `evo_motivo_sem_compra`, `evo_motivo_nao_fecha`, `evo_motivo_candles`, `evo_motivo_periodo`, `evo_leg_compra`, `evo_leg_venda`, `evo_aria` ({ticker},{inicio},{fim},{min},{max},{ultimo}).
- Específicas por modo (3): `atn_nenhuma`, `evo_sem_dados`, `evo_explica`.
- Reusar `tentar_de_novo` (já existente).
- Guardião `test_cartao_posicao_espelho.mjs` estendido (NEUTRAS + ESPECIFICAS) com a nota `2026-10-13 (quick 261013-svo)`; nada removido.

### Pontos de atenção para a leva 2
- `hojeBRT`, `ymdParaBr` e `periodoCandles` existem para que o componente não toque em Date/Intl/toFixed (guardião do grupo 8 da Tarefa 4).
- Nenhum comentário/copy/SUMMARY afirma economia de brapi (o período só recorta a cauda do payload).
- `git status`: apenas o diretório `.planning/quick/261013-svo-...` untracked; SUMMARY/PLAN/CONTEXT/STATE.md não commitados, como pedido.

## Leva 2

### Commits
- `abd0b51d` feat(quick-261013-svo): painel de atenção/hoje na aba Posições com filtro tocável e gráfico do resultado em aberto na folha (Tarefa 3: `web/src/App.jsx`)
- `ff09e933` test(quick-261013-svo): guardião estático do painel, do filtro e do gráfico da folha; test_ritmo_sp cobre os 5 componentes novos (Tarefa 4: `web/tests/test_painel_evolucao_ui.mjs`, `web/tests/test_ritmo_sp.mjs`)

### O que entrou
- 5 componentes (`ContadoresAtencao`, `BlocoHoje`, `PainelPosicoes`, `GraficoResultadoPosicao`, `EvolucaoResultadoPosicao`) imediatamente antes do comentário que abre `SeletorFace`, dentro da fatia do transversal.
- `CarteiraScreen`: `filtroNivel` (estado), `resumo`/`filtro`/`hoje`/`avulsasVisiveis`/`grupoFiltro` derivados, reusando `m` (portfolioMetrics continua 7). Ordem: hero, aviso de opções, painel, concentração, chamada de opções, vazio, linha "Mostrando só", chips, lista. Filtro comparado com `null` (nível 0 é válido).
- `CartaoPosicao`: `{naFolha && <EvolucaoResultadoPosicao .../>}` depois da face e antes do `BlocoBorisIA`.
- Candles só ao montar a folha, por `store.technicals(p.t, periodo)` (sem método novo em store). Marcas ▲/▼ do gráfico são `<path>` com `translate(x y)` e triângulo fixo (sem conta no componente); cores por `style`, não por atributo.

### Verifies
- Tarefa 3 (`vite build` + 14 guardiões, cada um separado): falhas=0; `<CapitalCurve` = 1; `portfolioMetrics(` = 7.
- Tarefa 4: `test_painel_evolucao_ui` e `test_ritmo_sp` ok; `vite build` ok.

### Guardiões alterados
| Arquivo | Asserção antiga | Substituta |
|---|---|---|
| test_ritmo_sp.mjs | `componentesV6` até `CorpoLinhaLista` | mesma lista + `PainelPosicoes`, `ContadoresAtencao`, `BlocoHoje`, `EvolucaoResultadoPosicao`, `GraficoResultadoPosicao` (nota `2026-10-13 (quick 261013-svo)`) |
| test_cartao_posicao_espelho.mjs (Leva 1) | NEUTRAS/ESPECIFICAS até as chaves da cqk | + 38 neutras e 3 específicas |
| test_painel_evolucao_ui.mjs | (novo) | grupos 1-8 do PLAN, mais checagem de `filtro !== null` |

Nenhuma asserção removida; nenhum outro guardião precisou de substituta.

### Loop completo de `web/tests/*.mjs` (221 arquivos, cada um separado)
- 220 ok, 1 falha: `test_ios_assets.mjs` ("MESMO build nos dois lados": chunks do `dist` recém-gerado pelo `vite build` ausentes no bundle do iOS). Não é regressão de código: o `vite build` desta leva gerou hashes novos e o bundle do iOS só se alinha com `npx cap copy ios`, que o PLAN reserva ao orquestrador antes da suíte canônica. Deve passar depois do `cap copy ios`.

### Desvios
- Nenhum de regra. `NIVEIS_PAINEL` não foi importado em App.jsx (o painel só usa `CHAVE_NIVEL`); a constante segue exportada e usada dentro de `painelPosicoes.js`.
- Linha "Mostrando só" (`atn_mostrando`) usa `grupoFiltro` derivado em `CarteiraScreen` (via `resumo.grupos.find`), fora dos 5 componentes novos.

### Não verificado em runtime
- Layout no aparelho (390x844), painel com 0/1/vários níveis, quebra de linha dos contadores.
- Gráfico nos dois modos (Estudo/Operador) com candles reais, marcas ▲/▼ sob `preserveAspectRatio="none"`, posição com venda parcial.
- Posição com estrutura de opções (nota `evo_opcoes_fora`) e posição só de opções.
- Filtro tocável (aria-pressed, "Ver todas", filtro que some quando o nível zera) e `A.go("evolucao")`.
- Estado de falha de candles com "Tentar de novo" (modo avião).
- Suíte canônica, `cap copy ios` e `test_ios_assets` ficam com o orquestrador.

### Follow-ups
- Horário por cotação: exige mudança de backend em `/api/quotes` (yahoo.py:139 e brapi). Hoje o painel mostra uma linha de fonte e horário do LOTE, mesma convenção da Watchlist. O texto original do CONTEXT falava em horário por cotação; a troca foi decidida pelo orquestrador e deve ser informada ao Alex.
- Snapshot diário no servidor (curva de patrimônio e série por posição sem depender de reconstrução): fora de escopo, segue como follow-up.

## Verificação do orquestrador (2026-10-13)
- Gate entre levas: verifies da leva 1 re-rodados pelo orquestrador antes da leva 2 (9 guardiões ok, test_skill_ref 49 ok, `portfolioMetrics(` = 7).
- Suíte canônica após a leva 2 (com `cap copy ios` antes): rc=0, pytest 3493 passed + todos os .mjs (o `test_ios_assets` que o executor viu falhar era só bundle iOS desatualizado; passou após o cap copy).
- App local (preview `api-qa-opcoes`, banco local de dev, conta de teste local), 390x844, Modo Estudo:
  - Painel: "1 Em risco" (BBAS3 abaixo do stop); tocar filtra a lista para BBAS3 com "Mostrando só: Em risco (1)"; "Ver todas" restaura; `aria-pressed` correto.
  - Hoje: "Carteira no dia · só ações", maiores altas/baixas e "Fonte: Yahoo · cotações de 13/10/2026 21:28" (horário do lote).
  - Gráfico na folha: PETR4 comprada no dia → "Não há dados suficientes… Menos de 2 pregões fechados desde a compra." VALE3 com histórico retroativo inserido SÓ no banco local de teste (compras 22/09 e 01/10, venda parcial 06/10) → curva desenhada com ▲/▼ nas datas certas, "Fechamentos diários · Yahoo · até 09/10/2026" (12/10 feriado; candle do dia fora).
  - FAB do Bóris não cobre linhas de posição no fim da lista (fica sobre "Ver histórico de operações", como antes).
- Decisão do orquestrador registrada no CONTEXT: horário do lote em vez de horário por cotação (payload não tem; mesma convenção da Watchlist). Informado ao Alex no fechamento.
- Não conferido: Modo Operador; posição com opções (nota evo_opcoes_fora); falha de candles com "Tentar de novo"; layout no aparelho.
