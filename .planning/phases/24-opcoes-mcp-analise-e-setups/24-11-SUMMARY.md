---
phase: 24-opcoes-mcp-analise-e-setups
plan: 11
subsystem: api
tags: [fastapi, react, opcoes, mcp, leitura, estado-vazio, transparencia]

requires:
  - phase: 24-opcoes-mcp-analise-e-setups (plano 02)
    provides: "a rota `/leitura/{ticker}` com o `behavior` verbatim, o bloco `AVISOS`, a tabela LEITURA DO ATIVO e o guardião `test_opcoes_analisar_ui.mjs`"
provides:
  - "`_lacunas_da_leitura` — helper puro que diz POR QUE cada campo ausente da leitura está ausente, derivado só do que o próprio `behavior` mostra"
  - "`_campo_vazio` — a ausência de `range_63_sessions` é conteúdo nulo, não chave nula"
  - "`MOTIVO_JANELA_63`/`MOTIVO_SERIE_CURTA`/`MOTIVO_HV_AUSENTE` em `AVISOS`"
  - "`lacunas` no payload da `/leitura`, ao lado de `behavior` — nenhuma chamada de tool nova"
  - "`LacunasDaLeitura` + `ROTULO_LEITURA` no rodapé do bloco de leitura, e `opcoesLacuna` nas duas vozes"
  - "duas travas contra afirmar tamanho de série (vocabulário + forma), com sanidade"
affects: [24-05 (publicação — este texto só chega ao usuário depois do bump + publicar-web.sh), qualquer plano futuro que acrescente campo à LEITURA DO ATIVO]

tech-stack:
  added: []
  patterns:
    - "estado vazio com motivo derivado da PRÓPRIA resposta: nada é consultado a mais para explicar o que já veio"
    - "explicar a ausência sem preenchê-la nem recalculá-la — `null` continua `null` e a fonte do número continua única"
    - "o motivo é do backend e viaja verbatim; o front só junta rótulos, e a gramática que os une tem voz por modo"

key-files:
  created: []
  modified:
    - server/app/options_mcp_api.py
    - server/tests/test_options_mcp_api.py
    - web/src/opcoes/OpcoesScreen.jsx
    - web/src/copy.js
    - web/tests/test_opcoes_analisar_ui.mjs

key-decisions:
  - "O motivo vai AGRUPADO no rodapé, não repetido em cinco linhas da tabela: repetir empurraria para fora da tela os números que vieram — o oposto do que o achado pede"
  - "A regra é de OBSERVAÇÃO, não de dedução: a lista nomeia só os campos que de fato vieram vazios, e o texto fala da JANELA que o serviço declara, nunca do tamanho da série (que o `behavior` não traz)"
  - "`behavior` sem `close` produz lista vazia: sem leitura nenhuma, dizer que 'o provedor não publica volatilidade para este ativo' seria uma acusação que ninguém mediu"
  - "A trava do guardião mudou de forma em relação ao plano ('dígito seguido de pregões' proibiria o próprio texto aprovado): virou vocabulário (só 21/63 podem ser número) + forma (nenhuma frase diz que a série TEM n pregões), as duas com sanidade"
  - "`range_63_sessions` chega SEMPRE como dict com os dois extremos nulos — a tela mostrava '— – —', travessão travestido de faixa; agora é UM travessão, com o motivo embaixo"

patterns-established:
  - "Sentinela em vez de cópia do texto real no guardião de front: o que se prova é o TRÂNSITO do motivo (entra inteiro, sai inteiro), sem criar uma segunda cópia da frase que envelheceria sem ninguém notar"

requirements-completed: ["achado ao vivo 2026-09-11 — LEITURA DO ATIVO com campos vazios"]

duration: 35min
completed: 2026-09-11
---

# Fase 24 Plano 11: a leitura do ativo diz por que o campo veio vazio — Summary

**Os cinco travessões mudos da LEITURA DO ATIVO passaram a ter motivo escrito
embaixo da tabela — derivado do que o próprio `behavior` mostra, sem preencher
número nenhum, sem recalcular indicador nenhum e sem uma chamada de tool a
mais.**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-09-11T21:07 (-03, aprox.)
- **Completed:** 2026-09-11T21:41 (-03), somando a suíte canônica
- **Tasks:** 3
- **Files modified:** 5

## O que estava errado, em uma passagem

Na screenshot do Alex (PETR4, pregão de 2026-09-08), `Fechamento`, `RSI 14`,
`Distância da média 21` e `Variação em 21 pregões` vieram; `Tendência`, `HV 21`,
`HV 63`, `Distância da média 63` e `Faixa de 63 pregões` mostravam travessão e
mais nada.

O diagnóstico (já no PLAN, medido no serviço): tudo que exige 63 pregões falta
porque a série não fecha essa janela — `sma63` nulo derruba junto `trend`,
`distance_from_sma63_pct` e `range_63_sessions`; e os dois `hv` faltam porque
são colunas **diretas** do candle, que o MyData não populou (o serviço não as
calcula).

Travessão mudo não é estado vazio: quem olha não sabe se o app quebrou, se o
ativo é estranho ou se falta dado (princípio 9). Das quatro saídas
apresentadas, o Alex escolheu **dizer o motivo na tela, sem duplicar cálculo** —
preencher o número seria fabricar (princípio 4) e recalcular criaria uma
segunda implementação do mesmo indicador, divergindo da do serviço em silêncio.

## Prova RED → GREEN

Os testes foram escritos **antes** da correção e rodados contra o código de
antes (arquivos temporários, depois movidos para os guardiões canônicos e
apagados).

| Correção | Teste escrito primeiro | RED observado (código de antes) | GREEN |
|---|---|---|---|
| helper + motivos + rota | 10 testes do bloco 24-11 em `test_options_mcp_api.py` | `10 failed` — `AttributeError: module 'app.options_mcp_api' has no attribute '_lacunas_da_leitura'` (×8), `... 'MOTIVO_JANELA_63'` (×1), `KeyError: 'lacunas'` (×1) | `10 passed` |
| a tela mostra os motivos | bloco 15 de `test_opcoes_analisar_ui.mjs` (28 asserções) | `18 FALHA(S)` | `todos os testes passaram` |

As 10 asserções que já passavam no RED são as que **não descrevem a correção**:
2 de sanidade de regex (precisam passar nos dois estados — é o que sanidade
significa), 5 de "nenhum arquivo de `web/src/opcoes/` recalcula indicador"
(regra que já valia e este plano não podia quebrar), a paridade de chaves
`opcoes*` (que já estava no arquivo) e **2 que passavam por vacuidade**: "a
frase não afirma tamanho de série" sobre a string vazia que uma
`cp.opcoesLacuna` inexistente produzia. Foi isso que motivou a terceira
asserção de sanidade da versão final — a que prova que essa regex pega
"a série tem 42 pregões".

Trechos do RED do backend:

```
E       AttributeError: module 'app.options_mcp_api' has no attribute '_lacunas_da_leitura'
E       AttributeError: module 'app.options_mcp_api' has no attribute 'MOTIVO_JANELA_63'
E       KeyError: 'lacunas'
FAILED tests/...::test_lacunas_da_tela_do_alex_sao_janela_de_63_e_hv
```

E do front:

```
FALHOU existe componente próprio para as lacunas da leitura
FALHOU o motivo do backend só entra como ARGUMENTO de `cp.opcoesLacuna`
FALHOU a faixa de 63 usa o helper que devolve UM travessão sem os dois extremos
FALHOU estudo: `opcoesLacuna` é função
FALHOU operador: o motivo do backend aparece VERBATIM
...
18 FALHA(S)
```

## Task Commits

1. **Task 1 — `_lacunas_da_leitura` no backend** — `4801487` (feat)
2. **Task 2 — a tela mostra os motivos, agrupados** — `56f61b7` (feat)
3. **Task 3 — guardiões nos dois lados** — `0dac014` (test)

## Files Created/Modified

- `server/app/options_mcp_api.py` — os três `MOTIVO_*` (acrescentados a
  `AVISOS`), `_CAMPOS_DE_63`/`_CAMPOS_DE_JANELA`/`_CAMPOS_DE_HV`,
  `_campo_vazio`, `_lacunas_da_leitura`, e `"lacunas"` no envelope da
  `/leitura` ao lado de `behavior`
- `server/tests/test_options_mcp_api.py` — bloco 24-11: 10 testes (9 do helper
  puro + 1 de rota), com o `behavior` real da screenshot; `import re`; linha
  nova no docstring do arquivo
- `web/src/opcoes/OpcoesScreen.jsx` — `faixa()`, `ROTULO_LEITURA`,
  `LacunasDaLeitura`, o componente renderizado abaixo do carimbo do pregão e a
  linha da Faixa de 63 usando o helper
- `web/src/copy.js` — `opcoesLacuna` nos DOIS modos (voz de professor × voz de
  mesa), com a mesma substância
- `web/tests/test_opcoes_analisar_ui.mjs` — bloco 15 (28 asserções, 3 delas de
  sanidade), `readdirSync` no import e duas linhas no cabeçalho

## O que a tela passou a dizer

```
[estudo]   Tendência, Distância da média 63 e Faixa de 63 pregões não vieram:
           exigem 63 pregões e a série disponível não fecha essa janela — a de
           21 fecha, por isso os campos de 21 vieram. Nada foi estimado no lugar.
[estudo]   HV 21 e HV 63 não vieram: o provedor não publica volatilidade
           realizada para este ativo; ela não é calculada aqui, por isso não há
           número a mostrar. Nada foi estimado no lugar.

[operador] Tendência, Distância da média 63 e Faixa de 63 pregões sem número:
           exigem 63 pregões e a série disponível não fecha essa janela — a de
           21 fecha, por isso os campos de 21 vieram. Nada estimado no lugar.
[operador] HV 21 e HV 63 sem número: o provedor não publica volatilidade
           realizada para este ativo; ela não é calculada aqui, por isso não há
           número a mostrar. Nada estimado no lugar.
```

Os três motivos dizem O QUE falta, POR QUE falta e que ninguém estimou nada no
lugar. Nenhum culpa quem lê nem sugere ação que não existe — "tente de novo"
não encurta uma série de pregões.

## Decisões Made

1. **Agrupado no rodapé, não repetido na tabela.** Cinco linhas de explicação
   dentro da tabela empurrariam para fora da tela os números que **vieram** —
   o oposto do que o achado pede. A tabela continua com travessão; o porquê
   fica ao lado do carimbo "Leitura referente ao pregão de …", na mesma linha
   discreta (`textMuted`, 11,5 px), sem ícone de alerta: é informação, não erro.
2. **Observação, nunca dedução.** A lista nomeia só o que de fato veio vazio.
   No caso da série curta demais, `rsi14` (que precisa de 14 pregões e veio)
   fica de fora — nomear um campo presente como ausente seria a mesma
   fabricação, na direção contrária. Guardião próprio nos dois casos.
3. **O texto fala de JANELA, nunca de tamanho de série.** "exigem 63 pregões e
   a série disponível não fecha essa janela" é observável; "a série tem 42
   pregões" seria inventado — o `behavior` não traz a contagem de candles.
4. **`behavior` sem `close` produz lista vazia.** Fora do que o plano
   enumerava: com o envelope degenerado, a regra 3 (hv nulo) sozinha diria "o
   provedor não publica volatilidade realizada para este ativo", que é uma
   afirmação sobre o provedor sustentada em nada. Sem leitura, não há ausência
   a explicar — e a tela já tem estado próprio para isso.
5. **Um mapa só de rótulo↔campo.** `ROTULO_LEITURA` fica ao lado do render da
   tabela: dois vocabulários divergiriam no primeiro rótulo renomeado, e a
   frase passaria a nomear um campo que a tabela não mostra com esse nome.
6. **A gramática é do `copy.js`, o motivo é do backend.** O front junta os
   rótulos ("A, B e C") e escolhe singular/plural; o motivo entra verbatim,
   como argumento. O guardião proíbe interpolá-lo dentro de outra frase.
7. **Nenhuma chamada de tool nova.** A explicação é derivada da mesma resposta
   que já veio: `with _cap_check(uid, 3)` intacto, e o teste de rota afirma que
   as tools chamadas continuam sendo `propose_option_setups` e `list_setups`.

## Deviations from Plan

### 1. [Rule 1 — Bug] A trava do guardião mudou de forma (o plano se contradizia)

- **Found during:** Task 3
- **Issue:** A Task 3 pedia a asserção "nenhuma string de `AVISOS` nem de
  `lacunas` contém dígito seguido de `pregões`". Essa regex reprova o **próprio
  texto aprovado** no mesmo plano: `MOTIVO_JANELA_63` começa com "exigem 63
  pregões". As duas partes do plano não podiam valer ao mesmo tempo.
- **Fix:** Prevaleceu a INTENÇÃO, declarada três vezes no plano e no briefing —
  *não afirmar o tamanho da série*. A trava virou duas camadas, cada uma com
  sanidade própria: (a) **vocabulário** — os únicos números que um motivo pode
  citar são as janelas que o serviço declara nos nomes dos campos (`21`, `63`);
  (b) **forma** — nenhuma frase diz que a série *tem/possui/traz/é de* n
  pregões, e essa camada varre `AVISOS` inteiro. Uma sozinha não bastaria: a
  primeira deixaria passar "a série tem 21 pregões", a segunda deixaria passar
  "restam 42 pregões na base".
- **Files modified:** `server/tests/test_options_mcp_api.py`
- **Commit:** `0dac014`

### 2. [Rule 1 — Bug] "— – —" na Faixa de 63 pregões

- **Found during:** Task 2
- **Issue:** `range_63_sessions` chega **sempre** como dicionário — com
  `highest` e `lowest` nulos quando a janela não fechou. O render antigo
  testava só a existência do objeto, então a linha exibia `— – —`: travessão
  travestido de faixa, que se lê como formatação quebrada e não como ausência
  de dado. É o campo do próprio achado.
- **Fix:** `faixa()` devolve UM travessão quando nenhum dos dois extremos é
  número. O mesmo cuidado está no backend, em `_campo_vazio`: a ausência deste
  campo é conteúdo nulo, não chave nula — tratá-lo como os demais faria o app
  dar por presente uma faixa que não existe.
- **Files modified:** `web/src/opcoes/OpcoesScreen.jsx`,
  `server/app/options_mcp_api.py`
- **Commit:** `56f61b7`, `4801487`

### 3. [Rule 3 — Blocking] `web/dist` restaurado depois do `npx vite build`

- **Found during:** verificação final
- **Issue:** A árvore principal já tinha trabalho em curso de outra sessão (não
  meu): `web/src/version.js` bumpado para `F10-20260911-05`, `server/web_dist`
  republicado e o bundle iOS (`web/ios/App/App/public`, gitignored) sincronizado
  com esse build das 20:29. O `npx vite build` que o plano exige regerou
  `web/dist` **com o mesmo carimbo** e hashes de chunk diferentes, e
  `test_ios_assets.mjs` reprovou exatamente a condição que ele existe para
  pegar: *mesmo build nos dois lados, chunks irmãos faltando*.
- **Fix:** `web/dist` restaurado a partir de `server/web_dist` (byte a byte o
  build das 20:29 — as duas listas de assets conferem). Nenhum arquivo
  versionado foi tocado: `web/dist` e `web/ios/` são gitignored, e o
  `version.js`/`web_dist` da outra sessão ficaram exatamente como estavam. O
  `vite build` já tinha cumprido o papel dele (provar que o JSX compila) antes
  da restauração.
- **Files modified:** nenhum arquivo versionado
- **Commit:** — (artefato local, fora do git)

## Verificação

`bash scripts/executar.sh --testes` — **fora do sandbox** (dentro dele o
`ssl.load_verify_locations` levanta `PermissionError` e a suíte mente com ~26
falhas falsas):

```
2457 passed, 5 skipped, 651 warnings in 55.05s
129 arquivos web/tests/*.mjs [OK]
exit=0
```

Baseline a não regredir: `2447 passed, 5 skipped` + 129 `.mjs`. O delta de +10
são exatamente os testes novos do backend (o bloco do front é um guardião só,
já contado entre os 129).

`cd web && npx vite build` — verde (`23 entries (921.09 KiB)` precacheadas,
`dist/sw.js` gerado) antes da restauração descrita no Desvio 3.

Guardiões específicos, todos verdes: `test_guardrail_imperativo.py`,
`test_mcp_guardioes.py` (AST do `_cap_check`), `test_options_mcp_leitura.py`,
`test_opcoes_mcp_aba_ui.mjs`, `test_copy_theme.mjs`, `test_ios_assets.mjs`.

## Limitações conhecidas

- **Sem verificação ao vivo.** `MCP_CLIENT_SECRET` não está no ambiente de
  desenvolvimento (D-24.7): todo teste é offline, com espião de
  `mcp_client.call_tool`. O caso do achado foi reproduzido com os números da
  screenshot, não com uma resposta viva.
- **O texto ainda não chegou ao usuário.** Isto é mudança de front: só vai ao
  ar com bump + `publicar-web.sh` (plano 24-05, que por desenho só roda com o
  OK explícito do Alex), e no iPhone só com build novo.
- **`/proposta` e `/possibilidades` também devolvem `behavior`** e não ganharam
  `lacunas` — fora do escopo do plano, e a tela lê a leitura da `/leitura`.
  Se algum dia essas seções exibirem a tabela de comportamento, o helper já
  está pronto e é puro.

## Self-Check: PASSED

- `server/app/options_mcp_api.py` — FOUND (`_lacunas_da_leitura`, `MOTIVO_*`,
  `"lacunas"` na rota)
- `web/src/opcoes/OpcoesScreen.jsx` — FOUND (`LacunasDaLeitura`,
  `ROTULO_LEITURA`, `faixa`)
- `web/src/copy.js` — FOUND (`opcoesLacuna` nos dois modos)
- `server/tests/test_options_mcp_api.py` — FOUND (bloco 24-11, 10 testes)
- `web/tests/test_opcoes_analisar_ui.mjs` — FOUND (bloco 15)
- Commits `4801487`, `56f61b7`, `0dac014` — FOUND em `git log`
</content>
