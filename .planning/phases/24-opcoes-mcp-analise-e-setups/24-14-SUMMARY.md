---
phase: 24-opcoes-mcp-analise-e-setups
plan: 14
subsystem: api
tags: [fastapi, react, opcoes, mcp, setups, backtest, transparencia, dsl]

requires:
  - phase: 24-opcoes-mcp-analise-e-setups (plano 04)
    provides: "a rota `/setups/compilar` com o dry-run e o `backtest` verbatim, o card do ensaio em `CriarSetup.jsx` e o guardião `test_opcoes_criar_setup_ui.mjs`"
  - phase: 24-opcoes-mcp-analise-e-setups (plano 11)
    provides: "`_lacunas_da_leitura` — o padrão de explicar a ausência a partir da PRÓPRIA resposta, sem preencher número e sem chamada nova"
provides:
  - "`_ensaio_inconclusivo` — helper puro que diz quais condições nunca fecharam a janela no histórico do ensaio"
  - "`_janela_declarada` — a janela de um lado da comparação, lida pela FORMA do dado (`window`), sem copiar a lista de indicadores do serviço"
  - "`MOTIVO_JANELA_NUNCA_FECHOU`/`MOTIVO_JANELA_CURTA_PARA_SEQUENCIA`/`AVISO_ENSAIO_INDISPARAVEL` em `AVISOS`"
  - "campo `ensaio` no 200 de `/setups/compilar`, ao lado do `backtest` verbatim — nenhuma chamada nova"
  - "`EnsaioInconclusivo` no card do ensaio, ACIMA dos números, e `opcoesEnsaioIndisparavel`/`opcoesEnsaioRessalva`/`opcoesEnsaioCondicao` nas duas vozes"
  - "guardiões nos dois lados: 33 testes no backend e 26 asserções novas no front"
affects: [24-05 (publicação — este texto só chega ao usuário depois do bump + publicar-web.sh), qualquer plano futuro que mexa no ensaio de setup ou acrescente indicador com janela]

tech-stack:
  added: []
  patterns:
    - "demonstração de impossibilidade em vez de opinião: o aviso só afirma o que a aritmética de janela prova, e cala onde a prova não alcança (OR, sequência curta)"
    - "detecção pela FORMA do dado (`window` declarado) em vez de allowlist de vocabulário — ENG-06 aplicado a um helper de leitura"
    - "aviso ACIMA do número que ele qualifica: ressalva depois do número chega tarde, porque a conclusão já foi formada"
    - "informar sem bloquear: a tela impede a conclusão errada, não a ação da pessoa"

key-files:
  created: []
  modified:
    - server/app/options_mcp_api.py
    - server/tests/test_opcoes_dsl.py
    - web/src/opcoes/CriarSetup.jsx
    - web/src/copy.js
    - web/tests/test_opcoes_criar_setup_ui.mjs

key-decisions:
  - "O veredito `indisparavel` fica reservado ao caso DEMONSTRÁVEL: condição sem ponto nenhum dentro de um `AND`. Com `OR` a condição morta não impede as outras, e afirmar indisparabilidade que não se prova trocaria uma leitura errada por outra"
  - "`pontos = n - w + 1` é o TETO de propósito: as médias produzem essa contagem e os indicadores que olham o pregão anterior produzem um ponto a menos. Errar para o lado generoso só pode deixar de avisar — nunca dar como morta uma condição que teve valor"
  - "Nenhuma lista de indicadores com janela entrou no Boris (desvio do PLAN, que previa `JANELA_POR_INDICADOR`): quem declara janela é a condição, e o serviço só aceita `window` em indicador que a use. A allowlist seria a segunda cópia do contrato, a que ninguém atualiza quando o serviço ganha o próximo indicador (ENG-06)"
  - "O botão de gravar continua existindo nos dois casos: não é a tela que decide o que a pessoa faz com um setup que ela escreveu. Bloquear trocaria um problema de informação por um de autonomia"
  - "O texto do `MOTIVO_JANELA_CURTA_PARA_SEQUENCIA` foi reescrito em relação ao PLAN ('pregões demais no fim do histórico' se lê como 'pregões em excesso', o oposto do que a condição descreve)"
  - "O `ensaio` é calculado sobre `setup_as_interpreted` — o objeto que a tela mostra e que `/setups/confirmar` recebe de volta. Calculá-lo sobre o que a IA respondeu descreveria um setup que ninguém vai gravar"

patterns-established:
  - "Guardião de extrapolação: o texto de um aviso derivado de número passa por varredura que proíbe previsão ('dispararia com mais histórico'), juízo ('setup ruim') e ação que a tela não oferece ('aumente o período'), com sanidade da regex"
  - "Varredura de vocabulário como CÓDIGO (nome de indicador entre aspas) e não como prosa: a regra ENG-06 pega a allowlist e deixa passar a frase que explica o achado"

requirements-completed: ["achado ao vivo 2026-09-11 — ensaio de 0 disparos que não testou nada"]

duration: 40min
completed: 2026-09-12
---

# Fase 24 Plano 14: o ensaio que não testou nada passou a dizer isso — Summary

**Um setup cuja condição nunca teve valor no histórico devolvia `disparos: 0`
com `pregoes_avaliaveis: 31` — números certos que se leem como "testei e não
disparou". O card do ensaio passou a dizer, ACIMA desses números e a partir
deles mesmos, quais condições nunca puderam ser verificadas e por que aquele
zero é consequência da conta, não de raridade.**

## Performance

- **Duration:** ~40 min
- **Started:** 2026-09-11T23:37 (-03, aprox.)
- **Completed:** 2026-09-12T00:17 (-03), somando a suíte canônica
- **Tasks:** 3
- **Files modified:** 5

## O que estava errado, em uma passagem

Achado ao vivo em 2026-09-11, reproduzido contra o motor real do serviço
(`~/dev/MCP/servers/mydata/setups.py`, medição já no PLAN): um setup com
`sma 200` sobre 48 pregões devolve

```
condição "close > sma200"  ->  0 valores não-None em 48   (NUNCA avaliável)
condição "rsi14 < 30"      -> 34 valores não-None em 48
diario: True=0  False=31  None=17
backtest.pregoes_avaliaveis: 31    backtest.disparos: 0
```

Os números estão **certos**. O motor combina com `all` e curto-circuita: `AND`
com um `False` conhecido é `False`, e nos 31 dias em que o RSI estava acima de
30 o dia é comprovadamente falso — daí os 31 avaliáveis. O serviço não tem
defeito.

O que engana é a leitura. "0 disparos em 31 pregões avaliáveis" comunica
*testei e não disparou*, quando a verdade é *nunca pôde disparar*: a condição
da média não teve valor em pregão nenhum, e por construção o dia nunca pôde
ser verdadeiro.

É pior que o caso do 24-11. Lá o campo vinha vazio e a pessoa via que faltava
algo; aqui vem um número plausível, e número plausível não levanta suspeita.
O fim da linha é alguém **gravar** um setup acreditando que ele foi validado
contra o histórico.

## O que foi feito

### A conta, que é de janela e não de análise técnica

`_ensaio_inconclusivo(setup, backtest)` compara a janela que cada condição
DECLARA com o tamanho do período que o backtest informou. Uma janela de `w`
sobre `n` pregões produz no máximo `n - w + 1` pontos:

- `pontos <= 0` → a condição não teve valor em dia nenhum
  (`MOTIVO_JANELA_NUNCA_FECHOU`);
- `0 < pontos < consecutive_days` → a sequência exigida não teve como se
  formar (`MOTIVO_JANELA_CURTA_PARA_SEQUENCIA`).

Os dois lados da comparação contam, e a maior janela manda — no caso real a
janela que mata o ensaio mora na `reference` (`close > média de 200`), não no
lado esquerdo. `consecutive_days` e `logic` usam os defaults do próprio motor
(`1` e `"AND"`), senão o caso mais comum — setup sem `logic` explícita —
perderia justamente o aviso.

Nenhum número é recalculado e nenhuma chamada é feita: `setup` e `backtest`
são o que o dry-run já devolveu, na mesma resposta.

### O que se afirma e o que se cala

`indisparavel` só é verdadeiro quando alguma condição tem `pontos <= 0` **e** a
lógica é `AND`. Aí a impossibilidade é aritmética: se uma condição do `AND`
nunca é verdadeira, o dia nunca é verdadeiro, logo `disparos` é 0 por
construção.

Nos outros dois casos a condição é listada como **ressalva**, sem veredito:

- com `OR`, uma condição morta não impede as outras de disparar;
- com a janela curta para a sequência, a condição TEVE valor em alguns
  pregões — o ensaio avaliou alguma coisa, o que não coube foi a sequência.

`n - w + 1` é o teto, e é assim de propósito: as médias produzem essa contagem
(`_movel`), e `highest`/`lowest`/`rel_volume`/`change_pct` produzem um ponto a
menos (olham o pregão anterior). Errar para o lado generoso só pode deixar de
avisar — nunca dar como morta uma condição que teve valor.

### A faixa, acima dos números

`EnsaioInconclusivo` entra entre a lista de condições e o bloco do backtest.
Com `indisparavel`, tom forte e `opcoesEnsaioIndisparavel`; com condição
listada sem veredito, tom discreto e `opcoesEnsaioRessalva`. Cada condição sai
com o indicador, a janela declarada e o **motivo verbatim do backend** — que
entra como argumento de `cp.opcoesEnsaioCondicao` e não é reescrito no front
(padrão do 24-11: a segunda cópia da frase é a que envelhece sem ninguém
notar).

Sem `ensaio` no payload — servidor anterior a este plano — nada é renderizado.

O botão de gravar continua existindo nos dois casos.

## O que a tela passou a dizer

```
[estudo]   Este ensaio não testou o setup. Uma das condições exige mais
           pregões do que o histórico usado aqui tem, então ela não teve valor
           em nenhum dia — e o setup só dispara quando todas as condições
           valem no mesmo pregão. Por isso o número de disparos abaixo é
           consequência da conta, não sinal de que a condição é rara. Nada foi
           estimado no lugar.
             · sma (janela de 200 pregões): esta condição precisa de mais
               pregões do que o histórico do ensaio tem, então ela não teve
               valor em nenhum dia — não é que não tenha ocorrido, é que não
               deu para verificar.

[operador] Ensaio sem valor de teste. Uma das condições exige mais pregões do
           que o histórico usado tem e ficou sem valor em todos os dias — e o
           setup só dispara com todas as condições valendo no mesmo pregão. O
           zero de disparos abaixo sai da conta, não de raridade. Nada
           estimado no lugar.
```

E o helper, rodado contra o caso medido:

```json
{"indisparavel": true, "pregoes": 48,
 "condicoes": [{"indicador": "sma", "janela": 200, "pontos": -151,
                "motivo": "esta condição precisa de mais pregões…"}]}
```

## Prova RED → GREEN

Os testes foram escritos **antes** da correção, nos arquivos canônicos, e
rodados contra o código de antes.

| Correção | Teste escrito primeiro | RED observado (código de antes) | GREEN |
|---|---|---|---|
| helper + motivos + rota | bloco 16 de `test_opcoes_dsl.py` (33 testes) | `33 failed, 35 passed` — `AttributeError: module 'app.options_mcp_api' has no attribute '_ensaio_inconclusivo'` (×29), `… 'MOTIVO_JANELA_NUNCA_FECHOU'` (×2), `KeyError: 'ensaio'` (×2) | `68 passed` no arquivo, `229 passed` com os irmãos |
| a faixa no card do ensaio | blocos 13 e 14 de `test_opcoes_criar_setup_ui.mjs` (26 asserções) | `11 FALHOU` + `TypeError: COPY[m].opcoesEnsaioCondicao is not a function` (o arquivo nem terminava de rodar) | `todos os testes passaram` |

Trecho do RED do backend:

```
E       AttributeError: module 'app.options_mcp_api' has no attribute '_ensaio_inconclusivo'
E       AttributeError: module 'app.options_mcp_api' has no attribute 'MOTIVO_JANELA_NUNCA_FECHOU'
E       KeyError: 'ensaio'
33 failed, 35 passed
```

E do front:

```
FALHOU existe componente próprio para o ensaio inconclusivo
FALHOU a faixa aparece ANTES dos números do backtest
FALHOU sem condição listada, a faixa não renderiza nada
FALHOU o motivo do backend entra como argumento de `cp.opcoesEnsaioCondicao`
FALHOU COPY tem opcoesEnsaioIndisparavel nos dois modos
…
TypeError: COPY[m].opcoesEnsaioCondicao is not a function
```

As asserções que já passavam no RED são as que **não descrevem a correção**:
as de sanidade (precisam passar nos dois estados — é o que sanidade significa)
e as regras que já valiam e este plano não podia quebrar (sem HTML cru, sem
vocabulário da DSL no front, paridade de chaves `opcoes*`). Uma passava por
vacuidade — "o texto da faixa não extrapola" sobre um conjunto de chaves
inexistentes —, e foi por isso que ela veio acompanhada da sanidade que prova
que a regex pega "com mais histórico esta condição dispararia".

## Task Commits

1. **Task 1 — `_ensaio_inconclusivo` no backend** — `f754d98` (feat)
2. **Task 2 — a faixa no card do ensaio** — `838439f` (feat)
3. **Task 3 — guardiões nos dois lados** — `4523101` (test)

## Files Created/Modified

- `server/app/options_mcp_api.py` — os três textos novos (acrescentados a
  `AVISOS`), `_janela_declarada`, `_ensaio_inconclusivo` e o campo `ensaio` no
  200 de `/setups/compilar`, lido do `setup_as_interpreted`
- `server/tests/test_opcoes_dsl.py` — bloco 16: 33 testes (31 do helper puro +
  2 de rota), com o setup e o backtest MEDIDOS como fixture; `import re`; duas
  linhas no docstring do arquivo
- `web/src/opcoes/CriarSetup.jsx` — `EnsaioInconclusivo`, montado entre a
  lista de condições e o bloco do backtest
- `web/src/copy.js` — `opcoesEnsaioIndisparavel`, `opcoesEnsaioRessalva` e
  `opcoesEnsaioCondicao` nos DOIS modos
- `web/tests/test_opcoes_criar_setup_ui.mjs` — blocos 13 e 14 (26 asserções, 3
  delas de sanidade) e três linhas no cabeçalho

## Deviations from Plan

### 1. [Rule 2 — vocabulário duplicado] `JANELA_POR_INDICADOR` não foi criado

- **Found during:** Task 1
- **Issue:** o PLAN previa uma tupla com os oito indicadores que têm janela
  (`sma`, `ema`, `rsi`, `atr`, `highest`, `lowest`, `rel_volume`,
  `change_pct`). Isso é a segunda cópia do contrato do serviço dentro do
  Boris — exatamente o que o ENG-06 proíbe e o que o guardião
  `test_system_do_compilador_e_puro_e_nao_carrega_indicador_hardcodado`
  existe para impedir no prompt. Quando o serviço ganhar o próximo indicador
  com janela, a lista envelhece em silêncio e o aviso deixa de sair.
- **Fix:** a detecção saiu da FORMA do dado: quem declara janela é a condição
  que traz `window` (inteiro ≥ 1, `bool` recusado), e o serviço só aceita
  `window` em indicador que a use ("não usa janela — remova"). Um indicador
  que ainda não existe é detectado automaticamente — há teste para isso.
- **Files modified:** `server/app/options_mcp_api.py`,
  `server/tests/test_opcoes_dsl.py`
- **Commit:** `f754d98`, `4523101`

### 2. [Rule 1 — texto ambíguo] `MOTIVO_JANELA_CURTA_PARA_SEQUENCIA` reescrito

- **Found during:** Task 1
- **Issue:** o texto do PLAN ("só teve valor em pregões demais no fim do
  histórico para formar a sequência") se lê como "pregões **em excesso**" —
  o oposto exato do que a condição descreve. Num texto cujo propósito inteiro
  é impedir uma leitura errada, a ambiguidade é o defeito.
- **Fix:** "esta condição só passou a ter valor nos últimos pregões do
  histórico, em quantidade menor que a sequência de dias seguidos que o setup
  exige — a sequência não teve como se formar". Os outros dois textos ficaram
  byte a byte como o PLAN os escreveu.
- **Files modified:** `server/app/options_mcp_api.py`
- **Commit:** `f754d98`

### 3. [Rule 3 — artefato local do próprio build] bundle iOS ressincronizado

- **Found during:** Task 3 (suíte canônica)
- **Issue:** `test_ios_assets.mjs` falhou em "MESMO build nos dois lados ⇒
  TODOS os chunks do dist no bundle do iOS". Causa: o `npx vite build` exigido
  pela validação do `CLAUDE.md` regerou `web/dist` com hashes novos enquanto o
  `BUILD_ID` continuava o mesmo (bump é proibido nesta execução) — o guardião
  lê os dois carimbos, os vê iguais e passa a exigir paridade de chunks.
- **Fix:** `npx cap copy ios` (copia os assets web, **não** regenera o projeto
  Xcode nem mexe em plugin). Os dois lados são gitignored: nenhum arquivo
  versionado foi tocado e nada entrou em commit.
- **Files modified:** — (`web/dist` e `web/ios/App/App/public`, ambos
  gitignored)
- **Commit:** — (artefato local, fora do git)

### 4. [processo] testes escritos nos arquivos canônicos, commitados na Task 3

- **Found during:** Task 1
- **Issue:** a exigência de provar RED antes de cada correção convive mal com
  a divisão do PLAN, que põe os dois arquivos de teste na Task 3.
- **Fix:** os testes foram escritos direto nos guardiões canônicos e rodados
  contra o código de antes (RED registrado acima); os commits das Tasks 1 e 2
  levam só o fonte, e a Task 3 leva os dois arquivos de teste. Mesmo desenho
  do 24-11, sem os arquivos temporários.

## Verificação

```
bash scripts/executar.sh --testes    # exit 0
2511 passed, 5 skipped, 659 warnings in 63.34s
129 arquivos web/tests/*.mjs [OK], 0 [X]
```

Baseline a não regredir: `2478 passed, 5 skipped` + 129 `.mjs`. O delta de
`+33` é exatamente o bloco 16 deste plano; o front ganhou 26 asserções dentro
de um arquivo que já contava (103 → 129).

```
cd web && npx vite build    # ✓ built in 1.11s
```

Os guardiões da Task 1 rodados isolados:
`tests/test_opcoes_dsl.py tests/test_guardrail_imperativo.py
tests/test_mcp_guardioes.py tests/test_options_mcp_api.py` → `229 passed`.

## Limitações conhecidas

- **Nada disto está no ar.** O backend só vale depois de um deploy e o front
  só depois de `bump.sh` + `publicar-web.sh` — os dois fora do escopo desta
  execução (produção segue em `F10-20260911-07`). Nenhum push, nenhum PR.
- **Sem verificação ao vivo.** A faixa não foi vista numa tela real; o que
  existe é o build verde, os guardiões de fonte e o helper exercitado contra
  os números medidos. O card com um ensaio indisparável de verdade só aparece
  quando alguém compilar um setup de janela longa depois da publicação.
- **O aviso é de JANELA, não de qualidade de dado.** Uma condição pode ficar
  sem valor por buraco na série (candle faltando) sem que a janela seja o
  motivo — esse caso não é detectado, e de propósito: o `backtest` não traz
  como os `None` se distribuem, e afirmar a causa errada seria a fabricação
  que o plano existe para impedir. `pregoes_sem_indicador` continua ao lado,
  verbatim.
- **`pregoes` é o único insumo de tamanho.** Sem ele (ou com valor não
  inteiro, `bool`, zero ou negativo) o helper cala e a tela não afirma nada.

## Self-Check: PASSED

- `server/app/options_mcp_api.py` — FOUND
- `server/tests/test_opcoes_dsl.py` — FOUND
- `web/src/opcoes/CriarSetup.jsx` — FOUND
- `web/src/copy.js` — FOUND
- `web/tests/test_opcoes_criar_setup_ui.mjs` — FOUND
- `.planning/phases/24-opcoes-mcp-analise-e-setups/24-14-SUMMARY.md` — FOUND
- Commits `f754d98`, `838439f`, `4523101` — FOUND em `git log`
