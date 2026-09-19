---
phase: 27-aba-opcoes-sobre-a-carteira
plan: 03
subsystem: api
tags: [fastapi, snapshot-tecnico-unico, regime, react, capacitor, adr-027]

requires:
  - phase: 24-aba-opcoes-mcp
    provides: "ADR-027 e a fronteira que esta fase atravessa deliberadamente"
  - phase: 27-aba-opcoes-sobre-a-carteira
    provides: "27-01 — rota de custo zero fora do prefixo `/mcp/` (o precedente que este plano reusa)"
provides:
  - "`opcoes_tecnico.py` — leitura técnica determinística da aba (tendência, volatilidade, níveis) + régua de 7 pregões"
  - "`GET /api/options/tecnico/{ticker}` — custo ZERO de MCP, `custoMcp: 0` como contrato"
  - "`unidade: \"pct\"` sempre presente no bloco de volatilidade (o formatador do 27-04 sai dele)"
  - "`opcoesTecnico` nos DOIS stores do front"
  - "Emenda 2 do ADR-027 — a travessia da fronteira registrada, com o que NÃO afrouxa"
  - "`_pet_resumo_opcoes` descrevendo a aba sobre a carteira E atribuindo a leitura técnica ao motor interno"
affects: [27-04, aba-opcoes, front-opcoes, assistente]

tech-stack:
  added: []
  patterns:
    - "régua temporal que ALIMENTA o classificador canônico um índice por vez, em vez de reimplementá-lo"
    - "profundidade de histórico por pregão derivada de `historyStats.candlesAvailable`, nunca da posição na cauda do STU"
    - "unidade de grandeza como CAMPO DE CONTRATO (`unidade: \"pct\"`), presente inclusive quando o valor é `None`"
    - "pureza de módulo provada por `ast` sobre o próprio fonte, não por docstring"

key-files:
  created:
    - server/app/opcoes_tecnico.py
    - server/tests/test_opcoes_tecnico.py
    - server/tests/test_opcoes_tecnico_rota.py
    - web/tests/test_opcoes_tecnico_stores.mjs
  modified:
    - server/app/main.py
    - server/tests/test_pet_todas_telas.py
    - web/src/api.js
    - web/src/persistence.js
    - docs/adr/027-consumo-do-servico-mcp-autenticado.md

key-decisions:
  - "A profundidade de histórico de cada segmento é `candlesAvailable - (L-1-i)`, não `i+1` — com a cauda de 126 velas, `i+1` faria os 7 segmentos discordarem da linha de tendência logo acima (C7)"
  - "A régua chama `regime.classificar` por índice em vez de reimplementar direção × força — uma segunda régua de regime no app é a classe de defeito que o STU existe para matar"
  - "`unidade: \"pct\"` é contrato consumido e sai SEMPRE: o `hv21Pct` interno é percentual e o `hv21` do serviço é fração, e os dois convivem na mesma tela"
  - "A rota nasce em `main.py` com `current_scope` — mesmo gate de `/api/technicals`, porque é o MESMO dado público; duas réguas de acesso para a mesma informação seriam o defeito"
  - "`opcoesTecnico` e não `mcpTecnico`: neste código o prefixo `mcp*` significa 'custa cota', e esta leitura não custa"
  - "A divergência entre a HV interna e a HV do serviço é ACEITA e registrada como informação, não erro — cada bloco com fonte e carimbo próprios; unificação é fase futura com gatilho"
  - "O bloco `medias` expõe sma20/sma50/sma200 + ema9/ema21 — `sma9`/`sma21` pedidos pelo plano não existem no motor"

patterns-established:
  - "Guardião de texto do assistente com lado NEGATIVO e lado POSITIVO: sem o positivo, apagar a frase faria o teste passar por vacuidade"
  - "Granularidade de asserção declarada no próprio teste (item de `fala`, não sentença) com a razão por escrito"
  - "Injeção de defeito exercitada de fato e revertida antes do commit — e quando a previsão do plano não se confirma, a medição vira nota no guardião"

requirements-completed: [SC-3, SC-4, D1, G3, G4, ADR-027-EMENDA]

duration: 24 min
completed: 2026-09-13
---

# Phase 27 Plan 03: Leitura técnica interna da aba Opções Summary

**O motor determinístico que já alimenta Radar e Watchlist passa a responder tendência, volatilidade, suporte/resistência e a evolução de sete pregões para a aba Opções — por zero chamada do serviço de opções — com a travessia da fronteira do ADR-027 registrada como Emenda 2 e o assistente reescrito para parar de atribuir a leitura técnica a quem não a produz mais.**

## Performance

- **Duração:** ~24 min (07:21:59Z → 07:46Z)
- **Tasks:** 3 de 3
- **Arquivos:** 9 (4 criados, 5 modificados)
- **Suíte canônica:** `2773 passed, 5 skipped, 3 xfailed, 0 failed` + `140/140 .mjs`, **exit 0**, fora do sandbox
- **Baseline de entrada (pós-27-01):** `2729 passed` + `138/138`
- **`npx vite build`:** verde

### A aritmética da suíte, medida e não presumida

`2729 + 44 = 2773`. Os 44 se decompõem assim, e o quadragésimo quarto é o que
não é óbvio:

| Origem | Δ pytest |
|--------|----------|
| `test_opcoes_tecnico.py` (novo) | +29 |
| `test_opcoes_tecnico_rota.py` (novo) | +11 |
| `test_pet_todas_telas.py` (26 → 29) | +3 |
| `test_mcp_guardioes.py` guardião (iii), **parametrizado sobre TODOS os módulos de `server/app/`** — `opcoes_tecnico.py` acrescenta um caso | +1 |

Os `.mjs` vão de 138 a 140: `test_opcoes_tecnico_stores.mjs` (meu) e
`test_opcoes_universo_carteira.mjs` (do 27-02, que roda em paralelo na mesma
árvore e ainda não commitou). Nenhuma regressão.

## Accomplishments

- **A régua não contradiz a linha de tendência.** É a substância da correção
  C7 e não é detalhe de implementação: `snap["indicators"]` é a CAUDA do
  período (126 velas no padrão da tela) enquanto `candlesAvailable` conta a
  série inteira buscada (~500, o fetch é fixo em 2 anos). Passar `i+1` como
  profundidade faria os SETE segmentos caírem em `base="sma50"`/
  `confiavel=False` — abaixo do piso da SMA200 — enquanto a linha logo acima,
  que passa o snapshot inteiro para a MESMA `classificar`, diria
  `sma200`/`confiavel=True`. Dois vereditos sobre o mesmo dia, na mesma tela,
  vindos da mesma função. A fórmula `candlesAvailable - (L-1-i)` faz o último
  segmento valer exatamente `candlesAvailable`, e é por isso que ele sai
  idêntico a `classificar(snap)` — asserção obrigatória, e há uma versão dela
  pelo caminho HTTP também.
- **Nenhuma segunda régua de regime nasceu.** `regua()` monta um
  snapshot-sombra por índice e alimenta `regime.classificar`; não existe uma
  linha de direção × força no módulo novo (`grep -nE "adx *[<>]="` não casa
  nada). Se o limiar de ADX mudar, muda num lugar só.
- **Nenhuma volatilidade histórica foi recalculada.** Os valores saem do
  `context["volatility"]` que o STU já produz. O `options_api._technical_context`
  faz o contrário — refaz a HV sobre uma série que ele mesmo busca — e é
  exatamente a duplicação que este módulo existe para não repetir.
- **`unidade: "pct"` virou contrato consumível, não anotação.** Ele sai
  SEMPRE, inclusive quando os valores são `None` com motivo, porque é dele que
  o 27-04 escolhe o formatador. O `hv21Pct` daqui está em percentual (31.4) e
  o `hv21` do serviço chega em fração (0.31), convertido na tela por `fracPct`:
  os dois ficam lado a lado no mesmo ecrã, e um bloco sem unidade é como se
  erra 10× sem nenhum teste vermelho.
- **Custo zero é propriedade do grafo de imports, não promessa.** Um teste de
  `ast` sobre o próprio fonte reprova `httpx`/`mcp`/`mcp_client`/
  `candle_provider`/`asyncio` em `opcoes_tecnico.py`, e uma bomba em
  `mcp_client.call_tool` cobre a rota pelo caminho HTTP.
- **`_pet_resumo_opcoes` corrigido nos DOIS pontos, não em um.** Trocar
  `watchlist` por `positions` teria deixado viva a frase "a leitura da aba é
  de FIM DE PREGÃO e vem do serviço de opções" — meia verdade dita como
  verdade inteira depois do D1, e a mesma classe de defeito (A1/A5/A6) que a
  Fase 26 acabou de corrigir, sobrevivendo dentro da mesma função.

## Task Commits

1. **Task 1 (RED): régua e leitura, testes primeiro** — `8a25d5f` (test)
2. **Task 1 (GREEN): `opcoes_tecnico.py`** — `c821f6a` (feat)
3. **Task 2: rota + contrato nos dois stores** — `33e53bd` (feat)
4. **Task 3: Emenda 2 do ADR-027 + assistente + 3 guardiões** — `4427aab` (docs)

## Files Created/Modified

- `server/app/opcoes_tecnico.py` — módulo PURO: `PREGOES_DA_REGUA`, `regua(snap)`, `leitura(snap)`, motivos em constante de módulo
- `server/app/main.py` — import + `GET /api/options/tecnico/{ticker}` + `_pet_resumo_opcoes` reescrito
- `server/tests/test_opcoes_tecnico.py` — 29 testes sobre snapshots sintéticos
- `server/tests/test_opcoes_tecnico_rota.py` — 11 testes pelo caminho HTTP, offline
- `server/tests/test_pet_todas_telas.py` — +3 guardiões (nada apagado)
- `web/src/api.js` — `opcoesTecnico`
- `web/src/persistence.js` — `opcoesTecnico` nos dois stores
- `web/tests/test_opcoes_tecnico_stores.mjs` — paridade derivada da fonte + a rota FORA de `/mcp/`
- `docs/adr/027-consumo-do-servico-mcp-autenticado.md` — Emenda 2

## Decisions Made

Além das registradas no frontmatter:

- **A Emenda 2 convive com a Emenda 1 por escopo declarado**: a 1 trata de
  *quem é o dono* do que se grava no armazém compartilhado; a 2 trata de *de
  onde sai o número* que a aba lê. O texto diz isso explicitamente, para que
  nenhuma das duas seja lida como revisão da outra.
- **A unificação das duas fontes de HV tem gatilho, no mesmo formato da
  Decisão 3 do ADR**: paridade viva em staging por 10 pregões seguidos, ou a
  primeira divergência material (sinal trocado ou ordem de grandeza), o que
  vier antes. Sem gatilho, "unificar um dia" viraria dívida sem dono.
- **O resumo do assistente também NÃO busca candle.** A rota nova é custo zero
  de *MCP*, não de *requisição de mercado* — ela pode acionar o provedor e o
  orçamento da brapi é finito (ADR-008). Dizer de onde a leitura vem é
  diferente de buscá-la; a docstring registra a distinção para a próxima
  pessoa não "enriquecer" o resumo com um fetch.
- **`_da_cauda` alinha as séries PELO FIM.** Uma série que venha um elemento
  mais curta perde o pregão mais antigo, nunca desloca o mais recente —
  deslocar o recente trocaria o veredito de hoje pelo de ontem, em silêncio.

## Injeções de defeito — de fato exercitadas

Toda não-vacuidade exigida foi injetada, o guardião reprovou, e o defeito foi
revertido antes do commit. Nenhuma foi presumida.

| # | Injeção | Guardião que reprovou | Resultado medido |
|---|---------|----------------------|------------------|
| 1 | profundidade volta a `i + 1` | `test_profundidade_vem_de_candles_available_e_nao_do_indice_na_cauda` + `test_ultimo_item_da_regua_e_identico_ao_classificar_do_snapshot` + `test_profundidade_decresce_um_por_pregao_recuado` | 3 falhas; a régua inteira caiu em `sma50` enquanto a linha de tendência dizia `sma200` |
| 2 | régua repete `classificar(snap)` sete vezes | `test_serie_variavel_produz_segmentos_DIFERENTES` + `test_profundidade_decresce_um_por_pregao_recuado` | 2 falhas: "At index 0 diff: 'tendencia_alta' != 'lateral'" |
| 3 | rota chama `mcp_client.call_tool` | `test_a_rota_nao_chama_o_servico_de_opcoes` | `AssertionError: /api/options/tecnico chamou o serviço de opções` (mais 8 falhas colaterais — sem credencial, a chamada real derruba a rota) |
| 4 | universo volta de `positions` para `watchlist` | `test_resumo_opcoes_com_carteira_vazia_...` + `test_resumo_opcoes_nomeia_os_papeis_DA_CARTEIRA` | `AssertionError: ITUB4 é da watchlist e vazou para o resumo da aba` |
| 5 | frase antiga restaurada ("a leitura da aba (tendência, volatilidade, cadeia) é de FIM DE PREGÃO e vem do serviço de opções") | `test_resumo_opcoes_nao_atribui_a_leitura_tecnica_ao_servico_de_opcoes` | 1 falha: "o resumo atribui a leitura técnica do ativo ao serviço de opções" |

## Deviations from Plan

### Auto-fixed

**1. [Rule 1 - Bug] O plano pedia `summary.sma9`/`sma21`, que não existem no motor**
- **Encontrado em:** Task 1.
- **Problema:** o bloco `tendencia` deveria expor "`summary.sma9/sma21/sma50/sma200` para a tela poder mostrar a base". O `indicators.compute` calcula **SMA** de 20/50/200 e **EMA** de 9/21; `sma9`/`sma21` não existem em lugar nenhum do app. Expor os dois seria expor campos que nunca têm valor — travessão permanente sem motivo, o oposto do princípio 4.
- **Correção:** `medias` traz `sma20`/`sma50`/`sma200` do `summary` e `ema9`/`ema21` do `context["trend"]`, todos com `None` quando ausentes. O que a tela precisa de fato — qual média decidiu a direção — continua vindo do campo `base` do `classificar`.
- **Verificação:** `test_tendencia_e_o_classificar_inteiro_mais_as_medias`.
- **Commit:** `c821f6a`.

### Divergência entre a previsão do plano e o comportamento medido

**2. A injeção nº 2 NÃO é reprovada pelo par ADX-alto × ADX-baixo, ao contrário do que o plano afirmava.**
O plano dizia, em `<acceptance_criteria>`: *"trocar o corpo da régua por 'repete
`classificar(snap)` sete vezes' faz o par de testes ADX-alto × ADX-baixo
FALHAR (os sete itens ficariam iguais)"*. **Medido: não faz.** Esses dois
testes usam séries de ADX CONSTANTES — repetir a classificação de hoje sete
vezes devolve exatamente a mesma resposta, e o par passa verde com a régua
sabotada. Um guardião que o plano descrevia como prova era, sozinho, vácuo.
Por isso o arquivo inclui `test_serie_variavel_produz_segmentos_DIFERENTES`
(ADX cruzando o limiar no meio da janela, sete itens com dois regimes
distintos) — é ele, com `test_profundidade_decresce_um_por_pregao_recuado`,
que de fato reprova a sabotagem. O par ADX-alto × ADX-baixo fica: ele prova
outra coisa (que o limiar é lido do classificador canônico), só não prova
esta. Registrado em comentário no próprio teste.

### Desvio de critério de aceite (aritmética do plano, não do código)

**3. `grep -c "opcoesTecnico" web/src/persistence.js` devolve 4, não 2.**
Mesma causa do desvio nº 4 do 27-01: o critério presumia que o `deviceStore`
usaria o estilo propriedade-seta do `serverStore`. Ele usa método-atalho
`async`, então ocupa DUAS linhas (assinatura + delegação), e o comentário de
espelho cita o nome uma vez. `grep -c` conta LINHAS: 1 (serverStore) + 2
(deviceStore) + 1 (comentário) = 4. A substância — o método nos dois stores,
delegando para uma função que existe em `api.js` — está provada por
`test_opcoes_tecnico_stores.mjs` (igualdade de conjunto derivada da fonte) e
pelo guardião genérico de paridade.

### Higiene de ambiente

**4. [Rule 3 - Blocking] `web/dist` restaurado ao build publicado**
- **Encontrado em:** verificação final.
- **Problema:** o mesmo do desvio nº 3 do 27-01. `npx vite build` (exigido pelo
  plano, front editado) regenera `web/dist` com hashes de chunk novos **sem**
  bump de versão, e `test_ios_assets.mjs` compara `dist/assets` com
  `web/ios/App/App/public/assets` quando os dois carregam o mesmo carimbo de
  build. Mesmo carimbo + hashes diferentes = 16 chunks "faltando". **A árvore
  já estava nesse estado quando comecei** (o 27-02 havia construído antes),
  então não foi dano que eu introduzi — mas seria eu a entregar a suíte
  vermelha.
- **Correção:** o build rodou e passou verde (é o que o plano exige), e depois
  `web/dist` foi restaurado a partir de `server/web_dist` — a cópia versionada
  do MESMO build publicado. Cópia do build novo guardada no scratchpad da
  sessão.
- **Verificação:** `test_ios_assets.mjs` verde; suíte canônica exit 0.
- **Nada commitado** (`web/dist` é gitignorado).

---

**Total:** 1 auto-fix (bug de especificação), 1 previsão do plano corrigida por
medição, 1 critério de aceite corrigido por aritmética, 1 higiene de ambiente.
**Impacto:** nenhum scope creep. O item nº 2 é o mais relevante para quem ler
depois: um dos dois guardiões que o plano nomeava como prova de não-vacuidade
era vácuo, e o arquivo entrega um que não é.

## Issues Encountered

- **Nenhum bloqueio.** As três tasks rodaram autônomas, sem checkpoint.
- **Execução em paralelo com o 27-02 na MESMA árvore** (sem worktree, por
  instrução). Nenhum arquivo em comum foi tocado: staging sempre por arquivo
  nomeado, nunca `git add .`/`-A`. As três alterações do 27-02
  (`App.jsx`, `copy.js`, `OpcoesScreen.jsx`) e o `.mjs` novo dele seguem
  **não commitados** e intactos. A suíte final roda sobre a árvore unificada,
  que é o que o `<verification>` do plano pedia.
- **Coerência com o 27-02 sem editar nada dele:** o estado vazio do assistente
  foi escrito com a MESMA substância de `copy.opcoesCarteiraVazia` (lido, não
  editado) — a aba opera sobre o que a pessoa tem, lista de interesse não é
  lastro, e o caminho é a Carteira. Se o assistente dissesse outra coisa, ele
  contradiria a tela que a pessoa está olhando enquanto pergunta.

## Achados que merecem decisão (não bloqueiam)

**1. `test_opcoes_fronteira.py` NÃO cobre `opcoes_tecnico.py`.** O
`<interfaces>` do plano o lista como guardião que "passa a olhar este código",
mas o arquivo é parametrizado sobre `_MODULOS_NOVOS_FASE_15`
(`opcoes_payoff`, `opcoes_gatilho`, `opcoes_motor`) — uma tupla literal. Não
acrescentei `opcoes_tecnico` lá porque o arquivo não está em `files_modified`
(seria expansão de escopo por conta própria). A pureza está coberta por
`test_modulo_nao_importa_rede_nem_o_servico_de_opcoes`, dentro do arquivo de
teste do próprio módulo, com a mesma técnica de `ast`. Candidato natural a uma
linha de plano futuro: promover essa checagem para a tupla compartilhada.

**2. O achado nº 2 do 27-01 (`/setups/{name}/grafico` sem gate de dono)
continua aberto.** Nada neste plano o toca — a decisão do Alex (fechar em
27-04 ou aceitar por escrito) segue pendente.

## User Setup Required

Nenhum. Nenhuma variável de ambiente nova, nenhum pacote novo (`T-27-SC` do
threat model: zero `npm install`/`pip install` nesta fase).

## Estado de publicação

**Nada foi publicado e nada foi empurrado a `origin`.** Sem `bump.sh`, sem
`publicar-web.sh`, sem `entregar.sh`. `server/web_dist`, `server/admin_dist`,
`web/src/version.js` e `SERVER_BUILD_ID` **intocados**. O checkpoint final do
27-01 continua aberto e segura o push da fase inteira.

**`STATE.md` e `ROADMAP.md` não foram tocados** por dois motivos somados: o
27-02 roda em paralelo na mesma árvore (escrita concorrente no mesmo arquivo)
e o `CLAUDE.md` deste repositório proíbe os mutadores de estado do `gsd-sdk`.
A atualização é do orquestrador, à mão, depois que as duas ondas fecharem.

## Next Phase Readiness

- **27-04 está destravado.** O contrato que ele consome existe e está
  exercitado: `GET /api/options/tecnico/{ticker}` pelos dois stores
  (`store.opcoesTecnico(t, q)`), com `tendencia` (inclui `base` e `medias`),
  `volatilidade` (com `unidade`), `niveis` (verbatim do STU), `regua`
  (`{itens, motivo}`) e `carimbo`.
- **Três campos que o 27-04 precisa conhecer:** `volatilidade.unidade` (é por
  ele que o formatador é escolhido — o `behavior.hv21` do serviço continua em
  fração e continua precisando de `fracPct`), `regua.motivo` (não-nulo sempre
  que houver menos de 7 segmentos: é estado a desenhar, não ruído a esconder) e
  `custoMcp` (é dele que sai o rótulo "grátis" do controle — não redigitar o
  rótulo no front).
- **O que o 27-04 NÃO deve fazer:** renderizar a régua a partir do
  `behavior` do serviço, nem misturar os dois blocos num número só. A Emenda 2
  aceita por escrito que as duas fontes divergem e exige que cada uma carregue
  o próprio carimbo.

## Self-Check: PASSED

- `server/app/opcoes_tecnico.py` — FOUND
- `server/tests/test_opcoes_tecnico.py` — FOUND
- `server/tests/test_opcoes_tecnico_rota.py` — FOUND
- `web/tests/test_opcoes_tecnico_stores.mjs` — FOUND
- `docs/adr/027-consumo-do-servico-mcp-autenticado.md` (Emenda 2) — FOUND
- commits `8a25d5f`, `c821f6a`, `33e53bd`, `4427aab` — FOUND em `git log`
- `GET /api/options/tecnico/{ticker}` registrada com dependency `current_scope`
  (medido por `tests/rotas_fastapi.nomes_dependencias`); allowlist pública do
  ADR-013 segue em 25
- `bash scripts/executar.sh --testes` — **exit 0**, `2773 passed, 0 failed` +
  `140/140 .mjs`, fora do sandbox
- `cd web && npx vite build` — verde

---
*Phase: 27-aba-opcoes-sobre-a-carteira*
*Completed: 2026-09-13*
