---
phase: 27-aba-opcoes-sobre-a-carteira
plan: 01
subsystem: api
tags: [fastapi, sqlite-kv, mcp, sha256, rbac, react, capacitor]

requires:
  - phase: 24-aba-opcoes-mcp
    provides: "rotas do serviço MCP autenticado (`options_mcp_api.py`), cap por usuário, ADR-027"
  - phase: 26-b3-opcoes
    provides: "aba Opções no front (`OpcoesScreen.jsx`), `useOpcoesMcp.js`"
provides:
  - "`opcoes_vigias.py` — o conceito 'meus vigias', que não existia em lugar nenhum do sistema"
  - "isolamento por prefixo determinístico no armazém compartilhado do MCP (ensaio E gravação)"
  - "`GET /api/options/vigias` — lista de custo ZERO, para a aba abrir sem gastar cota"
  - "`GET /api/options/mcp/setups` — lista com estado do dia, custo fixo 2"
  - "gate de dono no backend em `/setups/{name}/desativar` (403 `setup_de_outro_dono`)"
  - "filtro de dono em `/leitura/{ticker}`"
  - "`mcpVigias`/`mcpSetupsListar` nos DOIS stores do front"
  - "Emenda 1 do ADR-027 (Decisão 7) com o tratamento datado do legado"
affects: [27-02, 27-03, aba-opcoes, front-opcoes]

tech-stack:
  added: []
  patterns:
    - "namespacing de identidade em armazém de terceiro por hash truncado do uid (nunca o uid)"
    - "índice local por usuário como espelho de metadado que o serviço externo não guarda"
    - "rota de custo zero DELIBERADAMENTE fora do prefixo `/mcp/`, porque o guardião (iv) obriga o cap lá"

key-files:
  created:
    - server/app/opcoes_vigias.py
    - server/tests/test_opcoes_vigias.py
    - server/tests/test_opcoes_vigias_rotas.py
    - web/tests/test_opcoes_vigias_stores.mjs
  modified:
    - server/app/options_mcp_api.py
    - server/app/main.py
    - server/tests/test_opcoes_dsl.py
    - server/tests/test_options_mcp_leitura.py
    - web/src/api.js
    - web/src/persistence.js
    - docs/adr/027-consumo-do-servico-mcp-autenticado.md

key-decisions:
  - "Prefixo = sha256(uid)[:8] + '-' — hash truncado e nunca o uid, porque o nome viaja para um serviço de terceiro visível a todos os clientes dele"
  - "`nome_no_servico` é idempotente por desenho: o ida-e-volta ensaio→gravação passa o nome por ela duas vezes"
  - "A rota de custo zero mora em `main.py` e não em `options_mcp_api.py` — o guardião (iv) obriga toda rota `/api/options/mcp/*` a passar pelo cap"
  - "Ordenação dos vigias: 'quem disparou primeiro' (armed → streak → antiguidade → nome), decisão do executor herdada do protótipo aprovado (27-CONTEXT, Em aberto item 1)"
  - "A antiguidade desempata por POSIÇÃO no índice, não pelo texto de `criadoEm`: `_agora_brt()` grava dd/mm/aaaa e ordenar essa string ordenaria o dia do mês"
  - "Sem campo `meu` nas listagens: numa lista em que tudo é meu, o booleano seria constante"
  - "Legado fora de toda listagem e ainda assim desativável (D6 do Alex, 2026-09-13) — órfão sem porta de saída vira lixo permanente"

patterns-established:
  - "Vazio com MOTIVO em constante de módulo (`MOTIVO_FORA_DO_SERVICO`, `MOTIVO_SEM_DATA`): princípio 4 do CLAUDE.md, sem texto redigitado em dois lugares"
  - "Guardião de paridade derivado da FONTE (igualdade de conjunto extraída do arquivo), nunca de lista redigitada"
  - "Guardião novo só entra depois da injeção de defeito ser de fato exercitada e revertida"

requirements-completed: [SC-1, G2, A3, ADR-027-D7]

duration: 1h 05m
completed: 2026-09-13
---

# Phase 27 Plan 01: Backend de "meus vigias" Summary

**Prefixo determinístico `sha256(uid)[:8]` no nome enviado ao `mcp.semente.dev` (ensaio e gravação) + índice por usuário no kv + duas rotas de listagem (custo 0 e custo fixo 2) + gate de dono no backend — o conceito "meus setups", que não existia em lugar nenhum do sistema, passa a existir.**

## Performance

- **Duração:** ~1h 05m
- **Tasks:** 4 de 5 (a Task 0 foi resolvida pelo Alex; o checkpoint final está ABERTO)
- **Arquivos:** 11 (4 criados, 7 modificados)
- **Suíte canônica:** `2729 passed, 5 skipped, 3 xfailed, 0 failed` + `138/138 .mjs`, exit 0, fora do sandbox
- **Baseline de entrada:** `2691 passed, 5 skipped, 3 xfailed` + `137/137` → **+38 testes pytest, +1 `.mjs`, zero regressão**
- **`npx vite build`:** verde

## Task 0 — resposta do Alex, verbatim

O plano exigia descobrir, ANTES de qualquer código, se `mcp.semente.dev` aceita
um `name` com prefixo. Eu não pude exercitar o serviço sozinho (`MCP_CLIENT_ID`
/`MCP_CLIENT_SECRET` só existem no env do Railway, e a rota exige sessão com
`opcoes.criar_setup`), então devolvi checkpoint com o roteiro pronto. O Alex
rodou contra o serviço REAL. Saída verbatim:

```
--- ENSAIO com prefixo 'abcdef12-teste-fase-27': ACEITO ---
name devolvido: abcdef12-teste-fase-27
status: dry_run

--- ENSAIO de CONTROLE, sem prefixo 'teste fase 27 controle': ACEITO ---
name devolvido: teste fase 27 controle
status: dry_run

=== VEREDITO ===
O servico ACEITA o formato prefixado. Gravando de verdade (confirm=True)...
GRAVADO. name: abcdef12-teste-fase-27 | status: ativo
```

Três fatos **medidos** (não presumidos), e o que cada um destrava:

1. O serviço aceita `[8 hex]-[texto]` como `name` → o desenho de isolamento da
   fase se sustenta; nenhuma alternativa de formato precisou ser considerada.
2. O serviço devolve o `name` **exatamente como enviado** — sem normalizar,
   truncar ou reescrever, no ensaio e na gravação → é o que torna
   `nome_no_servico`/`nome_do_usuario` confiáveis nos dois sentidos. Registrado
   na docstring de `opcoes_vigias.py` e na Emenda 1 do ADR-027.
3. O controle **sem** prefixo também foi aceito → o serviço não impõe formato
   nenhum em direção alguma; a unicidade continua sendo responsabilidade nossa,
   exatamente como o plano previa.

**Setup pré-existente criado:** `abcdef12-teste-fase-27`, PETR4, `ativo`. Ver
"Achado" nº 1 abaixo — ele NÃO é legado para o código, e isso muda o roteiro do
checkpoint final.

## Accomplishments

- **`opcoes_vigias.py`**: as duas metades que resolvem coisas diferentes — o
  prefixo isola no armazém compartilhado (é o que impede A desativar o setup de
  B) e o índice local é o único lugar do sistema com o nome que a pessoa
  escreveu, o ticker e a data (o `list_setups` não devolve nenhum dos três).
- **O ensaio passou a validar o nome REAL.** Até hoje o dry-run mandava um nome
  e a gravação mandava outro; uma recusa de FORMATO só apareceria depois de a
  pessoa pagar 2 chamadas do cap + uma análise de LLM.
- **Gate de dono no backend**, antes do `_cap_check`: 403 sem viagem e sem
  cobrar cota. Legado passa de propósito — é a única porta que remove um órfão.
- **Duas rotas de listagem**, e elas são duas porque são dois custos: a de custo
  ZERO (que a aba usa ao abrir) e a de custo fixo 2 (estado do dia). O custo
  não cresce com o número de vigias — teste parametrizado com 2 e com 10.
- **Emenda 1 do ADR-027**, datada, declarando o que muda, o tratamento do
  legado e — explicitamente — o que NÃO se faz (varrer o armazém).

## Task Commits

1. **Task 1: módulo do índice e do namespacing** — `c327d35` (feat)
2. **Task 2: fiação nas rotas de escrita/leitura + Emenda 1 do ADR-027** — `7a80429` (feat)
3. **Task 3: as duas rotas de listagem + contrato nos dois stores** — `bf07bd0` (feat)

## Injeções de defeito — de fato exercitadas

Toda não-vacuidade exigida foi injetada, o guardião reprovou, e o defeito foi
revertido antes do commit. Nenhuma foi presumida:

| # | Injeção | Guardião que reprovou | Resultado |
|---|---------|----------------------|-----------|
| 1 | `e_meu` → `return True` | `test_opcoes_vigias.py` | 3 testes falharam, inclusive o de isolamento cruzado |
| 2 | gate de `setup_desativar` → `if False:` | `test_desativar_setup_de_outra_conta...` | 200 onde esperava 403 |
| 3 | prefixo fora do `create_setup` do ENSAIO | `test_o_ensaio_valida_o_nome_que_vai_ser_gravado` | nome sem prefixo no argumento espionado |
| 4 | desprefixação fora do `interpretado` | `test_ida_e_volta...` + `test_o_ensaio_valida...` | "o hash vazou para o nome que a pessoa lê" |
| 5 | listagem virando N chamadas (`evaluate` por vigia) | `test_o_custo_e_2_com_dois_vigias_e_continua_2_com_dez` | 9 chamadas a mais com 10 vigias |
| 6 | filtro de dono da listagem desligado | `test_setup_de_outro_dono_e_setup_legado_nao_aparecem...` | vazaram o alheio e o legado |
| 7 | `mcpVigias` apagado do `deviceStore` | `test_opcoes_vigias_stores.mjs` | 2 asserções vermelhas (e o guardião genérico também pegou) |

## Deviations from Plan

### Auto-fixed

**1. [Rule 1 - Bug] Ordenação por `criadoEm` como string produziria ordem errada**
- **Encontrado em:** Task 3.
- **Problema:** o plano especificava desempate por `criadoEm` desc. `_agora_brt()`
  grava `dd/mm/aaaa HH:MM BRT`, e comparar essa string é comparar o DIA DO MÊS:
  `"02/10/2026"` sai antes de `"13/09/2026"` lexicograficamente. A lista sairia
  fora de ordem toda virada de mês.
- **Correção:** o desempate usa a POSIÇÃO no índice. O índice já nasce
  mais-recente-primeiro (`registrar` insere no topo), então a posição É a ordem
  de criação — medida, não reconstruída de um texto de exibição. Documentado na
  docstring de `_ordem_dos_vigias`.
- **Commit:** `bf07bd0`.

**2. [Rule 1 - Bug] `setup_as_interpreted` não-dict derrubaria a rota**
- **Encontrado em:** Task 2.
- **Problema:** `dados.get("setup_as_interpreted") or setup` aceita qualquer
  valor truthy. Com o `dict(interpretado, name=...)` novo, uma resposta
  patológica do serviço (string, lista) viraria `TypeError` → 500.
- **Correção:** guarda `isinstance(..., dict) and ...` antes, nas duas rotas
  (`compilar` e `confirmar`).
- **Commit:** `7a80429`.

**3. [Rule 3 - Blocking] `web/dist` restaurado ao build publicado**
- **Encontrado em:** verificação final.
- **Problema:** o `<verification>` do plano manda rodar `npx vite build` (front
  editado). O build regenerou `web/dist` com hashes de chunk novos **sem** bump
  de versão — e `test_ios_assets.mjs` compara `dist/assets` com
  `web/ios/App/App/public/assets` **quando os dois têm o mesmo carimbo de
  build**. Mesmo carimbo + hashes diferentes = 16 chunks "faltando" no bundle
  do iOS. Suíte vermelha.
- **Correção:** o build rodou e passou verde (que é o que o plano exige), e
  depois `web/dist` foi restaurado a partir de `server/web_dist` — a cópia
  versionada do MESMO build publicado, byte a byte igual à de
  `web/ios/.../public`. `web/dist` é gitignorada e é regenerada pelo
  `bump.sh`/`publicar-web.sh` na etapa humana de publicação. Cópia do build
  novo guardada no scratchpad da sessão.
- **Verificação:** `test_ios_assets.mjs` verde; suíte canônica exit 0.
- **Nada commitado** (artefato gitignorado).

### Desvio de critério de aceite (não de código)

**4. `grep -c "mcpVigias\|mcpSetupsListar" web/src/persistence.js` devolve 6, não 4.**
O critério do plano presumia que o `deviceStore` usaria o estilo
propriedade-seta do `serverStore`. Ele usa método-atalho `async`, então cada
método ocupa DUAS linhas (assinatura + delegação) e `grep -c` conta LINHAS:
2 (serverStore) + 4 (deviceStore) = 6. A substância — os dois métodos nos dois
stores — está provada pelo `test_opcoes_vigias_stores.mjs` (igualdade de
conjunto derivada da fonte) e pela injeção nº 7. Aritmética do plano, não do
código.

### Divergência entre a previsão do plano e o comportamento medido

**5. A injeção nº 4 não produz "prefixo duplo", como o plano previa.**
O plano dizia que tirar a desprefixação do `interpretado` faria o teste de
ida-e-volta "FALHAR com prefixo duplo". Não faz: a idempotência de
`nome_no_servico` absorve o segundo prefixo. O dano REAL é outro e é pior de
diagnosticar — o hash vira "o nome que a pessoa escreveu", na tela **e no
índice**, e a listagem passa a exibir `a1b2c3d4-IFR baixo` para sempre. O teste
foi **reforçado** por causa disso: além do nome na resposta, ele agora afirma
sobre o conteúdo do índice (`opcoes_vigias.listar`). Registrado em comentário
datado no próprio teste.

---

**Total:** 3 auto-fixes (2 bugs, 1 bloqueio), 1 critério de aceite corrigido,
1 previsão do plano corrigida por medição.
**Impacto:** nenhum scope creep. Os dois bugs seriam defeitos em produção; o
terceiro item é higiene de ambiente.

## Achados que exigem decisão do Alex

**1. `abcdef12-teste-fase-27` é "de outro dono" para o código, não legado.**
`abcdef12` casa `^[0-9a-f]{8}-`, então `e_legado()` é **False** e
`e_meu(uid_do_alex, ...)` também é **False**. Consequências concretas: ele
**não vai aparecer** em `/api/options/mcp/setups` nem em `/leitura/PETR4`, e
`/desativar` sobre ele responde **403 `setup_de_outro_dono`**. Isso é o
comportamento CORRETO (é um controle negativo perfeito), mas significa que o
passo 5 do checkpoint final — "prove que a listagem funciona sobre um setup
pré-existente" — não pode usá-lo. O caminho para ter um pré-existente de
verdade está no roteiro do checkpoint abaixo.

**2. `/setups/{name}/grafico` não tem gate de dono, e isso foi deliberado.**
O `<threat_model>` do plano enumera dispositions para `leitura`, `GET /setups`,
`desativar`, `compilar` e `prefixo` — e **não menciona `/grafico`**. Não
expandi o escopo por conta própria (seria Rule 4). Risco residual, medido:
para ver o gráfico do setup de outra conta é preciso conhecer o nome COMPLETO,
incluindo os 8 hexadecimais do hash dela — e nenhuma rota do produto enumera
esses nomes (as duas listagens e a `/leitura` filtram por dono). Não é
enumerável pelo produto, então classifico como **baixo**. Decisão do Alex:
fechar em 27-02/27-03 ou aceitar por escrito.

## Issues Encountered

- **Suíte vermelha depois do build do front** — diagnosticada e resolvida; ver
  desvio nº 3. Não era regressão de código.
- **Nenhum `ENOSPC`.** 64 GiB livres no início, suíte completa rodada duas
  vezes sem incidente.

## User Setup Required

Nenhum. Nenhuma variável de ambiente nova, nenhum pacote novo
(`T-27-SC` do threat model: zero `npm install`/`pip install` nesta fase).

## Checkpoint final — PARTE 2 FECHADA, PARTE 1 AGUARDA PUBLICAÇÃO

O plano termina num `checkpoint:human-verify` com duas partes, e **nenhuma das
duas pode ser automatizada**: a primeira precisa do serviço real com as
credenciais do Railway, a segunda é operação destrutiva sobre dado real de um
armazém compartilhado.

### Parte 2 — limpeza dos antigos: FEITA em 2026-09-13, 12:03 (decisão D6)

O Alex executou a varredura (o agente foi barrado pelo classificador de
permissão nas duas tentativas — credencial de produção + escrita destrutiva em
serviço externo; ele rodou no terminal dele). Saída verbatim registrada:

| nome verbatim | prefixo? | ticker | status antes | ação |
|---|---|---|---|---|
| `PETR4 3 pregões abaixo da média móvel` | NÃO | PETR4 | ativo | **desativado** |
| `Pullback + Confirmação` | NÃO | PETR4 | ativo | **desativado** |
| `VALE3 Pullback + Confirmação Direcional` | NÃO | VALE3 | ativo | **desativado** |
| `abcdef12-teste-fase-27` | sim | PETR4 | ativo | **mantido de propósito** |

O armazém inteiro tinha **4 registros**. Os três legados eram inequivocamente
do Alex (nomes em português, tickers da B3, vocabulário do produto), o que
confirma em retrospecto que a ressalva de "pode haver setup de outro cliente
do serviço" era teórica neste caso — `mcp.semente.dev` é do próprio Alex, como
`boris.semente.dev` e `mydata.semente.dev`. A cautela de não varrer continua
correta como regra; só não tinha mordida aqui.

`abcdef12-teste-fase-27` **fica até a fase fechar** — é o pré-existente que a
Parte 1 usa para provar a listagem e o gate de dono sobre algo que nasceu
antes do índice. Removê-lo é passo de encerramento da fase, não de agora.
Note que ele NÃO é legado para o código (`abcdef12` casa o formato de
prefixo), então serve de controle negativo: `/desativar` sobre ele responde
403 para qualquer conta cujo hash não seja `abcdef12`.

### Parte 1 — validação ao vivo: BLOQUEADA POR SEQUÊNCIA DE PUBLICAÇÃO

Não é pendência de disposição do Alex: ela exige o backend desta fase **no
ar**, e publicar só o backend quebraria "Disparos do setup" e "Desativar" no
app publicado (o front de hoje manda `s.name` sem prefixo → 422). Por isso
**27-01 e 27-02 saem juntos**, e a Parte 1 vira validação conjunta pós-deploy.
Detalhe no achado nº 1 da seção "Achados que exigem decisão do Alex".

**Nada foi publicado e nada foi empurrado a `origin`.** Sem `bump.sh`, sem
`publicar-web.sh`, sem `entregar.sh`. `server/web_dist`, `server/admin_dist`,
`web/src/version.js` e `SERVER_BUILD_ID` intocados.

## Next Phase Readiness

- **27-02 está destravado** no que depende deste plano: o contrato do front
  (`mcpVigias`/`mcpSetupsListar`) existe nos dois stores, e o formato de item
  das duas listagens usa os MESMOS nomes de campo da `/leitura` — a tela não
  precisa de dois renderizadores.
- **Dois campos novos que a tela precisa conhecer:** `nomeNoServico` (é ele que
  vai em `/grafico` e `/desativar`, nunca o `name`) e `noIndice`/`motivo`
  (estados reais a desenhar, não ruído a esconder).
- **O que 27-02 NÃO deve fazer:** chamar `mcpSetupsListar` ao abrir a aba. Ela
  custa 2. A abertura usa `mcpVigias`, que custa zero — é a razão de as duas
  existirem.
- **Bloqueio para publicação:** o checkpoint final precisa ser fechado antes de
  qualquer push da fase (histórico: "fase com checkpoint humano segura o push
  da FASE INTEIRA").

## Self-Check: PASSED

- `server/app/opcoes_vigias.py` — FOUND
- `server/tests/test_opcoes_vigias.py` — FOUND
- `server/tests/test_opcoes_vigias_rotas.py` — FOUND
- `web/tests/test_opcoes_vigias_stores.mjs` — FOUND
- commits `c327d35`, `7a80429`, `bf07bd0` — FOUND em `git log`
- `bash scripts/executar.sh --testes` — exit 0, sem regressão da baseline

---
*Phase: 27-aba-opcoes-sobre-a-carteira*
*Completed: 2026-09-13 (checkpoint final em aberto)*
