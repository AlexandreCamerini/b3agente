---
phase: 26-otimizacao-ux-ia
plan: 01
subsystem: ui
tags: [assistente-ia, kb, copy, tour, metering, skill, guardioes, react, fastapi]

# Dependency graph
requires:
  - phase: 24-aba-opcoes
    provides: a aba Opções (BottomNav, OpcoesScreen, copy por modo, rotas MCP) — é a tela que ficou ausente dos outros registros
  - phase: 25-planos-comerciais
    provides: o gate de análises por plano e o carimbo do 402 (`marcar_o_limite`), que o fixture de teste do A6 reproduz
  - phase: qa/45
    provides: a reorganização do Perfil em 5 telas (rename "Conta & preferências" → "Preferências"/"IA & Boris"/"Fonte de dados") — a causa raiz do A6
provides:
  - aba Opções visível para o assistente de IA (PET_TELAS, /api/pet/resumo, petSnapshot)
  - KB (83 verbetes) responde antes da validação de tela/setor, sem gastar IA
  - guardião do vocabulário por modo da aba Opções
  - tour com passo zero (nomeia a tela em que o app abre) e passo da aba Opções; seção de Ajuda espelhada em docs/AJUDA.md
  - frase canônica única para evidência insuficiente (CLAUDE.md como fonte, lida pelo guardião)
  - mensagem de cota apontando para um tile que existe, com guardião cruzando backend × PerfilHub
  - SKILL.md da didática descrevendo o mascote real
affects: [26-02, fase-de-arquitetura-C3-registro-unico-de-telas, publicacao-do-front]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Guardião que DERIVA a lista de telas da fonte (BottomNav.defs) em vez de redigitá-la — test_pet_opcoes.mjs"
    - "Guardião que LÊ o texto canônico do arquivo de norma (CLAUDE.md) em vez de redigitá-lo — test_fonte_explicacao.mjs"
    - "Guardião que executa a função real com um `cp` real em vez de casar regex — test_tour_opcoes.mjs"
    - "Guardião de par backend×front cruzando string de prosa com o símbolo real da UI — test_perfil_reorg.mjs seção 7"

key-files:
  created:
    - web/tests/test_pet_opcoes.mjs
    - web/tests/test_vocabulario_opcoes.mjs
    - web/tests/test_tour_opcoes.mjs
  modified:
    - server/app/conceitos.py
    - server/app/main.py
    - server/app/metering.py
    - web/src/App.jsx
    - web/src/copy.js
    - docs/AJUDA.md
    - server/tests/test_pet_todas_telas.py
    - server/tests/test_opcoes_dsl.py
    - web/tests/test_pet_ui.mjs
    - web/tests/test_fonte_explicacao.mjs
    - web/tests/test_perfil_reorg.mjs
    - .claude/skills/didatica-boris/SKILL.md

key-decisions:
  - "A3 já estava implementado pela Fase 24 (commit 404f8e6) — o item virou criação do guardião que faltava, não reimplementação"
  - "A frase canônica de evidência insuficiente é a do CLAUDE.md ('Não há dados suficientes para concluir.'); skill_ref.sem_setup fica intocada por ser conceito diferente"
  - "O resumo do pet para a aba Opções tem custo ZERO de MCP (ADR-027): manda o determinístico do servidor e DIZ o que não sabe, em vez de inventar"
  - "O título da aba Opções é igual nos dois modos por decisão (não há sinônimo de mesa para 'Opções'); só o subtítulo muda de voz"
  - "web/src/api.js:11 (ADDR_HINT) tem o mesmo defeito do A6 e NÃO foi corrigido — fora do escopo literal da task, registrado como achado"

patterns-established:
  - "Guardião novo nasce derivando da fonte, nunca redigitando o texto que ele trava"
  - "Rename de tela do Perfil quebra teste em vez de matar silenciosamente o caminho citado em prosa pelo backend"

requirements-completed: ["Fase A do 26-CONTEXT — sete itens independentes, barato e alto impacto"]

# Metrics
duration: ~40 min (em duas sessões, separadas por um checkpoint de disco cheio)
completed: 2026-09-13
---

# Phase 26 Plan 01: Fase A — sete correções baratas de UX e da camada de IA Summary

**A aba Opções deixa de ser invisível para o assistente, a KB responde antes da validação de tela, o tour começa onde o app realmente abre, e três textos que descreviam um produto que não existe mais (frase de evidência, caminho da mensagem de cota, SKILL.md do mascote) passam a bater com o código — com guardião novo em cada ponto que tinha apodrecido em silêncio.**

## Performance

- **Duração:** ~40 min de execução efetiva, distribuídos em duas sessões
- **Primeiro commit (A1):** 2026-09-12T23:58:35-03:00
- **Último commit (A7):** 2026-09-13T00:23:50-03:00
- **Tasks:** 7/7
- **Arquivos tocados:** 15 (3 criados, 12 modificados)
- **Commits de tarefa:** 7 + 1 nota de teste fora de escopo

## Accomplishments

- **A aba mais nova do app parou de ser muda.** `pet:opcoes` respondia 400 e `/api/pet/resumo?tela=opcoes` devolvia a Watchlist com cara de resposta certa — nada quebrava, nada logava.
- **A base de conhecimento saiu de trás da validação de tela.** 83 verbetes que respondem de graça deixaram de ser recusados por causa da tela de onde a pergunta partiu.
- **Três documentos/textos alinhados com a realidade** (frase de evidência insuficiente, caminho citado na mensagem de cota, descrição do mascote na skill) — todos eram descrições de comportamento que já não existia.
- **Quatro guardiões novos/corrigidos**, cada um derivando da fonte em vez de redigitar o texto que trava — o modo de falha que produziu três dos sete achados.

## Task Commits

| # | Item | Commit | Tipo |
|---|------|--------|------|
| 1 | A1 — Registrar a aba Opções no assistente de IA | `65ab89e` | feat |
| 2 | A2 — KB responde antes da checagem de tela | `5155229` | fix |
| 3 | A3 — Vocabulário de modo na aba Opções (guardião) | `9265f0f` | test |
| 4 | A4 — Tour cobre a tela atual e a aba Opções | `2ffb4bf` | feat |
| 5 | A5 — Uma frase só para evidência insuficiente | `6144507` | fix |
| 6 | A6 — Corrigir o caminho que a mensagem de cota indica | `704955d` | fix |
| 7 | A7 — SKILL.md da didática, texto morto | `fa19bcf` | docs |
| — | (fora de escopo) nota de flakiness sob carga | `16c07a2` | docs |

## Um bloco por item

### A1 — Registrar a aba Opções no assistente de IA — `65ab89e`

A aba nasceu na Fase 24 já no `BottomNav` e nunca entrou nos outros registros de tela. `POST /api/assistente` com `tela:"pet:opcoes"` respondia 400 "Tela desconhecida."; `GET /api/pet/resumo?tela=opcoes` caía no fallback de `"mercado"` e devolvia a Watchlist — **falha silenciosa**, o pior formato: nada quebrava e nada logava.

- `conceitos.PET_TELAS` ganha `"opcoes"` (8ª tela), com nota datada.
- `main.py`: `_pet_resumo_opcoes` + ramo na rota. **Custo zero por contrato** — não toca `mcp.semente.dev` (ADR-027: a leitura da aba sai de clique explícito). Manda o que é determinístico do servidor (universo da watchlist, `optionPositions` com lastro) e **diz o que não sabe** em vez de inventar: a seleção ativo/tese/vencimento é estado local de `OpcoesScreen` (princípio 4 do CLAUDE.md).
- `App.jsx`: `case "opcoes"` no `petSnapshot`, com o motivo no lugar do valor ausente — nem `null` nem omissão, que seriam lidos como "não escolheu ativo nenhum".
- Guardiões **atualizados, não relaxados**: `test_pet_todas_telas.py` segue com igualdade exata (agora 8 telas) + dois testes novos (o resumo de opções não é o de mercado; bomba em `mcp_client.call_tool` prova o custo zero).
- `web/tests/test_pet_opcoes.mjs` (novo) **deriva** a lista de telas de `BottomNav.defs` e exige cada aba no `petSnapshot` e em `PET_TELAS` — rede de segurança até o C3 do 26-CONTEXT.

Verificado no endpoint real: `pet:opcoes` → 200 `fonte=kb`; `pet:invalida` segue 400.

### A2 — KB responde antes da checagem de tela — `5155229`

A ordem anterior validava `tela` contra as allowlists e só depois tentava a KB — pergunta de glossário era recusada com 400 **por causa da tela de onde partiu**. A dependência estava invertida: `kb.resolver` recebe só `(pergunta, voc)`, não lê a tela.

A allowlist **não afrouxou**: `tela` continua nunca entrando em `kb.resolver`, e quando a KB devolve `None` as duas checagens rodam abaixo, antes de exigir conta e antes de qualquer gasto. Quatro guardiões (dois atualizados com nota datada, dois novos) travam os dois lados da fronteira, inclusive o contra-guardião "tela inválida sem cobertura da KB continua recusada". 144 passed em `-k "assistente or kb or pet or setor"`.

### A3 — Vocabulário de modo na aba Opções — `9265f0f`

**Desvio registrado (Rule 1 — o achado estava desatualizado):** a reconferência mostrou que a Fase 24 (`404f8e6`) **já** havia criado `tituloOpcoes`/`subtituloOpcoes` nos dois blocos de `copy.js` e já os lia em `OpcoesScreen.jsx:392,394`. O briefing descrevia a árvore de antes dela. O item estava satisfeito; o que faltava era a rede de proteção.

`web/tests/test_vocabulario_opcoes.mjs` (novo) trava: as duas chaves nos DOIS blocos (chave só no Estudo faria a aba cair no fallback do JSX em Operador, em silêncio); o **subtítulo** difere entre Estudo e Operador; o **título é igual por decisão** ("Opções" é o nome da coisa nos dois registros — travado como igual para que divergência futura seja decisão, não acidente); `tabOpcoes` não muda por modo; os dois subtítulos dizem, na própria tela, que nenhuma ordem sai dali.

### A4 — Tour cobre a tela atual e a aba Opções — `2ffb4bf`

Dois buracos medidos: o tour abre **sobre** o "Acompanhar" (`useState("evolucao")`) e o primeiro passo mandava "Descubra no Radar"; e nem `tourPassos` nem `ajudaSecoes` citavam a aba Opções, 5º item da barra desde a Fase 24.

`tourPassos`: 4 → 6 passos (passo zero novo nomeando "Acompanhar" + 4º passo apresentando Opções, sem renumerar 1-3). `ajudaSecoes`: seção nova entre Portfólio e Operador IA, dizendo de onde vem o dado, que é leitura de fim de pregão (princípio 3), que campo ausente é travessão e nunca zero, e que nenhuma ordem sai dali. `docs/AJUDA.md` espelhado (o topo daquele arquivo declara espelhar `ajudaSecoes`).

`test_tour_opcoes.mjs` **executa** as duas funções com um `cp` real em vez de casar regex — contar passos por regex daria falso verde na primeira reorganização do array.

### A5 — Uma frase só para evidência insuficiente — `6144507`

Duas frases para a mesma coisa, e um comentário afirmando que uma era cópia da outra: `CLAUDE.md` diz "Não há dados suficientes para concluir."; `App.jsx` renderizava "…para uma explicação agora."; e o comentário logo acima dizia "frase MANDATÓRIA do CLAUDE.md, verbatim" — falso, com o guardião repetindo a mesma alegação e **travando a divergência**.

`App.jsx` passa a renderizar a frase do `CLAUDE.md` byte a byte; o comentário registra o achado e a distinção para `skill_ref.vocab[*]["sem_setup"]` (ausência de SETUP ≠ ausência de DADO — intocada, como manda o plano); o guardião foi **corrigido, não relaxado**: continua exigindo igualdade verbatim e ocorrência única, mas agora **lê** a frase do `CLAUDE.md` em vez de redigitá-la (redigitar foi como as duas divergiram).

### A6 — Corrigir o caminho que a mensagem de cota indica — `704955d`

As três mensagens de 402 do `metering.py` mandavam a pessoa para "Perfil → Conta & preferências" — tela renomeada no qa/45 Decisão 1. O bloco de BYOK/modelo vive em "IA & Boris" desde então: **cota esgotada virava beco sem saída**.

- `server/app/metering.py`: as 3 strings passam a citar "Perfil → IA & Boris" (teto diário por conta, varredura profunda, teto global do servidor).
- `server/tests/test_opcoes_dsl.py:813`: o `parametrize` reproduz o **texto real** de cada teto (é dado de teste, não asserção — o docstring do próprio arquivo diz isso), então acompanha a fonte; nota datada 2026-09-13 explicando que segue o rename. A trava do teste (o copy de BYOK não vaza para a aba Opções) continua intacta.
- `web/tests/test_perfil_reorg.mjs`: **guardião novo (seção 7)** cruzando todo `"Perfil → X"` citado pelo `metering.py` contra os `title="X"` reais do `PerfilHub`. O rename anterior passou silencioso justamente porque nada cruzava backend × tiles — o teste travava os tiles, o backend citava um caminho em prosa, e os dois nunca se olhavam. Agora um próximo rename quebra ali.

### A7 — SKILL.md da didática, texto morto — `fa19bcf`

Dois pontos mortos, mais um terceiro achado ao reconferir o código:

1. "Coruja" não existe como componente — é `Boris` (`web/src/pet/Boris.jsx`, importado em `App.jsx:20`); coruja é a forma desenhada, não o nome do símbolo. `PetFab`/`PetSheet` ficam em `App.jsx`.
2. "só na Watchlist do Estudo" é falso desde 2026-08-08 — a Fase 1 da auditoria de UX reverteu a restrição por modo, reversão registrada no comentário do render (`App.jsx` ~`:9590`). O FAB aparece em qualquer aba, nos dois modos; o que ainda o condiciona é didática ligada + tela livre de overlay + `config.fabVisivel` (F10-20260809, default LIGADO — opção de esconder, não reversão).
3. **[desvio, Rule 1]** a voz não é mais `speechSynthesis` direto: desde F10-20260807-03 é roteada por plataforma em `web/src/pet/vozBoris.js`. Também caiu o "pendente de medição no aparelho real" (já medido) e entraram os guardiões que nasceram depois.

## Testes executados

| Verificação | Resultado |
|---|---|
| `bash scripts/executar.sh --testes` (fora do sandbox, ao final) | **2691 passed, 5 skipped, 3 xfailed, 0 failed**; **137/137 `.mjs` OK**; `exit=0` |
| Baseline de entrada (mesma medição, antes do A1) | 2682 passed, 5 skipped, 3 xfailed + 134 `.mjs` |
| `cd web && npx vite build` | verde (`✓ built in 2.26s`, PWA gerado) |
| `pytest -k metering` (A6) | 19 passed |
| `pytest tests/test_opcoes_dsl.py` (A6) | 68 passed |
| `node web/tests/test_perfil_reorg.mjs` (A6) | todos os testes passaram |
| `grep "Coruja\|só na Watchlist" SKILL.md` (A7) | vazio |

Delta de +9 testes pytest e +3 `.mjs` é exatamente o que os itens criaram (A1: 2 pytest novos + `test_pet_opcoes.mjs`; A2: 3 pytest novos; A3: `test_vocabulario_opcoes.mjs`; A4: `test_tour_opcoes.mjs`; A6: 4 asserções novas dentro de um `.mjs` existente). **Zero regressão.**

## Decisões Made

- **A3 não foi reimplementado.** A Fase 24 já havia entregue o que o achado pedia; o item virou criação do guardião ausente. Registrar o achado como "desatualizado" é mais honesto que fabricar trabalho.
- **Título igual, subtítulo diferente** na aba Opções: "Opções" não tem sinônimo de mesa (ao contrário de Watchlist × Monitoramento). A igualdade ficou travada em teste para que uma divergência futura seja decisão, não acidente.
- **Custo zero de MCP no resumo do pet da aba Opções** (ADR-027): o servidor manda o determinístico e nomeia o que falta, em vez de chamar o serviço pago ou inventar.
- **`skill_ref.sem_setup` intocada** no A5: ausência de SETUP é conceito diferente de ausência de DADO.
- **Guardião novo deriva da fonte.** Três dos sete achados (A1, A5, A6) nasceram de texto redigitado que apodreceu; todo guardião criado aqui lê a fonte (`BottomNav.defs`, `CLAUDE.md`, `PerfilHub`) em vez de repetir o texto.

## Deviations from Plan

### Auto-fixed / registradas

**1. [Rule 1 — Achado desatualizado] A3 já estava implementado**
- **Encontrado em:** Task A3
- **Problema:** o plano pedia criar `tituloOpcoes`/`subtituloOpcoes` em `copy.js` e ligá-los em `OpcoesScreen.jsx`; a Fase 24 (`404f8e6`) já havia feito as duas coisas.
- **Correção:** o item virou o guardião que faltava (`test_vocabulario_opcoes.mjs`) + nota datada nos dois blocos de `copy.js`. Nenhum texto de produto alterado.
- **Commit:** `9265f0f`

**2. [Rule 1 — Bug de documentação, mesmo parágrafo] Voz do Boris descrita como `speechSynthesis`**
- **Encontrado em:** Task A7
- **Problema:** além dos dois pontos que o plano listava, o mesmo parágrafo do `SKILL.md` afirmava que a voz é `speechSynthesis` pt-BR — obsoleto desde F10-20260807-03 (`web/src/pet/vozBoris.js` roteia por plataforma; o app Capacitor usa o plugin TTS nativo). Também dizia "pendente de medição no aparelho real", já feita.
- **Correção:** parágrafo reescrito com a rota real e os guardiões que nasceram depois.
- **Commit:** `fa19bcf`

**3. [fora de escopo, NÃO corrigido] `web/src/api.js:11` (`ADDR_HINT`) tem o mesmo defeito do A6**
- **Encontrado em:** Task A6
- **Problema:** o `ADDR_HINT` cita "Perfil → Conta & preferências" quando o bloco SERVIDOR DO APP migrou para "Perfil → Fonte de dados" (qa/45 Decisão 1). É o mesmo defeito, em outro arquivo e com outro destino.
- **Decisão:** **não corrigido** — a task A6 é escopada a `metering.py` e a correção pertence a outro item. Registrado em três lugares para não se perder: neste SUMMARY, no comentário da seção 7 de `web/tests/test_perfil_reorg.mjs` (com a instrução de como ampliar o guardião quando o achado for fechado) e na mensagem do commit `704955d`.
- **Por que o guardião do A6 lê só `metering.py`:** ampliá-lo para o front agora falharia de propósito, transformando um guardião em um TODO vermelho permanente.

**4. [fora de escopo, commit separado] Flakiness sob carga concorrente**
- **Encontrado em:** entre A5 e A6, com várias sessões rodando a suíte em paralelo
- **Problema:** `test_opcoes_dsl.py`/`test_thread_safety.py` falham ocasionalmente sob carga concorrente pesada — não relacionado a nenhuma edição desta fase.
- **Ação:** investigado e documentado em `server/tests/test_thread_safety.py`, commit `16c07a2`, **separado** dos commits de tarefa para não contaminar a atomicidade dos itens.

---

**Total de desvios:** 2 auto-corrigidos (2× Rule 1), 2 registrados sem correção (1 fora de escopo, 1 pré-existente não relacionado).
**Impacto no plano:** nenhum scope creep. Os dois auto-fixes são do mesmo tipo do trabalho pedido (documentação/texto que descreve comportamento inexistente). Os dois registrados ficaram deliberadamente fora.

## Issues Encountered

**Disco cheio (ENOSPC) no meio do A6.** O acúmulo de diretórios SQLite temporários de várias sessões rodando a suíte completa em paralelo encheu o volume; a execução anterior travou com `metering.py` já editado e não commitado. Resolvido pelo usuário (liberou espaço; 8,8 GiB livres na retomada) e a execução foi retomada em sessão nova a partir do estado confirmado por `git status`/`grep`. Nenhum trabalho perdido — as partes pendentes do A6 (fixture de teste + guardião novo) foram feitas na retomada e commitadas juntas, mantendo o item atômico.

## Known Stubs

Nenhum. Todo dado exibido vem de fonte real ou é explicitamente nomeado como ausente (o `_pet_resumo_opcoes` do A1 diz o que não sabe em vez de preencher com `null`/omissão).

## User Setup Required

Nenhum — nenhuma configuração de serviço externo.

## Next Phase Readiness

**Pronto.** Os sete itens da Fase A estão fechados, cada um com commit próprio, suíte canônica sem regressão e `vite build` verde.

**Atenção para o próximo passo:**

1. **Publicação do front é etapa separada e obrigatória.** A1, A3, A4 e A5 tocam `web/src/` (`App.jsx`, `copy.js`). Sem `scripts/bump.sh` + `scripts/publicar-web.sh`, o trabalho fica testado e nunca vai ao ar. `server/web_dist`, `web/src/version.js` e `SERVER_BUILD_ID` ficaram **intocados** de propósito, à espera do OK humano.
2. **Backend também precisa de deploy:** A1, A2 e A6 tocam `server/app/` (`conceitos.py`, `main.py`, `metering.py`).
3. **Achado aberto:** `web/src/api.js:11` (`ADDR_HINT`) — mesmo defeito do A6, outro destino. Candidato natural a uma quick-task ou ao próximo plano desta fase.
4. **C3 do 26-CONTEXT segue aberto** (registro único de telas no front). O `test_pet_opcoes.mjs` criado no A1 é a rede de segurança provisória: aba nova na barra sem snapshot/allowlist agora falha, em vez de emudecer o assistente.
5. **B2 e B3** continuam em backlog, como o 26-CONTEXT registra (B2 sem decisão de abordagem; B3 aguarda fase de planejamento própria).

---
*Phase: 26-otimizacao-ux-ia*
*Completed: 2026-09-13*

## Self-Check: PASSED

- Arquivos criados conferidos em disco (3 guardiões novos + este SUMMARY): todos FOUND.
- Os 8 commits da fase conferidos em `git log --oneline --all`: todos FOUND.
- `git log --name-only 65ab89e..HEAD` não toca `server/web_dist`, `server/admin_dist`, `web/src/version.js` nem `SERVER_BUILD_ID`.
