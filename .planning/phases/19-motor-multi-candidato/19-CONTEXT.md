# Phase 19: Motor multi-candidato - Context

**Gathered:** 2026-09-03
**Status:** Ready for planning
**Source:** Síntese manual, autonomia concedida pelo Alex (mesmo padrão das
Fases 17/18 — "seguir direto e com autonomia para aprovar as decisões",
nunca revogado nesta sessão). A regra de QUAIS candidatos coexistem por
`decisao` é uma decisão de produto real, tomada aqui com essa autonomia e
documentada com o raciocínio completo abaixo — não é óbvia a partir do
ROADMAP/REQUIREMENTS sozinhos.

<domain>
## Phase Boundary

Cobre MULTI-01/02: o motor (`opcoes_lastreadas.propor()`) deixa de escolher
UMA estrutura fixa por posição e passa a devolver TODOS os candidatos
elegíveis simultaneamente; o detalhe da posição em Posições (Fase 18) mostra
os N lado a lado; usuário aceita exatamente um. Não reabre ENG-01..06 (Fase
15, motor `rastrear()`/`avaliar()` em si) nem LIB-01..03 (Fase 16, as 3
estruturas em si) — é extensão aditiva sobre a MESMA aritmética e as MESMAS
3 estruturas, só a política de "quantos candidatos oferecer ao mesmo tempo"
muda.

</domain>

<decisions>
## Implementation Decisions

### Estado real do código a estender

`server/app/opcoes_lastreadas.py:158-335` — `propor()`: hoje o branch em
`plano.decisao`/`plano.lado` (linhas 198-212) escolhe exatamente UM `tipo`
(`put_protecao` | `call_coberta` | `sem_setup` cedo demais pra sequer
tentar) e devolve `{"proposta": <dict|None>, "motivo": <str>}` — um dict
único, nunca uma lista. Dentro do branch `put_protecao` (linhas 246-263), o
collar já existe no código, mas só como FALLBACK: só é tentado quando
`contratos < 1` (caixa insuficiente pro put puro) — nunca como candidato
paralelo quando o put puro CABE no caixa. `_propor_collar()` (linhas 41-155)
recebe o `contrato_put` JÁ SELECIONADO por parâmetro — nunca reseleciona —
então chamá-la de novo, num contexto onde o put puro também é viável, é
seguro e não duplica a régua de seleção.

`server/app/main.py:2506-2595` — `POST /api/options/lastreada/abrir-collar`
(Fase 17, ADR-026): re-deriva a proposta chamando `propor(...,
multiperna=True)` de novo e checa `resultado.get("motivo") != "collar"`
(linha 2583) — **esta checagem quebra com o motor multi-candidato**: se o
put_protecao E o collar passam a coexistir, `motivo` do resultado (que vai
virar o motivo do candidato PRIMÁRIO, ver decisão de compatibilidade abaixo)
será `"put_protecao"`, não `"collar"`, mesmo quando o usuário está
aceitando explicitamente o candidato collar que a UI ofereceu — a rota
rejeitaria com 409 uma aceitação legítima. **Esta rota precisa mudar nesta
fase** (não é opcional): procurar o candidato de `tipo == "collar"` dentro
da nova lista de candidatos, não assumir que é o resultado primário.

`server/app/main.py:2429-2482` — `POST /api/options/lastreada/abrir`
(single-leg): **NÃO precisa mudar**. Confirmado lendo o código: esta rota
NUNCA chama `propor()` nem re-deriva nada — valida o `contractSymbol`
submetido direto contra a cadeia AO VIVO (`chain.get("calls"...)`/`puts`,
linha ~2464) e abre com `store.abrir_call_coberta`/`comprar_put_protecao`.
Ela já aceita qualquer contrato válido da cadeia, então oferecer múltiplos
candidatos (cada um com seu próprio `contractSymbol`) não exige nenhuma
mudança aqui — o usuário aceitando o candidato put_protecao (não-collar)
continua batendo nesta rota sem alteração.

`web/src/App.jsx:3919-4127` (Fase 18) — `OportunidadesOpcoes`,
`PropostaDaPosicao`, `useOpcoesPropostas`: todos leem `r.proposta.proposta`
(o dict único de hoje). Ver decisão de compatibilidade abaixo — o campo
`proposta` PERMANECE existindo com a MESMA forma (não deixa de existir),
então este código continua funcionando sem edição. A UI nova desta fase lê
um campo ADICIONAL.

### MULTI-01 — regra de quais candidatos coexistem (decisão de produto)

Generalização MÍNIMA e conservadora, ancorada no que o motor já calcula —
não inventa estrutura nova, só para de esconder uma que já existia como
fallback:

- **`decisao == "VENDER"` ou `lado == "baixa"`** (branch `put_protecao`,
  linha 201-203): quando `multiperna=True`, o motor tenta os DOIS
  candidatos de forma independente — `put_protecao` (se `contratos >= 1`,
  cabe no caixa) E `collar` (sempre que `_propor_collar()` encontrar uma
  call líquida e o custo líquido couber, INDEPENDENTE de o put puro caber
  ou não). Antes: collar só aparecia quando o put puro NÃO coubesse
  (fallback exclusivo). Depois: se AMBOS couberem, os DOIS aparecem juntos
  — são estratégias concorrentes genuinamente diferentes (pagar por
  proteção pura vs. financiar a proteção abrindo mão de upside), a leitura
  técnica (`VENDER`/`baixa`) sustenta as duas igualmente. Se só um coubar,
  só esse aparece (comportamento de hoje, preservado). Se nenhum coubar,
  lista vazia + `motivo="caixa_insuficiente"` (preservado). Quando
  `multiperna=False`, comportamento byte-idêntico a hoje (nunca tenta
  collar) — a negociação de capacidade da Fase 16 continua valendo.
- **`decisao in ("AGUARDAR CONFIRMAÇÃO", "NÃO OPERAR")` ou `lado ==
  "neutro"`** (branch `call_coberta`, linha 204-206): candidato único
  (`call_coberta`), sem mudança — não há segunda estrutura que a leitura
  técnica "sem tendência" sustente ao mesmo tempo (put custaria caro sem
  motivo de queda; collar sem intenção de venda não faz sentido).
- **`decisao == "COMPRAR"` ou `lado == "alta"`** (linha 207-212): sem
  mudança — `sem_setup`, lista vazia. A razão já documentada no código
  (vender call trava o movimento que o motor está lendo; comprar put é
  proteção que ninguém pediu) vale igual com N candidatos: nenhuma das 3
  estruturas faz sentido aqui, oferecer qualquer uma seria o motor
  inventando convicção que a leitura técnica não sustenta.

Resultado prático: **N > 1 só acontece no branch VENDER/baixa, e só quando
`multiperna=True`** — os outros dois branches continuam de candidato único
(ou zero). Isso é deliberado, não uma limitação a resolver depois: é a
generalização que os dados de hoje sustentam, sem forçar candidato onde a
leitura técnica não indica um segundo caminho plausível.

### MULTI-01 — forma de retorno (compatibilidade aditiva)

`propor()` passa a devolver `{"proposta": <dict|None>, "motivo": <str>,
"candidatos": [<dict>, ...]}` — campo NOVO, aditivo, mesmo padrão já usado
pela Fase 16 (`estrutura`/`caixa`/`precoObjeto` entraram do mesmo jeito).
`candidatos` é a lista completa (0, 1 ou 2 dicts, cada um na MESMA forma que
`proposta` tem hoje — `tipo`/`pernasContratos`/`manchete`/`estrutura`/etc.,
ver `server/app/opcoes_lastreadas.py:307-335` e `:116-155`). `proposta`
continua sendo o PRIMEIRO candidato da lista (`candidatos[0]` se não-vazia,
senão `None`) — não um campo recalculado à parte. Ordem de preferência
quando os dois existem: **`put_protecao` antes de `collar`** (proteger
capital sem abrir mão de upside é o candidato mais conservador — vai
primeiro; o índice 0 é quem qualquer consumidor ANTIGO que só lê `.proposta`
continua recebendo, então a leitura mais conservadora ficar em primeiro é
também a escolha mais segura de preservar como comportamento herdado).
`motivo` continua sendo o `tipo` do candidato primário (ou o motivo negativo
de sempre quando `candidatos` está vazia) — nenhuma mudança de contrato para
quem só lê `motivo`.

**Por que isto preserva TODO consumidor existente sem tocar:** `AtivoCard`
(Watchlist/Radar, Fase 14), `PropostaLastreada`/`PropostaDaPosicao`/
`OportunidadesOpcoes` (Fase 17/18), a rota `GET /api/options/proposta/
{ticker}` (que só repassa o dict de `propor()` — linha `"proposta":
resultado["proposta"]` em `main.py`), e a rota `POST .../abrir` (que nem
olha pra `propor()`) — nenhum precisa mudar UMA linha. Só a UI NOVA desta
fase (que lista `candidatos`) e a rota `abrir-collar` (que precisa parar de
assumir "motivo da proposta única == collar") precisam de código novo.

### MULTI-02 — UI: N candidatos lado a lado

Extensão de `PropostaDaPosicao` (`web/src/App.jsx:3992-4060`, Fase 18):
quando `r.candidatos.length > 1`, renderizar os N candidatos lado a lado
(mesmo padrão de card/scroll horizontal já usado por `OportunidadesOpcoes`,
Fase 18, `web/src/App.jsx:3934-3980` — reusar o mesmo estilo de item, não
inventar um terceiro padrão visual nesta fase). Quando `r.candidatos.length
<= 1`, o comportamento é o de hoje sem mudança visual (card único da Fase
17/18) — cumpre a Success Criterion 4 do ROADMAP ("nenhuma regressão pra
posições com um candidato só") por construção, não por caso especial extra.
Cada candidato mostra sua PRÓPRIA manchete verbatim (guardrail CVM —
`pr.manchete`, nunca composta) e seu próprio payoff (`estrutura`), igual ao
card de hoje.

Aceite: cada candidato tem seu próprio CTA, indo pra `A.abrirLastreada`
(candidatos `call_coberta`/`put_protecao`) ou `A.abrirCollar` (candidato
`collar`) — MESMAS duas funções já usadas por `PropostaDaPosicao` hoje
(`web/src/App.jsx:4015-4037`), só parametrizadas pelo candidato clicado em
vez do único `r.proposta` de hoje. Nenhuma função de store nova.

**Guarda "aceitar um não deixa aceitar outro pra mesma posição" (MULTI-02,
critério 3):** não precisa de guarda NOVA de código — já é estrutural.
`store.abrir_call_coberta`/`comprar_put_protecao`/`abrir_collar` validam
lastro/caixa DE NOVO sob `ORDER_LOCK` no momento da execução (não confiam no
que a proposta exibida disse); se o candidato A consumiu o lastro livre ou o
caixa que o candidato B também precisava, a tentativa de abrir B falha na
validação de sempre (mensagem de erro já existente, não uma nova). O plano
desta fase deve ter um teste que PROVA isso (abrir um candidato, tentar
abrir o outro na mesma posição, esperar rejeição) — não implementar uma
trava nova onde a trava de sempre já resolve.

### Claude's Discretion

- Nome exato de variáveis internas em `propor()` pra montar a lista de
  candidatos (loop, list comprehension, etc.) — implementação, não produto.
- Se `PropostaDaPosicao` ganha um sub-componente novo pro item de candidato
  (`CandidatoOpcao` ou equivalente) ou se o JSX fica inline — mesma
  discricionariedade já usada nas Fases 17/18, seguir o padrão visual
  existente (pills, `T.bgBase`, mono pra número).
- Mensagem de erro exata quando a segunda aceitação falha por lastro/caixa
  já consumido — reusar a mensagem que `ValueError` de
  `abrir_call_coberta`/`comprar_put_protecao`/`abrir_collar` já produz
  (não inventar texto novo).
- Cobertura de teste do front — `web/tests/*.mjs`
  (`scripts/executar.sh --testes` roda as DUAS suítes); qualquer mudança em
  `web/src/App.jsx` PRECISA rodar `npx vite build` antes de declarar pronto
  (guardrail do CLAUDE.md do projeto).
- Cobertura de teste do backend — `server/tests/test_opcoes_*.py` já tem
  guardiões de VENDER→put/collar isolados (Fase 14/16); este plano precisa
  de um teste NOVO que prova os DOIS candidatos coexistindo quando ambos
  cabem no caixa, e um teste que prova `abrir-collar` aceitando um collar
  que NÃO é o candidato primário da lista.

</decisions>

<specifics>
## Specific Ideas

Nenhuma além do que está em `<decisions>` — este plano nasceu de leitura de
código real (`opcoes_lastreadas.py`, `main.py`), não de mockup.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Motor a estender
- `server/app/opcoes_lastreadas.py:158-335` — `propor()`, o branch de
  decisão (linhas 198-212) e o ponto exato onde o collar é tentado hoje
  (linhas 246-263).
- `server/app/opcoes_lastreadas.py:41-155` — `_propor_collar()`, já aceita
  `contrato_put` pronto por parâmetro (não reseleciona).
- `server/app/opcoes_motor.py` — `rastrear()`/`avaliar()` (Fase 15,
  verificada, NÃO tocar).

### Rotas a estender
- `server/app/main.py:2506-2595` — `POST /api/options/lastreada/abrir-collar`
  — checagem `resultado.get("motivo") != "collar"` (linha 2583) PRECISA
  mudar pra procurar dentro de `candidatos`.
- `server/app/main.py:2429-2482` — `POST /api/options/lastreada/abrir` —
  confirmado que NÃO precisa mudar (não consulta `propor()`).
- `server/app/main.py:2348-2422` — `GET /api/options/proposta/{ticker}` —
  só repassa o dict de `propor()`; ganha `candidatos` automaticamente por
  já devolver `resultado` quase inteiro (conferir se o dict de retorno
  precisa de uma chave nova explícita pra `candidatos`, hoje só repassa
  `proposta`/`motivo`/`motivoTexto`).

### Frontend a estender
- `web/src/App.jsx:3992-4060` — `PropostaDaPosicao` (Fase 18).
- `web/src/App.jsx:3919-3981` — `OportunidadesOpcoes` (Fase 18, padrão
  visual de card/scroll a reusar).
- `web/src/App.jsx:4072-4127` — `useOpcoesPropostas` (Fase 18, hook de
  fan-out — não precisa mudar, só passa a carregar um payload maior).
- `web/src/App.jsx:3006-3062` (aprox.) — `PropostaLastreada`, assinatura
  congelada, não mexer.

### Decisão de escopo e requirements
- `.planning/REQUIREMENTS.md` — MULTI-01/02.
- `.planning/ROADMAP.md` — seção Phase 19.
- `.planning/STATE.md` — nota sobre a Fase 18 ainda não fechada (risco
  herdado se esta fase chegar a publicar).
- `docs/adr/025-collar-e-estrutura-multiperna.md`,
  `docs/adr/026-execucao-de-estrutura-multiperna.md` — a re-derivação que
  esta fase precisa generalizar de "um resultado" pra "lista de
  candidatos".

</canonical_refs>

<deferred>
## Deferred Ideas

- Publicação (bump/publicar-web.sh) e checkpoint humano desta fase — se o
  planner incluir isso como último plano (mesmo padrão de 17-06/18-05),
  sinalizar explicitamente que herda o risco da Fase 18 ainda não fechada
  (ver ROADMAP.md Phase 19 "Depends on").
- Setup customizado pelo usuário, estruturas além das 3 do v1 — fora do
  milestone (REQUIREMENTS.md Future Requirements).
- Integração MCP real (Estratégia C) — condicionada à aprovação externa,
  não relacionada a esta fase.

</deferred>

---

*Phase: 19-motor-multi-candidato*
*Context gathered: 2026-09-03 via síntese manual (leitura de código real, sem discuss-phase)*
