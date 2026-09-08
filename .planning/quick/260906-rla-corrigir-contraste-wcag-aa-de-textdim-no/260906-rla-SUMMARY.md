---
phase: quick-260906-rla
plan: 01
subsystem: front-web
tags: [acessibilidade, wcag, contraste, tokens, guardiao]

requires: []
provides:
  - "web/src/App.jsx:91 — PALETTE.light.textDim corrigido de #6b7288 para #646b7f (contraste contra bgPanel sobe de 4,20:1 para 4,67:1)"
  - "web/tests/test_brand_book_v2_tokens.mjs seção 5 — guardião de contraste estendido de textFaint para textFaint+textDim, nos 4 esquemas (Estudo/Operador × dark/light) × 3 superfícies"
affects: [tema-claro, modo-estudo, acessibilidade]

tech-stack:
  added: []
  patterns:
    - "Ajuste de hex preservando matiz (HSL H/S constantes, só luminosidade reduzida) — mesma metodologia do FIX-C16 original"
    - "Guardião de contraste parametrizado por token (loop sobre uma lista de chaves) em vez de hardcoded para um token só — evita a mesma classe de omissão se um 5º token de texto surgir no futuro"

key-files:
  created: []
  modified:
    - web/src/App.jsx
    - web/tests/test_brand_book_v2_tokens.mjs
    - .planning/PROJECT.md

key-decisions:
  - "Corrigir SÓ PALETTE.light.textDim — os outros 3 textDim (PALETTE.dark 5,15:1, MODE_OPERADOR.dark 5,59:1, MODE_OPERADOR.light 4,70:1, todos pior-caso) já passam AA e foram deixados byte-idênticos, confirmado por grep pós-fix."
  - "Estender o guardião da seção 5 em vez de criar um teste novo — a lacuna real não era falta de token corrigido, era o guardião medir só textFaint; um guardião novo teria corrigido o sintoma sem fechar a causa (o próprio texto do guardião já nomeia essa classe de omissão, agora reaplicada na dimensão do token em vez da superfície)."
  - "Nenhum guardião pré-existente fazia match hardcoded no hex antigo #6b7288 — busca em web/tests/*.mjs e server/tests/*.py confirmou isso; as únicas ocorrências fora de App.jsx:91 estão em documentos ARQUIVADOS de planejamento (.planning/milestones/v1.1-phases/04-*), que são histórico e não se reescrevem."
  - "Sem npx vite build nem bump/publicar-web.sh — mudança é um literal de string dentro de um objeto já existente, sem alteração de sintaxe JS; dois testes que fazem parse do App.jsx (o guardião estendido e test_mode_operador_light_palette.mjs) já exercitam o bloco alterado."
  - "Suíte canônica completa (bash scripts/executar.sh --testes) rodada e confirmada verde ANTES de editar PROJECT.md — não se move o achado de Active para Validated com a suíte ainda vermelha."

requirements-completed: []

duration: ~25min (planner + executor)
completed: 2026-09-06
status: complete
---

# Quick Task 260906-rla: Corrigir contraste WCAG AA de textDim no tema claro, Summary

## O que foi feito

`PALETTE.light.textDim` (Modo Estudo, tema claro) reprovava WCAG AA contra
`bgPanel` — achado colateral da Fase 4/FIX-C16, catalogado em
`.planning/PROJECT.md` seção Active há semanas e nunca corrigido. Pior: como
`textFaint` já tinha sido corrigido nessa mesma fase, a hierarquia visual
ficava invertida no tema claro — o token que deveria ler mais apagado
(`textFaint`, 4,56:1) contrastava MAIS que o `textDim` (4,20:1).

Medição confirmada com a fórmula WCAG de luminância relativa (mesma do
`contrast()` já existente em `test_brand_book_v2_tokens.mjs`):

| Superfície | hex antigo `#6b7288` | hex novo `#646b7f` |
|---|---|---|
| bgBase `#f7f8fc` | 4,51:1 | 5,01:1 |
| bgPanel `#eef0f7` (pior caso) | **4,20:1 — reprova** | **4,67:1 — passa** |
| bgCard `#ffffff` | 4,79:1 | 5,32:1 |

Os outros 3 `textDim` do arquivo já passavam AA e foram deixados
byte-idênticos: `PALETTE.dark` (`#8890a8`, pior caso 5,15:1),
`MODE_OPERADOR.dark` (`#8492ac`, pior caso 5,59:1), `MODE_OPERADOR.light`
(`#5c6d67`, pior caso 4,70:1).

## Como foi corrigido

1. **`web/src/App.jsx:91`** — `textDim: "#6b7288"` → `textDim: "#646b7f"`.
   Novo hex derivado preservando o matiz HSL (H=225,5°, S=0,119), só
   reduzindo a luminosidade (L de 0,476 para 0,446) — mesma metodologia do
   FIX-C16 original. Comentário datado (2026-09-06) adicionado acima da
   linha, no mesmo estilo dos comentários FIX-C16 vizinhos, explicando a
   origem colateral e os números antes/depois.

2. **`web/tests/test_brand_book_v2_tokens.mjs`** (seção 5) — o loop que
   media contraste só de `textFaint` nas 3 superfícies passou a medir
   `textFaint` E `textDim`, mantendo a mesma asserção (`>= 4.5`) e o mesmo
   formato de mensagem. Isso fecha a lacuna real: o `textDim` nunca tinha
   entrado em nenhum guardião de contraste do repo, por isso o bug
   sobreviveu à Fase 4 inteira e a todo o milestone v1.5 sem nenhum teste
   reclamar. Nenhuma asserção existente foi removida ou relaxada.

3. **`.planning/PROJECT.md`** — item removido de `### Active`, entrada nova
   adicionada em `### Validated` com o hex antigo/novo, contraste
   antes/depois nas 3 superfícies e referência ao guardião estendido.

## Validação

- `bash scripts/executar.sh --testes` (suíte canônica completa) — verde:
  2021 passed / 1 skipped (backend) + todos os `web/tests/*.mjs` OK.
- `node web/tests/test_brand_book_v2_tokens.mjs` isoladamente — todas as
  asserções passam, incluindo as 12 novas de `textDim` (4 esquemas × 3
  superfícies) e as 12 pré-existentes de `textFaint`, intocadas.
- `grep -n textDim web/src/App.jsx` confirma os 4 valores esperados
  (`#646b7f`, `#8890a8`, `#8492ac`, `#5c6d67`) e ausência de `6b7288` no
  arquivo.

## Limitações conhecidas

- Sem verificação visual ao vivo no navegador (nenhuma ferramenta de browser
  disponível nesta sessão de execução) — compensado pelas 24 asserções
  automatizadas de contraste (12 novas de `textDim` + 12 de `textFaint`
  intactas) e pela suíte canônica completa verde.
- A suíte canônica precisou de `dangerouslyDisableSandbox` porque
  `scripts/executar.sh --testes` usa `mktemp -d` internamente, que o sandbox
  padrão do Bash bloqueia (caminho fora do allowlist de escrita) — não é uma
  falha de teste, é uma restrição de ambiente já documentada em memória
  deste projeto.

## Nota do orquestrador

O executor rodou em worktree isolado e criou este SUMMARY.md lá, sem
committá-lo (por desenho — commits de docs ficam a cargo do orquestrador).
Ao mergear a branch e remover o worktree, este arquivo não commitado foi
perdido junto com o diretório. Reconstruído aqui a partir do relatório
completo do executor e, mais importante, verificado byte a byte contra os
3 commits reais já mesclados (`5263ca7`, `64c368f`, `6dd54bf`) e uma
reexecução ao vivo do guardião — nenhum dado inventado, só reescrito a
partir de fonte primária confirmada.
