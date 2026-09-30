# Phase 45: Card de posição estruturada - Context

**Gathered:** 2026-09-29
**Status:** Ready for planning

<domain>
## Phase Boundary

O card de Posições (`web/src/App.jsx`, ~4499-4640) passa a mostrar a estrutura de opções inteira de cada ativo — nome (collar / call coberta / put de proteção), resultado total ações+opções, régua de faixa no vencimento, pernas sempre visíveis, os 5 estados (vigente / ≤5 dias / exercício provável / prêmio indisponível / vencida) e "Encerrar" bloqueado com motivo — lendo a chave `estrutura` entregue pela Fase 44. Sem o aviso falso "Posição sem stop definido" nem `R:R —` em estrutura protegida. Só front (+ ajustes de vocabulário com paridade). Sem execução nova de ordem, sem rota nova, sem fill parcial, sem estruturas além das 3 da biblioteca, sem mudar manchete/decisão do motor.

Mock aprovado (fonte visual): https://claude.ai/artifact/JEpy5VmkoddNTHyVYnYWZc — artboard `CardEstrutura` (componente com tweaks variante × estado × modo × tema) e as 12 variações. Números do mock são ilustrativos; no app todo número vem do motor.

</domain>

<decisions>
## Implementation Decisions

### Busca da estrutura (fonte do dado)
- **D-01:** O card busca `estrutura` reusando `store.optionsProposta(t, true)` (já paritário em `serverStore`/`deviceStore`, `persistence.js:277/1340`) — UMA chamada por ativo que tenha opção aberta (o front já sabe pelas `optionPositions`), em paralelo, ao montar Posições. Sem rota leve nova (mantém D-01 da Fase 44). Custo aceito: a rota também calcula candidatos/proposta e consome cota brapi.
- **D-02:** Ativo sem `optionPositions` não chama a rota; o card fica como hoje (ação simples), sem regressão.
- **D-03:** Durante a carga e na falha (timeout 30s / 502) o card renderiza o card ATUAL + aviso discreto ("Lendo a estrutura de opções…" / "Estrutura indisponível agora"). Nunca esconde pernas, nunca inventa número, e o aviso falso "sem stop" fica SUPRIMIDO enquanto não houver leitura (para não reintroduzir o bug original). Frases só de `skill_ref.py` + espelho em `copy.js`.
- **D-04:** Recarga: ao abrir a tela e após qualquer ação que altere as pernas (buy / sell / fechar opção). Sem polling nem acoplar ao refresh de cotação (protege a cota brapi de 15k/mês). Botão "Atualizar" discreto é opcional (decisão do planner).

### Encerrar estrutura
- **D-05:** "Encerrar estrutura…" NÃO executa nada no card. Navega para Opções > Operar já no ticker da posição (`ctx.goOpcoes(...)` + pré-seleção de ticker via `tickerInicialOpcoes`/`memoriaOpcoes`), onde o fluxo existente de proposta de fechamento (`/api/options/lastreada/fechar`, um contrato por vez, só Operador — 403 no Estudo) faz o resto. Zero capacidade de execução nova (sem fechar 2 pernas sem atomicidade).
- **D-06:** Um único botão. O link "Ver em Opções" do mock some (redundante). Bloqueado (prêmio indisponível / vencida) fica `disabled` com o motivo do motor (`encerrar.texto`) — CARD-04. Rótulo igual nos dois modos; a aba Operar já explica que o Estudo não executa.

### Blocos do card atual em posição estruturada
- **D-07:** A régua "POSIÇÃO NO RISCO" (`PlanRuler`) sai; entra a régua de faixa do mock (piso / PM / teto / hoje).
- **D-08:** MANTIDOS além do mock: botão "Stop/alvo (IA)" (`ctx.openStopAlvo`), links "Reanalisar" e "Histórico de análises" (`ctx.openAvaliar`, `analysisLog`) e a linha de contexto "dias em operação · % do capital · entrada pelo setup / gatilho" — SEM o `R:R` quando não houver stop E alvo. `AvisoLiquidacao` também permanece (comportamento existente, fora do mock).
- **D-09:** "Compras desta posição" (acordeão de memória do PM) NÃO é mantida na posição estruturada (o PM aparece na régua). Decisão do Alex; vale só para estrutura — ação sem opção mantém o acordeão.
- **D-10:** Stop/alvo já definidos aparecem como marcadores extras na régua de faixa (negativo/positivo, cores COR-01) E nas linhas "Stop"/"Alvo" do bloco de limites com o valor real. `R:R` volta só com stop E alvo. Stop/alvo nunca é vetado: `operar:false` é parecer; "definir stop e alvo" e "Aplicar proteção" sempre disponíveis (invariante do repo).

### Badge / chips (CARD-06)
- **D-11:** Chips neutros do mock: "ESTRUTURA · COLLAR" (Estudo: "ESTUDO · COLLAR") e "vence DD/MM · N dias" (aviso âmbar em ≤5 dias). A pill vermelha `badgeTravada` ("N travada(s) · lastro de CALL") permanece SÓ onde há call vendida (ações realmente travadas), com texto que cita collar quando for o caso. Put de proteção NÃO usa "travada" (não trava ações). Isto AJUSTA o texto de CARD-06 ("badgeTravada cobre collar e put") — o planner atualiza `REQUIREMENTS.md` com nota de reversão deliberada.

### Claude's Discretion
- Estado "vencida" e linha de fonte (área não discutida; padrão conservador aprovado): vencida = estado do motor + resultado com as últimas cotações, rótulo "vencida em DD/MM"; NÃO exibir "resultado final" nem "opções viraram pó" (o motor não devolve liquidação) e manter `AvisoLiquidacao`. Linha de fonte/horário/atrasado (princípio 3): usar só `providerStatus`/carimbo que a rota já devolve; sem horário → "sem horário da fonte"; nunca inventar "desde 10:42". O pesquisador confirma o que a rota carrega e o que falta.
- Tokens/escala: usar `T.*`/`SP` do app (não as hexes do mock); contraste AA nas 4 combinações tema×modo; verde/vermelho só em manchete/preço/P&L (COR-01); `aria-label` nos elementos novos.
- Como o "Registrar saída…" reflete `qtyTravada`/lastro (reusar `avisoTravaNaVenda` existente), extração do card em componente próprio (`CardPosicaoEstruturada`) e nomes de props.
- Âncoras proibidas "trava protetora"/"abate o custo": usar "collar". Reconciliar `tiraOpcoesMotivo`/collar deixados intocados no 44-01 (`copy.js`), com nota de reversão deliberada nos guardiões.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requisitos, roadmap e mock
- `.planning/REQUIREMENTS.md` — CARD-01..06 e Out of Scope da v2.0 (CARD-06 será ajustado por D-11)
- `.planning/ROADMAP.md` §Phase 45 — goal e 4 critérios de sucesso
- https://claude.ai/artifact/JEpy5VmkoddNTHyVYnYWZc — mock Design (artboards `CardEstrutura`, `Atual`, variantes/estados/modos); ler via Artifact `read` com `paths`
- `.planning/phases/44-motor-estrutura-por-ativo/44-CONTEXT.md`, `44-VERIFICATION.md`, `44-REVIEW.md` — contrato do motor e correções WR-01..06

### Backend entregue na Fase 44
- `server/app/estrutura_posicao.py` — `ler_estrutura`; payload `estrutura` (nome, nomeTexto, pernas[], acoes, resultado{total,acoes,pernasCotadas,incompleto,pernasSemCotacao,pernasSemDados,texto}, faixa{piso,teto,perdaMaxima,ganhoMaximo,breakevens,qtdBase,qtdPut,textos}, estado/estadoTexto, descoberta, abertaSemProposta, encerrar{permitido,motivo,texto}, stopTexto, incompleto)
- `server/app/skill_ref.py` `ESTRUTURA_POSICAO` (29 chaves × 2 modos) + `estrutura_posicao_txt` — vocabulário pronto
- `server/app/main.py` `options_proposta` (~3273) — onde `estrutura` sai; `options_lastreada_fechar` (~4144) — fluxo de fechar (Operador-only)

### Front a estender
- `web/src/App.jsx` ~4499-4640 (card de Posição: `TravaPill` 1216-1219, `PlanRuler`, aviso "sem stop" 4575, R:R 4565, compras 4589, botões 4610+); `ctx.goOpcoes` 9127; `LinhaChamadaOpcoes` 4488
- `web/src/opcoes/OpcoesScreen.jsx` 334-339 (`abaInicialOpcoes`, `ctx.opcoesAbaInicial`) e `web/src/opcoes/memoriaOpcoes.js` (`tickerInicialOpcoes`)
- `web/src/copy.js` `estruturaPosicao` / `opcoesLastreadasMotivo` (espelho Fase 44), `badgeTravada` (738, 1591)
- `web/src/persistence.js` 277, 1340 (`optionsProposta` nos dois stores), `web/src/api.js:327`

### Guardrails
- `CLAUDE.md` — princípios 3/4/5/9, paridade `skill_ref.py`↔`copy.js`, "Stop/alvo nunca são vetados", guardiões não se apagam, `vite build` obrigatório, App.jsx nunca lido inteiro
- `.claude/skills/didatica-boris/SKILL.md` — vocabulário por modo (Estudo completo, Operador direto)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `store.optionsProposta(t, multiperna)` já paritário entre `serverStore` e `deviceStore`; `resposta.estrutura` chega pronta do servidor (texto incluso).
- `ctx.goOpcoes(aba)` + `opcoesAbaInicial` e `tickerInicialOpcoes` para levar ao ticker certo em Opções > Operar.
- `TravaPill`, `AvisoLiquidacao`, `PlanRuler`, tokens `T`/`SP`, `MONO`.

### Established Patterns
- Vocabulário só em `skill_ref.py` com espelho em `copy.js` (guardião de paridade); front nunca compõe frase.
- Chave aditiva na resposta; `null` = desconhecido, nunca 0.
- Front edita → `npx vite build` obrigatório (grep não pega erro de sintaxe JS).

### Integration Points
- Bloco por posição em `App.jsx` (~4499): decidir renderização estruturada vs atual por ativo (existe `estrutura` não-nula).
- Ações que alteram pernas (buy/sell/fechar opção) disparam recarga da estrutura (D-04).

</code_context>

<specifics>
## Specific Ideas

Caso de referência: UGPA3, 1000 ações, PM R$ 39,50, put 33,25 + call 42,00 (collar) — hoje o card mostra "1000 travada(s) · lastro de CALL", P&L só das ações e aviso falso de "sem stop". Estados obrigatórios do mock: vigente, perto do vencimento, exercício provável, prêmio indisponível (mostra só ações, encerrar bloqueado) e vencida.

</specifics>

<deferred>
## Deferred Ideas

- Rota leve `/api/options/estrutura` só com `ler_estrutura` (menos latência e cota) — descartada agora (D-01); reavaliar se a cota brapi ou a latência doerem em produção.
- Encerrar estrutura inline (sheet com as 2 pernas, execução atômica) — capacidade nova, fica para milestone futura.
- Infos do review da 44 ainda abertas (lógica de `encerrar` duplicada, frase "vence hoje", `_liquidez` zerado→None, `get_options` serial sem timeout) — candidatos a quick task.
- Quick task avulsa já registrada em REQUIREMENTS §Future (remover `tiraOpcoesSemCobertura/SemSetup/SemMercado`).

</deferred>

---

*Phase: 45-Card de posição estruturada*
*Context gathered: 2026-09-29*
