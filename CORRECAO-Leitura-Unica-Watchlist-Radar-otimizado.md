# Correção: um ativo, uma leitura — Watchlist e Radar divergem

## Objetivo

Restaurar a invariante do produto: **o mesmo ativo, olhado no mesmo instante,
tem uma única leitura em todas as telas**. Hoje TIMS3 aparece como "Estudar
baixa · Setup 9.3" na Watchlist e "Estudar alta · Reversão de sobrevenda" no
Radar, simultaneamente, com preços e variações também diferentes.

Duas leituras contraditórias do mesmo papel destroem a confiança no plano
educacional — que é o produto.

## Evidência (capturada em 2026-08-09, domingo, mercado fechado)

| | Watchlist | Radar de mercado |
|---|---|---|
| TIMS3 — plano | Estudar **baixa** | Estudar **alta** |
| TIMS3 — setup | Setup 9.3 (baixa) | Reversão de sobrevenda |
| TIMS3 — preço | R$ 18,76 | R$ 18,90 |
| TIMS3 — variação | −0,74% | −11,72% |
| carimbo na tela | cotações 09/08/2026 19:50 | varredura de 07/08 08:45 |

## O que já foi verificado no código — parta daqui, não re-investigue

**O repositório único do ativo está íntegro.** `server/app/technical_snapshot.py`
(STU) é a fonte única, e os dois caminhos convergem para a mesma função de
cálculo: `technical_snapshot.build` → `setups.detect_setups`. Não existe
segunda implementação de veredito/confluência/setup — nem no backend nem no
frontend, que só lê `r.veredito` / `sc.veredito`. Não há duplicação para
remover.

**Causa raiz 1 — bifurcação de caminho de dados em `server/app/main.py:736`:**

- `GET /api/scan?tickers=…` (Watchlist, `web/src/api.js:217`) → chama
  `scanner.run_scan` **a cada request**, cache de 60 s em `scanner._SCAN_CACHE`,
  sobre `candle_cache` revalidado a cada 45 s.
- `GET /api/scan` sem `tickers` (Radar, `web/src/App.jsx:5244`) → serve o
  payload **congelado** de `radar_daily.get_stored`, gravado no kv sob
  `radarDaily:{period}`.

`radar_daily.get_stored` (`server/app/radar_daily.py:77`) **não tem política de
expiração**: só verifica se o dict tem `results`. O payload só é substituído por
`should_run` (`radar_daily.py:47` — dia útil, hora ≥ 08:45 BRT, ainda não rodou
hoje) ou por `?force=1`. 08/08 foi sábado e 09/08 domingo, então a varredura de
sexta persiste sem nenhum aviso além do rótulo.

**Causa raiz 2 — semânticas diferentes no mesmo slot, em `web/src/App.jsx:5375`:**

```js
q: { price: r.close, change: r.variacaoPeriodoPct, error: false }
```

O Radar injeta campos do snapshot no slot da cotação do `AtivoCard`.
`r.variacaoPeriodoPct` é a variação do **período inteiro** (1 ano, calculada em
`technical_snapshot.py:137`); a Watchlist põe ali `regularMarketChangePercent`,
a variação **do dia**. Os dois passam pelo mesmo `pct()`, sem rótulo que os
distinga. Este defeito sobrevive à correção do frescor — trate-o como item
próprio.

**Lacuna de teste:** `server/tests/test_snapshot_consistency.py` trava a
coerência N1×N2×N3 *dentro de um snapshot*. Nada compara o ramo `?tickers=` com
o ramo armazenado para o mesmo ticker, e nada cobre a semântica de `change` em
`radarVm`.

## Invariante a restaurar

Para um mesmo ticker exibido em duas telas ao mesmo tempo, o usuário nunca vê
vereditos que se contradizem. Quando uma tela mostra dado mais velho que a
outra, isso é **visível e nomeado na interface** — o app diz de quando é aquela
leitura, em vez de apresentar duas verdades lado a lado.

Você decide a arquitetura da correção. Três direções plausíveis, e a escolha é
sua desde que a invariante e as restrições abaixo sejam respeitadas:

1. Radar passa a servir leitura viva para os ativos que a Watchlist também
   mostra, mantendo o armazenamento para o resto do universo.
2. As duas telas passam por um mesmo portão de frescor, que decide recalcular
   ou servir do armazenamento com o mesmo critério.
3. O payload armazenado ganha política de validade, e o que expirou é
   recalculado sob demanda em vez de servido em silêncio.

Se você discordar de todas as três e vir uma quarta melhor, siga com ela e diga
em uma frase por quê.

## Restrições

- **Preserve a razão de a varredura diária existir.** Ela varre 74 ativos e roda
  1×/dia por custo e latência. Fazer o Radar recalcular o universo inteiro a
  cada request troca um defeito por outro.
- **O filtro CVM vale antes de qualquer outro.** Vocabulário educacional, sem
  imperativo de compra/venda; a LLM não entra nesse caminho — o cálculo é
  determinístico e assim permanece.
- **`Modo Operador` intacto.** As chaves de `/api/timing` nos dois modos são
  congeladas por teste; nada aqui as altera.
- **Paridade dos dois stores.** Se tocar em `web/src/persistence.js`, método novo
  entra no `deviceStore` (nativo) e no `serverStore` (web).
- **Entregue no escopo pedido.** Decida sozinho o rotineiro; sinalize em uma
  frase se discordar de algo e siga em frente. Este é um bug de coerência de
  dados, não uma oportunidade de refatorar o `AtivoCard`.
- **Sem subagentes** — o terreno já está mapeado acima.

## Critério de aceite

A entrega está pronta quando todos estes forem verdade, com a evidência real de
execução colada na resposta (saída do pytest, não afirmação de que passou):

1. **Teste novo que trava a invariante Watchlist×Radar.** Para um mesmo ticker,
   o que o ramo `?tickers=` devolve e o que o ramo armazenado devolve não podem
   apresentar vereditos conflitantes ao usuário. O teste falha contra o código
   atual e passa depois da correção — mostre as duas execuções.
2. **Teste novo sobre a semântica de `change` em `radarVm`**, garantindo que
   variação de período e variação do dia não ocupam o mesmo campo sem
   distinção.
3. **`bash scripts/test.sh` verde**, sem regressão nos testes existentes de
   `test_snapshot_consistency.py`, `test_radar_daily.py`, `test_scanner.py`,
   `test_setups.py` e `test_setups_br.py`.
4. **Verificação ao vivo, não só unitária.** Suba o app pelo
   `.claude/launch.json` do projeto, abra Watchlist e Radar, e mostre um
   screenshot de um ticker presente nas duas telas com a leitura coerente.
   Bugs desta família já escaparam de testes unitários e só apareceram na tela.
5. **A divergência de preço e variação sumiu** ou está explicitamente rotulada,
   de modo que dois números com semânticas diferentes nunca aparecem com a
   mesma formatação e sem nome.

## Fora de escopo

Redesenho do `AtivoCard`, mudanças no motor de setups, ajuste dos critérios de
confluência, e a decisão sobre trocar de provedor de cotações.
