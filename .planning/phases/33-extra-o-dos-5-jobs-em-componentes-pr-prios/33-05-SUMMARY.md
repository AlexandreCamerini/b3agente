---
phase: 33-extra-o-dos-5-jobs-em-componentes-pr-prios
plan: 05
subsystem: ui
tags: [react, refactor, opcoes, guardian-tests, static-analysis]

# Dependency graph
requires:
  - phase: 33-extra-o-dos-5-jobs-em-componentes-pr-prios (plano 33-04)
    provides: "web/src/opcoes/SecaoComparar.jsx (job 4), Linha/RazaoGanhoPerda em uiOpcoes.jsx, guardião proativo de Pitfall 6 (test_opcoes_vigias_ui.mjs, varredura de diretório) já cobrindo SecaoAnalisar.jsx antes dela nascer"
provides:
  - "web/src/opcoes/SecaoAnalisar.jsx — job 3 (analisar um ticker manualmente) extraído: tabela de comportamento (LEITURA DO ATIVO), montador de estrutura (O QUE DÁ PARA MONTAR), painel local de cadeia/operáveis — ÚLTIMO dos 5 jobs extraídos, fecha D-03/REORG-01"
  - "D-04a fechado: SubAbaOperar deixa de buscar gate/proposta por conta própria (2 useEffect + 2 useState removidos) e passa a ler opcoesPorTicker/opcoesPorTickerCarregando por prop, o mesmo fan-out que a sub-aba Setups já paga"
  - "4 guardiões reapontados (test_opcoes_subabas_ui.mjs, test_opcoes_analisar_ui.mjs, test_opcoes_mcp_aba_ui.mjs) + 1 achado além do censo do plano (test_opcoes_leitura_interna_ui.mjs, só na suíte completa)"
  - "Os 5 jobs de REORG-01 estão extraídos; App.jsx intocado em toda a Fase 33 (33-01..33-05); fase pronta para a Fase 34 (hub × workspace)"
affects: [34-redesenho-navegacao-hub-workspace]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "SecaoAnalisar.jsx: mesmo padrão props-in/callback-out dos 4 irmãos desta fase — recebe temLeitura/semCandles/behavior/lacunas/pregao/expirations/vencimentos/tese/vencimento/lote (+setters)/loteOk/temTese/proposta/montarProposta/cadeia/operaveis/abrirCadeia/abrirOperaveis/custos/cp/palette, nenhum store.*/hook instanciado"
    - "painel (cadeia/operáveis) é o ÚNICO useState local desta seção — reseta via useEffect([ticker]) DENTRO do componente, porque SecaoAnalisar não desmonta ao trocar de ticker (fica na mesma posição da árvore); antes, o reset era um setPainel(\"\") síncrono dentro de escolherTicker em OpcoesScreen.jsx. Prop ticker desce só para viabilizar esse efeito."
    - "Pernas/TabelaDeOpcoes/LacunasDaLeitura/ROTULO_LEITURA e os formatadores fracPct/txt/faixa migraram INTEIROS para dentro de SecaoAnalisar.jsx (não viraram mirror local) — único consumidor de cada um depois da extração, nenhum outro lugar de web/src/opcoes/ os chama"
    - "D-04a: gate/prop deixam de ser useState locais e passam a ser DERIVADOS de opcoesPorTicker[ticker] a cada render (const entrada = opcoesPorTicker[ticker] || null; gate = entrada && entrada.gate; prop = entrada && entrada.proposta) — nenhuma chamada de rede nova, nenhum fallback de fetch local por desenho (D-04a emendado)"
    - "Guarda null-safe nova em SubAbaOperar (!gate || !gate.liquida, era só !gate.liquida): o fold-in introduz um estado que a busca-própria antiga não alcançava — fan-out concluído (carregando=false) mas ESTE ticker sem entrada (falha isolada do gate fetch para ele). Sem o guard, `gate.liquida` estouraria em null. Rule 1 (bug de correção, não feature nova)."

key-files:
  created:
    - web/src/opcoes/SecaoAnalisar.jsx
  modified:
    - web/src/opcoes/OpcoesScreen.jsx
    - web/tests/test_opcoes_subabas_ui.mjs
    - web/tests/test_opcoes_analisar_ui.mjs
    - web/tests/test_opcoes_mcp_aba_ui.mjs
    - web/tests/test_opcoes_leitura_interna_ui.mjs

key-decisions:
  - "SecaoAnalisar recebe temLeitura/semCandles como props JÁ CALCULADOS pelo orquestrador (não recalcula behavior.status === 'sem_candles' internamente) — mesma disciplina de custos/loteOk/temTese que os 4 irmãos já seguem: fonte única no orquestrador, seção só decide o que RENDERIZAR com o valor pronto."
  - "expirations (raw, l.expirations, para a linha 'Vencimentos disponíveis') e vencimentos (filtrado, para o <select>) são DOIS props distintos — mesma distinção que já existia implicitamente em OpcoesScreen.jsx antes da extração (duas variáveis, dois usos), preservada em vez de colapsada numa só para não mudar o dado exibido em nenhum dos dois lugares."
  - "loteNum é derivado LOCALMENTE em SecaoAnalisar.jsx a partir do prop cru `lote` (Option B, mesmo precedente de SecaoComparar.jsx/33-04 — 'formatador de uma linha, espelho declarado local') em vez de o orquestrador computar e descer pronto; loteOk (usado para desabilitar o botão) continua vindo do orquestrador porque também alimenta SecaoComparar."
  - "D-04a implementado SEM a cláusula de fallback removida na emenda do 33-CONTEXT.md: quando opcoesPorTicker[ticker] ainda não existe, o estado é 'ainda não varrido' (carregandoGate = opcoesPorTickerCarregando && !entrada), nunca um fetch local — confirmado por leitura que o universo do fan-out (carteira.map((p) => p.t), OpcoesScreen.jsx:316) é o MESMO array de onde o ticker de Operar é escolhido, então nunca fica de fora."
  - "test_opcoes_mcp_aba_ui.mjs: iDados trocou de indexOf('cp.opcoesLeituraTitulo', iRender) para indexOf('<SecaoAnalisar', iRender) — medido ANTES de editar: a chave cp.opcoesLeituraTitulo restante em OpcoesScreen.jsx (blocoLeituraDoServico) fica ANTES de iRender no texto-fonte (é uma const declarada fora do return), então a busca a partir de iRender já dava -1 (falha alta, não falso-positivo silencioso) — confirmado rodando o guardião antes de tocar no arquivo."

patterns-established:
  - "Quinto e último componente Secao*.jsx da fase nasce sem precisar de guardião novo para Pitfall 6 — a varredura de diretório criada no 33-04 (test_opcoes_vigias_ui.mjs, seção 4d) já cobriu SecaoAnalisar.jsx automaticamente, confirmando a previsão registrada no 33-04-SUMMARY.md."
  - "Regra 3 de test_opcoes_subabas_ui.mjs migrou de contagem-em-um-arquivo para contagem-por-diretório (mesmo padrão D-02 já usado 4x nesta fase) — precedente que sobrevive a qualquer realocação futura de gate/proposta dentro de web/src/opcoes/."

requirements-completed: [REORG-01, REORG-02, REORG-03, REORG-05, REORG-06]

duration: sessão contínua, sem interrupção de rate limit
completed: 2026-09-20
---

# Phase 33 Plan 05: Extração de SecaoAnalisar + fold-in D-04a Summary

**Job 3 ("analisar um ticker manualmente") extraído para SecaoAnalisar.jsx — último dos 5 jobs da fase —, com o fold-in D-04a fechando o fetch redundante de gate/proposta em SubAbaOperar (2 useEffect + 2 useState a menos), 4 guardiões reapontados mais 1 achado além do censo do plano, e as 5 provas negativas da Task 4 todas reprovando o defeito certo.**

## Performance

- **Duration:** sessão contínua, sem interrupção
- **Tasks:** 4/4 completas
- **Files modified:** 1 criado + 5 modificados

## Accomplishments

- `web/src/opcoes/SecaoAnalisar.jsx` criado: job 3 como componente próprio, props-in/callback-out, zero `store.*`/`useOpcoesMcp`/`useState` de estado compartilhado — só `painel` (`"" | "cadeia" | "operaveis"`) é local, confirmado por grep e pelo guardião de Pitfall 6 (proativo desde o 33-04).
- `Pernas`/`TabelaDeOpcoes`/`LacunasDaLeitura`/`ROTULO_LEITURA` e os formatadores `fracPct`/`txt`/`faixa` migraram INTEIROS de `OpcoesScreen.jsx` para dentro de `SecaoAnalisar.jsx` — único consumidor de cada um depois da extração; `OpcoesScreen.jsx` perdeu também `CAMPO`/`ROTULO`/`ROLAGEM`/`TABELA`/`TH`/`TD`/`LADO`/`desabilitado` (órfãos após o move), mantendo `CAIXA`/`BOTAO`/`CUSTO_NO_BOTAO`/`AJUDA`/`pct`/`ehNum`/`fmt` (ainda usados por `blocoLeituraDoServico`/`LastroDoAtivo`/`LeituraInterna`).
- `OpcoesScreen.jsx` renderiza `<SecaoAnalisar .../>` como primeiro elemento do ramo "4. DADOS", seguido de `{temLeitura ? <SecaoComparar .../> : null}` — mesma posição exata e mesma condição de antes (`SecaoComparar` nunca aparece sem `temLeitura`, idêntico ao comportamento pré-extração).
- **D-04a fechado**: `SubAbaOperar` perdeu os dois `useEffect` (`store.optionsGate`/`store.optionsProposta`) e os dois `useState` (`gate`/`prop`) — agora deriva `entrada = opcoesPorTicker[ticker] || null`, `gate = entrada && entrada.gate`, `prop = entrada && entrada.proposta` a cada render, lendo o MESMO fan-out (`useOpcoesPropostas`) que a sub-aba Setups já paga. Nenhuma chamada de rede nova; nenhum fallback de fetch local (a cláusula de fallback foi removida na emenda do CONTEXT.md, verificada por leitura antes de implementar — ver Decisions).
- Guarda null-safe adicionada em `SubAbaOperar` (`!gate || !gate.liquida`, era só `!gate.liquida`): o fold-in torna alcançável um estado que a busca-própria antiga nunca alcançava (fan-out concluído mas ESTE ticker sem entrada, por falha isolada do gate fetch) — sem o guard, acessar `gate.liquida` sobre `null` estouraria. Rule 1 (correção, não feature).
- 4 guardiões reapontados (censo do plano): `test_opcoes_subabas_ui.mjs` (regra 3 virou varredura de diretório com nota datada da queda 1→0; regra 4 reapontada para `useOpcoesPropostas.js` + asserção nova de contrapartida contra o retorno do fetch), `test_opcoes_analisar_ui.mjs` (a fatia "Analisar" virou o arquivo `SecaoAnalisar.jsx` inteiro — itens de ordem/razão/faixa/lacunas/CAMPO/ROLAGEM todos reapontados), `test_opcoes_mcp_aba_ui.mjs` (`iDados` desambiguado: `indexOf("cp.opcoesLeituraTitulo", iRender)` → `indexOf("<SecaoAnalisar", iRender)`).
- 1 achado ALÉM do censo do plano, achado só ao rodar a suíte completa: `test_opcoes_leitura_interna_ui.mjs` seção 5b tinha uma sanidade ("há uso de `fracPct` na tela") que dependia do job 3 estar em `OpcoesScreen.jsx` — depois da extração, `tela` não tem mais nenhum `fracPct(`, e a sanidade passaria por vacuidade (ou reprovaria por vacuidade, dependendo da leitura). Corrigido somando `SecaoAnalisar.jsx` à varredura.
- 5 provas negativas reais na Task 4, todas reprovando o defeito certo e revertidas: (1) `store.optionsGate` reintroduzido em `SubAbaOperar` reprova por contagem-na-pasta E pela contrapartida nova; (2) `if (gate && gate.liquida)` removido de `useOpcoesPropostas.js` reprova a regra 4; (3) `{proposta.dados.manchete}` em `SecaoAnalisar.jsx` reprova o guardrail CVM generalizado (REORG-06), nomeando o arquivo; (4) `faixa(...)` trocado por extremos crus reprova a asserção de faixa; (5) multiplicação por `lote` em `SecaoAnalisar.jsx` reprova a varredura de recálculo do 33-01, nomeando o arquivo novo.
- `App.jsx` intocado em TODA a Fase 33 — confirmado `git diff --stat b72ab44~1..HEAD -- web/src/App.jsx` (commit antes do 33-01) e `git diff --stat origin/main...HEAD -- web/src/App.jsx`, ambos vazios.

## Task Commits

1. **Tasks 1+2+3: Criar SecaoAnalisar.jsx, fold-in D-04a em SubAbaOperar, reapontar os 4 guardiões (+1 achado além do censo)** — `1809893` (refactor) — código e guardiões no MESMO commit, por decisão explícita do plano.
2. **Task 4: Provas negativas + baseline final** — nenhum commit (task de verificação pura: cada defeito foi injetado, confirmado, e revertido com `git checkout --`; `git status` limpo ao final).

**Plan metadata:** este arquivo (SUMMARY) + atualização de STATE.md/ROADMAP.md pelo orquestrador (fora do escopo deste executor, por guardrail do repositório).

## Files Created/Modified

- `web/src/opcoes/SecaoAnalisar.jsx` (novo) — job 3, tabela de comportamento + montador de estrutura + painel local de cadeia/operáveis.
- `web/src/opcoes/OpcoesScreen.jsx` — perde o JSX do job 3, o `useState` de `painel`, e os helpers/estilos órfãos (`fracPct`/`txt`/`faixa`/`ROTULO_LEITURA`/`LacunasDaLeitura`/`CAMPO`/`ROTULO`/`desabilitado`/`ROLAGEM`/`TABELA`/`TH`/`TD`/`LADO`/`Pernas`/`TabelaDeOpcoes`); ganha o import de `SecaoAnalisar.jsx` e `<SecaoAnalisar .../>` na posição exata; `SubAbaOperar` ganha as props `opcoesPorTicker`/`opcoesPorTickerCarregando` e perde os 2 `useEffect`/2 `useState` de gate/proposta.
- `web/tests/test_opcoes_subabas_ui.mjs` — regra 3 (varredura de diretório, nota datada 1→0) e regra 4 (reapontada para `useOpcoesPropostas.js` + contrapartida nova).
- `web/tests/test_opcoes_analisar_ui.mjs` — `secaoAnalisar` como nova fonte lida; seções 5 (ordem), 12 (CAMPO/ROLAGEM), 13 (razão), 15 (lacunas/faixa/motivo) reapontadas.
- `web/tests/test_opcoes_mcp_aba_ui.mjs` — `iDados` desambiguado (`<SecaoAnalisar` em vez de `cp.opcoesLeituraTitulo`).
- `web/tests/test_opcoes_leitura_interna_ui.mjs` — achado tardio: sanidade de `fracPct` passa a somar `SecaoAnalisar.jsx`.

## Decisions Made

Ver `key-decisions` no frontmatter. Resumo: `temLeitura`/`semCandles` chegam prontos por prop (não recalculados); `expirations` (raw) e `vencimentos` (filtrado) são props distintos preservando os dois usos originais; `loteNum` derivado localmente (Option B, mesmo precedente do 33-04); D-04a implementado sem fallback de fetch local (emenda do CONTEXT.md confirmada por leitura: `carteira.map((p) => p.t)` é o MESMO array de onde o ticker de Operar é escolhido); `iDados` do `mcp_aba_ui` corrigido por medição real (rodei o guardião ANTES de editar — deu -1, falha alta, não o falso-positivo silencioso que o plano temia, mas a correção é a mesma).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `painel` perderia o reset ao trocar de ticker se só virasse `useState` local**
- **Found during:** Task 1, ao mover `painel` para dentro de `SecaoAnalisar.jsx`
- **Issue:** Em `OpcoesScreen.jsx`, `escolherTicker` chamava `setPainel("")` no MESMO handler que trocava o ticker — reset síncrono. Depois da extração, `SecaoAnalisar` não desmonta ao trocar de ticker (fica na mesma posição da árvore, só `temLeitura`/`behavior` mudam de valor), então um `useState` local sozinho NÃO reseta: o painel ficaria "cadeia"/"operaveis" preso entre trocas de ativo — regressão silenciosa de comportamento (viola "zero funcionalidade nova"/D-03).
- **Fix:** `SecaoAnalisar` recebe `ticker` por prop (só para este fim) e usa `useEffect(() => setPainel(""), [ticker])` para reproduzir o reset. `OpcoesScreen.jsx` documentou a troca de mecanismo no comentário de `escolherTicker`.
- **Files modified:** `web/src/opcoes/SecaoAnalisar.jsx`, `web/src/opcoes/OpcoesScreen.jsx`
- **Verification:** `npx vite build` verde; comportamento de reset preservado por leitura de código (o efeito dispara toda vez que `ticker` muda, mesma condição do `setPainel("")` original).
- **Committed in:** `1809893` (mesmo commit da Task 1, achado antes do commit)

**2. [Rule 1 - Bug] Guarda de liquidez em `SubAbaOperar` quebraria com `gate` null depois do fold-in**
- **Found during:** Task 2, ao revisar o novo estado alcançável por `opcoesPorTicker[ticker]`
- **Issue:** O código original tinha `gate === null` como precondição EXAUSTIVA antes de `!gate.liquida` (o efeito só resolvia `gate` para um objeto real ou ficava preso em `null` para sempre em caso de falha). Depois do fold-in, é possível o fan-out terminar (`opcoesPorTickerCarregando === false`) mas este ticker específico não ter entrada (falha isolada do `optionsGate` dele dentro do `.forEach` do hook) — nesse caso `gate` é `undefined`/`null` e `!gate.liquida` estouraria `TypeError`.
- **Fix:** Guarda alterada para `!gate || !gate.liquida`. Não afrouxa nem adiciona funcionalidade — só evita um crash num estado que o fold-in tornou alcançável (antes era impossível chegar a essa combinação).
- **Verificação adicional (pós-revisão):** no MESMO estado (`entrada` null, fan-out concluído), `prop` também é `null`, então `candidatos = []`/`multi = false` — mas o ramo `!gate || !gate.liquida` é avaliado ANTES do ramo `multi`/`PropostaLastreada` na cascata (`OpcoesScreen.jsx`), então esse estado nunca chega a renderizar `<PropostaLastreada r={null} .../>` de qualquer forma. Conferido por leitura que `PropostaLastreada` (`PropostaLastreada.jsx:169`, `if (!r) return null;`) já tolera `r === null` como "ainda carregando" mesmo assim — dupla proteção, não single point of failure.
- **Files modified:** `web/src/opcoes/OpcoesScreen.jsx`
- **Verification:** `npx vite build` verde; `bash scripts/executar.sh --testes` sem regressão nos guardiões de `SubAbaOperar` (multi-candidato, proposta, faixa de liquidez).
- **Committed in:** `1809893` (mesmo commit da Task 2, achado antes do commit)

**3. [Rule 3 - Blocking] `test_opcoes_leitura_interna_ui.mjs` quebrado por migração de arquivo, fora do censo do plano**
- **Found during:** Task 3, ao rodar `bash scripts/executar.sh --testes` pela primeira vez após o commit do refactor
- **Issue:** A seção 5b (armadilha de unidade, C6) tinha uma sanidade "há uso de `fracPct` na tela" que dependia de `fracPct(behavior.hv21)`/`fracPct(behavior.hv63)` (job 3) estarem em `OpcoesScreen.jsx`. Depois da extração, `tela` não contém mais nenhum `fracPct(`, e a sanidade reprovava. O censo do plano (grep de palavras-chave) não previu este arquivo — só apareceu ao rodar a suíte completa, mesma classe de achado que 33-01/33-02/33-03/33-04 já documentaram.
- **Fix:** O guardião passou a somar `SecaoAnalisar.jsx` na varredura de `fracPct(` (junto com `tela`). A garantia central da seção (nenhum campo de `tecnico.dados` — o bloco interno — passa por `fracPct`) não afrouxou: continua cobrindo os usos legítimos (campos do serviço MCP, agora em `SecaoAnalisar.jsx`) e continua vazia de usos ilegítimos.
- **Files modified:** `web/tests/test_opcoes_leitura_interna_ui.mjs`
- **Verification:** `node web/tests/test_opcoes_leitura_interna_ui.mjs` — todos os testes passam; suíte canônica completa confirmou nenhum outro guardião afetado pelo mesmo padrão.
- **Committed in:** `1809893` (mesmo commit da Task 3, achado antes do commit)

---

**Total deviations:** 3 auto-fixed (2 Rule 1 — bug de regressão comportamental achado ANTES de virar defeito real, prevenido na própria extração; 1 Rule 3 — guardião bloqueado por migração de arquivo não coberta pelo censo textual do plano)
**Impact on plan:** nenhum afrouxamento de garantia; os dois achados de Rule 1 são o tipo de coisa que só aparece quando se pensa em "o componente não desmonta mais" — nenhum deles chegou a produzir um defeito observável porque foram pegos durante a própria escrita do código, não depois.

## Issues Encountered

- `test_ios_assets.mjs` falha na suíte canônica com `ENOENT` para `web/ios/App/App/Assets.xcassets/...` — gap documentado no `CLAUDE.md` do repositório (`web/ios/` gitignored, nasce ausente em worktree novo). Pré-existente, sem relação com `web/src/opcoes/`, fora do escopo desta task. Não corrigido — idêntico à baseline herdada do 33-01/33-02/33-03/33-04.

## Negative-Proof Log (Task 4)

Guardião que passa não prova que guarda. Cada defeito abaixo foi injetado À MÃO, o guardião correspondente rodado sozinho, a saída real conferida, e o arquivo revertido com `git checkout --` (confirmado `git status --porcelain` limpo depois de cada um).

**1. Reintroduzir `store.optionsGate(ticker)` dentro de `SubAbaOperar`**
- Injeção: `store.optionsGate(ticker);` colado logo após `const entrada = opcoesPorTicker[ticker] || null;` em `OpcoesScreen.jsx`.
- Comando: `node web/tests/test_opcoes_subabas_ui.mjs`
- Saída real:
  ```
  FALHOU `store.optionsGate(` aparece exatamente 1× em toda web/src/opcoes/ (fonte única, fold-in D-04a)
  FALHOU `store.optionsGate(` aparece 0× em OpcoesScreen.jsx (queda de 1→0: a busca mudou de arquivo, não desapareceu)
  FALHOU `SubAbaOperar` não contém `store.options` nenhum (gate/proposta vêm do fan-out por prop, não de fetch local)
  ```
- Revert: `git checkout -- web/src/opcoes/OpcoesScreen.jsx`; guardião volta a passar (`todos os testes passaram`).
- Prova de que a queda 1→0 e a contrapartida nova NÃO afrouxaram nada: as duas reprovaram juntas.

**2. Remover `if (gate && gate.liquida)` de `useOpcoesPropostas.js`**
- Injeção: `if (gate && gate.liquida) {` → `if (true) {`.
- Comando: `node web/tests/test_opcoes_subabas_ui.mjs`
- Saída real: `FALHOU useOpcoesPropostas.js guarda \`store.optionsProposta\` com \`if (gate && gate.liquida)\` ANTES da chamada`.
- Revert: `git checkout -- web/src/opcoes/useOpcoesPropostas.js`; guardião volta a passar.

**3. Renderizar `{proposta.dados.manchete}` dentro de `SecaoAnalisar.jsx`**
- Injeção: `<div>{proposta.dados.manchete}</div>` colado antes de `<PayoffChart` no ramo `proposta.dados`.
- Comando: `node web/tests/test_opcoes_subabas_ui.mjs`
- Saída real: `FALHOU nenhum arquivo de web/src/opcoes/ FORA da allowlist renderiza manchete (REORG-06) (violam: SecaoAnalisar.jsx)` — nomeia o arquivo certo.
- Revert: `git checkout -- web/src/opcoes/SecaoAnalisar.jsx`; guardião volta a passar.
- Prova de que REORG-06 (guardrail CVM generalizado no 33-02) cobre `SecaoAnalisar.jsx` por MEDIÇÃO, não por analogia.

**4. Trocar `valor={faixa(behavior.range_63_sessions)}` por dois extremos crus**
- Injeção: `valor={fmt(behavior.range_63_sessions.lowest) + " – " + fmt(behavior.range_63_sessions.highest)}`.
- Comando: `node web/tests/test_opcoes_analisar_ui.mjs`
- Saída real: `FALHOU a faixa de 63 usa o helper que devolve UM travessão sem os dois extremos`.
- Revert: `git checkout -- web/src/opcoes/SecaoAnalisar.jsx`; guardião volta a passar.

**5. Multiplicar um valor em reais por `lote` dentro de `SecaoAnalisar.jsx`**
- Injeção: `const brutoInjetado = proposta.dados ? proposta.dados.emReais.ganhoMaximo * lote : null;` colado logo após a declaração de `loteNum`.
- Comando: `node web/tests/test_opcoes_analisar_ui.mjs`
- Saída real: `FALHOU SecaoAnalisar.jsx não multiplica por lote` — nomeia o arquivo novo, provando que a varredura por diretório do 33-01 cobre `SecaoAnalisar.jsx` automaticamente.
- Revert: `git checkout -- web/src/opcoes/SecaoAnalisar.jsx`; guardião volta a passar.

Nenhuma injeção foi vácua: as 5 reprovaram nomeando exatamente a asserção esperada, sem precisar corrigir regex nenhuma desta vez (diferente do 33-04, que achou 1 regex estreita demais durante a própria prova negativa).

## Baseline da suíte canônica — início da fase (33-01) × fim da fase (33-05)

Rodado fora do sandbox padrão (`dangerouslyDisableSandbox: true`) porque o sandbox interno reprova `pytest` com `PermissionError` de SSL ao carregar `certifi` — achado conhecido e documentado (memória do projeto: "sandbox mente"), não uma falha real.

| Métrica | 33-01 (início da fase) | 33-05 (fim da fase, este plano) | Delta |
|---|---|---|---|
| pytest | 2923 passed, 5 skipped, 3 xfailed, 0 failed | 2923 passed, 5 skipped, 3 xfailed, 0 failed | 0 — nenhum plano da Fase 33 tocou `server/` |
| `.mjs` (arquivos) | 151 OK + 1 falha pré-existente (`test_ios_assets.mjs`) = 152 | 151 OK + 1 falha pré-existente (`test_ios_assets.mjs`) = 152 | 0 arquivos novos — nenhum plano desta fase criou um `.mjs` novo; D-02 (varredura de diretório) existe exatamente para isso |
| `npx vite build` | verde | verde (3 rodadas: pós-Task1/2, durante as reversões da Task 4, pós-commit) | — |

O número de arquivos `.mjs` nunca mudou durante a Fase 33 inteira (152 desde antes do 33-01) — os 5 componentes `Secao*.jsx` novos e o fold-in D-04a entraram por EXTENSÃO de guardiões já existentes (4 reapontados neste plano + 1 achado tardio), nunca por arquivo de teste novo. Isso confirma, pela quinta vez consecutiva, a decisão de arquitetura de teste D-02 do `33-CONTEXT.md`: varredura de diretório em vez de lista fixa paga o custo de manutenção zero para cada `Secao*.jsx` novo.

**Os 5 jobs estão extraídos** (REORG-01 fechado): `SecaoVigias.jsx` (33-01), `SecaoDescobrir.jsx` (33-02), `SecaoSetups.jsx` (33-03), `SecaoComparar.jsx` (33-04), `SecaoAnalisar.jsx` (33-05, este plano).

**`App.jsx` intocado em TODA a Fase 33** (REORG-04): `git diff --stat b72ab44~1..HEAD -- web/src/App.jsx` (commit imediatamente anterior ao início do 33-01) e `git diff --stat origin/main...HEAD -- web/src/App.jsx` — ambos vazios.

**Nada foi publicado**: sem `bump.sh`, sem `publicar-web.sh`, sem push a `origin`. A Fase 34 (redesenho hub × workspace) depende desta suíte verde, não de publicação.

## Verificação manual (Pitfall 7)

Conferido à mão no fonte: a "Leitura referente ao pregão de ..." (linha de carimbo abaixo da tabela de comportamento) continua visível sem clique extra, no mesmo lugar relativo (logo abaixo da tabela `<Linha>`, acima de `<LacunasDaLeitura>`) — `SecaoAnalisar.jsx` reproduz o JSX de `OpcoesScreen.jsx` linha a linha, só trocando as variáveis livres por props. Reorganizar não reduziu informação.

## Next Phase Readiness

- Os 5 jobs de REORG-01 estão extraídos, cada um em `web/src/opcoes/Secao*.jsx`, todos props-in/callback-out, nenhum importando `App.jsx`, nenhum instanciando hook de dados, nenhum redeclarando `ticker`/`tese`/`vencimento`/`lote` (guardião de Pitfall 6 cobrindo os 5 por varredura de diretório desde o 33-04).
- D-04a fechado — o `.planning/todos/pending/subaba-operar-fetch-redundante-gate-proposta.md` pode ser arquivado/fechado pelo orquestrador.
- `App.jsx` intocado em toda a fase (REORG-04 preservado de ponta a ponta).
- Suíte canônica idêntica à baseline de entrada da fase (2923 pytest / 152 `.mjs`, 1 falha ambiental conhecida e não-regressiva) — pronto para a Fase 34 (redesenho de navegação hub+workspace) começar sobre uma base verde.
- Nenhum bloqueio conhecido para a Fase 34.

## Self-Check: PASSED

- `web/src/opcoes/SecaoAnalisar.jsx` — FOUND
- `web/src/opcoes/OpcoesScreen.jsx` (modificado, `<SecaoAnalisar` presente, `<SecaoComparar` presente depois) — FOUND
- Commit `1809893` (refactor: SecaoAnalisar + fold-in D-04a + guardiões) — FOUND in `git log`
- `bash scripts/executar.sh --testes` — 2923 pytest passed, 151/152 `.mjs` OK (1 falha ambiental conhecida) — CONFIRMED
- `npx vite build` — verde — CONFIRMED
- `git diff --stat origin/main...HEAD -- web/src/App.jsx` — vazio — CONFIRMED

---
*Phase: 33-extra-o-dos-5-jobs-em-componentes-pr-prios*
*Plan: 05*
*Completed: 2026-09-20*
