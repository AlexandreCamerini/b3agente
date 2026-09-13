---
phase: 25-planos-comerciais
plan: 04
subsystem: api
tags: [plano-comercial, adr-010, adr-013, gates, owner, d3, conciliacao, codigo-de-erro, guardioes]

requires:
  - phase: 25-planos-comerciais
    provides: "25-03 (`plan.LIMITES_DE_PLANO`, `limites_do_plano`, `env_key`, `plan.configure_db`) — o catálogo que ninguém lia; e 25-02 (`rbac.OWNER`) para a D3"
  - phase: adr-010
    provides: "a separação teto FÍSICO × cap COMERCIAL (decisão 2: 'um usuário pago consome da MESMA cota física')"
  - phase: adr-013
    provides: "RBAC sem cache por decisão explícita (revogação imediata > latência) — respeitado, nenhum cache novo"
provides:
  - "`main._limite_do_plano(scope, chave, global_fn, plano)`: a CONCILIAÇÃO plano → override global → env → default, no chamador"
  - "`main._plano_efetivo(scope, plano)`: o dict de plano com os limites do catálogo aplicados, devolvendo o MESMO objeto quando nada foi configurado"
  - "`main._escopo_e_owner(scope)`: a D3, fail-closed, sem cache e fora do caminho feliz"
  - "`options_mcp_api.marcar_o_limite`/`codigo_do_limite` + `COD_PLANO_ANALISES`/`COD_IA_GERENCIADA`: a recusa classificada por código"
  - "`options_mcp_api.configure(..., limite_do_plano=...)`: o 4º extra da injeção"
  - "`assistente.responder(..., teto=...)`: teto resolvido pelo chamador, com sentinela própria (`None` = sem teto)"
  - "server/tests/test_gates_por_plano.py — 28 casos em 6 blocos"
affects: [25-05-modulo-no-portal, 25-06-plano-visivel-no-app]

tech-stack:
  added: []
  patterns:
    - "Conciliação por injeção de `global_fn`: a REGRA mora num lugar só (main.py) e o BINDING (qual resolvedor global) é argumento — é o que permite `plan.py` continuar sem importar `managed`/`options_mcp_api`"
    - "Precedência decidida pela ORIGEM, não pelo valor: só `origem == kv` (ou env com `{PLANO}`) vence o override global; `default` nunca vence, porque o default do catálogo É o número global de sempre"
    - "Carimbo na exceção no ponto da decisão (`marcar_o_limite`), lido só na tradução — reuso do padrão `ATR_DEBITADO` que o próprio módulo já tinha"
    - "Consulta cara só no ramo de NEGAÇÃO: o owner é perguntado depois de o gate já ter decidido barrar, então o caminho feliz não paga"

key-files:
  created:
    - server/tests/test_gates_por_plano.py
  modified:
    - server/app/main.py
    - server/app/options_mcp_api.py
    - server/app/assistente.py
    - server/app/managed.py
    - server/tests/test_opcoes_dsl.py

key-decisions:
  - "A conciliação decide pela ORIGEM do valor, não por ele existir: `origem == default` NÃO vence o override global, porque o default do catálogo é exatamente o número que o resolvedor global já devolve — tratá-lo como 'configuração do plano' faria o painel admin perder para um literal"
  - "As três constantes do código de erro moram em `options_mcp_api`, não em `plan.py`: `main.py` já importa aquele módulo (o contrário seria circular) e os dois códigos são CONTRATO publicado da aba (`detail.code`)"
  - "O `detail` do 402 continua sendo STRING. Transformá-lo em dict — a outra via sugerida pelo plano — mudaria o contrato de `/api/analyze` e o app mostraria `[object Object]`; o carimbo viaja como atributo da exceção e some na serialização"
  - "`assistente.responder` ganhou sentinela própria (`_TETO_NAO_INFORMADO`) em vez de usar `None` como 'não informado': `None` passou a ser valor legítimo (plano sem teto), e as duas coisas no mesmo símbolo trariam o freio de R$ 1/dia de volta calado"
  - "O owner é consultado DEPOIS de o gate negar: resultado idêntico ao de perguntar antes, e o caminho feliz não paga uma consulta de papel por requisição de IA"
  - "`opcoes.criar_setup` NÃO migrou do RBAC para o plano (D2) — escopo reduzido deliberado, ver a seção própria"

patterns-established:
  - "Guardião que compara os kwargs REAIS passados a `metering.check` (espião) em vez de ler o código: é a única forma de provar que o teto físico não mudou de valor NEM de origem"
  - "Casos com os textos TROCADOS entre si para provar que a classificação não depende do texto — se dependesse, os dois casos inverteriam"

requirements-completed: ["Fase 3 do 25-CONTEXT — gates leem o plano (D3)"]

duration: 55min
completed: 2026-09-12
---

# Phase 25 Plan 04: Gates leem o plano — Summary

**O limite que barra uma conta deixou de ser um número igual para toda a base:
os cinco pontos de controle de IA passam a resolver pelo plano da conta, com o
override global do portal como camada de baixo — e há 28 casos provando que,
sem configuração nenhuma, o app decide exatamente como decidia ontem, que os
tetos físicos não se moveram, que o `owner` pula só o cap comercial e que a
recusa parou de ser classificada raspando uma frase.**

## Performance

- **Duração:** ~55 min
- **Tasks:** 3 de 3
- **Arquivos:** 5 modificados, 1 criado

## Task Commits

1. **Task 1: os gates de limite resolvem pelo plano** — `3ab1ea1` (feat)
2. **Task 2: D3 — o owner e o cap comercial, e o erro por código** — `ab632f3` (feat)
3. **Task 3: guardiões** — `b45027e` (test)

## A conciliação, e por que a ORIGEM decide

A regra implementada é a do plano, com um detalhe que só aparece na
implementação e muda o resultado:

```
limite do PLANO (kv por plano → env por plano)
  → override GLOBAL de hoje (admin_config / kv, que o portal já escreve)
    → env global
      → default
```

`plan.limites_do_plano()` já devolve um valor para os cinco pontos **sempre** —
com `origem: "default"` quando nada foi configurado. Se o chamador usasse esse
valor por ele existir, o default do catálogo (20 análises/dia, 60 chamadas/dia,
R$ 1,00) passaria na frente do `llmDailyQuota` que o admin digitou no painel.
Os números coincidem hoje, então o defeito seria **invisível até alguém mexer
no painel** — e aí o painel confirmaria uma configuração que não vale.

Por isso quem decide é `_e_limite_por_plano(chave, origem)`:

| origem | vence o global? | por quê |
|---|---|---|
| `kv` | **sim** | a chave de kv carrega o id do plano (`planoFree.…`) — só existe se alguém configurou AQUELE plano |
| `env` com `{PLANO}` | **sim** | `B3_PLANO_FREE_WATCHLIST` é, por construção, configuração de plano |
| `env` sem `{PLANO}` | não | é a MESMA env global que `managed`/`options_mcp_api` leem — tratá-la como plano faria a env saltar na frente do painel, invertendo a precedência de hoje |
| `default` | nunca | o default do catálogo **é** o número global de sempre |

`_limite_do_plano` mora em `main.py` — no chamador, como o plano exige — e
chega a `options_mcp_api` pelo **4º extra de `configure()`**, ao lado de
`require_user`, `gate_analise` e `config_do_usuario`, pela mesma razão que
aqueles três: nasce de `plan` + `db` + `_plano_do_escopo`, que moram em
`main.py`, e o import ao contrário seria circular. Uma implementação só, dois
consumidores — duas cópias de uma regra de precedência que decide dinheiro
divergiriam na primeira manutenção.

`plan.py` **não foi tocado**. A fronteira de import do 25-03 continua travada
por AST.

### Os cinco pontos, um a um

| ponto | onde resolve | camada de baixo (quem não configurou) |
|---|---|---|
| `max_analyses_per_month` | `_gate_analise` via `_plano_efetivo` | o default do catálogo (30/`None`) — não há override global |
| `max_watchlist` | `PUT /api/watchlist`, `POST /api/watchlist/add`, `GET /api/watchlist/quota` | idem (10/`None`) |
| `ia_gerenciada_dia` | `_ai_apply_managed` | `managed.daily_quota()` (override admin → env → 20) |
| `opcoes_chamadas_dia` | `options_mcp_api._cota_usuario(uid)`, dentro de `_cap_check` | `cota_usuario_dia()` (kv global → env → 60) |
| `assistente_brl_dia` | `POST /api/assistente` | `assistente.teto_dia_brl()` (env → 1.0) |

`managed.daily_quota`, `options_mcp_api.cota_usuario_dia` e
`assistente.teto_dia_brl` **não mudaram uma linha de lógica** — só ganharam a
docstring dizendo que viraram a camada de baixo. É exatamente por não mudarem
que "sem configuração, nada muda" vale.

### O que NÃO mudou, e está provado

`managed.global_daily_cap()`, `managed.rate_per_min()`,
`options_mcp_api.cota_global_dia()`, `options_mcp_api.rate_min()` e
`TETO_SERVICO_DIA` seguem intocados — **por medição, não por leitura**: o
guardião espia os kwargs reais de `metering.check` e compara `cap_global` e
`rate_per_min` com plano configurado em 999.

## D3 — o owner, e a metade que importa

`_gate_analise` deixa de barrar o `owner` pelo cap **comercial**, na mesma
posição lógica do BYOK (que já pulava o gate mensal). E é **só** o comercial:
`_ai_apply_managed` continua rodando normalmente para ele, com cota diária,
rate e teto global da chave do servidor intactos.

Duas decisões de implementação:

**1. A pergunta vem depois da negação.** `_escopo_e_owner(scope)` só é chamado
quando `can_analyze` já decidiu barrar. O resultado observável é idêntico ao de
perguntar antes, e o caminho feliz — a esmagadora maioria das requisições — não
paga uma consulta de papel. O critério de aceite pedia "nenhuma consulta de
papel nova fora do caminho do gate"; isto é mais estrito que o pedido.

**2. Nenhum cache.** O ADR-013 escolheu revogação imediata acima de latência, e
`rbac` não tem cache por decisão explícita. Papel cacheado é papel que continua
valendo depois de revogado.

Fail-closed: qualquer falha de leitura devolve `False`, ou seja, a conta
**continua barrada**. Errar para o lado de barrar o dono é aborrecimento;
errar para o outro liberaria o cap comercial da base inteira num banco
intermitente.

## O código de erro, e por que não virou `detail` estruturado

`options_mcp_api.py:2326` descobria se um 402 vinha do gate mensal ou da cota
diária procurando a substring `"analises/mes"` na mensagem. Frágil e silencioso:
reescrever a frase — ou só acentuar "análises" — faria a aba Opções chamar de
`ia_gerenciada` um limite **mensal de plano**, e nenhum teste reclamaria no
momento do erro.

O plano oferecia duas vias ("a `HTTPException` carrega `detail.code` **ou** uma
exceção de domínio distingue os dois"). **A primeira foi descartada com
medição:** o `detail` do 402 de `_gate_analise` é lido como TEXTO pelo app
(`enrichErrorMessage` em `web/src/api.js` e o fallback determinístico do
FIX-C01 usam `e.detail` direto), e transformá-lo em dict faria a tela mostrar
`[object Object]`. Além disso vários testes existentes comparam
`r.json()["detail"]` com a frase.

A via escolhida é o **carimbo na exceção**, que é o padrão que o próprio módulo
já tinha (`ATR_DEBITADO`, 24-07: "marca posta na exceção NO PONTO em que o
débito acontece e lida só aqui, na tradução"):

- `marcar_o_limite(HTTPException(402, reason), COD_PLANO_ANALISES)` no gate
  mensal; `COD_IA_GERENCIADA` no `_ai_apply_managed`;
- `codigo_do_limite(e)` na tradução;
- a serialização do FastAPI ignora o atributo → **o texto que chega ao usuário
  não muda em nada**, e há caso de teste exigindo que `detail` continue sendo
  `str`.

As três constantes moram em `options_mcp_api` e não em `plan.py` por dois
motivos: `main.py` já importa aquele módulo (o contrário seria ciclo), e os dois
códigos são contrato publicado da aba (`detail.code`, consumido pelo front).

## RED medido antes de cada correção

`test_gates_por_plano.py` foi escrito inteiro **antes** de qualquer mudança de
código e rodado contra `HEAD~3`:

```
17 failed, 11 passed in 1.95s
```

Depois da Task 1 (os limites), **só os 7 casos da Task 2** seguiam vermelhos:

```
7 failed, 21 passed in 1.92s
```

Depois da Task 2: `28 passed`.

**Os 11 que passavam nos DOIS estados, e por que isso é o ponto:**

| caso | por que passa nos dois estados |
|---|---|
| os 4 do bloco 1 (`max_analyses_per_month`, `max_watchlist`, `ia_gerenciada_dia`, `opcoes_chamadas_dia` sem configuração) | é **exatamente** o que este plano promete: sem configuração, nada muda. Um teste que ficasse vermelho aqui estaria dizendo que a política mudou |
| os 3 do bloco 3 (tetos físicos e rate/min) | idem — eles não podiam se mover |
| `conta_comum_com_o_mes_estourado_continua_barrada` | prova que a isenção da D3 é do `owner`, não do gate inteiro |
| `sem_owner_configurado_ninguem_pula_o_cap_comercial` | idem, pelo lado da âncora desligada |
| `o_texto_que_chega_ao_usuario_nao_mudou` | o critério do código estruturado é **não** mudar o texto |
| `plan_py_continua_sem_importar_managed_e_options_mcp_api` | a fronteira do 25-03 tinha de sobreviver |

O 5º caso do bloco 1 (o teto do assistente) ficou **vermelho** porque a rota
não resolvia teto nenhum — o valor chegava a `responder` por dentro do próprio
módulo. Os outros 16 vermelhos são os blocos 2, 4, 5 e 6.

**Ressalva honesta:** um teste que passa nos dois estados prova
**não-regressão**, não a mudança. Como o critério principal deste plano é
justamente *não mudar nada para quem não configurou*, a não-regressão aqui **é**
o entregável — mas ela só tem valor porque os 17 vermelhos provam que o
mecanismo novo existe e funciona.

## Os 6 blocos do guardião (28 casos)

1. **Sem configuração, nada muda** — os cinco limites, kv vazio, números
   escritos à mão (30, 10, 20, 60, 1.0). As envs do catálogo são apagadas pela
   fixture, inclusive as três compartilhadas que podem estar no ambiente de
   quem roda a suíte.
2. **Com limite por plano, é ele que barra** — um caso por limite, mais dois de
   conciliação (`ia_gerenciada_dia` e `opcoes_chamadas_dia` contra o override
   global, com o caso "sem plano, o global manda" ao lado no mesmo teste), mais
   `free` e `pro` não disputando o mesmo registro.
3. **Tetos físicos intactos** — `cap_global` e `rate_per_min` dos dois caminhos,
   por espião no `metering.check`, com plano configurado em 999; e o conjunto de
   chaves do catálogo cravado (um teto físico entrando lá força decisão
   consciente).
4. **D3** — owner passa o comercial; owner é barrado pelo físico; conta comum
   segue barrada com a mesma frase; `B3_OWNER_EMAIL` vazia não libera ninguém.
5. **Código, não frase** — o carimbo nos dois caminhos reais; os dois códigos
   cravados por extenso; e o caso central: os textos das duas recusas **trocados
   entre si** — se a frase ainda decidisse, os dois inverteriam. Mais a
   degradação de um 402 sem carimbo (vira código válido, nunca 500) e a prova de
   que `detail` continua `str`.
6. **Fail-closed** — anônimo cai no free; falha ao ler o usuário degrada para o
   menos privilegiado mesmo com a conta marcada como `pro`; chave fora do
   catálogo cai no resolvedor global em vez de estourar no meio de uma análise;
   e a fronteira de import de `plan.py` por AST.

## Guardiões atualizados (nunca apagados)

Guardrail do `CLAUDE.md`: reversão deliberada atualiza o guardião com nota.

- **`test_gate_de_analise_nega_com_texto_proprio_da_aba`** — a recusa simulada
  passa a vir carimbada, como o gate real a produz. As duas frases continuam no
  teste de propósito: elas são o texto real de cada teto, e ele segue provando
  que o copy de BYOK não vaza para a aba Opções.
- **`test_marca_do_gate_mensal_ainda_existe_em_plan`** → **`test_a_classificacao_do_402_nao_depende_mais_da_frase`.**
  O antigo travava a substring na frase de `plan.can_analyze`, ou seja,
  **protegia o acoplamento em vez de removê-lo** — e cobria só metade do risco
  (traduzir ou acentuar quebraria igual, sem ele reclamar). O novo trava o
  oposto: que `_MARCA_DO_GATE_MENSAL` não voltou, que a string `"analises/mes"`
  sumiu do código de `options_mcp_api` (por leitura sem comentários) e que os
  dois códigos são os publicados. A frase em si continua verificada onde ela é
  contrato — na tela do usuário.

## Verificação

`bash scripts/executar.sh --testes`, **fora do sandbox**, `exit 0`:

```
2649 passed, 5 skipped, 3 xfailed, 859 warnings in 63.97s
132 arquivos web/tests/*.mjs [OK]
```

Baseline: `2621 passed, 5 skipped, 3 xfailed` + 132 `.mjs`. **+28 são exatamente
os casos novos**; skipped, xfailed e a contagem de `.mjs` inalterados.

Recortes das tasks:

- Task 1 — `-k "plan or quota or metering or mcp_cap or assistente or watchlist"`:
  299 passaram (só os 7 casos da Task 2 vermelhos, como esperado). **Nenhum
  teste existente desses domínios precisou mudar.**
- Task 2 — `-k "gate or owner or mcp or plan"`: 498 passaram, 4 skipped.

Front não foi tocado (nada em `web/src/`), então não houve `vite build`.

Índice conferido com `git diff --cached --stat` antes de cada um dos três
commits; os 4 diretórios não rastreados em `.claude/skills/` seguem intocados.
`git diff --diff-filter=D` nos três commits: **nenhuma** deleção de arquivo.

## Deviations from Plan

### 1. [Rule 2 — funcionalidade crítica ausente] `/api/ai/quota` e `/api/watchlist/quota` publicam o limite EFETIVO

- **Encontrado em:** Task 1
- **Situação:** o plano lista os cinco **gates**. As duas rotas de cota são de
  exibição e continuariam publicando `managed.daily_quota()` e o
  `max_watchlist` do dict estático — ou seja, a tela "Atividade da IA" e o
  contador da watchlist diriam um teto enquanto o 402 diria outro. Para o
  `/api/watchlist/quota` é pior: ele é a **única** fonte de `max_watchlist`
  fora de `plan.py` (o `deviceStore` do iOS não pode hardcodar 10, critério 6
  do ROADMAP da Fase 13), então o iPhone mostraria "7/10" e seria barrado em 3.
- **Correção:** as duas rotas passam pela mesma conciliação.
- **Arquivos:** `server/app/main.py`
- **Commit:** `3ab1ea1`

### 2. [Rule 3 — bloqueio] `server/app/assistente.py` precisou de sentinela própria

- **Encontrado em:** Task 1
- **Situação:** o plano pede que o teto do assistente seja resolvido no
  chamador, mas `teto_dia_brl()` é chamada **dentro** de `responder()`. Passar
  o valor pronto exigia parâmetro novo — e `teto=None` como "não informado"
  colidiria com `None` = "plano sem teto", que é valor legítimo no catálogo
  (`TXT_SEM_LIMITE`). O freio de R$ 1,00/dia voltaria calado para o plano
  ilimitado.
- **Correção:** `_TETO_NAO_INFORMADO = object()`, mesma técnica do `_AUSENTE`
  que o 25-03 estabeleceu em `plan.py` e pelo mesmo motivo. Omitir o parâmetro
  (o que todos os testes unitários do módulo fazem) é byte a byte o
  comportamento anterior.
- **Arquivos:** `server/app/assistente.py`
- **Commit:** `3ab1ea1`

### 3. [Registro] `server/tests/test_opcoes_dsl.py` fora da lista de arquivos

O plano lista só `main.py` e `options_mcp_api.py` na Task 2, mas a própria ação
manda atualizar o guardião existente "com nota datada". Ele mora em
`test_opcoes_dsl.py`. Fica registrado para ninguém procurar o diff onde ele não
está.

### 4. [Registro] `_plano_efetivo` devolve o MESMO objeto quando nada mudou

Não é micro-otimização: `test_fase3_gate_plano.py` compara por **identidade**
(`espiao["plan"] is main.plan.ACTIVE_PLAN`). Construir um dict novo
incondicionalmente quebraria esse guardião sem que comportamento nenhum tivesse
mudado — e a alternativa (afrouxar o guardião de `is` para `==`) seria mexer num
teste por conveniência do código novo. "Sem configuração, nada muda" passou a
valer até a identidade do objeto.

---

**Total:** 2 desvios (1× Rule 2, 1× Rule 3) + 2 registros. Nenhum desvio de
escopo — os dois acréscimos são consequência direta do que o plano cobra.

## O que este plano deliberadamente NÃO fez

### `opcoes.criar_setup` NÃO migrou do RBAC para o plano (decisão D2) — PENDÊNCIA NOMEADA

Escopo reduzido por decisão do Alex (2026-09-12, "da forma mais segura e
rápida"), registrado aqui como pendência e **não como esquecimento**.

- **Estado hoje:** `require_criar_setup` continua consultando a permissão
  `opcoes.criar_setup` do RBAC; só quem tem `role_admin` (ou `owner`) cria
  setup.
- **Por que não migrou:** liberar por plano **ampliaria** o acesso — qualquer
  conta `pro` passaria a gravar no armazém compartilhado do serviço MCP, que
  tem teto de 2.000 `tools/call`/dia para a base inteira. Ampliar acesso a um
  recurso compartilhado não é a mudança que se faz "da forma mais segura".
- **O que já está pronto:** `plan.funcoes_do_plano(id)` (25-03) declara
  `opcoes.criar_setup` em `pro` e devolve conjunto vazio para plano
  desconhecido (fail-closed). **Ninguém lê essa função.**
- **O que a migração exige, quando houver planos comerciais reais:** tirar a
  permissão de `GRUPOS["opcoes"]` (`rbac.py`), ajustar
  `ENTIDADES_POR_PERMISSAO` (`rbac.py:121`) e os casos de
  `test_opcoes_dsl.py:341-348`, e decidir o que acontece com quem hoje cria
  setup por papel administrativo e amanhã estaria num plano `free`.

### Outros

- **`plan.py` não foi tocado.** A conciliação mora no chamador; o catálogo
  segue sendo declaração.
- **Nada foi publicado.** Nenhum push, nenhum PR, nenhum `bump.sh`,
  `publicar-web.sh` ou `publicar-admin.sh`. É mudança **só de backend** e exige
  deploy com **bump manual de `SERVER_BUILD_ID`**.
- **Os mutadores de estado do `gsd-sdk` não foram chamados** (decisão do Alex):
  `STATE.md` foi atualizado à mão.
- **A decisão aberta do 25-01 continua aberta** — a ativação do gate mensal em
  `/api/scan/deep`, `/api/carteira-stopalvo` e `/api/assistente`. Os três casos
  seguem na suíte como `xfail(strict=True)` e falham no dia da ativação. Nada
  neste plano a aproximou nem a afastou. **Nota que vale para a decisão:** com
  a Fase 3 no ar, o limite mensal passou a ser configurável por plano — ou
  seja, a opção "ativar junto com os limites novos" (recomendação do 25-01)
  está tecnicamente disponível a partir de agora.
- **`web/src/plan.js` não foi tocado.** O espelho do front continua com `null`
  nos dois planos por desenho; o limite real chega do endpoint, e há guardião
  `.mjs` exigindo isso.

## Threat Flags

Nenhuma. O plano não cria rota, não toca autenticação e não abre superfície
nova. As três mudanças com implicação de segurança são todas **restritivas ou
neutras**:

- a isenção da D3 é **limitada ao cap comercial** e fail-closed (falha de
  leitura de papel = continua barrado);
- os tetos físicos, que são a defesa do serviço compartilhado, não mudaram de
  valor nem de origem — provado por medição;
- o valor vindo do plano para o cap da aba Opções é validado antes de virar cap
  (tipo, `bool`, negativo), pela mesma razão que `_kv_int` já validava: um
  número torto ali seria o freio desligado sobre um teto compartilhado.

## Next Phase Readiness

Pronto para o **25-05** (módulo no portal). O que ele herda:

- os cinco limites **realmente decidem** agora — o painel deixou de ser
  cosmético antes de existir;
- `plan.LIMITES_DE_PLANO` para iterar e `plan.limites_do_plano(id)` para
  renderizar (valor, origem, env, kv, default, tipo);
- **um cuidado novo, que o card `CotaOpcoes` não tinha:** a origem `default`
  agora significa "o resolvedor global manda", não "o valor do plano manda". O
  painel precisa dizer isso, senão o admin verá `60 · default` no plano `free`
  sem saber que quem decide, naquele estado, é o `mcpCotaUsuarioDia` global do
  card vizinho. Os dois cards vão conviver na mesma tela;
- a limitação do 25-03 continua: **não há como LIMPAR um limite gravado no kv**
  (`db` não expõe delete de chave global). Uma vez configurado, o valor vence a
  env para sempre. O 25-05 decide se isso vira um botão "voltar ao padrão".

E para o **25-06** (plano visível no app): `/api/ai/quota` e
`/api/watchlist/quota` já publicam o número **efetivo**, então a tela pode
mostrar o limite real do plano sem hardcodar nada.

**Não está no ar.** Deploy do backend com bump manual de `SERVER_BUILD_ID`.
**Efeito no primeiro request depois do deploy:** nenhum visível — sem kv de
plano configurado, os cinco limites resolvem nos mesmos números, e a conta
âncora (`B3_OWNER_EMAIL`) ganha a isenção do cap comercial que ela, na prática,
provavelmente nunca alcançou.

## Self-Check: PASSED

- `server/app/main.py` — FOUND
- `server/app/options_mcp_api.py` — FOUND
- `server/app/assistente.py` — FOUND
- `server/app/managed.py` — FOUND
- `server/tests/test_opcoes_dsl.py` — FOUND
- `server/tests/test_gates_por_plano.py` — FOUND
- commit `3ab1ea1` — FOUND
- commit `ab632f3` — FOUND
- commit `b45027e` — FOUND
- `git diff --diff-filter=D HEAD~3 HEAD` — **nenhuma** deleção de arquivo
- frontmatter deste SUMMARY e de `STATE.md` validados por `yaml.safe_load`

---
*Phase: 25-planos-comerciais*
*Completed: 2026-09-12*
