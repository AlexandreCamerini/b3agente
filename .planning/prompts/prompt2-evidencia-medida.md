# Prompt 2 — Revisão dos setups e camada de evidência medida

**Alvo:** Claude Code no repo `b3-agente` · **Modo:** Plan Mode primeiro
**Natureza:** desenho + implementação faseada. Planejar antes de escrever código.

> Este bloco é autossuficiente: todos os números necessários estão aqui. Os
> documentos-fonte servem para aprofundar, não para você reconstruir o contexto.

---

<fontes>
- `docs/adr/016-qualidade-do-sinal-do-motor-de-setups.md` — a investigação
  completa, com 7 adendos. **Leia antes de propor qualquer coisa.**
- `docs/adr/015-assertividade-do-motor-de-recomendacao.md` — a medição forward
  quebrada; a Phase 6 que a conserta.
- `.planning/prompts/insumo-consolidado-qualidade-do-sinal.md` — resumo executivo.
- `.planning/prompts/pesquisa-externa-qualidade-do-sinal.md` — literatura e
  prática B3, rotulada por tipo de evidência.
- `.planning/phases/06-instrumentacao-assertividade-adr015/` — 5 planos prontos,
  revisados por plan-checker (0 blockers), **não executados**.
- `scripts/backtest_{sinal,analise,placebo,horizonte,comprado,periodo,operador,gate,pesos}.py`
  — o harness. Determinístico, sem LLM, sem consumo de orçamento brapi.
</fontes>

<estado_da_evidencia>
Replay determinístico do motor real: 74 tickers, **15 anos (2011–2026), 125.938
sinais resolvidos**. Nenhum código de produção foi alterado em nenhuma medição.

**O motor tem expectância negativa e perde para o acaso.**
−0,105R por operação (t = −39,6), acerto 44,6%. Entrada em dia sorteado com a
mesma geometria rende −0,016R — o setup seleciona momentos **piores que o
aleatório** (diferença −0,088R, t = −12,4).

**Não é artefato de período.** Anos de alta do índice: −0,091R. Anos de baixa:
−0,132R. Nem vendendo em ano de queda o motor ganha (−0,089R).

**Não é artefato de geometria de saída.** A mecânica real do Operador foi medida
(trailing ATR 2× + alvo dinâmico, réplica de `agent.py:804-836`): **−0,167R**,
pior que o plano do Estudo (−0,115R). O trailing dobrou o ganho médio
(+1,00R → +1,99R) e o acerto caiu de 44,3% para 25,3% — gestão de risco limita
estrago, não cria edge.

**O lado comprado perde de simplesmente segurar a ação** por 1,49 p.p. por
operação (t = −32,6), em comparação pareada (mesmo papel, mesmo dia, mesmo prazo).

**A confluência não discrimina, e não tinha como.** 93,1% dos sinais valem 100%,
porque `_vale()` (`setups.py:504-506`) exige todos os critérios `obrigatorio=True`
e cada setup tem só 3 critérios. Em 2 dos 13, 100% é o **único** valor possível;
em 5 outros, um de dois. `regime.ranquear()` (`regime.py:212-262`) ordena o Radar
por essa variável quase constante.

## Hipóteses ELIMINADAS por medição — não repropor

| Hipótese | Resultado |
|---|---|
| Horizonte maior (20/40/60 pregões) | Piora: −0,110 / −0,114 / −0,113R |
| Barra semanal | Agregado pior (−0,167R, n=9.671) |
| Só comprado | Perde de segurar (−1,49 p.p., t=−32,6) |
| Gestão de saída (trailing, alvo dinâmico, parcial) | Todas pioram |
| Gate de regime como porta | Melhor combinação em −0,051R |
| Filtro de volatilidade corrente | Nulo (−0,113 / −0,100 / −0,103) |
| Continuação alinhada à tendência (tese do ADR-009) | **Pior** que a base (−0,128R) |
| Filtro de média móvel | Evidência externa contrária (QuantBrasil, IFR2) |
| Momentum relativo cross-sectional | Direção certa em 6/6, t = +0,6 a +1,1, forte viés de sobrevivência |
| Redesenhar só a confluência | Setups negativos em todas as faixas |
| Scraping do TradingView | ToS §3 proíbe o uso pretendido |

## O que FUNCIONA — e é a base desta fase

**Pesar setups pelo desempenho histórico.** Protocolo anti-circularidade: peso
sempre de janela anterior, avaliação out-of-sample.

- **Persistência confirmada:** Spearman médio de **+0,523** entre rankings de
  janelas consecutivas (erro-padrão 0,070, **t = +7,52**), positiva em **13 de 14**
  transições. O ranking de setups não embaralha.
- **Efeito out-of-sample:** selecionar só os setups positivos na janela anterior
  leva a expectância de **−0,099R para +0,005R** — elimina praticamente todo o
  déficit. As três regras testadas (positivos, top 3, top 1) chegam ao mesmo
  lugar, então não é regra escolhida a dedo.
- **O que ela é:** filtro que remove os perdedores consistentes, não seletor que
  acha o vencedor. Leva ao **empate** (t = +0,67), não ao lucro. Empate antes de
  custos é prejuízo depois deles.
- **Teto:** com informação do futuro (impossível) o resultado seria +0,062R. Não
  há prêmio grande escondido esperando a regra de seleção certa.
- **Custo:** corta 84% dos sinais (117.530 → 18.936).

## O único setup com evidência positiva

**IFR2 (alta)** é positivo e significativo nos dois intervalos com amostra grande:

| Intervalo | n | Expectância | t | Acerto | PF |
|---|---:|---:|---:|---:|---:|
| Diário, 15 anos | 2.934 | **+0,072R** | **+3,99** | 53,4% | 1,16 |
| Semanal, 10 anos | 263 | **+0,164R** | **+2,79** | 58,2% | 1,42 |

Ambos acima do limiar deflacionado de |t| ≈ 2,4 para 17 configurações. É reversão
à média — coerente com o único recorte que a literatura acertou aqui (reversão em
mercado lateral foi o melhor recorte família × regime da investigação, −0,051R).
</estado_da_evidencia>

<tabela_dos_setups>
Desempenho de cada setup, 15 anos, barreira `alvo1` (1R), saída fixa. **Esta é a
base da revisão pedida no Bloco 0** — não precisa recalcular.

| Setup | n | Expectância | IC95 | t | Acerto | PF |
|---|---:|---:|---|---:|---:|---:|
| IFR2 (alta) | 2.934 | **+0,072R** | [+0,04; +0,11] | **+3,99** | 53,4% | 1,16 |
| PFR (alta) | 2.280 | −0,008R | [−0,05; +0,03] | −0,42 | 49,4% | 0,98 |
| Setup 9.3 (alta) | 15.580 | −0,010R | [−0,02; +0,01] | −1,24 | 49,4% | 0,98 |
| Setup 9.1 (baixa) | 4.708 | −0,031R | [−0,06; −0,00] | −2,25 | 48,6% | 0,93 |
| Setup 9.1 (alta) | 5.134 | −0,036R | [−0,06; −0,01] | −2,70 | 48,2% | 0,93 |
| Inside Bar (alta) | 2.071 | −0,045R | [−0,09; −0,01] | −2,18 | 47,2% | 0,91 |
| 123 de fundo (alta) | 9.286 | −0,051R | [−0,07; −0,03] | −5,58 | 47,3% | 0,88 |
| Setup 9.3 (baixa) | 14.496 | −0,058R | [−0,07; −0,04] | −7,38 | 46,8% | 0,88 |
| Máx/Mín LW 9.4 (alta) | 8.558 | −0,101R | [−0,12; −0,08] | −9,80 | 44,9% | 0,80 |
| 123 de topo (baixa) | 8.805 | −0,104R | [−0,12; −0,09] | −11,23 | 44,4% | 0,77 |
| PFR (baixa) | 2.517 | −0,105R | [−0,14; −0,07] | −5,47 | 44,4% | 0,80 |
| Máx/Mín LW 9.4 (baixa) | 10.484 | −0,162R | [−0,18; −0,14] | −17,74 | 41,7% | 0,70 |
| Inside Bar (baixa) | 1.940 | −0,167R | [−0,21; −0,13] | −8,00 | 41,9% | 0,69 |
| Setup 9.2 (alta) | 17.519 | −0,191R | [−0,20; −0,18] | −26,31 | 40,4% | 0,67 |
| Setup 9.2 (baixa) | 15.636 | −0,204R | [−0,22; −0,19] | −26,70 | 39,8% | 0,65 |
| Ponto Contínuo (alta) | 2.410 | −0,230R | [−0,27; −0,19] | −12,08 | 38,3% | 0,61 |
| Ponto Contínuo (baixa) | 1.580 | −0,261R | [−0,31; −0,21] | −11,18 | 36,8% | 0,57 |

Detectores em `setups.py`: `_setup_pullback`, `_setup_rompimento`,
`_setup_reversao`, `_setup_compressao`, `_setup_9_1`, `_setup_9_2`, `_setup_9_3`,
`_setup_ifr2`, `_setup_pfr`, `_setup_123`, `_setup_ponto_continuo`,
`_setup_inside_bar`, `_setup_9_4_lw` (linhas 214-478, `detect_setups` em 483).
</tabela_dos_setups>

<decisao_de_produto_a_confrontar>
O ADR-016 recomendou parar de apresentar o sinal como operável. Este trabalho é a
forma construtiva disso: em vez de remover a recomendação, **substituí-la por
evidência medida** — e usar a evidência como insumo do próprio motor.

A tese: o Boris+ para de ser provedor de sinal e passa a ser escola de avaliação
de sinal. O usuário não aprende "compre quando o 9.2 aparecer"; aprende "o 9.2
apareceu — e é assim que se descobre se ele vale alguma coisa".

**Confronte a tese explicitamente no plano, não a assuma.** Quatro perguntas a
responder antes de propor tela:

1. Um produto que mostra que seus próprios setups perdem dinheiro ainda tem
   proposta de valor? Qual, exatamente, e o que no fluxo atual sustenta ou
   contradiz isso?
2. **Modo Operador**: ele executa automaticamente a pior das mecânicas medidas
   (−0,167R). Manter com seleção dinâmica, restringir ou desligar é decisão de
   produto — apresente o trade-off com recomendação e marque como decisão do
   Alex. Enquanto não for decidido, cada dia é mais perda simulada do usuário.
3. **IFR2**: expor o único vencedor entre dezessete convida o usuário a operá-lo
   isoladamente. Isso é responsável, dado que ele é positivo mas modesto
   (+0,072R) e que concentrar num único setup é o oposto do que a evidência
   ensina?
4. **A seleção dinâmica leva ao empate, não ao lucro.** Como o produto comunica
   isso sem que o usuário leia "agora funciona"?

Se concluir que a tese não se sustenta, diga em uma frase e proponha a
alternativa — não entregue tela bonita sobre premissa furada.
</decisao_de_produto_a_confrontar>

<escopo>

## Bloco 0 — Revisão de todos os setups (pedido explícito do Alex)

Decidir, **setup por setup**, o destino de cada um dos 17 pares da tabela acima.
Três destinos possíveis, e a decisão precisa de justificativa por evidência:

- **Aposentar** — sai do motor de decisão. Candidatos óbvios: Ponto Contínuo
  (ambos os lados, −0,23R e −0,26R, t = −12 e −11) e Setup 9.2 (ambos, −0,19R e
  −0,20R, t = −26). São os que a seleção dinâmica removeria de qualquer forma.
- **Manter como material didático, fora da decisão** — o padrão gráfico continua
  sendo ensinado e identificado na tela, sem virar recomendação.
- **Manter no motor** — só com evidência que sustente. Hoje isso é IFR2 (alta).

Restrições dessa revisão:
- Aposentar ≠ apagar. Guardião de teste não se apaga (regra do repo); detector
  removido do motor de decisão precisa de nota dizendo por quê e com qual número.
- `detect_setups` alimenta o STU (`technical_snapshot.py:133`), que N1/N2/N3
  leem. Mexer no conjunto de setups muda o `snapshotId` e o que a IA enxerga —
  mapeie o efeito antes de propor.
- A decisão de aposentar é **de produto**, não sua. Traga a tabela com a
  recomendação por linha e o critério usado; o Alex decide.

## Bloco 1 — O backtest vira dado de produto E insumo de decisão

Duas funções, e a segunda é a novidade:

**(a) Evidência para mostrar** — o histórico medido de cada setup vira dado
servido pela API, exibido junto do setup.

**(b) Insumo do próprio motor** — a seleção dinâmica do Adendo 7: a cada janela,
os setups elegíveis são os que tiveram expectância positiva na janela anterior.
Determinístico, auditável, sem IA.

Decisões que o plano precisa tomar, com justificativa:
- **Onde o cálculo roda.** 125k sinais por request está fora de questão. O padrão
  de cache diário do ADR-012 (`admin_cache`, hook no `scheduler_loop`) é
  precedente do repo.
- **Qual a janela de reavaliação** e como evitar que o produto fique instável
  (setup entra e sai a cada rodada). O Adendo 7 usou 15 janelas em 15 anos
  (~1 ano cada); janela mais curta reage mais rápido e rui mais.
- **Como o dado envelhece.** Carimbo de data de corte visível. Dado de 2026
  exibido em 2027 sem carimbo é o mesmo pecado de proveniência do FIX-C11.
- **Piso de amostra por célula** e o que exibir abaixo dele.
- **Reprodutibilidade.** O comando que reproduz o número fica documentado.

Reuse `scripts/backtest_sinal.py` — já é determinístico e puro. Extraia o
compartilhado; não reescreva o motor de replay.

## Bloco 2 — Instrumentação prospectiva

A Phase 6 está planejada, revisada (0 blockers) e não executada. Decida: executar
como está, ajustar, ou sequenciar depois do Bloco 1 — com o motivo. Ela conserta
a âncora, a duplicação, os campos ausentes (`entrada`, `confluencia`, `alvo2`,
`rr2`) e o `motivo` em `store.sell()`.

Atenção: com o Bloco 1 entregue, o dado retrospectivo existe e o prospectivo
continua raso por meses. A UI precisa conviver com isso sem sugerir que são a
mesma coisa.

## Bloco 3 — Interface

- A evidência aparece **junto do setup**, quando ele é apresentado — não numa aba
  de estatísticas que ninguém abre.
- Resultado negativo com o mesmo destaque que positivo. O CLAUDE.md já proíbe
  manipulação visual de resultado; aqui é o ponto central.
- Vocabulário por modo vem de `skill_ref.py` (backend) e `copy.js` (front). O
  front não compõe vocabulário.
- Estados completos: sem amostra, amostra insuficiente, dado desatualizado,
  setup aposentado.
- Consulte `.claude/skills/didatica-boris/SKILL.md` antes de escrever texto
  didático.

## Bloco 4 — Camada de IA

- Recebe o número pronto no snapshot; nunca recalcula nem infere.
- Explica o conceito: expectância × taxa de acerto, R múltiplo, tamanho de
  amostra, por que "perdeu de segurar a ação" importa, por que empate antes de
  custos é prejuízo depois.
- Amostra insuficiente → diz textualmente.
- Prompt novo entra nos **dois** lados da paridade byte-exata.

</escopo>

<restricoes_invariantes>
- **Princípio 5 / guardrail CVM.** Todo número de performance vem de código
  determinístico. A IA lê o número pronto e explica; nunca calcula nem estima. A
  manchete do card continua vindo do motor. **A seleção dinâmica do Bloco 1(b) é
  regra determinística — se em algum momento a proposta for deixar a IA escolher
  setup, ordenar Radar ou decidir entrada, isso é mudança de natureza e exige
  aprovação separada e explícita.**
- **Nunca misturar metodologias no mesmo número.** Expectância retrospectiva
  (backtest) e prospectiva (`analysis_outcomes`) medem coisas diferentes. Cada
  número exibido declara origem e janela. Misturá-las repete o erro do ADR-015 um
  nível acima.
- **Sem promessa.** Amostra insuficiente se declara como tal. A frase canônica
  ("Não há dados suficientes para concluir") existe para isso.
- Paridade obrigatória: `server/app/defaults.py` ↔ `web/src/catalog.js` (byte a
  byte) e `deviceStore` ↔ `serverStore` em `web/src/persistence.js`.
- Fonte de dados: brapi master com orçamento, Yahoo backup (ADR-001, ADR-008). O
  backtest usa cache e não consome cota do app.
- **Cuidado com o Yahoo:** `range=max` devolve velas MENSAIS com HTTP 200 mesmo
  pedindo `1d` ou `1wk` — o guard de `yahoo.get_history` só cobre intraday. Ranges
  honrados: `15y`/`1d`, `10y`/`1wk`. `scripts/backtest_sinal.py` tem
  `_confere_granularidade()`; reuse essa defesa em qualquer código novo que baixe
  série.
- Validação: `bash scripts/executar.sh --testes` (as DUAS suítes). Front editado
  → `npx vite build`.
- Guardião de teste não se apaga; reversão deliberada atualiza o guardião com nota.
</restricoes_invariantes>

<entregavel>
1. **Tabela de decisão do Bloco 0** — 17 linhas, destino recomendado e critério.
2. **ADR** para as decisões estruturais do Bloco 1 (onde roda, janela de
   reavaliação, política de exibição) e para o destino do Modo Operador.
3. **Plano de fase GSD** em `.planning/phases/`, no padrão do repo (frontmatter,
   waves, `must_haves`, tasks com `read_first`/`action`/`acceptance_criteria`
   verificáveis). Rode o plan-checker antes de executar.
4. **Implementação** dos blocos aprovados, suíte canônica verde, `npx vite build`
   quando o front for tocado.
5. **Verificação ao vivo**: o número na tela é o mesmo que o harness produz, e o
   carimbo de data está correto.
</entregavel>

<como_trabalhar>
- Plan Mode primeiro. Nenhum código de produção antes do plano aprovado.
- Inventário do que já existe antes de propor peça nova — o repo tem precedente
  para quase tudo (cache diário do ADR-012, STU, vocabulário por modo, editor de
  prompt byte-exato).
- Decida sozinho o rotineiro. Traga ao Alex só decisão de produto: destino dos
  setups, destino do Modo Operador, quanto de resultado negativo o produto exibe.
- Se discordar de algo aqui, diga em uma frase e siga com sua recomendação
  registrada — não pare para debater.
- Teto de 4 subagentes simultâneos.
</como_trabalhar>
