# Requirements: Boris+ (b3-agente) — Milestone v1.8

**Defined:** 2026-09-23
**Core Value:** O usuário leigo sai do Modo Estudo entendendo de verdade como
o mercado funciona — não decorou uma resposta, aprendeu o raciocínio — e só
então tem acesso a automações do Modo Operador.

## v1 Requirements

Retomado do backlog da Fase 26 (v1.4, `26-CONTEXT.md`), priorizado por valor
de produto — não por ordem de descoberta.

### KB Didática

- [x] **KB-01**: Usuário pode buscar um verbete entre os 83 da KB de mecânica
  B3 (mecanismo de busca — livre, por família, ou os dois — decidido em
  discuss-phase, não travado aqui)
- [x] **KB-02**: Usuário vê link "saiba mais" para um verbete relevante nas 4
  abas que hoje não têm essa cobertura (requer extrair `SetorAlvo`/
  `ConceitoSheet` de `App.jsx` para módulo compartilhado, sem violar o
  isolamento deliberado de `OpcoesScreen.jsx` — `OpcoesScreen.jsx:20-24` não
  importa nada de `App.jsx`)

### Reestruturação de navegação

- [x] **NAV-01**: A aba Opções passa a ter 3 abas fixas de nível 1 —
  Oportunidades, Recomendadas, Montar — substituindo as duas camadas
  ortogonais de navegação atuais (`subaba` + `abaWorkspace`, `OpcoesScreen.jsx`).
  Vigias deixa de ser sub-aba e vira ícone/badge no cabeçalho (sheet), sempre
  acessível independente da aba ativa. A sub-aba "Operar" é dissolvida — a
  ação de executar migra para dentro do card de oportunidade (aba
  Recomendadas), inline, no padrão que `CuradoriaEstruturas.jsx` já usa. O
  nome "Setups" é preservado para o recurso existente (condição salva em
  português livre, `SecaoSetups.jsx`/`CriarSetup.jsx`); a aba nova usa
  "Recomendadas" para evitar colisão de rótulo (achado do design-audit
  2026-09-23). Origem: achado ao vivo do Alex ("não consigo montar uma
  estrutura e efetivá-la", "não sei pra que serve a aba Operar") +
  auditoria de design da aba Opções (2026-09-23) — não estava no backlog da
  Fase 26; é achado novo, sequenciado ANTES de ESTADO-01 porque essa fase
  pressupõe a estrutura de navegação atual como o estado a preservar.
  Metodologia de ranking da aba Recomendadas (filtro por probabilidade +
  ordenação por prêmio anualizado, discutido em sessão separada) e a faixa
  de corte de probabilidade ficam para decisão em discuss-phase — não
  travadas aqui.

### Continuidade UX

- [ ] **ESTADO-01**: Estado da aba Opções (ticker selecionado, aba ativa)
  sobrevive à troca para outra aba principal e volta — abordagem
  de implementação (memória local × persistência) a decidir em
  discuss-phase. Depende da navegação de NAV-01 já estar definida (a
  navegação a preservar muda de forma com NAV-01). *Revisado 2026-09-25
  (discuss-phase, `40-CONTEXT.md`): decidido estado em memória no
  `App.jsx` (D-01); filtros internos NÃO são lembrados e voltam ao default
  (D-02) — o texto original incluía "filtros".*

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

| Requirement | Phase | Status |
|-------------|-------|--------|
| KB-01 | Phase 38 | Done |
| KB-02 | Phase 38 | Done |
| NAV-01 | Phase 39 | Done |
| ESTADO-01 | Phase 40 | Pending |
| TELAS-01 | Phase 41 | Pending |

**Coverage:**
- v1 requirements: 5 total
- Mapped to phases: 5
- Unmapped: 0 ✓

---
*Requirements defined: 2026-09-23*
*Last updated: 2026-09-23 — Fase 38 fechada: KB-01/KB-02 Done, publicado em
produção (`F10-20260923-01`), checkpoint humano do roteiro de 9 itens
aprovado pelo Alex (38-06). Ver STATE.md/ROADMAP.md para o detalhe.*
*Last updated: 2026-09-23 — NAV-01 adicionado (auditoria de design da aba
Opções, achado ao vivo do Alex), inserido como Fase 39; ESTADO-01/TELAS-01
renumeradas para Fase 40/41 (NAV-01 precisa fechar antes de ESTADO-01 porque
muda a navegação que ESTADO-01 preservaria).*
*Last updated: 2026-09-24 — Fase 39 fechada, requirement NAV-01 concluído,
publicado em produção (`F10-20260924-01`), checkpoint humano do roteiro de 10
itens + DR-1/DR-2 nomeadas aprovado pelo Alex (39-06), incluindo override ao
vivo de D-03 (rótulo "Recomendadas" → "Destacadas", ambiguidade regulatória
CVM). Ver STATE.md/ROADMAP.md para o detalhe.*
