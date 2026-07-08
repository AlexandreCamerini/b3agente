# PROPOSTA — Modo Operador (FASE 7)
*Gate de aprovação: nada daqui foi implementado. Aprove/ajuste este escopo e o
mock (`qa/mocks/modo-operador.html`) antes de eu escrever código.*

## 1. Conceito

Um seletor global no Perfil alterna o comportamento do app inteiro:

| | **Modo Estudo** (atual, intacto) | **Modo Operador** (novo) |
|---|---|---|
| Objetivo | Aprender a ler o mercado | Decidir e executar com disciplina |
| Carteira | Simulada (paper trading) | **Trades reais registrados à mão** (a ordem é executada na SUA corretora) |
| Vocabulário | "Estudar alta", "Monitorar", "Aguardar" | **"Comprar", "Vender", "Aguardar confirmação", "Não operar"** |
| Saída da IA | Leitura didática, cenários de estudo | **Plano operacional completo**: direção, tipo de entrada, faixa de entrada, stop técnico, alvo 1, alvo 2, R:R, condição de confirmação e de cancelamento, prazo |
| Risco | Não dimensiona | **Position sizing**: risco máx. % do capital (padrão 1%), tamanho da posição calculado por ATR/stop |
| Regra de corte | — | **R:R < 1,5:1 ⇒ o app NÃO apresenta plano** ("Não há operação com vantagem estatística clara") |
| Confiança | baixa/moderada | baixa/moderada/**alta** (alta exige confluência + confirmação multi-timeframe; sem 2º timeframe, teto = moderada) |
| Telemetria | Log de análises | **Painel de assertividade**: taxa de acerto, R médio realizado, drawdown, desempenho por tipo de setup e por regime (tendência × lateral) |

Base metodológica (persona `analise-tecnica-b3` + práticas de operadores de alta
assertividade já detectadas pelo motor): setups Stormer 9.1/9.2/9.3, IFR2,
PFR, 123, Ponto Contínuo, Inside Bar, Larry Williams 9.4 — com gestão de risco
de Stormer (stop na invalidação técnica, nunca arbitrário; parcial no alvo 1;
R:R mínimo 1,5:1, ideal ≥2:1) e position sizing por % fixo de risco.

## 2. O que muda tela a tela

1. **Perfil** — novo card "Modo de trabalho" (Estudo ↔ Operador). A troca para
   Operador exige o **Termo de Responsabilidade** (1ª vez): checkbox + rolagem
   completa; aceite fica registrado (data/versão) na conta.
2. **Radar** — mesmo scan determinístico; no modo Operador o veredito vira
   decisão (COMPRAR / VENDER / AGUARDAR CONFIRMAÇÃO / NÃO OPERAR) e o card
   ganha o mini-plano (entrada·stop·alvo·R:R). Ativos com R:R ruim mostram
   explicitamente "sem vantagem estatística".
3. **Aprofundar com IA (N1)** — novo formato `OPERADOR_PRO` (paralelo ao
   educacional, sem tocar no existente): resumo executivo, leitura técnica,
   plano operacional, invalidação, gestão de risco e UMA conclusão canônica
   entre as 4 frases fixas da persona. O LLM segue interpretando SOMENTE
   números pré-calculados (STU) — regra do projeto preservada.
4. **Watchlist/Avaliar (N2)** — análise completa com o mesmo contrato + campo
   "checklist pré-operação" (7 itens: tendência, estrutura, volume, momentum,
   volatilidade, R:R, multi-timeframe) com ✓/✗ por item.
5. **Portfólio → separação total** — nova aba interna "Trades reais": registro
   manual de ordens executadas na corretora (ticker, lado, qtd, preço, taxa,
   data, setup de origem, stop/alvo planejados). NUNCA mistura com a carteira
   simulada (armazenamento em seções novas: `realTrades`, `realPositions`).
6. **Acompanhar** — no modo Operador, o painel de assertividade substitui o
   bloco didático: acerto %, R médio, expectativa matemática, drawdown máx.,
   série de resultados por setup. Alimentado pelos trades reais fechados +
   comparação plano × executado (disciplina).
7. **Operador IA (agente)** — no modo Operador ele NÃO opera nada real (limite
   regulatório): passa a ser um **monitor de planos** — avisa por push quando
   preço atinge gatilho/entrada/stop/alvo dos planos armados.

## 3. O que NÃO muda (limites não negociáveis)

- O app **não envia ordens** a corretora nenhuma; execução é sempre do usuário.
- **Nenhuma recomendação personalizada** (perfil do usuário não altera a
  decisão técnica; altera apenas o position sizing, que é aritmética).
- Cálculo 100% em Python (indicadores/setups/R:R/sizing); LLM só redige sobre
  números prontos. Guardrail novo `GUARDRAILS_PRO`: proíbe promessa de
  resultado, percentuais de acerto sem base, e mantém as 4 conclusões fixas.
- Disclaimer obrigatório em TODA saída do modo Operador (texto da persona).
- Modo Estudo permanece o padrão para contas novas e para a App Store.

## 4. Arquitetura (resumo técnico)

- `config.appMode: "estudo" | "operador"` (padrão "estudo") + 
  `config.operadorTermo: {aceitoEm, versao}` — nos dois stores, mesma interface.
- `config.risco: {pctPorTrade: 1.0, capitalOperacional: null}` (sizing).
- Backend: `llm.OPERADOR_PRO` + `PRO_FORMAT` (JSON com decisão/plano/checklist)
  paralelos aos educacionais; rota N1/N2 escolhe o formato pelo `appMode` do
  escopo. `setups.py` já produz gatilho/invalidação/alvo — ganha função pura
  `plano_operacional(setup, atr, capital, pct_risco)` (entrada, stop, alvos,
  R:R, qtd) com testes.
- Seções novas no kv: `realTrades` (histórico), `realPositions` (abertas),
  `planosArmados` (monitor). Espelho no deviceStore (local-first, como sempre).
- Assertividade: agregado calculado em Python (`kpi_operador.py`) sobre
  `realTrades` — taxa de acerto, R médio, expectativa, drawdown, por setup.

## 5. Entrega em fases (cada uma com hard stop)

- **F7.1** Seletor de modo + termo + vocabulário/decisões no Radar (sem IA
  nova) + `plano_operacional()` com testes.
- **F7.2** Formato PRO no N1/N2 + checklist pré-operação + guardrails PRO.
- **F7.3** Trades reais (registro/posições/histórico) + monitor de planos com
  push.
- **F7.4** Painel de assertividade + comparação plano × executado.

## 6. Riscos e mitigação

- **App Store**: manter Estudo como padrão + termo explícito + disclaimers
  reduz risco de rejeição (finance guidelines); revisar `qa/17` antes da F7.2.
- **Confusão simulado × real**: separação visual forte (mock) + seções de
  dados distintas + banner permanente "trades reais são registros manuais".
- **Expectativa de "sinal infalível"**: as 4 conclusões canônicas + regra de
  corte por R:R tornam o "não operar" um resultado de primeira classe.

---
*Aprovando (ou ajustando) esta proposta + o mock, eu inicio a F7.1.*
