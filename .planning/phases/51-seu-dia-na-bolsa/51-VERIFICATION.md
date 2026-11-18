---
phase: 51-seu-dia-na-bolsa
verified: 2026-11-18
status: human_needed
score: 7/7 success criteria verified in code; 0 gaps; human checkpoint items pending
gaps: []
human_verification:
  - test: "Teste em iPhone real (push do fechamento, toque no push, toggle em Perfil, convite no card)"
    expected: "Push chega só após aceitar o convite (conta existente) e abre o card"
    why_human: "APNs e WKWebView não verificáveis por grep/pytest"
  - test: "Rodar scripts/dia_na_bolsa_calibrar.py com rede (12 meses)"
    expected: "Frequência das regras de raridade aceitável (alvo ~1 fato/semana pela união); p95 isolado do IBOV ~5% dos pregões"
    why_human: "Sandbox sem rede; limiares travados, decisão do Alex. Amplitude exige >=30 ativos (catálogo tem 20; o job usa o universo do Radar, a confirmar na calibração)"
  - test: "P-C: job roda às 17:20 BRT, textos dizem ~17:15"
    expected: "Decisão do Alex (ajustar texto ou horário)"
    why_human: "Decisão de produto"
  - test: "P-D: frequência/tom do card em uso real"
    expected: "Card desperta curiosidade sem induzir operação"
    why_human: "Qualidade percebida"
---

# Fase 51 — Seu dia na bolsa: Verificação

**Objetivo:** card determinístico no fim do pregão (setups vistos e não operados, ação do motor na carteira, fato raro ligado a conceito); streak = dias de decisão; portal mede exploração e overtrading.

**Testes executados pelo verifier:** `pytest tests/test_dia_na_bolsa_*.py` = 105 passed; `test_skill_ref.py` + `test_pregao*.py` = 84 passed; `web/tests/test_dia_na_bolsa_{card,push_prefs,stores,ui}.mjs` todos ok. Suíte completa não rodada (orquestrador: 3886 passed, 31 falhas pré-existentes de sandbox/certifi, 237/237 mjs, vite build ok).

## Critérios de sucesso

| # | Critério | Status | Evidência |
|---|----------|--------|-----------|
| 1 | Números só do motor; sem IA nem brapi no job | VERIFIED | `dia_na_bolsa.py:30-31` importa só benchmark/candle_cache/setups/yahoo etc. (sem `llm`, sem `brapi`); `dia_na_bolsa_regras.py:27-28` usa `indicators` + `_avaliar_entry`. Coleta: `_coletar` (l.320-360) cache-first (`candle_cache.peek_meta`) + `yahoo.get_history` com teto diário `_max_yahoo`; IBOV via `benchmark.serie_ibov` (benchmark.py:10 declara não consumir brapi). Sem barra de hoje = sem dado, nunca estimativa (l.329). Card montado por `_montar_card` (l.639) só com R/regras. |
| 2 | Stop e alvo com igual destaque; sem "perdeu/oportunidade/urgência"; guardião | VERIFIED | `tests/test_dia_na_bolsa_vocab.py:14` trava regex `perdeu\|perda\|prejuízo\|oportunidade\|imperdível\|última chance\|só hoje`; teste passa; templates em `skill_ref.DIA_NA_BOLSA`. Aspecto visual do mesmo destaque: coberto por `test_dia_na_bolsa_ui.mjs` (ok), conferência visual em NEEDS-HUMAN. |
| 3 | Feriado/fim de semana e dia vazio: sem push nem card novo | VERIFIED | `should_run`/`deve_fechar` (l.232-248) exigem `pregao.is_trading_day` (pregao.py:106, que cobre feriado via `is_holiday`:102). Dia sem família: `_montar_card` devolve `{"vazio": True}` (l.659-660), `_run` não chama push se vazio (l.729) e `payload_para` devolve `card: None` para vazio (l.~880). |
| 4 | Conta existente sem push antes do convite; conta nova com; teto 2/dia; register-token não muda consentimento | VERIFIED | `push.py:112` default `fechamento: False`; `quer_fechamento` fail-closed (l.171-178); `decidir_fechamento` única porta (l.187), chamada em `auth.py:111,371` (conta nova, True) e `main.py:5786` (convite); `set_prefs` descarta `fechamento`/`fechamentoDecidido` (push.py:145-148, fora de PREFS_BOOLS); `reservar_engajamento` (l.198) limite 2 e 1 por tipo/dia, usado pelo fechamento (dia_na_bolsa.py:789) e pelo Radar (radar_daily.py:432, fail-closed). Front: `fechamento` fora de `_pushPrefsLocais` (persistence.js:279,1295), teste passa. |
| 5 | Streak não conta abrir app, não zera, não quebra no fim de semana; data BRT | VERIFIED | App.jsx:10416-10423 `registrarDecisao` só aceita origem card/plano/stop, usa `hojeBRT()`, dedupe por dia, `putConfig({diasDecisao})` + `track("decision_day")`; App.jsx:10976 comentário e ausência de bump por abertura (grep `streak` só em comentário); união aditiva `uniaoDiasDecisao` (persistence.js:176, nunca remove) e no servidor `store.py:258-264`; faixa `faixaDots` marca dia sem pregão como `sem_pregao`, nunca `vazio` (diaNaBolsaLogica.js:62-68); janela 28 dias vem do servidor (`_ultimas_4_semanas`). |
| 6 | Portal: exploração, WAU e ops por usuário ativo lado a lado; RBAC no backend | VERIFIED | `analytics.engajamento_fechamento` (analytics.py:429-534) devolve `exploracao`, `wau7d`, `operacoesPorAtivo` e séries; rota `main.py:1124` com `Depends(require_permission("observabilidade.ver"))`; painel `web-admin/src/App.jsx:272-335` (KPIs WAU e Operações/usuário ativo no mesmo bloco, sem meta/alerta). Só agregados, sem user_id/ticker. |
| 7 | Paridade skill_ref↔copy.js e deviceStore↔serverStore | VERIFIED | Guardiões `test_dia_na_bolsa_vocab.py`/`test_dia_na_bolsa_card.mjs` e `test_dia_na_bolsa_stores.mjs` passam; `getDiaNaBolsa/registrarVistos/decidirFechamento` nos dois stores (persistence.js:281-283 e 1296-1309), `diasDecisao` nos dois (l.201, 567, 848). Suíte canônica verde segundo orquestrador. |

## Checagens adicionais

- Isolamento por usuário: todo registro por dia (`vistos`, `card`) usa `user_id=uid` (dia_na_bolsa.py:95,171,727); rotas `GET /api/dia-na-bolsa`, `/vistos`, `/convite` usam `Depends(require_user)` e `user["id"]` (main.py:5754-5787), nunca uid do corpo; preço do corpo de `/vistos` é ignorado (`registrar_vistos` nem o recebe).
- Gate `fechamento` fail-closed: confirmado (`push.quer_fechamento`, `except -> False`); o Radar permanece fail-open na pref `radar` mas fail-closed no teto.
- Hook do scheduler: `agent.py:1675-1678`, guardado por try/except; ENG-10 em `radar_daily.py:387-403` sem push novo.
- Marcadores de dívida (TBD/FIXME/XXX) nos arquivos da fase: nenhum.

## Observações (não bloqueiam)

- Emenda D-16: "decidir não entrar" fora da v1; `decision_day` cobre card, plano e stop (ROADMAP e REQUIREMENTS atualizados no commit 1edec3ad).
- Regra de amplitude exige 30 ativos; catálogo tem 20. O job usa o universo do arquivo do Radar (fallback `scanner.DEFAULT_UNIVERSE`), então depende de o universo ter >=30 ativos com 253 barras. Confirmar na calibração.
- Desvios conhecidos listados no 51-11-SUMMARY (texto do botão de retry, rodapé com `DISCLAIMERS.short`, rótulos de KPI pelo período do seletor).

## Resultado

Nenhum gap de código. Status `human_needed` por causa do checkpoint 51-11 ainda aberto (iPhone real, calibração com rede, P-C, P-D), todos já conhecidos.
