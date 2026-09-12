---
phase: 24-opcoes-mcp-analise-e-setups
plan: 12
subsystem: api
tags: [fastapi, react, opcoes, mcp, frescor, calendario-b3, transparencia]

requires:
  - phase: 24-opcoes-mcp-analise-e-setups (plano 02)
    provides: "o envelope de `/status` e `/leitura` com `pregao` e `frescor`, e o chip de frescor em três variantes"
  - phase: "pregao.py (2026-08-17)"
    provides: "`is_trading_day`/`is_holiday`/`feriados` — o calendário da B3 com fixos, móveis derivados da Páscoa, exceções por ofício e `B3_FERIADOS_EXTRA`"
provides:
  - "`_atraso_em_pregoes` — helper puro que conta os pregões ESTRITAMENTE entre o dado e hoje, pelo calendário da B3"
  - "`atraso: {pregoes, referencia, fonte}` no envelope de `/status` e de `/leitura` — sem chamada de tool nova"
  - "a QUARTA variante do chip da aba Opções, com precedência sobre `dado em dia`"
  - "`opcoesAtrasoPregoes`/`opcoesAtrasoAjuda` nas duas vozes"
  - "guardiões nos dois lados, todos com relógio fixo por `_hoje`"
affects: [24-05 (publicação — este texto só chega ao usuário depois do bump + publicar-web.sh), qualquer plano futuro que queira BLOQUEAR por distância (esta entrega deliberadamente não bloqueia)]

tech-stack:
  added: []
  patterns:
    - "medir em vez de herdar: o veredito do fornecedor (SLA) e a pergunta do usuário (de quando é este número?) são coisas diferentes"
    - "relógio injetável (`_hoje`) no helper puro — mesmo padrão de `_dia_sp`; nenhum teste muda de resultado conforme o dia em que a suíte roda"
    - "calendário com fonte única: a contagem delega a `pregao.is_trading_day`, e um guardião proíbe `weekday()` dentro do helper"

key-files:
  created: []
  modified:
    - server/app/options_mcp_api.py
    - server/tests/test_options_mcp_api.py
    - web/src/opcoes/OpcoesScreen.jsx
    - web/src/copy.js
    - web/tests/test_opcoes_mcp_aba_ui.mjs

key-decisions:
  - "A distância VENCE o veredito herdado no chip: com pregão faltando, 'dado em dia' é falso mesmo assinado pelo fornecedor. Mas quando o frescor TAMBÉM bloqueia as duas informações SOMAM — idade da carga e pregões faltando medem coisas diferentes"
  - "O dia corrente nunca conta: o COTAHIST sai depois do fechamento, e contar hoje faria o app acusar atraso toda manhã sobre um dado que ainda não poderia existir — alerta que toca todo dia deixa de ser lido"
  - "`pregoes: None` para data ausente, torta ou futura — nunca 0, que afirmaria 'está no último pregão fechado' sem ter como saber"
  - "NADA passou a ser bloqueado: quem barra veredito e criação de setup continua sendo o frescor do serviço (ADR-027, Decisão 8). Mudar o critério de bloqueio seria outra decisão"
  - "A ajuda da contagem só aparece quando há contagem na tela — explicar um número que ninguém está vendo é ruído"
  - "O rótulo do chip é o MESMO nos dois modos: é contagem de pregão, não juízo; a voz por modo mora na frase de ajuda"

patterns-established:
  - "Sanidade de ORDEM no guardião de front: a função que compara posições no fonte é exercitada também contra uma string com a ordem invertida, senão a asserção passaria para sempre por um typo de regex"

requirements-completed: ["achado ao vivo 2026-09-11 — 'dado em dia' com dois pregões faltando"]

duration: 40min
completed: 2026-09-11
---

# Fase 24 Plano 12: a tela diz a distância em pregões, em vez de herdar o SLA da fonte — Summary

**A aba Opções passou a afirmar quantos pregões separam o dado exibido do
último pregão fechado, medindo pelo calendário da B3 — e essa medição tem
precedência sobre o "dado em dia" que o fornecedor assina, sem bloquear nada e
sem uma chamada de tool a mais.**

## Performance

- **Duration:** ~40 min
- **Started:** 2026-09-11T22:05 (-03, aprox.)
- **Completed:** 2026-09-11T22:46 (-03), somando a suíte canônica
- **Tasks:** 3
- **Files modified:** 5

## O que estava errado, em uma passagem

Medido ao vivo em 2026-09-11 com `scripts/diagnostico-leitura-opcoes.sh`: a
aba mostrava "Pregão: 2026-09-08" numa **sexta (11/09)**, com o chip dizendo
**"dado em dia"**. O serviço estava coerente com o próprio contrato —
`negociacao_b3` com idade de 49,58 h contra um SLA de 96 h — e mesmo assim
quarta (09) e quinta (10) não estavam na base.

Um SLA de quatro dias para cotação diária permite que o app afirme "em dia"
sobre dado de dois pregões atrás. O princípio 3 do `CLAUDE.md` pede o oposto:
dizer se o dado é de tempo real, atrasado ou histórico. O Boris tem calendário
de pregão próprio (`server/app/pregao.py`) e pode afirmar a distância REAL em
vez de repassar o veredito de quem publica.

`2026-09-07` foi feriado (Independência, segunda) — é dele o 404 do
`COTAHIST_D07092026.ZIP` no `last_failure` do MyData, porque a B3 não publica
arquivo de dia sem pregão. Esse erro é esperado e **não entra na conta**: o
teste do feriado prova exatamente isso.

## Prova RED → GREEN

Os testes foram escritos **antes** da correção e rodados contra o código de
antes (arquivos temporários, depois movidos para os guardiões canônicos e
apagados).

| Correção | Teste escrito primeiro | RED observado (código de antes) | GREEN |
|---|---|---|---|
| `_atraso_em_pregoes` + envelope das duas rotas | 16 testes do bloco 24-12 em `test_options_mcp_api.py` | `16 failed` — `AttributeError: module 'app.options_mcp_api' has no attribute '_atraso_em_pregoes'` (×14) e `KeyError: 'atraso'` (×2) | `16 passed` |
| o chip diz a distância | bloco 12 de `test_opcoes_mcp_aba_ui.mjs` (23 asserções) | `14 FALHA(S)` | `todos os testes passaram` |

RED do backend, agrupado:

```
  14 E       AttributeError: module 'app.options_mcp_api' has no attribute '_atraso_em_pregoes'
   2 E       KeyError: 'atraso'
```

RED do front:

```
FALHOU o chip tem a QUARTA variante (distância em pregões)
FALHOU a distância vem do `atraso` da resposta, na mesma origem do `pregao`
FALHOU só conta como distância a partir de 1 pregão (0 e null seguem o caminho de hoje)
FALHOU a checagem do atraso vem ANTES da que escolhe "dado em dia"
FALHOU com distância, "dado em dia" não é alcançável (guarda explícita no ramo)
FALHOU a ajuda da contagem vai no rodapé do cabeçalho
FALHOU COPY tem opcoesAtrasoPregoes nos dois modos
...
14 FALHA(S)
```

As 3 asserções que já passavam no RED são as que **não descrevem a correção**:
a sanidade da checagem de ordem (que precisa passar nos dois estados — é o que
sanidade significa), "a distância não pinta o chip" (verdadeira por ausência) e
a paridade do conjunto `opcoes*` (que já valia e este plano não podia quebrar).

## Task Commits

1. **Task 1 — `_atraso_em_pregoes` no backend** — `0f10c7d` (feat)
2. **Task 2 — o chip da tela diz a distância** — `7c0b10d` (feat)
3. **Task 3 — guardiões nos dois lados** — `5e43c74` (test)

Cada commit foi conferido com `git diff --cached --stat` antes de fechar:
1, 2 e 2 arquivos respectivamente, nenhum arquivo de terceiros dentro (ver
"Nota operacional"). Nenhum dos três apaga arquivo nenhum
(`git diff --diff-filter=D` vazio nos três).

## Files Created/Modified

- `server/app/options_mcp_api.py` — `from . import ... pregao`, `date` no
  import de `datetime`, `FONTE_DO_ATRASO`, `_atraso_em_pregoes`, e o
  `pregao_do_dado` extraído para variável nas duas rotas (era expressão
  inline no `return`) para que `atraso` meça o MESMO valor que `pregao` exibe
- `server/tests/test_options_mcp_api.py` — bloco 24-12: 16 testes (8 do
  helper puro, 9 deles vindos de uma parametrização, mais 2 de rota), duas
  linhas no docstring do arquivo, `date` e `pregao` nos imports
- `web/src/opcoes/OpcoesScreen.jsx` — `atraso`/`pregoesAtras`/`distancia`, a
  quarta variante do chip com a guarda explícita no ramo do "em dia", a soma
  condicionada ao alerta do serviço, e a linha de ajuda no rodapé do cabeçalho
- `web/src/copy.js` — `opcoesAtrasoPregoes` e `opcoesAtrasoAjuda` nos DOIS
  modos
- `web/tests/test_opcoes_mcp_aba_ui.mjs` — bloco 12 (23 asserções, 1 delas de
  sanidade de ordem) e cinco linhas no cabeçalho do arquivo

## O que a tela passou a dizer

No caso medido (pregão de 2026-09-08 visto numa sexta, 11/09, com o serviço
dizendo `em_dia`):

```
antes:   Pregão: 2026-09-08   Fonte: mcp.semente.dev   [ dado em dia ]

depois:  Pregão: 2026-09-08   Fonte: mcp.semente.dev   [ 2 pregões atrás ]
         A conta é de pregões FECHADOS, pelo calendário da B3: fim de semana e
         feriado não entram. O pregão de hoje também não — o fechamento dele
         só sai à noite, então ele só passa a contar amanhã.
```

Com o frescor do serviço também bloqueando, as duas informações convivem —
elas medem coisas diferentes:

```
[ dado atrasado (50 h) · 2 pregões atrás ]
```

Voz de mesa (Modo Operador), mesma substância na ajuda: "Contagem de pregões
FECHADOS pelo calendário da B3 — fim de semana e feriado fora. O pregão de
hoje só entra depois de publicado o fechamento."

## Decisões Made

1. **A distância vence o veredito herdado, mas não o apaga.** Com
   `atraso.pregoes >= 1` o chip deixa de poder dizer "dado em dia" (guarda
   explícita no ramo, e a checagem do atraso vem ANTES no fonte — as duas
   coisas travadas por guardião). Quando o serviço TAMBÉM bloqueia, a
   distância **soma** ao alerta em vez de substituí-lo: idade da carga e
   pregões faltando são grandezas diferentes, e escolher uma esconderia a
   outra.
2. **O dia corrente nunca entra na conta.** Não é conservadorismo: o COTAHIST
   de um pregão só sai depois do fechamento, então contar hoje faria o app
   acusar atraso todas as manhãs sobre um dado que ainda não poderia existir.
   Alerta que toca todo dia deixa de ser lido — e aí ele não serve nem quando
   está certo.
3. **`None`, nunca 0, por falta de informação.** `0` é uma afirmação forte
   ("o dado está no último pregão fechado"). Data ausente, malformada ou no
   futuro devolve a tela ao comportamento de antes, que é o que se sabe dizer.
4. **Nada passou a ser bloqueado.** Quem barra veredito e criação de setup
   continua sendo o frescor do serviço (ADR-027, Decisão 8). O carimbo
   informa; mudar o critério de bloqueio seria outra decisão, e não é esta.
   Há asserção explícita disso no guardião de rota (`frescor.bloqueia is
   False` no cenário com atraso medido).
5. **Calendário com fonte única.** A contagem delega a `pregao.is_trading_day`
   — que conhece Carnaval, Corpus Christi, as exceções por ofício e a env
   `B3_FERIADOS_EXTRA`. Um guardião proíbe `weekday()` dentro do helper: uma
   segunda contagem divergiria em silêncio no primeiro Carnaval.
6. **`fonte: "calendario_b3"` no envelope.** É o que permite à tela (hoje ou
   amanhã) dizer de onde veio o número sem raspar texto. Token de máquina, não
   prosa — por isso não entra em `AVISOS` nem na varredura do guardião
   imperativo.
7. **`pregao_do_dado` virou variável nas duas rotas.** A expressão estava
   inline no `return`; recalculá-la para o `atraso` abriria a porta a dois
   carimbos discordando no mesmo corpo. O guardião compara o `atraso` da rota
   com o helper aplicado ao `pregao` que a própria rota devolveu.
8. **A ajuda só aparece quando há contagem.** Explicar a regra de um número
   que não está na tela é ruído; e a regra que ela explica ("hoje ainda não
   conta") é exatamente a que faria alguém achar que o app está mentindo às
   11 h da manhã.
9. **O rótulo do chip é idêntico nos dois modos.** Contagem de pregão não tem
   voz — "2 pregões atrás" já é a frase mais curta que diz o fato. A voz por
   modo mora na ajuda, onde há espaço para explicar.

## Deviations from Plan

### 1. [Rule 3 — Blocking] Testes temporários não podiam importar o módulo canônico

- **Found during:** Task 1 (prova RED)
- **Issue:** `server/tests/` não é pacote e `pytest.ini` só põe `server/` no
  `pythonpath`, então `from test_options_mcp_api import _client, ...` no
  arquivo temporário morria em `ModuleNotFoundError` na coleta.
- **Fix:** os helpers de isolamento (`_isolado`, `_client`, `_registra`,
  `_auth`, `_usado`, `_espiao`) foram copiados para o arquivo temporário, que
  existiu só para a prova RED e foi apagado na Task 3. O bloco definitivo, no
  módulo canônico, usa os helpers de lá sem duplicar nada.
- **Files modified:** nenhum arquivo versionado
- **Commit:** — (arquivo temporário, fora do git)

### 2. [Rule 3 — Blocking] `web/dist` restaurado depois do `npx vite build`

- **Found during:** Task 2 (verificação)
- **Issue:** Durante esta execução, **outra sessão publicou o front na mesma
  árvore** (`web/src/version.js` e `SERVER_BUILD_ID` bumpados para
  `F10-20260911-06`, `server/web_dist` regravado — arquivos com mtime 22:14 e
  22:15, enquanto eu editava `options_mcp_api.py`). Antes do meu build,
  `web/dist` e `server/web_dist` eram byte a byte idênticos (`diff -rq`
  limpo). Rodar `npx vite build` (exigido pelo plano) regeraria `web/dist`
  com o MEU código e o mesmo carimbo, e uma republicação subsequente da outra
  sessão levaria ao ar, sem checkpoint, um front que ninguém aprovou.
- **Fix:** `rsync -a --delete server/web_dist/ web/dist/` depois do build —
  `web/dist` voltou a ser byte a byte o artefato publicado (`diff -rq` limpo
  de novo). O build já tinha cumprido o papel dele (provar que o JSX compila)
  antes da restauração. `web/dist` é gitignored; nenhum arquivo versionado foi
  tocado, e os arquivos da outra sessão ficaram exatamente como estavam.
  `test_ios_assets.mjs` continuou verde nos dois momentos (o bundle iOS está
  em `F10-20260911-05`, e builds diferentes são meio-de-entrega tolerado).
- **Files modified:** nenhum arquivo versionado
- **Commit:** — (artefato local, fora do git)

## Nota operacional — árvore compartilhada

O briefing desta execução afirmava árvore limpa. Ela não estava: entre o
primeiro `git status` (limpo, só as 4 pastas não rastreadas de
`.claude/skills/`) e o primeiro `git add`, uma publicação de outra sessão
apareceu no índice — `server/app/main.py`, `web/src/version.js` e 30+ arquivos
de `server/web_dist`. **Nenhum deles entrou em commit meu**: cada `git add`
foi por caminho explícito e conferido com `git diff --cached --stat` antes do
commit (1, 2 e 2 arquivos). Nada de `git add -A`, nenhum push, nenhum PR,
`bump.sh`/`publicar-web.sh` não foram executados por mim.

## Verificação

`bash scripts/executar.sh --testes` — **fora do sandbox** (dentro dele o
`ssl.load_verify_locations` levanta `PermissionError` e a suíte mente com ~26
falhas falsas):

```
2473 passed, 5 skipped, 655 warnings in 60.30s
129 arquivos web/tests/*.mjs [OK]
exit=0
```

Baseline a não regredir: `2457 passed, 5 skipped` + 129 `.mjs`. O delta de
**+16** são exatamente os testes novos do backend (o bloco do front é um
guardião só, já contado entre os 129).

`cd web && npx vite build` — verde (`23 entries (921.95 KiB)` precacheadas,
`dist/sw.js` gerado) antes da restauração descrita no Desvio 2.

Guardiões específicos, todos verdes: `test_options_mcp_api.py` (76),
`test_options_mcp_leitura.py`, `test_mcp_guardioes.py` (AST do `_cap_check`),
`test_mcp_cap.py`, `test_opcoes_mcp_aba_ui.mjs`, `test_opcoes_analisar_ui.mjs`,
`test_copy_theme.mjs`, `test_ios_assets.mjs`.

## Limitações conhecidas

- **Sem verificação ao vivo.** `MCP_CLIENT_SECRET` não está no ambiente de
  desenvolvimento (D-24.7): todo teste é offline, com espião de
  `mcp_client.call_tool`. O caso do achado foi reproduzido com as datas
  medidas, não com uma resposta viva.
- **O texto ainda não chegou ao usuário.** Isto é mudança de front: só vai ao
  ar com bump + `publicar-web.sh` (plano 24-05, que por desenho só roda com o
  OK explícito do Alex), e no iPhone só com build novo. A publicação que
  aconteceu durante esta execução (`F10-20260911-06`) é de OUTRA sessão e
  **não** contém estas mudanças.
- **Só `/status` e `/leitura` carregam `atraso`.** `/cadeia`, `/operaveis`,
  `/proposta`, `/possibilidades` e `/setups/{name}/grafico` também devolvem
  `pregao` e não ganharam o campo — fora do escopo do plano. O helper é puro e
  já está pronto para elas.
- **A contagem é O(dias) em laço.** Para um `trading_date` muito antigo
  (anos), o laço percorre dia a dia chamando `pregao.is_trading_day`. Na
  prática o valor vem do nosso próprio serviço e a distância é de dias; não há
  entrada de usuário nesse caminho.

## Self-Check: PASSED

- `server/app/options_mcp_api.py` — FOUND (`_atraso_em_pregoes`,
  `FONTE_DO_ATRASO`, `"atraso"` nas duas rotas)
- `web/src/opcoes/OpcoesScreen.jsx` — FOUND (`atraso`, `pregoesAtras`,
  `distancia`, `cp.opcoesAtrasoAjuda`)
- `web/src/copy.js` — FOUND (`opcoesAtrasoPregoes`/`opcoesAtrasoAjuda` nos
  dois modos)
- `server/tests/test_options_mcp_api.py` — FOUND (bloco 24-12, 16 testes)
- `web/tests/test_opcoes_mcp_aba_ui.mjs` — FOUND (bloco 12, 23 asserções)
- Commits `0f10c7d`, `7c0b10d`, `5e43c74` — FOUND em `git log`
