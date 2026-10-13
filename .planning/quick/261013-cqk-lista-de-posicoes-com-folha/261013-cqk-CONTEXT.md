# Quick Task 261013-cqk: Lista de posições + folha de detalhe (opção B) — Context

**Gathered:** 2026-10-13
**Status:** Ready for planning
**Origem:** design critique de 2026-10-13 + mockup aprovado (https://claude.ai/artifact/TJaJEJipdksEPky2xy61zX, pranchetas "B · lista compacta" e "B · folha de detalhe"). A opção A (quick 261013-29f, publicada em F10-20261013-02) reorganizou o corpo aberto do `CartaoPosicao`; B troca a forma de navegar: lista compacta de todas as posições + folha com o detalhe.

<domain>
## Task Boundary

Aba Posições/Portfólio (`CarteiraScreen`, `web/src/App.jsx` ~5728-5880): o loop de cards grandes vira LISTA COMPACTA (uma linha de 2 andares por posição); tocar abre uma FOLHA (bottom sheet) com o detalhe completo — o conteúdo do card aberto da opção A. Vale nos dois modos (Estudo/Operador, copy por modo, paridade `skill_ref.py` ↔ `copy.js`). Inclui posições com estrutura (opções) e pernas avulsas.

FORA de escopo: opção C (painel de evolução, série histórica), contagem em pregões/calendário B3, total combinado na lista, mudanças no motor de carteira/ordens.
</domain>

<decisions>
## Implementation Decisions (LOCKED — Alex, 2026-10-13)

### D1. Regra de atenção — NOVA, no backend
- `server/app/cartao_posicao.py` (`leitura_plano`, ~188-242) ganha estado determinístico de proximidade, calculado SÓ no backend (guardiões proíbem aritmética financeira nos componentes do card):
  - **perto do stop**: plano completo, preço DENTRO do plano e o preço já percorreu **>= 75% do caminho entre o preço médio e o stop**: `(pm − preço) / (pm − stop) >= 0,75`.
  - **perto do alvo**: idem rumo ao alvo: `(preço − pm) / (alvo − pm) >= 0,75`.
  - Limiar numa constante única nomeada (ex.: `LIMIAR_PROXIMIDADE = 0.75`), com teste. Casos de borda (stop >= PM, p.ex. stop movido para proteger lucro; alvo <= PM; pm == stop; preço ausente; plano incompleto) têm regra explícita escolhida pelo planner e documentada — nunca divisão por zero, nunca estado inventado (sem dado → sem estado de proximidade). Sugestão para o planner avaliar: quando o caminho PM→stop não existe (stop >= PM), usar a fração na régua stop→alvo.
  - Campo novo no payload (ex.: `proximidade: "perto_stop" | "perto_alvo" | null`) + copy por modo. Espelhar onde o front já espelha `leitura_plano` (deviceStore/serverStore se aplicável — paridade obrigatória).
- **Prioridade de atenção** (para ordenar, helper PURO em `web/src/estruturaCard.js` ou módulo puro novo, testado): abaixo do stop / acima do alvo / exercício provável / vencida (topo) > perto do stop > vence em até 5 dias (`ate_5_dias`, dias corridos) > sem stop / sem plano > perto do alvo > dentro do plano. Planner pode refinar a ordem, mas a tabela fica no PLAN e no teste.

### D2. Topo e ordenação
- O hero atual (PATRIMÔNIO TOTAL, RESULTADO ABERTO, CAIXA DISPONÍVEL, EM POSIÇÕES) FICA como está (travado por test_fase21). Nada de total novo na lista.
- Chips de ordenação: **Atenção primeiro** (padrão), **Resultado**, **Vencimento** (dias corridos, `diasParaVencimento`; posições sem opção vão ao fim). `aria-pressed`, ≥44px de alvo de toque. Ordenação em helper puro testado; desempate estável (ticker).
- Vencimento SEMPRE em dias corridos, com o texto que já existe ("vence em N dias") — o "pregões" do mockup NÃO entra.

### D3. Linha da lista (do mockup B)
- Andar 1: ticker (mono) + selo "+ <estratégia>" quando há estrutura | resultado do cabeçalho (o MESMO `res.cabecalho` de `linhasResultadoV6`: combinado ações+opções quando a estrutura tem resultado; senão só ações com a legenda existente; suspenso/desatualizado com o chip existente).
- Andar 2: mini-régua (sem estrutura e com plano completo) OU texto curto da estrutura (piso/teto) | chip de estado (o estado principal + proximidade/vencimento, por prioridade — UM chip) | variação %.
- Linha inteira é um `<button>` (ou `<a>`) acessível, ≥44px, `aria-label` com ticker + resultado + estado. Mantém `id={"posicao-" + p.t}` no item (travado em test_cartao_v6_fechado:99 e âncora de deep link).
- Perna avulsa entra como linha também (sem régua; "só opções"), DEPOIS das posições como hoje, e abre a folha com o conteúdo atual do `CartaoPernaAvulsa`.
- Estados: carregando/falha de leitura por linha usam os mesmos estados de hoje (`situacaoPlano`, `modoLeitura`), com "Tentar de novo" acessível na folha.

### D4. Folha de detalhe
- Camada nova de navegação (Onda J): id novo em `ORDEM_CAMADAS` (navStack.js), `estadoNav.modais`, `fecharCamada` em `aplicarSubida`; estado de qual posição está aberta sobe para o App (padrão `stopAlvoFor`) ou via canal tipo `reportarNav*`. Swipe/voltar/Esc fecham. `useDialogA11y` (foco, Esc, devolve foco à linha). Guardião `test_ui_onda_j.mjs:19` atualizado com nota datada.
- Conteúdo = o card de posição como já existe (cabeçalho com resultado + corpo enxuto da opção A, faces Ação/Opções, Bóris IA, Compras, editor de stop/alvo), aberto por padrão dentro da folha. Preferir REUSAR `CartaoPosicao` (ex.: prop que força aberto / modo folha) a duplicar markup, preservando os recortes `functionBody(...)` dos guardiões.
- `prefers-reduced-motion` respeitado na animação da folha.

### Claude's Discretion
- Reuso exato do `BottomSheet` existente (App.jsx ~1962) vs painel próprio; nome da camada; onde vive o estado da ordenação (local da tela; persistir em localStorage com try/catch é opcional).
- Guardiões: toda asserção que trave o loop de cards grandes (test_cartao_v6_*, test_estrutura_card_ui, test_carteira_perna_avulsa, test_fase461_ui, test_concentracao_carteira, test_ui_onda_g, test_curadoria_ui, test_carteira_lastro_ui, test_ritmo_sp …) ganha substituta com nota `2026-10-13 (quick 261013-cqk)`; nada apagado sem substituta. Componente novo entra na lista do test_ritmo_sp.
</decisions>

<specifics>
- Inventário (Explore, 2026-10-13), pontos-chave: CarteiraScreen 5728-5880 (loop 5854-5869, avulsas 5870-5876); hooks `useEstruturasPosicao` 4379 e `useLeiturasPlano` 4478; `estadoPrincipalV6` estruturaCard.js:220-256; `linhasResultadoV6` estruturaCard.js:408-498; `_estado` de estrutura estrutura_posicao.py:277-314 (dias corridos); `leitura_plano` cartao_posicao.py:188-242 (`posicaoNoPlano`, `distStopPct`, `distAlvoPct`); BottomSheet App.jsx:1962-1984; navStack ORDEM_CAMADAS l.38; fiação de camada App.jsx ~10324 / ~10343; `aberto` do CartaoPosicao é estado local (4937) e não entra no estadoNav.
- `openPnL` do hero soma só ações (opções separadas em `opcoesPnL`) — não mexer.
- App.jsx ~164k tokens: NUNCA ler inteiro. Sem dependências novas, sem worktree, sem publicar/push. Executor roda guardiões tocados + testes novos + pytest dos módulos do backend tocados + `npx vite build`; suíte canônica e `cap copy ios` com o orquestrador.
- Skill `didatica-boris` para toda copy nova (Estudo = professor, Operador = mesa); nenhuma promessa de resultado.
</specifics>

<canonical_refs>
- ./CLAUDE.md; .claude/skills/didatica-boris/SKILL.md
- Mockup: https://claude.ai/artifact/TJaJEJipdksEPky2xy61zX (OpcaoBLista.dc.html, OpcaoBFolha.dc.html)
- .planning/quick/261013-29f-card-de-posicao-enxuto/261013-29f-SUMMARY.md (corpo enxuto, guardião test_cartao_posicao_enxuto)
</canonical_refs>
