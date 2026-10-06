---
phase: quick-261006-dvf
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - server/app/store.py
  - server/app/skill_ref.py
  - server/app/main.py
  - server/tests/fixtures/retorno_acumulado_casos.json
  - server/tests/test_retorno_acumulado_base.py
  - server/tests/test_persistence.py
  - web/src/finance.js
  - web/src/persistence.js
  - web/src/copy.js
  - web/src/App.jsx
  - web/tests/test_retorno_acumulado_base.mjs
  - web/tests/test_finance.mjs
  - web/tests/test_numeros_fundamentados.mjs
  - web/tests/test_vocabulario_espelho.mjs
autonomous: true
requirements: [QUICK-261006-dvf]

must_haves:
  truths:
    - "O caso real (snapshots antigos sem base com patrimônio ~1.000.000, `initialBudget` 10.000 e snapshots posteriores carimbados com base 10.000) exibe o retorno medido desde o 1º dia registrado (≈ +2,9 %), nunca +10.193 %"
    - "Snapshot cuja série começa com `base` carimbada mede o retorno sobre essa base (comportamento atual preservado: +8 % com orçamento adulterado para 380)"
    - "Série sem base no início e sem âncora válida depois mede o retorno desde o 1º dia registrado e a tela diz isso, com a data"
    - "Sem nenhum snapshot válido, ou com bases inconsistentes, o acumulado aparece como `—` com o motivo, e `retAcum` é null (nunca 0, nunca calculado sobre o `initialBudget`)"
    - "Mudança de capital (orçamento alterado antes de qualquer operação: aporte ou retirada) reinicia a janela de medição: não vira retorno (+400 %) nem drawdown (-80 %)"
    - "Front (`equityCurve`) e backend (`_pet_resumo_evolucao`) produzem a MESMA base, origem e retorno para os mesmos casos (fixture compartilhado)"
    - "Ler o acumulado nunca reescreve `equitySnapshots` gravados"
    - "deviceStore e serverStore carimbam `base` pela MESMA regra e os dois zeram a série no Recomeçar do zero"
  artifacts:
    - path: "server/tests/fixtures/retorno_acumulado_casos.json"
      provides: "Casos numéricos únicos da paridade front×backend"
      contains: "casos"
    - path: "server/app/store.py"
      provides: "resolver_base_serie (puro) + regra de carimbo em upsert_snapshot"
      contains: "def resolver_base_serie"
    - path: "web/src/finance.js"
      provides: "resolverBaseSerie (gêmeo) + equityCurve usando-o"
      contains: "export function resolverBaseSerie"
    - path: "server/app/skill_ref.py"
      provides: "RETORNO_ACUMULADO por modo + retorno_acumulado_txt"
      contains: "RETORNO_ACUMULADO = {"
    - path: "web/src/copy.js"
      provides: "COPY[modo].retornoAcumulado espelho byte a byte + retornoAcumuladoTxt"
      contains: "retornoAcumulado"
  key_links:
    - from: "server/app/main.py:_pet_resumo_evolucao"
      to: "store.resolver_base_serie"
      via: "chamada direta, sem usar cfg.initialBudget como divisor"
      pattern: "resolver_base_serie\\("
    - from: "web/src/finance.js:equityCurve"
      to: "resolverBaseSerie"
      via: "chamada interna"
      pattern: "resolverBaseSerie\\("
    - from: "web/src/App.jsx:CapitalCurve"
      to: "ec.retAcum / ec.baseOrigem"
      via: "retVsInicio deixa de usar budget"
      pattern: "retornoAcumuladoTxt\\("
    - from: "web/tests/test_retorno_acumulado_base.mjs"
      to: "server/tests/fixtures/retorno_acumulado_casos.json"
      via: "readFileSync do mesmo fixture que o pytest lê"
      pattern: "retorno_acumulado_casos\\.json"
---

<objective>
Corrigir o retorno acumulado exibido com base errada (dívida ALTA, 46.1-05-SUMMARY, Achados item 2: +10.193 % exibido para retorno real ≈ +2,9 %). A base passa a ser resolvida de forma determinística na LEITURA a partir da própria série de snapshots, sem reescrever o histórico gravado e sem usar `initialBudget` (campo de formulário) como divisor. Na ESCRITA, `base` só é carimbada quando é comprovadamente o capital aportado. Mudança de capital entra como fluxo (reinicia a janela), não como retorno.

Purpose: princípio 5 (número determinístico) e "resultados sem manipulação". Número errado na tela é pior que "—".
Output: resolvedor puro gêmeo (Python + JS) com fixture de paridade, regra de carimbo nos dois stores, texto por origem nos dois modos (skill_ref ↔ copy.js), consumidores (CapitalCurve, Home, contexto do assistente, `pet:evolucao`) usando a base resolvida.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@./CLAUDE.md
@.claude/skills/didatica-boris/SKILL.md
@.planning/phases/46.1-fechamento-das-ressalvas-da-fase-46/46.1-05-SUMMARY.md

## Investigação (feita no planejamento, 2026-10-06) — conclusões que o executor NÃO precisa refazer

### (1) Onde o acumulado é calculado e qual base cada um usa
- `web/src/finance.js:243 equityCurve(snapshots, budget, livePatr, todayYmd)` — base = `base` do PRIMEIRO snapshot que tiver carimbo (`snaps.find`, não necessariamente o 1º cronológico); sem carimbo, `initialBudget`; sem os dois, 1º snapshot. Quando `b > 0` antepõe o ponto-base à curva (`datas[0] = null`). `retAcum` cai em `0` quando base ≤ 0 (viola null-nunca-zero).
- Consumidores no front (`web/src/App.jsx`, NUNCA ler inteiro): `CapitalCurve` em ~2045 (`ec` em 2056; `retVsInicio` em 2057 usa `budget` DIRETO — segunda fonte do bug, exibida em ~2150 como "vs. início"; stat "RETORNO ACUMULADO" em ~2175); Home em ~2251 (`ec`) e ~2342 (`ACUMULADO`, `aColor` em ~2270 com `ec.retAcum || 0`); contexto do assistente `case "evolucao"` em ~10373–10379 (`retornoAcumuladoPct: ec.retAcum`); gravação do snapshot diário em ~10088 (`store.putSnapshot({data, patrimonio, caixa, posicoesValor})`).
- Backend: `server/app/main.py:4798 _pet_resumo_evolucao` usa `cfg.initialBudget` como base (NEM lê o carimbo — diverge de `finance.js`), fala "Desde o orçamento inicial, o retorno acumulado é de {ret:+.1f}%" (ponto decimal). `ret_acum = 0.0` quando base ≤ 0.
- Benchmark (`benchmarkSerie`) mede o Ibovespa desde a 1ª data COBERTA de `ec.datas`; não usa base de carteira. Só depende de `ec.datas` ficar paralelo a `ec.curve` — preservar.

### (2) Origem do capital
- `initialBudget`: campo de config editável (`store.update_config` ~223 / `persistence.js` ~743). Mexe no CAIXA só quando não há posições nem histórico (`store.py:231`) — esse é o ÚNICO evento de aporte/retirada que existe no sistema (não há feature de aporte). Com operação, editar o campo não mexe no caixa.
- `reset_portfolio` (`store.py:353`): caixa = `initialBudget`, zera posições/histórico/`equitySnapshots` (servidor). **Furo de paridade**: `deviceStore.resetPortfolio` (`persistence.js` ~1097–1119) NÃO zera `doc.equitySnapshots` em nenhum dos dois ramos (logado via `_adotarCarteiraDoServidor`, que não adota snapshots; e local).
- `caixaReservado` é derivado de ordens pendentes e entra no patrimônio; não é fluxo de capital.
- Reconstruir o capital pelo ledger (`history`) foi DESCARTADO: 8+ escritores de histórico (ações, opções, vencimento, pendentes, agente) — reconstrução errada seria um número inventado com cara de exato.

### (3) Formato dos snapshots e por que a base saiu errada
- Servidor (`store.upsert_snapshot` ~1478): `{data, patrimonio, caixa, posicoesValor, base}`; `base` = base do 1º snapshot QUE TENHA base, senão `initialBudget` corrente. **Causa do +10.193 %**: a série herdada do aparelho não tinha `base` → o servidor carimbou `initialBudget` (10.000) nos snapshots NOVOS → `equityCurve` achou esse carimbo e dividiu ~1.029.000 por 10.000.
- `deviceStore` (`persistence.js:82 upsertSnapshot`) NUNCA carimba `base` (furo de paridade: toda série do iOS é sem base). O documento local sobe ao servidor no 1º login (`_localSeed`, ~1749 `equitySnapshots`).
- Testes de leitura exigem que a leitura não mute snapshots (`server/tests/test_patrimonio_opcao_avulsa.py::test_historico_equity_snapshots_intacto`).

### (4) Regra decidida (determinística, sem estimativa)
**Escrita (os dois stores, mesma regra):**
- `sem_operacao` = posições, `optionPositions`, `pendingOrders` e `history` todos vazios. Nesse estado patrimônio == caixa == capital aportado: carimba `base = caixa do store` (servidor: `cash` do kv; aparelho: `doc.cash`), arredondado a 2 casas. Nunca o `patrimonio` enviado pelo cliente, nunca `initialBudget`.
- Com operação: herda a `base` do registro mais recente com `data <= data nova` (inclui o registro do mesmo dia que será substituído). Se esse registro não tem base, ou a série está vazia, grava `base: null` (desconhecida). NUNCA `initialBudget`.

**Leitura (`resolver_base_serie` / `resolverBaseSerie`, puros, mesma saída):** entrada = snapshots; filtra os que têm `patrimonio` numérico finito e `data` string, ordena por `data`. `conhecida(s)` = `base` numérica finita > 0. Varredura:
1. Série vazia → `{origem: "sem_serie", base: null, inicio: null, desde: null}`.
2. `vigente = null`, `inicio = null`. Se `conhecida(s0)` → `vigente = s0.base`, `inicio = 0` (carimbo legado no 1º registro é aceito: foi escrito quando a série começou).
3. Para i ≥ 1: se `conhecida(si)` e `vigente` é null → é âncora SÓ se `|si.base − si.patrimonio| <= 0.01` (ponto sem operação da regra nova); senão ignora (é o carimbo legado de `initialBudget` sobre série sem base — o caso do bug). Se `conhecida(si)` e `vigente` não é null e `si.base != vigente` → se `|si.base − si.patrimonio| <= 0.01` é FLUXO (aporte/retirada): `vigente = si.base`, `inicio = i`; senão → retorna `{origem: "inconsistente", base: null, ...}`. Se `si` sem base → herda `vigente` (cliente antigo), segue.
4. Fim: `vigente` não null → `{origem: "carimbada", base: vigente, inicio, desde: data de snaps[inicio]}`. `vigente` null e `snaps[0].patrimonio > 0` → `{origem: "primeiro_registro", base: snaps[0].patrimonio, inicio: 0, desde: snaps[0].data}`. Senão → `sem_serie`.
- Retorno = `(fim − base) / base × 100` onde fim = patrimônio ao vivo (front) / patrimônio calculado na rota (backend); `null` quando base null.
- Janela: só os snapshots de `inicio` em diante entram na curva e no drawdown (antes de um fluxo não há operação, logo o retorno ali é exatamente 0 — descartar não perde informação). `origem: "carimbada"` antepõe o ponto-base (`datas[0] = null`, comportamento atual); `primeiro_registro` NÃO antepõe (a base já é o 1º ponto).
- Caso real verificado contra a regra: snaps sem base (patr ~1.000.000) + snaps posteriores com base 10.000 e patr ~1.029.000 → nenhuma âncora (10.000 ≠ ~1.029.000) → `primeiro_registro` sobre ~1.000.000 → ≈ +2,9 %.
- Limitação aceita (registrar no SUMMARY): carimbo legado no 1º registro vindo de `initialBudget` divergente do caixa real é aceito; e uma coincidência exata `base == patrimonio` com operação aberta vira início de janela (retorno medido desde essa data, ainda real).

### (5) Paridade
- deviceStore ↔ serverStore: regra de carimbo e zeragem no reset entram nos DOIS (Task 2).
- front ↔ backend: um fixture JSON lido por pytest e por `.mjs` (padrão de `server/tests/fixtures/patrimonio_opcoes_paridade.json`, quick 261006-bwv).
- Textos: `skill_ref.RETORNO_ACUMULADO` ↔ `COPY[modo].retornoAcumulado`, byte a byte, travado por `web/tests/test_vocabulario_espelho.mjs` (dict `DICTS` ~121, `MODO_JS` educacional↔estudo).

### (6) Guardiões que travam o comportamento atual (reconciliar com nota datada 2026-10-06, nunca apagar asserção de negócio)
- `server/tests/test_persistence.py:354 test_base_do_retorno_nao_muda_quando_o_orcamento_e_editado` e `:381 test_base_carimbada_sobrevive_a_snapshot_do_mesmo_dia` — fixtures SEM operação: pela regra nova a edição do orçamento MOVE o caixa (aporte real). Asserção de negócio ("editar o campo durante a simulação não reescreve a base") continua válida: o fixture ganha UMA operação no histórico ENTRE o 1º snapshot e a edição, e as asserções `[10000, 10000]` / `5000` ficam inalteradas. `:369 test_recomecar_do_zero_zera_a_serie_de_patrimonio` fica intacto.
- `web/tests/test_numeros_fundamentados.mjs:18-21` — regex do código-fonte antigo (`snaps.find(...)`, `const b = carimbada ? ...`): troca por regex que prova o uso de `resolverBaseSerie` e a AUSÊNCIA de `budget` como divisor. `:24-32` (orçamento adulterado → +8 %, base 10.000) inalterados. `:34-36` ("sem série, o orçamento ainda serve de base", +20 %): REVERSÃO DELIBERADA → `retAcum === null` e `baseOrigem === "sem_serie"`, com nota (era exatamente o campo de formulário como divisor).
- `web/tests/test_finance.mjs:180-215` — fixtures sem `base` com `budget` 10.000 começando em 10.000: números (6 %, -10 %, dd 25 %, base 5000, 10 %) continuam batendo via `primeiro_registro`; `ec.curve[0] === 10000` continua (1º snapshot). `:255-278` combinações 1 e 3 ("COM base" = só budget): `datas` passa de `[null, "d1", ...]` para `["d1", ...]` (sem ponto-base em `primeiro_registro`) — atualizar o esperado com nota; manter a asserção `datas.length === curve.length`.
- `web/tests/test_c09_drawdown_alerta.mjs:88-104` e `web/tests/test_fase21_dedup_consolidacao.mjs:95-140` — fixtures com `base` no 1º registro: devem passar SEM alteração (prova de não-regressão). Se algum falhar, o erro é da implementação, não do guardião.
</context>

<interfaces>
Contratos novos (os dois lados idênticos em semântica):

Python, `server/app/store.py`:
- `def resolver_base_serie(snaps) -> dict` — puro; retorna `{"origem": "carimbada"|"primeiro_registro"|"sem_serie"|"inconsistente", "base": float|None, "inicio": int|None, "desde": "YYYY-MM-DD"|None}`; `inicio` indexa a lista JÁ filtrada e ordenada, devolvida em `"serie"` (lista) para o chamador não refiltrar.
- `def _sem_operacao(conn, user_id=None) -> bool` — positions, optionPositions, pendingOrders e history vazios.

JS, `web/src/finance.js`:
- `export function resolverBaseSerie(snapshots)` → `{ origem, base, inicio, desde, serie }` com os mesmos valores.
- `equityCurve(...)` mantém a assinatura (o parâmetro `budget` permanece por compatibilidade de chamada e deixa de ser usado como divisor — comentário datado explicando) e passa a retornar também `baseOrigem`, `baseDesde`; `retAcum` vira `null` quando a base é null; `days` = nº de snapshots da janela.

Texto, `server/app/skill_ref.py` ↔ `web/src/copy.js`:
- `RETORNO_ACUMULADO[modo][estado]`, modos `operador`/`educacional`, estados `carimbada`, `primeiro_registro`, `sem_serie`, `inconsistente`; placeholders `{pct}` e `{desde}` (DD/MM/AAAA).
- `def retorno_acumulado_txt(modo, estado, pct="", desde="") -> str` ↔ `export function retornoAcumuladoTxt(mode, estado, vals)`.
</interfaces>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Backend — resolvedor puro, regra de carimbo e fixture de paridade</name>
  <files>server/tests/fixtures/retorno_acumulado_casos.json, server/tests/test_retorno_acumulado_base.py, server/app/store.py, server/tests/test_persistence.py</files>
  <behavior>
    - Fixture (JSON, `_nota` datada 2026-10-06 citando esta quick), cada caso com `snapshots`, `fim` e `esperado {origem, base, inicio, desde, retAcum (2 casas ou null)}`:
      A "caso real": 3 snaps sem base (2026-07-01 patr 1000000, 07-02 1004000, 07-03 1010000) + 2 com base 10000 (07-04 patr 1020000, 07-05 1029000), fim 1029000 → primeiro_registro, base 1000000, desde "2026-07-01", retAcum 2.9 — e asserção explícita de que retAcum < 100.
      B "carimbada": [{08-01 10500 base 10000}, {08-02 10800 base 10000}], fim 10800 → carimbada, base 10000, retAcum 8.0.
      C "sem base derivável": [{d 5000}, {d 5200}] fim 5500 → primeiro_registro, base 5000, retAcum 10.0.
      D "indeterminável": [] → sem_serie, base null, retAcum null; e [{data, patrimonio: 0}] → sem_serie.
      E "aporte como fluxo": [{09-01 10000 base 10000}, {09-02 10000 base 10000}, {09-03 50000 base 50000}, {09-04 51000 base 50000}] fim 51000 → carimbada, base 50000, inicio 2, desde "2026-09-03", retAcum 2.0 (não 410).
      F "retirada como fluxo": [{09-01 50000 base 50000}, {09-02 10000 base 10000}, {09-03 9900 base 10000}] fim 9900 → carimbada, base 10000, inicio 1, retAcum -1.0; drawdown esperado 1.0 (não 80).
      G "inconsistente": [{09-01 10000 base 10000}, {09-02 12000 base 11000}] → inconsistente, base null, retAcum null.
      H "cliente antigo após carimbo": [{10000 base 10000}, {10500 sem base}] fim 9700 → carimbada, base 10000, retAcum -3.0.
    - Escrita: conta nova sem operação → `upsert_snapshot` carimba `base == cash` (não o patrimonio enviado). Com operação e série vazia → `base is None`. Com operação e registro anterior com base → herda. Série legada sem base + operação → novos registros com `base is None` (nunca `initialBudget`). Orçamento alterado sem operação (caixa movido) → novo registro com a base nova (fluxo). Leitura via `resolver_base_serie` não muta a lista recebida.
  </behavior>
  <action>
    Crie o fixture com os casos acima (números exatos; `retAcum` arredondado a 2 casas; drawdown só no caso F). Crie `server/tests/test_retorno_acumulado_base.py` parametrizado sobre o fixture chamando `store.resolver_base_serie` e calculando `retAcum = (fim - base)/base*100` (o teste confere origem/base/inicio/desde/retAcum), mais os testes de escrita listados em behavior usando `_fresh_db` no padrão de `test_persistence.py` (operação = `store.buy` ou `db.kv_set` de uma entrada em `history`). Rode — DEVE falhar (RED).
    Em `server/app/store.py`: adicione `resolver_base_serie(snaps)` (puro, sem I/O, sem mutar a entrada) exatamente pelo algoritmo da seção "(4) Regra decidida" do contexto, tolerância 0.01 para âncora/fluxo; adicione `_sem_operacao(conn, user_id)`; reescreva o cálculo de `base` em `upsert_snapshot` pela regra de escrita (sem operação → `round(cash, 2)` lido do kv; com operação → herda do registro mais recente com `data <= data nova`, inclusive o do mesmo dia; ausência → `None`). Substitua o comentário do bloco "BASE DA SÉRIE" por um que preserve o histórico (+9990 %, reporte de 09/08) e acrescente a nota "2026-10-06 (quick 261006-dvf): +10.193 % — carimbar `initialBudget` sobre série sem base dividia ~1.029.000 por 10.000; base só se carimba quando provada (sem operação = caixa)". Não grave `0.0` como base desconhecida (null-nunca-zero).
    Reconcilie `test_persistence.py`: em `test_base_do_retorno_nao_muda_quando_o_orcamento_e_editado` e `test_base_carimbada_sobrevive_a_snapshot_do_mesmo_dia`, insira UMA operação (entrada em `history`) entre o 1º `upsert_snapshot` e a edição do orçamento, com comentário "2026-10-06 (quick 261006-dvf): sem operação a edição move o caixa — é aporte real e reinicia a base (fluxo); a regra de negócio protegida aqui é a edição DURANTE a simulação". Asserções `[10000, 10000]` e `== 5000` permanecem idênticas. Não toque `test_recomecar_do_zero_zera_a_serie_de_patrimonio`.
  </action>
  <verify>
    <automated>cd server && .venv/bin/python -m pytest tests/test_retorno_acumulado_base.py tests/test_persistence.py tests/test_patrimonio_opcao_avulsa.py -q</automated>
  </verify>
  <done>Os 8 casos do fixture passam no pytest; caso A sai 2,9 % e < 100; testes de escrita passam; os 3 guardiões de `test_persistence.py` passam com asserções numéricas inalteradas; `grep -n "base_atual = cfg.get(\"initialBudget\")" server/app/store.py` não retorna nada.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Front — gêmeo em finance.js e paridade de carimbo/reset no deviceStore</name>
  <files>web/tests/test_retorno_acumulado_base.mjs, web/src/finance.js, web/src/persistence.js, web/tests/test_finance.mjs, web/tests/test_numeros_fundamentados.mjs</files>
  <behavior>
    - `web/tests/test_retorno_acumulado_base.mjs` lê `server/tests/fixtures/retorno_acumulado_casos.json` (mesmo caminho relativo usado por `web/tests/test_patrimonio_opcao_avulsa.mjs`) e, para cada caso, confere `resolverBaseSerie` (origem/base/inicio/desde) e `equityCurve(snapshots, 10000, fim, "2099-01-01")` → `retAcum` (2 casas ou null), `baseOrigem`, e no caso F `drawdown` 1.0. Caso A: `retAcum < 100` explícito. Passar `budget` 10000 em todos prova que o orçamento não é divisor.
    - `equityCurve` em `sem_serie`/`inconsistente`: `retAcum === null`, `curve`/`datas` paralelos, sem exceção.
    - Escrita no aparelho: `upsertSnapshot` com contexto sem operação carimba `base` = caixa; com operação herda do registro mais recente com data ≤; série sem base + operação → `base: null`. `resetPortfolio` (ramo logado e ramo local) deixa `doc.equitySnapshots` vazio.
  </behavior>
  <action>
    Escreva o `.mjs` (padrão `ok(nome, cond)` + `process.exit(fails ? 1 : 0)` dos guardiões existentes) e rode — DEVE falhar.
    Em `web/src/finance.js`: adicione `export function resolverBaseSerie(snapshots)`, espelho exato de `store.resolver_base_serie` (mesmo algoritmo, mesma tolerância 0.01, comentário "gêmeo de store.resolver_base_serie — paridade travada por test_retorno_acumulado_base.mjs/.py"). Reescreva o miolo de `equityCurve` para: resolver a base com ela; montar `plot`/`datasPlot` só com a janela `serie.slice(inicio)` (mantendo a regra atual de substituir/anexar o ponto ao vivo); antepor o ponto-base (`curve[0] = base`, `datas[0] = null`) SÓ em `origem === "carimbada"`; `retAcum = base > 0 ? ((end - base)/base)*100 : null`; drawdown sobre a mesma curva; `days` = tamanho da janela; retornar também `baseOrigem` e `baseDesde`. Mantenha a assinatura (o `budget` fica sem uso como divisor — comentário datado 2026-10-06 dizendo por quê). Atualize o cabeçalho do arquivo (linhas 18-20, "Retorno acumulado: base = ORÇAMENTO INICIAL") para a regra nova, preservando a menção histórica.
    Em `web/src/persistence.js`: `upsertSnapshot(list, snap, ctx)` recebe `ctx = { semOperacao, caixa }` e aplica a MESMA regra de escrita do servidor (comentário "espelho de store.upsert_snapshot"); `deviceStore.putSnapshot` calcula `semOperacao` de `doc.positions`, `doc.optionPositions`, `doc.pendingOrders`, `doc.history` (todos vazios) e passa `doc.cash`. Em `deviceStore.resetPortfolio`, nos DOIS ramos, `doc.equitySnapshots = []` com comentário de paridade com `store.reset_portfolio` (o servidor já zerava; o aparelho misturava duas simulações). `serverStore` não muda (o servidor carimba).
    Reconcilie guardiões com nota "2026-10-06 (quick 261006-dvf)": `test_numeros_fundamentados.mjs` linhas 18-21 → regex que prove `resolverBaseSerie(` dentro de `equityCurve` e que `Number(budget)` não aparece mais em `finance.js`; linhas 34-36 → REVERSÃO DELIBERADA para `retAcum === null && baseOrigem === "sem_serie"` (motivo: era o campo de formulário como divisor). `test_finance.mjs` combinações 1 e 3 (~255-278) → `datas` esperado sem o `null` inicial (série sem carimbo = `primeiro_registro`, sem ponto-base), mantendo `datas.length === curve.length`. Demais asserções de `test_finance.mjs` 180-215 devem passar sem alteração; se não passarem, corrija a implementação.
  </action>
  <verify>
    <automated>cd web && for f in tests/test_retorno_acumulado_base.mjs tests/test_finance.mjs tests/test_numeros_fundamentados.mjs tests/test_c09_drawdown_alerta.mjs tests/test_fase21_dedup_consolidacao.mjs tests/test_benchmark_curva.mjs tests/test_api_parity.mjs; do node "$f" >/dev/null || { echo "FALHOU $f"; exit 1; }; done; echo OK</automated>
  </verify>
  <done>Os mesmos 8 casos do fixture passam no `.mjs` com os mesmos números do pytest; `test_c09_drawdown_alerta.mjs` e `test_fase21_dedup_consolidacao.mjs` passam sem edição; `grep -c "equitySnapshots = \[\]" web/src/persistence.js` ≥ 2; `grep -n "Number(budget)" web/src/finance.js` vazio.</done>
</task>

<task type="auto">
  <name>Task 3: Texto por origem nos dois modos (skill_ref ↔ copy.js) e `pet:evolucao` pela base resolvida</name>
  <files>server/app/skill_ref.py, web/src/copy.js, web/tests/test_vocabulario_espelho.mjs, server/app/main.py, server/tests/test_retorno_acumulado_base.py</files>
  <action>
    Leia `.claude/skills/didatica-boris/SKILL.md` antes. Em `server/app/skill_ref.py`, junto de `HISTORICO`, crie `RETORNO_ACUMULADO` com exatamente estes textos:
    educacional — carimbada: "Desde o capital inicial desta simulação, o retorno acumulado é de {pct}." / primeiro_registro: "Desde {desde}, o primeiro dia registrado, o retorno acumulado é de {pct}. O capital inicial desta série não foi registrado, por isso a conta parte desse dia." / sem_serie: "Não há dados suficientes para concluir. Ainda não há nenhum dia de patrimônio registrado nesta simulação." / inconsistente: "Não há dados suficientes para concluir. A série de patrimônio registra bases diferentes sem um ajuste de capital que as explique."
    operador — carimbada: "Retorno acumulado desde o capital inicial: {pct}." / primeiro_registro: "Retorno acumulado desde {desde} (1º dia registrado): {pct}. Capital inicial da série não registrado." / sem_serie: "Não há dados suficientes para concluir. Sem dia de patrimônio registrado." / inconsistente: "Não há dados suficientes para concluir. Bases da série inconsistentes, sem ajuste de capital registrado."
    Adicione `retorno_acumulado_txt(modo, estado, pct="", desde="")` (estado desconhecido cai em `sem_serie`; interpola `{pct}`/`{desde}`). Em `web/src/copy.js` adicione `retornoAcumulado` em `COPY.estudo` e `COPY.operador` com as strings byte a byte e `export function retornoAcumuladoTxt(mode, estado, vals)` espelho (mesmo critério de modo de `historicoTxt`). Em `web/tests/test_vocabulario_espelho.mjs` inclua `RETORNO_ACUMULADO` em `DICTS`, o mapeamento para `retornoAcumulado` e a lista de chaves `["carimbada", "primeiro_registro", "sem_serie", "inconsistente"]`, com nota datada.
    Em `server/app/main.py` `_pet_resumo_evolucao` (Read com offset/limit em ~4798–4860, nunca o arquivo inteiro): troque o cálculo de `base` (hoje `cfg.initialBudget`) por `store.resolver_base_serie(store.get(..."equitySnapshots"...))`; `ret_acum = (patrimonio - base)/base*100` se `base` não for None, senão `None`; a fala do acumulado vem de `skill_ref.retorno_acumulado_txt("operador" if operador else "educacional", origem, pct=<+X,X% pt-BR com vírgula>, desde=<DD/MM/AAAA>)`, substituindo as duas frases antigas ("Desde o orçamento inicial..." e "Ainda não há orçamento inicial..."); devolva também `retornoAcumuladoOrigem` e `retornoAcumuladoDesde`. Atualize a docstring com nota datada 2026-10-06 (antes divergia de `finance.js` e usava o campo de formulário). Não adicione I/O nem escrita: a rota continua só-leitura.
    Em `server/tests/test_retorno_acumulado_base.py` adicione: (a) rota `/api/pet/resumo?tela=evolucao` (padrão `_client`/`_registrar` de `test_patrimonio_opcao_avulsa.py`) com o caso A gravado via `db.kv_set` e `initialBudget` 10000 → `retornoAcumuladoPct` < 100 e fala contendo "primeiro dia registrado" ou "1º dia registrado"; (b) série vazia → `retornoAcumuladoPct is None` e fala contendo "Não há dados suficientes para concluir."; (c) `equitySnapshots` idêntico antes/depois da chamada.
  </action>
  <verify>
    <automated>cd server && .venv/bin/python -m pytest tests/test_retorno_acumulado_base.py tests/test_skill_ref.py tests/test_ordens_pendentes_rotas.py tests/test_patrimonio_opcao_avulsa.py tests/test_pet_todas_telas.py -q && cd ../web && node tests/test_vocabulario_espelho.mjs >/dev/null && echo OK</automated>
  </verify>
  <done>Espelho byte a byte passa com o dict novo; `pet:evolucao` no caso A devolve ≈ 2,9 e não ≥ 100; série vazia devolve null + "Não há dados suficientes para concluir."; `grep -n "Desde o orçamento inicial, o retorno" server/app/main.py` vazio; guardiões de pet/pendentes seguem verdes.</done>
</task>

<task type="auto">
  <name>Task 4: Tela — CapitalCurve, Home e contexto do assistente pela base resolvida</name>
  <files>web/src/App.jsx, web/tests/test_retorno_acumulado_base.mjs</files>
  <action>
    `App.jsx` NUNCA é lido inteiro: Grep por `retVsInicio`, `RETORNO ACUMULADO`, `ACUMULADO</div>`, `aColor`, `retornoAcumuladoPct` e Read com offset/limit (~2045–2180, ~2248–2345, ~10366–10382). Importe `retornoAcumuladoTxt` de `./copy.js` (ou use o helper de modo já usado no arquivo para `copyFor`).
    CapitalCurve: `retVsInicio` passa a ser `ec.retAcum` (remove `budget` como divisor — segunda fonte do bug; comentário datado 2026-10-06); o rótulo "vs. início" vira "desde DD/MM/AAAA" quando `ec.baseOrigem === "primeiro_registro"`; quando `ec.retAcum == null`, cor neutra (`T.textMuted`) em vez de positivo/negativo. Abaixo da linha de stats (e também quando `!hasSeries` mas `baseOrigem` é `sem_serie`/`inconsistente`), renderize a frase de `retornoAcumuladoTxt(modo, ec.baseOrigem, {pct: pct(ec.retAcum), desde})` em 11px `T.textFaint` (mesmo estilo da nota "Comparação com o Ibovespa indisponível agora.") SOMENTE para `primeiro_registro`, `sem_serie` e `inconsistente` — `carimbada` não ganha linha nova. `desde` formatado DD/MM/AAAA a partir de `ec.baseDesde`.
    Home (~2342): `pct(ec.retAcum)` já rende "—" para null; troque `aColor` para neutro quando `ec.retAcum == null` (hoje `ec.retAcum || 0` pinta null como positivo) e ponha `title`/`aria-label` com a frase de `retornoAcumuladoTxt` quando `baseOrigem !== "carimbada"`.
    Contexto do assistente `case "evolucao"`: mantenha `retornoAcumuladoPct: ec.retAcum` (null quando indeterminado — nunca 0) e acrescente `retornoAcumuladoOrigem: ec.baseOrigem` e `retornoAcumuladoDesde: ec.baseDesde`, para a IA dizer quando a base é parcial/insuficiente (princípio 7).
    Acrescente ao `web/tests/test_retorno_acumulado_base.mjs` guardiões estáticos sobre `App.jsx`: não existe mais `((patr - budget) / budget)`; existe `retornoAcumuladoTxt(`; `retornoAcumuladoOrigem` presente no contexto `evolucao`; não existe `(ec.retAcum || 0)`.
  </action>
  <verify>
    <automated>cd web && node tests/test_retorno_acumulado_base.mjs >/dev/null && node tests/test_benchmark_curva.mjs >/dev/null && node tests/test_numeros_fundamentados.mjs >/dev/null && npx vite build >/dev/null && echo OK</automated>
  </verify>
  <done>`npx vite build` sem erro; guardiões estáticos novos passam; nenhum caminho de tela usa `initialBudget` como divisor do acumulado (`grep -n "patr - budget" web/src/App.jsx` vazio); estado null aparece "—" com cor neutra e a frase do motivo.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| cliente → `POST /api/snapshot` | `patrimonio` enviado pelo cliente é dado não confiável para definir a base |
| documento local do aparelho → servidor (`_localSeed`) | série legada sem base sobe ao servidor |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-dvf-01 | Tampering | `store.upsert_snapshot` | mitigate | base carimbada só a partir do `cash` do kv do servidor em estado sem operação; nunca do `patrimonio` do corpo nem de `initialBudget` |
| T-dvf-02 | Information integrity (Repudiation de número) | `equityCurve` / `_pet_resumo_evolucao` | mitigate | base resolvida pela série com regra única gêmea + fixture de paridade; sem base provável → `primeiro_registro` com data explícita ou null + "Não há dados suficientes para concluir." |
| T-dvf-03 | Tampering (histórico) | leitura de `equitySnapshots` | mitigate | resolvedores puros, sem escrita; teste antes/depois do snapshot gravado |
| T-dvf-04 | Denial of Service | resolvedor | accept | série limitada a 400 registros (cap existente); varredura O(n) |
</threat_model>

<verification>
- Executor: só os guardiões listados em cada `<verify>` + `npx vite build` (Task 4). Não roda o loop completo de `web/tests/*.mjs` nem `cap copy ios`.
- Orquestrador (fora do sandbox, uma vez ao final): `cd web && npx vite build && npx cap copy ios`, depois `bash scripts/executar.sh --testes` (rc=0).
- `git diff --stat` não mostra alteração em `qa/`, `ESTADO-*`, `CHECKOUT-*`, `server/web_dist`, `server/defaults.py`/`web/src/catalog.js`.
</verification>

<success_criteria>
- Caso real (base declarada 10.000 × capital efetivo ~1.000.000) sai ≈ +2,9 % no front e no backend; nunca +10.193 %.
- Os 8 casos do fixture dão o mesmo resultado em pytest e `.mjs`.
- Aporte/retirada pré-operação não produzem retorno nem drawdown.
- Base indeterminável → `—` + motivo nos dois modos; `retAcum`/`retornoAcumuladoPct` null.
- Nenhum snapshot gravado é reescrito pela leitura; deviceStore e servidor carimbam e zeram pela mesma regra.
- Guardiões reconciliados com nota 2026-10-06; nenhuma asserção de negócio válida apagada.
</success_criteria>

<output>
Criar `.planning/quick/261006-dvf-acumulado-de-retorno-com-base-errada-ini/261006-dvf-SUMMARY.md` ao final, com: arquivos alterados, guardiões reconciliados (antes → depois, motivo), limitações aceitas (carimbo legado no 1º registro; coincidência base==patrimônio com operação; iOS logado não envia snapshots ao servidor, então `pet:evolucao` pode divergir da tela no iPhone — dívida pré-existente, fora de escopo), e a ligação com a quick do `_localSeed` (conta nova limpa) ainda pendente.
</output>
