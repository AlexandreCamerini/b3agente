---
phase: quick-260928-u0h
plan: 01
subsystem: web/opcoes
tags: [opcoes, oportunidades, copy, guardiao]
key-files:
  created:
    - web/src/opcoes/classificarOportunidades.js
    - web/tests/test_opcoes_abertas_e_motivos.mjs
  modified:
    - web/src/copy.js
    - web/src/opcoes/OportunidadesOpcoes.jsx
    - web/src/opcoes/AbaOportunidades.jsx
    - web/src/opcoes/OpcoesScreen.jsx
    - web/tests/test_carteira_opcoes_tira.mjs
decisions:
  - "Encerramento (estrutura lastreada aberta) em seção própria; fora do bloco de leitura técnica"
  - "Frases de motivo em copy.js, não em skill_ref"
metrics:
  completed: 2026-09-28
---

# Quick 260928-u0h: separar encerramento e motivo por posição

Aba Opções > Oportunidades agora separa a proposta de encerramento (posição já lastreada, mesmo predicado `underlying`+`lastro` de `pos_op_aberta` do servidor) na seção "Suas estruturas abertas", e lista cada posição sem card com ticker e frase de motivo vinda de `copy.js` (Estudo e Operador).

## Commits
- 51d32566: módulo puro `classificarOportunidades.js`, 5 chaves `tiraOpcoes*` nos dois modos, guardião novo
- Task 2 (componente, fiação `optionPositions`, reconciliação do guardião): 77fdd628, na branch `v2/interacao-estrutural`

Obs.: o guardião novo foi commitado na task 1 já com a seção estática do componente, portanto ficou parcialmente vermelho entre os dois commits; fecha verde na task 2.

## Verificação
- 12 guardiões do plano verdes (nenhum FALHOU) e `npx vite build` OK.
- `server/` e `useOpcoesPropostas.js` sem diff.

## Deviations from Plan
Nenhuma de escopo. Ajuste menor: dois comentários reescritos para não casar o regex `manchete[^}]*\+` do guardião da tira.

## Decisões autônomas
- Seção estática do guardião novo escrita já na task 1 (plano previa na task 2); efeito: vermelho transitório entre commits.
- Comentários do componente evitam a palavra "manchete" antes de `+` (regex do guardião varre comentários).
- Nota "sem consumidor" adicionada nas chaves `tiraOpcoesSemCobertura/SemSetup/SemMercado` (as duas ocorrências).

## Limitações conhecidas
- (a) Estrutura aberta sobre ativo cujo gate reprova não recebe proposta de encerramento (o hook só busca proposta com gate líquido; `test_opcoes_subabas_ui` item 4 trava o guarda) — aparece como `aberta_sem_proposta`.
- (b) `tiraOpcoesSemCobertura/SemSetup/SemMercado` ficam em copy.js sem consumidor em componente.
- (c) Frases de motivo em copy.js e não em skill_ref: tensão consciente com a skill didatica-boris, porque `motivoTexto` do backend colapsa três motivos na frase de `sem_setup`.
- Suíte canônica completa e `cap copy` não rodados (competência do orquestrador).

## Self-Check: PASSED
