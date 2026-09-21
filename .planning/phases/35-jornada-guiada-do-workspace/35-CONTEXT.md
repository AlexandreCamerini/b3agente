# Phase 35: Jornada Guiada do Workspace - Context

**Gathered:** 2026-09-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Dentro do workspace da sub-aba "Setups" (ticker selecionado), o usuário passa
por um portão obrigatório de leitura paga ("Ler no serviço de opções", 3
chamadas) antes de qualquer uma das 3 pills (Analisar/Comparar/Setups
salvos) mostrar conteúdo útil. Hoje os 3 CTAs principais da jornada ("Ler no
serviço", "Montar estrutura", "Ver possibilidades") usam o MESMO estilo
visual neutro de qualquer botão secundário/exploratório do app — zero
hierarquia, zero indicação de onde o usuário está ou o que fazer a seguir.
Esta fase corrige isso: hierarquia visual real no CTA do próximo passo, um
indicador de progresso honesto (sem fingir sequência onde não há), e a
correção de um bug colateral encontrado durante a discussão (Setups salvos
preso atrás do portão de leitura sem precisar dela). Não é redesenho visual
do zero nem mudança de arquitetura de dados — é hierarquia + progresso sobre
a estrutura de componentes já existente (`OpcoesScreen.jsx` +
`SecaoAnalisar.jsx`/`SecaoComparar.jsx`/`SecaoSetups.jsx`).

</domain>

<decisions>
## Implementation Decisions

### Estrutura do fluxo — Opção A (escolhida sobre B e C)
- **D-01:** O bloco "LEITURA DO ATIVO" (`OpcoesScreen.jsx:540-563`) ganha
  rótulo de estágio "Passo 1 de 2". O carril de pills (`workspacePillRow`)
  ganha rótulo "Passo 2 de 2" — **como estágio único**, nunca numerando
  Analisar/Comparar entre si (elas são duas ações independentes dentro do
  mesmo estágio, não uma sequência 2→3). Zero mudança de arquitetura: o
  `temLeitura`/branch 4 (DADOS) continua exatamente como é hoje — isto é
  rótulo/copy sobre a estrutura existente, não reabertura de condição de
  render.
- **D-02 (bug corrigido de graça, achado nesta discussão):** `SecaoSetups`
  não depende de `temLeitura` (confirmado por leitura direta —
  `SecaoSetups.jsx` nunca checa a flag), mas hoje o bloco de leitura
  aparece incondicionalmente acima do carril mesmo quando a pill ativa é
  "Setups salvos", bloqueando visualmente quem só quer ver/criar um setup
  salvo. Corrigir: o convite de leitura (`blocoLeituraDoServico`) só
  aparece quando a pill ativa é Analisar ou Comparar — nunca quando é
  Setups salvos.
- **Rejeitada — Opção B** (carril numerado "1. Ler ativo → 2. Analisar →
  3. Comparar" com cadeado nas pills bloqueadas, Setups salvos deslocada
  para fora do carril sequencial): fica registrada como candidata futura se
  o Alex quiser a sensação de wizard mais forte — não escolhida agora
  porque desloca a posição de "Setups salvos" (mudança de layout, não só
  estilo) sem necessidade comprovada.
- **Rejeitada — Opção C** (absorver o convite de leitura dentro do próprio
  render da pill Analisar): contraria decisão de arquitetura já fechada na
  Fase 27 (`OpcoesScreen.jsx:517-536`, comentário citando ADR-027 Emenda 2
  — a pill Analisar só renderiza no ramo que JÁ depende de `temLeitura`;
  mover o convite pra lá tornaria o próprio convite inalcançável). Não
  reabrir esta decisão nesta fase.

### Hierarquia visual do CTA
- **D-03:** Extensão aprovada do "reserved-for" de `T.accent` do
  `34-UI-SPEC.md` (hoje só a aba ativa do carril). Novo `BOTAO_PRIMARIO` —
  mesma geometria do `BOTAO` atual (`minHeight`/`padding`/`borderRadius`/
  `fontWeight`/`fontSize` idênticos), só troca `border: none`,
  `background: T.accent`, `color: "#fff"`. Precedente já em produção:
  `CuradoriaEstruturas.jsx:268` (sub-aba Operador) usa exatamente este
  padrão (fill sólido de accent) para o botão de confirmação — a distinção
  entre "accent = aba ativa" e "accent = CTA primário" é de FORMA
  (borda+tint vs. preenchido sólido), não de cor nova.
- **D-04:** `BOTAO_PRIMARIO` aplica-se exatamente a 3 botões: "Ler no
  serviço de opções" (`OpcoesScreen.jsx:552-560`), "Montar estrutura"
  (`SecaoAnalisar.jsx:320-329`), "Ver possibilidades"
  (`SecaoComparar.jsx:152-161`). Todo o resto ("Ver a cadeia", "Ver as
  operáveis", botões de `SecaoSetups.jsx`, "Voltar" do
  `WorkspaceHeader.jsx`) permanece com o `BOTAO` neutro atual — são
  exploração opcional ou navegação, não o próximo passo obrigatório.
- **D-05:** Estado "desabilitado" do `BOTAO_PRIMARIO` usa `opacity: 0.55`
  (não o `0.45` do botão neutro — um preenchido a 0.45 ainda lê como
  vívido/clicável sobre fundo escuro). Precedente:
  `CuradoriaEstruturas.jsx:268` já usa `0.55` para o mesmo botão preenchido
  em estado bloqueado. Nunca some — mesma regra de sempre.
- **D-06:** Estado "concluído" tem dois tratamentos, porque o
  comportamento por trás já é diferente hoje:
  - **Leitura (a ação some):** o bloco inteiro já desaparece quando
    `temLeitura` é verdadeiro (`OpcoesScreen.jsx:700`, comportamento atual
    preservado). O `Kicker` "LEITURA DO ATIVO" que passa a ocupar aquele
    espaço ganha sufixo discreto "· leitura já feita" (cor `T.textMuted`,
    mesma do próprio Kicker — é metadado, não celebração).
  - **Montar estrutura / Ver possibilidades (a ação convive com o
    resultado, re-clicável):** o botão NÃO some nem desabilita depois do
    clique — trocar tese/lote e montar de novo é uso legítimo (comparar
    cenários). Uma marca neutra `✓` (cor `T.textMuted`, nunca `T.positive`/
    `T.negative` — esse par é reservado para direção financeira,
    `PropostaLastreada.jsx`, e reusar aqui colidiria com "alta"/"baixa" no
    mesmo campo visual) aparece entre o botão e o resultado.
- **D-07 (risco aberto, não resolvido nesta discussão):** o subtexto de
  custo dentro do botão preenchido precisa de uma cor clara sobre o fundo
  `T.accent` (proposta: branco a ~72% via `color-mix`, técnica já usada no
  repo em `PropostaLastreada.jsx:254`). Contraste no TEMA CLARO não foi
  verificado nesta discussão — quem executar/verificar esta fase MUST
  confirmar contraste real nos dois temas antes de fechar a fase, não
  assumir que passa porque o par 100%/100% (branco puro sobre accent) já
  está em produção no Operador.

### Indicador de progresso
- **D-08:** Linguagem numerada "Passo 1 de 2" / "Passo 2 de 2" — mas
  **só no nível porta→carril** (2 estágios reais), nunca numerando
  Analisar/Comparar entre si (ver D-01). Além da numeração, uma linha de
  transição (`AJUDA`, token já existente, zero cor nova) aparece acima do
  carril quando `temLeitura`: "Leitura concluída — escolha Analisar ou
  Comparar." — o texto exato é candidato a virar chave `cp.*` (Claude's
  Discretion, ver abaixo), este é o conteúdo semântico decidido.

### Claude's Discretion
- Redação final das strings de copy (viram chaves `cp.*` em `copy.js`
  seguindo o padrão de vocabulário por modo Estudo/Operador já
  estabelecido em toda a pasta `web/src/opcoes/` — não decidido aqui se
  precisam divergir de tom entre os dois modos, como `opcoesAbaSetupsSalvos`
  já diverge).
- Ajuste fino do percentual de `color-mix` para o subtexto de custo, depois
  da verificação visual de contraste no tema claro (D-07).
- Nome exato das novas constantes de estilo (`BOTAO_PRIMARIO`,
  `CUSTO_NO_BOTAO_PRIMARIO`, `MARCA_RESULTADO`, `desabilitadoPrimario`) e se
  centralizam em `uiOpcoes.jsx` (module de primitivos compartilhados já
  usado por `SecaoAnalisar.jsx`/`SecaoComparar.jsx`) ou ficam duplicadas por
  arquivo como o `BOTAO` atual já é hoje — o planner decide olhando o
  padrão real de duplicação já existente antes de introduzir a primeira
  centralização nova.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Decisão de UI que esta fase estende
- `.planning/milestones/v1.6-phases/34-navega-o-hub-workspace/34-UI-SPEC.md`
  — a linha "Accent reserved for: the active state of pill-row tabs.
  Nothing new gets accent in this phase" é a regra que D-03 estende
  explicitamente (aprovado pelo Alex nesta discussão)

### Decisão de arquitetura que esta fase NÃO reabre
- `web/src/opcoes/OpcoesScreen.jsx:517-536` — comentário da Fase 27
  (ADR-027 Emenda 2) explicando por que o convite de leitura não pode
  morar dentro da pill Analisar (Opção C, rejeitada acima)

### Requisitos e roadmap
- `.planning/REQUIREMENTS.md` — JORN-01, JORN-02, JORN-03 (esta fase)
- `.planning/ROADMAP.md` — seção "Phase 35: Jornada Guiada do Workspace"

### Precedentes de código citados nas decisões
- `web/src/opcoes/CuradoriaEstruturas.jsx:268` — precedente em produção do
  botão preenchido com `T.accent`/`#fff` e `opacity: 0.55` desabilitado
- `web/src/opcoes/PropostaLastreada.jsx:183,254` — regra de que
  `T.positive`/`T.negative` são reservados a direção financeira, nunca
  reusados para "sucesso" de UI; e o precedente de `color-mix()` já em uso
- `web/src/opcoes/uiOpcoes.jsx` — módulo de primitivos compartilhados
  (`Kicker`, `Aviso`, `ErroDoMcp`, `Linha`, `RazaoGanhoPerda`) — candidato
  natural para centralizar os estilos novos, se o planner decidir por isso

### Guardrails do repositório
- `CLAUDE.md` (raiz) — princípio 5 (nunca inventar número) é a razão
  explícita por trás de D-01/D-08 (não numerar Analisar/Comparar como
  passos sequenciais que não existem)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `BOTAO`/`CAIXA`/`CAMPO`/`AJUDA` (objetos de estilo já declarados,
  duplicados por arquivo hoje — `OpcoesScreen.jsx`, `SecaoAnalisar.jsx`,
  `SecaoComparar.jsx`) — `BOTAO_PRIMARIO` deve seguir a MESMA geometria,
  só variando cor/fundo
- `Kicker` (`uiOpcoes.jsx`) já aceita `children` — o sufixo "· leitura já
  feita" (D-06) não exige mudança no componente, só no conteúdo passado
- `desabilitado(cond)` (padrão já usado nos 3 arquivos) — `BOTAO_PRIMARIO`
  precisa do equivalente com `0.55` (D-05), não reusar o `0.45` existente

### Established Patterns
- Custo declarado DENTRO do botão, segunda linha (`CUSTO_NO_BOTAO`) — já
  correto, não mexer; só precisa de variante de cor para fundo preenchido
  (D-07)
- Botão desabilitado sempre visível (nunca `display: none`) — regra a
  preservar no `BOTAO_PRIMARIO` também
- `color-mix()` já em uso no repo (`PropostaLastreada.jsx:254`) — técnica
  válida a reaproveitar para D-07, não introduzir abordagem nova

### Integration Points
- `OpcoesScreen.jsx` continua dono de `podePedirLeitura`/
  `blocoLeituraDoServico` — D-02 (gate condicionado à pill ativa) se
  implementa ali, checando `abaWorkspace` (estado já existente da Fase
  34-03) antes de renderizar o bloco de leitura

</code_context>

<specifics>
## Specific Ideas

Valores de estilo concretos já propostos (ponto de partida para o planner,
ajustar só se o valor literal não bater com a resolução real do token):

```js
const BOTAO_PRIMARIO = {
  minHeight: "44px", padding: "10px 14px", borderRadius: "11px",
  border: "none", background: T.accent, color: "#fff",
  fontWeight: 700, fontSize: "13px",
};
const CUSTO_NO_BOTAO_PRIMARIO = {
  display: "block", fontSize: "11px", fontWeight: 600,
  color: "color-mix(in srgb, #fff 72%, transparent)", marginTop: "3px",
};
const desabilitadoPrimario = (cond) => (cond ? { opacity: 0.55, cursor: "not-allowed" } : null);
const MARCA_RESULTADO = {
  display: "flex", alignItems: "center", gap: "5px",
  fontSize: "11px", color: T.textMuted, marginTop: "6px",
};
```

</specifics>

<deferred>
## Deferred Ideas

- **Opção B** (carril numerado com cadeado, Setups salvos deslocada para
  fora do carril sequencial) — candidata a fase futura se o Alex quiser a
  sensação de wizard mais forte depois de ver a Opção A em produção.
- Centralizar `BOTAO`/`CAIXA`/`CAMPO`/`AJUDA` (hoje duplicados por arquivo)
  num módulo compartilhado — achado colateral da discussão, não é escopo
  desta fase (que só adiciona `BOTAO_PRIMARIO`, não refatora o que já
  existe).

### Reviewed Todos (not folded)
- `carimbo-frescor-blocos-cross-carteira.md` — match fraco por palavra-chave
  genérica, sem relação com clareza de jornada
- `opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp.md` — tracking de
  aprovação de serviço externo, sem ação de UI nesta fase
- `revisao-arquitetura-mcp-ecossistema-b3.md` — revisão de arquitetura
  maior, já registrada como prioridade alta separada; o Alex optou por
  tratar depois, fora do v1.7
- `subaba-operar-fetch-redundante-gate-proposta.md` — já executado como
  fold-in na Fase 33, esquecido em `pending/` por dívida de bookkeeping,
  não é escopo desta fase

</deferred>

---

*Phase: 35-jornada-guiada-do-workspace*
*Context gathered: 2026-09-21*
