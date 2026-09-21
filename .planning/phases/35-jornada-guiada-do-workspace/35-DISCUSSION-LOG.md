# Phase 35: Jornada Guiada do Workspace - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-21
**Phase:** 35-Jornada Guiada do Workspace
**Areas discussed:** Estrutura do fluxo (portão de leitura × carril de pills), hierarquia visual do CTA, indicador de progresso, paridade entre as 3 pills — tratadas juntas por decisão do Alex de trazer agentes especializados (UX Researcher + UI Designer) para propor opções concretas antes de decidir.

---

## Estrutura do fluxo

Pesquisa (UX Researcher, com WebSearch sobre padrões de progressive disclosure e apps de trading para iniciantes) mais leitura direta do código atual identificaram um achado que mudou o enquadramento: o portão de leitura ficar fora do carril de pills não é descuido, é decisão de arquitetura já fechada na Fase 27 (comentário citando ADR-027 Emenda 2, `OpcoesScreen.jsx:517-536`) — a pill Analisar só renderiza no ramo que já depende de `temLeitura`, então mover o convite pra lá o tornaria inalcançável.

| Option | Description | Selected |
|--------|-------------|----------|
| A — Passo numerado, sem tocar arquitetura | "Passo 1 de 2" no bloco de leitura + "Passo 2 de 2" no carril de pills (sem numerar Analisar/Comparar entre si); Setups salvos deixa de ficar preso atrás do portão à toa. Zero mudança de arquitetura. | ✓ |
| B — Carril numerado com cadeado | "1. Ler ativo → 2. Analisar → 3. Comparar", pills bloqueadas com ícone de cadeado; Setups salvos sai do carril sequencial pra um ponto de entrada à parte. Sensação de wizard mais forte, mas desloca layout. | |
| C — Portão absorvido dentro da pill Analisar | Contraria a decisão já fechada da Fase 27 (branch de render de Analisar já depende de `temLeitura` — o convite ficaria inalcançável ali dentro). | |

**User's choice:** Opção A
**Notes:** Achado colateral aproveitado de graça nesta opção: `SecaoSetups.jsx` não depende de `temLeitura`, mas hoje topa com o portão de leitura no caminho mesmo assim — corrigido (D-02 do CONTEXT.md). Opção B fica registrada como candidata futura, não descartada de vez.

---

## Hierarquia visual do CTA

Leitura direta do design system atual (UI Designer, lendo `SecaoAnalisar.jsx`/`SecaoComparar.jsx`/`OpcoesScreen.jsx`/`CuradoriaEstruturas.jsx`/`PropostaLastreada.jsx`/`34-UI-SPEC.md`) achou que `T.accent` já tem um "reserved for" documentado no UI-SPEC recém-aprovado da Fase 34 (só a aba ativa do carril) — usar a mesma cor como preenchimento do CTA primário é uma extensão dessa regra, não invenção de cor nova, com precedente real em produção (`CuradoriaEstruturas.jsx:268`, sub-aba Operador).

| Option | Description | Selected |
|--------|-------------|----------|
| Estender accent para CTA primário preenchido | `BOTAO_PRIMARIO` = mesma geometria do `BOTAO`, fundo `T.accent` sólido, texto branco. Aplica-se só aos 3 CTAs principais (Ler no serviço, Montar estrutura, Ver possibilidades). | ✓ |
| Manter accent restrito à aba ativa | CTAs primários ganhariam outro tratamento (borda mais grossa, sem cor nova) — não detalhado, o Alex não escolheu esta opção. | |

**User's choice:** Estender accent para CTA primário preenchido
**Notes:** Risco aberto, não resolvido nesta discussão: contraste do subtexto de custo (branco a ~72% via `color-mix`) sobre `T.accent` no TEMA CLARO não foi verificado — fica como item de verificação obrigatória para quem executar/verificar a fase (D-07 do CONTEXT.md).

---

## Indicador de progresso

| Option | Description | Selected |
|--------|-------------|----------|
| Numerado "Passo 1 de 2" | Só no nível porta→carril (2 estágios reais) — nunca numerando Analisar/Comparar entre si, porque não são sequenciais (são 2 ações independentes + 1 job à parte). | ✓ |
| Só texto, sem número | "Leitura concluída — escolha Analisar ou Comparar", sem nenhum "Passo N" em lugar nenhum. | |

**User's choice:** Numerado "Passo 1 de 2"
**Notes:** O UI Designer argumentou contra numerar Analisar=2/Comparar=3 (implicaria sequência obrigatória que o produto não tem, citando o princípio 5 do CLAUDE.md — nunca inventar número/ordem que não existe). A escolha do Alex preserva a numeração só no nível porta→carril (2 estágios), que não tem esse problema — coerente com a objeção do agente, não contra ela.

---

## Todos revisados, não dobrados

Match fraco por palavra-chave genérica (`todo.match-phase`, score 0.6 nos 4): `carimbo-frescor-blocos-cross-carteira.md`, `opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp.md`, `revisao-arquitetura-mcp-ecossistema-b3.md`, `subaba-operar-fetch-redundante-gate-proposta.md` — nenhum é sobre clareza de jornada/passos, nenhum dobrado.

---

*Phase: 35-jornada-guiada-do-workspace*
*Discussion completed: 2026-09-21*
