---
quick_id: 260910-biz
titulo: "Aba Opções — Fase 2: leitura, setups e a troca de aba"
phase: quick-260910-biz
plan: 01
type: execute
wave: 1
depends_on: ["260909-waw"]
autonomous: true
requirements: ["PLANO-aba-opcoes-F2"]
files_modified:
  - server/app/options_mcp_api.py
  - server/tests/test_options_mcp_leitura.py
  - server/tests/test_guardrail_imperativo.py
  - web/src/chartutil.js
  - web/src/api.js
  - web/src/persistence.js
  - web/src/copy.js
  - web/src/App.jsx
  - web/src/opcoes/OpcoesScreen.jsx
  - web/src/opcoes/useOpcoesMcp.js
  - web/src/opcoes/SetupChart.jsx
  - web/tests/test_opcoes_mcp_aba_ui.mjs
  - web/tests/test_operador_ia_subtela.mjs
  - web/tests/test_pet_ui.mjs

must_haves:
  truths:
    - "Logado, o usuário abre a aba Opções na barra inferior (5 itens; Opções no lugar de Operador IA) e vê pregão, fonte e frescor sem afirmar 'em dia' por default."
    - "Escolhendo um ticker, o usuário vê a leitura de comportamento (tendência, RSI, hv21/hv63, faixa de 63 pregões) com o pregão a que ela se refere."
    - "O usuário vê os setups daquele ticker com armado/streak e, quando o serviço recusa avaliar, o motivo verbatim em vez de silêncio."
    - "O usuário abre o gráfico de um setup e vê os disparos marcados sobre os candles."
    - "O usuário chega ao Operador IA por uma linha no topo do Portfólio, com seta de voltar, e a tela é a mesma de antes."
    - "Serviço não configurado, cota estourada, serviço fora do ar e erro de pedido têm cada um seu estado próprio na tela — nenhum vira tela em branco."
  artifacts:
    - path: "server/app/options_mcp_api.py"
      provides: "GET /leitura/{ticker} e GET /setups/{name}/grafico"
      contains: "async def leitura"
    - path: "server/tests/test_options_mcp_leitura.py"
      provides: "cap, degradação e forma das duas rotas novas"
      contains: "nao_avaliado"
    - path: "web/src/chartutil.js"
      provides: "extentOf/linePath/lastVal compartilhados"
      exports: ["extentOf", "linePath", "lastVal"]
    - path: "web/src/opcoes/OpcoesScreen.jsx"
      provides: "tela da aba Opções (cabeçalho, Leitura, Setups)"
      min_lines: 200
    - path: "web/src/opcoes/useOpcoesMcp.js"
      provides: "estado de carregamento/erro das chamadas MCP"
    - path: "web/src/opcoes/SetupChart.jsx"
      provides: "adaptador get_setup_chart para ctx.PriceChart"
    - path: "web/tests/test_operador_ia_subtela.mjs"
      provides: "guardião da troca de aba e da sub-tela"
  key_links:
    - from: "web/src/opcoes/OpcoesScreen.jsx"
      to: "web/src/persistence.js (store.mcpLeitura)"
      via: "store recebido por ctx/prop"
      pattern: "mcpLeitura"
    - from: "web/src/persistence.js"
      to: "web/src/api.js"
      via: "delegação pura nos DOIS stores"
      pattern: "api\\.mcpLeitura"
    - from: "web/src/App.jsx"
      to: "web/src/chartutil.js"
      via: "import"
      pattern: "from \"./chartutil.js\""
    - from: "web/src/opcoes/SetupChart.jsx"
      to: "ctx.PriceChart"
      via: "prop do ctx, sem import de App.jsx"
      pattern: "ctx\\.PriceChart"
---

<objective>
Fase 2 do `docs/PLANO-aba-opcoes.md`: as duas rotas de leitura do serviço MCP
(`/leitura/{ticker}`, `/setups/{name}/grafico`), a tela da aba Opções em
arquivo próprio, e a troca de navegação decidida em D-0.1 — **Opções entra na
barra no lugar de "Operador IA", que vira sub-tela do Portfólio** (mesmo
mecanismo que "Histórico" já usa).

Purpose: dar ao usuário a primeira superfície real da aba Opções — o que o
serviço já sabe (comportamento recente, catálogo, vencimentos, setups
gravados) — sem cadeia, sem payoff, sem veredito (Fases 3–4).

Output: 2 rotas, 3 arquivos novos de front (`web/src/opcoes/`), 1 módulo de
helpers extraído (`chartutil.js`), 3 métodos em `api.js` e nos DOIS stores,
chaves de copy nos dois modos, 2 guardiões novos, 1 guardião atualizado com
nota, suíte canônica verde e `vite build` ok.

**NÃO entra:** publicar front, `bump.sh`, deploy, Railway, `web-admin`,
`SERVER_BUILD_ID`, `/cadeia`, `/operaveis`, `/proposta`, `/possibilidades`,
`/veredito`, `/setups/compilar|confirmar|desativar`, `PayoffChart`.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@CLAUDE.md
@.planning/STATE.md
@docs/PLANO-aba-opcoes.md
@docs/adr/027-consumo-do-servico-mcp-autenticado.md
@.planning/quick/260909-waw-aba-opcoes-f1-adr027-cliente-mcp/260909-waw-SUMMARY.md
@server/app/options_mcp_api.py
@server/app/mcp_client.py
@server/tests/test_mcp_cap.py
@server/tests/test_mcp_guardioes.py

<inventario>
Rodado em 2026-09-10 sobre esta branch (`v2/interacao-estrutural`).
**Não repita estes greps — os resultados abaixo são o insumo do plano.**

**(a) `grep -n '"agente"' web/src/App.jsx` — 5 ocorrências, só DUAS são navegação:**

| Linha | Trecho | É navegação? | Ação na Task 3 |
|---|---|---|---|
| 971 | `["agente", "Operador IA"]];` (defs do `BottomNav`) | **SIM** | trocar por `["opcoes", (cp && cp.tabOpcoes) \|\| "Opções"]` |
| 9295 | `{tab === "agente" && <AgenteScreen ctx={ctx} />}` | **SIM** | virar ramo de `tab === "carteira" && carteiraView === "agente"` |
| 5432 | `{row("agente", "Operações do agente", …)}` | não — preferência de push | **não tocar** |
| 8761 | `notify.notifyIfEnabled(n, "agente", …)` | não — classe de notificação | **não tocar** |
| 9199 | `case "agente": {` (dentro de `petSnapshot`) | não — chave do snapshot do pet | **não tocar** (`test_pet_ui.mjs` exige que continue existindo) |

**Zero call sites de `go("agente")` / `navigate("agente")` / `setTab("agente")`.**
Confirmado por `grep -n "setTab(\|navigate(" web/src/App.jsx` (10 hits: 978,
7846, 8121, 8281, 8283, 9041, 9052, 9122, 9133, 9282 — nenhum com `"agente"`)
e por `grep -n "A\.go(" web/src/App.jsx` (7 hits: `"mercado"`×3, `"radar"`,
`"carteira"`, `"perfil"`×3). `grep -n "agente" web/src/main.jsx
web/src/notify.js web/src/sync.js web/src/api.js` → **nenhum deep link nem
push abre a aba "agente"**; as ocorrências em `notify.js` (220, 335, 339) e
`persistence.js` (408, 679, 680) são a CLASSE de notificação `notif.agente`,
não navegação. `web/src/push*.js` **não existe**.

**Consequência:** `goAgente()` NÃO tem call site antigo para redirecionar. Ele
nasce para (i) a linha nova no topo do Portfólio e (ii) ser o ponto único
caso um deep link futuro precise abrir o Operador IA. O guardião novo conta
**zero** `tab === "agente"` e **zero** `["agente", "Operador IA"]` sobrando —
é assim que "todos os call sites migraram" fica verdadeiro e não-vácuo.

**(b) `grep -rn "extentOf\|linePath\|lastVal" web/src/*.jsx web/src/*.js web/src/pet/*.jsx`**
Só `web/src/App.jsx`. Definições: `extentOf` L1443, `linePath` L1450,
`lastVal` L1459. Usos: L1071, L1087 (mini-gráfico), L1483, L1497-1498
(RSI/MACD), L1631, L1634-1636 (fallback SVG do `PriceChart`), L1770-1771
(`IndCell`). **Nenhum outro arquivo importa** — a extração é segura.

**(c) `grep -n "carteiraView" web/src/App.jsx`** — 4 hits: L7844
(`useState("main")`, comentário `// main | historico`), L7846 (`navigate`
reseta para `"main"`), L9152/9155 (`petTela`), L9296-9298 (render). É o
mecanismo exato a espelhar para `"agente"`.

**(d) Guardiões que citam a aba (`grep -rn '"agente"' web/tests/*.mjs`):**

| Arquivo | Linha | O que afirma | Dispara? |
|---|---|---|---|
| `test_pet_ui.mjs` | 161 | regex EXATA de `const petTela = tab === "carteira" ? (carteiraView === "historico" ? "historico" : "carteira") : tab;` | **SIM** — `petTela` muda. Atualizar COM NOTA. |
| `test_pet_ui.mjs` | 160 | `ABAS_PET` contém `"agente"`; exige `case "agente":` em App.jsx | não — `petSnapshot` mantém o `case` |
| `test_fase22_componentes_compartilhados.mjs` | 179 | `NavIcon.paths` tem os ids `opcoes` **e** `agente` | não — os dois ícones já existem e nenhum é removido |
| `test_didatica_parity.mjs` / `test_push_prefs_classes.mjs` | 108 / 76-78 | lista de classes de push `notif.agente` | não |
| `test_agente_hero_infodot.mjs` | 36-62 | corpo de `AgenteScreen` (herói, InfoDot, rodapé) | não — `AgenteScreen` não é editada |
| `test_agente_modo_estudo_ui.mjs`, `test_auditoria_status_strip.mjs`, `test_alvo_dinamico_ui.mjs`, `test_agent_server_toggle.mjs` | — | corpo de `AgenteScreen` | não |
| `test_copy_theme.mjs` | 51-55 | `["mercado", (cp && cp.tituloWatchlist)` e `["radar", (cp && cp.tabRadar)` em `defs` | não — as duas linhas ficam intactas |
| `test_fase20_fundacao_visual.mjs` | 79-81 | `maxWidth: CONTENT_MAX_WIDTH` aparece **exatamente 2×** em App.jsx | não — **desde que** `OpcoesScreen.jsx` não use `CONTENT_MAX_WIDTH` (o guardião só lê App.jsx, e o wrapper de conteúdo já limita a largura) |
| `test_wiring_deps.mjs` | 30-80 | estados lidos no `useMemo(A)` estão nas deps | não — `goAgente` só chama setters (estáveis) e mora no `ctx`, não no `A` |

**Conclusão: um único guardião dispara — `test_pet_ui.mjs:161`.**
</inventario>

<interfaces>
<!-- Contratos exatos, extraídos do código. O executor NÃO precisa explorar. -->

**1. `mcp_client` (F1) — o que a rota pode usar:**
```python
class ResultadoTool(NamedTuple):
    dados: Any     # structured_content da tool (dict)
    cache: bool    # True = veio do cache L1, NAO gastou chamada no servico

async def call_tool(nome: str, args: dict | None = None, *,
                    read_timeout_seconds: float = 30.0) -> ResultadoTool

# Excecoes (todas subclasse de McpErro):
McpNaoConfigurado, McpNaoAutorizado, McpIndisponivel,
McpTetoAtingido(data: dict),            # -32000 do servico
McpErroDeTool(msg, available, hint)     # `error` no structured_content
```

**2. `options_mcp_api` (F1) — helpers a reusar, sem reescrever:**
`_cap_check(uid, custo)` (levanta 402 antes da rede) · `_cap_consume(uid, custo)`
(só por chamada que NÃO veio do cache) · `_erro_http(e)` (503/402/422, nada cai
no 500) · `_frescor(sc, erro)` · `BRT`, `FONTE`, `RESET_TXT`, `CLASSE_CRITICA`,
`EM_DIA`, `SECTION`, `_dia_sp()`.

**3. `propose_option_setups(ticker)` SEM `direction`/`kind` — resposta real
(`servers/mydata/server.py:1165`):**
```json
{ "ticker": "PETR4", "trading_date": "2026-08-28", "underlying_price": 38.42,
  "behavior": { "trading_date": "2026-08-28", "close": 38.42, "sma21": 37.9,
                "sma63": 36.4, "distance_from_sma21_pct": 1.4,
                "distance_from_sma63_pct": 5.5, "trend": "alta", "rsi14": 58.2,
                "hv21": 0.31, "hv63": 0.28,
                "range_63_sessions": {"highest": 41.0, "lowest": 33.2},
                "change_21_sessions_pct": 4.1 },
  "catalog": [ {"kind": "...", "name": "...", "thesis": ["..."],
                "summary": "...", "risk": "..."} ],
  "expirations": ["2026-09-19", "2026-10-17"],
  "next_step": "...", "note": "(so quando a cadeia falha)" }
```
Sem candles, `behavior` vira `{"status": "sem_candles"}` (`setups.py:600`).
Falha de cotações vira `{"error": ...}` → `mcp_client` já converte em
`McpErroDeTool`.

**4. `list_setups()` — resposta real (`server.py:869`):**
```json
{ "setups": [ { "setup": {"name":"...","ticker":"PETR4","description":"...",
                          "conditions":[], "logic":"AND","consecutive_days":2,
                          "options_intent":"...","valid_until":null},
                "status": "ativo",
                "backtest_na_criacao": {"disparos": 7} } ],
  "count": 1 }
```
`status` do REGISTRO ∈ {`ativo`, `inativo`} — **não confundir** com o `status`
da AVALIAÇÃO.

**5. `evaluate_setups()` — resposta real (`server.py:947`):**
```json
{ "trading_date": "2026-08-28",
  "data_freshness": {"quotes": "em_dia", "quotes_age_hours": 12},
  "evaluations": [ {"name":"...","ticker":"PETR4","trading_date":"2026-08-28",
                    "status":"avaliado","conditions":[{"summary":"...","met":true}],
                    "conditions_met_today":2,"streak":3,"required_streak":2,
                    "armed":true,"triggered_today":false} ],
  "armed": ["nome"], "note": "..." }
```
Gate de frescor (antes de tudo):
`{"status": "nao_avaliado", "reason": "<texto verbatim>"}`.
Sem setups ativos: `{"status": "sem_setups", "note": "..."}`.
Por setup, `status` ∈ {`avaliado`, `nao_avaliavel`, `expirado`, `invalido`,
`erro`, `sem_candles`}.

**6. `get_setup_chart(name)` — resposta real (`server.py:897`), ARRAYS PARALELOS:**
```json
{ "name":"...", "ticker":"PETR4", "trading_date":"2026-08-28",
  "description":"...", "logic":"AND", "required_streak":2, "status":"ativo",
  "options_intent":"...",
  "conditions":[{"left":"close","op":">","right":"sma21","value":null,
                 "label":"close > sma21","met":[true,false]}],
  "dates":["2026-05-02"], "open":[], "high":[], "low":[],
  "close":[], "volume":[],
  "series": {"sma21":[], "rsi14":[]},
  "triggers":[41,77,120], "trigger_dates":["2026-05-22","2026-06-11","2026-08-19"],
  "daily":[], "streaks":[] }
```
`series` tem nomes ARBITRÁRIOS (os indicadores que as condições do setup
citam) — **nunca** `sma20`/`sma50`/`bbUpper`/`bbLower`. `triggers` são
ÍNDICES em `dates`/`close`.

**7. `PriceChart` (App.jsx:1521) — formato EXATO que ele espera:**
```jsx
<PriceChart candles={} ind={} show={} priceLines={} viewBars={} onRange={} />
```
- `candles`: `Array<{ date: "YYYY-MM-DD", open, high, low, close, volume }>`.
  `c.date` é passado **cru** como `time` da lightweight-charts (business-day
  string). Vela sem `close` numérico > 0 é **descartada**; `open/high/low`
  ausentes ou 0 caem para o `close` (doji sintético); outliers vs. mediana
  (×6) e vs. vizinho (×5) são descartados. `c.volume || 0` no histograma.
- `ind`: `{ sma20: (number|null)[], sma50: (number|null)[], bbUpper: (number|null)[],
  bbLower: (number|null)[] }` — **os quatro obrigatórios**, arrays paralelos a
  `candles`. `pair()` faz `arr[i]` sem guard: chave ausente = `TypeError`.
- `show`: `{ sma20: bool, sma50: bool, bb: bool, vol: bool }`.
- `priceLines`: `Array<{ price: number, color: string(hex), title: string,
  dashed: bool }>` — item com `price == null` é filtrado. `color` tem que ser
  **hex resolvido** (`ctx.palette`), nunca `T.x`/`var(--x)`: guardião
  `test_chart_colors_theme_aware.mjs` e o bug real do Modo Operador.
- `viewBars`: número de barras visíveis no fim da série. `onRange`: opcional.
- Fallback SVG interno (estado `failed`) usa `extentOf`/`linePath` — depois da
  Task 2 vêm de `chartutil.js`.

**8. `req` de `web/src/api.js` (L138) hoje perde o `code` do backend:**
`enrichErrorMessage(status, data, path)` (L69) devolve **string**; `detail.code`
(`mcp_nao_configurado` / `mcp_cota` / `mcp_teto_servico` / `mcp_erro_de_tool`)
é descartado. A tela precisa dele para escolher o estado — ver Task 2, item 2.2.
</interfaces>
</context>

<source_audit>
Fonte única: `docs/PLANO-aba-opcoes.md` §4 "Fase 2" + as restrições do
orquestrador (decisões travadas do Alex). Nenhum item fica de fora.

| # | Item da fonte | Coberto por |
|---|---|---|
| S-01 | rota `GET /leitura/{t}` (custo 3) | Task 1 |
| S-02 | rota `GET /setups/{name}/grafico` (custo 1) | Task 1 |
| S-03 | `evaluate_setups` `nao_avaliado` → 200 com `reason` verbatim | Task 1 |
| S-04 | `McpErroDeTool` → 422 via `_erro_http` | Task 1 |
| S-05 | `behavior.status == "sem_candles"` → 200 | Task 1 |
| S-06 | `chartutil.js` (extrair `extentOf/linePath/lastVal`) | Task 2 |
| S-07 | `api.js`: 3 métodos, timeout 30000, `encodeURIComponent` | Task 2 |
| S-08 | `persistence.js`: 3 métodos nos DOIS stores, delegação pura | Task 2 |
| S-09 | `copy.js`: `tabOpcoes`, `tituloOperadorIA`, textos nos dois modos | Task 2 |
| S-10 | `FONTES` do `test_guardrail_imperativo.py` | Task 2 (com ressalva escrita) |
| S-11 | `OpcoesScreen.jsx` (cabeçalho, Leitura, Setups) | Task 3 |
| S-12 | `useOpcoesMcp.js` | Task 3 |
| S-13 | `SetupChart.jsx` (disparos em `priceLines`) | Task 3 |
| S-14 | `defs`: `["agente","Operador IA"]` → `["opcoes", …]` | Task 3 |
| S-15 | render `tab === "opcoes"` | Task 3 |
| S-16 | `AgenteScreen` sob `carteiraView === "agente"` + `BackHeader` | Task 3 |
| S-17 | linha "Operador IA" no topo do Portfólio, padrão de "Histórico" | Task 3 |
| S-18 | `goAgente()` como ponto único | Task 3 |
| S-19 | `ctx.PriceChart` / `ctx.palette` | Task 3 |
| S-20 | `test_opcoes_mcp_aba_ui.mjs`, `test_operador_ia_subtela.mjs` | Task 3 |
| S-21 | estados: carregando → erro/não-configurado/cota/atrasado → vazio → dados | Task 3 |
| S-22 | 44px, `aria-label`, `aria-pressed`, sem `CONTENT_MAX_WIDTH`, zero import de `../App.jsx` | Task 3 |
| S-23 | `bash scripts/executar.sh --testes` + `npx vite build` | Task 4 |

**Instalação de pacote:** NENHUMA (npm/pip/cargo). O `mcp>=2.1,<3` entrou na
F1 e já está nos dois requirements. Não há Package Legitimacy Gate aplicável
nesta fase.
</source_audit>

<tasks>

<task type="auto">
  <name>Task 1: rotas de leitura e de gráfico de setup no options_mcp_api</name>
  <files>server/app/options_mcp_api.py, server/tests/test_options_mcp_leitura.py</files>
  <action>
Acrescente DUAS rotas ao router existente, sem mexer no `/status` (o
comportamento decidido na F1 §1 — erro de tool no `/status` responde 200 com
`bloqueia: true` — fica intacto).

**Antes de escrever, leia `server/app/options_mcp_api.py` inteiro uma vez.** Os
helpers `_cap_check`, `_cap_consume`, `_erro_http`, `_frescor`, `_dia_sp`,
`BRT`, `FONTE`, `RESET_TXT` já existem — reuse, não reescreva.

**(1.1) Constantes de texto e chave `medido` no frescor.**
Extraia o literal hoje inline em `_frescor` (linha 257, `frescor não medido: a
classe negociacao_b3 não veio na resposta`) para a constante de módulo
`AVISO_FRESCOR_NAO_MEDIDO`, e crie a segunda,
`AVISO_FRESCOR_NAO_MEDIDO_NA_LEITURA`, com o texto: `frescor não medido nesta
leitura: nenhum setup deste ticker foi avaliado`. Acrescente a chave `medido`
(booleano) ao dicionário devolvido por `_frescor` — verdadeiro apenas quando a
classe `negociacao_b3` veio na resposta E não houve erro de tool. Chave
ADITIVA: nenhum teste da F1 compara o dicionário inteiro (verificado —
`test_mcp_cap.py` só lê `bloqueia`, `warning`, `stale`, `bruto`).

**(1.2) `GET /leitura/{ticker}` — custo 3.**
Assinatura: função `async` com parâmetro de path `ticker` e
`user: dict = Depends(require_user)`. `_cap_check(uid, 3)` **na primeira linha
útil da própria função de rota** — o guardião (iv) da F1
(`test_mcp_guardioes.py:241`) faz `ast.walk` procurando o `Name` `_cap_check`
DENTRO da função decorada; esconder a chamada num helper reprova o guardião.

Sequência de chamadas, nesta ordem, cada uma sob `try/except`:
1. `propose_option_setups` com `{"ticker": ticker.upper()}` — sem `direction`,
   sem `kind`. É o que devolve `behavior`/`catalog`/`expirations`.
2. `list_setups` com `{}`.
3. `evaluate_setups` com `{}` — **pulada** quando o passo 2 não devolveu
   nenhum registro do ticker pedido (economia real de uma chamada; o cap já
   foi checado por 3, consumir menos é sempre permitido).

`_cap_consume(uid, 1)` após CADA chamada bem-sucedida cujo `ResultadoTool.cache`
seja falso. Acerto de cache não consome — mesma regra e mesmo motivo do
`/status`. Registre em comentário a decisão herdada da F1: **chamada que
terminou em `McpErroDeTool` NÃO consome** (o `/status` já opera assim); é uma
linha se o Alex preferir o contrário, e o SUMMARY tem de declarar isso como
decisão a avalizar.

Tratamento de exceção: `McpErro` e `ValueError` de qualquer um dos três passos
→ `obslog.log` no canal `mcp` com `level="warn"`, `rota`, `uid`, `ticker` e
`erro=type(e).__name__`, e então `raise _erro_http(e)`. `McpErroDeTool`
inclusive — aqui o erro da tool é falha do PEDIDO (ticker inexistente, sem
cotações), não estado a exibir: 422, exatamente como o `_erro_http` da F1 já
manda e como o SUMMARY da F1 previu.

Montagem da resposta (nada fabricado; ausência é `None`, nunca `0`, nunca lista
inventada):
- `pregao`: `trading_date` do `propose`, senão do `evaluate`, senão `None`.
- `fonte`: `FONTE`. `at`: agora em `BRT` no formato `%d/%m/%Y %H:%M` + sufixo ` BRT`.
- `behavior`: o `behavior` do `propose` **verbatim** (pode ser
  `{"status": "sem_candles"}` — passa igual, sem interpretar).
- `catalog`: o `catalog` do `propose` verbatim (`None` quando não veio).
- `expirations`: idem (`None` quando não veio).
- `setups`: lista, SÓ os registros cujo ticker do `setup` (em maiúsculas) bate
  com `ticker.upper()`. Cada item com as chaves:
  `name` (do `setup`); `ticker` em maiúsculas;
  `status` = o status do REGISTRO (`ativo`/`inativo`), com comentário
  explicitando que NÃO é o status da avaliação, que vive em `avaliacao.status`;
  `avaliacao` = o item de `evaluations` cujo `name` bate, ou `None`;
  `armed` e `streak` = da `avaliacao`, ou `None`;
  `required_streak` = da `avaliacao` quando houver, senão o `consecutive_days`
  do próprio `setup` (valor DECLARADO, não calculado — não é fabricação);
  `conditions` = da `avaliacao`, ou `None`;
  `backtest_na_criacao` = do registro.
- `setupsNaoAvaliados`: dicionário com a chave `reason` contendo o `reason` do
  `evaluate` **verbatim** quando o `status` do `evaluate` for `nao_avaliado`;
  caso contrário `None`. O status `sem_setups` NÃO é bloqueio:
  `setupsNaoAvaliados` fica `None` e cada `avaliacao` fica `None`.
- `frescor`: derivado SEM quarta chamada, por um helper novo
  `_frescor_da_avaliacao(evaluate_dados, chamou_evaluate)` que devolve as
  MESMAS chaves de `_frescor` (`classes`, `stale`, `warning`, `bloqueia`,
  `medido`, `bruto`) para o front ter um renderizador só:
  · `data_freshness` presente → uma entrada em `classes` com a classe
    `CLASSE_CRITICA` e a situação de `quotes`, e `bruto` = o próprio
    `data_freshness`; `medido` = situação diferente de `desconhecido`;
    `bloqueia` = situação diferente de `EM_DIA`;
  · status `nao_avaliado` → `warning` = o `reason` verbatim, `bloqueia`
    verdadeiro, `medido` falso;
  · `evaluate` não foi chamada → `classes` vazia, `bruto` `None`, `warning` =
    `AVISO_FRESCOR_NAO_MEDIDO_NA_LEITURA`, `medido` falso, `bloqueia`
    verdadeiro.
  Comentário obrigatório explicando POR QUE não há `check_data_freshness`
  aqui: o custo declarado no ADR-027 §3.3 é **3**, e uma quarta chamada faria
  o `_cap_check(uid, 3)` prometer menos do que o consumo real. O frescor
  medido de verdade continua vindo do `/status` (cache 600 s), que a tela
  chama junto — e "não medido" nunca passa por "em dia" (ADR-027, Decisão 8).
- `cap`: mesmo bloco do `/status` (`usado`, `limite`, `reinicia`).

**(1.3) `GET /setups/{name}/grafico` — custo 1.**
`_cap_check(uid, 1)` na própria função. `call_tool` da tool `get_setup_chart`
com `{"name": name}`. Consome 1 só quando `cache` for falso. Erro →
`_erro_http` (422 para setup inexistente, que é o `error` que a tool devolve).
Resposta: o dicionário da tool **espalhado primeiro**, e só depois as chaves de
envelope `pregao` (= `trading_date` da tool), `fonte` e `at` — nessa ordem,
para o envelope não ser sobrescrito pelo payload. **Sem `frescor` nesta rota**
(decisão travada do orquestrador; anote em comentário que diverge do "toda
resposta traz frescor" do §3.3 do PLANO, e o motivo: o gráfico é insumo do que
a leitura já carimbou, e uma chamada de frescor aqui violaria o custo 1).
Registre em comentário a limitação conhecida: nome de setup contendo barra não
resolve nesta rota (`{name}` não é conversor `path`, senão engoliria
`/grafico`).

**(1.4) Testes — `server/tests/test_options_mcp_leitura.py`.**
REUSE o esqueleto de `server/tests/test_mcp_cap.py`: fixture `_isolado`,
`_client(monkeypatch)`, `_registra`, `_auth`. O espião precisa ser mais rico
que o `_espiao` da F1 (que responde igual para toda tool): faça um
`_espiao_por_tool(monkeypatch, respostas)` que despacha pelo NOME da tool,
registra os pares nome/argumentos e levanta quando o valor mapeado é exceção.
Casos, um assert central cada:
1. sem sessão → 401 e **zero** chamadas ao serviço (nas duas rotas);
2. caminho feliz das três tools → 200 com `behavior`/`catalog`/`expirations`
   verbatim, `pregao` do `trading_date`, `fonte` igual a `mcp.semente.dev`, e
   `setups` com `armed`/`streak`/`required_streak` vindos de `evaluations`;
3. `list_setups` com registro de OUTRO ticker → `setups` vazio e
   `evaluate_setups` **não foi chamada** (o espião prova) — e o cap consumiu 2,
   não 3;
4. `evaluate_setups` devolvendo status `nao_avaliado` com um `reason` → 200,
   `setupsNaoAvaliados["reason"]` byte a byte igual ao `reason`, toda
   `avaliacao` `None`, `frescor["bloqueia"]` verdadeiro e `frescor["medido"]`
   falso;
5. `evaluate_setups` devolvendo status `sem_setups` → 200 e
   `setupsNaoAvaliados` `None`;
6. `propose` com `behavior` igual a `{"status": "sem_candles"}` → 200 e
   `behavior` idêntico;
7. `McpErroDeTool` em CADA uma das três tools (parametrizado) → 422 com
   `detail["code"]` igual a `mcp_erro_de_tool`;
8. cota estourada → 402 `mcp_cota` e **zero** chamadas ao serviço;
9. cache: `ResultadoTool` com `cache=True` nas três → 200 e `metering.used`
   inalterado (cache não gasta cap);
10. `/setups/{nome}/grafico` feliz → 200 com `pregao`/`fonte`/`at` E os arrays
    `dates`/`close`/`triggers`/`trigger_dates` intactos; nome inexistente
    (`McpErroDeTool`) → 422;
11. `pregao` é `None` quando nenhuma resposta traz `trading_date` — **nunca**
    uma data fabricada.

NÃO toque em `test_mcp_cap.py`, `test_mcp_guardioes.py`, `test_mcp_client.py`
nem `test_mcp_vivo.py`. Os guardiões (iv) e (v) da F1 passam a cobrir as rotas
novas automaticamente — se algum reprovar, o defeito é do código novo, não do
guardião.
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2/server && /Users/acamerini/dev/borisv2/server/.venv/bin/python -m pytest -q tests/test_options_mcp_leitura.py tests/test_mcp_cap.py tests/test_mcp_guardioes.py tests/test_adr013_rbac.py tests/test_opcoes_fronteira.py</automated>
  </verify>
  <done>As duas rotas respondem; `nao_avaliado` vira 200 com `reason` verbatim; erro de tool vira 422; cota estourada vira 402 sem tocar a rede; cache não consome cap; `pregao` é `None` quando não veio; guardiões (i)-(v) da F1 verdes.</done>
</task>

<task type="auto">
  <name>Task 2: infraestrutura de front — chartutil, api, stores, copy</name>
  <files>web/src/chartutil.js, web/src/App.jsx, web/src/api.js, web/src/persistence.js, web/src/copy.js, server/tests/test_guardrail_imperativo.py</files>
  <action>
**(2.1) `web/src/chartutil.js` — novo.**
Mova `extentOf` (App.jsx:1443), `linePath` (1450) e `lastVal` (1459) **byte a
byte**, com os comentários de origem, e exporte os três. Em `App.jsx`,
substitua as três definições por um import de `./chartutil.js` junto dos demais
imports do topo. Os usos internos (L1071, 1087, 1483, 1497-1498, 1631,
1634-1636, 1770-1771) continuam funcionando sem edição. Precedente da casa:
`markdown.jsx`. O módulo é puro (zero import de React, zero import de
`App.jsx`) — é isso que permite `SetupChart.jsx` usá-lo sem ciclo.

**(2.2) `web/src/api.js` — 3 métodos + `code` preservado no erro.**
Três métodos novos, no bloco dos demais métodos de opções, timeout **30000**
(dado de mercado, mesma classe de `optionsChain`/`optionsGate`; nenhum deles
chama LLM, então nada de `TIMEOUT_LLM`), com `encodeURIComponent` em todo
segmento vindo do usuário:
`mcpStatus` → GET `/api/options/mcp/status`;
`mcpLeitura(t)` → GET `/api/options/mcp/leitura/` + ticker codificado;
`mcpSetupGrafico(name)` → GET `/api/options/mcp/setups/` + nome codificado +
`/grafico`.

Em `req` (L138) o erro hoje perde o `code` do backend — a tela não consegue
distinguir `mcp_nao_configurado` de `mcp_cota` de `mcp_erro_de_tool` sem raspar
a string, o que é proibido. Correção MÍNIMA e aditiva: no ramo de resposta não
ok, extraia o `detail` com a MESMA regra de `enrichErrorMessage` (L70-71),
construa o `Error` com a mensagem **inalterada** (`enrichErrorMessage` continua
sendo a mensagem, byte a byte) e anexe as propriedades `status`, `code`
(= `code` do `detail` quando ele é objeto, senão `null`) e `detail`. Fatore a
extração do `detail` num helper `detalheDoErro(data)` usado nos dois pontos,
para não haver duas cópias da regra. Nenhum consumidor existente lê `.code` /
`.status` / `.detail`, e a `message` não muda — mudança sem risco de regressão.

**(2.3) `web/src/persistence.js` — 3 métodos nos DOIS stores.**
Delegação PURA, sem persistir nada (leitura de dado de mercado nunca se duplica
no aparelho — mesma regra já escrita para `optionsGate`/`optionsChain`/
`optionsProposta`). No `serverStore` (junto de `optionsProposta`, ~L269) os três
métodos delegam direto para `api`. No `deviceStore` (junto de `optionsProposta`,
~L1221) os MESMOS três nomes, `async`, cada um chamando `ensure()` antes de
delegar — igual ao `optionsProposta` de lá. Mesmo commit, mesmos nomes:
`test_fase3_paridade_stores_generica.mjs` compara os conjuntos e reprova
assimetria.

**(2.4) `web/src/copy.js` — chaves novas nos DOIS modos.**
Chaves IDÊNTICAS em `COPY.estudo` e `COPY.operador` (o guardião compara os
conjuntos ordenados). Bloco novo, colado logo depois de `tituloPortfolio` /
`subtituloPortfolio` em cada modo:

`tabOpcoes` (rótulo curto da barra) · `tituloOpcoes` · `subtituloOpcoes` ·
`tituloOperadorIA` · `linkOperadorIA` (texto da linha no topo do Portfólio) ·
`opcoesLeituraTitulo` · `opcoesSetupsTitulo` · `opcoesPregaoRotulo` ·
`opcoesFonteRotulo` · `opcoesFrescorEmDia` · `opcoesFrescorAtrasado` ·
`opcoesFrescorNaoMedido` · `opcoesSemSetups` · `opcoesNaoAvaliado` (função de 1
argumento, o `reason` verbatim; **tem de tolerar nulo** e devolver texto sem o
motivo nesse caso) · `opcoesNaoConfigurado` · `opcoesCota` (função de 1
argumento, a hora do reset; tolera nulo) · `opcoesIndisponivel` ·
`opcoesCarregando` · `opcoesEscolherAtivo` · `opcoesDisclaimer` ·
`opcoesGraficoTitulo` · `opcoesDisparosRotulo`.

Duas regras que `test_copy_theme.mjs` já impõe e que reprovam em silêncio quem
não souber:
· ele chama TODA função do dicionário com três strings **e** com nulo/zeros —
  nenhuma função pode estourar com argumento nulo;
· o regex do ramo ESTUDO é case-insensitive e casa `COMPRAR` e `VENDER` — ou
  seja, as palavras "comprar" e "vender" (e qualquer substring delas, como
  "vendedor") estão **PROIBIDAS** no ramo `estudo`. Fale de "estrutura",
  "posição", "montar", "estudar". No ramo `operador` o vocabulário de mesa é
  permitido, como no resto do arquivo.

Os textos de `estudo` seguem a voz de professor (explica o porquê) e os de
`operador` a voz de mesa — mesmo par de vozes do resto do dicionário. Nenhum
texto promete resultado; `opcoesDisclaimer` diz que a aba é educacional e que
os dados são de fim de pregão.

**(2.5) `FONTES` do `test_guardrail_imperativo.py` — o que fazer, e por quê.**
Esse guardião é **Python-only**: importa módulos e varre atributos de texto
(`llm.GUARDRAILS`, `skill_ref.TIMING`, `conceitos.CONCEITOS`). `copy.js` é
JavaScript e **não pode** entrar em `FONTES`; quem já cobre o ramo estudo de
`copy.js` é `web/tests/test_copy_theme.mjs` (assert "ramo ESTUDO sem
vocabulário de ordem"). É assim que o `[R-12]` do PLANO se cumpre — anote isso
em comentário datado no arquivo de teste.

A única adição real do lado Python é o texto fixo novo criado na Task 1:
acrescente a `FONTES` uma entrada `options_mcp_api.AVISOS` juntando
`AVISO_FRESCOR_NAO_MEDIDO` e `AVISO_FRESCOR_NAO_MEDIDO_NA_LEITURA` com quebra
de linha, com o `import` do módulo no topo do arquivo de teste, mais o
comentário datado registrando que a F1 já tinha esse literal sem cobertura. Se
o import de `options_mcp_api` puxar dependência pesada no teste, use
`importlib` como o resto da suíte já faz — não relaxe a asserção.
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2 && node web/tests/test_copy_theme.mjs && node web/tests/test_fase3_paridade_stores_generica.mjs && node web/tests/test_wiring_deps.mjs && node web/tests/test_chart_colors_theme_aware.mjs && node web/tests/test_fase20_fundacao_visual.mjs && (cd server && /Users/acamerini/dev/borisv2/server/.venv/bin/python -m pytest -q tests/test_guardrail_imperativo.py) && (cd web && npx vite build)</automated>
  </verify>
  <done>`chartutil.js` exporta os três helpers e App.jsx os importa (zero definição local sobrando); os 3 métodos existem em `api.js` e nos DOIS stores com nomes idênticos; `err.code` chega ao chamador sem mudar `err.message`; chaves de copy espelhadas nos dois modos, ramo estudo sem "comprar"/"vender"; `vite build` verde.</done>
</task>

<task type="auto">
  <name>Task 3: tela da aba Opções, troca de navegação e guardiões</name>
  <files>web/src/opcoes/OpcoesScreen.jsx, web/src/opcoes/useOpcoesMcp.js, web/src/opcoes/SetupChart.jsx, web/src/App.jsx, web/tests/test_opcoes_mcp_aba_ui.mjs, web/tests/test_operador_ia_subtela.mjs, web/tests/test_pet_ui.mjs</files>
  <action>
**(3.1) `web/src/opcoes/useOpcoesMcp.js` — novo.**
Hook que encapsula as três chamadas. Recebe o `store` por argumento (nunca
importa `persistence.js` direto: mantém o arquivo testável e evita acoplar a
tela ao módulo de estado). Expõe, para cada chamada, o trio
`dados / carregando / erro`, onde `erro` guarda o objeto de erro inteiro (para
a tela ler `erro.code` e `erro.message`). Regras:
· `status` e `leitura` disparam por `useEffect`; `grafico` dispara sob demanda
  (o usuário abre um setup);
· toda chamada em voo é invalidada quando o ticker muda (guarde um contador de
  requisição num `useRef` e descarte resposta antiga) — sem isso, trocar de
  ticker rápido pinta a tela com o dado do ticker anterior;
· `carregando` começa **verdadeiro** e só vira falso quando a promessa
  resolve ou rejeita — o estado "carregando" tem de vir ANTES do estado
  "vazio", nunca depois.

**(3.2) `web/src/opcoes/SetupChart.jsx` — novo.**
Recebe `{ ctx, grafico, palette }`. Adapta a resposta de `get_setup_chart`
(arrays paralelos) para o formato exato de `ctx.PriceChart` descrito em
`<interfaces>` item 7:
· `candles[i] = { date: dates[i], open: open[i], high: high[i], low: low[i],
  close: close[i], volume: volume[i] }` — construído por índice sobre `dates`;
· `ind`: os QUATRO campos são obrigatórios, senão `PriceChart` estoura em
  `arr[i]`. `series` traz nomes arbitrários (`sma21`, `rsi14`, `highest20`),
  nunca `sma20`/`sma50`. Regra determinística: ordene as chaves de `series`
  alfabeticamente, jogue a 1ª no slot `sma20` e a 2ª no slot `sma50`, e
  preencha `bbUpper`/`bbLower` (e os slots sem série) com um array de `null` do
  mesmo comprimento de `candles`. Renderize uma legenda dizendo o NOME REAL de
  cada série mapeada — o usuário não pode ler "SMA 20" onde o dado é `rsi14`.
  Por isso `show` deve vir com `bb` falso e `vol` verdadeiro, e os rótulos dos
  toggles vêm da legenda, não das constantes de App.jsx;
· `priceLines`: para cada índice em `triggers`, um item com `price` =
  `close[indice]`, `title` = a data correspondente em `trigger_dates`,
  `dashed` verdadeiro e `color` = `palette.accent` (**hex resolvido do
  `ctx.palette`**, nunca `T.x`/`var(--x)` — guardião
  `test_chart_colors_theme_aware.mjs` e o bug real do Modo Operador). Item com
  `close` não numérico é DESCARTADO (nunca vira 0). Limite a 8 linhas, as mais
  recentes, e diga em texto quantos disparos existem no total quando houver
  mais — o eixo de preço fica ilegível com dezenas de linhas;
· `viewBars`: número fixo razoável (por exemplo 120) ou o comprimento da série
  quando for menor.

**Fallback obrigatório:** quando `ctx.PriceChart` for ausente, renderize a
lista textual dos disparos (data + preço de fechamento), com o mesmo aviso de
pregão. Nunca uma tela em branco.

Tokens: bloco `VARKEY`/`TOKENS`/`T` idêntico ao de `web/src/pet/BorisChat.jsx`
(linhas 26-33) — **zero import de `../App.jsx`** (ciclo).

**(3.3) `web/src/opcoes/OpcoesScreen.jsx` — novo.**
Assinatura `function OpcoesScreen({ ctx })`. Mesmo bloco de tokens do item
anterior. Consome `ctx.store` (ou `ctx.A`/`ctx` conforme o que já estiver
disponível — **verifique no `ctx` real antes de decidir**, e se o `store` não
estiver lá, adicione-o ao `ctx` no item 3.4), `ctx.cp`, `ctx.palette`,
`ctx.PriceChart`.

Ordem de estados, exatamente esta (nenhum pulado):
1. **carregando** — esqueleto, texto de `cp.opcoesCarregando`;
2. **erro / não configurado / cota / atrasado**, nesta precedência, escolhidos
   pelo `erro.code` que a Task 2 passou a expor:
   `mcp_nao_configurado` → `cp.opcoesNaoConfigurado`;
   `mcp_cota` e `mcp_teto_servico` → `cp.opcoesCota(reinicia)` lendo
   `erro.detail.reinicia` (nulo é tolerado pela função);
   `mcp_indisponivel` → `cp.opcoesIndisponivel`;
   qualquer outro (inclusive `mcp_erro_de_tool`) → renderize `erro.message`
   cru, com `whiteSpace: "pre-wrap"` (a mensagem já vem multi-linha com
   "Como corrigir:" / "Dica:" do `enrichErrorMessage`);
3. **vazio com motivo** — sem ticker escolhido (`cp.opcoesEscolherAtivo`), ou
   ticker sem setups (`cp.opcoesSemSetups`), ou `behavior.status` igual a
   `sem_candles` (texto próprio dizendo que não há candles para este ativo).
   Vazio **nunca** é silêncio;
4. **dados**.

Cabeçalho, sempre visível e sempre no topo, mesmo nos estados de erro em que
haja dado parcial: o **pregão** (do `/leitura` ou do `/status`), o rótulo de
fonte (`cp.opcoesFonteRotulo` + `mcp.semente.dev`), e o chip de frescor em
TRÊS variantes distintas — `em dia` (`cp.opcoesFrescorEmDia`), `atrasado` com a
idade real quando houver (`cp.opcoesFrescorAtrasado`), e `não medido`
(`cp.opcoesFrescorNaoMedido`). **Nunca afirme "em dia" por default**: a
variante "em dia" só aparece quando `frescor.medido` for verdadeiro E
`frescor.bloqueia` for falso. `frescor.bloqueia` verdadeiro vira aviso visível
— e **não bloqueia a leitura**, só marca (a Fase 2 não tem veredito nem criação
de setup para bloquear).

Seção **Leitura**: tendência, RSI 14, hv21/hv63, distância das médias 21/63,
faixa de 63 pregões (máxima/mínima) e variação de 21 pregões — todos vindos de
`behavior`, todos com o carimbo do pregão. Campo ausente mostra travessão,
**nunca 0**. Nenhum número é recalculado no front.

Seção **Setups**: um cartão por item de `setups`, com `name`, o status do
registro, `armed`/`streak`/`required_streak` quando houver, as `conditions`
(cada uma com o `summary` e se bateu), e `backtest_na_criacao` resumido. Quando
`setupsNaoAvaliados` não for nulo, uma faixa no topo da seção com
`cp.opcoesNaoAvaliado(reason)` exibindo o motivo **verbatim** e cada cartão sem
veredito de armado (nunca "não armado" por ausência de avaliação). Um botão por
cartão abre o `SetupChart` daquele setup.

Acessibilidade e layout: todo alvo de toque com `minHeight: "44px"`; todo botão
só-ícone com `aria-label`; todo seletor (lista de tickers, escolha de setup)
com `aria-pressed`; **não** use `CONTENT_MAX_WIDTH` (o wrapper de conteúdo do
App já limita, e o guardião `test_fase20_fundacao_visual.mjs` conta exatamente
2 usos em App.jsx); nada de verde/vermelho fora de P&L; sem "probabilidade de
sucesso" nem promessa de resultado; `cp.opcoesDisclaimer` fixo no rodapé da
tela.

A lista de tickers oferecida vem da watchlist do usuário (`ctx.data.watchlist`)
— não invente um universo, e não faça chamada extra para descobrir tickers.

**(3.4) `web/src/App.jsx` — navegação e ctx.**
· Import de `OpcoesScreen` junto dos demais imports do topo.
· `defs` do `BottomNav` (L971): trocar `["agente", "Operador IA"]` por
  `["opcoes", (cp && cp.tabOpcoes) || "Opções"]`. As duas linhas que
  `test_copy_theme.mjs` afirma (`["mercado", (cp && cp.tituloWatchlist)` e
  `["radar", (cp && cp.tabRadar)`) ficam INTACTAS. O ícone `opcoes` já existe
  em `NavIcon.paths` (Fase 22) — e o `agente` também, e **não pode ser
  removido** (`test_fase22_componentes_compartilhados.mjs:179`).
· `carteiraView` (L7844): comentário passa a `// main | historico | agente`.
· `goAgente`: função no escopo do componente raiz que faz
  `setPerfilView("hub")`, `setTab("carteira")` e `setCarteiraView("agente")`,
  exposta no `ctx` (e em `A`, se algum consumidor fora do `ctx` precisar —
  atenção: se entrar no `useMemo(A)`, ela só chama setters, que são estáveis,
  então nenhuma dep nova é necessária e `test_wiring_deps.mjs` continua verde).
· Render (L9295): remova `{tab === "agente" && <AgenteScreen ctx={ctx} />}` e
  acrescente `{tab === "opcoes" && <OpcoesScreen ctx={ctx} />}` na mesma lista.
· Ramo do Portfólio (L9296-9298): passa a ter três casos, no MESMO padrão que
  "Histórico" já usa —
  `carteiraView === "historico"` → `BackHeader` + `HistoricoScreen`;
  `carteiraView === "agente"` → `BackHeader` com `cp.tituloOperadorIA` e
  `onBack` voltando para `"main"`, seguido de `<AgenteScreen ctx={ctx} />`;
  caso contrário → `CarteiraScreen` mais, **no topo** (antes do conteúdo do
  Portfólio, não no rodapé), uma linha de acesso ao Operador IA no mesmo estilo
  visual do botão "Ver histórico de operações" já existente, com
  `cp.linkOperadorIA`, `minHeight` de pelo menos 48px e `onClick` chamando
  `goAgente()`. O botão de histórico continua onde está.
· `petTela` (L9155): passa a mapear `carteiraView === "agente"` para
  `"agente"`, mantendo `"historico"` e o default `"carteira"`. O `case
  "agente":` do `petSnapshot` (L9199) **fica** — é ele que
  `test_pet_ui.mjs:160` exige.
· `ctx`: acrescente `PriceChart` (o componente, referenciado por nome — ele já
  está no escopo do módulo) e `palette` (o resultado de `usePalette()`; se o
  raiz ainda não chamar `usePalette`, chame — é o mesmo hook que `PriceChart`
  usa). Acrescente `store` ao `ctx` **apenas se ele ainda não estiver lá**;
  confira antes com uma leitura do bloco `const ctx = {` (L9011) — se as telas
  hoje chegam ao store por outro caminho, use o caminho existente em vez de
  criar um segundo.
· Textos do tour e do card de modo que dizem "a aba Operador IA" (L2261, L2262,
  L2379 e o texto de L6423) deixaram de ser verdade: troque "aba Operador IA"
  por "Operador IA (dentro do Portfólio)" nos quatro pontos. **Cuidado:** L2379
  é a CHAVE de uma entrada de tour (`["Operador IA", [ … ]]`) — o título pode
  ficar; o que muda é o corpo que chama de "aba".

**(3.5) `web/tests/test_operador_ia_subtela.mjs` — novo.**
Padrão "static source inspection" da casa (leitura de `App.jsx` + import de
`COPY`, sem build e sem DOM), com a higiene de filtrar linhas de comentário
ANTES de qualquer contagem — o próprio comentário deste plano ou de App.jsx
inflaria o número e auto-invalidaria o guardião. Asserções:
1. `defs` do `BottomNav` tem 5 itens e o 5º é `["opcoes", (cp && cp.tabOpcoes)`;
2. **zero** ocorrências de `["agente", "Operador IA"]` no fonte sem comentários;
3. **zero** ocorrências de `tab === "agente"` no fonte sem comentários;
4. existe `tab === "opcoes" && <OpcoesScreen`;
5. existe `carteiraView === "agente"` no ramo do Portfólio, com `BackHeader`
   e `<AgenteScreen ctx={ctx} />` no mesmo ramo;
6. `goAgente` está definido uma única vez e é chamado pela linha do Portfólio;
7. a linha do Portfólio usa `cp.linkOperadorIA` e `minHeight` de ao menos 48px;
8. `NavIcon.paths` continua com os ids `opcoes` E `agente`;
9. `petTela` cobre os três casos (`agente`, `historico`, default);
10. o `case "agente":` do `petSnapshot` continua existindo;
11. `COPY.estudo` e `COPY.operador` têm `tabOpcoes`, `tituloOperadorIA` e
    `linkOperadorIA`, com os mesmos conjuntos de chaves;
12. nenhum ponto do fonte chama a superfície de "aba Operador IA" (o texto
    antigo sumiu dos quatro pontos).

**(3.6) `web/tests/test_opcoes_mcp_aba_ui.mjs` — novo.**
Mesma técnica, lendo os TRÊS arquivos de `web/src/opcoes/` (mais `COPY`).
Asserções:
1. nenhum dos três importa `../App.jsx` (regex sobre a linha de import) — ciclo;
2. os três declaram o bloco `VARKEY`/`TOKENS`/`T` local (padrão `BorisChat`);
3. `OpcoesScreen` contém, na ordem em que aparecem no fonte, os quatro estados:
   carregando → (erro | `mcp_nao_configurado` | `mcp_cota` | frescor
   bloqueante) → vazio com motivo → dados (asserte por índice de ocorrência,
   não só por presença);
4. o ramo de erro renderiza `whiteSpace: "pre-wrap"` e usa `erro.message`;
5. os códigos `mcp_nao_configurado`, `mcp_cota`, `mcp_teto_servico` e
   `mcp_indisponivel` aparecem todos, cada um com sua chave de copy;
6. a frase de frescor "em dia" está **condicionada** a `frescor.medido` — o
   guardião procura a leitura de `medido` no mesmo bloco da variante em dia;
7. `pregao` aparece no cabeçalho e não está dentro de nenhum ramo condicional
   de erro;
8. há ao menos um `minHeight: "44px"`, ao menos um `aria-label` e ao menos um
   `aria-pressed`;
9. **zero** ocorrências de `CONTENT_MAX_WIDTH` nos três arquivos;
10. `SetupChart` usa `ctx.PriceChart`, tem o ramo de fallback textual, mapeia
    `trigger_dates`/`triggers` para `priceLines`, e **não** usa `T.` dentro de
    `color:` de `priceLines` (usa `palette.`);
11. `SetupChart` sempre preenche os quatro campos de `ind`
    (`sma20`/`sma50`/`bbUpper`/`bbLower`) — o guardião procura os quatro nomes;
12. nenhum dos três arquivos contém "probabilidade de sucesso", "garantia",
    "lucro certo", nem "comprar"/"vender" em texto de UI do ramo estudo (a
    tela lê tudo de `cp`, então basta afirmar que não há literal de frase
    longa hardcodado fora de `cp.`);
13. o comprimento do array de `null` usado para preencher `ind` deriva do
    comprimento dos candles (nada de tamanho fixo).

**(3.7) `web/tests/test_pet_ui.mjs` — guardião que DISPARA, atualizar com nota.**
A linha 161 afirma a regex EXATA do `petTela` antigo. Atualize a regex para a
forma nova (três casos) e acrescente **acima dela** um comentário datado
`2026-09-10 (aba-opcoes F2, quick 260910-biz)` dizendo o que mudou e por quê:
Operador IA virou sub-tela do Portfólio (D-0.1 do `docs/PLANO-aba-opcoes.md`),
então `carteiraView` passou a ter três valores e o cálculo do `petTela`
acompanhou. **Não apague nada** e não relaxe a asserção para um regex frouxo —
a nova regex tem de ser tão exata quanto a antiga. `ABAS_PET` (L160) fica
intacta.
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2 && node web/tests/test_operador_ia_subtela.mjs && node web/tests/test_opcoes_mcp_aba_ui.mjs && node web/tests/test_pet_ui.mjs && node web/tests/test_copy_theme.mjs && node web/tests/test_fase22_componentes_compartilhados.mjs && node web/tests/test_fase20_fundacao_visual.mjs && node web/tests/test_chart_colors_theme_aware.mjs && (cd web && npx vite build)</automated>
  </verify>
  <done>Barra com 5 itens e `Opções` no lugar de `Operador IA`; `tab === "opcoes"` renderiza `OpcoesScreen`; Operador IA acessível pela linha no topo do Portfólio com `BackHeader` e por `goAgente()`; zero `tab === "agente"` e zero `["agente", "Operador IA"]` sobrando; os três arquivos de `web/src/opcoes/` sem import de `App.jsx` e sem `CONTENT_MAX_WIDTH`; `vite build` verde.</done>
</task>

<task type="auto">
  <name>Task 4: validação canônica e commits</name>
  <files>(nenhum arquivo de código — validação e commits)</files>
  <action>
**(4.1) Suíte canônica INTEIRA, uma vez, com a saída colada no SUMMARY:**
`bash scripts/executar.sh --testes` a partir da raiz do repositório. Ela roda
as DUAS suítes (pytest do backend + `web/tests/*.mjs`); `scripts/test.sh`
sozinho é meia baseline e **não conta** como validação.

Ressalva conhecida da F1, registrada no SUMMARY dela: rodando de worktree, o
wrapper cai no venv do clone principal, que pode não ter o `mcp` instalado — o
sintoma são falhas `ModuleNotFoundError: No module named 'mcp'` **apenas** em
`test_mcp_client.py`. Se aparecer, rode a linha de pip que a F1 documentou
(`server/.venv/bin/python -m pip install -r server/requirements.txt` no clone
principal) e rode a suíte de novo. Falha de qualquer outra natureza é
regressão desta fase e tem de ser corrigida, não explicada.

Baselines para comparar (STATE.md / SUMMARY da F1): backend **2225 passed, 4
skipped**; web **124/124 arquivos OK**. Os arquivos novos sobem os dois
números; nenhum número pode CAIR.

**(4.2) `npx vite build` dentro de `web/`** — obrigatório porque esta fase
edita `web/src/`. Grep e teste estático não pegam erro de sintaxe JS.

**(4.3) Higiene do diff antes de commitar:**
`git diff --stat` contra a base tem de bater exatamente com `files_modified`
do frontmatter. **Zero** arquivos de `web-admin/`, `server/web_dist`,
`server/admin_dist`, `server/ios_dist`, `SERVER_BUILD_ID`, `web/src/version.js`
ou configuração do Railway. `docs/PLANO-aba-opcoes.md` **não** pode aparecer no
diff. Varredura de segredo no diff (`MCP_CLIENT_SECRET`, tokens `eyJ`,
`mcp_...`): zero ocorrência real.

**(4.4) Commits atômicos, PT-BR, referenciando `aba-opcoes F2` e `260910-biz`,
um por task:**
`feat(260910-biz): rotas de leitura e grafico de setup (aba-opcoes F2)`;
`feat(260910-biz): chartutil, api, stores e copy da aba (aba-opcoes F2)`;
`feat(260910-biz): tela de Opcoes e Operador IA como sub-tela (aba-opcoes F2)`.

**(4.5) NÃO fazer, em nenhuma hipótese:** `bump.sh`, `publicar-web.sh`,
`atualizar.sh`, deploy no Railway, editar `server/web_dist`, mexer em
`SERVER_BUILD_ID`, tocar `web-admin/`, dar push para `origin`.

**(4.6) O SUMMARY tem de declarar, em seção própria:** (a) a decisão herdada
sobre não consumir cap em chamada que terminou em `McpErroDeTool`, para o Alex
avalizar; (b) o desvio deliberado de `/setups/{name}/grafico` não carregar
`frescor` (contra o "toda resposta traz frescor" do §3.3 do PLANO) e o motivo;
(c) que o `frescor` do `/leitura` é derivado do `data_freshness` do
`evaluate_setups`, sem quarta chamada, para o custo continuar sendo 3; (d) que
`copy.js` não entrou em `FONTES` do `test_guardrail_imperativo.py` porque o
guardião é Python-only e `test_copy_theme.mjs` já cobre; (e) a limitação de
nome de setup com barra na rota de gráfico; (f) que a tela **não foi verificada
ao vivo** — sem `MCP_CLIENT_SECRET` no ambiente, a aba mostra "serviço de
opções não configurado", que é o comportamento correto mas não prova a
renderização com dado real.
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2 && bash scripts/executar.sh --testes</automated>
  </verify>
  <done>Suíte canônica inteira verde (backend sem cair de 2225 passed, web 124+/124 arquivos OK); `npx vite build` verde; diff bate com `files_modified`, sem `web_dist`/`SERVER_BUILD_ID`/`web-admin`/segredo; três commits atômicos criados; nenhum push, nenhum bump, nenhum deploy.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| navegador/iPhone → `/api/options/mcp/*` | entrada não confiável (`ticker`, `name`) cruza aqui |
| backend Boris → `mcp.semente.dev` | credencial de máquina e teto compartilhado por TODA a base |
| resposta do serviço MCP → UI | payload de terceiro renderizado ao usuário |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-biz-01 | Elevation of Privilege | `GET /leitura/{ticker}`, `GET /setups/{name}/grafico` | mitigate | `Depends(require_user)` em ambas; guardião (iv) da F1 (`test_mcp_guardioes.py:241`) reprova rota sem ele; teste 1 da Task 1 prova 401 com zero chamadas à rede |
| T-biz-02 | Denial of Service | teto de 2.000 chamadas/dia compartilhado | mitigate | `_cap_check` na PRÓPRIA função de rota antes de qualquer chamada (custo 3 e 1); `_cap_consume` só por chamada que não veio do cache; teste 8 prova 402 sem tocar a rede |
| T-biz-03 | Information Disclosure | `MCP_CLIENT_SECRET` em log/erro | mitigate | nenhum literal de segredo é escrito; `_erro_http` já não ecoa credencial; guardião (iii) da F1 varre `server/app/` inteiro; item 4.3 varre o diff |
| T-biz-04 | Tampering | `name`/`ticker` vindos do cliente na URL | mitigate | `encodeURIComponent` no `api.js`; o valor é repassado como ARGUMENTO de tool JSON-RPC (não concatenado em SQL/shell); nome com barra simplesmente 404, documentado |
| T-biz-05 | Spoofing | payload do serviço renderizado na UI | mitigate | React escapa texto por default; nenhum `dangerouslySetInnerHTML` nos três arquivos novos; `reason` e `error.message` vão para nós de texto com `pre-wrap`, nunca para HTML |
| T-biz-06 | Repudiation | quem chamou o quê e quanto gastou | mitigate | `obslog.log` no canal `mcp` em cada rota, com `uid`, `rota`, `ticker`, `cache` e `erro`; o cap grava em `mcpUsage*` por escopo |
| T-biz-07 | Information Disclosure | licença de uso pessoal do serviço MCP reexposta a terceiros | accept | risco aceito pelo Alex em D-0.2 e registrado no ADR-027 §Decisão 6; mitigação nomeada (um `require_permission` por rota) se a licença apertar |
| T-biz-SC | Tampering | instalações npm/pip/cargo | n/a | **nenhum pacote novo nesta fase**; `mcp>=2.1,<3` entrou na F1 com os pins já auditados. Se o executor precisar instalar QUALQUER pacote, PARE e volte ao orquestrador — o gate de legitimidade não foi rodado para esta fase |
</threat_model>

<verification>
1. `bash scripts/executar.sh --testes` — as DUAS suítes, saída colada no SUMMARY.
2. `cd web && npx vite build` — obrigatório, `web/src/` foi editado.
3. `git diff --stat` bate com `files_modified`; zero `web_dist`, `admin_dist`,
   `ios_dist`, `SERVER_BUILD_ID`, `web-admin/`, `docs/PLANO-aba-opcoes.md`.
4. Guardião `test_pet_ui.mjs` atualizado COM nota datada — nenhum apagado.
5. Backend sem cair de 2225 passed; web sem cair de 124 arquivos OK.
</verification>

<success_criteria>
- As duas rotas novas respondem e degradam pelos códigos do ADR-027 (503
  `mcp_nao_configurado`, 402 `mcp_cota`/`mcp_teto_servico`, 422
  `mcp_erro_de_tool`, 503 `mcp_indisponivel`) — nada cai no handler 500.
- `evaluate_setups` com `nao_avaliado` vira 200 com o `reason` verbatim e
  `avaliacao` nula, nunca "não armado" por ausência de avaliação.
- `pregao` é `None` quando não veio; nenhum campo ausente vira 0.
- Cache não gasta cap; recusa por cota acontece antes da rede.
- Barra inferior com 5 itens, `Opções` no lugar de `Operador IA`; Operador IA
  acessível pelo topo do Portfólio, com `BackHeader`, tela inalterada.
- Zero `tab === "agente"` e zero `["agente", "Operador IA"]` sobrando.
- Os três arquivos de `web/src/opcoes/` não importam `App.jsx` e não usam
  `CONTENT_MAX_WIDTH`.
- Chaves de copy espelhadas nos dois modos; ramo estudo sem "comprar"/"vender".
- `test_pet_ui.mjs` atualizado com nota datada; nenhum outro guardião tocado.
- Suíte canônica verde e `vite build` verde.
- Nenhuma publicação, nenhum bump, nenhum deploy, nenhum push.
</success_criteria>

<output>
Create `.planning/quick/260910-biz-aba-opcoes-f2-leitura-setups-troca-de-aba/260910-biz-SUMMARY.md` when done.
</output>
