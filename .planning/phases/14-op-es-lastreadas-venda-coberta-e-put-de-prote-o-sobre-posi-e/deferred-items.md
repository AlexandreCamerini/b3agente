# Deferred Items — Phase 14

Out-of-scope discoveries logged during execution, not fixed (per SCOPE BOUNDARY:
only auto-fix issues directly caused by the current task's changes).

## Plano 08

### Task 2 (bugfix do checkpoint humano — proposta de fechamento estável)

- **Manchete de `proposta_fechar()` (`server/app/opcoes_lastreadas.py`) reusa
  o texto de `propor()` para `call_coberta`/`put_protecao`, que fala em
  "Vender N call(s)..."/"Comprar N put(s)..." — verbo de ABERTURA, mesmo
  quando a posição JÁ ESTÁ aberta e a proposta é de FECHAMENTO.** O botão da
  UI (`web/src/App.jsx`, `PropostaLastreada`, `cp.ctaFecharLastreada`) já diz
  "Recomprar"/"fechar" corretamente — só a MANCHETE acima do botão (e a
  `didatica` do modo Estudo) ficam com a frase de abertura. Intencionalmente
  NÃO corrigido nesta task: o objetivo do bugfix é o `contractSymbol`
  estável (motor determinístico continua batendo com a posição real); o
  texto exibido é decisão de copy, fora do escopo desta correção pontual
  (`skill_ref.OPCOES_LASTREADAS` precisaria de 2 chaves novas —
  `call_coberta_fechar`/`put_protecao_fechar` — uma mudança de vocabulário,
  não de motor). Sem impacto de correção financeira: os números (contratos,
  strike, prêmio) continuam certos, só a frase de abertura soa estranha no
  estado já-aberto. Fix sugerido para quem pegar: adicionar as 2 chaves de
  fechamento em `OPCOES_LASTREADAS` (`operador`/`educacional`) e passar um
  `tipo` distinto (ex. `"call_coberta_fechar"`/`"put_protecao_fechar"`) para
  `skill_ref.opcoes_lastreadas_txt` dentro de `proposta_fechar()`, mantendo
  o `motivo`/`tipo` de retorno como `"call_coberta"`/`"put_protecao"` (o
  front não precisa mudar).

### Task 1 (verificação ponta a ponta original)

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
