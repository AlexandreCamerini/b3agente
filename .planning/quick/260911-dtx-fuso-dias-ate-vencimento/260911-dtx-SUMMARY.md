---
quick_id: 260911-dtx
phase: quick-260911-dtx
plan: 01
status: complete
commit: 43dc815
branch: worktree-agent-a5662a541f0ee2535
expected_base: 55693a6b5930a75e0553a8bcd8abb96100cacc83
files_modified:
  - server/app/options_api.py
  - server/app/main.py
  - server/app/mydata_client.py
  - server/app/options_provider_mock.py
  - server/tests/test_fuso_dias_ate_vencimento.py
suite: "2342 passed, 4 skipped (pytest) + 126/126 web/tests — exit 0"
---

# Quick 260911-dtx — o "hoje" do prazo até o vencimento em horário de Brasília

O achado D-2 tinha duas metades. A parte 1 (260911-dcq) era cosmética: o
carimbo exibido saía 3h à frente. Esta é a que **muda decisão**: a aritmética de
dias até o vencimento usava `date.today()` naive e, como produção roda no
Railway com o container em UTC, das 21:00 às 23:59 BRT todo prazo saía **um dia
a menos**.

## Commit

`43dc815` — `fix(fuso): dias ate o vencimento contados no dia de Brasilia (D-2, parte 2)`
(5 arquivos, +485/−12; nenhuma deleção de arquivo rastreado)

## Prova de IMPACTO NO GATE — a que decide esta task

Montada pelo **caminho real** (`TestClient` → `GET /api/options/proposta/PETR4`
→ `opcoes_lastreadas.propor` de verdade), nunca por mock da função de prazo.
O `hoje` chega ao motor puro **por argumento**, vindo do chamador.

Instante cravado nos dois lados: **01:30 UTC do dia 10/09 = 22:30 BRT do dia
09/09** — UTC e BRT em dias diferentes. Provider `mock`, vencimento pinado, sem
rede. O código de ANTES veio de `git show HEAD:<arquivo>` para uma árvore FORA
do repo (`$TMPDIR/dtx-red`); o de DEPOIS, uma cópia da árvore corrigida
(`$TMPDIR/dtx-green`). Nenhum `git stash`.

O harness da prova congela o relógio no nível do stdlib porque no código de
ANTES o `import datetime as dt` de `main.py` é **local à função** — não existe
atributo de módulo para monkeypatchar. Mesmo arquivo, mesmo instante, duas
fontes.

### Borda de `_PRAZO_MIN_DIAS` (15) — o gate RECUSAVA o que deveria aceitar

| | vencimento | dias BRT | dias UTC (naive) | motivo | proposta |
|---|---|---|---|---|---|
| **ANTES** | 2026-09-24 | 15 | 14 | `sem_vencimento_elegivel` | **NÃO** |
| **DEPOIS** | 2026-09-24 | 15 | 14 | `call_coberta` | **SIM** |

A proposta sumia da tela às 21:00 e voltava à meia-noite, sem nada ter mudado
no mercado.

### Borda de `_PRAZO_MAX_DIAS` (60) — o erro oposto, e pior

| | vencimento | dias BRT | dias UTC (naive) | motivo | proposta |
|---|---|---|---|---|---|
| **ANTES** | 2026-11-09 | 61 | 60 | `call_coberta` | **SIM** (aceito indevidamente) |
| **DEPOIS** | 2026-11-09 | 61 | 60 | `sem_vencimento_elegivel` | **NÃO** |

O teto de 60 dias vazava: um contrato de 61 dias reais entrava como candidato.

### `riskFlag` de vencimento curto (<= 21 dias)

| | vencimento | `daysToExpiration` | flags |
|---|---|---|---|
| **ANTES** | 2026-10-01 | 21 | `['Vencimento curto: theta pode corroer o prêmio rapidamente.']` |
| **DEPOIS** | 2026-10-01 | 22 | `['Risco principal: perda total do prêmio pago na simulação comprada.']` |

RED: `3 failed` de 4 na árvore pré-fix. GREEN: `4 passed` na árvore corrigida.

## Prova do prazo isolado (o degrau)

`options_api._days_to("2026-09-24")` com o mesmo instante cravado:
`== 15` (dia de Brasília), enquanto `(venc - dia_UTC).days == 14`. O segundo
assert existe para o primeiro não virar tautologia se alguém mexer no instante.

## O que foi feito em cada ponto

| # | Arquivo:linha (antes) | O que era | O que passou a ser |
|---|---|---|---|
| 1 | `options_api.py:36` | `(d - dt.date.today()).days` | `(d - hoje_brt()).days`; módulo passou a `from datetime import date, datetime, timedelta, timezone` + `BRT` local + `hoje_brt()` |
| 2 | `main.py:2515` (`proposta_fechar`) | `dt.date.today()` | `_hoje_brt()` |
| 3 | `main.py:2540` (`propor`, rota de leitura) | `dt.date.today()` | `_hoje_brt()` |
| 4 | `main.py:2741` (`propor`, rota de escrita do collar) | `dt.date.today()` | `_hoje_brt()` |
| 5 | `mydata_client.py:202` | `date.today() - timedelta(...)` | `datetime.now(BRT).date() - timedelta(...)` |
| 6 | `options_provider_mock.py:146` | `dt.date.today()` | `hoje_brt()` |

O **6º ponto** não estava no plano: foi encontrado durante a execução, é da
mesma classe e do mesmo caminho (calendário de vencimento) e por isso entrou —
`B3_OPTIONS_PROVIDER=mock` é ligado em staging, que também roda em UTC, e a
terceira-sexta "mais próxima" podia pular uma no limiar.

`main.py` já não tem `_hoje_brt` como quinto helper solto: não havia helper de
data BRT em `main.py` (só `now_str()`, que delega a `store.now_str()`), então
foi criado ao lado dele. Os dois `import datetime as dt` **locais** de `main.py`
(linhas 2483/2674) ficaram mortos com a mudança e saíram junto — verificado por
AST antes de remover.

`BRT = timezone(timedelta(hours=-3))` local ao módulo em cada um dos quatro,
com comentário de decisão: é o padrão já estabelecido no repo
(`store.py:14-17`, `pregao.py`, `agent.py`, `brapi_budget.py`) — não há módulo
compartilhado de fuso, e criar um agora seria mudança arquitetural fora do
escopo desta quick.

## O que NÃO foi tocado

Os quatro módulos puros de opções (`opcoes_lastreadas`, `opcoes_motor`,
`opcoes_payoff`, `opcoes_gatilho`) — guardião por AST em
`test_opcoes_fronteira.py` proíbe relógio neles, e é justamente receber `hoje`
por argumento que os torna testáveis. As assinaturas de `propor` /
`proposta_fechar` / `_dias_ate` seguem congeladas (há teste novo que as
congela explicitamente). Nenhum arquivo de `web/` no diff, portanto sem
`vite build`.

## Guardião novo — `server/tests/test_fuso_dias_ate_vencimento.py` (16 testes)

- prazo isolado (`_days_to`, `hoje_brt`) com o instante que separa UTC de BRT;
- impacto no gate nas duas bordas (15 e 61 dias), pelo caminho real;
- espião de **argumento**: registra o `hoje` que o chamador passou e delega
  para a função REAL — cobre `propor` e `proposta_fechar` sem substituir regra;
- `riskFlag` de 21 dias via `POST /api/options/analyze`;
- janela `de` do `mydata_client`;
- guardiões estruturais por AST: nenhum dos quatro módulos com prazo volta a
  chamar `today()`; os quatro módulos puros de opções seguem sem `today`/`now`/
  `utcnow`; as três assinaturas que injetam `hoje` seguem congeladas.

Contra o código de ANTES o guardião fica vermelho com mensagem legível
(`"app.options_api.py perdeu o nome datetime — o helper de fuso BRT foi
removido"`), não `AttributeError` cru.

## Defeito encontrado e corrigido durante a execução (Rule 1)

O guardião passava sozinho e **falhava na suíte inteira** (3 testes de rota).
Causa raiz, isolada por bissecção: `test_admin_summary.py` re-importa
`app.main` (`sys.modules.pop` + `importlib.import_module`) e restaura só
`sys.modules["app.main"]` — o atributo `main` do **pacote** `app` fica
apontando para o módulo NOVO, enquanto o objeto `app` (FastAPI) usado pelo
`TestClient` é o do módulo ORIGINAL. `from app import main as main_mod`
devolvia o módulo errado e o relógio cravado não alcançava a rota; o resultado
dependia da ordem de coleta do pytest.

Correção: a fixture ancora o patch nos **globais da própria função-rota**
(`endpoint.__globals__` de `options_proposta`), que é a única referência imune
a re-import. Documentado no próprio arquivo para a próxima pessoa.

## Suíte

`bash scripts/executar.sh --testes` (exit 0):

```
== Suítes do backend ==
2342 passed, 4 skipped, 485 warnings in 50.16s
== web/tests ==
126 [OK], 0 [X]
```

Primeira execução dentro do sandbox falhou com `Operation not permitted` ao
escrever os `.log` das suítes web (o `mktemp` do script resolveu vazio e o
caminho virou `/test_x.mjs.log`) — reexecutada com o sandbox desligado, como
prevê a nota de ambiente. Não é falha de teste.

## Limitações conhecidas

- Deploy **não** foi feito (fora do escopo). É mudança só-backend: quando for
  ao ar, `SERVER_BUILD_ID` precisa de bump manual.
- O comportamento só se manifesta das 21:00 às 23:59 BRT; verificação ao vivo
  em produção exige essa janela ou `TZ` forçado.

## Self-Check: PASSED

- `server/tests/test_fuso_dias_ate_vencimento.py` — existe, versionado no commit
- commit `43dc815` — existe em `git log`
- diff do commit contém exatamente os 5 arquivos, sem deleções
- working tree limpo após o commit
