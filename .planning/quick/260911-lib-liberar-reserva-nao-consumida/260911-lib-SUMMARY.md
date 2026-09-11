---
quick_id: 260911-lib
phase: quick-260911-lib
plan: 01
status: complete
depends_on: [260910-wfp]
commit: 5b9c980
files_modified: [server/app/options_mcp_api.py, server/tests/test_mcp_cap.py]
metering_tocado: false
front_tocado: false
deploy: nao (deploy so-backend + bump manual ficam para o dono)
completed: 2026-09-11
---

# Quick 260911-lib: devolver a reserva de cota não consumida (aba Opções)

Decisão (A) do achado A-07 executada: a reserva não consumida volta na saída da
rota, a proteção atômica continua de pé, e o falso "Cota do dia da aba Opções
esgotada." desaparece.

**Commit:** `5b9c980` — `fix(260911-lib): devolve a reserva de cota nao
consumida na aba Opcoes` (um commit, dois arquivos: `server/app/options_mcp_api.py`
e `server/tests/test_mcp_cap.py`).

## A medição — o relatório anterior está CONFIRMADO, com uma nuance

A aritmética do SUMMARY de 260910-wfp nunca havia sido medida ao vivo. Foi
medida agora, pelo caminho HTTP completo (TestClient, `mcp_client.call_tool`
substituído, tudo servido por cache), contra o módulo pré-correção carregado de
um arquivo **fora do repo** (`git show HEAD:server/app/options_mcp_api.py`
injetado em `sys.modules` — nenhum `git stash`, worktree nunca sujo).

Nos valores DEFAULT do relatório (cota 60/dia, rate 20/min, `/leitura` custo 3):

```
ANTES                                        DEPOIS
apos 20 leituras: usado=0 reservado=60 rl=20  apos 20 leituras: usado=0 reservado=0 rl=20
21a leitura: 402 mcp_cota                     21a leitura: 402 (rate limit, ver D-01)
  usado: 0, limite: 60   <- contradicao
janela 60-120 s (rate limpo, reserva viva):   janela 60-120 s:
  402 mcp_cota, reservado=60, usado=0           200, reservado=0, usado=0
```

**Confirmado:** 20 leituras servidas por cache reservavam 60 unidades contra uma
cota de 60/dia, sem consumir nenhuma, e a recusa saía com `usado: 0, limite: 60`
no mesmo corpo — a resposta se contradizendo. É afirmação falsa ao usuário, a
mesma classe do A-08.

**A nuance que a medição acrescentou:** na 21ª leitura DENTRO do mesmo minuto o
rate limit (20/min) também teria recusado, então aquele 402 específico não
isolava a causa. O que isola é a janela **60–120 s**: rate limit já vencido,
reserva ainda viva (`RESERVA_TTL_S` = 120 s). Ali a recusa é 100% da reserva
presa — e é exatamente onde o defeito morde o usuário real, que espera o minuto
passar e continua ouvindo "cota esgotada". Medido simulando a passagem do tempo
pelos timestamps do kv (`rl` em −61 s, `resv` em −30 s), sem dormir um minuto.

Versão reduzida e determinística do mesmo cenário (cota 6, três leituras), que é
a que foi para o teste:

```
ANTES                              DEPOIS
n  http  codigo     usado  resv    n  http  usado  resv
1  200   -              0     3    1  200       0     0
2  200   -              0     6    2  200       0     0
3  402   mcp_cota       0     6    3  200       0     0
```

## Prova RED/GREEN do cenário (c) — o que decide a task

`test_leituras_por_cache_nao_acumulam_reserva_ate_falso_esgotado`, rodado contra
o módulo de ANTES (arquivo em `$TMPDIR`, injetado via plugin de pytest):

```
### app.options_mcp_api carregado de /tmp/.../options_mcp_api_ANTES.py
E  AssertionError: reserva acumulada depois da 1ª leitura — é assim que o
   falso esgotado se forma
E  assert 3 == 0
...
8 failed, 14 passed      <- os 8 novos falham; os 14 antigos seguem passando
```

Com o código corrigido: `22 passed` em `tests/test_mcp_cap.py`. O laço do teste
vai a 4 leituras de propósito — 4 × 3 = 12 reservaria o dobro da cota de 6,
então o teste reprova mesmo se a devolução voltar só parcialmente.

Os outros três testes pedidos pelo plano, também RED antes / GREEN depois:
(a) reserva 3 / consome 1 / devolve 2, provado por `metering.reservado` e
`used` (estado, não log), inclusive no registro **global**; (b) rota que levanta
devolve tudo (`/leitura` → 422 e `/status` → 503); (d) soma devolvida nunca
excede a reservada — aritmética fechada numa bateria de seis caminhos
(rede, cache, misto, exceção, status rede, status cache):
`devolvido == reservado − consumido`, com `reservado == 14`.

Mais duas bordas que a revisão do invariante expôs e que viraram teste:
- `metering.liberar` normaliza `custo` para no mínimo 1 (`max(1, ...)`). Chamá-la
  com saldo 0 devolveria **uma unidade que ninguém reservou** — cota de graça.
  `devolver()` não chama; há teste espiando que `liberar` nunca é invocada
  quando a reserva foi toda consumida.
- `devolver()` é idempotente (devolução explícita + saída do `with` não devolve
  duas vezes), e consumo ACIMA do reservado satura o saldo em 0 em vez de virar
  devolução extra — sem esconder o consumo real no `count`.

## Desenho escolhido: objeto `_Reserva` usado como context manager

`_cap_check` passou a **devolver** uma `_Reserva` (antes devolvia `None`); a rota
a usa como `with _cap_check(uid, 3) as cap:`; `_chamada_com_cap` recebe a reserva
em vez do `uid` e conta o consumo; a saída do `with` devolve o saldo.

As três opções consideradas:

| Desenho | Por que não / por que sim |
|---|---|
| Contabilidade inline nas três rotas | Recusado. São 3 rotas hoje e a 4ª vem na Fase 3 do PLANO — divergiria justamente na que for escrita depois, e divergir para o lado de devolver a MAIS é cota de graça, pior que o defeito. O plano já avisava. |
| Helper + `try/finally` em cada rota | Recusado pelo mesmo motivo, em grau menor: o `finally` é correto mas precisa ser repetido, e o número do custo aparece em dois lugares (check e devolução) que podem divergir. |
| **Objeto `_Reserva` devolvido pelo próprio `_cap_check`, usado como context manager** | **Escolhido.** Uma única fonte do número do custo (o argumento do `_cap_check`), devolução em UM lugar, cobre o caminho de exceção por construção. E preserva intacto o guardião (iv) de `test_mcp_guardioes.py`, que exige por AST o Name `_cap_check` no corpo de cada rota — um context manager com outro nome (`_cap_reserva(...)`) faria a rota parecer "sem cap" e obrigaria a mexer num guardião de segurança, que é o que não se faz. |

Risco do desenho e como ficou fechado: chamar `_cap_check` **sem** o `with`
criaria a reserva e jogaria o objeto fora — volta silenciosa ao defeito, com o
caminho feliz ainda respondendo 200 e nenhum teste de rota reprovando. Daí o
guardião novo em `test_mcp_cap.py`, que exige por AST que toda função `@router`
chame `_cap_check` dentro de um `ast.With`.

**`metering.py` não foi tocado** — a API (`liberar`, `reservado`, `RESERVA_TTL_S`)
já existia da quick 260910-wfp; esta task só passou a ser o caller que faltava.
Front não foi editado (sem `vite build`). Sem deploy, sem bump.

Limite herdado, declarado e não alterado: `liberar` remove as reservas mais
ANTIGAS da fila do usuário, que é compartilhada entre requisições concorrentes
da mesma conta — então em concorrência uma requisição pode devolver a entrada
criada por outra. O TOTAL continua exato (é o que a cota compara), e é a mesma
semântica que `consume` já tinha ao liquidar. Não é regressão nova.

## Validação

```
bash scripts/executar.sh --testes
  2281 passed, 4 skipped, 444 warnings in 42.18s     (pytest, backend)
  126 [OK], zero [X]                                 (web/tests/*.mjs)
```

Suítes vizinhas em foco: `test_mcp_cap.py` (22), `test_metering.py`,
`test_options_mcp_leitura.py`, `test_mcp_guardioes.py`, `test_opcoes_fronteira.py`
→ **147 passed**. Nenhum guardião precisou ser afrouxado: (iv) e (v) de
`test_mcp_guardioes.py` passam sem edição.

A primeira execução da suíte canônica falhou por sandbox (`mktemp` negado, o
script tentou escrever `/test_*.mjs.log`); repetida com sandbox desligado,
conforme as notas do ambiente.

## Achado fora de escopo (não corrigido)

`deferred-items.md` → **D-01**: com o rate limit estourado, a rota ainda responde
`mcp_cota` / "Cota do dia da aba Opções esgotada." (o `_motivo` do metering é
descartado de propósito, §3.2 do PLANO). As duas recusas do `check` saem com a
MESMA mensagem, e a recusa por ritmo afirma cota esgotada com `usado: 0,
limite: 60`. Mesma classe de afirmação falsa do A-07/A-08, no eixo do motivo em
vez do número. Mexe em contrato de resposta que a UI lê — pede decisão do dono.

## Self-Check: PASSED

- `server/app/options_mcp_api.py` — presente, modificado, no commit `5b9c980`
- `server/tests/test_mcp_cap.py` — presente, modificado, no commit `5b9c980`
- `server/app/metering.py` — **não** aparece no diff do commit (verificado)
- commit `5b9c980` existe em `worktree-agent-a253d96e89725e6b7`; nenhuma deleção
  de arquivo no commit (`git diff --diff-filter=D HEAD~1 HEAD` vazio)
