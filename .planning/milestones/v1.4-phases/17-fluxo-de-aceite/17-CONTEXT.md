# Phase 17: Fluxo de aceite - Context

**Gathered:** 2026-09-02
**Status:** Ready for planning
**Source:** Síntese manual, autonomia concedida pelo Alex. Uma decisão de escopo
real foi tomada aqui (ver seção própria) — o código da Fase 16 deixou um
comentário explícito dizendo que o collar "continua sem caminho de EXECUÇÃO
até a Fase 17" e que a trava atual do 16-04 é provisória até esta fase.

<domain>
## Phase Boundary

Cobre FLOW-01..04: exibir a proposta completa (incluindo os campos de
payoff que a Fase 16 já calcula), fluxo de aceite/recusa explícito, execução
via `store.py`, e frescor do dado sempre declarado. Isso inclui — não é
opcional, é o que a própria Fase 16 deixou pendente — abrir a execução real
de 2 pernas do collar, porque hoje ele só é PROPOSTO, nunca EXECUTADO
(bloqueado por design em `main.py:2445-2456`, comentário explícito
apontando pra esta fase).

</domain>

<decisions>
## Implementation Decisions

### Estado real do código a estender

`web/src/App.jsx:3006-3062` — `PropostaLastreada` (componente já existe,
Fase 14): mostra `manchete`/`didatica`/`chips`, um único CTA
(`onAbrir`/`onFechar`), degrada por `providerStatus`. NÃO exibe os campos
novos que a Fase 16 adicionou ao dict `proposta` (payoff/estrutura/caixa) —
FLOW-01 pede exatamente isso.

`server/app/main.py:2348-2422` — `GET /api/options/proposta/{ticker}`: já
aceita — confirmar exatamente como foi ligado no Plano 16-04 — o parâmetro
de negociação de capacidade (`multiperna`) que decide se o collar é
oferecido. Ler o Plano `16-04-PLAN.md`/`16-04-SUMMARY.md` pra saber o nome
exato do parâmetro e onde ele mora antes de estender a rota.

`server/app/main.py:2430-2482` — `POST /api/options/lastreada/abrir`: hoje
executa SÓ 1 perna (`store.abrir_call_coberta` ou
`store.comprar_put_protecao`). Tem uma trava de 400 explícita (Fase 16,
Plano 04) que recusa QUALQUER corpo de requisição com `tipo=="collar"` ou
mais de 1 perna em `pernasContratos` — essa trava fica intocada; **não
remover, não enfraquecer**. Esta fase cria uma rota NOVA (ou uma extensão
explícita e claramente distinta, nunca reaproveitando a mesma rota sem essa
trava) para executar o collar de verdade.

`server/app/store.py:886` — `abrir_call_coberta(conn, contract, contratos,
price, user_id, meta, origem)`: leitura da posição + validação + escrita
inteiras dentro de UMA aquisição de `ORDER_LOCK` — é o padrão de atomicidade
que qualquer execução nova tem que seguir.
`server/app/store.py:1021` — `comprar_put_protecao`, mesmo padrão.

### FLOW-01 — exibir payoff completo

`PropostaLastreada` (ou um componente novo que ele passa a usar) precisa
mostrar os campos de `estrutura`/`caixa` que a Fase 16 adicionou ao dict
`proposta` (ver `16-01-SUMMARY.md`/`16-03-SUMMARY.md` pros nomes exatos de
campo — não inventar nome novo, usar o que o motor já produz). Pelo menos:
ganho máximo, perda máxima, breakeven(s). `null` explícito quando o motor
não calcula um valor (ex.: ganho ilimitado na put de proteção) — nunca `0`
no lugar de "não aplicável" (regra já vigente no projeto, guardião
`test_m3_format_pede_null_nunca_zero` é o precedente de estilo, mesmo que
seja de outro domínio).

### FLOW-02 — aceite/recusa explícito

Já existe estruturalmente: o CTA (`onAbrir`) só executa quando clicado,
Modo Estudo nunca mostra CTA de execução (`!operador` → só `didatica`, sem
botão). "Recusar" é a ausência de clique — não é preciso inventar um botão
de recusa distinto, a menos que o planner identifique um caso real onde
isso muda o comportamento observável. Não inventar UI nova sem necessidade.

### FLOW-03 — execução real do collar (decisão de escopo desta sessão)

**Decisão, com autonomia concedida:** esta fase constrói a execução de
verdade do collar, não deixa a "trava vazia" da Fase 16 como estado final
do milestone. Racional: LIB-03 já entrega a proposta completa (as 2 pernas,
o payoff); uma feature que propõe mas nunca deixa aceitar é escopo
inacabado, e o próprio código (comentário em `main.py`) já aponta essa fase
como a dona da lacuna.

Desenho mínimo:
- Nova função `store.abrir_collar(conn, contract_call, contract_put,
  contratos, premio_call, premio_put, user_id, ...)` (nome exato a critério
  do planner) — chama a MESMA validação de lastro/caixa que
  `abrir_call_coberta`/`comprar_put_protecao` já fazem, mas dentro de UMA
  aquisição de `ORDER_LOCK` cobrindo as DUAS pernas: valida as duas ANTES de
  escrever qualquer uma, escreve as duas ou nenhuma. Isso é o mesmo
  princípio de "tudo-ou-nada" que já é invariante do produto (CLAUDE.md:
  "execução tudo-ou-nada por desenho... não implementar fill parcial") —
  aqui aplicado a nível de ESTRUTURA (2 pernas), não só de ordem única.
- Rota nova (`POST /api/options/lastreada/abrir-collar` ou nome equivalente
  claro) — NUNCA reaproveitar `/abrir` sem a trava de 16-04, que continua
  ativa e intocada nessa rota antiga.

### Endurecimento da trava — item sinalizado pelo plan-checker da Fase 16

O `docs/adr/025-collar-e-estrutura-multiperna.md` documenta explicitamente:
a trava de 400 do 16-04 confia no `tipo`/`pernasContratos` que o PRÓPRIO
CLIENTE declara no corpo da requisição — não há re-derivação server-side.
Isso foi aceitável na Fase 16 porque nenhum cliente real submetia
`multiperna=1`. **Esta fase é exatamente onde isso deixa de ser verdade** —
o cliente que esta fase constrói vai submeter propostas de collar de
verdade. Portanto, a rota NOVA de abertura de collar desta fase (FLOW-03)
precisa RE-DERIVAR a proposta no servidor (chamar
`opcoes_lastreadas.propor(..., multiperna=True)` de novo, com
posicao/plano/caixa atuais) e cruzar os `contractSymbol` submetidos contra
essa proposta fresca — não aceitar cegamente o que o corpo da requisição
diz que é. Isso fecha a limitação que o ADR-025 já deixou documentada como
pendência — não é decisão nova, é a decisão que faltava implementar.

### FLOW-04 — frescor sempre declarado

`r.providerStatus` já existe e já é checado no front (`degradado`). Conferir
se isso é suficiente pro requirement ("declara a fonte e o horário do dado")
ou se falta expor um timestamp explícito — ler `check_data_freshness`/
equivalente do motor (se existir consumo já pronto em outro card do app,
tipo `FonteDadosScreen`, reusar o mesmo padrão em vez de inventar um novo).

### Claude's Discretion

- Se `PropostaLastreada` ganha um sub-componente novo pros campos de payoff
  ou se os campos entram inline — decisão de UI, seguir o estilo visual já
  usado nos `chips` existentes (pills, `T.bgBase`, mono pra número).
- Nome exato da rota/função de abertura de collar.
- Cobertura de teste do front — este projeto tem `web/tests/*.mjs`
  (`scripts/executar.sh --testes` roda as DUAS suítes); qualquer mudança em
  `web/src/App.jsx` PRECISA rodar `npx vite build` antes de declarar pronto
  (guardrail do CLAUDE.md do projeto — grep/teste estático não pega erro de
  sintaxe JS).

</decisions>

<specifics>
## Specific Ideas

Nenhuma além do que está em `<decisions>`.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Frontend a estender
- `web/src/App.jsx:3006-3062` — `PropostaLastreada`.
- `web/src/copy.js` — vocabulário de UI por modo (`cp.eyebrowPropostaCall`,
  `cp.ctaVendaCoberta`, etc.) — qualquer texto novo de UI (não manchete —
  manchete é do motor) segue esse padrão, nunca hardcoded no componente.

### Backend a estender
- `server/app/main.py:2348-2422` — rota GET da proposta (parâmetro
  `multiperna`, ligado no Plano 16-04).
- `server/app/main.py:2430-2482` — rota POST de abertura single-leg (trava
  de 400 intocada).
- `server/app/store.py:886,1021` — `abrir_call_coberta`/
  `comprar_put_protecao`, padrão de `ORDER_LOCK` a replicar pro collar.
- `docs/adr/025-collar-e-estrutura-multiperna.md` — limitação da trava
  documentada, esta fase é quem fecha.

### Decisão de escopo e requirements
- `.planning/REQUIREMENTS.md` — FLOW-01..04.
- `.planning/phases/16-biblioteca-de-estruturas/16-04-SUMMARY.md` — nomes
  exatos de campo em `proposta` (estrutura/caixa/payoff) e do parâmetro
  `multiperna`.
- `.planning/phases/16-biblioteca-de-estruturas/16-VERIFICATION.md` — o que
  a Fase 16 de fato entregou (evidência real).

</canonical_refs>

<deferred>
## Deferred Ideas

- Aba de navegação — Fase 18.
- Estruturas adicionais além das 3 do v1 — fora do milestone.

</deferred>

---

*Phase: 17-fluxo-de-aceite*
*Context gathered: 2026-09-02 via síntese manual (sem discuss-phase, autonomia concedida)*
