# Phase 16: Biblioteca de estruturas - Context

**Gathered:** 2026-09-02
**Status:** Ready for planning
**Source:** Síntese manual, sem `/gsd-discuss-phase` — decisões de escopo (venda
coberta + put + collar) já fechadas na exploração desta sessão. Uma decisão de
produto nova (quando propor collar) foi tomada aqui, com autonomia concedida
pelo Alex ("seguir direto e com autonomia para aprovar as decisões") — está
marcada explicitamente como julgamento, não fato herdado.

<domain>
## Phase Boundary

Migrar venda coberta e put de proteção do motor single-leg (`propor()`,
Fase 14) para o motor comum de N-pernas da Fase 15 (`opcoes_motor.rastrear`/
`avaliar`), e adicionar collar como nova composição de 2 pernas sobre a
mesma posição. Cobre LIB-01, LIB-02, LIB-03. Sem UI (Fase 18), sem fluxo de
aceite novo (Fase 17 usa o que esta fase produzir).

</domain>

<decisions>
## Implementation Decisions

### Estado real do código a estender (ler antes de planejar)

`server/app/opcoes_lastreadas.py:62-149` — `propor(underlying, chain, spot,
plano, posicao, cash, modo, hoje)` é a função inteira a generalizar. Hoje:

1. Valida `chain`/`posicao` (curto-circuita em `degradado`/`sem_lastro`).
2. Decide `tipo` a partir de `plano.decisao`/`plano.lado`:
   - `VENDER` ou `lado=="baixa"` → `put_protecao`
   - `AGUARDAR CONFIRMAÇÃO`/`NÃO OPERAR` ou `lado=="neutro"` → `call_coberta`
   - `COMPRAR`/`lado=="alta"` → `sem_setup` (não propõe nada)
3. Filtra candidatos por janela de prazo (`_PRAZO_MIN_DIAS`/`_PRAZO_MAX_DIAS`).
4. Escolhe contrato — **hoje via `_escolher_contrato`/`_candidato_valido`
   locais; a Fase 15 já rebindou `_LIQUIDEZ_MINIMA` pra
   `opcoes_motor.LIQUIDEZ_MINIMA`, mas a função de escolha em si ainda não
   chama `opcoes_motor.rastrear()`.** Esta fase troca isso.
5. Calcula `contratos`/`premioTotal` ad-hoc (sem usar `opcoes_payoff`).
6. Monta `proposta` com `manchete`/`didatica`/`chips` via
   `skill_ref.opcoes_lastreadas_txt(modo, tipo, **dados)`.

`server/app/opcoes_motor.py` (Fase 15, já em produção neste repo):
- `rastrear(cadeia, filtros) -> [contratos]` — screening por liquidez
  (`LIQUIDEZ_MINIMA = 40`).
- `perna_de_contrato(contrato, lado, quantidade=1)` / `perna_de_acao(ticker,
  preco, quantidade)` — adaptadores pro formato de perna.
- `avaliar(pernas) -> {...}` — delega pra
  `opcoes_payoff.perfil_da_estrutura()`.

`server/app/opcoes_payoff.py` (Fase 15):
- `perfil_da_estrutura(pernas) -> dict` — devolve custo líquido, ganho/perda
  máximos, breakevens, delta somado. Esta é a fonte dos campos que
  `propor()` NÃO calcula hoje (FLOW-01 do REQUIREMENTS pede exatamente isso
  na proposta exibida — construir esses campos é trabalho desta fase, não
  da Fase 17, que só exibe o que já estiver no dict).

`server/app/skill_ref.py:513-556` — `OPCOES_LASTREADAS` (dict por modo
operador/educacional, chave por `tipo`) e `opcoes_lastreadas_txt(modo,
chave, **dados)`. Único lugar onde a manchete nasce (guardrail CVM — front
nunca compõe). Collar precisa de uma entrada nova nos dois modos, mesmo
padrão de interpolação `{...}`.

### LIB-01 / LIB-02 — migração pro motor comum

`propor()` passa a montar as `pernas` via `opcoes_motor.perna_de_contrato()`
(pra a opção) — a `opcoes_motor.perna_de_acao()` só é necessária se o
payoff precisar incluir a posição em ações no cálculo de ganho/perda; avaliar
com o time se isso é preciso pro breakeven fazer sentido pro usuário (uma
venda coberta sem a posição-lastro no payoff mostra só o resultado da perna
de opção isolada, não da estrutura completa "ação + opção" — decisão de
implementação do planner, documentar a escolha na SUMMARY). A escolha de
contrato passa a vir de `opcoes_motor.rastrear(chain, filtros)` — **mesma
régua de liquidez, agora pela função compartilhada**, não mais pela lógica
duplicada `_escolher_contrato`/`_candidato_valido` locais (que podem ser
removidas se `rastrear()` cobrir o mesmo comportamento, ou mantidas como
wrapper fino — decisão do planner, desde que não haja DUAS implementações
divergentes da mesma régua no arquivo).

O resultado de `opcoes_motor.avaliar(pernas)` (custo, ganho_max, perda_max,
breakevens, delta) entra no dict `proposta` como campos novos, aditivos —
não remover `premioTotal`/`chips` existentes, que a Fase 17/18 e o
`14-UI-SPEC.md` já pressupõem.

### LIB-03 — collar (trava protetora), estrutura nova

Duas pernas sobre a mesma posição: vender 1 call OTM (mesma seleção que
`call_coberta` já faz — `strike > spot`, liquidez ≥ 40) + comprar 1 put
(mesma seleção que `put_protecao` já faz — `strike <= spot`, liquidez ≥ 40),
mesmo vencimento elegível. `avaliar()` recebe as duas pernas juntas — é
exatamente o caso de uso que `opcoes_payoff.perfil_da_estrutura` foi
desenhado pra suportar desde a Fase 15 (N pernas, não só 1).

**Decisão de produto tomada nesta sessão, com autonomia concedida — quando
propor collar em vez de put_protecao isolado:** quando `decisao == VENDER`
(a leitura técnica já pede proteção) **e** a put de proteção isolada seria
rejeitada por `caixa_insuficiente` (linha ~103 de `opcoes_lastreadas.py`,
`contratos < 1` após o corte por caixa). Racional: collar é uma forma de
financiar a proteção com o prêmio da call vendida — faz sentido oferecê-lo
exatamente onde a put pura já não cabe no caixa disponível, em vez de só
devolver "caixa insuficiente" sem alternativa. Isso é julgamento de produto,
não fato herdado de nenhuma decisão anterior — se não fizer sentido na
prática, é reversível numa fase futura sem mexer no motor (só na regra de
`propor()` que decide QUANDO oferecer qual tipo).

Vocabulário novo em `skill_ref.py` — adicionar chave `"collar"` em
`OPCOES_LASTREADAS["operador"]` e `["educacional"]`, mesmo padrão de frase
com `{...}` interpolados (ex.: operador — "Vender {n} call(s) de {ticker}
strike {strikeCall} e comprar {n} put(s) strike {strikePut} — trava
protetora financiada pelo prêmio da call."; adaptar aos dados reais que a
estrutura de 2 pernas produzir). `didatica` no mesmo padrão condicional
("Se você tivesse montado esta trava protetora agora...").

### Claude's Discretion

- Se `propor()` continua sendo uma função só ou vira um dispatcher fino
  chamando 3 funções internas (`_propor_call_coberta`, `_propor_put_protecao`,
  `_propor_collar`) — o planner decide pelo tamanho real do diff.
- Formato exato dos novos campos de payoff dentro do dict `proposta` (nomes
  de chave) — seguir o vocabulário que `opcoes_payoff.perfil_da_estrutura()`
  já usa como saída, não inventar um novo.
- Cobertura de teste — mesmo padrão `server/tests/test_<feature>.py` já
  estabelecido; a Fase 15 deixou `test_opcoes_motor.py`/`test_opcoes_payoff.py`
  como referência de estilo.

</decisions>

<specifics>
## Specific Ideas

Nenhuma além do que está em `<decisions>`.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Motor da Fase 15 (já em produção, não redesenhar)
- `server/app/opcoes_motor.py` — `rastrear()`, `avaliar()`,
  `perna_de_contrato()`, `perna_de_acao()`, `LIQUIDEZ_MINIMA`.
- `server/app/opcoes_payoff.py` — `perfil_da_estrutura()` (custo, ganho/perda
  máximos, breakevens, delta).
- `docs/adr/024-limite-interno-rastrear-avaliar.md` — racional do limite
  interno que esta fase passa a consumir de verdade.

### Código a migrar
- `server/app/opcoes_lastreadas.py` — `propor()` e as funções privadas que
  ela usa hoje (`_escolher_contrato`, `_candidato_valido`, `_dias_ate`,
  `_label_liquidez`).
- `server/app/skill_ref.py:513-556` — `OPCOES_LASTREADAS`,
  `opcoes_lastreadas_txt()`.

### Requirements e decisão de escopo
- `.planning/REQUIREMENTS.md` — LIB-01, LIB-02, LIB-03.
- `.planning/notes/opcoes-v2-b-mcp-exploracao.md` — racional de por que
  collar entrou no v1 (mesmas 2 pernas já calculadas) e por que
  straddle/cash-secured put ficaram fora.
- `.planning/phases/15-motor-de-proposta-arquitetura-interna/15-VERIFICATION.md`
  — confirma o que a Fase 15 entregou de fato (evidência real, não prosa).

</canonical_refs>

<deferred>
## Deferred Ideas

- Exibição da proposta e fluxo de aceite — Fase 17.
- Aba de navegação — Fase 18.
- Revisitar a regra de "quando propor collar" se, na prática (Fase 17/18 em
  uso), o gatilho por `caixa_insuficiente` não capturar os casos que fariam
  sentido pro usuário — não é uma decisão irreversível.

</deferred>

---

*Phase: 16-biblioteca-de-estruturas*
*Context gathered: 2026-09-02 via síntese manual (sem discuss-phase, autonomia concedida)*
