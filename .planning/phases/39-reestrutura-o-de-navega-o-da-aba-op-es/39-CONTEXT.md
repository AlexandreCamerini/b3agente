# Phase 39: Reestruturação de navegação da aba Opções - Context

**Gathered:** 2026-09-24
**Status:** Ready for planning

<domain>
## Phase Boundary

A aba Opções passa a ter exatamente 3 abas fixas de nível 1 — **Oportunidades**,
**Recomendadas**, **Montar** — substituindo as duas camadas ortogonais de
navegação atuais (`subaba` + `abaWorkspace` em `OpcoesScreen.jsx`) e as duas
telas cujo propósito não é óbvio hoje ("Operar", "saiba mais" genérico).
Inclui trocar a métrica de ranking da aba Recomendadas (hoje só
`premio/perda_maxima`) para incorporar um piso de probabilidade de ficar OTM.
Não inclui: execução a descoberto (B3, fora de escopo da milestone v1.8),
consolidação dos 5 registros de tela do app (Fase 41, TELAS-01), persistência
de estado entre trocas de aba (Fase 40, ESTADO-01 — depende desta fase estar
pronta primeiro).

</domain>

<decisions>
## Implementation Decisions

### Navegação de nível 1
- **D-01:** 3 abas fixas — Oportunidades, Recomendadas, Montar — sem segunda
  camada de abas dependente de estado intermediário (ticker escolhido). Isto
  substitui `subaba` (`"setups"`/`"operar"`) e `abaWorkspace`
  (`"analisar"`/`"comparar"`/`"setups"`) por um único nível de navegação.
- **D-02:** **Oportunidades** = conteúdo atual do hub "Descobrir" quando há
  liquidez confirmada (hoje `OportunidadesOpcoes.jsx`, carrossel de posições
  com proposta líquida e concreta) — "o que já está pronto pra operar agora".
- **D-03:** **Recomendadas** = lista ranqueada hoje produzida por
  `CuradoriaEstruturas.jsx`/`server/app/opcoes_curadoria.py` ("as 4 melhores
  estruturas", sem gate de liquidez) — renomeada de "Setups" pra evitar
  colisão com o recurso existente de condição salva em português livre
  (`SecaoSetups.jsx`/`CriarSetup.jsx`, que MANTÉM o nome "Setups" sem
  alteração).
- **D-04:** **Montar** = `SecaoAnalisar.jsx` (montar estrutura manualmente,
  já com o botão de executar da quick `260923-ndy`).
- **D-05:** A sub-aba "Operar" (`SubAbaOperar`, `OpcoesScreen.jsx:1090-1222`)
  é DISSOLVIDA. A ação de executar uma estrutura proposta pelo motor migra
  pra dentro do card da aba Recomendadas, inline, no mesmo padrão que
  `CuradoriaEstruturas.jsx` já usa (`handleExecutar`, painel expandido com
  prêmio/perda/breakeven + botão Executar + checkbox de liquidez DIFÍCIL
  quando aplicável).
- **D-06:** `SecaoComparar.jsx` (comparar vencimentos) vira uma sub-ação
  dentro de Montar — um link "ver outros vencimentos" depois de montar uma
  estrutura, não mais aba própria. Reaproveita a mesma tese/lote de Montar
  (hoje já é assim, `SecaoComparar.jsx` usa a MESMA tese/lote de
  `SecaoAnalisar.jsx` em modo somente-leitura).
- **D-07:** `SecaoVigias.jsx` (gerenciar vigias) não vira aba — vira
  ícone/badge no cabeçalho da aba Opções (com contador), visível
  independente de qual das 3 abas está ativa, abre um sheet. Decisão travada
  em turno anterior desta mesma sessão de trabalho.

### Ranking de Recomendadas
- **D-08:** Piso de admissão: candidato só entra na lista de Recomendadas se
  tiver **≥ 60% de probabilidade de ficar OTM no vencimento** (calculada via
  Black-Scholes, `prob_itm` de `server/app/options_quant.py`, já implementado
  e testado mas hoje só usado na rota educacional `options_api.py:103`,
  nunca em `opcoes_curadoria.py`). Abaixo do piso, o candidato NÃO aparece na
  lista (filtro de admissão), não apenas perde posição no ranking.
- **D-09:** Dentro do piso, ordenação por prêmio anualizado
  (`(prêmio/spot) × (365/dias)`), substituindo a ordenação atual por
  `premio/perda_maxima`.
- **D-10:** Esta é uma métrica de **admissão + ordenação**, não de **seleção
  de contrato dentro da cadeia** — não conflita com a proibição do ENG-01
  (`opcoes_payoff.py:22-24`, "a régua do Boris é liquidez + strike extremo"
  para escolher QUAL contrato). O ENG-01 continua vigente para a escolha de
  contrato; D-08/D-09 decidem só QUAIS candidatos já selecionados aparecem e
  em que ordem. Downstream (research/planner) deve deixar essa distinção
  explícita no código (comentário) para não ser lida como reversão do ENG-01.
- **D-11:** Lista vazia (piso filtra tudo): mostrar mensagem explicando o
  motivo ("nenhum candidato com ≥60% de chance de ficar OTM hoje"), nunca
  esconder a seção sem explicação nem relaxar o piso silenciosamente.
- **D-12:** Escopo backend: a mudança de ranking toca `opcoes_curadoria.py`
  (usado por Recomendadas). NÃO toca `opcoes_lastreadas.py` (usado por
  Oportunidades, que já é uma lista pré-filtrada por liquidez confirmada, sem
  ranking — não precisa de probabilidade).

### Cabeçalho e texto
- **D-13:** O link "saiba mais" do cabeçalho (hoje abre glossário genérico de
  "opção") é removido do topo global. A função do glossário é preservada mas
  vira um ⓘ contextual dentro de cada uma das 3 abas, não um único ponto de
  entrada no topo.
- **D-14:** Texto de bastidor que hoje aparece inline antes do conteúdo
  (explicação de cache/cota do dia, mecânica de lastro em ações/contratos,
  "pontuação de curadoria: 0.02" bruta) deixa de aparecer como parágrafo —
  vira detalhe atrás de um ⓘ, ou é removido quando não muda a decisão do
  usuário. O número de curadoria vira posição no ranking ("1ª de N"), nunca o
  score bruto.

### Claude's Discretion
- Ícone exato do badge de Vigias (sino, olho, etc.) e microcopy do sheet —
  não travado nesta discussão; planner/UI-spec decide dentro do design
  system existente.
- Se `ConfluenceRing` (já especificado em
  `qa/AUDITORIA-Design-System-v1.md` §4, nunca usado em Opções) substitui a
  exibição de posição no ranking em Recomendadas — recomendado, mas fica a
  critério do UI-spec.

### Folded Todos
- **Carimbo de frescor nos blocos cross-carteira** (`.planning/todos/pending/carimbo-frescor-blocos-cross-carteira.md`,
  princípio 3 do CLAUDE.md) — os blocos de Oportunidades e Recomendadas já
  mostram dado cross-carteira; esta fase exige que o carimbo de
  horário/fonte fique visível nesses cards novos, não é mais um TODO solto.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requisito e roadmap
- `.planning/REQUIREMENTS.md` (seção "Reestruturação de navegação") — texto
  completo de NAV-01
- `.planning/ROADMAP.md` (Phase 39) — Success Criteria formais

### Arquitetura atual da aba Opções (mapa completo, achado 2026-09-23)
- `web/src/opcoes/OpcoesScreen.jsx:291-297` — os dois estados de navegação
  ortogonais a substituir (`subaba`, `abaWorkspace`)
- `web/src/opcoes/OpcoesScreen.jsx:801-1044` — árvore de renderização atual
  (hub vs. workspace, `SubAbaOperar`)
- `web/src/opcoes/OportunidadesOpcoes.jsx` — carrossel de Oportunidades
  (base da nova aba 1)
- `web/src/opcoes/CuradoriaEstruturas.jsx` — lista ranqueada + execução
  inline (base da nova aba 2, padrão de UI a reaproveitar)
- `web/src/opcoes/SecaoAnalisar.jsx` — montar estrutura manual + executar
  (base da nova aba 3)
- `web/src/opcoes/SecaoComparar.jsx` — comparar vencimentos (vira sub-ação
  de Montar, D-06)
- `web/src/opcoes/SecaoVigias.jsx` — vigias (vira ícone/sheet, D-07)
- `web/src/opcoes/SecaoSetups.jsx`, `web/src/opcoes/CriarSetup.jsx` — recurso
  "Setups" existente que NÃO muda de nome (D-03)
- `web/src/copy.js:1133,1139,1143` — colisão de rótulo "Setups" já
  documentada, chaves a renomear

### Ranking e probabilidade
- `server/app/opcoes_curadoria.py` — ranking atual (`premio/perda_maxima`) a
  substituir por D-08/D-09
- `server/app/options_quant.py:49-88` — `black_scholes()`/`prob_itm` já
  implementado e testado, hoje só usado em `options_api.py:103` (taxa livre
  de risco hardcoded `0.105` — precisa virar constante nomeada no mínimo)
- `server/app/opcoes_payoff.py:22-24` — ENG-01, proibição de delta como
  critério de SELEÇÃO de contrato — ver D-10 pra distinção de escopo
- `server/app/options_provider_yahoo.py` — provider padrão de produção, SEM
  Greeks nativos; IV vem sem garantia de preenchimento (fallback a decidir
  em research/planning — a rota educacional já usa `hv21`)

### Design system
- `qa/AUDITORIA-Design-System-v1.md` — tokens, `ConfluenceRing`, padrão de
  disclaimer único por tela (ⓘ+sheet) — nunca aplicado em Opções até agora

### Histórico (por que isto não é a primeira tentativa)
- `.planning/PROJECT.md` (milestones v1.6, linhas ~86-103, e v1.7, linhas
  ~48-84) — duas reorganizações anteriores da mesma aba que não resolveram a
  causa raiz; ler antes de propor qualquer solução incremental

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `CuradoriaEstruturas.jsx` (`handleExecutar`, painel `abertoId`, checkbox de
  liquidez DIFÍCIL) — padrão de execução inline a reaproveitar em
  Recomendadas no lugar da aba Operar dissolvida
- `ExecutarProposta.jsx` (quick `260923-ndy`) — padrão de estado
  busy/erro/ok já usado em Montar, mesmo padrão a preservar
- `ConfluenceRing`, ⓘ+sheet — especificados no design system, nunca
  implementados em Opções

### Established Patterns
- Dois stores paralelos (`serverStore`/`deviceStore`) — qualquer novo campo
  de estado de navegação (ex.: aba ativa persistida, que é assunto da Fase
  40, não desta) precisa entrar nos dois
- `copy.js` — vocabulário por modo (Estudo/Operador), chaves idênticas nos
  dois; renomear "Setups"→ manter, aba nova usa chave nova ("Recomendadas")
- `OpcoesScreen.jsx` mantém ZERO import de `App.jsx` (isolamento ADR-027) —
  qualquer solução de ⓘ contextual por aba deve instanciar localmente, como
  o "saiba mais" da Fase 38 já faz

### Integration Points
- `OpcoesScreen.jsx` é o único ponto de orquestração de nível 1 — a
  navegação de 3 abas substitui a lógica de render ali, sem tocar
  `App.jsx`/`BottomNav.defs` (Opções continua sendo a 5ª aba principal, sem
  mudança)

</code_context>

<specifics>
## Specific Ideas

- Exemplo de card real testado nesta sessão (UGPA3, covered call): spot
  38,82, strike 39,50, prêmio 1,62, 23 dias → perda_máxima R$37.200
  corretamente inclui a posição em ações pré-existente (não é bug), mas a
  apresentação hoje não deixa isso claro — vale considerar contexto
  comparativo no card de Recomendadas/Oportunidades quando o planner chegar
  no detalhe visual (não travado como decisão formal aqui, é antecedente do
  achado de UX que motivou toda a discussão).
- Pedido original do Alex (verbatim, traduzido em D-01 a D-07): "3 abas: uma
  traz oportunidades do mercado usando o portfólio; outra apresenta
  possibilidades de Setups ordenadas da mais recomendada pra menos,
  mostrando 3 e deixando escolher mais se quiser; a terceira o usuário monta
  sua própria estrutura."

</specifics>

<deferred>
## Deferred Ideas

- Migração completa do motor de opções pro MCP único (mydata) — fora de
  escopo, mencionado em `.planning/PROJECT.md` como revisão de arquitetura
  separada.
- Taxa livre de risco real (Selic/CDI) em vez do hardcoded `0.105` — D-08
  precisa só que `black_scholes()` seja chamado com ALGUMA taxa; trocar por
  fonte real de Selic é melhoria futura, não bloqueia esta fase.
- Comparativo visual antes/depois no card de perda máxima (achado da sessão
  anterior sobre `PropostaLastreada.jsx`) — não é parte desta fase (esta
  fase é navegação, não a apresentação de risco de cada card); registrar
  como candidato a fase futura se o Alex quiser.

### Reviewed Todos (not folded)
- `.planning/todos/pending/medir-rate-limit-mydata.md` — sobre trocar fonte
  de dados em produção, não sobre navegação; fora de escopo desta fase.
- `.planning/todos/pending/revisao-arquitetura-mcp-ecossistema-b3.md` —
  revisão de arquitetura maior já reconhecida como fora de escopo em
  `.planning/PROJECT.md`.
- `.planning/todos/pending/subaba-operar-fetch-redundante-gate-proposta.md`
  — fica **resolvido por remoção**, não por correção: D-05 dissolve
  `SubAbaOperar` inteiro, então o fetch duplicado que o todo reportava deixa
  de existir junto com o componente. Marcar o todo original como resolvido
  quando esta fase fechar.
- `.planning/todos/pending/opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp.md`
  — acompanhamento operacional de aprovação de serviço externo, sem relação
  com navegação.

</deferred>

---

*Phase: 39-reestrutura-o-de-navega-o-da-aba-op-es*
*Context gathered: 2026-09-24*
