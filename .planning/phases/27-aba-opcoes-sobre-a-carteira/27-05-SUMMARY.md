---
phase: 27-aba-opcoes-sobre-a-carteira
plan: 05
subsystem: ui
tags: [react, jsx, custo-declarado, adr-027, guardioes, acessibilidade, copy-por-modo]

requires:
  - phase: 27-04
    provides: "bloco de leitura técnica interna (custo zero) na tela do ativo, `cp.opcoesSemCusto` derivado, extração do guardião de efeitos ampliada para todo `store.<método>`"
  - phase: 27-02
    provides: "bloco 'Seus vigias', allowlist `EFEITO_PERMITIDO` com `mcpLeitura` marcada TRANSITÓRIA, `opcoesCustoChamadas` como forma canônica de declarar custo"
provides:
  - "`mcpLeitura` (custo 3) FORA de qualquer `useEffect`: trocar de ativo — inclusive clicando num vigia — não consome cota nenhuma"
  - "`abrirLeitura`: a leitura paga saindo de um clique que diz '3 consultas' antes de sair"
  - "`CUSTO_DA_ACAO`: nove chaves espelhando os `_cap_check(uid, N)` das nove rotas do serviço"
  - "rótulo de custo DENTRO de todos os sete controles que não tinham, na forma canônica única (`cp.opcoesCustoChamadas`)"
  - "`cp.opcoesCustoAnaliseIA`: o segundo eixo de custo do compilar (cota de IA), o único controle com dois"
  - "`cp.opcoesCustoFrescor`: o custo do `mcpStatus` (até 1, sem controle) declarado no cabeçalho"
  - "`test_opcoes_custo_declarado.mjs` — 84 asserções cruzando front × backend, com cobertura DERIVADA do hook e sanidade do extrator de rotas"
  - "custo também no `aria-label` dos dois botões que o têm (ele substitui o texto do botão no leitor de tela)"
affects: [aba-opcoes, front-opcoes]

tech-stack:
  added: []
  patterns:
    - "tabela de custo no front como ESPELHO declarado do backend, com guardião que lê os dois fontes e reprova a divergência"
    - "cobertura de guardião DERIVADA do fonte auditado (chamada nova sem classificação reprova) em vez de lista fixa"
    - "custo declarado na SEGUNDA LINHA do próprio botão, e no `aria-label` quando há um"
    - "efeito que só APAGA: invalidação sem disparo"

key-files:
  created:
    - web/tests/test_opcoes_custo_declarado.mjs
  modified:
    - web/src/opcoes/useOpcoesMcp.js
    - web/src/opcoes/OpcoesScreen.jsx
    - web/src/opcoes/CriarSetup.jsx
    - web/src/copy.js
    - web/tests/test_opcoes_analisar_ui.mjs
    - web/tests/test_opcoes_mcp_aba_ui.mjs
    - web/tests/test_opcoes_vigias_ui.mjs
    - web/tests/test_opcoes_criar_setup_ui.mjs

key-decisions:
  - "O convite da leitura paga NÃO mora dentro do bloco 'LEITURA DO ATIVO' que o plano indicava: aquele bloco só renderiza no ramo DADOS, que depende de a leitura JÁ ter voltado — um convite para pedir a leitura que só aparece depois dela seria inalcançável"
  - "`recarregarLeitura` perdeu o corpo próprio e virou nome sobre `abrirLeitura`: a razão escrita da duplicação (o efeito PRECISAR ser o lugar do disparo inicial) desapareceu quando a leitura saiu do efeito"
  - "`leitura` passou a nascer VAZIA: com `carregando: true` e sem disparo automático, a tela ficaria presa em 'Consultando o serviço' afirmando uma consulta que ninguém pediu"
  - "'Nenhum setup gravado para este ativo' passou a exigir leitura respondida (`l &&`): sem ela, a tela afirmaria o estado do armazém de um ativo que nunca consultou"
  - "O convite some quando o erro tem código acionável (não configurado / cota / teto / indisponível): um botão que só pode falhar é pior que botão nenhum; erro SEM código mantém o convite, porque ali repetir é legítimo"
  - "O custo entra no `aria-label` dos botões que têm um: `aria-label` SUBSTITUI o texto do botão no leitor de tela, e o critério 4 valeria só para quem enxerga a tela"
  - "`CUSTO_LISTAR_VIGIAS` foi absorvida por `CUSTO_DA_ACAO.listarVigias` sem mudar de valor: duas formas de declarar a mesma grandeza na mesma tela divergem na primeira manutenção feita só numa delas"
  - "A frase da cota de IA NOMEIA o consumo e não crava número: o teto vive no gate do `metering` e tem tela própria"

patterns-established:
  - "Guardião de espelho: o front declara, o backend cobra, e o teste lê os DOIS fontes — divergir reprova a suíte em vez de produzir rótulo errado em produção"
  - "Sanidade do extrator como cláusula de primeira classe: rota renomeada no backend não pode virar 'nada a conferir'"

requirements-completed: [SC-4, D4, G4]

duration: ~40 min
completed: 2026-09-13
---

# Phase 27 Plan 05: Custo declarado em cada controle Summary

**Nenhum botão da aba Opções gasta cota em silêncio: a leitura do serviço (3 chamadas) saiu do efeito de troca de ativo e virou um clique que diz o preço antes de sair, os sete controles que não declaravam custo passaram a declarar, o frescor do cabeçalho — a única chamada que ainda roda sozinha — está escrito na tela, e um guardião novo lê a tabela do front e os `_cap_check` do Python e reprova a suíte quando os dois discordam.**

## Performance

- **Duração:** ~40 min (11:22 → 12:02 BRT)
- **Tasks:** 2 de 3 (a terceira é o `checkpoint:human-verify` com `gate="blocking"`, **ABERTO**)
- **Arquivos:** 9 (1 criado, 8 modificados)
- **Commits de produção:** 2
- **Suíte canônica:** `2780 passed, 5 skipped, 3 xfailed, 0 failed` + `143/143 .mjs`, **exit 0**, fora do sandbox
- **Baseline de entrada:** `2780 passed` + `142/142` — o delta é **+1 `.mjs`** (`test_opcoes_custo_declarado`, 84 asserções) e **zero** em pytest, porque nenhuma linha de backend foi tocada. **Zero regressão.**
- **`npx vite build`:** verde a cada task

## Accomplishments

### A leitura paga saiu do efeito — e o que sobrou do efeito é só o apagar (C2)

`store.mcpLeitura` custa **3** chamadas do cap. Enquanto o ticker nascia vazio e
a única porta era o chip do ativo, o gasto ainda era consequência indireta de um
clique de quem queria a leitura. O bloco "Seus vigias" do 27-02 quebrou essa
leitura benigna: clicar num cartão de vigia **também** troca o ticker, e ali o
gesto se parece com navegação. Pagar 3 por navegar é exatamente o que o §3.3 do
ADR-027 proíbe — ele não fala de `useEffect`, fala de clique explícito com custo
declarado.

O efeito de troca de ticker continua existindo e continua fazendo o que sempre
importou: invalidar o que está em voo e apagar os trios, para que o dado do
ativo anterior não fique sob o cabeçalho do ativo novo. **Ele deixou de pedir.**
Quem pede é `abrirLeitura`, um `useCallback` chamado pelo botão que declara as
três consultas na segunda linha dele.

Três consequências que só aparecem lendo o código, e as três foram tratadas:

1. **`leitura` passou a nascer VAZIA.** Com `carregando: true` herdado da F2 e
   sem disparo automático, a tela ficaria presa em "Consultando o serviço de
   opções…" para sempre — e travar é o menor dos problemas: ela estaria
   afirmando uma consulta que ninguém pediu. Mesma disciplina do `tecnico`
   (27-04), pela mesma razão.
2. **`recarregarLeitura` perdeu o corpo próprio.** A duplicação tinha uma razão
   escrita no fonte ("o efeito PRECISA continuar sendo o lugar onde a leitura
   inicial dispara"), e essa razão desapareceu. Ficou o nome — porque o motivo é
   outro (a pessoa não pediu essa leitura, ela é consequência da escrita que já
   pagou) e quem lê `confirmarSetup` precisa disso no nome, não num comentário
   distante.
3. **"Nenhum setup gravado para este ativo" virou afirmação falsa** nos segundos
   entre escolher o ativo e clicar em ler. É uma afirmação sobre o armazém do
   serviço, e quem a mede é a própria leitura. Passou a exigir `l &&`.

### A tabela que a tela lê e o backend cobra

`CUSTO_DA_ACAO`, nove chaves, cada uma com o comentário da rota que a espelha.
Mesma disciplina de `N_MAX_VENCIMENTOS` e `ACOES_POR_CONTRATO`, que já viviam
neste arquivo pelo mesmo motivo: **a tela precisa dizer o preço antes de
perguntar ao servidor** — perguntar seria uma chamada para saber o preço de uma
chamada.

O mapa do plano foi **conferido linha a linha contra
`server/app/options_mcp_api.py`** antes de virar código (lição das três ondas
anteriores). Os nove valores bateram; nenhuma divergência a registrar neste
eixo.

Custo zero fica **fora**: `mcpVigias` e `opcoesTecnico` custam 0 por contrato da
rota, e declarar custo onde não há custo mente para o outro lado.
`mcpPossibilidades` fica fora porque o custo dela é calculado (`2 * N + 1`) e já
era declarado. `mcpStatus` fica fora porque não tem controle — e é o caso 6
abaixo.

### O custo no próprio controle, uma forma só de dizê-lo

Sete controles ganharam a segunda linha com `cp.opcoesCustoChamadas(n)`: cadeia,
só com liquidez, montar a estrutura, disparos do setup, ver a interpretação e o
ensaio, gravar, desativar. **Dentro** do botão, não ao lado — o preço tem de
viajar junto do alvo de toque.

O compilar é o único com custo em **dois eixos**: 2 chamadas do cap *e* uma
análise da cota de IA (`consumir_analise()` no backend), que tem teto próprio e
tela própria. A frase nova nomeia o consumo e **não crava número** — o teto vive
no gate do `metering`, e um número redigitado ali envelheceria em silêncio na
próxima mudança de plano.

### O custo também é falado em voz alta

`aria-label` **substitui** o texto do botão para quem usa leitor de tela. Os dois
botões da aba que têm `aria-label` — "Disparos do setup" e "Desativar este
setup" — passariam a exibir o custo e a **não dizê-lo** justamente para quem não
pode conferir na tela. O custo entrou no `aria-label` dos dois, e os dois
guardiões que fixavam a forma exata do rótulo foram atualizados com nota datada
(a exigência sobre o nome anunciado é a mesma; o que saiu foi a âncora de fim de
expressão, reposta por uma asserção positiva sobre o sufixo).

No botão de disparos, o rótulo **some** quando ele vira "Fechar gráfico":
fechar é local e não custa nada, e declarar custo numa ação de graça mente na
outra direção.

### A única exceção ao critério 4, escrita na tela

`mcpStatus` sai no mount e reserva 1 chamada — que só vira consumo quando a
consulta precisa mesmo ir ao serviço. Ela não vira botão, e a razão não é
conveniência: um gate de frescor que só aparece depois de um clique não protege
ninguém, porque a pessoa já teria lido a tela inteira acreditando no dado
(ADR-027, Decisão 8). A correção honesta não é esconder o custo, é declará-lo —
`cp.opcoesCustoFrescor`, sem condição de render, porque a reserva sai antes da
resposta e calar no estado de erro seria calar exatamente onde a pessoa vai
reclamar do contador.

O guardião não aceita a exceção de graça: `SEM_CONTROLE` é nomeado no mapa, a
declaração é **exigida** no fonte da tela e nos dois blocos de copy, e o número
da frase ("até 1") é cruzado com o `_cap_check(uid, 1)` da rota `status`.

### O guardião que fecha o critério 4

`test_opcoes_custo_declarado.mjs`, 84 asserções, com o mapa explícito no topo —
não "cruze pelo nome", porque os nomes não coincidem e nunca vão
(`mcpSetupsListar` → `listarVigias`, `mcpSetupGrafico` → `grafico`,
`mcpSetupCompilar` → `compilar`).

O que ele faz, e por que cada parte existe:

| Asserção | O que ela impede |
|---|---|
| Cobertura DERIVADA do hook (13 métodos) | chamada nova sem custo declarado — modo de falha silencioso: não quebra a tela, só aparece no contador da pessoa |
| Lado inverso: toda classificação corresponde a chamada real | entrada morta no mapa, que é permissão que ninguém revoga |
| Tabela × `_cap_check` das nove rotas | rótulo que envelhece em silêncio quando o backend muda o preço |
| **Sanidade: as NOVE rotas têm de ser achadas** | rota renomeada virar "nada a conferir" e a seção passar por vacuidade |
| Custo zero proibido na tabela | declarar preço onde não há preço |
| `SEM_CONTROLE` exige declaração | custo sem controle **e** sem declaração — o pior dos casos |
| `CALCULADO` com expressão, não literal | o `2 * N + 1` virar um número fixo que mente com N diferente |
| Todo controle com rótulo, pela função canônica | um segundo vocabulário de custo, que diverge do primeiro |
| Queda para travessão nos dois lados | número chutado quando a prop não chega — custo errado é crível, e por isso pior que custo nenhum |

## Task Commits

| # | Task | Commit |
|---|------|--------|
| 1 | `mcpLeitura` sai do efeito, convite com custo, frescor declarado, guardião de efeitos | `d7ff61c` (feat) |
| 2 | `CUSTO_DA_ACAO`, rótulo nos sete controles, cota de IA, guardião de cruzamento | `c494ead` (feat) |

## Injeções de defeito — de fato exercitadas

Todas foram injetadas, o guardião reprovou, e o defeito foi revertido antes do
commit. **Nenhuma foi presumida.**

| # | Injeção | Guardião | Resultado medido |
|---|---------|----------|------------------|
| A | `store.mcpLeitura(ticker)` de volta para dentro do `useEffect` de troca de ticker | `test_opcoes_analisar_ui.mjs` | **2 falhas**: "está na allowlist EFEITO_PERMITIDO" e "nenhum useEffect chama store.mcpLeitura" |
| B | fatiador de efeito quebrado de forma a produzir corpos VAZIOS (`t.split("{")[0]`) | idem | **3 falhas**, entre elas a âncora nova ("a fatia de efeito enxerga o que está dentro dele") — a seção não passa por vacuidade |
| C | `cadeia: 1` → `cadeia: 2` na tabela, sem tocar o backend | `test_opcoes_custo_declarado.mjs` | 1 falha: "a tela declara 2 e a rota cadeia cobra 1" |
| D | `store.mcpAlgoNovo()` acrescentado ao hook, sem classificação | idem | 1 falha: "store.mcpAlgoNovo está classificado" |
| E | `opcoesTecnico: 1` acrescentado à tabela (custo zero declarado) | idem | **3 falhas**: sanidade das nove entradas, "fica fora de CUSTO_DA_ACAO" e a exigência de rótulo |
| F | rota `cadeia` renomeada para `cadeia_v2` no backend | idem | **2 falhas**, a primeira pela SANIDADE do extrator ("achou 8 de 9") — não passou por vacuidade |

Nota sobre a injeção B: a primeira tentativa (trocar `"}, ["` por um marcador
inexistente) produz um fatiador **super-inclusivo**, não vacuoso — ele passa a
enxergar o arquivo inteiro e o guardião reprova com 16 falhas. Falha alta, mas
não é o modo que a âncora protege. A medição correta é a que consta acima: um
fatiador que devolve corpos vazios, onde a âncora nova é uma das três asserções
que reprovam.

## Deviations from Plan

### 1. [Rule 3 — Blocking] O convite não cabia onde o plano o colocou

- **Encontrado em:** Task 1, alínea (b).
- **O plano dizia:** *"Dentro do bloco 'LEITURA DO ATIVO', quando ainda não há
  `leitura.dados`, mostrar um estado de convite."*
- **Medido no fonte:** aquele bloco vive no ramo 4 (DADOS) da cascata, atrás de
  `nadaParaMostrar = semTicker || (!temLeitura && setups.length === 0)`. Sem
  `leitura.dados`, `temLeitura` é falso e o ramo inteiro não renderiza — um
  convite para PEDIR a leitura que só aparece DEPOIS de a leitura existir seria
  inalcançável, e a tela cairia no ramo 3 com "Nenhum setup gravado para este
  ativo" e nenhuma porta.
- **Correção:** `blocoLeituraDoServico` é montado fora da cascata, irmão de
  `blocoVigias`, e renderizado logo abaixo do bloco técnico interno — a ordem da
  Emenda 2 do ADR-027 (o que não custa vem primeiro) fica preservada. Montá-lo
  antes do `return` também mantém intactas as âncoras de ordem que
  `test_opcoes_mcp_aba_ui.mjs` ancora em `{cabecalho}`.
- **Commit:** `d7ff61c`.

### 2. [Rule 1 — Bug] "Nenhum setup gravado para este ativo" virou afirmação sobre o que ninguém mediu

- **Encontrado em:** Task 1, ao seguir o caminho da tela sem a leitura automática.
- **Problema:** com o ticker escolhido e a leitura ainda não pedida, o ramo 3
  afirmava o estado do armazém do serviço para um ativo que a tela nunca
  consultou. É o princípio 4 do `CLAUDE.md` ao contrário.
- **Correção:** `!semTicker && l && setups.length === 0`. Sem leitura pedida,
  quem fala é o convite.
- **Commit:** `d7ff61c`.

### 3. [Rule 2 — Acessibilidade] O custo ficaria invisível para leitor de tela em dois controles

- **Encontrado em:** Task 2, ao rotular "Disparos do setup" e "Desativar este setup".
- **Problema:** os dois têm `aria-label`, e `aria-label` **substitui** o conteúdo
  do botão para tecnologia assistiva. O `<span>` com o custo seria lido por
  ninguém — o critério 4 do ROADMAP valeria só para quem enxerga a tela.
- **Correção:** custo concatenado ao `aria-label` dos dois. Dois guardiões
  fixavam a forma exata do rótulo (`test_opcoes_vigias_ui.mjs` e
  `test_opcoes_criar_setup_ui.mjs`) e foram atualizados com nota datada, sem
  afrouxar: a exigência sobre o nome anunciado é idêntica, a âncora de fim de
  expressão saiu e foi **reposta por uma asserção positiva** sobre o sufixo.
- **Commit:** `c494ead`.

### 4. `recarregarLeitura` colapsou em vez de ganhar um irmão — e o `grep -c` do critério devolve 1, não 2

- **O critério dizia:** `grep -c "store.mcpLeitura" useOpcoesMcp.js` devolve **2**
  (`abrirLeitura` + `recarregarLeitura`).
- **Por que não:** os dois corpos seriam **idênticos** — mesmo endpoint, mesmo
  ticker, mesmas duas conferências de ref. Duas cópias do mesmo pedido divergem
  na primeira manutenção feita só numa delas, que é a regra que este repositório
  aplica em todo lugar (e que o próprio comentário do `recarregarLeitura`
  invocava). A razão escrita da duplicação existente — *"o efeito PRECISA
  continuar sendo o lugar onde a leitura inicial dispara"* — **deixou de valer
  no momento em que o efeito parou de disparar**.
- **O que foi feito:** o corpo mora em `abrirLeitura`; `recarregarLeitura` é um
  `useCallback` de uma linha sobre ela, com o nome preservado porque o MOTIVO da
  chamada é outro e os call sites precisam disso.
- **A intenção do critério foi preservada e provada:** as duas funções existem,
  nenhuma delas dentro de `useEffect` (`mcpLeitura` está em `METODOS`), e o
  guardião ganhou uma asserção nova sobre a porta única
  (`const recarregarLeitura = useCallback(() => { abrirLeitura(); }`).
- **Terceiro `grep -c` desta fase a tropeçar** (27-04, desvio 5; e dois antes).

### 5. [Rule 3 — Blocking] Dois guardiões ancoravam em formas que a mudança correta quebrou

Nenhum foi apagado; os dois ganharam nota datada com a razão.

- **`test_opcoes_vigias_ui.mjs`**: exigia o literal
  `const CUSTO_LISTAR_VIGIAS = 2;`. A constante foi absorvida por
  `CUSTO_DA_ACAO.listarVigias` **sem mudar de valor** — duas formas de declarar a
  mesma grandeza na mesma tela divergiriam. A asserção passou a exigir o número
  literal **dentro da tabela** e a leitura da tabela no botão; o cruzamento com
  o backend, que ela nunca fez, passou a existir no guardião novo.
- **`test_opcoes_mcp_aba_ui.mjs`**: exigia
  `const meu = ++tickerRef.current` dentro do hook. O efeito deixou de capturar
  o número porque deixou de disparar — sobrou o incremento, que é a parte que de
  fato invalida o que está em voo. A asserção passou a exigir que o **incremento
  esteja dentro de um `useEffect`** (fora dele, trocar de ativo não invalidaria
  nada) E que a conferência na volta continue existindo. Mais forte que a
  anterior, não mais fraca.

### 6. A âncora de sanidade do guardião de efeitos trocou de método — como o 27-04 previu

`efeitos.some(c => c.includes("store.mcpLeitura"))` ficaria **permanentemente
falsa**, e o dano não seria o vermelho: seria alguém apagá-la por estar
"quebrada", e sem ela um fatiador quebrado faria a seção 8 inteira passar por
vacuidade. Trocada por `store.mcpStatus`, que continua dentro de um efeito e não
tem plano de sair (o gate de frescor precisa existir na abertura). A razão está
escrita no fonte do guardião.

### 7. [Rule 3 — Blocking] `web/dist` restaurado ao build publicado, a cada build

Mesmo achado do 27-01 (nº 3), 27-02 (nº 5), 27-03 (nº 4) e 27-04 (nº 4):
`npx vite build` regenera `web/dist` com hashes de chunk novos sem bump, e
`test_ios_assets.mjs` fica vermelho. Cada build foi rodado (é o que o plano
exige) e `web/dist` foi restaurado de `server/web_dist` em seguida. `web/dist` é
gitignorada; nada commitado. **É o quinto plano seguido com o mesmo desvio — o
candidato óbvio a um quick é o próprio `executar.sh`/guardião, não o executor.**

### 8. Chaves de copy: quatro, as quatro previstas

`opcoesLerNoServico`, `opcoesLeituraConvite`, `opcoesCustoFrescor` (Task 1) e
`opcoesCustoAnaliseIA` (Task 2), todas nos DOIS blocos, com voz por modo. Sem
chave extra — diferente do 27-04, que precisou de seis além das cinco previstas.

## Issues Encountered

- **Nenhum bloqueio.** As duas tasks rodaram autônomas, árvore exclusiva,
  commits por arquivo nomeado — `git add .`/`-A` nunca foi usado, `git clean`
  nunca foi executado.

## Achados que merecem decisão (não implementados — fora do escopo)

**1. A aba ficou com DUAS portas pagas para o mesmo ativo, e uma delas é
cascata.** Sem a leitura do serviço, as seções "O QUE DÁ PARA MONTAR",
"COMPARAR OS VENCIMENTOS", "SETUPS GRAVADOS" e "CRIAR UM SETUP" não aparecem —
elas vivem no ramo DADOS, que depende da leitura. É o desenho híbrido do D1 (o
grátis primeiro, o pago sob clique) levado às últimas consequências, e é o que o
plano pedia. Mas significa que **criar um setup passou a custar 3 chamadas a
mais** do que custava (a leitura que antes saía sozinha). Vale a pergunta ao
Alex no checkpoint: o convite deveria dizer isso ("é esta leitura que abre as
seções de montar estrutura e criar vigia")? Hoje ele diz o que a leitura traz,
não o que ela destranca.

**2. Os dois achados abertos do 27-04 continuam abertos:** o `degradado` da rota
técnica não é exibido, e `atr14Pct` chega no contrato sem ser mostrado. Nenhum
dos dois era deste plano.

**3. `web/dist` regenerado a cada build (desvio 7) é o quinto plano seguido.**
Candidato a quick próprio: ou `test_ios_assets.mjs` ignora a divergência quando
o carimbo é o mesmo, ou o `executar.sh` restaura sozinho.

## User Setup Required

Nenhum. Nenhuma variável de ambiente nova, nenhum pacote novo (`T-27-SC` do
threat model: zero `npm install`/`pip install` nesta fase).

## Threat model — o que este plano fechou

| Threat ID | Como ficou |
|-----------|-----------|
| T-27-17 (rótulo divergente do cobrado) | `test_opcoes_custo_declarado.mjs` cruza `CUSTO_DA_ACAO` com os `_cap_check(uid, N)` das nove rotas, com sanidade do extrator; injeções C e F medem |
| T-27-22 (`mcpLeitura` por troca de ticker) | a chamada saiu do `useEffect` e virou `abrirLeitura` sob clique; `mcpLeitura` entrou em `METODOS` e saiu de `EFEITO_PERMITIDO`; injeção A mede |
| T-27-23 (`mcpStatus`, custo sem controle) | **accept, declarado**: `cp.opcoesCustoFrescor` no cabeçalho, `SEM_CONTROLE` nomeado no guardião, e o "até 1" da frase cruzado com o `_cap_check(uid, 1)` da rota |
| T-27-24 (chamada nova sem custo declarado) | cobertura DERIVADA do fonte do hook: método novo sem classificação reprova; injeção D mede |

## Checkpoint final — ABERTO (bloqueante)

O plano termina num `checkpoint:human-verify` com `gate="blocking"`, e ele
**não pode ser automatizado**. O guardião prova que os NÚMEROS batem com o
`_cap_check` — mas ele não vê a tela, e não prova que o rótulo está no controle
CERTO nem que o contador se move como o rótulo diz. `ui_safety_gate` está ligado
nesta fase.

Roteiro entregue ao desenvolvedor na resposta ao orquestrador (os oito passos do
plano, verbatim). **Resposta do Alex: aguardando** — será registrada aqui
verbatim, inclusive os números de `usado` anotados, quando chegar.

## Estado de publicação

**Nada foi publicado e nada foi empurrado a `origin`.** Sem `bump.sh`, sem
`publicar-web.sh`, sem `entregar.sh`. `server/web_dist`, `server/admin_dist`,
`web/src/version.js` e `SERVER_BUILD_ID` **intocados**. Os checkpoints do
27-01, 27-02, 27-04 e deste continuam abertos e seguram o push da fase inteira
(histórico: "fase com checkpoint humano segura o push da FASE INTEIRA").

**`STATE.md` e `ROADMAP.md` não foram tocados**, pela mesma decisão dos quatro
planos anteriores e por instrução explícita do orquestrador: a consolidação da
fase é dele, depois dos checkpoints humanos. O `CLAUDE.md` deste repositório
também proíbe os mutadores de estado do `gsd-sdk`.

Este é o último plano da fase. Depois da aprovação dos checkpoints, a publicação
(`scripts/bump.sh` + `scripts/publicar-web.sh`) e o deploy do backend continuam
sendo etapa HUMANA separada — sem eles a fase fica testada e nunca vai ao ar
(lição registrada em `fase-sem-plano-de-publicacao-front`).

## Self-Check: PASSED

- `web/tests/test_opcoes_custo_declarado.mjs` — FOUND (84 asserções, exit 0)
- `web/src/opcoes/useOpcoesMcp.js` — `const abrirLeitura = useCallback` presente, `store.mcpLeitura` em NENHUM `useEffect`
- `web/src/opcoes/OpcoesScreen.jsx` — `CUSTO_DA_ACAO` declarada, 11 ocorrências, `custos={CUSTO_DA_ACAO}` em 2 call sites
- `COPY.estudo`/`COPY.operador` — as quatro chaves novas presentes nos dois blocos
- commits `d7ff61c`, `c494ead` — FOUND em `git log`
- `bash scripts/executar.sh --testes` — **exit 0**, `2780 passed, 5 skipped, 3 xfailed, 0 failed` + `143/143 .mjs`, fora do sandbox
- `cd web && npx vite build` — verde; `web/dist` restaurado ao build publicado (`diff` contra `server/web_dist`: idêntico)
- `git status --short` — limpo

---
*Phase: 27-aba-opcoes-sobre-a-carteira*
*Completed: 2026-09-13 (checkpoint final em aberto)*
