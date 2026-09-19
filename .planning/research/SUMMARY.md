# Project Research Summary

**Project:** Boris+ (b3-agente) — Milestone v1.6, reorganização por job-to-be-done da aba Opções, sub-aba "Setups"
**Domain:** Reorganização de UI React densa já publicada (fintech educacional/regulatório-adjacente), sem router, sem state library, sem UI kit — zero capability nova
**Researched:** 2026-09-19
**Confidence:** HIGH no geral, com uma exceção MEDIUM explícita (ver Confidence Assessment)

## Executive Summary

Este não é um projeto greenfield: é a reorganização de uma tela React já em produção (`web/src/opcoes/OpcoesScreen.jsx`, sub-aba "Setups") que hoje mistura 5 jobs-to-be-done distintos numa rolagem única. As quatro pesquisas concordam num ponto central: o app já possui, três vezes over, todos os primitivos de UI necessários (toggle-button `aria-pressed`, acordeão `aria-expanded`, rail `carouselTrackStyle`) e todo o mecanismo de estado necessário (`ticker` já gateia o "drill-down" para análise de um ativo). A reorganização é composição de padrões existentes, não adoção de tecnologia nova — zero npm packages, zero router, zero state library se justificam para este milestone, e a v1.5 já fechou essa decisão de arquitetura como travada.

A abordagem recomendada, vinda da pesquisa de arquitetura, é dividir o trabalho em duas fases de risco crescente: primeiro extrair cada job para seu próprio componente/arquivo preservando comportamento e ordem atuais (baixo risco, checkpoint com suíte verde), e só depois redesenhar a navegação entre jobs (hub + workspace, sem 3º nível de abas). Fazer as duas coisas juntas — mover código de lugar E mudar como se navega entre lugares — é o erro mais caro identificado: dois eixos de risco mudando ao mesmo tempo sem ponto de checagem intermediário.

O risco dominante não é técnico-genérico, é específico deste codebase: um conjunto de guardiões de teste (`web/tests/test_opcoes_*.mjs`) verifica a garantia "sem duplicação de fetch/gate" e "manchete só vem do motor" por meio de regex/`indexOf` sobre o texto-fonte de UM arquivo, não por comportamento. Mover código de lugar (sem mudar lógica nenhuma) derruba esses guardiões pelo motivo errado, e pior — pode deixar de cobrir uma seção nova sem que a suíte acuse nada. Isso precisa ser orçado explicitamente em cada fase que move código, não descoberto depois que a suíte fica vermelha. Além disso, há uma decisão de produto genuína e não resolvida por esta pesquisa: os jobs "analisar ticker", "comparar vencimentos" e "gerenciar setups salvos" compartilham a MESMA resposta paga de 3 chamadas MCP — a navegação por job precisa decidir explicitamente se um único ponto de entrada paga uma vez para os três, ou se cada um paga a própria leitura.

## Key Findings

### Recommended Stack

Nenhuma tecnologia nova. Os três primitivos necessários já existem e estão em produção neste exato arquivo/família de arquivos: `useState` para o estado "qual seção está ativa" (já usado para o toggle Setups/Operar em `OpcoesScreen.jsx:339`), o grupo de botões `aria-pressed` (não `role="tab"` — convenção deliberada e repetida do app) para trocar de seção, o acordeão `aria-expanded` (com suporte a teclado Enter/Space quando o gatilho não é `<button>`) para disclosure dentro de um job, e o rail `carouselTrackStyle`/`carouselItemStyle` (`App.jsx:350-364`, padrão único desde a Fase 22) para comparação lado a lado (ex.: comparar vencimentos). Nenhum router, UI kit ou state-management library deve ser considerado — todos são explicitamente vetados por decisões de arquitetura já travadas (v1.5: "sem migração de stack") e por convenções já duplamente aplicadas no próprio código.

**Core technologies:**
- `useState` (React 18.3.1, já em uso) — estado de "qual job/seção está ativa" — extensão direta do padrão `subaba` já existente, zero conceito novo
- Grupo de toggle-button `aria-pressed` (padrão da casa, não lib) — navegação entre seções de job — implementação idêntica já existe e testada em `OpcoesScreen.jsx:762-779` e em `BottomNav`
- Acordeão `aria-expanded` + `useState` (padrão da casa) — disclosure dentro de um job (nunca para trocar de job) — 6+ instâncias já em produção, mantém compatibilidade com o gate `prefers-reduced-motion`

### Expected Features

A pesquisa de features confirma que o mecanismo de "hub + workspace" já existe quase pronto: o estado `ticker` já funciona, estruturalmente, como o gatilho de "entrar em modo de trabalho profundo" — só falta esconder os blocos de descoberta/vigias quando um ticker está selecionado, em vez de empilhar tudo. Padrões de mercado (ThinkorSwim, Barchart, tastytrade) confirmam de forma independente que descoberta, análise de instrumento único e gestão de automações salvas devem ser destinos distintos, nunca misturados numa única rolagem — e que abas aninhadas além de 2 níveis prejudicam orientação, o que é diretamente relevante porque o app já está em 2 níveis (bottom nav → Setups/Operar).

**Must have (table stakes):**
- Hub view (estado padrão da sub-aba "Setups", sem ticker selecionado): frase-ponte → Bloco A → Bloco B → vigias → setups salvos, nessa ordem fixa
- Workspace view (ticker selecionado): seletor/LastroDoAtivo → LeituraInterna → blocoLeituraDoServico → cadeia/estrutura → comparação de vencimentos
- Rótulos de seção usando o padrão `cp.*` existente, para nomear explicitamente cada job (usuário leigo não infere o job pelo formato do conteúdo)

**Should have (competitive/diferenciador):**
- Affordance "você está aqui" / voltar-ao-hub dentro do workspace — evita que o usuário se perca numa troca de estado sem URL/back button; é o item com maior risco de virar "feature nova" se superconstruído (nada de histórico de breadcrumb, só um botão voltar)
- Rótulo explícito para o bloco "comparar vencimentos" dentro do workspace, separado visualmente da análise manual

**Defer (v2+):**
- Disclosure progressiva adaptativa da frase-ponte, modelo de progresso do aprendiz, desafio personalizado por padrão observado, layout de hub personalizável/reordenável — todos já explicitamente fora de escopo no PROJECT.md ("reorganizar primeiro, personalizar depois"), incluindo um risco regulatório já anotado (personalização podendo se aproximar de "recomendação")

**Anti-features confirmados (não construir):** IA baseada em router com URLs por job; terceiro nível de abas aninhadas dentro de "Setups"; layout multi-painel simultâneo estilo terminal profissional; busca universal "jump to anything"; auto-refresh contínuo do hub (conflita com a disciplina de frescor/staleness do CLAUDE.md).

### Architecture Approach

A reorganização deve preservar rigorosamente três invariantes já estabelecidos: (1) `useOpcoesMcp` continua sendo chamado uma única vez no componente orquestrador, cada job-section recebe seus dados por prop, nunca instancia o hook de novo; (2) `curadoriaAtiva`/`useCuradoria` vivem uma camada acima (em `App()`, gateados por `tab`), e a reorganização por job dentro da aba Opções não pode promover esse gate para o nível de job — isso reintroduziria o problema que a Fase 32 já corrigiu (fetch pago amarrado à visita de uma tela); (3) estado consumido por 2+ jobs (`ticker`, `tese`, `vencimento`, `lote`) permanece no componente orquestrador — só desce para um job-section o estado usado por exatamente um job.

**Major components:**
1. `OpcoesScreen.jsx` (orquestrador) — mantém os hooks de dados chamados uma única vez e o estado compartilhado entre jobs; distribui por prop
2. Job-sections extraídos (`SecaoDescobrir`, `SecaoVigias`, `SecaoAnalisar`, `SecaoComparar`, `SecaoSetups`) — cada um em arquivo próprio sob `web/src/opcoes/`, sem import de `App.jsx`, sem chamada direta a `store.*`/`api.*` (dado por prop, ação por callback)
3. `<CascataDoServico>` (novo, recomendado) — componente compartilhado para a lógica carregando→erro→vazio→dados hoje duplicada implicitamente entre jobs 3/4/5, evitando a divergência silenciosa que o próprio código já identifica como risco conhecido

### Critical Pitfalls

1. **Guardiões de teste cegos a migração de arquivo** — múltiplos guardiões (`test_opcoes_subabas_ui.mjs`, `test_opcoes_consolidacao_ui.mjs`, `test_opcoes_analisar_ui.mjs`, `test_opcoes_vigias_ui.mjs`, `test_opcoes_mcp_aba_ui.mjs`) verificam contagem/ordem por regex/`indexOf` sobre o texto-fonte de UM arquivo específico. Mover código para um arquivo novo (refactor puro, sem mudança de comportamento) derruba esses guardiões pelo motivo errado, OU pior, deixa de cobrir uma seção nova sem acusar nada (ex.: o guardrail CVM de manchete, escopado só a `SubAbaOperar`, não vê uma seção nova que renderiza `candidato.manchete`). Mitigação: antes de mover qualquer bloco citado nos guardiões, mapear quais testes leem o arquivo de origem e decidir explicitamente — estender o guardião para varrer o diretório inteiro (como já faz o guardião "ninguém importa App.jsx"), ou manter a chamada física no orquestrador e só passar o resultado por prop.
2. **Extração de componente desloca sem querer "quem decide" para "quem narra"** — hoje `top`/`meta` (saída determinística do motor) e `narrativa` (texto de IA) convivem no mesmo array/componente. Separar por job pode levar a nova seção de narração a reordenar/filtrar por conveniência, quebrando a garantia de fonte única de ranking mesmo sem tocar em `avaliar()`/`rastrear()`. Mitigação: `ctx.curadoria.top` é imutável, passado por referência/índice; nenhuma seção nova pode ter `.sort()`/`.filter()` tocando esse array.
3. **Frase-ponte (mitigação regulatória D-05) perde adjacência física ao Bloco B** — se Bloco A e Bloco B forem para seções diferentes, a frase-ponte precisa migrar junto com o Bloco B, sempre imediatamente acima, sem gate/scroll entre os dois; isso é uma decisão de produto explícita a registrar no CONTEXT.md da fase, não um efeito colateral aceitável da separação.
4. **Estado de erro/degradado perde a garantia de "impossível não ver"** — hoje tudo está numa rolagem só, então qualquer aviso de dado degradado é necessariamente visto. Em navegação por seções mutuamente exclusivas, um aviso que hoje é global (ex.: MCP fora do ar) pode ficar isolado dentro de uma seção que o usuário nunca abre. Mitigação: mapear todo estado de erro hoje visível e classificar explicitamente local-a-um-job vs. global-precisa-de-banner-fora-de-qualquer-seção.
5. **Estado de navegação (ticker/vencimento) não sobrevive à troca de seção** — dívida já conhecida e nunca resolvida (backlog B2, Fase 26/v1.4); a reorganização multiplica o número de "lugares" na tela, multiplicando a chance desse reset acontecer se seções passarem a montar/desmontar em vez de só ocultar. Mitigação: manter esse estado no componente pai comum, nunca redeclarar `useState` local equivalente dentro de um job-section — e aproveitar esta fase para fechar o B2 de vez.

## Implications for Roadmap

A pesquisa de arquitetura já define a estrutura de fase mais defensável — o roadmap deve adotá-la como espinha dorsal, não reinventar uma sequência própria.

### Fase A: Extração de componentes, comportamento e ordem preservados
**Rationale:** Menor risco possível — separa o eixo "estrutura de arquivo" do eixo "fluxo de navegação". Permite reescrever os guardiões de ordem de forma mecânica (trocar nome do marcador textual, preservando a mesma relação de ordem) em vez de reescrever a lógica deles.
**Delivers:** Cada job (`SecaoDescobrir`, `SecaoVigias`, `SecaoAnalisar`, `SecaoComparar`, `SecaoSetups`) em arquivo próprio sob `web/src/opcoes/`, renderizados na MESMA sequência de hoje; `<CascataDoServico>` compartilhado extraído; guardiões atualizados só na sintaxe do marcador.
**Addresses:** Não resolve nenhum feature de UX ainda — é pré-condição estrutural para o hub/workspace da Fase B.
**Avoids:** Pitfall 1 (guardiões cegos a migração de arquivo) tratado no melhor momento possível — enquanto a ordem textual ainda é preservável 1:1.

### Fase B: Redesenho da navegação (hub + workspace)
**Rationale:** Só depois de componentes isolados e testáveis independentemente (checkpoint da Fase A com suíte verde). Troca a rolagem única por hub (descoberta + vigias + setups salvos, sem ticker) e workspace (análise + comparação de vencimentos, com ticker) — reutilizando o estado `ticker` já existente como gatilho, sem router, sem nova infraestrutura.
**Delivers:** Navegação hub/workspace funcional; guardiões de ordem reescritos como verificação de alcançabilidade ("todo job é alcançável a partir do menu") em vez de ordem textual cross-job; guardrail CVM estendido para varredura por diretório.
**Uses:** Toggle-button `aria-pressed` (padrão da casa) para o hub; estado `ticker` já existente como gate hub↔workspace.
**Implements:** A decisão de produto pendente sobre job3/4/5 compartilharem o mesmo fetch pago precisa ser tomada ANTES ou DURANTE esta fase — ela determina se os jobs 4/5 mostram um CTA "leia o ativo primeiro" (opção recomendada pela pesquisa de arquitetura, alinhada ao guardrail ADR-027 §3.3) ou pedem leitura própria.

### Phase Ordering Rationale

- Fundir extração de componente com redesenho de navegação numa fase só faria dois eixos de risco mudarem ao mesmo tempo (estrutura de arquivo + fluxo de navegação) sem checkpoint intermediário em que a suíte ainda esteja verde — a pesquisa de arquitetura é explícita que isso deve ser evitado.
- A Fase A entrega o checkpoint necessário: componentes extraídos, suíte verde, mesmo comportamento visível, guardiões atualizados só na sintaxe.
- A decisão de produto sobre o fetch compartilhado (job3/4/5) não bloqueia a Fase A, mas bloqueia o detalhamento de tarefas da Fase B — deve ser resolvida com o Alex antes do planejamento de tarefas da Fase B, não durante a execução.

### Research Flags

Needs research: Fase B (navegação hub/workspace) — a mecânica de UI-SPEC específica (como o CTA "leia o ativo primeiro" aparece, onde o banner global de erro/degradado vive) ainda não está desenhada; a pesquisa de features e pitfalls levantou o quê, não o layout exato.

Standard patterns: Fase A (extração de componentes) — segue precedente já duas vezes aplicado no próprio código (extração de `OportunidadesOpcoes.jsx`/`CuradoriaEstruturas.jsx` na Fase 32); mecânica bem documentada, sem necessidade de pesquisa adicional.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Toda recomendação citada a file:line deste codebase; nenhuma inferência de ecossistema genérico |
| Features | MEDIUM | Princípios gerais de IA (hub vs. workspace, limite de 2 níveis de abas) são corroborados externamente (ThinkorSwim/Barchart/tastytrade docs + fontes de UX), mas o mapeamento específico para este código é leitura própria do pesquisador, não uma afirmação citada — a própria FEATURES.md sinaliza esse split |
| Architecture | HIGH | Leitura direta e completa de `OpcoesScreen.jsx` (2010 linhas), `useOpcoesMcp.js` (466 linhas) e dos 6+ guardiões de teste relevantes |
| Pitfalls | HIGH | Todos os achados vêm de leitura direta do código-fonte e dos guardiões reais, não de padrões genéricos de refactoring React |

**Overall confidence:** HIGH, com a ressalva explícita de FEATURES.md (MEDIUM) sobre o mapeamento específico da IA proposta para este código.

### Gaps to Address

- **Decisão de produto pendente — fetch compartilhado entre jobs 3/4/5:** não é uma lacuna de pesquisa inconclusiva, é uma decisão que só o Alex pode tomar ("a decisão é do Alex, não desta pesquisa" — ARCHITECTURE.md). Precisa ser resolvida antes do detalhamento de tarefas da Fase B, porque determina a forma concreta da navegação entre esses três jobs (CTA compartilhado vs. leitura independente por job).
- **Layout exato da Fase B (UI-SPEC):** onde o banner global de erro/degradado vive quando as seções passam a ser mutuamente exclusivas; como o affordance "você está aqui"/voltar é desenhado sem virar histórico de navegação — ambos precisam de uma etapa de CONTEXT.md/UI-SPEC dedicada antes da implementação da Fase B, não de pesquisa adicional.
- **Cobertura de guardiões pós-migração:** a lista exata de quais dos 9 arquivos de teste que hoje leem `OpcoesScreen.jsx` (`grep -rln "OpcoesScreen.jsx" web/tests/*.mjs`) precisam de reescrita vs. atualização mecânica só pode ser fechada durante a execução da Fase A, arquivo por arquivo — mapeado como tarefa, não como risco residual.

## Sources

### Primary (HIGH confidence)
- `web/src/opcoes/OpcoesScreen.jsx` (leitura completa, 2010 linhas) — estrutura atual, ordem de blocos, estado local, comentários de decisão D-02/D-04/D-05/D-07
- `web/src/opcoes/useOpcoesMcp.js` (leitura completa, 466 linhas) — contrato dos hooks de dados por job
- `web/src/App.jsx` (trechos `useCuradoria`/`curadoriaAtiva`/`carouselTrackStyle`/`BottomNav`/acordeões) — gate de fetch de nível superior, primitivos de UI reutilizáveis
- `web/tests/test_opcoes_consolidacao_ui.mjs`, `test_opcoes_subabas_ui.mjs`, `test_opcoes_analisar_ui.mjs`, `test_opcoes_vigias_ui.mjs`, `test_opcoes_mcp_aba_ui.mjs`, `test_opcoes_custo_declarado.mjs`, `test_opcoes_universo_carteira.mjs` — guardiões reais, lidos diretamente
- `.planning/PROJECT.md` — escopo do Milestone v1.6, decisões travadas ("reorganizar primeiro, personalizar depois"), backlog B2 (Fase 26/v1.4)
- `CLAUDE.md` (raiz do repo) — princípios 4/5, convenções de stack, guardrails de paridade e CVM

### Secondary (MEDIUM confidence)
- thinkorswim mobile Getting Started (Schwab, docs oficiais) — padrão bottom-menu Watchlist/Scanner separado de symbol detail
- Barchart Options Screener, tastytrade Watchlist Scanner — screener/watchlist/alertas como destinos distintos
- UX Planet "Tabs for Mobile UX Design", LogRocket "Tabbed navigation in UX", Design Monks "Nested Tab UI Examples" — convergência independente em "não mais de 2 níveis de abas aninhadas"

### Tertiary (LOW confidence)
- DayTradingz "7 Best Options Screeners", ChartingLens roundup — usados apenas para corroboração cruzada de padrão (screener vs. chain analysis vs. alertas como destinos distintos), não como fonte única de nenhuma recomendação

---
*Research completed: 2026-09-19*
*Ready for roadmap: yes*
