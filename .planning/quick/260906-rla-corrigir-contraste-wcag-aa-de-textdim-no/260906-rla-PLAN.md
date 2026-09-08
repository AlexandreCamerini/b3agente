---
phase: quick-260906-rla
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - web/src/App.jsx
  - web/tests/test_brand_book_v2_tokens.mjs
  - .planning/PROJECT.md
autonomous: true
requirements: [FIX-C16-COLATERAL]
must_haves:
  truths:
    - "O texto em textDim do tema claro (Modo Estudo) passa WCAG AA (>= 4.5:1) nas TRES superficies onde renderiza: bgBase, bgPanel e bgCard"
    - "Os outros 3 textDim (PALETTE.dark, MODE_OPERADOR.dark, MODE_OPERADOR.light) permanecem com o hex original"
    - "Um guardiao de teste falha se qualquer textDim voltar a reprovar AA em qualquer das 3 superficies"
    - "A suite canonica completa (pytest + web/tests) sai verde"
    - "PROJECT.md nao lista mais o achado em Active e registra o fix em Validated"
  artifacts:
    - path: "web/src/App.jsx"
      provides: "PALETTE.light.textDim = #646b7f com comentario datado no estilo FIX-C16"
      contains: "textDim: \"#646b7f\""
    - path: "web/tests/test_brand_book_v2_tokens.mjs"
      provides: "Guardiao de contraste da secao 5 estendido de textFaint para textFaint + textDim"
      contains: "textDim"
    - path: ".planning/PROJECT.md"
      provides: "Achado movido de Active para Validated"
  key_links:
    - from: "web/tests/test_brand_book_v2_tokens.mjs"
      to: "web/src/App.jsx"
      via: "parser scheme() le o bloco PALETTE/MODE_OPERADOR do fonte e mede contraste"
      pattern: "textFaint\", \"textDim"
---

<objective>
Corrigir o contraste WCAG AA de `PALETTE.light.textDim` no tema claro do Modo
Estudo (`#6b7288` -> `#646b7f`) e fechar a lacuna do guardiao que deixou esse
token passar.

Purpose: achado colateral da Fase 4 / FIX-C16, catalogado em `.planning/PROJECT.md`
seccao Active e nunca corrigido. O hex atual mede **4,203:1** contra `bgPanel`
(`#eef0f7`), abaixo do minimo AA de 4,5:1. Pior: como `textFaint` ja foi
corrigido para 4,56:1 na Fase 4, hoje a hierarquia visual esta **invertida** no
tema claro — o token que deveria ler como mais apagado (`textFaint`) contrasta
MAIS que o `textDim`.

Output: token corrigido, guardiao de teste estendido (anti-regressao), PROJECT.md
atualizado.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/STATE.md

@web/src/App.jsx
@web/tests/test_brand_book_v2_tokens.mjs

<measurements>
<!-- Medicoes CONFIRMADAS pelo planner com a formula WCAG de luminancia -->
<!-- relativa (mesma do `contrast()` em test_brand_book_v2_tokens.mjs:80). -->
<!-- O executor NAO precisa remedir — os numeros abaixo sao a fonte. -->

PALETTE.light (Modo Estudo, tema claro):
  superficies: bgBase #f7f8fc | bgPanel #eef0f7 | bgCard #ffffff

  textDim ATUAL  #6b7288 -> 4,510 | 4,203 (REPROVA AA) | 4,786
  textDim NOVO   #646b7f -> 5,008 | 4,667 (passa)      | 5,315

  Derivacao do novo hex: mesmo matiz HSL preservado (H=225,5 graus, S=0,119),
  so a luminosidade reduzida (L 0,476 -> 0,446). Metodologia identica a do
  FIX-C16 original e a do dourado claro #8a6c1c (seccao 3 do teste).
  Margem resultante fica na mesma faixa dos outros hex do FIX-C16 nesta
  paleta (4,55:1 a 4,93:1).

Os OUTROS TRES textDim ja passam AA e NAO devem ser tocados:
  PALETTE.dark        L69  #8890a8 -> 5,876 | 5,490 | 5,149 (pior: bgCard)
  MODE_OPERADOR.dark  L138 #8492ac -> 6,226 | 5,909 | 5,589 (pior: bgCard)
  MODE_OPERADOR.light L158 #5c6d67 -> 5,019 | 4,695 | 5,471 (pior: bgPanel)
</measurements>

<test_findings>
<!-- Levantamento ja feito pelo planner. NAO refazer a busca. -->

1. NENHUM teste faz match hardcoded no hex antigo `#6b7288`. Busca feita em
   `web/tests/*.mjs`, `server/tests/*.py`, `*.js`, `*.jsx`. As unicas
   ocorrencias fora de `App.jsx:91` estao em documentos ARQUIVADOS de
   planejamento (`.planning/milestones/v1.1-phases/04-*`), que sao historico e
   NAO se reescrevem (regra do CLAUDE.md). Portanto: nenhum guardiao a
   atualizar, e nada a apagar.

2. A LACUNA REAL esta em `web/tests/test_brand_book_v2_tokens.mjs`, secao 5
   (linhas 175-190): o loop que checa AA nas TRES superficies cobre apenas
   `textFaint`. O bloco de contraste anterior (linha 163) cobre
   `textPrimary/textMuted/accent/positive/negative` mas so contra o CARD.
   `textDim` nunca entrou em nenhum dos dois — e por isso o bug de 4,203:1
   sobreviveu a Fase 4 e a todo o milestone v1.5. O proprio comentario da
   linha 175-180 nomeia essa classe de omissao ("testar so o card... e a
   omissao que originou o bug").

3. O bloco NEUTROS (linhas 101-106) fixa hex literais de v2 mas NAO inclui
   `textDim` — logo, mudar o valor nao quebra essa checagem.

4. O parser `scheme()` (linha 45) captura qualquer par `chave: "#hex"` do
   bloco, entao `textDim` ja esta disponivel em `estudo[tema]`/`operador[tema]`
   sem nenhuma mudanca de infraestrutura no teste.

5. `web/tests/test_mode_operador_light_palette.mjs:27` itera sobre `textDim`
   mas so compara PALETTE.light vs MODE_OPERADOR.light para garantir que os
   valores DIFEREM. `#646b7f` != `#5c6d67`, entao continua passando.
</test_findings>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Corrigir PALETTE.light.textDim e documentar no estilo FIX-C16</name>
  <files>web/src/App.jsx</files>
  <action>
Na linha 91 de `web/src/App.jsx`, dentro de `PALETTE.light`, trocar
`textDim: "#6b7288"` por `textDim: "#646b7f"`. Nao alterar nenhum outro token
dessa mesma linha (`textPrimary`, `textSecondary`, `textMuted` ficam intocados).

Acrescentar um comentario ACIMA da linha 91, no MESMO formato dos comentarios
"FIX-C16 (REPORT-01)" que ja existem nas linhas 70-73, 92-94, 135-137 e 155-157
(prosa curta, indentada com 4 espacos, "o hex antigo media X:1 ... Este e o
mesmo tom com luminosidade ajustada: ... (pior caso Z)"). O comentario deve
deixar explicito, alem dos numeros:
  - que este e um achado COLATERAL da Fase 4, FORA do escopo do C-16 original
    (que corrigiu `textFaint` nesta mesma paleta mas nao `textDim`);
  - a data de hoje, 2026-09-06;
  - os numeros confirmados: antigo 4,51 / 4,20 (reprova, pior caso bgPanel) /
    4,79; novo 5,01 / 4,67 / 5,32;
  - opcionalmente, a consequencia que motivou o fix: com `textFaint` ja em
    4,56:1, o `textDim` a 4,20:1 invertia a hierarquia visual pretendida no
    tema claro.

Escrever o comentario em PT-BR, sem acento omitido (o arquivo usa acentuacao
normal), seguindo o tom seco dos comentarios vizinhos — eles carregam historia
de decisao, nao reafirmam o que o codigo diz.

NAO tocar em `textFaint`, nem em `PALETTE.dark.textDim` (linha 69), nem em
`MODE_OPERADOR.dark.textDim` (linha 138), nem em `MODE_OPERADOR.light.textDim`
(linha 158). NAO tocar em nenhum outro token de cor.
  </action>
  <verify>
    <automated>grep -n 'textDim' web/src/App.jsx | grep -c '#646b7f\|#8890a8\|#8492ac\|#5c6d67' | grep -q '^4$' &amp;&amp; ! grep -q '6b7288' web/src/App.jsx &amp;&amp; echo OK</automated>
  </verify>
  <done>`PALETTE.light.textDim` vale `#646b7f`, com comentario datado 2026-09-06 acima da linha; os outros 3 `textDim` seguem com o hex original; `6b7288` nao aparece mais em `web/src/App.jsx`.</done>
</task>

<task type="auto">
  <name>Task 2: Estender o guardiao de contraste da secao 5 para cobrir textDim</name>
  <files>web/tests/test_brand_book_v2_tokens.mjs</files>
  <action>
Fechar a lacuna que deixou este bug passar: no loop da secao 5
(linhas 181-190), que hoje mede apenas `p.textFaint` contra as tres superficies,
adicionar um loop interno sobre os DOIS tokens — `textFaint` e `textDim` — de
forma que as 4 combinacoes (Estudo/Operador x dark/light) x 3 superficies x 2
tokens sejam medidas. Manter a assercao `razao >= 4.5` e o formato da mensagem
do `ok(...)` (nome/tema, token, hex, superficie, hex da superficie, razao com 2
casas, referencia ao criterio) — apenas parametrizar o nome do token na string.

Isto ADICIONA cobertura; nada e removido nem afrouxado (regra do repo:
guardiao de teste nao se apaga). O `textFaint` continua sendo medido
exatamente como hoje.

Estender tambem o comentario de bloco das linhas 175-180 com uma nota datada
(2026-09-06) registrando por que `textDim` entrou: o FIX-C16 original corrigiu
`textFaint` e este guardiao so o cobriu, entao `PALETTE.light.textDim` seguiu
em 4,203:1 contra `bgPanel` por todo o v1.1 e o v1.5 sem nenhum teste
reclamando — exatamente a mesma classe de omissao que o comentario original ja
descreve ("testar so o card ... e a omissao que originou o bug"), so que na
dimensao do TOKEN em vez da dimensao da SUPERFICIE.

Referencia dos valores esperados (todos passam apos a Task 1, confirmado pelo
planner): Estudo/dark 5,88/5,49/5,15; Estudo/light 5,01/4,67/5,32;
Operador/dark 6,23/5,91/5,59; Operador/light 5,02/4,70/5,47. Com o hex ANTIGO
o caso Estudo/light/bgPanel daria 4,20 e o teste falharia — e essa a prova de
que o guardiao morde.

Nao alterar nenhuma outra secao do arquivo (NEUTROS, acentos, LogoMark).
  </action>
  <verify>
    <automated>node web/tests/test_brand_book_v2_tokens.mjs &amp;&amp; node web/tests/test_brand_book_v2_tokens.mjs 2>&amp;1 | grep -qi 'textDim' &amp;&amp; echo GUARDIAO-OK</automated>
  </verify>
  <done>O teste passa e sua saida inclui medicoes nomeadas de `textDim` para os 4 esquemas x 3 superficies; `textFaint` continua medido; nenhuma assercao foi removida ou relaxada.</done>
</task>

<task type="auto">
  <name>Task 3: Rodar a suite canonica e mover o achado de Active para Validated no PROJECT.md</name>
  <files>.planning/PROJECT.md</files>
  <action>
Primeiro rodar a suite canonica COMPLETA — `bash scripts/executar.sh --testes`
(pytest do backend + todos os `web/tests/*.mjs`). `scripts/test.sh` sozinho nao
conta como validacao (regra do CLAUDE.md do repo). Confirmar codigo de saida 0
antes de qualquer edicao no PROJECT.md. Se algo falhar, corrigir a causa e
rodar de novo — nao seguir com a suite vermelha.

Nao e necessario `npx vite build`: a mudanca e um literal de string dentro de
um objeto ja existente, sem alteracao de sintaxe JS ou de estrutura de
componente; e os dois testes que fazem parse do `App.jsx` (o guardiao da Task 2
e `test_mode_operador_light_palette.mjs`) ja exercitam o bloco alterado. Se o
executor tiver feito qualquer edicao estrutural alem do literal e do
comentario, ai sim rodar `npx vite build` antes de declarar ok.

Depois da suite verde, editar `.planning/PROJECT.md`:

1. Na secao `### Active` (linha ~292), REMOVER o item de 3 linhas que comeca
   com "`textDim` do tema claro tambem reprova contraste WCAG AA (4.20:1)".
   Nao mexer nos outros itens de Active.

2. Na secao `### Validated` (linha ~160), ADICIONAR uma entrada nova no fim da
   lista, no mesmo formato dos itens existentes (marcador `- ✓`, prosa
   compacta), registrando: token `PALETTE.light.textDim` do tema claro (Modo
   Estudo); hex antigo `#6b7288` -> novo `#646b7f`; contraste contra `bgPanel`
   de 4,20:1 (reprovava AA) para 4,67:1, e as outras duas superficies subindo
   junto (bgBase 4,51 -> 5,01; bgCard 4,79 -> 5,32); que era achado COLATERAL
   da Fase 4, fora do escopo do C-16 original (que cobriu `textFaint` mas nao
   `textDim`); que o guardiao `test_brand_book_v2_tokens.mjs` secao 5 foi
   estendido de `textFaint` para `textFaint`+`textDim` nas 3 superficies, o que
   fecha a lacuna que permitiu o bug sobreviver a Fase 4 e ao v1.5; corrigido
   em 2026-09-06.

NAO fazer bump de build nem `publicar-web.sh` — este e um fix de fonte, sem
deploy nesta task.
  </action>
  <verify>
    <automated>bash scripts/executar.sh --testes &amp;&amp; ! grep -q 'textDim` do tema claro também reprova' .planning/PROJECT.md &amp;&amp; grep -q '646b7f' .planning/PROJECT.md &amp;&amp; echo OK</automated>
  </verify>
  <done>`bash scripts/executar.sh --testes` sai com codigo 0 (pytest + web/tests); o item nao aparece mais em `### Active`; ha uma entrada nova em `### Validated` citando o token, os dois hex, o contraste antes/depois, a origem colateral na Fase 4 e a data 2026-09-06.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

Nenhuma. A mudanca e um literal de cor em um objeto de tokens de tema
(`web/src/App.jsx`), consumido apenas como valor de CSS custom property. Nao ha
entrada de usuario, chamada de rede, persistencia, nem superficie de API tocada.

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-quick-01 | Tampering | `PALETTE`/`MODE_OPERADOR` em `web/src/App.jsx` | mitigate | Edicao de um unico literal, cercada pelo guardiao estendido da Task 2 que mede AA nos 4 esquemas x 3 superficies — regressao em qualquer `textDim` ou `textFaint` derruba a suite |
| T-quick-02 | Information Disclosure | — | accept | Sem dado sensivel envolvido; token de cor publico no bundle por natureza |
| T-quick-SC | Tampering | npm/pip/cargo installs | n/a | Nenhuma dependencia adicionada ou alterada; `npm install` explicitamente fora de escopo |
</threat_model>

<verification>
- `bash scripts/executar.sh --testes` sai com codigo 0 (suite canonica completa: pytest do backend + `web/tests/*.mjs`).
- `grep -n "textDim" web/src/App.jsx` mostra 4 ocorrencias: `#646b7f` em `PALETTE.light` e os outros tres (`#8890a8`, `#8492ac`, `#5c6d67`) intocados. Nenhuma ocorrencia de `6b7288`.
- `node web/tests/test_brand_book_v2_tokens.mjs` imprime medicoes nomeadas de `textDim` para Estudo/Operador x dark/light x bgBase/bgPanel/bgCard, todas >= 4,5:1.
- Prova de que o guardiao morde: reverter mentalmente para `#6b7288` faria o caso `Estudo/light: textDim sobre bgPanel` medir 4,20:1 e falhar.
- `.planning/PROJECT.md` nao lista mais o item em `### Active` e registra o fix em `### Validated`.
</verification>

<success_criteria>
- `PALETTE.light.textDim === "#646b7f"`, com comentario datado no estilo FIX-C16 explicando origem colateral (Fase 4), numeros antes/depois e a data 2026-09-06.
- Os outros tres `textDim` do arquivo permanecem byte-identicos.
- Guardiao de contraste estendido cobre `textDim` alem de `textFaint`, sem remover nem relaxar nenhuma assercao existente.
- Suite canonica verde.
- PROJECT.md: item fora de `### Active`, registrado em `### Validated`.
</success_criteria>

<output>
Create `.planning/quick/260906-rla-corrigir-contraste-wcag-aa-de-textdim-no/260906-rla-SUMMARY.md` when done
</output>
