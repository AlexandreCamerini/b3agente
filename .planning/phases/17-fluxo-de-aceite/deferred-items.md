# Deferred Items — Fase 17

Itens fora do escopo do Plano 17-02, descobertos ao rodar `bash scripts/test.sh`
completo no worktree paralelo. NÃO corrigidos aqui (regra de escopo do
executor: só corrigir o que a mudança do PLANO causou).

## Falhas pré-existentes de rede/sandbox (27 testes, não relacionadas a FLOW-04)

`bash scripts/test.sh` no worktree isolado (sandbox sem egress de rede real)
reprova 27 testes que dependem de chamadas HTTP externas reais (Yahoo,
Anthropic/OpenAI, benchmark IBOV) — todos com `[Errno 1] Operation not
permitted` ou equivalente no stack. Confirmado que NENHUM deles toca
`options_proposta` (a rota alterada por este plano) exceto um:

- `test_opcoes_lastreadas_rotas.py::test_vender_posicao_100_por_cento_travada_via_sell_devolve_400`
  — falha com 502 em vez de 400 porque `/api/sell` chama
  `candle_provider.get_quote` (Yahoo real), bloqueado pelo sandbox. Testado
  isoladamente: mesma causa raiz das outras 26 falhas de rede. NÃO relacionado
  à mudança deste plano (`options_proposta`, não `/api/sell`).

Demais arquivos afetados por esta classe de falha (rede/sandbox, não FLOW-04):
`test_benchmark_ibov.py`, `test_fase3_kill_switch_duracao.py`,
`test_options_provider_yahoo.py`, `test_push_registro_evento.py`,
`test_rotas_fase4.py::test_benchmark_ibov_cache_evita_segunda_chamada_ao_provedor`,
`test_texto_vazio.py`, `test_yahoo_granularidade.py`, `test_yahoo_intraday.py`.

**Recomendação:** rodar `bash scripts/executar.sh --testes` fora do sandbox
(ambiente com egress de rede liberado) antes do merge da fase, para confirmar
que estas 27 falhas são mesmo só do sandbox e não regressões reais.

## Suíte web (`web/tests/*.mjs`) não executada neste worktree

`web/node_modules` ausente neste worktree paralelo (não instalado). O Plano
17-02 é backend-only (`git status --porcelain web/` vazio — nenhum arquivo em
`web/` foi tocado), então a suíte web não tinha o que verificar deste plano
especificamente. Não executada por falta de `node_modules` + rede sandboxed
para `npm install`. Recomenda-se rodar `bash scripts/executar.sh --testes`
completo (as DUAS suítes) no ambiente de merge/CI antes de fechar a fase.
