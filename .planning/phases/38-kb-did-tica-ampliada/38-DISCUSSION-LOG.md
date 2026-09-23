# Phase 38: KB Didática ampliada - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-23
**Phase:** 38-KB Didática ampliada
**Areas discussed:** Mecanismo de busca (KB-01), Onde a busca vive, Âncora do "saiba mais" por aba (KB-02), Comportamento dos resultados

---

## Mecanismo de busca (KB-01)

| Option | Description | Selected |
|--------|-------------|----------|
| Os dois | Busca livre + navegação por família na mesma tela | ✓ |
| Só busca livre | Campo de texto, sem navegação por categoria | |
| Só por família | Navegação em 9 categorias, sem campo de texto | |

**User's choice:** Os dois.

| Option | Description | Selected |
|--------|-------------|----------|
| Campo de texto no topo + lista de famílias abaixo | Um único componente, campo filtra a lista inteira | ✓ |
| Toggle entre dois modos ("Buscar"/"Explorar") | Duas telas/abas dentro da busca | |

**User's choice:** Campo de texto no topo + lista de famílias abaixo.

| Option | Description | Selected |
|--------|-------------|----------|
| Serve como está | Mantém kb.buscar() sem mudar lógica de match (palavra/frase completa) | ✓ |
| Precisa de match parcial (prefixo) | Digitar "ind" já sugere "indicador" | |

**User's choice:** Serve como está — não estender kb.buscar() para prefixo/substring.

---

## Onde a busca vive

| Option | Description | Selected |
|--------|-------------|----------|
| Dentro da aba Perfil | Perfil já é onde config/ajuda vivem; sem ícone novo na BottomNav | ✓ |
| Ícone global | Ícone fixo no header em todas as telas | |
| Dentro da folha de ajuda existente | Nova seção da folha "?" | |

**User's choice:** Dentro da aba Perfil.

| Option | Description | Selected |
|--------|-------------|----------|
| Tile novo → tela dedicada | Mesmo padrão de Preferências/Config | ✓ |
| Dentro de uma tela existente do Perfil | Seção extra em "Sobre" ou "Conta & preferências" | |

**User's choice:** Tile novo → tela dedicada.

---

## Âncora do "saiba mais" por aba (KB-02)

| Option | Description | Selected |
|--------|-------------|----------|
| Fixo por aba | 1 verbete-âncora fixo por aba, sem lógica condicional | ✓ |
| Contextual | Varia com setup/ticker ativo na tela | |

**User's choice:** Fixo por aba.

| Option | Description | Selected |
|--------|-------------|----------|
| Proponho no plano, você aprova depois | Planner escolhe o vid por aba; Alex aprova antes de codar | ✓ |
| Decido agora, um por um | Trava o vid exato de cada aba nesta conversa | |

**User's choice:** Proponho no plano, você aprova depois.
**Notes:** vid exato por aba fica como Claude's Discretion no CONTEXT.md, com critério explícito (coerência temática com a família de cada aba) e obrigação de apresentar a escolha no plano.

---

## Comportamento dos resultados

| Option | Description | Selected |
|--------|-------------|----------|
| Sem limite | Mostra todos os que baterem — limite=5 é pra assistente, não navegação | ✓ |
| Mantém top-5, com "ver mais" | Mesmo limite de hoje, com paginação | |

**User's choice:** Sem limite.

| Option | Description | Selected |
|--------|-------------|----------|
| Live + mensagem clara no vazio | Filtra a cada tecla, client-side; famílias continuam visíveis mesmo com 0 resultados de texto | ✓ |
| Só ao confirmar | Enter/botão buscar | |

**User's choice:** Live + mensagem clara no vazio.

---

## Claude's Discretion

- `vid` exato (dentre os 83 de `kb.py`) que ancora cada uma das 4 abas sem cobertura — proposta do planner, aprovação do Alex antes de codar.
- Mecanismo técnico de ponte entre `kb.py` (formato `kb.formatar()`) e `ConceitoSheet`/`store.conceito()` (hoje só resolve via `conceitos.py`/`conceitos.montar()`) — as duas fontes não se falam hoje.
- Nome/label do tile novo em Perfil e da tela de busca.
- Rota/endpoint novo para expor o catálogo completo de `kb.py` (hoje só existe `GET /api/kb/buscar`, que devolve resultado já pontuado/limitado).

## Deferred Ideas

None — discussão ficou dentro do escopo da fase 38 (KB-01/KB-02). Nenhum todo pendente foi dobrado: os 4 matches de `todo.match-phase` (revisão de arquitetura MCP, carimbo de frescor, aprovação de serviço MCP, fetch redundante da sub-aba Operar) são ruído de palavra-chave genérica (scores 0.2-0.6, sem relação temática com busca de verbetes) — nenhum foi apresentado como pergunta separada por decisão do orquestrador.
