---
quick_id: 260909-waw
titulo: "Aba Opções — Fase 1: ADR-027, cliente MCP, cap por usuário, guardiões"
status: complete
data: 2026-09-09
base: 9e46b68041dfb16fc3976c7c87d42bcbdc6b038a
branch: worktree-agent-a43d78d0303f28b21
commits:
  - 0568271 "feat(260909-waw): ADR-027, pins e guardioes invertidos (aba-opcoes F1)"
  - 0a38cda "feat(260909-waw): mcp_client, fronteira unica do ADR-027 (aba-opcoes F1)"
  - 63d038b "feat(260909-waw): rota /status, cap por usuario em SP e fiacao (aba-opcoes F1)"
suite:
  backend: "2225 passed, 4 skipped (baseline 2026-09-08: 2110 passed)"
  web: "124/124 arquivos OK"
  ressalva: "o wrapper `scripts/executar.sh --testes` cai no venv do clone principal, que ainda não tem o `mcp` — uma linha de pip resolve, ver §4"
deploy: nenhum (sem bump, sem publicar, sem railway)
front_tocado: não
---

# Quick 260909-waw — Aba Opções, Fase 1

Fronteira nova do ADR-027 aberta: um cliente único do serviço MCP autenticado
(`mcp.semente.dev`), cap por usuário/dia ancorado em São Paulo, uma rota
(`GET /api/options/mcp/status`) e os guardiões que passam a valer. Nada de
front, nada de deploy, `docs/PLANO-aba-opcoes.md` intocado.

---

## 1. DECISÃO PARA O ALEX CONFIRMAR — `/status` responde 200 com `bloqueia: true`

**Duas regras do plano se cruzam em `/status` e uma tinha de ceder.**

- O mapeamento HTTP do ADR-027 manda `McpErroDeTool → 422`.
- A Decisão 8 do mesmo ADR manda `bloqueia = negociacao_b3 fora de em_dia
  **OU** warning presente **OU** erro da tool`.

Se `/status` devolvesse 422 quando a tool falha, a tela não teria **nada** que
mostrar — e "idade desconhecida" viraria silêncio, que o usuário lê como "em
dia". É exatamente o que a Decisão 8 existe para impedir, e é o princípio 9 do
CLAUDE.md (estados completos).

**Implementado:** `/status` captura `McpErroDeTool` e responde **200**, com
`frescor.warning = <mensagem da tool>` e `frescor.bloqueia = true`. O **422
segue valendo** no helper `_erro_http`, que as rotas de leitura das Fases 2+
usam — ali o erro da tool é falha do PEDIDO (ticker errado, vencimento
inexistente), não um estado a exibir.

Os dois caminhos estão testados
(`test_erro_de_tool_no_status_e_200_com_bloqueia_true` e o `_erro_http`
exercitado pelos casos de teto/indisponibilidade). **Se o Alex preferir 422 em
`/status` também, é uma linha** — mas a tela da Fase 2 precisará de outro jeito
de saber o pregão e o frescor.

---

## 2. O que mudou

### ADR-027 (`docs/adr/027-consumo-do-servico-mcp-autenticado.md`)
Transcreve o §2 do plano aprovado: 10 decisões, contexto, consequências e a
lista de guardiões. Substitui as Decisões 1 e 2 do ADR-024 — os dois motivos
originais caíram (`mcp.semente.dev` é outro processo, com dado real; o
transporte é streamable-http, não stdio). A Decisão 3 do ADR-024 (canal único
do MyData) permanece. O ADR-024 **não** foi editado: quem o substitui é este.

### `server/app/mcp_client.py` — a fronteira única
- Único módulo de `server/app/` que importa `mcp`/`httpx2`, provado por
  **igualdade de conjunto** (não denylist).
- Token `client_credentials` **à mão**, não pelo `ClientCredentialsOAuthProvider`:
  o `async_auth_flow` do provider segura um lock durante o round-trip inteiro e
  serializaria todas as chamadas MCP do processo. Lock só na renovação, com
  double-check; renova 5 min antes do `exp`; um `AsyncClient` por processo;
  `Semaphore(4)`.
- **Import do SDK é tardio, dentro das funções.** `main.py` importa este módulo
  na cadeia de boot — SDK ausente derrubaria o app inteiro em vez de só a aba.
  Efeito colateral verificado na prática: com o venv sem `mcp`, o app sobe e
  2217 testes passam (§4).
- Tradução de erro: `error` no `structured_content` **mesmo com
  `is_error: false`** → `McpErroDeTool`; `MCPError` com `-32000` →
  `McpTetoAtingido` com o `data` do serviço preservado; 401/403 →
  `McpNaoAutorizado`; resto → `McpIndisponivel` com **só `type(e).__name__`**,
  nunca `{e!r}` (o repr de um erro do stack HTTP arrasta headers, e o header
  que este módulo escreve é o `Authorization`).
- Cache L1 só no sucesso (A-07 do ADR-020): 900 s default, 600 s no frescor,
  3600 s em prompt/resource. `reset_cache()` limpa o token junto.

### `server/app/options_mcp_api.py` — rota, cap e degradação
- `GET /api/options/mcp/status`, `Depends(require_user)` (delegado do `main`
  via `configure()`, sem import circular) + `_cap_check` antes de chamar.
- Seções próprias `mcpUsage` / `mcpUsageGlobal` / **`mcpUsageMonth`**. A mensal
  própria não é arrumação: sem ela, cada chamada de tool queimaria o balde
  mensal de análises do plano comercial (`aiUsageMonth`, ADR-010) — o usuário
  perderia análise de IA por olhar a aba Opções.
- O `reason` do metering é **descartado**: o texto dele fala de BYOK e mandaria
  o usuário configurar uma chave de LLM que não resolve nada aqui.
- `pregao` é `None` quando a resposta não traz pregão. Nunca fabricado.
- `frescor` é tolerante à FORMA (a forma real de `check_data_freshness` só se
  confirma ao vivo) e devolve `bruto` inteiro — a Fase 2 lê a forma real dali
  sem gastar outra chamada.

### `server/app/metering.py` — achado que mudou o desenho
**`_now` nunca decidiu o dia.** `check(..., _now=...)` só alimenta o rate limit
(`now - t < 60.0`, epoch float); o dia sempre saiu de `_today()`, em UTC, sem
ponto de injeção. Sem isso, o cap do usuário viraria **três horas antes** do
teto do serviço (que reinicia às 00:00 America/Sao_Paulo) — o app liberaria
chamada que o serviço já estaria recusando.

Overrides `_dia`/`_mes` **opcionais**, default `None` = comportamento anterior
byte a byte (nenhum call site de IA gerenciada mudou), mais `used()` (espelho
diário de `month_used`). Travado por
`test_dia_do_cap_vira_a_meia_noite_de_sao_paulo_nao_em_utc`: 02:30 UTC de 10/09
é `2026-09-09` em SP, enquanto UTC diria `2026-09-10`.

### Guardiões
| Guardião | Estado | Nota |
|---|---|---|
| A (módulos puros) | atualizado | ganhou `httpx2` — `"httpx2" != "httpx"` passava batido no filtro por igualdade |
| B (importador de `mcp`) | **invertido** | de "nenhum módulo" para "exatamente `{mcp_client}`", por igualdade de conjunto |
| B-requirements | **invertido** | de "proibida" para "`mcp>=2.1,<3` presente e IDÊNTICO nos dois arquivos" |
| C, D, E, ENG-04, ENG-06 | intocados | — |
| (i) sem fixture/`MYDATA_MODO`/`b-mcp` na fronteira | novo | + contra-guardião contra vacuidade |
| (ii) só as 2 URLs do contrato em `mcp_client.py` | novo | + contra-guardião: as constantes têm de existir |
| (iii) sem literal com formato de segredo em `server/app/` | novo | parametrizado por módulo, varre o app inteiro |
| (iv) toda rota `/api/options/mcp/*` com `require_user` E `_cap_check` | novo | assert de não-vacuidade explícito |
| (v) `consume` sempre com `month_section` própria | novo | resolve `Name` → constante do módulo |
| 401 sem `Authorization` (comportamento) | novo | prova que a delegação é real, não só um nome |

As reversões de B e B-requirements estão registradas **com nota datada** na
docstring de `test_opcoes_fronteira.py` — nenhum guardião foi apagado.

### RBAC
Grupo `opcoes` com `opcoes.criar_setup` (ADR-027 §2.7). Bootstrap passa de 8
para 9 permissões. `ENTIDADES_POR_PERMISSAO` **não** ganhou entrada: nenhum
`audit.record` grava entidade de setup ainda, e o contrato documentado do mapa
é "cobre toda `entity` HOJE gravada" — entra na Fase 5, com a rota de escrita.

---

## 3. Desvios do plano (todos documentados, nenhum arquitetural)

1. **[Rule 1 — bug] `url()` saiu de dentro do `try` do `_access_token`.**
   Avaliado como argumento de `http.post(...)`, o `ValueError` de `MCP_URL` com
   esquema inválido era capturado pelo `except Exception` e virava
   `McpIndisponivel` — a rota diria "o serviço não respondeu" para um problema
   que nenhum retry resolve. Pego pelo teste
   `test_mcp_url_com_esquema_invalido_vira_503_e_nunca_500`.
2. **[Rule 3 — bloqueio] `metering._resolve_dia`/`_resolve_mes`.** O plano
   pedia `_today(_dia)` chamado direto no corpo. Isso quebra
   `test_fase5_gate_mensal`, que monkeypatcha `_today`/`_month` por lambdas de
   **zero argumentos** (`TypeError` em vez de guardião). Os helpers resolvem o
   override antes e só chamam a função sem argumento quando não há override; o
   parâmetro segue na assinatura, como o plano pediu.
3. **[Rule 2 — degradação] `_erro_http` também mapeia `ValueError` → 503
   `mcp_nao_configurado`.** Sem isso, `MCP_URL` torta cairia no handler
   genérico de 500, e o ADR-027 exige que nada da aba caia nele.
4. **Guardião (v) resolve `Name` → constante do módulo** em vez de exigir o
   literal na chamada. O plano dizia "literal `"mcpUsageMonth"`" no guardião e
   `month_section=MONTH_SECTION` no código — incompatíveis. Resolver é o único
   caminho que satisfaz os dois E é mais estrito: pega
   `month_section=OUTRA_COISA`, que o literal cru deixaria passar.
5. **`ResultadoTool.dados` anotado `Any`, não `dict`.** `call_tool` devolve
   dict, mas `get_prompt`/`read_resource` devolvem o objeto do SDK — `dict`
   seria mentira para dois dos três.
6. **Guardião (iv) precisou achatar rotas recursivamente** (ver achado abaixo).

---

## 4. Suítes — o que rodou, literalmente

### Ressalva de ambiente (uma linha de pip resolve)

`bash scripts/executar.sh --testes` chama `scripts/test.sh`, que **de propósito**
cai no venv do clone principal quando roda de worktree:

```
usando o venv do clone principal: /Users/acamerini/dev/bolsia/b3-agente/server/.venv/bin/python
8 failed, 2217 passed, 4 skipped, 393 warnings in 46.44s
```

As **8 falhas são todas `ModuleNotFoundError: No module named 'mcp'`**
(confirmado: `grep -c "No module named 'mcp'"` = 8), nos 8 testes de
`test_mcp_client.py` que constroem a sessão falsa. Esse venv tem fastapi
0.141.1 / starlette 1.6.0 / pydantic 2.13.4 / uvicorn 0.52.1 e **não tem o
`mcp`** — é o efeito esperado de uma fase que ACRESCENTA dependência, não uma
regressão de código.

**Ação do Alex (1 comando):**
```bash
/Users/acamerini/dev/bolsia/b3-agente/server/.venv/bin/python -m pip install -r server/requirements.txt
```

*Detalhe que vale registrar:* que 2217 testes passem sem o SDK instalado é a
prova viva do import tardio — o app sobe inteiro sem o `mcp`, e só a aba Opções
degrada. Era exatamente o desenho pedido.

### Backend, com interpretador que tem a dependência

```
cd server && /Users/acamerini/dev/borisv2/server/.venv/bin/python -m pytest -q
2225 passed, 4 skipped in 45.12s
```

Baseline de 2026-09-08 (STATE.md, quick 260908-ldg): **2110 passed**. Sem
regressão; +115 vêm dos arquivos novos (o guardião (iii) é parametrizado por
módulo de `server/app/`).

Os 4 `skipped`: 3 de `test_mcp_vivo.py` (opt-in, sem `MCP_CLIENT_SECRET` no
ambiente — comportamento correto e verificado) + 1 pré-existente.

### Web

```
web/tests: 124/124 arquivos OK (rc=0)
```

`web/node_modules` nasce ausente no worktree; instalado com `npm ci` (439
pacotes), que é exatamente o que `scripts/executar.sh --testes` faz sozinho.
Antes da instalação, 8 arquivos falhavam com `ERR_MODULE_NOT_FOUND` — nenhum
deles por causa desta fase (nada de `web/` foi tocado).

### Higiene do diff

- `git diff --stat` contra a base: **14 arquivos**, todos em `files_modified`.
- Zero arquivos de `web/`, `web-admin/`, `server/web_dist`, `SERVER_BUILD_ID`
  ou Railway.
- `docs/PLANO-aba-opcoes.md` **não** aparece no diff.
- Varredura de segredo no diff (`MCP_CLIENT_SECRET *=`, `eyJ…`, `mcp_…`): sem
  ocorrência real — os únicos casamentos são nomes longos de função de teste
  (`test_mcp_url_com_esquema_invalido_…`) em arquivos de `tests/`, que o
  guardião (iii) nem varre (ele só olha `server/app/`).
- Único não-rastreado: `deferred-items.md` desta pasta (artefato de
  planejamento, não commitado por instrução do orquestrador).

---

## 5. Achado FORA DE ESCOPO — decisão do Alex (alta severidade)

**`test_adr013_cobertura_rotas` está cego para rotas registradas por
`include_router`.** Com fastapi 0.141.1 / starlette 1.6.0, `include_router()`
não achata as rotas em `app.routes` — insere um `_IncludedRouter` com `.path
is None` e o `APIRouter` pendurado em `.original_router`. O guardião varre
`app.routes` procurando `.path` e pula o que não tem.

Verificado no worktree:
```python
from app.main import app
[p for p in (str(getattr(r, "path", "") or "") for r in app.routes) if "expirations" in p]
# => []
```

Ou seja: `/api/options/expirations`, `/chain`, `/gate` e `/analyze` **não são
verificados hoje** — o guardião de cobertura de rotas do ADR-013 passa por
vacuidade para tudo que entra por router.

**Não foi corrigido aqui** porque (a) o arquivo não está em `files_modified`
desta quick e (b) fazer o guardião enxergar essas rotas pode revelar rotas sem
gate reconhecido, mexendo na allowlist que o plano manda deixar em 19 — é
mudança de guardião de segurança, decisão do Alex (Rule 4).

**Mitigação já no repo:** o guardião (iv) desta fase tem o helper
`_todas_as_rotas` (descida recursiva por `original_router.routes`), pronto para
ser reusado. A rota nova `/api/options/mcp/status` **está** verificada por ele,
então não depende dessa correção. Registrado em `deferred-items.md`.

---

## 6. Riscos declarados

**Pins medidos numa venv 3.14; produção roda 3.12.** `fastapi==0.141.1`,
`starlette==1.6.0`, `pydantic==2.13.5`, `uvicorn[standard]==0.52.4` foram
medidos em Python 3.14.6 e **não foram exercitados em 3.12**
(`server/.python-version` fixa `3.12`, que é o que o Nixpacks usa). O
`requirements-prod.txt` traz o aviso escrito no topo: **se a resolução falhar
em 3.12, não relaxe o pin — é decisão do Alex** (§3.7 do plano). Duas coisas
reduzem o risco: as quatro versões já são o que a resolução livre entrega hoje,
e a faixa `mcp>=2.1,<3` é a do próprio contrato do serviço. Ainda assim, **o
primeiro deploy em staging é o teste real deste item.**

**Dois stacks HTTP no processo** (`httpx` do resto do app + `httpx2` que o SDK
traz), registrado como consequência aceita no ADR-027.

**Teto de 2.000 chamadas/dia é compartilhado por toda a base.** Cap (60/usuário,
20/min, 1.800 global) + cache são o freio. Se a base crescer, o freio certo é
subir o TTL do cache (o dado é EOD), não pedir teto maior.

**Licença de uso pessoal** — risco aceito pelo Alex em D-0.2, registrado no
ADR-027 §Decisão 6, com a mitigação nomeada (um `require_permission` por rota)
caso aperte.

---

## 7. Pendências do lado do Alex (§7 do plano, antes de rodar ao vivo)

1. Confirmar `boris` (`Bn-7QVs7cOl7qchEcf1UKQ`) em `MCP_CLIENTES` no serviço e
   o par cliente/segredo.
2. `MCP_CLIENT_ID` / `MCP_CLIENT_SECRET` no Railway (**staging primeiro**) e no
   `.env` local. Nunca no repo — o guardião (iii) reprova literal com formato
   de segredo em `server/app/`.
3. Depois da primeira chamada real, conferir `credencial: "jwt"` em
   `GET https://mcp.semente.dev/observabilidade`. Enquanto disser `"chave"`, o
   corte de chaves legadas derruba o Boris.
4. **Confirmar a premissa D-0.1:** Operador IA vira sub-tela do **Portfólio**
   (padrão do "Histórico", com `carteiraView`) ou do **Perfil**? A Fase 2
   depende dessa resposta para redirecionar todos os `go("agente")`.
5. Refrescar o venv do clone principal (§4) para o comando canônico voltar a
   ficar verde.
6. Dar o aval (ou o veto) da decisão do §1.

---

## 8. O que fica para as Fases 2+

- **Fase 2:** rotas `/leitura/{t}` e `/setups/{name}/grafico`; `OpcoesScreen.jsx`;
  troca de aba (Opções no lugar de Operador IA); `goAgente`; `chartutil.js`.
  A forma real do `check_data_freshness` sai do `frescor.bruto` ou do
  `test_mcp_vivo.py` — **não invente campo**.
- **Fase 3:** `/cadeia`, `/operaveis`, `/proposta`, `/possibilidades`;
  `PayoffChart`; paridade `opcoes_payoff` × MCP (fixture + viva em staging).
- **Fase 4:** `/veredito`; `opcoes_veredito.py`; `FONTES` do
  `test_guardrail_imperativo`.
- **Fase 5:** NL→DSL; `ENTIDADES_POR_PERMISSAO` para `opcoes.criar_setup`.
- **Fase 6:** fluxo do iniciante, mobile, checkpoint humano no iPhone,
  publicação (`bump.sh` → `publicar-web.sh` → TestFlight).
- Consolidação dos módulos puros de payoff: ADR futuro, com o gatilho já
  definido no ADR-027 Decisão 3 (10 pregões de paridade viva verde em staging,
  ou a primeira divergência).

## Self-Check: PASSED

Arquivos criados conferidos no disco (`docs/adr/027-*.md`,
`server/app/mcp_client.py`, `server/app/options_mcp_api.py`,
`server/tests/test_mcp_{client,guardioes,cap,vivo}.py`) e os 3 commits
conferidos em `git log` (`0568271`, `0a38cda`, `63d038b`).
