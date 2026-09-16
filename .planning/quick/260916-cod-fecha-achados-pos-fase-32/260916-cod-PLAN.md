---
quick_id: 260916-cod
slug: fecha-achados-pos-fase-32
date: 2026-09-16
type: quick
autonomous: true
origem:
  - .planning/phases/32-consolida-o-das-opera-es-de-op-es-na-aba-op-es-standalone/32-REVIEW.md (WR-01, IN-01, IN-02)
  - .planning/phases/32-consolida-o-das-opera-es-de-op-es-na-aba-op-es-standalone/32-VERIFICATION.md (item 8 / MULTI-02)
files_modified:
  - web/src/App.jsx
  - web/src/opcoes/CuradoriaEstruturas.jsx
  - web/tests/test_opcoes_consolidacao_ui.mjs
  - web/src/version.js
  - server/web_dist
---

<objective>
Fechar os três achados do code review da Fase 32 e a dívida de verificação do
item 8, e publicar. O que amarra os quatro num único trabalho é a publicação:
os três primeiros mudam `web/src/`, e fase/quick que toca `web/src/` sem passo
de publicação fica testada e invisível em produção.
</objective>

<contexto>
WR-01 é o achado que importa; os outros dois são higiene da extração.

`useCuradoria` (App.jsx) tem `carregando` nascendo `false` — deliberado, com
comentário: com a flag desligada não há busca em voo e a tela não pode mostrar
"Verificando…" para sempre. A flag `curadoriaAtiva` é monotônica e liga por
`useEffect` ao visitar Posições ou Opções, NUNCA em boot (mitigação T-32-03 de
DoS auto-infligido contra o orçamento de requisições).

A consequência não intencional: no render em que o usuário CHEGA em Posições,
`curadoriaAtiva` ainda é `false` e `carregando` é `false`, então
`LinhaChamadaOpcoes` cai no ramo `top.length === 0` e afirma "Nenhuma
oportunidade de opções agora" ANTES de a varredura começar. É a mesma classe
de erro que a Fase 32 acabou de corrigir na curadoria (princípio 4: não
afirmar resultado que ninguém mediu), com gravidade menor — dura poucos ciclos
de render, no máximo uma vez por sessão.

A correção NÃO pode reintroduzir "Verificando…" eterno: se o componente passar
a tratar "flag desligada" como carregando de forma incondicional, qualquer tela
que renderize a linha sem nunca ligar a flag trava no texto de carregamento.
O estado a distinguir é "ainda não terminou a primeira busca" × "terminou e
não achou nada" — não "flag ligada ou não".
</contexto>

<tasks>

<task type="auto">
  <name>Task 1: WR-01 — a linha não afirma "nenhuma" antes de medir</name>
  <files>web/src/App.jsx, web/tests/test_opcoes_consolidacao_ui.mjs</files>
  <read_first>
    - `web/src/App.jsx` `useCuradoria` (~4140-4180): os estados, o `useEffect` com guarda `if (!ativo) return;` e o comentário que explica por que `carregando` nasce `false`.
    - `web/src/App.jsx` `LinhaChamadaOpcoes` (~4216-4240): a cadeia de precedência `erro > carregando > vazio > n≥1`.
    - `web/src/App.jsx` (~7706-7719): a flag `curadoriaAtiva` e o `useEffect` que a liga.
    - `.planning/phases/32-.../32-REVIEW.md` seção WR-01.
  </read_first>
  <action>
Fazer `useCuradoria` expor um estado explícito de "a primeira busca já
terminou" — sugestão: `concluido` (nasce `false`, vira `true` no `finally` da
primeira busca e no ramo de erro). `LinhaChamadaOpcoes` passa a exibir o texto
de VAZIO apenas quando `concluido === true`; enquanto `!concluido && !erro`,
usa o texto de carregando.

NÃO usar `carregando` para isso: ele significa "requisição em voo" e é lido em
outro lugar; sobrecarregá-lo para significar também "ainda não comecei"
reintroduz o "Verificando…" eterno que o comentário atual previne.

O comentário existente que justifica `carregando` nascer `false` NÃO se apaga —
ganha a nota de que o estado "ainda não buscou" passou a ser expresso por
`concluido`, com a data e a referência a WR-01 (guardrail: reversão/ajuste
deliberado atualiza o comentário, não o apaga).

Verificar se `ctx.curadoria` precisa carregar o campo novo para `OpcoesScreen`
— se o bloco da curadoria lá também distingue vazio de não-medido, aplicar a
mesma precedência; se não, deixar como está e dizer por quê no SUMMARY.

Guardião: `web/tests/test_opcoes_consolidacao_ui.mjs` ganha regra que reprova
`LinhaChamadaOpcoes` exibindo o texto de vazio sem checar o estado de
conclusão. A regra tem de FALHAR se alguém reverter a correção — provar isso
por injeção real de defeito e reversão limpa, como o Plano 32-04 fez com
MULTI-02.
  </action>
  <verify>
    <automated>bash scripts/executar.sh --testes &amp;&amp; npm --prefix web run build</automated>
  </verify>
  <acceptance_criteria>
    - Nenhum caminho de render exibe o texto de vazio antes de a primeira varredura terminar.
    - Nenhum caminho exibe o texto de carregando indefinidamente quando a flag nunca liga (conferir lendo os call sites, não só o componente).
    - A precedência `erro > carregando/não-medido > vazio > n≥1` continua valendo; erro segue sem mostrar número.
    - Guardião novo falha com o defeito injetado e passa depois da reversão; evidência no SUMMARY.
  </acceptance_criteria>
  <done>A linha de chamada nunca afirma um resultado que o motor não mediu.</done>
</task>

<task type="auto">
  <name>Task 2: IN-01 e IN-02 — higiene da extração</name>
  <files>web/src/App.jsx, web/src/opcoes/CuradoriaEstruturas.jsx</files>
  <read_first>
    - `web/src/App.jsx:24-25` — os imports `PayoffChart`/`estruturaParaPayoff`.
    - `web/src/opcoes/CuradoriaEstruturas.jsx:86,156` — as duas ligações de `item`.
  </read_first>
  <action>
IN-01: remover os imports órfãos de `App.jsx` APÓS confirmar por grep que não
resta uso no arquivo (inclusive dentro de string/JSX). Se houver qualquer uso,
não remover e registrar o motivo.

IN-02: renomear a variável sombreada em `CuradoriaEstruturas.jsx` para algo que
diga o que ela é no escopo interno. É renome local, sem mudança de
comportamento — o diff não pode alterar nenhuma expressão além do nome.
  </action>
  <verify>
    <automated>bash scripts/executar.sh --testes &amp;&amp; npm --prefix web run build</automated>
  </verify>
  <acceptance_criteria>
    - `grep -n "PayoffChart\|estruturaParaPayoff" web/src/App.jsx` não devolve import algum (comentário de histórico pode permanecer).
    - Nenhuma asserção de guardião perdida; contagem de `ok(` por arquivo igual ou maior.
  </acceptance_criteria>
  <done>Sobras da extração da Fase 32 removidas sem mudança de comportamento.</done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <name>Task 3: Item 8 — ver o ramo multi-candidato rodando</name>
  <files>(nenhum arquivo de produção é modificado)</files>
  <read_first>
    - `server/app/opcoes_lastreadas.py` ~240-300 — o ramo que decide `tipo`, e por que o collar é tentado SEMPRE que a leitura é de proteção.
    - `web/src/opcoes/OpcoesScreen.jsx` — o ramo `candidatos.length > 1` de `SubAbaOperar`.
  </read_first>
  <action>
O ramo multi-candidato só renderiza quando `propor()` devolve 2 candidatos, e
isso exige `tipo == "put_protecao"` — ou seja, plano com `decisao == "VENDER"`
ou `lado == "baixa"` (opcoes_lastreadas.py:247). Com leitura de alta ou plano
vazio a função devolve `sem_setup` e nunca há coexistência.

Portanto a fixture é ESCOLHER A POSIÇÃO CERTA, não alterar código de produção:

1. Subir `api-qa-opcoes` (mercado aberto + `B3_OPTIONS_PROVIDER=mock`) e o `web`.
2. Achar, entre os ativos varridos, um cujo plano leia VENDER/baixa — consultar
   o motor de setups em vez de adivinhar pelo gráfico.
3. Comprar esse ativo em quantidade que deixe lastro livre E caixa suficiente
   para a put isolada (a put exige `cash >= 100 * premio` por contrato; sem
   caixa o ramo devolve só o collar e a coexistência não aparece).
4. Abrir a sub-aba Operar nessa posição e confirmar VISUALMENTE: dois cartões
   `CandidatoOpcao` lado a lado, mesma largura, um de put de proteção e outro
   de collar.
5. Capturar screenshot como evidência e registrar no SUMMARY o ticker, o plano
   lido (decisão/lado), os dois tipos e as quantidades.

Se, esgotada a varredura, nenhum ativo produzir a coexistência no mock,
registrar isso explicitamente — a dívida continua aberta e honesta, e
`32-VERIFICATION.md` permanece `human_needed`. NÃO forçar o cenário editando
código de produção só para o teste passar.
  </action>
  <resume-signal>Screenshot com os dois cartões, ou o registro de que o mock não produz a coexistência</resume-signal>
  <acceptance_criteria>
    - O SUMMARY registra o ticker, `decisao`/`lado` lidos e os dois tipos de candidato — ou a constatação negativa com o que foi tentado.
    - Nenhum arquivo de `server/app/` ou `web/src/` foi alterado para produzir o cenário.
  </acceptance_criteria>
  <done>O ramo multi-candidato foi visto renderizando, ou está registrado por que não pôde ser.</done>
</task>

<task type="auto">
  <name>Task 4: Bump, publicação e push nas duas branches</name>
  <files>web/src/version.js, server/web_dist, server/app/main.py</files>
  <read_first>
    - `.planning/phases/32-.../32-05-SUMMARY.md` seção "Task 3" — a sequência que acabou de ser executada, incluindo os detalhes do sandbox.
  </read_first>
  <action>
1. `git fetch origin main` e conferir que `origin/main` é ancestral do HEAD
   (usar `origin/main`, NUNCA a branch local `main`, que está atrasada).
2. `bash scripts/bump.sh`.
3. `bash scripts/publicar-web.sh` — precisa rodar FORA do sandbox (`npm ci`
   exige o registry; o sandbox derruba o TLS com "failed to copy trust
   settings of system certificate").
4. Reescrever à mão o comentário do `SERVER_BUILD_ID` para descrever ESTA
   entrega, preservando o texto anterior como HISTORICO na mesma linha.
5. `bash scripts/executar.sh --testes` depois do bump — exit 0.
6. Commit dos artefatos; `git status --porcelain` vazio ao final.
7. Push em `v2/interacao-estrutural` E `git push origin HEAD:main`.
8. Confirmar por HTTP que `boris.semente.dev/api/health` carimba a versão nova.
  </action>
  <verify>
    <automated>bash scripts/executar.sh --testes &amp;&amp; git status --porcelain</automated>
  </verify>
  <acceptance_criteria>
    - `git rev-parse HEAD` == `git rev-parse origin/main`.
    - O carimbo consultado por HTTP bate com o gerado pelo `bump.sh`, registrado no SUMMARY.
    - `server/web_dist` regenerado pelo script, sem hunk manual.
  </acceptance_criteria>
  <done>A correção está em produção, com o carimbo confirmado por consulta HTTP.</done>
</task>

</tasks>

<output>
Create `.planning/quick/260916-cod-fecha-achados-pos-fase-32/260916-cod-SUMMARY.md` when done.
</output>
