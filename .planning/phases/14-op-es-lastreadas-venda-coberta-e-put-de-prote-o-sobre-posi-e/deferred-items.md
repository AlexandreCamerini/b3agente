# Deferred Items — Phase 14

Out-of-scope discoveries logged during execution, not fixed (per SCOPE BOUNDARY:
only auto-fix issues directly caused by the current task's changes).

## Plano 08

- **`GET /api/options/proposta/{ticker}` — `motivoTexto` fica com placeholders
  não substituídos (`{n}`, `{strike}`, `{premioTotal}`) quando `motivo` é um
  motivo de SUCESSO (`call_coberta`/`put_protecao`).** Achado durante a
  verificação ponta a ponta da Task 1: a rota (`server/app/main.py`,
  `options_proposta`, Plano 14-03) sempre chama
  `skill_ref.opcoes_lastreadas_txt(modo, motivo, ticker=t)` passando só
  `ticker=t` — correto para os motivos de AUSÊNCIA (`sem_lastro`/`degradado`/
  `sem_setup`/etc., que só usam `{ticker}`), mas incompleto para os motivos de
  sucesso, cujo template usa `{n}`/`{strike}`/`{premioTotal}` (só preenchidos
  dentro de `opcoes_lastreadas.propor()`, que grava o texto certo em
  `proposta.manchete`/`proposta.didatica`). `skill_ref.opcoes_lastreadas_txt`
  usa `str.replace` por chave (nunca `KeyError`), então o resultado é uma
  string com chaves literais não substituídas, sem erro 500.
  **Sem impacto no produto**: `PropostaLastreada` (`web/src/App.jsx:3010-3020`)
  só renderiza `r.motivoTexto` dentro do ramo `if (!r.proposta)` — quando
  `motivo` é de sucesso, `r.proposta` é truthy e o componente usa sempre
  `p.manchete`/`p.didatica` (corretos), nunca `r.motivoTexto`. Confirmado por
  leitura de código, não corrigido (fora do escopo da Task 1 do Plano 08 —
  não faz parte da sequência de curl exigida pelos acceptance_criteria, e não
  foi causado pelas mudanças desta task). Fix sugerido para quem pegar:
  passar os mesmos `dados` de `opcoes_lastreadas.propor()` para o
  `motivo_texto` também, ou simplesmente não recalcular `motivoTexto` quando
  `resultado["proposta"]` já existe (usar `proposta["manchete"]` como
  `motivoTexto` nesse caso).

## Plano 07

- **`server/tests/test_reuso_analise_n2.py::test_rota_reaproveita_e_so_chama_a_ia_quando_a_pergunta_muda`**
  e **`server/tests/test_rotas_fase4.py::test_ia_sem_chave_gera_fallback_deterministico_technical`**
  falham quando a suíte pytest inteira roda (`bash scripts/executar.sh --testes`),
  mas passam limpos quando rodados isoladamente (`pytest tests/test_reuso_analise_n2.py
  tests/test_rotas_fase4.py` → 44 passed). Indica poluição de estado entre arquivos
  de teste (provável módulo global não resetado entre suites, ex.: cache de
  `technical_snapshot`), não relacionada a opções lastreadas — o plano 14-07 não
  tocou nenhum arquivo em `server/`. Não corrigido (fora do escopo desta task);
  registrado para investigação futura.
