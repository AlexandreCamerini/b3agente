# QA 31 — Fase A implementada: autoavaliação da IA (qa/30)
*09/07/2026 · build alvo: F9-20260709-7*

Implementação do modelo aprovado em `qa/30` — Fase A (autoavaliação da IA).
Fase B (trades reais) segue pendente, sem depender desta entrega.

## 1. O que entra nesta entrega

- **Novo módulo `server/app/analysis_outcomes.py`**: captura (`registrar`),
  avaliação pura sem I/O (`_avaliar_entry`), agregação de métricas
  (`compute_stats`) e o job diário injetável (`avaliar_pendentes` +
  `maybe_run`, mesmo padrão de `radar_daily.py`).
- **Captura server-side** em `server/app/main.py`:
  - N1 (`scan_deep_run` → `deep_call`): registra quando o plano determinístico
    (`setups.plano_do_resultado`) decide COMPRAR/VENDER (stop/alvo1 sempre
    definidos nesse caso).
  - N2 (`analyze_technical_model`): registra quando a IA devolveu `proposal`
    com stop E alvo definidos (texto livre sem proposal não entra —
    avaliação só onde há risco mensurável).
  - Ambos best-effort (try/except, nunca derruba a resposta ao usuário).
- **Job diário** encaixado no `scheduler_loop` existente (`agent.py`), no
  MESMO ciclo que já roda `radar_daily.maybe_run` — sem scheduler novo.
  Prazo fixo de **10 pregões** (decidido com o Alex): dentro da janela,
  confere se bateu stop (conservador quando os dois batem no mesmo candle) ou
  alvo; se não bateu nenhum, decide pelo fechamento do 10º pregão
  (`expirou_pos`/`expirou_neg`).
- **Endpoints novos**: `GET /api/analysis-outcomes` (lista crua) e
  `GET /api/analysis-outcomes/stats` (taxa de acerto, R médio, recorte por
  setup — filtráveis por `modo`/`tipo`). Fora do `public_state` de propósito
  (pode crescer até 500 registros; só carrega quando a tela é aberta).
- **UI**: painel "EFICIÊNCIA DA IA" em Perfil → Observabilidade — taxa de
  acerto, R médio/análise, nº avaliadas, nº aguardando prazo, recorte por
  setup. Carrega 1x (não no intervalo de 15s dos outros cards — muda no
  máximo 1x/dia).
- **Armazenamento**: seção `analysisOutcomes` no kv, por escopo (`user_id`),
  cap de 500 registros OU 180 dias (o que vier primeiro). `kv_delete_user`
  já limpa por prefixo — exclusão de conta cobre esta seção automaticamente
  sem mudança adicional.

## 2. Decisões tomadas com o Alex (AskUserQuestion, registradas em qa/30)

- Escopo: autoavaliação da IA e trades reais são features SEPARADAS —
  só a primeira entra aqui.
- Horizonte: prazo FIXO de 10 pregões (não "até bater stop/alvo" em aberto).
- Cobertura: N1 (Plano da mesa) **e** N2 (Aprofundar com IA) alimentam a
  estatística.
- Onde roda o job: SERVIDOR, reaproveitando o scheduler do Radar diário.

## 3. Testes

Novo guardião puro `server/tests/test_analysis_outcomes.py` (13 casos):
registro válido/descartado/prune por quantidade; `_avaliar_entry` pura
(pendente por poucos candles, bate alvo/stop em compra, expira
positivo/negativo, geometria invertida em venda); `compute_stats` (taxa de
acerto, R médio, filtro por modo, recorte por setup); `avaliar_pendentes`
fim a fim com fetch injetado (isolamento por escopo, inclusive escopo
legado/global); `_scopes_com_outcomes`.

Novo guardião web `web/tests/test_analysis_outcomes_ui.mjs` (4 casos):
contrato do endpoint de stats (GET, filtro `?modo=`), paridade
`analysisOutcomesStats` nos dois stores, wiring real da tela (chama o store,
mostra o painel, exibe taxa de acerto e R médio).

```
Backend (offline, sandbox sem rede): 20/20 — 0 falhas, 1 pulada
(test_llm_errors.py, dependência ausente no sandbox).
Web: 26/26 — 0 falhas.
```

Sintaxe verificada (sandbox não builda Vite/pytest completo):
`python3 -m py_compile` em `main.py`/`agent.py`/`analysis_outcomes.py` e
`@babel/parser` (modo JSX) em `App.jsx` — ambos sem erro.

**Nenhum endpoint FastAPI (`/api/scan/deep`, `/api/technical/analyze`) tem
teste via `TestClient` neste projeto** — os pontos de captura novos são
cobertos indiretamente (compilação + testes puros do módulo); a validação
funcional real fica para o roteiro de hard stop abaixo.

## 4. Build

`web/src/version.js`: `BUILD_ID` `F9-20260709-6` → **`F9-20260709-7`**.

## 5. Roteiro de hard stop

1. `bash entregar.sh "qa/31: eficiência da IA (Fase A)"` (no Mac).
2. Xcode: ⇧⌘K + Run no iPhone físico.
3. Perfil → rodapé → confirmar **F9-20260709-7**.
4. Radar → "Plano da mesa (IA)" num ativo com plano COMPRAR/VENDER → confere
   se não quebrou nada (a captura é best-effort, não deve mudar o
   comportamento visível).
5. Perfil → Observabilidade → conferir o novo card "EFICIÊNCIA DA IA"
   aparece (provavelmente com "nenhuma análise ainda" na primeira vez).
6. **Não dá pra validar o job de avaliação no mesmo dia** — ele só resolve
   análises depois de 10 pregões. Validação real: registrar algumas análises
   agora, voltar em ~2 semanas e conferir se `avaliadas`/`taxaAcerto` saíram
   do zero. Se quiser confirmar a MECÂNICA mais cedo, dá pra rodar
   manualmente no servidor (Railway shell, se disponível) chamando
   `analysis_outcomes.avaliar_pendentes` com um prazo menor via env — não
   implementado nesta entrega (deixado como está, prazo fixo de 10 pregões,
   conforme decidido).

## 6. Pendente

Fase B (trades reais, mock `modo-operador.html` tela 4) — qa/30 seção B, não
iniciada. Também seguem pendentes do pedido anterior do Alex: fraseologia
(copy.js) contra os mocks, Radar sem "análise inicial rápida", "desenhar o
prompt como especialista no Claude", e itens B(resto)/C/D/E da matriz qa/26.
