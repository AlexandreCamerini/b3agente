---
quick_id: 260923-ndy
slug: adicionar-botao-executar-na-aba-opcoes-analisar
date: 2026-09-23
type: quick
phase: quick-260923-ndy
plan: 01
wave: 1
depends_on: []
autonomous: true
requirements: [QUICK-260923-ndy]
origem:
  - achado ao vivo do Alex (2026-09-23) — montou uma estrutura em Opções → Analisar e não conseguiu executá-la
files_modified:
  - server/app/options_mcp_api.py
  - server/tests/test_options_mcp_proposta_execucao.py
  - server/tests/test_options_mcp_api.py
  - web/src/opcoes/ExecutarProposta.jsx
  - web/src/opcoes/SecaoAnalisar.jsx
  - web/src/opcoes/OpcoesScreen.jsx
  - web/src/App.jsx
  - web/src/copy.js
  - web/tests/test_opcoes_analisar_executar_ui.mjs
  - web/src/version.js
  - server/web_dist
  - server/app/main.py

must_haves:
  truths:
    - "Em Modo Operador, uma estrutura de 1 perna montada em Analisar mostra um botão de execução que executa pelo mesmo caminho de store da curadoria (executarCandidato)"
    - "Estrutura de 2+ pernas (trava, collar) mostra o motivo do servidor, verbatim, e nenhum botão"
    - "Em Modo Estudo não existe botão de execução — só o texto de Estudo"
    - "Erro de execução aparece verbatim (e.message); recusa de liquidez DIFÍCIL abre checkbox de consentimento e só reenvia com aceitaLiquidezDificil === true"
    - "Depois de executar com sucesso, a mesma proposta não oferece o botão de novo; montar outra estrutura zera o estado"
    - "Tamanho da ordem (contratos/qtyAcoes) e tipo de execução são decididos pelo backend, nunca calculados no front"
  artifacts:
    - path: "server/app/options_mcp_api.py"
      provides: "_execucao_da_proposta + campo `execucao` na resposta de POST /api/options/mcp/proposta"
      contains: "def _execucao_da_proposta"
    - path: "web/src/opcoes/ExecutarProposta.jsx"
      provides: "bloco de execução da estrutura montada (gate Estudo, motivo verbatim, erro verbatim, consentimento de liquidez)"
      exports: ["default", "ehRecusaLiquidezDificil"]
    - path: "web/tests/test_opcoes_analisar_executar_ui.mjs"
      provides: "guardião render (SSR) + estático do bloco de execução"
    - path: "server/tests/test_options_mcp_proposta_execucao.py"
      provides: "casos da função pura de derivação da execução"
  key_links:
    - from: "web/src/opcoes/OpcoesScreen.jsx"
      to: "ctx.A.executarCandidatoCurado"
      via: "prop onExecutarProposta passada a SecaoAnalisar"
      pattern: "onExecutarProposta=\\{\\(cand, o\\) => ctx\\.A\\.executarCandidatoCurado\\(cand, \\{ \\.\\.\\.o, origem: \"analisar\" \\}\\)\\}"
    - from: "web/src/opcoes/ExecutarProposta.jsx"
      to: "proposta.dados.execucao"
      via: "leitura do bloco derivado pelo backend"
      pattern: "execucao"
    - from: "web/src/opcoes/ExecutarProposta.jsx"
      to: "server/app/main.py (texto 'Liquidez DIFÍCIL (score')"
      via: "prefixo da recusa de liquidez"
      pattern: "Liquidez DIFÍCIL"
---

<objective>
Fechar o buraco de fluxo achado ao vivo pelo Alex: em Opções → Analisar, a
estrutura montada pelo próprio usuário ("Montar estrutura" → `montarProposta()`
→ `proposta.dados.estruturas[0]`) é só leitura. Não existe caminho de
execução. Este plano acrescenta um bloco de execução, reusando o despacho que já
existe (`executarCandidato.js` via `ctx.A.executarCandidatoCurado`), com o mesmo
padrão de estado e UI de `CuradoriaEstruturas.jsx`.

Purpose: se o dono do produto não consegue montar e efetivar uma estrutura, o
usuário final também não vai conseguir.
Output: campo `execucao` na rota de proposta (backend), componente
`ExecutarProposta.jsx` ligado em `SecaoAnalisar.jsx`, guardiões, publicação.
</objective>

<premissas_e_desvios>
Investigado nesta sessão de planejamento. O executor NÃO precisa redescobrir;
cada item corrige ou refina o briefing do orquestrador:

1. **`proposta.dados.kind` NÃO é o tipo da estrutura.** A rota
   (`options_mcp_api.py`, `proposta()`, ~linha 2324) devolve
   `"kind": dados.get("kind") or tipo`, e `tipo` é `CALL`/`PUT`/`None`
   (`TIPOS_DE_OPCAO = ("CALL", "PUT")`). `behavior` é a leitura técnica
   (trend/rsi/hv). O vocabulário real da estrutura é por PERNA:
   `estruturas[0].legs[i] = {contract, side: "buy"|"sell", kind: "CALL"|"PUT",
   quantity, strike, premium, delta, expiration?}`, e a estrutura tem
   `kind` (nome de estratégia do serviço, ex. `"trava_de_alta"`), `name`,
   `expiration`. O tipo de execução (`call_coberta`/`put_protecao`/
   `opcao_a_descoberto`) sai de **side × kind da perna única**, não do envelope.
2. **A resposta não ecoa o `lote`**, e `contratos` (rota lastreada) é número de
   CONTRATOS enquanto o lote do Analisar é em AÇÕES. Converter lote→contratos no
   front seria a "segunda versão da conta" que o repositório proíbe
   (`executarCandidato.js`: "ZERO aritmética financeira… nada de `* 100`";
   `test_opcoes_analisar_ui.mjs` §2: nenhum arquivo de `web/src/opcoes/`
   multiplica por lote; `_em_reais` fecha a conta no backend, D-24.2).
   **Decisão do planner:** a derivação vai para o BACKEND, na rota que já existe
   (sem rota nova): `_execucao_da_proposta(estruturas, lote)` devolve um bloco
   `execucao` pronto. O front só lê e repassa. Princípio 5 do CLAUDE.md.
3. **`/api/options/buy` NÃO tem 403 de Modo Estudo** (só o gate de opção a
   descoberto, `store.buy_option` → `MOTIVO_DESCOBERTO_DESLIGADO`). O briefing
   afirmava o contrário. Só `/api/options/lastreada/abrir` tem o 403. Isso é
   pré-existente (a curadoria usa o mesmo caminho para `opcao_a_descoberto`) e
   fica FORA do escopo — registrar no SUMMARY como risco, não corrigir aqui.
4. **Liquidez:** a proposta do MCP não traz faixa de liquidez (diferente do
   candidato da curadoria, que traz `item.liquidez.faixa`). O servidor recusa
   com 400 cujo texto começa com `Liquidez DIFÍCIL (score N/100) — …`
   (`main.py`, `options_lastreada_abrir`). O consentimento nasce, portanto,
   DEPOIS dessa recusa: o texto do servidor é o aviso lido, verbatim, e só então
   o checkbox aparece. Recusa `Liquidez SEM MERCADO` é terminal (sem checkbox).
5. **Risco de produto a expor ao Alex (não resolver):** a fixture real do
   serviço (`server/tests/fixtures/mcp_evaluate_petr4.json`, e `_setup` em
   `test_options_mcp_api.py`) é trava de alta de **2 pernas**. Se o serviço
   propõe majoritariamente travas para uma tese direcional, a maior parte das
   estruturas montadas cairá no ramo "não executável aqui" — o achado do Alex
   fica só parcialmente fechado. Executar trava exige rota multi-perna nova no
   motor (`store.py` executa uma perna por chamada) — decisão de produto, fora
   desta quick.
6. **Mapa perna→tipo (discrição do planner, documentar no código):**
   sell+CALL → `call_coberta`; buy+PUT → `put_protecao` (lastro obrigatório é o
   padrão da conta, `MOTIVO_DESCOBERTO_DESLIGADO`; sem posição no ativo o
   servidor recusa verbatim); buy+CALL → `opcao_a_descoberto` (mesma escolha da
   curadoria, `opcoes_curadoria.py` ~linha 480: "a descoberto" = compra de call a
   seco); sell+PUT → não executável (não há rota de venda de put no simulador).
7. **Botão de execução NÃO usa preenchimento de accent.** A Fase 35 (D-04)
   trava exatamente 3 CTAs preenchidos em Opções, e `test_opcoes_jornada_ui.mjs`
   §11 restringe `BOTAO_PRIMARIO` a 3 arquivos. O botão novo é contornado
   (borda `T.accent`, texto `T.accent`, fundo transparente), mesmo desenho do
   botão "narrar" de `CuradoriaEstruturas.jsx`.
8. **Pós-sucesso sem nova chamada paga:** em vez de chamar `montarProposta` de
   novo (custa cap: 1 + 1 do valorHoje), o estado de execução é amarrado à
   IDENTIDADE de `proposta.dados`: executada → mensagem de sucesso, sem botão;
   uma nova montagem produz outro objeto `dados` e o bloco volta ao estado
   inicial. É o "limpar o resultado" que o briefing admite, sem `useEffect`.
</premissas_e_desvios>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@./CLAUDE.md
@web/src/opcoes/SecaoAnalisar.jsx
@web/src/opcoes/CuradoriaEstruturas.jsx
@web/src/opcoes/executarCandidato.js

<interfaces>
Extraído do código nesta sessão. Use direto; não precisa explorar.

server/app/options_mcp_api.py, rota `proposta()` (~2323-2420): dentro do
`with _cap_check(uid, 1) as cap:`, já existem `estruturas` (lista de dicts do
serviço) e `lote` (int validado por `_lote`, ou None). O dict de retorno tem
`ticker`, `direction`, `kind`, `behavior`, `estruturas`, `motivo`, `nota`,
`emReais`, `razaoGanhoPerda`, `dominio`, `segmentos`, `valorHoje`, `frescor`,
`cap`. Acrescentar `"execucao": _execucao_da_proposta(estruturas, lote)`.

web/src/opcoes/executarCandidato.js:
- `corpoDoCandidato(cand, { aceitaLiquidezDificil })` — tipos:
  `call_coberta`/`put_protecao` exigem `ticker, contractSymbol, expiration,
  contratos` → `optionsAbrirLastreada`; `opcao_a_descoberto` exige `ticker,
  contractSymbol, expiration, qtyAcoes` → `optionsBuy` (corpo `qty`).
- `executarCandidato(cand, { store, aceitaLiquidezDificil })`.

web/src/App.jsx ~8423: `executarCandidatoCurado: async (cand, opts) => { const s
= await executarCandidato(cand, { store, aceitaLiquidezDificil: opts &&
opts.aceitaLiquidezDificil }); setData(s); track("trade_simulated", { side:
"abrir", ticker: cand.ticker, instrument: "curadoria_" + cand.tipo });
flash(cp.curadoriaExecutada); return s; }` — erro é RELANÇADO (quem chama
grava `e.message`).

web/src/opcoes/OpcoesScreen.jsx: `SecaoAnalisar` é renderizado dentro de
`OpcoesScreen({ ctx })` (~linha 945, ramo `abaWorkspace === "analisar"`);
`ctx` está no escopo. Operador = `!!(ctx && ctx.operador)`.
GUARDIÃO: `test_opcoes_consolidacao_ui.mjs:197` conta EXATAMENTE 1 ocorrência
de `onExecutar={(cand, o) => ctx.A.executarCandidatoCurado(cand, o)}` somando
OpcoesScreen + SecaoDescobrir — o novo prop NÃO pode ter essa forma literal.

Copy existente, dois modos (`web/src/copy.js` ~801 e ~1411):
`curadoriaExecutarCta`, `curadoriaExecutando`, `curadoriaExecutada`,
`curadoriaLiquidezConsentir`, `curadoriaEstudoNaoExecuta`.

Erros HTTP 4xx com `detail` string chegam ao front como `e.message` = o texto
do servidor, sem sufixo (`api.js` `enrichErrorMessage`, sufixo só em 5xx).

Loader para importar `.jsx` em teste Node: `web/tests/_jsx_loader.mjs`
(`register("./_jsx_loader.mjs", import.meta.url)`; exemplo em
`web/tests/test_explicacao_payoff.mjs`). `react-dom/server` existe em
`web/node_modules`.
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Backend — bloco `execucao` derivado na rota de proposta</name>
  <files>server/app/options_mcp_api.py, server/tests/test_options_mcp_proposta_execucao.py, server/tests/test_options_mcp_api.py</files>
  <behavior>
    Função pura `_execucao_da_proposta(estruturas, lote)`:
    - `[]` → `None` (nada montado; a UI já mostra `motivo`).
    - 2+ estruturas → `{"executavel": False, "motivo": MOTIVO_EXEC_VARIAS}`.
    - estrutura com 2+ pernas (fixture `_setup`, trava de alta) → `{"executavel": False, "motivo": MOTIVO_EXEC_MULTIPERNA}`.
    - 1 perna sell+CALL, lote 200 → `{"executavel": True, "tipo": "call_coberta", "contractSymbol": "PETRI400", "expiration": "2026-09-19", "contratos": 2, "qtyAcoes": 200}` (chaves exatamente estas).
    - 1 perna buy+PUT, lote 100 → tipo `put_protecao`, contratos 1, qtyAcoes 100.
    - 1 perna buy+CALL, lote 100 → tipo `opcao_a_descoberto`, contratos 1, qtyAcoes 100.
    - 1 perna sell+PUT → `executavel False`, `MOTIVO_EXEC_VENDA_PUT`.
    - side/kind com caixa diferente (`"SELL"`, `"call"`) → normaliza, mesmo resultado.
    - `expiration` ausente na estrutura mas presente na perna → usa a da perna.
    - sem `contract` ou sem vencimento algum → `MOTIVO_EXEC_INCOMPLETA`.
    - `quantity` diferente de 1 (inclusive booleano `True`) → `MOTIVO_EXEC_PROPORCAO`.
    - `lote` None → `MOTIVO_EXEC_SEM_LOTE`; lote 150 → `MOTIVO_EXEC_LOTE_CENTENA` (nunca arredonda).
    - Rota: `POST /api/options/mcp/proposta` com `com_tese` de 1 perna sell+CALL e `lote: 200` devolve `corpo["execucao"]["tipo"] == "call_coberta"` e `contratos == 2`; com a fixture padrão de 2 pernas devolve `executavel False` com `MOTIVO_EXEC_MULTIPERNA`.
  </behavior>
  <action>
RED primeiro: criar `server/tests/test_options_mcp_proposta_execucao.py`
importando `_execucao_da_proposta` e as constantes `MOTIVO_EXEC_*` de
`app.options_mcp_api` (confira o import-path usado no topo de
`server/tests/test_options_mcp_api.py`), cobrindo todos os casos de
`<behavior>` com fixtures literais de perna no formato do serviço (`contract`,
`side`, `kind`, `quantity`, `strike`, `premium`, `delta`). Acrescentar em
`test_options_mcp_api.py`, junto de `test_proposta_com_lote_converte_a_estrutura_unica`
(~linha 397), um teste de rota que usa `_espiao(monkeypatch, _roteador(com_tese=...))`
com uma proposta de 1 perna (copie a forma de `_proposta()`, trocando `legs`
por uma perna só sell/CALL `PETRI400`) e asserte o bloco `execucao`; e uma
asserção extra no teste existente de 2 pernas (ou um teste novo) de que
`execucao["executavel"] is False`. Rodar e ver falhar. Commit `test(quick-260923-ndy): ...`.

GREEN: em `options_mcp_api.py`, perto de `_em_reais`/`_vezes_lote` (~1274-1320),
declarar as constantes de motivo (texto PT-BR, fonte única, mostrado verbatim
pela UI) e a função pura. Textos:
- `MOTIVO_EXEC_VARIAS`: "O serviço devolveu mais de uma estrutura. Escolha um vencimento e monte de novo para executar uma só."
- `MOTIVO_EXEC_MULTIPERNA`: "Estruturas de mais de uma perna (como travas e collar) ainda não são executáveis a partir da análise manual. O collar pode ser executado pelo bloco \"As 4 melhores oportunidades de opções\"."
- `MOTIVO_EXEC_VENDA_PUT`: "Venda de put não tem caminho de execução no simulador — esta estrutura fica só como leitura."
- `MOTIVO_EXEC_INCOMPLETA`: "O serviço não informou o contrato ou o vencimento desta perna — nada é executado sem eles."
- `MOTIVO_EXEC_PROPORCAO`: "A perna veio com proporção diferente de 1 contrato por lote — a execução manual só cobre a proporção 1:1."
- `MOTIVO_EXEC_SEM_LOTE`: "Informe o lote em ações e monte a estrutura de novo para executar."
- `MOTIVO_EXEC_LOTE_CENTENA`: "Para executar, o lote precisa ser múltiplo de 100 ações (1 contrato = 100 ações). Ajuste o lote e monte de novo."
Ordem das checagens: vazio → várias → pernas≠1 → incompleta → proporção → lado/tipo (sell+PUT e combinação desconhecida → não executável; desconhecida usa `MOTIVO_EXEC_INCOMPLETA`) → lote None → lote não múltiplo de 100. `contratos = lote // 100` e `qtyAcoes = lote` SÓ depois de provar `lote % 100 == 0` — por isso o lote centena é exigido: o que executa tem de ser o mesmo tamanho que `emReais` mostrou em reais (`buy_option` normaliza para centena e divergiria em silêncio). Comentário no código explicando: por que a derivação está aqui e não no front (princípio 5, D-24.2, premissa 2 deste plano), o mapa side×kind→tipo (premissa 6) e por que sell+PUT não executa. `quantity` booleano é recusado (mesma disciplina de `_lote`). Acrescentar `"execucao": _execucao_da_proposta(estruturas, lote)` ao dict de retorno de `proposta()` com comentário curto. NÃO tocar `/possibilidades` nem outras rotas. Commit `feat(quick-260923-ndy): ...`.
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2/server &amp;&amp; .venv/bin/python -m pytest tests/test_options_mcp_proposta_execucao.py tests/test_options_mcp_api.py -q</automated>
  </verify>
  <done>Todos os casos de `<behavior>` passam; nenhum teste pré-existente de `test_options_mcp_api.py` regrediu; a rota devolve `execucao` e nenhuma outra chave mudou.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Front — ExecutarProposta.jsx ligado em SecaoAnalisar + guardião</name>
  <files>web/src/opcoes/ExecutarProposta.jsx, web/src/opcoes/SecaoAnalisar.jsx, web/src/opcoes/OpcoesScreen.jsx, web/src/App.jsx, web/src/copy.js, web/tests/test_opcoes_analisar_executar_ui.mjs</files>
  <behavior>
    Render (SSR via `react-dom/server` `renderToStaticMarkup` + `_jsx_loader.mjs`, `React.createElement`, sem JSX no .mjs), `cp = COPY.operador`/`COPY.estudo`:
    - `dados` sem `execucao` → markup vazio.
    - `operador=false`, execucao executável → contém `cp.curadoriaEstudoNaoExecuta`, NÃO contém `cp.curadoriaExecutarCta`, nenhum `<button`.
    - `operador=true`, execucao executável → contém `cp.curadoriaExecutarCta` e `cp.opcoesExecucaoSimulada`.
    - `operador=true`, `{executavel:false, motivo:"MOTIVO-X"}` → contém "MOTIVO-X" verbatim, nenhum `<button`.
    - `ehRecusaLiquidezDificil("Liquidez DIFÍCIL (score 30/100) — ...")` → true; `("Liquidez SEM MERCADO ...")` → false; `(null)`/`("")` → false.
    Estático (fonte sem comentário):
    - `server/app/main.py` contém `Liquidez DIFÍCIL (score` (acoplamento de texto declarado, com sanidade).
    - `ExecutarProposta.jsx`: erro renderizado como expressão nua (`{<x>.erro}`), sem `+` concatenado ao erro; `(e && e.message) || String(e)` presente; `aceitaLiquidezDificil:` construído com `=== true`; sem `BOTAO_PRIMARIO`, sem `#fff`, sem `* 100`/`/ 100`/`* lote`; sem import de `../api`/`persistence`/`store`; sem `useEffect`.
    - `SecaoAnalisar.jsx` renderiza `<ExecutarProposta` dentro do ramo `proposta.dados ?` (depois de `<Pernas`).
    - `OpcoesScreen.jsx` passa `operador=` e `onExecutarProposta=` a `<SecaoAnalisar`.
    - Cada regex de defeito tem asserção de sanidade (pega o padrão quando ele existe).
  </behavior>
  <action>
RED: criar `web/tests/test_opcoes_analisar_executar_ui.mjs` no padrão da casa (contador `fails` + helper `ok`, `process.exit(fails ? 1 : 0)` como os irmãos; `register("./_jsx_loader.mjs", import.meta.url)` e `await import("../src/opcoes/ExecutarProposta.jsx")`; strip de comentário como `semComentario` dos irmãos). Cobrir todo o `<behavior>`. Rodar: falha (arquivo não existe). Commit `test(quick-260923-ndy): ...`.

GREEN — `web/src/opcoes/ExecutarProposta.jsx` (componente novo, props `{ dados, operador, onExecutar, cp }`):
- Cabeçalho de comentário: por que existe (achado do Alex), que espelha o padrão de `CuradoriaEstruturas.jsx` (busy/erro/ok, erro verbatim — princípio 4, T-J5L-03; consentimento por identidade — T-J5L-04), que NÃO faz conta (tamanho/tipo vêm de `dados.execucao`, backend, premissa 2), por que o botão é contornado e não preenchido (Fase 35 D-04, premissa 7), e por que o estado se amarra à identidade de `dados` (premissa 8).
- Tokens: `VARKEY`/`TOKENS`/`T` como os irmãos; TODO `T.<nome>` usado precisa estar no array (guardião §10 de `test_opcoes_jornada_ui.mjs`).
- `export const PREFIXO_LIQUIDEZ_DIFICIL = "Liquidez DIFÍCIL"` e `export function ehRecusaLiquidezDificil(msg)` (string não vazia que começa com o prefixo).
- `const ex = dados && dados.execucao;` sem `ex` → `null`.
- `!operador` → só `cp.curadoriaEstudoNaoExecuta` (itálico, `T.textMuted`), sem botão (mesmo gate de `CuradoriaEstruturas.jsx:229-236`).
- `ex.executavel !== true` → `ex.motivo` verbatim num `Aviso`-like (ou `Aviso` de `uiOpcoes.jsx`), sem botão; sem `motivo`, não renderiza nada (nunca compõe causa).
- Executável: estado único `useState({ ref: null, busy: false, erro: null, ok: false, aceite: false })`; `const atual = st.ref === dados ? st : INICIAL` (constante de módulo). Candidato montado SÓ com campos lidos: `{ tipo: ex.tipo, ticker: dados.ticker, contractSymbol: ex.contractSymbol, expiration: ex.expiration, contratos: ex.contratos, qtyAcoes: ex.qtyAcoes }`. Handler: grava `{ ref: dados, busy: true, erro: null, ok: false, aceite: atual.aceite }`; `await onExecutar(cand, { aceitaLiquidezDificil: atual.aceite === true })`; sucesso → `ok: true`; catch → `erro: (e && e.message) || String(e)` e `aceite: false`. Sem reenvio automático.
- Render executável: linha `cp.opcoesExecucaoSimulada`; se `atual.ok` → `cp.curadoriaExecutada` (cor `T.textMuted`, NÃO `T.positive` — D-06 da Fase 35: positive/negative são direção financeira) e NENHUM botão; senão, se `ehRecusaLiquidezDificil(atual.erro)` → checkbox cujo rótulo é `{atual.erro} {cp.curadoriaLiquidezConsentir}` (o texto do servidor É o aviso lido) e o onChange grava `aceite` mantendo `ref: dados`; senão, se `atual.erro` → caixa de erro com `{atual.erro}` nu (cor `T.warn`, adicionar ao TOKENS); botão `type="button"`, `minHeight: "44px"`, largura 100%, borda `1px solid T.accent`, fundo transparente, texto `T.accent`, rótulo `atual.busy ? cp.curadoriaExecutando : cp.curadoriaExecutarCta`, `disabled` quando `atual.busy` ou (`ehRecusaLiquidezDificil(atual.erro)` e `!atual.aceite`), desabilitado continua visível (opacity 0.55, nunca `display: none`).

`web/src/copy.js`: nova chave `opcoesExecucaoSimulada` nos DOIS modos, perto das `opcoes*` do Analisar. Estudo: "Execução simulada com dinheiro virtual — nenhuma ordem vai para corretora ou bolsa." Operador: "Execução simulada, saldo virtual — nenhuma ordem sai do app." Sem linguagem de ganho (princípio 8).

`web/src/opcoes/SecaoAnalisar.jsx`: import de `ExecutarProposta`; novas props `operador` e `onExecutarProposta` na assinatura; renderizar `<ExecutarProposta dados={proposta.dados} operador={operador} onExecutar={onExecutarProposta} cp={cp} />` logo depois de `<Pernas …/>` (~linha 407), dentro do mesmo fragmento. Atualizar o comentário de cabeçalho (a frase "zero funcionalidade nova (D-03)" era da extração da Fase 33 — acrescentar nota datada 2026-09-23 desta quick, sem apagar a original; histórico não se reescreve). NÃO declarar `useState` de ticker/tese/vencimento/lote.

`web/src/opcoes/OpcoesScreen.jsx` (~linha 945, `<SecaoAnalisar`): acrescentar `operador={!!(ctx && ctx.operador)}` e `onExecutarProposta={(cand, o) => ctx.A.executarCandidatoCurado(cand, { ...o, origem: "analisar" })}` — forma diferente da literal travada em `test_opcoes_consolidacao_ui.mjs:197` (a contagem de 1 continua valendo).

`web/src/App.jsx` (~8426, `executarCandidatoCurado`): só o `track` muda para `instrument: (opts && opts.origem === "analisar" ? "analisar_" : "curadoria_") + cand.tipo`, com comentário de uma linha. `origem` não entra no corpo (executarCandidato só lê `aceitaLiquidezDificil`). Nada mais em App.jsx.

Rodar o guardião novo (passa), depois prova negativa: remover temporariamente o gate `!operador` em `ExecutarProposta.jsx` → o guardião FALHA nomeando o caso Estudo; reverter → passa. Registrar no SUMMARY. `npx vite build` em `web/`. Commit `feat(quick-260923-ndy): ...`.
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2 &amp;&amp; node web/tests/test_opcoes_analisar_executar_ui.mjs &amp;&amp; node web/tests/test_opcoes_consolidacao_ui.mjs &amp;&amp; node web/tests/test_opcoes_jornada_ui.mjs &amp;&amp; node web/tests/test_opcoes_analisar_ui.mjs &amp;&amp; node web/tests/test_opcoes_vigias_ui.mjs &amp;&amp; node web/tests/test_curadoria_ui.mjs &amp;&amp; (cd web &amp;&amp; npx vite build) &amp;&amp; bash scripts/executar.sh --testes</automated>
  </verify>
  <done>Guardião novo verde e provado não-vácuo; guardiões de opções pré-existentes verdes sem afrouxamento; `npx vite build` limpo; suíte canônica verde (mesma baseline: falhas conhecidas só de TLS-sandbox/`test_ios_assets.mjs`, rodar fora do sandbox se necessário).</done>
</task>

<task type="auto">
  <name>Task 3: Bump, publicação e push nas duas branches</name>
  <files>web/src/version.js, server/web_dist, server/app/main.py</files>
  <action>
Regra permanente do repositório: quick que toca `web/src/` sem publicação fica
testada e invisível em produção; aqui também há mudança de backend. Mesma
sequência das quicks `260915-j5l`/`260916-cod`/`260916-g6p`.

1. `git fetch origin main` e conferir que `origin/main` é ancestral do HEAD (usar `origin/main`, nunca a `main` local). `web/package-lock.json` modificado no working tree é fora de escopo — não commitar; mover de lado antes de qualquer script que faça `git add -A` e restaurar depois.
2. `bash scripts/bump.sh`.
3. `bash scripts/publicar-web.sh` — FORA do sandbox (o `npm ci` precisa do registry; sandbox derruba TLS/EPERM). Nunca editar `server/web_dist` à mão.
4. Reescrever à mão o comentário de `SERVER_BUILD_ID` em `server/app/main.py` descrevendo ESTA entrega (campo `execucao` na proposta, bloco de execução no Analisar, limites: só 1 perna, travas/collar não executam daqui, lote centena), preservando o texto anterior inteiro como `HISTORICO` na mesma linha.
5. `bash scripts/executar.sh --testes` depois do bump — exit 0 (fora do sandbox se as falhas de TLS aparecerem).
6. Commit dos artefatos; `git status --porcelain` limpo ao final (exceto o `web/package-lock.json` pré-existente).
7. Push em `v2/interacao-estrutural` E `git push origin HEAD:main` (o Railway só observa `main`).
8. Confirmar por HTTP que `https://boris.semente.dev/api/health` devolve o carimbo novo (aguardar o redeploy; 502 transitório na troca de container é esperado).
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2 &amp;&amp; git fetch origin main &amp;&amp; test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" &amp;&amp; curl -fsS https://boris.semente.dev/api/health</automated>
  </verify>
  <done>`HEAD == origin/main`; `/api/health` carimba o build gerado pelo `bump.sh`, registrado no SUMMARY; `server/web_dist` regenerado pelo script.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| serviço MCP → backend | estrutura/pernas vêm de serviço externo; forma não garantida |
| cliente → rotas de execução | corpo montado no front; o servidor re-busca a cadeia e revalida |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-NDY-01 | Tampering | `_execucao_da_proposta` | mitigate | perna validada campo a campo (contract, side, kind, quantity === 1 não-booleano, vencimento); qualquer forma inesperada vira `executavel: False` com motivo, nunca corpo parcial |
| T-NDY-02 | Tampering | corpo de execução no front | accept | as rotas `lastreada/abrir` e `options/buy` já re-buscam a cadeia, re-leem prêmio e revalidam lastro/caixa/liquidez no servidor; o front não dita preço |
| T-NDY-03 | Elevation | execução em Modo Estudo | mitigate | UI sem botão quando `!operador` (guardião SSR); `lastreada/abrir` tem 403. RISCO DECLARADO: `/api/options/buy` não tem 403 de Estudo (pré-existente, premissa 3) — registrar no SUMMARY para decisão, não corrigir aqui |
| T-NDY-04 | Repudiation/Integrity | consentimento de liquidez | mitigate | checkbox só aparece após recusa `Liquidez DIFÍCIL` do servidor (texto verbatim como aviso); `aceitaLiquidezDificil` só por `=== true`; servidor checa por identidade (`is not True`) |
| T-NDY-05 | Information integrity | mensagens | mitigate | erro e motivo exibidos verbatim; nenhum texto de causa composto no front (princípio 4) |
| T-NDY-06 | Integrity | tamanho da ordem | mitigate | contratos/qtyAcoes derivados no backend só com lote múltiplo de 100 — execução idêntica ao que `emReais` mostrou; zero aritmética no front (guardião) |
</threat_model>

<verification>
- `bash scripts/executar.sh --testes` — exit 0 nas duas suítes, contagem ≥ baseline (+ testes novos).
- `npx vite build` em `web/` verde.
- Guardião novo com defeito injetado (gate de Estudo removido): FALHA; revertido: passa.
- `test_opcoes_consolidacao_ui.mjs`, `test_opcoes_jornada_ui.mjs`, `test_opcoes_analisar_ui.mjs`, `test_opcoes_vigias_ui.mjs`, `test_curadoria_ui.mjs` verdes sem alteração.
- Produção: `/api/health` com o carimbo novo.
</verification>

<success_criteria>
- Em Modo Operador, estrutura de 1 perna montada em Analisar tem botão de execução que chama `executarCandidato` via `ctx.A.executarCandidatoCurado` e, em sucesso, atualiza a carteira (setData) e troca o botão pela mensagem de executada.
- Estrutura de 2+ pernas / venda de put / lote fora de centena mostram o motivo do backend verbatim, sem botão.
- Modo Estudo: nenhum botão.
- Nenhuma conta de tamanho de ordem no front.
- Publicado em produção.
</success_criteria>

<output>
Criar `.planning/quick/260923-ndy-adicionar-botao-executar-na-aba-opcoes-a/260923-ndy-SUMMARY.md`. Declarar obrigatoriamente, sem resolver:
1. Risco já existente e correto: a estrutura do MCP pode não coincidir com a cadeia Yahoo no clique; a rota de execução re-busca e pode recusar (contrato sumido, liquidez) com mensagem clara — não é bug novo.
2. Premissa 5: se o serviço propõe sobretudo travas de 2 pernas, a maioria das montagens cai em "não executável aqui". Executar trava exige rota multi-perna — decisão de produto para o Alex.
3. Premissa 3: `/api/options/buy` sem 403 de Modo Estudo (pré-existente).
4. Premissa 6: buy+PUT vai para `put_protecao` (exige lastro); put a seco com flag de descoberto ligado não é oferecido por este caminho.
5. iOS: o app nativo carrega bundle local — o botão só chega ao iPhone num build novo de TestFlight; o campo `execucao` do backend já vale.
6. Não chamar mutadores de estado do `gsd-sdk`; STATE.md, se atualizado, à mão.
</output>
