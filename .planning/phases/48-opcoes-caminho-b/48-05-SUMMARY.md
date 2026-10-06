---
phase: 48-opcoes-caminho-b
plan: 05
subsystem: didatica-opcoes
tags: [conceitos, kb, setores, opcoes, glossario]
requires: [48-02]
provides:
  - "CONCEITOS['opc-put-protetora'] e ['opc-collar'] com números do caso (collar com estado custa/recebe/zero)"
  - "TEXTO_OPC onda 2 (fonte única, reusada por kb.py)"
  - "SETORES opc_put_protetora / opc_collar (allowlist do /api/assistente)"
  - "verbetes KB opc-put-protetora e opc-collar; veja de opc-premio/opc-perda-maxima aponta para eles"
key-files:
  modified:
    - server/app/conceitos.py
    - server/app/kb.py
    - server/tests/test_conceitos_opcoes_escada.py
    - server/tests/test_setores.py
    - server/tests/test_kb_catalogo.py
requirements-completed: [OPC-09]
completed: 2026-10-05
---

# Phase 48 Plan 05: termos onda 2 (put protetora, collar) Summary

Put protetora e collar clicáveis (tela 2 e 4) com números do caso e verbete no glossário, mesmo texto (`conceitos.TEXTO_OPC`), nos dois modos. Texto sem promessa: "limita a perda, não a queda"; "não é proteção total".

## Commits
- 20f15b23 feat(48-05): conceitos + setores + guardião
- 097b042b feat(48-05): verbetes KB + contagens do catálogo

## Setores (nota do 48-04)
O plano cobria o registro de `opc_put_protetora` e `opc_collar` em `SETORES`; feito. Novo guardião `test_termos_dos_objetivos_com_setor_existem_em_setores` assegura que todo `setor` dos `termos` de `opcoes_escada.objetivos()` está em `conceitos.setores()` e todo `kb` existe no catálogo (nos dois modos). Teste de setores da onda 2 em `test_setores.py`.

## Decisões / desvios
- `liquido` do collar formata sem sinal (`_num_abs`): o sentido vem do `estado` (custa/recebe/zero) no texto, evitando "R$ -75,00 ... custo". Texto não diz "por ação" pois o plano não define se `liquido` é por ação ou total; o chamador (plano de front/API) deve passar o mesmo critério do motor.
- [Rule 3] `test_kb_catalogo.py`: 91 -> 93 e 82 -> 84 (+2 verbetes manuais), reversão deliberada do guardião com nota.
- `veja` dos CONCEITOS segue vazio (como no 48-02); o encadeamento mora no `veja` dos verbetes KB, atualizado.

## Limitações conhecidas
- `_num` não usa separador de milhar ("R$ 1100,00"), comportamento pré-existente, não alterado.

## Verificação
`pytest -k "kb or conceito or setores or guardrail or glossario or didatica or assistente or pet"`: 282 passed, 1 xfailed. Front não tocado. Suíte canônica fica com o orquestrador.

## Known Stubs
Nenhum.

## Self-Check: PASSED
Commits 20f15b23 e 097b042b existem; STATE.md/ROADMAP.md não tocados.
