---
quick_id: 260910-biz
titulo: "Aba Opções — Fase 2: leitura, setups e a troca de aba"
status: complete
data: 2026-09-10
base: fbc47226ed53015514275f96e2810cf848eda304
branch: worktree-agent-a696d3f6a2f9d0694
commits:
  - 3aff231 "feat(260910-biz): rotas de leitura e grafico de setup (aba-opcoes F2)"
  - 404f8e6 "feat(260910-biz): chartutil, api, stores e copy da aba (aba-opcoes F2)"
  - 3be7a30 "feat(260910-biz): tela de Opcoes e Operador IA como sub-tela (aba-opcoes F2)"
  - 5de774c "fix(260910-biz): dois guardioes que a troca de aba derrubou (aba-opcoes F2)"
suite:
  backend: "2239 passed, 4 skipped (baseline F1: 2225 passed, 4 skipped)"
  web: "126/126 arquivos OK (baseline F1: 124/124)"
  comando: "bash scripts/executar.sh --testes (RC=0)"
build: "cd web && npx vite build — ✓ built in 1.17s"
deploy: nenhum (sem bump, sem publicar, sem railway, sem push)
front_tocado: sim (web/src/ — publicação é de outra fase)
verificado_ao_vivo: não (sem MCP_CLIENT_SECRET no ambiente)
---

# Quick 260910-biz — Aba Opções, Fase 2

Duas rotas de leitura do serviço MCP, a tela da aba Opções em arquivos
próprios (`web/src/opcoes/`), e a troca de navegação da D-0.1: **Opções entra
na barra inferior no lugar de "Operador IA", que virou sub-tela do
Portfólio**. Sem cadeia, sem payoff, sem veredito — isso é Fase 3–4.

---

## 1. DECISÕES E DESVIOS PARA O ALEX AVALIZAR

### (a) Chamada que morre em `McpErroDeTool` NÃO consome cap — herdado da F1

`_chamada_com_cap` consome 1 do cap **depois** do `await`, então qualquer
exceção pula o consumo — inclusive `McpErroDeTool`, que é o caso em que a
viagem até o serviço de fato aconteceu e o teto compartilhado de 2.000/dia
foi tocado. É o mesmo comportamento que o `/status` da F1 já tinha.

O argumento a favor: o usuário não deve pagar cota por um ticker que não
existe. O argumento contra: o teto do SERVIÇO foi consumido de qualquer
jeito, e um laço de pedidos inválidos queima o teto de toda a base sem gastar
a cota de ninguém. **É uma linha para inverter** (mover o `_cap_consume` para
um `finally`). Fica registrado para decisão, não implementado.

### (b) `GET /setups/{name}/grafico` não carrega `frescor` — desvio deliberado

O §3.3 do `docs/PLANO-aba-opcoes.md` diz "toda resposta traz `pregao`,
`fonte`, `at`, `frescor`". Esta rota traz os três primeiros e **não** o
frescor. Motivo: medir frescor exigiria uma segunda chamada de tool, e o
custo declarado da rota no ADR-027 é **1**. Quem carimba frescor é o
`/leitura` e o `/status`, que a tela chama antes desta — o gráfico é insumo do
que a leitura já carimbou. Anotado em comentário na própria rota.

### (c) O `frescor` do `/leitura` é DERIVADO, sem quarta chamada

`_frescor_da_avaliacao()` monta as mesmas chaves de `_frescor` a partir do
`data_freshness` que `evaluate_setups` já devolveu. Não há
`check_data_freshness` na rota: o custo declarado é 3, e uma quarta chamada
faria `_cap_check(uid, 3)` prometer menos do que o consumo real — subestimar
o consumo é exatamente como o teto compartilhado estoura em silêncio.

Quando não há medição (evaluate pulada, ou gate `nao_avaliado`), `medido` é
falso e `bloqueia` é verdadeiro. **"Não medido" nunca passa por "em dia"**
(ADR-027, Decisão 8) — e a tela só mostra a variante "em dia" com
`frescor.medido` verdadeiro E `frescor.bloqueia` falso.

### (d) `copy.js` NÃO entrou em `FONTES` do `test_guardrail_imperativo.py`

Não é esquecimento: aquele guardião é **Python-only** — importa módulos e lê
atributos de texto. `copy.js` é JavaScript. Quem tranca o ramo estudo de
`copy.js` contra vocabulário de ordem é `web/tests/test_copy_theme.mjs`
("ramo ESTUDO sem vocabulário de ordem"), que já roda na suíte canônica. É
assim que o `[R-12]` do PLANO se cumpre. Anotado em comentário datado dentro
do próprio `FONTES`.

O que **entrou** de verdade em `FONTES`: `options_mcp_api.AVISOS`, os dois
textos de frescor que chegam ao usuário sem passar por LLM nenhuma. A F1
tinha criado esse literal inline e ele estava sem cobertura.

### (e) Limitação conhecida: nome de setup com barra

`GET /setups/{name}/grafico` usa `{name}` como segmento simples, não
conversor `path` — transformá-lo em `path` engoliria o `/grafico` do fim da
URL. Setup cujo nome contenha `/` devolve 404 do roteador. Documentado em
comentário na rota.

### (f) A tela NÃO foi verificada ao vivo

Sem `MCP_CLIENT_SECRET` no ambiente, a aba mostra "serviço de opções não
configurado" — que é o comportamento correto, e é exatamente o estado que os
testes cobrem, mas **não prova a renderização com dado real**. A leitura, os
cartões de setup e o gráfico de disparos só se confirmam com credencial no
servidor. Nenhum print, nenhum caminho feliz visto com os olhos.

---

## 2. O que mudou

### Backend — `server/app/options_mcp_api.py`

Duas rotas novas, `/status` intocado (o 200-com-`bloqueia` da F1 continua
valendo).

**`GET /leitura/{ticker}`, custo 3.** `_cap_check(uid, 3)` na primeira linha
útil da própria função (o guardião (iv) da F1 faz `ast.walk` e reprova quem
esconde a chamada num helper). Sequência: `propose_option_setups`
(sem `direction`/`kind` — é a forma que devolve `behavior`/`catalog`/
`expirations`), `list_setups`, e `evaluate_setups` **pulada** quando o ticker
não tem nenhum registro (gasta 2 em vez de 3; consumir menos que o checado é
sempre permitido, o contrário não).

Resposta: `behavior`, `catalog`, `expirations` e `conditions` viajam
**verbatim**. `pregao` é `None` quando nenhuma resposta traz `trading_date`.
`setupsNaoAvaliados.reason` é byte a byte o `reason` do serviço, e nesse caso
toda `avaliacao` fica `None` — ausência de leitura não vira "não armado".
`required_streak` sem avaliação cai no `consecutive_days` DECLARADO no setup
(valor escrito pelo usuário, não número calculado).

`status` do REGISTRO (`ativo`/`inativo`) fica separado do `status` da
AVALIAÇÃO (`avaliado`/`nao_avaliavel`/…), que vive em `avaliacao.status` —
confundir os dois faria a tela dizer "ativo" onde o serviço disse "não
consegui avaliar".

**`GET /setups/{name}/grafico`, custo 1.** Payload da tool espalhado
primeiro, envelope depois (invertido, o `trading_date` do payload
sobrescreveria o `pregao` do envelope).

Também: `AVISO_FRESCOR_NAO_MEDIDO` e `AVISO_FRESCOR_NAO_MEDIDO_NA_LEITURA`
extraídos para constante; chave `medido` (aditiva) no `_frescor`, para a UI
separar os três estados sem raspar o texto do `warning`.

### Backend — `server/tests/test_options_mcp_leitura.py` (novo, 14 testes)

Espião `_espiao_por_tool` que despacha pelo NOME da tool — a `/leitura` chama
três numa requisição só, e a afirmação central de dois testes é justamente
*qual* delas foi chamada. Cobre: 401 sem tocar a rede (nas duas rotas);
caminho feliz verbatim; economia de chamada (evaluate pulada, cap consumiu 2);
`nao_avaliado` com `reason` byte a byte e zero veredito; `sem_setups` não é
bloqueio; `sem_candles` idêntico; `McpErroDeTool` em cada um dos três passos
(parametrizado) → 422; cota cheia → 402 sem rede; cache não consome; gráfico
com arrays intactos e setup inexistente → 422; `pregao` `None`.

### Front — `web/src/chartutil.js` (novo)

`extentOf`/`linePath`/`lastVal` saíram de `App.jsx` **byte a byte**.
Módulo puro (zero React, zero `App.jsx`) — é o que permite `SetupChart.jsx`
usá-los sem ciclo. Precedente da casa: `markdown.jsx`.

### Front — `web/src/api.js`

Três métodos (`mcpStatus`, `mcpLeitura`, `mcpSetupGrafico`), timeout 30000
(dado de mercado, mesma classe de `optionsChain`; nenhum chama LLM),
`encodeURIComponent` em todo segmento vindo do usuário.

`req()` passou a anexar `status`, `code` e `detail` ao `Error`. **A
`message` não mudou um byte** — continua saindo de `enrichErrorMessage`. Sem
o `code`, a tela teria de raspar a string para distinguir
`mcp_nao_configurado` de `mcp_cota`, que é o jeito que quebra na primeira
mudança de copy. Regra de extração do `detail` fatorada em
`detalheDoErro(data)`, usada nos dois pontos.

### Front — `web/src/persistence.js`

Os três métodos nos **DOIS** stores, no mesmo commit, delegação pura (dado de
mercado não se duplica no aparelho — cachear carimbaria pregão velho como se
fosse do dia). `test_fase3_paridade_stores_generica.mjs` verde (server=70,
device=70).

### Front — `web/src/copy.js`

23 chaves novas, espelhadas nos dois modos, voz de professor em `estudo` e voz
de mesa em `operador`. `opcoesNaoAvaliado(motivo)` e `opcoesCota(reinicia)`
toleram nulo (o guardião chama toda função com nulo/zeros). Ramo estudo sem
"comprar"/"vender".

### Front — `web/src/opcoes/` (três arquivos novos)

**`useOpcoesMcp.js`** — `store` por argumento, nunca import de
`persistence.js`. Trio `dados/carregando/erro` por chamada, com o objeto de
erro inteiro. **Dois** contadores de requisição: `tickerRef` invalida tudo em
voo quando o ticker muda (sem isso, trocar de ativo rápido pinta o cabeçalho
com o ticker novo sobre números do antigo); `graficoRef` invalida só o
gráfico, para abrir um segundo setup não descartar a leitura em voo.
`carregando` nasce verdadeiro — o estado "carregando" vem ANTES do "vazio".

**`SetupChart.jsx`** — adapta os arrays paralelos de `get_setup_chart` para o
`ctx.PriceChart`. Os QUATRO campos de `ind` são sempre preenchidos (`pair()`
faz `arr[i]` sem guard; chave ausente = `TypeError`), com array de `null` cujo
comprimento DERIVA dos candles. `series` traz nomes arbitrários — mapeamento
determinístico (ordem alfabética) para os dois slots de linha, e a **legenda
diz o nome REAL**: ninguém pode ler "SMA 20" onde o dado é `rsi14`. Disparos
viram `priceLines` com `color` do `palette.accent` (**hex resolvido**,
`var()` não resolve em canvas — bug real do Modo Operador), limitados aos 8
mais recentes com o total dito em texto. Disparo sem fechamento numérico é
descartado, nunca vira 0. Fallback textual quando não há `PriceChart` ou não
há candles — tela em branco nunca.

**`OpcoesScreen.jsx`** — cabeçalho sempre visível (pregão, fonte, chip de
frescor em três variantes) + Leitura + Setups. Estados na ordem
carregando → erro/degradação → vazio com motivo → dados, escolhidos pelo
`erro.code`. `mcp_erro_de_tool` e qualquer código desconhecido caem no
`erro.message` cru com `whiteSpace: "pre-wrap"` (a mensagem já vem
multi-linha com "Como corrigir:"/"Dica:"). Campo ausente vira travessão,
nunca 0. Alvos de 44px, `aria-label` e `aria-pressed`. Zero
`CONTENT_MAX_WIDTH`, zero import de `App.jsx`. Universo = a watchlist do
usuário (nenhuma chamada extra para descobrir tickers).

### Front — `web/src/App.jsx`

- `defs` do `BottomNav`: `["agente","Operador IA"]` → `["opcoes", (cp &&
  cp.tabOpcoes) || "Opções"]`. As linhas de `mercado` e `radar` intactas.
- `{tab === "opcoes" && <OpcoesScreen ctx={ctx} />}`; `tab === "agente"`
  removido (zero ocorrências restantes).
- Portfólio com três casos: `historico`, `agente` (BackHeader com
  `cp.tituloOperadorIA` + `AgenteScreen`) e o default, que ganhou **no topo**
  a linha `cp.linkOperadorIA` (48px) chamando `goAgente()`. O botão de
  histórico continua onde estava.
- `goAgente()` no `ctx` como ponto único.
- `petTela` com três casos; `case "agente":` do `petSnapshot` intacto.
- `ctx` ganhou `PriceChart`, `palette` e `store`.
- Três textos que chamavam o Operador IA de "aba" corrigidos, e o tour ganhou
  uma linha dizendo onde ele fica.

---

## 3. Desvio de implementação: `paletteFor()` extraída de `usePalette()`

O plano mandava pôr em `ctx.palette` "o resultado de `usePalette()`; se o raiz
ainda não chamar `usePalette`, chame". **Não dá.** O `ThemeCtx.Provider` é
montado DENTRO do `return` de `App()`, então `usePalette()` chamado em `App()`
leria o contexto default (`dark`/`estudo`) — a aba Opções desenharia com a
paleta errada em tema claro e no Modo Operador, que é exatamente o bug que o
`usePalette` existe para não repetir.

Correção: a mescla tema+modo virou o helper puro `paletteFor(key, mode)`;
`usePalette()` passou a chamá-lo, e `App()` chama `paletteFor(themeKey,
appMode)` com as duas variáveis que ele já tem (as MESMAS que alimentam o
Provider). Zero mudança de comportamento no hook.
`test_chart_colors_theme_aware.mjs` verde.

---

## 4. Guardiões tocados

| Guardião | O que aconteceu |
|---|---|
| `web/tests/test_pet_ui.mjs:161` | **Atualizado com nota datada** (previsto no plano). `carteiraView` passou de dois para três valores; a regex nova trava a expressão inteira, tão exata quanto a antiga. `ABAS_PET` intacta. |
| `web/tests/test_benchmark_curva.mjs` | **Atualizado com nota datada** (NÃO previsto). Lia o índice FIXO `split("\n")[14]` para achar o import de `finance.js` e quebrou com os dois imports novos acima. As três condições da asserção continuam idênticas; só a busca virou por conteúdo em vez de posição. |
| `web/tests/test_c07_modo_operador_nomeia_operador_ia.mjs` | **Atualizado com nota datada** (NÃO previsto). Pinava verbatim "Inclui a aba Operador IA — …", que deixou de ser verdade. O contrato do C-07 (nomear o Operador IA e dizer que ele pode vender sozinho) está intacto; o texto anterior fica registrado em comentário. |

**Nenhum guardião foi apagado ou relaxado.** Os dois não previstos são o
custo real de o inventário do plano ter varrido `'"agente"'` em `web/tests/`,
mas não a frase de UI nem o índice de linha de import.

Guardiões novos: `web/tests/test_operador_ia_subtela.mjs` (27 asserções) e
`web/tests/test_opcoes_mcp_aba_ui.mjs` (68 asserções).

Um desvio dentro do guardião novo: o plano pedia que os **três** arquivos de
`web/src/opcoes/` declarassem o bloco `VARKEY/TOKENS/T`. `useOpcoesMcp.js` é
lógica de estado pura, não renderiza — um bloco de tokens ali seria código
morto que o próximo leitor tomaria por cor em uso. O guardião exige o bloco
dos DOIS `.jsx` e, do hook, o oposto: nenhum acoplamento a `persistence.js`.

---

## 5. Validação

### `bash scripts/executar.sh --testes` (RC=0)

```
== Suítes do backend ==
2239 passed, 4 skipped, 421 warnings in 49.87s

== Suítes web ==
  [OK] web/tests/test_acessibilidade_acordeao.mjs
  ... (126 arquivos, TODOS [OK], nenhum [X])
```

Backend: **2239 passed, 4 skipped** — baseline da F1 era 2225 passed, 4
skipped; +14 são exatamente os testes novos de `test_options_mcp_leitura.py`.
Web: **126/126 arquivos OK** — baseline 124, +2 são os guardiões novos.
Nenhum número caiu.

Confirmado que a suíte rodou contra o WORKTREE (o log traz
`.../worktrees/agent-a696d3f6a2f9d0694/server/tests/...`). A ressalva de
`ModuleNotFoundError: No module named 'mcp'` registrada na F1 **não** ocorreu
— o venv do clone principal já tem o pacote.

Sandbox: a primeira execução falhou com `Operation not permitted` no
`mktemp -d` do wrapper (os logs por teste iam para `/test_*.log`). Repetida
fora do sandbox; a falha era de ambiente, não de código.

### `cd web && npx vite build`

```
dist/assets/index-Bx3T1_u6.js                    826.96 kB │ gzip: 241.80 kB

(!) Some chunks are larger than 500 kB after minification. Consider:
- Using dynamic import() to code-split the application
- Use build.rollupOptions.output.manualChunks to improve chunking
- Adjust chunk size limit for this warning via build.chunkSizeWarningLimit.
✓ built in 1.17s

PWA v0.21.2
mode      generateSW
precache  23 entries (877.88 KiB)
files generated
  dist/sw.js
  dist/workbox-9c191d2f.js
```

O aviso de chunk > 500 kB é pré-existente (o bundle já vinha de 812 kB antes
desta fase).

### Higiene do diff

```
 server/app/options_mcp_api.py             | 300 +++++++-
 server/tests/test_guardrail_imperativo.py |  14 +-
 server/tests/test_options_mcp_leitura.py  | 384 ++++++++++
 web/src/App.jsx                           |  79 +++---
 web/src/api.js                            |  31 ++-
 web/src/chartutil.js                      |  28 +++
 web/src/copy.js                           |  62 +++++
 web/src/opcoes/OpcoesScreen.jsx           | 332 ++++++++++
 web/src/opcoes/SetupChart.jsx             | 162 +++++++
 web/src/opcoes/useOpcoesMcp.js            |  91 ++++
 web/src/persistence.js                    |  22 ++
 web/tests/test_opcoes_mcp_aba_ui.mjs      | 180 ++++++
 web/tests/test_operador_ia_subtela.mjs    | 107 ++++
 web/tests/test_pet_ui.mjs                 |  11 +-
 web/tests/test_benchmark_curva.mjs        |  15 +-
 web/tests/test_c07_...operador_ia.mjs     |  12 +-
```

Zero `web-admin/`, zero `web_dist`/`admin_dist`/`ios_dist`, zero
`SERVER_BUILD_ID`, zero `web/src/version.js`, zero config do Railway, zero
`docs/PLANO-aba-opcoes.md`. Zero deleções de arquivo. Varredura de segredo
(`MCP_CLIENT_SECRET=`, tokens `eyJ`) sem ocorrência. Nenhum push, nenhum
bump, nenhum deploy.

---

## 6. Threat model — o que foi de fato mitigado

| Threat | Como ficou |
|---|---|
| T-biz-01 (EoP) | `Depends(require_user)` nas duas rotas; guardião (iv) da F1 verde; teste 1 prova 401 com zero chamadas |
| T-biz-02 (DoS) | `_cap_check` na própria função antes de qualquer rede; `_cap_consume` só por chamada fora do cache; teste prova 402 sem tocar o serviço |
| T-biz-03 (InfoDisc) | nenhum literal de segredo; `_erro_http` reusado; diff varrido |
| T-biz-04 (Tampering) | `encodeURIComponent` no `api.js`; valor vai como ARGUMENTO de tool JSON-RPC; nome com barra 404, documentado |
| T-biz-05 (Spoofing) | React escapa; zero `dangerouslySetInnerHTML` nos três arquivos novos; `reason` e `message` em nó de texto com `pre-wrap` |
| T-biz-06 (Repudiation) | `obslog.log` no canal `mcp` nas duas rotas, com `uid`, `rota`, `ticker`/`setup`, `cache`, `passo` e `erro` |
| T-biz-07 | risco aceito (D-0.2 / ADR-027 §Decisão 6) — nada feito, por desenho |
| T-biz-SC | **nenhum pacote instalado** nesta fase |

---

## 7. Para a Fase 3

- Verificação ao vivo com `MCP_CLIENT_SECRET` — nada da renderização com dado
  real foi visto.
- Rotas `/cadeia`, `/operaveis`, `/proposta`, `/possibilidades` e o
  `PayoffChart.jsx`.
- Publicação do front: esta fase editou `web/src/` e **não** publicou. Uma
  fase que toque `web/src/` precisa de task de `bump.sh` + `publicar-web.sh`,
  senão o merge fica testado e nunca vai ao ar.
- Decisão (a) acima: inverter ou não o consumo de cap em `McpErroDeTool`.
- O `catalog` do `propose_option_setups` chega na resposta do `/leitura` mas a
  tela da F2 ainda **não** o renderiza (só os `expirations`) — é a seção
  "Analisar" da Fase 3.

---

## Self-Check: PASSED

Arquivos criados, todos presentes:
`server/app/options_mcp_api.py` (modificado), `server/tests/test_options_mcp_leitura.py`,
`web/src/chartutil.js`, `web/src/opcoes/OpcoesScreen.jsx`,
`web/src/opcoes/useOpcoesMcp.js`, `web/src/opcoes/SetupChart.jsx`,
`web/tests/test_opcoes_mcp_aba_ui.mjs`, `web/tests/test_operador_ia_subtela.mjs`.

Commits presentes no log: `3aff231`, `404f8e6`, `3be7a30`, `5de774c`.
