---
title: Revisão de arquitetura — consolidar motor de opções no MCP e desenhar o Boris+ como plataforma para o ecossistema de mercado de capitais brasileiro
date: 2026-09-20
priority: high
---

# Revisão de arquitetura — MCP único + visão de plataforma B3

Levantado durante o checkpoint humano da Fase 34 (`34-04-PLAN.md`, Task 1),
quando o Alex confirmou que **dois** hosts MCP relacionados a opções estão
no ar: `https://mcp.semente.dev/health` (o serviço "oficial", autenticado
por bearer de máquina, já parcialmente integrado — ver abaixo) e
`https://b-mcp.semente.dev` (o portal pessoal/dev). O Alex pediu duas
coisas, nesta ordem:

1. Colocar **todos** os tools de opções no mesmo MCP (hoje divididos entre
   motor interno do Boris e `mcp.semente.dev` — ver "Estado atual").
2. Uma **revisão completa da arquitetura** para decidir o melhor desenho
   para o ambiente, com uma ambição maior declarada por ele: **que este
   ambiente sirva de base para suportar todo o ecossistema do mercado de
   capitais brasileiro** — não só o Boris+ como está hoje.

Isso é maior que um todo de acompanhamento — é uma decisão estratégica de
arquitetura/produto. Registrado aqui para não se perder, com o estado
factual levantado até agora, para quem for planejar essa revisão não
precisar redescobrir.

## Estado atual (verificado por leitura de código + notas, 2026-09-20)

O subsistema de Opções do Boris tem **dois motores separados** hoje, não
um só:

1. **Vigias/setups salvos** (condição técnica DSL, ex.: "IFR de 2 períodos
   abaixo de 25") — já usa `mcp.semente.dev` desde a Fase 27 (produção).
   `server/app/mcp_client.py` é a fronteira única (ADR-027, Decisão 1);
   `server/app/opcoes_vigias.py`/`options_mcp_api.py` consomem por cima
   dela. Tools usadas: `create_setup`/`list_setups`/`deactivate_setup`/
   `get_setup_chart`/`evaluate_setups`.
2. **Descoberta/análise de estrutura de opções** (venda coberta, put,
   collar — o que `SecaoDescobrir`/`SecaoAnalisar`/`SecaoComparar` mostram
   na aba Opções, ranking por prêmio÷perda máxima) — **motor interno**
   (`server/app/opcoes_lastreadas.py`, seleção por `liquidity_score >= 40`
   + strike extremo). Mantido fora do MCP por decisão explícita de
   2026-09-02 (`.planning/notes/opcoes-v2-b-mcp-exploracao.md`, seção
   "Arquitetura decidida — independência do b-mcp no v1", Estratégia B
   escolhida sobre a Estratégia C porque `plano-mcp-servico.md` estava "em
   avaliação, não aprovado" na época).

**"Colocar todos os tools no mesmo MCP" = migrar o item 2 pra também
chamar `mcp.semente.dev`** (tools `find_tradable_options`/
`evaluate_option_structure`), completando a Estratégia C que ficou
descartada "por ora" — agora que o Alex confirma o serviço no ar.

## Conflito real já medido, não hipotético

`opcoes_lastreadas.py` (motor interno, produção) escolhe contrato por
**liquidez** (`liquidity_score`); `~/dev/MCP/servers/mydata/estruturas.py`
(o motor por trás de `evaluate_option_structure`) escolhe por **delta**
(0,25 asa / 0,5 ATM) e **não filtra liquidez**. São réguas incompatíveis —
migrar mudaria QUAIS opções são propostas/ranqueadas, não é troca de
transporte invisível. Precisa de reconciliação de critério antes de
qualquer migração de código, não é decisão técnica pura.

## Por que isso não entrou na Fase 34

A Fase 34 (Navegação hub + workspace) e a Fase 33 antes dela foram
desenhadas explicitamente para separar o eixo "estrutura de arquivo/
navegação" do eixo "motor de dados" — ver `.planning/ROADMAP.md`, nota de
Phase Numbering da Fase 33/34: "não misturar o eixo estrutura de arquivo
com o eixo fluxo de navegação numa fase só". REORG-07 (Fase 33, já
verificado 7/7) trava que a seleção do motor (`top`/`meta`) chega imutável
a qualquer seção — trocar o motor por trás dela é exatamente o tipo de
mudança que essas fases decidiram adiar. Migrar o motor DURANTE a Fase 34
reabriria os dois eixos ao mesmo tempo, sem checkpoint intermediário.

## Escopo da revisão pedida (para quem for planejar)

O pedido do Alex vai além de "qual MCP usar para opções" — é repensar a
arquitetura de dados/integração do Boris+ com o objetivo de servir como
plataforma para o ecossistema de mercado de capitais brasileiro em geral,
não só a feature de opções. Isso toca (lista não exaustiva, a levantar na
revisão):

- Qual o papel de `mydata.semente.dev` (REST, hub de mercado) vs.
  `mcp.semente.dev` (MCP autenticado, hoje só vigias/setups) vs. o motor
  interno do Boris — um serviço por tipo de dado, ou consolidação?
- Reconciliação da régua de seleção (liquidez vs. delta) se o motor de
  estrutura migrar.
- Orçamento/rate-limit compartilhado (`mydata_budget.py`, WR-01) sob uma
  carga maior se mais chamadas migrarem pro hub.
- Guardrail CVM (princípio 5 do CLAUDE.md — cálculo nunca pela IA,
  determinístico) precisa continuar valendo qualquer que seja o desenho.
- Ambição declarada de plataforma B3-ampla: que outros produtos/instrumentos
  (ações, futuros, renda fixa?) essa arquitetura precisaria suportar além
  de opções — isso pode mudar a resposta de "qual serviço fica dono de
  quê".

## Fontes já levantadas (não redescobrir)

- `.planning/notes/opcoes-v2-b-mcp-exploracao.md` — exploração completa
  2026-09-01/02, as 5 estratégias avaliadas, achado do conflito de régua
- `.planning/seeds/opcoes-v2-setups-propostos-via-b-mcp.md` — resumo/seed
- `.planning/todos/pending/opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp.md`
  — todo anterior sobre o mesmo tema, ainda pendente, superado em parte por
  este (o Alex acabou de confirmar `mcp.semente.dev` no ar)
- `~/dev/MCP/docs/plano-mcp-servico.md` — o plano do serviço MCP (fora
  deste repo, ler se acessível)
- `server/app/mcp_client.py`, `opcoes_vigias.py`, `options_mcp_api.py`,
  `opcoes_lastreadas.py` — estado real de código hoje

## Próximo passo sugerido

Não decidir agora, dentro da Fase 34. Quando a Fase 34 fechar, propor ao
Alex `/gsd-new-milestone` ou pesquisa dedicada (`gsd-project-researcher`)
para esta revisão de arquitetura — é maior que uma fase, tem cheiro de
milestone próprio dado o tamanho da ambição declarada.
