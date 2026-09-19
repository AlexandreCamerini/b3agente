---
phase: 24-opcoes-mcp-analise-e-setups
plan: 06
subsystem: api
tags: [fastapi, httpx, react, opcoes, mcp, degradacao, auditoria]

requires:
  - phase: 24-opcoes-mcp-analise-e-setups (planos 01–04)
    provides: "as 7 rotas novas da aba Opções (`_em_reais`, `/proposta`, `/possibilidades`, `/setups/*`), o `PayoffChart` e as duas seções da tela"
provides:
  - "`_razao_ganho_perda(dados)` puro: razão adimensional, `None` COM motivo nos quatro casos em que ela não existe"
  - "campo `razaoGanhoPerda` em `/proposta` e por item de `/possibilidades`, FORA do bloco `emReais`"
  - "`RazaoGanhoPerda` nas duas seções da tela, com o motivo verbatim quando não há número"
  - "503 `ia_indisponivel` em `/setups/compilar` para qualquer falha de transporte da LLM — a rota deixou de ter caminho para o handler 500"
  - "`_audita()`: auditoria de setup que falha em silêncio REGISTRADO, sem derrubar escrita externa já efetivada"
affects: [24-05 (publicação), Fase 4 do PLANO-aba-opcoes (veredito, que consome a razão G/P como fato determinístico)]

tech-stack:
  added: []
  patterns:
    - "helper puro adimensional ao lado do helper de dinheiro: a ausência do parâmetro `lote` na assinatura é a trava, não um teste"
    - "`except Exception` justificado por escrito quando o limite é código de terceiro, com as classes conhecidas nomeadas ACIMA do genérico"
    - "contabilidade (auditoria/custo) nunca derruba rota cuja escrita externa já foi efetivada"

key-files:
  created: []
  modified:
    - server/app/options_mcp_api.py
    - server/tests/test_options_mcp_api.py
    - server/tests/test_opcoes_dsl.py
    - web/src/opcoes/OpcoesScreen.jsx
    - web/src/copy.js
    - web/tests/test_opcoes_analisar_ui.mjs

key-decisions:
  - "A razão ganho/perda segue a MESMA régua de ambiguidade do `emReais` em `/proposta` (uma estrutura só), e NÃO a de lote: adimensional, ela existe mesmo sem lote informado"
  - "Os quatro motivos de razão indefinida são constantes em `AVISOS` — o guardião imperativo varre o texto que chega ao usuário sem passar por LLM"
  - "`AVISO_IA_INDISPONIVEL` não nomeia provedor nem modelo: no caminho gerenciado a chave é do servidor, e o nome do provedor não é informação acionável pelo usuário"
  - "`audit.record` foi fatorado em `_audita()` em vez de dois `try/except` colados — a justificativa da assimetria mora num lugar só"
  - "F-04 intocado: zero linhas em `mcp_client.py`, zero mudança em `cap.consome` e em custo declarado de rota"

patterns-established:
  - "Razão indefinida com motivo: `{valor: None, motivo: <texto>}` nunca vira 0, ∞ ou `null` mudo — a ordem dos testes (ilimitados antes de 'sem dado') preserva informação em vez de trocá-la por ignorância"
  - "Falha de transporte de terceiro → 503 acionável com a frase que remove o medo do usuário ('nada foi gravado'), e o tipo real só no obslog"

requirements-completed: ["24-VERIFICATION F-01", "24-VERIFICATION F-02", "24-VERIFICATION F-03"]

duration: 41min
completed: 2026-09-11
---

# Fase 24 Plano 06: correção dos achados F-01, F-02 e F-03 — Summary

**A razão ganho/perda passou a existir (adimensional, com motivo quando não existe), a compilação de setup perdeu o último caminho para o handler 500, e a auditoria deixou de poder derrubar uma escrita que o serviço já efetivou.**

## Performance

- **Duration:** ~41 min
- **Started:** 2026-09-11T22:05Z (aprox.)
- **Completed:** 2026-09-11T22:46Z (aprox.)
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- **F-01 fechado.** O critério 1 do ROADMAP termina em "breakevens e **razão ganho/perda**" e ela não existia em lugar nenhum do código. Agora existe no backend (`_razao_ganho_perda`, puro), viaja nas duas rotas e aparece nas duas seções da tela. Os quatro casos em que a razão **não existe** — ganho sem teto, perda sem piso, dado ausente, perda zero — devolvem `None` com motivo próprio, nunca um número.
- **F-02 fechado.** `httpx.ReadTimeout`/`ConnectError` do provedor de LLM subiam intactas para o `@app.exception_handler(Exception)` e viravam 500 com `{"detail": "ReadTimeout: "}`. Agora são 503 `ia_indisponivel` com a frase que faltava: **"nada foi gravado"** (a compilação é dry-run, a falha é inócua).
- **F-03 fechado.** `audit.record` roda DEPOIS de `create_setup(confirm=true)`. Falha de contabilidade não derruba mais a resposta — ela vai para o obslog em `level="warn"`, e a escrita efetivada é reportada como efetivada.
- **F-04 intocado e registrado como pendente de decisão do Alex** (ver "Pendências" abaixo).

## Prova RED → GREEN (a regra de ouro deste plano)

Cada correção tem teste que **falha sem ela**. A prova foi feita na ordem: escrever o teste → rodar contra o código atual → ver vermelho → corrigir → ver verde.

| Achado | Teste escrito primeiro | RED observado (código de antes) | GREEN (depois) |
|---|---|---|---|
| F-01 | 14 testes em `test_options_mcp_api.py` (5 casos do helper + assinatura sem `lote` + `AVISOS` + 4 de rota) | `14 failed, 33 deselected` — `AttributeError: module 'app.options_mcp_api' has no attribute '_razao_ganho_perda'` | `51 passed` (com `test_guardrail_imperativo.py`) |
| F-01 (front) | 13 asserções novas em `test_opcoes_analisar_ui.mjs` | `7 FALHA(S)` — componente, fiação nas duas seções, motivo, e as 4 de copy | `todos os testes passaram` |
| F-02 | 2 testes em `test_opcoes_dsl.py` (`httpx.ReadTimeout` e `RuntimeError`) | `2 failed` — a exceção **escapou da rota** até o cliente de teste, que é exatamente o caminho do handler 500 em produção | `129 passed` (com fronteira + guardiões MCP + imperativo) |
| F-03 | 1 teste em `test_opcoes_dsl.py` (`audit.record` levantando `RuntimeError`) | `1 failed` — `RuntimeError: database is locked` escapou das duas rotas | `30 passed` |

## Task Commits

1. **Task 1 (F-01): razão ganho/perda no backend e na tela** — `1dda475` (feat)
2. **Task 2 (F-02): falha de rede da LLM não vira 500** — `434afb0` (fix)
3. **Task 3 (F-03): auditoria não derruba rota com escrita já efetivada** — `477e27e` (fix)

## Files Created/Modified

- `server/app/options_mcp_api.py` — `_razao_ganho_perda` (puro, ao lado de `_em_reais`); `_audita`; `_erro_de_ia`; 5 constantes novas em `AVISOS`; `import httpx`; fiação de `razaoGanhoPerda` em `/proposta` e nos três ramos do item de `/possibilidades`
- `server/tests/test_options_mcp_api.py` — seção "razão ganho/perda" com 14 testes
- `server/tests/test_opcoes_dsl.py` — 3 testes de degradação (timeout, exceção genérica, auditoria que levanta)
- `web/src/opcoes/OpcoesScreen.jsx` — componente `RazaoGanhoPerda`, renderizado nas duas seções
- `web/src/copy.js` — `opcoesRazaoRotulo` e `opcoesRazaoAjuda` nos DOIS modos
- `web/tests/test_opcoes_analisar_ui.mjs` — bloco 13 (razão: renderizada nas duas seções, não recalculada, não encostada em `emReais`, motivo visível, ajuda que nega "probabilidade"), com asserções de sanidade nas duas regex novas

## Decisões Made

1. **A razão em `/proposta` usa a régua de ambiguidade do `emReais`, não a de lote.** `emReais` exige lote **e** estrutura única; a razão exige só estrutura única. O plano dizia "quando há estrutura": com duas estruturas no envelope, uma razão solta não diria de qual delas é — é o mesmo argumento que o código já fazia para o dinheiro, e o front só renderiza `estruturas[0]`. Com `len(estruturas) != 1` o campo sai `null`, exatamente como `emReais`.
2. **A ordem dos testes dentro do helper é o desenho.** Os dois `unlimited_*` vêm ANTES da checagem de número porque, nesse caso, `max_gain`/`max_loss` costuma vir `null` junto — e cair em `RAZAO_SEM_DADO` trocaria "sem teto" (informação do serviço) por "não veio o dado" (ignorância do app). Está comentado no código.
3. **Booleano não é número.** Mesma régua de `_vezes_lote`: `True` passaria por 1 num `isinstance(x, (int, float))` ingênuo e produziria uma razão. Há caso de teste para isso.
4. **`AVISO_IA_INDISPONIVEL` virou constante em `AVISOS`,** embora as mensagens inline de `_erro_http` não estejam lá. Precedente seguido: os dois 402 do gate (`AVISO_PLANO_ANALISES`/`AVISO_IA_GERENCIADA`) são constantes em `AVISOS`; texto novo que chega ao usuário entra na varredura ([R-12]).
5. **`audit.record` fatorado em `_audita()`** em vez de dois `try/except` colados nas rotas: a justificativa da assimetria (a escrita externa já aconteceu; retentativa duplica no armazém sem dono) mora num lugar só, e um terceiro chamador futuro herda a proteção em vez de reintroduzir o defeito.
6. **Nenhum `except Exception` sem justificativa escrita.** Os dois novos (`_erro_de_ia` e `_audita`) carregam, no código, o motivo de existirem e o motivo de não serem preguiça.

## Deviations from Plan

### Ajustes de forma (nenhum de escopo)

**1. [Rule 2 — Missing critical] `action` no corpo do 503 de IA indisponível**
- **Found during:** Task 2
- **Issue:** O plano especificava `{"code", "message", "action": ...}` sem dizer o texto do `action`. Sem ele, o `enrichErrorMessage` do front não monta a linha "Como corrigir:" e o 503 vira um 500 com outro número.
- **Fix:** `action` explicando que a cadeia, as operáveis e os setups já gravados seguem funcionando (não dependem de IA). Teste assert `detalhe.get("action")`.
- **Committed in:** `434afb0`

**2. [Rule 3 — Blocking] `except (httpx.TimeoutException, httpx.HTTPError)` e `except Exception` como cláusulas SEPARADAS**
- **Found during:** Task 2
- **Issue:** O plano pedia as três numa lista. `except (A, B, Exception)` é sintaticamente válido mas equivale a `except Exception` e esconde a intenção.
- **Fix:** Duas cláusulas, a nomeada primeiro (documenta o caso que de fato acontece), a genérica depois (rede de segurança do critério 7), ambas chamando `_erro_de_ia`. Comentado no código, inclusive a nota de que `HTTPException` levantada num `except` irmão não cai na cláusula genérica.
- **Committed in:** `434afb0`

**3. [Rule 2 — Missing critical] O motivo da razão indefinida ocupa a linha inteira, com quebra**
- **Found during:** Task 1
- **Issue:** O plano dizia "com `valor` nulo, o `motivo` verbatim em vez do número". O componente `Linha` põe o valor à direita, numa única linha com `tabular-nums` — um motivo de ~100 caracteres seria cortado em 375 px, e é justamente ele que impede a leitura errada.
- **Fix:** Com número, `<Linha>` normal ("1 : 2,23"); sem número, um bloco de duas linhas com `whiteSpace: pre-wrap`.
- **Committed in:** `1dda475`

**4. [Rule 1 — Consistência] `razaoGanhoPerda: None` nos três ramos do item de `/possibilidades`**
- **Found during:** Task 1
- **Issue:** O plano pedia o campo "por item com estrutura". Os itens sem estrutura (vencimento que não montou, vencimento recusado pela tool) ficariam sem a chave, e o front comenta explicitamente que "a lista aqui é uniforme justamente para não precisar testar existência de chave".
- **Fix:** Os três ramos carregam a chave; dois deles com `None`. Teste cobre o item sem estrutura.
- **Committed in:** `1dda475`

---

**Total deviations:** 4 (2 missing-critical, 1 blocking, 1 consistência). **Nenhuma de escopo.** Todas tornam a entrega do plano correta em vez de maior.

## Critérios de aceite — leitura literal × intenção

Os critérios deste plano não trazem `grep -c` (ao contrário dos planos 01–04, onde a contagem por linha enganou quatro executores). Um ponto pedia leitura de intenção:

- **"`razaoGanhoPerda` presente em `/proposta`"** — presente quando há UMA estrutura, `null` quando há duas ou zero. A alternativa literal (sempre presente com ≥1 estrutura) publicaria uma razão sem dizer de qual das estruturas ela é, que é o defeito que o próprio código já evitava para o `emReais`. Cumpri o guardrail.

## Issues Encontradas

- **`TestClient` com `raise_server_exceptions=True` (default) propaga a exceção em vez de devolver 500.** O RED de F-02 e F-03 apareceu como `RuntimeError`/`httpx.ReadTimeout` estourando dentro do teste, e não como `assert 500 == 503`. É o mesmo caminho: a Starlette chama o handler global, devolve o 500 ao cliente real e **re-levanta** para o cliente de teste. A prova é válida e, depois da correção, os mesmos testes passam a receber 503.
- Nenhuma outra. A suíte não teve falha intermitente.

## Validação (fora do sandbox)

**Suíte canônica — `bash scripts/executar.sh --testes`, exit 0:**

```
== Suítes do backend ==
........................................................................ [  2%]
[...]
2424 passed, 5 skipped, 609 warnings in 49.73s

== Suítes do front (web/tests/*.mjs) ==
  [OK] web/tests/test_opcoes_analisar_ui.mjs
  [OK] web/tests/test_opcoes_criar_setup_ui.mjs
  [OK] web/tests/test_opcoes_mcp_aba_ui.mjs
  [...]
  [OK] web/tests/test_wiring_deps.mjs
```

- **129 arquivos `.mjs [OK]`** (contagem programática: `grep -c "\[OK\]"` = 129), **exit 0**.
- **Backend: 2424 passed, 5 skipped.** Baseline era `2407 passed, 5 skipped`: **+17**, exatamente os 17 testes novos (14 de F-01, 2 de F-02, 1 de F-03). **Zero regressão.**
- As duas ocorrências de "FALHA" na saída são nomes de teste (`test_scan_rankeia_tolera_falha_e_tem_disclaimer`, `test_fase3_custos_falha_brapi.mjs`), não falhas.

**Build do front — `cd web && npx vite build`:**

```
✓ built in 1.65s
PWA v0.21.2
precache  23 entries (918.74 KiB)
```

## F-04 — INTOCADO, pendente de decisão do Alex

Verificado programaticamente sobre o diff dos três commits (`git diff 948a588..HEAD -- server/app/`):

- `server/app/mcp_client.py`: **0 linhas alteradas** (o cache de erro / `_cache_put` não foi tocado).
- Nenhuma linha do diff casa `cap.consome`, `_cache_put` ou `custo`.
- `with _cap_check(` continua com 11 usos + 1 na docstring (12 linhas), os mesmos de antes: **nenhum custo declarado de rota mudou.**

A decisão segue aberta e é de produto, não de código — são três caminhos (cobrar a viagem que a tool recusou; cachear a recusa com TTL curto; teto de falhas por requisição em `/possibilidades`). O `24-VERIFICATION.md` recomenda decidir **antes** de o 24-05 publicar, porque depois de no ar o custo do erro é da base inteira.

## Known Stubs

Nenhum. Nenhum valor fixo, nenhum componente sem fonte de dado, nenhum `TODO`/`FIXME` introduzido.

## O que continua SEM prova

Inalterado em relação ao `24-VERIFICATION.md` — este plano não abriu nem fechou nenhuma dessas frentes:

1. Nenhuma chamada ao serviço MCP real (`MCP_CLIENT_SECRET` fora do ambiente, D-24.7). A razão G/P é calculada sobre `max_gain`/`max_loss` que **só a fixture** forneceu.
2. Nenhuma chamada de LLM real. O 503 novo foi exercitado com exceção injetada, não com um modelo que de fato tenha estourado 60 s.
3. Nada em aparelho. A linha nova da razão (e o bloco de motivo com quebra) não foi vista em 375 px.

## Next Phase Readiness

- Os três achados de escopo do `24-VERIFICATION.md` estão fechados, cada um com guardião que os trava.
- **Bloqueadores para o 24-05 (publicação):** (a) a decisão do Alex sobre F-04; (b) o primeiro teste ao vivo que a verificação nomeia — `pytest tests/test_opcoes_paridade_mcp.py::test_paridade_viva` com `MCP_CLIENT_SECRET` no ambiente.
- A Fase 4 do `PLANO-aba-opcoes.md` (veredito) herda `_razao_ganho_perda` pronto: era ela que precisaria da razão como fato determinístico para o critério de 1,5:1 (§3.4), e agora não precisa recalculá-la.

---
*Phase: 24-opcoes-mcp-analise-e-setups*
*Completed: 2026-09-11*

## Self-Check: PASSED

- 6 arquivos modificados e o SUMMARY existem em disco.
- Os 3 commits (`1dda475`, `434afb0`, `477e27e`) existem no histórico.
- `def _razao_ganho_perda` presente 1×; `razaoGanhoPerda` renderizado 2× em `OpcoesScreen.jsx` (uma seção cada).
