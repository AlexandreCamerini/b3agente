# Prompt de execução — Otimização de UX e da camada de IA do Boris+
(preservado verbatim como recebido do Alex em 2026-09-12; números de linha
DESATUALIZADOS — ver 26-CONTEXT.md para as referências reconferidas)

Origem: análise das cinco abas e da camada de IA feita em 12/09/2026 (artefatos
"Anatomia do Boris+" e "Boris+ Reorganizado"), mais um inventário verificado
arquivo:linha da camada de IA. Este documento consolida TODOS os achados que
melhorariam a versão atual, ordenados por custo e risco. Nada foi implementado
ainda — este é o insumo para planejamento, não a execução.

**Antes de tocar em qualquer código**: os números de linha abaixo foram
medidos em 12/09/2026, na branch `v2/interacao-estrutural`. Reconfirme com
`grep`/`git blame` antes de editar — se a linha mudou, ajuste a referência no
plano em vez de editar às cegas.

**Guardrails do projeto que nenhum item abaixo pode violar** (não
re-litigar): manchete do card só do motor determinístico (guardrail CVM);
stop/alvo nunca vetado; paridade `defaults.py` × `catalog.js` e `deviceStore`
× `serverStore`; toda elegibilidade/ranking é regra determinística (ADR-017)
— nenhum item aqui aproxima a IA de calcular ou de ordenar o Radar; guardiões
de teste não se apagam, só se atualizam com nota.

**Como rodar isto**: o volume total pede `/gsd-execute-phase` com as fases
abaixo, ou uma sequência de `/gsd-quick` — uma chamada por item da Fase A,
que são independentes entre si. Não misture itens de fases diferentes num
único commit. Cada item fecha com `bash scripts/executar.sh --testes` verde;
item que toca `web/src/` fecha também com `npx vite build`.

---

## Fase A — Barato e de alto impacto (texto, ordem de validação, roteamento)

Sete itens independentes entre si. Cada um cabe num `/gsd-quick` isolado.

### A1 — Registrar a aba Opções no assistente de IA
**O problema, com evidência.** `PET_TELAS` em `server/app/conceitos.py:555`
lista sete telas e não inclui `"opcoes"`. Consequência em cascata,
confirmada por leitura de código: (a) `GET /api/pet/resumo?tela=opcoes`
(`server/app/main.py:3529`) cai no `if tela not in PET_TELAS: tela =
"mercado"` e devolve, com HTTP 200, o resumo da Watchlist — o campo `r.tela`
que denunciaria a troca vai na resposta e `PetSheet`
(`web/src/App.jsx:2935-2949`) não o lê; (b) `petSnapshot`
(`web/src/App.jsx:9202-9272`) não tem `case "opcoes"` e cai no
`default: return {}` — a IA não recebe nada da tela; (c) `POST
/api/assistente` com `tela: "pet:opcoes"` é recusado com `HTTPException(400,
"Tela desconhecida.")` (`server/app/main.py:3606`), inclusive para perguntas
que a base de conhecimento responderia de graça, porque essa checagem roda
antes de `kb.resolver` (linha 3614).
**O que fazer.** Acrescentar `"opcoes"` a `PET_TELAS`; escrever
`_pet_resumo_opcoes` no padrão dos outros ramos de `server/app/main.py:3533-3552`
(ticker lido, tese escolhida, série mais líquida — os campos que
`OpcoesScreen.jsx` já tem em estado); acrescentar `case "opcoes"` em
`petSnapshot` no front, com o que a aba já tem carregado (ticker, cadeia,
proposta); atualizar `server/tests/test_pet_todas_telas.py:44-45` (o
guardião trava a lista com igualdade exata — atualize-o com nota da
correção, não o contorne).
**Teste.** Novo teste de integração: `GET /api/pet/resumo?tela=opcoes` sem
achar `"mercado"` na resposta; `POST /api/assistente` com
`tela:"pet:opcoes"` e um ticker no snapshot não devolve 400.

### A2 — Inverter a ordem de validação de tela e busca no catálogo
**O problema.** Em `server/app/main.py`, a checagem de tela conhecida
(linha ~3606) roda antes da consulta a `kb.resolver` (linha ~3614). Toda
pergunta cai em 400 antes de a base de conhecimento (83 verbetes) ter chance
de responder de graça — mesmo numa tela cadastrada corretamente, mas ainda
mais numa tela nova como Opções antes do item A1 estar pronto.
**O que fazer.** Mover a chamada a `kb.resolver` para antes da checagem de
`tela in PET_TELAS`. Uma pergunta que a KB responde com confiança suficiente
sai sem custo de IA e sem depender do registro de telas. Isso é
independente de A1 e o precede em valor: mesmo que A1 atrase, esta inversão
já reduz o dano.
**Teste.** Pergunta que a KB cobre (ex. "o que é RSI?"), feita com
`tela:"pet:opcoes"` antes de A1 existir, responde pela KB em vez de 400.

### A3 — Vocabulário de modo na aba Opções
**O problema.** `web/src/App.jsx:985` e `web/src/copy.js` fazem `tabOpcoes:
"Opções"` idêntico nos dois modos (linhas 52 e 456 de `copy.js`), enquanto
Radar vira Mesa e Portfólio vira Posições no Operador. É a única aba fora do
sistema de vocabulário por modo que sustenta o resto do produto.
**O que fazer.** Manter o rótulo curto da barra (`tabOpcoes`) igual —
mudá-lo alteraria a barra em produção sem necessidade. Mudar `tituloOpcoes`
e `subtituloOpcoes` (criar essas chaves em `copy.js`, espelhando o padrão de
`tituloWatchlist`/`subtituloWatchlist`) para refletir registro de professor
no Estudo e registro de mesa no Operador, e ler essas chaves em
`OpcoesScreen.jsx` no lugar do texto fixo atual.
**Teste.** `web/tests/test_api_parity.mjs` ou teste novo de `.mjs`
confirmando que `COPY.estudo.tituloOpcoes !== COPY.operador.tituloOpcoes`.

### A4 — Tour começa na tela atual e cobre Opções
**O problema.** `tourPassos` (`web/src/App.jsx:2403-2410`) tem quatro
passos e o primeiro já aponta para o Radar, mesmo que o usuário esteja em
Acompanhar, que é onde o app abre (`useState("evolucao")`,
`web/src/App.jsx:7867`). `ajudaSecoes` (`web/src/App.jsx:2350`) tem sete
seções e nenhuma delas é Opções.
**O que fazer.** Acrescentar um passo zero nomeando a tela em que o usuário
está (Acompanhar) e um quinto passo apresentando Opções, mantendo a mesma
função `tourPassos(cp)` e o padrão de substituição de placeholders já usado.
Espelhar em `ajudaSecoes` com uma seção nova sobre Opções, no mesmo formato
título/parágrafos das demais.
**Teste.** `.mjs` verificando `tourPassos(cp).length === 5` e que o array de
`ajudaSecoes` inclui uma entrada cujo título menciona Opções.

### A5 — Fechar a divergência na frase de evidência insuficiente
**O problema.** Duas frases diferentes disputam ser a canônica: o código
renderiza "Não há dados suficientes para uma explicação agora."
(`web/src/App.jsx:1424`, comentário na linha 1415-1416 afirma "verbatim do
CLAUDE.md" — falso) e o `CLAUDE.md` do repo declara "Não há dados
suficientes para concluir." (linha 74-76). Nenhuma das duas é usada dentro
de prompt nenhum — a frase que de fato é injetada na IA é outra, fixa, para
ausência de setup (`server/app/skill_ref.py:221`, `:227`).
**O que fazer.** Decisão de uma linha, não de arquitetura: escolher qual das
duas frases é a canônica (recomendo manter a do `CLAUDE.md`, por ser a norma
declarada do produto) e corrigir o outro lado — o texto renderizado em
`App.jsx:1424` e o comentário que afirma verbatim incorretamente.
**Teste.** Grep de que só uma redação aparece no repo para esse propósito
específico (não confundir com a frase fixa de ausência de setup, que é
outro texto e está correta).

### A6 — Corrigir a rota que a mensagem de cota esgotada indica
**O problema.** As três mensagens de 402 do `metering.py` (linhas 252-253,
258-259, 270-271) mandam o usuário para "Perfil → Conta & preferências".
Essa tela foi renomeada e dividida; a chave hoje mora em "Perfil → IA &
Boris" (`web/src/App.jsx:5743`, tile em `:2557`).
**O que fazer.** Atualizar as três strings em `metering.py` para o caminho
atual. Item isolado, sem dependência de outro.
**Teste.** Grep confirmando que nenhuma mensagem de 402 cita o caminho
antigo.

### A7 — Atualizar a SKILL.md da didática, que descreve comportamento morto
**O problema.** `.claude/skills/didatica-boris/SKILL.md:62-64` afirma que o
`PetFab` aparece "só na Watchlist do Estudo" — falso desde 08/08/2026, ele
aparece em qualquer aba e nos dois modos (`web/src/App.jsx:9384-9389`, com o
motivo da reversão registrado ali). O mesmo trecho cita um componente
"Coruja" que não existe; o nome real é `Boris`
(`web/src/pet/Boris.jsx`).
**O que fazer.** Corrigir os dois pontos na SKILL.md. É documentação, não
código de produto — sem teste automatizado, apenas revisão de texto.

---

## Fase B — Estrutural, precisa de plano curto antes de codar

Quatro itens, três dão para planejar já; o quarto (B3) é decisão do Alex, não tarefa de execução.

### B1 — Perfil marcado como ativo na barra
**O problema.** Com o Perfil aberto (`web/src/App.jsx:9342` e a lógica de
`tab`/`perfil` em torno de `:7867`), nenhum item de `BottomNav`
(`web/src/App.jsx:982-999`) fica com `aria-pressed="true"`, porque a barra
só conhece as cinco abas, não o Perfil. O usuário perde a âncora de onde
estava.
**O que fazer, sem criar sexta aba.** Dar ao avatar da Topbar um estado
visual ativo quando o Perfil está aberto, e uma faixa curta ("Você saiu de
X → Voltar") no topo da tela de Perfil, reaproveitando o padrão que
`Histórico`/`Operador IA` já usam como sub-tela do Portfólio. Guardar qual
aba estava ativa antes de abrir o Perfil (uma variável de estado local
basta, não precisa persistência).
**Teste.** `.mjs` ou verificação manual documentada: abrir Perfil, conferir
`aria-pressed` de todos os itens da barra é `false` e o avatar carrega
classe/atributo ativo.

### B2 — Preservar estado ao trocar de aba
**O problema, é o de maior retorno da lista.** `{tab === "x" &&
<Tela/>}` em `web/src/App.jsx:9333-9342` desmonta cada tela ao trocar de
aba. Dois comentários no próprio código já reconhecem isso
(`web/src/App.jsx:3893`, `:6873`). A perda concreta: a varredura do Radar
(`RadarScreen`) e a leitura de opções (`OpcoesScreen`) consomem,
respectivamente, orçamento mensal de cotações e cota diária do serviço de
opções — refazer por causa de troca de aba gasta recurso limitado, não só
tempo do usuário.
**Decisão de arquitetura a tomar antes de codar** (não decida sozinho, leve
as duas opções ao Alex numa fase de planejamento curta):
  1. Manter todas as cinco telas montadas e alternar visibilidade via
     `hidden`/`display:none` em vez de desmontar — mais simples, mais
     memória, resolve tudo de uma vez.
  2. Elevar o estado que importa (resultado da varredura, ticker e leitura
     de opções carregada, painéis abertos) para fora dos componentes de
     tela, num objeto de estado do nível do `App` — mais trabalho, menos
     memória, mais controle fino sobre o que persiste e o que não.
**Escopo se a opção 1 for escolhida.** Trocar a renderização condicional
por montagem permanente com `hidden`, cuidando de: (a) efeitos que hoje
rodam só na montagem (`useEffect` com array vazio) não podem re-disparar ao
"reaparecer"; (b) o `scheduler_loop`/timers do front que dependem de
`tab === "x"` como guarda precisam de guarda equivalente por visibilidade,
não por montagem.
**Teste.** `.mjs` de integração: varrer o Radar, mudar para `carteira`,
voltar para `radar`, confirmar que a lista de candidatos não foi
limpa e que nenhuma nova chamada de rede foi disparada no meio do caminho.

### B3 — Decidir o verbo da aba Opções (decisão de produto, não tarefa de código)
**O problema.** `OpcoesScreen.jsx` lê, monta proposta e desenha gráfico.
Nenhum botão chama as rotas de compra, venda ou fechamento de opção que o
backend já expõe (`server/app/main.py` tem as rotas de
`/api/options/buy`, `/api/options/sell`,
`/api/options/lastreada/fechar`, já corrigidas quanto a `qty` inválido em
tarefas anteriores desta sessão). O usuário monta uma proposta e chega a um
beco, em qualquer modo.
**As duas saídas legítimas, para o Alex escolher, não para o executor
decidir:**
  1. Ligar a tela às rotas existentes, com a mesma guarda de quantidade e o
     mesmo registro de rejeição do resto do app, liberando execução
     simulada pelo menos no Modo Operador.
  2. Assumir que esta versão só lê, e dizer isso explicitamente na tela, com
     caminho para operar a partir do Portfólio.
**Não iniciar B3 sem essa decisão registrada** (nem que seja um "sim" curto
do Alex). Depois de decidido, abre-se um plano de fase separado — o escopo
de qualquer das duas opções é grande demais para `/gsd-quick`.

### B4 — Expor a cota diária de IA, não só a mensal
**O problema.** `GET /api/ai/quota` (`server/app/main.py:598-609`) já
devolve `quota`/`used`/`remaining` diários, mas `AtividadeIAScreen`
(`web/src/App.jsx:5905`) só lê `monthUsed`/`monthLimit`
(`:5927-5928`). Some a isso que o contador mensal de 30 análises cobre só
duas das cinco rotas de IA: `/api/technical/analyze` e a rota legada
`/api/analyze` passam pelo gate mensal (`server/app/main.py:1987`,
`:2192`); `/api/scan/deep`, `/api/carteira-stopalvo/{t}` e
`/api/assistente` usam só a cota diária, sem entrar na conta mensal
mostrada na tela.
**O que fazer.** Renderizar também o contador diário (já disponível na
resposta da rota) em `AtividadeIAScreen`, e acrescentar uma linha de texto
dizendo que o número mensal não inclui aprofundamento do Radar, stop/alvo
por IA nem o assistente. Não é bug de cálculo — é omissão de exibição de um
dado que o servidor já calcula.
**Teste.** `.mjs` verificando que a tela renderiza o par `used`/`quota`
diário quando a resposta de `/api/ai/quota` os inclui.

---

## Fase C — Maior escopo, cada item é uma fase própria de planejamento

Não tentar em `/gsd-quick`. Cada um precisa de `RESEARCH.md`/plano completo.

### C1 — Dar uma porta de busca aos 83 verbetes da KB
**O problema.** `server/app/kb.py` tem 83 entradas (medido por execução:
`len(kb.catalogo())`), das quais só 9 são alcançáveis pelo usuário via
`SetorAlvo`/`ConceitoSheet` (os `CONCEITOS` de `conceitos.py`). A rota `GET
/api/kb/buscar` existe no servidor (`server/app/main.py:3561`), está
declarada em `web/src/api.js:285` e nos dois stores
(`web/src/persistence.js:239`, `:1123`) — nenhum componente da interface a
chama. `AjudaScreen` é texto estático, sem glossário.
**Escopo a planejar.** Uma tela de glossário buscável (dentro de Ajuda ou
como item novo do `PerfilHub`), consumindo a busca já existente, com
paginação ou agrupamento por família (indicadores, estrutura, setups,
mecânica da B3, etc. — as famílias já existem na contagem do inventário).
Decisão de UX a resolver no plano: buscar por texto livre, por família, ou
os dois.
**Por que é Fase C e não A.** Não é uma correção pontual: é feature nova,
com decisões de layout e de que subconjunto mostrar por padrão.

### C2 — Ancorar verbete nas quatro abas que não têm nenhum
**O problema.** `SetorAlvo`/`A.abrirVerbete` só aparece em telas onde
`AtivoCard` é renderizado (Watchlist `web/src/App.jsx:4026`, Radar `:7113`)
e em dois pontos isolados do Portfólio
(`diversificacao` em `:4611`, `liquidez-opcao` em `:3720`/`:4328`/`:4334`).
Acompanhar, Histórico, Operador IA e Opções não têm nenhum ponto tocável de
explicação.
**Por que precisa de plano, não de quick-task.** `OpcoesScreen.jsx`
deliberadamente não importa nada de `App.jsx` (comentário em
`OpcoesScreen.jsx:27`), por desenho de isolamento do módulo. Ancorar verbete
lá exige primeiro extrair `SetorAlvo`/`ConceitoSheet` para um módulo
compartilhado que os dois lados possam importar sem violar esse isolamento
— é refatoração real, não só adicionar um botão.
**Escopo a planejar.** (1) extrair o par `SetorAlvo`/`ConceitoSheet` de
`App.jsx` para um módulo próprio; (2) escrever os verbetes que faltam para
os termos específicos de opções que hoje não têm conceito nem verbete —
payoff, breakeven, strike, gregas, collar — nenhum desses ids existe em
`conceitos.py` nem em `kb.py` (confirmado no inventário); (3) ancorar pelo
menos um ponto tocável em cada uma das quatro abas sem cobertura.

---

## Fora de escopo deste prompt — não fazer sem pedido explícito

- **P7 do inventário original**: fundir Radar e Watchlist numa superfície
  segmentada. Depende de medir quantos usuários usam as duas abas na mesma
  sessão antes de qualquer prototipagem. Reorganizar sem medir foi o erro
  que o Trading 212 cometeu e reverteu sob protesto — não repetir aqui.
- **Ampliar o gate mensal de 30 análises** para cobrir as três rotas de IA
  que hoje ficam fora dele. Isso é decisão de modelo comercial (afeta
  monetização do plano gratuito), não bug de UX — leve ao Alex como pauta
  separada, citando o achado B4 como evidência.
- **Remover as rotas órfãs** `POST /api/analyze/{t}` (legada, sem chamador
  no front) e `POST /api/options/analyze` (órfã e, além disso, não chama IA
  nenhuma — é texto determinístico por f-string). Descomissionar rota em
  produção é decisão de produto, não limpeza automática.
- **Sexta aba na barra inferior.** Já foi proposta, revertida e a reversão
  estava certa (D-0.1, 10/09/2026). Nenhum item deste prompt reabre essa
  discussão.

---

## Checklist de fechamento, por item

- [ ] `bash scripts/executar.sh --testes` inteira verde (as DUAS suítes).
- [ ] Item que edita `web/src/` roda `npx vite build` antes de declarar ok.
- [ ] Item que edita `web/src/` verifica paridade `deviceStore` ×
      `serverStore` quando mexe em `persistence.js`.
- [ ] Commit atômico por item, mensagem em PT-BR citando este documento e o
      código do achado (A1, B2, C1, etc.).
- [ ] Nenhum item faz deploy, bump de `SERVER_BUILD_ID` ou toca Railway sem
      pedido explícito à parte.
