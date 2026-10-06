---
phase: 48-opcoes-caminho-b
plan: 02
subsystem: didatica-opcoes
tags: [conceitos, kb, setores, opcoes, glossario]
requires: []
provides:
  - "CONCEITOS['opc-premio'] e ['opc-perda-maxima'] com números do caso"
  - "conceitos.TEXTO_OPC (fonte única do texto genérico, reusada por kb.py)"
  - "SETORES opc_premio / opc_perda_maxima (allowlist do /api/assistente)"
  - "verbetes KB opc-premio e opc-perda-maxima"
affects: [48-05, front tela 3 (gráfico, legenda, frase de risco)]
tech-stack:
  patterns: ["parágrafo-dict por modo em montar() (aditivo)"]
key-files:
  created: [server/tests/test_conceitos_opcoes_escada.py]
  modified:
    - server/app/conceitos.py
    - server/app/kb.py
    - server/tests/test_setores.py
    - server/tests/test_conceitos.py
    - server/tests/test_guardrail_imperativo.py
    - server/tests/test_kb_catalogo.py
requirements-completed: [OPC-08]
duration: ~15min
completed: 2026-10-05
---

# Phase 48 Plan 02: termos clicáveis onda 1 (prêmio, perda máxima) Summary

Conceitos `opc-premio` e `opc-perda-maxima` com números do caso (ticker, strike, prêmio, total, lote, vencimento, piso, perda) e verbetes KB com o mesmo texto (`conceitos.TEXTO_OPC`), nos dois modos; setores registrados na allowlist do assistente.

## Commits
- f366b764 feat(48-02): conceitos + TEXTO_OPC + setores + guardião
- 806a2286 feat(48-02): verbetes KB
- 33af08c7 test(48-02): contagens do catálogo KB

## Decisões
- Parágrafo `{"educacional","operador"}` resolvido por `_por_modo` em `montar()`; str e tupla intactos (teste congela gatilho/stop/liquidez-opcao).
- Valores monetários saem de `_num` já com "R$"; o texto dos parágrafos não prefixa "R$" (o plano sugeria prefixo; teria dado "R$ R$").
- `veja` dos conceitos vazio (ids KB não podem entrar ali); o encadeamento fica no `veja` dos verbetes KB.

## Deviations from Plan

**1. [Rule 3 - Bloqueio] Guardiões que não toleravam parágrafo-dict**
- `test_guardrail_imperativo.py` (join do catálogo) e `test_conceitos.py` (guardião estático de `{campo}`) assumiam str/tupla; passaram a achatar os dois textos do dict (varredura mais completa, não menos). Nota de Fase 48 nos comentários.

**2. [Rule 3 - Bloqueio] Contagens do catálogo KB**
- `test_kb_catalogo.py`: 89 -> 91 e 80 -> 82 (+2 verbetes manuais, independentes da chave de didática). Reversão deliberada do guardião, com nota.

**3. Formatação**: `qtd`, `strike`, `premio`, `premioTotal`, `piso`, `perdaTotal`, `perdaAcao` adicionados a `_FORMATADORES` (`_num` / `_volume_milhar`).

## Verificação
`pytest -k "kb or conceito or assistente or didatica or guardrail or glossario or setores or pet"`: 274 passed, 1 xfailed. Front não tocado (sem vite build). Suíte canônica fica com o orquestrador.

## Known Stubs
Nenhum.

## Self-Check: PASSED
Arquivos e commits f366b764, 806a2286, 33af08c7 existem; STATE.md/ROADMAP.md intactos.
