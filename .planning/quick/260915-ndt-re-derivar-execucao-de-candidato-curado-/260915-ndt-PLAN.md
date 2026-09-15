---
phase: quick-260915-ndt
plan: 01
type: execute
wave: 1
depends_on: []
autonomous: true
requirements: [QUICK-260915-NDT]
files_modified:
  - server/app/main.py
  - server/tests/test_curadoria_collar_rota.py
  - web/src/api.js
  - web/src/persistence.js
  - web/src/opcoes/executarCandidato.js
  - web/src/copy.js
  - web/src/App.jsx
  - web/tests/test_executar_candidato.mjs
  - web/tests/test_opcoes_collar_ui.mjs
  - web/tests/test_curadoria_ui.mjs

must_haves:
  truths:
    - "D-01: Um collar da lista curada EXECUTA quando a leitura técnica NÃO endossa collar — o caso que hoje devolve 409 sempre."
    - "D-01: A execução de um candidato curado é re-derivada pelo MESMO motor que gerou o card (opcoes_curadoria), nunca por opcoes_lastreadas.propor()."
    - "D-02: Corpo adulterado continua REJEITADO: idCandidato que não bate, perna trocada, lado invertido ou contratos diferentes devolvem 409 e não abrem posição."
    - "D-02: Nenhum número executado vem do corpo — prêmio, strike, expiração e contratos saem sempre do candidato RE-DERIVADO pelo servidor."
    - "D-03: Venda coberta, put de proteção e opção a descoberto da lista curada continuam executando pelas rotas de hoje, sem uma linha de mudança nelas."
    - "D-04: Modo Estudo (403), lastreada já aberta no underlying (409), gate de liquidez em 3 faixas e a checagem de caixa/lastro de store.abrir_collar continuam valendo na rota nova."
    - "D-05: O painel inline de confirmação deixa de rotular o prêmio em reais com o rótulo da RAZÃO — os dois números têm rótulos diferentes, nos DOIS modos."
  artifacts:
    - path: "server/app/main.py"
      provides: "_curadoria_scan_posicao (helper extraído de _curadoria_top) + rota POST /api/options/curadoria/abrir-collar"
      contains: "curadoria/abrir-collar"
    - path: "server/tests/test_curadoria_collar_rota.py"
      provides: "Prova central (velha 409 × nova 200 no MESMO cenário) + guardiões de adulteração e de defesas preservadas"
      min_lines: 200
    - path: "web/src/opcoes/executarCandidato.js"
      provides: "Ramo collar despachando para optionsCuradoriaAbrirCollar com idCandidato no corpo"
      contains: "idCandidato"
    - path: "web/src/copy.js"
      provides: "curadoriaPremioRotulo nos dois modos (rótulo do prêmio em reais, distinto do rótulo da razão)"
      contains: "curadoriaPremioRotulo"
  key_links:
    - from: "web/src/opcoes/executarCandidato.js"
      to: "web/src/persistence.js (serverStore + deviceStore)"
      via: "store.optionsCuradoriaAbrirCollar(body)"
      pattern: "optionsCuradoriaAbrirCollar"
    - from: "web/src/api.js"
      to: "POST /api/options/curadoria/abrir-collar"
      via: "req(\"POST\", ...)"
      pattern: "curadoria/abrir-collar"
    - from: "server/app/main.py (rota nova)"
      to: "server/app/opcoes_curadoria.candidatos_da_posicao"
      via: "_curadoria_scan_posicao — a MESMA varredura de _curadoria_top"
      pattern: "_curadoria_scan_posicao"
    - from: "server/app/main.py (rota nova)"
      to: "server/app/store.abrir_collar"
      via: "execução com contratos/prêmios do candidato re-derivado"
      pattern: "store\\.abrir_collar"
---

<objective>
Fechar o defeito em que TODO collar da lista curada ("AS 4 MELHORES OPORTUNIDADES
DE OPÇÕES") devolve 409 ao ser executado, e corrigir um rótulo financeiro errado
no painel de confirmação inline.

Causa raiz (diagnóstico FECHADO — premissa, não re-investigar): existem dois
motores de proposta de opções com regras diferentes. `opcoes_curadoria.py` gera a
lista curada **sem** porta de setup/plano técnico (comentário literal em
`opcoes_curadoria.py:211-218`: "Deliberadamente NÃO há porta de setup/plano
técnico aqui"). `opcoes_lastreadas.propor()` EXIGE `plano.decisao`/`plano.lado`
e devolve `sem_setup` quando o motor técnico não endossa. A rota
`POST /api/options/lastreada/abrir-collar` (`main.py:3649`) re-deriva por
`propor(..., multiperna=True)` (`main.py:3739`) e 409a quando não acha candidato
de tipo `collar` (`main.py:3753-3756`) — então o card curado, que nasceu sem o
gate técnico, morre no gate técnico da outra rota. Reproduzido em produção
(UGPA3, 2026-09-15): a tira de cima dizia que a leitura técnica não indicava
collar enquanto a lista curada logo abaixo oferecia 4 collars.

Decisão de produto TRAVADA (Alex, AskUserQuestion, 2026-09-15): **re-derivar pelo
motor certo**. A execução de um candidato curado passa a re-derivar por
`opcoes_curadoria`, o MESMO motor que gerou o card. A defesa anti-adulteração
continua intacta — o servidor recalcula tudo e nunca confia no corpo; só deixa de
exigir endosso da leitura técnica, coerente com o guardrail que já existe no
`CLAUDE.md`: "Stop/alvo nunca são vetados: `operar: false` é parecer, não veto".

Purpose: o bloco de curadoria da Fase 31 tem 4 tipos de estrutura e hoje 3
executam; o collar é o único morto — e morre com uma mensagem que fala de um
recálculo que o usuário não pediu e não entende.

Output: rota nova `POST /api/options/curadoria/abrir-collar`, despacho de front
por ela, chave de copy nova para o prêmio, e guardiões que travam a classe
inteira do bug.
</objective>

<decisoes_de_desenho>
As duas decisões que o plano precisa justificar, resolvidas aqui — o executor
implementa, não re-decide.

## 1. ROTA NOVA, não um ramo/flag na rota existente

O precedente é do próprio repositório (ADR-026, Decisão 1, citado em
`main.py:3656-3660`): quando a Fase 17 precisou executar collar, criou uma rota
NOVA em vez de uma flag na `/abrir`, porque *"um parâmetro tipo
`permitirMultiperna` no corpo transformaria essa defesa de servidor num opt-out
do próprio cliente — exatamente o que ela existe para impedir"*.

Uma flag no corpo escolhendo QUAL motor valida (`origem: "curadoria"`) é o MESMO
anti-padrão, agravado: o cliente escolheria qual gate atravessar. **Descartada.**

A rota nova é `POST /api/options/curadoria/abrir-collar` — namespace `curadoria`
porque o namespace nomeia o motor que valida. `POST /api/options/lastreada/abrir-collar`
fica **byte a byte como está**: continua sendo o caminho da proposta única
(a tira "OPORTUNIDADES DE OPÇÕES"), com o gate técnico do `propor()` — que ali é
correto, porque aquele card nasceu do `propor()`.

**Escopo da rota nova: SÓ collar.** Os outros três tipos não passam por
re-derivação via `propor()` — `POST /api/options/lastreada/abrir` (`main.py:3566`)
e `POST /api/options/buy` (`main.py:3017`) validam o contrato contra a cadeia e a
liquidez e executam. Por isso venda coberta da lista curada JÁ FUNCIONA
(verificado ao vivo pelo orquestrador em 2026-09-14: clique → posição real
aberta, caixa creditado +R$130,00). Mexer neles seria risco sem ganho.

## 2. `idCandidato` é a CHAVE de re-derivação, não a fonte dos dados

`opcoes_curadoria.id_candidato(tipo, ticker, expiration, contract_symbol, *,
strike_call, strike_put)` (`opcoes_curadoria.py:106-126`) é identidade **estável
e total**; para collar inclui os DOIS strikes, porque collar não tem
`contractSymbol` único.

O corpo manda `idCandidato`; o servidor **RECALCULA** os candidatos daquela
posição pela mesma varredura de `_curadoria_top` e procura o que bate. Nada do
corpo vira número executado: contratos, pernas, prêmios, strikes e expiração
saem todos do candidato re-derivado. `underlying` no corpo serve só para escolher
QUAL posição varrer — apontar para a posição errada faz o `idCandidato` não bater
e cair no 409, não vira brecha.

`pernasContratos` e `contratos` continuam no corpo **apesar de não serem
confiados**: eles existem para o CROSS-CHECK explícito (perna trocada, lado
invertido, contratos divergentes → 409), que é o guardião de adulteração que a
verificação exige. É a mesma disciplina da rota irmã, só que contra o candidato
da curadoria.

`expiration` NÃO vai no corpo (a rota irmã aceita): o `idCandidato` já carrega a
expiração, e aceitá-la de novo criaria uma segunda fonte de verdade para o mesmo
campo.

## 3. Reuso da varredura, não uma segunda cópia dela

`_curadoria_top` (`main.py:3287`) já faz a varredura server-side por posição (até
`opcoes_curadoria.VENCIMENTOS_POR_POSICAO` = 2 vencimentos, com cotação uma vez
por ticker). A rota nova NÃO duplica esse laço: a Task 1 **extrai** o corpo do
laço para `_curadoria_scan_posicao(...)` e faz `_curadoria_top` chamá-lo. Duas
varreduras divergentes é exatamente como o card e a execução voltariam a
discordar.

Consequência de custo, declarada: a rota nova varre **uma** posição (até 2
`get_options` + 1 `get_quote`), nunca a carteira inteira — e o cache de 300s do
provedor costuma absorver, já que o usuário acabou de ver a lista.
</decisoes_de_desenho>

<defesas_que_continuam>
Nomeadas explicitamente porque a decisão do Alex afrouxa UMA coisa (o endosso
técnico) e nada mais. Cada uma tem caso de teste na Task 1.

| Defesa | Onde | Como continua na rota nova | Teste |
|--------|------|----------------------------|-------|
| Modo Estudo não executa | 403, `main.py:3675` | Primeira checagem da rota, ANTES de qualquer rede | `test_curada_modo_estudo_403_sem_tocar_provider` (bomba em `get_options`) |
| Lastreada já aberta no underlying | 409, `main.py:3710` | Mesma checagem, ANTES da re-derivação (evita fetch inútil) | `test_curada_recusa_segunda_estrutura_no_mesmo_underlying` |
| Anti-adulteração: corpo nunca vira dado executado | ADR-026 D2 | Tudo vem do candidato re-derivado; cross-check de contratos e de `{contractSymbol: lado}` | `test_curada_*_adulterad*` (4 casos) + guardião estrutural de fonte |
| Gate de liquidez em 3 faixas | `main.py:3767-3785` | Idêntico, lendo `p["liquidez"]["faixa"]`/`["score"]` do candidato RE-DERIVADO, nunca do corpo | `test_curada_liquidez_dificil_exige_consentimento` |
| Caixa / lastro / atomicidade das 2 pernas | `store.abrir_collar`, `store.py:1170` | Inalterado — a rota chama a MESMA função sob `ORDER_LOCK` | `test_curada_sem_caixa_400_sem_meia_estrutura` |
| Fase 29 (opção a descoberto exige flag) | `store.buy_option` | A rota nova passa `permitir_a_descoberto=False` FIXO e só aceita `tipo == "collar"` — não é caminho alternativo para a descoberto | `test_curada_recusa_id_de_outro_tipo` |
| Guardrail CVM (manchete só do motor) | `test_opcoes_collar_vocab.py` | Nenhuma string-âncora nova em código/comentário de `web/src/*.js*` nem de `server/app/*.py` | a própria suíte, que varre os arquivos |

**Nota sobre o gate de liquidez:** com `PISO_LIQUIDEZ = LIQUIDEZ_NEGOCIAVEL`
passado explicitamente a `rastrear()` (`opcoes_curadoria.py:237-240, 321-324`),
as duas pernas do candidato curado já são NEGOCIÁVEL ou melhor — o ramo DIFÍCIL
é hoje praticamente inalcançável por esta rota. **Não remova o gate por isso.**
`PISO_LIQUIDEZ` é constante ajustável (já foi recalibrada uma vez, quick
260908-ldg); sem o gate, uma recalibração futura abriria execução sem
consentimento em silêncio. O caso de teste força a faixa por fixture.
</defesas_que_continuam>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@./CLAUDE.md
@.planning/quick/260915-j5l-corrigir-clique-nos-cards-da-lista-curad/260915-j5l-SUMMARY.md

Backend: `server/app/main.py` (3287 `_curadoria_top`, 3416 `/api/options/curadoria`,
3566 `/lastreada/abrir`, 3649 `/lastreada/abrir-collar`),
`server/app/opcoes_curadoria.py`, `server/app/store.py` (`abrir_collar`, 1170).
Front: `web/src/opcoes/executarCandidato.js`, `web/src/api.js`,
`web/src/persistence.js`, `web/src/copy.js`, `web/src/App.jsx`
(`CuradoriaEstruturas`, 4198-4396 — arquivo tem ~9700 linhas, **use Grep antes de
Read**).
Testes de referência: `server/tests/test_opcoes_collar_rota.py` (fixtures de
cenário de collar), `server/tests/test_opcoes_curadoria_rota.py` (fixtures de
cadeia/contador de chamadas), `web/tests/test_executar_candidato.mjs`,
`web/tests/test_opcoes_collar_ui.mjs` (guardiões de paridade dos stores, ~205-219),
`web/tests/test_curadoria_ui.mjs` (regras 1-22 e a lista `CHAVES`, linha 135).

<interfaces>
Contratos já verificados nesta sessão — use direto, não re-descubra.

Candidato de collar produzido por `opcoes_curadoria.candidatos_da_posicao`
(`opcoes_curadoria.py:430-471`):
  tipo="collar", ticker, contractSymbol=None, optionType=None, strike=None,
  strikeCall, strikePut, pernasContratos=[{contractSymbol, optionType, lado,
  strike, premioUnitario} × 2 — call "venda" primeiro, put "compra" depois],
  expiration, diasParaVencimento, contratos, qtyAcoes, premioUnitario,
  premioTotal, liquidez={score, faixa, aviso, spreadPct}, estrutura, razao,
  manchete, didatica, precoObjeto, idCandidato, posicaoNoRanking (após rankear).

  `id_candidato("collar", ticker, expiration, None, strike_call=X, strike_put=Y)`
  → f"collar:{ticker}:{expiration}:{X}/{Y}".

  `candidatos_da_posicao(underlying, chain, spot, posicao, modo, hoje, *, n,
  permitir_a_descoberto)` é PURA e **não recebe `cash`** (comentário em
  `opcoes_curadoria.py:453-458`: "a varredura é DESCOBERTA, o caixa é cobrado na
  execução (`store.abrir_collar`). Não 'conserte' adicionando um parâmetro de
  caixa").

`store.abrir_collar(conn, contract_call, contract_put, contratos, premio_call,
premio_put, user_id=None, origem="manual") -> None` — levanta `ValueError` em
prêmio <= 0, contratos < 1, optionType errado, lastro/caixa insuficiente; as
duas pernas abrem juntas ou nenhuma abre (ORDER_LOCK).
`contract_*` shape: {id, underlying, optionType, strike, expiration, ivEntrada}.

Já importados em `main.py` e usados pela rota irmã: `FAIXA_SEM_MERCADO`,
`FAIXA_DIFICIL`, `faixa_de_liquidez`, `liquidity_score`, `_normalize_ticker`,
`_spot_from_chain_or_quote`, `_hoje_brt`, `_disparar_ciclo_imediato`,
`store.public_state`.
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Rota POST /api/options/curadoria/abrir-collar re-derivando pelo motor da curadoria</name>
  <files>server/app/main.py, server/tests/test_curadoria_collar_rota.py</files>
  <behavior>
    Casos que o arquivo de teste novo precisa cravar (RED medido antes de
    implementar a rota — a rota não existe, então a PROVA CENTRAL falha com 404):

    - PROVA CENTRAL (um único teste, as duas metades juntas para o contraste
      ficar no artefato): cenário com Modo Operador + posição com 300 ações
      livres + cadeia com calls e puts líquidas, e `setups.plano_do_resultado`
      devolvendo NÃO OPERAR (monkeypatch — é o cenário comum, em que a leitura
      técnica não endossa collar). Assert 1: `POST /api/options/lastreada/abrir-collar`
      devolve **409** com a mensagem de "não está mais disponível" (o bug de
      hoje, preservado de propósito naquela rota). Assert 2: no MESMO escopo e
      cenário, `POST /api/options/curadoria/abrir-collar` com o `idCandidato`
      lido de `GET /api/options/curadoria` devolve **200**, e
      `optionPositions` passa a ter as 2 pernas com `lastro`, e o caixa mudou.
    - `idCandidato` que não bate (string inventada) → 409, nenhuma posição aberta.
    - `pernasContratos` com um `contractSymbol` real da cadeia mas diferente do
      proposto → 409.
    - `lado` invertido entre as duas pernas → 409.
    - `contratos` diferente do re-derivado (ex.: 1 quando o motor diz 3) → 409.
    - `premioUnitario`/`strike` inflados no corpo NÃO chegam à execução:
      `premiosUsados` na resposta traz os prêmios da CADEIA.
    - `idCandidato` de um candidato `call_coberta` (tipo errado) → 409; nenhuma
      venda coberta aberta por esta rota.
    - Modo Estudo → 403, com bomba em `options_provider.get_options` provando
      que nem a cadeia foi buscada.
    - Lastreada já aberta no underlying → 409 com a mensagem de
      "feche-a antes de montar outra estrutura", sem tocar no provider.
    - Liquidez DIFÍCIL (fixture com volume/OI baixos na perna pior) → 400 pedindo
      `aceitaLiquidezDificil`; com `aceitaLiquidezDificil: true` → 200.
    - Caixa insuficiente para o débito do collar → 400 (ValueError de
      `store.abrir_collar`) e **nenhuma perna aberta** (`optionPositions` vazio —
      prova da atomicidade).
    - Cadeia degradada (`providerStatus != "ok"`) → 502, nunca 409 (um 409 diria
      ao usuário que a estrutura sumiu quando na verdade a fonte caiu).
    - Guardião estrutural (`inspect.getsource(main.options_curadoria_abrir_collar)`):
      a fonte da rota **não** menciona `opcoes_lastreadas.propor` e **não** lê
      `premioUnitario`/`strike`/`expiration` de `body` — é a prova de que a
      re-derivação é do motor da curadoria e de que nenhum número vem do corpo.
    - Não-regressão da extração: `server/tests/test_opcoes_curadoria_rota.py`
      inteiro continua passando sem uma linha alterada.
  </behavior>
  <action>
Duas mudanças em `server/app/main.py`, nesta ordem.

(1) EXTRAIR o corpo do laço de `_curadoria_top` (`main.py:3330-3390`) para um
helper novo, `async def _curadoria_scan_posicao(t, posicao, modo, hoje, *,
permitir_a_descoberto)`, que faz exatamente o que o laço faz hoje para UMA
posição: primeira `options_provider.get_options(t)` sem `expiration`; cotação uma
única vez por ticker via `candle_provider.get_quote`; `_spot_from_chain_or_quote`;
`opcoes_curadoria.candidatos_da_posicao(...)`; depois os vencimentos extras por
`opcoes_curadoria.proximos_vencimentos(...)` limitados a
`VENCIMENTOS_POR_POSICAO - 1`, cada um tratado independentemente (falha de extra
nunca derruba o vencimento que deu certo). Devolve
`(candidatos, chains_por_expiration, vencs_varridos, degradado)`, onde
`chains_por_expiration` mapeia a expiração efetiva de cada cadeia buscada para a
própria cadeia — é dela que a rota nova tira `impliedVolatility`/`strike` do
contrato, dado que o candidato não carrega IV. Falha ou `providerStatus != "ok"`
na PRIMEIRA cadeia devolve `([], {}, [], True)`.

`_curadoria_top` passa a ser o laço sobre `elegiveis` chamando esse helper, com
o `meta` montado exatamente como hoje (`avaliadas`, `ignoradas`, `degradados`
deduplicado, `candidatosAvaliados`, `candidatosPorTipo`, `vencimentosPorTicker`,
`tetoVencimentos`, `source`). `source` continua saindo da primeira cadeia bem
sucedida. **Mudança de comportamento observável: NENHUMA** — a prova é
`test_opcoes_curadoria_rota.py` passar intacto (ele conta chamadas ao provider
par a par).

(2) CRIAR `@app.post("/api/options/curadoria/abrir-collar")`,
`async def options_curadoria_abrir_collar(body: dict = Body(default={}), scope:
Optional[str] = Depends(current_scope))`, na ordem abaixo — a ordem é parte do
contrato, porque decide qual erro o usuário vê primeiro:

  1. `cfg = store.get(_conn, "config", user_id=scope) or {}`; `appMode != "operador"`
     → 403 com a MESMA frase das rotas irmãs ("Modo Estudo não executa ordens —
     troque para o Modo Operador para operar.").
  2. `underlying = _normalize_ticker(str(body.get("underlying") or ""))`,
     `len < 4` → 400 "Operação lastreada inválida."
  3. `id_candidato = body.get("idCandidato")` — não-string ou vazia → 400
     "Estrutura curada inválida — falta a identificação do candidato."
  4. `pernasContratos`: exatamente 2, cada uma dict com `contractSymbol` string
     não vazia e `lado` em ("venda", "compra") → senão 400 "Collar exige
     exatamente duas pernas." (mesma validação de forma de `main.py:3681-3689`).
  5. `contratos` numérico >= 1 → senão 400 "Operação lastreada inválida."
  6. Lastreada já aberta em `underlying` (`optionPositions` com `lastro`) → 409
     com a frase existente de `main.py:3711-3713`. **Antes da rede**, mesmo
     motivo comentado na rota irmã.
  7. Posição: `next((p for p in positions if p["t"] == underlying), None)`;
     ausente ou `store.qty_livre(pos) < 100` → 409 (estrutura não mais
     disponível).
  8. RE-DERIVAÇÃO: `await _curadoria_scan_posicao(underlying, posicao, modo,
     _hoje_brt(), permitir_a_descoberto=False)` dentro de `try/except HTTPException:
     raise / except Exception: raise HTTPException(502, "Não foi possível
     recalcular a varredura — tente novamente.")`. `permitir_a_descoberto=False`
     é FIXO e nunca lido do corpo nem da config: esta rota só executa collar, e
     um `True` aqui só serviria para transformá-la num caminho paralelo ao gate
     da Fase 29. Se `degradado and not candidatos` → 502 "Cotação de opções
     indisponível no momento — tente novamente." (nunca 409: fonte caída não é
     estrutura que sumiu).
  9. `p = next((c for c in candidatos if c.get("idCandidato") == id_candidato
     and c.get("tipo") == "collar"), None)`; se não achar → 409 "Esta estrutura
     não está mais disponível — o servidor refez a varredura e o resultado
     mudou." (mensagem DISTINTA da rota irmã de propósito: um 409 em produção
     precisa dizer qual dos dois caminhos o produziu). O duplo critério
     (`idCandidato` E `tipo`) é defesa em profundidade — o id já carrega o tipo
     no prefixo, e checar os dois torna a rota imune a um formato de id futuro.
 10. CROSS-CHECK contra `p`: `int(contratos) != p["contratos"]` → 409;
     `{perna["contractSymbol"]: perna["lado"] for perna in pernas}` diferente do
     mesmo dict montado de `p["pernasContratos"]` → 409. Mensagem única: "Os
     contratos enviados não conferem com a estrutura recalculada pelo servidor."
 11. Gate de liquidez em 3 faixas lendo `p["liquidez"]["faixa"]` e `["score"]`,
     com as MESMAS duas mensagens de `main.py:3776-3785` (SEM MERCADO
     incondicional primeiro; DIFÍCIL depois, destravado só por
     `body.get("aceitaLiquidezDificil") is True` — identidade, nunca
     truthiness).
 12. Pernas por `optionType` (nunca por índice): `perna_call`/`perna_put` de
     `p["pernasContratos"]`; qualquer uma ausente → 409 (mesma mensagem do
     cross-check). `chain = chains.get(p["expiration"])`; ausente → 502.
     `contrato_call`/`contrato_put` por `contractSymbol` em
     `[*chain["calls"], *chain["puts"]]`; ausente → 404 "Contrato não encontrado
     na cadeia atual."
 13. Monta `contract_call`/`contract_put` no shape de `store.abrir_collar`
     (`id`, `underlying`, `optionType`, `strike` e `ivEntrada` do contrato da
     CADEIA; `expiration` de `chain.get("expiration")`), prêmios de
     `float(perna_*["premioUnitario"])` — do candidato RE-DERIVADO, nunca do
     corpo.
 14. `store.abrir_collar(_conn, contract_call, contract_put, int(p["contratos"]),
     premio_call, premio_put, user_id=scope)` em `try/except ValueError as e:
     raise HTTPException(400, str(e))`.
 15. `_disparar_ciclo_imediato(scope)`; `out = store.public_state(...)`;
     `out["premiosUsados"]` no mesmo formato da rota irmã
     (`main.py:3825-3828`); `return out`.

Docstring da rota: registre (a) por que rota nova e não flag (ADR-026 D1 —
flag no corpo escolhendo o motor validador é opt-out do cliente sobre a defesa
do servidor); (b) por que a re-derivação é por `opcoes_curadoria` e não por
`opcoes_lastreadas.propor` (o card nasceu sem gate técnico; exigir o gate na
execução é a incoerência que este plano fecha — decisão do Alex, 2026-09-15,
alinhada ao guardrail "operar: false é parecer, não veto"); (c) que
`/api/options/lastreada/abrir-collar` continua existindo e continua com o gate
do `propor()`, porque serve o card que nasceu do `propor()`.

**PROIBIDO:** escrever as strings-âncora do guardrail CVM ("trava protetora",
"abate o custo") em qualquer literal de código deste arquivo —
`test_opcoes_collar_vocab.py` varre `server/app/*.py`. Use "collar", como
`store.py:1202-1210` já faz e explica.

Arquivo de teste NOVO `server/tests/test_curadoria_collar_rota.py`, autocontido
(padrão da casa: não importar fixture de outro módulo de teste). Copie o estilo
de fixture de `test_opcoes_curadoria_rota.py` (cadeia sintética com
`_contrato()`/`_cadeia()`, `_contador()`, `_quote_fake` autouse, `_novo_escopo`,
`_liga_operador`) — mas a cadeia precisa de **calls E puts** (as fixtures de lá
usam `puts: []`, que nunca gera collar). Não invente helper de rede: tudo por
monkeypatch de `options_provider.get_options`.
  </action>
  <verify>
    <automated>cd server && .venv/bin/python -m pytest tests/test_curadoria_collar_rota.py tests/test_opcoes_curadoria_rota.py tests/test_opcoes_collar_rota.py tests/test_gate_liquidez_rotas.py tests/test_opcoes_collar_vocab.py -q</automated>
  </verify>
  <done>A prova central passa (velha 409 e nova 200 no MESMO cenário), os 4 casos de adulteração devolvem 409 sem abrir posição, as 6 defesas da tabela têm caso verde, e as suítes de collar/curadoria/liquidez/vocab pré-existentes passam sem edição.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Front despacha collar curado para a rota nova, com paridade nos dois stores</name>
  <files>web/src/api.js, web/src/persistence.js, web/src/opcoes/executarCandidato.js, web/tests/test_executar_candidato.mjs, web/tests/test_opcoes_collar_ui.mjs</files>
  <behavior>
    - `corpoDoCandidato(candidatoCollar)` devolve `metodo ===
      "optionsCuradoriaAbrirCollar"` e body deep-equal a
      `{underlying, idCandidato, pernasContratos: [{contractSymbol, lado} × 2],
      contratos}` — sem `expiration`, sem prêmio, sem strike.
    - Com `{aceitaLiquidezDificil: true}` a chave entra no body; com
      `"true"`/`1`/`{}` NÃO entra (identidade, não truthiness — regra já
      existente do módulo).
    - Candidato de collar sem `idCandidato` lança Error nomeado e não chama
      store nenhum.
    - `call_coberta`, `put_protecao` e `opcao_a_descoberto` continuam com
      método e corpo IDÊNTICOS aos de hoje (deep-equal contra os mesmos
      literais dos casos 1/2/4 do arquivo) — nenhuma regressão nos três
      caminhos que já funcionam.
    - `optionsCuradoriaAbrirCollar` existe nos DOIS stores de
      `persistence.js`, e o ramo sem sessão do `deviceStore` lança erro
      nomeado em vez de reimplementar a estrutura localmente.
  </behavior>
  <action>
`web/src/api.js`: acrescentar, ao lado de `optionsAbrirCollar` (linha ~331),
`optionsCuradoriaAbrirCollar: (body) => req("POST", "/api/options/curadoria/abrir-collar", body)`.
Comentário curto dizendo que é a rota do candidato CURADO (re-derivação pelo
motor da curadoria) e que `optionsAbrirCollar` continua servindo a proposta
única. Nome com prefixo `options` para ficar com os outros métodos de EXECUÇÃO
(o `opcoesCuradoria` vizinho é leitura); `Curadoria` no meio para não colidir
como substring com os guardiões existentes de `optionsAbrirCollar`.

`web/src/persistence.js`: adicionar `optionsCuradoriaAbrirCollar` nos DOIS
stores — paridade é guardrail do repositório, não opcional.
  - `serverStore` (~linha 327): `(body) => api.optionsCuradoriaAbrirCollar(body)`.
  - `deviceStore` (~linha 1619): espelho EXATO de `optionsAbrirCollar` — com
    sessão delega, `_adotarCarteiraDoServidor(r)`, `write()`, devolve `pub()`
    com `premiosUsados`; sem sessão lança erro nomeado. O motivo é o mesmo já
    escrito ali (T-17-25): a atomicidade das duas pernas sob `ORDER_LOCK` e a
    re-derivação server-side não existem no aparelho, e reimplementá-las criaria
    um segundo motor divergente. Aqui o motivo é ainda mais forte — a
    re-derivação pela varredura de curadoria é a própria defesa da rota.

`web/src/opcoes/executarCandidato.js`, ramo `tipo === "collar"`:
  - `exigirCampos(cand, ["ticker", "contratos", "idCandidato"], "collar")` —
    `expiration` sai da lista.
  - body: `{ underlying: cand.ticker, idCandidato: cand.idCandidato,
    pernasContratos, contratos: cand.contratos }`, mantendo o `map` que copia
    SÓ `contractSymbol` e `lado` de cada perna.
  - `metodo: "optionsCuradoriaAbrirCollar"`.
  - Comentário datado explicando a troca: o corpo antigo ia para
    `/api/options/lastreada/abrir-collar`, que re-deriva por
    `opcoes_lastreadas.propor()` e 409ava todo collar curado quando a leitura
    técnica não endossava; a rota nova re-deriva pelo motor que gerou o card, e
    `idCandidato` é a chave dessa re-derivação. `expiration` saiu do corpo
    porque o `idCandidato` já a carrega e duas fontes para o mesmo campo é como
    elas divergem.
  - As três regras não-negociáveis do topo do módulo continuam: zero aritmética
    financeira, zero composição de mensagem de erro, `aceitaLiquidezDificil` só
    por identidade. Atualize o cabeçalho do módulo: ele hoje afirma "ZERO método
    novo de store" — **reversão deliberada, com nota datada (2026-09-15) e
    motivo**, nunca apagar a frase antiga em silêncio (guardrail do repositório).

`web/tests/test_executar_candidato.mjs`: atualizar os casos (3) e (5), que
comparam o corpo do collar por deep-equal, com **nota datada explicando a
reversão** (o guardião não se apaga: ele muda com a razão escrita). Acrescentar
o caso novo "collar sem idCandidato lança e não chama store".

MAIS DUAS ATUALIZAÇÕES NO MESMO ARQUIVO, achadas pelo plan-checker — não são
opcionais e não estão nos casos (3)/(5): (a) `storeEspiao()` (~linhas 62-70)
declara `optionsAbrirCollar` como chave do espião; (b) o bloco de asserção de
despacho sem rótulo (~linhas 150-153) faz
`executarCandidato(collar, { store: espiao2, ... })`, que internamente chama
`store[metodo](body)`. Com o método renomeado para
`optionsCuradoriaAbrirCollar`, o espião não tem a chave e isso vira
`TypeError` SÍNCRONO — o script inteiro quebra em vez de falhar uma asserção,
num ponto que os casos (3)/(5) não cobrem. Atualize as duas para o nome novo.

`web/tests/test_opcoes_collar_ui.mjs`: espelhar os guardiões de paridade de
~205-219 para `optionsCuradoriaAbrirCollar` (existe nos dois stores; existe
dentro do bloco de `deviceStore`; ramo sem sessão lança).

NÃO toque em `App.jsx` nesta task: `A.executarCandidatoCurado` já delega ao
módulo e não conhece nome de método.
  </action>
  <verify>
    <automated>cd web && node tests/test_executar_candidato.mjs && node tests/test_opcoes_collar_ui.mjs && node tests/test_fase3_paridade_stores_generica.mjs && node tests/test_api_parity.mjs && npx vite build</automated>
  </verify>
  <done>O collar curado resolve para `optionsCuradoriaAbrirCollar` com `idCandidato` no corpo e sem `expiration`; os outros três tipos têm corpo byte a byte igual ao de antes; o método existe nos dois stores; `vite build` verde.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Rótulo próprio para o prêmio em reais no painel de confirmação inline</name>
  <files>web/src/copy.js, web/src/App.jsx, web/tests/test_curadoria_ui.mjs</files>
  <behavior>
    - `COPY.estudo.curadoriaPremioRotulo` e `COPY.operador.curadoriaPremioRotulo`
      existem, são strings, e são DIFERENTES de `curadoriaRazaoRotulo` no mesmo
      modo.
    - O painel inline de `CuradoriaEstruturas` usa `cp.curadoriaPremioRotulo` ao
      lado de `money(item.premioTotal)`; `cp.curadoriaRazaoRotulo` continua
      aparecendo **uma única vez** no componente — no card, ao lado de
      `item.razao.toFixed(2)`.
    - Nenhuma copy nova contém as palavras proibidas já travadas pela regra (8)
      ("garantido", "lucro garantido", "sem risco", "certeza") nem as
      strings-âncora do guardrail CVM.
    - A lista `CHAVES` do guardião sobe de 25 para 26, com nota datada.
  </behavior>
  <action>
O defeito: no painel de confirmação inline (`web/src/App.jsx:4313-4314`,
introduzido pela quick 260915-j5l) a linha do prêmio usa
`cp.curadoriaRazaoRotulo` — que é "prêmio / perda máxima" (Operador,
`copy.js:1148`) / "prêmio sobre perda máxima" (Estudo, `copy.js:623`), ou seja o
rótulo da RAZÃO — exibindo `money(item.premioTotal)`, que é o PRÊMIO em reais.
Em produção o painel mostrou "prêmio / perda máxima  R$ 847,00" enquanto o card
logo acima mostrava "prêmio / perda máxima: 77.00". Mesmo rótulo, dois números
diferentes, na mesma tela — num app financeiro isso é defeito sério
(princípio 4 do `CLAUDE.md`).

`web/src/copy.js` — chave NOVA nos DOIS modos (paridade de conjunto já é
testada), inserida junto de `curadoriaRazaoRotulo`/`curadoriaRazaoAjuda` em cada
bloco:
  - Estudo (`COPY.estudo`, bloco ~623):
    `curadoriaPremioRotulo: "prêmio líquido (positivo você recebe, negativo você paga)"`
    — o modo Estudo explica o sinal, que é justamente o que confunde em put de
    proteção e collar de débito (a mesma assimetria já documentada em
    `opcoes_curadoria.py:341-343`).
  - Operador (`COPY.operador`, bloco ~1148): `curadoriaPremioRotulo: "prêmio líquido"`
    — mesa fala curto; o sinal já está no número.
  Comentário datado acima das chaves registrando o defeito corrigido e a razão
  de existir uma chave separada. **Não escreva "trava protetora" nem "abate o
  custo" em nenhum lugar deste arquivo, inclusive em comentário** —
  `test_opcoes_collar_vocab.py::test_nenhum_arquivo_front_compoe_manchete_do_collar`
  lê o texto CRU de `web/src/*.js`/`*.jsx`, comentário incluso (achado Rule 1 das
  duas quicks anteriores).

`web/src/App.jsx:4313`: trocar `{cp.curadoriaRazaoRotulo}` por
`{cp.curadoriaPremioRotulo}` na linha do painel. **Só isso** — não acrescente uma
linha de razão ao painel, não reordene o bloco, não mexa em perda máxima/
breakeven. O card continua exibindo a razão como hoje (linha 4297).

`web/tests/test_curadoria_ui.mjs`:
  - `CHAVES` (linha 135) ganha `"curadoriaPremioRotulo"`; os dois `ok(...)` que
    citam "25 chaves" passam a citar 26, e a NOTA de linhas 131-134 ganha a
    entrada datada (2026-09-15, quick 260915-ndt) explicando por que subiu.
  - Regra (23) NOVA: no painel inline, o rótulo ao lado de `money(item.premioTotal)`
    é `cp.curadoriaPremioRotulo` — prova POSICIONAL (mesma técnica da regra 14):
    extraia a fatia do componente e assert que `curadoriaPremioRotulo` aparece
    antes de `money(item.premioTotal)` dentro da mesma linha/bloco flex.
  - Regra (24) NOVA: `cp.curadoriaRazaoRotulo` aparece **exatamente uma vez** em
    `CuradoriaEstruturas` — é a regressão que este plano fecha (dois usos =
    rótulo da razão de volta sobre um número que não é razão).
  - Regra (25) NOVA: `COPY.estudo.curadoriaPremioRotulo !== COPY.estudo.curadoriaRazaoRotulo`
    e o mesmo em `operador` — rótulos iguais para números diferentes é
    exatamente o defeito.
  </action>
  <verify>
    <automated>cd web && node tests/test_curadoria_ui.mjs && npx vite build && cd ../server && .venv/bin/python -m pytest tests/test_opcoes_collar_vocab.py -q</automated>
  </verify>
  <done>O painel mostra o prêmio em reais sob um rótulo próprio nos dois modos, a razão continua com o rótulo da razão só no card, e o guardião CVM segue verde.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| cliente → `POST /api/options/curadoria/abrir-collar` | Corpo inteiramente não confiável; é a superfície nova desta mudança |
| rota → `opcoes_curadoria` (varredura) | Fronteira interna: é aqui que a verdade sobre contratos/prêmios/contratos é produzida |
| rota → `store.abrir_collar` | Escrita em caixa/posição sob `ORDER_LOCK` |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-NDT-01 | Tampering | corpo da rota nova (prêmio/strike/contratos) | mitigate | Nada do corpo vira número executado: tudo sai do candidato re-derivado; cross-check de `contratos` e `{contractSymbol: lado}` → 409; guardião estrutural por `inspect.getsource` provando que a rota não lê `premioUnitario`/`strike` de `body` |
| T-NDT-02 | Elevation of Privilege | `permitir_a_descoberto` na rota nova | mitigate | `False` FIXO no código, nunca do corpo nem da config; além disso a rota só aceita `tipo == "collar"` — o gate da Fase 29 (`store.buy_option`) não ganha caminho paralelo |
| T-NDT-03 | Elevation of Privilege | Modo Estudo tentando executar | mitigate | 403 como PRIMEIRA checagem, antes de qualquer rede; teste com bomba em `get_options` |
| T-NDT-04 | Tampering | consentimento de liquidez (`aceitaLiquidezDificil`) | mitigate | Faixa lida do candidato RE-DERIVADO (`p["liquidez"]["faixa"]`), nunca do corpo; destrave só por `is True` (identidade); SEM MERCADO é incondicional |
| T-NDT-05 | Repudiation / Integrity | meia estrutura aberta (uma perna só) | mitigate | Execução inalterada via `store.abrir_collar` sob `ORDER_LOCK` (tudo-ou-nada); caso de teste de caixa insuficiente assertando `optionPositions` vazio |
| T-NDT-06 | Information Disclosure | mensagem de erro revelando estado de outra conta | accept | Todas as mensagens são as já existentes das rotas irmãs, escopadas por `current_scope`; nenhuma nomeia dado de terceiro |
| T-NDT-07 | Denial of Service | custo de rede da re-derivação | mitigate | A rota varre UMA posição (até 2 `get_options` + 1 `get_quote`), nunca a carteira; cache de 300s do provedor absorve o clique logo após ver a lista |
| T-NDT-SC | Tampering | npm/pip/cargo installs | mitigate | Nenhum pacote novo neste plano — se algum install aparecer, pare e escale |
</threat_model>

<verification>
Suíte canônica (as DUAS suítes — `scripts/test.sh` sozinho é meia baseline e não
conta):

```
bash scripts/executar.sh --testes
```

Front editado → build obrigatório (grep e teste estático não pegam erro de
sintaxe JS):

```
cd web && npx vite build
```

Baseline a declarar no SUMMARY: rode a suíte canônica ANTES da Task 1 e registre
os números; ao final, o delta de pytest e de `.mjs` tem que ser exatamente o
número de casos criados. **Não rode a suíte canônica mais de duas vezes** (uma
baseline, uma final) — as verificações por task acima são dirigidas de propósito,
para não queimar contexto.

Prova negativa obrigatória (esta fase não passa por `gsd-plan-checker`): APAGUE
(não comente) o cross-check de `{contractSymbol: lado}` da rota nova, rode
`pytest tests/test_curadoria_collar_rota.py -q`, confirme que os casos de
adulteração CAEM de verdade, e reverta com `git diff` limpo. Um guardião que não
falha quando a defesa some é guardião vazio.

**NÃO publicar.** Nada de `scripts/bump.sh`, nada de `scripts/publicar-web.sh`,
nada de push. Verificação ao vivo e publicação são do orquestrador. Lembre no
SUMMARY que esta mudança tem DUAS superfícies (backend precisa de deploy com bump
manual de `SERVER_BUILD_ID`; front precisa de `bump.sh` + `publicar-web.sh`) e
que o backend tem de ir PRIMEIRO — front novo contra backend velho chamaria uma
rota que o servidor não tem (404), trocando um 409 por um erro pior.
</verification>

<success_criteria>
- Um collar da lista curada executa e abre posição real quando
  `opcoes_lastreadas.propor()` NÃO endossa collar — provado no MESMO teste que
  mostra a rota antiga devolvendo 409 no mesmo cenário.
- Corpo adulterado (idCandidato, perna, lado, contratos) devolve 409 e não abre
  nenhuma perna.
- Venda coberta, put de proteção e opção a descoberto da lista curada continuam
  com método e corpo idênticos aos de hoje; `main.py:3566` e `main.py:3017` não
  foram tocados.
- `POST /api/options/lastreada/abrir-collar` segue existindo, com o gate do
  `propor()` intacto e seus guardiões passando sem edição.
- O prêmio em reais e a razão têm rótulos diferentes, nos dois modos.
- `bash scripts/executar.sh --testes` verde nas duas suítes; `npx vite build`
  verde; guardião CVM `test_opcoes_collar_vocab.py` verde.
- Nada publicado, nada empurrado a origin.
</success_criteria>

<output>
Create `.planning/quick/260915-ndt-re-derivar-execucao-de-candidato-curado-/260915-ndt-SUMMARY.md` when done.

No SUMMARY, registre obrigatoriamente: (1) os números de baseline e final das
duas suítes, com o delta explicado caso a caso; (2) o resultado da prova negativa
(comando, saída real, confirmação de reversão limpa); (3) que a decisão "rota
nova, não flag" segue o precedente ADR-026 Decisão 1 — e considere se
`docs/adr/026-*` merece uma nota de extensão (não crie ADR novo sem pedir);
(4) as duas publicações pendentes e a ordem entre elas.
</output>
