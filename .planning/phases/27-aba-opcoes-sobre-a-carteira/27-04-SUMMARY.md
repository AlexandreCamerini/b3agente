---
phase: 27-aba-opcoes-sobre-a-carteira
plan: 04
subsystem: ui
tags: [react, jsx, acessibilidade, unidades, regime, copy-por-modo, adr-027, guardioes]

requires:
  - phase: 27-03
    provides: "`GET /api/options/tecnico/{ticker}` (custo ZERO de MCP), `volatilidade.unidade`, `regua.itens`, `carimbo`, `custoMcp: 0` e `store.opcoesTecnico` nos dois stores"
  - phase: 27-02
    provides: "universo = carteira, bloco 'Seus vigias', lastro no cartão, allowlist `EFEITO_PERMITIDO` no guardião de efeitos"
provides:
  - "bloco `LeituraInterna` na tela do ativo — tendência, força, base, HV 21/63, suporte e resistência, de GRAÇA e sem mexer no contador de cota"
  - "`unidades.js` — `formatarVolatilidade(valor, unidade)`: a unidade DECLARADA no contrato escolhe o formatador; unidade desconhecida vira travessão sem dígito"
  - "`ReguaRegime.jsx` — até 7 segmentos, um por pregão fechado, cor do estado MEDIDO, hoje destacado, informação inteira em texto"
  - "selo de gratuidade DERIVADO de `custoMcp === 0`, nunca escrito fixo"
  - "`PERIODO_DA_LEITURA` fixo no hook — dois períodos na mesma tela dariam duas leituras do mesmo dia"
  - "`test_opcoes_leitura_interna_ui.mjs` — 74 asserções, lista de regimes DERIVADA de `regime.py` e o formatador EXERCITADO, não grepado"
  - "extração do guardião de efeitos ampliada para TODO `store.<método>` (era só `store.mcp*`)"
affects: [27-05, aba-opcoes, front-opcoes]

tech-stack:
  added: []
  patterns:
    - "unidade de grandeza como DESPACHANTE de formatador, não como anotação de contrato"
    - "guardião que IMPORTA e exercita a função (módulo `.js`, não `.jsx`) em vez de grepar o fonte"
    - "tabela de cores por estado derivada da tupla canônica do backend, nunca redigitada no front"
    - "allowlist de efeitos auditando todo `store.<método>`, não só os de prefixo conhecido"

key-files:
  created:
    - web/src/opcoes/unidades.js
    - web/src/opcoes/ReguaRegime.jsx
    - web/tests/test_opcoes_leitura_interna_ui.mjs
  modified:
    - web/src/opcoes/OpcoesScreen.jsx
    - web/src/opcoes/useOpcoesMcp.js
    - web/src/copy.js
    - web/tests/test_opcoes_analisar_ui.mjs

key-decisions:
  - "O bloco interno fica FORA da cascata de estados do serviço MCP: se o serviço cair, a leitura de graça continua na tela — e é justamente aí que ela mais vale"
  - "A invalidação do efeito usa `vivo` (cleanup), não `tickerRef`: ler `tickerRef.current` acoplaria a correção à ORDEM DE DECLARAÇÃO dos efeitos, e mover o bloco para cima deixaria a tela permanentemente em branco, em silêncio"
  - "A extração do guardião de efeitos passou a olhar TODO `store.<método>`: com a regex antiga (`store\\.mcp*`), a entrada `opcoesTecnico` na allowlist nasceria INERTE — e toda rota barata nasce fora do prefixo `mcp` por decisão do 27-03"
  - "`formatarVolatilidade` checa o VALOR antes da unidade: sem número, o travessão seco é a resposta certa (o motivo do bloco explica logo abaixo); com número e sem unidade, o travessão carrega o porquê"
  - "`lateral` e `indefinido` recebem tokens neutros (`textMuted`/`borderFaint`): pintá-los de verde ou vermelho afirmaria direção onde não há"
  - "Régua com `itens` vazio não é desenhada: sete segmentos \"indefinido\" seriam lidos como \"a semana inteira sem direção\", que é afirmação diferente de \"não há dado\""
  - "Régua vazia é falada pelo BLOCO PAI (`opcoesReguaSemDados` + motivo do backend), não pelo componente — o componente devolve `null`"

patterns-established:
  - "Guardião com lado NEGATIVO e lado POSITIVO sobre a mesma regra: 'nenhum `fracPct` sobre campo interno' passaria por vacuidade se a tela simplesmente deixasse de exibir volatilidade; o lado positivo exige que TODA chamada do formatador leia `.unidade` do próprio dado"
  - "Injeção de defeito prevista pelo plano é MEDIDA antes de ser aceita — as duas previsões do 27-04 estavam erradas e a medição virou nota no SUMMARY"

requirements-completed: [SC-3, D1, D4, G3, G4]

duration: ~55 min
completed: 2026-09-13
---

# Phase 27 Plan 04: Leitura técnica interna e régua de regime Summary

**Escolher um ativo na aba Opções passou a responder na hora — tendência, força, base da média, HV 21/63, suporte e resistência e a evolução de sete pregões — de graça, com carimbo de pregão e fonte, e com a unidade da volatilidade virando despachante de formatador em vez de anotação decorativa no contrato.**

## Performance

- **Duração:** ~55 min (10:25 → 11:20 BRT)
- **Tasks:** 2 de 3 (a terceira é o `checkpoint:human-verify`, **ABERTO**)
- **Arquivos:** 7 (3 criados, 4 modificados)
- **Commits de produção:** 2
- **Suíte canônica:** `2780 passed, 5 skipped, 3 xfailed, 0 failed` + `142/142 .mjs`, **exit 0**, fora do sandbox
- **Baseline de entrada:** `2780 passed` + `141/141` — o delta é **+1 `.mjs`** (`test_opcoes_leitura_interna_ui`, 74 asserções) e **zero** em pytest, porque nenhuma linha de backend foi tocada. **Zero regressão.**
- **`npx vite build`:** verde a cada task

## Accomplishments

### A unidade deixou de ser anotação e virou despachante (C6)

É o item de maior consequência do plano e o único que protege um número que
entra em decisão. Na MESMA tela convivem `volatilidade.hv21Pct` (motor
interno, **percentual**, com `unidade: "pct"` no contrato) e `behavior.hv21`
(serviço MCP, **fração**, sem campo de unidade nenhum, convertido por
`fracPct`). O 27-03 já declarava a unidade, mas **ninguém a consumia — e campo
que ninguém consome não impede erro nenhum.**

`unidades.js` é módulo puro, `.js` de propósito (importável por `node`), com
três ramos e o terceiro sendo o ponto: `"pct"` formata como está, `"frac"`
multiplica por 100, e **qualquer outra coisa devolve travessão sem um dígito
sequer**. Adivinhar a unidade é exatamente o erro de 10× que se quer
impossível; "não sei em que unidade isto está" é informação legítima
(princípio 4).

O guardião **exercita a função**, não o fonte: `(31,"pct")` e `(0,31,"frac")`
dão o mesmo texto, `(31,"frac")` não dá, e unidade desconhecida/ausente nunca
vira número. E tranca os dois lados na tela: nenhum `fracPct` recebe campo do
bloco interno **e** toda chamada do formatador lê `.unidade` do próprio dado
(sem o lado positivo, bastaria parar de exibir volatilidade para a asserção
passar por vacuidade).

### A régua não introduz uma terceira régua (C7)

`ReguaRegime.jsx` não classifica nada — cada item já chega classificado do
backend, que alimenta `regime.classificar` um pregão por vez com a
profundidade de histórico correta de cada dia. O guardião varre TODO arquivo
de `web/src/opcoes/` procurando comparação de preço com média ou limiar de ADX
e reprova qualquer uma: o oráculo de VALOR da concordância é do backend
(`test_opcoes_tecnico.py`: o último item da régua é idêntico a
`classificar(snap)`); o que se tranca aqui é que a tela não invente um terceiro
veredito sobre o mesmo dia.

A tabela `CORES_DO_REGIME` é conferida contra a tupla `REGIMES` **lida de
`server/app/regime.py`** — e a tabela de rótulos do `copy.js` também, nos dois
modos. Um quinto regime no backend reprova três asserções de uma vez.

### Cor não é informação

Cada segmento é `role="listitem"` com `title` **e** `aria-label` compostos por
dia, regime, força, "hoje" e a ressalva de janela curta. Opacidade reduzida
marca `confiavel: false`, mas **nunca sozinha** — o motivo vai junto, em texto.
Sete colunas de largura igual em `grid`, sem rolagem horizontal, com o dia
abaixo de cada uma.

### O selo "grátis" some sozinho se a rota passar a cobrar

`const semCusto = !!dados && dados.custoMcp === 0;` — derivado da resposta,
nunca escrito fixo (T-27-19). Trocá-lo por um texto constante reprova o
guardião.

### O período é fixo, e o fonte diz por quê

`PERIODO_DA_LEITURA = "1y"`, constante nomeada no topo do hook, com as duas
razões escritas: a régua precisa de sete velas fechadas na cauda (período
curto faria o `motivo` aparecer em toda leitura, sem defeito nenhum por trás)
e o período escolhe a CAUDA, não o histórico (o warmup das médias longas é
fixo em 2 anos no backend). Não passar `period` seria pior: o default sumiria
do fonte que a tela lê.

### O bloco interno e a leitura paga são independentes nos DOIS sentidos

O bloco fica fora da cascata de estados do MCP. Se o serviço de opções estiver
fora do ar ou não configurado, a leitura interna continua aparecendo — e é
exatamente aí que ela mais vale. Se ela degradar, os vigias e a leitura do
serviço seguem na tela. Duas fontes, dois carimbos, nenhuma escondendo a
outra: é o que a Emenda 2 do ADR-027 aceitou por escrito.

## Task Commits

| # | Task | Commit |
|---|------|--------|
| 1 | Bloco de leitura interna, `unidades.js`, hook, allowlist | `0ec5ed7` (feat) |
| 2 | `ReguaRegime.jsx` + guardião de 74 asserções | `60f93d0` (feat) |

## Injeções de defeito — de fato exercitadas

Toda não-vacuidade exigida foi injetada, o guardião reprovou, e o defeito foi
revertido antes do commit. **Nenhuma foi presumida** — e duas previsões do
plano não se confirmaram (ver Desvios).

| # | Injeção | Guardião que reprovou | Resultado medido |
|---|---------|----------------------|------------------|
| A | quinto regime (`acumulacao`) em `regime.py::REGIMES` | `test_opcoes_leitura_interna_ui.mjs` | 3 falhas: `CORES_DO_REGIME` + `opcoesRegimeRotulo` nos dois modos |
| B | `formatarVolatilidade(vol.hv21Pct, vol.unidade)` → `fracPct(vol.hv21Pct)` | idem | 2 falhas: "nenhum `fracPct` recebe campo do bloco interno" e "o formatador em ao menos DUAS linhas" |
| C | unidade FIXA como literal: `formatarVolatilidade(vol.hv21Pct, "frac")` | idem | 1 falha: "TODA chamada lê a unidade do próprio dado". Valor na tela: **3100,0% no lugar de 31,0%** |
| D | selo derivado → `const semCusto = true;` | idem | 1 falha: "o selo sai de `custoMcp === 0` da resposta (T-27-19)" |
| E | `store.opcoesTecnico` → `store.mcpCadeia` dentro do efeito | `test_opcoes_analisar_ui.mjs` | 3 falhas: allowlist, `METODOS` em efeito e a sanidade da extração |
| F | `"opcoesTecnico"` REMOVIDO de `EFEITO_PERMITIDO` | idem | 1 falha — a entrada é load-bearing, não decorativa |

## Deviations from Plan

### Divergências entre a previsão do plano e o comportamento MEDIDO

**1. A injeção nº 3 da Task 1, como o plano a escreveu, NÃO reprovava nada — e o guardião ia nascer com um buraco maior.**
O plano dizia: *"trocar `store.opcoesTecnico` por `store.mcpLeitura` dentro do
efeito faz `test_opcoes_analisar_ui.mjs` FALHAR pela allowlist"*. **Medido:
`mcpLeitura` ESTÁ na allowlist** (entrou no 27-02, marcada TRANSITÓRIA), então
a troca passaria verde por ela. Pior: a extração do guardião era
`/store\.(mcp[A-Za-z0-9_]*)/` — **só enxerga métodos com prefixo `mcp`**. Como
o 27-03 decidiu, com razão, que neste código `mcp*` significa "custa cota",
toda rota barata nasce FORA do prefixo — e era justamente essa classe que
atravessava o portão sem ser auditada. Acrescentar `"opcoesTecnico"` à
allowlist, como o plano mandava, criaria uma entrada **inerte**: o guardião
nunca olharia para ela.
- **Correção:** a extração passou a casar `/store\.([A-Za-z0-9_]+)/`, com nota
  datada e a razão por escrito, mais uma asserção de sanidade nova ("a
  extração enxerga chamada de store SEM o prefixo `mcp`"). A regra passou a
  ser: toda chamada ao store dentro de efeito precisa estar na allowlist — o
  prefixo do nome não decide mais quem é auditado.
- **Verificação:** injeções E e F. Com a regex antiga, E passaria verde.
- **Commit:** `0ec5ed7`.

**2. A aritmética da injeção nº 1 da Task 1 está invertida no plano.**
O plano previa que fixar a unidade em `"frac"` faria *"o valor na tela cair de
31,0% para 0,3%"*. **Medido: sobe para 3100,0%** — declarar "fração" para um
número que já está em percentual MULTIPLICA por 100. A queda para 0,3% é o
defeito espelho (tratar fração como percentual), que é o que aconteceria se
alguém passasse `behavior.hv21` pelo ramo `"pct"`. O erro de 10× existe nos
dois sentidos; a injeção mede um deles.

### Auto-fixed

**3. [Rule 1 - Bug] A invalidação por `tickerRef` prescrita pelo plano acopla a correção à ordem de declaração dos efeitos**
- **Encontrado em:** Task 1, alínea (a).
- **Problema:** o plano pedia "`tickerRef` + contador próprio `tecnicoRef`".
  Quem INCREMENTA `tickerRef` é o efeito de `leitura`, declarado logo acima.
  Capturar `tickerRef.current` no efeito novo só funciona enquanto ele estiver
  DEPOIS daquele: mover o bloco para cima faria a comparação ser sempre falsa
  e **nenhuma resposta pintaria a tela** — em silêncio, sem teste vermelho, com
  o bloco simplesmente não aparecendo.
- **Correção:** `vivo` no cleanup, a MESMA disciplina dos dois efeitos de custo
  zero já existentes no arquivo (`mcpStatus`, `mcpVigias`). Garante o mesmo
  ("resposta de PETR4 nunca pinta a tela de VALE3", porque a troca de ticker
  roda o cleanup antes de reexecutar o efeito) sem depender de ordem nenhuma.
  O `tecnicoRef` ficou de fora por ser redundante com o cleanup — maquinaria
  que o próximo leitor não conseguiria justificar é pior que nenhuma.
- **Verificação:** comentário no fonte explicando a escolha; suíte verde.
- **Commit:** `0ec5ed7`.

**4. [Rule 3 - Blocking] `web/dist` restaurado ao build publicado, a cada build**
Mesmo achado do 27-01 (desvio nº 3), do 27-02 (nº 5) e do 27-03 (nº 4):
`npx vite build` regenera `web/dist` com hashes de chunk novos **sem** bump, e
`test_ios_assets.mjs` compara `dist/assets` com `web/ios/.../public/assets`
quando os dois carregam o mesmo carimbo. **Medido vermelho durante a Task 1**
(16 chunks "faltando"); cada build foi rodado (é o que o plano exige) e
`web/dist` foi restaurado de `server/web_dist` em seguida. `web/dist` é
gitignorada; nada commitado. Cópias dos builds guardadas no scratchpad da
sessão.

### Desvios de critério de aceite (aritmética do plano, não do código)

**5. `grep -c "store.opcoesTecnico" useOpcoesMcp.js` devolve 1 — mas só porque o comentário foi reescrito.**
O critério exige exatamente 1. O guard de método ausente é uma segunda linha
com o mesmo nome, então o plano só fecha com o padrão de **porta única** que o
27-02 estabeleceu em `atualizarVigias` (`const ler = store &&
store.opcoesTecnico; if (typeof ler !== "function") …`) — que é melhor código,
e foi o adotado. Ainda assim o número quase mentiu: `grep -c` conta LINHAS, e o
comentário que explica a porta única citava o nome, fechando em 2. O
comentário foi reescrito ("o método `opcoesTecnico` do store"). Registrado
porque o próximo critério desse tipo vai tropeçar no mesmo lugar — é o terceiro
`grep -c` desta fase a contar comentário.

### Chaves de copy a mais do que o plano listou

**6. Seis chaves além das cinco nomeadas, todas nos DOIS blocos.**
`opcoesInternaCarregando`, `opcoesInternaErro`, `opcoesForcaRotulo` e as três
da régua (`opcoesReguaTitulo`/`Ajuda`/`SemDados`, essas previstas na Task 2).
A que exige justificativa é a primeira: reusar `cp.opcoesCarregando`
("Consultando o serviço de opções…") no bloco interno seria **mentira** — esta
leitura não consulta serviço nenhum, e é esse o ponto dela. `opcoesForcaRotulo`
existe porque a força chega como `"transicao"` (sem acento, vocabulário de
código) e o `aria-label` da régua a lê em voz alta.

## Issues Encountered

- **Nenhum bloqueio.** As duas tasks rodaram autônomas, árvore exclusiva
  (nenhum outro agente), commits por arquivo nomeado — `git add .`/`-A` nunca
  foi usado.

## Achados que merecem decisão (não implementados — fora do escopo)

**1. `degradado` da rota não é exibido.** `GET /api/options/tecnico/{ticker}`
devolve `degradado: bool` (estado do orçamento da brapi, mesmo par de
`/api/technicals`), e o bloco interno não o mostra. Não estava no plano e
exigiria chave de copy nova; o carimbo (`asOf`, `source`, `cacheStatus`) já
diz de quando e de onde é a leitura. Candidato natural ao **27-05**, que já
mexe em declaração de custo e estado de dado.

**2. `atr14Pct` chega no contrato e não é exibido.** O plano lista HV 21 e HV
63; a ATR% ficou de fora por disciplina de escopo. Ela é a medida de
volatilidade mais direta para dimensionar estrutura de opção — item barato para
o 27-05 ou para um quick.

**3. Os achados abertos do 27-02/27-03 continuam abertos**: `test_opcoes_fronteira.py`
não cobre `opcoes_tecnico.py` (a pureza está coberta dentro do arquivo de teste
do próprio módulo) e o `name` prefixado devolvido por `/setups/{name}/desativar`
— este último foi corrigido no backend em `e220196`, antes deste plano.

## User Setup Required

Nenhum. Nenhuma variável de ambiente nova, nenhum pacote novo (`T-27-SC` do
threat model: zero `npm install`/`pip install` nesta fase).

## Threat model — o que este plano fechou

| Threat ID | Como ficou |
|-----------|-----------|
| T-27-16 (DoS por efeito) | só a rota interna (`custoMcp: 0`) dispara por efeito; o guardião passou a auditar TODO `store.<método>` em efeito, não só `mcp*` |
| T-27-18 (unidade da volatilidade) | formatador ESCOLHIDO por `unidade`; desconhecida vira travessão sem dígito; guardião PERMANENTE exercita a função e tranca os dois lados na tela |
| T-27-21 (régua × linha de tendência) | período FIXO na chamada + nenhuma derivação de regime em `web/src/opcoes/` (varredura em todo o diretório) + o oráculo de valor no backend |
| T-27-19 (selo "grátis") | derivado de `custoMcp === 0`; injeção D mede |
| T-27-20 (régua com dados parciais) | `itens` vazio devolve `null` e o pai fala; `motivo` VERBATIM no rodapé da faixa |

## Checkpoint final — ABERTO (bloqueante)

O plano termina num `checkpoint:human-verify` com `gate="blocking"`, e ele
**não pode ser automatizado**. Os 74 guardiões travam estrutura, cor, unidade,
acessibilidade e a ausência de uma terceira régua — mas **nenhum deles vê a
tela**, e dois riscos só aparecem no aparelho: a régua em 375 px (sete
segmentos numa faixa estreita) e as duas volatilidades lado a lado no mesmo
ecrã. `ui_safety_gate` está ligado nesta fase.

Roteiro entregue ao desenvolvedor na resposta ao orquestrador (os sete passos
do plano, verbatim). **Resposta do Alex: aguardando** — será registrada aqui
verbatim quando chegar.

## Estado de publicação

**Nada foi publicado e nada foi empurrado a `origin`.** Sem `bump.sh`, sem
`publicar-web.sh`, sem `entregar.sh`. `server/web_dist`, `server/admin_dist`,
`web/src/version.js` e `SERVER_BUILD_ID` **intocados**. Os checkpoints do
27-01, do 27-02 e deste continuam abertos e seguram o push da fase inteira
(histórico: "fase com checkpoint humano segura o push da FASE INTEIRA").

**`STATE.md` e `ROADMAP.md` não foram tocados**, pela mesma decisão dos três
planos anteriores desta fase: o `CLAUDE.md` deste repositório proíbe os
mutadores de estado do `gsd-sdk`, o `STATE.md` ainda descreve a Fase 26 (as
quatro ondas da Fase 27 não estão lá) e escrever a narrativa da fase inteira a
partir de um plano só produziria um texto errado. A atualização é do
orquestrador, à mão, quando a fase fechar.

## Next Phase Readiness

- **O 27-05 está destravado** no que depende deste plano. O que ele herda,
  nomeado:
  - tirar `mcpLeitura` do efeito de troca de ticker, movê-la para `METODOS` e
    removê-la de `EFEITO_PERMITIDO` — o comentário no guardião diz isso com
    todas as letras, e a asserção nasce verde no dia em que as duas metades
    forem feitas juntas;
  - declarar na tela o custo de `mcpStatus` (até 1);
  - o selo `opcoesSemCusto` já existe e é derivado — o 27-05 **não** precisa
    criar um segundo vocabulário de gratuidade.
- **O que o 27-05 NÃO deve fazer:** passar qualquer campo de `tecnico.dados`
  por `fracPct`, nem chamar `formatarVolatilidade` com unidade literal. As duas
  coisas têm guardião permanente.

## Self-Check: PASSED

- `web/src/opcoes/unidades.js` — FOUND
- `web/src/opcoes/ReguaRegime.jsx` — FOUND (156 linhas, `export default`, zero hex)
- `web/tests/test_opcoes_leitura_interna_ui.mjs` — FOUND (74 asserções, exit 0)
- commits `0ec5ed7`, `60f93d0` — FOUND em `git log`
- `bash scripts/executar.sh --testes` — **exit 0**, `2780 passed, 5 skipped, 3 xfailed, 0 failed` + `142/142 .mjs`, fora do sandbox
- `cd web && npx vite build` — verde; `web/dist` restaurado ao build publicado
- `git status --short` — limpo

---
*Phase: 27-aba-opcoes-sobre-a-carteira*
*Completed: 2026-09-13 (checkpoint final em aberto)*
