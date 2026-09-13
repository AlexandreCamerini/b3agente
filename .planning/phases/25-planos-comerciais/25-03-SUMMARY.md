---
phase: 25-planos-comerciais
plan: 03
subsystem: api
tags: [plano-comercial, adr-010, catalogo, kv, precedencia, guardioes, freemium]

requires:
  - phase: 25-planos-comerciais
    provides: "25-01 (conserto do contador mensal) e 25-02 (papel owner) — nao ha acoplamento de codigo; este e a Fase 2 do mesmo 25-CONTEXT"
  - phase: 24-aba-opcoes
    provides: "o padrao `_valor_e_origem` de `options_mcp_api.py` (24-15) — a mais completa das quatro implementacoes de memoria→kv→env→default do repo"
provides:
  - "`LIMITES_DE_PLANO`: declaracao unica dos cinco pontos de controle que variam por plano (chave, sufixo de kv, env, tipo, defaults por plano)"
  - "`limites_do_plano(id)`: valor vigente + ORIGEM (kv|env|default) + env + chave de kv + default + tipo, por ponto de controle"
  - "`set_limite_do_plano(id, chave, valor)`: persiste no kv e invalida cache; recusa lixo em vez de clampar"
  - "`funcoes_do_plano(id)`: conjunto de funcoes de PRODUTO por plano (D2), com `opcoes.criar_setup` declarada em `pro`"
  - "`kv_key`/`env_key`/`reset_cache_planos` — o que a rota admin (25-05) e os testes precisam"
  - "`plan.configure_db(_conn)` em main.py, mesmo padrao das outras quatro injecoes"
  - "server/tests/test_catalogo_planos.py — 31 casos, o guardiao de que sem configuracao nada mudou"
affects: [25-04-gates-leem-o-plano, 25-05-modulo-no-portal, 25-06-plano-visivel-no-app]

tech-stack:
  added: []
  patterns:
    - "Sentinela proprio (`_AUSENTE`) quando `None` e valor legitimo — a quinta variacao do padrao NAO foi inventada, mas a semantica de `None` teve de mudar e isso esta escrito"
    - "Molde de env com `{PLANO}`: uma coluna so decide se a env e por plano ou global, e ela e global exatamente onde o valor de hoje ja e global"
    - "Guardiao que le por AST em vez de `in` quando a docstring cita de proposito o que o teste proibe"

key-files:
  created:
    - server/tests/test_catalogo_planos.py
  modified:
    - server/app/plan.py
    - server/app/main.py

key-decisions:
  - "`plan_at_least` REMOVIDA: orfa desde que nasceu, apontando para um `require_plan()` inexistente, e a D2 escolheu conjunto de funcoes em vez de ordem de tier — manter os dois mecanismos garantiria o dia da divergencia. `_ORDEM_PLANO` fica (tem consumidor real)"
  - "`None` no kv e o `null` do proprio JSON, nao uma string-sentinela: linha AUSENTE e linha com `null` ja sao distinguiveis em `db.kv_get`, e inventar sentinela seria uma segunda convencao para o que o formato ja expressa"
  - "A env dos tres pontos novos e a MESMA que os modulos leem hoje (`B3_MANAGED_DAILY_QUOTA`, `B3_MCP_COTA_USUARIO_DIA`, `B3_ASSISTENTE_TETO_BRL`) — o catalogo espelha a realidade em vez de inventar um segundo numero para o mesmo teto"
  - "`set_limite_do_plano` RECUSA lixo em vez de clampar (divergencia deliberada de `options_mcp_api._set_limite`): la o clamp protege teto fisico compartilhado; aqui `0` e intencao de produto e engolir lixo faria o painel confirmar o que nao foi pedido"
  - "Os tres gates continuam lendo o dict estatico de `current_plan`, nao o catalogo — este plano cria estrutura; ligar e o 25-04"

patterns-established:
  - "Defaults com uma copia so: `PLAN_FREE`/`PLAN_PRO` sao CONSTRUIDOS a partir de `LIMITES_DE_PLANO`, entao o literal e o catalogo nao podem divergir"
  - "Guardiao que crava os numeros por extenso quando o objetivo do plano e NAO mudar nada — ler o mesmo dicionario que se testa acompanharia a mudanca em silencio"

requirements-completed: ["Fase 2 do 25-CONTEXT — catálogo de planos"]

duration: 40min
completed: 2026-09-12
---

# Phase 25 Plan 03: Catálogo de planos — Summary

**`plan.py` era o único bloco de limites 100% literal do app; agora os cinco
pontos de controle que variam por plano são uma declaração única que resolve
por memória → kv → env → default e diz de onde veio cada valor — e há 31 casos
provando que, sem nada configurado, `free` e `pro` decidem exatamente como
decidiam antes.**

## Performance

- **Duração:** ~40 min
- **Tasks:** 2 de 2
- **Arquivos:** 2 modificados, 1 criado

## Task Commits

1. **Task 1: o catálogo com limites e funções** — `eff99ba` (feat)
2. **Task 2: o guardião de que nada mudou** — `b13e746` (test)

**Metadados do plano:** `4e3ac49` (docs)

## O que entrou

### O catálogo (`server/app/plan.py`)

`LIMITES_DE_PLANO` é a declaração única. Cada linha carrega
`(chave, sufixo_kv, env, tipo, {plano: default})`:

| chave | kv | env | free | pro |
|---|---|---|---|---|
| `max_watchlist` | `planoFree.watchlist` / `planoPro.watchlist` | `B3_PLANO_{PLANO}_WATCHLIST` | 10 | `None` |
| `max_analyses_per_month` | `plano{Id}.analisesMes` | `B3_PLANO_{PLANO}_ANALISES_MES` | 30 | `None` |
| `ia_gerenciada_dia` | `plano{Id}.iaGerenciadaDia` | `B3_MANAGED_DAILY_QUOTA` | 20 | 20 |
| `opcoes_chamadas_dia` | `plano{Id}.opcoesChamadasDia` | `B3_MCP_COTA_USUARIO_DIA` | 60 | 60 |
| `assistente_brl_dia` | `plano{Id}.assistenteBrlDia` | `B3_ASSISTENTE_TETO_BRL` | 1.0 | 1.0 |

Os dois primeiros nomes **não mudaram**: têm chamador desde a Fase 12
(`can_analyze`, `can_add_ticker`, `can_grow_watchlist_to`), e renomear
quebraria sem ganho nenhum.

Quatro escolhas que valem registro, porque as três fases seguintes consomem o
formato:

**1. O `tipo` é uma coluna, não inferência.** Um dos cinco é dinheiro (R$/dia);
o painel (25-05) precisa saber renderizar e validar. Inferir do default
falharia justamente onde importa: `pro` tem `None` em dois pontos, e `None` não
tem tipo.

**2. O molde de env decide sozinho se a env é por plano ou global.** Se o nome
contém `{PLANO}`, é por plano (`B3_PLANO_FREE_WATCHLIST`); se não contém, é
global. E é global exatamente nos três pontos cujo valor **hoje já é global** —
reusando a env que já os controla. Uma env única para `max_watchlist`
achataria `free` (10) e `pro` (sem teto) num número só; uma env nova para
`ia_gerenciada_dia` criaria um segundo número para o mesmo teto, e o dia em que
os dois divergissem ninguém saberia qual manda.

**3. O `None` no kv é o `null` do próprio JSON.** `db.kv_get` já distingue
linha ausente de linha com `null` (a primeira devolve o default passado; a
segunda devolve `None` de verdade). Por isso o default passado ao `kv_get` é um
sentinela (`_AUSENTE`) e não `None`: sem isso, "plano sem limite" viraria
"plano não configurado" no primeiro ida e volta, que é o modo silencioso de
transformar um plano ilimitado num plano que cai no limite do free. Na env, que
só carrega texto, "sem limite" se escreve `ilimitado`.

**4. A precedência copiou `options_mcp_api._valor_e_origem`, com duas
divergências declaradas no código:**

- lá, `<= 0` é lixo, porque um `0` no teto do serviço seria o freio DESLIGADO.
  Aqui `0` é valor legítimo — é como um plano bloqueia um ponto de controle.
  Lixo continua sendo negativo, texto, `bool` e não-finito;
- lá, `None` significa "não achei". Aqui `None` é valor, e o "não achei" é o
  `_AUSENTE`.

`set_limite_do_plano` **recusa** lixo (`ValueError`) em vez de clampar com
`max(1, int(n))`. Divergência deliberada: lá o clamp protege um teto físico
compartilhado de quem digitou errado; aqui um `0` é intenção de produto e um
lixo é lixo — engolir em silêncio faria o painel confirmar uma configuração que
não foi a pedida. Aceita texto (`"5"`, `"2.5"`, `"ilimitado"`) porque é o que um
formulário manda.

### As funções de produto (D2)

`FUNCOES_DE_PLANO` declara `opcoes.criar_setup` em `pro` e nada em `free` —
a primeira função de produto comercializável, vinda da decisão D2 (RBAC é
administração, plano é produto). `funcoes_do_plano` devolve **cópia** do
conjunto e conjunto **vazio** para plano desconhecido (fail-closed, igual ao
`current_plan` caindo para `free`). `FUNCOES_CANDIDATAS`
(`agente_autonomo`, `analises_ilimitadas` — as duas que a docstring de
`requires_subscription` já citava) fica registrada e não liberada, para que a
próxima função de produto não nasça como literal solta numa rota.

**Ninguém lê isto ainda.** `require_criar_setup` continua consultando a
permissão do RBAC; a migração é o 25-04.

### A fiação

`plan.configure_db(_conn)` em `main.py`, no mesmo bloco das outras quatro
injeções. Sem ela a camada de kv ficaria inerte e o painel comercial escreveria
num lugar que ninguém lê. Sem conexão, a resolução **degrada** para env →
default — é o que acontece num teste unitário que não quer banco, e é
degradação, não erro.

## A decisão sobre `plan_at_least` — REMOVIDA

Pedida explicitamente pelo plano ("implementar o gate de tier ou remover a
função e a menção; não deixe o docstring mentindo").

**Fatos medidos antes de decidir:**

- zero call sites em `server/app/` e `server/tests/` (o REPORT-01 já a
  registrava assim em 2026-08, e a própria docstring dizia "nenhuma rota usa
  isto ainda");
- o `require_plan()` que a docstring citava como consumidor **nunca existiu**
  em `main.py` — é esboço do ADR-013 (`:393`), não código;
- `_ORDEM_PLANO`, que ela usava, **tem** consumidor real: `main.py:1139` ordena
  `planosDisponiveis` por ela, e `test_admin_plano_usuario.py:273` trava isso.

**Decisão: remover a função, manter `_ORDEM_PLANO`.** A D2 escolheu outro
mecanismo para gate de função — **conjunto de funções por plano**, não ordem de
tier. Manter os dois convites garantiria o dia em que um recurso fosse liberado
por `plan_at_least("pro")` e outro por `funcoes_do_plano`, com regras que
divergem sem ninguém notar. Um ponteiro para código inexistente é pior que
ausência, porque quem lê acredita.

O esboço segue registrado no ADR-013 — **o ADR não foi tocado**: é história, e
história não se reescreve (guardrail do `CLAUDE.md`). A remoção e a razão estão
datadas na docstring de `plan.py`, e há caso de teste que proíbe a volta
(`def plan_at_least` e `plan_at_least(` ausentes de todo `server/app/*.py`).

## O guardião (`server/tests/test_catalogo_planos.py`)

31 casos em 8 blocos. Os valores esperados estão **escritos por extenso** (30,
10, `None`, 20, 60, 1.0) em vez de lidos de `plan.py` — a duplicação é o ponto:
um guardião que lê o mesmo dicionário que testa acompanha qualquer mudança em
silêncio e não guarda nada.

1. sem kv e sem env, os cinco limites dos dois planos são os de hoje, todos com
   `origem: "default"` — mais uma asserção de que o **conjunto de chaves** não
   mudou, para que um ponto de controle novo force uma decisão consciente aqui;
2. `can_analyze` permite em 29, nega em 30, com a frase byte a byte;
3. `can_add_ticker` (`>=`) e `can_grow_watchlist_to` (`>`) idem, com a
   diferença de semântica que separa os dois preservada;
4. precedência kv > env > default, um degrau por caso, mais env mudando em
   runtime e valor do painel sobrevivendo a `reset_cache_planos()`;
5. `None` ≠ `0` no ida e volta pelo kv — com a env declarada de propósito, para
   que um `None` lido como "não configurado" caísse nela e a origem entregasse
   o defeito;
6. lixo no kv (texto, `bool`, negativo, float em chave inteira, lista, dict)
   cai para env/default e **nunca** vira `None`;
7. funções: conjunto, cópia, fail-closed, candidatas não liberadas;
8. fronteira de import por AST, e `plan_at_least` sem definição nem chamada.

### RED medido

Contra o `plan.py` anterior (restaurado por `git checkout HEAD~1 -- server/app/plan.py`,
rodado, e restaurado de volta — nada de `stash`, nada de `reset`):

```
31 errors in 0.14s
```

**Ressalva honesta, porque a distinção importa neste plano:** os 31 deram
ERROR, não FAIL, e todos no mesmo ponto — a fixture chama `plan.env_key`, que
não existia. Ou seja, o RED prova "a API não existia", não "a política estava
errada". Os blocos 2 e 3 (as frases de recusa e os números dos gates) são
**não-regressão**: a lógica deles já passava antes e continua coberta por
`test_fase12_cap_analises.py` e `test_fase12_cap_watchlist.py`, que seguem
verdes sem uma linha alterada. Um teste que passa nos dois estados prova
não-regressão, não a mudança — e é exatamente isso que se queria aqui, já que o
objetivo DESTE plano era não mudar nada.

## Verificação

`bash scripts/executar.sh --testes`, **fora do sandbox**:

```
2621 passed, 5 skipped, 3 xfailed, 809 warnings in 61.67s
132 arquivos web/tests/*.mjs [OK]
```

Baseline: `2590 passed, 5 skipped, 3 xfailed` + 132 `.mjs`. **+31 são exatamente
os casos novos**; skipped, xfailed e a contagem de `.mjs` inalterados.

Nenhum teste existente de plano/watchlist/quota precisou mudar — os 152 casos
do recorte `-k "plan or watchlist or quota or metering"` passaram sem alteração.

Front não foi tocado (nada em `web/src/`), então não houve `vite build`.

## Deviations from Plan

### `server/app/main.py` acrescentado ao escopo — [Rule 3 - Blocking]

- **Encontrado em:** Task 1
- **Situação:** `plan.py` não tinha conexão com o banco. Sem injeção, a camada
  de kv do catálogo nasceria morta em produção — a rota admin do 25-05
  escreveria num lugar que ninguém lê, e a precedência prometida
  ("memória → kv → env → default") seria de três camadas, não quatro.
- **Correção:** uma linha, `plan.configure_db(_conn)`, no mesmo bloco das
  outras quatro injeções (`candle_cache`, `brapi_budget`, `agent_mod`,
  `timing_watch`), com comentário datado dizendo que não muda comportamento.
- **Por que não muda comportamento:** nada lê o catálogo ainda, e sem kv
  configurado a resolução devolve os mesmos defaults.
- **Arquivos:** `server/app/main.py`
- **Commit:** `eff99ba`

Nenhum outro desvio. Os guardiões estáticos de `main.py` que contam ocorrências
(`plan.can_analyze(` ×1, `plan.can_add_ticker(` ×1, `plan.can_grow_watchlist_to(` ×1)
seguem exatos.

## O que este plano deliberadamente NÃO fez

- **Ninguém LÊ o catálogo.** Os três gates continuam lendo o dict estático que
  `current_plan()` devolve. É o 25-04 que troca a fonte, e é lá que a decisão
  "o que acontece quando o kv do plano diz 40 e a env global diz 9" precisa ser
  tomada com nome e sobrenome.
- **Os overrides globais que já existem ficaram fora da cadeia.** O
  `llmDailyQuota` do painel (em `managed`, via `admin_config`) e o
  `mcpCotaUsuarioDia` (em `options_mcp_api`, via kv) **não** são consultados
  pelo catálogo, porque `plan.py` não pode importar aqueles módulos (ciclo — é
  por isso que `options_mcp_api` é fiado por injeção). Consequência real e
  conhecida: se o admin já tiver mexido naqueles dois pelo painel, o catálogo
  reporta o valor da env/default enquanto o serviço aplica o do painel.
  **Conciliar os dois é trabalho do 25-04**, e está escrito na docstring de
  `plan.py` em vez de ficar como surpresa.
- **Não há como LIMPAR um limite gravado no kv.** Uma vez configurado, o valor
  vence a env para sempre (mesma limitação que `options_mcp_api` já tem, pelo
  mesmo motivo: `db` não expõe delete de chave global). O 25-05 decide se isso
  vira um botão "voltar ao padrão" com uma função nova em `db.py`.
- **`web/src/plan.js` não foi tocado.** O espelho do front continua com `null`
  nos dois planos por desenho (o limite real chega do endpoint, critério 6 do
  ROADMAP da Fase 13), e há guardião `.mjs` que exige isso. Nada do catálogo
  precisa aparecer lá antes do 25-06.

## Threat Flags

Nenhuma. O plano não cria rota, não toca autenticação e não altera nenhum
caminho de decisão em produção.

## Next Phase Readiness

Pronto para o 25-04 (gates leem o plano). O que ele herda:

- `limites_do_plano(id)` para trocar a fonte dos três gates, com `origem` para
  a recusa poder dizer **qual** limite bateu (o 25-CONTEXT já pede que
  `options_mcp_api.py:2326` pare de raspar a string `"analises/mes"` e passe a
  código de erro estruturado);
- `funcoes_do_plano(id)` para `require_criar_setup` consultar o plano em vez da
  permissão (D2), lembrando que isso mexe em `ENTIDADES_POR_PERMISSAO`
  (`rbac.py:121`) e em `test_opcoes_dsl.py:341-348`;
- `rbac.OWNER` (do 25-02) para a D3 — pula o cap comercial, **nunca** o teto
  físico;
- a decisão pendente do 25-01 (ativar o gate mensal nas três rotas órfãs),
  cujos três casos estão na suíte como `xfail(strict=True)` e falham no dia da
  ativação.

E para o 25-05 (portal): `LIMITES_DE_PLANO` é o que a rota itera, e
`limites_do_plano` já devolve tudo que o card `CotaOpcoes` renderiza hoje
(valor, origem, env, default) mais o `tipo`, que aquele card não precisava
porque os três tetos dele são inteiros.

**Não está no ar.** É mudança de backend e exige deploy com bump manual de
`SERVER_BUILD_ID`. Sem consequência visível para o usuário: até o 25-04 nada
consome o catálogo, e é por isso que o deploy deste plano pode ir junto com o
do próximo em vez de sozinho.

## Self-Check: PASSED

- `server/app/plan.py` — FOUND
- `server/app/main.py` — FOUND
- `server/tests/test_catalogo_planos.py` — FOUND
- commit `eff99ba` — FOUND
- commit `b13e746` — FOUND
