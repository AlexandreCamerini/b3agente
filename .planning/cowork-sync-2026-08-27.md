# Sync do Cowork Project — Boris++ (27/08/2026)

> Cole isto por cima do contexto antigo do Cowork Project. O contexto anterior
> apontava para o repositório ERRADO e está integralmente superado por este.
> Anexe este repositório (`/Users/acamerini/dev/bolsia/b3-agente`) como pasta
> do projeto — o `CLAUDE.md` da raiz já documenta stack, convenções e
> guardrails; este arquivo cobre só o histórico de decisão que o CLAUDE.md
> não carrega.

## Correção que invalida o contexto anterior

O primeiro levantamento (26-27/08) foi feito contra
`~/dev/rail/prod/b3agente-main` — uma cópia morta, 0 commits, `main.py` com
583 linhas. **O repositório real e ativo é `~/dev/bolsia/b3-agente`**
(`origin` = `github.com/AlexandreCamerini/b3agente.git`, `main.py` com 2.991
linhas, 19 ADRs, 467 testes, último commit 2026-08-24). Sete das nove
premissas técnicas do contexto antigo eram falsas. Detalhe completo em
`docs/boris-pp-00-mapa-de-realidade.md` (nesse outro repo — ver seção
Referência abaixo). `~/dev/rail/prod/b3agente-main` fica desconsiderado, não
apagado — não editar, não mapear.

## O que isso muda no projeto

O projeto nasceu desenhado como **fusão de dois sistemas complementares**
(`mydata`, MCP de análise B3, + `b3agente`/"Boris", app de paper trading).
Os dois convergiram sozinhos: hoje é **duplicação em seis frentes**, não
complementaridade. **Boris++ é um projeto de deduplicação e consolidação**,
não de integração.

| Capacidade | mydata | Boris (real) | Situação |
|---|---|---|---|
| COTAHIST diário B3 | `fonte.py` | `b3_historical.py` + ADR-019 (locked) | Duplicado |
| Calendário/feriados B3 | `FERIADOS_B3` | `pregao.py` (feriados móveis, janela oficial) | Duplicado — Boris melhor |
| Indicadores técnicos | `calculos.py` | `indicators.py` | Duplicado |
| Cadeia de opções/gregas/IV | tools do MCP | `options_api.py`/`options_quant.py` + ADR-003/004/005 (locked) | Duplicado |
| Motor de setups | `setups.py` (DSL) | motor próprio + ADR-015/016/017 (016 não travada, 017 travada — seleção dinâmica por desempenho histórico) | Duplicado — Boris já mediu que o sinal ingênuo perde dinheiro |
| Job diário | `job_diario.py` | hooks no `scheduler_loop` (`agent.py`) | Duplicado |
| **Compilação NL→DSL de setup** | `create_setup` | não existe | **Delta real do mydata** |
| **Ferramentas MCP conversacionais** | 11 tools | não existe | **Delta real do mydata** |

O delta genuíno do `mydata` cabe em duas linhas. Tudo o mais já tem dono no
Boris, com ADR aceito e teste.

## Ingest de documentação — concluído (commit `6886385` neste repo)

Rodei `/gsd:ingest-docs` neste repositório (modo merge) sobre os 33 documentos
de `docs/` (19 ADR, 5 SPEC, 8 DOC, 1 excluído por decisão sua —
`docs/prompts/admin-mobile-otimizado.md`, classificado UNKNOWN, preservado em
`.planning/intel/classifications/_excluded/`).

- **14 ADRs travadas**: 001, 003, 004, 005, 006, 007, 008, 009, 012, 013, 014
  (você confirmou que foi aprovada e implementada — o texto "Proposto" na
  própria ADR está desatualizado), 017, 018, 019.
- **5 ADRs propostas, aguardando decisão sua**: 002 (tríade temporal), 010
  (planos/cap comercial), 011 (observabilidade — hospedagem/auth), 015
  (instrumentação de assertividade), 016 (qualidade do sinal — já superada
  em termos de decisão pela 017, mas não formalmente travada).
- **Ledger completo**: `.planning/intel/decisions.md` — é a fonte a consultar
  antes de propor qualquer coisa que toque uma dessas áreas, em vez de reabrir
  os 19 arquivos ADR um a um.
- **Zero requisitos novos, zero mudança em PROJECT.md/ROADMAP.md/STATE.md** —
  o ingest só formalizou o que já existia; nenhuma fase nova foi necessária
  (v1.0+v1.1 já shipped, 8/8 fases completas, sem milestone aberto).
- Relatório de conflito (0 bloqueadores, 0 avisos, 7 informativos):
  `.planning/INGEST-CONFLICTS.md`.

## Decisões em aberto (nesta ordem — a primeira trava as outras)

1. **Milestone novo vs. fechar backlog primeiro** — `PROJECT.md` já registra
   essa escolha pendente, independente do Boris++: seis itens em "Active"
   (decisão comercial do ADR-010, 2 human-checks nunca confirmados ao vivo,
   9 achados Baixo do REPORT-01, contraste WCAG do tema claro, 9 tickers com
   404 no bootstrap do ledger). Decidir se o Boris++ vira o próximo milestone
   ou se esse backlog fecha antes.
2. **Direção de deduplicação, módulo a módulo** — das 6 frentes duplicadas
   na tabela acima: quem fica dono, o que migra, o que é descartado. Esta é
   a decisão que define o Boris++, maior que qualquer decisão de transporte
   de MCP.
3. **Risco declarado a respeitar na decisão 2**: a ADR-016 (não travada, mas
   com medição real — 125.938 sinais, 15 anos) mostrou que o sinal de setup
   ingênuo do `mydata`/`setups.py` **perdia dinheiro**; a ADR-017 (travada)
   corrigiu ponderando por desempenho histórico. Portar `setups.py` sem
   passar pelo mesmo harness de backtest reintroduz um defeito já pago.

## Governança deste repositório (o Cowork precisa respeitar, não é opcional)

- **GSD Workflow Enforcement**: nenhuma edição de arquivo fora de um comando
  GSD (`/gsd-quick`, `/gsd-debug`, `/gsd-execute-phase`, ou para este caso
  `/gsd-explore` → `/gsd-new-milestone`), salvo bypass explícito seu.
- Guardrails invioláveis do produto (resumo — ver `CLAUDE.md` da raiz para o
  texto completo): bundle id `com.alexandrecamerini.bolsia` não muda;
  paridade obrigatória `defaults.py` ↔ `catalog.js` e `deviceStore` ↔
  `serverStore`; manchete do card vem só do motor determinístico (guardrail
  CVM); stop/alvo nunca são vetados; histórico (`qa/`, `ESTADO-*`,
  `CHECKOUT-*`, RELEASES) não se reescreve; login obrigatório; execução
  tudo-ou-nada por desenho (sem fill parcial).
- Suíte canônica de validação: `bash scripts/executar.sh --testes` (as duas
  suítes — `scripts/test.sh` sozinho não conta).

## Referência (anexar/ler)

- `/Users/acamerini/dev/bolsia/b3-agente/.planning/intel/decisions.md` — ledger das 19 ADRs
- `/Users/acamerini/dev/bolsia/b3-agente/.planning/intel/constraints.md` — as 5 SPECs
- `/Users/acamerini/dev/bolsia/b3-agente/.planning/intel/context.md` — as 8 DOCs
- `/Users/acamerini/dev/bolsia/b3-agente/.planning/intel/SYNTHESIS.md` — resumo do ingest
- `/Users/acamerini/dev/bolsia/b3-agente/.planning/INGEST-CONFLICTS.md` — relatório de conflito
- `/Users/acamerini/dev/bolsia/b3-agente/.planning/PROJECT.md` — estado do produto, decisão de milestone pendente
- `/Users/acamerini/dev/bolsia/b3-agente/CLAUDE.md` — stack, convenções, guardrails (já cobre o que não está aqui)
- `/Users/acamerini/dev/MCP/docs/boris-pp-00-mapa-de-realidade.md` — a correção completa (repositório errado, achados 1-3)
- `/Users/acamerini/dev/MCP/docs/adr-fusao-b3agente-mydata.md` — ADR original do `mydata`, **superada**, mantida só como registro histórico do raciocínio pré-correção

## Artefatos superados (não usar como contexto ativo)

- `/Users/acamerini/dev/MCP/docs/cowork-project-context.md` — versão anterior deste mesmo arquivo, contexto errado
- `~/dev/rail/prod/b3agente-main` — cópia morta do Boris, desconsiderar

## Próxima ação

`/gsd-explore` neste repositório para pensar a decisão 2 (dedup módulo a
módulo) sem ainda comprometer escopo, depois `/gsd-new-milestone` quando a
direção firmar — condicionado a fechar a decisão 1 (milestone novo vs.
backlog) primeiro.
