# Phase 33: Extração dos 5 jobs em componentes próprios - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-19
**Phase:** 33-extração dos 5 jobs em componentes próprios
**Areas discussed:** Estratégia de guardião, Ordem de extração, Dobrar 2 todos pendentes, Nome dos componentes novos

---

## Estratégia de guardião

| Option | Description | Selected |
|--------|-------------|----------|
| Escanear o diretório inteiro | Mesmo padrão do guardião "ninguém importa App.jsx" já existente — sobrevive a futuras extrações sem reescrever o teste | ✓ |
| Manter por arquivo, só trocar o marcador | Cada guardião aponta pro arquivo novo específico — mais frágil a mudança futura | |

**User's choice:** Escanear o diretório inteiro (recomendado)
**Notes:** Precedente exato mirrorado de `test_opcoes_subabas_ui.mjs:101-114`.

---

## Ordem de extração

| Option | Description | Selected |
|--------|-------------|----------|
| Um de cada vez | 5 planos sequenciais, menor risco por passo, mais fácil isolar quebra de guardião | ✓ |
| Todos de uma vez | 1 plano só, mais rápido mas mistura risco de vários guardiões quebrando junto | |

**User's choice:** Um de cada vez (recomendado)
**Notes:** Ordem sugerida do mais isolado (SecaoVigias) ao mais entrelaçado (SecaoAnalisar), ver D-03 em CONTEXT.md.

---

## Dobrar 2 todos pendentes

| Option | Description | Selected |
|--------|-------------|----------|
| Fetch redundante do SubAbaOperar | Ataca exatamente REORG-03/04, não é escopo extra de verdade | ✓ |
| Carimbo de frescor nos Blocos A/B | UI nova (mostrar horário) — contraria "zero feature nova", mas resolve dívida de princípio 3 | ✓ |
| Nenhum agora | Fase fica 100% extração pura | |

**User's choice:** Ambos os fold-ins (multiSelect)
**Notes:** O carimbo de frescor é EXCEÇÃO EXPLÍCITA registrada a REORG-02, não scope creep silencioso — ver D-04b em CONTEXT.md.

---

## Nome dos componentes novos

| Option | Description | Selected |
|--------|-------------|----------|
| Aceitar sugestão da pesquisa | SecaoDescobrir, SecaoVigias, SecaoAnalisar, SecaoComparar, SecaoSetups | ✓ |
| Quero nomes diferentes | Outro padrão de nome | |

**User's choice:** Aceitar sugestão da pesquisa

---

## Claude's Discretion

Detalhamento exato de props/assinatura de cada `Secao*` (nomes de prop,
formato exato do JSX movido) — decisões acima fixam o QUE preservar e a
ORDEM, não a forma exata do código.

## Deferred Ideas

- Redesenho de navegação (hub + workspace) — Fase 34, já roteirizada
- Explicação adaptativa, progresso do aprendiz, desafio personalizado — v2 requirements, fora do roadmap
- Fechar o backlog B2 (estado não sobrevive à troca de aba) — dívida pré-existente, não incluída sem pedido explícito
