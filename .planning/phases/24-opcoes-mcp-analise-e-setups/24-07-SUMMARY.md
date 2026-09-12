---
phase: 24-opcoes-mcp-analise-e-setups
plan: 07
subsystem: api
tags: [fastapi, react, opcoes, mcp, cap, cota, transparencia]

requires:
  - phase: 24-opcoes-mcp-analise-e-setups (planos 01–04, 06)
    provides: "`_chamada_com_cap`, `_cap_check`/`_Reserva`, `_erro_http`, `AVISOS`, o fan-out de até 6 vencimentos do `/possibilidades` e as duas seções da tela"
provides:
  - "recusa de tool debita 1 do cap do usuário — regra em UM ponto (`_chamada_com_cap`), replicada só no `/status`, que chama `call_tool` direto"
  - "as quatro falhas sem viagem provada seguem sem debitar, com os quatro motivos escritos no código"
  - "`cobrado`/`nota` nos 422 de erro de tool, vindos de uma MARCA posta no ponto do débito — nunca de um literal fixo"
  - "`AVISO_RECUSA_COBRADA` em `AVISOS` (varredura do guardião imperativo)"
  - "`opcoesRecusaCobrada` nos dois modos + `RecusaCobrada` nos dois ramos de erro da tela"
affects: [24-05 (publicação), observabilidade do cap (o contador do usuário passa a acompanhar o do serviço)]

tech-stack:
  added: []
  patterns:
    - "o FATO viaja na exceção: quem sabe que houve débito é quem debitou, e a tradução do erro lê a marca em vez de adivinhar"
    - "campo ausente é a forma de não afirmar — `cobrado` só existe quando houve cobrança"

key-files:
  created: []
  modified:
    - server/app/options_mcp_api.py
    - server/tests/test_mcp_cap.py
    - server/tests/test_options_mcp_api.py
    - server/tests/test_opcoes_dsl.py
    - web/src/copy.js
    - web/src/opcoes/OpcoesScreen.jsx
    - web/tests/test_opcoes_analisar_ui.mjs

key-decisions:
  - "`cobrado: True` NÃO é fixo no `_erro_http`: `_material_do_compilador` fabrica um `McpErroDeTool` sem nenhuma `tools/call`, e um literal afirmaria à pessoa um débito inexistente — o erro do F-04 invertido, agora na tela"
  - "A marca do débito é posta em `_chamada_com_cap` (e lida em `_erro_http`) em vez de passada por parâmetro em cada `raise _erro_http(e)`: o parâmetro precisaria ser repetido em 11 rotas e divergiria na primeira manutenção"
  - "Os 422 de `setup_invalido` e `setup_desconhecido` ganharam o mesmo par `cobrado`/`nota` — são recusas de tool e custam a mesma viagem; o campo vem da mesma marca, não de uma segunda regra"
  - "`test_leitura_que_levanta_devolve_a_reserva_inteira` trocou `McpErroDeTool` por `McpIndisponivel` em vez de mudar o número: a afirmação original (\"falha não gasta cota\") continua verdadeira para falha SEM viagem, e o guardião segue guardando o que sempre guardou"
  - "Cache negativo da recusa NÃO foi implementado — era a alternativa, o Alex escolheu só cobrar; `mcp_client.py` tem 0 linhas alteradas"

patterns-established:
  - "Prova de não-vacuidade por injeção do defeito OPOSTO: os quatro testes de \"não debita\" não podem ser vistos em vermelho (o comportamento deles não muda), então a prova é trocar `except McpErroDeTool` por `except McpErro` e ver os quatro reprovarem"

requirements-completed: ["24-VERIFICATION F-04"]

duration: 25min
completed: 2026-09-11
---

# Fase 24 Plano 07: cobrar a viagem que a tool recusou (F-04) — Summary

**A recusa de tool deixou de ser de graça para quem a provoca e cara para a base inteira: ela debita 1 do cap do usuário, as quatro falhas sem viagem provada continuam sem debitar, e a pessoa é avisada de que a tentativa consumiu cota.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-09-11T18:55Z (aprox.)
- **Completed:** 2026-09-11T19:05Z (aprox., somando a suíte canônica)
- **Tasks:** 3
- **Files modified:** 7

## O que estava errado, em uma passagem

O serviço MCP conta **toda** `tools/call` no porteiro, **antes** de executar a
tool. O Boris debitava só no sucesso: `_chamada_com_cap` punha o `cap.consome`
depois do `await`, e a exceção o pulava. Resultado medido pelo verificador, num
ticker cuja cadeia não precifica:

- requisição 1: 13 chamadas reais ao serviço, 7 debitadas do usuário;
- requisição 2, dentro do TTL de 15 min: base e os 6 `propose` vêm do cache; as
  6 recusas de `evaluate` **nunca entram em cache** (o `mcp_client` levanta
  antes do `_cache_put`) → **6 chamadas reais cobradas pelo serviço, 0
  debitadas do usuário e 0 do contador global**.

~330 toques no botão esgotavam os 2.000/dia de toda a base sem mover os 60/dia
de ninguém. **Decisão do Alex em 2026-09-11: cobrar a viagem.** O critério
passou a ser literal — *tocou a rede, debitou*.

## Prova RED → GREEN (a regra de ouro deste plano)

| Correção | Teste escrito primeiro | RED observado (código de antes) | GREEN |
|---|---|---|---|
| recusa debita 1 | `test_recusa_de_tool_debita_um_porque_a_viagem_aconteceu` | `assert 0 == 1` | passa |
| **cenário F-04 medido** | `test_f04_seis_evaluate_recusados_com_propose_em_cache_debitam_seis` | `assert 0 == 6` — o número exato do achado | passa |
| contabilidade da reserva | `test_f04_reserva_de_doze_com_seis_recusas_devolve_seis` | `consumo diferente das 6 recusas: []` | passa |
| `/status` 200 E debita | `test_status_com_erro_de_tool_segue_200_e_debita_um` | `assert 0 == 1` | passa |
| 422 diz que cobrou | `test_f04_o_422_de_erro_de_tool_diz_que_cobrou` | `KeyError: 'cobrado'` | passa |
| a tela diz | bloco 14 de `test_opcoes_analisar_ui.mjs` (10 asserções) | `10 FALHA(S)` | `todos os testes passaram` |

**As outras quatro exceções não podem ser vistas em vermelho** — o
comportamento delas não muda. A prova é por **injeção do defeito oposto**:
trocando `except mcp_client.McpErroDeTool` por `except mcp_client.McpErro` (a
"uniformização" que o comentário do código proíbe), as quatro reprovam:

```
FAILED tests/test_mcp_cap.py::test_as_quatro_falhas_sem_viagem_provada_nao_debitam[erro0-503]
FAILED tests/test_mcp_cap.py::test_as_quatro_falhas_sem_viagem_provada_nao_debitam[erro1-503]
FAILED tests/test_mcp_cap.py::test_as_quatro_falhas_sem_viagem_provada_nao_debitam[erro2-503]
FAILED tests/test_mcp_cap.py::test_as_quatro_falhas_sem_viagem_provada_nao_debitam[erro3-402]
4 failed, 24 deselected
```

Mesma técnica para a condicionalidade do `cobrado` (ver Desvio 1): trocando
`_bloco_cobrado` por um dicionário fixo,
`test_material_ausente_vira_422_em_vez_de_compilar_de_memoria` reprova. Os dois
defeitos foram revertidos imediatamente depois da medição.

## Task Commits

1. **Task 1 — cobrar a recusa, em um ponto só** — `74f5632` (fix)
2. **Task 2 — o cenário medido do F-04 e o novo critério** — `cb62e46` (test)
3. **Task 3 — a tela diz que a recusa consumiu cota** — `60c26d0` (feat)

## Files Created/Modified

- `server/app/options_mcp_api.py` — `_chamada_com_cap` com `try/except
  McpErroDeTool` (consome + marca + re-levanta) e docstring reescrita; `/status`
  consumindo na recusa; `AVISO_RECUSA_COBRADA` em `AVISOS`; `ATR_DEBITADO`,
  `_debitou_a_viagem`, `_bloco_cobrado`; `cobrado`/`nota` nos três 422 de erro
  de tool
- `server/tests/test_mcp_cap.py` — 6 testes novos (1 debita + 4 não debitam +
  `/status`); `test_leitura_que_levanta_devolve_a_reserva_inteira` migrado para
  `McpIndisponivel` com a razão e a data no código
- `server/tests/test_options_mcp_api.py` — 3 testes novos (o cenário F-04, a
  contabilidade da reserva, o 422 que diz que cobrou); expectativa de
  `test_falha_na_primeira_etapa_vira_422_sem_segunda_etapa` invertida com nota
- `server/tests/test_opcoes_dsl.py` — `test_material_ausente...` reforçado: o
  422 fabricado **não** pode dizer `cobrado`
- `web/src/copy.js` — `opcoesRecusaCobrada` nos DOIS modos
- `web/src/opcoes/OpcoesScreen.jsx` — `RecusaCobrada`, renderizado nos dois
  ramos de erro (cascata principal e `ErroDoMcp`)
- `web/tests/test_opcoes_analisar_ui.mjs` — bloco 14 (10 asserções)

## Decisões Made

1. **`cobrado: True` não é literal fixo.** O plano pedia o campo no 422 de
   `mcp_erro_de_tool`. Fixo, ele mentiria: `_material_do_compilador`
   **fabrica** um `McpErroDeTool` quando o serviço não publica o schema ou o
   texto de `create_setup`, e ali nenhuma `tools/call` aconteceu (`tools/list`
   e `resources/read` são protocolo, grátis no teto e fora do cap). O campo vem
   de uma marca posta no ponto do débito. Guardião próprio em
   `test_opcoes_dsl.py`.
2. **A marca viaja na exceção, não por parâmetro.** `_erro_http(e,
   cobrado=...)` obrigaria as 11 rotas a saberem se a recusa veio de uma
   `tools/call` — exatamente o conhecimento que o `_chamada_com_cap` já tem.
   Uma regra em dois lugares diverge na primeira manutenção; é o mesmo
   argumento do guardrail "um ponto só" do plano.
3. **Os quatro motivos de NÃO cobrar estão no código, não só no plano.** A
   próxima pessoa que ler o `except` vai querer uniformizar; o comentário
   nomeia cada exceção e por que ela é diferente, e termina com a frase que
   fecha o argumento: cobrar o que não se sabe se foi cobrado é o mesmo erro,
   invertido.
4. **`/status` continua respondendo 200.** Só o débito mudou. A finalidade da
   rota é reportar estado do dado, e um 422 faria "idade desconhecida" virar
   silêncio — que o usuário lê como "em dia" (ADR-027; princípio 9 do
   `CLAUDE.md`). O comentário registra que um 200 é justamente a resposta de
   que ninguém desconfiaria de ter custado.
5. **A frase da tela é do front, não do backend.** O backend manda `nota`
   (para qualquer consumidor da API); a tela usa `copy.js` porque a informação
   é sobre a **cota da pessoa** e tem voz por modo. O que aconteceu com o
   pedido continua vindo do serviço, verbatim, na linha de cima.
6. **Cache negativo não foi implementado.** Era a alternativa (b) do
   `24-VERIFICATION.md`; o Alex escolheu (a). `git diff` confirma: 0 linhas em
   `server/app/mcp_client.py`.

## Deviations from Plan

### 1. [Rule 1 — Bug] `cobrado` condicional em vez de literal

- **Found during:** Task 1
- **Issue:** O plano especificava `"cobrado": True` direto no 422 de
  `_erro_http`. Nem todo `McpErroDeTool` vem de uma `tools/call`:
  `_material_do_compilador` (`options_mcp_api.py`) fabrica um quando o serviço
  não publica o `inputSchema` ou o resource, e ele cai justamente em
  `_erro_http`. O literal afirmaria um débito que não existe — e nesse caminho
  o cap de fato **não** foi tocado, então a resposta se contradiria com o
  próprio contador.
- **Fix:** `ATR_DEBITADO` posta em `_chamada_com_cap` no mesmo bloco do
  `cap.consome`; `_bloco_cobrado(e)` devolve `{}` sem a marca. Ausência do
  campo é a forma de não afirmar.
- **Files modified:** `server/app/options_mcp_api.py`,
  `server/tests/test_opcoes_dsl.py`
- **Commit:** `74f5632`

### 2. [Rule 2 — Missing critical] `cobrado`/`nota` também nos 422 de setup

- **Found during:** Task 1
- **Issue:** O plano citava só `_erro_http`. `_erro_de_setup_invalido` e
  `_erro_de_setup_desconhecido` também nascem de `except McpErroDeTool` colado
  num `_chamada_com_cap` — mesma viagem, mesma cobrança, e o corpo não diria
  nada sobre ela.
- **Fix:** Os dois usam o MESMO `_bloco_cobrado`, então não há segunda regra a
  divergir. Ver "Deferred" abaixo: a tela da seção *Criar setup* ainda não
  renderiza essa linha.
- **Files modified:** `server/app/options_mcp_api.py`
- **Commit:** `74f5632`

### 3. [Rule 3 — Blocking] Guardião migrado de exceção em vez de ter o número trocado

- **Found during:** Task 1
- **Issue:** `test_leitura_que_levanta_devolve_a_reserva_inteira` afirmava
  `usado == 0` com a mensagem "falha gastou cota", usando `McpErroDeTool`.
  Trocar só o número apagaria a afirmação original, que continua verdadeira
  para falha **sem** viagem.
- **Fix:** O teste passou a usar `McpIndisponivel` (falha sem viagem provada) e
  segue provando o "não gasta" + a devolução da reserva; o novo critério tem
  guardião próprio. A razão e a data estão na docstring do teste.
  `test_falha_na_primeira_etapa_vira_422_sem_segunda_etapa` não tinha essa
  saída (o cenário dele É a recusa de tool): mudou de `0` para `1`, com a nota
  explicando que o que ele guarda — a segunda etapa não acontece, nada fica
  preso — não mudou.
- **Files modified:** `server/tests/test_mcp_cap.py`,
  `server/tests/test_options_mcp_api.py`
- **Commit:** `74f5632`

### 4. [Rule 3 — Blocking] Divisão dos commits das Tasks 1 e 2

- **Found during:** Task 1
- **Issue:** O plano põe o código na Task 1 e os testes na Task 2. Como duas
  expectativas de testes EXISTENTES se invertem com a decisão, um commit de
  Task 1 sem elas deixaria o `HEAD` vermelho — commit atômico que não passa na
  própria suíte.
- **Fix:** Task 1 levou o código **mais** as duas expectativas migradas e o
  reforço do guardião do `_material_ausente`; Task 2 levou os 9 testes novos.
  Os dois commits são verdes em `HEAD`. As provas RED foram todas feitas antes
  do primeiro commit.
- **Commits:** `74f5632`, `cb62e46`

---

**Total deviations:** 4 (1 bug, 1 missing-critical, 2 blocking). **Nenhuma de
escopo** — cache negativo segue não implementado, e nenhum custo declarado de
rota mudou.

## Critérios de aceite — leitura literal × intenção

- **"`grep -c "cap.consome(1)"` cobre os caminhos de sucesso E de recusa"** —
  cumprido: `grep -c` dá **4**, e são exatamente os dois pares de
  sucesso/recusa — linhas 830 e 834 em `_chamada_com_cap`, linhas 1088 e 1106
  no `/status`, que é a única rota que chama `call_tool` direto. Vale o alerta
  de sempre: `grep -c` conta LINHAS e já enganou quatro executores desta fase;
  a prova de que cada um dos quatro caminhos faz o que deve é comportamental,
  nos testes.
- **"o detail do 422 `mcp_erro_de_tool` ganha `cobrado: True`"** — cumprido
  como verdade, não como literal. Ver Desvio 1: o literal mentiria no caminho
  do `_material_do_compilador`. O guardrail que isso protege (não afirmar o que
  não se sabe) é o mesmo do plano.

## Validação (fora do sandbox)

**Suíte canônica — `bash scripts/executar.sh --testes`, exit 0:**

```
== Suítes do backend ==
........................................................................ [  2%]
[...]
2433 passed, 5 skipped, 627 warnings in 65.77s (0:01:05)

== Suítes web ==
  [OK] web/tests/test_opcoes_analisar_ui.mjs
  [OK] web/tests/test_opcoes_criar_setup_ui.mjs
  [OK] web/tests/test_opcoes_mcp_aba_ui.mjs
  [...]
  [OK] web/tests/test_wiring_deps.mjs
```

- **129 arquivos `.mjs [OK]`** (contagem programática: `grep -c "\[OK\]"` =
  129), **exit 0**.
- **Backend: 2433 passed, 5 skipped.** Baseline do 24-06 era `2424 passed, 5
  skipped`: **+9**, exatamente os 9 testes novos de backend (6 em
  `test_mcp_cap.py` — 1 + 4 parametrizados + 1 — e 3 em
  `test_options_mcp_api.py`). **Zero regressão.**
- As duas ocorrências de "falha" na saída são nomes de teste
  (`test_scan_rankeia_tolera_falha_e_tem_disclaimer`,
  `test_fase3_custos_falha_brapi.mjs`), não falhas.

**Build do front — `cd web && npx vite build`:**

```
✓ built in 1.07s
PWA v0.21.2
precache  23 entries (919.52 KiB)
```

## Known Stubs

Nenhum. Nenhum valor fixo, nenhum componente sem fonte de dado, nenhum
`TODO`/`FIXME` introduzido.

## Deferred

- **A seção *Criar setup* não mostra a linha da cota.** `CriarSetup.jsx` tem a
  própria cascata (`ErroDaCriacao`) e os códigos dela são `setup_invalido` /
  `setup_desconhecido`. O backend já manda `cobrado`/`nota` nesses 422 (Desvio
  2), mas o arquivo está fora dos `files_modified` deste plano e a mudança
  pediria o guardião de front correspondente
  (`test_opcoes_criar_setup_ui.mjs`). É meia hora de trabalho, e o efeito é a
  mesma linha discreta que a aba Analisar ganhou.

## O que continua SEM prova

Inalterado em relação ao `24-VERIFICATION.md` e ao 24-06 — este plano não abriu
nem fechou nenhuma dessas frentes:

1. **Nenhuma chamada ao serviço MCP real** (`MCP_CLIENT_SECRET` fora do
   ambiente, D-24.7). Que o serviço conte a `tools/call` recusada é fato
   **lido do fonte dele** (`servico.py`, middleware) e do contrato, não medido
   contra o `/observabilidade` ao vivo. É exatamente o que o segundo teste ao
   vivo da fila do `24-VERIFICATION.md` mediria.
2. **Nenhuma chamada de LLM real.**
3. **Nada em aparelho.** A linha nova da recusa cobrada não foi vista em
   375 px.

## Next Phase Readiness

- **Os quatro achados do `24-VERIFICATION.md` estão fechados** (F-01/F-02/F-03
  no 24-06; F-04 aqui), cada um com guardião que os trava.
- **A fase está pronta para a revisão do Alex.**
- **Bloqueadores que seguem para o 24-05 (publicação):** (a) o OK explícito do
  Alex, que é o desenho do plano (`autonomous: false`); (b) o primeiro teste ao
  vivo que a verificação nomeia —
  `pytest tests/test_opcoes_paridade_mcp.py::test_paridade_viva` com
  `MCP_CLIENT_SECRET` no ambiente; (c) o segundo da fila, `/possibilidades`
  com N=6 ao vivo, que agora também confirma se o contador do serviço e o cap
  do usuário sobem juntos.
- Nada foi empurrado a `origin`, nenhum PR aberto.

---
*Phase: 24-opcoes-mcp-analise-e-setups*
*Completed: 2026-09-11*
</content>
</invoke>

## Self-Check: PASSED

- Os 7 arquivos modificados e o SUMMARY existem em disco.
- Os 3 commits (`74f5632`, `cb62e46`, `60c26d0`) existem no histórico.
- `grep -c "cap.consome(1)"` = **4** (dois pares sucesso/recusa: linhas 830/834
  em `_chamada_com_cap`, 1088/1106 no `/status`).
- `<RecusaCobrada` renderizado **2×** em `OpcoesScreen.jsx` (um por ramo de
  erro); `opcoesRecusaCobrada:` **2×** em `copy.js` (um por modo).
- `git diff 9666ac7..HEAD -- server/app/mcp_client.py` = **0 linhas**: o cache
  negativo da recusa não foi implementado, como a decisão manda.
- `grep -c "with _cap_check("` = **12** (11 usos + 1 na docstring), o mesmo
  número de antes: **nenhum custo declarado de rota mudou.**
