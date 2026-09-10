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
