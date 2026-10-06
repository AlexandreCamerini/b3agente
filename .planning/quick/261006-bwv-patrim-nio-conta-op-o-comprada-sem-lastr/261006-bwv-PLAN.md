---
phase: quick-261006-bwv
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - server/app/store.py
  - server/app/main.py
  - server/tests/fixtures/patrimonio_opcoes_paridade.json
  - server/tests/test_patrimonio_opcao_avulsa.py
  - web/src/finance.js
  - web/tests/test_finance.mjs
  - web/tests/test_patrimonio_opcao_avulsa.mjs
  - web/src/App.jsx
  - web/src/copy.js
autonomous: true
requirements: [quick-261006-bwv]

must_haves:
  truths:
    - "Comprar a PUT VALEV731W2 (100 x R$ 0,92) sem ações de VALE3 debita R$ 92 do caixa e o patrimônio fica IGUAL ao de antes da compra (perna marcada pelo prêmio de abertura), na Carteira, na curva de Evolução e na fala do Boris (pet:evolucao)"
    - "Perna sem lastro COM cotação viva em optionQuotes entra marcada a mercado (qty x prêmio vivo); SEM cotação entra pelo custo de entrada (avg), nunca 0, e é contada em opcoesSemMarcacao / sem_marcacao"
    - "Perna com side='vendida' (com ou sem lastro) SUBTRAI qty x prêmio do patrimônio; perna sem `side` (modelo buy_option) é tratada como comprada"
    - "Pernas COM lastro (call coberta / put de proteção) produzem exatamente os mesmos números de antes"
    - "finance.portfolioMetrics e store.valor_opcoes devolvem os MESMOS números para a MESMA fixture JSON compartilhada"
    - "Sempre que alguma perna estiver marcada sem cotação viva, Carteira e Evolução mostram a linha cp.linhaPatrimonioOpcoes com o valor das opções — nunca silencioso"
    - "equitySnapshots de dias anteriores não são reescritos (nenhum recálculo retroativo)"
  artifacts:
    - path: "server/app/store.py"
      provides: "valor_opcoes(option_positions, option_quotes=None) -> {valor, pnl, sem_marcacao}, pura"
      contains: "def valor_opcoes"
    - path: "server/app/main.py"
      provides: "_pet_resumo_evolucao soma valor_opcoes ao patrimônio"
      contains: "store.valor_opcoes"
    - path: "server/tests/fixtures/patrimonio_opcoes_paridade.json"
      provides: "fixture única de paridade front x backend (casos + esperado)"
      contains: "VALEV731W2"
    - path: "server/tests/test_patrimonio_opcao_avulsa.py"
      provides: "guardião backend: VALEV731W2, com/sem cotação, lastreada inalterada, vendida subtrai, histórico intacto, paridade com fixture"
    - path: "web/src/finance.js"
      provides: "portfolioMetrics conta perna sem lastro; devolve opcoesSemMarcacao"
      contains: "opcoesSemMarcacao"
    - path: "web/tests/test_patrimonio_opcao_avulsa.mjs"
      provides: "guardião front: mesma fixture, mesmos números; sinalização na UI"
  key_links:
    - from: "server/app/main.py:_pet_resumo_evolucao"
      to: "store.valor_opcoes"
      via: "chamada direta com optionPositions do escopo"
      pattern: "store\\.valor_opcoes\\("
    - from: "web/tests/test_patrimonio_opcao_avulsa.mjs"
      to: "server/tests/fixtures/patrimonio_opcoes_paridade.json"
      via: "readFileSync da MESMA fixture lida pelo pytest"
      pattern: "patrimonio_opcoes_paridade\\.json"
    - from: "web/src/App.jsx (CarteiraScreen e CapitalCurve)"
      to: "m.opcoesSemMarcacao"
      via: "condição de render da linha cp.linhaPatrimonioOpcoes"
      pattern: "opcoesSemMarcacao > 0"
---

<objective>
Fazer a perna de opção comprada SEM lastro (modelo `store.buy_option`, a "perna avulsa") entrar no patrimônio, com paridade exata front x backend e sinalização explícita quando a marcação não é cotação viva.

Purpose: caso real do Alex — PUT VALEV731W2, 100 un a R$ 0,92 (06/10/2026 07:46) debitou R$ 92 do caixa e sumiu do patrimônio (R$ 92 menor). Dinheiro simulado desaparecendo da tela viola a transparência (princípios 1, 3, 4 e 5 do CLAUDE.md).
Output: `store.valor_opcoes` (backend, puro), `portfolioMetrics` ampliado (front), fixture de paridade compartilhada, guardiões novos e reconciliados, linha de sinalização na Carteira e na Evolução.
</objective>

<investigation>
Conclusões da investigação (2026-10-06), registradas antes de planejar:

1. Onde o patrimônio é calculado.
   - Front: `web/src/finance.js:113` `portfolioMetrics` é a fonte única; 7 call sites em `web/src/App.jsx` (2052 CapitalCurve/Evolução, 2241 Home, 5607 CarteiraScreen, 10076 snapshot diário, 10312 chip do topo, 10349/10359 snapshot do assistente). Todos passam 5 args (`data.optionPositions`), nenhum passa `optionQuotes` → toda perna hoje é marcada pelo `avg` (prêmio de abertura).
   - `persistence.js` (deviceStore/serverStore) NÃO calcula patrimônio: só faz `upsertSnapshot` do que o App manda (`web/src/persistence.js:82-87`, `store.putSnapshot` em `App.jsx:10077`). Não há método novo nos stores → paridade deviceStore↔serverStore não é tocada.
   - Backend: `store.upsert_snapshot` (store.py:1429) apenas persiste o `patrimonio` enviado pelo cliente (`POST /api/snapshot`, main.py:1891). O ÚNICO cálculo de patrimônio no servidor é `_pet_resumo_evolucao` (main.py:4798), que hoje soma só caixa + reservado + ações — ignora TODAS as opções, inclusive as lastreadas (divergência pré-existente com a tela). Agente (`agent.py`) não usa patrimônio. Logo há DOIS cálculos que precisam bater: `portfolioMetrics` e `_pet_resumo_evolucao`.
   - Benchmark/drawdown/retorno acumulado: `equityCurve`/`benchmarkSerie` operam sobre `equitySnapshots` + `livePatr = m.patr`; corrigir `portfolioMetrics` corrige os três por construção.
2. Pernas COM lastro já contam (D-6, Fase 14): `comprada` → `+qty*preço`, `vendida` → `-qty*preço` (prêmio recebido já está em `cash`). Ações travadas como lastro contam inteiras em `posVal`; a perna é coleção própria (`optionPositions`) — não há dupla contagem com ações nem com `caixaReservado` (buy_option debita `cash` direto, não reserva). A perna avulsa NÃO tem chave `side` (store.py:841-849) → o loop atual a descartaria mesmo sem o filtro de `lastro`; a regra nova trata ausência de `side` como comprada.
3. Histórico: snapshots de dias passados são imutáveis por construção (upsert por `data`). Só o snapshot de HOJE é regravado pelo cliente na próxima sessão (comportamento já existente: valor novo, não reescrita). Nada nesta tarefa toca `equitySnapshots`, `history` ou `upsert_snapshot`.
4. Guardiões que travam o comportamento antigo:
   - `web/tests/test_finance.mjs:136-144` ("opção sem lastro: opcoesVal = 0 / patr não muda") → reversão deliberada, reconciliar com nota datada 2026-10-06 (não apagar o bloco: vira a expectativa nova).
   - `web/tests/test_carteira_lastro_ui.mjs:84-92` (todas as chamadas passam optionPositions; concentracaoMaxima sem optionPositions) → continua válido, não muda.
   - `web/tests/test_status_mercado_ui.mjs:103` (exatamente 7 chamadas de `portfolioMetrics(`) → não adicionar nem remover chamadas em App.jsx.
   - `server/tests/test_ordens_pendentes_rotas.py:496` (pet:evolucao soma reservado) → continua válido.
5. Sinalização na UI: já existe `cp.linhaPatrimonioOpcoes` (copy.js:787 estudo "opções lastreadas (marcadas pelo prêmio de abertura — sem cotação ao vivo)", copy.js:2083 operador "perna de opções (prêmio de abertura — sem cotação ao vivo)"), renderizada só na Carteira (App.jsx:5650) e só quando há perna com `lastro`. Chave é só do front (não está em `skill_ref.py`), logo não há espelho byte a byte a manter. Histórico (sub-tela) não exibe patrimônio; a Evolução (CapitalCurve, "PATRIMÔNIO SIMULADO", App.jsx:2127) exibe e não tem ressalva.

Regra decidida para perna sem cotação viva: carregar pelo CUSTO DE ENTRADA (`avg`, prêmio efetivamente pago), contar em `opcoesSemMarcacao` e SEMPRE mostrar a linha `cp.linhaPatrimonioOpcoes` com o valor. Motivo: (a) `avg` é número registrado (o caixa que saiu), não estimado — não é invenção nem 0; (b) a compra fica neutra no patrimônio, que é a verdade contábil do instante da compra; (c) é a MESMA regra já vigente para ações sem cotação (`markPrice` → `avg`) e para pernas lastreadas (D-6) — uma regra só, sem caso especial; (d) a alternativa "patrimônio incompleto excluindo a perna" reproduz exatamente o defeito relatado (R$ 92 sumindo) e distorce mais. Limitação conhecida e dita na tela: o prêmio de mercado do contrato pode ter mudado; o valor exibido é o de abertura.
</investigation>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@./CLAUDE.md
@.planning/quick/261006-axi-op-o-comprada-sem-a-es-do-ativo-some-da-/261006-axi-SUMMARY.md

Regras de leitura: `App.jsx` e `main.py` NUNCA inteiros — Grep + Read com offset/limit nas linhas citadas acima.

<interfaces>
From web/src/finance.js (atual, linhas 113-151):
export function portfolioMetrics(positions, quotes, cash, reservado, optionPositions, optionQuotes)
  -> { posVal, cost, openPnL, openPct, dayVal, patr, cash, reservado, opcoesVal, opcoesPnL }
  loop de opções: pula op sem `lastro` (linha 135); preço = optionQuotes[op.id] se number > 0, senão avg;
  side "comprada": opcoesVal += qty*preco, opcoesPnL += (preco-avg)*qty;
  side "vendida": opcoesVal -= qty*preco, opcoesPnL += (avg-preco)*qty.
  patr = cash + reservado + posVal + opcoesVal.

From server/app/store.py:
def buy_option(conn, contract, qty, price, user_id=None, meta=None, origem="manual")  # 805; exige cfg.permitirOpcaoADescoberto truthy; grava pos SEM `side` e SEM `lastro`; cash -= qty*price
def comprar_put_protecao(conn, contract, contratos, price, user_id=None, meta=None, ...)  # 1082; side="comprada", lastro={"t","qty"}
def caixa_reservado(conn, user_id=None) -> float  # 610
def upsert_snapshot(conn, snap, user_id=None) -> list  # 1429; NÃO alterar

From server/app/main.py:4798:
def _pet_resumo_evolucao(scope, intra_stored, operador) -> {"fala": [...], "patrimonio", "retornoAcumuladoPct", "perguntas"}
  patrimonio = cash + reservado + pos_val   (linha 4827; sem opções)
  rota: GET /api/pet/resumo?tela=evolucao (padrão de teste: server/tests/test_ordens_pendentes_rotas.py:496, helpers _client/_registrar)
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Backend — store.valor_opcoes puro + pet:evolucao soma opções + fixture de paridade</name>
  <files>server/app/store.py, server/app/main.py, server/tests/fixtures/patrimonio_opcoes_paridade.json, server/tests/test_patrimonio_opcao_avulsa.py</files>
  <behavior>
    - Fixture: cada caso tem cash, reservado, optionPositions, optionQuotes e esperado {opcoesVal, opcoesPnL, semMarcacao, patr} (positions sempre [] para isolar opções). Casos obrigatórios: (A) VALEV731W2 PUT sem side/sem lastro, qty 100, avg 0.92, cash 9908, sem cotação → opcoesVal 92, opcoesPnL 0, semMarcacao 1, patr 10000; (B) mesma perna com optionQuotes {VALEV731W2: 1.10} → 110, 18, 0, 10018; (C) put lastreada side comprada avg 2 quote 3, cash 1000 → 300, 100, 0, 1300; (D) call coberta lastreada side vendida avg 2 quote 1, cash 1000 → -100, 100, 0, 900; (E) side vendida SEM lastro avg 1.5 quote 2, cash 1000 → -200, -50, 0, 800; (F) misto A+C sem cotação nenhuma → semMarcacao 2; (G) cotação inválida (0, negativa, string, true) cai no avg e conta em semMarcacao.
    - store.valor_opcoes(fixture.optionPositions, fixture.optionQuotes) == esperado (valor/pnl/sem_marcacao) para todos os casos, tolerância 1e-9; cash+reservado+valor == esperado.patr.
    - Integração: conta registrada, config permitirOpcaoADescoberto=True, cash inicial lido de /api/state; store.buy_option VALEV731W2 100 x 0.92 → cash cai exatamente 92.00 e GET /api/pet/resumo?tela=evolucao devolve patrimonio igual ao de antes (approx 1e-6) e alguma linha da fala menciona "prêmio de abertura".
    - Perna lastreada (comprar_put_protecao ou optionPositions seedado com lastro) muda o patrimonio do pet:evolucao exatamente por valor_opcoes (antes desta tarefa o pet a ignorava — assert sobre o número novo).
    - Histórico intacto: equitySnapshots seedados com 2 datas passadas antes do buy_option + chamada do pet:evolucao → lista byte-idêntica (json.dumps igual) depois.
  </behavior>
  <action>
    Criar a fixture JSON compartilhada `server/tests/fixtures/patrimonio_opcoes_paridade.json` com os casos A-G da behavior (é a fonte única de números para os dois lados; o teste Node da Task 2 lê o MESMO arquivo).
    Em `server/app/store.py`, perto de `caixa_reservado`/`qty_livre`, criar a função pura `valor_opcoes(option_positions, option_quotes=None) -> dict` com chaves `valor`, `pnl`, `sem_marcacao`, gêmea declarada de `portfolioMetrics` (comentário: "espelho de web/src/finance.js portfolioMetrics — quick 261006-bwv, 2026-10-06; paridade travada por server/tests/fixtures/patrimonio_opcoes_paridade.json"). Regras: ignora item não-dict; qty/avg não numéricos leem 0 (espelho de `Number(x)||0`); prêmio vivo só se `option_quotes.get(id)` for int/float NÃO-bool, finito e > 0, senão usa avg e incrementa `sem_marcacao`; `side == "vendida"` → valor -= qty*preco, pnl += (avg-preco)*qty; qualquer outro side (incluindo ausente, que é a perna de `buy_option`) → valor += qty*preco, pnl += (preco-avg)*qty. SEM filtro de `lastro` — perna com e sem lastro seguem a mesma regra. Sem I/O, sem arredondamento interno (arredondamento é de exibição).
    Em `server/app/main.py` `_pet_resumo_evolucao` (linhas ~4814-4840, ler só esse trecho): ler `optionPositions` do escopo, chamar `store.valor_opcoes(opts, None)` (sem cotação de contrato nesta rota custo-zero, mesmo motivo do front: orçamento do provedor), somar `valor` ao `patrimonio`. Quando houver ao menos uma perna: a frase do patrimônio passa a "(caixa R$ X + posições R$ Y + opções R$ Z)" e anexar a linha "O valor das opções usa o prêmio de abertura de cada contrato — sem cotação ao vivo." Sem pernas, a fala fica byte-idêntica à atual. Atualizar a docstring com nota datada 2026-10-06 (quick 261006-bwv) registrando que antes a rota ignorava todas as opções.
    Escrever `server/tests/test_patrimonio_opcao_avulsa.py` com os testes da behavior, reaproveitando os helpers de cliente/registro de `test_ordens_pendentes_rotas.py` (importar ou replicar o padrão `_client(monkeypatch)`/`_registrar`). RED primeiro (rodar e ver falhar), depois implementar. Não tocar `upsert_snapshot`, `buy_option`, `sell_option` nem nenhum dado gravado.
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2/server && .venv/bin/python -m pytest tests/test_patrimonio_opcao_avulsa.py tests/test_ordens_pendentes_rotas.py tests/test_opcao_descoberto_gate.py -q</automated>
  </verify>
  <done>
    - `grep -c "def valor_opcoes" server/app/store.py` = 1 e `grep -c "store.valor_opcoes(" server/app/main.py` >= 1.
    - Fixture contém os 7 casos (A-G) e a string "VALEV731W2".
    - Os 3 arquivos de pytest passam; o teste de integração prova caixa −92,00 e patrimônio do pet:evolucao inalterado após a compra; snapshots passados idênticos.
    - `git diff server/app/store.py` não altera `upsert_snapshot`, `buy_option` nem `sell_option`.
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Front — portfolioMetrics conta perna sem lastro + opcoesSemMarcacao + guardião reconciliado</name>
  <files>web/src/finance.js, web/tests/test_finance.mjs, web/tests/test_patrimonio_opcao_avulsa.mjs</files>
  <behavior>
    - Para cada caso da fixture `server/tests/fixtures/patrimonio_opcoes_paridade.json`: portfolioMetrics([], {}, cash, reservado, optionPositions, optionQuotes) devolve opcoesVal, opcoesPnL, opcoesSemMarcacao e patr iguais a `esperado` (tolerância 1e-9) — os MESMOS números que o pytest da Task 1 confere contra store.valor_opcoes.
    - VALEV731W2: patrimônio antes da compra (cash 10000, sem pernas) == patrimônio depois (cash 9908 + perna) == 10000; com cotação 1.10 → 10018.
    - Chamada com 4 argumentos continua idêntica (opcoesVal 0, opcoesSemMarcacao 0).
    - Bloco antigo de test_finance.mjs ("opção sem lastro … fora do agregado") passa a esperar a perna CONTADA (opcoesVal 200, patr 1200, opcoesPnL 0), com nota datada.
  </behavior>
  <action>
    Em `web/src/finance.js` `portfolioMetrics` (linhas 113-151): remover o `continue` do filtro de `lastro` (linha 135); trocar o ramo `if (op.side === "comprada")` por `if (op.side === "vendida") { passivo } else { ativo }` — perna sem `side` (modelo `buy_option`) é comprada. Contar `opcoesSemMarcacao` (+1 sempre que o preço usado for o `avg` por falta de prêmio vivo `number > 0`) e devolvê-lo no objeto de retorno (aditivo; nenhum campo existente muda de nome). Reescrever o bloco de comentário das linhas 78-112: manter o histórico da Fase 14/D-6 e acrescentar nota "quick 261006-bwv (2026-10-06): perna sem lastro (buy_option) passa a entrar no agregado — antes ficava fora e o caixa debitado sumia do patrimônio (caso VALEV731W2); regra sem cotação = custo de entrada (avg), sinalizada via opcoesSemMarcacao; gêmeo backend store.valor_opcoes, paridade pela fixture compartilhada". Não mudar `markPrice`, `concentracaoMaxima`, `equityCurve`, `benchmarkSerie`.
    Em `web/tests/test_finance.mjs` linhas 136-144: NÃO apagar o bloco; reescrevê-lo como reversão deliberada com comentário "2026-10-06 (quick 261006-bwv): D-6 deixou de ser não-retroativo por decisão do Alex — perna sem lastro conta no patrimônio pelo avg quando não há prêmio vivo" e asserções novas (opcoesVal 200, opcoesPnL 0, patr 1200, opcoesSemMarcacao 1). Os demais blocos do arquivo continuam como estão.
    Criar `web/tests/test_patrimonio_opcao_avulsa.mjs` (padrão `ok(...)`/exit code dos outros .mjs) que lê a fixture via `readFileSync(join(here, "..", "..", "server", "tests", "fixtures", "patrimonio_opcoes_paridade.json"))` e confere todos os casos, mais o antes/depois do VALEV731W2 e a chamada de 4 argumentos. RED antes de editar finance.js.
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2 && node web/tests/test_patrimonio_opcao_avulsa.mjs && node web/tests/test_finance.mjs && node web/tests/test_status_mercado_ui.mjs && node web/tests/test_carteira_lastro_ui.mjs</automated>
  </verify>
  <done>
    - `grep -v '^\s*//' web/src/finance.js | grep -c 'typeof op.lastro'` = 0 (filtro de lastro removido do código, comentário histórico pode citar).
    - `grep -c "opcoesSemMarcacao" web/src/finance.js` >= 2 (contagem + retorno).
    - Os 4 testes Node passam; test_finance.mjs contém a nota "2026-10-06" no bloco reconciliado.
  </done>
</task>

<task type="auto">
  <name>Task 3: UI — sinalizar marcação pelo prêmio de abertura na Carteira e na Evolução</name>
  <files>web/src/App.jsx, web/src/copy.js, web/tests/test_patrimonio_opcao_avulsa.mjs</files>
  <action>
    Em `web/src/App.jsx` CarteiraScreen (Read offset ~5640, limit ~20): trocar a condição de render da linha de patrimônio de opções de `(data.optionPositions || []).some((p) => p && p.lastro)` para `m.opcoesSemMarcacao > 0` (aparece sempre que alguma perna — com ou sem lastro — está marcada pelo prêmio de abertura), mantendo `{cp.linhaPatrimonioOpcoes}` e `{moneySigned(m.opcoesVal)}`. Atualizar o comentário JSX com nota 2026-10-06 (quick 261006-bwv).
    Em `CapitalCurve` (Read offset ~2044 e ~2120, limit ~20 cada): logo abaixo do rótulo "PATRIMÔNIO SIMULADO", renderizar a mesma linha (mesmo estilo de 11px/T.textMuted, `cp.linhaPatrimonioOpcoes` + `moneySigned(m.opcoesVal)`) sob a condição `m.opcoesSemMarcacao > 0`. `cp` já vem de `ctx` nesse componente; confirmar por Grep que `moneySigned` está no escopo do módulo. NÃO adicionar nem remover chamadas de `portfolioMetrics(` (guardião exige exatamente 7).
    Em `web/src/copy.js` linha ~787 (modo estudo): trocar "opções lastreadas (marcadas pelo prêmio de abertura — sem cotação ao vivo)" por "opções em aberto (marcadas pelo prêmio de abertura — sem cotação ao vivo)" — a linha agora cobre a perna avulsa. Operador (linha ~2083) já é genérico ("perna de opções …"), não muda. Chave só do front (não existe em `skill_ref.py`), sem espelho a manter; atualizar o comentário vizinho com nota datada.
    Acrescentar ao `web/tests/test_patrimonio_opcao_avulsa.mjs` asserções estáticas sobre o fonte: App.jsx contém `opcoesSemMarcacao > 0` pelo menos 2 vezes; App.jsx não contém mais `.some((p) => p && p.lastro) && (`; o número de `portfolioMetrics(` em App.jsx continua 7; `COPY.estudo.linhaPatrimonioOpcoes` e `COPY.operador.linhaPatrimonioOpcoes` contêm "prêmio de abertura" e "sem cotação ao vivo"; COPY.estudo.linhaPatrimonioOpcoes não contém "lastreadas".
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2 && node web/tests/test_patrimonio_opcao_avulsa.mjs && node web/tests/test_carteira_lastro_ui.mjs && node web/tests/test_status_mercado_ui.mjs && node web/tests/test_carteira_perna_avulsa.mjs && cd web && npx vite build</automated>
  </verify>
  <done>
    - `grep -c "opcoesSemMarcacao > 0" web/src/App.jsx` >= 2.
    - Número de chamadas `portfolioMetrics(` em App.jsx inalterado (7) — provado por `node web/tests/test_status_mercado_ui.mjs` verde.
    - Os 4 testes Node passam e `npx vite build` termina sem erro.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| cliente → POST /api/snapshot | patrimônio do dia é calculado no cliente e persistido pelo servidor (pré-existente, não alterado) |
| optionPositions (kv do escopo) → valor_opcoes | dado do próprio usuário, pode conter itens legados malformados |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-bwv-01 | Tampering | store.valor_opcoes / portfolioMetrics | mitigate | entradas não numéricas leem 0, bool/0/negativo/string como cotação caem no avg (caso G da fixture); nenhuma exceção derruba pet:evolucao |
| T-bwv-02 | Information disclosure | _pet_resumo_evolucao | accept | lê só optionPositions do próprio `scope` (current_scope), mesmo isolamento já usado para positions/cash |
| T-bwv-03 | Repudiation/Integrity | equitySnapshots | mitigate | upsert_snapshot não é tocado; teste prova snapshots passados byte-idênticos |
| T-bwv-04 | Spoofing (dado) | marcação sem cotação | mitigate | valor pelo avg é sempre acompanhado da linha "prêmio de abertura — sem cotação ao vivo" (opcoesSemMarcacao > 0) e da frase no Boris; nunca 0, nunca inventado |
</threat_model>

<verification>
Executor: só os testes listados nas tasks + `npx vite build`.
Orquestrador (fora do sandbox, uma vez): `cd web && npx vite build`, `npx cap copy ios`, `bash scripts/executar.sh --testes`.
Checagem manual opcional: conta com a PUT VALEV731W2 → Carteira mostra PATRIMÔNIO TOTAL igual a caixa + ações + 92,00 e a linha "opções em aberto (marcadas pelo prêmio de abertura — sem cotação ao vivo) +R$ 92,00"; Evolução mostra a mesma linha.
</verification>

<success_criteria>
- Caso VALEV731W2: caixa −92,00 e patrimônio inalterado na Carteira, Evolução e pet:evolucao.
- Fixture única com 7 casos verde no pytest e no Node (paridade front x backend com os mesmos números).
- Pernas lastreadas inalteradas; vendida subtrai; sem cotação usa avg e é sinalizada.
- Guardião antigo reconciliado com nota 2026-10-06; nenhum guardião apagado; histórico gravado intacto.
</success_criteria>

<output>
Create `.planning/quick/261006-bwv-patrim-nio-conta-op-o-comprada-sem-lastr/261006-bwv-SUMMARY.md` when done
</output>
