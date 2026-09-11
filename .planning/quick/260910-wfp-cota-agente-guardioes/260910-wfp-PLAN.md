---
quick_id: 260910-wfp
phase: quick-260910-wfp
plan: 01
type: quick
wave: 1
depends_on: []
files_modified: [server/app/metering.py, server/app/agent.py, server/tests/test_metering.py, server/tests/test_agent.py, server/tests/test_adr013_cobertura_rotas.py, server/tests/test_fase3_gate_plano.py]
autonomous: true
---

<objective>
Últimos quatro achados de peso da auditoria de 2026-09-10. Dois têm
consequência real (dinheiro e afirmação falsa ao usuário); dois são guardiões
provados cegos por reintrodução do defeito.
</objective>

<tasks>
<task type="auto">
  <name>Task 1 (A-07): reserva atômica da cota de IA</name>
  <files>server/app/metering.py, server/tests/test_metering.py</files>
  <action>
  `check()` (metering.py:146) compara `count` com `quota` mas NÃO reserva;
  `consume()` (:194) só roda depois da resposta do modelo, que espera até 60 s.
  Reproduzido pela auditoria: `used=4 quota=5`, três requisições concorrentes
  passam todas, estado final `used=7`. Como a cota gerenciada usa a chave PAGA
  do servidor, o excesso é gasto real. O mesmo buraco existe no `cap_global`.

  **CUIDADO — este módulo governa TODA rota de IA do produto.** O contrato
  atual é: `check` não cobra, `consume` cobra só no sucesso (falha não gasta
  cota). Preserve essa propriedade: a correção é reservar em `check` e
  DEVOLVER quando a chamada falhar, não passar a cobrar falha.

  Leia `_gate_analise`/`_ai_apply_managed` em `main.py` (~467-520) antes: o
  `consume` é devolvido como closure e chamado pelo caller. A devolução em
  caso de falha precisa de um caminho — decida lendo (closure de estorno?
  try/except no caller? `consume` idempotente por id de reserva?) e explique
  a escolha no comentário. Se a mudança exigir tocar os callers, PARE e
  reporte o escopo antes de seguir.

  Teste: reproduzir a corrida do relatório (três tasks concorrentes com
  `used=quota-1`) e provar que só uma passa; e provar que falha devolve a
  reserva (cota não é consumida quando o modelo não responde).
  </action>
  <verify>pytest test_metering.py e os testes de gate/cota que já existem (test_fase3_gate_plano.py, test_fase5_gate_mensal.py) — nenhum pode quebrar</verify>
  <done>Corrida reproduzida falha antes e passa depois; falha continua não cobrando.</done>
</task>

<task type="auto">
  <name>Task 2 (A-08): o agente não anuncia venda que não houve</name>
  <files>server/app/agent.py, server/tests/test_agent.py</files>
  <action>
  `agent.py:955-962`: quando `pnl is None` (a posição sumiu entre a leitura e
  a venda — outro caminho já vendeu), o ciclo ainda faz `executed += 1`,
  `_bump_ops(...)` e emite evento `kind:"buy"` com o texto "Proteção simulada:
  X vendido". O texto do resultado JÁ é condicional a `pnl is not None`
  (linha 958) — o que falta é condicionar o RESTO.

  Consequências medidas pela auditoria: o Diário registra venda que não
  aconteceu, o funil de push dispara "vendido" ao usuário, e o teto diário de
  operações é consumido por operação inexistente. Nenhum número de carteira é
  afetado. Viola o princípio 9.

  Correção: `executed`, `_bump_ops` e o evento `kind:"buy"` só quando
  `pnl is not None`. Quando for `None`, emitir evento informativo dizendo que
  a posição já não estava lá (estado correto, não silêncio — princípio 9), ou
  nenhum evento se isso poluir o Diário; decida e justifique no comentário.
  `ORDER_LOCK` NÃO é a correção (o ciclo teria de segurar a trava atravessando
  espera de rede, o que o repositório proíbe).

  Teste: ciclo com posição que desaparece antes da venda → nenhum evento
  `kind:"buy"`, `executed` não incrementa, teto diário não consome.
  </action>
  <verify>pytest test_agent.py e test_agent_options.py inteiros</verify>
  <done>Venda fantasma não produz evento de venda nem consome teto.</done>
</task>

<task type="auto">
  <name>Task 3 (A-17): guardião de permissões enxerga rotas de router</name>
  <files>server/tests/test_adr013_cobertura_rotas.py</files>
  <action>
  `test_adr013_cobertura_rotas.py:59` varre `app.routes` procurando `.path`,
  mas o FastAPI 0.141 insere `_IncludedRouter` com `.path is None` — 7 rotas
  ficam invisíveis (4 em `/api/options/*`, 3 em `/api/options/mcp/*`).
  **Provado cego pela auditoria:** removendo o `require_user` da rota de
  status do MCP, o guardião PASSOU; o guardião irmão falhou corretamente.

  Correção: varredura recursiva, reusando o helper `_todas_as_rotas()` que já
  existe em `server/tests/test_mcp_guardioes.py` (resolve `.original_router`).
  Extrair para lugar compartilhado em vez de terceira cópia, se couber.
  A allowlist de rotas públicas vai crescer para acomodar as 4 rotas antigas
  de `/api/options/*` que são públicas por desenho — documente cada uma com o
  motivo, e atualize a asserção de tamanho da allowlist com nota datada.
  Atualizar o guardião COM NOTA, nunca apagar.

  Prova obrigatória: reintroduza o defeito (remova um gate de uma rota de
  router, por monkeypatch em memória) e mostre que o guardião agora FALHA.
  </action>
  <verify>pytest do arquivo; a prova de cegueira invertida</verify>
  <done>Rota de router sem gate faz o guardião falhar.</done>
</task>

<task type="auto">
  <name>Task 4 (A-18): filtro de comentário que não deixa passar comentário de cauda</name>
  <files>server/tests/test_fase3_gate_plano.py (+ as outras duas cópias do helper)</files>
  <action>
  `_main_source_sem_comentarios()` só descarta linha que COMEÇA com `#`.
  **Provado:** a auditoria removeu a única chamada real ao gate comercial e
  deixou o nome da função num comentário de cauda; a asserção de contagem
  continuou passando. O helper está duplicado em três arquivos
  (`test_fase3_gate_plano.py`, `test_fase12_cap_watchlist.py`,
  `test_fase5_gate_mensal.py`) que podem divergir.

  Correção: cortar a linha no primeiro `#` (cuidado com `#` dentro de string
  literal — decida se isso importa aqui e justifique) e extrair o helper para
  UM módulo compartilhado usado pelos três.

  Prova obrigatória: reintroduzir o bypass com comentário de cauda e mostrar
  que a asserção agora FALHA.
  </action>
  <verify>pytest dos três arquivos; a prova de bypass invertida</verify>
  <done>Bypass escondido em comentário de cauda não passa mais.</done>
</task>
</tasks>

<success_criteria>
Commits atômicos por task, PT-BR, referenciando o achado. Front NÃO é editado.
Deploy disto é só-backend (bump manual) — NÃO fazer. Guardiões atualizados com
nota, nunca apagados.
</success_criteria>
