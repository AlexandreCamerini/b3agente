---
quick_id: 260908-ldg
status: complete
date: 2026-09-08
files_modified:
  - server/app/options_quant.py
  - server/app/opcoes_motor.py
  - server/app/opcoes_lastreadas.py
  - server/app/skill_ref.py
  - server/app/options_api.py
  - server/app/main.py
  - server/app/conceitos.py
  - server/app/kb.py (não listado no plano — Rule 2, ver Deviations)
  - server/app/options_provider_mock.py
  - server/tests/test_faixas_liquidez.py (novo)
  - server/tests/test_gate_liquidez_rotas.py (novo)
  - server/tests/test_conceito_liquidez_opcao.py (novo)
  - server/tests/test_opcoes_motor.py
  - server/tests/test_opcoes_lastreadas_proposta.py
  - server/tests/test_opcoes_collar.py
  - server/tests/test_liquidity_score_mydata.py
  - web/src/finance.js
  - web/src/App.jsx
  - web/src/copy.js
  - web/src/persistence.js
  - web/tests/test_faixa_liquidez_ui.mjs (novo)
  - web/tests/test_carteira_opcoes_tira.mjs
  - web/tests/test_opcoes_proposta_ui.mjs
  - web/tests/test_opcoes_collar_ui.mjs
---

# Summary — 260908-ldg

## O que foi entregue

Corte binário de liquidez de opção (score ≥ 40 existe / < 40 não existe)
trocado pelas três faixas que a UI já nomeava (NEGOCIÁVEL ≥55 / DIFÍCIL
30-54 / SEM MERCADO <30), com comportamento distinto em descoberta, seleção
do motor e execução do Modo Operador. Três commits atômicos, um por task do
plano:

1. `03c7e8a feat: régua de liquidez em três faixas, duas passadas e liquidez.aviso`
2. `a34a22d feat: gate de descoberta em três faixas, recusas do servidor e verbete didático`
3. `de47a2a feat: consentimento de liquidez no front, paridade dos stores, estado vazio e chip→verbete`

## A régua

`server/app/options_quant.py` — fonte ÚNICA no repo:

```python
LIQUIDEZ_NEGOCIAVEL = 55
LIQUIDEZ_DIFICIL = 30
FAIXA_NEGOCIAVEL, FAIXA_DIFICIL, FAIXA_SEM_MERCADO = "NEGOCIÁVEL", "DIFÍCIL", "SEM MERCADO"

def faixa_de_liquidez(score) -> str: ...  # None/negativo/não-numérico → SEM MERCADO, nunca exceção
```

`liquidity_score` (a fórmula, recalibrada na quick anterior 260908-dnl) NÃO
mudou — `git diff 3c49f43 -- server/app/options_quant.py` só mostra adições
ao redor da função (docstring + as constantes/função acima), zero linha do
corpo alterada. Espelho declarado no front: `web/src/finance.js` exporta
`FAIXA_NEGOCIAVEL_MIN`/`FAIXA_DIFICIL_MIN`/`faixaDeLiquidez`, com paridade
byte-a-byte testada em `test_faixa_liquidez_ui.mjs` (lê os dois
arquivos-fonte).

## Onde a faixa passou a mudar comportamento

| Ponto | Antes | Depois |
|---|---|---|
| `opcoes_motor.rastrear()` | corte único `LIQUIDEZ_MINIMA=40`, uma passada | duas passadas: NEGOCIÁVEL primeiro; só se vazio, DIFÍCIL. `LIQUIDEZ_MINIMA` apagada |
| `opcoes_lastreadas.propor/_propor_collar/proposta_fechar` | `liquidez: {score, label}` | `liquidez: {score, faixa, volume, spreadPct, aviso}` via `_bloco_liquidez`; `_label_liquidez` apagada |
| `GET /api/options/gate/{t}` | `liquida = score>=40 em algum contrato` | `liquida = faixa≠SEM MERCADO` (DIFÍCIL passa a "existir"); resposta ganha `faixa`/`melhorScore` em TODOS os ramos (inclusive degradado: `faixa=SEM MERCADO`, `melhorScore=null`, nunca `0.0`) |
| `POST /api/options/analyze` | bandeira de risco só < 40 | bandeira dispara quando faixa ≠ NEGOCIÁVEL, nomeando a faixa (decisão do orquestrador #1: alarga a transparência de 40-54, hoje silenciosa; reversível em 1 linha) |
| `POST /api/options/lastreada/abrir` e `/abrir-collar` | sem checagem de liquidez na execução | SEM MERCADO → 400 incondicional; DIFÍCIL sem `aceitaLiquidezDificil: true` (comparação `is not True`, não truthiness) → 400; NEGOCIÁVEL ignora a flag. Collar lê `p["liquidez"]["faixa"]` da proposta RE-DERIVADA, nunca do corpo |
| `POST /api/options/lastreada/fechar` | sem checagem | continua SEM checagem — assimetria deliberada (ver abaixo) |
| Front, dois handlers de aceite | put sem confirm nenhum; call com confirm só de estrutura | confirm de liquidez PRÓPRIO, disparado ANTES do de estrutura, texto `liq.aviso` verbatim; corpo carrega `aceitaLiquidezDificil` |
| `deviceStore.optionsAbrirLastreada` (ramo offline) | sem régua de liquidez nenhuma | mesma régua e mesmas mensagens do servidor, usando `contrato.liquidity` (nunca reimplementa `liquidity_score`) |
| Chip "liquidez" na proposta | `<span>` estático | `<button>` acessível que abre o verbete `liquidez-opcao` |
| `OportunidadesOpcoes` (tira, sem proposta) | 2 motivos (sem cobertura / sem setup) | 3º motivo: nenhuma posição líquida + alguma SEM MERCADO → `tiraOpcoesSemMercado`, nomeando a faixa |

## Assimetria deliberada abrir × fechar

`proposta_fechar` ganha os mesmos 5 campos de `liquidez`, mas NENHUMA rota
de fechamento (`/fechar` no backend, ramo offline no front) bloqueia por
faixa. Travar a saída de uma posição em contrato ruim prenderia o usuário
exatamente onde ele mais precisa sair. Comentário no código nos dois lados
(server e a régua do front) registrando a decisão — não é esquecimento.

## O texto do consentimento

`skill_ref.OPCOES_LASTREADAS["liquidez_dificil"]` nos dois modos +
`LIQUIDEZ_FRAGMENTOS` (factual, igual nos dois modos — mesmo precedente de
`HISTORICO["insuficiente"]`). Cobre os dois casos que "0" mentiria: sem
livro (`spreadPct is None` → "sem livro publicado", nunca "0%") e sem
negócio hoje com OI presente (caminho Yahoo → "sem negócio registrado
hoje", nunca "0 unidades"). Guardião de âncora AST (mesmo padrão de
`test_opcoes_collar_vocab.py`) prova que "sem livro publicado" e "poderia
não ser atendida" só existem em `skill_ref.py`, nos dois lados (backend
`server/app/*.py` e front `web/src/*.js*`).

## Verbete didático (D-09)

`conceitos.CONCEITOS["liquidez-opcao"]` — custo zero de LLM, três faixas
explicadas com os números do card (`{ticker}`, `{faixa}`, `{score}`,
`{volume}`, `{spreadPct}`), formatadores pt-BR novos (`_score_inteiro`,
`_volume_milhar`). Aberto pelo chip de liquidez via `A.abrirVerbete`.

## Prova contra dado real (rastrear() nas 20 cadeias reais de 2026-09-08, não versionadas)

| ticker | NEGOCIÁVEL | DIFÍCIL | SEM MERCADO | `rastrear` call (acima) | `rastrear` put (abaixo/igual) |
|---|---|---|---|---|---|
| ABEV3 | 10 | 4 | 1 | NEGOCIÁVEL 56.7 | NEGOCIÁVEL 64.3 |
| B3SA3 | 9 | 5 | 2 | NEGOCIÁVEL 75.0 | NEGOCIÁVEL 58.6 |
| BBAS3 | 42 | 18 | 6 | NEGOCIÁVEL 70.0 | NEGOCIÁVEL 70.0 |
| BBDC4 | 13 | 6 | 3 | NEGOCIÁVEL 70.0 | NEGOCIÁVEL 71.0 |
| BPAC11 | 13 | 14 | 1 | NEGOCIÁVEL 61.8 | NEGOCIÁVEL 57.3 |
| ELET3 | 0 | 0 | 0 | sem_contrato_liquido | sem_contrato_liquido |
| EQTL3 | 2 | 10 | 1 | DIFÍCIL 54.0 | NEGOCIÁVEL 55.7 |
| ITSA4 | 2 | 11 | 3 | NEGOCIÁVEL 59.3 | NEGOCIÁVEL 70.8 |
| ITUB4 | 32 | 13 | 2 | NEGOCIÁVEL 75.0 | NEGOCIÁVEL 68.1 |
| JBSS3 | 0 | 0 | 0 | sem_contrato_liquido | sem_contrato_liquido |
| PETR3 | 15 | 20 | 6 | NEGOCIÁVEL 57.1 | NEGOCIÁVEL 75.0 |
| PETR4 | 38 | 14 | 8 | NEGOCIÁVEL 70.0 | NEGOCIÁVEL 70.0 |
| PRIO3 | 32 | 19 | 18 | NEGOCIÁVEL 56.9 | NEGOCIÁVEL 75.0 |
| **RADL3** | **0** | **5** | 5 | **DIFÍCIL 50.9** | **DIFÍCIL 32.1** |
| RDOR3 | 6 | 22 | 12 | NEGOCIÁVEL 61.4 | NEGOCIÁVEL 55.4 |
| RENT3 | 4 | 6 | 3 | NEGOCIÁVEL 60.5 | NEGOCIÁVEL 60.9 |
| SUZB3 | 8 | 20 | 3 | NEGOCIÁVEL 63.6 | NEGOCIÁVEL 64.6 |
| VALE3 | 46 | 16 | 5 | NEGOCIÁVEL 70.0 | NEGOCIÁVEL 75.0 |
| VIVT3 | 2 | 2 | 0 | NEGOCIÁVEL 67.7 | sem_contrato_liquido |
| WEGE3 | 8 | 22 | 4 | NEGOCIÁVEL 65.2 | NEGOCIÁVEL 63.8 |
| **TOTAL** | **282** | **227** | **83** | | |

Soma 592, bate exato com o `measured_facts` do plano. RADL3 (0 NEGOCIÁVEL, 5
DIFÍCIL) prova a segunda passada: sem ela, `rastrear` devolveria `[]` para
os dois lados (o defeito que esta quick corrige) — com ela, os dois lados
selecionam um contrato DIFÍCIL real (score 50.9 e 32.1). ELET3/JBSS3 têm
cadeia vazia nos dois lados, como o plano já previa.

## Correções do plan-checker aplicadas (C1, C2)

- **C1** (fixture do collar, `test_opcoes_collar.py:373-395`): valor real
  medido é call 67,0 (NEGOCIÁVEL) / put 53,0 (DIFÍCIL) — não "85/71, ambas
  NEGOCIÁVEL" como uma versão anterior do plano dizia. A proposta do collar
  já sai DIFÍCIL hoje; o teste ganhou `assert faixa == "DIFÍCIL"` e vira o
  guardião natural do caso MISTO.
- **C2** (`test_liquidity_score_mydata.py`, `test_piso_sem_livro_e_mil_unidades`):
  1.000 unidades (`_s(1000) == 40,0`) e 900 (`_s(900) == 39,1`) caem em
  DIFÍCIL, não "aprovado sem aviso" — testes renomeados
  (`test_mil_unidades_sem_livro_e_piso_de_dificil_nao_de_negociavel`,
  `test_volume_500_com_um_lado_zerado_cai_em_dificil_nao_em_negociavel`) com
  nota datada; `CORTE=40` vira referência histórica, `PISO_DIFICIL=30`/
  `PISO_NEGOCIAVEL=55` são o critério vigente.

## Guardiões atualizados (12 da tabela do plano — nenhum apagado)

| # | Arquivo | Antes | Depois |
|---|---|---|---|
| G1 | `test_opcoes_lastreadas_proposta.py:309` | `{score, label}` | `{score, faixa, volume, spreadPct, aviso}`, com `faixa=="DIFÍCIL"` e `aviso` não-vazio (a fixture usada tem score 47,0) |
| G2 | `test_opcoes_motor.py::test_corte_de_liquidez_tem_fonte_unica` | provava ausência de `_LIQUIDEZ_MINIMA`/`_candidato_valido` | reforçado: também prova ausência de `_label_liquidez` e `opcoes_motor.LIQUIDEZ_MINIMA` |
| G3 | docstring de `test_opcoes_motor.py` | "liquidez >= 40 + strike extremo" | descreve as duas passadas |
| G4 | `test_liquidity_score_mydata.py:20` (`CORTE`) | citava dois consumidores agora apagados | vira referência histórica; `PISO_DIFICIL`/`PISO_NEGOCIAVEL` são o critério vigente |
| G5 | 2 testes do mesmo arquivo | nome "reprova" | renomeados + nota datada (C2 acima) |
| G6 | `test_rastrear_inclui_caso_real_mydata_sem_open_interest` | sem afirmar a faixa | `assert faixa_de_liquidez(...) == "DIFÍCIL"` explícito |
| G7 | `test_opcoes_collar.py:373-395` | `score == menor` só | + `faixa == "DIFÍCIL"` (C1 acima) |
| G8 | `test_opcoes_collar_vocab.py:74` | paridade de chaves | intocado — `liquidez_dificil` já entra nos dois modos, guardião continua verde |
| G9 | `test_copy_theme.mjs:27` | paridade estudo/operador | intocado — `tiraOpcoesSemMercado` já entra nos dois ramos |
| G10 | `test_carteira_opcoes_tira.mjs` | 6 chaves, assinatura sem `onVerbeteLiquidez` | 7 chaves + assinatura atualizada + distinção SemMercado≠SemCobertura≠SemSetup |
| G11 | `test_opcoes_proposta_ui.mjs` | assinatura sem `onVerbeteLiquidez`; sem asserção de ordem | assinatura atualizada + bloco novo de ordem dos 2 confirms nos 2 handlers |
| G12 | `test_opcoes_collar_ui.mjs` | só contava `confirmAbrirCollar(` == 1 | mantém a contagem (1, "frágil por construção" — o novo confirm usa `liq.`, não `cp.`) + asserção POSITIVA do 2º confirm e da ordem |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] `server/app/kb.py` precisou de entrada espelhada para "liquidez-opcao"**
- **Found during:** Task 2, ao rodar a suíte completa (não estava no `<verify>` da task, só apareceu no `pytest -q` geral)
- **Issue:** `test_kb_espelho.py::test_todo_conceito_tem_verbete_com_o_mesmo_id` é um guardião cross-cutting que exige que TODO id de `conceitos.CONCEITOS` tenha um verbete correspondente em `kb.py` (a KB deriva o texto de `conceitos.montar`). O plano não listava `kb.py` nos `files_modified` da Task 2 porque não sabia da existência desse guardião.
- **Fix:** `_FAMILIA_DO_CONCEITO["liquidez-opcao"] = "mercado_b3"` em `kb.py` — reusa a derivação genérica já existente (`_de_conceito`), sem prosa nova.
- **Files modified:** `server/app/kb.py`
- **Verification:** `test_kb_espelho.py` (5/5) e suíte completa (2110 passed, 1 skipped)
- **Committed in:** `a34a22d` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 2 — missing critical, guardião cross-cutting não mapeado pelo plano)
**Impact on plan:** Fix pequeno e cirúrgico (1 linha + comentário), zero mudança de comportamento do produto. Sem scope creep.

## Issues Encontradas (ambiente)

- Este worktree nasceu sem `server/.venv` nem `web/node_modules` (ambos
  gitignored, não recriados automaticamente em worktree novo). Symlinks
  locais para o clone principal (`server/.venv`, `web/node_modules`)
  criados só para RODAR a suíte — não commitados, não fazem parte do
  diff. `scripts/test.sh` já tem lógica própria para achar o venv do clone
  principal a partir de um worktree; os symlinks foram redundantes mas
  inofensivos.

## Validação

- `bash scripts/executar.sh --testes` — as DUAS suítes, exit 0:
  **2110 passed, 1 skipped** (backend; baseline 2064 + 46 novos) e
  **todos os 128 arquivos de `web/tests/*.mjs` OK** (zero falhas).
- `cd web && npx vite build` — build limpo, sem erro de sintaxe JSX (PWA
  gerado normalmente).
- `git diff 3c49f43 -- server/app/options_quant.py` restrito a adições ao
  redor de `liquidity_score` — corpo da função intocado.
- `grep -rn "LIQUIDEZ_MINIMA\|_label_liquidez" server/app` — vazio.
- Nenhum arquivo em `server/web_dist` tocado; `scripts/bump.sh` e
  `scripts/publicar-web.sh` NÃO foram executados nesta sessão.

## Pendência

**Publicação.** O front mudou (`web/src/App.jsx`, `copy.js`, `finance.js`,
`persistence.js`) mas a publicação (`scripts/bump.sh` + `publicar-web.sh`)
está FORA de escopo desta quick por decisão explícita do scope fence —
fica para um passo posterior, empilhada sobre o PR #31 que já aguardava
promoção (mencionado no STATE.md como pendência anterior a esta quick).
`server/web_dist` segue intocado.

**Deploy do backend.** Mesma situação de sempre nesta branch
(`v2/interacao-estrutural`): em produção, o gate de liquidez continua na
régua antiga (corte único 40) até a branch ser promovida — clique manual
no painel do Railway (auto-deploy desligado desde 2026-09-07, ver
`STAGING.md`).
