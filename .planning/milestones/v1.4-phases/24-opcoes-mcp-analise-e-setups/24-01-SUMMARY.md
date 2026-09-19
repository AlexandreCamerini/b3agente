---
phase: 24-opcoes-mcp-analise-e-setups
plan: 01
subsystem: api
tags: [fastapi, mcp, opcoes, payoff, metering, cap, pytest]

# Dependency graph
requires:
  - phase: 23 (aba-opcoes F1/F2 — ADR-027)
    provides: "`mcp_client` (fronteira única), `options_mcp_api` com `_cap_check`/`_chamada_com_cap`/`_erro_http`/`_frescor*`, guardiões i–v"
  - phase: 15 (ENG-02)
    provides: "`opcoes_payoff.perfil_da_estrutura` — a matemática de payoff do Boris, pura"
provides:
  - "`GET /api/options/mcp/cadeia/{ticker}` — cadeia verbatim com `truncado` e frescor medido do anexo"
  - "`GET /api/options/mcp/operaveis/{ticker}` — peneira do Boris com o critério declarado na resposta"
  - "`POST /api/options/mcp/proposta` — estruturas para uma tese, com `emReais` opcional"
  - "`POST /api/options/mcp/possibilidades` — 2×N+1 com reserva de cap em duas etapas"
  - "`_em_reais`/`_lote` — a única conta desta camada, fechada no backend"
  - "`_frescor_do_anexo`/`_frescor_nao_medido` — os dois lados do carimbo de idade"
  - "paridade `opcoes_payoff` × `evaluate_option_structure` travada por teste (gatilho do ADR-027, Decisão 3)"
affects: [24-02, 24-03, 24-04, 24-05, aba-opcoes-front, fase-4-veredito]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Reserva de cap em duas etapas quando o custo depende do resultado da primeira chamada (D-24.1)"
    - "Conversão por lote fechada no backend, com breakeven estruturalmente fora do bloco de reais (D-24.2)"
    - "Espião de tool que despacha por NOME e por FORMA do pedido (a mesma tool tem duas formas no contrato)"
    - "Fixture DERIVADA do motor puro como oráculo de paridade, com contra-guardião de divergência"

key-files:
  created:
    - server/tests/test_options_mcp_api.py
    - server/tests/test_opcoes_paridade_mcp.py
    - server/tests/fixtures/mcp_evaluate_petr4.json
  modified:
    - server/app/options_mcp_api.py

key-decisions:
  - "`/possibilidades` reserva 1, descobre N em `expirations` e aninha `with _cap_check(uid, 2*N)` — reservar o teto recusaria quem tem cota; reservar 1 e gastar 13 faria o cap mentir"
  - "`/possibilidades` exige tese (`direction` ou `kind`), como `/proposta`: o serviço não escolhe direção e esta camada menos ainda"
  - "Item de possibilidade tem forma UNIFORME (`estrutura`/`emReais`/`motivo`/`erro` sempre presentes) — a tela renderiza uma lista só"
  - "`kind`/`name` da estrutura vêm do `propose` (quem montou), não do `evaluate` (quem avaliou)"
  - "`MOTIVO_SEM_VENCIMENTO` é o ÚNICO motivo escrito por esta camada, e só porque não houve segunda chamada para citar um `reason` do serviço"
  - "A explicação do breakeven em `_em_reais` mora em comentário ACIMA do `def`: o critério de aceite do plano proíbe a palavra dentro do corpo, docstring incluída"

patterns-established:
  - "Validação do pedido ANTES do `_cap_check`, e o cap antes da rede: dois degraus do mesmo princípio (pedido torto não custa chamada do teto compartilhado)"
  - "`McpErroDeTool` capturado DENTRO do laço (é sobre aquele item); as demais exceções FORA (são sobre o serviço)"
  - "Texto fixo novo do módulo entra em `AVISOS`, que é a superfície de varredura do `test_guardrail_imperativo`"

requirements-completed: ["PLANO Fase 3 — backend"]

# Metrics
duration: 32min
completed: 2026-09-11
---

# Phase 24 Plano 01: Aba Opções — cadeia, operáveis, proposta e possibilidades Summary

**Quatro rotas novas levam a aba de "ler o ativo" para "ver o que dá para montar e quanto custa": cadeia verbatim com truncamento à mostra, peneira com o critério declarado, proposta por tese e o 2×N+1 de `/possibilidades` com reserva de cap em duas etapas — mais a paridade entre a matemática do Boris e a do serviço travada por teste.**

## Performance

- **Duration:** 32 min
- **Started:** 2026-09-11T19:10:00Z
- **Completed:** 2026-09-11T19:42:00Z
- **Tasks:** 3
- **Files modified:** 4 (1 modificado, 3 criados)

## Accomplishments

- `GET /cadeia/{ticker}` e `GET /operaveis/{ticker}` (custo 1 cada), com envelope completo, frescor honesto nos dois modos (medido pelo anexo × não medido declarado) e `criterioAplicado` expondo os números do Boris.
- `POST /proposta` (custo 1) e `POST /possibilidades` (custo 2×N+1), esta última com a reserva em duas etapas do D-24.1: reserva 1, descobre N real, aninha `with _cap_check(uid, 2*N)`, e devolve o que não consumiu.
- `_em_reais`: a multiplicação pelo lote fechada no backend, com `null` preservado e breakeven estruturalmente fora do bloco de reais.
- 33 testes de rota offline + 5 de paridade (4 executados, 1 vivo pulado sem credencial), sobre fixture DERIVADA de `opcoes_payoff` com contra-guardião de divergência.
- Guardião de reserva **provado**: sem o `with` do segundo cap, o teste de duas consultas por cache fica vermelho (evidência abaixo).

## Task Commits

1. **Task 1: frescor do anexo, helper de lote e as duas rotas de leitura de cadeia** — `54c88a1` (feat)
2. **Task 2: `/proposta` e `/possibilidades` — a reserva em duas etapas** — `d445214` (feat)
3. **Task 3: testes das quatro rotas e paridade `opcoes_payoff` × MCP** — `46d1d3e` (test)

## Files Created/Modified

- `server/app/options_mcp_api.py` — +4 rotas; `_frescor_do_anexo`, `_frescor_nao_medido`, `_em_reais`, `_vezes_lote`, `_lote`, `_tipo_de_opcao`, `_direcao`, `_limite`, `_preco_de_cenario`, `_ticker_do_corpo`, `_tese`, `_pernas_para_avaliar`; constantes `OPERAVEIS_*`, `N_MAX_VENCIMENTOS`, `CHAVES_DA_ESTRUTURA`, `AVISO_FRESCOR_SEM_ANEXO`, `MOTIVO_SEM_VENCIMENTO`.
- `server/tests/test_options_mcp_api.py` — 33 testes das quatro rotas pelo caminho HTTP completo, offline.
- `server/tests/test_opcoes_paridade_mcp.py` — paridade campo a campo e ponto a ponto + contra-guardião + variante viva (skip sem `MCP_CLIENT_SECRET`).
- `server/tests/fixtures/mcp_evaluate_petr4.json` — trava de alta de 2 pernas em PETR4, com todos os números derivados de `opcoes_payoff.perfil_da_estrutura` e gravados no vocabulário do serviço.

## Verificação

Suíte canônica inteira, FORA do sandbox (`bash scripts/executar.sh --testes`):

```
2379 passed, 5 skipped, 550 warnings in 68.69s (0:01:08)
127 arquivos web/tests/*.mjs [OK], 0 falhas
exit=0
```

Baseline antes deste plano: **2342 passed, 4 skipped**. Delta: **+37 passed** (33 de `test_options_mcp_api.py` + 4 de `test_opcoes_paridade_mcp.py`) e **+1 skipped** (`test_paridade_viva`, sem credencial).

Demais critérios:

- `git diff --stat server/requirements.txt server/requirements-prod.txt` — vazio (nenhuma dependência nova).
- `grep -c "@router.post" server/app/options_mcp_api.py` → **2**.
- `grep -n "def _em_reais"` → **1**; a palavra `breakeven` NÃO aparece entre `def _em_reais` e o `def` seguinte (checagem do plano roda e sai 0).
- Nenhum `or 0` novo: os dois `or 0` do arquivo são os pré-existentes de `_Reserva` (`int(reservado or 0)`, `int(custo or 0)`).
- `metering.consume` continua aparecendo em UM lugar só, dentro de `_cap_consume`.
- `McpErroDeTool` capturado dentro do `for` de `/possibilidades` (linha 1307); `(McpErro, ValueError)` fora dele.

**Prova do guardião de reserva** (critério de aceite da Task 3): troquei `with _cap_check(uid, 2 * len(escolhidos)) as cap2:` por `cap2 = _cap_check(...)` + `if True:`, rodei e obtive

```
FAILED tests/test_options_mcp_api.py::test_duas_consultas_por_cache_nao_produzem_falso_esgotado
1 failed, 1 passed, 31 deselected
```

e revertí com `git checkout -- server/app/options_mcp_api.py` (o arquivo já estava commitado; `git status` limpo depois). O teste não passa por vacuidade.

## Decisions Made

- **Exigir tese também em `/possibilidades`.** O plano só declarou `tese_ausente` em `/proposta`, mas o corpo de `/possibilidades` carrega os mesmos `direction`/`kind`, e sem tese a segunda etapa chamaria `propose_option_setups` sem direção — o serviço devolveria catálogo, não estrutura, e a rota gastaria 2×N chamadas para montar nada.
- **Item de possibilidade com forma uniforme.** O plano descrevia três formas de item (sucesso, sem estrutura, erro) com chaves diferentes. A tela renderiza UMA lista; chave que aparece e some obriga o front a testar existência em vez de valor. `estrutura`, `emReais`, `motivo` e `erro` existem sempre, com `None` onde não se aplica.
- **`kind`/`name` vêm do `propose`.** `evaluate_option_structure` não devolve esses dois campos (não é ele quem nomeia a estrutura). Sem o preenchimento a partir do setup, a tela mostraria payoff sem nome.
- **`MOTIVO_SEM_VENCIMENTO` entrou em `AVISOS`.** É a superfície que o `test_guardrail_imperativo` varre (FONTES). Texto fixo novo que chega ao usuário tem de nascer coberto — mesmo que o guardião só procure verbo de ordem hoje.

## Deviations from Plan

### Auto-fixed / ajustes de execução

**1. [Rule 2 — correção] `bool` recusado em `quotes_age_hours`**
- **Found during:** Task 1 (extração de `_frescor_do_anexo`)
- **Issue:** o ramo original testava `isinstance(idade, (int, float))`, e `bool` é subclasse de `int`: um `True` no campo viraria "1 hora" na tela — número inventado a partir de um dado que não é número (princípio 4).
- **Fix:** `idade_ok = isinstance(idade, (int, float)) and not isinstance(idade, bool)`, mesma régua de `_numero` em `opcoes_payoff.py`.
- **Verification:** `test_options_mcp_leitura.py` e `test_mcp_cap.py` seguem verdes (o caso nunca era exercido; a mudança é aditiva).
- **Committed in:** `54c88a1`

**2. [Rule 3 — contradição interna do plano] docstring de `_em_reais` × critério de aceite**
- **Found during:** Task 1
- **Issue:** o plano escreveu a explicação do breakeven DENTRO da docstring de `_em_reais` e, no mesmo bloco, um critério de aceite que reprova a palavra `breakeven` em qualquer lugar entre `def _em_reais` e o `def` seguinte — docstring incluída. Seguir o texto reprovaria o critério.
- **Fix:** a explicação (por que breakeven não está ali, e por que isso não é esquecimento) virou comentário imediatamente ACIMA do `def`. A docstring mantém o resto.
- **Verification:** a checagem do plano roda e sai 0.
- **Committed in:** `54c88a1`

**3. [ajuste] `MOTIVO_SEM_VENCIMENTO` como constante coberta por `AVISOS`**
- **Found during:** Task 2
- **Issue:** o plano pedia "`motivo` dizendo que não há vencimento aberto" sem dizer onde o texto mora; texto fixo solto ficaria fora do guardião imperativo (o mesmo descuido que a F2 corrigiu com os avisos de frescor).
- **Fix:** constante de módulo, acrescentada a `AVISOS`, com comentário explicando que `AVISOS` é a superfície de varredura do módulo — não só os avisos de frescor.
- **Committed in:** `d445214`

**4. [ajuste] `precoObjeto` no envelope de `/operaveis`**
- `find_tradable_options` não devolve `underlying_price` no contrato; o campo sai `None`. Mantido por simetria de envelope com `/cadeia` — e `None` é a resposta honesta, não um preço fabricado.

**5. [ajuste] códigos de erro nomeados pelo executor**
- O plano nomeou `kind_invalido`, `tese_ausente`, `lote_invalido` e `cenario_invalido`. Os outros dois nasceram aqui: `limite_invalido` (faixa de `limit`) e `ticker_ausente` (corpo de POST sem ativo).

### Divergências de contagem nos critérios de aceite (não são defeito)

**6. `grep -c "with _cap_check("` dá 9, não 7.** São 8 usos reais + 1 ocorrência na docstring do próprio `_cap_check`. A conta do plano ("3 rotas antigas + 2 do Task 1 + 2 aninhados") esqueceu que `/proposta` também tem o seu: 3 antigas + `/cadeia` + `/operaveis` + `/proposta` + os 2 de `/possibilidades` = 8.

**7. `grep -rn "httpx\|requests\|mcp.semente" tests/test_options_mcp_api.py` retorna 1 linha.** É `assert corpo["fonte"] == "mcp.semente.dev"` — asserção do RÓTULO de fonte que a rota devolve, idêntica à do arquivo irmão `test_options_mcp_leitura.py:178`, e não uma dependência de rede. O arquivo não importa `httpx`/`requests` em lugar nenhum e substitui `mcp_client.call_tool` por espião em todos os testes. A régua do guardião (ii) do `test_mcp_guardioes.py` faz a mesma distinção: `mcp.semente.dev` sem esquema é rótulo, não endereço.

**8. Contagem de testes acima do pedido.** `test_options_mcp_api.py` tem 33 (o plano pedia ≥16 e listou 16 afirmações — todas cobertas, algumas parametrizadas em mais de um caso). `test_opcoes_paridade_mcp.py` tem 4 executados + 1 skipped (o plano previa 3 + 1): acrescentei `test_fixture_declara_a_forma_do_contrato`, que reprova se a fixture perder um campo do contrato — sem ele, um campo sumindo da fixture faria a comparação encolher em silêncio.

---

**Total deviations:** 5 ajustes + 3 divergências de contagem. Nenhuma mudança arquitetural; nenhuma dependência nova.
**Impact on plan:** nenhum item do plano deixou de ser entregue. Os ajustes 1–3 são de correção/cobertura; 4–5 são preenchimento de lacuna do texto.

## Issues Encountered

- **A mesma tool com duas formas.** `propose_option_setups` sem tese devolve catálogo/vencimentos, e com tese devolve estruturas — as duas chamadas de `/possibilidades` batem na MESMA tool. O espião herdado da F2 despacha só por nome e não distinguiria as duas; o deste plano despacha por nome **e** pela forma do pedido (`_roteador`). Sem isso, o teste do `setups: []` estaria afirmando sobre a chamada errada.
- **Cache L1 e chaves de argumento.** As chamadas por vencimento carregam `expiration` nos args, então não colidem com a chamada base no cache do `mcp_client` — verificado pela contagem exata de 7 chamadas no teste.

## Known Stubs

Nenhum. Este plano não toca front: nenhuma tela consome as rotas novas ainda (é o 24-02 que faz a fiação). As rotas respondem dado real do serviço ou erro declarado — nenhum valor de placeholder.

## Pendências de verificação (declaradas)

- **D-24.7 — nada foi exercitado ao vivo.** `MCP_CLIENT_SECRET` não está no ambiente de desenvolvimento. `test_paridade_viva` nasce `skip` e é o que o smoke de staging deve rodar.
- **Aceite "N=6 abaixo de 20 s" não medido.** O custo 2×N+1 foi provado na contagem de chamadas, não em latência real — depende de credencial.
- **`emReais` na tela.** A conversão está travada por teste no backend; que a tela mostre reais onde é reais e preço onde é preço é aceite do 24-02.

## Threat Flags

Nenhuma superfície nova fora do `<threat_model>` do plano. As quatro rotas ficam atrás de `require_user` + `_cap_check` (guardião iv confirma por AST), nenhum segredo entra em resposta (o texto de 503 não diferencia credencial recusada de serviço fora do ar — o detalhe vai só ao obslog) e nenhum pacote foi instalado.

## Next Phase Readiness

Pronto para o **24-02** (front da Fase 3): as quatro rotas respondem, o envelope é estável (`pregao`/`fonte`/`at`/`frescor`/`cap` em todas) e `chamadasPrevistas` já sai na resposta para a UI mostrar o custo antes de disparar. O helper `escolherFrescor` do front precisa preferir o frescor MEDIDO (`/status`, `/cadeia`) ao `medido: false` das rotas sem anexo — é a contraparte de `AVISO_FRESCOR_SEM_ANEXO`.

Bloqueio conhecido para a publicação: nada deste plano vai ao ar sem o bump + `publicar-web.sh` do 24-05, que só roda com o OK explícito do Alex.

---
*Phase: 24-opcoes-mcp-analise-e-setups*
*Completed: 2026-09-11*

## Self-Check: PASSED

Arquivos afirmados existem (`options_mcp_api.py`, `test_options_mcp_api.py`, `test_opcoes_paridade_mcp.py`, `fixtures/mcp_evaluate_petr4.json`, este SUMMARY) e os três commits estão no histórico (`54c88a1`, `d445214`, `46d1d3e`). Coleta do pytest: 38 testes nos dois arquivos novos (33 + 5).
