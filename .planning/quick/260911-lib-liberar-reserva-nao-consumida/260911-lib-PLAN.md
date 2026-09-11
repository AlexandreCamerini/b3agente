---
quick_id: 260911-lib
phase: quick-260911-lib
plan: 01
type: quick
wave: 1
depends_on: [260910-wfp]
files_modified: [server/app/options_mcp_api.py, server/tests/test_mcp_cap.py]
autonomous: true
---

<objective>
Fechar a decisão pendente deixada pela quick 260910-wfp (achado A-07): a
reserva atômica da cota protege de verdade, mas o que é reservado e NÃO
consumido só volta por expiração (120 s). Nas rotas da aba Opções isso produz
um falso "Cota do dia da aba Opções esgotada" — afirmação falsa ao usuário,
a MESMA classe do A-08 corrigido no mesmo lote.

**Decisão tomada pelo orquestrador: opção (A)** — devolver a reserva não
consumida num `finally`, mantendo a proteção. As alternativas foram recusadas:
(B) desligar a reserva na aba tiraria a proteção justamente onde o teto é
compartilhado com toda a base (2.000/dia do client `boris`); (C) aceitar
contradiria a correção do A-08 feita no mesmo lote.
</objective>

<context>
A aritmética do problema (do SUMMARY de 260910-wfp, NÃO medida ao vivo):
`/mcp/leitura` faz `_cap_check(uid, 3)` e pode consumir 0 quando as três tools
vêm do cache. Com `rate_per_min=20`, chega a 60 unidades reservadas por
minuto contra uma cota de 60/dia — falso esgotado, transitório mas real.

Call sites em `server/app/options_mcp_api.py`: `_cap_check` nas linhas ~419
(status, custo 1) e ~474 (leitura, custo 3), mais o do gráfico; `_cap_consume`
em ~382, ~442 e no da leitura. `metering.liberar(conn, user_id, *, custo, section)`
já existe e é testada (quick 260910-wfp) — NÃO toca `count`, só devolve reserva.
</context>

<tasks>
<task type="auto">
  <name>Task 1: devolver a reserva não consumida</name>
  <files>server/app/options_mcp_api.py, server/tests/test_mcp_cap.py</files>
  <action>
  Em cada rota que chama `_cap_check`, garantir que a diferença entre o
  RESERVADO e o CONSUMIDO volte — inclusive quando a rota levanta
  `HTTPException` no meio. Desenho sugerido, mas decida lendo: um helper
  (`_cap_saldo(uid, reservado)` ou um context manager) que conte o consumido e
  libere o resto num `finally`. Evite contabilidade manual espalhada por três
  rotas, que divergiria na quarta.

  Invariantes que NÃO podem quebrar:
  - falha nunca gasta cota (propriedade preservada em 260910-wfp);
  - acerto de cache nunca gasta cota (decisão A-07 do ADR-027);
  - `liberar` nunca mexe em `count`;
  - a soma liberada nunca excede a reservada (liberar a mais daria cota de
    graça — pior que o defeito que estamos corrigindo).

  Testes em `test_mcp_cap.py`: (a) rota que reserva 3 e consome 1 devolve 2 —
  provar pelo `metering.snapshot`/estado, não por log; (b) rota que reserva e
  levanta `HTTPException` devolve tudo; (c) **o caso do relatório**: N chamadas
  seguidas servidas por cache não acumulam reserva até falso esgotado (monte o
  cenário com a cota baixa por env e prove que a (N+1)-ésima ainda passa);
  (d) a soma liberada nunca excede a reservada.
  </action>
  <verify>pytest test_mcp_cap.py, test_metering.py e test_options_mcp_leitura.py; depois `bash scripts/executar.sh --testes`</verify>
  <done>Cenário do falso esgotado provado RED antes e GREEN depois.</done>
</task>
</tasks>

<success_criteria>
Um commit atômico. `metering.py` NÃO é tocado (a API já existe). Front não é
editado. Deploy só-backend, bump manual — NÃO fazer.
</success_criteria>
