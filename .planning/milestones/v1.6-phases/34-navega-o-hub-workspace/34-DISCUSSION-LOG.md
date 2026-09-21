# Phase 34: Navegação hub + workspace - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-20
**Phase:** 34-Navegação hub + workspace
**Areas discussed:** Divisão de "setups salvos" (hub × workspace), estado do workspace ao voltar, sub-navegação dentro do workspace, arranjo do pill row (follow-up), ordem das seções do hub, header/botão de voltar

---

## Divisão de "setups salvos" (hub × workspace)

| Option | Description | Selected |
|--------|-------------|----------|
| Split: lista no hub, criar no workspace | A listagem de todos os setups (cross-ticker) fica no hub, junto de vigias. Criar um setup novo (exige ticker/tese/vencimento) abre dentro do workspace, ao lado de Analisar/Comparar, reusando a mesma leitura MCP já paga do ticker selecionado. | ✓ |
| Tudo no hub | SecaoSetups inteira (lista + criação) fica no hub; NAV-05 estaria com erro de redação a corrigir. | |
| Tudo no workspace | SecaoSetups inteira só aparece depois de selecionar um ticker; NAV-01 estaria com erro de redação a corrigir. | |

**User's choice:** Split: lista no hub, criar no workspace
**Notes:** Resolve a contradição aparente entre NAV-01 (setups salvos no hub) e NAV-05 (gerenciar setups salvos dentro do workspace) — os dois textos do ROADMAP.md estavam certos, cada um descrevendo metade do job.

---

## Estado do workspace ao voltar pro hub

| Option | Description | Selected |
|--------|-------------|----------|
| Reseta sempre | Cada entrada no workspace começa limpa, igual hoje. Zero estado novo escondido, fiel a "reorganização pura". | ✓ |
| Preserva na sessão | Voltar ao mesmo ticker restaura tese/vencimento/lote da última vez — resolveria o backlog B2 de passagem, mas é comportamento novo. | |

**User's choice:** Reseta sempre
**Notes:** Decisão explícita de NÃO fechar o backlog B2 (Fase 26, v1.4) de passagem nesta fase.

---

## Sub-navegação dentro do workspace

| Option | Description | Selected |
|--------|-------------|----------|
| Pill row (mesmo padrão Setups/Operar) | Reusa o componente de abas já existente, um nível abaixo, entre os jobs do workspace. | ✓ |
| Empilhado, sem troca | Analisar e Comparar um embaixo do outro na mesma rolagem do workspace. | |

**User's choice:** Pill row (mesmo padrão Setups/Operar)

---

## Arranjo do pill row (follow-up, pós-decisão de setups salvos)

| Option | Description | Selected |
|--------|-------------|----------|
| Sim, 3 abas | Analisar, Comparar e Criar Setup como 3 pills no mesmo nível dentro do workspace. | ✓ |
| Não — Criar Setup dentro da aba Analisar | Só 2 pills; "criar um setup" vira CTA dentro da tela de Analisar, sem pill próprio. | |

**User's choice:** Sim, 3 abas
**Notes:** Consequência direta da decisão anterior (setups salvos split) — perguntado como follow-up porque a primeira formulação da pergunta de sub-navegação assumia só 2 jobs no workspace.

---

## Ordem das seções do hub

| Option | Description | Selected |
|--------|-------------|----------|
| Aceitar ordem da pesquisa | Frase-ponte + Bloco A + Bloco B → Meus vigias → Meus setups salvos (lista). Mantém a ordem já existente no código. | ✓ |
| Quero ordem diferente | Outra sequência de seções. | |

**User's choice:** Aceitar ordem da pesquisa (recomendada)

---

## Botão/header de voltar ao hub

| Option | Description | Selected |
|--------|-------------|----------|
| Header fixo com ticker + voltar | Linha fixa no topo do workspace: nome do ticker + botão "Voltar". Resolve a orientação ("you are here") apontada pela pesquisa como maior risco de virar feature nova. | ✓ |
| Só um botão discreto, sem header novo | Botão de voltar simples, sem linha de cabeçalho nova. | |

**User's choice:** Header fixo com ticker + voltar

---

## Claude's Discretion

- Detalhamento exato de props/assinatura da divisão de `SecaoSetups.jsx` (sub-componente interno vs. prop `modo: "lista" | "criar"`)
- Estilo visual exato do header fixo do workspace
- Confirmação de que `useOpcoesMcp`/`useOpcoesPropostas` continuam chamados só no orquestrador `OpcoesScreen.jsx` (invariante herdado da Fase 33, não é decisão nova)

## Deferred Ideas

- Fechar o backlog B2 (estado não sobrevive à troca de aba/seção) — explicitamente não dobrado nesta fase
- Personalização (Fases 2-4 do plano de UX maior) — fora do roadmap deste milestone
- Deep-link direto pra um ticker específico a partir de um card de vigia/setup salvo — não veio à tona na discussão, registrado como candidato de fase futura
