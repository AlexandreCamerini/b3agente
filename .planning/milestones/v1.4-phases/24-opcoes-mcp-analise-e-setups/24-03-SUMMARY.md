---
phase: 24-opcoes-mcp-analise-e-setups
plan: 03
subsystem: api
tags: [fastapi, mcp, opcoes, llm, rbac, auditoria, metering, pytest]

# Dependency graph
requires:
  - phase: 24 (plano 01)
    provides: "`options_mcp_api` com `_cap_check`/`_chamada_com_cap`/`_erro_http`/`_frescor*`; `mcp_client` como fronteira única"
  - phase: ADR-013
    provides: "`require_permission`, `rbac.GRUPOS['opcoes']`, `audit.record`, `ENTIDADES_POR_PERMISSAO`"
  - phase: C-32 (main.py)
    provides: "`_gate_analise` — ponto único de gate de análise (plano mensal + IA gerenciada)"
provides:
  - "`mcp_client.list_tools()` — `tools/list` com TTL de 1 h, de graça no teto do serviço"
  - "`McpErroDeTool.bruto` — o `structured_content` da recusa, onde viajam `problems[]` e `known_setups[]`"
  - "`POST /api/options/mcp/setups/compilar` — descrição em PT-BR → setup declarativo, com dry-run obrigatório"
  - "`POST /api/options/mcp/setups/confirmar` — grava o que o usuário viu, sem LLM"
  - "`POST /api/options/mcp/setups/{name}/desativar` — sem frescor bloqueante, por desenho"
  - "`require_criar_setup` — sessão + `opcoes.criar_setup`, falhando FECHADO (503) sem fiação"
  - "`_system_compilador(schema, texto)` — o `system` montado em RUNTIME, puro e testável sem rede"
  - "auditoria `opcoes_setup` gravada e visível pelo mapa do ADR-013"
  - "a fiação de LLM que a Fase 4 (veredito) vai REUSAR, não duplicar (D-24.5)"
affects: [24-04, 24-05, fase-4-veredito, aba-opcoes-front]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "`system` de LLM montado em runtime do contrato vivo do serviço (schema + resource), nunca de constante local — ENG-06 aplicado a prompt"
    - "Campo do usuário sobrescrito DEPOIS da LLM e antes da gravação (`description`/`ticker`), com a razão no comentário"
    - "Dois 402 de significado diferente na mesma rota, com código próprio e texto da aba"
    - "Frescor bloqueante assimétrico: trava o que AFIRMA, libera o que PARA de afirmar"
    - "Auditoria e resposta lendo a MESMA variável de estado, para não poderem divergir"

key-files:
  created:
    - server/tests/test_opcoes_dsl.py
  modified:
    - server/app/mcp_client.py
    - server/app/options_mcp_api.py
    - server/app/main.py
    - server/app/rbac.py
    - server/tests/test_guardrail_imperativo.py
    - server/tests/test_mcp_client.py

key-decisions:
  - "`require_criar_setup` recebe `Depends(require_user)` em vez do header cru — é o que faz a árvore da rota carregar sessão E permissão, que é o que os dois guardiões de cobertura exigem"
  - "Compilar e confirmar reservam 2 (frescor + create_setup), não 1: o cap nunca pode prometer menos do que o consumo real"
  - "Os dois 402 se separam por uma marca do texto de `plan.can_analyze`, com um guardião que trava a marca em vez de deixar a heurística silenciosa"
  - "`McpErroDeTool` ganhou `bruto` (o structured_content inteiro) em vez de um atributo por tool — quem escolhe o que repassar é a rota"
  - "`pregao` das rotas de setup sai de quem MEDIU (`check_data_freshness`), porque `create_setup` não devolve `trading_date` no contrato"

patterns-established:
  - "Prova de não-vacuidade por injeção de defeito, registrada no commit (o 403 e o cap ficam vermelhos quando o gate/contagem some)"
  - "Sentinela `_PADRAO` em helper de teste quando `None` é um CASO do teste, não 'use o default'"

requirements-completed: ["PLANO Fase 5 — backend"]

# Metrics
duration: 25min
completed: 2026-09-11
---

# Phase 24 Plano 03: Criar setup por descrição em português Summary

**Três rotas de escrita trazem a criação de setup para dentro do Boris — compilar (LLM + ensaio obrigatório), confirmar e desativar — com permissão de verdade no backend, `system` montado em runtime do contrato vivo do serviço (zero vocabulário de DSL copiado), `description` provada como a da pessoa, frescor que bloqueia criar mas nunca desligar, e auditoria em tudo que grava.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-09-11T20:25:00Z
- **Completed:** 2026-09-11T20:50:00Z
- **Tasks:** 3
- **Files modified:** 7 (6 modificados, 1 criado)

## Accomplishments

- `mcp_client.list_tools()` — `tools/list` com cache de 1 h, documentado como PROTOCOLO (não conta no teto de 2.000/dia do serviço nem no cap por usuário). É a fonte do `inputSchema` vivo.
- `POST /setups/compilar` (custo 2 + 1 LLM): frescor bloqueante → gate de análise → material do serviço (de graça) → LLM → forma → `create_setup(confirm=false)`. Nada é gravado sem a pessoa ver a interpretação e o backtest.
- `POST /setups/confirmar` (custo 2): grava o objeto que o usuário viu, sem LLM e sem recompilar, com frescor medido de novo.
- `POST /setups/{name}/desativar` (custo 1): **sem** frescor bloqueante — assimetria deliberada e travada por teste.
- `require_criar_setup`: 403 do backend para quem não tem `opcoes.criar_setup`, 401 para anônimo, **503 sem a fiação** (falha fechado).
- Auditoria `opcoes_setup` em confirmar e desativar + a entrada em `rbac.ENTIDADES_POR_PERMISSAO` que faz o admin enxergar o evento.
- 28 testes novos (27 em `test_opcoes_dsl.py` + 1 em `test_mcp_client.py`), todos offline, com **duas provas de não-vacuidade** executadas e revertidas.

## Task Commits

1. **Task 1: `list_tools` no cliente e a fiação de permissão e LLM no `configure`** — `227c178` (feat)
2. **Task 2: o compilador NL→DSL e as três rotas de setup** — `9883d65` (feat)
3. **Task 3: testes da Fase 5 e `FONTES` do guardião imperativo** — `10cfa7d` (test)

## Files Created/Modified

- `server/app/mcp_client.py` — `list_tools()`; `McpErroDeTool.bruto` (o `structured_content` da recusa, com `problems[]`/`known_setups[]` dentro).
- `server/app/options_mcp_api.py` — +3 rotas; `require_criar_setup`, `configure()` estendido; `_material_do_compilador`, `_system_compilador` (puro), `_user_do_compilador`, `_schema_da_tool`, `_texto_do_resource`, `_campo_de`; `_frescor_bloqueante`, `_erro_de_frescor`, `_numero_de`, `_pregao_medido`; `_gate_de_analise`; `_descricao_do_corpo`, `_campos_faltando`, `_setup_do_corpo`, `_lista_verbatim`, `_erro_de_setup_invalido`, `_erro_de_setup_desconhecido`; constantes `SYSTEM_COMPILADOR_CABECALHO`, `PERM_CRIAR_SETUP`, `ENTIDADE_AUDITORIA`, `URI_CREATE_SETUP`, `TOOL_*`, `TIPO_ATIVIDADE`, `DESCRICAO_MAX`, `AVISO_DADO_*`, `AVISO_PLANO_ANALISES`, `AVISO_IA_GERENCIADA`.
- `server/app/main.py` — `configure` passa `require_permission`, `_gate_analise` e a leitura de config.
- `server/app/rbac.py` — `"opcoes.criar_setup": {"opcoes_setup"}`, substituindo a nota "entra na Fase 5".
- `server/tests/test_opcoes_dsl.py` — 27 testes da Fase 5, offline.
- `server/tests/test_guardrail_imperativo.py` — `SYSTEM_COMPILADOR_CABECALHO` em `FONTES`.
- `server/tests/test_mcp_client.py` — `list_tools` no `_SessaoFalsa` + teste de cache/TTL.

## Verificação

Suíte canônica inteira, FORA do sandbox (`bash scripts/executar.sh --testes`):

```
2407 passed, 5 skipped, 597 warnings in 55.34s
128 arquivos web/tests/*.mjs [OK]
exit=0
```

Baseline antes deste plano: **2379 passed, 5 skipped** (128 `.mjs`). Delta: **+28 passed**, zero regressão, zero skip novo.

Demais critérios do plano:

- `grep -c "async def list_tools" server/app/mcp_client.py` → **1**, e a função usa `TTL_ESTATICO_S`.
- `grep -n "require_permission_dep\|gate_analise\|config_do_usuario" server/app/main.py` → as três na chamada de `configure`.
- `grep -n "opcoes_setup" server/app/rbac.py` → a entrada nova.
- `grep -c "@router.post" server/app/options_mcp_api.py` → **5** (2 do 24-01 + 3 aqui).
- `grep -rn "indicator\s*==\|crosses_above\|bullish_engulfing\|rel_volume" server/app/options_mcp_api.py` → **nada**.
- `git diff --stat server/requirements.txt server/requirements-prod.txt` → **vazio** (nenhuma dependência nova).
- `configure(conn, require_user)` sem kwargs continua válido (os três extras são keyword-only com default `None`).
- As três rotas novas aparecem com `require_criar_setup` **e** `require_user` na árvore de dependências (verificado via `tests/rotas_fastapi.todas_as_rotas`), e `test_adr013_cobertura_rotas` segue com a allowlist pública em 19.

**Provas de não-vacuidade** (executadas e revertidas, árvore limpa depois):

1. Trocando `Depends(require_criar_setup)` por `Depends(require_user)` nas três rotas:
   ```
   FAILED tests/test_opcoes_dsl.py::test_sem_a_permissao_as_tres_rotas_de_escrita_sao_403_e_nao_tocam_o_servico
   FAILED tests/test_opcoes_dsl.py::test_sem_a_fiacao_de_permissao_a_rota_de_escrita_falha_fechado
   2 failed, 25 passed
   ```
2. Injetando `cap.consome(2)` logo depois do material do compilador (simulando `tools/list`/`resources/read` cobrando cap):
   ```
   FAILED tests/test_opcoes_dsl.py::test_tools_list_e_resource_nao_consomem_cap
   1 failed, 26 passed
   ```

## Decisions Made

- **`require_criar_setup` depende de `require_user` por `Depends`, não do header cru.** O plano descrevia a assinatura `(authorization: Header)`, no molde do `require_user` local. Seguir isso deixaria `require_user` FORA da árvore de dependências das três rotas — e o guardião (iv) de `test_mcp_guardioes` reprova toda rota `/api/options/mcp/*` sem esse nome. Recebendo o `user` já resolvido e repassando à dependency de `main.py`, a árvore carrega os dois nomes e a sessão é resolvida uma vez só.
- **Compilar e confirmar reservam 2, não 1.** O `<guardrails>` do plano diz "compilar 1, confirmar 1", mas o próprio corpo da Task 2 manda medir frescor nas duas (e o teste 14 conta consumo 2). A régua da casa, escrita no 24-01, é que o cap nunca prometa menos do que o consumo real — reservar 1 e gastar 2 faria o cap mentir. Reservei o número de chamadas possíveis; o não consumido volta na saída do `with`.
- **Os dois 402 se separam por uma marca do texto do gate, com guardião.** `_gate_analise` é ponto único e devolve TEXTO. Reimplementar aqui a regra do plano mensal para descobrir a causa duplicaria o gate; classificar pelo texto é frágil sozinho — por isso `_MARCA_DO_GATE_MENSAL` vem acompanhada de `test_marca_do_gate_mensal_ainda_existe_em_plan`, que quebra ALTO se `plan.py` mudar a frase.
- **`McpErroDeTool.bruto` em vez de um atributo por tool.** `problems[]` e `known_setups[]` são de tools diferentes; promover cada um a atributo faria a classe crescer a cada tool nova. A rota lê a chave que espera e nunca devolve o blob inteiro.
- **Auditoria e resposta leem a MESMA variável de estado.** O estado vem do serviço (`dados["status"]`); um log dizendo "ativo" enquanto a tela mostra outra coisa seria pior que não logar.
- **Validação de forma ANTES da sobrescrita de `description`.** Ordem do plano, mantida: a sobrescrita existe contra a paráfrase (tampering), não para suprir um campo que a IA não produziu. Resposta sem `description` é resposta que não seguiu o contrato — e compilar em cima dela seria confiar no que não dá.

## Deviations from Plan

### Auto-fixed / ajustes de execução

**1. [Rule 3 — contradição com guardrail] assinatura de `require_criar_setup`**
- **Found during:** Task 1
- **Issue:** a implementação literal do plano (`authorization: Header`) deixaria `require_user` fora da árvore de dependências, reprovando o guardião (iv) de `test_mcp_guardioes` — o mesmo guardião que o plano manda manter verde.
- **Fix:** `def require_criar_setup(user: dict = Depends(require_user))`, repassando o `user` resolvido à dependency de `main.py`.
- **Verification:** as três rotas listam `['require_criar_setup', 'require_user']`; `test_mcp_guardioes` e `test_adr013_cobertura_rotas` verdes.
- **Committed in:** `227c178`

**2. [Rule 3 — a informação acionável não cabia na exceção] `McpErroDeTool.bruto`**
- **Found during:** Task 1 (previsto para consumo na Task 2)
- **Issue:** o plano exige `problems` item a item e `known_setups` verbatim, mas `McpErroDeTool` só carregava `available`/`hint` — a lista morria dentro do `mcp_client`.
- **Fix:** atributo `bruto` com o `structured_content` da recusa, default vazio (nenhuma recusa antiga muda de forma).
- **Committed in:** `227c178`

**3. [Rule 3 — ordem de definição] `_gate_analise` passado como lambda**
- **Found during:** Task 1
- **Issue:** `options_mcp_api.configure(...)` é chamado em `main.py:~190`, e `_gate_analise` só é definido ~330 linhas abaixo (depende de `plan`/`managed`). Passá-lo direto seria `NameError` no import.
- **Fix:** `gate_analise=lambda scope, config: _gate_analise(scope, config)` — o nome se resolve na chamada. A alternativa (descer a fiação) mudaria a ordem de registro das rotas do router, que a F1 fixou ali de propósito.
- **Committed in:** `227c178`

**4. [Rule 1 — bug achado pelo teste] `pregao` saía `None` com o frescor medido na mão**
- **Found during:** Task 3
- **Issue:** as rotas de setup liam `pregao` da resposta de `create_setup`, que **não** devolve `trading_date` no contrato. A tela mostraria "pregão desconhecido" ao lado de um frescor "em dia" — duas afirmações contraditórias no mesmo corpo, a classe do achado A-08.
- **Fix:** `_pregao_medido(frescor, dados)` — lê do bruto de `check_data_freshness` (quem mediu), com a resposta da tool como segunda porta. `None` continua sendo a resposta quando nenhum dos dois traz data.
- **Verification:** `test_compilar_devolve_dry_run_com_o_backtest_verbatim` assere `pregao == "2026-09-10"`.
- **Committed in:** `10cfa7d`

**5. [Rule 2 — validação de entrada] `DESCRICAO_MAX`**
- O plano só previa `descricao_ausente`. A descrição vai inteira para dentro de um prompt pago (a chave do servidor, no caminho gerenciado): sem teto, uma colagem de 200 KB viraria uma conta que ninguém pediu. 422 `descricao_longa` acima de 2.000 caracteres.

**6. [Rule 2 — superfície de prompt injection] descrição delimitada e rotulada**
- O texto da pessoa é dado, não instrução. Vai entre marcas `<<<DESCRICAO … DESCRICAO>>>` e rotulado como "escrita pela pessoa" — sem isso, "ignore as regras acima" chegaria ao modelo indistinguível do `system`. É a mitigação do T-24-12 no lado da entrada; a do lado da saída (validação de forma + `create_setup(confirm=false)` como validador semântico) é a do plano.

**7. [ajuste] códigos de erro nomeados pelo executor**
- O plano nomeou `descricao_ausente`, `compilacao_invalida`, `forma_invalida`, `setup_invalido`, `dado_atrasado`, `plano_analises`, `ia_gerenciada`. Nasceram aqui: `descricao_longa`, `setup_ausente` (corpo de `/confirmar` sem setup) e `setup_desconhecido` (`deactivate_setup` com nome que não existe).

**8. [ajuste] `motivo` do 409 com DOIS valores, e forma uniforme**
- O plano escreveu `"idadeHoras"|"motivo": "nao_medido"`. Chave que aparece e some obriga o front a testar existência em vez de valor (decisão do 24-01): o 409 traz sempre `motivo` (`"atrasado"` | `"nao_medido"`), `idadeHoras`, `slaHoras` e `frescor`, com `None` onde não se aplica.

### Divergências de contagem nos critérios de aceite (não são defeito)

**9. `grep -c "audit.record" server/app/options_mcp_api.py` dá 3, não 2.** São as 2 chamadas reais (confirmar e desativar) + 1 menção no comentário que explica de onde vem a entidade. A régua que interessa — duas gravações — está cumprida; `grep -n` mostra as linhas 1966 e 2017 como código e a 58 como comentário.

**10. Contagem de testes acima do pedido.** O plano pedia ≥15 e listou 15 afirmações; o arquivo tem 27 (todas as 15 cobertas, algumas parametrizadas, mais: 503 sem fiação, entidade no mapa do RBAC, `conditions` vazia, descrição/ticker vazios, `LLMUserError` → 400, material ausente → 422, `known_setups` verbatim, corpo torto no confirmar, devolução de reserva no 409).

---

**Total deviations:** 6 ajustes de execução + 2 divergências de contagem. Nenhuma mudança arquitetural; nenhuma dependência nova.
**Impact on plan:** nenhum item do plano deixou de ser entregue.

## Issues Encountered

- **`None` como "use o default" num helper de teste.** `_material(monkeypatch, schema=None)` significava "o serviço não publicou o schema" e o default do parâmetro era `None` — o caso de teste virava o caso feliz, em silêncio. Resolvido com sentinela `_PADRAO`. Vale como lembrete: em helper de teste, `None` costuma ser um CASO, não uma ausência.
- **A forma real de `check_data_freshness` continua não confirmada ao vivo.** `_numero_de` aceita cinco grafias de idade e quatro de SLA pela mesma razão que `_frescor` é tolerante desde a F1 — mas o `idadeHoras` do 409 só se prova de verdade com credencial (ver Pendências).

## Known Stubs

Nenhum. Este plano não toca front: nenhuma tela consome as três rotas ainda (é o 24-04 que faz a fiação). As rotas respondem dado real do serviço ou erro declarado.

## Pendências de verificação (declaradas)

- **D-24.7 — nada foi exercitado AO VIVO.** `MCP_CLIENT_SECRET` fora do ambiente. Em particular: (a) a forma real de `inputSchema` e do resource `mydata://tools/create_setup`, que o `_system_compilador` serializa; (b) a grafia real de idade/SLA dentro de `check_data_freshness`, que decide se o 409 mostra número ou `null`; (c) se `create_setup(confirm=true)` devolve `status: "ativo"` como o contrato diz.
- **Nenhuma chamada de LLM real foi feita.** `llm._call_llm` é substituído em 100% dos testes. Que um modelo de verdade devolva JSON compilável a partir do `system` montado é a primeira coisa a exercitar quando houver credencial — e é o que decide se `MAX_TOKENS_COMPILADOR = 1500` é suficiente.
- **O front não existe.** `/setups/compilar` responde, mas ninguém a chama ainda.

## Threat Flags

Nenhuma superfície nova fora do `<threat_model>` do plano. T-24-10 (permissão) tem prova por injeção de defeito; T-24-11 (`description`) e T-24-12 (resposta da LLM) têm teste dedicado, com a delimitação do texto do usuário somada do lado da entrada; T-24-13 (auditoria) grava e é visível pelo mapa do ADR-013; T-24-14 usa `llm.public_error`, já sanitizado; T-24-15 é o 409; T-24-SC: nenhum pacote instalado.

## Next Phase Readiness

Pronto para o **24-04** (front da Fase 5): as três rotas respondem, o envelope é estável (`pregao`/`fonte`/`at`/`frescor`/`cap` em todas), o 422 de `setup_invalido` já vem com a lista de `problems` pronta para a tela listar item a item, e o 409 traz `motivo` para a tela escolher entre "atrasado" e "não medido" sem raspar texto.

A Fase 4 (veredito) REUSA a fiação criada aqui (`configure` estendido, `_gate_de_analise`, os dois 402, `ai_activity`) — D-24.5 cumprido; duplicá-la seria o defeito.

Bloqueio conhecido para a publicação: nada deste plano vai ao ar sem o deploy do backend do 24-05, que só roda com o OK explícito do Alex.

---
*Phase: 24-opcoes-mcp-analise-e-setups*
*Completed: 2026-09-11*

## Self-Check: PASSED

Arquivos afirmados existem (`test_opcoes_dsl.py`, `options_mcp_api.py`, `mcp_client.py`, este SUMMARY) e os três commits estão no histórico (`227c178`, `9883d65`, `10cfa7d`). Coleta do pytest: 27 testes em `test_opcoes_dsl.py`; suíte canônica em 2407 passed / 5 skipped com exit 0.
