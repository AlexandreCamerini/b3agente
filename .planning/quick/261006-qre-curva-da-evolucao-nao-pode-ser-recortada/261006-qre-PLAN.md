---
phase: quick-261006-qre
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - web/src/finance.js
  - web/tests/test_retorno_acumulado_base.mjs
  - server/app/skill_ref.py
  - web/src/copy.js
  - web/tests/test_vocabulario_espelho.mjs
  - server/tests/test_retorno_acumulado_base.py
  - web/src/App.jsx
autonomous: true
requirements: [QUICK-261006-QRE]

must_haves:
  truths:
    - "Com janela reiniciada (inicio > 0), a Evolução desenha TODOS os snapshots registrados + o ponto ao vivo; nada do começo some"
    - "retAcum, drawdown, base, baseInicio, baseOrigem, baseDesde e a série alinhada ao Ibovespa (ec.datas/ec.curve) continuam medidos só na janela — valores idênticos aos de hoje para os 11 casos do fixture"
    - "A parte anterior ao início da janela é visualmente distinta por padrão de traço (pontilhado + opacidade), não só por cor, e vem com UMA linha de legenda vinda de skill_ref ↔ copy.js nos 2 modos"
    - "Com inicio 0 (ou base indeterminada), curvaCompleta === curve e datasCompleta === datas (mesma referência): render idêntico ao atual, sem legenda nem marcador"
    - "Nenhum zero inventado: sem base, retAcum continua null; o texto de carimbada/carimbada_reinicio não muda"
  artifacts:
    - path: "web/src/finance.js"
      provides: "equityCurve expõe curvaCompleta, datasCompleta, inicioNaCurvaCompleta, diasJanela"
      contains: "inicioNaCurvaCompleta"
    - path: "server/app/skill_ref.py"
      provides: "dict CURVA_EVOLUCAO + curva_evolucao_txt"
      contains: "CURVA_EVOLUCAO = {"
    - path: "web/src/copy.js"
      provides: "COPY[modo].curvaEvolucao + curvaEvolucaoTxt (espelho byte a byte)"
      contains: "curvaEvolucao"
    - path: "web/src/App.jsx"
      provides: "CapitalCurve desenha a curva completa com trecho anterior distinto"
      contains: "ec.curvaCompleta"
  key_links:
    - from: "web/src/App.jsx CapitalCurve"
      to: "equityCurve().curvaCompleta"
      via: "pctCarteira mapeia ec.curvaCompleta; xAt sobre o comprimento completo"
      pattern: "ec\\.curvaCompleta\\.map"
    - from: "web/src/App.jsx CapitalCurve (Ibovespa)"
      to: "benchmarkSerie(ibov.candles, ec.datas)"
      via: "bm.pct[i] desenhado em xAt(i + k), k = ec.inicioNaCurvaCompleta"
      pattern: "benchmarkSerie\\(ibov\\.candles, ec\\.datas\\)"
    - from: "web/tests/test_vocabulario_espelho.mjs"
      to: "skill_ref.CURVA_EVOLUCAO ↔ COPY.*.curvaEvolucao"
      via: "DICTS/CHAVE_JS/CHAVES_ESPERADAS"
      pattern: "CURVA_EVOLUCAO"
---

<objective>
Corrigir a regressão da quick 261006-dvf: `equityCurve` (web/src/finance.js:289) faz `const snaps = r.serie.slice(r.inicio || 0)` e usa `snaps` também para a LINHA desenhada e as datas. Quando o resolvedor aceita a âncora num registro posterior (caso I2 do fixture: série legada sem base + snapshot âncora) ou a janela reinicia por aporte/retirada (casos E, F), o começo da curva some da tela. O patrimônio passado é dado real e não depende da base — só o retorno % depende.

Correção: a MEDIÇÃO (retAcum, drawdown, base, baseInicio, ec.curve/ec.datas usados por benchmarkSerie) segue na janela; a EXIBIÇÃO ganha a curva completa (`curvaCompleta`, `datasCompleta`, `inicioNaCurvaCompleta`), e o `CapitalCurve` desenha a curva inteira com o trecho pré-janela pontilhado/esmaecido + uma linha de legenda.

Output: finance.js + App.jsx (CapitalCurve) + texto novo em skill_ref ↔ copy.js + guardiões.
Não muda: deviceStore/serverStore (persistence.js), escrita de snapshot, fixture JSON (valores esperados intocados), bloco switch de petSnapshot (hash em test_telas_registro.mjs), texto de RETORNO_ACUMULADO.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@./CLAUDE.md
@.planning/quick/261006-dvf-acumulado-de-retorno-com-base-errada-ini/261006-dvf-SUMMARY.md
@.claude/skills/didatica-boris/SKILL.md

Regras de leitura: `web/src/App.jsx` NUNCA inteiro — Grep + Read offset/limit (CapitalCurve ≈ 2061-2236; fraseRetornoAcumulado ≈ 342-355). `web/src/finance.js` só 244-326. `web/src/copy.js`: Grep `retornoAcumulado` (≈ 600 e ≈ 1916) e `export function retornoAcumuladoTxt` (≈ 2694). `server/app/skill_ref.py`: Grep `RETORNO_ACUMULADO` (≈ 428-458).

<interfaces>
Estado atual (extraído do código em 2026-10-06):

finance.js
- `resolverBaseSerie(snapshots)` → `{ origem, base, inicio, desde, serie }`; `serie` já filtrada/ordenada; `inicio` indexa `serie`; `inicio` é null em sem_serie/inconsistente. NÃO alterar.
- `equityCurve(snapshots, budget, livePatr, todayYmd)` hoje retorna `{ curve, series, days, retAcum, drawdown, base, end, datas, baseOrigem, baseDesde, baseInicio }`.
  - `snaps = r.serie.slice(r.inicio || 0)`; `series` = patrimônios de `snaps`; `plot`/`datasPlot` = `series`/datas com o ponto ao vivo substituindo o snapshot de hoje (mesma data) ou anexado (data `todayYmd`).
  - `comPontoBase = r.origem === "carimbada"` → `curve = [base, ...plot]`, `datas = [null, ...datasPlot]`.
  - `retAcum = base > 0 ? ((end - base)/base)*100 : null`; drawdown percorre `curve`.
- `benchmarkSerie(candles, datas)` → `{ pct: (number|null)[] alinhado a datas, retAcum, ... } | null`. NÃO alterar.

App.jsx CapitalCurve (≈ 2061)
- `const ec = equityCurve(data.equitySnapshots, budget, patr, todayYmd);`
- `const hasSeries = ec.days >= 3;` / `const poucosDias = ec.days >= 1 && ec.days < 3;` (literais travados por test_fase21_dedup_consolidacao.mjs)
- `const series = ec.curve;` → `pctCarteira = series.map(v => ec.base > 0 ? ((v - ec.base)/ec.base)*100 : 0)`
- `bm = hasSeries && ibov ? benchmarkSerie(ibov.candles, ec.datas) : null`
- `xAt = (i) => (pctCarteira.length === 1 ? 0 : (i / (pctCarteira.length - 1)) * 300)`; `path` = carteira; `ibovPath` = Ibovespa (null interrompe com M)
- SVG: `<path d={ibovPath} ... stroke={P.textDim} strokeWidth="1.5" strokeDasharray="3 3" />` → área `<path d={`${path} L300,92 L0,92 Z`} fill={`url(#${gid})`} ... />` → `<path d={path} fill="none" stroke={up ? P.positive : P.negative} strokeWidth="2" />`
- `fraseRetornoAcumulado(ec, operador)` formata `ec.baseDesde` (YYYY-MM-DD → DD/MM/AAAA) e chama `retornoAcumuladoTxt`.

Guardiões estáticos sobre o corpo de CapitalCurve que NÃO podem quebrar:
- test_benchmark_curva.mjs: `strokeDasharray="3 3"` e `stroke={P.textDim}` no path `<path d={ibovPath}`; `cc.indexOf("<path d={ibovPath}") < cc.indexOf("<path d={path}")`; nenhuma linha com `bm.pct`/`ibovPath` contém `|| 0`/`?? 0`; `benchmarkSerie(ibov.candles, ec.datas)`; placeholder vazio intacto.
- test_chart_colors_theme_aware.mjs: `usePalette()` e NENHUM `fill={T.` / `stroke={T.` (atributo SVG usa `P.*`).
- test_fase21_dedup_consolidacao.mjs: `ec.days >= 3`, `ec.days >= 1 && ec.days < 3`, `cp.curvaPoucosDias(ec.days)`, `const { data, quotes, cp } = ctx;`, texto "Sua curva começa amanhã...".
- test_c09_drawdown_alerta.mjs: `LIMIAR_DRAWDOWN_ALERTA`, nenhum `disabled=`.
- test_retorno_acumulado_base.mjs / dvf: `ec.retAcum == null ?` presente e `(ec.retAcum || 0)` ausente em App.jsx.
- test_vocabulario_espelho.mjs: parser exige dict no formato `NOME = {` no início da linha, sub-bloco `"modo": {` ... `\n    },` e pares `"chave": "valor"` SEM aspas internas.
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: equityCurve expõe a curva completa (medição na janela, exibição inteira)</name>
  <files>web/src/finance.js, web/tests/test_retorno_acumulado_base.mjs</files>
  <behavior>
    - Para os 11 casos do fixture (budget 10000, live = c.fim, todayYmd "2099-01-01"): retAcum, origem, base, inicio, desde, drawdown e `datas.length === curve.length` continuam passando sem mudar nenhum valor do JSON.
    - Para cada caso: k = `ec.inicioNaCurvaCompleta` === (`e.inicio` ?? 0); `curvaCompleta.length === k + curve.length`; `datasCompleta.length === curvaCompleta.length`; `curvaCompleta.slice(k)` deep-igual a `curve`; `datasCompleta.slice(k)` deep-igual a `datas`; `curvaCompleta.slice(0, k)` deep-igual aos patrimônios dos k primeiros snapshots ordenados por data (resolverBaseSerie(c.snapshots).serie).
    - Casos com inicio 0 ou null (A, B, C, D1, D2, G, H, I1): `ec.curvaCompleta === ec.curve` e `ec.datasCompleta === ec.datas` (mesma referência) e k === 0.
    - Casos com inicio > 0 (E, F, I2): curvaCompleta contém TODOS os snapshots da série (contagem de valores com data em datasCompleta === nº de snapshots válidos) + o ponto ao vivo como último elemento (`curvaCompleta.at(-1) === c.fim`, `datasCompleta.at(-1) === "2099-01-01"`); retAcum/drawdown idênticos ao esperado do fixture.
    - Caso sintético de regressão (no .mjs, não no fixture): 30 snapshots legados sem base (2026-07-01..2026-07-30, patrimônio crescente) + 1 snapshot âncora (2026-07-31, base == patrimônio) + live com todayYmd "2026-08-01" → `curvaCompleta.length >= 32`, `inicioNaCurvaCompleta === 30`, `days === 31`, `diasJanela === 1`, retAcum calculado só desde a âncora.
    - Live com a mesma data do último snapshot (todayYmd = data do último): o último ponto de curvaCompleta é substituído pelo live (não anexado), igual ao comportamento de curve.
    - Leitura não muta a entrada (JSON.stringify antes/depois igual).
  </behavior>
  <action>
RED primeiro: acrescentar as asserções acima em `web/tests/test_retorno_acumulado_base.mjs` (dentro do laço existente sobre `fixture.casos` + bloco novo do caso sintético), com comentário de cabeçalho datado "2026-10-06 (quick 261006-qre): curva completa — a janela mede, a exibição mostra tudo". NÃO alterar `server/tests/fixtures/retorno_acumulado_casos.json` nem a asserção "fixture tem 11 casos". Rodar e ver falhar.

GREEN em `web/src/finance.js`, só dentro de `equityCurve` (resolverBaseSerie e benchmarkSerie intocados):
- Manter `snaps`, `series`, `plot`, `datasPlot`, `curve`, `datas`, `retAcum`, `drawdown`, `end` exatamente como hoje (medição na janela).
- Calcular `k = r.inicio || 0` e o prefixo `antes = r.serie.slice(0, k)`.
- `curvaCompleta = k > 0 ? [...antes.map(s => s.patrimonio), ...curve] : curve`; `datasCompleta = k > 0 ? [...antes.map(s => s.data), ...datas] : datas` (mesma referência quando k === 0 — é o que garante render idêntico ao atual). O ponto-base de `carimbada` (sem data) continua só onde já está em `curve`, logo fica na posição k da completa.
- `days` passa a ser o nº de snapshots da série inteira (`r.serie.length`): é o rótulo "DIAS REGISTRADOS" e o limiar `hasSeries` do CapitalCurve; com a janela reiniciada ontem a curva inteira sumiria sob o limiar antigo — mesma classe do bug. Expor também `diasJanela = series.length` (contagem antiga). Para inicio 0/null os dois valores coincidem (test_finance "dias = nº de snapshots" e os casos FIX-03 de test_fase21 seguem verdes sem edição).
- `series` mantém o significado atual (patrimônios da janela).
- Retornar adicionalmente `curvaCompleta, datasCompleta, inicioNaCurvaCompleta: k, diasJanela`.
- Atualizar o comentário do bloco: a janela vale para o retorno/drawdown/benchmark; o patrimônio anterior é dado real e entra só na exibição (nota datada 2026-10-06, quick 261006-qre, regressão da 261006-dvf). Remover a frase antiga "descartar não perde informação" (estava errada para a exibição).
Nada de 0 inventado: se `r.serie` vazia, `curvaCompleta === curve` (vazia ou só live), comportamento atual.
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2/web && node tests/test_retorno_acumulado_base.mjs && node tests/test_finance.mjs && node tests/test_numeros_fundamentados.mjs && node tests/test_c09_drawdown_alerta.mjs && node tests/test_fase21_dedup_consolidacao.mjs && node tests/test_benchmark_curva.mjs</automated>
  </verify>
  <done>Todos os 6 .mjs verdes; fixture JSON sem diff (`git diff --stat server/tests/fixtures/` vazio); equityCurve retorna os 4 campos novos; para inicio 0 `curvaCompleta === curve`; casos E/F/I2 e o sintético mostram a série inteira com retAcum idêntico ao fixture.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: CapitalCurve desenha a curva completa + legenda em skill_ref ↔ copy.js</name>
  <files>server/app/skill_ref.py, web/src/copy.js, web/tests/test_vocabulario_espelho.mjs, server/tests/test_retorno_acumulado_base.py, web/src/App.jsx, web/tests/test_retorno_acumulado_base.mjs</files>
  <behavior>
    - skill_ref.CURVA_EVOLUCAO["operador"|"educacional"]["antes_da_base"] ↔ COPY.operador/estudo.curvaEvolucao.antes_da_base idênticos byte a byte (test_vocabulario_espelho).
    - `curva_evolucao_txt(modo, "antes_da_base", desde="06/10/2026")` contém "06/10/2026" e não contém "{desde}"; chave desconhecida cai em `antes_da_base`; modo desconhecido cai em educacional. `curvaEvolucaoTxt` (JS) idem.
    - Guardião estático (corpo de CapitalCurve isolado por `indexOf("function CapitalCurve(")` até o próximo `"\nfunction "`): contém `ec.curvaCompleta.map`, `ec.inicioNaCurvaCompleta`, `curvaEvolucaoTxt(`, `benchmarkSerie(ibov.candles, ec.datas)`; o path do trecho anterior (`<path d={pathAntes}`) tem `strokeDasharray` diferente de "3 3" e `strokeOpacity`; a legenda é condicional a k > 0; App.jsx continua com `ec.retAcum == null ?` e sem `(ec.retAcum || 0)`.
  </behavior>
  <action>
Texto (Claude's discretion; tom dos modos conforme skill didatica-boris; sem aspas internas, sem promessa, sem número):
- `server/app/skill_ref.py`, logo após `retorno_acumulado_txt`: dict `CURVA_EVOLUCAO = {` com os modos "operador" e "educacional", cada um com uma única chave "antes_da_base", formatado igual a RETORNO_ACUMULADO (multilinha, `    },` fechando cada modo, `}` na coluna 0). Frases:
  - operador: "Antes de {desde} (pontilhado): só patrimônio registrado, fora da base do retorno."
  - educacional: "Antes de {desde} a linha fica pontilhada: mostra só o patrimônio registrado, porque o retorno acumulado só é medido a partir desse dia."
  Comentário datado 2026-10-06 (quick 261006-qre). Helper `curva_evolucao_txt(modo, chave, desde="")` com queda para "antes_da_base" e para "educacional", `{desde}` vazio vira "?" (mesmo padrão de retorno_acumulado_txt).
- `web/src/copy.js`: `curvaEvolucao: { antes_da_base: "..." }` em COPY.estudo (junto de `retornoAcumulado`, ≈ 600) e COPY.operador (≈ 1916), byte a byte, com comentário "espelho byte a byte de skill_ref.CURVA_EVOLUCAO"; `export function curvaEvolucaoTxt(mode, chave, vals)` logo após `retornoAcumuladoTxt`, mesmo padrão.
- `web/tests/test_vocabulario_espelho.mjs`: nota datada 2026-10-06 (quick 261006-qre) e `CURVA_EVOLUCAO` em DICTS, `CHAVE_JS.CURVA_EVOLUCAO = "curvaEvolucao"`, `CHAVES_ESPERADAS.CURVA_EVOLUCAO = ["antes_da_base"]`. Nenhuma asserção existente removida.
- `server/tests/test_retorno_acumulado_base.py`: 1 teste novo para `curva_evolucao_txt` (interpolação, quedas de chave/modo). Não tocar o teste parametrizado do fixture.

Render (`web/src/App.jsx`, só dentro de CapitalCurve; ler ≈ 2061-2236 com offset/limit; importar `curvaEvolucaoTxt` na linha de import de `./copy.js` onde já está `retornoAcumuladoTxt`):
- `const k = ec.inicioNaCurvaCompleta || 0;` e `const series = ec.curvaCompleta;` (atualizar o comentário: curva exibida = série inteira; a janela de retorno começa em k).
- `hasSeries`/`poucosDias` mantêm os literais `ec.days >= 3` e `ec.days >= 1 && ec.days < 3` (days agora é a série inteira, Task 1).
- `pctCarteira = ec.curvaCompleta.map(...)` com a MESMA transformação afim de hoje sobre `ec.base` (inclusive o ramo existente sem base — fora de escopo, não mexer). A transformação é monotônica, então o trecho anterior aparece na forma real do patrimônio; o eixo não tem rótulo de %, nada novo é afirmado.
- `bm = hasSeries && ibov ? benchmarkSerie(ibov.candles, ec.datas) : null` INALTERADO (Ibovespa compara só a janela). No laço de `ibovPath` usar `xAt(i + k)` — `bm.pct[i]` corresponde a `ec.datas[i]`, que fica na posição `i + k` da completa. Sem `|| 0`/`?? 0` nessas linhas.
- `path` (carteira, traço cheio) passa a cobrir só os índices `k..fim` (primeiro ponto com "M"); `pathAntes` cobre `0..k` (inclui o ponto k para ligar os trechos), vazio quando k === 0. Área: `${path} L300,92 L${xAt(k).toFixed(1)},92 Z` — com k === 0 equivale a `L0,92` (render idêntico).
- SVG, ordem: `<path d={ibovPath}` (inalterado) → `{pathAntes && <path d={pathAntes} fill="none" stroke={up ? P.positive : P.negative} strokeWidth="1.5" strokeOpacity="0.45" strokeDasharray="1 3" strokeLinecap="round" />}` → área → `<path d={path}` → quando k > 0, `<line x1={xAt(k)} x2={xAt(k)} y1="8" y2="84" stroke={P.chartGrid} strokeWidth="1" />` marcando o início da janela. Pontilhado "1 3" + opacidade ≠ tracejado "3 3" cinza do Ibovespa. Nenhum `stroke={T.` / `fill={T.`.
- Legenda (alternativa textual do trecho pontilhado; CapitalCurve não tem tabela hoje — confirmado por grep — então a linha visível é a alternativa): quando `hasSeries && k > 0`, logo abaixo do container do SVG, `<div>` fontSize "11px", color T.textFaint, marginTop "6px", lineHeight 1.4, com uma amostra `aria-hidden` (span inline 14px, `borderTop: \`2px dotted ${up ? T.positive : T.negative}\``, opacity 0.6 — CSS, não atributo SVG) + texto `curvaEvolucaoTxt(ctx.operador ? "operador" : "estudo", "antes_da_base", { desde })`, `desde` = `ec.baseDesde` formatado DD/MM/AAAA pelo mesmo regex de `fraseRetornoAcumulado`. Se `ec.baseDesde` não for string válida, não renderiza a legenda (nunca "?" na tela). Com k === 0 nada novo aparece.
- Não alterar: `fraseRetornoAcumulado`, stats (RETORNO ACUMULADO / DRAWDOWN / DIAS REGISTRADOS / VS. IBOVESPA), frase de indisponibilidade, card de drawdown, `retVsInicio`, o texto "vs. início"/"desde", Home (≈ 2273) e contexto do assistente (≈ 10398), bloco switch de petSnapshot.
- Guardião estático: acrescentar em `web/tests/test_retorno_acumulado_base.mjs` (lê App.jsx, nota datada 2026-10-06 quick 261006-qre) as asserções do <behavior> sobre o corpo isolado de CapitalCurve.
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2/web && node tests/test_retorno_acumulado_base.mjs && node tests/test_vocabulario_espelho.mjs && node tests/test_benchmark_curva.mjs && node tests/test_chart_colors_theme_aware.mjs && node tests/test_fase21_dedup_consolidacao.mjs && node tests/test_c09_drawdown_alerta.mjs && node tests/test_telas_registro.mjs && npx vite build && cd ../server && .venv/bin/python -m pytest -q tests/test_retorno_acumulado_base.py tests/test_skill_ref.py</automated>
  </verify>
  <done>Todos os .mjs listados verdes, pytest verde, `npx vite build` ok. CapitalCurve consome `ec.curvaCompleta`, desenha o trecho pré-janela pontilhado/esmaecido com marcador vertical e legenda de uma linha só quando k > 0; com k === 0 o JSX gera os mesmos paths de antes. `git diff web/src/persistence.js` vazio; bloco switch de petSnapshot sem diff.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| snapshots (servidor/aparelho) → equityCurve | série de patrimônio pode vir legada/inconsistente; só leitura, nunca escrita |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-qre-01 | Tampering (integridade do número) | equityCurve retAcum/drawdown | mitigate | medição permanece na janela; 11 casos do fixture travam retAcum/inicio/origem sem alteração de valores esperados |
| T-qre-02 | Repudiation/transparência (comparar períodos diferentes) | benchmarkSerie no CapitalCurve | mitigate | Ibovespa segue alinhado a `ec.datas` (janela), desenhado em xAt(i + k); guardião estático exige `benchmarkSerie(ibov.candles, ec.datas)` |
| T-qre-03 | Information disclosure / leitura enganosa | trecho pré-janela | mitigate | traço pontilhado + opacidade + legenda explícita de que ali não há base de retorno; legenda omitida se `baseDesde` inválida (sem "?") |
| T-qre-04 | Tampering (persistência) | persistence.js | accept | não tocado; leitura não muta a entrada (asserção existente) |
</threat_model>

<verification>
Orquestrador, fora do sandbox, após a execução:
- `cd web && npx vite build`
- `cd web && npx cap copy ios`
- `bash scripts/executar.sh --testes; echo "rc=$?"` com rc gravado no SUMMARY
- `git diff --stat server/tests/fixtures/ web/src/persistence.js` vazio
</verification>

<success_criteria>
- Série com janela reiniciada (inicio > 0) → `curvaCompleta` tem todos os snapshots + ponto ao vivo; retAcum/drawdown idênticos aos de hoje.
- Série com inicio 0 → `curvaCompleta === curve`, sem legenda nem marcador, paths idênticos.
- Trecho anterior distinto por padrão de traço (não só cor) + legenda de uma linha nos 2 modos, paridade byte a byte skill_ref ↔ copy.js.
- Guardiões listados verdes; nenhuma asserção válida apagada; reconciliações com nota datada 2026-10-06.
- Sem push/bump/publicar; sem segredos.
</success_criteria>

<output>
Create `.planning/quick/261006-qre-curva-da-evolucao-nao-pode-ser-recortada/261006-qre-SUMMARY.md` when done
</output>
