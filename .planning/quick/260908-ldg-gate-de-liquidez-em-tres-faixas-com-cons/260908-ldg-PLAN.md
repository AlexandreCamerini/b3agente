---
quick_id: 260908-ldg
phase: quick-260908-ldg
plan: 01
type: execute
wave: 1
depends_on: []
date: 2026-09-08
status: planned
depende_de: 260908-dnl (a recalibração de liquidity_score que tornou as faixas úteis)
autonomous: true
requirements: [D-01, D-02, D-03, D-04, D-05, D-06, D-07, D-08, D-09]
files_modified:
  - server/app/options_quant.py
  - server/app/opcoes_motor.py
  - server/app/opcoes_lastreadas.py
  - server/app/skill_ref.py
  - server/app/options_api.py
  - server/app/main.py
  - server/app/conceitos.py
  - server/tests/test_opcoes_motor.py
  - server/tests/test_opcoes_lastreadas_proposta.py
  - server/tests/test_liquidity_score_mydata.py
  - server/tests/test_faixas_liquidez.py
  - server/tests/test_gate_liquidez_rotas.py
  - server/tests/test_conceito_liquidez_opcao.py
  - web/src/finance.js
  - web/src/App.jsx
  - web/src/copy.js
  - web/src/persistence.js
  - web/tests/test_faixa_liquidez_ui.mjs

must_haves:
  truths:
    - "O usuário vê a faixa de liquidez (NEGOCIÁVEL / DIFÍCIL / SEM MERCADO) da estrutura proposta, com o score e os números que a produziram."
    - "Quando a pior perna é DIFÍCIL, o usuário é obrigado a consentir explicitamente antes de a ordem sair — com texto vindo do motor, nunca composto no front."
    - "Quando a pior perna é SEM MERCADO, o servidor recusa a abertura e nenhuma flag do cliente destrava."
    - "O motor nunca oferece um contrato DIFÍCIL quando existe um NEGOCIÁVEL elegível na mesma cadeia."
    - "Um ativo cujo melhor contrato é SEM MERCADO cai no estado vazio existente, com o texto nomeando a faixa — nunca uma caixa em branco."
    - "No Modo Estudo o chip de liquidez abre um verbete determinístico que explica a faixa com os números daquele card, sem custo de LLM."
    - "Nenhum caminho automático (agente autônomo) abre estrutura de opção — provado por guardião estrutural, não por leitura."
  artifacts:
    - path: "server/app/options_quant.py"
      provides: "Fonte ÚNICA dos dois limiares (55/30) + faixa_de_liquidez(score)"
      contains: "def faixa_de_liquidez"
    - path: "server/app/opcoes_motor.py"
      provides: "rastrear() em duas passadas; LIQUIDEZ_MINIMA removida"
      contains: "faixa_de_liquidez"
    - path: "server/app/opcoes_lastreadas.py"
      provides: "proposta.liquidez com faixa/volume/spreadPct/aviso; _label_liquidez removida"
      contains: "\"aviso\""
    - path: "server/app/skill_ref.py"
      provides: "Frase de consentimento liquidez_dificil nos DOIS modos + fragmentos factuais"
      contains: "liquidez_dificil"
    - path: "server/app/conceitos.py"
      provides: "Verbete determinístico liquidez-opcao"
      contains: "liquidez-opcao"
    - path: "web/src/finance.js"
      provides: "faixaDeLiquidez(score) — espelho declarado de options_quant"
      contains: "faixaDeLiquidez"
    - path: "server/tests/test_faixas_liquidez.py"
      provides: "Guardião das duas passadas + campos novos + fixtures reais de 2026-09-08"
    - path: "server/tests/test_gate_liquidez_rotas.py"
      provides: "Guardião das recusas de /abrir e /abrir-collar e do gate com faixa"
    - path: "web/tests/test_faixa_liquidez_ui.mjs"
      provides: "Guardião do confirm de consentimento, da paridade dos stores e do espelho 55/30"
  key_links:
    - from: "server/app/opcoes_motor.rastrear"
      to: "server/app/options_quant.faixa_de_liquidez"
      via: "duas passadas com os limiares centralizados"
      pattern: "LIQUIDEZ_NEGOCIAVEL|LIQUIDEZ_DIFICIL"
    - from: "server/app/main.options_lastreada_abrir"
      to: "body.aceitaLiquidezDificil"
      via: "recusa 400 quando a faixa é DIFÍCIL sem consentimento"
      pattern: "aceitaLiquidezDificil"
    - from: "web/src/App.jsx"
      to: "proposta.liquidez.aviso"
      via: "window.confirm exibindo o texto do motor verbatim"
      pattern: "window\\.confirm\\(p\\.liquidez\\.aviso\\)"
    - from: "web/src/App.jsx (chip liquidez)"
      to: "conceitos.CONCEITOS['liquidez-opcao']"
      via: "A.abrirVerbete"
      pattern: "abrirVerbete\\(\"liquidez-opcao\""
    - from: "web/src/persistence.js deviceStore"
      to: "faixaDeLiquidez"
      via: "ramo offline aplica a mesma régua do servidor"
      pattern: "faixaDeLiquidez"
---

<objective>
Trocar o corte binário de liquidez de opção (score ≥ 40 existe / < 40 não
existe) pelas três faixas que a UI já nomeia (NEGOCIÁVEL ≥ 55, DIFÍCIL 30-54,
SEM MERCADO < 30), com comportamento distinto em cada ponto onde a nota é
usada: descoberta, seleção pelo motor e execução no Modo Operador.

Purpose: hoje o produto esconde a diferença entre "líquido" e "quase sem
mercado" atrás de um booleano, e executa os dois igual. Com a régua de três
faixas o usuário VÊ o grau de liquidez e CONSENTE quando ela é ruim — e o
simulador nunca finge que uma ordem seria atendida ao último preço num
contrato que negociou 400 unidades no dia (CLAUDE.md princípios 4, 5 e 9).

Output: régua centralizada em `options_quant`, `rastrear()` em duas passadas,
`proposta.liquidez` com faixa/volume/spread/aviso, consentimento exigido pelo
SERVIDOR nas duas rotas de abertura, gate de descoberta em três faixas,
verbete didático "liquidez de opção" e os guardiões correspondentes.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@CLAUDE.md
@.planning/quick/260908-ldg-gate-de-liquidez-em-tres-faixas-com-cons/260908-ldg-CONTEXT.md
@.claude/skills/didatica-boris/SKILL.md
@docs/MEDICAO-gate-liquidez-mydata-2026-09-08.md

@server/app/options_quant.py
@server/app/opcoes_motor.py
@server/app/opcoes_lastreadas.py
@server/app/options_api.py
@server/app/conceitos.py
</context>

<measured_facts>
Medição feita pelo planner em 2026-09-08 contra as 20 cadeias reais de
produção (`$TMPDIR/.../scratchpad/chains/*.json`, não versionadas). Estes
números são o contexto que dispensa o executor de remedir:

**Distribuição das faixas — 592 contratos:**

| faixa | contratos | % |
|---|---|---|
| NEGOCIÁVEL (≥55) | 282 | 47,6% |
| DIFÍCIL (30-54) | 227 | 38,3% |
| SEM MERCADO (<30) | 83 | 14,0% |

Com o corte atual de 40, 461/592 passavam. A faixa 30-39 acrescenta 48
contratos que hoje somem — e a faixa 40-54 (179 contratos) passa a exigir
consentimento onde hoje executa em silêncio.

**Tickers que provam a segunda passada:** RADL3 tem 0 NEGOCIÁVEL, 5 DIFÍCIL e
5 SEM MERCADO — sem a segunda passada, RADL3 nunca teria proposta. ELET3 e
JBSS3 vieram com cadeia vazia (nem uma coisa nem outra).

**Fixtures reais para os guardiões** (`liquidity_score(volume, oi, bid, ask)`):

| contrato real | args | score | spreadPct | faixa |
|---|---|---|---|---|
| ABEVI147W2 | (21100, None, 1.04, 0.0) | 66,5 | None | NEGOCIÁVEL |
| PRIOI650W2 | (5700, None, 0.0, 1.59) | 55,1 | None | NEGOCIÁVEL (fronteira) |
| ABEVI160W2 | (4800, None, 0.01, 0.16) | 48,6 | 176,47 | DIFÍCIL (com spread medido) |
| ABEVI165W2 | (2000, None, 0.0, 0.0) | 46,0 | None | DIFÍCIL (sem livro) |
| ITSAI137W2 | (400, None, 0.0, 0.0) | 32,1 | None | DIFÍCIL (fronteira baixa) |
| B3SAI167W2 | (300, None, 0.0, 0.0) | 29,6 | None | SEM MERCADO (topo) |
| RADLU194W2 | (100, None, 0.0, 0.0) | 20,1 | None | SEM MERCADO |

**Fixtures dos testes existentes, já classificadas** (nenhuma delas quebra):
`_cadeia_base()` de `test_opcoes_motor` (5000/1.48/1.52) = **79,0 NEGOCIÁVEL**;
o caso mydata de `test_rastrear_inclui_caso_real_mydata_sem_open_interest`
(100/1.48/1.52) = **45,1 DIFÍCIL** (segue selecionado pela SEGUNDA passada, pois
a cadeia daquele teste tem um contrato só); o excluído (10, sem livro) = **0,8
SEM MERCADO**; as pernas de `test_opcoes_collar` = **85,0** (call) e **71,0**
(put), ambas NEGOCIÁVEL.
</measured_facts>

<guardioes_que_viram>
Guardião NÃO se apaga (CLAUDE.md). Cada um abaixo é ATUALIZADO com nota
datada "2026-09-08, quick 260908-ldg", nunca deletado nem enfraquecido.

| # | Arquivo:linha | O que afirma hoje | Por que vira |
|---|---|---|---|
| G1 | `server/tests/test_opcoes_lastreadas_proposta.py:309` | `set(p["liquidez"].keys()) == {"score","label"}` | O dict ganha `faixa`/`volume`/`spreadPct`/`aviso` e `label` é renomeado para `faixa`. Vira igualdade exata contra o novo conjunto de 5 chaves — continua sendo igualdade exata (não vira `>=`), senão deixaria de ser guardião. |
| G2 | `server/tests/test_opcoes_motor.py:167-202` (`test_corte_de_liquidez_tem_fonte_unica`) | `not hasattr(opcoes_lastreadas, "_LIQUIDEZ_MINIMA"/"_candidato_valido")` + `propor()` nunca passa `liquidez_minima` | Continua valendo e é REFORÇADO: acrescenta `not hasattr(opcoes_lastreadas, "_label_liquidez")` e `not hasattr(opcoes_motor, "LIQUIDEZ_MINIMA")` — a fonte única passa a ser `options_quant.LIQUIDEZ_NEGOCIAVEL/LIQUIDEZ_DIFICIL`. |
| G3 | `server/tests/test_opcoes_motor.py:10` (docstring) | "a régua de seleção já em produção (liquidez >= 40 + strike extremo)" | Passa a descrever as duas passadas. |
| G4 | `server/tests/test_liquidity_score_mydata.py:20` | `CORTE = 40  # options_api.liquidity_gate e opcoes_motor.LIQUIDEZ_MINIMA` | **Os dois consumidores citados deixam de existir.** As asserções continuam numericamente verdadeiras, mas o comentário vira mentira e DUAS delas mudam de significado (ver G5). Vira `PISO_DIFICIL = 30` / `PISO_NEGOCIAVEL = 55` com nota datada explicando a migração do corte único. |
| G5 | `test_liquidity_score_mydata.py:56-59` (`test_volume_500_com_um_lado_zerado_reprova`) e `:75-81` (`test_piso_sem_livro_e_mil_unidades`, linha `_s(900) < CORTE`) | Nomes dizem "reprova"; `_s(500)=34,0` e `_s(900)=39,1` | Ambos passam a ser **DIFÍCIL** (≥30) — aparecem com consentimento em vez de sumir. Renomear para `..._cai_em_dificil_nao_em_negociavel` e reancorar: `PISO_DIFICIL <= _s(500) < PISO_NEGOCIAVEL`. Nota datada obrigatória: esta é a mudança de comportamento mais afiada da task. |
| G6 | `test_opcoes_motor.py:112-117` (`test_rastrear_inclui_caso_real_mydata_sem_open_interest`) | Nome sugere contrato aprovado | Score real 45,1 = DIFÍCIL. Segue passando (segunda passada), mas ganha asserção explícita da faixa, senão o teste vira falso-verde sobre QUAL passada o selecionou. |
| G7 | `server/tests/test_opcoes_collar.py:373-395` | `liquidez.score == menor` e ordem dos chips | Sem mudança de valor (85/71, ambos NEGOCIÁVEL), mas acrescentar asserção de `faixa == "NEGOCIÁVEL"` para travar que o collar leva a faixa da PIOR perna. |
| G8 | `server/tests/test_opcoes_collar_vocab.py:74` (`test_vocab_chaves_de_operacao_existem_nos_dois_modos_com_collar`) | Paridade de chaves entre `operador` e `educacional` | Não muda de forma, mas TRAVA a chave nova: `liquidez_dificil` entra nos DOIS modos ou o guardião fica vermelho. Não editar — só obedecer. |
| G9 | `web/tests/test_copy_theme.mjs:27` | Chaves espelhadas em `COPY.estudo`/`COPY.operador` | Idem G8: `tiraOpcoesSemMercado` entra nos DOIS ramos. Não editar. |
| G10 | `web/tests/test_carteira_opcoes_tira.mjs:50-63` | Lista de chaves e "SemCobertura ≠ SemSetup" nos dois modos | A chave nova entra na lista e ganha as mesmas asserções de distinção. |
| G11 | `web/tests/test_opcoes_proposta_ui.mjs:19-29,86-88` | `CHAVES_LASTREADAS` + `window.confirm(cp.confirmAbrirCoberta(` existe | Continua valendo; ganha a asserção de ORDEM (o confirm de liquidez vem ANTES do confirm da estrutura). |
| G12 | `web/tests/test_opcoes_collar_ui.mjs:117-120` | `window.confirm(cp.confirmAbrirCollar(` aparece exatamente 1x por handler | **Frágil por construção**: o handler passa a ter DOIS `window.confirm`. A contagem de `confirmAbrirCollar` continua 1 (o novo usa `p.liquidez.aviso`, não `cp.`), então o guardião passa — verificar isso explicitamente e acrescentar a asserção do segundo confirm em vez de confiar na sorte. |

**Comentários/docstrings stale a corrigir junto (não são guardiões, mas mentem):**
`server/app/opcoes_lastreadas.py:43` ("liquidez >= 40"), `:255-257` (comentário
sobre o default de `rastrear`), `server/app/options_quant.py:105-106`
(docstring: "o corte de aprovação é 40"), `server/app/options_provider_mock.py:39`
("score >= 40").
</guardioes_que_viram>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Régua centralizada, duas passadas e os campos novos de `liquidez`</name>
  <files>server/app/options_quant.py, server/app/opcoes_motor.py, server/app/opcoes_lastreadas.py, server/app/skill_ref.py, server/tests/test_faixas_liquidez.py, server/tests/test_opcoes_motor.py, server/tests/test_opcoes_lastreadas_proposta.py, server/tests/test_liquidity_score_mydata.py, server/tests/test_opcoes_collar.py</files>
  <behavior>
    - `faixa_de_liquidez(66.5) == "NEGOCIÁVEL"`; `(55.0) == "NEGOCIÁVEL"`; `(54.9) == "DIFÍCIL"`; `(30.0) == "DIFÍCIL"`; `(29.6) == "SEM MERCADO"`; `(None)` e `(-1)` → `"SEM MERCADO"` (nunca exceção).
    - `rastrear` numa cadeia com um NEGOCIÁVEL (66,5) e um DIFÍCIL (48,6) de strike "melhor" devolve o NEGOCIÁVEL — a segunda passada nem roda.
    - `rastrear` numa cadeia SÓ com DIFÍCIL (fixture RADL3: 46,0 / 43,5 / 32,1) devolve o DIFÍCIL pelo critério de strike.
    - `rastrear` com `n=3` numa cadeia mista devolve SÓ os NEGOCIÁVEL, mesmo que sobrem vagas — nunca completa a lista com DIFÍCIL.
    - `rastrear` numa cadeia só com SEM MERCADO (29,6 / 20,1) devolve `[]`.
    - `rastrear(..., {"liquidez_minima": 99})` continua fazendo UMA passada nesse limiar e devolve `[]` (override explícito não vira duas passadas).
    - `propor()` sobre contrato DIFÍCIL: `proposta["liquidez"] == {"score","faixa","volume","spreadPct","aviso"}` com `faixa == "DIFÍCIL"` e `aviso` string não-vazia contendo o score arredondado, o volume e a cláusula de livro.
    - `propor()` sobre contrato NEGOCIÁVEL: mesmo conjunto de chaves, `aviso is None` (nunca `""`).
    - Contrato com `spreadPct is None` → o `aviso` diz "sem livro publicado" e **nunca** "0%".
    - Contrato com `volume` 0/None mas OI alto (caminho Yahoo) → o `aviso` diz "sem negócio registrado hoje", nunca "0 unidades".
    - Collar cuja call é NEGOCIÁVEL e a put é DIFÍCIL: `liquidez.faixa == "DIFÍCIL"` e `volume`/`spreadPct` são os da PUT (a pior perna), não os da call.
    - `skill_ref.OPCOES_LASTREADAS["operador"]["liquidez_dificil"] != ...["educacional"]["liquidez_dificil"]` e nenhuma das duas cai no fallback `sem_setup`.
    - Nenhum módulo de `server/app/*.py` fora de `skill_ref.py` contém as strings-âncora `"sem livro publicado"` / `"poderia não ser atendida"`.
  </behavior>
  <action>
Implementa D-01, D-02, D-04.

**(a) `server/app/options_quant.py` — fonte ÚNICA da escala.** Acrescenta, ao
lado de `liquidity_score` (cuja fórmula NÃO se toca — scope fence), as
constantes `LIQUIDEZ_NEGOCIAVEL = 55` e `LIQUIDEZ_DIFICIL = 30`, os três
rótulos como constantes (`FAIXA_NEGOCIAVEL`, `FAIXA_DIFICIL`,
`FAIXA_SEM_MERCADO`) e `faixa_de_liquidez(score) -> str`. Score não-numérico
ou negativo devolve `FAIXA_SEM_MERCADO` — degradação definida, nunca exceção
(mesmo padrão de `_num` em `conceitos.py`). Atualiza a docstring de
`liquidity_score` (linhas 105-106): o corte único de 40 deixou de existir;
citar as duas fronteiras e a quick 260908-ldg. Este módulo é a escolha certa
porque `opcoes_motor`, `opcoes_lastreadas` e `options_api` já o importam — o
único ponto que os três alcançam sem criar import novo entre camadas.

**(b) `server/app/opcoes_motor.py` — duas passadas.** Apaga
`LIQUIDEZ_MINIMA = 40` (D-01: "o número que morre"). `rastrear()` passa a
executar, quando `filtros` NÃO traz `liquidez_minima`: primeira passada
filtrando `faixa_de_liquidez(score) == FAIXA_NEGOCIAVEL`; se e SÓ SE a lista
sair vazia, segunda passada com `FAIXA_DIFICIL`. Nunca concatena as duas
listas — a ordenação por strike e o corte por `n` acontecem DENTRO da passada
vencedora. Quando `filtros["liquidez_minima"]` vem explícito, mantém o
comportamento de hoje: UMA passada naquele limiar (é o que o guardião
`test_rastrear_liquidez_minima_explicita_sobrescreve_default` trava, e é a
semântica correta de um override). `_candidato_valido` continua recebendo um
piso numérico — o que muda é quem o escolhe. Atualiza o comentário do bloco
de docstring que ainda descreve o corte único.

**(c) `server/app/opcoes_lastreadas.py` — o dado que sustenta o consentimento.**
Apaga `_label_liquidez` (a escala agora vive em `options_quant`; manter um
alias local recriaria a duplicação que a própria docstring da função proibia)
e importa `faixa_de_liquidez`. Cria um helper privado
`_bloco_liquidez(contrato, liq, modo)` que devolve o dict completo
`{"score", "faixa", "volume", "spreadPct", "aviso"}`:
  - `score` = `liq["score"]`, `spreadPct` = `liq["spreadPct"]` (pode ser
    `None` — nunca 0.0, regra do repositório);
  - `volume` = `contrato.get("volume")` cru (pode ser `None`);
  - `faixa` = `faixa_de_liquidez(score)`;
  - `aviso` = `skill_ref.opcoes_lastreadas_txt(modo, "liquidez_dificil", ...)`
    SOMENTE quando `faixa == FAIXA_DIFICIL`; `None` nas outras duas faixas.
Usa `_bloco_liquidez` nos TRÊS pontos que hoje montam `{"score","label"}`:
`_propor_collar` (linha ~143, com o contrato da perna PIOR — hoje só o
`liq` é guardado em `pior`, é preciso guardar o par contrato+liq),
`propor` (linha ~348) e `proposta_fechar` (linha ~470). Os `chips` passam a
ler `bloco["faixa"]` em vez de `_label_liquidez(...)` — o texto do chip não
muda, a fonte sim.
**`proposta_fechar` recebe os mesmos campos mas NENHUMA rota de fechamento é
bloqueada por faixa** — travar a saída de uma posição em contrato ruim
prenderia o usuário exatamente onde ele mais precisa sair. Registrar esta
decisão em comentário no código, senão a assimetria abrir/fechar parece
esquecimento.

**(d) `server/app/skill_ref.py` — o texto vem do motor.** Acrescenta a chave
`liquidez_dificil` em `OPCOES_LASTREADAS["operador"]` E
`["educacional"]` (guardião G8 exige paridade de chaves). Placeholders:
`{score}`, `{atividade}`, `{livro}`.
  - operador: `"Liquidez DIFÍCIL ({score}/100): {atividade}, {livro}. O preço simulado é o do último negócio; no mercado real sua ordem poderia não ser atendida a esse preço. Continuar?"`
  - educacional (descreve condição, sem verbo de ordem nem "Continuar?"): `"Esta opção tem liquidez DIFÍCIL ({score}/100): {atividade}, {livro}. O preço simulado é o do último negócio — no mercado real, uma ordem a esse preço poderia não ser atendida."`
Acrescenta também `LIQUIDEZ_FRAGMENTOS` (dict de nível de módulo, factual e
igual nos dois modos, mesmo precedente de `HISTORICO["insuficiente"]`):
`atividade` = `"{volume} unidades negociadas hoje"`, `atividade_sem_negocio`
= `"sem negócio registrado hoje"`, `livro` = `"spread {spread}"`,
`livro_ausente` = `"sem livro publicado"`. `_bloco_liquidez` seleciona o
fragmento e interpola — **todo texto visível continua nascendo em
`skill_ref.py`**, o motor só escolhe qual. `{score}` chega como
`str(int(round(score)))` (a frase de referência do CONTEXT diz "38/100", não
"38,60/100"); `{volume}` por `num_br` sem decimais.

**(e) Guardiões.** Cria `server/tests/test_faixas_liquidez.py` com o bloco
`<behavior>` acima, usando as fixtures reais da tabela `<measured_facts>` (os
20 JSONs NÃO são versionados — os números entram como literais com o
`contractSymbol` real no comentário). Atualiza G1, G2, G3, G4, G5, G6 e G7
conforme a tabela `<guardioes_que_viram>`, cada um com nota datada
"2026-09-08, quick 260908-ldg" explicando o que mudou e por quê. Acrescenta o
guardião de âncora (varredura AST de `server/app/*.py`, mesmo padrão de
`test_opcoes_collar_vocab.py:118-127`) provando que "sem livro publicado" e
"poderia não ser atendida" só existem em `skill_ref.py`.
  </action>
  <verify>
    <automated>cd server &amp;&amp; .venv/bin/python -m pytest tests/test_faixas_liquidez.py tests/test_opcoes_motor.py tests/test_opcoes_lastreadas_proposta.py tests/test_opcoes_collar.py tests/test_opcoes_collar_vocab.py tests/test_liquidity_score_mydata.py tests/test_guardrail_imperativo.py -q</automated>
    <automated>cd server &amp;&amp; .venv/bin/python -m pytest -q</automated>
    <automated>grep -rn "LIQUIDEZ_MINIMA\|_label_liquidez" server/app || echo "OK: nenhum dos dois nomes sobreviveu"</automated>
  </verify>
  <done>`options_quant.faixa_de_liquidez` é a única escala do backend; `rastrear()` nunca devolve DIFÍCIL quando existe NEGOCIÁVEL elegível; `proposta.liquidez` traz as 5 chaves em `propor`/`_propor_collar`/`proposta_fechar`; a frase de consentimento existe nos dois modos em `skill_ref`; suíte pytest inteira verde com os 7 guardiões atualizados com nota datada.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Gate de descoberta, recusas do servidor e verbete didático</name>
  <files>server/app/options_api.py, server/app/main.py, server/app/conceitos.py, server/app/options_provider_mock.py, server/tests/test_gate_liquidez_rotas.py, server/tests/test_conceito_liquidez_opcao.py</files>
  <behavior>
    - `GET /api/options/gate/{t}` com melhor contrato 66,5 → `{"liquida": true, "faixa": "NEGOCIÁVEL", "melhorScore": 66.5}`.
    - Melhor contrato 46,0 → `liquida: true`, `faixa: "DIFÍCIL"` (compat: todo consumidor de `opGate.liquida` continua vendo `true`).
    - Melhor contrato 29,6 → `liquida: false`, `faixa: "SEM MERCADO"`, `melhorScore: 29.6`.
    - Cadeia vazia ou degradada → `liquida: false`, `faixa: "SEM MERCADO"`, `melhorScore: null` (nunca 0.0).
    - `POST /api/options/lastreada/abrir` com contrato NEGOCIÁVEL e sem `aceitaLiquidezDificil` → executa normalmente (a flag é ignorada).
    - Mesmo contrato NEGOCIÁVEL com `aceitaLiquidezDificil: true` → executa igual (flag redundante nunca é erro).
    - Contrato DIFÍCIL sem a flag → 400 cuja mensagem nomeia a faixa e diz o que fazer.
    - Contrato DIFÍCIL com `aceitaLiquidezDificil: true` → executa.
    - Contrato SEM MERCADO com `aceitaLiquidezDificil: true` → 400 mesmo assim, mensagem distinta da anterior.
    - `POST /api/options/lastreada/abrir-collar`: as mesmas quatro regras, decididas pela faixa da proposta RE-DERIVADA (`p["liquidez"]["faixa"]`), nunca pelo corpo.
    - `POST /api/options/lastreada/fechar` sobre um contrato SEM MERCADO **continua fechando** — nenhuma trava de faixa na saída.
    - `conceitos.montar("liquidez-opcao", "operador", {...})` devolve os três blocos com o score/faixa/volume/spread daquele card; sem `dados`, o texto genérico não sobra nenhum `{`.
    - `"liquidez-opcao" in conceitos.ids()` e aparece em `conceitos.catalogo()`.
    - `agent.py` não chama `abrir_call_coberta`, `comprar_put_protecao` nem `abrir_collar` — guardião estrutural por AST.
  </behavior>
  <action>
Implementa D-05, D-07, D-08, D-09.

**(a) `options_api.liquidity_gate`.** Substitui o literal `>= 40` (linha 153)
por: calcula o score de todos os contratos, guarda o MAIOR
(`melhorScore`), deriva `faixa = faixa_de_liquidez(melhorScore)` e devolve
`liquida = faixa != FAIXA_SEM_MERCADO` (D-07: DIFÍCIL ou melhor, preservando
todo consumidor de `opGate.liquida`). A resposta ganha `faixa` e
`melhorScore` em TODOS os ramos, inclusive nos dois `return` de degradação
do topo (`QuoteUnavailable` e `providerStatus != "ok"`) — ali `faixa` é
`FAIXA_SEM_MERCADO` e `melhorScore` é `None`, nunca `0.0`. Cadeia sem nenhum
contrato: mesmo tratamento.

**(b) `options_api.analyze_options`, linha 178.** O literal `< 40` é um
SEGUNDO corte solto, fora do quadro do D-01, e sobrevive à morte de
`LIQUIDEZ_MINIMA`. Passa a usar `faixa_de_liquidez`: a bandeira de risco
dispara quando a faixa **não** é NEGOCIÁVEL, e o texto passa a nomear a
faixa (`"Liquidez DIFÍCIL: risco de entrada/saída ruim."` /
`"Liquidez SEM MERCADO: ..."`). Isto ALARGA a bandeira (hoje 40-54 não
avisa nada; passa a avisar) — mudança deliberada, na direção da transparência,
registrada em comentário datado. Se for reprovada na revisão, reverter é uma
linha.

**(c) `main.py`, `options_lastreada_abrir` (~2452).** Depois de localizar
`contrato` na cadeia e validar o prêmio (a rota já faz isso), calcula
`liquidity_score` do contrato e a faixa. Ordem das recusas — SEM MERCADO
primeiro, porque é a incondicional:
  - `SEM MERCADO` → `HTTPException(400, ...)` SEMPRE, sem flag que destrave.
    Mensagem acionável em PT-BR nomeando a faixa e o motivo determinístico
    ("sem negócio no dia não há prêmio real para simular" — CLAUDE.md
    princípio 4).
  - `DIFÍCIL` e `body.get("aceitaLiquidezDificil") is not True` →
    `HTTPException(400, ...)` dizendo que a operação exige confirmação
    explícita de liquidez. Comparação por identidade com `True` (`is not
    True`), não truthiness: `"false"`, `1` e `"sim"` NÃO destravam.
  - `NEGOCIÁVEL` → ignora a flag inteiramente.
Comentário explicando que esta é a mesma disciplina do 403 de Modo Estudo e
da trava de multiperna já presentes na rota: **a UI pode ter bug, o servidor
recusa igual** (anti-padrão "esconder só no front", CLAUDE.md).

**(d) `main.py`, `options_lastreada_abrir_collar` (~2515).** A rota já
re-deriva a proposta e encontra `p` (o candidato collar). Aplica as MESMAS
três regras lendo `p["liquidez"]["faixa"]` — nunca recalculando um score
próprio e nunca lendo faixa do corpo. Posiciona a checagem **depois** do
cross-check de contratos/quantidade (409) e **antes** de
`store.abrir_collar`: um corpo que não confere com a proposta é um erro mais
básico e deve continuar respondendo 409.

**(e) `conceitos.py` — verbete `liquidez-opcao` (D-09).** Entrada nova em
`CONCEITOS` no padrão dos existentes:
  - `titulo`: `{"educacional": "Liquidez de uma opção", "operador": "Liquidez do contrato"}`.
  - `campos`: `("ticker", "faixa", "score", "volume", "spreadPct")`.
  - `naoAcontece` PRIMEIRO (regra do módulo): o app não compra nem vende
    nada; a faixa não prevê preço; consentir em liquidez DIFÍCIL não torna a
    ordem mais provável de ser atendida.
  - `oQueE`: liquidez é quanto o contrato foi de fato negociado e quão
    apertado está o livro; as três faixas e o que cada uma significa para
    quem está simulando; o parágrafo ancorado cita `{faixa}`, `{score}`,
    `{volume}` e `{spreadPct}` do card.
  - `oQueAcontece`: NEGOCIÁVEL o app propõe primeiro; DIFÍCIL só entra
    quando não há NEGOCIÁVEL e exige confirmação; SEM MERCADO não vira
    proposta nenhuma; o preço simulado é sempre o do último negócio.
  - `veja`: `[]` (nenhum conceito existente é irmão direto — link fantasma é
    404 na cara do usuário, regra do módulo).
  Acrescenta em `_FORMATADORES`: `"spreadPct": _pct`, `"score": <formatador
  novo que devolve o inteiro arredondado como str>` e `"volume": <formatador
  de milhar pt-BR>`. Sem eles, `_valores` cai no `str(v)` e imprime "48.6" e
  "4800" com ponto — o guardião
  `test_numeros_do_card_aparecem_formatados_em_pt_br` existe exatamente
  contra isso. NÃO registrar em `SETORES`: o acesso é por chip
  (`A.abrirVerbete`), não por região do card.

**(f) `options_provider_mock.py:39`** — comentário stale citando "score >= 40";
atualizar para as faixas.

**(g) Guardiões novos.** `server/tests/test_gate_liquidez_rotas.py` cobre o
bloco `<behavior>` de gate e das duas rotas de abertura (usando o mesmo
padrão de cliente de teste dos testes de rota existentes) MAIS o guardião
estrutural do agente autônomo (D-08): parse AST de `server/app/agent.py`
provando que nenhuma das três funções de abertura é chamada ali — o grep do
planner confirmou que o agente só LIQUIDA vencidas
(`liquidar_lastreada_vencida`, `agent.py:559`), então este guardião registra
um fato hoje verdadeiro e impede que um caminho automático apareça depois sem
humano para consentir. `server/tests/test_conceito_liquidez_opcao.py` cobre o
verbete.
  </action>
  <verify>
    <automated>cd server &amp;&amp; .venv/bin/python -m pytest tests/test_gate_liquidez_rotas.py tests/test_conceito_liquidez_opcao.py tests/test_conceitos.py tests/test_guardrail_imperativo.py tests/test_didatica_rotas.py tests/test_setores.py -q</automated>
    <automated>cd server &amp;&amp; .venv/bin/python -m pytest -q</automated>
    <automated>grep -rn "score.*&gt;= 40\|&lt; 40" server/app || echo "OK: nenhum literal de corte 40 sobrou em server/app"</automated>
  </verify>
  <done>O gate devolve `faixa`/`melhorScore` nos quatro ramos; as duas rotas de abertura recusam DIFÍCIL sem consentimento e SEM MERCADO sempre; a rota de fechamento segue livre; `liquidez-opcao` está em `conceitos.ids()` com números formatados em pt-BR; o guardião do agente prova que não existe caminho automático de abertura; suíte pytest inteira verde.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Consentimento no front, paridade dos stores, estado vazio e chip→verbete</name>
  <files>web/src/finance.js, web/src/App.jsx, web/src/copy.js, web/src/persistence.js, web/tests/test_faixa_liquidez_ui.mjs, web/tests/test_carteira_opcoes_tira.mjs, web/tests/test_opcoes_proposta_ui.mjs, web/tests/test_opcoes_collar_ui.mjs</files>
  <behavior>
    - `faixaDeLiquidez(66.5) === "NEGOCIÁVEL"`, `(46) === "DIFÍCIL"`, `(29.6) === "SEM MERCADO"`, `(null) === "SEM MERCADO"`.
    - Os dois limiares e os três rótulos do JS são byte-idênticos aos do Python — guardião lê os dois arquivos e compara.
    - Nos DOIS handlers de aceite (`onAbrirLastreada` em AtivoCard, `aceitarCandidato` em PropostaDaPosicao): quando `p.liquidez.faixa === "DIFÍCIL"`, `window.confirm(p.liquidez.aviso)` é chamado ANTES de qualquer `cp.confirmAbrir*`; recusar aborta sem tocar a rede.
    - `faixa === "DIFÍCIL"` sem `aviso` (backend antigo/degradado) → aborta com erro nomeado; o front NUNCA compõe o texto.
    - `faixa === "NEGOCIÁVEL"` → nenhum confirm de liquidez; o fluxo de hoje é byte-idêntico.
    - Corpo enviado às duas rotas carrega `aceitaLiquidezDificil: true` quando e só quando o confirm de liquidez foi aceito.
    - `deviceStore` e `serverStore` aceitam o campo novo; o ramo OFFLINE de `deviceStore.optionsAbrirLastreada` aplica a mesma régua e rejeita SEM MERCADO / DIFÍCIL sem flag com a mesma mensagem do servidor.
    - `cp.tiraOpcoesSemMercado` existe nos dois modos, difere entre eles e difere de `tiraOpcoesSemCobertura`/`tiraOpcoesSemSetup`.
    - `OpcaoContrato` não tem mais os literais 55/30 inline — usa `faixaDeLiquidez`.
    - Nenhum arquivo de `web/src/*.js*` contém "sem livro publicado", "unidades negociadas hoje" ou "poderia não ser atendida".
  </behavior>
  <action>
Implementa D-03, D-06, D-07 (lado do cliente) e o gancho didático do D-09.

**(a) `web/src/finance.js` — espelho declarado.** Exporta
`FAIXA_NEGOCIAVEL_MIN = 55`, `FAIXA_DIFICIL_MIN = 30` e
`faixaDeLiquidez(score)` devolvendo os três rótulos. Comentário no padrão já
usado no arquivo ("espelho de store.py"): **espelho de
`server/app/options_quant.faixa_de_liquidez`**, e o guardião que trava a
paridade. O front precisa da escala porque `/api/options/chain` entrega
`liquidity.score` cru (sem rótulo) e o ramo offline do `deviceStore` decide
sem servidor — não é uma segunda régua, é a mesma régua replicada e testada,
mesma disciplina de `deviceStore` × `store.py`.

**(b) `web/src/App.jsx` — o confirm PRÓPRIO (D-03).** Em `onAbrirLastreada`
(~3446) e em `aceitarCandidato` (~4192), no TOPO de cada handler, antes do
ramo `p.tipo === "collar"` e antes do `if (p.optionType === "call" && ...)`:

```
const liq = p.liquidez || {};
if (liq.faixa === "DIFÍCIL") {
  if (!liq.aviso) return;                     // motor mudo: não inventar texto
  if (!window.confirm(liq.aviso)) return;
  aceita = true;
}
```
`aceita` vira `aceitaLiquidezDificil: aceita` nos corpos de
`A.abrirLastreada(...)` e `A.abrirCollar(...)`. O texto exibido é
`liq.aviso` VERBATIM — nenhuma concatenação, nenhuma chave de `copy.js`
(o guardrail "o front nunca compõe vocabulário" vale aqui como vale para a
manchete). O confirm de liquidez vem PRIMEIRO porque decide se a operação
faz sentido; o da estrutura decide o que ela trava. A put, que hoje não tem
confirm nenhum, passa a ter este quando é DIFÍCIL.

**(c) `web/src/App.jsx` — chip de liquidez → verbete (D-09).** Em
`PropostaLastreada` (~3220) e `CandidatoOpcao` (~4300), o chip de `k ===
"liquidez"` vira um `<button>` acessível (aria-label "O que é liquidez de
opção?", `minHeight: 44px` como o resto dos alvos táteis) que chama
`onVerbeteLiquidez(p)`. `onVerbeteLiquidez` é prop nova, passada por
AtivoCard e por PropostaDaPosicao — os dois já têm `A` em escopo — e faz
`A.abrirVerbete("liquidez-opcao", { ticker, faixa, score, volume, spreadPct })`.
Usar `abrirVerbete` e NÃO `openConceito`/`abrirSetor`: os dois últimos
contaminam métricas que não são desta interação (`coach_tip_shown` e
`gestoUso`) — precedente já registrado em App.jsx:8628. Os outros chips
seguem `<span>`: a afordância nova é só do chip que tem verbete.

**(d) `web/src/App.jsx` — `OpcaoContrato` (3098-3099).** Substitui os
literais 55/30 e os três rótulos inline por `faixaDeLiquidez(liq.score)`; o
mapa de cor continua no componente (cor é tema, não escala).

**(e) `web/src/App.jsx` + `copy.js` — estado vazio da faixa (D-07).**
`OportunidadesOpcoes` (~4088) hoje escolhe entre `tiraOpcoesSemSetup` e
`tiraOpcoesSemCobertura` por `gate.liquida`. Acrescenta o terceiro caso: se
NENHUMA posição tem `gate.liquida` **e** ao menos uma tem
`gate.faixa === "SEM MERCADO"`, exibe `cp.tiraOpcoesSemMercado` — texto que
NOMEIA a faixa em vez de dizer genericamente "sem liquidez suficiente".
Chave nova nos dois ramos de `copy.js` (~253 e ~470), distinta entre modos e
distinta das outras duas (guardiões G9/G10). Estudo = voz de professor,
Operador = voz de mesa; nenhum dos dois usa verbo de ordem.

**(f) `web/src/persistence.js` — paridade dos DOIS stores (D-06).**
`serverStore.optionsAbrirLastreada`/`optionsAbrirCollar` (linhas 270/274)
são delegação pura, então o campo novo já trafega — **mas isso não é a
paridade que importa aqui.** O ramo OFFLINE de
`deviceStore.optionsAbrirLastreada` (a partir da linha ~1244, quando
`!sync.hasSession()`) reimplementa a validação inteira em JS e hoje NÃO tem
régua de liquidez nenhuma: sem esta task ele vira o buraco por onde a
recusa do servidor é contornada. Acrescenta, logo depois da validação de
prêmio e ANTES de qualquer escrita em `doc`, a mesma régua usando
`contrato.liquidity.score` (a rota `/api/options/chain` já enriquece cada
contrato com `liquidity`, `options_api._enrich_contract:87`) e
`faixaDeLiquidez`:
  - `liquidity` ausente/sem score → erro nomeado ("não foi possível medir a
    liquidez deste contrato"), nunca assumir NEGOCIÁVEL — princípio 4;
  - SEM MERCADO → `_registrarRejeicaoLocal` + erro, sempre;
  - DIFÍCIL sem `body.aceitaLiquidezDificil === true` → `_registrarRejeicaoLocal`
    + erro;
  - NEGOCIÁVEL → segue o fluxo de hoje.
As mensagens são as MESMAS do servidor (Task 2c), copiadas literalmente com
comentário apontando a origem — mesma convenção "espelho de store.py" já
usada no arquivo. `optionsAbrirCollar` offline já lança
"exige estar conectado", então nada a fazer lá.

**(g) Guardiões.** Cria `web/tests/test_faixa_liquidez_ui.mjs` cobrindo o
bloco `<behavior>`: paridade dos limiares/rótulos JS×Python (lê os dois
arquivos-fonte), ordem dos dois confirms nos DOIS handlers (regex sobre a
fatia de cada handler, mesmo padrão de `test_opcoes_collar_ui.mjs:117-120`),
`aceitaLiquidezDificil` nos dois corpos, a régua no ramo offline do
`deviceStore`, ausência das strings do motor em `web/src`, e o chip
chamando `abrirVerbete("liquidez-opcao"`. Atualiza G10/G11/G12 conforme a
tabela — em especial confirmar que G12 (`confirmAbrirCollar` exatamente 1x
por handler) continua verde com o segundo `window.confirm` presente, e
acrescentar a asserção positiva do segundo em vez de deixá-la implícita.

**(h) Validação canônica e SUMMARY.** Roda `npx vite build` em `web/` (front
editado — grep e teste estático não pegam erro de sintaxe JSX) e a suíte
canônica `bash scripts/executar.sh --testes` (as DUAS suítes). **NÃO** rodar
`scripts/bump.sh` nem `scripts/publicar-web.sh`, **NÃO** tocar
`server/web_dist` (scope fence): registrar a publicação como pendência
explícita no SUMMARY, junto com o PR #31 que já aguarda promoção.
  </action>
  <verify>
    <automated>cd web &amp;&amp; npx vite build</automated>
    <automated>node web/tests/test_faixa_liquidez_ui.mjs &amp;&amp; node web/tests/test_opcoes_proposta_ui.mjs &amp;&amp; node web/tests/test_opcoes_collar_ui.mjs &amp;&amp; node web/tests/test_carteira_opcoes_tira.mjs &amp;&amp; node web/tests/test_copy_theme.mjs &amp;&amp; node web/tests/test_api_parity.mjs</automated>
    <automated>bash scripts/executar.sh --testes</automated>
    <automated>grep -rn "&gt;= 55\|&gt;= 30" web/src/App.jsx || echo "OK: escala saiu do App.jsx"</automated>
  </verify>
  <done>Os dois handlers de aceite disparam o confirm de liquidez antes do confirm da estrutura e enviam `aceitaLiquidezDificil`; o ramo offline do `deviceStore` aplica a mesma régua do servidor; o chip de liquidez abre o verbete; o estado vazio nomeia SEM MERCADO nos dois modos; `npx vite build` passa e a suíte canônica (pytest + `web/tests/*.mjs`) está verde; SUMMARY escrito com a publicação registrada como pendência.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| cliente (web/iOS) → `POST /api/options/lastreada/abrir*` | O corpo é 100% controlado pelo cliente, inclusive a flag nova de consentimento |
| provedor de mercado (mydata/Yahoo) → motor | `volume`/`bid`/`ask` podem vir ausentes, zerados ou incoerentes |
| ramo offline do `deviceStore` → estado local do aparelho | Escrita de carteira sem passar pelo servidor |

## STRIDE Threat Register

| Threat ID | Categoria | Componente | Disposição | Mitigação |
|-----------|-----------|------------|------------|-----------|
| T-LDG-01 | Elevation of Privilege | `body.aceitaLiquidezDificil` | mitigate | A flag só destrava DIFÍCIL; SEM MERCADO é 400 incondicional. Comparação `is not True` — `"false"`/`1`/`"sim"` não destravam (Task 2c) |
| T-LDG-02 | Spoofing | corpo do `/abrir-collar` | mitigate | A faixa vem da proposta RE-DERIVADA no servidor (`p["liquidez"]["faixa"]`), nunca do corpo — reusa a defesa do ADR-026 Decisão 2 |
| T-LDG-03 | Tampering | ramo offline do `deviceStore` | mitigate | Mesma régua e mesmas mensagens do servidor no ramo sem sessão (Task 3f); sem isso o aparelho executaria o que o servidor recusa |
| T-LDG-04 | Information Disclosure | `liquidez.aviso` | accept | Só carrega score/volume/spread do contrato — dado público de mercado, já exibido no chip |
| T-LDG-05 | Repudiation | rejeição por liquidez no aparelho | mitigate | `_registrarRejeicaoLocal` grava a rejeição no histórico com o motivo, como as demais rejeições de ordem |
| T-LDG-06 | Denial of Service | segunda passada de `rastrear` | accept | Custo O(n) extra sobre uma cadeia já em memória (≤70 contratos medidos); nenhuma chamada de rede nova |
| T-LDG-07 | Tampering | instalação de pacote | mitigate | Nenhuma dependência nova em `requirements.txt` nem em `package.json` — não há superfície de supply chain nesta task |
</threat_model>

<verification>
1. `bash scripts/executar.sh --testes` verde nas DUAS suítes (pytest + `web/tests/*.mjs`) — `scripts/test.sh` sozinho não conta.
2. `npx vite build` em `web/` sem erro.
3. `grep -rn "LIQUIDEZ_MINIMA\|_label_liquidez" server/app` não devolve nada.
4. Os 12 guardiões da tabela `<guardioes_que_viram>` foram ATUALIZADOS com nota datada — nenhum apagado, nenhum enfraquecido (`==` não virou `>=`, asserção não virou comentário).
5. Nenhum arquivo em `server/web_dist` foi tocado; `scripts/bump.sh` e `scripts/publicar-web.sh` não foram executados.
6. `liquidity_score` (a fórmula) está byte-idêntica ao commit 3c49f43 — `git diff 3c49f43 -- server/app/options_quant.py` só mostra adições (constantes, `faixa_de_liquidez`, docstring), nenhuma linha do corpo da função alterada.
</verification>

<success_criteria>
- Um contrato de score 46,0 (DIFÍCIL real, ABEVI165W2) aparece na proposta, exibe a faixa no chip e só executa depois de um `window.confirm` cujo texto veio do backend.
- Um contrato de score 29,6 (B3SAI167W2) não vira proposta, e uma tentativa direta na rota responde 400 mesmo com `aceitaLiquidezDificil: true`.
- Numa cadeia com NEGOCIÁVEL e DIFÍCIL, a proposta é sempre a NEGOCIÁVEL.
- RADL3 (0 NEGOCIÁVEL, 5 DIFÍCIL) passa a ter proposta, onde hoje o gate a apagava.
- O Modo Estudo explica a faixa por verbete determinístico, com custo zero de LLM.
- Suíte canônica verde e `npx vite build` limpo.
</success_criteria>

<output>
Escrever `.planning/quick/260908-ldg-gate-de-liquidez-em-tres-faixas-com-cons/260908-ldg-SUMMARY.md` ao final, incluindo: guardiões atualizados (com o antes/depois de cada um), a decisão sobre `analyze_options` (bandeira alargada — revertível em uma linha), a assimetria deliberada abrir×fechar, e a publicação registrada como PENDÊNCIA (bump + `publicar-web.sh` fora de escopo, PR #31 já aguardando promoção).
</output>
</content>
</invoke>

---

## Resoluções do orquestrador (2026-09-08, antes do dispatch) — LOCKED para o executor

Os oito pontos levantados pelo planner, decididos sob a delegação do Alex
("avance tomando as decisões necessárias") e dentro do quadro que ele
confirmou. O executor NÃO reabre nenhum deles.

| # | Ponto | Decisão |
|---|---|---|
| 1 | `options_api.analyze_options:178` tem um segundo corte 40 solto | **ACEITO**: bandeira de risco dispara quando `faixa != NEGOCIÁVEL`. Alarga a transparência para 40–54, que hoje não avisa nada — é a direção do produto (princípio 3). Comentário datado; reversível em uma linha. |
| 2 | Paridade real está no ramo OFFLINE de `deviceStore.optionsAbrirLastreada` (~1244), sem régua de liquidez | **ACEITO, obrigatório**. Sem isso o aparelho sem sessão executa o que o servidor recusa — anti-padrão documentado. Usar `liquidity.score` que `/api/options/chain` já enriquece por contrato; não reimplementar `liquidity_score` em JS. Guardião cobrindo as três faixas no ramo offline. |
| 3 | Front já duplica a escala (`App.jsx:3098-3099`) | **ACEITO**: centralizar em `finance.js` como espelho declarado de `options_quant`, com guardião comparando os dois arquivos-fonte. Não é régua nova — é a existente, agora testada. |
| 4 | Fechamento (`proposta_fechar`, rota `/fechar`) ganha os campos mas NÃO bloqueia por faixa | **ACEITO**: travar a saída em contrato ruim prende o usuário onde ele mais precisa sair. Comentário no código registrando a assimetria como deliberada. |
| 5 | Agente autônomo não abre estruturas | **ACEITO**: guardião estrutural (AST) provando que `agent.py` não chama `abrir_call_coberta`/`comprar_put_protecao`/`abrir_collar`. Sem código de gate. |
| 6 | Escala em `options_quant.py` (`LIQUIDEZ_NEGOCIAVEL=55`, `LIQUIDEZ_DIFICIL=30`, `faixa_de_liquidez()`) | **ACEITO**: único módulo que os três consumidores já importam. `liquidity_score` byte-idêntica (provar via `git diff 3c49f43 -- server/app/options_quant.py` restrito a adições ao redor). |
| 7 | Frase em `skill_ref.OPCOES_LASTREADAS["liquidez_dificil"]` + `LIQUIDEZ_FRAGMENTOS` | **ACEITO**: todo texto visível nasce em `skill_ref`; o motor só escolhe o fragmento. Cobre volume 0 com OI alto (Yahoo), onde "0 unidades hoje" seria falso. |
| 8 | Mensagens 400 inline em `main.py` | **ACEITO** pelo precedente da própria rota (403/409/502 inline). D-04 é sobre o texto do consentimento, não da recusa. |

Sobre G5 (`test_liquidity_score_mydata.py:56-59, :75-81`): os testes chamados
`..._reprova` continuam numericamente verdadeiros (`< 40`) mas o SENTIDO mudou
— 30–39 agora é DIFÍCIL, aparece com consentimento. Atualizar nome + docstring
com nota datada (2026-09-08, quick 260908-ldg); a asserção de "< 30 é SEM
MERCADO / bloqueado" é a que carrega o critério de gate daqui em diante.
`CORTE = 40` vira referência às duas faixas. Nenhum guardião se apaga.

## Correções pós plan-checker (2026-09-08) — sobrepõem o texto da Task 1 onde conflitarem

O gsd-plan-checker verificou por execução direta dois fatos que a Task 1
tinha errado. Corrigidos aqui pelo orquestrador (confirmados por execução
independente), sem nova rodada de planner.

**C1 — G7, fixture do collar (`test_opcoes_collar.py:373-395`).** O plano
dizia "85,0 / 71,0, ambas NEGOCIÁVEL" e mandava assertar
`faixa == "NEGOCIÁVEL"`. Valor real com a fórmula atual: **call 67,0
(NEGOCIÁVEL) / put 53,0 (DIFÍCIL)**; a pior perna é a put → a proposta do
collar já sai **DIFÍCIL** hoje. A instrução correta: assertar
`r["proposta"]["liquidez"]["faixa"] == "DIFÍCIL"` e registrar em docstring
que este fixture é o caso MISTO — o guardião natural de "collar leva a faixa
da pior perna", que exercita o caminho do consentimento diretamente.
Atualizar o `measured_facts` correspondente.

**C2 — G5, `test_liquidity_score_mydata.py:75-81`
(`test_piso_sem_livro_e_mil_unidades`).** A linha `_s(1000) >= CORTE` fica
numericamente verdadeira para sempre (40,0 ≥ 40), mas a docstring afirma que
1.000 unidades é volume "cheio" — falso sob as três faixas: **40,0 é DIFÍCIL**,
exige consentimento. Renomear para algo como
`test_mil_unidades_sem_livro_e_piso_de_dificil_nao_de_negociavel`, reescrever
a docstring com nota datada (2026-09-08, quick 260908-ldg), e assertar a
faixa explicitamente (`faixa_de_liquidez(_s(1000)) == "DIFÍCIL"`). Mesma nota
para a linha `_s(900)` (39,1 → também DIFÍCIL, não "reprova"). O critério de
gate que segue valendo é `< 30` = SEM MERCADO.

Limiares de volume implicados pelas faixas (informativo, para docstrings e
para o verbete — derivados da fórmula, não escolhidos):
- sem livro publicado: DIFÍCIL a partir de ~320 un.; NEGOCIÁVEL a partir de ~5.600 un.
- livro apertado (≤3%): DIFÍCIL a partir de ~17 un.; NEGOCIÁVEL a partir de ~320 un.
