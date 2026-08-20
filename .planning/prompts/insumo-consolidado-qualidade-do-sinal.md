# Insumo consolidado — investigação de assertividade do Boris+ (2026-08-20)

Bloco de contexto para colar num prompt novo. Tudo aqui foi medido ou verificado
no repo; nada é estimativa. Onde não há dado, está dito que não há.

Fontes primárias: `docs/adr/015-assertividade-do-motor-de-recomendacao.md`,
`docs/adr/016-qualidade-do-sinal-do-motor-de-setups.md`,
`.planning/prompts/pesquisa-externa-qualidade-do-sinal.md`.

---

## 1. Como a investigação começou e o que ela virou

O gatilho foi a observação do dono do produto: os ativos com confluência 100%
para alta saíam majoritariamente por stop, com o usuário perdendo dinheiro.

Duas investigações distintas saíram disso:

| | Objeto | Veredito |
|---|---|---|
| **ADR-015** | O **medidor** (`analysis_outcomes`) | Quebrado, e mentindo na direção otimista |
| **ADR-016** | O **sinal** (motor de setups) | Expectância negativa; perde para o acaso |

A observação original estava certa e era **conservadora** — não é um subconjunto
de sinais que falha, é o motor inteiro.

---

## 2. ADR-015 — a medição (Phase 6 planejada, NÃO executada)

Defeitos verificados em produção (392 registros, 159 resolvidos):

- `analysis_outcomes.registrar` ancora o outcome no **close do dia da análise**,
  não no gatilho (`main.py:1313-1325` grava `preco=snap["close"]` e nunca grava
  `plano["entrada"]`). Mede o ruído entre close e gatilho, não o motor.
- `n` inflado por duplicação: até 12 gravações do mesmo plano em produção, 24 em
  dev. `compute_stats_all_users` concatena escopos sem deduplicar, então
  `MIN_N=10` não protege de nada.
- Efeito combinado medido em dev: o painel reportaria **+2,56R (n=44)** onde a
  metodologia correta dá **0,00R (n=6)**. Erro otimista.
- `confluencia` **nunca foi gravada** — 0 de 159 registros resolvidos. A pergunta
  comercial central não tinha dado.
- `store.sell()` (`store.py:621`) não tem `motivo`; `sell_option()` tem
  (`store.py:704-715`). Taxa stop×alvo de carteira de ação é incomputável.
- `RR_MIN` vive em 3 constantes Python + 7 literais no front; só uma tem guardião.
- **Segmentação por regime tem N=0, não N baixo**: `regime` só passou a ser
  gravado em 2026-08-11; dos 159 resolvidos, nenhum tem o campo.
- Correção a uma suposição inicial: `confianca` **não** é constante em produção
  (moderada 326, baixa 39, alta 4, None 23).

**Estado:** Phase 6 planejada e revisada (5 plans, 3 waves, 2 rodadas de
plan-checker, 0 blockers) em
`.planning/phases/06-instrumentacao-assertividade-adr015/`. **Não executada.**

---

## 3. ADR-016 — o sinal (a investigação principal)

### Método

Replay determinístico do motor real: para cada pregão, recomputa
`detect_setups` + `plano_do_resultado` sobre a janela que a produção teria visto,
e avalia as N barras seguintes. Indicadores são causais e alinhados ao array de
candles, então fatiar em `t` reproduz o estado do dia `t` — sem vazamento de
futuro.

| Parâmetro | Valor |
|---|---|
| Universo | 74 tickers (`scanner.DEFAULT_UNIVERSE`) |
| Período | 2023-07 → 2026-08 (~756 pregões) |
| Janela do motor | 252 barras (`resolve_keep("1y")`, a do Radar) |
| Horizonte base | 10 pregões (`HORIZON_PREGOES`) |
| Fonte | Yahoo diário, cache em disco (não consumiu orçamento brapi) |
| Sinais gerados | 41.144 · **resolvidos: 32.095** · sem gatilho: 9.049 |

Entrada ancorada no gatilho (nunca no close). Plano "a mercado" abre a barreira
na primeira barra sem exigir toque. Empate intrabar a favor do stop. Sinal que
nunca acionou fica fora do denominador.

### Resultado central

| Barreira | n | Expectância | IC95 | t | Acerto | PF |
|---|---:|---:|---|---:|---:|---:|
| `alvo1` (1R) | 32.095 | **−0,104R** | [−0,114; −0,094] | −19,7 | 44,8% | 0,80 |
| `alvo2` (projeção) | 32.095 | −0,094R | [−0,107; −0,080] | −13,9 | 35,8% | 0,84 |

### Controle nulo — o achado que define tudo

| | n | Expectância | Acerto | t |
|---|---:|---:|---:|---:|
| Placebo (dia sorteado, mesma geometria) | 41.105 | −0,016R | 49,1% | −3,3 |
| **Motor (setup)** | 32.095 | **−0,104R** | 44,8% | −19,7 |
| **Diferença** | | **−0,088R** | | **−12,4** |

O motor **não é neutro — seleciona momentos piores que sortear um dia**. Os
setups disparam depois de o preço já ter se movido.

### Confluência

93,1% dos 41.144 sinais têm confluência 100%. Expectância por faixa:
100% → −0,103R · 86% → −0,119R · 71% → −0,094R. Não há gradiente.

Causa estrutural (não é bug de peso): `_confluencia()` (`setups.py:68-71`) divide
pelo peso total dos critérios do próprio setup, e `_vale()` (`setups.py:504-506`)
já exige todos os `obrigatorio=True`. Valores alcançáveis:

| Setup | Confluências possíveis |
|---|---|
| Setup 9.3, Ponto Contínuo | **[100]** — constante |
| 9.2, IFR2, PFR, Inside Bar, 9.4 LW | [86, 100] |
| Reversão / Compressão | [71,100] / [75,100] |
| Pullback | [62, 75, 100] |
| Rompimento, 9.1, 123 | 4 valores |

`regime.ranquear()` (`regime.py:212-262`) usa `−confluência` para ordenar o Radar.

### Por setup (diário, `alvo1`)

Nenhum positivo com significância. Melhor: **Setup 9.3 alta +0,001R (t=+0,05)**.
PFR alta +0,031R (t=+0,76). Piores: Setup 9.2 baixa −0,197R (t=−13,9), Ponto
Contínuo alta −0,230R (t=−5,8). Com 17 configurações testadas, o limiar
deflacionado é |t| ≳ 2,4 — nenhum chega perto.

### Walk-forward (6 janelas)

Nenhum setup positivo em mais de 4/6. Os dois que chegam a 4/6 (Setup 9.1 baixa,
PFR alta) têm expectância ≈ 0. Os de maior volume: 0/6, 1/6 ou 2/6.

### Regime

Lateral −0,098R · Tendência alta −0,077R · Tendência baixa −0,157R. Das 49
células setup × regime, **nenhuma positiva com significância**. A tese do ADR-009
não se sustenta como implementada.

---

## 4. Adendo 1 — teste de horizonte (hipótese eliminada)

**Variante 1 — mesmos setups diários, horizonte maior:**

| Horizonte | n | Expectância | t |
|---:|---:|---:|---:|
| 10 (produto) | 32.095 | −0,104R | −19,7 |
| 20 | 34.439 | −0,110R | −20,9 |
| 40 | 36.347 | −0,114R | −22,1 |
| 60 | 37.059 | −0,113R | −21,9 |

Piora de leve e estabiliza. Nenhum dos 17 pares melhora com significância.

**Variante 2 — barra semanal (análogo do Pellin):** agregado **pior**, −0,197R
(t=−6,5, n=956). IFR2 alta fica +0,315R (t=+2,17, n=40) mas não sobrevive à
deflação (limiar 2,35 para 16 configurações). Setup 9.1 alta — o do Pellin —
confirma a direção (55,7% de acerto) mas não a magnitude (ele reportou 67%) nem
a significância (t=+0,74, n=61).

**Lado, semanal:** comprado −0,042R (t=−0,95, indistinguível de zero) · vendido
−0,356R (t=−8,94).

---

## 5. Adendo 2 — teste "só comprado" (hipótese eliminada)

Comparação **pareada**: mesmo papel, mesmo dia, mesmo prazo — setup contra
simplesmente segurar.

**Diário (15.241 operações compradas):**

| Braço | Retorno/operação | t |
|---|---:|---:|
| Setup (entra no gatilho) | **−0,186%** | −7,1 |
| **Segurar a ação o mesmo prazo** | **+1,307%** | +25,2 |
| Placebo (dia sorteado) | −0,020% | −0,8 |

Setup − Segurar: **−1,493%, t = −32,6**, vence em 34,6% dos casos.

**Semanal (480 operações):** setup −0,249% contra segurar +4,177%; diferença
−4,426% (t=−5,05).

8 de 9 setups comprados são piores que segurar, com t entre −2,9 e −23,3.

**Única exceção — IFR2 (alta):** bate o benchmark nos dois intervalos (diário
+0,399%, t=+2,2, n=695). Mas bate **porque segurar é ainda pior** — dispara em
papéis que seguem caindo (hold −0,670%) e a saída no alvo captura o repique. O
retorno do próprio setup continua negativo (−0,271%). É o único achado
genuinamente interessante; não é produto.

**Custos:** as comparações pareadas são invariantes a custo (ambos pagam um
round-trip). O efeito de carteira favorece segurar ainda mais — o setup faz
dezenas de round-trips contra um.

---

## 6. Evidência externa (converge por caminho independente)

- **Multicolinearidade** explica o colapso da confluência: diagnóstico de 39
  indicadores técnicos achou VIF > 5 em quase todos. Checklist cujos itens
  derivam do mesmo cálculo não dá confirmações independentes. **Implicação:**
  redesenhar a confluência só ajuda com fatores de conceitos não-correlatos
  (estrutura × momentum × volume × volatilidade).
- **Chen & Metghalchi** testaram regras técnicas no Bovespa 1996–2011: não
  superaram buy-and-hold. É a evidência acadêmica mais direta sobre o mercado-alvo
  e bate com o backtest.
- **QuantBrasil** já testou IFR2 + filtro de média móvel (LREN3, 2015–2020):
  operações caíram de 160 para 100 e o retorno por operação não melhorou. **O
  atalho intuitivo tem evidência contrária.**
- **Pellin (EnANPAD 2022)**: Setup 9.1 em gráfico **semanal**, 4 ativos,
  2012–2021, 67% de acerto — mas 12–14 operações por ativo, sem custos nem
  aluguel de ação, "acumulado" em soma aritmética.
- Fora dos 13 setups: **Donchian / momentum de série temporal** tem o maior
  lastro acadêmico (horizonte de semanas a meses); **pairs trading** tem paper
  específico sobre o mercado brasileiro.

---

## 7. Hipóteses ELIMINADAS — não refazer

| Hipótese | Por que caiu |
|---|---|
| Horizonte de avaliação maior (20/40/60) | Expectância piora; nenhum setup melhora |
| Barra semanal | Agregado pior (−0,197R); só IFR2 nominal, não sobrevive à deflação |
| Só comprado | Perde de segurar por 1,49 p.p./operação (t=−32,6) |
| Filtro de média móvel como remédio | Evidência externa contrária (QuantBrasil no IFR2) |
| Redesenhar só a confluência | Setups são negativos em **todas** as faixas — reordena o ruim |
| Scraping do TradingView | ToS §3 proíbe nominalmente o uso pretendido (ADR-015) |
| Regime como salvador (ADR-009) | 49 células setup × regime, nenhuma positiva |

---

## 8. O que continua ABERTO

1. **IFR2 isolado** — mecanismo de reversão com saída disciplinada. Único setup
   que bate o benchmark, mas com retorno próprio negativo. Pergunta: existe
   configuração (filtro de entrada, alvo, prazo) em que o retorno próprio vira
   positivo?
2. **Momentum relativo cross-sectional** — o ADR-009 já o implementou em
   `regime.ranquear` mas **nunca o isolou como sinal**. Maior lastro acadêmico da
   pesquisa.
3. **Donchian / trend-following** em horizonte de semanas a meses.
4. **Pairs trading** — família estrutural diferente, com evidência B3.
5. **Score de fatores não-correlatos** para substituir a confluência na ordenação
   do Radar.
6. **Confound não resolvido:** o período medido (2021–2026 semanal, 2023–2026
   diário) tem viés de alta estrutural. "Vender é ruim" pode ser "o mercado
   subiu". Separar exige medir o lado vendido em período de baixa.

---

## 9. Alternativas do ADR-016 e recomendação atual

- **A — Parar de apresentar o sinal como operável.** Setups viram material
  didático; `plano_do_resultado` deixa de emitir COMPRAR/VENDER como manchete;
  Radar para de ordenar por confluência. Custo baixo, reversível, endereça o dano
  ao usuário hoje. **Recomendada, imediata.**
- **B — Reconstruir a seleção sobre o que o backtest mostrar.** Harness já existe.
  Custo alto, sem garantia. **Recomendada em seguida.**
- **C — Reconstruir só a confluência.** É a resposta literal à pergunta original e
  a que menos muda o resultado do usuário. **Armadilha.**

Os adendos 1 e 2 reforçaram A: cada remédio testado se eliminou.

---

## 10. Guardrails invariantes (não re-litigar)

- **Princípio 5 / guardrail CVM**: manchete, entrada, stop, alvo e posicionamento
  vêm de regra determinística; a IA explica, nunca decide. Mudar **quais** regras
  determinísticas o motor usa está no escopo; mover decisão para julgamento da IA
  exige aprovação separada e explícita.
- Bundle id `com.alexandrecamerini.bolsia` não muda.
- Paridade obrigatória `server/app/defaults.py` ↔ `web/src/catalog.js` (byte a
  byte) e `deviceStore` ↔ `serverStore` em `web/src/persistence.js`.
- Fonte de dados: brapi master com orçamento, Yahoo backup/intraday (ADR-001,
  ADR-008). Não reabrir.
- Validação: `bash scripts/executar.sh --testes` (as DUAS suítes). Front editado
  → `npx vite build`.
- Guardião de teste não se apaga; reversão deliberada atualiza o guardião com nota.

---

## 11. Artefatos

| Arquivo | O que é |
|---|---|
| `docs/adr/015-*.md` | Diagnóstico da medição |
| `docs/adr/016-*.md` | Diagnóstico do sinal + 2 adendos |
| `.planning/prompts/pesquisa-externa-qualidade-do-sinal.md` | Literatura e prática B3, rotulada por tipo de evidência |
| `scripts/backtest_sinal.py` | Replay do motor (`--horizonte`, `--intervalo 1d\|1wk`) |
| `scripts/backtest_analise.py` | Significância, IC, walk-forward, deflação |
| `scripts/backtest_placebo.py` | Controle nulo |
| `scripts/backtest_horizonte.py` | Comparação entre horizontes |
| `scripts/backtest_comprado.py` | Pareado setup × segurar × placebo |
| `.planning/phases/06-*/` | Phase 6 (instrumentação) planejada, não executada |

Nenhum código de produção (`server/app/`, `web/src/`) foi alterado em nenhuma
etapa. Suíte canônica verde em todos os commits (1104 testes pytest + runners web).

**Reprodução completa:**

```bash
cd server
./.venv/bin/python ../scripts/backtest_sinal.py --anos 3 --saida /tmp/l.json
./.venv/bin/python ../scripts/backtest_analise.py /tmp/l.json
./.venv/bin/python ../scripts/backtest_placebo.py /tmp/l.json
./.venv/bin/python ../scripts/backtest_comprado.py /tmp/l.json --intervalo 1d
```
