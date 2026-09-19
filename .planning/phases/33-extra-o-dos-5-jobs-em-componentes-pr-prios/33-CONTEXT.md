# Phase 33: Extração dos 5 jobs em componentes próprios - Context

**Gathered:** 2026-09-19
**Status:** Ready for planning

<domain>
## Phase Boundary

A sub-aba "Setups" da aba Opções mistura hoje 5 trabalhos diferentes numa
rolagem única: descobrir oportunidades cross-carteira (Blocos A+B), gerenciar
vigias, analisar um ticker manualmente, comparar vencimentos, e
gerenciar/criar setups salvos. Esta fase extrai cada job para seu próprio
componente em `web/src/opcoes/`, preservando exatamente comportamento, dados
e ordem visível ao usuário — zero funcionalidade nova, exceto as duas
exceções explícitas registradas em D-4. É pré-condição estrutural para a
Fase 34 (redesenho de navegação hub+workspace), que só começa depois desta
fechar com suíte verde.

</domain>

<decisions>
## Implementation Decisions

### Nomenclatura
- **D-01:** Cinco componentes novos: `SecaoDescobrir`, `SecaoVigias`,
  `SecaoAnalisar`, `SecaoComparar`, `SecaoSetups`, todos em
  `web/src/opcoes/`. Padrão "Secao*" sinaliza que são job-sections do hub.
  Os componentes hoje existentes que cada seção vai conter/reusar
  (`OportunidadesOpcoes.jsx`, `CuradoriaEstruturas.jsx`, `CriarSetup.jsx`)
  NÃO são renomeados — continuam sendo o motor de dados+ranking dentro da
  seção nova.

### Estratégia de guardião
- **D-02:** Os 5 guardiões afetados (`test_opcoes_subabas_ui.mjs`,
  `test_opcoes_consolidacao_ui.mjs`, `test_opcoes_analisar_ui.mjs`,
  `test_opcoes_vigias_ui.mjs`, `test_opcoes_mcp_aba_ui.mjs`) passam a
  verificar por varredura de **diretório inteiro** (`readdirSync` sobre
  `web/src/opcoes/`), não por caminho de arquivo fixo. Precedente exato a
  mirrorar literalmente: `web/tests/test_opcoes_subabas_ui.mjs:101-114`
  ("nenhum arquivo de web/src/opcoes/ importa App.jsx") — já escaneia o
  diretório inteiro com sanity-check de contagem mínima de arquivos e
  comentário datado explicando por quê. Justificativa: sobrevive a futuras
  extrações sem reescrita — REORG-06 (guardrail CVM de manchete, hoje só em
  `SubAbaOperar`) e qualquer seção nova herdam a cobertura automaticamente.

### Ordem de extração
- **D-03:** 5 planos sequenciais (não 1 grande), cada um extraindo
  exatamente um job, com suíte canônica verde antes do próximo começar.
  Ordem (do mais isolado ao mais entrelaçado):
  1. `SecaoVigias` — menos acoplado aos outros jobs
  2. `SecaoDescobrir` — Blocos A+B + a frase-ponte (`cp.duasLeiturasIntro`,
     `OpcoesScreen.jsx:713`) junto, porque é mitigação regulatória D-05
     amarrada à adjacência física com o Bloco B
  3. `SecaoSetups` — "setups gravados" + "criar um setup"
  4. `SecaoComparar` — "comparar os vencimentos"
  5. `SecaoAnalisar` — manual builder + fold-in do fetch redundante (D-04),
     por último por ser o mais entrelaçado com `SubAbaOperar`
  Cada extração é só mover JSX+state local pro componente novo e passar
  dado por prop — `OpcoesScreen.jsx` continua único chamador de
  `useOpcoesMcp`/`useOpcoesPropostas` (REORG-03/04). Estado consumido por
  2+ jobs (`ticker`, `tese`, `vencimento`, `lote`) NÃO desce para nenhuma
  seção — fica no orquestrador.

### Fold-in de todos pendentes
- **D-04a (fold-in 1, sem exceção de escopo):** Fetch redundante de
  gate/proposta em `SubAbaOperar`
  (`.planning/todos/pending/subaba-operar-fetch-redundante-gate-proposta.md`).
  Ataca exatamente o que REORG-03/04 já exige — não é escopo extra de
  verdade. Ao extrair `SecaoAnalisar`, subir `opcoesPorTicker`/
  `opcoesCarregando` (saída de `useOpcoesPropostas`, já calculada no topo)
  por prop, em vez dos dois `useEffect` locais. Cair no fetch local só
  quando o ticker não tiver sido varrido no fan-out do topo. Atualizar
  `test_opcoes_subabas_ui.mjs` regra 3 com nota datada quando a contagem
  cair de 1 pra 0 nesse componente.
- **D-04b (fold-in 2, EXCEÇÃO EXPLÍCITA a REORG-02):** Carimbo de frescor
  nos Blocos A/B
  (`.planning/todos/pending/carimbo-frescor-blocos-cross-carteira.md`).
  Lacuna real do princípio 3 do CLAUDE.md, mas é UI nova — contraria "zero
  feature nova". Aceito pelo Alex como exceção registrada, não scope creep
  silencioso. Descoberta necessária antes de implementar: verificar se o
  dado de frescor já existe na resposta das rotas de
  `OportunidadesOpcoes`/`CuradoriaEstruturas` (o bloco de leitura técnica
  por ticker já exibe carimbo — achar a fonte). Se não existir no backend,
  atenção a `mydata_budget` (Fase 31 D1) antes de mexer na rota da
  curadoria. Usar vocabulário de frescor já existente via `copy.js`, não
  inventar rótulo novo. Encaixa dentro da extração de `SecaoDescobrir`
  (passo 2 de D-03).
- Todos NÃO dobrados: "acompanhar aprovação do serviço MCP" (tracking
  externo, irrelevante a esta fase) e "medir rate-limit do mydata" (fora do
  escopo de UI desta fase).

### Claude's Discretion
Detalhamento exato de props/assinatura de cada `Secao*` (nomes de prop,
formato exato do JSX movido) fica a critério de quem planeja/executa cada um
dos 5 planos — as decisões acima fixam limites (o QUE preservar, a ORDEM, o
QUE não pode quebrar), não a forma exata do código.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Pesquisa desta milestone (base de todas as decisões acima)
- `.planning/research/STACK.md` — três primitivos já existentes mapeados
  para os 5 jobs, zero dependência nova
- `.planning/research/FEATURES.md` — hub+workspace, table-stakes/anti-
  features, recomendação de destinos separados
- `.planning/research/ARCHITECTURE.md` — pontos de integração hook/estado,
  risco de guardião, ordem de build sugerida (base de D-02/D-03)
- `.planning/research/PITFALLS.md` — 7 pitfalls críticos (guardião cego a
  migração de arquivo, narração vs. decisão, frase-ponte D-05, estado de
  erro enterrado, backlog B2)
- `.planning/research/SUMMARY.md` — síntese executiva das 4 pesquisas

### Requisitos e roadmap
- `.planning/REQUIREMENTS.md` — REORG-01..07 (esta fase), NAV-01..06 (Fase
  34, fora de escopo aqui)
- `.planning/ROADMAP.md` — Fase 33/34, dependência bloqueante entre elas

### Todos dobrados nesta fase
- `.planning/todos/pending/subaba-operar-fetch-redundante-gate-proposta.md`
- `.planning/todos/pending/carimbo-frescor-blocos-cross-carteira.md`

### Guardrails do repositório
- `CLAUDE.md` (raiz) — princípios 3, 4 e 5; guardrail CVM de manchete;
  paridade `deviceStore`/`serverStore`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `web/tests/test_opcoes_subabas_ui.mjs:101-114` — padrão de varredura por
  diretório já implementado e testado (mirrorar literalmente para D-02)
- `useOpcoesMcp.js`/`useOpcoesPropostas.js` — hooks de dados já centralizados
  no orquestrador, só precisam de distribuição por prop mais granular
- `CriarSetup.jsx` — já é módulo próprio, só muda quem o envolve

### Established Patterns
- Extração de componente sem tocar hooks de dados: mesmo padrão já usado
  nas Fases 28/32 (`SubAbaOperar`, `OportunidadesOpcoes`,
  `CuradoriaEstruturas` já nasceram assim)
- Guardrail CVM de manchete: hoje escopado a `SubAbaOperar`
  (`test_opcoes_subabas_ui.mjs`) — precisa generalizar via D-02

### Integration Points
- `OpcoesScreen.jsx` continua o único ponto de chamada de
  `useOpcoesMcp`/`useOpcoesPropostas` e dono do estado compartilhado
  (`ticker`, `tese`, `vencimento`, `lote`, `subaba`)
- `curadoriaAtiva` vive em `App.jsx`, fora desta fase — não pode ser tocado
  nem re-implementado por nenhuma seção nova

</code_context>

<specifics>
## Specific Ideas

Nenhuma referência visual externa — a fase é reorganização de código
existente, não redesenho visual (isso é Fase 34).

</specifics>

<deferred>
## Deferred Ideas

- Redesenho de navegação (hub + workspace, botão de volta, jobs 3/4/5
  compartilhando leitura paga) — Fase 34, já roteirizada em
  `.planning/ROADMAP.md`
- Explicação com profundidade adaptativa, modelo de progresso do aprendiz,
  desafio personalizado por padrão observado — v2 requirements, fora do
  roadmap deste milestone (`.planning/REQUIREMENTS.md`)
- Fechar o backlog B2 (estado não sobrevive à troca de aba) — dívida
  pré-existente (Fase 26, v1.4); a pesquisa recomendou aproveitar esta fase
  pra fechar, mas o Alex não pediu — fica registrado para decisão futura

### Reviewed Todos (not folded)
- "Acompanhar aprovação do serviço MCP autenticado" — item de tracking
  externo, sem ação de código nesta fase
- "Medir rate-limit real do mydata" — fora do escopo de UI desta fase

</deferred>

---

*Phase: 33-Extração dos 5 jobs em componentes próprios*
*Context gathered: 2026-09-19*
