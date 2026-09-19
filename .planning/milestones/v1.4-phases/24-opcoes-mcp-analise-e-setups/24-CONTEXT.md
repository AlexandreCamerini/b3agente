# 24-CONTEXT — Aba Opções sobre MCP: análise e criação de setups

**Fase 24 do ROADMAP = Fases 3 e 5 do `docs/PLANO-aba-opcoes.md`.** A Fase 4
(veredito) fica FORA, por decisão do Alex em 2026-09-11 ("faz a 3 primeiro e a
5 em seguida"). A ordem tem razão: montar setup sem ver cadeia e vencimentos na
tela é montar no escuro.

Este arquivo NÃO repete o PLANO nem o ADR. Ele registra só (a) o que já existe
e os planos consomem, (b) as decisões que o PLANO deixou em aberto e foram
travadas aqui, e (c) o que fica declaradamente fora.

## Leitura obrigatória (não redesenhar)

- `docs/PLANO-aba-opcoes.md` — §3.3 (tabela rota × tools × custo), §3.5
  (NL→DSL), §4 Fases 3 e 5 (aceite literal).
- `docs/adr/027-consumo-do-servico-mcp-autenticado.md` — fronteira, cap,
  guardiões, Decisão 7 (setups sem dono) e Decisão 8 (dado é fim de pregão).
- `CLAUDE.md` (raiz) — princípios 4, 5 e 9; guardrails do repositório.

## O que já está em produção (Fases 1 e 2 do PLANO)

`server/app/mcp_client.py` — único importador de `mcp`/`httpx2`.

```python
class McpErro(RuntimeError): ...
class McpNaoConfigurado(McpErro): ...      # sem MCP_CLIENT_ID/SECRET
class McpNaoAutorizado(McpErro): ...       # 401 do serviço
class McpIndisponivel(McpErro): ...        # timeout/5xx
class McpTetoAtingido(McpErro):            # JSON-RPC -32000
    data: dict                             # {cliente, escopo, chamadas_hoje, teto, reinicia}
class McpErroDeTool(McpErro):              # `error` no structured_content
    available: list | None
    hint: str | None

class ResultadoTool(NamedTuple):
    dados: Any      # structured_content (dict) em call_tool
    cache: bool     # True = NÃO tocou a rede (não consome cap)

async def call_tool(nome: str, args: dict | None = None, *,
                    read_timeout_seconds: float = 30.0) -> ResultadoTool
async def get_prompt(nome: str, args: dict | None = None) -> ResultadoTool
async def read_resource(uri: str) -> ResultadoTool
def configurado() -> bool
def url() -> str          # levanta ValueError com MCP_URL de esquema inválido
def reset_cache() -> None # usado pelos testes
```

Cache L1 por `(rotulo, args_json)`: TTL 900 s para tools (600 s para
`check_data_freshness`, 3.600 s para prompts/resources). **Não existe
`list_tools`** — quem precisar de `tools/list` (Fase 5) acrescenta a função
NESTE módulo, nunca importa `mcp` em outro lugar.

`server/app/options_mcp_api.py` — `APIRouter(prefix="/api/options/mcp")`, hoje
com `/status`, `/leitura/{ticker}` e `/setups/{name}/grafico`. Peças que os
planos reusam sem reescrever:

- `configure(conn, require_user_dep)` chamado por `main.py:181`;
  `require_user` é delegação local (o nome importa: é o que
  `test_adr013_cobertura_rotas` reconhece como gate de identidade).
- `_cap_check(uid, custo) -> _Reserva`, context manager: reserva antes da rede
  e devolve o saldo não consumido na saída, inclusive em `raise`.
  **Uso obrigatório: `with _cap_check(uid, n) as cap:`.**
- `_chamada_com_cap(cap, nome, args) -> (dados, cache)` — uma tool + consumo
  de 1 quando tocou a rede.
- `_erro_http(e)` — tradução única de exceção → HTTPException (503/402/422).
  Nada cai no handler 500.
- `_frescor(sc, erro)` / `_frescor_da_avaliacao(...)` — mesmas chaves
  (`classes/stale/warning/bloqueia/medido/bruto`), um renderizador só no front.
- `_agora_brt()`, `_cap_bloco(uid)`, constantes `FONTE`, `SECTION`,
  `GLOBAL_SECTION`, `MONTH_SECTION`, `RESET_TXT`, `BRT`.

Front: `web/src/opcoes/{OpcoesScreen.jsx,SetupChart.jsx,useOpcoesMcp.js}`,
`web/src/chartutil.js` (`extentOf`, `linePath`, `lastVal`), bloco
`VARKEY/TOKENS/T` local em cada arquivo (zero import de `App.jsx`),
`api.js` (`mcpStatus`/`mcpLeitura`/`mcpSetupGrafico`), delegação nos DOIS
stores de `persistence.js`, textos em `copy.js` nos DOIS modos.

## Guardiões que quebram se a regra for violada

| Guardião | O que exige |
|---|---|
| `test_mcp_guardioes.py::..._iv_...` | AST: TODA função decorada com `@router.*` em `options_mcp_api.py` contém o Name `_cap_check`; toda rota registrada tem `require_user` nas dependências |
| `test_mcp_guardioes.py::..._v_...` | todo `metering.consume` do módulo leva `month_section` que RESOLVE para `"mcpUsageMonth"` |
| `test_mcp_guardioes.py::..._i_/_ii_/_iii_` | sem literal `"fixture"`/`MYDATA_MODO`/`b-mcp`; únicas URLs literais do cliente são as do contrato; nenhum literal com formato de segredo em `server/app/` |
| `test_opcoes_fronteira.py` / `test_opcoes_gatilho.py` | só `mcp_client` importa `mcp`/`httpx2`; nenhuma DSL de setup portada para o app (ENG-06) |
| `test_adr013_cobertura_rotas.py` | rota nova sem gate precisa entrar na allowlist pública — o que NÃO pode acontecer aqui |
| `test_guardrail_imperativo.py` | texto fixo novo entra em `FONTES` na fase que o cria |
| `web/tests/test_opcoes_mcp_aba_ui.mjs` | ordem no fonte carregando → erro → vazio-com-motivo → dados; erro escolhido por `code`; chip de frescor nas três variantes |

## Contrato do serviço (campos que os planos consomem)

Fonte: `~/dev/MCP/docs/contrato-mcp-servico.md` e
`~/dev/MCP/servers/mydata/server.py` (lidos em 2026-09-11). Resumo do que
importa; campo ausente é `None`, nunca 0.

`get_option_chain(ticker, expiration?, kind?, limit=50)` →
`{ticker, trading_date, underlying_price, matched, returned, options[], truncated?, data_freshness{quotes, quotes_age_hours, instrument_registry, warning}}`.
Cada item de `options` traz os campos do contrato (contrato, tipo, strike,
premio, volatilidade_implicita, delta, situacao_sigma, total_negocios,
dt_vencimento, dt_pregao, preco_objeto…). `truncated` é texto explicando a
omissão — exibir, nunca engolir.

`find_tradable_options(ticker, expiration?, kind?, delta_min?, delta_max?, min_trades?)` →
`{ticker, trading_date, criteria (texto), options[], excluded, note}`.

`propose_option_setups(ticker)` (sem direction/kind) →
`{ticker, trading_date, underlying_price, behavior, catalog[], expirations[], next_step, note?}`.
Com `direction` e/ou `kind` (+ `expiration?`) →
`{..., direction, kind, setups: [{kind, name, expiration, legs[], net_cost, flow, max_gain, max_loss, unlimited_gain, unlimited_loss, breakevens}], note}`;
`setups: []` + `reason` (PT-BR, verbatim) quando a cadeia não preenche a perna.

`evaluate_option_structure(ticker, legs[{contract, side, quantity?}], scenarios[{name, underlying}]?)` →
`{ticker, trading_date, underlying_price, legs[], net_cost, flow(debit|credit|flat), max_gain, max_loss, unlimited_gain, unlimited_loss, breakevens[], net_delta, legs_without_delta, payoff[{underlying, result}], unit, sessions_to_nearest_expiry?, scenarios{sigma{hv21, sessions_to_expiry, sigma_to_expiry, formula}|null, scenarios[{name, underlying, result}]}, note?}`.
**Toda cifra é por unidade do objeto (uma ação).**

`create_setup(setup, confirm=false)` → `{status: "dry_run", setup_as_interpreted, backtest, next_step}`;
com `confirm=true` → `{status: "ativo", name, backtest, note}`; inválido →
`{error, problems[]}`. `backtest` =
`{periodo{de,ate,pregoes}, pregoes_avaliaveis, pregoes_sem_indicador, disparos, datas_de_disparo[], disparos_por_100_pregoes_avaliaveis, retorno_apos_disparo{d+5,d+10:{com_dado, retorno_medio_pct, retorno_mediano_pct}}}`.

`deactivate_setup(name)` → `{status: "inativo", name}` ou
`{error, known_setups[]}`.

Schema de `Setup` (o que `tools/list` publica como `inputSchema`):
`name, ticker, description, conditions[]` obrigatórios; `logic (AND|OR)`,
`consecutive_days`, `valid_until`, `options_intent{direction, target_delta,
target_sessions_to_expiry, note}` opcionais. Condição é comparação
(`indicator`, `window?`, `operator`, `value` ou `reference{indicator, window?}`)
ou padrão (`pattern` sozinho). Resource com o texto para humanos:
`mydata://tools/create_setup`.

## Decisões travadas nesta fase (o PLANO deixou em aberto)

**D-24.1 — Reserva de cap do `/possibilidades` em DUAS etapas.** O custo
declarado é 2×N+1, mas N só se conhece depois da primeira chamada. Reservar o
teto (13) recusaria usuário com cota de sobra; reservar 1 e consumir 13 mentiria
o cap. Então: `with _cap_check(uid, 1)` para o `propose_option_setups(ticker)`
que traz `expirations`, e, com N já conhecido, um `with _cap_check(uid, 2*N)`
aninhado para o resto. As duas reservas devolvem saldo na saída. `N ≤ 6`.

**D-24.2 — A multiplicação pelo lote é do BACKEND, e breakeven não tem bloco
de reais.** O PLANO exige "breakeven nunca × lote" e "`null` nunca vira 0". Um
teste estático no front prova ausência de um bug; o desenho o torna
impossível: a resposta traz `emReais: {custoLiquido, ganhoMaximo, perdaMaxima,
cenarios[]}` e `breakevens` fica FORA desse bloco, em preço do objeto. Campo
`null` no MCP sai `null` em `emReais` — nunca 0. Helper puro
`_em_reais(dados, lote)` em `options_mcp_api.py`, testado por import direto.

**D-24.3 — `lote` é número de AÇÕES, validado como inteiro ≥ 1.** A UI oferece
múltiplos de 100 e diz "1 contrato = 100 ações" (`[R-18]`). O backend NÃO
força múltiplo de 100 (rejeitar 150 seria inventar regra que a B3 aplica por
série), mas rejeita 0, negativo e não-inteiro com 422.

**D-24.4 — `/operaveis` declara o critério na resposta.** `min_trades=100`,
`delta_min=0.25`, `delta_max=0.55` são o critério do Boris, não do serviço:
vão como constantes nomeadas no módulo, entram na resposta em
`criterioAplicado` (junto do `criteria` verbatim do serviço) e a UI os mostra.
Números escondidos viram "a peneira sumiu com meu strike" sem explicação.

**D-24.5 — A Fase 5 traz a fiação de LLM que a Fase 4 traria.** Pular a Fase 4
significa que `/setups/compilar` é a PRIMEIRA rota de LLM desta aba. Ela
carrega, portanto: `configure()` estendido com o gate de análise e o
`require_permission` de `main.py`, os DOIS 402 distintos (`plano_analises`/
`ia_gerenciada` do gate; `mcp_cota` do cap) e o registro em `ai_activity`.
Quando a Fase 4 for feita, ela REUSA essa fiação — não a duplica.

**D-24.6 — Auditoria da escrita de setup entra agora.**
`rbac.ENTIDADES_POR_PERMISSAO` tem nota explícita dizendo que
`opcoes.criar_setup` entra "na Fase 5, junto com a rota de escrita que a
gravará". Os planos cumprem: entidade `opcoes_setup`, `audit.record` em
confirmar e desativar.

**D-24.7 — Sem chamada ao vivo nesta execução.** `MCP_CLIENT_SECRET` não está
no ambiente de desenvolvimento. Todo teste novo é OFFLINE (espião de
`mcp_client.call_tool`), no padrão de `test_options_mcp_leitura.py`. Os testes
"ao vivo" do aceite (`/possibilidades` N=6 abaixo de 20 s; paridade viva no
smoke de staging) nascem `skip` sem segredo e ficam declarados como pendência
de verificação do Alex.

## Fora de escopo (declarado)

- Fase 4 do PLANO (veredito por prompt + critério) — `/veredito`,
  `opcoes_veredito.py`, seção de veredito, os textos de veredito em `FONTES`.
- Fase 6 (fluxo do iniciante, glossário, links das 3 superfícies, cobertura
  mobile) — a seção "Analisar" desta fase é a superfície de detalhe, não o
  fluxo guiado.
- Consolidação dos módulos puros (`opcoes_payoff` × MCP) — ADR-027 Decisão 3
  fixa o gatilho; esta fase entrega só o teste de paridade que o dispara.
- Publicação em produção: o plano 24-05 existe, mas só roda com o OK explícito
  do Alex (bump + `publicar-web.sh` + checkpoint no iPhone).
