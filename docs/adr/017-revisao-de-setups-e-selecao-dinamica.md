# ADR-017: Revisão de setups e seleção dinâmica por desempenho histórico

**Status:** Aceito — decisões de produto tomadas pelo Alex (revisão em Plan Mode, 2026-08-20).
**Data:** 2026-08-20
**Companion:** ADR-015 (medição), ADR-016 (diagnóstico). Este ADR é sobre **o que fazer** com o
diagnóstico do ADR-016 — Alternativa B ("reconstruir a seleção sobre o que o backtest mostrar
que funciona"), especificamente o Adendo 7 (pesar setups por desempenho histórico, a primeira
intervenção que funciona).
**Harness:** `scripts/backtest_sinal.py`, `scripts/backtest_pesos.py` — reexecutáveis, sem I/O
de produção. Nenhum código de produção foi alterado na investigação (ADR-016) nem neste ADR.

---

## Contexto

O ADR-016 mediu, em replay determinístico sobre 15 anos (2011–2026, 125.938 sinais, 74 tickers),
que o motor de setups tem expectância negativa (−0,105R/operação) e perde para entrar em dia
sorteado com a mesma geometria (−0,016R). O Modo Operador (mecânica real: trailing ATR 2× + alvo
dinâmico) é a pior das quatro mecânicas de saída testadas (−0,167R). O único achado positivo do
ADR-016 (Adendo 7): pesar setups pela expectância medida na janela anterior, com protocolo
estritamente out-of-sample (walk-forward, sem vazamento de futuro), leva a expectância de
−0,099R para +0,005R — empate estatístico, não lucro, mas elimina quase todo o déficit. Persistência
confirmada (Spearman +0,523 entre rankings de janelas consecutivas, t=+7,52, positiva em 13 de 14
transições).

Este ADR decide: (1) o destino de cada um dos 17 pares setup×lado, (2) onde e como o mecanismo
de seleção dinâmica roda em produção, (3) o destino imediato do Modo Operador.

## Decisão 1 — critério de revisão dos 17 setups

**Rejeitado:** cortar por |t| (significância estatística). t = ExpR × √n / desvio é efeito ×
tamanho de amostra — usar |t| como critério de aposentadoria faz o corte responder a quantas
observações existem, não ao prejuízo. Prova no próprio dado: Setup 9.1 baixa (−0,031R, n=4.708,
t=−2,25) e Setup 9.1 alta (−0,036R, n=5.134, t=−2,70) têm dano quase idêntico e vereditos opostos
só por causa de 426 observações a mais — um critério que muda de resposta sozinho conforme a
amostra cresce não é critério de decisão, é cronômetro.

**Adotado:** magnitude econômica (ExpR), em 3 faixas. Só a faixa catastrófica (ExpR ≤ −0,15R)
recebe aposentadoria **estática** do motor de decisão — piso de segurança defensável mesmo com
dado novo chegando. As faixas intermediária ("custam material", −0,05 a −0,11R) e de ruído
(ExpR > −0,05R) **não** recebem veredito estático — ficam para a seleção dinâmica (Decisão 2), que
se autocorrige e pode reabilitar um setup que volte a funcionar, algo que uma lista estática fixa
não pode fazer sem reabrir o mesmo debate todo ano.

| Faixa | Setups | Destino |
|---|---|---|
| Sangram de verdade (≤−0,15R) | Ponto Contínuo (baixa/alta), Setup 9.2 (baixa/alta), Inside Bar (baixa), Máx/Mín LW 9.4 (baixa) — 6 pares, 49.569 sinais, ExpR médio ≈−0,192R | **Aposentar do motor** (estático) |
| Custam material (−0,05 a −0,11R) | PFR (baixa), 123 topo, Máx/Mín LW 9.4 (alta), Setup 9.3 (baixa), 123 fundo — 5 pares | Aguarda seleção dinâmica |
| Ruído (>−0,05R) | Inside Bar (alta), Setup 9.1 (alta/baixa), Setup 9.3 (alta), PFR (alta) — 5 pares | Manter didático (decisão pedagógica, custo de operar ~zero) |
| Positivo | IFR2 (alta): +0,072R, n=2.934, t=+3,99 | **Manter no motor**, sempre exposto com o número — nunca como setup vencedor isolado |

Aposentar a faixa catastrófica tira o motor de −0,105R para ≈−0,048R — melhora real, ainda
negativo. Essa aritmética, por si, é **in-sample** (seleciona pelos mesmos 15 anos sobre os quais
a "melhora" é medida — o mesmo erro que o ADR-015 documentou, um nível acima); a estimativa
honesta de ganho é o +0,005R out-of-sample já medido no Adendo 7, não a aritmética desta tabela.
A tabela é transparência e piso de segurança, não o conserto.

Padrão observado e explicitamente **não** transformado em critério: em 6 de 8 pares alta/baixa,
o lado comprado tem dano menor que o vendido — consistente com o achado colateral do Adendo 1
(lado vendido pior nos dois intervalos), mas "restrição de lado" já foi testada e refutada como
filtro (Adendo 6) e o período medido tem viés de alta estrutural não separado por lado. Não se
decide por lado sem medir num período de baixa.

"Aposentar" ≠ apagar: o detector permanece em `server/app/setups.py` (guardião de teste não se
apaga); sai da lista que `_vale()`/`regime.ranquear()` tratam como operável, ganhando um campo
informativo (`aposentado: true`, com o número que justifica) em vez de ser removido da lista —
`detect_setups()` tem chamador único (`technical_snapshot.py`), mas o STU alimenta 8+ rotas
(scan, radar diário, N1/N2/N3, trailing); remover da lista quebraria consumidores por engano.

## Decisão 2 — arquitetura da seleção dinâmica

**Um ledger, duas leituras**, não dois mecanismos independentes. Tabela nova no banco principal
(`ticker, setup, lado, data_sinal, data_resolucao, resultado, status`) — o banco principal, não
`admin_cache`/`analytics.db` (esse é só para o portal admin; o motor de decisão precisa ler do
mesmo banco que `radar_daily`/`kv` já usam). Duas agregações SQL sobre o mesmo ledger:
**cumulativa** (histórico exibido junto do setup na UI, atualizada a cada sinal resolvido) e
**por janela fechada** (elegibilidade que `regime.ranquear()` consome, congelada até a próxima
virada de janela).

- **Bootstrap** (15 anos × 74 tickers, ~126k sinais): roda **uma vez**, fora do `scheduler_loop`
  (não pode competir com heartbeat/kill-switch no mesmo laço asyncio). Comando manual documentado,
  não recorrente; reexecutável para disaster recovery ou mudança de família de setup.
- **Manutenção diária**: hook novo no padrão de `radar_daily.should_run()`/`maybe_run()`,
  pendurado no `scheduler_loop` — avança o cursor por ticker com candles que `candle_cache` já
  buscou (sem custo extra de brapi, ADR-008), resolve sinais pendentes, regrava as agregações.
  Custo comparável ao próprio `radar_daily` — O(74 tickers) com candles marginais.
- **Janela de reavaliação: anual.** Não é meio-termo arbitrário — é a granularidade sob a qual
  `scripts/backtest_pesos.py` mediu a persistência (Spearman +0,523, t=+7,52). Janela mais curta
  fura ainda mais o piso mínimo de amostra por célula; mais longa dilui reatividade sem ganho de
  evidência medida.
- **Dois pisos de amostra, para perguntas diferentes**: revisão estrutural (Decisão 1, all-time)
  usa n≥100; elegibilidade por janela herda **n≥40 literalmente** de `backtest_pesos.py` (mudar o
  número invalidaria o resultado empírico que justifica a técnica). Célula abaixo do piso nunca
  vira "elegibilidade negativa" — ausência de evidência ≠ prova de mau desempenho; cai no
  comportamento atual sem peso histórico.
- **Carimbo obrigatório**: `medidoAte`/`calculadoEm` em todo número exibido. Degrada visualmente
  (nunca bloqueia) se o job atrasar mais de 2 dias úteis.
- **Reprodutibilidade**: as funções puras de replay (`sinais_do_ticker`, `avaliar`) são promovidas
  de `scripts/backtest_sinal.py` para um módulo novo em `server/app/` (`signal_replay.py`); o
  script vira wrapper fino sobre a mesma lógica — uma única fonte de verdade, não duas
  implementações do mesmo cálculo. Sentido de dependência preservado (scripts→app, nunca o
  contrário).
- **Guard do bug de granularidade do Yahoo** (`range=max` devolve velas mensais mesmo pedindo
  diário/semanal — hoje só coberto em `backtest_sinal.py`, ausente em `server/app/yahoo.py` para
  intervalos não-intraday): porta `_confere_granularidade` para dentro de `yahoo.get_history`,
  cobrindo todos os intervalos — impossível de esquecer, em vez de depender de cada novo caller
  lembrar de importar um utilitário.
- **`detect_setups()`** ganha campo informativo (`historico: {expR, n, medidoAte, elegivel}`),
  lido de cache em processo com TTL curto — nunca esconde o setup, só anota. **`regime.ranquear()`
  usa `elegivel`/`expR` como peso novo no `radarScore`**, no mesmo lugar onde `gatilhoAlinhado` e
  o desempate por confluência já vivem — regra determinística, testável isolada.

**Guardrail explícito (CVM/princípio 5, já vetado pelo ADR-016):** isto é regra determinística.
Se em algum momento a proposta for deixar a IA escolher setup, ordenar o Radar ou decidir entrada,
isso é mudança de natureza e exige aprovação separada.

## Decisão 3 — destino do Modo Operador

O Modo Operador executa automaticamente, com dinheiro simulado do usuário, a pior mecânica de
saída medida (−0,167R), e nenhum setup hoje — aposentado ou mantido — sustenta operação com
confiança; IFR2 (alta), o único positivo, é modesto demais para sustentar o Operador sozinho.

**Decidido:** suspender `entradaAuto` do Modo Operador imediatamente (gate reversível, não é
desligar a feature), religando automaticamente — gated pela elegibilidade da seleção dinâmica
(Decisão 2) — quando o Bloco 1 estiver em produção. Enquanto a seleção dinâmica não existe, cada
dia de `entradaAuto` ligado é mais perda simulada sem base estatística para justificá-la.

## Sequenciamento de entrega

1. **Fase 6** (ADR-015 — instrumentação prospectiva, já planejada e revisada, 0 blockers) primeiro:
   execução pura, zero risco de design, destrava a fundação de medição prospectiva antes de
   qualquer texto de produto precisar contrastar retrospectivo × prospectivo.
2. **Revisão dos setups** (Decisão 1: campo `historico`/`aposentado`, gate de `entradaAuto`).
3. **Seleção dinâmica** (Decisão 2: ledger, bootstrap, hook diário, guard do Yahoo, `regime.ranquear`).
4. **Interface e IA**: vocabulário novo (`skill_ref.py`/`copy.js`, sem frase canônica hoje para
   "expectância negativa medida" nem "empate estatístico, não lucro"), telas do Radar/Watchlist/
   Operador, religa `entradaAuto` gated pela elegibilidade.

## Consequências

- O Radar e o card de setup passam a mostrar histórico medido, não confluência como proxy de
  qualidade — muda a métrica primária que o usuário vê primeiro.
- O Modo Operador fica sem entrada automática até a seleção dinâmica existir — usuários que
  dependiam disso precisam ser avisados (Bloco 3/4, vocabulário e estado de UI dedicados).
- Nenhuma regra de decisão migra para julgamento de IA; toda a seleção continua auditável e
  testável isoladamente, como qualquer outro cálculo determinístico do motor.
