---
title: Opções v2 (setups propostos via b-mcp) — exploração de arquitetura e decisões autônomas
date: 2026-09-01
context: Sessão /gsd-explore rodada em modo autônomo (usuário foi dormir, autorizou
  decidir e documentar sem esperar resposta). Investiga a ideia de uma experiência
  de Opções no Boris+ que propõe setups a partir de análise técnica, usando o MCP
  "mydata"/"b-mcp" como backend.
---

# Opções v2 — setups propostos via b-mcp: exploração de arquitetura

## Ideia original (sem alteração de escopo)

Nova experiência de Opções no Boris+, restrita a opções com cobertura real na
carteira (mesma régua da Fase 14 — venda coberta, put de proteção). A partir do
snapshot de análise técnica de um ativo, propor um setup de opções (ou uma
perna) que o usuário aceita ou recusa. V1 usa uma biblioteca fixa dos setups
mais conhecidos do mercado; setup customizado pelo usuário fica para depois.

Colocação na navegação (aba própria fora do Operador / dentro de "Posições" /
fundida com "Mesa") ficou deliberadamente em aberto no prompt original — não é
resolvida nesta sessão, ver seção própria abaixo.

## Achado principal: "b-mcp" não é hipótese — é infraestrutura real já no ar

O prompt original tratava "b-mcp" como codinome incerto. Não é. É o nome do
serviço Railway que publica o server MCP em `~/dev/MCP/servers/mydata/`:
portal conversacional em `https://b-mcp.semente.dev` (atrás de senha), com 10
tools MCP já implementadas — não as 4 do rascunho de 25/08
(`docs/prompt-proximos-passos.md`, que é histórico, superado pela
implementação real):

| Tool | O que faz |
|---|---|
| `list_option_expirations` | Vencimentos disponíveis pro ticker |
| `get_option_chain` | Cadeia completa, com ilíquidos |
| `find_tradable_options` | Cadeia filtrada por IV computado, `min_trades`, faixa de `delta` — "screen the option chain down to contracts worth looking at" |
| `evaluate_option_structure` | Tool genérica de N pernas (contrato, lado, quantidade) → custo líquido, ganho/perda máximos, breakeven, delta somado. Trava, straddle e borboleta são ENTRADAS desta tool, não tools separadas (DECISÃO 7 do server) |
| `create_setup` / `list_setups` / `deactivate_setup` / `get_setup_chart` / `evaluate_setups` | DSL declarativa de setup técnico (`setups.py`) — condições sobre indicadores (sma/ema/rsi/atr/highest/lowest/rel_volume/change_pct), padrões de candle, lógica AND/OR, `consecutive_days`. Puro, determinístico, testável |
| `check_data_freshness` | Frescor do dado anexado em toda resposta |

**O achado que muda a proposta original:** o `Setup` (TypedDict em `server.py`)
já tem um campo `options_intent` — `{direction, target_delta,
target_sessions_to_expiry, note}` — "what the trigger is for: the options
trade it should suggest." Ou seja, a ponte "gatilho técnico → intenção de
opções" já está no schema. O que NÃO existe ainda (confirmado por leitura
direta do código, não por inferência): a lógica que cruza essa intenção com uma
posição REAL da carteira do usuário e decide QUAL estrutura nomeada propor
(venda coberta vs. put de proteção vs. outra) — isso é código que falta, e
falta nos dois lados (nem no mydata, nem hoje no Boris).

## Padrão de arquitetura já validado do lado do mydata — replicável

Documentado explicitamente em `server.py`, seção "DECISÃO 8 — setups: o LLM
compila, o código avalia":

> modelo → compila a frase do usuário para a DSL, UMA vez, na criação.
> código → valida, faz backtest e avalia pregão a pregão. Determinístico, sem
> token, testável — mesma DSL + mesma série = mesmo resultado.

Isso é exatamente o guardrail do CLAUDE.md do Boris (princípio 5: "cálculo
nunca pela IA") aplicado à letra, num sistema irmão. Confirma que o desenho da
ideia original — v1 com biblioteca FIXA de setups conhecidos, custom fica para
depois — já está alinhado com o único padrão que o próprio mydata considera
seguro. Não é preciso reabrir essa decisão.

Segundo princípio relevante, de `docs/prompt-proximos-passos.md` (dated mas a
lição sobrevive): **"fato na tool, juízo na skill"** — as tools do MCP devolvem
fato e conta pública (prêmio, delta, payoff); o critério operacional (o que
conta como "vale propor") fica numa skill separada, hoje `analise-tecnica-b3`
do lado do mydata. O Boris JÁ TEM o equivalente: a skill `analise-tecnica-b3`
está no catálogo deste projeto. Mapeamento direto: a lógica de "qual setup
propor sobre esta posição" deveria estender essa skill (ou o código
determinístico que ela invoca), não a tool MCP.

## Decisões tomadas nesta sessão (autônomas, usuário ausente — revisar ao acordar)

Numeração espelha as 7 perguntas do prompt original + navegação.

**1. O módulo `setups` do mydata é o motor de proposta ou só suporte de
cálculo?** DECISÃO: é suporte de cálculo + ponte de intenção (`options_intent`),
NÃO o motor de decisão "qual estrutura propor sobre esta posição real". Essa
lógica falta em ambos os repos e é trabalho do Boris, porque só o Boris tem a
carteira do usuário (o mydata é deliberadamente stateless de carteira — ver
ADR de fusão, Decisão 2, ainda válida: "carteira fica no aparelho/servidor do
Boris; mydata recebe no máximo `{ticker,qty,avg}` por chamada, sem persistir").

**2. Transporte em produção.** PARCIALMENTE RESOLVIDO, com um ponto BLOQUEADO
(ver seção Bloqueios). O Boris já tem `server/app/mydata_client.py` (existe de
verdade, não é hipótese — Fase 9, HTTP client puro, sem protocolo MCP,
`MYDATA_URL` default `https://mydata.acamerini.app`) e `options_provider_mydata.py`
consumindo dado de opções por REST, em produção desde 31/08 (Fase 14). Esse é
o padrão certo a estender — REST determinístico, nunca subir um client MCP
stdio dentro do processo único do Railway. O que falta decidir é qual
domínio/serviço tem as tools de `setups`/`evaluate_option_structure` em modo
produção — ver bloqueio.

**3. Interação com o lock do WR-01 (`mydata_budget.py`).** DECISÃO: qualquer
chamada nova ao hub mydata (screening de opções, avaliação de estrutura) DEVE
passar pelo mesmo `reservar()`/lock que já existe — não é opcional, é extensão
do mesmo cliente (`mydata_client.py`), não um canal paralelo. Isso é uma
constraint de design a registrar na fase de implementação, não uma decisão de
produto — registrando aqui para não se perder.

**4. Conflito com o guardrail CVM (motor determinístico decide, LLM explica).**
DECISÃO: sem conflito, DESDE QUE se siga o mesmo padrão "LLM compila uma vez,
código decide sempre" que o próprio mydata já usa. A biblioteca v1 de setups
de opções (venda coberta, put de proteção, e o que mais entrar) deve ser
código Python determinístico do lado do Boris — não um setup "gerado" por LLM
por request. Isso é compatível com a ideia original do usuário (biblioteca
fixa em v1) e não precisa de decisão nova.

**5. Escopo do v1 da biblioteca além de venda coberta / put de proteção.**
NÃO DECIDIDO — deixado em aberto de propósito. Escolher a próxima estratégia
(collar? straddle coberto?) é decisão de produto/pedagógica que depende de
critério que só o Alex tem contexto pra fechar (liquidez real de opções B3 por
ticker, o que faz sentido pedagogicamente no Modo Estudo). Registrado como
pergunta em aberto, não como bloqueio técnico.

**6. Fluxo de aceite (motor de ordens existente vs. automação nova).**
DECISÃO: reusar o motor de opções lastreadas que a Fase 14 já entrega
(`store.py`, mesmo fluxo de aceite humano). Não há indício em nenhum dos
documentos levantados de que isso devesse mudar — introduzir uma automação
nova (tipo `agent.py`) não foi pedido pelo usuário e contradiz o próprio
enunciado da ideia ("o usuário poderá ou não aceitar o setup" — aceite manual,
não automação).

**7. Plano comercial (gratuito vs. pago).** NÃO DECIDIDO — decisão comercial,
fora do que um agente pode assumir sozinho por princípio (ver CLAUDE.md global:
não decidir número comercial sem o Alex). Registrado como pergunta em aberto.

## Navegação — recomendação, não decisão fechada

Três candidatos levantados pelo usuário: (a) aba própria fora do Operador, (b)
contextual dentro de "Posições", (c) fundir/otimizar com a aba "Mesa"
existente. Esta sessão NÃO tem acesso a como o app realmente se parece hoje
nem a critério de gosto de produto — não é uma decisão de arquitetura que dá
pra fechar por leitura de código. Recomendação, com reserva:

Como a feature é estritamente "opções sobre posição que já existe" (nunca
opção nua), o candidato (b) — contextual dentro de Posições — tem a vantagem
de nunca aparecer vazio (só existe quando há cobertura real) e evita adicionar
mais uma aba a um app que já tem Operador + Mesa + Posições. Mas isso é
palpite fundamentado, não veredito. Fica como pendência explícita para rodar
`design-with-claude:navigation-specialist` com o Alex acordado, comparando as
3 opções com trade-off de verdade (densidade, descoberta, coerência com Mesa/
Posições) antes de comprometer.

## Bloqueios — precisam do Alex, não adivinhados

1. ~~`mydata.semente.dev` × `mydata.acamerini.app` — mesmo hub?~~
   **RESOLVIDO 2026-09-01, pelo Alex: `mydata.semente.dev` é o canônico.**
   Confirmação técnica direta: os dois domínios respondem no mesmo Railway
   edge (`jfk1`) com `x-hikari-trace: jfk1.57w5` e `content-length`
   idênticos — é o mesmo serviço sob dois nomes DNS (rename em andamento,
   não dois hubs). `acamerini.app` segue funcional hoje (sem incidente em
   produção), mas `server/app/mydata_client.py:21`
   (`BASE_DEFAULT = "https://mydata.acamerini.app"`) está desatualizado
   frente ao nome canônico — Railway não tem `MYDATA_URL` setada, então
   produção depende inteiramente desse default. Ação de baixo risco
   registrada em `.planning/todos/pending/opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp.md`,
   aguardando confirmação do Alex antes de trocar.
2. **O portal `b-mcp.semente.dev` é protegido por senha para uso humano
   (`PORTAL_SENHA`) — as tools de `setups`/`evaluate_option_structure`
   expostas por ele têm uma via de acesso server-to-server (sem senha
   interativa) que o backend do Boris possa chamar?** Os docs do MCP tratam
   esse server como "pessoal, local, stdio, servindo só você" — não achei
   nenhuma confirmação de que ele foi desenhado para ser cliente de outro
   backend em produção (multi-tenant), diferente do hub `mydata.*` que já é.
   Sem essa confirmação, presumir que o Boris pode chamar as tools de setups
   do b-mcp direto em produção seria arquitetura inventada.
3. **Rate-limit real do hub mydata segue não medido** (já era ressalva aberta
   em `.planning/notes/boris-pp-centralizacao-dados-mydata.md` de 27/08, e no
   todo pendente `medir-rate-limit-mydata.md`, prioridade média). Um fluxo de
   setups que varre `find_tradable_options` por ticker consome mais chamadas
   que o fluxo atual de opções lastreadas — isso reforça a prioridade desse
   todo, não é um achado novo, mas vale reabrir a prioridade quando esta ideia
   virar fase.

## Fontes consultadas nesta sessão

- `~/dev/MCP/servers/mydata/server.py`, `setups.py`, `calculos.py`,
  `armazem.py` (leitura direta de código, não de doc)
- `~/dev/MCP/docs/prompt-proximos-passos.md` (25/08 — histórico, arquitetura
  ainda válida, números de tool contagem já superados)
- `~/dev/MCP/docs/adr-fusao-b3agente-mydata.md`,
  `~/dev/MCP/docs/boris-pp-00-mapa-de-realidade.md`,
  `~/dev/MCP/docs/briefing-setups.md`, `~/dev/MCP/docs/cowork-project-context.md`
  (síntese via subagente — cadeia de correções, ver aviso abaixo)
- `.planning/notes/boris-pp-centralizacao-dados-mydata.md` (27/08 — a versão
  corrigida/vigente da comparação Boris×mydata, dentro deste repo)
- `server/app/mydata_client.py`, `options_provider_mydata.py`,
  `mydata_budget.py` (estado real do Boris hoje)

**Aviso de cadeia de correção:** os 4 docs do MCP citados acima têm cabeçalhos
de invalidação cruzada (`adr-fusao` e `cowork-project-context` marcam-se como
"BASE INVALIDADA 2026-08-27"; o próprio `mapa-de-realidade` tem uma correção
posterior no mesmo dia). A nota deste repo
(`boris-pp-centralizacao-dados-mydata.md`) é a mais nova da cadeia e foi
tratada aqui como a mais confiável — mas ela também tem 3 ressalvas próprias
não resolvidas (rate-limit, `provento_b3` sem carga completa, hub com um único
consumidor). Se decisões futuras dependerem de detalhe fino desses 4 docs do
MCP, releia — não confie em memória desta síntese para nuance.

## Próximo passo formal

Não virou fase nem requirement — os 3 bloqueios acima (domínio do hub, acesso
server-to-server ao b-mcp, rate-limit) são o que trava `/gsd-plan-phase`. Ver
todo criado nesta sessão.
