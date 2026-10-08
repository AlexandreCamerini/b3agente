---
phase: 47-didatica-expectativa-matematica-x-taxa-de-acerto
verified: 2026-10-07T00:00:00Z
status: human_needed
score: 4/4 must-haves verified (código); 1 item visual pendente
gaps: []
human_verification:
  - test: "Estudo, AtivoCard com histórico medido: tocar na cláusula sublinhada 'sinal técnico e histórico medido são coisas diferentes'"
    expected: "Abre a folha 'Expectativa matemática × taxa de acerto' (não 'A confluência') com n, janela e resultado médio (R) do card; estado inelegível mostra o parágrafo 'ganhos não cobriram as perdas' com sinal −; insuficiente/nunca medido mostra 'Não há dados suficientes para concluir.' e nenhum número"
    why_human: "Renderização, gesto de toque e folha só se confirmam na tela"
  - test: "Modo Operador: mesma linha de elegibilidade"
    expected: "Sem cláusula tocável (só o fato curto)"
    why_human: "Comportamento visual por modo"
  - test: "VoiceOver no botão da cláusula"
    expected: "Lê 'O que é a expectativa matemática?'"
    why_human: "Leitor de tela real"
  - test: "Anel/linha de chips do card"
    expected: "Continua abrindo 'A confluência'"
    why_human: "Regressão visual do destino que não deveria mudar"
---

# Fase 47 — Verificação

**Objetivo:** o tema obrigatório do CLAUDE.md (expectativa matemática × taxa de acerto) ganha verbete e o microtexto passa a abri-lo.
**Status:** human_needed (todas as verdades verificadas no código; falta conferir na tela).
**Re-verificação:** não. Evidência de suíte fornecida pelo orquestrador (executar.sh --testes rc=0, 3458 passed; vite build rc=0), não reexecutada.

## Verdades observáveis

| # | Verdade | Status | Evidência |
|---|---------|--------|-----------|
| 1 | Conceito, verbete KB e setor `expectativa-matematica` existem, com o MESMO texto | VERIFICADO | `server/app/conceitos.py:114-165` (`TEXTO_EXPECTATIVA`, dois modos, ilustração gerada de `_ILUSTRACAO_EXPECTATIVA`); conceito em `conceitos.py:579-613` usa `TEXTO_EXPECTATIVA` em `oQueE`; setor `"expectativa": "expectativa-matematica"` em `conceitos.py:816`; verbete em `server/app/kb.py:1103-1115` com `"texto": conceitos.TEXTO_EXPECTATIVA` (mesmo objeto, identidade). |
| 2 | Rótulo da cláusula nasce em `skill_ref.py` com espelho byte a byte em `copy.js` | VERIFICADO | `server/app/skill_ref.py:535` `RECONCILIACAO_POR_QUE_IMPORTA_ROTULO = "a expectativa matemática"`; `web/src/copy.js:2750` mesma string. Guardião lê o .py como texto e compara (`web/tests/test_reconciliacao_elegibilidade.mjs:213-218`); `server/tests/test_skill_ref.py:297-302`. |
| 3 | `HistoricoPill` abre `expectativa-matematica` com os números do caso, sem número inventado nem promessa | VERIFICADO (visual pendente) | `web/src/App.jsx:7902` `dadosExpectativa = {...dados, n, janela, expR, estado}` vindos de `historico` (null permanece null; `conceitos._valores` descarta None, teste `test_dado_invalido_derruba_paragrafo_nunca_vira_zero`); `App.jsx:7918` `setorId="expectativa"` atrás do gate `!operador`; rótulo vem de `reconciliacaoPorQueImportaRotulo` (import em `App.jsx:9`), consumido em `web/src/entendimento.jsx:105` (`aria-label "O que é " + rotulo + "?"`). Ilustração +0,6R / −0,5R é gerada por fórmula, rotulada "Ilustração, não resultado do seu histórico" e acompanhada de "não é previsão nem promessa" (`conceitos.py:148-155`). `setorId="analise"` preservado fora do HistoricoPill (guardião `test_reconciliacao_elegibilidade.mjs:211`). |
| 4 | Guardiões existem e travam o prometido | VERIFICADO | `server/tests/test_conceito_expectativa.py` (14 testes: números ancorados, sinal U+2212, estados sem dado usam a frase fixa, ilustração bate com a fórmula e é rotulada, varredura sem "100%"/"garant"/"lucro certo" em todos os modos×estados, verbete KB `texto is TEXTO_EXPECTATIVA`, `veja` existente, busca); `server/tests/test_setores.py` e `test_kb_catalogo.py` (contagens 93→94, 84→85 com nota datada); `test_skill_ref.py:297`; `test_reconciliacao_elegibilidade.mjs:197-225` (gate Operador antes do setor, `dados={dadosExpectativa}` por regex, cadeia App.jsx→SETORES→CONCEITOS→kb, sem literal do rótulo em App.jsx). |

## Requisitos

| Requisito | Evidência | Status |
|-----------|-----------|--------|
| DIDA-01 (verbete na KB/conceitos, sem promessa de rentabilidade) | `conceitos.py:114-165,579`; `kb.py:1103-1115`; `test_conceito_expectativa.py::test_linguagem_sem_promessa`, `test_verbete_kb_mesma_fonte_do_conceito` | SATISFEITO |
| DIDA-02 (cláusula abre o verbete, não `confluencia`; paridade skill_ref↔copy.js) | `skill_ref.py:535`, `copy.js:2750`, `App.jsx:7918`; guardiões acima | SATISFEITO (confirmação visual pendente) |

Sem requisitos órfãos (REQUIREMENTS.md mapeia só DIDA-01..02 à Fase 47). Obs.: os checkboxes de DIDA-01/02 em REQUIREMENTS.md e da Fase 47 no ROADMAP seguem `[ ]` — fechamento de bookkeeping a cargo do orquestrador.

## Princípios do CLAUDE.md

- 5 (determinístico): texto fixo + números do histórico medido pelo motor; ilustração por constantes; nenhuma chamada a IA.
- 6/8 (sem promessa): texto afirma "Resultado médio passado não é previsão nem promessa"; parágrafo "elegível" diz "a próxima pode perder, e os custos reduzem a vantagem"; varredura de termos proibidos travada em teste.
- Caso sem dado: "Não há dados suficientes para concluir." (frase canônica) e nenhum número; `null` nunca vira 0.
- "15 anos" no estado `aposentado` não é número novo: reaproveita o dado já existente em `skill_ref.py:512` (ADR-016).

## Anti-padrões

Sem TBD/FIXME/XXX introduzidos nos arquivos citados (inspeção dirigida); nenhum stub. Paridade `defaults.py`↔`catalog.js` e `deviceStore`↔`serverStore` não tocadas.

## Gaps

Nenhum.

## Humano precisa conferir

1. Estudo: tocar na cláusula sublinhada e ver a folha "Expectativa matemática × taxa de acerto" (não "A confluência") com n/janela/R do card, nos estados elegível, inelegível e insuficiente/nunca medido.
2. Operador: sem cláusula tocável.
3. VoiceOver: "O que é a expectativa matemática?".
4. Anel/linha de chips ainda abre "A confluência".

_Verificador: Claude (gsd-verifier)_
