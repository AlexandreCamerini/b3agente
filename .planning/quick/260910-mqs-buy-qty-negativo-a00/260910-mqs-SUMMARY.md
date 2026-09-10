---
quick_id: 260910-mqs
phase: quick-260910-mqs
plan: 01
status: complete
commit: 45fdbe3
branch: worktree-agent-abcd37bd389f2bdbc
expected_base: 4b4e61feacdf959084c71598212876a57ec40843
files_modified: [server/app/main.py, server/tests/test_fase5_rejeicao_rotas.py]
tests_added: 5
suite: verde (2244 passed, 4 skipped no backend; 126/126 web; exit 0)
deploy: nao (sem bump, sem Railway, sem publicacao, front intocado)
---

# Quick 260910-mqs: `/api/buy` rejeita `qty` inválido (achado A-00/A-00b)

`POST /api/buy` passou a rejeitar `qty` negativo, zero e não numérico com 400
"Quantidade inválida." e registro no histórico, espelhando a guarda que
`/api/sell` já tinha desde a regressão F10-20260819.

## NÃO tem relação com a aba de Opções

Registro explícito para quem revisar o PR #39: esta correção é de um **bug
pré-existente da rota principal de compra de ação** (`/api/buy`), achado pela
auditoria de 2026-09-10. Ela entrou nesta branch por conveniência, não porque
tenha qualquer ligação com a aba de Opções, com `/api/options/buy` ou com a
investigação da falha da aba em produção. Nenhum arquivo de opções foi tocado.

## Achado, verificado antes de corrigir

A auditoria estava **certa e completa**. Reprodução contra o endpoint real
(TestClient, cotação fake de R$ 30,00, em pregão), com o código de antes:

```
{"t": "PETR4", "qty": -500} -> HTTP 200 | body={"catalog":[...]}
    positions=[{'t': 'PETR4', 'qty': 100, 'avg': 30.0, ...}] cash=7000.0 history=[('executada', 'COMPRA', 100)]
{"t": "PETR4", "qty": 0}    -> HTTP 200 | ... positions=[{'t': 'PETR4', 'qty': 100, ...}] cash=7000.0
{"t": "PETR4", "qty": "abc"} -> HTTP 500 | body={"detail":"ValueError: invalid literal for int() with base 10: 'abc'"}
{"t": "PETR4"}              -> HTTP 200 | positions=[{'t': 'PETR4', 'qty': 100, ...}] cash=7000.0
```

Confirmado o mecanismo exato: a coerção para 100 é o `max(100, round(qty/100)*100)`
do ramo em pregão — `round(-500/100)*100 = -500`, e o `max` o eleva ao lote
mínimo. Não é uma constante 100 solta. O mesmo `max(100, ...)` existe em
`pending_orders.criar_compra:104`, então o ramo de **ordem pendente** (fora de
pregão) engolia o negativo do mesmo jeito — a auditoria não menciona esse
segundo ramo, e a guarda foi posicionada para cobrir os dois.

Depois da correção:

```
{"t": "PETR4", "qty": -500}  -> HTTP 400 | {"detail":"Quantidade inválida."}  positions=[] cash=10000.0 history=[('rejeitada','COMPRA',-500)]
{"t": "PETR4", "qty": 0}     -> HTTP 400 | {"detail":"Quantidade inválida."}  positions=[] cash=10000.0 history=[('rejeitada','COMPRA',0)]
{"t": "PETR4", "qty": "abc"} -> HTTP 400 | {"detail":"Quantidade inválida."}  positions=[] cash=10000.0 history=[('rejeitada','COMPRA','abc')]
{"t": "PETR4"}               -> HTTP 200 | positions=[{'t':'PETR4','qty':100,...}] cash=7000.0 history=[('executada','COMPRA',100)]
```

## Decisão: onde a guarda foi posta, e por quê

Ordem final em `/api/buy`: parse de `qty` → normalização do ticker → rejeição
de ticker curto → **rejeição de `qty`** → `get_quote`.

1. **Depois do ticker, não antes.** A rejeição precisa gravar no histórico o
   ticker já normalizado (T-04-03) e o ticker inválido continua tendo
   precedência, como sempre teve.
2. **Antes de `get_quote`.** Um pedido que já se sabe inválido não pode queimar
   requisição do orçamento da brapi (ADR-008, 15k/mês para o app inteiro). É a
   diferença deliberada em relação à venda: lá a cotação já tinha sido buscada
   por outro motivo (a checagem de 502), então a venda grava `price` na
   rejeição; aqui o registro sai com `price=None`, igual à rejeição de ticker
   logo acima e nunca `0.0` (CLAUDE.md item 4).
3. **Antes da bifurcação de pregão.** Cobre de uma vez o caminho imediato e o
   de ordem pendente, que tinham a mesma normalização de lote e a mesma falha.
4. **Parse tolerante, rejeição explícita.** `qty` não conversível grava o valor
   **cru** no histórico — mesmo comportamento que a venda já tem
   (`registrar_rejeicao(..., _qty, ...)`), então nenhuma variante nova aparece
   no histórico.
5. **Mensagem ao usuário:** exatamente `"Quantidade inválida."`, a mesma string
   da venda — a UI não ganha texto novo para tratar.

**Contrato preservado:** `qty` AUSENTE do corpo continua significando "lote
mínimo de 100". A correção distingue `None` (ausente) de zero/negativo
explícito, exatamente como a venda faz; ela rejeita valor inválido, não muda o
contrato da rota. Isso ficou travado por um teste guardião próprio
(caminho 12 do inventário).

## Prova RED/GREEN

`server/app/main.py` verificado byte a byte idêntico ao `HEAD` no momento do
RED (`git show HEAD:server/app/main.py` para `/tmp/claude-501/main_pre.py` +
`diff -q` — sem `git stash`, cuja pilha é compartilhada entre worktrees).

**RED** (testes novos contra o código de ANTES):

```
$ python -m pytest tests/test_fase5_rejeicao_rotas.py -k "auditoria_a00 or qty_invalida_anonimo or qty_ausente" -p no:randomly -q
=========================== short test summary info ============================
FAILED tests/test_fase5_rejeicao_rotas.py::test_buy_qty_negativo_400_auditoria_a00
FAILED tests/test_fase5_rejeicao_rotas.py::test_buy_qty_zero_400_auditoria_a00
FAILED tests/test_fase5_rejeicao_rotas.py::test_buy_qty_nao_inteiro_400_auditoria_a00b
FAILED tests/test_fase5_rejeicao_rotas.py::test_buy_qty_invalida_anonimo_nao_grava_no_balde_compartilhado
4 failed, 1 passed, 5 deselected, 11 warnings in 0.90s
```

O `1 passed` do RED é o guardião de contrato
(`test_buy_qty_ausente_continua_comprando_lote_minimo_contrato_preservado`):
ele tem de passar antes **e** depois — se falhasse no RED, a correção estaria
mudando o contrato de `qty` ausente.

**GREEN** (mesmos testes, com a correção):

```
$ python -m pytest tests/test_fase5_rejeicao_rotas.py -k "auditoria_a00 or qty_invalida_anonimo or qty_ausente" -p no:randomly -q
5 passed, 5 deselected, 11 warnings in 0.58s
```

## Suíte canônica

```
$ bash scripts/executar.sh --testes
== Suítes do backend ==
2244 passed, 4 skipped, 430 warnings in 46.13s
== Suítes web ==
126 arquivos [OK], 0 [X]
EXIT=0
```

Nota de ambiente: a primeira execução falhou na metade web por restrição de
sandbox (`mktemp -d` fora dos caminhos graváveis → `Operation not permitted` ao
escrever o log de cada teste, o que marcava todos como `[X]`). Repetida com o
sandbox desligado, passou limpa. `web/node_modules` nasceu ausente no worktree
e foi instalado pelo próprio `executar.sh`.

Front não editado — sem `vite build`, por decisão de escopo.

## Achado colateral, NÃO corrigido (fora de escopo)

`server/app/main.py`, `/api/options/buy`: `qty = int(body.get("qty") or 0)` tem
o **mesmo** vazamento de `ValueError` de A-00b (`qty:"abc"` → 500 com texto cru
da exceção). O `qty <= 0` de lá já barra negativo e zero, então A-00 não se
aplica. Deixado intocado de propósito: corrigi-lo aqui contaminaria um commit
que precisa ficar comprovadamente sem relação com a aba de Opções às vésperas
da revisão do PR #39. Vale um quick próprio.

## Self-Check: PASSED

- `server/app/main.py` — FOUND (modificado, commitado)
- `server/tests/test_fase5_rejeicao_rotas.py` — FOUND (modificado, commitado)
- commit `45fdbe3` — FOUND em `git log`
- `git diff --diff-filter=D HEAD~1 HEAD` — vazio (nenhuma deleção)
- `git status --short` — limpo (nenhum untracked)
