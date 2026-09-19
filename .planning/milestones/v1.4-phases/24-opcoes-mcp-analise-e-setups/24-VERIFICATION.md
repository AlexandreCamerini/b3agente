---
phase: 24-opcoes-mcp-analise-e-setups
verified: 2026-09-11T21:26:30Z
status: gaps_found
score: 5/7 critérios plenamente verificados (2 parciais)
veredito: cumpre com ressalvas
overrides_applied: 0
gaps:
  - truth: "SC-1 — a aba mostra por vencimento … breakevens e razão ganho/perda"
    status: partial
    reason: >-
      Tudo o que o critério enumera está na tela (estrutura, custo/ganho/perda
      em reais para o lote, ±1σ, alvo/stop, breakevens) MENOS a razão
      ganho/perda. Ela não existe em lugar nenhum do código nem de nenhum dos
      5 planos — foi perdida silenciosamente entre o aceite do PLANO e o
      planejamento da fase.
    artifacts:
      - path: "web/src/opcoes/PayoffChart.jsx"
        issue: "cabeçalho mostra custo, ganho máx., perda máx. e breakevens; nenhuma razão G/P"
      - path: "server/app/options_mcp_api.py"
        issue: "`_em_reais` e `CHAVES_DA_ESTRUTURA` não carregam razão G/P"
    missing:
      - "Razão ganho/perda (|max_gain / max_loss|), com tratamento explícito de `unlimited_gain`/`unlimited_loss` e de `max_loss = 0` — nunca 0 nem ∞ silencioso"
  - truth: "SC-7 — nenhuma rota nova escapa de require_user + _cap_check, e nada cai no handler 500"
    status: partial
    reason: >-
      A primeira metade está provada (guardião iv resolve a árvore de
      dependências e o AST de `_cap_check`; 11 usos reais cobrem as 10 rotas).
      A segunda metade tem duas brechas concretas e reproduzíveis em rotas
      NOVAS desta fase.
    artifacts:
      - path: "server/app/options_mcp_api.py:1856-1862"
        issue: "`llm._call_llm` só tem `except llm.LLMUserError`; `httpx.ReadTimeout`/`ConnectError` do provedor sobem para o handler global (main.py:91) e viram 500"
      - path: "server/app/options_mcp_api.py:1985,2039"
        issue: "`audit.record` sem guarda DEPOIS de `create_setup(confirm=true)`: falha de escrita local vira 500 com o setup já gravado no armazém compartilhado"
    missing:
      - "Capturar exceção de rede/timeout do provedor de LLM em `/setups/compilar` e traduzi-la para 503 acionável (o padrão `_erro_http` já existe)"
      - "Envolver `audit.record` no mesmo padrão do `ai_activity.registrar_uso` (`except Exception` + print), ou justificar por escrito por que a auditoria deve derrubar uma escrita já efetivada"
  - truth: "Contabilidade do cap — a reserva do Boris nunca pode prometer menos do que o serviço cobra"
    status: partial
    reason: >-
      `_chamada_com_cap` NÃO debita o cap quando a tool responde erro
      (`mcp_client.call_tool` levanta antes do `cap.consome` e antes do
      `_cache_put`), mas o serviço COBRA toda `tools/call` no middleware,
      antes de executar a tool. A decisão é herdada da F2 ("a avalizar"), e é a
      Fase 24 que a torna explorável — `/possibilidades` faz fan-out de até 6
      vencimentos e engole `McpErroDeTool` por item com `continue`.
    artifacts:
      - path: "server/app/options_mcp_api.py:707-727"
        issue: "`cap.consome(1)` depois do `await`: exceção pula o consumo"
      - path: "server/app/mcp_client.py:631-640"
        issue: "recusa de tool levanta ANTES de `_cache_put` — erro nunca entra no cache, então repete a viagem toda vez"
      - path: "server/app/options_mcp_api.py:1435-1450"
        issue: "`except McpErroDeTool: … continue` dentro do laço de até 6 vencimentos"
    missing:
      - "Decisão do Alex: cobrar a viagem que a tool recusou (uma linha em `_chamada_com_cap`) OU cachear a recusa por um TTL curto OU um teto de falhas por requisição em `/possibilidades`"
deferred:
  - truth: "Razão G/P como fato determinístico do Boris no prompt de veredito"
    addressed_in: "Fase 4 do PLANO (fora do escopo da Fase 24)"
    evidence: "docs/PLANO-aba-opcoes.md §3.4: '…frescor, razão ganho/perda calculada pelo Boris'. Isto NÃO substitui a exibição pedida no aceite da Fase 3."
human_verification:
  - test: "Rodar a aba Opções com MCP_CLIENT_SECRET no ambiente e chamar /possibilidades com N=6"
    expected: "resposta abaixo de 20 s; `chamadasPrevistas` = 13; cada item com estrutura, emReais e curva; o contador de /observabilidade do serviço sobe exatamente 13"
    why_human: "exige credencial do serviço, que não está no ambiente de desenvolvimento (D-24.7)"
  - test: "Compilar um setup a partir de uma descrição em português com uma chave de LLM real"
    expected: "a LLM devolve JSON que `create_setup(confirm=false)` aceita; o ensaio aparece com disparos e retornos d+5/d+10; MAX_TOKENS_COMPILADOR=1500 é suficiente"
    why_human: "`llm._call_llm` está substituído em 100% dos testes; nenhuma chamada de modelo real foi feita"
  - test: "Abrir a aba no iPhone (375 px) depois do 24-05"
    expected: "tabela de cadeia rola na horizontal sem quebrar a tela; <select>, <input type=number> e <textarea> funcionam no WKWebView; as duas cores de P&L têm contraste nos dois temas"
    why_human: "nada foi verificado em aparelho; o 24-05 (publicação) está pendente de OK humano por desenho"
---

# Fase 24: Aba Opções sobre MCP — análise e criação de setups — Verificação

**Objetivo da fase:** Fases 3 e 5 do `docs/PLANO-aba-opcoes.md` — a aba deixa de só LER
o serviço e passa a (a) mostrar cadeia/catálogo/proposta/possibilidades com dinheiro
em reais para o lote e (b) criar setups técnicos a partir de descrição em português,
com ensaio antes de gravar e permissão de verdade.

**Verificado:** 2026-09-11T21:26:30Z
**Escopo:** `9ac079a..HEAD` (17 commits, `8ad53db`..`9bc76f8`); 24-05 pendente de OK humano por desenho.

## Veredito

**Cumpre com ressalvas.** Cinco dos sete critérios do ROADMAP são verdade no código,
com evidência de arquivo:linha e prova comportamental. Dois são parciais: o critério 1
perde um item enumerado (**razão ganho/perda não existe em lugar nenhum**) e o
critério 7 cumpre a metade estrutural (gate + cap, provados por guardião) mas tem duas
brechas concretas de "nada cai no handler 500". Somam-se a isso um achado de
**contabilidade de cap** que ataca exatamente a razão de ser do critério 7 — o teto de
2.000/dia é do servidor inteiro, e a Fase 24 abriu um caminho em que o serviço é
cobrado e a cota do usuário não.

Nada disso é stub, nada é fachada. O código é substantivo, os guardiões existentes
continuam guardando (nenhum assert afrouxado, nenhum teste apagado, nenhuma allowlist
crescida), a suíte relevante roda verde e o `vite build` passa. As ressalvas são
lacunas pontuais, não buraco de fundação.

## Goal Achievement

### Observable Truths — os 7 critérios do ROADMAP

| # | Critério | Status | Evidência |
|---|----------|--------|-----------|
| 1 | Por vencimento: estrutura, custo/ganho/perda em REAIS para o lote, ±1σ, alvo/stop, breakevens e **razão G/P** | PARCIAL | Tudo presente exceto razão G/P — ver F-01 |
| 2 | Breakeven nunca × lote; campo ausente nunca vira 0 (backend E tela) | VERIFICADO | `_em_reais` (options_mcp_api.py:825-864) não tem breakeven por desenho; `_vezes_lote` (816-822) devolve `None` para não-número; guardião de front com sanidade (test_opcoes_analisar_ui.mjs:85-105) |
| 3 | UI mostra "2×N+1 chamadas" ANTES de disparar, N ≤ 6 | VERIFICADO | OpcoesScreen.jsx:205-209 e 548-559; `N_MAX_VENCIMENTOS = 6` nos dois lados (options_mcp_api.py:163, OpcoesScreen.jsx:114) |
| 4 | Paridade `opcoes_payoff` × `evaluate_option_structure` campo a campo, com variante viva pronta | VERIFICADO (com ressalva) | test_opcoes_paridade_mcp.py; 4 passam, `test_paridade_viva` skip sem credencial — ver O-01 |
| 5 | PT → setup validado pelo serviço, dry-run (`disparos`, `disparos_por_100`, `retorno d+5/d+10`) visto antes de gravar, `problems` item a item | VERIFICADO | CriarSetup.jsx:276-357 (ensaio) e 203-215 (problems verbatim); options_mcp_api.py:1810-1934; 27 testes em test_opcoes_dsl.py |
| 6 | Sem `opcoes.criar_setup` a seção não existe **e** a rota responde 403; ENG-06 verde | VERIFICADO (com ressalva) | OpcoesScreen.jsx:145,712,731 (render condicionado); options_mcp_api.py:283-305 (`require_criar_setup`); test_opcoes_dsl.py:285 (403 nas três rotas, com prova por injeção de defeito) — ver O-02 |
| 7 | Nenhuma rota nova escapa de `require_user` + `_cap_check`; nada cai no handler 500 | PARCIAL | Gate e cap provados (guardião iv resolve a árvore de dependências); 500 tem duas brechas — ver F-02 e F-03 |

**Score:** 5/7 plenamente verificados.

### Achados

#### F-01 — Razão ganho/perda não existe (Severidade: MÉDIA)

O critério 1 do ROADMAP termina em "**breakevens e razão ganho/perda**", e o aceite
literal do `docs/PLANO-aba-opcoes.md` §4 Fase 3 diz "breakeven, razão G/P". Ela não
está no backend, não está no front, não está no `copy.js`, e — o que explica o resto —
**não aparece em nenhum dos cinco planos da fase**. A perda aconteceu no planejamento,
não na execução; os executores entregaram o que os planos pediram.

Evidência de ausência (varredura em `web/src/opcoes/`, `web/src/copy.js` e
`server/app/options_mcp_api.py` por `razão|razao|ganho/perda|G/P|ratio`): as únicas
ocorrências são a palavra "razão" em prosa de comentário.

O que está na tela hoje: `ganho máx.` e `perda máx.` lado a lado, por ação e em reais
(PayoffChart.jsx:158-180). A pessoa consegue fazer a conta de cabeça; o produto não a
faz por ela, e era isso que o aceite pedia.

**Cenário que expõe:** trava de alta com `max_gain = 0,80` e `max_loss = -1,20`. A tela
mostra os dois números e nunca diz que a estrutura paga 0,67 por 1 de risco — que é o
número que decide se vale montar, e o mesmo que a Fase 4 usaria contra o critério de
1,5:1 (PLANO §3.4).

**Ao corrigir:** `unlimited_gain`/`unlimited_loss` e `max_loss = 0` precisam de
tratamento explícito. Uma razão que vira `null` silencioso, `0` ou `Infinity` seria pior
do que a ausência atual — repetiria exatamente o defeito que o critério 2 proíbe.

#### F-02 — `/setups/compilar` cai no handler 500 em falha de rede do provedor de LLM (Severidade: MÉDIA)

`options_mcp_api.py:1856-1862` envolve `llm._call_llm` num `try` que só captura
`llm.LLMUserError`. `llm._call_anthropic` (llm.py:388-390) usa
`httpx.AsyncClient(timeout=60)` sem capturar nada: `httpx.ReadTimeout`,
`httpx.ConnectError` e `httpx.RemoteProtocolError` sobem intactos.

**Cenário:** o modelo demora mais de 60 s para compilar o setup (plausível com
`MAX_TOKENS_COMPILADOR = 1500` e um system que carrega o `inputSchema` inteiro
serializado). `httpx.ReadTimeout` propaga → `@app.exception_handler(Exception)`
(main.py:91) → **HTTP 500** com `{"detail": "ReadTimeout: "}`. O `ErroDoMcp` da tela
não tem `code` para esse corpo e cai no ramo genérico, sem "como corrigir".

A reserva de cap É devolvida (o `__exit__` de `_Reserva` roda na exceção) e nenhuma
chave vaza — o dano é a mensagem inútil, não segurança. O padrão é o mesmo do
`assistente.py:301`, ou seja, é dívida da casa, não invenção desta fase. Mas o critério
7 desta fase diz "nada cai no handler 500", e esta rota é nova.

#### F-03 — `audit.record` sem guarda depois de uma escrita externa já efetivada (Severidade: BAIXA)

`options_mcp_api.py:1985` e `:2039` chamam `audit.record` DEPOIS do
`create_setup(confirm=true)` / `deactivate_setup` já terem gravado no armazém
compartilhado do serviço. `audit.record` (audit.py:13-17) não tem guarda e vai direto ao
SQLite.

**Cenário:** `db.audit_insert` levanta (`database is locked` sob concorrência, disco
cheio no Railway). O usuário recebe 500, acredita que a gravação falhou, tenta de novo —
e o armazém, que é SEM DONO (ADR-027, Decisão 7), fica com dois setups.

A inconsistência está visível no mesmo arquivo: `ai_activity.registrar_uso`
(options_mcp_api.py:1920-1924) é envolvido com o comentário "contabilidade nunca derruba
a rota". A auditoria de uma escrita já efetivada merece o mesmo tratamento — ou uma
justificativa escrita de por que não.

#### F-04 — O cap não debita a viagem que a tool recusou, e o serviço cobra (Severidade: ALTA — decisão do Alex)

O serviço conta **toda** `tools/call` no middleware, antes de executar a tool
(`~/dev/MCP/servers/mydata/servico.py:467-477`; o contrato confirma: "Só `tools/call`
conta"). O Boris não: `_chamada_com_cap` (options_mcp_api.py:724-726) põe o
`cap.consome(1)` DEPOIS do `await`, e `mcp_client.call_tool` levanta `McpErroDeTool`
(mcp_client.py:631-639) **antes** do `cap.consome` e **antes** do `_cache_put`. Recusa de
tool, portanto: custa viagem ao teto compartilhado, não custa nada ao usuário, e não
entra em cache — logo repete integralmente na próxima tentativa.

A decisão é herdada da F2 e está declarada como "a avalizar" no próprio docstring. O que
a **Fase 24 acrescenta é a amplificação**: `/possibilidades` captura `McpErroDeTool`
por vencimento e faz `continue` (options_mcp_api.py:1435-1450), com até 6 vencimentos.

**Cenário concreto:** ticker cuja cadeia não traz `preco_objeto` — `evaluate_option_structure`
devolve `{"error": "leg X: the chain carries no underlying …"}` para todos os vencimentos
(server.py:585).

- Requisição 1: 13 chamadas reais ao serviço; cap do usuário debitado 7 (base + 6 `propose`; os 6 `evaluate` erram e não debitam).
- Requisição 2, dentro dos 15 min de TTL: base e os 6 `propose` vêm do cache (0 cap, 0 rede); os 6 `evaluate` NÃO estão em cache → **6 chamadas reais cobradas pelo serviço, 0 debitadas do cap do usuário e 0 do contador global do Boris**.

Repetir o botão ~330 vezes esgota os 2.000/dia de toda a base sem mover o contador de
60/dia de ninguém — e o guardião iv do `test_mcp_guardioes.py` nomeia exatamente esse
risco na própria mensagem de falha ("o teto de 2.000 chamadas/dia é do SERVIDOR, não do
usuário").

**Não é defeito de código a corrigir sem decisão** — é escolha de produto, e são três os
caminhos: (a) cobrar a viagem recusada (mover `cap.consome(1)` para antes do `await`, ou
um `try/finally`); (b) cachear a recusa com TTL curto; (c) teto de falhas por requisição
em `/possibilidades`. Recomendo decidir antes do 24-05 publicar.

### Observações (não são achados)

**O-01 — A fixture de paridade é derivada do próprio motor do Boris.** `test_opcoes_paridade_mcp.py`
declara isso no topo, com honestidade, e adiciona `test_divergencia_e_detectada` como
contra-guardião. O que a fixture trava é a TRADUÇÃO de vocabulário
(`net_cost`↔`custo_liquido` etc.) e a forma da resposta — não o acordo numérico com o
serviço real. Esse acordo só o `test_paridade_viva` prova, e ele está `skip`. O critério 4
diz "com a variante viva **pronta** para o smoke de staging", e ela está: `publicar-staging.sh:59`
roda `scripts/executar.sh --testes`, que a executa automaticamente se
`MCP_CLIENT_SECRET` estiver exportado. O PLANO §4 Fase 3 pedia mais ("o smoke de staging
**ganha** a paridade viva"); nenhum script foi tocado na fase. A diferença é operacional:
ninguém garante que o segredo esteja no ambiente na hora de publicar.

**O-02 — O guardião ENG-06 histórico não cobre os módulos novos.** `test_opcoes_gatilho.py:191`
varre `_MODULOS_OPCOES = ["opcoes_gatilho.py", "opcoes_payoff.py", "opcoes_lastreadas.py"]` —
não `options_mcp_api.py`, não `web/src/opcoes/`. Ele continua verde, e verde legítimo,
mas verde sobre uma superfície que não é onde a DSL poderia ter sido copiada nesta fase.
A cobertura nova é pontual e boa (`test_opcoes_dsl.py:772` prova que
`_system_compilador({}, "")` não contém `rsi`/`volume_relativo`/`cruza_acima`/`media_movel`),
e a varredura independente que fiz confirma: nenhum vocabulário de DSL em
`server/app/options_mcp_api.py` nem em `web/src/opcoes/` — as únicas ocorrências são
comentários que explicam a proibição e `behavior.rsi14`, que é campo LIDO do serviço.
Mas uma lista de indicadores hardcodada num helper de validação futuro passaria por
todos os guardiões de hoje.

### Required Artifacts

| Artefato | Esperado | Status | Detalhe |
|---|---|---|---|
| `server/app/options_mcp_api.py` | 7 rotas novas + `_em_reais`/`_lote`/`_vezes_lote` + compilador | VERIFICADO | +1405 linhas; 11 `with _cap_check` cobrindo as 10 rotas (linhas 926, 987, 1100, 1152, 1204, 1298, 1374, 1417, 1835, 1954, 2022) |
| `server/app/mcp_client.py` | `list_tools()` + `bruto` no `McpErroDeTool` | VERIFICADO | list_tools com TTL 3600 s, declarado protocolo (grátis) — confirmado no contrato do serviço |
| `server/app/rbac.py` | `opcoes.criar_setup → {opcoes_setup}` | VERIFICADO | linha 103-109; a nota anterior ("entra na Fase 5") foi cumprida, não apagada |
| `server/app/main.py` | `configure` com permissão + gate de análise + config | VERIFICADO | linhas 181-197; lambda para `_gate_analise` justificada (ordem de registro do router) |
| `web/src/opcoes/PayoffChart.jsx` | curva em preço do objeto, sem conta nova | VERIFICADO | 305 linhas; nenhum `* lote`; breakevens em bloco separado; nenhum `fill` nos `<path>` |
| `web/src/opcoes/CriarSetup.jsx` | seção gateada, ensaio, problems verbatim | VERIFICADO | 391 linhas; `<pre>` com nó de texto, zero `dangerouslySetInnerHTML` em uso |
| `web/src/opcoes/OpcoesScreen.jsx` | seções Analisar e Possibilidades | VERIFICADO | +526 linhas; custo antes do clique; ordem carregando→erro→vazio→dados |
| `web/src/persistence.js` | 7 métodos MCP novos nos DOIS stores | VERIFICADO | serverStore 282-294, deviceStore 1281-1314 — mesma assinatura, `ensure()` antes da delegação no nativo |
| `web/src/copy.js` | textos nos dois modos | VERIFICADO | 63 chaves `opcoes*` em `estudo` e 63 em `operador`, conjunto idêntico, tipos idênticos |
| `web/src/api.js` | 7 métodos + `qs()` | VERIFICADO | timeouts diferenciados justificados (60 s em `/possibilidades`, `TIMEOUT_LLM` em `/compilar`) |
| `server/tests/test_opcoes_dsl.py` | cobertura da F5 | VERIFICADO | 27 testes |
| `server/tests/test_options_mcp_api.py` | cobertura das 4 rotas da F3 | VERIFICADO | 33 testes |
| `server/tests/test_opcoes_paridade_mcp.py` | paridade + contra-guardião + viva | VERIFICADO | 4 passam, 1 skip |
| `web/tests/test_opcoes_analisar_ui.mjs` / `test_opcoes_criar_setup_ui.mjs` | guardiões de front | VERIFICADO | passam; asserções de sanidade presentes (a regex de `* lote` é provada contra o padrão que deveria pegar) |

### Key Link Verification

| De | Para | Via | Status | Detalhe |
|---|---|---|---|---|
| `OpcoesScreen` | `/possibilidades` | `useChamadaSobDemanda` → `store.mcpPossibilidades` | WIRED | sob demanda; nenhum dos 2 `useEffect` do hook menciona as chamadas da F3/F5 |
| `OpcoesScreen` | `l.expirations` | `/leitura` (F2) | WIRED | `leitura` devolve `expirations` verbatim (options_mcp_api.py:1077); sem isso N seria sempre 0 e a seção nasceria morta |
| `CriarSetup` | `/setups/compilar\|confirmar` | `store.mcpSetup*` | WIRED | confirmar envia `dados.setup` do dry-run, e o backend (`_setup_do_corpo`) não recompila |
| `require_criar_setup` | `require_user` | `Depends(require_user)` | WIRED | é o que faz a árvore da rota carregar sessão E permissão — guardião iv resolve `dependant` |
| `/possibilidades` | `_em_reais` | por item, com lote validado | WIRED | `breakevens` fica na `estrutura`, fora do bloco de reais |
| `_system_compilador` | `tools/list` + `resources/read` | `_material_do_compilador` | WIRED | schema e texto em runtime; 422 quando faltam, em vez de compilar de memória |
| `audit.record` | `rbac.ENTIDADES_POR_PERMISSAO` | `"opcoes_setup"` | WIRED | mesma string nas duas pontas (constante `ENTIDADE_AUDITORIA`) |

### Data-Flow Trace (Level 4)

| Artefato | Variável | Fonte | Dado real flui | Status |
|---|---|---|---|---|
| Seção Possibilidades | `possibilidades.dados.possibilidades` | `/possibilidades` → `evaluate_option_structure` | sim | FLOWING |
| `PayoffChart` | `e.payoff`, `e.scenarios` | `evaluate_option_structure` (contrato confirmado no fonte do serviço: `-1σ`/`spot`/`+1σ` + extras) | sim | FLOWING |
| `Cenarios` | `emReais.cenarios` | `_em_reais` (resultado × lote; `underlying` verbatim) | sim | FLOWING |
| `N` / `chamadasPrevistas` | `l.expirations` | `/leitura` | sim | FLOWING |
| `podeCriarSetup` | `ctx.authUser.permissions` | `App.jsx:9113` (`authUser` no ctx) | sim | FLOWING |
| Ensaio / backtest | `dados.backtest` | `create_setup(confirm=false)` | sim (forma do contrato; **nunca uma resposta real**) | FLOWING (não exercitado ao vivo) |

### Behavioral Spot-Checks

| Comportamento | Comando | Resultado | Status |
|---|---|---|---|
| Guardiões existentes continuam guardando | `pytest test_mcp_guardioes test_opcoes_fronteira test_opcoes_gatilho test_adr013_cobertura_rotas test_guardrail_imperativo` | 119 passed | PASS |
| Cobertura nova roda | `pytest test_options_mcp_api test_opcoes_dsl test_opcoes_paridade_mcp test_mcp_client test_options_mcp_leitura test_mcp_cap` | 129 passed, 1 skipped | PASS |
| `_em_reais` não fabrica zero nem toca breakeven | import direto, `max_gain=None`, lote 100 | `ganhoMaximo=None`; chaves sem breakeven; `underlying` não multiplicado | PASS |
| `_lote` recusa o que não é lote | import direto: `0, -1, 1.5, True, "100", None` | 422 em todos; 150 e 100 aceitos (D-24.3) | PASS |
| Paridade de chaves de copy | comparação programática dos conjuntos `opcoes*` | 63 = 63, conjunto idêntico, tipos idênticos | PASS |
| Copy sem promessa / Estudo sem vocabulário de ordem | varredura de 8 frases proibidas + 8 de ordem nas 126 chaves | único acerto é o próprio disclaimer, que NEGA ("nada aqui é ordem…") | PASS |
| Front compila | `npx vite build` | `✓ built in 1.28s`, PWA 23 entries | PASS |
| Testes de front relevantes | `node web/tests/test_opcoes_{analisar,criar_setup}_ui.mjs`, `test_opcoes_mcp_aba_ui`, `test_api_parity`, `test_copy_theme` | 5/5 OK | PASS |

### Contabilidade do cap — reserva × consumo real

| Rota | Reserva | Consumo máximo real | Veredito |
|---|---|---|---|
| `/cadeia/{t}` | 1 | 1 (`get_option_chain`) | OK |
| `/operaveis/{t}` | 1 | 1 (`find_tradable_options`) | OK |
| `/proposta` | 1 | 1 (`propose_option_setups`) | OK |
| `/possibilidades` | 1 + 2×N (N ≤ 6) | 1 + 2×N | OK (duas etapas, D-24.1; ambas devolvem saldo) |
| `/setups/compilar` | 2 | 2 (`check_data_freshness` + `create_setup`) | OK — o PLANO §3.3 declarava 1, e **o executor do 24-03 corrigiu para cima com razão**: o frescor bloqueante do aceite é uma `tools/call` a mais; reservar 1 faria o cap mentir. `tools/list` e `resources/read` são protocolo e grátis (confirmado no contrato do serviço, linha 394) |
| `/setups/confirmar` | 2 | 2 (`check_data_freshness` + `create_setup`) | OK |
| `/setups/{name}/desativar` | 1 | 1 (`deactivate_setup`) | OK — sem frescor bloqueante, assimetria deliberada e justificada (desativar é PARAR de afirmar) |

**Nenhuma rota reserva menos do que consome.** A brecha não está na reserva, está no
lado do consumo: viagem recusada pela tool não debita nada (F-04).

### Guardiões existentes — nenhum afrouxado

`git diff 9ac079a..HEAD -- server/tests/ web/tests/` = **+2361 linhas, 0 remoções, 0
arquivos deletados**. `test_mcp_guardioes.py`, `test_opcoes_fronteira.py`,
`test_opcoes_gatilho.py` e `test_adr013_cobertura_rotas.py` **não foram tocados**.
`test_guardrail_imperativo.py` só ganhou uma FONTE nova
(`options_mcp_api.SYSTEM_COMPILADOR_CABECALHO`), que é o oposto de afrouxar: submete à
varredura o texto que vira instrução de sistema numa LLM cuja resposta a pessoa grava
como vigia. Nenhuma allowlist cresceu — a do `test_adr013_cobertura_rotas` continua no
tamanho de antes porque todas as 7 rotas novas passam pelo gate de identidade.

`AVISOS` (options_mcp_api.py:131-139) absorveu os 4 textos fixos novos da fase
(`AVISO_FRESCOR_SEM_ANEXO`, `MOTIVO_SEM_VENCIMENTO`, `AVISO_DADO_ATRASADO`,
`AVISO_DADO_NAO_MEDIDO`) mais os dois 402 — a regra `[R-12]` foi cumprida na fase que os
criou.

### Coerência entre os 4 SUMMARY e o código

Conferi cada divergência declarada contra o código. **Todas são reais, todas conferem, e
nenhuma contradiz guardrail do `CLAUDE.md`.**

| SUMMARY | Divergência declarada | Confere? |
|---|---|---|
| 24-01 #6 | `grep -c "with _cap_check("` dá 9, não 7 (8 usos + docstring) | SIM, e hoje são 11 usos + 1 docstring = 12, porque o 24-03 somou três rotas |
| 24-01 #7 | `mcp.semente.dev` em teste é rótulo de fonte, não endereço | SIM — mesma distinção que o guardião (ii) faz |
| 24-02 #6 / 24-04 #7 | `grep -c` conta LINHAS: 2 ocorrências em CADA store | SIM — verificado fatiando o arquivo; os 7 métodos existem nos dois |
| 24-02 #8 / 24-04 #11 | `minHeight: "44px"` por constante (`BOTAO`/`CAMPO`), não repetido | SIM — o guardião checa as constantes, que é a trava mais forte |
| 24-03 key-decision | compilar/confirmar reservam 2, não 1 | SIM, e a correção é para o lado certo (ver tabela de cap) |
| 24-03 #9 | `audit.record` 3× = 2 chamadas + 1 comentário | SIM (linhas 1985, 2039 código; 58 comentário) |
| 24-04 #8 | `dangerouslySetInnerHTML` 1× = comentário, zero uso | SIM |
| 24-04 #9 | `opcoesCriarConfirmarDesativacao` contém `opcoesCriarConfirmar`; guardião usa `(?!Desativacao)` | SIM |

### Requirements Coverage

| Requisito | Fonte | Status | Evidência |
|---|---|---|---|
| PLANO Fase 3 — backend | `docs/PLANO-aba-opcoes.md` §4 | SATISFEITO com lacuna | 4 rotas + `_em_reais` + paridade; razão G/P ausente (F-01) |
| PLANO Fase 3 — front | idem | SATISFEITO com lacuna | seções Analisar/Possibilidades, `PayoffChart`; razão G/P ausente (F-01) |
| PLANO Fase 5 — backend | idem | SATISFEITO | 3 rotas, RBAC, auditoria, compilador em runtime |
| PLANO Fase 5 — front | idem | SATISFEITO | seção gateada, ensaio, `problems` item a item |
| D-24.1 a D-24.7 (CONTEXT) | `24-CONTEXT.md` | SATISFEITOS | D-24.1 duas etapas ✓; D-24.2 breakeven fora do bloco ✓; D-24.3 lote ≥ 1 inteiro ✓; D-24.4 `criterioAplicado` ✓; D-24.5 fiação de LLM reusável ✓; D-24.6 entidade no RBAC ✓; D-24.7 tudo offline ✓ |
| Publicação | ROADMAP, 24-05 | PENDENTE POR DESENHO | `autonomous: false`; nada foi empurrado, nenhum PR aberto |

### Anti-Patterns Found

| Arquivo | Linha | Padrão | Severidade | Impacto |
|---|---|---|---|---|
| — | — | `TBD`/`FIXME`/`XXX` | — | **Nenhum.** Os 5 acertos de `TODO` na varredura são a palavra portuguesa "todo/toda" em prosa de comentário |
| `server/app/options_mcp_api.py` | 314, 389, 399 | `int(x or 0)` | INFO | Pré-existentes de `_Reserva` (normalização de reserva/custo, onde 0 é o valor correto). `git diff` confirma: **nenhum `or 0` novo** no diff da fase |
| `web/src/opcoes/*` | — | `\|\| 0` / `?? 0` | INFO | Nenhum. O padrão do front é `ehNum(v) ? … : "—"` e `moeda()` devolvendo travessão |
| — | — | stub / placeholder / dado fixo | — | Nenhum. Toda seção nova lê das rotas reais; nenhum componente recebe mock |

### Probe Execution

Não se aplica: o projeto não tem `scripts/*/tests/probe-*.sh`, e nenhum plano da fase
declarou probe. A verificação executável foi feita via pytest + node + `vite build`
(tabela de spot-checks acima).

## O que continua SEM prova

Isto não é ressalva de formalidade — é o contorno exato do que a fase entregou às cegas.

1. **Nenhuma chamada ao serviço MCP real.** `MCP_CLIENT_SECRET` está fora do ambiente
   (D-24.7). Todo teste novo substitui `mcp_client.call_tool` por espião. Segue sem prova:
   a forma real de `check_data_freshness` (que decide se o 409 mostra `idadeHoras` ou
   `null`), a forma real de `inputSchema` e do resource `mydata://tools/create_setup`
   (que o `_system_compilador` serializa), e se `create_setup(confirm=true)` devolve
   `status: "ativo"` como o contrato diz.
2. **Nenhuma chamada de LLM real.** `llm._call_llm` está substituído em 100% dos testes.
   Que um modelo devolva, a partir do `system` montado em runtime, um JSON que
   `create_setup` aceite é hipótese não testada — e é ela que decide se
   `MAX_TOKENS_COMPILADOR = 1500` é suficiente.
3. **Nada em aparelho.** `<textarea>` e `<select>` no WKWebView, rolagem horizontal da
   tabela de cadeia em 375 px, alvo de toque e contraste das duas cores de P&L nos dois
   temas.
4. **O fluxo completo nunca rodou ponta a ponta.** compilar → ensaio → confirmar → o
   setup aparecer em `list_setups`: as peças estão provadas isoladamente, a sequência não.
5. **Nada foi publicado.** O 24-05 é pendente de OK humano por desenho. `server/web_dist`
   não mudou; o que está em produção continua sendo a F2.

### O PRIMEIRO teste ao vivo que deve rodar

**`pytest tests/test_opcoes_paridade_mcp.py::test_paridade_viva` com `MCP_CLIENT_SECRET`
no ambiente** — antes de qualquer outro, e antes do 24-05.

Por quê, e não outro: é o único teste da fase que confronta os DOIS motores de cálculo
financeiro sobre um dado real do serviço, campo a campo e ponto a ponto da curva. Toda a
aba, e o dinheiro em reais que a pessoa vê na tela, repousa sobre a premissa de que
`opcoes_payoff` e `evaluate_option_structure` concordam — e essa premissa hoje está
provada apenas contra uma fixture derivada do próprio `opcoes_payoff`, o que é
consistência consigo mesmo, não acordo com o serviço (O-01). Se os dois divergirem, todo
o resto da fase mostra número errado com carimbo de fonte, que é a pior classe de
defeito num simulador financeiro (`CLAUDE.md`, princípios 4 e 5).

Ele também é o mais barato: duas `tools/call`, sem LLM, sem permissão, sem escrita, sem
aparelho. Um comando, dois segundos, e derruba ou sustenta a fundação.

**Segundo da fila:** `/possibilidades` com N=6 ao vivo — mede o tempo abaixo de 20 s (o
aceite pede), confirma que o contador de `/observabilidade` do serviço sobe exatamente 13
e é o que exporia o F-04 em condições reais.

## Gaps Summary

A fase entregou trabalho denso e cuidadoso: 1.405 linhas de backend, 4 componentes de
front, 60 testes novos, guardiões com prova de não-vacuidade por injeção de defeito,
zero dependência nova, zero guardião afrouxado. O desenho do `_em_reais` — deixar o
breakeven estruturalmente FORA do bloco de reais, em vez de proibi-lo por teste — é a
melhor decisão técnica da fase, porque torna o defeito impossível em vez de vigiado.

O que falta fecha em três frentes:

1. **Uma omissão de escopo (F-01):** a razão ganho/perda nunca chegou a ser planejada.
   Correção pequena, de front, com cuidado explícito para `unlimited_*` e `max_loss = 0`.
2. **Duas brechas de degradação (F-02, F-03):** rotas novas que, em falha de rede do
   provedor de LLM ou de escrita local de auditoria, caem no 500 genérico — contra o que
   o próprio critério 7 promete. F-03 é a mais incômoda porque o 500 vem DEPOIS de uma
   escrita externa já efetivada.
3. **Uma decisão de produto adiada que a fase tornou urgente (F-04):** recusa de tool
   custa ao teto de 2.000/dia do servidor e não custa nada ao usuário. Era dívida
   declarada da F2; o fan-out de até 6 vencimentos do `/possibilidades` a transformou em
   caminho barato para queimar a cota de toda a base.

**Recomendação:** F-01, F-02 e F-03 cabem numa correção curta. F-04 precisa de uma escolha
do Alex, não de código. Nenhum dos quatro justifica desfazer a fase — mas F-04 deveria ser
decidido antes de o 24-05 levar isto ao ar, porque depois de publicado o custo do erro é
da base inteira, não de quem testa.

---

*Verificado: 2026-09-11T21:26:30Z*
*Verificador: Claude (gsd-verifier) — goal-backward, stance adversarial*
