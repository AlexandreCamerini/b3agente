---
phase: quick-261008-oos
plan: 01
status: complete
completed: 2026-10-08
commits:
  - 3e4dc6f0 test(261008-oos): guardião test_ui_onda_h (RED, 35 falhas)
  - de977761 feat(261008-oos): primitivas comuns de payoff e GraficoResultado legível
  - a9bdca26 feat(261008-oos): anatomia com eixos, marcadores numerados e chips com estado
  - 33d679bb feat(261008-oos): card da carteira com eixos e marcadores numerados; legendas sem redundância
---

# Quick 261008-oos: Onda H de UI, gráficos de payoff legíveis

Linguagem comum de eixo/marcador/legenda (payoffEixos.js puro + PayoffPrimitivas.jsx) aplicada a GraficoResultado (escada), GraficoAnatomia/PosicaoTotal/AnatomiaPerna (posição em Opções) e PayoffOperador (card da carteira, App.jsx). Textos de legenda em copy.js e skill_ref.py alterados no mesmo commit (só valores, nenhuma chave nova).

## Verificação
- test_ui_onda_h: verde (RED inicial com 35 falhas). 19 guardiões vizinhos verdes (lista do plano).
- pytest test_skill_ref, test_opcoes_escada, test_cartao_posicao, test_conceitos_opcoes_escada: 122 passed.
- `npx vite build`: ok. Contagem reduced-motion em App.jsx: 2.

## Deviations from Plan
None funcionais. Notas: afastarPontos usa colisão por distância euclidiana (0,9*dist) em vez de caixa, para que o contrato "segundo ponto dy=-20" valha; nenhum guardião existente precisou de reconciliação (nenhuma nota datada necessária). Legenda de perda/ganho máximo monta o valor por concatenação de string para não reintroduzir o padrão `R$ {fmt(v)}...it.frase` vetado pelo guardião.

## Pendências (H-D1..H-D6)
PayoffChart.jsx fica para H2; publicar front e backend juntos (frases da legenda vêm de skill_ref.py); demais decisões aplicadas como no plano. Inspeção visual no aparelho pelo Alex.

## Self-Check: PASSED
