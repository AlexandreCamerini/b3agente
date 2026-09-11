---
quick_id: 260911-axj
phase: quick-260911-axj
plan: 01
type: quick
wave: 1
depends_on: []
files_modified: [server/app/agent.py, server/app/radar_daily.py, server/app/analysis_outcomes.py, server/app/fundamentals.py, server/app/intraday.py, server/tests/test_agent.py]
autonomous: true
---

<objective>
Achado ao vivo no painel de administração (2026-09-11, relatado pelo Alex):
quatro jobs aparecem como **"nunca rodou"**. A investigação mostrou que eles
muito provavelmente RODARAM — o painel é que esquece a cada reinício do
container, e reiniciamos produção quatro vezes hoje (deploys `-01` a `-04`).
</objective>

<context>
Os quatro marcadores que o painel lê são dicts de MÓDULO, em memória do
processo, e nenhum é lido do banco:
- `radar_daily.LAST_DAILY` (`radar_daily.py:40`)
- `analysis_outcomes.LAST_EVAL` (`analysis_outcomes.py:88`)
- `fundamentals.LAST_WARM` (`fundamentals.py:404`)
- `intraday.LAST_PASS` (`intraday.py:77`)

`agent.status_snapshot(conn, ...)` (`agent.py:~1534`) copia os quatro direto da
memória. **Ela já recebe `conn`**, e o arquivo já tem o precedente certo: o
heartbeat é gravado com `db.kv_set(conn, "agentHeartbeat", ...)`
(`agent.py:1207`) e lido com `db.kv_get` (`:1521`). Os quatro ficaram em
memória por esquecimento, não por decisão.

O radar JÁ persiste parte: `db.kv_set(conn, "radarDailyLastRun", ...)`
(`radar_daily.py:83`) e `last_run_date(conn)` (`:187`) — a informação correta
existe e a tela não a usa.

**Por que isso importa além do incômodo:** "nunca rodou" é afirmação sobre toda
a história do sistema; o que o painel sabe é "sem registro neste processo". É a
mesma classe dos achados corrigidos hoje (afirmar mais do que se mediu), agora
na observabilidade — e justamente onde alguém recorre para diagnosticar.
</context>

<tasks>
<task type="auto">
  <name>Task 1: marcadores de job sobrevivem ao reinício</name>
  <files>server/app/radar_daily.py, server/app/analysis_outcomes.py, server/app/fundamentals.py, server/app/intraday.py, server/app/agent.py, server/tests/test_agent.py</files>
  <action>
  Cada um dos quatro módulos passa a PERSISTIR o seu registro completo no kv
  global (`user_id=None`), no mesmo ponto onde hoje atualiza o dict de memória,
  e `status_snapshot` passa a LER do banco, caindo para a memória só quando o
  banco não tem nada.

  Desenho sugerido (decida lendo e justifique): um helper único no `agent.py`
  ou em `db.py` — `marcar_job(conn, nome, payload)` / `ler_job(conn, nome)` —
  em vez de quatro pares de `kv_set`/`kv_get` espalhados, que divergiriam no
  quinto job. Chaves no padrão do repo (camelCase, como `agentHeartbeat`).

  Invariantes:
  - **A escrita NUNCA pode derrubar o job.** `try/except` em volta, no mesmo
    padrão de `brapi_budget._persiste` ("contador é proteção, nunca derruba") e
    do próprio heartbeat. Um job que falha por não conseguir anotar que rodou é
    pior que o defeito.
  - O dict de memória CONTINUA sendo atualizado (é o que os testes existentes
    leem, e é o caminho rápido). A persistência é aditiva.
  - `status_snapshot` mantém a MESMA forma de resposta — o front
    (`web-admin/src/App.jsx:122-127`) lê `data.radarDiario?.date` etc. Nenhuma
    chave muda de nome ou de tipo.
  - Escopo global (`user_id=None`): são jobs do processo, não de usuário.

  **Distinguir os três estados**, que é o ponto do achado:
  (a) registro no banco → mostra a data real, mesmo após reinício;
  (b) sem registro no banco E sem memória → aí "nunca rodou" é VERDADE;
  (c) job que só roda em certa janela e o processo subiu depois → hoje isso
      também cai em (b). Se for baixo custo, devolva no snapshot um campo
      aditivo que permita à tela dizer "aguardando a próxima janela" em vez de
      "nunca rodou" (ex.: o `at` do boot do processo, ou o horário-alvo do
      job). Se exigir mexer no front, NÃO mexa — registre como pendência e
      deixe o backend pronto.

  Testes em `test_agent.py`: (1) marcador gravado sobrevive a um "reinício"
  (zerar o dict de memória e provar que `status_snapshot` ainda devolve a
  data); (2) banco vazio e memória vazia continuam produzindo o estado que a
  tela lê como "nunca rodou"; (3) falha de escrita no kv não propaga (espião
  que levanta em `kv_set` e o job conclui); (4) a forma do `status_snapshot`
  não muda — compare as chaves contra a lista atual.
  </action>
  <verify>pytest test_agent.py, test_agent_options.py e os testes que tocam radar/intraday/fundamentals; depois `bash scripts/executar.sh --testes`</verify>
  <done>Zerar a memória e ainda ver a data no snapshot; banco vazio ainda produz "nunca rodou"; falha de escrita não derruba job.</done>
</task>
</tasks>

<success_criteria>
Um commit atômico. Front NÃO é editado — a tela ganha o dado certo sem mudar
uma linha. Deploy só-backend (bump manual) — NÃO fazer.
</success_criteria>
