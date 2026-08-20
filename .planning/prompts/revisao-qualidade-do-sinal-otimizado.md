# Prompt — Revisão da qualidade do sinal (confluência, famílias de setup, novos setups)

**Alvo:** Claude Code, no repo `b3-agente`
**Modo sugerido:** Plan Mode
**Natureza:** pesquisa + desenho. Nenhuma alteração em código de produção neste prompt.

---

<contexto_travado>
Estes pontos já foram verificados no código e nos dados. Use-os como ponto de
partida — investigar de novo é desperdício.

**1. A confluência quase não varia — por construção.**
`_confluencia()` (`setups.py:68-71`) é `round(100 × Σpeso_ok / Σpeso)` sobre os
critérios do próprio setup. `_vale()` (`setups.py:504-506`) exige que TODOS os
critérios `obrigatorio=True` estejam `ok` para o setup sequer aparecer. Como
cada setup tem 3 critérios e a maioria é obrigatória, a confluência varia apenas
pelo critério opcional restante. Enumerando os valores alcançáveis por setup:

| Setup | Pesos (\* = obrigatório) | Confluências possíveis |
|---|---|---|
| `_setup_9_3` | 3\*, 2\*, 3\* | **[100]** |
| `_setup_ponto_continuo` | 3\*, 2\*, 3\* | **[100]** |
| `_setup_9_2` | 3\*, 3\*, 1 | [86, 100] |
| `_setup_ifr2` | 3\*, 3\*, 1 | [86, 100] |
| `_setup_pfr` | 3\*, 3\*, 1 | [86, 100] |
| `_setup_inside_bar` | 3\*, 3\*, 1 | [86, 100] |
| `_setup_9_4_lw` | 3\*, 3\*, 1 | [86, 100] |
| `_setup_reversao` | 3\*, 2, 2 | [71, 100] |
| `_setup_compressao` | 3, 1 | [75, 100] |
| `_setup_pullback` | 3\*, 3, 2 | [62, 75, 100] |
| `_setup_rompimento` | 4\*, 3, 1 | [50, 62, 88, 100] |
| `_setup_9_1` | 4\*, 2, 1 | [57, 71, 86, 100] |
| `_setup_123` | 4\*, 2, 1 | [57, 71, 86, 100] |

Em dois setups a confluência é literalmente constante. Em cinco, "100%" significa
apenas que o critério opcional de peso 1 (de 7) também bateu.

**2. A confluência governa a ordenação do Radar.** `regime.ranquear()`
(`regime.py:212-262`) ordena por `(tier de regime, momentum relativo, gatilho
alinhado, −confluência)`. Uma variável quase constante está no critério de
desempate que decide o que o usuário vê primeiro.

**3. Observação do dono do produto:** os ativos com confluência 100% para alta
saíram majoritariamente por stop, com prejuízo simulado. Isso é consistente com
(1) — um seletor que não seleciona entrega uma amostra aproximadamente aleatória.
Confirmar ou refutar isso com dado é o item 1 do trabalho.

**4. `confluencia` não é gravada no outcome** (`analysis_outcomes.registrar`,
`analysis_outcomes.py:60-100`). Não existe hoje série histórica ligando
confluência a desfecho. A Fase 6 (ADR-015) passa a gravá-la, mas gera dado só
daqui pra frente. Para responder agora, o caminho é recomputar setups sobre
candles históricos — ver `<fases>`, Fase 1.

**5. O que NÃO é o problema aqui.** O ADR-015 (`docs/adr/015-*.md`) diagnosticou
que a *medição* de eficiência está quebrada, e a Phase 6 conserta isso. Este
trabalho é sobre a *qualidade do sinal* — escopo distinto. Não re-litigue o
ADR-015 nem reabra a rejeição do TradingView (ToS §3, decidida).
</contexto_travado>

<objetivo>
Responder, com evidência: **o motor de seleção do Boris+ produz sinal com
expectativa positiva, e se não produz, o que muda isso?**

Quatro perguntas subordinadas:
1. A confluência, como implementada, tem poder discriminante? (hipótese de
   trabalho: quase nenhum — quantifique.)
2. As famílias de setup hoje implementadas têm expectativa positiva quando
   medidas individualmente sobre histórico real da B3?
3. Que setups, filtros ou critérios documentados na literatura e na prática de
   operadores de referência da B3 se aplicam a este motor e valem ser testados?
4. Qual o desenho de menor risco que melhora a assertividade sem sair do cálculo
   determinístico?
</objetivo>

<fases>

## Fase 1 — Medir o motor contra histórico real (fundação; nada depende de opinião)

Construa um harness de replay determinístico, fora do caminho de produção
(sugestão: `scripts/` ou `server/tools/`, não `server/app/`). `detect_setups`,
`plano_operacional`, `plano_do_resultado` e `_avaliar_entry` são funções puras
sem I/O — dá para rodá-las sobre candles históricos direto. `candle_cache.py` já
persiste candles; complete o que faltar via a fonte já contratada (brapi/Yahoo,
ADR-008), respeitando o orçamento de requisições.

Cobertura mínima para o resultado ter significância: universo do Radar (ou os
~60 tickers mais líquidos da B3), 3+ anos, todos os 13 setups.

Meça, por setup e por faixa de confluência:
- taxa de acerto, expectância em R, profit factor, drawdown máximo em R;
- número de observações independentes por célula (célula com n baixo é reportada
  como insuficiente, não como resultado);
- desfecho segmentado por regime (`regime.classificar()`) — a tese do ADR-009
  nunca foi validada por falta de amostra, e aqui ela é validável de graça.

Ancore a entrada no gatilho (`plano["entrada"]`), não no close — o ADR-015
mostra que ancorar no close mede ruído e infla a taxa de stop. Se a Phase 6 já
tiver sido executada, reuse `_avaliar_entry` corrigida; se não, replique a regra
correta no harness e diga isso no relatório.

**Proteção contra o próprio harness:** 13 setups × faixas × regimes é seleção
múltipla. Reporte o número de configurações avaliadas junto com qualquer
resultado, e valide em janelas rolantes (walk-forward) em vez de um backtest
único. Um número bonito obtido testando 40 combinações não é evidência —
Bailey & López de Prado, *The Deflated Sharpe Ratio* (2014).

**Critério de aceite:** uma tabela por setup com n, expectância em R e IC ou
faixa de incerteza, reproduzível por um comando; e um veredito explícito sobre
a hipótese "confluência 100% não discrimina" — confirmada, refutada ou sem
amostra suficiente para decidir.

## Fase 2 — Confrontar com o que a evidência externa diz

Duas frentes, ambas alimentando hipóteses testáveis na Fase 1 (não conclusões
soltas):

**a) Literatura e prática de mercado.** Gestão de risco e desenho de sistemas
sistemáticos: dimensionamento de posição por volatilidade, R:R assimétrico,
filtros de regime, validação walk-forward, sobreajuste por seleção múltipla.
Priorize fonte primária e prática documentada sobre blog agregador.

**b) Operadores de referência da B3.** Material público de operadores e casas de
análise reconhecidas no mercado brasileiro, com atenção ao que é específico da
B3: liquidez por papel, leilão de abertura e fechamento, circuit breaker,
after-market, comportamento de gap, sazonalidade de vencimento de opções e
futuros. Os setups 9.x/IFR2/PFR/123/inside bar/Larry Williams já implementados
vêm dessa escola — vale entender como quem os usa profissionalmente os filtra,
porque a diferença entre o setup cru e o setup filtrado costuma ser o que separa
resultado de ruído.

**Uso de material de terceiros:** sintetize e cite a fonte; não reproduza trechos
extensos de texto protegido. Prefira fonte de acesso público. Nada de scraping do
TradingView — ToS §3, já rejeitado no ADR-015.

**Critério de aceite:** cada achado externo vira uma hipótese formulada de modo
testável no harness da Fase 1 ("filtro X sobre o setup Y deve elevar a
expectância de A para B"), com a fonte citada. Achado que não vira hipótese
testável entra numa lista separada de "contexto, não acionável".

## Fase 3 — Desenho das mudanças

Proponha de 2 a 4 mudanças concretas, cada uma com: o que muda em qual arquivo,
o ganho medido no backtest, o que se perde, e como falha.

Espaço de solução que já se abre a partir do contexto travado — não é lista
fechada, e não presuma que a resposta está aqui:
- redesenhar a escala de confluência para que ela discrimine (mais critérios
  opcionais, pesos que separem, ou substituir o percentual por um score contínuo
  com evidência de poder preditivo);
- aposentar ou rebaixar setups cuja expectância medida não se sustente;
- promover filtros que a Fase 1 mostrar eficazes (regime, liquidez,
  volatilidade, distância da média, contexto de índice);
- trocar o eixo de ordenação do Radar se a confluência não sobreviver como
  critério de desempate;
- ajustar o piso de R:R ou o dimensionamento — sabendo que consolidar a constante
  é pré-requisito (ADR15-05, Phase 6) e que o valor em si é decisão de produto.

**Marque explicitamente** qualquer proposta que aproxime a decisão de julgamento
não verificável da IA. O cálculo de manchete, entrada, stop, alvo e
posicionamento vem de regra determinística (CLAUDE.md, Princípio 5; guardrail
CVM). Mudar *quais* regras determinísticas o motor usa está dentro do escopo;
mover a decisão para a IA está fora e precisa de aprovação separada e explícita.

</fases>

<entregavel>
Um ADR em `docs/adr/` (numeração seguinte à 015), no formato narrativo dos ADRs
existentes do repo, contendo:

1. Diagnóstico com números reais do backtest — nenhum número estimado. Onde o
   dado não existir, diga que não existe.
2. As alternativas da Fase 3 com trade-off explícito de cada uma.
3. Uma recomendação, com o que ela custa e onde ela quebra.
4. Seção própria marcando o que exigiria aprovação separada por tocar o
   Princípio 5.
5. Limitações honestas: tamanho de amostra, número de configurações testadas,
   viés de sobrevivência do universo escolhido, período coberto.

O harness da Fase 1 fica versionado e reexecutável — o resultado precisa ser
reproduzível por quem ler o ADR depois.
</entregavel>

<restricoes>
- Pesquisa e desenho neste ciclo. Mudança em `server/app/` ou `web/src/` fica
  para depois da aprovação do ADR, em prompt separado.
- O harness de backtest é código novo, fora do caminho de produção — não altera
  o motor que hoje atende o usuário.
- Todo número do relatório vem do harness ou de fonte citável.
- Suíte canônica verde ao final: `bash scripts/executar.sh --testes`.
- Entregue no escopo pedido. Se discordar da direção, diga em uma frase e siga
  com a sua recomendação registrada no ADR.
- Delegue a subagentes quando a pesquisa externa e o backtest puderem correr em
  paralelo; teto de 4 subagentes simultâneos.
</restricoes>
