---
phase: quick-260906-ugb
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - web/src/App.jsx
  - web/tests/test_agente_modo_estudo_ui.mjs
  - server/app/kb.py
  - .planning/STATE.md
  - .planning/PROJECT.md
autonomous: true
requirements: [REPORT-01-C18, REPORT-01-C08, REPORT-01-C28]
must_haves:
  truths:
    - "O botao \"Executar (vende no stop/alvo)\" desabilitado em Modo Estudo aponta, via aria-describedby, para o paragrafo que explica o motivo — leitor de tela que cai direto no botao ouve a explicacao"
    - "O botao \"Apenas sinalizar\" (nunca desabilitado) NAO emite aria-describedby no DOM"
    - "O verbete setup-ifr2 nomeia explicitamente o principio geral de reversao a media no texto educacional"
    - "O verbete setup-ifr2 e encontravel por busca pelo termo \"reversao a media\""
    - "O texto operador do setup-ifr2 permanece byte-identico (resumo de mesa, sem camada conceitual)"
    - "Um guardiao de teste falha se o aria-describedby do botao Executar for removido"
    - "A suite canonica completa (pytest do backend + web/tests/*.mjs) sai verde, exit code 0"
    - "STATE.md e PROJECT.md refletem: C-08 e C-18 corrigidos nesta task, C-28 encontrado ja resolvido (zero mudanca de codigo), 6 achados Baixo restantes ainda no backlog"
  artifacts:
    - path: "web/src/App.jsx"
      provides: "aria-describedby condicional no botao + id no paragrafo de gate do AgenteScreen"
      contains: "executar-gate-hint"
    - path: "web/tests/test_agente_modo_estudo_ui.mjs"
      provides: "Guardiao anti-regressao do vinculo botao->explicacao (FIX-C18)"
      contains: "aria-describedby"
    - path: "server/app/kb.py"
      provides: "setup-ifr2 com termo de busca e frase conceitual de reversao a media"
      contains: "reversão à média"
    - path: ".planning/STATE.md"
      provides: "Linha do backlog de achados Baixo reduzida de 9 para 6"
    - path: ".planning/PROJECT.md"
      provides: "Os 3 achados movidos de Active para Validated"
  key_links:
    - from: "web/src/App.jsx (button do map [\"executar\",\"sinalizar\"])"
      to: "web/src/App.jsx (<p> do bloco {!operador && ...})"
      via: "aria-describedby -> id=\"executar-gate-hint\""
      pattern: "aria-describedby=\\{desabilitado \\? \"executar-gate-hint\" : undefined\\}"
    - from: "web/tests/test_agente_modo_estudo_ui.mjs"
      to: "web/src/App.jsx"
      via: "leitura do fonte + regex sobre o bloco do AgenteScreen"
      pattern: "executar-gate-hint"
---

<objective>
Fechar 3 achados Baixo do REPORT-01 (18/08/2026) reverificados contra o codigo
atual de 2026-09-06:

- **C-18 (existe, corrigir)** — o botao "Executar (vende no stop/alvo)" fica
  `disabled` fora do Modo Operador e um paragrafo logo abaixo explica o porque,
  mas nada liga os dois: leitor de tela que navega por botoes nao ouve a
  explicacao. Falta `aria-describedby`.
- **C-08 (existe, corrigir)** — o verbete `setup-ifr2` da KB explica a mecanica
  (RSI(2)<=25, filtro SMA200, saida na maxima dos 2 candles) mas nunca nomeia o
  principio geral que a sustenta: reversao a media. Nao existe verbete padrao
  de "reversao a media" em `kb.py`/`conceitos.py`/`mercado_ref.py` para
  cross-referenciar (confirmado por grep) — e caso de explicar inline, nao de
  criar link cruzado.
- **C-28 (JA RESOLVIDO, so documentar)** — o achado apontava 2 pontos com
  `appMode || "estudo"` cru (passthrough sem normalizacao). Reverificado hoje:
  `grep -n 'appMode' web/src/App.jsx | grep -v '==='` nao retorna nenhum
  `|| "estudo"`; os dois pontos (linhas 7989 e 9071) leem a variavel canonica
  `appMode`, ja normalizada pelo ternario seguro, ambos com o comentario
  "FIX-C21: le a fonte unica". O passthrough morreu como efeito colateral do
  refactor FIX-C21, antes desta sessao. **Nenhuma linha de codigo muda por
  causa de C-28.**

Purpose: os 3 estao na tabela "Deferred Items" do STATE.md e na secao Active do
PROJECT.md desde o fechamento do v1.0, sem fase mapeada. Sao fixes de fonte
simples, sem dependencia de fase nem de verificacao humana.

Output: 2 fixes reais de codigo + 1 guardiao estendido + 2 arquivos de
planejamento atualizados. Sem bump de build, sem `publicar-web.sh`.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/PROJECT.md
@CLAUDE.md
</context>

<pre_verified_facts>
Fatos ja confirmados no planejamento — o executor NAO precisa reverificar,
so usar. As linhas do REPORT-01 original (18/08) estao todas defasadas; as
linhas abaixo sao as reais em 2026-09-06.

**C-18 — `web/src/App.jsx`, dentro de `AgenteScreen`:**
- 4889: `{["executar", "sinalizar"].map((m) => {`
- 4891: `const desabilitado = m === "executar" && !operador;`
- 4897: abertura do `<button key={m} onClick={...} disabled={desabilitado}` — e AQUI que entra o `aria-describedby`
- 4904: `{!operador && (`
- 4905: abertura do `<p style={{ margin: "9px 0 0", ... }}>` — e AQUI que entra o `id`
- 4906: texto "Disponivel no Modo Operador — em Modo Estudo o agente so orienta, nunca vende sozinho."
- 4907-4909: botao-link "Trocar para Modo Operador →" (dentro do mesmo `<p>`)

**C-08 — `server/app/kb.py`, verbete `"id": "setup-ifr2"`:**
- 803: `"id": "setup-ifr2",`
- 804: `"termos": ("IFR2", "ifr2", "rsi2", "rsi(2)", "larry connors"),`
- 806-815: `"educacional"` (bloco de string implicita concatenada)
- 816-820: `"operador"` — NAO TOCAR
- 822: `"veja": ["ind-rsi", "ind-medias-lentas"],`

**C-28 — nada a fazer no codigo.** `grep -n 'appMode || ' web/src/App.jsx`
retorna vazio (exit 1). Linhas 7989 e 9071 ja estao corretas.

**Guardioes existentes que tocam essas regioes (verificados no planejamento):**
1. `web/tests/test_agente_modo_estudo_ui.mjs:41-51` — casa
   `const desabilitado = m === "executar" && !operador;`, `disabled={desabilitado}`,
   `onClick={() => !desabilitado && putAg({ mode: m })}`, o texto do `<p>` e
   `{!operador && (`. **Nenhum desses regex quebra** com as duas adicoes. E o
   arquivo certo para receber a assercao nova (Task 1).
2. `web/tests/test_auditoria_modo_link_restart.mjs:35-37` — fatia
   `blocoBotoes` = 900 chars a partir de `{["executar", "sinalizar"].map` e
   afirma NEGATIVAMENTE que `title={desabilitado ? "Disponível no Modo Operador`
   nao existe mais. Assercao negativa: crescer o bloco em ~55 chars nao a
   quebra. **Nao editar este arquivo.**
3. `server/tests/test_kb.py` — os que importam para C-08:
   - `test_todo_verbete_tem_pelo_menos_um_termo` / `test_todo_verbete_tem_texto_nos_dois_modos` — adicionar termo/texto so ajuda.
   - `test_modo_educacional_sem_verbo_de_ordem_obvio` — proibe
     `\bcompre\b`, `\bcomprem\b`, `\bvenda\s+(agora|já)\b`, `\bentre\s+agora\b`
     no texto educacional. A frase nova NAO pode conter nenhum desses.
   - `test_nenhum_texto_usa_expressao_proibida_fora_de_negacao` — vocabulario
     proibido (`EXPRESSOES_PROIBIDAS`, topo do arquivo) fora de negacao.
   - `test_buscar_e_verbete_funcionam` — exige que `kb.buscar("como funciona o
     setup IFR2")` ainda retorne `setup-ifr2`. Preservar o termo `"IFR2"`.
4. `server/tests/test_kb_espelho.py` criterio 2 — os nomes base que
   `setups._mk(...)` produz (inclui `"IFR2 (alta)"`) precisam aparecer
   normalizados como termo EXATO de algum verbete de familia "setups".
   **`"IFR2"` NAO pode sair da tupla.** Adicionar termo e seguro.
5. `kb.py` NAO tem espelho no front — `grep 'ifr2' web/src/*.js*` retorna
   vazio. A regra de paridade do CLAUDE.md e `defaults.py` <-> `catalog.js`
   (prompts), que esta task nao toca.

**Colisao de termo:** `grep -n 'revers' server/app/kb.py` mostra que
"reversao" aparece so em prosa de 4 verbetes, nunca como TERMO de busca.
Nenhum verbete tem "reversao a media" em `termos`. Sem colisao.
</pre_verified_facts>

<deviation_declared>
**Desvio deliberado da instrucao literal, com justificativa tecnica — precisa
constar no SUMMARY.**

A instrucao original pedia adicionar DOIS termos: `"reversão à média"` E
`"reversao a media"`. Este plano adiciona **apenas o acentuado**.

Motivo: `kb._pontuar` (server/app/kb.py) roda `_normalizar(termo)` em cada
termo antes de casar — e `_normalizar` faz NFD + descarta categoria Unicode
`Mn`, ou seja, remove acento e baixa a caixa. As duas formas normalizam para a
mesma string `"reversao a media"`. A forma sem acento ja e casada pela
entrada acentuada; adicionar as duas nao amplia cobertura nenhuma e faz
`_pontuar` somar `len(t)` DUAS VEZES pelo mesmo match (17 + 17 = 34 pontos em
vez de 17), inflando artificialmente o rank de `setup-ifr2` contra os outros
verbetes em `buscar()` e barateando o corte `_CONFIANCA_MIN` de `resolver()`.
Pontuacao deterministica inflada e exatamente o tipo de efeito colateral
silencioso que o principio 5 do CLAUDE.md rejeita.

Reversivel em uma linha se o Alex preferir a forma literal: basta adicionar
`"reversao a media"` a tupla, aceitando o double-count.
</deviation_declared>

<tasks>

<task type="auto">
  <name>Task 1: C-18 — ligar o botao "Executar" desabilitado a sua explicacao (aria-describedby)</name>
  <files>web/src/App.jsx, web/tests/test_agente_modo_estudo_ui.mjs</files>
  <action>
Duas edicoes cirurgicas em `web/src/App.jsx`, dentro de `AgenteScreen`:

1. Linha 4905 — no `<p>` do bloco `{!operador && (`, adicionar `id="executar-gate-hint"`
   como primeiro atributo, antes do `style`. Nada mais nesse `<p>` muda: o texto,
   o `style` e o botao-link "Trocar para Modo Operador →" ficam como estao.

2. Linha 4897 — no `<button key={m} ...>`, adicionar
   `aria-describedby={desabilitado ? "executar-gate-hint" : undefined}`
   logo depois de `disabled={desabilitado}`. O ternario e essencial: o `.map`
   renderiza DOIS botoes e para `m === "sinalizar"` a variavel `desabilitado` e
   sempre `false` — com `undefined` o React omite o atributo do DOM, entao
   "Apenas sinalizar" nao aponta para um hint que nao fala dele. Nao usar
   string vazia nem `null` condicional invertido.

Acrescentar um comentario datado no bloco de comentario que ja existe nas
linhas 4893-4896 (estilo da casa: `qa/audit-...`), na linha do
`FIX-C18 (2026-09-06)`, dizendo que o `title` invisivel em toque ja tinha sido
resolvido antes e que agora o vinculo semantico com o paragrafo fecha o lado do
leitor de tela.

Atencao ao acoplamento condicional: o `<p>` so existe no DOM quando
`!operador`, e `desabilitado` so e `true` quando `!operador` — as duas
condicoes sao a mesma, entao o `aria-describedby` nunca aponta para um id
ausente. Nao inverter nenhuma das duas condicoes.

Depois, estender o guardiao `web/tests/test_agente_modo_estudo_ui.mjs`: na
secao "texto explica" (por volta da linha 47-51, depois do `ok(...)` que casa
`{!operador && (`), adicionar DUAS assercoes novas no mesmo estilo `ok(nome, cond)`
que o arquivo ja usa, sobre a variavel `screen` (o recorte do AgenteScreen que
o teste ja monta):
  - o `<p>` de explicacao carrega `id="executar-gate-hint"`;
  - o botao carrega `aria-describedby={desabilitado ? "executar-gate-hint" : undefined}`
    (regex sobre a forma condicional exata, nao so sobre a presenca da palavra
    `aria-describedby` — o que trava e o ternario, nao o atributo solto).
Cada assercao com um comentario `FIX-C18 (2026-09-06)` acima explicando o que
prova. NAO apagar nem reescrever nenhuma assercao existente do arquivo.

NAO editar `web/tests/test_auditoria_modo_link_restart.mjs` — a assercao dele
sobre este bloco e negativa (`!title=...`) e continua verdadeira.
  </action>
  <verify>
    <automated>node web/tests/test_agente_modo_estudo_ui.mjs && node web/tests/test_auditoria_modo_link_restart.mjs && node web/tests/test_entrada_automatica_ui.mjs && grep -c 'executar-gate-hint' web/src/App.jsx</automated>
  </verify>
  <done>
`node web/tests/test_agente_modo_estudo_ui.mjs` sai 0 com as 2 assercoes novas
em "ok"; `test_auditoria_modo_link_restart.mjs` e `test_entrada_automatica_ui.mjs`
seguem verdes; `grep -c 'executar-gate-hint' web/src/App.jsx` retorna 2 (o `id`
e a referencia no ternario).
  </done>
</task>

<task type="auto">
  <name>Task 2: C-08 — nomear o principio de reversao a media no verbete setup-ifr2</name>
  <files>server/app/kb.py</files>
  <action>
Duas edicoes no verbete `"id": "setup-ifr2"` de `server/app/kb.py`
(bloco das linhas 802-823):

1. Linha 804 — adicionar `"reversão à média"` ao FIM da tupla `"termos"`,
   preservando as 5 entradas atuais na ordem em que estao. Resultado:
   `("IFR2", "ifr2", "rsi2", "rsi(2)", "larry connors", "reversão à média")`.
   **Nao adicionar a variante sem acento** — ver `<deviation_declared>` deste
   plano: `kb._pontuar` normaliza cada termo com `_normalizar` (remove acento,
   baixa caixa) antes de casar, entao a forma sem acento ja e coberta, e as
   duas juntas fariam o mesmo match contar pontuacao dobrada.
   `"IFR2"` NAO pode sair da tupla (`test_kb_espelho.py` criterio 2 e
   `test_buscar_e_verbete_funcionam` dependem dela).

2. Linhas 806-815 — inserir 1-2 frases no texto `"educacional"` nomeando
   explicitamente o principio geral. Colocar a frase LOGO NO INICIO do bloco,
   antes da mecanica: o padrao didatico do arquivo e nomear o conceito e depois
   detalhar, e o CLAUDE.md exige jargao sempre explicado antes de usado.
   Conteudo obrigatorio da frase (redacao livre dentro dessas restricoes):
     - nomear a expressao "reversao a media" com acento;
     - dizer que depois de um movimento extremo de curto prazo o preco TENDE a
       voltar em direcao a sua media (tendencia, nunca certeza — sem promessa);
     - amarrar ao que o setup mede: o RSI(2) extremo e a medida do exagero, e a
       SMA200 mantem a leitura a favor da tendencia de longo prazo.
   Manter o estilo do arquivo: string Python implicitamente concatenada, uma
   linha por trecho, frases curtas, sem markdown, sem bullet.
   O resto do texto educacional atual (setup de FECHAMENTO, saida na maxima dos
   2 candles anteriores, invalidacao por ATR) fica intacto.

3. **NAO tocar** no texto `"operador"` (816-820) nem no `"veja"` (822). O
   `"operador"` e resumo direto de mesa, sem camada conceitual — e a assimetria
   e deliberada.

Restricoes de vocabulario que a frase nova precisa respeitar (guardioes ja
existentes, ver `<pre_verified_facts>`): nada de `compre`/`comprem`/
`venda agora`/`entre agora` (`test_modo_educacional_sem_verbo_de_ordem_obvio`),
e nada da lista `EXPRESSOES_PROIBIDAS` do topo de `server/tests/test_kb.py`
fora de negacao (ler a constante antes de escrever a frase).

Nao criar verbete novo de "reversao a media" nem adicionar entrada ao `"veja"`:
o alvo nao existe em `kb.py`/`conceitos.py`/`mercado_ref.py`, e
`test_veja_nunca_e_link_morto` quebraria.
  </action>
  <verify>
    <automated>cd server && python -m pytest tests/test_kb.py tests/test_kb_espelho.py tests/test_assistente_kb.py tests/test_didatica_fonte.py tests/test_guardrail_imperativo.py -q && python -c "from app import kb; v=kb.verbete('setup-ifr2'); assert 'reversão à média' in v['texto']['educacional'], 'principio nao nomeado no educacional'; assert any(x['id']=='setup-ifr2' for x in kb.buscar('o que e reversão à média')), 'nao encontravel pelo termo novo'; assert any(x['id']=='setup-ifr2' for x in kb.buscar('como funciona o setup IFR2')), 'busca antiga quebrou'; print('ok')"</automated>
  </verify>
  <done>
Os testes de KB saem verdes; `kb.verbete('setup-ifr2')['texto']['educacional']`
contem "reversão à média"; `kb.buscar` acha `setup-ifr2` tanto pelo termo novo
quanto pela pergunta antiga; `git diff server/app/kb.py` nao mostra nenhuma
linha alterada dentro do bloco `"operador"` (816-820).
  </done>
</task>

<task type="auto">
  <name>Task 3: suite canonica completa + fechar as 3 pendencias em STATE.md e PROJECT.md</name>
  <files>.planning/STATE.md, .planning/PROJECT.md</files>
  <action>
1. Rodar a suite canonica COMPLETA: `bash scripts/executar.sh --testes`
   (pytest do backend + `web/tests/*.mjs`). Exigir exit code 0. `scripts/test.sh`
   sozinho NAO conta como validacao (regra do CLAUDE.md do repo).
   Como esta task edita `web/src/App.jsx` (Task 1), rodar tambem
   `npx vite build` a partir de `web/` — grep e teste estatico nao pegam erro
   de sintaxe JSX. Nao publicar, nao bumpar: o build aqui e so prova de sintaxe.

   Se algum guardiao NAO previsto no plano falhar por casar texto exato do
   verbete `setup-ifr2` ou do JSX do botao: atualizar o valor esperado com um
   comentario de reversao deliberada DATADO (2026-09-06) explicando o que mudou
   e por que — **nunca apagar o teste** (guardrail do CLAUDE.md). Se a falha
   nao for de snapshot mas de comportamento, parar e reportar em vez de
   relaxar a assercao.

2. `.planning/STATE.md`, tabela "Deferred Items": substituir a linha
   `| Backlog | 9 achados Baixo do REPORT-01 (C-06..C-10, C-17, C-18, C-28, C-29) | Not mapped to any phase — explicit backlog | v1.0 close |`
   por uma linha equivalente que registre:
     - 6 achados Baixo restantes, nominalmente C-06, C-07, C-09, C-10, C-17,
       C-29, ainda sem fase mapeada;
     - C-08 e C-18 corrigidos na quick task 260906-ugb (2026-09-06);
     - C-28 encontrado ja resolvido na reverificacao (efeito colateral do
       refactor FIX-C21, anterior a esta sessao) — zero mudanca de codigo.
   Manter o formato de 4 colunas da tabela e a coluna "Deferred At" como
   `v1.0 close` (a origem do deferral nao muda).

3. `.planning/STATE.md`, tabela "Quick Tasks Completed": adicionar uma linha
   para `260906-ugb` no mesmo formato das existentes (`# | Description | Date |
   Commit | Status | Directory`), Status `Verified`, apontando para
   `./quick/260906-ugb-corrigir-3-achados-baixo-do-report-01-c-/`. Preencher a
   coluna Commit com o SHA real depois do commit, ou `-` se o commit for feito
   pelo orquestrador depois deste passo.

4. `.planning/PROJECT.md`: remover das linhas 289-290 da secao `### Active` o
   item `- [ ] Backlog (não mapeado a fase ainda): os 9 achados Baixo do
   REPORT-01 (C-06..C-10, C-17, C-18, C-28, C-29)` e recoloca-lo como os 6
   restantes (C-06, C-07, C-09, C-10, C-17, C-29). Acrescentar ao FIM da secao
   `### Validated` (depois da entrada do `textDim`, linha ~278) uma entrada
   compacta no mesmo estilo `- ✓ ...` cobrindo os tres, citando:
     - C-18: `aria-describedby` condicional ligando o botao "Executar (vende no
       stop/alvo)" desabilitado ao paragrafo `id="executar-gate-hint"` que
       explica o gate, em `web/src/App.jsx` (`AgenteScreen`), com guardiao novo
       em `web/tests/test_agente_modo_estudo_ui.mjs`;
     - C-08: verbete `setup-ifr2` de `server/app/kb.py` passa a nomear o
       principio de reversao a media no texto educacional e a ser buscavel pelo
       termo; texto `"operador"` intocado de proposito;
     - C-28: encontrado JA RESOLVIDO na reverificacao — os 2 pontos de
       `appMode || "estudo"` cru sumiram no refactor FIX-C21 antes desta
       sessao; nenhuma mudanca de codigo foi necessaria.
   Datar 2026-09-06.

5. **NAO tocar** em `.planning/milestones/v1.1-REQUIREMENTS.md` nem em nenhum
   arquivo sob `.planning/milestones/` — sao historico arquivado ("Historico
   nao se reescreve", CLAUDE.md). **NAO** rodar `scripts/bump.sh` nem
   `publicar-web.sh`: fix de fonte simples, sem deploy nesta task.
  </action>
  <verify>
    <automated>bash scripts/executar.sh --testes && (cd web && npx vite build >/dev/null) && grep -c 'C-06, C-07, C-09, C-10, C-17, C-29' .planning/STATE.md .planning/PROJECT.md && grep -q '260906-ugb' .planning/STATE.md && ! grep -q '9 achados Baixo' .planning/STATE.md && ! grep -q '9 achados Baixo' .planning/PROJECT.md && git diff --name-only | grep -qv 'milestones/' && echo OK</automated>
  </verify>
  <done>
`bash scripts/executar.sh --testes` sai com codigo 0 (as duas suites);
`npx vite build` em `web/` conclui sem erro; STATE.md e PROJECT.md citam
exatamente os 6 achados restantes e nenhum dos dois ainda diz "9 achados
Baixo"; STATE.md tem a linha da quick task 260906-ugb; `git status` nao mostra
nenhum arquivo modificado sob `.planning/milestones/`, nem `web_dist`, nem bump
de build.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| (nenhuma nova) | A task nao adiciona rota, input, dependencia nem chamada externa |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-ugb-01 | Information Disclosure | `server/app/kb.py` — texto do verbete `setup-ifr2` servido por `GET /api/kb/buscar` (rota publica) | accept | Conteudo puramente didatico e generico, sem dado de conta, posicao ou preco; o verbete ja e publico hoje e a frase nova nao introduz nenhum campo do snapshot do usuario |
| T-ugb-02 | Tampering | Guardrail CVM — texto determinístico exibido ao usuario | mitigate | A frase nova entra no texto `"educacional"` da KB deterministica, nunca em caminho de LLM; `test_modo_educacional_sem_verbo_de_ordem_obvio` e `test_nenhum_texto_usa_expressao_proibida_fora_de_negacao` continuam barrando verbo de ordem e promessa de resultado (verificacao automatizada da Task 2) |
| T-ugb-SC | Tampering | npm/pip/cargo installs | n/a | Nenhum pacote novo e instalado nesta task — `files_modified` nao inclui `package.json`, `package-lock.json`, `requirements.txt` nem `requirements-prod.txt` |
</threat_model>

<verification>
1. `bash scripts/executar.sh --testes` — exit 0 (suite canonica: pytest do
   backend + `web/tests/*.mjs`). Baseline de referencia: ~2021 passed,
   1 skipped no pytest + web ok (ultimo numero registrado no STATE.md).
2. `cd web && npx vite build` — conclui sem erro (prova de sintaxe do JSX
   editado; nao publica nada).
3. `grep -c 'executar-gate-hint' web/src/App.jsx` retorna 2.
4. `git diff server/app/kb.py` nao altera nenhuma linha dentro do bloco
   `"operador"` do verbete `setup-ifr2`.
5. `git status --short` nao lista `server/web_dist/`, `.planning/milestones/`,
   nem qualquer arquivo de versao/bump.
</verification>

<success_criteria>
- Um leitor de tela que aterrissa no botao "Executar (vende no stop/alvo)"
  desabilitado recebe, pela relacao `aria-describedby`, a explicacao de que o
  recurso e do Modo Operador — sem depender de o usuario varrer o resto do card.
- O botao "Apenas sinalizar" nao ganha nenhum `aria-describedby` no DOM.
- Quem pergunta a KB sobre "reversao a media" chega ao verbete `setup-ifr2`, e
  quem le o verbete aprende o principio geral antes da mecanica.
- O resumo de mesa (`"operador"`) do `setup-ifr2` segue byte-identico.
- Dois guardioes novos impedem que o vinculo do C-18 seja removido em silencio;
  nenhum guardiao existente foi apagado.
- Suite canonica verde, exit 0.
- STATE.md e PROJECT.md contam a verdade dos 3 achados: 2 corrigidos aqui, 1 ja
  estava resolvido antes desta sessao, 6 continuam no backlog sem fase.
- Nenhum deploy, bump, publicacao ou edicao de arquivo arquivado.
</success_criteria>

<output>
Create `.planning/quick/260906-ugb-corrigir-3-achados-baixo-do-report-01-c-/260906-ugb-SUMMARY.md` when done.

O SUMMARY precisa registrar explicitamente:
- que C-28 nao gerou mudanca de codigo (achado ja resolvido na reverificacao,
  nao um item pulado);
- o desvio declarado em `<deviation_declared>`: so o termo acentuado
  `"reversão à média"` foi adicionado, com a justificativa do double-count de
  `_pontuar`, e como reverter para a forma literal se o Alex preferir;
- que as linhas citadas no REPORT-01 original (18/08/2026) estavam defasadas e
  foram reverificadas em 2026-09-06.
</output>
