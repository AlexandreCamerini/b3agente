# QA 15 — FASE 4 "Fechamento" · migração de identidade + correções 1.1–1.4
*07/07/2026 · sessão de versão final (prompt-mestre Fase 4)*

## Escopo desta rodada

1. **Migração de identidade (DECISÃO TRAVADA)** — `appId
   com.alexandrecamerini.bolsia` / `appName BolsIA` aplicados em todos os
   pontos vivos; codinome interno `b3-agente` preservado.
2. **1.1 Venda silenciosa (regressão)** — corrigida + teste-guardião.
3. **1.3 Radar 1x/dia** — automático em dia útil + manual sob demanda.
4. **1.4 Leitura da IA** — popup fechável/rolável (a) + colapsáveis e
   concisão no prompt (a+b light).
5. Manutenções de QA de baseline (asserção do `test_agent`).

## 1.1 — Venda: causa raiz e correção

**Sintoma (aparelho):** modal de venda abre, "Confirmar venda" não faz nada
(cenário confirmado pelo Alex).

**Causa raiz:** o objeto `A` é um `useMemo` cujo array de deps tinha
`buyModal` mas **não** `sellModal`. Abrir o modal de venda não recriava o
`A`; `confirmSell` ficava com closure de `sellModal = null` e o
`if (!sm) return;` virava no-op silencioso. A compra funcionava porque
`buyModal` estava nas deps. A correção anterior (`ctx.A.openSell`) estava
presente — este era um SEGUNDO bug na mesma cadeia, alcançável só depois do
primeiro.

**Correção:** `sellModal` adicionado às deps — junto com `wlScanLoading`,
`destaque` e `quotes` (mesma classe: guards furados → fetch duplicado; preço
defasado gravado no log de análise).

**Blindagem:** `web/tests/test_wiring_deps.mjs` — extrai os estados do
componente raiz, o corpo do `useMemo(A)` (strings/comentários removidos) e o
array de deps, e FALHA se qualquer estado lido no corpo estiver fora das
deps. Provado nos dois sentidos (falha sem a correção; passa com ela).

## 1.3 — Radar diário (aprovado: proposta + push opcional)

- `server/app/radar_daily.py`: gating puro testável (`should_run` — dia
  útil, horário, 1x/dia), armazenamento global (`kv` sem `user_id`; o
  universo é o mesmo para todos), telemetria `LAST_DAILY` exposta no
  `status_snapshot` (Observabilidade).
- Horário default **08:45 BRT** (candle da véspera fechado, pré-pregão);
  configurável `B3_RADAR_DAILY_HHMM`; desligável `B3_RADAR_DAILY_OFF`;
  respeita o kill-switch geral do agente.
- Roda DENTRO do `scheduler_loop` existente (`radar_fetch=yahoo.get_history`
  no startup) — sem segundo scheduler; custo de rede via `candle_cache`
  (delta + stale fallback, resiliente ao rate-limit do Yahoo).
- `GET /api/scan`: com `tickers` (watchlist) segue computando na hora; sem
  `tickers` serve o RESULTADO DO DIA armazenado; `?force=1` (botão "Varrer
  novamente") recomputa e substitui o do dia. `destaque` do dia passa a
  reusar o resultado armazenado (consistência + custo zero).
- Push "Radar do dia pronto 📡" best-effort só para quem tem token
  registrado (mesma permissão do Operador IA); falha de push nunca derruba a
  varredura.
- UI: chip "📡 Varredura automática de hoje · dd/mm hh:mm" (ou "↻ Última
  varredura (manual)") na aba Radar.
- Cadeia `force` atravessa `App.jsx → persistence.js (DOIS stores, mesma
  assinatura) → api.js → /api/scan` — invariante da interface preservado.

## 1.4 — Leitura da IA (a + b light)

**(a) Popup:** bug de flexbox — conteúdo longo sem `flex:1 + minHeight:0`
empurrava o rodapé (único "Fechar") para fora da tela e a rolagem interna
nunca ativava. Corrigido: card `overflow:hidden`, área de conteúdo
`flex:1 minHeight:0` com `-webkit-overflow-scrolling:touch` e
`overscroll-behavior:contain` (não trava a página atrás), rodapé
`flexShrink:0` + safe-area, e **✕ sempre visível no cabeçalho**. Tap fora
preservado. Resumo fica aberto; "Leitura por setup", "Cenários" e "Riscos"
viram `<Fold>` colapsáveis (mesmo padrão do "+ Modelos utilizados").

**(b light):** instrução de CONCISÃO no formato N1 do `llm.py` (resumo ≤ 3
frases; leitura por setup ≤ 2; cenário 1 frase; ≤ 3 riscos de 1 frase;
invalidação 1 frase) — "clareza didática vale mais que exaustividade".
Guardado por `server/tests/test_llm_prompt_concisao.py` (padrão grep de
wiring — verde mesmo sem `httpx`).

## Migração de identidade

`scripts/atualizar-identidade.sh` (idempotente; `--verificar` só confere)
cobre: `capacitor.config.ts`, `index.html` (title + metas
`apple-mobile-web-app-title`/`application-name`), manifest PWA do
`vite.config.js`, banner do `disclaimers.js` (dizia "B3 Agente" — violava o
invariante do nome), `configurar-apns.sh` (TOPIC), `ios-allow-http.sh`,
título do `/docs` no `main.py`, `APNS_TOPIC` do teste de push. Exceções
conscientes: guard de legado no `setup-ios.sh`, snapshots históricos
(`qa/`, `09/10/11-*.md`). Passos manuais no
`ATUALIZAR-Git-Railway-iOS.md` (portal Apple → Railway → setup-ios → clean
build → **remover app antigo** → reinstalar → reativar push).

## Nota de processo (transparência)

Durante a sessão houve um retry de turno: uma primeira passada implementou
1.3/1.4b e foi descartada, mas os arquivos persistiram no ambiente. A
passada seguinte detectou os arquivos como de origem desconhecida e os
tratou como NÃO CONFIÁVEIS: inventário completo contra a cópia pristina do
zip, revisão de segurança linha a linha (rede/eval/exec/BYOK), checagem de
invariantes e validação total — só então foram adotados, com a confirmação
do Alex de que nenhuma outra ferramenta atua no projeto.

## Validação no corte

- Backend: **23 suítes ✅** (incl. `test_radar_daily` 8/8 e
  `test_llm_prompt_concisao` 3/3) + 4 ⏭️ conhecidas (`httpx` ausente no
  sandbox — passam no pytest completo).
- Web: **11/11 ✅** (incl. `test_wiring_deps` e
  `test_fase4_radar_deepmodal`).
- `py_compile` 53 arquivos ✅ · balance do `App.jsx` ✅ ·
  `atualizar-identidade.sh --verificar` ✅.
- Correção de baseline: asserção do `test_agent` atualizada (a linha-resumo
  de ciclo da F3 entra APÓS a venda; checagem agora é por conteúdo).

## Roteiro do hard stop (aparelho) — ver ATUALIZAR-Git-Railway-iOS.md

1. Migração de identidade (passos manuais) + reinstalação.
2. Venda: parcial e total pelo Portfólio (deve executar e atualizar KPIs).
3. Leitura da IA: abrir no Radar → rolar → fechar por ✕, por "Fechar" e por
   tap fora; conferir resumo aberto + seções colapsáveis.
4. Radar: abrir a aba (deve servir resultado armazenado com chip de data) →
   "Varrer novamente" (manual substitui o do dia).
5. Push: "Testar push agora" na Observabilidade (Diário mostra motivo exato)
   → depois validar o push do Radar diário na manhã seguinte.
