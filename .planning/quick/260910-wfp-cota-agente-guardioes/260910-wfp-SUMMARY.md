---
quick_id: 260910-wfp
status: completo-com-decisao-pendente
data: 2026-09-10
base: 5efc24fa8bbd2f61b518eb5b734efc03c0b8b55b
branch: worktree-agent-a1217294ea32a6d8f
achados: [A-07, A-08, A-17, A-18]
suite: "2273 passed, 4 skipped (pytest) + 126 testes web OK — exit 0"
deploy: nao-feito (so-backend, exige bump manual de SERVER_BUILD_ID)
decisao_pendente: "estorno eager da reserva de cota nos callers (ver secao DECISAO PENDENTE)"
---

# 260910-wfp — os ultimos quatro achados de peso da auditoria

Quatro tasks, quatro commits, cada um com prova. Os dois primeiros tem
consequencia fora do repositorio (dinheiro e afirmacao falsa ao usuario); os
dois ultimos eram guardioes provados cegos, agora com prova invertida.

## Commits

| # | Hash | Assunto |
|---|------|---------|
| 1 | `f377e62` | `fix(metering): reserva atomica da cota de IA (auditoria A-07)` |
| 2 | `68b5bc5` | `fix(agent): ciclo nao anuncia venda que nao houve (auditoria A-08)` |
| 3 | `a9994b9` | `test(adr013): guardiao de permissoes enxerga rota de router (auditoria A-17)` |
| 4 | `2d13333` | `test(gate): filtro de comentario pega comentario de cauda (auditoria A-18)` |

Arquivos: `server/app/metering.py`, `server/app/agent.py`,
`server/tests/test_metering.py`, `server/tests/test_agent.py`,
`server/tests/test_adr013_cobertura_rotas.py`, `server/tests/test_mcp_guardioes.py`,
`server/tests/test_fase3_gate_plano.py`, `server/tests/test_fase5_gate_mensal.py`,
`server/tests/test_fase12_cap_watchlist.py`, e dois modulos de insumo novos
(`server/tests/rotas_fastapi.py`, `server/tests/fonte_python.py`).
Front NAO foi tocado. Nenhum deploy, nenhum bump, nenhum `railway`.

---

## Task 1 (A-07) — reserva atomica da cota de IA

### A corrida reproduzida

Reproduzida ANTES de mudar uma linha, com `db.shared()` (uma conexao real por
thread, igual ao singleton de `main.py` — `db.connect()` direto levanta
`ProgrammingError` em outra thread e o teste morreria sem testar nada):

```
estado inicial: used=4 quota=5
passaram na checagem: 3
estado final: used=6 quota=5  ESTOUROU
global: 7
```

**Descoberta que a auditoria nao tinha:** o estado final divergiu — contador do
usuario em **6**, global em **7**. O `read-modify-write` de `consume()` tambem
perdia atualizacao (duas threads leram `count=4`, a ultima escrita venceu). O
contador do usuario ficava MENOR que a verdade, ou seja o proprio defeito
**mascarava parcialmente o estouro** que ele causava. A trava fecha os dois.

Depois da correcao, mesmo script:

```
estado inicial: used=4 quota=5
passaram na checagem: 1
estado final: used=5 quota=5  ok
global: 5
```

### Desenho escolhido

- `METERING_LOCK` (`threading.RLock`, padrao de `mydata_budget` / WR-01) envolve
  o read-modify-write de `check`/`consume`/`liberar`. Limite declarado no
  comentario: a trava e de **processo** — cobre a concorrencia real (um unico
  uvicorn no `Procfile`), nao cobriria dois processos no mesmo SQLite.
- `check()` grava **reserva** (`resv`: uma entrada de epoch por unidade de
  custo) e compara `count + reservas + custo` com a cota. Com `cap_global`
  ligado, reserva tambem no registro global — o mesmo buraco existia la. Com
  `cap_global=None` o registro global nao e tocado por `check` (nenhuma escrita
  nova no caminho default).
- `check()` que devolve `False` **nao reserva** (so a poda do rate limit e
  salva) — senao uma recusa por rate limit comeria cota.
- `consume()` **liquida** a reserva (remove as `custo` mais antigas) no mesmo
  passo em que incrementa o confirmado. Nunca debita em dobro.
- **A propriedade que nao podia quebrar esta de pe:** `consume` segue sendo o
  unico ponto que incrementa `count`. Falha nao gasta cota — `used`,
  `month_used` e o global ficam em zero quando o modelo nao responde (testado).
- `used()`/`snapshot()`/`month_used()` continuam devolvendo **so o confirmado**.
  Reserva nao e gasto; quem mostra "usado/limite" na tela nao mudou de numero.
  `reservado()` expoe a reserva viva para teste/observabilidade.
- Registro antigo do kv (sem `resv`) e valor corrompido normalizam em `_load`.

### Como a reserva e DEVOLVIDA (a pergunta do PLAN)

Duas vias, e so uma esta em uso:

1. **Expiracao** (`RESERVA_TTL_S = 120.0`) — a que de fato acontece hoje. O
   numero cobre a janela real entre `check` e `consume`: fetch de candles + a
   chamada ao modelo, cujo `httpx.AsyncClient(timeout=60)` em `llm.py` e o teto
   de uma chamada (nao ha retry no modulo).
2. **`liberar()`** — estorno imediato, implementado e testado, **sem nenhum
   caller hoje**. E o caminho correto; esta la para o dia em que o estorno
   eager entrar. Contrato: devolve reserva e nunca toca `count`.

**Por que nao closure de estorno agora:** o `consume` chega as rotas como
closure criada em `main.py::_ai_apply_managed`, e estornar na falha exige
`try/finally` em cinco call sites (`main.py` 1609/1718/1923/2016/3239 e
`options_mcp_api.py`). O PLAN manda parar e reportar antes de mexer em caller —
feito, ver **DECISAO PENDENTE** abaixo. Nenhum caller foi tocado.

### Testes (10 novos em `test_metering.py`)

Corrida da auditoria com barreira de tres threads; teto global sob concorrencia
(tres usuarios distintos num cap de 1); falha nao gasta cota; reserva bloqueia
enquanto vale e a cota volta inteira depois de expirar; liquidacao sem debito em
dobro; consumo parcial do deep (reserva 10, consome 4, sobra 6 reservadas);
`liberar()`; check negado nao reserva; registro legado/corrompido; guardiao de
desenho da trava.

**Prova invertida (bonus, nao era exigida nesta task):** removida a linha da
reserva, `test_a07_corrida_tres_concorrentes_nao_estouram_a_cota` FALHA com
`assert 3 == 1`. Restaurada, passa.

Suites de cota/gate que nao podiam quebrar (`test_fase3_gate_plano`,
`test_fase5_gate_mensal`, `test_fase12_cap_analises`, `test_qa42_finops`,
`test_mcp_cap`, `test_options_mcp_leitura`): 191 passed.

---

## Task 2 (A-08) — o agente nao anuncia venda que nao houve

### A venda fantasma reproduzida

Sem stub do motor. `_run_cycle_inner` le `positions` **antes** do
`await quotes_getter(...)`; a venda concorrente entra dentro do getter, que e
exatamente o ponto de espera onde ela acontece em producao. A lista que o laco
percorre fica velha e `store.sell` devolve `None`.

Antes: `executed == 1`, `opsToday == 1`, evento `kind:"buy"` com
`"Protecao simulada: PETR4 vendido (stop atingido) a R$ 37.50."`, e no historico
**uma** venda (a manual) — ou seja, o Diario e o push afirmavam uma venda que o
motor nunca fez. Depois: `executed == 0`, `opsToday == 0`, nenhum evento
`kind:"buy"`, nenhuma ocorrencia de "vendido".

### O que o agente emite quando a posicao sumiu (decisao de desenho)

Evento, nao silencio (principio 9) — mas `kind:"warn"`, que o funil de push
ignora (o filtro dele e literalmente `e.get("kind") != "buy": continue`), e
**sem `tag`**: nao houve operacao, logo nao existe classe de push a notificar.
Texto: `"PETR4 com stop atingido (R$ 37.50): nenhuma venda foi feita porque <X>.
Nada foi debitado do teto diario de operacoes."`

`store.sell` devolve `None` por **dois** motivos distintos (`store.py:709`
posicao ausente; `store.py:712` lastro travado de CALL coberta, que ja registra
rejeicao). O ciclo **re-le a posicao pelo motor** para dizer qual dos dois foi —
nunca infere. Os dois casos tem teste.

`ORDER_LOCK` nao foi usado: o ciclo teria de segurar a trava atravessando o
`await` das cotacoes, o que o repositorio proibe. A venda perdida e legitima —
quem vendeu primeiro vendeu; o defeito era mentir sobre isso.

### Prova invertida

Com a guarda de `pnl is None` removida, os 5 testes novos FALHAM (4 deles pela
afirmacao falsa / teto consumido). Restaurada, 5 passam. Contraprova incluida:
a venda real continua com `executed`, `_bump_ops`, `kind:"buy"`, `tag` e
resultado realizado no texto — o caminho feliz nao foi estreitado junto.

---

## Task 3 (A-17) — guardiao de permissoes enxerga rota de router

### Medicao

```
objetos em app.routes            : 105
com .path (varredura RASA, hoje) : 102
varredura RECURSIVA              : 110

objetos com .path is None: _IncludedRouter /api/options, _IncludedRouter /api/options/mcp

rotas INVISIVEIS para o guardiao (7):
  GET  /api/options/chain/{ticker}        GET  /api/options/expirations/{ticker}
  GET  /api/options/gate/{ticker}         POST /api/options/analyze
  GET  /api/options/mcp/status            GET  /api/options/mcp/leitura/{ticker}
  GET  /api/options/mcp/setups/{name}/grafico
```

### PROVA INVERTIDA (tres cenarios)

| Cenario | Teste de gate | Trava de vacuidade (nova) |
|---|---|---|
| `/api/options/mcp/status` sem `require_user`, varredura recursiva | **FALHA** (antes passava) | passa |
| gate presente, varredura de volta ao raso | passa | **FALHA** |
| os dois juntos (= o guardiao exatamente como estava) | **PASSA (retorno 0)** — cegueira original reproduzida | **FALHA** |

A terceira linha e a prova do achado: o guardiao como estava aprovava uma rota
de opcoes sem sessao. A trava nova pega esse cenario.

### Decisoes

- Varredura recursiva extraida para `tests/rotas_fastapi.py`, modulo de
  **insumo sem nenhuma assercao**. Isso atende a razao original da copia
  ("guardiao nao importa guardiao" — nenhum depende do veredito do outro) sem a
  terceira copia. A **divergencia entre as copias era o defeito**: a do
  `test_mcp_guardioes` ja resolvia o router, a do ADR-013 (a de seguranca) nao.
- Trava de vacuidade nova (`test_a17_...`): piso de 90 rotas + ancoras de router
  explicitas (uma publica, uma gated). Sem ela um guardiao de cobertura "passa"
  quando nao olha nada — o modo mais silencioso de falhar.
- **A allowlist NAO cresceu** e o assert continua 19 — contra a expectativa do
  PLAN. Conferido rota por rota: as 4 publicas de `/api/options/*` **ja estavam
  listadas** (escritas quando a aba Opcoes entrou, mas nunca de fato exercitadas
  por este guardiao, porque ele nao as via) e as 3 do MCP tem `require_user`.
  Nota datada registra isso no proprio teste. Nenhuma rota foi promovida a
  publica nesta correcao.

---

## Task 4 (A-18) — filtro de comentario pega comentario de cauda

### PROVA INVERTIDA

Bypass do auditor reintroduzido em `main.py` (a unica chamada real ao gate
comercial sai, o nome fica num comentario de cauda):

```
filtro ANTIGO (so linha que comeca com #) conta: 1   <- cego, assercao PASSAVA
filtro NOVO  (tokenize)                  conta: 0   <- guardiao FALHA, correto

FAILED test_fase3_gate_plano.py::test_plan_can_analyze_aparece_exatamente_uma_vez_no_main
FAILED test_fase5_gate_mensal.py::test_plan_can_analyze_continua_aparecendo_exatamente_uma_vez_no_main
```

### Decisao de desenho: `tokenize`, nao corte textual no primeiro `#`

O PLAN pedia para decidir e justificar o caso de `#` dentro de string literal.
**Importa, e muito.** Cortar a linha no primeiro `#` com busca textual apagaria
codigo real depois de uma string como `"#ff0000"` ou de um path com fragmento —
a contagem cairia e o guardiao passaria a reprovar/aprovar por motivo errado.
Seria trocar um jeito de ficar cego por outro, pior.

O corte usa `tokenize` (stdlib): so o que o proprio Python classifica como
`COMMENT` sai, na coluna exata do token; `#` em string literal nao e `COMMENT`.
Erro de tokenizacao **propaga de proposito** — cair num filtro mais fraco em
silencio e exatamente como um guardiao fica cego.

Helper unico em `tests/fonte_python.py`, usado pelos tres arquivos; os nomes
locais ficam como alias e cada copia removida deixou nota datada no lugar.
Teste novo (`test_a18_...`) trava a propriedade direto, sem depender de
`main.py`: comentario de cauda nao conta **e** `#` em string nao leva codigo.

Varredura do repo: nao sobrou nenhuma outra copia do filtro fraco em fonte
Python. A unica ocorrencia restante de `startswith("#")`
(`test_opcoes_fronteira.py:236`) le `requirements.txt`, onde nao ha chamada de
funcao a esconder — fora de escopo, verificado, nao afetado.

---

## DECISAO PENDENTE (Alex) — estorno eager da reserva de cota

**Nao e bug do que foi entregue; e um efeito colateral que eu nao quis esconder
nem resolver por conta propria, porque resolver exige tocar caller.**

Com reserva por expiracao, um request que **checa mais do que consome** segura
cota por ate 120 s. Nas rotas de IA isso e inofensivo (`custo=1`, e o consume
vem no sucesso; quando falha, segurar a vaga por 2 min e até desejavel — evita
martelar o modelo com a chave paga do servidor). O problema concentra-se na
**aba Opcoes**, porque la o contrato e explicitamente "consumir menos que o
checado e sempre permitido" e o cache L1 dura 10–15 min:

- `/api/options/mcp/leitura/{ticker}` faz `_cap_check(uid, 3)` e, em acerto de
  cache, consome **0**.
- Cota 60/dia, rate 20/min (`B3_MCP_COTA_USUARIO_DIA`, `B3_MCP_RATE_MIN`).
- Pior caso aritmetico: 20 requests/min × 3 unidades = 60 unidades reservadas
  por minuto. Dentro da janela de 120 s isso **sozinho** chega no teto de 60/dia
  e o usuario veria `"Cota do dia da aba Opcoes esgotada."` sem ter gasto nada.
  Transitorio (cura sozinho em 2 min) e exige navegacao rapida entre tickers,
  mas e uma afirmacao falsa ao usuario — a mesma classe do A-08.

**Nao exercitei isso contra o aparelho nem em producao** — o numero acima e
aritmetica sobre os defaults, nao medicao.

Tres caminhos, todos pequenos; escolha sua:

| Opcao | Mudanca | Efeito |
|---|---|---|
| **A** (recomendada) | `metering.liberar(...)` num `finally` no `/mcp/leitura`, no `/mcp/status` e no `/api/scan/deep` (3 call sites, ~2 linhas cada) | mantem a protecao nova e elimina o bloqueio falso. `liberar()` ja existe e esta testada |
| **B** | `reservar=False` (parametro novo) em `options_mcp_api._cap_check` | aba Opcoes volta ao comportamento de hoje — zero risco de regressao, zero protecao nova la. A cota de IA (o dinheiro do A-07) fica protegida |
| **C** | nada | aceita o bloqueio falso transitorio na aba Opcoes |

Enquanto nao decidir, sugiro **nao mergear a task 1 para producao** (as tasks 2,
3 e 4 sao independentes e podem ir sozinhas).

## Residuos anotados, nao corrigidos (fora de escopo)

- **Gate MENSAL do plano tem a mesma classe de corrida do A-07.**
  `_gate_analise` le `metering.month_used(...)` e o incremento vem no `consume`,
  depois do modelo. A reserva fechou a janela DIARIA e a GLOBAL, nao a mensal —
  fecha-la exige o limite mensal chegar ao `check`, e o limite vive em `plan.py`
  / `main.py`. Mesma decisao de escopo acima.
- Achados da auditoria deliberadamente fora desta quick: A-06, A-09, A-10,
  A-11 (inerte), A-12, A-13 (absorvido pelo A-17), A-14, A-15, A-16, A-19.

## Validacao

- `bash scripts/executar.sh --testes` → **exit 0**; pytest **2273 passed, 4
  skipped**; **126** arquivos de teste web `[OK]`, nenhuma falha.
- A suite completa do backend foi rodada depois de **cada** task (2266 → 2271 →
  2272 → 2273), nunca so no fim.
- Front nao editado → nenhum `vite build` (regra do CLAUDE.md respeitada por
  nao aplicavel).
- Sandbox: a primeira rodada completa deu 27 falhas por `PermissionError` em
  `ssl.create_default_context` (restricao de sandbox, nao regressao); repetida
  com sandbox desligado, zero falhas.
- Scripts de reproducao e de prova invertida viveram **fora do repositorio**
  (`$TMPDIR/wfp/`). Nenhum `git stash` foi usado em nenhum momento.
