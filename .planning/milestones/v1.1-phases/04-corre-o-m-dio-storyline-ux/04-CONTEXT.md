# Phase 4: Correção Médio — Storyline & UX — Context

**Gathered:** 2026-08-21
**Status:** Ready for planning
**Source:** REQUIREMENTS.md (FIX-C01..C05, FIX-C13..C16) + ROADMAP.md (Goal/Success Criteria, já definidos na criação do roadmap v1.1, 2026-08-18) + evidência original de
`.planning/milestones/v1.0-phases/01-auditoria-diagn-stica-consolidada/REPORT-01.md` (achados C-01 a C-05 — STORY, linhas 302-340 — e C-13 a C-16 — UX, linhas 435-465).

**Aviso de idade da evidência**: as citações `arquivo:linha` abaixo são do
momento da auditoria (2026-08-18), ANTES das Fases 2, 3, 6, 7 e 8 — `App.jsx`
em particular cresceu bastante desde então (Phase 8 sozinha adicionou
`HistoricoPill` e novas linhas de transparência). Re-grep obrigatório em
tempo de planejamento/execução, não confiar no número da linha.

<domain>
## Phase Boundary

Fecha 9 achados Médio do REPORT-01 (v1.0, fechado 2026-08-18) que nunca
tiveram fase própria: 5 STORY (lacunas pedagógicas que atacam direto o Core
Value — "sai entendendo de verdade, não decorou resposta") e 4 UX
(experiência/acessibilidade). Nenhum dos 9 é novo — são risco silencioso
documentado há mais de um mês, represado atrás das Fases 6/7/8 (que vieram de
pesquisa ad-hoc sobre o motor de recomendação, não deste backlog).

</domain>

<decisions>
## Implementation Decisions

### STORY — lacunas pedagógicas

**C-01 — Passo 7 sem fallback determinístico quando a IA está indisponível.**
`POST /api/analyze/{ticker}` e `POST /api/technical/analyze/{ticker}`
(`server/app/main.py`, ~1218/1362 na auditoria) devolvem `HTTP 502
{"code":"missing_key"}` quando não há chave BYOK nem cota gerenciada — o
usuário grátis sem chave nunca recebe NENHUMA explicação após operar.
**Decidido**: quando a IA não estiver disponível, montar uma explicação
mínima determinística a partir do setup/indicador já calculado, usando
`server/app/conceitos.py`/`server/app/kb.py` (fonte já existente de
verbetes 0-custo) — nunca um card vazio ou só o erro técnico.

**C-02 — Ordem rejeitada não deixa rastro.** `/api/buy`/`/api/sell`
(`main.py`, ~1501-1535 na auditoria) devolvem `HTTPException` sem persistir a
tentativa — `history[0]` de uma compra bem-sucedida não tem campo `status`.
**Decidido**: toda tentativa de ordem (aceita OU rejeitada) grava `status`
(`executada`/`rejeitada`) e `motivo`, mesmo sem abrir posição — o caso mais
educativo (estourou risco, caixa insuficiente) precisa ficar revisável no
histórico.

**C-03 — Passo 8 sem comparação com benchmark real.** `equityCurve`
(`web/src/finance.js`, ~56-93 na auditoria) calcula `retAcum`/`drawdown` só
sobre a própria carteira; comentário em `App.jsx` já confirma a ausência
como intencional na época. **Decidido**: adicionar série de retorno do
Ibovespa (mesmo provedor Yahoo já em uso — ver `server/app/yahoo.py`),
exibida lado a lado com o retorno da carteira simulada no Passo 8. Sem essa
referência o usuário leigo não consegue avaliar se o resultado foi bom ou
ruim — exatamente o raciocínio que o Core Value promete ensinar.

**C-04 — Transição Estudo→Operador só tem critério legal.** O único gate
hoje é `!c.operadorTermo` (`App.jsx` ~1832 na auditoria, espelhado em
`server/app/store.py` ~235-239) — testado ao vivo: `PUT /api/config` com
`{"appMode":"operador"}` sozinho foi SILENCIOSAMENTE ignorado, só mudou com
`operadorTermo` junto. Nenhum campo de progresso pedagógico é consultado.
**Decidido**: critério mínimo de prontidão SOFT (aviso, não bloqueio duro —
ex.: "você ainda não fez nenhuma análise no Estudo, tem certeza que quer
ativar o Operador?"), não um novo gate duro que impediria acesso. A
recomendação original do REPORT-01 já qualifica isso como "mesmo que soft".

**C-05 — "Diversificação" ausente do produto.** Zero ocorrência de
"diversific" em `server/app/*.py`/`web/src/*.js`/`web/src/*.jsx`/`docs/*.md`
— nem verbete em `kb.py`, nem aviso na tela de Carteira. Um dos 13 conceitos
obrigatórios da seção "Camada educacional" do `CLAUDE.md` do repo nunca é
ensinado. **Decidido**: verbete novo em `server/app/kb.py` (mesmo padrão dos
demais, ex. `setup-ifr2`) + aviso na tela de Carteira quando a concentração
num único ativo passar de 50% do patrimônio.

### UX

**C-13 — Disclaimer de operação simulada nunca renderiza no momento da
decisão.** `DISCLAIMERS.trade` existe (`web/src/disclaimers.js` ~24-26:
"Nenhuma ordem real é enviada a uma corretora") mas nenhuma das ocorrências
de `DISCLAIMERS.` em `App.jsx` usa `.trade`; `BuyModal` só mostra o rótulo
curto "COMPRA SIMULADA". **Decidido**: renderizar `DISCLAIMERS.trade` no
`BuyModal`/`SellModal`, perto do botão de confirmação — no instante de maior
atenção do usuário, a garantia explícita precisa estar na tela, não só em
outros pontos.

**C-14 — "Ordem parcialmente executada" não existe no modelo de dados.**
`store.buy`/`store.sell` executam 100% ou rejeitam inteiro — não há caminho
de API pra provocar esse estado porque ele estruturalmente não existe.
**Decidido** (per Success Criteria do ROADMAP, já fechado): NÃO implementar
fill parcial. Declarar formalmente, em copy/doc, que a simulação é
"tudo-ou-nada" por desenho — defensável pelo princípio 5 do CLAUDE.md
(cálculo determinístico). Onde documentar: `CLAUDE.md` (seção "Modelo de
simulação") e/ou um texto visível na tela de Carteira/histórico, a critério
do planejamento — não inventar um estado que o motor nunca produz.

**C-15 — Toggle "acordeão" não responde a teclado.**
`<div onClick={onToggle} role="button" tabIndex={0}>` (`App.jsx` ~2706,2773
na auditoria) sem `onKeyDown`/`onKeyPress` — usuário por teclado/leitor de
tela foca mas não consegue ativar. **Decidido**: trocar por `<button>`
nativo OU adicionar `onKeyDown={(e) => (e.key === "Enter" || e.key === " ")
&& onToggle()}` em todo ponto que usa esse padrão (re-grep obrigatório, mais
de um ponto de uso na auditoria original).

**C-16 — `textFaint` abaixo do contraste WCAG AA.** `textFaint: "#6f7797"`
(tema escuro) sobre `bgBase: "#10121a"` = 4.24:1; `textFaint: "#7a8099"`
(tema claro) sobre `bgBase: "#f7f8fc"` = 3.68:1 — mínimo AA pra texto normal
é 4.5:1 (`web/src/App.jsx` ~70,87 na auditoria, tema em `T`/`P`). Usado em
rótulos de fonte, timestamps, disclaimers auxiliares, mensagens de erro
secundárias. **Decidido**: escurecer/clarear `textFaint` até ≥4.5:1 nos DOIS
temas, OU reservar a cor a texto ≥14px em negrito (WCAG permite contraste
menor pra texto grande) — decisão de qual caminho fica pro UI-SPEC, mas o
resultado final tem que passar 4.5:1 real, calculado a partir dos hex
finais, não estimado.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Evidência original (fonte primária de cada achado)
- `.planning/milestones/v1.0-phases/01-auditoria-diagn-stica-consolidada/REPORT-01.md` linhas 302-340 (C-01..C-05, STORY) e 435-465 (C-13..C-16, UX) — evidência, impacto e recomendação originais de cada achado, testados ao vivo onde indicado.

### Backend
- `server/app/main.py` — rotas `/api/analyze/{ticker}`, `/api/technical/analyze/{ticker}` (C-01), `/api/buy`, `/api/sell` (C-02).
- `server/app/conceitos.py`, `server/app/kb.py` — fonte de verbetes determinísticos 0-custo, padrão a seguir pro fallback do C-01 e o verbete novo do C-05.
- `server/app/store.py` — `buy()`/`sell()` (C-02, C-14), trava de `operadorTermo` (C-04).
- `server/app/yahoo.py` — provedor já usado, mesmo padrão pro benchmark Ibovespa do C-03.
- `CLAUDE.md` (raiz do repo) — seção "Modelo de simulação" (C-14, onde declarar tudo-ou-nada), "Camada educacional" (lista dos 13 conceitos obrigatórios, C-05).

### Frontend
- `web/src/finance.js` — `equityCurve` (C-03, onde entra a série do Ibovespa).
- `web/src/disclaimers.js` — `DISCLAIMERS.trade` (C-13, já existe, só não é renderizado).
- `web/src/App.jsx` — `BuyModal`/`SellModal` (C-13), toggle de acordeão (C-15, mais de um ponto de uso — re-grep), tema `T`/`P` e `textFaint` (C-16), gate `operadorTermo` (C-04).

### Padrão de guardião a seguir
- Todo achado corrigido precisa de teste que trava o comportamento (regra da casa, CLAUDE.md "Validação obrigatória") — `server/tests/` pro backend, `web/tests/*.mjs` pro front, suíte canônica `bash scripts/executar.sh --testes`.

</canonical_refs>

<specifics>
## Specific Ideas

- C-01 e C-05 reusam a MESMA fonte determinística (`conceitos.py`/`kb.py`) —
  pode fazer sentido planejar os dois no mesmo plano/wave se tocarem o mesmo
  arquivo.
- C-13 (disclaimer no modal) e C-15 (acordeão) e C-16 (contraste) são só
  frontend, sem risco de tocar `regime.py`/`setups.py`/backend financeiro —
  candidatos a wave paralela com C-01/C-02 (backend).
- C-16 precisa de UI-SPEC com os valores hex finais calculados e o cálculo
  de contraste anotado (não "escureci até parecer melhor") — dimensão Color
  do checker vai exigir isso.

</specifics>

<deferred>
## Deferred Ideas

- C-06 a C-10 e C-17/C-18 (achados Baixo do REPORT-01) — explicitamente fora
  desta fase, backlog não mapeado (ver STATE.md "Deferred Items").
- Fill parcial de ordem de verdade (rejeitado em C-14 — decisão de produto
  já fechada no ROADMAP, não reabrir).
- Qualquer mudança de critério LEGAL de transição de modo (aceite de termo)
  — C-04 é só a camada pedagógica ADICIONAL, o gate legal continua.

</deferred>

<scope_fence>
## Scope Fence

**Dentro do escopo:** os 9 requirements FIX-C01, FIX-C02, FIX-C03, FIX-C04,
FIX-C05, FIX-C13, FIX-C14, FIX-C15, FIX-C16 — exatamente como descritos
acima, nada mais.

**Fora do escopo:**
- Fase 5 (CODE/GATE/ADMIN, FIX-C21..C39) — fase irmã, independente, não
  sequenciada por dependência técnica.
- Qualquer achado Baixo (C-06..C-10, C-17, C-18) — backlog, não esta fase.
- Mudança de critério legal de transição de modo.
- Implementação de fill parcial real (C-14 é só declaração de escopo,
  não feature nova).
- Motor de setups/seleção dinâmica (ADR-016/017) — sem relação com esta
  fase.

</scope_fence>

---

*Phase: 04-corre-o-m-dio-storyline-ux*
*Context gathered: 2026-08-21, a partir do REPORT-01 original (não houve discuss-phase — requirements e evidência já vinham completos do audit)*
