# ADR-015: Assertividade do motor de recomendação — diagnóstico e caminho de melhoria

**Status:** Proposto — aguardando aprovação. Nenhum código de produção foi
alterado nesta rodada; este documento é pesquisa + desenho.
**Data:** 2026-08-20
**Pesquisa completa:** `.planning/quick/260820-0hl-pesquisa-e-design-assertividade-do-motor/260820-0hl-RESEARCH.md`
**Gatilho:** observação subjetiva do Alex de que as operações fecham
desproporcionalmente mais por STOP do que por ALVO; hipótese inicial de
scraping do TradingView para embasar a revisão.

---

## Resumo para decisão

1. **A observação original não é a causa raiz.** O motor pode até estar
   stopando demais — mas o instrumento que mediria isso está quebrado, e
   quebrado na direção que esconde o problema, não que o revela.
2. **A medição de eficiência da IA fabrica stops.** `analysis_outcomes`
   avalia um trade que o motor nunca propôs: ancora a entrada no *close* do
   dia da análise, ignorando o gatilho. Reavaliando os mesmos planos com o
   gatilho correto, o placar muda de forma material (ver §2).
3. **O painel "Eficiência da IA" reporta o erro na direção oposta ao que o
   Alex percebeu.** Com os dados de desenvolvimento, a metodologia atual do
   produto mediu **expectância +2,56R (n=44)** — edge aparentemente forte,
   acima do piso de amostra do próprio produto. A metodologia corrigida, nos
   mesmos dados, mede **0,00R (n=6)**. O erro é otimista, não pessimista.
4. **Em produção o volume é maior (392 registros, 159 resolvidos) e os dois
   bugs de instrumentação estão presentes em 100% dos registros** — não é
   artefato do banco local de dev.
5. **TradingView está descartado**: sem API pública de dados e com o ToS
   proibindo nominalmente o uso pretendido (scraping, "price referencing",
   "algorithmic decision-making", "risk management programs" e "creating
   products or services based on TradingView content").
6. **Nenhuma alternativa deste documento move cálculo do motor determinístico
   para julgamento de IA.** Todos os defeitos encontrados são código
   determinístico medindo código determinístico — Princípio 5 do CLAUDE.md e
   o guardrail CVM (manchete só do motor) permanecem intactos em todas as
   opções abaixo.

---

## Contexto

### Como a pergunta foi verificada

Não há "taxa de stop×alvo" pronta no produto — ela precisou ser reconstruída.
Duas fontes de dado real foram usadas, ambas leitura pura (nenhuma escrita):

- **Dev local**: `server/data/b3_agente.db`, consulta direta à tabela `kv`.
- **Produção** (Railway, projeto `bolsIA`, serviço `b3agente`): `railway ssh`
  rodando um script Python read-only (`sqlite3` em `mode=ro`, sem importar
  módulos do app, sem tocar estado de processo vivo) contra `/data/b3.db`.
  Aprovado explicitamente pelo Alex antes de execução, por tocar produção.

### O que existe hoje — pipeline determinístico (arquivo:linha)

| Etapa | Onde | O que faz |
|---|---|---|
| Confluência | `setups.py:68-71` `_confluencia()` | `round(100 × Σpeso_ok/Σpeso)` |
| Corte de confluência | `setups.py:480` `MIN_CONFLUENCIA=50` + obrigatórios `ok` | Filtra setup fraco |
| Plano operacional | `setups.py:575-654` | entrada (gatilho), stop, alvo1 (1R), alvo2 (2R), rr2 |
| Gate de R:R | `setups.py:559,635-637` `RR_MINIMO=1.5` | `rr2 < 1.5` ⇒ NÃO OPERAR |
| Sizing | `web/src/finance.js:107-121` | Fixed-fractional, 1% padrão, teto 5% — **usa o gatilho corretamente** |
| Execução simulada | `agent.py:821-856` | `breach_stop`/`hit_alvo`, trailing (stop só sobe), alvo dinâmico |
| Registro p/ autoavaliação | `main.py:1311-1327` (N1), `main.py:1416-1432` (N2) | Grava em `analysisOutcomes` — **aqui mora o defeito** |
| Resolução do outcome | `analysis_outcomes.py:289-325` `_avaliar_entry()` | Barreira tripla (triple-barrier: stop/alvo/10 pregões) |

A arquitetura de avaliação (barreira tripla) é a escolha certa — é o método
de López de Prado (*Advances in Financial Machine Learning*, 2018, cap. 3), a
prática padrão para rotular trades. O defeito não está na escolha do método;
está em como ele é alimentado.

### O defeito central

`main.py:1313-1325` grava, verificado linha a linha:

```python
stop  = plano.get("stop")     # invalidação do setup, ancorada no gatilho
alvo  = plano.get("alvo1")    # 1R a partir da ENTRADA (=gatilho)
preco = snap.get("close")     # close do dia da análise — NÃO é a entrada
```

`plano["entrada"]` existe (é o gatilho, usado corretamente pelo sizing em
`finance.js`) e **não é gravado**. `_avaliar_entry` usa `close` como preço de
entrada. Quando o setup está *armado* (gatilho ainda não rompido — condição
explícita de vários detectores, `setups.py:377,459`), o close cai entre o
gatilho e a invalidação: a barreira de stop fica artificialmente perto do
preço de referência.

Medido nos 13 planos de dev com desfecho: **6 de 13 tinham o stop a menos de
1% do preço de referência**, com o alvo 3,4-4,4% distante (mediana geral:
stop a 1,85%, alvo a 4,07%). Num papel da B3 com ATR diário típico de
1,5-2,5%, uma barreira a 0,6% é atingida quase com certeza em 10 pregões —
isso mede o ruído entre close e gatilho, não o motor.

Consequência quantificada (mesmos 11 planos de dev, dois cálculos sobre os
mesmos dados):

| Metodologia | n | Expectância | Placar |
|---|---:|---:|---|
| App, como o painel realmente conta (com duplicatas) | 44 | **+2,56R** | — |
| App, 1 voto por plano (sem duplicata) | 8 | +0,60R | 5 stop · 3 alvo |
| Corrigida (entrada = gatilho, alvo = alvo1 do plano) | 6 | **0,00R** | 3 stop · 3 alvo |

Dois bugs distintos, dois sinais distintos: a taxa de stop é inflada pela
âncora errada (mede ruído, não o motor); a expectância reportada é inflada
pela duplicação de `n` (abaixo) e por medir contra `alvo1` (1R) em vez do
`alvo2` que passa pelo gate de R:R real do produto. Não se cancelam —
corrompem métricas diferentes em direções diferentes, e a direção líquida do
painel é **otimista**.

### Confirmado em produção — não é artefato do banco de dev

Consulta read-only em `/data/b3.db` (392 registros em 8 escopos, período
2026-07-09 → 2026-08-20; aprovada e executada em 2026-08-20):

| Métrica | Valor |
|---|---|
| Registros resolvidos (raw, com duplicatas) | 159 |
| `resultado` raw | stop 105 · alvo 44 · expirou_pos 9 · expirou_neg 1 |
| Planos distintos (ticker,setup,stop,alvo) entre resolvidos | 66 |
| `resultado` após dedup por plano | stop 41 · alvo 21 · expirou_pos 4 |
| Maior duplicação de um único plano | 12 gravações |
| Registros com campo `entrada` presente | **0 de 159** |
| Registros com campo `confluencia` presente | **0 de 159** |

Os dois bugs de instrumentação (âncora errada, campo `confluencia` ausente)
estão em **100% dos registros de produção**, não em uma amostra pequena de
dev. O placar acima, mesmo após deduplicar por plano, ainda usa a âncora
errada (`close`, não gatilho) — **não foi refeito o replay com candle real em
escala de produção** (66 planos × histórico do Yahoo é viável, mas é trabalho
de implementação, fora do escopo desta pesquisa). Em dev, corrigir a âncora
moveu o placar de 5:3 para 3:3 no mesmo conjunto de dados — a direção do
viés é conhecida; a magnitude exata em produção, não.

### Outras lacunas de instrumentação confirmadas

- `confluencia` nunca é gravada — a pergunta comercial central do produto
  ("confluência alta acerta mais?") não tem dado para ser testada.
- `store.sell()` (`store.py:621`) não tem parâmetro `motivo` — só `origem`.
  `sell_option()` tem os dois (`store.py:704-715`, com docstring que já
  documenta a distinção certa). Para ação, a taxa stop×alvo de carteira real
  **não é computável a partir do histórico**, por design da assinatura.
- O R:R mínimo (1,5) existe em três constantes Python independentes
  (`skill_ref.RR_MIN`, `setups.RR_MINIMO`, `agent.RR_MINIMO`) mais sete
  literais hardcoded no front. Um único teste guardião cobre só
  `skill_ref` (`test_auditoria_prompts.py:167`). O comentário em
  `conceitos.py:354-356` já registra que esse valor "viveu como 1,5 em
  quatro lugares" — a auditoria de 2026-07 resolveu o texto didático, não os
  dois motores nem o front.
- Não existe motor de backtest (`grep -rn backtest server/app` só acha o
  metadado `backtestavel: True`). Toda validação depende do loop forward de
  10 pregões, que no ritmo atual (dezenas de planos por mês) leva meses a
  anos para atingir os 200+ trades que a literatura recomenda como piso de
  amostra.

---

## Alternativas avaliadas

### Alternativa 1 — Consertar só a instrumentação

Corrigir os bugs de medição sem tocar no motor de decisão:

- `main.py:1313-1327`/`1416-1432`: gravar `entrada=plano["entrada"]`,
  `alvo2`, `rr2`, `confluencia`; `_avaliar_entry` passa a exigir toque no
  gatilho antes de abrir a barreira e usa `entrada` como `preco0`.
- Deduplicar por `snapshotId` (já existe no registro, `main.py:1318`) antes
  de qualquer agregação em `compute_stats_all_users`.
- `store.sell(..., motivo=...)`, paridade com `sell_option`.
- Consolidar as três constantes de R:R em `skill_ref.RR_MIN` + guardião
  cruzado que trave as outras duas e os literais do front.
- Registros antigos sem `entrada` ficam marcados como não-comparáveis (não
  convertidos por inferência — misturar duas metodologias no mesmo agregado
  reproduziria o mesmo erro de hoje).

**Trade-off:** custo baixo (dias, não semanas), zero risco arquitetural, e é
pré-requisito de qualquer decisão futura baseada nesse painel. **Mas não
responde a pergunta original.** Mesmo corrigida, a instrumentação segue
forward-only: no ritmo atual de produção (~66 planos distintos em 6 semanas),
levaria meses para acumular amostra que a literatura considera mínima
(200+ trades, Bailey & López de Prado 2014).

### Alternativa 2 — Instrumentação corrigida + backtest determinístico com walk-forward

Alternativa 1 como pré-requisito, mais um motor de replay histórico:
`detect_setups`, `plano_operacional`, `plano_do_resultado` e (a versão
corrigida de) `_avaliar_entry` são funções puras, sem I/O — `candle_cache.py`
já persiste candles suficientes para rodar o pipeline sobre anos de histórico
e dezenas de tickers sem gastar orçamento de brapi nem 1 token de LLM.

Precisa nascer com duas proteções que a literatura marca como obrigatórias
quando 23 detectores competem e o sistema escolhe o "melhor" (`plano_do_
resultado`): **walk-forward** (reotimização/validação em janelas rolantes,
não um único backtest estático) e alguma forma de **deflação por seleção
múltipla** (Bailey & López de Prado, *The Deflated Sharpe Ratio*, 2014) —
sem isso, testar 23 detectores e reportar o melhor produz um número bonito e
estatisticamente enganoso, o mesmo tipo de erro que motivou este ADR.

**Trade-off:** é a maior alavanca de assertividade disponível — responde a
pergunta original em escala de milhares de observações em vez de dezenas, e
valida de graça a tese do ADR-009 (regime como eixo primário de seleção,
hoje implementada e não validada por falta de massa). Custo de engenharia
maior que a Alternativa 1 (motor de replay + walk-forward + deflação não são
triviais) e ainda depende da Alternativa 1 estar pronta primeiro (backtestar
com a âncora errada reproduziria o mesmo viés otimista, só que em escala
maior).

### Alternativa 3 — Scraping do TradingView (hipótese original do Alex) — não recomendada

Avaliada explicitamente por ter sido a sugestão inicial. Dois problemas
independentes, cada um suficiente para descartar:

1. **Não há API pública de dados de mercado.** TradingView não oferece
   preços, histórico ou indicadores via API; as integrações legítimas são
   webhooks de alerta (saída, não entrada de dado) e o Charting Library sob
   licença comercial separada (isso é sobre UI de gráfico, não sobre dado —
   não resolve nada de assertividade do motor).
2. **O ToS proíbe nominalmente o uso pretendido.** §3 ("Ownership of
   information... non-display usage") proíbe qualquer coleta automatizada
   ("scripts, APIs, screen scraping, data mining, robots... regardless of
   their intended purposes") e lista como uso proibido, verbatim, exatamente
   as três coisas que o Boris+ faria: *"price referencing"*,
   *"algorithmic decision-making"* e *"using data in operations control or
   risk management programs"* — além de vedar nominalmente *"creating
   products or services based on TradingView content"*, o que atinge de
   frente um produto que será comercializado (CLAUDE.md: "funções básicas
   grátis... escalando para planos pagos"). Serviços de scraping
   terceirizados não transferem esse risco — a mesma cláusula proíbe
   nominalmente o uso de "third-party products, tools, or services designed
   to facilitate... such non-display usage". TradingView bane contas por
   atividade automatizada detectada.

**Trade-off:** nenhum — é risco jurídico/comercial real sem contrapartida de
dado que as fontes já contratadas não ofereçam. A arquitetura de dados atual
(brapi master gratuita + Yahoo backup/intraday, ADR-001/ADR-008) já é decisão
travada do repo; se faltar cobertura de dado no futuro, o caminho é discutir
brapi paga ou outra fonte **licenciada**, não TradingView.

---

## Recomendação

**Alternativa 1 imediatamente, Alternativa 2 como próxima fase.** A
instrumentação está fabricando um número de negócio errado hoje — qualquer
decisão de produto apoiada no painel "Eficiência da IA" no estado atual corre
o risco de "confirmar" um edge que não existe (ou de descartar um setup
bom por causa de stops fantasmas). Consertar isso é barato e não é opcional.
O backtest com walk-forward é o que de fato responde "o motor stopa demais
proporcionalmente ao que deveria" com significância estatística — sem ele, a
pergunta original continua sem resposta confiável, só com um instrumento que
não mente mais mas ainda não tem amostra.

**Alternativa 3 (TradingView) rejeitada** — documentada aqui para que a
decisão fique registrada, não para reabrir a discussão.

**Nenhuma das alternativas recomendadas requer aprovação por tocar o
Princípio 5 ou o guardrail CVM** — são todas correções de código
determinístico medindo código determinístico. Aprovação necessária é sobre
**prioridade e orçamento de engenharia**, não sobre arquitetura de decisão.

## Fora de escopo desta rodada

- Qualquer mudança de limiar de R:R (ex. subir de 1,5 para 2,0) — não decidir
  isso antes da Alternativa 1 consolidar o valor numa única constante com
  guardião cruzado; mudar hoje significa editar 10 lugares sem rede de
  segurança.
- Implementação de qualquer item das Alternativas 1/2 — este documento é
  pesquisa + desenho, conforme escopo definido no pedido original.
- Re-litigar ADR-001/ADR-008 (fonte de dados) — a Alternativa 3 não encontrou
  motivo para reabrir essa decisão.

## Consequências se aprovado

- Registros históricos de `analysisOutcomes` anteriores à correção ficam
  marcados como não-comparáveis ao novo formato — não há reconstrução
  retroativa de `entrada` sem reintroduzir o mesmo viés (mesmo padrão já
  usado no ADR-012 para o campo `origem` de `history`).
- O painel "Eficiência da IA" (ADR-012, Fase 1) muda de número visivelmente
  após a correção — vale um aviso de release notando que o KPI foi
  recalibrado, não que "piorou".
- O backtest da Alternativa 2, se aprovado, é um motor novo (`server/app/`)
  sem I/O externo além de ler `candle_cache` — não consome orçamento de
  brapi (ADR-008, 15k/mês) nem cota de LLM gerenciada.

## Referência cruzada

- Pesquisa completa (achados B1-B5, I1-I7, fontes citadas, log de
  premissas): `.planning/quick/260820-0hl-pesquisa-e-design-assertividade-do-motor/260820-0hl-RESEARCH.md`
- `docs/adr/001-fonte-de-dados-intraday.md`, `docs/adr/008-fonte-de-cotacoes-selecionavel.md`
  — decisão travada de fonte de dados, não reaberta por este ADR.
- `docs/adr/009-eixo-de-selecao.md` — tese de regime como eixo primário,
  implementada e ainda não validada por falta de massa (a Alternativa 2 a
  validaria de graça).
- `docs/adr/012-observabilidade-v2-tendencia-eficiencia.md` — painel
  "Eficiência da IA" que consome `analysis_outcomes.compute_stats_all_users`
  e herda o defeito de instrumentação descrito aqui.
- CLAUDE.md do repo — Princípio 5 (cálculo por regra, nunca pela IA) e
  guardrail CVM (manchete só do motor determinístico), ambos intactos em
  todas as alternativas deste documento.
