---
title: Carimbo de frescor nos blocos cross-carteira da aba Opções (princípio 3)
date: 2026-09-15
priority: medium
---

# Os dois blocos cross-carteira não dizem de quando é o dado

Achado durante o `/gsd:ui-phase 32` (ver `32-UI-SPEC.md`, Open Question #4).

`OportunidadesOpcoes` (motor COM gate, `opcoes_lastreadas.propor()`) e
`CuradoriaEstruturas` (motor SEM gate, `opcoes_curadoria`) **não exibem
nenhum carimbo de frescor** — nada de "pregão", "em dia", "atrasado", nem
horário da última atualização. O bloco de leitura técnica por ticker exibe;
estes dois, não.

Isso é lacuna do **princípio 3 do `CLAUDE.md`**:

> Dados de mercado exibem fonte, horário da última atualização e se são em
> tempo real, atrasados ou históricos.

## Por que virou TODO e não tarefa da Fase 32

A lacuna é **pré-existente** — nasceu com esses blocos, não com a
consolidação. A Fase 32 move os dois para o topo da aba Opções (D-04/D-07),
o que torna a ausência mais visível, mas não a cria.

Decisão do Alex em 2026-09-15, durante o `ui-phase`: manter a Fase 32 no que
ela é — mover e unificar — em vez de expandir para tocar os hooks de onde o
timestamp teria de vir. A fase já carrega uma correção de princípio (o
`erro` de `useCuradoria()` que hoje se disfarça de estado vazio, violando o
princípio 4).

## O que fazer

1. Descobrir se o dado de frescor **existe** na resposta das rotas que
   alimentam os dois blocos, ou se precisa ser adicionado no backend. O
   bloco de leitura técnica por ticker já exibe carimbo — achar de onde ele
   tira e se a mesma fonte serve aqui.
2. Se o backend já devolve: é mudança só de front (exibir), barata.
   Se não devolve: decidir se vale mexer nas rotas — atenção ao fato de a
   rota da curadoria consumir orçamento do `mydata_budget` (Fase 31 D1).
3. Aplicar o mesmo vocabulário de frescor que já existe no app, nos DOIS
   modos (Estudo e Operador) via `copy.js` — não inventar rótulo novo.
4. Guardião de teste para os dois blocos, no padrão dos `web/tests/*.mjs`
   existentes.

## Contexto relacionado

- `32-UI-SPEC.md` — Open Question #4 (origem deste TODO) e o contrato visual
  dos dois blocos no topo da aba.
- `32-CONTEXT.md` D-04/D-07 — por que os dois blocos ficam lado a lado no
  topo da sub-aba Setups.
- Princípio 4 do `CLAUDE.md` (não inventar valor quando a fonte falha) — é o
  vizinho deste problema: sem carimbo, o usuário não distingue "dado de
  hoje" de "dado de três pregões atrás".
