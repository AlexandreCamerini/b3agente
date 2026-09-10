# PLANO — Aba "Opções" sobre o serviço MCP (mcp.semente.dev)

**Status:** rascunho v2 para aprovação do Alex. Nada implementado.
**Data:** 2026-09-09. **Autor:** Fable 5.1, a partir de
`~/dev/MCP/docs/prompt-boris-aba-opcoes-otimizado.md`. v2 incorpora a
revisão adversarial independente (24 achados; os aceitos estão marcados
`[R-n]`) e a mudança de navegação pedida pelo Alex.
**Base:** `main` = `2d5448c` (F10-20260909-01). Branch de trabalho:
`v2/interacao-estrutural`.

---

## 0. Decisões já tomadas nesta sessão (fecham ambiguidade do prompt)

| # | Pergunta | Decisão do Alex (2026-09-09) | Consequência |
|---|---|---|---|
| D-0.1 | "Candidato A — aba própria" foi REVERTIDO em 03/09 (`STATE.md:132-138`, ROADMAP Fase 18, `PROJECT.md:33-37`). Aba ou seção? | **Opções ocupa o lugar de "Operador IA" na barra (continua com 5 abas). "Operador IA" vira subitem.** (Revisto pelo Alex: "não vai ficar bom a sexta aba"). | `BottomNav.defs`: `["agente","Operador IA"]` → `["opcoes", (cp && cp.tabOpcoes) \|\| "Opções"]`. **Premissa (a confirmar):** Operador IA vira sub-tela do **Portfólio**, no mecanismo que "Histórico" já usa (`carteiraView`), com linha de acesso no topo do Portfólio e o mesmo `AgenteScreen` intacto. Todo `go("agente")`/`navigate("agente")` passa a abrir Portfólio → Operador IA. Alternativa, se o Alex preferir: hub do Perfil, ao lado de "Modo Operador". |
| D-0.2 | Contrato do MCP: "licença: uso pessoal, sem redistribuição — não pode reexpô-lo a terceiros". Boris é multiusuário e vai ser comercializado. Quem vê a aba? | **Todos os usuários logados.** | Premissa registrada no ADR-027 §6 como **risco aceito pelo Alex**. Anônimo é recusado (401) porque login é obrigatório no produto, não por licença. |

Condições de parada do prompt (contrato do MCP, semente.id, licença): a
licença foi levada (D-0.2). Contrato e semente.id **não mudam**; o que
falta do lado de lá está em §7 (só ações do Alex).

---

## 1. Contexto e o que muda

O Boris tem cópias da matemática de opções (`opcoes_payoff.py`,
`opcoes_motor.py`, `opcoes_lastreadas.py`, `opcoes_gatilho.py`) e dois
guardiões (`test_opcoes_fronteira.py` ENG-03, `test_opcoes_gatilho.py`
ENG-06) que proíbem **qualquer** módulo de `server/app/` de importar `mcp`
e proíbem a dependência nos requirements. O motivo no ADR-024 era duplo:
(a) o portal `b-mcp.semente.dev` servia **fixture** em produção; (b) subir
um client MCP **stdio** dentro do uvicorn. A Estratégia C ("MCP
autenticado, `mcp.semente.dev`") ficou "descartada por ora — depende de
`plano-mcp-servico.md`, ainda não aprovado".

Os dois motivos caíram: `mcp.semente.dev` responde hoje `fonte: "http"`
(dado real do MyData), transporte **streamable-http** (um POST, uma
resposta), autenticação `client_credentials` no `id.semente.dev` com
`resource` RFC 8707. O plano do serviço existe e este prompt é a
aprovação que o ADR-024 aguardava.

**Entra:** cliente único (`server/app/mcp_client.py`), router novo
(`/api/options/mcp/*`), cap por usuário/dia, ADR-027, guardiões
reescritos, aba React em arquivo próprio, veredito por prompt do MCP + LLM
do usuário em turno único, Operador IA como sub-tela.

**Não entra:** reimplementar tool; remover os módulos puros (consolidação
= ADR futuro, com gatilho definido); mudar o serviço MCP, o semente.id ou
a licença; fill parcial; "probabilidade de sucesso".

---

## 2. ADR-027 (rascunho) — Consumo do serviço MCP autenticado substitui a fronteira do ADR-024

**Arquivo:** `docs/adr/027-consumo-do-servico-mcp-autenticado.md` (Fase 1).
**Status:** Proposto. **Substitui:** ADR-024 Decisões 1 e 2; a Decisão 3
(canal único do MyData, Guardião C) **permanece e se estende** ao canal
MCP `[R-22]`. As assinaturas `rastrear(cadeia, filtros)` / `avaliar(pernas)`
continuam congeladas. **Relaciona:** ADR-004, 010, 013, 018, 020, 021–026.

### Contexto
(§1.) O `b-mcp` continua fixture pública; `mcp.semente.dev` é outro
processo, com dado real e porteiro. A proibição antiga era contra o portal
e contra stdio, não contra o serviço.

### Decisões

1. **Fronteira nova: "só o serviço autenticado, só dado real, nunca
   fixture".** Um único módulo, `server/app/mcp_client.py`, importa `mcp` e
   `httpx2`. Nenhum outro módulo de `server/app/` importa qualquer dos
   dois. Nenhum módulo do app contém literal `"fixture"` como modo de dado,
   `MYDATA_MODO` ou `b-mcp`. A URL do serviço é a do contrato
   (`https://mcp.semente.dev/mcp`, default de `MCP_URL`); outra URL só por
   env. Segredo (`MCP_CLIENT_SECRET`) só por env; guardião reprova literal
   com formato de segredo.
2. **Fato × juízo continua a lei.** Todo número na aba vem de tool do MCP ou
   de regra determinística do Boris. A LLM só (a) compila NL→DSL e (b) fecha
   o veredito; ambos em turno único (`llm._call_llm`), validados por código.
3. **Módulos puros ficam nesta entrega; consolidação tem gatilho** `[R-16]`:
   teste de paridade (`opcoes_payoff.perfil_da_estrutura` ×
   `evaluate_option_structure`) sobre fixture gravada **e** ao vivo no
   smoke de staging. Gatilho do ADR de consolidação: 10 pregões seguidos
   de paridade viva verde em staging, ou a primeira divergência — o que
   vier antes.
4. **Cap por usuário por dia** com `metering.check/consume` em seções
   próprias (`mcpUsage`, `mcpUsageGlobal`, **`mcpUsageMonth`** `[R-1]` —
   sem isso o balde mensal do plano, `aiUsageMonth`, seria queimado por
   chamada de tool). Dia do cap ancorado em **America/Sao_Paulo**, o
   mesmo reset do serviço `[R-3]`. Recusa **antes** de chamar. Cache não
   gasta cap.
5. **Navegação:** Opções entra na barra no lugar de "Operador IA", que
   vira sub-tela (D-0.1). A barra segue com 5 itens — a decisão de 03/09
   ("sem 6ª aba") é respeitada; o que muda é qual das cinco.
6. **Licença (risco aceito pelo Alex, D-0.2):** aba visível a todo usuário
   logado, sob a mesma cláusula que `options_provider_mydata` já opera.
   Permissão `opcoes.mcp.ver` **não** é criada agora; se a licença apertar,
   é um `require_permission` por rota.
7. **Setups sem dono:** armazém único no MCP, sem `owner`. Criar, confirmar
   e desativar exigem a permissão nova `opcoes.criar_setup` (grupo
   `opcoes`, ADR-013), que só `role_admin` recebe no bootstrap. Ler,
   avaliar e ver gráfico valem para todos. Lacuna: campo `owner` no MCP.
8. **Dado é fim de pregão.** Toda tela mostra `trading_date`. Bloqueiam
   veredito e criação de setup `[R-6]`: `negociacao_b3` fora de `em_dia`,
   **`warning` presente** (frescor não medido) e **erro** da tool — a UI
   distingue "atrasado (idade real)" de "idade desconhecida"; nunca "em
   dia" por default.
9. **Veredito:** o backend obtém `prompts/get veredito` e
   `resources/read mydata://criterio/operacional` (não contam no teto),
   reúne os fatos, chama a LLM do usuário uma vez, e valida: termina com
   uma das quatro frases literais **e** contém o aviso. Senão
   `veredito: null` + texto cru rotulado "sem veredito". Nunca fabricado.
10. **Sem promessa.** Rótulos permitidos: "cenários ±1σ" e "delta ≈ chance
    de terminar dentro do dinheiro (aproximação)". Aviso do critério sempre
    visível.

### Consequências
+ Uma fonte para leitura, catálogo, montagem e setups (regra do contrato:
  "fato bruto pelo MyData, derivação pelo MCP").
+ Setups NL→DSL, que o Boris não tinha.
− Dependência de rede em runtime para a aba.
− Dois stacks HTTP (`httpx` + `httpx2`) até migrar.
− 2.000/dia para TODOS os usuários do Boris: cache e cap são o freio.
− Segredo novo no Railway; rotação é do Alex.
− Até a consolidação, dois caminhos calculam payoff (Radar/lastreadas por
  `opcoes_payoff`; aba pelo MCP) — a paridade viva é o alarme.

### Guardiões
- Guardião A (módulos puros): mantém; **acrescenta `httpx2`** (hoje
  `"httpx2" != "httpx"` passa).
- Guardião B → **"exatamente um módulo importa `mcp`/`httpx2`:
  `mcp_client`"** (igualdade de conjunto).
- Guardião B-requirements → **inverte**: `mcp>=2.1,<3` presente e igual
  nos dois requirements.
- Guardião C: mantém; `mcp_client` não importa `mydata_client`.
- Novos: (i) sem literal `"fixture"`/`MYDATA_MODO`/`b-mcp` em
  `mcp_client.py` e `options_mcp_api.py`; (ii) única URL literal em
  `mcp_client.py` é a do contrato; (iii) sem literal com formato de segredo
  em `server/app/`; (iv) toda rota `/api/options/mcp/*` passa por
  `require_user` e pelo cap; (v) `consume` do cap sempre com
  `month_section="mcpUsageMonth"` `[R-1]`.
- `test_guardrail_imperativo.py` `[R-12]`: os textos fixos novos
  (`opcoes_veredito.py`, compilador NL→DSL, `copy.js` novo) entram em
  `FONTES` na fase que os cria.
- ENG-06: mantém — a DSL do MCP **não** é portada `[R-5]`.

---

## 3. Arquitetura

```
OpcoesScreen.jsx ──► api.js (/api/options/mcp/*) ──► options_mcp_api.py
                                                        │ require_user + cap (metering, seções mcp*, dia em SP)
                                                        ▼
                                              mcp_client.py ──► https://mcp.semente.dev/mcp
                                                        │      token client_credentials (POST /token à mão, cache, renova 5 min antes do exp)
                                                        ▼
                                        llm._call_llm (1 turno)  ← prompts/get veredito · resources/read criterio
```

### 3.1 `server/app/mcp_client.py` (único importador de `mcp`/`httpx2`)
- `configurado()`; `url()` lê `MCP_URL` (default do contrato; só `https://`).
- **Token à mão** `[R-4]`: `POST https://id.semente.dev/token` com
  `client_secret_basic` e `resource=<url>` (caminho que o contrato oferece);
  cache em memória `{access_token, exp}`, renovação quando faltarem 5 min,
  sob `asyncio.Lock` só na renovação. Motivo: o `ClientCredentialsOAuthProvider`
  segura um lock **durante o round-trip inteiro** (`oauth2.py:560-582`),
  o que serializaria todas as chamadas MCP do servidor. Um único
  `httpx2.AsyncClient(timeout=30)` por processo, header `Authorization`
  por requisição; chamadas concorrentes limitadas por `asyncio.Semaphore(4)`.
- Cada chamada: `streamable_http_client(url, http_client=http)` +
  `ClientSession` (stateless). `call_tool(nome, args, *,
  read_timeout_seconds=30)` `[R-20]` → `structured_content`; `is_error or
  "error" in sc` → `McpErroDeTool(msg, available, hint)`;
  `mcp.shared.exceptions.MCPError` com `code == -32000` → `McpTetoAtingido(
  data)` `[R-7]`; 401 → `McpNaoAutorizado`; timeout/5xx → `McpIndisponivel`;
  sem segredo → `McpNaoConfigurado`. Nunca eco de segredo.
- `get_prompt(nome, args: dict[str, str])` `[R-8]` e `read_resource(uri)`.
- Cache L1 `{(tool, args_json): (at, result)}`, TTL `B3_MCP_CACHE_S` (900 s);
  só sucesso (decisão A-07 do **ADR-020** `[R-19]`); `check_data_freshness`
  600 s; resources/prompts 3.600 s.
- `obslog.log("mcp", ...)`: tool, ms, hit/miss, `chamadas_hoje` do `-32000`.
- Carimbos em `BRT` desde o início.

### 3.2 Cap por usuário (`options_mcp_api.py`, reuso de `metering`)
- `metering.check(conn, uid, quota=B3_MCP_COTA_USUARIO_DIA (60),
  rate_per_min=B3_MCP_RATE_MIN (20), custo=n_tools,
  cap_global=B3_MCP_COTA_GLOBAL_DIA (1800), _now=datetime.now(SP),
  section="mcpUsage", global_section="mcpUsageGlobal")` antes de chamar;
  `metering.consume(..., section="mcpUsage", global_section="mcpUsageGlobal",
  month_section="mcpUsageMonth")` só no sucesso, por tool efetivamente
  chamada (cache hit não consome). Fase 1 confirma que `_now` decide o dia;
  se não, a seção mcp ganha `_today` próprio em SP.
- Estouro → **402** `{"detail": {"message": "Cota do dia da aba Opções
  esgotada.", "code": "mcp_cota", "usado", "limite", "reinicia": "00:00
  America/Sao_Paulo"}}`. `-32000` do serviço → 402 com `data.reinicia` e
  `escopo`.
- **Dois tetos no `/veredito`** `[R-14]`: o gate de análise do plano
  (`_gate_analise`: mensal + gerenciada) manda sobre a chamada de LLM; o
  cap MCP manda sobre as tools. Cada 402 traz `code` distinto
  (`plano_analises`, `ia_gerenciada`, `mcp_cota`) e texto próprio da aba
  (sem o copy de BYOK do metering).
- Anônimo: `require_user` → 401 antes do cap.

### 3.3 Router `server/app/options_mcp_api.py` — `APIRouter(prefix="/api/options/mcp")`
Todas com `Depends(require_user)`; escrita de setup com
`Depends(require_permission("opcoes.criar_setup"))`. Toda resposta traz
`pregao`, `fonte: "mcp.semente.dev"`, `at` (BRT), `frescor`.

| Rota | Tools | Custo cap |
|---|---|---|
| `GET /status` | `check_data_freshness` (cache 600 s) | 1 / 0 |
| `GET /leitura/{t}` | `propose_option_setups(t)` (behavior + catalog + expirations), `list_setups`, `evaluate_setups` filtrado por ticker | 3 |
| `GET /setups/{name}/grafico` | `get_setup_chart` | 1 |
| `GET /cadeia/{t}?expiration&kind` | `get_option_chain` | 1 |
| `GET /operaveis/{t}?expiration&kind` | `find_tradable_options(min_trades=100, delta 0,25–0,55)` — números do critério, declarados na resposta | 1 |
| `POST /proposta` `{t, direction\|kind, expiration?}` | `propose_option_setups` | 1 |
| `POST /possibilidades` `{t, direction, kind?, lote, alvo?, stop?}` | `propose_option_setups(t)` p/ vencimentos (cache do `/leitura`) + por vencimento: `propose(kind, expiration)` + `evaluate_option_structure(t, legs, scenarios=[alvo, stop])` `[R-17]` | **2×N + 1** (N ≤ 6) `[R-13]`; UI mostra o custo antes |
| `POST /veredito` `{t, direcao, pernas, horizonte?, lote}` | `evaluate_option_structure`, `check_data_freshness`, `find_tradable_options` (liquidez das pernas), `prompts/get`, `resources/read` + 1 turno LLM (`_gate_analise` + `ai_activity`) | 3 + LLM |
| `POST /setups/compilar` `{descricao}` [perm] | `tools/list` + `resources/read mydata://tools/create_setup` (cache 1 h) → LLM NL→DSL → `create_setup(confirm=false)` | 1 + LLM |
| `POST /setups/confirmar` `{setup}` [perm] | `create_setup(confirm=true)` | 1 |
| `POST /setups/{name}/desativar` [perm] | `deactivate_setup` | 1 |
| `GET /glossario` | `resources/read mydata://glossario` (cache 1 h) | 0 |

Degradação (princípios 4 e 9): `McpNaoConfigurado` → 503
`mcp_nao_configurado`; `McpIndisponivel` → 503 sem número; `McpErroDeTool`
→ 422 com `error/available/hint`; frescor bloqueante (§2.8) → 409
`dado_atrasado` com `idadeHoras/slaHoras` ou `motivo: "nao_medido"`;
`evaluate_setups` com `status: "nao_avaliado"` → resposta 200 com esse
estado e o `reason` verbatim `[R-15]`. Nada cai no handler 500.

`lote` = **número de ações** (contrato B3 = 100 ações; a UI oferece
múltiplos de 100 e diz "1 contrato = 100 ações") `[R-18]`; R$ =
`resultado × lote` só quando `resultado` é número (`null` nunca vira 0).
`alvo/stop`: opcionais; a UI pré-preenche com `setups.plano_operacional`
do Boris quando existir; senão ±1σ apenas.

### 3.4 Veredito (Fase 4)
- `prompts/get veredito` com `{ticker, direcao, pernas: "<PETRJ38 compra,
  PETRJ40 venda>", horizonte}` (`pernas` é texto livre `[R-8]`); a
  **primeira mensagem** (operador-b3) vira o `system` por convenção do
  Boris — o MCP não tem papel `system` `[R-9]`; a segunda vira o `user`.
- `[R-2]` O roteiro do MCP manda o agente **chamar** as tools ("sem essa
  chamada não há veredito"). A LLM do Boris é turno único. O `user` recebe
  um bloco **antes** do roteiro: "As tools abaixo JÁ FORAM chamadas por
  este sistema nesta sessão; os resultados seguem; não peça nem simule
  chamadas; responda com base neles." + `## Fatos` (JSON de
  `evaluate_option_structure`, liquidez das pernas com `total_negocios` e
  spread, frescor, razão ganho/perda calculada pelo Boris) + resource do
  critério. **Aceite da Fase 4 exige teste com LLM real** (opt-in por env)
  em 3 casos: estrutura boa, liquidez ruim, dado atrasado — a resposta
  fecha com a frase literal nos dois primeiros.
- Validação determinística: `texto.rstrip()` termina com uma das 4 frases
  (byte a byte) **e** contém o aviso → `veredito = frase`; senão
  `veredito = null, motivo`. Razão G/P vs 1,5:1 é fato do Boris.

### 3.5 NL→DSL (Fase 5) `[R-5]`
Sem `opcoes_dsl.py` com vocabulário copiado. O `system` do compilador é
montado **em runtime** a partir do `inputSchema` de `create_setup`
(`tools/list`, de graça) e do resource `mydata://tools/create_setup`
(cache 1 h); `user` = descrição. Saída por `llm._parse_json_loose`;
validação local só de **forma** (é objeto, tem `name/ticker/description/
conditions`); semântica quem valida é `create_setup(confirm=false)`, cujos
`problems` voltam item a item. `description` = palavras originais.
Confirmação é outra rota com o `setup` que o usuário viu.

### 3.6 Front (`web/src/opcoes/` + navegação)
- `OpcoesScreen.jsx` (`{ ctx }`), `useOpcoesMcp.js`, `PayoffChart.jsx`
  (SVG, eixo X = preço), `SetupChart.jsx` (wrapper de `PriceChart` via
  `ctx.PriceChart` + `ctx.palette`). Helpers `linePath/extentOf` saem de
  App.jsx para `web/src/chartutil.js` e são importados dos dois lados
  `[R-23]` (precedente `markdown.jsx`).
- Tokens: bloco `VARKEY/TOKENS/T` idêntico a `BorisChat.jsx:26-33`.
- **Navegação (D-0.1):** `defs` troca `["agente","Operador IA"]` por
  `["opcoes", (cp && cp.tabOpcoes) || "Opções"]` `[R-21]`; render
  `{tab === "opcoes" && <OpcoesScreen ctx={ctx} />}`; `AgenteScreen` passa
  a renderizar em `tab === "carteira" && carteiraView === "agente"`, com
  linha "Operador IA" no topo do Portfólio (mesmo padrão de "Histórico") e
  `BackHeader`. `navigate("agente")` vira `goAgente()` (tab carteira +
  view agente) e todos os call sites de `go("agente")` são redirecionados
  (grep na Fase 2; guardião `test_wiring_deps.mjs` se `A` mudar). Push do
  gatilho e deep links que abrem "agente" continuam funcionando pelo
  mesmo `goAgente`.
- Fluxo do iniciante (Fase 6): pergunta em PT → tese (sempre escolha do
  usuário) → lote em ações → UMA estrutura com custo/ganho/perda em R$,
  "por que esta" (thesis/summary do catálogo), "o que pode dar errado"
  (perda máx., `unlimited_loss`, liquidez, frescor) → Veredito. "Ver os
  detalhes": catálogo (13), deltas, cadeia, payoff por vencimento.
- Estados: carregando (antes de vazio), vazio com motivo, erro
  (`pre-wrap`), `mcp_nao_configurado`, `mcp_cota` (hora do reset),
  `plano_analises`/`ia_gerenciada`, `dado_atrasado` (idade real ou "não
  medido"), setups `nao_avaliado` (motivo verbatim), mercado fechado,
  pregão sempre visível. Aviso do critério: `InfoDot`+`AboutModal` **e**
  linha fixa no rodapé da seção de veredito.
- Glossário: termo com `SUBLINHADO` abre `BottomSheet` com verbete do
  `/glossario`; conceitos do Boris seguem via `A.abrirVerbete`.
- `api.js`: 1 linha por rota (30 s; `/veredito` e `/setups/compilar` com
  `TIMEOUT_LLM`; `/possibilidades` 60 s). `persistence.js`: delegação nos
  DOIS stores. `copy.js`: `tabOpcoes`, `tituloOperadorIA` e textos novos
  nos dois modos (chaves idênticas; sem vocabulário de ordem no estudo).

### 3.7 Dependências e ambiente
- `server/requirements*.txt`: `mcp>=2.1,<3`; **pins exatos testados**
  `[R-10]` para `fastapi`, `starlette`, `pydantic`, `uvicorn` (as versões
  que a suíte passar na Fase 1), nos dois arquivos. Verificado: `mcp` 2.1.0
  pede `pydantic>=2.12`, `starlette>=0.27`, `uvicorn>=0.31.1`,
  `python-multipart`; Python ≥3.10; produção 3.12.
- Env (Railway, só o Alex): `MCP_CLIENT_ID`, `MCP_CLIENT_SECRET`, `MCP_URL`
  (opcional), `B3_MCP_COTA_USUARIO_DIA`, `B3_MCP_RATE_MIN`,
  `B3_MCP_COTA_GLOBAL_DIA`, `B3_MCP_CACHE_S`. Aviso de boot vigia `MCP_`.

---

## 4. Fases (um commit por fase, suíte inteira verde, parada para revisão)

Cada fase roda como `/gsd-quick` (ou fase de ROADMAP se o Alex preferir).
Executor: `opus` nas fases 1–6; `sonnet` nos testes de paridade e no fluxo.

### Fase 1 — ADR-027 + cliente MCP + cap + guardiões
**Arquivos:** `docs/adr/027-...md`; `server/app/mcp_client.py`;
`server/app/options_mcp_api.py` (só `/status`); `server/app/main.py`
(include_router; `MCP_` no aviso de env); `server/app/rbac.py` (grupo
`opcoes`, `ENTIDADES_POR_PERMISSAO`); `server/requirements*.txt` (pins);
`test_opcoes_fronteira.py`, `test_opcoes_gatilho.py` (reescritos com
nota), `test_adr013_rbac.py` (8→9), `test_adr013_cobertura_rotas.py`
(rota gateada, allowlist fica em 19); novos `test_mcp_client.py`,
`test_mcp_cap.py`, `test_mcp_guardioes.py`, `test_mcp_vivo.py` (opt-in).
Sem tocar `web-admin` nem `test_fase5_auditoria_perm.mjs` `[R-11]`.
**Aceite:**
- Guardiões novos falham num módulo que aponte para fixture, embuta
  segredo, importe `mcp`/`httpx2` fora de `mcp_client`, ou use URL literal
  fora do contrato; passam com o cliente.
- `test_mcp_client.py` (sessão falsa): `error` no resultado →
  `McpErroDeTool`; `MCPError(code=-32000)` → `McpTetoAtingido` com
  `reinicia`; sem segredo → `McpNaoConfigurado`; token renovado 5 min
  antes do `exp` (relógio fixo); cache: 2ª chamada igual não toca a sessão.
- `test_mcp_cap.py`: 61ª chamada com cota 60 → 402 e zero chamadas ao
  serviço (espião); `consume` grava em `mcpUsage*` e **não** em
  `aiUsageMonth`; dia vira às 00:00 de São Paulo (relógio fixo em 02:30 UTC).
- `test_mcp_vivo.py` (com `MCP_CLIENT_SECRET`): token no semente.id,
  `get_option_chain("PETR4")` imprime `trading_date`; `skip` sem segredo.
- Sem segredo: `GET /api/options/mcp/status` → 503 `mcp_nao_configurado`.
- Suíte inteira verde `[R-24]`; saída colada no SUMMARY.

### Fase 2 — leitura, setups e a troca de aba
**Arquivos:** rotas `/leitura/{t}`, `/setups/{name}/grafico`;
`OpcoesScreen.jsx` (cabeçalho: ticker, pregão, frescor; "Leitura";
"Setups"), `SetupChart.jsx`, `chartutil.js`; `api.js`, `persistence.js`,
`copy.js`, `App.jsx` (troca de aba, Operador IA como sub-tela do
Portfólio, `goAgente`, `ctx.PriceChart/palette`);
`web/tests/test_opcoes_mcp_aba_ui.mjs`, `test_operador_ia_subtela.mjs`.
**Aceite:** leitura com tendência, RSI, hv21/hv63, range 63, `trading_date`;
setups com `armed/streak`, estado `nao_avaliado` com motivo, gráfico com
disparos em `priceLines`; carregando → vazio com motivo → erro; barra com
5 itens (`Opções` no lugar de `Operador IA`); Operador IA acessível do
Portfólio e por `goAgente` em todos os antigos call sites (teste conta
zero `go("agente")` restantes); paridade de stores verde; `vite build` ok.

### Fase 3 — cadeia, catálogo, proposta e possibilidades por vencimento
**Arquivos:** rotas `/cadeia`, `/operaveis`, `/proposta`, `/possibilidades`;
`PayoffChart.jsx`; seções "Analisar" e "Possibilidades";
`test_opcoes_paridade_mcp.py` (fixture gravada com `trading_date` +
variante viva opt-in), `test_options_mcp_api.py`; smoke de staging ganha
a paridade viva (`publicar-staging.sh`).
**Aceite:** PETR4 tese alta → por vencimento aberto: estrutura, custo em R$
para o lote (ações), ±1σ, alvo/stop quando há, breakeven, razão G/P;
números conferem campo a campo com `evaluate_option_structure` (fixture);
paridade `opcoes_payoff` × MCP verde (`custo_liquido=net_cost`,
`ganho_maximo=max_gain`, `perda_maxima=max_loss`, `breakevens`,
`delta_total.valor=net_delta`, `curva=payoff`); `null` nunca vira 0;
breakeven nunca × lote; lote 100 ações num caso de número conhecido; UI
mostra "2×N+1 chamadas" antes de disparar; `/possibilidades` com N=6 abaixo
de 20 s ao vivo (medido, com o semáforo de 4).

### Fase 4 — veredito por prompt + critério
**Arquivos:** rota `/veredito`; `server/app/opcoes_veredito.py` (puro:
monta system/user com o bloco "tools já chamadas", valida frases/aviso,
razão G/P); seção "Veredito"; `test_opcoes_veredito.py`; `FONTES` do
`test_guardrail_imperativo.py`; `test_opcoes_veredito_vivo.py` (opt-in).
**Aceite:** LLM falsa: frase literal + aviso → `veredito`; sem frase →
`null` + "sem veredito"; frescor atrasado/não medido → 409 e botão
desabilitado com a idade; sem chave → `missing_key` com `Como corrigir:`;
`pernas` chega ao `prompts/get` como string; os dois 402 (`plano_analises`,
`mcp_cota`) com textos próprios; **LLM real (opt-in)**: 3 casos, frase
literal nos dois esperados; `ai_activity` registra `tipo="Opções · veredito"`.

### Fase 5 — criação de setups NL→DSL com dry-run e entitlement
**Arquivos:** rotas `/setups/compilar|confirmar|desativar`; compilador em
`options_mcp_api.py` (schema/resource em runtime, sem vocabulário copiado);
seção "Criar setup" (só com `permissions ∋ opcoes.criar_setup`);
`test_opcoes_dsl.py`; `FONTES`.
**Aceite:** PT → DSL (LLM falsa) → dry-run com `disparos`,
`disparos_por_100`, `retorno_apos_disparo d+5/d+10` na tela → confirmar
grava → `list_setups` mostra; `problems` voltam item a item; sem
permissão o botão não existe **e** a rota responde 403; frescor bloqueante
→ 409; guardião ENG-06 continua verde (nenhuma DSL no app).

### Fase 6 — experiência do iniciante, mobile, cobertura
**Arquivos:** `OpcoesScreen.jsx` (fluxo pergunta→tese→lote→UMA
estrutura→veredito; "ver os detalhes"; glossário; links "abrir em
Opções" nas 3 superfícies vivas de opções); `copy.js`;
`test_opcoes_mcp_fluxo.py` (TestClient, `mcp_client` monkeypatchado com
respostas gravadas: leitura → tese → possibilidades → veredito);
`test_opcoes_mcp_estados.mjs` (estados presentes, `minHeight: 44px`,
`aria-*`, `pre-wrap`, sem "probabilidade de sucesso", sem verde/vermelho
fora de P&L).
**Aceite:** fluxo no padrão real do ADR-018 (TestClient + estático +
**checkpoint humano no iPhone**); 375 px sem scroll horizontal;
reduced-motion; dois temas; publicação `bump.sh` → `publicar-web.sh` →
TestFlight só depois do checkpoint.

---

## 5. Verificação (transversal)

- `bash scripts/executar.sh --testes` a cada fase; `npx vite build` quando
  `web/src` mudar; saída no SUMMARY.
- Ao vivo (opt-in por env) nas fases 1, 3 e 4; `/observabilidade` do MCP
  com `boris` em `credencial: "jwt"` após a primeira chamada.
- Sem `MCP_CLIENT_SECRET` em staging, a aba mostra "serviço de opções não
  configurado" e o resto do app não muda.
- Deploy: staging → PR → clique no Railway; `SERVER_BUILD_ID` acompanha o
  `version.js` via `bump.sh`.

## 6. Cota — estimativa `[R-F]`

Sessão típica do iniciante: `/status` (0–1) + `/leitura` (3) +
`/possibilidades` N=4 (9) + `/veredito` (3) = **~16 chamadas**, metade
cacheável em 15 min. Cap 60/dia por usuário ≈ 3–4 sessões completas.
Global 1.800 ≈ 110 sessões/dia ou 30 usuários ativos a 3–4 sessões —
fecha com 2.000 do client com 10% de folga para Radar/lastreadas futuras.
Se a base passar disso, o freio certo é subir o TTL do cache (dado é EOD:
TTL até a próxima carga é legítimo), não o teto.

## 7. Fora do repo — ações do Alex antes da Fase 1 rodar ao vivo
1. Confirmar `boris` (`Bn-7QVs7cOl7qchEcf1UKQ`) em `MCP_CLIENTES` e o segredo.
2. `MCP_CLIENT_ID`/`MCP_CLIENT_SECRET` no Railway (staging primeiro) e no
   `.env` local; nunca no repo.
3. Após a primeira chamada, `credencial: "jwt"` em `/observabilidade`.
4. Confirmar a premissa de D-0.1 (Operador IA no Portfólio × no Perfil).

## 8. Discordâncias declaradas (uma frase cada, e sigo)
- "Sem dependência nova além de `mcp`": `mcp` traz `httpx2` e ~10 pacotes;
  é o custo do SDK, e o OAuth não deve ser reimplementado.
- "Cobertura e2e (ADR-018)": o ADR-018 decidiu **não** adotar E2E; a
  Fase 6 entrega o padrão real dele (TestClient + estático + checkpoint).
- "`ClientCredentialsOAuthProvider` faz o fluxo inteiro": faz, mas
  serializa o servidor sob um lock por round-trip; o token à mão é o
  outro caminho que o próprio contrato documenta.

## 9. Achados da revisão NÃO aceitos (e por quê)
- Nenhum. Os 24 foram incorporados; o R-16 (dois caminhos de cálculo) foi
  aceito parcialmente: os módulos puros ficam por restrição do prompt, com
  gatilho de consolidação e paridade viva em staging.
