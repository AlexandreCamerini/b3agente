---
phase: 46-carteira-v6-card-de-posi-o-com-modos-estudo-e-operador
verified: 2026-10-02
status: passed
score: 7/7 requisitos CART6 verificados
gaps: []
deferred:
  - truth: "G-07 nome da empresa sem fallback"
    addressed_in: "aberto, fora do fechamento da 46 (registrado em 46-UAT.md)"
  - truth: "G-08 total suspenso sem causa explicada"
    addressed_in: "aberto, fora do fechamento da 46 (registrado em 46-UAT.md)"
---

# Fase 46 — Verificação

Goal: card de posição v6 (fechado com um visual/um estado, flip Ação/Opções, camada didática por modo), todo cálculo no backend.

## Evidência por requisito

| Req | Status | Evidência |
|---|---|---|
| CART6-01 | OK | `LinhaEstadoV6`/`estadoPrincipalV6`/`estruturaCard.js` (um estado, D-13); `test_cartao_v6_fechado.mjs` e `test_cartao_v6_logica.mjs` passam. G-01..G-06 do UAT fechados (nowrap/NBSP, chips, linhas rótulo/valor, régua ancorada). Total suspenso = "—" + chip (App.jsx ~4912); guardião proíbe "Parcial"/"indisp." |
| CART6-02 | OK | `estruturaCard.js:162-165` (170+170 ms; reduzido = 0); keyframes flip em App.jsx:5038; `test_cartao_v6_aberto.mjs` passa |
| CART6-03 | OK | `SimuladorEstudo` (App.jsx:5223); `test_cartao_v6_camadas.mjs` passa |
| CART6-04 | OK | PayoffChart sem texto + grade 3×2 com conta; `test_cartao_v6_camadas.mjs` passa; pytest `test_cartao_cenarios.py` checa BE/ganho/perda/conta |
| CART6-05 | OK | `server/app/cartao_posicao.py` (494 linhas) + `POST /api/carteira/leitura` (main.py:4339); UGPA3 (BE 38,01; +4.240; −38.010) e CXSE3 (BE 19,81; +1.210) em pytest; pytest `test_cartao_posicao.py`, `test_cartao_cenarios.py`, `test_carteira_leitura_rota.py` passam. Nenhum `optionsCalc` em `web/src` |
| CART6-06 | OK | `test_kb_verbetes_v6.py` cobre opc-lastro, opc-call-coberta, opc-teto, opc-piso, opc-equilibrio, mkt-preco-medio; 78 passed (com skill_ref, kb_espelho, leitura_rota) |
| CART6-07 | OK | `skill_ref.CARTAO_POSICAO`/`CARTAO_DIDATICA` ↔ `copy.js` (espelho); `test_skill_ref.py` e `test_cartao_posicao_espelho.mjs` verdes |

## Invariantes
- Cálculo só no backend: sem `optionsCalc`; guardião de aritmética em `test_cartao_v6_transversal.mjs` passa.
- Total nunca estimado / parcial = "—": `suspenso: total === null` em `estruturaCard.js:390,403`.
- Paridade skill_ref↔copy.js: verde. Paridade deviceStore↔serverStore: `carteiraLeitura` em ambos (persistence.js:278, 1347) e `test_carteira_leitura_paridade.mjs` passa.
- Cores só via `cartaoV6Cores.js` (`varsCartaoV6` no wrapper do card; guardião de "sem hex literal" passa).
- Sem TBD/FIXME/XXX nos arquivos da fase inspecionados.

## Execução (pontual, nesta verificação)
7 guardiões `web/tests/test_cartao*_*.mjs`/`test_carteira_leitura_paridade.mjs` OK; pytest 28 + 78 passed; `npx vite build` OK. Suíte canônica completa não reexecutada (orquestrador: 3211 pytest + .mjs verdes).

## Itens abertos (fora do escopo, apenas registrados)
- G-07 e G-08 constam em `46-UAT.md` com status `open`. Não constam em STATE.md/ROADMAP.md (não editados por esta verificação).
- Ressalva da aba Opções (executar estrutura): não reproduzida, fora da 46.

## Observações (WARNING administrativo, não bloqueia)
- `ROADMAP.md` ainda mostra `[ ]` nos 12 planos e a linha da Fase 46, e `REQUIREMENTS.md` mostra CART6-01..07 "Pending"; devem ser marcados pelo orquestrador no fechamento.
- Checkpoint humano no iPhone (46-12): aprovado com ressalvas em 2026-10-02 (informado pelo orquestrador); não verificável por grep.

## Gaps
Nenhum.
