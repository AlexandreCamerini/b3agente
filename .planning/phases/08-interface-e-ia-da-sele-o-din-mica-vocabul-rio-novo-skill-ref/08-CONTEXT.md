# Phase 8: Interface e IA da Seleção Dinâmica — Context

**Gathered:** 2026-08-21
**Status:** Ready for planning
**Source:** ADR Ingest Express Path (docs/adr/017-revisao-de-setups-e-selecao-dinamica.md) — escrito à mão porque o parser automático (`adr-parser.cjs --format auto`) não reconhece o formato "Decisão N" deste ADR e devolve 0 decisions (mesma limitação já documentada no CONTEXT.md da Fase 7). Decisões abaixo extraídas de "Decisão 2", "Decisão 3", "Sequenciamento de entrega" (item 4) e "Consequências" do ADR-017, cruzadas com o código real entregue na Fase 7 (Bloco 1) via leitura direta de `server/app/setups.py`, `server/app/regime.py`, `server/app/signal_ledger.py`, `server/app/scanner.py`, `server/app/agent.py`.

<domain>
## Phase Boundary

O Bloco 1 (Fase 7, concluída 2026-08-21) já entrega o histórico medido por
setup — `elegivel`, `expR`, `expRJanela`, `n`, `nJanela`, `janelaRef`,
`medidoAte`, `calculadoEm` — anexado em cada resultado de `/api/scan` (via
`regime.ranquear()` mutando `results` em `scanner.py:320`, campos
`setupHistorico`/`setupElegivel` por ticker, e `historico` por setup dentro de
`sres["setups"]`, vindo de `detect_setups()`). **Nenhum componente do front lê
esses campos hoje** — confirmado ao vivo (grep em `web/src/App.jsx` não
encontra `setupHistorico`/`setupElegivel`/`s.historico`; card do ativo idêntico
ao de antes do deploy do Bloco 1).

Esta fase é o Bloco 3 (interface) + Bloco 4 (religamento do Modo Operador) do
ADR-017: dar vitrine ao dado que já existe, e trocar a suspensão cega de
`entradaAuto` por um gate fino baseado nesse mesmo dado. **Não recalcula nada**
— é consumo do que o Bloco 1 já produz.

</domain>

<decisions>
## Implementation Decisions

### Vocabulário (skill_ref.py ↔ copy.js, fonte única + espelho)

- Frases novas entram em `server/app/skill_ref.py` (padrão `vocab[modo]`/
  `TIMING[modo][estado]` já existente, ver `server/app/skill_ref.py:217-265`)
  e no espelho `web/src/copy.js` (`COPY[modo]`, `web/src/copy.js:18+` — nota:
  a chave de modo no front é `estudo`/`operador`, no backend é
  `educacional`/`operador`; não unificar nesta fase, seguir a convenção já
  existente de cada arquivo). Texto novo NUNCA fica solto num componente —
  guardião de paridade de chaves (`web/tests/test_vocabulario_espelho.mjs`)
  precisa cobrir as chaves novas.
- Não existe hoje frase canônica para: setup aposentado (`s.aposentado`),
  elegibilidade positiva/negativa/desconhecida (`elegivel` True/False/None),
  amostra insuficiente (`historico.insuficiente` True ou `elegivel is None`),
  dado desatualizado (`medidoAte`/`calculadoEm` mais velho que 2 dias úteis —
  limiar do ADR-017 Decisão 2, "Carimbo obrigatório"), e o contraste
  "sem filtro: −0,099R · com filtro (setups positivos na janela anterior):
  +0,005R — estatisticamente empate, não lucro" (texto do Plano Mode original,
  Bloco 2, pergunta 4 — usar SEMPRE os dois números lado a lado, nunca o
  filtrado sozinho, quando esse contraste for exibido).
- Resultado negativo tem o MESMO destaque visual que positivo — não é
  preferência de design, é regra da `didatica-boris` skill (nenhuma
  manipulação visual de resultado).

### Telas — Radar, Watchlist, card de setup (SEM mudança de backend)

- **Radar/Watchlist** (nível ticker): `setupElegivel` (bool|None) e
  `setupHistorico` (dict|None, mesmo shape do item abaixo) já chegam em cada
  `results[i]` de `/api/scan` — consumidos onde hoje só `confluencia`/
  `melhorSetup`/`veredito` aparecem (`web/src/App.jsx`, região do `ConfluenceRing`
  e da lista de Watchlist, ~linhas 1688-1796 e ~5741-5876). Não precisa de
  rota nova nem de campo novo no backend.
- **Card de setup individual** (nível setup, dentro do card do ativo): cada
  item de `sres["setups"]` já carrega `historico` — dict com `{expR, n,
  medidoAte, elegivel, insuficiente, expRJanela, nJanela, janelaRef,
  calculadoEm}` (shape exato de `server/app/signal_ledger.py:222-246`,
  `_fundir`) — ou `None` se o setup nunca foi medido, ou a chave nem existe se
  o provedor estiver desligado (`hist_map is None`, ver `setups.py:554-558`).
  A UI que hoje lista `s.nome` + `s.confluencia`% (`web/src/App.jsx:5873`) é o
  ponto natural para anexar o número — tratar ausência de `historico` como
  "nunca medido" (estado próprio, não erro).
- **Setup aposentado** (`s.aposentado === true`, 6 setups da faixa
  catastrófica do ADR-016 — Ponto Contínuo, Setup 9.2, Inside Bar baixa,
  Máx/Mín LW 9.4 baixa): continua aparecendo na lista de setups do card
  (didático, não remove — regra do ADR-017 Decisão 1), mas precisa de rótulo
  visual próprio ("padrão gráfico identificado, sem vantagem estatística
  medida (ADR-016)"), nunca confundido com um setup mantido de baixa
  confluência.

### Estados completos (nenhum é opcional — princípio 9 do CLAUDE.md do repo)

1. Setup nunca medido (`historico` ausente/None) — não é "elegível=false", é
   "sem dado ainda".
2. Amostra insuficiente na janela (`historico.insuficiente === true` OU
   `elegivel === null`) — ausência de evidência ≠ prova de mau desempenho
   (ADR-017, "Dois pisos de amostra"); nunca estilizar como negativo.
3. Dado desatualizado (`medidoAte`/`calculadoEm` mais velho que 2 dias úteis)
   — degrada visualmente, nunca bloqueia a leitura (ADR-017, Decisão 2).
4. Setup aposentado (`aposentado === true`) — ver item acima.

### Religamento do Modo Operador (Decisão 3 do ADR-017 + Consequências)

- **Hoje**: `server/app/agent.py:603` (`ENTRADA_AUTO_SUSPENSA_ADR017 = True`)
  suspende TODA entrada automática do Modo Operador, incondicionalmente,
  dentro de `_avaliar_entradas()` (`agent.py:604-693`).
- **Decidido**: trocar a suspensão cega por um gate por elegibilidade do
  setup específico que disparou o gatilho — não é "remover a suspensão", é
  substituí-la por uma condição mais fina que só deixa passar o que o Bloco 1
  já mediu como positivo. Em `_avaliar_entradas`, o nome do setup do gatilho
  já está disponível em `r.get("setup")` (`agent.py:645`, mesmo valor usado em
  `meta={"setup": r.get("setup")}` na linha 675). Consultar
  `signal_ledger.historico_snapshot(conn)` (import local dentro da função,
  mesmo padrão já usado para `signal_ledger_job` em `agent.py:1112` — evita
  ciclo de import) e checar `elegivel` do setup do gatilho:
  - `elegivel is True` → gate passa, segue o fluxo de execução normal (lote,
    orçamento, teto diário, teto por operação — inalterados).
  - `elegivel is False` OU `elegivel is None` (nunca medido/amostra
    insuficiente) → bloqueia, mesmo comportamento de hoje (sem executar, sem
    warning extra — silencioso como a suspensão atual, já que não é erro).
- Hoje (dado do bootstrap de produção, 2026-08-21), só 5 pares setup×lado
  estão elegíveis na janela 2025: 123 de fundo (alta), IFR2 (alta), PFR
  (alta), Setup 9.1 (alta), Setup 9.3 (alta) — na prática, o gate restringe
  a entrada automática a esses, sem precisar de lista hardcoded (o dado
  decide, a cada virada de janela).
- **Checkpoint humano obrigatório antes do deploy em produção** desta mudança
  específica (mesmo padrão da Fase 7/07-06) — muda comportamento real de
  execução automática de dinheiro simulado do usuário; não é reversível sem
  novo deploy se algo sair errado.

### Guardrail explícito (repetido do ADR-017, não renegociável nesta fase)

Toda a seleção continua determinística — a fase é EXIBIÇÃO de número já
calculado e um GATE por valor já calculado, nunca julgamento de IA sobre
setup, ranking ou entrada. Se um prompt de IA novo entrar (ex.: assistente
explicando "por que este setup está elegível"), ele SÓ narra o número
recebido — não decide nada, e se citar texto de `defaults.py`, precisa manter
paridade byte-exata com `catalog.js` (guardião
`test_a8ii_paridade_defaults_carteira_com_catalog_js`,
`server/tests/test_auditoria_prompts.py:197`).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Arquitetura e decisão de produto
- `docs/adr/017-revisao-de-setups-e-selecao-dinamica.md` — Decisão 2
  (shape do histórico), Decisão 3 (destino do Operador), Sequenciamento de
  entrega item 4, Consequências, Adendo 1 (nomes reais de campo entregues no
  Bloco 1).
- `docs/adr/016-...md` (via referência no 017) — números de referência do
  motor (−0,105R, −0,167R do Operador) para qualquer texto que precise citar
  a razão da suspensão original.

### Dado já disponível (não recalcular)
- `server/app/regime.py:227-312` — `W_HISTORICO_ELEGIVEL`/
  `W_HISTORICO_INELEGIVEL`, `_elegibilidade()`, shape de saída de `ranquear()`
  (`setupHistorico`, `setupElegivel` por resultado).
- `server/app/setups.py:480-570` — `SETUPS_APOSENTADOS`, `set_historico_provider`,
  `_historico_map`, onde `s["aposentado"]`/`s["historico"]` são anexados.
- `server/app/signal_ledger.py:222-267` — `_fundir` (shape exato do dict
  `historico`), `historico_snapshot` (função a chamar para o gate do
  Operador).
- `server/app/scanner.py:280-320` — onde `results` (payload de `/api/scan`)
  já carrega `setups`, `veredito`, `confluencia`, `melhorSetup`, `plano`, e
  onde `regime.ranquear(results, snaps)` muta esse mesmo `results`.

### Vocabulário e didática
- `server/app/skill_ref.py:206-287` — `vocab`, `TIMING`, `timing_txt`,
  `decisoes_txt` (padrão de função helper por frase parametrizada).
- `web/src/copy.js:1-40` — `COPY[modo]`, convenção de chaves idênticas nos
  dois modos.
- `.claude/skills/didatica-boris/SKILL.md` — vocabulário não-negociável,
  "Explicação boa, nesta base" (3 perguntas: o que é / o que acontece quando
  ocorre / o que NÃO acontece), regra de guardião antes de entregar.
- `web/tests/test_vocabulario_espelho.mjs` — guardião de paridade de chaves
  entre `skill_ref.py` e `copy.js`.

### UI existente a estender (não recriar)
- `web/src/App.jsx` — `ConfluenceRing` (~1736, ~5825), lista de Watchlist
  (~5741-5876), lista de setups por card (~5873), região do card do ativo
  (~2900-3070).

### Religamento do Operador
- `server/app/agent.py:595-693` — `ENTRADA_AUTO_SUSPENSA_ADR017`,
  `_avaliar_entradas` (candidatos, gatilho, `r.get("setup")`, lote/orçamento/
  tetos inalterados), `agent.py:1107-1113` (padrão de import local já usado
  para `signal_ledger_job`, replicar para `signal_ledger`).

</canonical_refs>

<specifics>
## Specific Ideas

- O contraste "sem filtro vs. com filtro" (−0,099R / +0,005R) do Bloco 2 do
  Plan Mode original é um texto candidato a aparecer em algum lugar didático
  (ex.: explicação do painel do Operador ou de "por que a entrada automática
  está restrita a poucos setups") — se entrar nesta fase, os dois números
  sempre juntos, nunca o positivo isolado.
- IFR2 (alta) nunca deve ser apresentado como "o setup vencedor" isolado —
  sempre com o número de amostra/expectância por perto (regra já registrada
  no ADR-017 Decisão 1, reforçar na cópia se este setup for citado
  nominalmente em algum texto novo).
- "Aposentado ≠ apagado" precisa ficar claro na UI — o usuário que já viu
  esses 6 setups antes do Bloco 0 não pode interpretar o rótulo novo como bug
  ou remoção de funcionalidade.

</specifics>

<deferred>
## Deferred Ideas

- Filtro/restrição por lado (comprado vs. vendido) — já testado e refutado
  como critério (ADR-017 Decisão 1, Adendo 6 do ADR-016). Fora de escopo,
  não reabrir.
- Qualquer mudança no CÁLCULO do histórico (janela, `min_n`, pesos
  `W_HISTORICO_*`) — pertence ao Bloco 1 (Fase 7), já fechado; esta fase só
  consome.
- Prompt de IA elaborado explicando expectância/R-múltiplo em profundidade
  (Bloco 4 "completo", se distinto do religamento do Operador) — avaliar
  no planejamento se cabe nesta fase ou fica para uma fase futura; não é
  bloqueante para os outros itens.

</deferred>

<scope_fence>
## Scope Fence

**Dentro do escopo:**
- Vocabulário novo em `skill_ref.py` + espelho `copy.js`, guardião de
  paridade estendido.
- Radar/Watchlist mostrando `setupElegivel`/`setupHistorico` por ticker.
- Card de setup mostrando `historico` por setup, incluindo os 4 estados
  completos (nunca medido, amostra insuficiente, desatualizado, aposentado).
- Gate de elegibilidade em `_avaliar_entradas` substituindo
  `ENTRADA_AUTO_SUSPENSA_ADR017`, com checkpoint humano antes do deploy em
  produção.

**Fora do escopo (não implementar nesta fase):**
- Qualquer alteração em `regime.ranquear`, `setups.detect_setups`,
  `signal_ledger.py`, `signal_ledger_job.py` ou nos pesos `W_HISTORICO_*` —
  esse código já está correto e testado (Fase 7); esta fase só lê o que ele
  produz.
- Filtro por lado (comprado/vendido).
- Mudar a janela de reavaliação (anual) ou o piso de amostra (`min_n=40`).
- Remover o campo `aposentado` da lista de setups do card (o detector
  continua rodando e aparecendo, por decisão do ADR-017 Decisão 1).

</scope_fence>

---

*Phase: 08-interface-e-ia-da-sele-o-din-mica-vocabul-rio-novo-skill-ref*
*Context gathered: 2026-08-21 via ADR Ingest Express Path (manual, parser incompatível)*
