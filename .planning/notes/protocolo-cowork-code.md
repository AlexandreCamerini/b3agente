---
title: Protocolo Cowork × Code neste repositório
date: 2026-08-27
context: Nasce do incidente registrado em .planning/cowork-sync-2026-08-27.md
  — o Cowork Project mapeou o repositório errado (~/dev/rail/prod/b3agente-main,
  cópia morta) por uma sessão inteira antes de ser corrigido.
---

# Protocolo Cowork × Code

## Hierarquia de fonte de verdade

1. `CLAUDE.md` (raiz) — contrato estável, sempre atual.
2. `.planning/intel/*.md` (`decisions.md`, `constraints.md`, `context.md`,
   `SYNTHESIS.md`) — ledger das ADRs/SPECs ingeridas, atualizado por
   `/gsd-ingest-docs`.
3. `.planning/notes/*.md` — decisões pontuais capturadas em sessão
   (`/gsd-explore` e afins), duráveis.
4. `.planning/cowork-sync-*.md` — ponte transitória, cola-se por cima do
   contexto antigo do Cowork Project. **Não é memória durável.** Uma vez
   absorvido em nota própria (2 e 3 acima), apaga — não mantém como verdade
   paralela.

Cowork nunca é fonte primária. Se o contexto do Cowork divergir do que está
em `.planning/`, `.planning/` vence.

## Antes de confiar em qualquer contexto colado pelo Cowork

Confirmar o repositório ativo antes de agir sobre ele:
```bash
git remote -v && git log -1 --oneline
```
O incidente que motivou esta nota: uma sessão inteira raciocinou sobre
`~/dev/rail/prod/b3agente-main` (0 commits, cópia morta) achando que era
este repo. Nunca assumir que o path anexado no Cowork é o repo certo sem essa
checagem de um comando.

## Governança vale igual pros dois lados

GSD Workflow Enforcement (ver CLAUDE.md) não é bypassável pelo Cowork: sem
edição de arquivo fora de um comando GSD, salvo bypass explícito do Alex.
Guardrails invioláveis do produto (bundle id, paridade `defaults.py`↔
`catalog.js`, manchete só do motor determinístico, stop/alvo nunca vetado,
histórico não se reescreve) valem igual em qualquer sessão, Cowork ou Code.

## Descarte de artefatos superados

Repositórios/documentos identificados como base errada ficam **desconsiderados,
não apagados** (ex.: `~/dev/rail/prod/b3agente-main`) — decisão de apagar é
do Alex, não automática.
