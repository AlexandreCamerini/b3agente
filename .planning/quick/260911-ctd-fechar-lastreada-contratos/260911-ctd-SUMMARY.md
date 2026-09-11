---
quick_id: 260911-ctd
phase: quick-260911-ctd
plan: 01
status: complete
commit: 6e7dc35
files_modified: [server/app/main.py, server/tests/test_fase5_rejeicao_rotas.py]
tests_added: 11
suite: verde (2321 passed, 4 skipped + 126 testes web)
deploy: NAO feito (deploy so-backend, fora de escopo)
---

# Quick 260911-ctd: fechar lastreada distingue contratos ausente de invalido

Quinta e ultima ocorrencia da familia do `qty` falsy (origem F10-20260819 em
`/api/sell`). `POST /api/options/lastreada/fechar` agora rejeita `contratos`
zero/negativo/nao numerico com 400 `"Quantidade invalida."` nos DOIS ramos, e
`contratos` ausente continua fechando a operacao inteira.

## Commit

`6e7dc35` — `fix(260911-ctd): fechar lastreada distingue contratos ausente de invalido`
(2 arquivos, +283/−2; nenhum arquivo de `web/` tocado).

## O defeito

```python
contratos_n = int(contratos_body) if isinstance(contratos_body, (int, float)) and contratos_body > 0 else None
```

`0`, `-3` e `"abc"` caiam todos em `None` — que nesta rota significa **fechar a
operacao lastreada inteira**. Agravante frente as quatro anteriores: o
`isinstance` engolia o nao numerico em silencio (nas outras `"abc"` ao menos
explodia num 500 visivel), e a **tela manda o campo** (`web/src/App.jsx:3529`,
`A.fecharLastreada({ contractSymbol, contratos: p.contratos })`) — as quatro
anteriores so eram alcancaveis por chamada direta a API.

Segundo falsy, um andar abaixo, no ramo `comprada`:
`qty = contratos_n * 100 if contratos_n else None` → virou `is not None`.

## Prova RED — codigo de ANTES, endpoint real

Script descartavel fora do repo (`/tmp/claude-501/repro_ctd_fechar_lastreada.py`,
nao versionado; nenhum `git stash` foi usado em momento algum), rodando contra
`server/app/main.py` sem a correcao:

```
=== ramo 'vendida' (CALL coberta -> store.fechar_call_coberta) ===
[vendida ] contratos=  'abc' -> HTTP 200 | qty 300 -> 0 | FECHOU TUDO EM SILENCIO
[vendida ] contratos=      0 -> HTTP 200 | qty 300 -> 0 | FECHOU TUDO EM SILENCIO
[vendida ] contratos=     -3 -> HTTP 200 | qty 300 -> 0 | FECHOU TUDO EM SILENCIO

=== ramo 'comprada' (PUT de protecao -> store.sell_option) ===
[comprada] contratos=  'abc' -> HTTP 200 | qty 300 -> 0 | FECHOU TUDO EM SILENCIO
[comprada] contratos=      0 -> HTTP 200 | qty 300 -> 0 | FECHOU TUDO EM SILENCIO
[comprada] contratos=     -3 -> HTTP 200 | qty 300 -> 0 | FECHOU TUDO EM SILENCIO
```

Sem 500 em caso nenhum: 200 limpo, posicao de 300 contratos zerada, lastro
devolvido e caixa debitado pela recompra total. Exatamente o que o achado
descrevia.

RED tambem em pytest, com os testes novos contra o codigo de antes:

```
FAILED ...::test_lastreada_fechar_contratos_invalido_400_ramo_vendida[abc]
FAILED ...::test_lastreada_fechar_contratos_invalido_400_ramo_vendida[0]
FAILED ...::test_lastreada_fechar_contratos_invalido_400_ramo_vendida[-3]
FAILED ...::test_lastreada_fechar_contratos_invalido_400_ramo_comprada[abc]
FAILED ...::test_lastreada_fechar_contratos_invalido_400_ramo_comprada[0]
FAILED ...::test_lastreada_fechar_contratos_invalido_400_ramo_comprada[-3]
FAILED ...::test_lastreada_fechar_contratos_invalido_anonimo_nao_grava_no_balde_compartilhado
7 failed, 4 passed, 19 deselected
```

Os 4 que ja passavam no RED sao de proposito os guardioes de contrato
(`contratos` ausente, nos dois ramos) e as contraprovas de fechamento parcial
valido: eles tem de passar nos DOIS lados da prova.

## Prova GREEN — mesmo script, codigo de DEPOIS

```
=== ramo 'vendida' (CALL coberta -> store.fechar_call_coberta) ===
[vendida ] contratos=  'abc' -> HTTP 400 | qty 300 -> 300 | REJEITADO  detail='Quantidade inválida.'
[vendida ] contratos=      0 -> HTTP 400 | qty 300 -> 300 | REJEITADO  detail='Quantidade inválida.'
[vendida ] contratos=     -3 -> HTTP 400 | qty 300 -> 300 | REJEITADO  detail='Quantidade inválida.'

=== ramo 'comprada' (PUT de protecao -> store.sell_option) ===
[comprada] contratos=  'abc' -> HTTP 400 | qty 300 -> 300 | REJEITADO  detail='Quantidade inválida.'
[comprada] contratos=      0 -> HTTP 400 | qty 300 -> 300 | REJEITADO  detail='Quantidade inválida.'
[comprada] contratos=     -3 -> HTTP 400 | qty 300 -> 300 | REJEITADO  detail='Quantidade inválida.'
```

Posicao intacta nos seis (300 → 300), caixa intocado, nenhum 500. Arquivo de
teste inteiro: `30 passed`.

## Contrato preservado

`contratos` AUSENTE continua fechando a operacao INTEIRA, nos dois ramos —
verificado no mesmo script depois da correcao:

```
=== contrato a PRESERVAR: `contratos` AUSENTE = fechar tudo ===
[vendida ] contratos=   None -> HTTP 200 | qty 300 -> 0
[comprada] contratos=   None -> HTTP 200 | qty 300 -> 0
```

Guardiao proprio no arquivo de teste (caminho 21,
`test_lastreada_fechar_contratos_ausente_continua_fechando_tudo_contrato_preservado`,
parametrizado call/put): 200, `priceUsed`, posicao zerada, lastro destravado,
caixa de volta ao pre-abertura. Passa antes e depois da correcao, de proposito.
Contraprova adicional (caminho 22): `contratos: 1` sobre 3 contratos continua
sendo fechamento PARCIAL nos dois ramos.

## Suite canonica

`bash scripts/executar.sh --testes` (primeira tentativa morreu por sandbox —
`mktemp -d` fora do path gravavel, "Operation not permitted"; repetida sem
sandbox):

```
EXIT=0
2321 passed, 4 skipped, 484 warnings in 54.14s
126 testes web [OK]
```

Front nao foi editado, entao nao ha `vite build` — `git status` confirma so os
dois arquivos de `server/` no commit, nenhuma delecao.

## Sexta ocorrencia?

Varredura do padrao em `server/app/*.py` depois da correcao: as unicas
ocorrencias restantes de `int(...) if ... else None` / `or 0` ligadas a
quantidade de ordem sao **comentarios** de decisao das quatro correcoes
anteriores. `int(body.get("qty") or 0)` em `/api/options/buy` (linha 2348) ja
esta coberto pelo `try/except` + `qty <= 0` da quick 260911-15a. Os `or 0` das
linhas 3074+ sao leitura de metrica, nao quantidade de ordem. **Nada novo a
registrar em `deferred-items.md`.**

(Nota: `.planning/quick/260911-cf1-venda-opcao-qty-zero/deferred-items.md`
apontado no briefing nao existe no repo — aquela quick so deixou o PLAN. O
achado chegou aqui pelo proprio `260911-ctd-PLAN.md`, que o descreve na
integra.)

## Familia fechada

Com esta entrega as **cinco** rotas da familia — `/api/buy`, `/api/sell`,
`/api/options/buy`, `/api/options/sell` e `/api/options/lastreada/fechar` —
tem a mesma guarda (`is not None` + `try/int` + `<= 0`) e a mesma mensagem
`"Quantidade invalida."`. Nenhuma entrada invalida fecha ou executa operacao;
ausente continua sendo o default de cada rota.

## Nao feito (fora de escopo, por desenho)

Deploy, bump, `railway`, publicacao. A correcao e so-backend e vai ao ar no
proximo deploy de servidor (com bump manual de `SERVER_BUILD_ID`, conforme o
guardrail do repo).
