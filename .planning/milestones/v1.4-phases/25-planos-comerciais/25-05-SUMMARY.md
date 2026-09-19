---
phase: 25-planos-comerciais
plan: 05
subsystem: api
tags: [plano-comercial, adr-010, adr-013, portal-admin, auditoria, sentinela, guardioes]

requires:
  - phase: 25-planos-comerciais
    provides: "25-03 (`LIMITES_DE_PLANO`, `limites_do_plano`, `set_limite_do_plano`, `funcoes_do_plano`, o sentinela `_AUSENTE`) e 25-04 (a conciliacao `_limite_do_plano`/`_e_limite_por_plano`, e o achado de que `origem: default` num limite de PLANO significa 'quem manda e o resolvedor global')"
  - phase: adr-013
    provides: "auditoria de escrita admin + `ENTIDADES_POR_PERMISSAO` (o mapa que declara cobrir toda entity gravada)"
  - phase: 24-aba-opcoes
    provides: "o card `CotaOpcoes` (24-15) — o molde de previa + origem + auditoria por campo do portal"
provides:
  - "`GET /api/admin/planos`: planos, metadados de cada limite (rotulo, ajuda, tipo, resolvedor global), valor vigente por plano com `origem`/`decide`/`efetivo`, funcoes e `textoSemLimite`"
  - "`POST /api/admin/planos`: previa (sem `aplicar`) e aplicacao tudo-ou-nada, com auditoria de UM evento por campo alterado (entidade `plano_config`)"
  - "`plan.TXT_PADRAO` + `plan.restaurar_padrao_do_plano`: o caminho de VOLTAR AO PADRAO que nao existia — sentinela no kv que o resolvedor le como 'nao configurado'"
  - "`plan.coerce_limite` e `plan.valor_sem_painel`: validar antes de gravar (tudo-ou-nada) e saber ONDE o valor cai ao restaurar"
  - "`web-admin` `PlanosConfig` + `NotaDeOrigem`: o card, com a leitura de `origem: default` explicita na tela"
  - "server/tests/test_admin_planos_config.py (27 casos) + web/tests/test_admin_planos_config_ui.mjs"
affects: [25-06-plano-visivel-no-app]

tech-stack:
  added: []
  patterns:
    - "Sentinela ATRAVESSANDO o kv: uma linha PRESENTE cujo conteudo significa 'nao configurado' — resolve 'desfazer' sem abrir um DELETE de chave global em `db.py`"
    - "Auditoria pelo par `(valor, origem)` e nao so pelo valor: restaurar 10 sobre um padrao 10 nao muda o numero e MUDA quem decide, e essa escrita nao pode ficar sem registro"
    - "Metadado de UI no CHAMADOR: 'quem decide o global' e fato da conciliacao (main.py), nao do catalogo (plan.py) — e por isso mora ao lado dos bindings de `global_fn`"
    - "Iterar o CATALOGO e nao os metadados ao montar a lista: um ponto de controle novo aparece com o nome interno em vez de SUMIR da tela; guardiao exige rotulo proprio"

key-files:
  created:
    - server/tests/test_admin_planos_config.py
    - web/tests/test_admin_planos_config_ui.mjs
  modified:
    - server/app/main.py
    - server/app/plan.py
    - server/app/rbac.py
    - web-admin/src/App.jsx
    - web-admin/src/api.js

key-decisions:
  - "'Voltar ao padrao' virou SENTINELA no kv (`TXT_PADRAO = '__padrao__'`), nao DELETE novo em `db.py`: abrir um delete de chave global daria, de brinde, o poder de apagar qualquer chave global (kill-switch, cota da brapi, prompts) por uma necessidade que e de um campo so"
  - "`null` explicito = voltar ao padrao; `ilimitado` = sem limite. As duas viajariam como `null` no fio e sao OPOSTAS (a segunda e configuracao do plano e VENCE o global) — por isso o texto `ilimitado` e a palavra do backend, nao um `null` reaproveitado"
  - "A auditoria compara `(valor, origem)`: so o valor deixaria sem registro a restauracao que devolve o mesmo numero, que e justamente a mudanca que ninguem consegue explicar depois"
  - "`_META_LIMITES` (rotulo/ajuda/card global) mora em `main.py` e nao em `plan.py`: 'quem decide quando o plano nao decide' e fato da CONCILIACAO, que o 25-04 poe no chamador de proposito; `plan.py` segue declaracao pura e sem importar `managed`/`options_mcp_api`"
  - "O card publica o `efetivo` ao lado do valor do catalogo: quando `decide == global` os dois divergem, e esse e exatamente o estado que o card existe para desfazer"
  - "Duas frases diferentes para `origem: default`, porque a consequencia e diferente: com resolvedor global, existe outro lugar que manda e ele e NOMEADO; sem, o default do catalogo e a ultima palavra mesmo"

patterns-established:
  - "Guardiao ESTRUTURAL de condicional em JSX: em vez de so procurar a regex da condicao, localiza a frase e exige que o `if (` mais proximo acima contenha o valor — pega a frase que 'tem a condicao no arquivo' mas e renderizada solta"
  - "Marcadores de comentario delimitando a regiao somente-leitura (`funcoes do plano — SOMENTE LEITURA` … `fim das funcoes do plano`), para o guardiao recortar e proibir `<button`/`<input`/`onClick` la dentro"

requirements-completed: ["Fase 4 do 25-CONTEXT — módulo de configuração de planos no portal"]

duration: 50min
completed: 2026-09-12
---

# Phase 25 Plan 05: Módulo de planos no portal — Summary

**Os cinco limites e as funções de cada plano deixaram de ser editáveis só por
`sqlite3` no container: há um card no portal que lê, simula, aplica e — o que
não existia em lugar nenhum — DESFAZ uma configuração; e a origem `padrão`,
que o 25-04 identificou como ambígua entre "ninguém configurou" e "quem manda é
o card vizinho", agora diz na tela qual das duas é, nomeando o vizinho.**

## Performance

- **Duração:** ~50 min
- **Tasks:** 3 de 3
- **Arquivos:** 5 modificados, 2 criados

## Task Commits

1. **Task 1: rota de leitura e escrita, com prévia e auditoria por campo** — `dc58bf0` (feat)
2. **Task 2: o card no portal, com a leitura de origem explicada** — `cde55ef` (feat)
3. **Task 3: guardiões** — `3ff1772` (test)

## O problema que o plano nomeou, e como cada metade foi resolvida

### 1. "Voltar ao padrão" não existia — e `null` não servia

A limitação vinha do 25-03 e foi repetida no 25-04: **uma vez gravado no kv, um
limite vencia a env para sempre.** `db` expõe `kv_delete_user` (por usuário) e
**nenhum** delete de chave global.

A saída óbvia — gravar `None` — é a errada, e por um motivo que o próprio 25-03
estabeleceu: **`None` ali é valor legítimo** (`ilimitado`). Usá-lo para as duas
coisas transformaria "voltar ao padrão" em "este plano não tem limite nenhum",
que é o oposto do pedido, e num campo que decide dinheiro.

A escolha foi o **sentinela atravessando o kv** (`plan.TXT_PADRAO =
"__padrao__"`): uma linha **presente** cujo conteúdo significa "não
configurado". É o mesmo truque do `_AUSENTE` que o 25-03 já usa em memória,
agora persistido. `_do_kv` o reconhece e devolve `_AUSENTE`, e a decisão desce
para env → default.

**Por que não um `DELETE` novo em `db.py`,** que o plano deixava como
alternativa: abrir um delete de chave global daria, de brinde, o poder de apagar
**qualquer** chave global — kill-switch do agente, orçamento da brapi, prompts
publicados — por uma necessidade que é de um campo só. O sentinela custa três
linhas e não cria superfície nenhuma.

**Detalhe que a implementação obriga e é fácil esquecer:**
`restaurar_padrao_do_plano` faz `_limites_mem.pop(...)` em vez de guardar o
sentinela no cache. `_valor_e_origem` consulta o cache **por `in`** (porque
`None` é valor), então a marca no cache voltaria como se fosse limite.

**Honestidade sobre o mecanismo:** qualquer texto não-numérico no kv já cairia
em `_AUSENTE` pelo `_numero_valido` — ou seja, o sentinela "funcionaria" por
acidente. O tratamento é **explícito** de propósito, com constante nomeada e
comentário: depender do acidente faria a restauração sumir no dia em que a
validação mudasse, sem nenhum teste reclamar no lugar certo.

### 2. `origem: default` era ambíguo na tela

O 25-04 entregou o achado pronto: num limite de **plano**, `default` não quer
dizer "ninguém configurou nada" — quer dizer **"quem decide este número, hoje,
é o resolvedor GLOBAL"**. O admin veria `60 · padrão` no plano gratuito e
concluiria que o plano define 60.

O backend passou a publicar, por plano × limite, duas coisas que não existiam:

| campo | o que responde |
|---|---|
| `decide` | `"plano"` ou `"global"` — a MESMA pergunta que `_e_limite_por_plano` responde para o gate, agora publicada |
| `efetivo` | o número que **de fato barra**, pelo mesmo `_limite_do_plano` dos call sites reais |

E a tela ganhou **duas frases diferentes**, porque a consequência é diferente:

- **com** resolvedor global (`ia_gerenciada_dia`, `opcoes_chamadas_dia`,
  `assistente_brl_dia`): "sem valor próprio neste plano — quem decide é **Cota
  da aba Opções (aba Fontes de dados)** (`B3_MCP_COTA_USUARIO_DIA`)";
- **sem** resolvedor global (`max_watchlist`, `max_analyses_per_month`): "vale o
  padrão do catálogo, e não há outro lugar que o sobreponha".

Uma frase só, genérica, mentiria em um dos dois casos.

Há ainda um **terceiro** estado, que o plano não pedia e a tela mostra porque o
silêncio ali seria a mesma armadilha: `origem: "env"` numa das três envs
**globais** (`B3_MANAGED_DAILY_QUOTA` etc.) também **não** é configuração do
plano — o catálogo reusa a env que já controla o ponto hoje (25-03), e
`_e_limite_por_plano` a trata como global de propósito. A `NotaDeOrigem`
cobre esse caso com uma terceira frase, condicionada a `decide === "global"`.

### 3. Onde os metadados moram, e por que não em `plan.py`

`_META_LIMITES` (rótulo, ajuda e o **card que decide o global**) ficou em
`main.py`. Não é comodidade: "quem decide quando o plano não decide" é fato da
**conciliação**, que o 25-04 pôs no chamador justamente porque `plan.py` não
pode importar `managed` nem `options_mcp_api` (ciclo). O mesmo arquivo que
declara os bindings de `global_fn` declara os rótulos deles — duas listas em
arquivos diferentes divergiriam na primeira manutenção.

A lista publicada itera **`plan.LIMITES_DE_PLANO`**, não os metadados: um ponto
de controle novo sem rótulo aparece no painel com o nome interno em vez de
**sumir** dele. E há guardião exigindo rótulo próprio, para que a decisão seja
consciente em vez de `assistente_brl_dia` virar título de tela.

### 4. A auditoria compara `(valor, origem)`, não o número

Caso que decidiu o desenho: gravar `10` no free (cujo padrão também é 10) e
depois restaurar. **O número não muda** — mas quem decide passou de painel para
padrão. Auditar só por valor deixaria essa escrita sem registro nenhum, e é
exatamente o tipo de mudança que ninguém consegue explicar três meses depois.

Por isso `anterior`/`novo` viajam como `{"valor": …, "origem": …}` e a condição
de registro é a diferença do par. Um evento por campo, `entity_id` = o plano,
`field` = a chave do limite. Há caso de teste dedicado
(`test_restaurar_sem_mudar_o_numero_ainda_audita`).

`"plano_config"` entrou em `rbac.ENTIDADES_POR_PERMISSAO["usuarios.gerenciar"]`
— a quarta vez que essa entrada é necessária no repo (`mcp_cota`, `user_plan`,
`opcoes_setup` antes dela), e o efeito de esquecer é sempre o mesmo: o evento é
gravado e `entidades_visiveis` o filtra para fora de **todo** filtro, inclusive
o de quem acabou de produzi-lo.

## O contrato de escrita — três entradas, três significados

Esta é a parte do plano em que uma ambiguidade custaria dinheiro, então está
cravada em teste:

| entrada | significa | efeito na origem |
|---|---|---|
| chave **omitida** | não mexer | inalterada |
| `null` **explícito** | voltar ao padrão | deixa de ser `kv` |
| `"ilimitado"` | sem limite — **configuração do plano** | passa a ser `kv` |
| `0` | bloqueia o ponto de controle (valor legítimo, 25-03) | passa a ser `kv` |

`null` e `"ilimitado"` são **opostos** e viajariam parecidos (`null` dos dois
lados do fio, se a segunda fosse representada por `None`): uma devolve a decisão
ao global, a outra a toma do global. A palavra vem do backend
(`textoSemLimite`), não de um literal no portal.

Validação **tudo-ou-nada** antes de aplicar, mesma disciplina de
`_cota_opcoes_pedidos`: metade da mudança de pé deixa o admin sem saber qual
metade.

## O card

Dentro da aba **"Usuários e papéis"**, no mesmo padrão em que `CotaOpcoes` mora
dentro de "Fontes de dados". É a mesma decisão comercial: ali se muda o plano de
**uma conta**, aqui se muda **o que o plano significa**. Em abas separadas, o
admin mudaria um limite sem ver quem está no plano. **Nenhuma aba nova** — o
`VIEWS` continua com 10, e há guardião contando.

Nenhuma lista literal no portal: planos, limites, rótulos, ajuda, tipo, funções,
notas e até a palavra "sem limite" chegam de `api.planosGet()`. O guardião
proíbe explicitamente os nove literais que seriam a segunda cópia do catálogo
(`"free"`, `"pro"`, `"max_watchlist"`, …).

Detalhes que o molde do `CotaOpcoes` já resolvia e foram mantidos: prévia e
aplicação como chamadas **separadas** (a diferença é um `aplicar: true`, e um
flag opcional no meio de um objeto é o que se esquece de passar); campo vazio =
"não mexer"; origem traduzida pelo `ORIGEM_ROTULO` que já existia; **sem
`window.confirm`** — o par simular/aplicar é a confirmação da casa nesta classe.

O botão **"voltar ao padrão"** só aparece com `origem === "kv"`: sem
configuração de painel não há o que desfazer, e o botão seria um no-op que grava
um evento vazio. A prévia da restauração mostra **onde o valor vai cair** (`3 →
10 (volta ao padrão)`), porque "→ (padrão)" sem número faria o admin aplicar sem
saber o destino — `plan.valor_sem_painel` existe para isso.

As **funções do plano** são somente leitura, com a nota de que o RBAC ainda
controla o acesso. D2 segue pendente por decisão do Alex no 25-04, e o guardião
proíbe `<button`, `<input`, `onClick` e `onChange` entre os marcadores.

## RED medido antes de cada correção

**Backend** (`test_admin_planos_config.py`, escrito inteiro antes da rota):

```
27 failed, 53 warnings in 2.78s
```

Zero passaram — a rota não existia, e até o caso do 401 falhava (rota ausente
responde 404). Depois da Task 1: `27 passed`.

**Front** (`test_admin_planos_config_ui.mjs`, escrito antes do componente):

```
25 falha(s)
```

Depois da Task 2: `todos os testes passaram`.

**Ressalva honesta sobre o RED do front:** um punhado de asserções passava no
estado vermelho **por vacuidade** (proibir `<button>` num recorte vazio passa
trivialmente). É por isso que cada recorte tem uma asserção de tamanho mínimo ao
lado — `o bloco do card foi recortado (guarda contra vacuidade)`,
`o bloco das funções foi recortado` — e essas **falharam** no RED, que é o que
torna as proibições significativas depois.

## Os guardiões

**Backend — 27 casos**, todos pelo caminho HTTP completo:

1. **gate** (4): 401 sem sessão, 403 para conta comum, 403 para titular de
   **outra** permissão administrativa (prova que é `usuarios.gerenciar` e não
   "algum admin" — sem isso, trocar por `require_any_admin_permission` passaria
   e um editor de prompts mudaria o cap comercial), 200 com a permissão;
2. **catálogo publicado** (4): planos, chaves, rótulos, tipos, funções; todo
   limite com rótulo próprio; `decide`/`global` por limite; limite configurado
   passa a decidir e **não** contamina o outro plano;
3. **prévia** (2): não escreve nada (provado **relendo** os limites e a
   auditoria depois), e informar o valor vigente não lista mudança;
4. **aplicar** (4): um evento por campo com `entityId`/`field` certos; chave
   omitida não altera; `0` legítimo; `ilimitado` ≠ voltar ao padrão;
5. **voltar ao padrão** (4): a origem deixa de ser `kv`; cai na **env** quando
   ela existe; a prévia mostra o destino; restaurar sem mudar o número **ainda**
   audita;
6. **validação** (5): chave fora do catálogo, plano fora do catálogo nomeando os
   aceitos, tipo errado nomeando o tipo esperado, tudo-ou-nada, `limites` vazio;
7. **auditoria visível** (2): a entidade no mapa **e** o evento chegando ao `GET
   /api/admin/audit` de quem tem a permissão;
8. **funções** (2): publicadas com a nota, e a rota **não** aceita escrevê-las.

A fixture apaga as envs do catálogo — inclusive as **três globais**
(`B3_MANAGED_DAILY_QUOTA`, `B3_MCP_COTA_USUARIO_DIA`, `B3_ASSISTENTE_TETO_BRL`),
que existem de verdade no ambiente de quem roda a suíte. Sem isso o teste
mediria a máquina em vez do código — cuidado herdado do 25-04.

**Front — estático**, com uma técnica nova que vale registrar: em vez de só
procurar a regex da condição, o guardião **localiza a frase** "Sem valor próprio
neste plano", acha o `if (` mais próximo **acima** dela e exige que a condição
contenha `=== "default"`. Isso pega o caso que a regex simples deixa passar: a
condição existir em algum lugar do arquivo enquanto a frase é renderizada solta.

Cada regex de defeito tem asserção de sanidade contra uma string local — inclusive
as duas negativas (a regex da nota **recusa** `origem === "env"`; a do botão
**recusa** um render incondicional).

## Verificação

`bash scripts/executar.sh --testes`, **fora do sandbox**, `exit 0`:

```
2676 passed, 5 skipped, 3 xfailed, 911 warnings in 62.54s
133 arquivos web/tests/*.mjs [OK]
```

Baseline: `2649 passed, 5 skipped, 3 xfailed` + 132 `.mjs`. **+27 são exatamente
os casos novos**; skipped e xfailed inalterados; o `.mjs` a mais é o arquivo
novo.

`cd web-admin && npx vite build`: **verde** (`✓ 55 modules transformed`,
`built in 860ms`).

Recorte da Task 1 (`-k "plan or admin_users or rbac or adr013 or catalogo or
gates"`): **223 passaram**, nenhum teste existente precisou mudar.

Índice conferido com `git diff --cached --stat` antes de cada um dos três
commits; os 4 diretórios não rastreados em `.claude/skills/` seguem intocados.
`git diff --diff-filter=D HEAD~3 HEAD`: **nenhuma** deleção de arquivo.

## Deviations from Plan

### 1. [Rule 3 — bloqueio] `server/app/plan.py` fora da lista de arquivos da Task 1

- **Encontrado em:** Task 1
- **Situação:** a Task 1 lista `main.py` e `rbac.py`, mas a própria ação manda
  implementar "voltar ao padrão" por **sentinela que o RESOLVEDOR trata como
  'sem valor'" — e o resolvedor (`_do_kv`/`_valor_e_origem`) mora em `plan.py`.
  Não havia como cumprir a ação sem tocar o arquivo.
- **Correção:** `TXT_PADRAO`, o ramo explícito em `_do_kv`,
  `restaurar_padrao_do_plano`, `coerce_limite` e `valor_sem_painel`. A fronteira
  de import do 25-03 continua intacta (`plan.py` segue sem importar `managed`
  nem `options_mcp_api`, travado por AST em `test_gates_por_plano.py`).
- **Arquivos:** `server/app/plan.py`
- **Commit:** `dc58bf0`

### 2. [Rule 2 — funcionalidade crítica ausente] o card publica o número EFETIVO

- **Encontrado em:** Task 1
- **Situação:** o plano pede valor + origem por limite. Com `decide ==
  "global"`, o valor do **catálogo** e o que **de fato barra** podem divergir —
  e é justamente esse o estado que o card existe para desfazer. Mostrar só o
  catálogo repetiria, em forma nova, o defeito que o 25-04 corrigiu nas rotas
  de cota: a tela dizendo um teto e o 402 dizendo outro.
- **Correção:** `efetivo` por plano × limite, pelo **mesmo** `_limite_do_plano`
  dos call sites reais (nenhuma segunda implementação da conciliação), e a UI o
  mostra ao lado do valor **só quando os dois divergem**.
- **Arquivos:** `server/app/main.py`, `web-admin/src/App.jsx`
- **Commits:** `dc58bf0`, `cde55ef`

### 3. [Registro] uma terceira frase de origem, que o plano não pedia

O plano pede a linha explicativa para `origem: "default"`. Medindo o
`_e_limite_por_plano` do 25-04, apareceu um caso irmão: `origem: "env"` numa das
três envs **globais** também não é configuração do plano. Deixá-lo mudo
reproduziria a mesma ambiguidade num estado diferente — a `NotaDeOrigem` cobre
os dois, cada um com sua frase, e a condição de `default` continua sendo
exatamente a que o guardião exige.

---

**Total:** 2 desvios (1× Rule 3, 1× Rule 2) + 1 registro. Nenhum desvio de
escopo.

## O que este plano deliberadamente NÃO fez

- **`opcoes.criar_setup` continua sendo do RBAC (D2 pendente).** Escopo
  reduzido herdado do 25-04, por decisão do Alex. A função aparece na tela
  **sem nenhum controle de escrita** e com a nota dizendo quem manda; a rota
  também **recusa** `funcoes` no corpo. Há caso de teste exigindo que
  `"opcoes.criar_setup" in rbac.GRUPOS["opcoes"]` — o dia da migração derruba
  esse caso, que é o ponto.
- **`db.py` não ganhou delete de chave global.** Ver a decisão acima.
- **Nada foi publicado.** Nenhum push, nenhum PR, nenhum `bump.sh`,
  `publicar-web.sh` ou `publicar-admin.sh`. `server/web_dist`,
  `server/admin_dist`, `web/src/version.js` e `SERVER_BUILD_ID` intocados.
- **`web/src/` não foi tocado** — este plano é backend + portal admin. O app
  consumidor é o 25-06.
- **Os mutadores de estado do `gsd-sdk` não foram chamados** (decisão do Alex):
  `STATE.md` atualizado à mão.
- **A decisão aberta do 25-01 continua aberta** (ativar o gate mensal em
  `/api/scan/deep`, `/api/carteira-stopalvo` e `/api/assistente`). Os três casos
  seguem `xfail(strict=True)`. **Nota que vale para a decisão:** com este plano,
  o limite mensal por plano deixou de exigir acesso ao banco para ser ajustado —
  ou seja, a mitigação de "ativar e calibrar" ficou operacionalmente barata.

## Ordem de publicação (quando houver OK humano)

1. **deploy do backend** com **bump manual de `SERVER_BUILD_ID`** (mudança de
   `server/`, sem front novo);
2. **só depois**, `publicar-admin.sh`. O 25-CONTEXT é explícito: portal novo
   contra backend velho chama rota inexistente — o card renderizaria o estado de
   erro do `Estado` em cima de um 404.

Efeito no primeiro request depois do deploy do backend: **nenhum visível**. A
rota nova não é chamada por ninguém até o portal subir, e nenhum limite muda de
valor por ela existir.

## Threat Flags

Duas superfícies novas, ambas com a mitigação dentro do próprio plano — nenhuma
fora do modelo de ameaça que o ADR-013 já cobre:

| flag | arquivo | descrição |
|---|---|---|
| threat_flag: rota de escrita admin | `server/app/main.py` | `POST /api/admin/planos` grava valores que decidem cap comercial. Mitigado: `require_permission("usuarios.gerenciar")` (testado pelos três lados — sem sessão, conta comum, outra permissão admin), validação tudo-ou-nada com tipo e faixa **no backend** (a tela não é o único cliente possível), auditoria por campo com o id de quem clicou |
| threat_flag: escrita em kv global | `server/app/plan.py` | `restaurar_padrao_do_plano` escreve numa chave **global** do kv. Mitigado por construção: a chave é derivada de `kv_key(plano, chave)` com plano e chave **validados contra o catálogo** antes — não há caminho em que o nome da chave venha do corpo da requisição. É por isso que o sentinela foi preferido a um delete genérico em `db.py`, que aceitaria qualquer chave |

Os tetos **físicos** (2.000/dia do serviço MCP, cota da brapi, teto da chave do
servidor, rate por minuto) continuam fora deste card — o rodapé diz isso na tela,
e o ADR-010 (decisão 2) é a razão.

## Next Phase Readiness

Pronto para o **25-06** (plano visível no app). O que ele herda:

- os limites agora são **ajustáveis sem acesso ao banco**, então a tela do
  usuário pode ser calibrada sem deploy;
- `/api/ai/quota` e `/api/watchlist/quota` já publicam o número **efetivo**
  (25-04), que é o mesmo que este card mostra — uma fonte só;
- o vocabulário de origem (`kv`/`env`/`default` → painel/variável/padrão) e a
  distinção "quem decide" já existem traduzidos, se o app precisar dizer ao
  usuário de onde vem o limite dele. **Provavelmente não deve** — é vocabulário
  de operação, não de produto.

## Self-Check: PASSED

- `server/app/main.py` — FOUND
- `server/app/plan.py` — FOUND
- `server/app/rbac.py` — FOUND
- `web-admin/src/App.jsx` — FOUND
- `web-admin/src/api.js` — FOUND
- `server/tests/test_admin_planos_config.py` — FOUND
- `web/tests/test_admin_planos_config_ui.mjs` — FOUND
- commit `dc58bf0` — FOUND
- commit `cde55ef` — FOUND
- commit `3ff1772` — FOUND
- `git diff --diff-filter=D HEAD~3 HEAD` — **nenhuma** deleção de arquivo
- frontmatter deste SUMMARY e de `STATE.md` validados por `yaml.safe_load`

---
*Phase: 25-planos-comerciais*
*Completed: 2026-09-12*
