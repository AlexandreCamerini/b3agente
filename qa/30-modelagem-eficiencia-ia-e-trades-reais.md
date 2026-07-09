# QA 30 — Modelagem: eficiência das análises da IA + trades reais
*09/07/2026 · PROPOSTA — aguardando aprovação, nada implementado ainda*

Decisões já fechadas com o Alex (AskUserQuestion):
- **Escopo:** duas features SEPARADAS, sem misturar dado — (A) autoavaliação
  da IA (compara recomendação vs. o que o ativo fez depois) e (B) trades
  reais (registro manual, mede a disciplina do Alex), como já desenhado no
  mock `modo-operador.html` tela 4.
- **Horizonte:** prazo FIXO de 10 pregões pra uma análise (A) virar
  estatística.
- **Cobertura:** N1 (Plano da mesa/Radar, tem plano estruturado) **e** N2
  (análise individual, às vezes texto livre) entram na feature A.

---

## A. Autoavaliação da IA (o pedido original)

### A1. O que já existe e pode ser reaproveitado
- `server/app/store.py` `push_analysis_log()` + endpoint
  `POST /api/analysis-log/{ticker}` + `store.pushAnalysisLog()` no cliente —
  hoje só chamado pelo N2 individual (`App.jsx` linhas ~4169 e ~4348),
  cap de 20 entradas POR TICKER, sem avaliação (só guarda o que a IA disse).
  Vira a BASE da captura, mas precisa: (1) também disparar no N1/scanDeep,
  (2) perder o cap de 20/ticker (viraria estatística incompleta), (3) ganhar
  campos de resultado que hoje não existem.
- `setups.plano_do_resultado()` (N1) já calcula stop/alvo estruturado —
  usar como fonte de risco pra virar R-multiple. N2 às vezes só devolve
  markdown livre sem `proposal` — nesse caso a avaliação é só direcional
  (subiu/desceu vs. recomendado), sem R-multiple.
- `technical_snapshot` + `yahoo.get_history` já são a fonte de preço/candles
  usada em todo o app — reaproveitar pra buscar o preço N pregões depois.
- O agente (`agent`/scheduler) já roda em ciclo de fundo (ring buffer,
  próxima passada, guard de sobreposição) — encaixar o job de avaliação
  nesse mesmo ciclo em vez de criar um scheduler novo.

### A2. Modelo de dados (novo, servidor)
Nova seção KV `analysisOutcomes` (lista, não dict por ticker — precisa
agregar entre ativos pras estatísticas). Cada item:

```json
{
  "id": "uuid",
  "ticker": "PETR4",
  "modo": "operador",              // ou "estudo"
  "tipo": "n1",                    // "n1" (scanDeep) | "n2" (analyze)
  "modelo": "gpt-4o-mini",         // modelLabel/model retornado pela IA
  "setup": "IFR2",                 // melhorSetup do N1, quando houver
  "recomendacao": "comprar",       // do kpis.recomendacao / veredito
  "stopProposto": 37.60,
  "alvoProposto": 40.05,
  "precoNaAnalise": 38.57,
  "snapshotId": "...",
  "criadoEm": "2026-07-09T22:00:00Z",
  "prazoPregoes": 10,
  "resultado": "pendente",         // pendente | alvo | stop | expirou_pos | expirou_neg
  "precoResolucao": null,
  "rMultiple": null,
  "resolvidoEm": null
}
```

Cap por sanidade: manter os últimos **500 registros OU 180 dias**, o que
vier primeiro (evita blob JSON gigante no SQLite KV) — ajustável depois se
precisar de histórico maior.

### A3. Captura (onde entra no código)
- **N1** (`scan_deep_run`, `server/app/main.py`): dentro de `deep_call()`,
  logo após `res = await llm.analyze_deep(...)`, empurra 1 registro por
  ticker analisado — captura SERVER-SIDE (mais confiável que depender do
  cliente, já que scanDeep processa vários tickers de uma vez).
- **N2** (`analyze_technical_model`): mesma ideia, dentro do handler, após
  `result = await llm.analyze_structured(...)` — substitui/complementa o
  `pushAnalysisLog` client-side atual (best-effort, pode falhar em silêncio).

### A4. Avaliação (job periódico)
Roda 1x/dia (encaixado no ciclo do agente ou no mesmo horário do
`radar_daily`, 08:45 BRT): busca todos os `analysisOutcomes` com
`resultado == "pendente"` cujo `criadoEm` já passou de 10 pregões, pega o
preço mais recente via `yahoo.get_history`, e decide:
- Se o preço bateu o alvo em algum candle da janela → `"alvo"`.
- Se bateu o stop antes → `"stop"`.
- Se não bateu nenhum dos dois até o prazo → `"expirou_pos"` (fechou acima
  do preço de entrada) ou `"expirou_neg"` (fechou abaixo).
`rMultiple` só calculado quando há `stopProposto` (risco definido); senão
fica `null` e a entrada conta só pra taxa de acerto direcional.

### A5. Métricas + UI
Novo endpoint `GET /api/analysis-outcomes/stats` (filtros opcionais
`modo`, `setup`, `modelo`) devolvendo: taxa de acerto, R médio, nº de
análises avaliadas/pendentes, recorte por setup e por modo — mesmo padrão
visual de stat-cards do mock (`v`/`l`). Tela nova "Eficiência da IA",
proposta em Perfil → Observabilidade (mesmo lugar dos outros diagnósticos
técnicos, longe da carteira simulada pra não confundir).

---

## B. Trades reais (mock `modo-operador.html` tela 4)

Feature separada, sem tocar na carteira simulada nem no modelo acima.

### B1. Modelo de dados
Nova seção KV `realTrades` (lista): `{id, ticker, qtd, entrada, stop, alvo,
dataAbertura, status: "aberto"|"fechado", dataFechamento, precoSaida,
setup, origemPlanoId}`. `origemPlanoId` (opcional) referencia um
`analysisOutcomes.id` quando o trade nasceu de um plano da mesa — é o que
permite calcular "disciplina" de verdade (entrada/stop executados dentro do
que a IA/plano sugeriu) em vez de assumir.

### B2. Endpoints
`POST /api/real-trades` (registrar), `PATCH /api/real-trades/{id}` (fechar
com preço de saída), `GET /api/real-trades` (listar abertos/fechados).

### B3. UI
Réplica funcional da tela 4 do mock: card "ASSERTIVIDADE" (taxa de acerto,
R médio/trade, drawdown máx., disciplina%, recorte por setup) + tabela
"POSIÇÕES REAIS ABERTAS" + botão "+ Registrar trade". Push de aviso ao
tocar stop/alvo pode reaproveitar o `notify.js` já existente (mesma
mecânica de monitor armado do Radar).

---

## Ordem de implementação sugerida

1. **Fase A** primeiro (autoavaliação da IA) — é o pedido original, não
   depende de UI nova de cadastro manual, e o job de avaliação é o
   componente mais arriscado tecnicamente (vale validar cedo).
2. **Fase B** depois (trades reais) — feature de produto nova, maior
   superfície de UI, pode esperar a Fase A estar rodando e gerando dado
   real.

Cada fase segue o padrão do projeto: teste-guardião por mudança, suíte
completa antes de qualquer entrega, carimbo de build novo, doc de fechamento
em qa/.

**Decidido:** o job de avaliação roda no SERVIDOR (Railway), encaixado no
mesmo scheduler que já dispara o Radar diário (08:45 BRT) — não cria
infraestrutura nova, só mais uma tarefa no ciclo existente.
