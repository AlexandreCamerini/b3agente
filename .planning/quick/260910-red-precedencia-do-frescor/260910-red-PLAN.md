---
quick_id: 260910-red
phase: quick-260910-red
plan: 01
type: quick
wave: 1
depends_on: []
files_modified: [web/src/opcoes/OpcoesScreen.jsx, web/tests/test_opcoes_mcp_aba_ui.mjs]
autonomous: true
---

<objective>
Achado ao vivo em produção (2026-09-10, primeira leitura real de PETR4/VALE3):
a aba mostra "frescor não medido" mesmo com o dado em dia. O frescor da
LEITURA tem precedência sobre o do STATUS, e é justamente o da leitura que
não sabe nada quando não há setups gravados.
</objective>

<context>
Log de produção que expôs o defeito:
```
leitura ticker=PETR4 setups=0 avaliou=False cache=False bloqueia=True
status  ... bloqueia=False        (mais cedo, mesma sessão: dado EM DIA)
```

Cadeia da causa:
- `options_mcp_api._frescor_da_avaliacao` deriva o frescor do que
  `evaluate_setups` devolveu. Sem setups do ticker, a tool nem é chamada
  (`avaliou=False`), e a função devolve corretamente
  `{"medido": False, "bloqueia": True}` — ela não tem de onde medir, e
  "não medido" nunca pode passar por "em dia" (ADR-027, Decisão 8). O
  backend está CERTO.
- `web/src/opcoes/OpcoesScreen.jsx:82`:
  `const frescor = (l && l.frescor) || (status.dados && status.dados.frescor) || null;`
  A leitura vence sempre. Mas a rota `/status` chamou `check_data_freshness`
  e MEDIU de verdade. A informação que não sabe mascara a que sabe.

Impacto: hoje ninguém tem setups gravados (criar setup é a Fase 5), então
**todo** usuário vê o aviso de frescor não medido, sempre, com dado fresco.

É a MESMA classe do defeito corrigido hoje em 260910-d57 (precedência de erro
escolhendo por ordem de chamada em vez de por qualidade da informação).
</context>

<tasks>
<task type="auto">
  <name>Task 1: frescor medido vence não medido</name>
  <files>web/src/opcoes/OpcoesScreen.jsx, web/tests/test_opcoes_mcp_aba_ui.mjs</files>
  <action>
  Trocar a precedência por qualidade da informação, não por origem:
  - `frescor.medido === true` vence `medido !== true`, venha da leitura ou do
    status;
  - empate (os dois medidos, ou nenhum medido) mantém a leitura, que é a
    chamada que o usuário disparou ao escolher o ticker;
  - `null` de um lado nunca vence objeto do outro.
  Extrair helper puro (`escolherFrescor(daLeitura, doStatus)`) no fim do
  arquivo, no mesmo padrão de `escolherErroOpcoes`, com comentário citando o
  achado ao vivo, a data, e a simetria com 260910-d57.

  CUIDADO com o que NÃO muda: `pregao` e `fonte` continuam com a precedência
  atual (leitura primeiro) — são carimbo do dado exibido, não medição de
  qualidade, e o pregão da leitura é o correto para o que está na tela.
  Se ao ler o código isso se revelar errado, PARE e reporte em vez de mudar.

  Guardião em `test_opcoes_mcp_aba_ui.mjs`: acrescentar asserções que travem
  a CLASSE — a escolha de frescor não pode ser um `||` simples entre
  `l.frescor` e `status.dados.frescor`; tem de haver teste de `medido`.
  Filtrar comentários antes de contar. Asserção de sanidade que falha se a
  regex parar de casar.
  </action>
  <verify>
  RED/GREEN: rodar o guardião novo contra o código de ANTES (via
  `git show HEAD:web/src/opcoes/OpcoesScreen.jsx` para arquivo temporário
  FORA do repo — nunca `git stash`) e confirmar a falha; depois com a
  correção e confirmar que passa.
  Depois: `bash scripts/executar.sh --testes` inteira E `cd web && npx vite build`.
  </verify>
  <done>Suíte e build verdes, prova RED/GREEN registrada no SUMMARY.</done>
</task>
</tasks>

<success_criteria>
Um commit atômico. Backend NÃO é tocado (ele está correto). Sem deploy, sem
bump, sem publicação — o SUMMARY deve lembrar que esta correção só chega ao
usuário depois de `bump.sh` + `publicar-web.sh` + clique no Railway.
</success_criteria>
