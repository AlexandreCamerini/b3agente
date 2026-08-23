# Phase 5: Correção Médio — Código, Gate & Admin — Context

**Gathered:** 2026-08-22
**Status:** Ready for planning
**Source:** REQUIREMENTS.md (FIX-C21..C27, C33, C34, C38, C39) + ROADMAP.md (Goal/Success Criteria, definidos na criação do roadmap v1.1, 2026-08-18) + evidência original de
`.planning/milestones/v1.0-phases/01-auditoria-diagn-stica-consolidada/REPORT-01.md` (C-21..C27 CODE, linhas 552-608; C-33/C-34 GATE, linhas 694-709; C-38/C-39 ADMIN, linhas 755-768).

**Aviso de idade da evidência**: citações `arquivo:linha` são do momento da
auditoria (2026-08-18) — `App.jsx` cresceu MUITO desde então (Fases 2, 3, 4,
8 todas o tocaram pesado; C-21 cita `App.jsx:7214`, hoje o arquivo passa de
8000 linhas). Re-grep obrigatório em tempo de planejamento/execução.

**Três codebases nesta fase**: `server/app/` (backend), `web/src/` (app
consumidor — C-21, C-22, C-23, C-25, C-26, C-33), `web-admin/src/` (portal
admin, projeto npm separado — C-38, C-39). C-24/C-27 são de processo/suíte,
sem código de produto.

<domain>
## Phase Boundary

Fecha os 11 achados Médio restantes do REPORT-01 que não são STORY/UX (esses
foram a Fase 4): dívida técnica de leitura de `appMode` (CODE), gate
comercial rodando com dado hardcoded (GATE), e dois pontos de observabilidade
do portal admin sem alerta preventivo/rótulo consistente (ADMIN). Diferente
da Fase 4, nenhum destes é lacuna pedagógica — são risco de regressão
silenciosa, gate que quebraria na hora errada, e portal que não avisa antes
do problema.

</domain>

<decisions>
## Implementation Decisions

### CODE — dívida técnica

**C-21 — 10 de 12 pontos de leitura de `appMode` recalculam de forma
independente, em vez de ler `ctx.operador`** (já existe desde 07/08).
`App.jsx:7214-7220` define `ctx.operador` com comentário "Novo código deve
ler `ctx.operador`", mas 10 leituras independentes (linhas 1624, 1828, 2018,
3188, 4224, 5606, 5756, 6319, 6501, 6862, 7411 na auditoria — 2 delas,
1828/6319, são a própria tela de troca/origem, sem risco real, re-verificar
quais das 10 restantes ainda existem e ainda leem direto).
**Decidido**: migrar os pontos de recomputação redundante pra ler
`ctx.operador` — mecânico, SEM mudança de comportamento (mesmo resultado,
uma fonte). Considerar um teste estático (regex, mesmo padrão dos guardiões
de paridade já existentes) que falhe se `data.config.appMode` for lido fora
de `App()`/`ctx.operador`, fechando a classe do erro, não só a instância.
Severidade confirmada Médio pelo Alex no checkpoint humano da Fase 1 (sem
incidente causado por esta divergência especificamente).

**C-22 — `default_skill_text()`/`defaultSkillText()` sem guardião de
paridade byte-exata**, diferente do par `carteiraStopAlvo*` que já é
travado. Evidência: `server/app/defaults.py:22`, `web/src/catalog.js:54`; o
guardião existente (`test_a8ii_paridade_defaults_carteira_com_catalog_js`)
só compara `carteiraStopAlvo*`; `test_copy_theme.mjs` só verifica presença
da substring, nem cobre a versão sem `Operador`.
**Decidido**: estender o guardião existente (ou criar par equivalente) pra
cobrir `default_skill_text`/`defaultSkillText` com comparação byte-exata,
mesmo padrão do par já protegido — o texto que define a persona/skill do
Modo Estudo pode divergir entre app nativo e servidor hoje sem detecção.

**C-23 — Toggle mestre "Entrada automática" sem atributo HTML `disabled`
real nem feedback próprio.** `App.jsx:3924` (auditoria) —
`<Toggle on={!!ag.entradaAuto && operador} onClick={() => operador &&
putAg(...)} .../>`; o componente `Toggle` não recebe/aplica prop `disabled`.
Comparar com os outros 2 controles gateados na mesma tela (botão Executar,
slider `allocPct`) que JÁ têm `disabled` HTML + parágrafo com link — o
Toggle é o único sem.
**Decidido**: aplicar `disabled={!operador}` no Toggle, mesmo padrão do
slider `allocPct` logo abaixo — uma linha, sem mudança de lógica de negócio
(o comportamento funcional já está correto, só falta o feedback visual).

**C-24 — Suíte web falha em checkout/worktree novo por `web/node_modules`
ausente**, não regressão — mas os 7 testes que falham incluem os guardiões
dos 2 incidentes de paridade já documentados (carteira nativa, sincronização
de `appMode`). Confirmado repetidamente nesta sessão (Fases 6, 7, 8, 4 todas
bateram nesse mesmo gap em worktree novo).
**Decidido**: documentar como pré-requisito operacional — `npm install` em
`web/` ANTES de `scripts/executar.sh --testes` em qualquer checkout novo.
Avaliar se cabe automatizar (ex.: o próprio `executar.sh` checar
`web/node_modules` e rodar `npm install` sozinho se ausente) — decisão de
planejamento, não travada aqui.

**C-25 — Rejeição de ordem em `/api/buy`/`/api/sell` sem teste de rota
HTTP.** 3 caminhos de rejeição (`400 Ticker invalido`, `502 Sem cotacao`,
`400 Caixa insuficiente`, `main.py:1502-1518` na auditoria); zero arquivo de
teste cobre qualquer um via `TestClient`.
**Decidido**: 2-3 testes `TestClient` (banco temporário, reimport de
`app.main` — mesmo padrão já usado no resto da suíte) cobrindo os 3
caminhos de rejeição.

**C-26 — Recompra após venda parcial sem teste da reponderação.**
`store.py:539` (auditoria) reponderação roda em toda compra que encontra
posição existente; existe teste pra venda parcial isolada, mas nenhuma
sequência `buy → sell parcial → buy` foi encontrada.
**Decidido**: teste `buy(100@30) → sell(qty=40) → buy(60@40)`, assert do
`avg` resultante = 35 (60 remanescentes a 30 + 60 novas a 40, NÃO a média
das 160 cotas originais — validar a conta exata contra `store.py` real
antes de fixar o assert).

**C-27 — Ausência de E2E/browser automation na suíte canônica.**
`TESTING.md` já documenta "E2E tests: not present"; recorrente no histórico
do projeto (memória registra bugs "que só a verificação ao vivo pegou").
**Decidido**: a recomendação original do REPORT-01 é "**avaliar** E2E leve
(Playwright/similar) para o roteiro dos 8 passos da Experiência Principal" —
não implementar uma suíte E2E completa nesta fase (isso seria escopo muito
maior que um achado Médio). O Success Criteria do ROADMAP diz "cobertura E2E
mínima... é avaliada" — avaliada, não necessariamente implementada. Produto
do plano pode ser uma decisão documentada (ADR curto ou nota no
TESTING.md) sobre se/quando adotar E2E, não obrigatoriamente código Playwright
novo. Se o planejamento decidir implementar algo mínimo, manter MUITO
restrito (ex.: 1 fluxo crítico) — não abrir escopo de infraestrutura de
teste nova sem necessidade clara.

### GATE — ativação incompleta

**C-33 — `can_add_ticker`/`can_analyze` chamados com dado hardcoded (`0`),
não a contagem real do mês do usuário.** `main.py:1370` (auditoria) —
`plan.can_analyze(0) # FUTURO: passar a contagem do mes do usuario`;
`App.jsx:6627` tem o mesmo comentário no espelho front. Hoje irrelevante
porque `PLAN_FREE.max_analyses_per_month` é `None` — mas se o número
comercial for populado (ADR-010, decisão de negócio ainda pendente do Alex)
sem tocar esses call sites, o gate quebra silenciosamente (compara `0 >=
limite` sempre — bloqueia todo mundo ou ninguém, dependendo da ordem).
**Decidido**: os call sites (backend E front) precisam calcular a contagem
real de análises do mês corrente ANTES do gate virar operacional — mesmo
que `max_analyses_per_month` continue `None` por enquanto (ADR-010 não
mudou). Não é gate de negócio ativo, é fechar a lacuna estrutural que faria
o número comercial (quando vier) funcionar certo desde o primeiro dia.

**C-34 — Painel de orçamento brapi é 100% admin-only.** **Tensão resolvida
por verificação direta — já coberto, não construir UI nova.** A recomendação
ORIGINAL do achado diz: *"não é necessário expor orçamento bruto ao usuário
final... mesma mudança de C-30 resolve as duas questões."* Conferido contra
`03-01-SUMMARY.md` (Fase 3, `FIX-C30`, completo): `/api/technicals/{ticker}`
já devolve `degradado` (bool), `TechnicalModal` já mostra "aviso em âmbar na
mesma linha da fonte, **sem exposição de detalhes de orçamento/cota/limite**
(contrato do UI-SPEC)" — decisão deliberada, registrada explicitamente no
Copywriting Contract da Fase 3: "qualificador de degradado deliberadamente
não menciona orçamento/cota/mês/limite ao usuário final — só o efeito (dado
mais velho), nunca a causa." Construir um "medidor de consumo × limite"
agora contradiria essa decisão de produto já tomada e shippada.
**Decidido**: C-34 fica satisfeito pelo fix já entregue de C-30 — não
construir UI nova de medidor de orçamento. Escopo real desta fase pra C-34:
um teste/verificação que confirma que o comportamento de C-30 segue valendo
(o aviso de degradado aparece, sem vazar número de orçamento/cota/limite) —
fechamento por confirmação, não por feature nova. Se o Alex quiser reabrir
essa decisão de produto (expor medidor de verdade), é decisão dele a tomar
explicitamente, não algo pra inferir do Success Criteria do ROADMAP.

### ADMIN — portal (`web-admin/`)

**C-38 — Hard stop no teto global de gasto de IA existe, mas sem alerta
preventivo antes de bater o teto.** `server/app/metering.py:99-113` impõe
hard stop; aba Custos do portal mostra sparkline de tokens/dia sem limiar
configurável nem alerta automático.
**Decidido**: limiar configurável de "gasto de hoje X% acima da média dos
últimos N dias" com alerta visual — complementar ao hard stop já existente,
não substitui. Escopo mínimo: cálculo determinístico + indicador visual na
aba Custos do `web-admin/`; não é necessário push/e-mail (fica pra fase
futura, mesmo padrão do C-37 já entregue na Fase 3).

**C-39 — Aba "Auditoria" sem campo `perm`, diverge do padrão visual das
outras 9 abas.** `web-admin/src/App.jsx:1110` (auditoria) — única entrada
sem `perm`; linha `1176` filtra `!v.perm || perms.includes(v.perm)`, então
funciona hoje (sempre visível a qualquer permissão administrativa) mas sem
comunicar visualmente que a regra de acesso é DIFERENTE das outras 9
(qualquer permissão admin, não uma específica). Backend já gateia certo
(`require_any_admin_permission()`), não há vazamento de dado.
**Decidido**: adicionar o campo `perm` (ou equivalente visual) na entrada de
"Auditoria" alinhando com o padrão das outras 9 abas — cuidado para não
mudar a regra de acesso real (continua "qualquer permissão administrativa"),
só o rótulo/consistência visual.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Evidência original
- `.planning/milestones/v1.0-phases/01-auditoria-diagn-stica-consolidada/REPORT-01.md` linhas 552-608 (C-21..C27, CODE), 694-709 (C-33/C-34, GATE), 755-768 (C-38/C-39, ADMIN).

### CODE
- `web/src/App.jsx` — `ctx.operador` (definição, ~7214 na auditoria — re-grep), as leituras redundantes de `appMode`.
- `server/app/defaults.py`, `web/src/catalog.js` — par `default_skill_text`/`defaultSkillText`.
- `server/tests/test_auditoria_prompts.py` — `test_a8ii_paridade_defaults_carteira_com_catalog_js`, padrão de guardião byte-exato a estender.
- `web/tests/test_copy_theme.mjs` — checagem de presença hoje insuficiente pra C-22.

### GATE
- `server/app/main.py` — `can_analyze(0)` (~1370 na auditoria), `plan.py` (`can_add_ticker`/`can_analyze`).
- `web/src/App.jsx` — espelho front do mesmo call site hardcoded (~6627 na auditoria).
- `server/app/brapi_budget.py` — `snapshot()` (~170-189 na auditoria), já cobre normal+degradado.
- `docs/adr/010-...md` (números comerciais) — decisão de negócio ainda pendente, NÃO reabrir aqui.

### ADMIN (`web-admin/`, projeto npm separado)
- `server/app/metering.py` — hard stop (~99-113 na auditoria).
- `web-admin/src/App.jsx` — aba Custos (sparkline de tokens), entrada de "Auditoria" na lista de abas.

### Padrão de guardião a seguir
- Todo achado corrigido precisa de teste que trava o comportamento (CLAUDE.md "Validação obrigatória") — `server/tests/` backend, `web/tests/*.mjs` e possivelmente `web-admin/` front, suíte canônica `bash scripts/executar.sh --testes` (não cobre `web-admin/` — confirmar se há suíte própria pro portal admin antes de assumir).

</canonical_refs>

<specifics>
## Specific Ideas

- C-21 e C-22 são ambos "dívida silenciosa que não quebrou ainda" — bom
  candidato a uma wave só de backend/guardião, separada da UI.
- C-23 é uma linha (`disabled={!operador}`) — não precisa de plano próprio,
  cabe fácil junto de outro achado de front pequeno.
- C-34 precisa de decisão explícita ANTES de codar (ver tensão marcada
  acima) — o planejamento deve resolver isso lendo `FIX-C30`'s SUMMARY
  (Fase 3) pra confirmar o que já está coberto.
- **Confirmado**: `web-admin/` NÃO tem suíte de teste (`package.json` só tem
  `dev`/`build`/`preview`, nenhum framework de teste instalado, nenhum
  arquivo `*test*` no projeto). Acceptance criteria de C-38/C-39 não podem
  assumir `npm test`/`.mjs` guardian — só `npx vite build` (syntax check) +
  verificação visual/manual. Se o planejamento decidir introduzir o
  PRIMEIRO teste automatizado pro portal admin aqui, é uma decisão de
  escopo maior que precisa ficar explícita (não implícita num acceptance
  criteria que assume infra que não existe).

</specifics>

<deferred>
## Deferred Ideas

- Implementação completa de E2E/Playwright (C-27) — avaliação, não
  implementação obrigatória, ver decisão acima.
- Push/e-mail para alertas (C-37 já entregue na Fase 3 com esse escopo
  reduzido; C-38 segue o mesmo precedente — só indicador visual agora).
- Números comerciais do plano gratuito/pago (ADR-010) — decisão de negócio
  do Alex, fora do alcance técnico desta fase (C-33 prepara o terreno, não
  decide o número).
- Qualquer achado Baixo do REPORT-01 (C-06..C-10, C-17, C-18, C-28, C-29) —
  backlog explícito, fora desta fase.

</deferred>

<scope_fence>
## Scope Fence

**Dentro do escopo:** os 11 requirements FIX-C21, FIX-C22, FIX-C23,
FIX-C24, FIX-C25, FIX-C26, FIX-C27, FIX-C33, FIX-C34, FIX-C38, FIX-C39 —
exatamente como descritos acima.

**Fora do escopo:**
- Fase 4 (STORY/UX) — já fechada, não reabrir.
- Qualquer achado Baixo (C-06..C-10, C-17, C-18, C-28, C-29).
- Decisão de números comerciais (ADR-010).
- Suíte E2E completa (avaliar, não construir, salvo decisão explícita
  contrária no planejamento).
- Motor de setups/seleção dinâmica (ADR-016/017) — sem relação com esta fase.
- Push/e-mail para qualquer alerta novo (C-38) — só indicador visual.

</scope_fence>

---

*Phase: 05-corre-o-m-dio-c-digo-gate-admin*
*Context gathered: 2026-08-22, a partir do REPORT-01 original (não houve discuss-phase — requirements e evidência já vinham completos do audit)*
