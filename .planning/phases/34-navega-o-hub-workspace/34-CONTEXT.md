# Phase 34: Navegação hub + workspace - Context

**Gathered:** 2026-09-20
**Status:** Ready for planning

<domain>
## Phase Boundary

A sub-aba "Setups" da aba Opções (já reorganizada em 5 componentes próprios
pela Fase 33) troca a rolagem única por dois modos, reusando o estado
`ticker` que já existe: **hub** (sem ticker selecionado — descoberta
cross-carteira, vigias, lista de setups salvos) e **workspace** (ticker
selecionado — análise manual, comparação de vencimentos, criação de setup
para aquele ticker). É reshuffle de renderização sobre estado existente —
zero novo mecanismo de dado, zero rota, zero funcionalidade que não exista
hoje na sub-aba Setups.

</domain>

<decisions>
## Implementation Decisions

### Divisão hub × workspace
- **D-01:** "Setups salvos" se divide em duas metades. A **listagem**
  completa (todos os setups da carteira, cross-ticker) fica no **hub**,
  seção própria ao lado de vigias — é isso que NAV-01 descreve. **Criar** um
  setup novo (exige ticker/tese/vencimento) fica no **workspace**, como uma
  terceira aba ao lado de Analisar e Comparar, reusando a leitura MCP já
  paga do ticker selecionado — é isso que NAV-05 descreve. Resolve a
  aparente contradição entre NAV-01 ("setups salvos" no hub) e NAV-05
  ("gerenciar setups salvos" dentro do workspace): os dois estão certos,
  cada um descrevendo a metade certa. `SecaoSetups.jsx` (Fase 33) se
  particiona ao longo dessa mesma linha lista/criação — não precisa virar
  dois arquivos, mas o componente do workspace só renderiza o bloco de
  criação, não a lista inteira.
- **D-02:** Pill row do workspace tem **3 abas**: Analisar / Comparar /
  Criar Setup — não 2. Mesmo componente de pill já usado em Setups/Operar
  (um nível abaixo), consistente visualmente, sem componente novo.

### Estado do workspace
- **D-03:** Sair do workspace (botão voltar) **reseta** tese/vencimento/lote
  sempre — reentrar no mesmo ticker depois começa limpo, igual ao
  comportamento de hoje. Decisão explícita: **não** fechar o backlog B2
  (estado não sobrevive à troca de seção/aba) de passagem nesta fase — ficar
  fiel a "reorganização pura", sem estado novo escondido. B2 continua
  registrado como dívida pré-existente (Fase 26, v1.4), fora de escopo.

### Ordem e affordance do hub
- **D-04:** Ordem fixa das seções do hub, igual à recomendação da pesquisa e
  à ordem natural já existente no código: frase-ponte + Bloco A + Bloco B
  (descoberta) → Meus vigias → Meus setups salvos (lista).
- **D-05:** "Você está aqui" / voltar ao hub (NAV-03: um único botão, sem
  breadcrumb, sem histórico) vira um **header fixo no topo do workspace**:
  nome do ticker selecionado + botão "Voltar" — não um botão solto sem
  contexto. Resolve o item que a pesquisa (`FEATURES.md`) aponta como o de
  maior risco de virar feature nova: entrar no workspace sem esse header
  faria o usuário perder a noção de que saiu do modo hub. Continua sendo só
  um botão de volta — nenhum histórico, nenhuma pilha de navegação.

### Todos pendentes revisados (não dobrados)
- `carimbo-frescor-blocos-cross-carteira.md` e
  `subaba-operar-fetch-redundante-gate-proposta.md` já foram dobrados e
  executados na Fase 33 (D-04a/D-04b do `33-CONTEXT.md`) — os arquivos em
  `.planning/todos/pending/` ficaram esquecidos lá por dívida de processo,
  não são escopo desta fase. Fica anotado para alguém arquivar depois.
- `medir-rate-limit-mydata.md` e
  `opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp.md` — o matcher
  (`todo.match-phase`) os encontrou por keyword ("hub" no segundo, "mydata"
  em ambos), mas nenhum é sobre navegação de UI; são tracking de
  infraestrutura externa (rate-limit do provider, aprovação de serviço).
  Fora do domínio desta fase, não dobrados.

### Claude's Discretion
Detalhamento exato de props/assinatura da divisão de `SecaoSetups.jsx`
(nomes de prop, se vira sub-componente interno ou continua um arquivo só
com um prop `modo: "lista" | "criar"`), estilo exato do header fixo do
workspace (D-05), e onde exatamente o hook `useOpcoesPropostas`/
`useOpcoesMcp` é chamado (continuam no orquestrador `OpcoesScreen.jsx`,
REORG-03/04 da Fase 33 não muda) ficam a critério de quem planeja/executa.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Pesquisa desta milestone (base das decisões acima)
- `.planning/research/FEATURES.md` — linhas 26-51 (hub/workspace split via
  `ticker` existente, "you are here" affordance como item de maior risco de
  scope-creep, ordem fixa de seções, setups salvos como seção própria)
- `.planning/research/PITFALLS.md` — linha 340-451 (Pitfall 6: estado de
  navegação não sobrevive à troca de seção — decisão D-03 acima é a resposta
  explícita a esse pitfall: resetar, não preservar)
- `.planning/research/ARCHITECTURE.md`, `.planning/research/SUMMARY.md` —
  síntese e pontos de integração já mapeados no milestone

### Requisitos e roadmap
- `.planning/REQUIREMENTS.md` — NAV-01..06 (esta fase)
- `.planning/ROADMAP.md` — seção "Phase 34: Navegação hub + workspace"
  (Goal/Success Criteria); depende do fechamento verificado da Fase 33
  (`.planning/phases/33-.../33-VERIFICATION.md`, PASSED 7/7, 2026-09-20)

### Fase anterior (base estrutural)
- `.planning/phases/33-extra-o-dos-5-jobs-em-componentes-pr-prios/33-CONTEXT.md`
  — nomes/contratos dos 5 componentes `Secao*.jsx` que esta fase reorganiza
  em hub/workspace, sem recriar
- `web/src/opcoes/OpcoesScreen.jsx` — orquestrador atual, dono do estado
  `ticker`/`tese`/`vencimento`/`lote`/`subaba`; continua único chamador de
  `useOpcoesMcp`/`useOpcoesPropostas` (REORG-03/04, invariante que esta fase
  não pode quebrar)

### Guardrails do repositório
- `CLAUDE.md` (raiz) — princípio 3 (frescor/staleness), guardrail CVM de
  manchete (D-02 da Fase 33, generalizado por diretório — continua valendo
  para qualquer render novo desta fase)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ticker` (estado já existente em `OpcoesScreen.jsx`) — único gatilho
  necessário pro split hub/workspace (`ticker ? <Workspace/> : <Hub/>`),
  sem novo estado
- Pill row de Setups/Operar (componente já existente) — reusar um nível
  abaixo para Analisar/Comparar/Criar Setup dentro do workspace (D-02)
- Os 5 `Secao*.jsx` da Fase 33 — cada um já isolado, prontos pra distribuir
  entre hub e workspace por composição, sem reescrever lógica interna

### Established Patterns
- Guardrail de diretório (D-02 da Fase 33) — qualquer seção nova/dividida
  que renderize `.manchete` precisa continuar coberta pela varredura de
  `web/src/opcoes/`
- `useOpcoesPropostas`/`useOpcoesMcp` chamados uma vez só no orquestrador —
  hub/workspace são só destinos de renderização diferentes do mesmo dado,
  não novos consumidores dos hooks

### Integration Points
- `OpcoesScreen.jsx` continua o único dono do estado compartilhado e do
  toggle hub/workspace — nenhuma seção decide sozinha se está em modo hub ou
  workspace

</code_context>

<specifics>
## Specific Ideas

Nenhuma referência visual externa nova além da já registrada em
`FEATURES.md` (ThinkorSwim/Barchart/tastytrade como precedentes de mercado,
já processados na pesquisa da milestone). Esta fase é redesenho de fluxo de
navegação sobre componentes já existentes, não redesenho visual do zero.

</specifics>

<deferred>
## Deferred Ideas

- Fechar o backlog B2 (estado não sobrevive à troca de aba/seção) —
  explicitamente NÃO dobrado nesta fase (D-03) para manter escopo de
  "reorganização pura"; seguirá registrado como dívida pré-existente
- Personalização (progresso do aprendiz, desafio por padrão observado,
  explicação adaptativa) — Fases 2-4 do plano de UX maior, fora do roadmap
  deste milestone
- Deep-link direto pra um ticker específico a partir de um card de vigia ou
  setup salvo (pular a seleção manual no workspace) — feature nova, não
  reorganização; não veio à tona na discussão mas fica registrado como
  candidato natural de fase futura caso surja

### Reviewed Todos (not folded)
- `medir-rate-limit-mydata.md` — tracking de infraestrutura externa, sem
  ação de UI nesta fase
- `opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp.md` — tracking de aprovação
  de serviço externo, sem ação de código nesta fase

</deferred>

---

*Phase: 34-Navegação hub + workspace*
*Context gathered: 2026-09-20*
