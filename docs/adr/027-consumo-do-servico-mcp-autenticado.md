# ADR-027: Consumo do serviço MCP autenticado substitui a fronteira do ADR-024

**Status:** Proposto
**Data:** 2026-09-09
**Decisor:** Alex (aprovação do `docs/PLANO-aba-opcoes.md`, 2026-09-09)
**Substitui:** ADR-024 Decisões 1 e 2 (a Decisão 3 — canal único do MyData,
Guardião C — permanece e se estende ao canal MCP)
**Relaciona:** ADR-004, 010, 013, 018, 020, 021–026
**Base:** `docs/PLANO-aba-opcoes.md` §2 (plano aprovado);
`~/dev/MCP/docs/contrato-mcp-servico.md` (contrato do serviço);
`.planning/quick/260909-waw-aba-opcoes-f1-adr027-cliente-mcp/260909-waw-PLAN.md`.

As assinaturas `rastrear(cadeia, filtros)` / `avaliar(pernas)` do ADR-024
(ENG-04) continuam congeladas — este ADR não as toca.

---

## Contexto

O Boris tem cópias da matemática de opções (`opcoes_payoff.py`,
`opcoes_motor.py`, `opcoes_lastreadas.py`, `opcoes_gatilho.py`) e dois
guardiões (`test_opcoes_fronteira.py` ENG-03, `test_opcoes_gatilho.py`
ENG-06) que proibiam **qualquer** módulo de `server/app/` de importar `mcp`
e proibiam a dependência nos requirements. O motivo declarado no ADR-024 era
duplo: (a) o portal `b-mcp.semente.dev` servia **fixture** em produção, e
consumi-lo produziria número financeiro inventado (princípio 4 do
CLAUDE.md); (b) subir um client MCP **stdio** dentro do processo único do
uvicorn no Railway traria risco operacional sem necessidade. A Estratégia C
("MCP autenticado, `mcp.semente.dev`") ficou registrada lá como "descartada
por ora — depende de `plano-mcp-servico.md`, ainda não aprovado".

Os dois motivos caíram. `mcp.semente.dev` é outro processo, outro domínio:
responde `fonte: "http"` (dado real do MyData), transporte **streamable-http**
(um POST, uma resposta — não há stdio, não há sessão para gerir), e
autenticação `client_credentials` no `id.semente.dev` com `resource` da
RFC 8707. O plano do serviço existe e o `docs/PLANO-aba-opcoes.md`, aprovado
pelo Alex em 2026-09-09, é a aprovação que o ADR-024 aguardava.

A proibição antiga era contra o **portal** e contra **stdio** — não contra o
serviço autenticado. O que este ADR faz é trocar a fronteira, não removê-la.

## Decisões

### Decisão 1 — Fronteira nova: "só o serviço autenticado, só dado real, nunca fixture"

Um único módulo, `server/app/mcp_client.py`, importa `mcp` e `httpx2`.
Nenhum outro módulo de `server/app/` importa qualquer dos dois. Nenhum
módulo do app contém literal `"fixture"` como modo de dado, `MYDATA_MODO` ou
`b-mcp`. A URL do serviço é a do contrato (`https://mcp.semente.dev/mcp`,
default de `MCP_URL`); outra URL só por env, e só com esquema `https`.
Segredo (`MCP_CLIENT_SECRET`) só por env; guardião reprova literal com
formato de segredo em `server/app/`.

### Decisão 2 — Fato × juízo continua a lei

Todo número na aba vem de tool do MCP ou de regra determinística do Boris. A
LLM só (a) compila NL→DSL e (b) fecha o veredito; ambos em turno único
(`llm._call_llm`), validados por código. É o princípio 5 do CLAUDE.md sem
exceção nova: o serviço MCP não chama modelo nenhum, ele responde fato.

### Decisão 3 — Módulos puros ficam nesta entrega; a consolidação tem gatilho

Os módulos puros de payoff (`opcoes_payoff.py` e companhia) permanecem. A
consolidação com o cálculo do MCP é um ADR futuro, com gatilho explícito:
teste de paridade (`opcoes_payoff.perfil_da_estrutura` ×
`evaluate_option_structure`) sobre fixture gravada **e** ao vivo no smoke de
staging; o ADR de consolidação nasce após 10 pregões seguidos de paridade
viva verde em staging, ou na primeira divergência — o que vier antes.

### Decisão 4 — Cap por usuário por dia, ancorado em São Paulo

`metering.check`/`consume` em seções próprias (`mcpUsage`, `mcpUsageGlobal`,
**`mcpUsageMonth`**). O `month_section` próprio não é detalhe: sem ele o
balde mensal do plano comercial (`aiUsageMonth`, ADR-010) seria queimado por
chamada de tool, e uma sessão na aba Opções consumiria a cota de análises de
IA do usuário. O dia do cap é ancorado em **America/Sao_Paulo**, o mesmo
reset que o serviço usa para o teto dele. A recusa acontece **antes** de
chamar o serviço. Cache não gasta cap.

### Decisão 5 — Navegação: Opções entra no lugar de "Operador IA"

Opções entra na barra no lugar de "Operador IA", que vira sub-tela. A barra
segue com 5 itens — a decisão de 03/09 ("sem 6ª aba") é respeitada; o que
muda é qual das cinco. (Fase 2 do plano; nada disto é implementado nesta
fase.)

### Decisão 6 — Licença: risco aceito pelo Alex

O dado da B3 chega ao serviço sob restrição de **uso pessoal, sem
redistribuição** (ADR-18 do MyData; seção "Limites" do contrato). O Boris é
multiusuário e vai ser comercializado. Decisão do Alex (D-0.2 do PLANO, em
2026-09-09): a aba fica visível a **todo usuário logado**, sob a mesma
cláusula que `options_provider_mydata` já opera hoje. **Risco aceito e
registrado aqui.** Permissão `opcoes.mcp.ver` **não** é criada agora; se a
licença apertar, a mitigação é um `require_permission` por rota — mudança de
uma linha por rota, sem redesenho. Anônimo é recusado (401) porque login é
obrigatório no produto, não por causa da licença.

### Decisão 7 — Setups sem dono

O armazém de setups é único no MCP, sem campo `owner`. Criar, confirmar e
desativar exigem a permissão nova `opcoes.criar_setup` (grupo `opcoes`,
ADR-013), que só `role_admin` recebe no bootstrap. Ler, avaliar e ver
gráfico valem para todos os usuários logados. **Lacuna conhecida:** o campo
`owner` não existe no MCP — enquanto não existir, um setup criado é visível
a todos os clientes do serviço, e é por isso que a criação é restrita.

### Decisão 8 — Dado é fim de pregão, e o estado do dado é sempre visível

Toda tela mostra `trading_date`. Três condições **bloqueiam** veredito e
criação de setup: `negociacao_b3` fora de `em_dia`; **`warning` presente**
(frescor não medido); e **erro** da tool. A UI distingue "atrasado (idade
real)" de "idade desconhecida"; nunca "em dia" por default. É o princípio 9
do CLAUDE.md (estados completos) aplicado ao frescor.

### Decisão 9 — Veredito: prompt do serviço, LLM do usuário, validação por código

O backend obtém `prompts/get veredito` e `resources/read
mydata://criterio/operacional` (protocolo, não contam no teto do serviço),
reúne os fatos, chama a LLM do usuário **uma vez**, e valida o texto: tem de
terminar com uma das quatro frases literais **e** conter o aviso. Se não,
`veredito: null` + texto cru rotulado "sem veredito". Veredito nunca é
fabricado nem remendado.

### Decisão 10 — Sem promessa

Rótulos permitidos: "cenários ±1σ" e "delta ≈ chance de terminar dentro do
dinheiro (aproximação)". Aviso do critério sempre visível. Nada de
"probabilidade de sucesso", nada de garantia de lucro (princípios 6 e 8 do
CLAUDE.md).

## Consequências

**A favor:**

+ Uma fonte para leitura, catálogo, montagem e setups, respeitando a regra
  prática do contrato: "fato bruto pelo MyData, derivação pelo MCP".
+ Setups declarativos NL→DSL, que o Boris não tinha.

**Contra (aceito):**

− Dependência de rede em runtime para a aba Opções. Sem o serviço, a aba
  degrada com estado explícito; o resto do app não muda.
− Dois stacks HTTP no processo (`httpx` do resto do app + `httpx2` que o SDK
  do MCP traz) até uma migração futura. É o custo do SDK oficial; o
  alternativo seria reimplementar o OAuth à mão, o que é pior.
− Teto de 2.000 chamadas/dia para TODOS os usuários do Boris somados: cache
  e cap são o freio. Se a base crescer além disso, o freio certo é subir o
  TTL do cache (o dado é EOD; TTL até a próxima carga é legítimo), não pedir
  teto maior.
− Segredo novo no Railway (`MCP_CLIENT_SECRET`); a rotação é ação do Alex.
− Até a consolidação (Decisão 3), dois caminhos calculam payoff
  (Radar/lastreadas por `opcoes_payoff`; aba pelo MCP) — a paridade viva em
  staging é o alarme de divergência.

**Achado de implementação (Fase 1, 2026-09-09) — `metering._now` não decide o
dia.** `metering.check(..., _now=...)` só alimenta o rate limit (`now - t <
60.0`, epoch float); o dia sai de `_today()`, que lê
`datetime.now(timezone.utc)` sem ponto de injeção. A contingência prevista no
PLANO §3.2 se aplica: `metering` ganhou overrides **opcionais**
`_dia`/`_mes` (default `None` = comportamento anterior byte a byte, nenhum
call site existente muda) e a seção `mcpUsage*` passa o dia pronto, calculado
em `America/Sao_Paulo` por `options_mcp_api._dia_sp()`. `_dia` e `_mes`
sempre viajam juntos — a regra que `metering._month` já documentava (nunca
duas noções de tempo diferentes para dia e mês) continua valendo.

**Decisão de implementação (Fase 1) — `/status` reporta estado, não 422.** O
mapeamento HTTP deste ADR manda `McpErroDeTool → 422`; a Decisão 8 manda
`bloqueia = ... OU erro da tool`. Em `GET /api/options/mcp/status` as duas
regras se cruzam. **Decisão:** `/status` captura `McpErroDeTool` e responde
**200** com `frescor.warning = <mensagem da tool>` e `frescor.bloqueia =
true`, porque a finalidade de `/status` é justamente reportar o estado do
dado — princípio 9 do CLAUDE.md: "idade desconhecida" nunca pode virar "em
dia". O 422 segue valendo no helper `_erro_http`, usado pelas rotas de
leitura das Fases 2+, onde o erro da tool é falha do pedido e não um estado a
exibir. Ambos os caminhos são testados.

## Guardiões

- **Guardião A** (módulos puros de opções, ENG-03): mantém; **acrescenta
  `httpx2`** à lista de imports proibidos — hoje `"httpx2" != "httpx"`
  passava pelo filtro de igualdade.
- **Guardião B** → inverte de "nenhum módulo importa `mcp`" para
  **"exatamente um módulo de `server/app/` importa `mcp`/`httpx2`:
  `mcp_client`"**, por igualdade de conjunto (não por denylist).
- **Guardião B-requirements** → **inverte**: `mcp>=2.1,<3` presente e
  **idêntico** nos dois requirements.
- **Guardião C** (ENG-05, canal único do MyData): mantém inalterado e se
  estende ao canal MCP — `mcp_client` não importa `mydata_client`.
- **Novos:** (i) sem literal `"fixture"`/`MYDATA_MODO`/`b-mcp` em
  `mcp_client.py` e `options_mcp_api.py`; (ii) todo literal com `://` em
  `mcp_client.py` é uma das duas URLs do contrato; (iii) nenhum literal com
  formato de segredo (chave de máquina legada ou JWT) em `server/app/`;
  (iv) toda rota `/api/options/mcp/*` passa por `require_user` **e** pelo
  cap; (v) todo `metering.consume` do cap leva
  `month_section="mcpUsageMonth"`.
- `test_guardrail_imperativo.py`: os textos fixos novos
  (`opcoes_veredito.py`, compilador NL→DSL, `copy.js` novo) entram em
  `FONTES` na fase que os criar — não nesta.
- **ENG-06** (`test_opcoes_gatilho.py`): mantém inalterado — a DSL de setups
  do MCP **não** é portada para o app; ela é montada em runtime a partir do
  `inputSchema` da tool.

## Ambiente

Env do servidor (Railway; só o Alex configura): `MCP_CLIENT_ID`,
`MCP_CLIENT_SECRET`, `MCP_URL` (opcional),
`B3_MCP_COTA_USUARIO_DIA` (60), `B3_MCP_RATE_MIN` (20),
`B3_MCP_COTA_GLOBAL_DIA` (1800), `B3_MCP_CACHE_S` (900). O aviso de boot que
vigia nome de variável com espaço passa a vigiar o prefixo `MCP_` também.

Nenhum desses valores entra no bundle do front (guardrail do CLAUDE.md:
segredo só em env do servidor).

## Emenda 1 (Fase 27, 2026-09-13) — Decisão 7: o dono passa a existir do lado do Boris

A **lacuna declarada na Decisão 7 continua**: o campo `owner` não existe no
MCP, e um setup criado segue visível a todos os clientes do serviço. O que
muda é que o **Boris deixa de depender dela**.

Três peças, todas no backend:

1. **Prefixo determinístico por conta no nome enviado** —
   `opcoes_vigias.nome_no_servico(uid, nome)` produz `sha256(uid)[:8] + "-" +
   nome`. É `sha256` truncado e não o `user_id` porque o nome viaja para fora
   e fica visível a todos os clientes do serviço: identificador de conta em
   nome público é vazamento, não organização. O prefixo vale no **ensaio**
   (`/setups/compilar`, `create_setup` com `confirm: false`) **e** na gravação
   (`/setups/confirmar`) — até esta data o dry-run validava um nome e a
   gravação mandava outro, e uma recusa de formato só apareceria depois de a
   pessoa pagar 2 chamadas do cap e uma análise de LLM. A função é idempotente
   por desenho, porque o objeto do ensaio volta pela tela para ser gravado.
2. **Índice por usuário no kv** (`opcoes_vigias`, seção `opcoesVigias`,
   escopada por `db._scoped`) — é o único lugar do sistema com o nome que a
   PESSOA escreveu, o ticker e a data de criação. O `list_setups` não devolve
   nenhum dos três. O índice **não guarda estado** (`armed`/`streak`): estado é
   medição do serviço, e guardá-lo aqui produziria "armado" carimbado de
   ontem (princípio 4 do CLAUDE.md).
3. **Gate de dono no backend, nas DUAS rotas que recebem `{name}` na URL** —
   `POST /setups/{name}/desativar` e `GET /setups/{name}/grafico` recusam com
   403 `setup_de_outro_dono` quando o nome não é `e_meu` nem `e_legado`,
   **antes** do `_cap_check`. Esconder o botão na UI deixaria a rota aberta a
   qualquer `curl`; cobrar cota de uma recusa que não viajou seria cobrar pelo
   que não aconteceu. É a MESMA função (`_exige_dono`) nos dois lugares: duas
   cópias da condição divergem na primeira correção feita de um lado só, e o
   lado esquecido é o que fica aberto.

   **O `/grafico` só foi fechado em 2026-09-13, depois do 27-01, e o registro
   importa.** O gate nasceu só no `/desativar` porque o threat model daquele
   plano não listava a rota de gráfico — o executor não expandiu escopo por
   conta própria e registrou o risco residual por escrito. Até o fechamento,
   qualquer conta logada via as condições, a série e as datas de disparo do
   vigia de outra pessoa, bastando conhecer o nome completo (incluindo os 8
   hexadecimais do hash dela). Nenhuma rota do produto enumera esses nomes, o
   que mantinha o risco baixo — mas "não enumerável" nunca foi o mesmo que
   "fechado". Decisão do Alex, 2026-09-13: fechar.

**Medido contra o serviço real em 2026-09-13**, antes de qualquer código: o
`create_setup` aceita `[8 hexadecimais]-[texto]` como `name` e devolve o nome
EXATAMENTE como enviado, sem normalizar, truncar ou reescrever — no ensaio e
na gravação. Um nome SEM prefixo também é aceito: o serviço não impõe formato
nenhum, e a unicidade continua sendo responsabilidade do Boris.

### Legado (setup sem prefixo) — decisão do Alex, 2026-09-13

Perguntado o que fazer com os setups já gravados no armazém sem dono
conhecido, a resposta foi literal: **"pode apagar os antigos"**. O que isso
significa em código:

- **Fora de toda listagem.** Um nome sem prefixo não aparece em
  `/leitura/{ticker}`, não aparece em `GET /setups` e não aparece no bloco
  "Seus vigias". Ele deixou de ser conteúdo do produto. Cai junto a ideia de
  exibir legado com rótulo, e cai a ideia de "adoção".
- **E ainda assim desativável** por quem tem `opcoes.criar_setup`. A porta
  fica aberta de propósito: a LISTAGEM é sobre "o que é meu", a DESATIVAÇÃO é
  sobre "isto ainda dispara". Sem ela, um órfão vira lixo permanente que o
  produto não consegue remover enquanto o serviço segue avaliando-o todo
  pregão. Há um teste dedicado só para impedir que essa porta seja fechada por
  engano num refactor.
- **O que NÃO se faz: varrer.** Nada de "desativa tudo que não tem prefixo". O
  armazém "é visto por todos os clientes do serviço" (`server/app/rbac.py:29-34`),
  então um nome sem prefixo pode ser de OUTRO sistema — não do Boris+ e não do
  Alex. Apagar em massa ali seria destruir dado de terceiro, e não há `undo`.
  A limpeza é **operacional, com lista na mão, um a um, com aprovação do
  desenvolvedor**.

### O que esta emenda NÃO muda

`opcoes.criar_setup` continua restrita ao grupo `opcoes` do ADR-013. A emenda
**reduz o dano** da lacuna da Decisão 7 (colisão de nome, desativação cruzada,
invisibilidade dos próprios setups); ela **não fecha** a lacuna — quem tem a
permissão continua escrevendo num armazém que todos os clientes do serviço
enxergam. Por isso ela não é argumento para abrir a permissão.

## Emenda 2 (Fase 27, 2026-09-13) — leitura técnica interna para a aba

**Decisão D1 do Alex, 2026-09-13.** Perguntado de onde deve sair a análise
técnica da evolução dos ativos na aba Opções, a resposta foi **híbrido:
técnico interno + estrutura no MCP**. Este ADR fecha essa fronteira; a decisão
a atravessa deliberadamente, e isto é o registro — não uma nota de rodapé no
código.

Convive com a Emenda 1 sem conflito: a Emenda 1 trata de **quem é o dono** do
que se grava no armazém compartilhado do serviço; esta trata de **de onde sai
o número** que a aba lê. As duas empurram na mesma direção — reduzir a
dependência do serviço para o que o Boris já sabe fazer sozinho — e nenhuma
delas relaxa o cap, o gate de permissão ou o custo declarado.

### O que muda

O backend passa a servir leitura técnica **interna** e determinística para a
aba: `server/app/opcoes_tecnico.py` (módulo puro) e
`GET /api/options/tecnico/{ticker}` (rota nova em `main.py`). Ela responde
tendência, volatilidade histórica, suporte/resistência e uma régua de sete
pregões, lendo o **mesmo Snapshot Técnico Único** que serve
`/api/technicals/{ticker}`, o Radar e a Watchlist — nenhuma linha de
matemática nova, e nenhuma chamada a `mcp.semente.dev`.

A rota **não** mora em `options_mcp_api.py`, e isso é decisão e não
conveniência: o guardião (iv) obriga toda rota `/api/options/mcp/*` a passar
pelo `_cap_check`, e cobrar cota do serviço por uma leitura que não sai do
processo seria cobrar pelo que não aconteceu. Mesma razão de
`GET /api/options/vigias` (Emenda 1). Ela usa `Depends(current_scope)` — o
MESMO gate de `/api/technicals/{ticker}`, porque é o MESMO dado de mercado
público; exigir sessão só aqui criaria duas réguas de acesso para a mesma
informação. A allowlist pública do ADR-013 **não cresce** (segue em 25).

A resposta declara `custoMcp: 0` como campo de contrato — é dele que a tela
tira o rótulo "grátis" do controle, em vez de o front inventar o rótulo por
conta própria.

### O que NÃO muda

- **O isolamento de FRONT permanece.** `web/src/opcoes/*` continua sem
  importar `App.jsx`, e o guardião que trava isso continua. O que atravessou a
  fronteira foi o BACKEND, servindo dado do motor interno para a aba — não o
  acoplamento de componentes que o ADR evitou.
- **A Decisão 2 ("fato × juízo") permanece**, e esta emenda a reforça: o
  número vem do motor determinístico, a LLM só interpreta. É o princípio 5 do
  CLAUDE.md — se a leitura técnica viesse de um serviço pago por consulta, a
  tela teria de escolher entre gastar cota a cada abertura ou mostrar menos.
- **O §3.3 (custo de MCP só em clique explícito) NÃO afrouxa — fica mais
  forte.** A leitura interna existe justamente para a aba abrir com conteúdo
  sem gastar cota de ninguém. Toda chamada ao serviço continua saindo de
  clique explícito, com o custo declarado no controle. Um teste com bomba em
  `mcp_client.call_tool` prova que a rota nova não toca o serviço, e um teste
  de `ast` prova que `opcoes_tecnico.py` não importa `mcp`/`httpx`/
  `candle_provider`: custo zero é propriedade do grafo de imports, não frase
  de docstring.

### A divisão de trabalho (régua para quem acrescentar campo depois)

| Responde | Fonte | Exemplos |
|----------|-------|----------|
| Comportamento do **ATIVO** | motor interno (`opcoes_tecnico.py`) | tendência, volatilidade histórica, suporte/resistência, evolução em 7 pregões |
| O que é específico de **OPÇÃO** | serviço MCP | cadeia, vencimentos, estruturas operáveis, payoff, avaliação de setup |

Campo novo se decide por esta régua, não por qual chamada já está aberta.

### A consequência aceita: duas fontes descrevem o mesmo ativo

O `behavior` que o serviço devolve e a leitura interna falam do MESMO ativo e
**podem divergir** — HV medida pelo MyData × HV calculada pelo
`technical_models` sobre a série do Yahoo/brapi, sobre janelas e calendários
que não são obrigados a coincidir.

**A divergência é INFORMAÇÃO, não erro.** Cada bloco carrega a própria `fonte`
e o próprio carimbo (`snapshotId`, `asOf`, `source`, `cacheStatus` no lado
interno; `trading_date` no lado do serviço) — princípio 3 do CLAUDE.md — e
**nenhuma reescreve a outra**. Esconder uma das duas produziria a pior das
saídas: um número único sem dono, impossível de explicar quando alguém
perguntar por que a tela mudou.

Cuidado medido e registrado aqui porque é como se erra 10× em silêncio: o
`hv21Pct`/`hv63Pct` do `technical_models` está em **percentual**, enquanto o
`hv21`/`hv63` do serviço chega em **fração**. Por isso o bloco de volatilidade
da rota nova declara `"unidade": "pct"` **sempre**, inclusive quando os
valores são `null` com motivo — é por esse campo que a tela escolhe o
formatador, em vez de adivinhar.

**Unificar as duas é decisão futura, com gatilho, e não entra nesta fase** —
mesmo formato da Decisão 3: o ADR de unificação nasce depois de uma medição de
paridade viva (HV interna × HV do serviço para o mesmo ticker e o mesmo
pregão) em staging por 10 pregões seguidos, ou na primeira divergência
material (sinal trocado ou ordem de grandeza), o que vier antes. Até lá as
duas convivem, cada uma com o seu carimbo.

### Fiação do assistente (mesma data)

`_pet_resumo_opcoes` afirmava, numa frase só, que "a leitura da aba é de FIM DE
PREGÃO e vem do serviço de opções". Com o híbrido no ar isso virou meia
verdade dita como verdade inteira. O texto foi separado e nomeado: o que é do
ATIVO vem do motor interno (pregão fechado, custo zero); o que é de OPÇÃO vem
do serviço (fim de pregão). Guardião dedicado em `test_pet_todas_telas.py`,
com lado positivo e lado negativo, impede a volta da frase meio-certa. O
resumo continua **sem** chamar o serviço e passou a também **não** buscar
candle: dizer de onde a leitura vem é diferente de buscá-la, e o orçamento da
brapi é finito (ADR-008).
