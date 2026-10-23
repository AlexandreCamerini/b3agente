---
phase: quick-261023-msp
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - server/app/setups.py
  - server/tests/test_marcos_plano.py
  - server/app/skill_ref.py
  - server/app/store.py
  - server/app/agent.py
  - server/app/main.py
  - web/src/App.jsx
  - web/src/copy.js
  - web/src/persistence.js
  - web/tests/test_vocabulario_espelho.mjs (ou test_marcos_espelho.mjs — o que hoje trava MARCOS_PLANO)
  - web/tests/test_copy_theme.mjs
autonomous: true
requirements: [QUICK-261023-MSP-0..7]
---

# Quick 261023-msp — compra não preenche stop/alvo + pendências pequenas da Fase 50

## Contexto (debug, já diagnosticado pelo orquestrador)

Sintoma (Alex, 2026-10-23): ao comprar uma ação o app roda a análise (N3, StopAlvoModal
aberto por `confirmBuy` → `runStopAlvoFor`) mas STOP e ALVO ficam "—".

Causa: `setups.marcos_da_posicao` aplicava a regra D-02 de ENTRADA (resistência antes de
1,5R → recusa "Teto próximo demais") também à posição JÁ aberta. Em produção
(`POST /api/marcos/{t}`, 2026-10-23) 11 de 11 ativos líquidos (PETR4, VALE3, ITUB4, BBAS3,
WEGE3, MGLU3, ABEV3, B3SA3, RENT3, PRIO3, SUZB3) devolviam `valido:false`. O modal mostra
`m.valido ? m.stop : "—"`. Contraria D-12 ("R:R baixo é parecer, não veto").

## Tarefa 0 — JÁ APLICADA no working tree (não commitada): commitar como está

- `server/app/setups.py`: `_alvo_motor(..., exigir_rr=True)`; `_marcos_de(..., exigir_rr=True)`;
  `_marcos_da_posicao_base` passa `exigir_rr=False` e, com R:R < `RR_MINIMO`, acrescenta
  `m["parecer"]` (texto PT-BR do motor). Motivo do WR-01 sem a cláusula de R:R.
- `server/tests/test_marcos_plano.py`: 3 guardiões novos (posição com teto próximo → válido +
  parecer; R:R ok → sem parecer; ENTRADA segue recusando).
- Commit: `fix(quick-261023-msp): marcos da posição não recusam por R:R baixo (parecer, D-12)`.

## Tarefa 1 — modal mostra o parecer

`web/src/App.jsx` `StopAlvoModal` (~4169): quando `m && m.valido && m.parecer`, mostrar
`m.parecer` num aviso igual ao bloco `aguardar` (borda tracejada), logo abaixo da linha de R:R.
Aceite: com `/api/marcos` devolvendo parecer, STOP/ALVO preenchidos, aviso visível, Aplicar
funciona.

## Tarefa 2 — IN-01: literais para o vocabulário por modo

Ver `.planning/phases/50-*/50-REVIEW.md` IN-01. Criar chaves em `skill_ref.MARCOS_PLANO`
(educacional e operador) espelhadas byte a byte em `copy.js` (`marcosPlanoTxt`):
`modal_calculando` ("CALCULANDO…"), `modal_calculo_motor` ("CÁLCULO DO MOTOR"),
`modal_parecer_aguardar` ("PARECER: AGUARDAR"), `modal_ia_gauge` ("Explicação com IA") e
os steps do gauge se couber, `modal_marcos_calculando` e `modal_marcos_indisponiveis`
(recusas das linhas ~4206/4209), `modal_decisao_sua` ("A decisão é sua — isto não é
recomendação de investimento."), `acao_redefinir` ("Redefinir", ~5574), `regua_stop` /
`regua_entrada` (legendas "STOP"/"ENTRADA" da régua, ~1591). Texto pode ser igual nos dois
modos se não houver diferença de voz — o que importa é sair do JSX. Travar no teste de
espelho que já cobre MARCOS_PLANO.

## Tarefa 3 — IN-05

- `PlanoOperacionalBloco` (App.jsx ~1557): quando `plano.decisao !== "COMPRAR"` esconder a linha
  `bloco_breakeven` e usar rótulo de stop sem "folga de ATR" (chave existente antiga, ou nova
  `bloco_stop_legado` nos dois lados do espelho).
- `server/app/agent.py` `_avaliar_entradas` (~806): `modo_txt = "operador" if app_mode == "operador" else "educacional"`.

## Tarefa 4 — IN-06(c): toggle de gestão sem efeito

`StopAlvoModal`: `gestaoVisivel` também exige `!isNative || hasSession()` (imports já existem
no topo de App.jsx). Gestão automática só roda no servidor (D-14).

## Tarefa 5 — `stopInicial` ao somar lote (WR-03 item c)

`store.buy` e espelho `deviceStore.buy` (persistence.js ~1883): quando a posição EXISTE e os
marcos do motor NÃO são aplicados (usuário mantém marcos próprios ou não há marcos), o PM
muda e o `stopInicial` antigo deixa o 1R errado. Aplicar a MESMA regra de reancoragem de
`set_position(manual=True)` (store.py ~621-660; espelho em `deviceStore.putPosition`):
`stopInicial = stop` se `stop` existe e `stop < novo avg`, senão remover `stopInicial`.
Reusar o helper se existir; senão extrair um pequeno helper e chamar nos dois lugares.
Guardião pytest + caso no teste .mjs de marcos dos stores (paridade).

## Tarefa 6 — `set_option_position` sem validação numérica

`store.set_option_position` (~1113): usar `_marco_num` para stop/alvo (ValueError PT-BR);
conferir que a rota `PUT` em main.py (~3376) converte ValueError em 400 com a mensagem (como a
de ação). Espelho em `deviceStore.putOptionPosition` (persistence.js ~1394) se ele grava local
sem validar. Guardião pytest: `stop="abc"` → 400 PT-BR; `stop=True` → 400.

## Tarefa 7 — `notaStopAlvo` órfã

Remover `notaStopAlvo` de `copy.js` (linhas ~540 e ~2000) — não há leitor. Atualizar o
comentário/assert de `web/tests/test_copy_theme.mjs:210` se ele referir a chave (nota, não
apagar o guardião). Não existe em skill_ref.

## Fora do escopo

Sizing sobre patrimônio (IN-06b — decisão de produto), D-19, publicação/deploy.

## Regras

- Guardrails do CLAUDE.md: marcos só do motor; paridade skill_ref ↔ copy.js e
  deviceStore ↔ serverStore; guardiões não se apagam (atualizar com nota).
- `App.jsx` nunca lido inteiro: Grep + Read com offset/limit.
- Rodar só os testes tocados: `cd server && .venv/bin/python -m pytest -q tests/test_marcos_plano.py tests/test_skill_ref.py <novos>`
  e `node web/tests/<arquivo>.mjs` dos tocados; `cd web && npx vite build` ao final.
  NÃO rodar a suíte canônica inteira (o orquestrador roda).
- Um commit atômico por tarefa, mensagem `fix|refactor(quick-261023-msp): ...`, terminando com
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Não commitar PLAN/SUMMARY/STATE (o orquestrador faz). Não usar git stash. Não usar `gsd-sdk state.*`.
- Escrever `261023-msp-SUMMARY.md` neste diretório: o que mudou por tarefa, commits, testes rodados.
