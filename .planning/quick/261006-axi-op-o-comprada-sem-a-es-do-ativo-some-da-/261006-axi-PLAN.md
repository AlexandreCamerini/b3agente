---
phase: quick-261006-axi
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - web/src/estruturaCard.js
  - web/tests/test_estrutura_card_logica.mjs
  - server/tests/test_opcoes_anatomia_rota.py
  - web/src/opcoes/OpcoesScreen.jsx
  - web/src/opcoes/HubOpcoes.jsx
  - server/app/skill_ref.py
  - web/src/copy.js
  - web/tests/test_opcoes_fluxo_render.mjs
  - web/tests/test_opcoes_universo_carteira.mjs
  - web/tests/test_opcoes_hub_workspace_ui.mjs
  - web/src/App.jsx
  - web/tests/test_carteira_perna_avulsa.mjs
autonomous: true
requirements: [QUICK-261006-axi]

must_haves:
  truths:
    - "Uma opção aberta cujo ativo-objeto não está em `positions` (ex.: PUT VALEV731W2 sem VALE3) aparece na Carteira como card do ativo marcado 'sem ações', com a estrutura lida do motor e o botão Encerrar"
    - "O mesmo ativo aparece como card no hub de Opções, com subtítulo 'sem ações' (sem número inventado: nada de '0 ações · 0 livres'), e abrir o card leva ao nível objetivo com PernasAbertas/anatomia funcionando"
    - "O deep-link 'Encerrar opção' da Carteira (goOpcoes com abrirTicker) abre o ativo só-com-opção no hub, em vez de ser descartado pela validação de universo"
    - "GET /api/options/anatomia/{ticker} numa conta sem ações do ativo devolve estado ok, anatomia com acoes == None (nunca 0) e nenhum marcador precoMedio; POST /api/options/sell encerra a perna avulsa"
    - "Nenhum preço, nome ou quantidade de ações é inventado para o ativo sem ações: nome vem só do catálogo/cotação (senão nada), preço médio/stop/alvo ficam null"
  artifacts:
    - path: "web/src/estruturaCard.js"
      provides: "tickersComPernas (inclui ativo só com perna), tickersSoComPernas, universoOpcoes"
      exports: ["tickersComPernas", "tickersSoComPernas", "universoOpcoes"]
    - path: "web/tests/test_carteira_perna_avulsa.mjs"
      provides: "guardião do card de perna avulsa na Carteira"
    - path: "server/tests/test_opcoes_anatomia_rota.py"
      provides: "teste da anatomia e do sell com conta sem ações do ativo"
      contains: "def test_perna_avulsa_sem_acoes"
  key_links:
    - from: "web/src/opcoes/OpcoesScreen.jsx"
      to: "universoOpcoes"
      via: "carteiraHub e estadoInicialOpcoes derivados do universo (carteira + pernas avulsas)"
      pattern: "universoOpcoes\\("
    - from: "web/src/App.jsx CarteiraScreen"
      to: "tickersSoComPernas"
      via: "renderiza CartaoPernaAvulsa para cada ticker só com perna"
      pattern: "tickersSoComPernas\\("
    - from: "web/src/opcoes/HubOpcoes.jsx CardAtivo"
      to: "card_subtitulo_sem_acoes"
      via: "pos.semAcoes troca o subtítulo"
      pattern: "card_subtitulo_sem_acoes"
---

<objective>
Corrigir o sumiço de opção comprada cujo ativo-objeto não está na carteira de ações (caso real do Alex: PUT VALEV731W2, 100 un, R$ 0,92, aberta em 06/10/2026 07:46, sem VALE3). Causa confirmada: `tickersComPernas` (web/src/estruturaCard.js:10) parte de `positions`, e o hub de Opções monta cards só de `ctx.data.positions` (`carteira`/`carteiraHub` em OpcoesScreen.jsx). Ticker que só tem perna cai fora das duas telas.

Purpose: posição real do usuário não pode ficar invisível (princípio 9, estados completos; princípio 3, o usuário precisa ver e encerrar o que tem). Nada de cálculo novo no front: a estrutura e a anatomia já saem do backend com `posicao` ausente.
Output: helpers puros novos, card "sem ações" na Carteira, card "sem ações" no hub, testes (lógica, SSR do hub, guardião da Carteira, pytest da rota de anatomia + sell).
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@./CLAUDE.md
@.claude/skills/didatica-boris/SKILL.md
@web/src/estruturaCard.js

Regras do repositório que valem aqui (CLAUDE.md):
- App.jsx NUNCA é lido inteiro: Grep + Read com offset/limit.
- Textos novos: chave nova em `server/app/skill_ref.py` E `web/src/copy.js`, nos DOIS modos, byte a byte (guardiões de espelho travam).
- `null`/travessão, nunca 0 como "desconhecido". Cálculo só no backend/motor.
- Guardião não se apaga: asserção que muda de expectativa recebe nota datada "(reconciliado 2026-10-06, quick 261006-axi: ...)" e a asserção antiga é reescrita, não removida.
- Nenhum método novo em store (paridade deviceStore↔serverStore fica intacta: este plano NÃO toca `web/src/persistence.js`).

<interfaces>
Fatos lidos no código (o executor não precisa redescobrir):

web/src/estruturaCard.js:10 (hoje)
  export function tickersComPernas(positions, optionPositions) -> string[]
  // positions.filter(p => comPernas.has(p.t)).map(p => p.t)  -- descarta ticker só com perna
  export function assinaturaEstrutura(t, positions, optionPositions, operador)  // já trata p ausente ("-:-")
  export function estadoLeitura(temPernas, entrada) -> "atual"|"carregando"|"falha"|"estruturada"

Consumidores de tickersComPernas (App.jsx):
  ~4404 useEstruturasPosicao: const tickers = tickersComPernas(data.positions, data.optionPositions);  // dispara store.optionsProposta(t, true) por ticker
  ~5563 CarteiraScreen: const comPernas = new Set(tickersComPernas(...));
  ~5651 `{data.positions.length === 0 && (` -> estado "Portfólio vazio"
  ~5659 `{data.positions.map((p) => { ... <CartaoPosicao .../> })}` -> único render de cards
  ~4631 function CardPosicaoEstruturada({ p, leitura, cp, operador, ctx, data, onAtualizar }) -- de `p` usa SÓ `p.t`; exige leitura.estrutura != null; botão Encerrar chama ctx.goOpcoes("oportunidades", { abrirTicker: p.t })
  helpers já importados de estruturaCard.js em App.jsx:10 (inclui nomeEmpresaCard, estadoLeitura, tickersComPernas)
  BotaoAtualizarEstrutura({ leitura, onClick, cp }), estruturaCardTxt(modo, "lendo"|"indisponivel"), cartaoPosicaoTxt(modo, chave, vals)

web/src/opcoes/OpcoesScreen.jsx:
  325  const carteira = ((ctx && ctx.data && ctx.data.positions) || []).filter((p) => p && p.t);   // regex travada por test_opcoes_universo_carteira -- NÃO mudar
  348  useState(() => estadoInicialOpcoes({ abas, abaInicial, abrirTicker, memoria, carteira }))     // abrirTickerOpcoes/tickerInicialOpcoes validam ticker contra `carteira` (p.t)
  472  useOpcoesPropostas(store, carteira.map((p) => p.t))   // fonte de opcoesPorTicker (fallback de estrutura do PernasAbertas)
  710  const tickersEmCarteira = carteira.map((p) => p.t);  // useTecnicoCarteira (custo zero) no hub
  740  const carteiraHub = carteira.map((p) => ({ ...p, ticker: p.t }));   // regex /carteira=\{carteiraHub\}/ travada
  741  const optionPositionsAll = (ctx && ctx.data && ctx.data.optionPositions) || [];   // hoje definido DEPOIS de 472
  881  PropostaDoAtivo posicao={carteira.find((p) => p.t === nav.ticker) || null}   // fica em `carteira`: avulsa não tem lastro
  949  onConcluido: estadoInicialOpcoes({ abas: ABAS_OPCOES, carteira })
  985  {carteira.length > 0 ? seletor : null}   // seletor do Montar fica na CARTEIRA (montar exige lastro) -- não mudar

web/src/opcoes/HubOpcoes.jsx CardAtivo:
  const sub = opcoesEscadaTxt(mode, "card_subtitulo", { qtd: vz(pos.qty), livres: vz(qtyLivre(pos)) }) || "";
  // "{qtd} ações · {livres} livres para lastro" -- com qty 0 viraria "0 ações · 0 livres": proibido

server/app/main.py:
  3159 async def _estrutura_do_ativo(t, option_positions, posicao, modo, ...) -> (estrutura, spot, source); posicao None já suportado
  4028 GET /api/options/anatomia/{ticker}: posicao = next(... p.get("t") == t, None); chama _estrutura_do_ativo + anatomia_perna.ler_anatomia(option_positions, t, posicao, spot, estrutura, hoje, modo, excluir=...)
  3078 POST /api/options/sell {contractSymbol, qty?}: só lê optionPositions + cadeia; store.sell_option não olha `positions`
server/app/anatomia_perna.py:220-227: acoes só existe com posicao dict + qty + avg; senão acoes None, sem marcador precoMedio
server/app/estrutura_posicao.py:352: qtd_acoes None quando posicao não é dict (teste existente test_sem_posicao_em_acoes_total_e_soma_das_pernas)
server/tests/test_opcoes_anatomia_rota.py: fixtures _mock_provider, _expiracao_fixa, cli; helpers _novo_escopo(cli, slug) -> (uid, headers), _semear(cli, uid) (faz store.buy PETR4 300 e grava 2 pernas via db.kv_set), _get(cli, h, q="", t="PETR4")

ACHADO FORA DO ESCOPO (não alterar neste plano, reportar no SUMMARY):
web/src/finance.js:135 portfolioMetrics ignora perna sem `lastro` ("modelo antigo: fora do agregado", D-6, Fase 14), e store.buy_option (server/app/store.py:805) cria perna avulsa SEM `lastro`. Resultado: a PUT do Alex debitou R$ 92 do caixa e NÃO entra no patrimônio (patrimônio aparece R$ 92 menor). Guardião web/tests/test_finance.mjs:141-143 trava esse comportamento. Mudar exige decisão do Alex (semântica de patrimônio + paridade com o equity do backend/benchmark), por isso fica fora daqui.
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Helpers puros do universo com pernas avulsas + prova do backend com conta sem ações</name>
  <files>web/src/estruturaCard.js, web/tests/test_estrutura_card_logica.mjs, server/tests/test_opcoes_anatomia_rota.py</files>
  <behavior>
    - tickersComPernas([{t:"UGPA3"},{t:"PETR4"}], [{underlying:"UGPA3"},{underlying:"UGPA3"},{underlying:"VALE3"}]) -> ["UGPA3","VALE3"] (antes ["UGPA3"])
    - tickersComPernas(null, [{underlying:"VALE3"}]) -> ["VALE3"]; tickersComPernas([{t:"X"}], null) -> []
    - tickersSoComPernas([{t:"UGPA3"}], [{underlying:"UGPA3"},{underlying:"VALE3"},{underlying:"VALE3"},{underlying:"ITUB4"},{}, null]) -> ["VALE3","ITUB4"] (ordem de aparição, sem duplicata, ignora item sem underlying)
    - universoOpcoes([{t:"PETR4",qty:300,avg:30}], [{underlying:"VALE3"}]) -> [ mesmo objeto PETR4 (identidade preservada), {t:"VALE3", qty:0, qtyTravada:0, avg:null, stop:null, alvo:null, semAcoes:true} ]
    - universoOpcoes com optionPositions não-array devolve a carteira como veio; carteira não-array vira []
    - pytest: conta só com perna PUT de PETR4 (sem store.buy) -> GET /api/options/anatomia/PETR4 = 200, estado "ok", anatomia.acoes is None, nenhum marcador "precoMedio" em anatomia.total (quando total existe), estrutura presente; GET com ?excluir=ACOES não dá 400
    - pytest: na mesma conta, POST /api/options/sell {contractSymbol} = 200 e a perna some de optionPositions (store.get); positions continua vazio
  </behavior>
  <action>
RED primeiro: no fim de web/tests/test_estrutura_card_logica.mjs, adicione um bloco datado "// quick 261006-axi (2026-10-06): ticker só com opção (PUT VALEV731W2 sem VALE3) sumia da Carteira e do hub" com as asserções do <behavior> para tickersComPernas, tickersSoComPernas e universoOpcoes (use o `eq` e o `ok` já existentes no arquivo). A asserção existente da linha 15 ("tickersComPernas interseção") NÃO é apagada: troque a expectativa para ["UGPA3","VALE3"], renomeie para "tickersComPernas: carteira com pernas + ativo só com perna" e acrescente comentário "(reconciliado 2026-10-06, quick 261006-axi: o ticker só com perna passa a entrar; antes era descartado e a opção sumia da tela)". Em server/tests/test_opcoes_anatomia_rota.py adicione `def test_perna_avulsa_sem_acoes(cli)`: usa _novo_escopo, lê a cadeia de PETR4 como _semear faz, mas NÃO chama store.buy; grava via db.kv_set UMA perna PUT comprada (side "comprada", qty 100, avg 0.92, sem `lastro`) em optionPositions; asserta o comportamento do <behavior> para anatomia; depois POST /api/options/sell com headers e contractSymbol da perna e asserta 200 + perna ausente em store.get(_conn, "optionPositions", user_id=uid) + store.get(_conn, "positions", user_id=uid) vazio. Rode e confirme que o teste JS falha (helpers ausentes) antes de implementar.

GREEN em web/src/estruturaCard.js (módulo puro, sem React/I/O): (1) tickersComPernas passa a devolver os tickers de `positions` que têm perna (ordem de positions) seguidos dos underlyings com perna que não estão em positions (ordem de aparição, sem duplicata); `positions` não-array é tratado como []; `optionPositions` não-array continua devolvendo []. Atualize o comentário do topo da função com a nota datada. (2) Nova `tickersSoComPernas(positions, optionPositions)`: só os underlyings com perna e sem entrada em positions. (3) Nova `universoOpcoes(carteira, optionPositions)`: devolve a carteira na ordem e com os MESMOS objetos, mais um objeto sintético por ticker de tickersSoComPernas com o shape exato do <behavior> (`qty: 0` é fato — zero ações —; `avg/stop/alvo: null`, nunca 0; `semAcoes: true` é a marca que a UI usa para não exibir número de lastro). Comentário: nenhum preço/nome é fabricado; o objeto existe só para o ativo entrar no universo de leitura.

Backend: se o pytest passar sem mudança, NÃO toque server/app (o motor já trata posicao None; ver interfaces). Se falhar, corrija o ponto mínimo em server/app/main.py (options_anatomia / _estrutura_do_ativo) ou server/app/anatomia_perna.py para que `acoes` fique None (omitido do total, nunca 0) e registre a mudança no SUMMARY.
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2 && node web/tests/test_estrutura_card_logica.mjs && node web/tests/test_cartao_v6_logica.mjs && cd server && .venv/bin/python -m pytest tests/test_opcoes_anatomia_rota.py tests/test_estrutura_posicao.py tests/test_anatomia_perna.py -q</automated>
  </verify>
  <done>Os três helpers exportados com o comportamento do behavior; asserção antiga reconciliada com nota datada (não apagada); test_perna_avulsa_sem_acoes verde provando anatomia sem ações (acoes None) e Encerrar (sell) da perna avulsa; nenhum arquivo de server/app alterado a menos que o teste tenha exigido.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Hub de Opções inclui ativo só com perna (card "sem ações") e deep-link de Encerrar</name>
  <files>web/src/opcoes/OpcoesScreen.jsx, web/src/opcoes/HubOpcoes.jsx, server/app/skill_ref.py, web/src/copy.js, web/tests/test_opcoes_fluxo_render.mjs, web/tests/test_opcoes_universo_carteira.mjs, web/tests/test_opcoes_hub_workspace_ui.mjs</files>
  <behavior>
    - SSR: HubOpcoes com carteira=[{t:"PETR4",ticker:"PETR4",qty:300,...},{t:"VALE3",ticker:"VALE3",qty:0,qtyTravada:0,avg:null,stop:null,alvo:null,semAcoes:true}] renderiza 2 cards; o de VALE3 contém o texto de card_subtitulo_sem_acoes e NÃO contém "0 ações" nem "0 livres"
    - SSR: o card VALE3 com opcoesPorTicker {VALE3:{estrutura:{nome:"VALEV731W2"}}} mostra "estrutura aberta: VALEV731W2"
    - Fonte: OpcoesScreen deriva carteiraHub, o estado inicial do nav (inclui abrirTicker do Encerrar) e tickersEmCarteira/useOpcoesPropostas de universoOpcoes(carteira, optionPositionsAll); o seletor do Montar e PropostaDoAtivo seguem em `carteira`
    - Espelho: card_subtitulo_sem_acoes existe em OPCOES_ESCADA de skill_ref.py e no bloco correspondente de copy.js, nos dois modos, texto idêntico byte a byte entre os arquivos
  </behavior>
  <action>
Leia antes de editar: web/tests/test_opcoes_universo_carteira.mjs (seções 1 e 2), web/tests/test_opcoes_hub_workspace_ui.mjs (seção 7, linhas ~226-250), web/tests/test_opcoes_custo_declarado.mjs (confira se trava `useOpcoesPropostas(store, carteira.map` ou o universo; se travar, reconcilie igual aos outros), web/tests/test_opcoes_escada_espelho.mjs (como o espelho de OPCOES_ESCADA é conferido) e o bloco OPCOES_ESCADA em server/app/skill_ref.py (~1223, as duas vozes; card_subtitulo em ~1411 e ~1622) e copy.js (~1081 e ~2360).

Texto (per regra de paridade): crie a chave `card_subtitulo_sem_acoes` logo após `card_subtitulo` nas DUAS vozes de OPCOES_ESCADA em skill_ref.py e nos DOIS blocos de copy.js, com o mesmo texto byte a byte: "sem ações deste ativo · opção sem lastro". Mesmo texto nos dois modos é aceitável (é fato, não voz); se o guardião de espelho exigir diferença entre modos, siga o guardião e registre no SUMMARY. Sem promessa, sem número.

HubOpcoes.jsx CardAtivo: quando `pos.semAcoes === true`, `sub = opcoesEscadaTxt(mode, "card_subtitulo_sem_acoes") || ""` (sem vals); senão o ramo atual intacto. TermoOpcoes com TERMO_LASTRO continua envolvendo o texto (o termo "lastro" segue tocável). Atualize o comentário do topo ("Cards da CARTEIRA (só ativos com posição)") com nota datada: ativos com perna aberta sem ações entram como card "sem ações" (quick 261006-axi). Nada mais muda no card (régua/HV21/suporte/resistência vêm do técnico de custo zero; ausência já vira "—").

OpcoesScreen.jsx: importe `universoOpcoes` de "../estruturaCard.js" (confira que não há ciclo: estruturaCard.js só importa finance.js). Mova a definição de `optionPositionsAll` para logo após `const carteira = ...` (linha ~325; não altere a linha de `carteira`, regex travada) e remova a definição duplicada de ~741. Logo abaixo, `const universo = universoOpcoes(carteira, optionPositionsAll);` com comentário datado explicando a reconciliação da regra "universo = carteira" do 27-CONTEXT D3: o universo continua sendo POSIÇÃO (nunca watchlist); uma perna aberta é posição, e esconder a perna do usuário viola o princípio 9; o lastro continua vindo só de `carteira`. Troque para `universo`: o argumento `carteira` dos DOIS `estadoInicialOpcoes` (mount ~348 e onConcluido ~949) — passe `carteira: universo` —, o argumento de `useOpcoesPropostas` (`universo.map((p) => p.t)`), `tickersEmCarteira` (`universo.map((p) => p.t)`) e `carteiraHub` (`universo.map((p) => ({ ...p, ticker: p.t }))`, mantendo o nome e a prop `carteira={carteiraHub}`). NÃO troque: o seletor `{carteira.length > 0 ? seletor : null}` e o `carteira.map((p) =>` do seletor (Montar exige lastro), `posicaoSelecionada` e `PropostaDoAtivo posicao={carteira.find(...)}` (avulsa -> posicao null, que é o estado real "sem lastro"). `myOptionPositions`/PernasAbertas já filtram por nav.ticker e passam a funcionar para a perna avulsa sem mudança.

Guardiões (reconciliar, nunca apagar): em test_opcoes_hub_workspace_ui.mjs, a asserção "o hub recebe a CARTEIRA (carteiraHub, de ctx.data.positions)" permanece (regex `carteira=\{carteiraHub\}` + sem watchlist) e ganha irmã nova "(quick 261006-axi, 2026-10-06) carteiraHub deriva de universoOpcoes(carteira, optionPositionsAll): perna aberta sem ações entra no hub" checando `/const carteiraHub = universo\.map/` e `/universoOpcoes\(carteira, optionPositionsAll\)/` no fonte; acrescente ao cabeçalho do arquivo uma nota de reconciliação datada. Em test_opcoes_universo_carteira.mjs, acrescente ao cabeçalho a mesma nota (universo = posições de ações + pernas abertas; watchlist segue proibida; ticker continua nascendo vazio) e uma asserção nova: nenhum useEffect chama setNav com universo[0] (mesma regex do item de carteira[0], aplicada a `universo[0]`). Se alguma asserção existente quebrar por causa da troca de argumento (ex.: regex de `estadoInicialOpcoes({... carteira})` ou `useOpcoesPropostas(store, carteira.map`), reescreva a regex para o novo texto mantendo a invariante e anote "(reconciliado 2026-10-06, quick 261006-axi: ...)". Em test_opcoes_fluxo_render.mjs adicione um bloco datado com os casos SSR do <behavior> (reuse o padrão de render já existente na linha ~30 com `html(h(HubOpcoes, {...}))`).
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2 && for f in test_opcoes_fluxo_render test_opcoes_universo_carteira test_opcoes_hub_workspace_ui test_opcoes_custo_declarado test_opcoes_escada_espelho test_opcoes_caminho_b_ui test_opcoes_anatomia_render test_opcoes_consolidacao_ui; do node web/tests/$f.mjs > $TMPDIR/axi_$f.log 2>&1 || { echo "FALHOU $f"; grep FALHOU $TMPDIR/axi_$f.log; }; done; cd server && .venv/bin/python -m pytest tests/test_skill_ref.py -q && cd ../web && npx vite build</automated>
  </verify>
  <done>Hub mostra o ativo só com perna como card "sem ações" sem números de lastro; abrir o card leva ao objetivo com PernasAbertas; deep-link de Encerrar aceita o ticker avulso; chave nova espelhada byte a byte nos dois modos; guardiões verdes com notas de reconciliação datadas e nenhuma asserção removida; vite build verde.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Carteira renderiza card "sem ações" para ticker só com perna</name>
  <files>web/src/App.jsx, server/app/skill_ref.py, web/src/copy.js, web/tests/test_carteira_perna_avulsa.mjs</files>
  <behavior>
    - Guardião (fonte de App.jsx): CarteiraScreen calcula `tickersSoComPernas(data.positions, data.optionPositions)` e renderiza `<CartaoPernaAvulsa` para cada um, DEPOIS do map de data.positions
    - O estado "Portfólio vazio" só aparece com data.positions.length === 0 E nenhuma perna avulsa
    - CartaoPernaAvulsa: usa estadoLeitura(true, leituras[t]); "carregando"/"falha" mostram estruturaCardTxt lendo/indisponivel (+ BotaoAtualizarEstrutura na falha); "estruturada" renderiza CardPosicaoEstruturada com p sintético {t, qty:0, avg:null, stop:null, alvo:null, semAcoes:true}
    - CartaoPernaAvulsa NÃO renderiza FaceAcao, ReguaPlano, EditorStopAlvo, BlocoBorisIA nem pctDoCapital (sem ação não há plano de ação)
    - Nome: nomeEmpresaCard(t, quotes[t], data.catalog, nomesRef.current[t]) ou nada; nenhum preço de ação exibido
    - Espelho: chave `avulsa_sem_acoes` em CARTAO_POSICAO (skill_ref.py ~876) e no bloco espelhado de copy.js usado por cartaoPosicaoTxt, nos dois modos, byte a byte
  </behavior>
  <action>
Leia com Grep + Read offset/limit (nunca App.jsx inteiro): CarteiraScreen (~5549-5690), CartaoPosicao cabeçalho (~4899-4935, só para copiar estilo de título/rotulo/card/varsCartaoV6), CardPosicaoEstruturada assinatura (~4631) e o import da linha 10. Leia CARTAO_POSICAO em server/app/skill_ref.py (~876) e o bloco de copy.js lido por cartaoPosicaoTxt (~2638), e web/tests/test_cartao_posicao_espelho.mjs para saber como o espelho é conferido.

Texto: chave `avulsa_sem_acoes` em CARTAO_POSICAO nas duas vozes (skill_ref.py e copy.js, byte a byte): "Sem ações deste ativo: só a opção está aberta." Siga o guardião de espelho se ele exigir voz diferente por modo.

App.jsx: adicione `tickersSoComPernas` ao import de "./estruturaCard.js" na linha 10. Em CarteiraScreen, `const avulsas = tickersSoComPernas(data.positions, data.optionPositions);` junto de `comPernas`. Troque a condição do vazio para `data.positions.length === 0 && avulsas.length === 0` com comentário datado (quick 261006-axi). Mantenha `LinhaChamadaOpcoes` com a guarda atual. Depois do `data.positions.map(...)`, dentro do mesmo contêiner flex, renderize `avulsas.map((t) => <div key={"avulsa-" + t} id={"posicao-" + t} style={{ ...card, ...varsCartaoV6(themeKey, operador ? "operador" : "estudo"), padding: \`${SP[4]}px\` }}><CartaoPernaAvulsa t={t} ... /></div>)` passando leitura (`leituras[t]`), nome (nomeEmpresaCard como no map de positions, atualizando nomesRef do mesmo jeito), cp, operador, ctx, data e `onAtualizar={() => atualizarEstrutura(t)}`. `useEstruturasPosicao` já pede a leitura do ticker avulso porque tickersComPernas passou a incluí-lo (Task 1) — não mexa no hook.

Crie `function CartaoPernaAvulsa({ t, nomeEmpresa, leitura, cp, operador, ctx, data, onAtualizar })` perto de CartaoPosicao: modo = operador ? "operador" : "estudo"; `const modoLeitura = estadoLeitura(true, leitura)`; cabeçalho igual ao do CartaoPosicao (ticker em MONO, nome só se existir), linha `cartaoPosicaoTxt(modo, "avulsa_sem_acoes")` em estilo rótulo; carregando/falha com o mesmo bloco role="status" aria-live="polite" do CartaoPosicao (estruturaCardTxt + BotaoAtualizarEstrutura na falha); estruturada -> `<CardPosicaoEstruturada p={{ t, qty: 0, avg: null, stop: null, alvo: null, semAcoes: true }} leitura={leitura} cp={cp} operador={operador} ctx={ctx} data={data} onAtualizar={onAtualizar} />` (ela só lê p.t; o Encerrar já leva ao hub com abrirTicker, que a Task 2 tornou válido). Comentário no topo do componente: por que existe, que nada é fabricado (qty 0 é fato, avg/stop/alvo null), e o achado de patrimônio D-6 fora do escopo.

Guardião novo web/tests/test_carteira_perna_avulsa.mjs (padrão dos outros guardiões de fonte: lê App.jsx, remove comentários, `ok(name, cond)`, exit 1 se falhar): asserta tudo do <behavior> por regex sobre o fonte (import de tickersSoComPernas; `const avulsas = tickersSoComPernas(data.positions, data.optionPositions)`; condição do vazio com `avulsas.length === 0`; `<CartaoPernaAvulsa` dentro de `avulsas.map`; fatia do corpo de `function CartaoPernaAvulsa` sem `FaceAcao|ReguaPlano|EditorStopAlvo|BlocoBorisIA|pctDoCapital` e com `estadoLeitura(true, leitura)` e `<CardPosicaoEstruturada`; `semAcoes: true`, `avg: null`), mais espelho de `avulsa_sem_acoes` entre skill_ref.py e copy.js nos dois modos (importe COPY/cartaoPosicaoTxt de copy.js e compare com o literal lido de skill_ref.py). Inclua uma asserção de sanidade de que as regexes pegam o padrão quando ele existe.

Ao fim: `cd web && npx vite build && npx cap copy ios` (cap copy é pedido explícito desta tarefa rápida; se falhar por ausência de web/ios no worktree, registre no SUMMARY e siga).
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2 && node web/tests/test_carteira_perna_avulsa.mjs && node web/tests/test_cartao_posicao_espelho.mjs && node web/tests/test_estrutura_card_ui.mjs && node web/tests/test_carteira_lastro_ui.mjs && node web/tests/test_cartao_v6_fechado.mjs && cd server && .venv/bin/python -m pytest tests/test_skill_ref.py -q && cd ../web && npx vite build && npx cap copy ios</automated>
  </verify>
  <done>Na Carteira, conta com só a PUT VALEV731W2 mostra card VALE3 "sem ações" com a estrutura do motor e o Encerrar; Portfólio vazio não aparece nesse caso; nenhum número de ação inventado; guardião novo verde; espelho da chave nova verde; vite build e cap copy ios executados.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| cliente -> GET /api/options/anatomia/{ticker} | ticker e `excluir` vêm do cliente; posições só do escopo do token |
| cliente -> POST /api/options/sell | contractSymbol do cliente; preço só da cadeia do servidor |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-axi-01 | Tampering | universoOpcoes / card sintético | mitigate | objeto sintético tem avg/stop/alvo null e semAcoes true; nunca entra em portfolioMetrics nem em store; Task 1 testa o shape exato |
| T-axi-02 | Information disclosure | options_anatomia sem ações | accept | rota já lê só o escopo do token (test_isolamento_entre_contas existente); o plano não muda a leitura |
| T-axi-03 | Spoofing | deep-link abrirTicker | mitigate | abrirTickerOpcoes continua validando contra o universo derivado de posições/pernas DO ESCOPO (ctx.data), nunca de string livre |
| T-axi-04 | Repudiation | sell da perna avulsa | accept | store.sell_option já grava histórico com motivo/origem; sem mudança |
</threat_model>

<verification>
- Tarefas 1-3: comandos de verify de cada uma.
- Fechamento (orquestrador, fora do sandbox): `bash scripts/executar.sh --testes` (pytest + web/tests/*.mjs), depois de `npx vite build` e `npx cap copy ios` já rodados na Task 3.
- Conferir `git diff --stat`: nenhum arquivo fora de files_modified (server/app/main.py ou anatomia_perna.py só se o pytest da Task 1 exigiu, registrado no SUMMARY); web/src/persistence.js e web/src/finance.js sem diff.
</verification>

<success_criteria>
- A PUT avulsa (ativo sem ações) aparece na Carteira e no hub de Opções, rotulada "sem ações", com nome só de fonte real e nenhum preço/quantidade de ação fabricado.
- Abrir o ativo no hub mostra PernasAbertas/anatomia; Encerrar funciona (rota de sell coberta por pytest).
- Rota de anatomia com conta sem ações: estado ok, acoes None.
- Textos novos espelhados byte a byte skill_ref.py <-> copy.js nos dois modos.
- Guardiões reconciliados com nota datada; nenhuma asserção apagada.
- Achado D-6 (patrimônio ignora perna sem lastro) documentado no SUMMARY como pendente de decisão do Alex, sem mudança de código.
</success_criteria>

<output>
Create `.planning/quick/261006-axi-op-o-comprada-sem-a-es-do-ativo-some-da-/261006-axi-SUMMARY.md` when done
</output>
