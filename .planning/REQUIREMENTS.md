# Requirements: Boris+ (b3-agente) — Milestone v1.8

**Defined:** 2026-09-23
**Core Value:** O usuário leigo sai do Modo Estudo entendendo de verdade como
o mercado funciona — não decorou uma resposta, aprendeu o raciocínio — e só
então tem acesso a automações do Modo Operador.

## v1 Requirements

Retomado do backlog da Fase 26 (v1.4, `26-CONTEXT.md`), priorizado por valor
de produto — não por ordem de descoberta.

### KB Didática

- [ ] **KB-01**: Usuário pode buscar um verbete entre os 83 da KB de mecânica
  B3 (mecanismo de busca — livre, por família, ou os dois — decidido em
  discuss-phase, não travado aqui)
- [ ] **KB-02**: Usuário vê link "saiba mais" para um verbete relevante nas 4
  abas que hoje não têm essa cobertura (requer extrair `SetorAlvo`/
  `ConceitoSheet` de `App.jsx` para módulo compartilhado, sem violar o
  isolamento deliberado de `OpcoesScreen.jsx` — `OpcoesScreen.jsx:20-24` não
  importa nada de `App.jsx`)

### Continuidade UX

- [ ] **ESTADO-01**: Estado da aba Opções (ticker selecionado, sub-aba
  ativa, filtros) sobrevive à troca para outra aba principal e volta —
  abordagem de implementação (memória local × persistência) a decidir em
  discuss-phase

### Consolidação técnica

- [ ] **TELAS-01**: Registro único de telas no front (label, snapshot,
  passo de tour, seção de ajuda), do qual `BottomNav.defs`, `tourPassos`,
  `ajudaSecoes` e `petSnapshot` passam a ler — paridade seguindo o MESMO
  padrão de `defaults.py`×`catalog.js`: dois pontos testados (registro do
  front × `PET_TELAS` do backend), não um cruzando JS/Python

## v2 Requirements

Reconhecido, mas fora desta milestone — decisão de escopo pendente do Alex.

### Execução

- **EXEC-01**: Ligar a aba Opções a rotas de execução com flag opt-in a
  descoberto (B3) — pesquisa concluída em `26-CONTEXT.md`, decisão de
  escopo (posição a descoberto é feature de risco maior) segue pendente

## Out of Scope

| Item | Motivo |
|------|--------|
| CAP-12 (bypass de cap de watchlist no iOS) | Fix já pronto em código desde a Fase 13; falta só distribuição TestFlight — operacional, não requirement de fase |
| Verificação visual da Fase 37 em produção | Mesma distribuição TestFlight resolve; não é trabalho de código novo |
| Dívida de verificação ao vivo (multi-candidato Fase 19/32, entradaAuto, human-checks Fase 3, UAT v1.5) | Checkpoints que dependem do Alex testar ao vivo, não de código novo; ficam no backlog do PROJECT.md |
| 3 achados Baixo do REPORT-01 (C-10, C-17, C-29) | Baixo valor/urgência, cauda do backlog |
| Verbete de "drawdown" ausente em `kb.py`/`conceitos.py` | Gap real do CLAUDE.md, mas candidato a fold-in oportunista, não fase dedicada |
| `numHero` sem consumidor real | Candidato a fase de polish visual futura, sem urgência |

## Traceability

Preenchido na criação do roadmap.

| Requirement | Phase | Status |
|-------------|-------|--------|
| KB-01 | TBD | Pending |
| KB-02 | TBD | Pending |
| ESTADO-01 | TBD | Pending |
| TELAS-01 | TBD | Pending |

**Coverage:**
- v1 requirements: 4 total
- Mapped to phases: 0
- Unmapped: 4 ⚠️ (roadmap ainda não criado)

---
*Requirements defined: 2026-09-23*
*Last updated: 2026-09-23 after initial definition*
