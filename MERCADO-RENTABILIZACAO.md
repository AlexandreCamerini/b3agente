# MERCADO & RENTABILIZAÇÃO — BolsIA
*FASE 4 · Bloco 4 · visão de operador de bolsa + dev sênior de produto*

## 1. Posicionamento: qual guerra NÃO vamos lutar

O mercado BR de apps de bolsa tem quatro territórios ocupados: **dados e
monitoramento** (TradeMap — cotações, alertas, notícias), **fundamentos e
rankings** (Investidor10 — indicadores, comparadores), **consolidação de
patrimônio** (Gorila/Kinvo) e **execução** (home brokers e seus simuladores,
que são a corretora sem o risco — e sem professor). O jogo educacional da
própria B3 é gamificação rasa: ensina a mecânica do pregão, não a decisão.

Nenhum deles responde à pergunta que trava o nosso usuário: **"por que essa
seria (ou não) uma operação razoável — e como eu penso isso sozinho na
próxima vez?"**

**Job to be done:** "Já tenho conta na corretora e medo de errar. Quero
treinar decisões com dados reais e receber feedback que me ensine o
raciocínio, sem arriscar meu dinheiro." O BolsIA é o único posicionado como
**academia de decisão**: pipeline técnico determinístico + IA que explica em
vocabulário educacional + operador autônomo simulado que mostra disciplina
de risco funcionando + jornada completa (Radar → Avaliar → Operar →
Acompanhar). O concorrente real não é o TradeMap — é o usuário operar no
escuro ou pagar R$ 200/mês num curso gravado.

**Mensagem de uma linha:** *"Erre aqui, aprenda o porquê, acerte lá fora —
sem arriscar um centavo."*

## 2. Rentabilização: estrutura concreta do freemium

A alavanca é a **cota de IA gerenciada** (decisão já travada). O desenho
abaixo protege o hábito no grátis e cobra pela profundidade e pelo servidor:

| | **Grátis** | **BolsIA Pro** |
|---|---|---|
| Paper trading, carteira, KPIs | Ilimitado | Ilimitado |
| Radar diário (varredura armazenada) | ✅ (custo marginal ~zero) | ✅ |
| Leitura N1 (aprofundar com IA) | **3/dia** | 30/dia |
| Análise completa N2 | **1/dia** | 15/dia |
| Stop/alvo N3 com cenários | — | ✅ |
| Operador IA no servidor (app fechado) | — | ✅ |
| Push (Radar do dia, ações do operador) | — | ✅ |
| Relatório semanal da carteira | — | ✅ |
| **BYOK (sua chave OpenAI)** | **N1/N2/N3 ilimitados no aparelho** | idem |

- **Preço:** R$ 14,90/mês ou **R$ 99/ano** (~45% off — a assinatura anual é
  onde apps indie BR ganham margem e reduzem churn). Abaixo de R$ 15/mês é o
  teto psicológico do público iniciante BR; um único "curso de trade" custa
  10–20x isso — âncora fácil na comunicação.
- **Apple:** entre no **Small Business Program** ANTES da primeira venda
  (comissão cai de 30% para 15%): R$ 14,90 → ~R$ 12,66 líquidos. Anual R$ 99
  → ~R$ 84. Break-even da infra (Railway + IA gerenciada do free tier) fica
  na casa de poucas dezenas de assinantes.
- **BYOK permanece gratuito e ilimitado** para as análises — decisão
  estratégica: (a) custo zero para nós; (b) fideliza o público técnico que
  evangeliza; (c) é o nosso anti-lock-in honesto. A linha de corte do Pro
  fica nos recursos que EXIGEM o nosso servidor (operador agendado, push,
  relatório) — impossíveis de replicar com BYOK, portanto a alavanca não
  vaza.
- **Custo da cota grátis:** com o modelo barato, 3×N1 + 1×N2 por dia custa
  centavos/usuário/mês; o metering da Fase 3 já mede por usuário — revisar o
  teto após os primeiros 30 dias de dados reais.

## 3. Aquisição: canais realistas para um indie solo BR

1. **O próprio Radar como mídia (motor principal):** todo dia útil o app
   gera uma leitura educacional às 8h45. Publicar 1 short/dia
   (TikTok/Reels/YouTube Shorts) "a leitura do Radar de hoje em 60s" — com
   os disclaimers — é conteúdo infinito, barato e demonstra o produto. CTA:
   "a análise completa está grátis no app".
2. **Creators médios de finanças (10–100k):** não comprar publi de gigante;
   oferecer 3 meses de Pro + código de 1 mês para a audiência. O pitch para
   o creator é confortável: "simulador educacional, sem promessa de ganho" —
   ninguém queima reputação.
3. **ASO PT-BR:** "simulador de bolsa", "paper trading", "aprender a
   investir" têm volume alto e concorrência fraca em qualidade; a ficha
   proposta no qa/17 já mira esses termos.
4. **TestFlight público como pré-lançamento:** link aberto em comunidades de
   estudo (grupos de Telegram/Discord de análise técnica, r/investimentos)
   pedindo feedback — beta testers viram os primeiros reviews 5★.
5. **Não fazer (por enquanto):** mídia paga (CAC de finanças no BR é
   proibitivo para indie) e SEO de blog (retorno em 12+ meses).

## 4. Riscos e as linhas que NÃO cruzamos

- **Regulatório (CVM) — a linha vermelha:** recomendação individualizada de
  compra/venda de valores mobiliários é atividade regulada (análise: Res.
  CVM 20; consultoria: Res. CVM 19). Nossa proteção já está na arquitetura:
  vocabulário fixo sem imperativo (guardrail testado), LLM só interpreta
  números pré-calculados, disclaimers em todo output, dinheiro simulado.
  **Nunca adicionar:** "sinais" em tempo real acionáveis, ranking de "melhores
  ações para comprar", copy-trading, integração de execução com corretora,
  depoimentos de rentabilidade. Qualquer feature futura passa por este
  filtro antes de qualquer outro.
- **Dados (Yahoo/brapi):** dependência de fonte não-contratual; o
  candle_cache (delta + stale) já amortece. Gatilho de ação: no primeiro mês
  com receita recorrente, orçar provedor pago (ex.: Cedro, ou B3 UP2DATA via
  distribuidor) — custo entra no business case do Pro.
- **Custo de IA vs. receita:** o risco é o free tier viralizar sem
  conversão. Mitigações já embutidas: cota diária dura + metering por
  usuário + kill-switch; a conversão é puxada por recursos de servidor, não
  por "mais tokens".
- **Apple:** categoria Educação + posicionamento sem promessa financeira
  reduz fricção de revisão (justificado no qa/17).

## 5. Roadmap pós-lançamento (razão impacto/esforço)

1. **Relatório semanal por push** — "sua semana simulada: resultado, melhor
   e pior decisão, o que estudar". Infra 100% pronta (agente + push +
   snapshots + LLM). *Impacto alto / esforço baixo.* Retenção semanal e
   vitrine do Pro.
2. **Sequência de estudo (streak) sobre o Radar diário** — o Radar já cria o
   ritual das 8h45; contar dias seguidos de leitura custa um contador e
   multiplica DAU. *Alto / baixo.*
3. **Diário de trade com nota da IA no fechamento** — ao encerrar uma
   posição simulada, a IA compara plano × execução ("stop respeitado? saiu
   antes do alvo por quê?"). É o coração pedagógico do produto. *Alto /
   médio.*
4. **Ranking mensal de carteiras simuladas (opt-in, por apelido)** —
   competição saudável sem expor dados; zera todo mês para não desanimar
   entrantes. *Médio / médio.*
5. **Modo replay histórico** — treinar decisões num período passado do
   candle_cache (ex.: "opere 2020") com avanço candle a candle. Diferencial
   brutal de "academia", mas exige UI própria. *Alto / alto — fase seguinte.*

## 6. Sequência executiva sugerida (90 dias)

Semanas 1–2: TestFlight público + Small Business Program + publicar política
de privacidade. Semanas 3–4: submissão App Store + começar os shorts diários
do Radar. Mês 2: IAP do Pro no ar (paywall nos pontos N3/Operador/push) + 3
parcerias com creators. Mês 3: relatório semanal + streak; revisar cotas com
os dados do metering; decidir provedor de dados pago conforme receita.
