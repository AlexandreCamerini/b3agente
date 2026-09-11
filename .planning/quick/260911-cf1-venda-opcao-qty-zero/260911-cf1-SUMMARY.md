---
quick_id: 260911-cf1
phase: quick-260911-cf1
plan: 01
status: complete
commit: c7bd2b8
branch: worktree-agent-a67c9ab40b2ff54e7
expected_base: 4acb9ca2406bcf3676ee9c8d0228b34f1122924d
files_modified: [server/app/main.py, server/tests/test_fase5_rejeicao_rotas.py]
files_created: []
deploy: nao (deploy so-backend com bump manual de SERVER_BUILD_ID fica para outra sessao)
completed: 2026-09-11
---

# Quick 260911-cf1: venda de opção com `qty` falsy — Summary

`POST /api/options/sell` deixou de tratar `qty=0` como campo ausente: a
posição fica **intacta** e o pedido vira 400 `"Quantidade inválida."`, mesma
string das outras três rotas da família. Com esta entrega, as QUATRO rotas
(`/api/buy`, `/api/sell`, `/api/options/buy`, `/api/options/sell`) têm a mesma
guarda — esta era a última ocorrência aberta da armadilha do falsy de
F10-20260819.

## Commit

`c7bd2b8` — `fix(260911-cf1): venda de opcao com qty=0 vendia a posicao inteira (D-1)`
(219 inserções, 1 deleção; nenhum arquivo deletado; nenhum arquivo de `web/`
no diff, logo sem `vite build`).

## O que mudou

`server/app/main.py` (rota `/api/options/sell`), espelhando `/api/sell`:

- `qty` AUSENTE (`None`) → venda TOTAL (contrato preservado);
- `qty` ZERO ou NEGATIVO explícito → 400 `"Quantidade inválida."`;
- `qty` não numérico → mesmo 400 (antes: 500 com o texto cru do `ValueError`);
- rejeição de conta logada gravada via `store.registrar_rejeicao("VENDA",
  contractSymbol, ...)` — mesmo formato que `abrir_call_coberta`/
  `fechar_call_coberta` já usam para contrato de opção. Escopo anônimo NÃO
  grava (T-02-07: balde kv compartilhado).

`server/tests/test_fase5_rejeicao_rotas.py`: caminhos 15/16/17 na tabela do
docstring + 6 testes novos (zero, negativo, não numérico, anônimo, guardião do
contrato `qty` ausente, contraprova de venda parcial legítima).

## Prova RED/GREEN

O código de antes veio de `HEAD` via `git checkout HEAD -- server/app/main.py`
(a versão corrigida ficou salva em `$TMPDIR/main_fix_cf1.py` e foi restaurada
por `cp` logo depois). **Nenhum `git stash` foi usado.**

### RED — contra o código de antes (`qty=int(_qty) if _qty else None`)

Sonda direta contra o endpoint real (`/tmp/claude-501/prova_d1_cf1.py`):

```
ANTES     : optionPositions=[{'id': 'PETRK30', ..., 'qty': 200, 'avg': 1.5, ...}] cash=9700.0
RESPOSTA  : HTTP 200 | detail/priceUsed=1.5
DEPOIS    : optionPositions=[] cash=10000.0
HISTORICO : [{'type': 'VENDA', 't': 'PETRK30', 'kind': 'opcao', 'qty': 200, 'price': 1.5, 'pnl': 0.0, 'motivo': 'manual', 'origem': 'manual'}]
VEREDITO  : VENDA TOTAL SILENCIOSA A PARTIR DE qty=0 (defeito D-1)
```

Pytest dos testes novos contra o mesmo código de antes:

```
FAILED tests/test_fase5_rejeicao_rotas.py::test_options_sell_qty_zero_400_d1_mesma_armadilha_f10_20260819
FAILED tests/test_fase5_rejeicao_rotas.py::test_options_sell_qty_negativo_400_d1
FAILED tests/test_fase5_rejeicao_rotas.py::test_options_sell_qty_nao_inteiro_400_d1
FAILED tests/test_fase5_rejeicao_rotas.py::test_options_sell_qty_invalida_anonimo_nao_grava_no_balde_compartilhado
4 failed, 2 passed, 13 deselected, 13 warnings in 0.65s
```

### GREEN — com a correção

```
ANTES     : optionPositions=[{'id': 'PETRK30', ..., 'qty': 200, 'avg': 1.5, ...}] cash=9700.0
RESPOSTA  : HTTP 400 | detail/priceUsed='Quantidade inválida.'
DEPOIS    : optionPositions=[{'id': 'PETRK30', ..., 'qty': 200, 'avg': 1.5, ...}] cash=9700.0
HISTORICO : [{'type': 'VENDA', 't': 'PETRK30', 'qty': 0, 'price': 1.5, 'pnl': None, 'status': 'rejeitada', 'motivo': 'Quantidade inválida: 0. A venda usa lotes de 100.', 'origem': 'manual'}]
VEREDITO  : POSICAO INTACTA (correto)
```

```
6 passed, 13 deselected, 13 warnings in 0.64s
```

A asserção que decide a task não é o 400 — é `optionPositions[0]["qty"] == 200`
e `cash == 9700.0` depois da rejeição, mais `[h for h in history if
h["type"]=="VENDA" and h.get("status") != "rejeitada"] == []`: nenhuma venda
executada existe. O RED mostra a posição desaparecendo e o caixa voltando a
10000; o GREEN mostra os dois inalterados.

## Contrato de `qty` AUSENTE — intacto

Os 2 testes que **passaram nos DOIS lados da prova** são exatamente os
guardiões do contrato:

- `test_options_sell_qty_ausente_continua_vendendo_tudo_contrato_preservado` —
  `POST {"contractSymbol": "PETRK30"}` (sem `qty`) → 200, `priceUsed` 1.5,
  `optionPositions == []`, `cash == 10000.0`, histórico com
  `VENDA qty=200 kind="opcao" motivo="manual"`. É o caminho que a tela usa
  (`optionsSell` não monta `qty` no corpo).
- `test_options_sell_qty_parcial_valida_continua_funcionando` — `qty=100`
  sobre 200 continua venda PARCIAL (sobra 100, caixa 9850).

Passar antes e depois é a prova de que a guarda barra só o valor explícito
inválido e não estreitou o contrato.

## Suíte

`bash scripts/executar.sh --testes` (a canônica, as duas suítes):

```
2310 passed, 4 skipped, 462 warnings in 54.58s      # pytest backend
126 [OK] / 0 [X]                                     # web/tests/*.mjs
```

Primeira execução falhou por sandbox (`Operation not permitted` ao criar
`/test_*.mjs.log` — o `mktemp` do script resolveu para `/`), repetida com
sandbox desligado conforme a nota de ambiente. Front não foi editado, então
`vite build` não se aplica.

## Nota de família

Esta é a **QUARTA e última** rota da família a ganhar a guarda de `qty`:

| Rota | Fechada em |
|------|------------|
| `POST /api/sell` | F10-20260819 (regressão original do falsy) |
| `POST /api/buy` | quick 260910-mqs (achados A-00 / A-00b) |
| `POST /api/options/buy` | quick 260911-15a (resto do A-00b) |
| `POST /api/options/sell` | **esta quick, 260911-cf1 (D-1)** |

## Achado novo (NÃO corrigido — fora de escopo)

`POST /api/options/lastreada/fechar` (`server/app/main.py`, rota das opções
lastreadas da Fase 14) tem a MESMA classe de ambiguidade, por outra escrita:

```python
contratos_n = int(contratos_body) if isinstance(contratos_body, (int, float)) and contratos_body > 0 else None
```

`contratos: 0` (e `contratos: -3`, e `contratos: "abc"`) caem todos em `None`,
que nessa rota significa **fechar a operação inteira** — mesmo efeito de venda
total silenciosa, sem 400 nenhum. Não é o mesmo código nem a mesma rota do
D-1, e o plano é explícito em não tocar as rotas da Fase 14, então ficou de
fora desta entrega. É uma QUINTA ocorrência da família e merece quick própria
(há a diferença de que ali `contratos` ausente também é "fechar tudo", então a
correção tem o mesmo formato: distinguir ausente de explícito inválido).

Registrado também em `deferred-items.md` no diretório da quick.

## Decisões de implementação

- **String reusada, sem variante nova**: `"Quantidade inválida."` idêntica à
  de `/api/buy` e `/api/sell`. `/api/options/buy` usa
  `"Contrato de opção inválido."` porque lá o `qty` cai na validação de
  contrato — a instrução era usar a string das outras três e é essa.
- **`registrar_rejeicao` foi introduzido aqui pela primeira vez nesta rota**
  (antes ela levantava 400/502 sem gravar nada). Segui o precedente de
  `store.abrir_call_coberta`/`fechar_call_coberta`, que já registram rejeição
  de contrato de opção com `t = contractSymbol`, tipo `"VENDA"` e sem chave
  `kind`. Por isso o teste do balde anônimo foi incluído: a regra T-02-07
  precisa valer desde o primeiro dia da chamada nova.
- **`store.sell_option` não foi tocado.** Ele trata `qty=0` como venda total
  (`isinstance(qty, (int, float)) and qty > 0`), exatamente como `store.sell`
  — que também não foi tocado quando F10-20260819 foi corrigido. A guarda é de
  rota nas duas, por simetria; mexer na semântica do motor mudaria o contrato
  de `close_option_vencida` e do agente junto.

## Self-Check: PASSED

- `server/app/main.py` e `server/tests/test_fase5_rejeicao_rotas.py`
  modificados e presentes no commit `c7bd2b8` (`git log --oneline -1`).
- `git diff --diff-filter=D HEAD~1 HEAD` vazio — nenhum arquivo deletado.
- `git status --short` limpo após o commit; nenhum arquivo untracked.
- Nenhum arquivo de `web/`, `.planning/`, `STATE.md` ou `PLAN.md` no commit.
