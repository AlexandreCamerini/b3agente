# Phase 51: Seu dia na bolsa - Pattern Map

**Mapeado:** 2026-11-17
**Arquivos analisados:** 24 (novos ou modificados)
**Analogos encontrados:** 21 / 24 (3 sem analogo direto, ver "No Analog Found")
**Fontes:** `51-CONTEXT.md` (D-01..D-20), `51-UI-SPEC.md` (contrato visual, premissas P-1..P-13), CLAUDE.md do repo.

---

## Divergencias entre CONTEXT/UI-SPEC e o codigo (ler antes de planejar)

Estas sao premissas que nao batem com o codigo atual. O planner precisa decidir cada uma.

1. **Default `fechamento: True` vaza para contas antigas (D-13).** `push.prefs_for` faz `{**PREFS_PADRAO, **p}` (`server/app/push.py:111`). Com `"fechamento": True` em `PREFS_PADRAO` (L101), toda conta sem a chave gravada ganha o push ligado, inclusive contas existentes. O comentario de `push.py` (L85-100) diz que "o default E a migracao" e isso so vale para defaults `True` que ja existiam. Para `fechamento`, o default precisa ser `False` no `PREFS_PADRAO` e a conta nova precisa de outro caminho (flag gravada na criacao ou `created_at` da conta comparado com o deploy).
2. **`_pushPrefsLocais` reenvia o conjunto inteiro a cada sync.** `web/src/persistence.js:722-735` monta `prefs` com `gatilho`, `radar`, `execucao`, `protecao` a partir de `config.notif` e envia em todo `registerPushToken`/`syncPushPrefs` (L1256, L1261). Se `fechamento` entrar nesse objeto como `n.fechamento === true` ou `!== false`, cada sync do aparelho sobrescreve o aceite/recusa do servidor com o default do aparelho. A decisao de consentimento precisa ser enviada SOMENTE quando o usuario decidiu (convite aceito ou recusado), e o aparelho nao pode mandar `false` por omissao.
3. **`pregao.is_holiday` nao cobre fim de semana (D-13).** `is_holiday` (`server/app/pregao.py:102`) testa so `feriados(ano)`. O gate correto e `pregao.is_trading_day` (L108), que combina `weekday() < 5` e `not is_holiday`. Os jobs irmaos (`snapshot_diario.should_run/deve_fechar`) ja usam `is_trading_day`.
4. **Regua de desfecho: a referencia `signal_ledger.py:66-83` e so armazenamento.** `signal_ledger.registrar_linhas` (L60-83) grava o que o replay produz; nao calcula nada. A regua de alvo/stop/expirou esta em dois lugares:
   - `server/app/analysis_outcomes.py:516-606` (`_avaliar_entry`, funcao pura com candles injetados; rotulos `stop`, `alvo`, `expirou_pos`, `expirou_neg`, `sem_gatilho`; prazo `HORIZON_PREGOES=10` em L24).
   - `server/app/signal_replay.py:97-153` (`avaliar`; rotulos `stop`, `alvo`, `expirou`, `sem_gatilho`; `r` ja calculado).
   Os rotulos NAO sao iguais (`expirou_pos`/`expirou_neg` x `expirou`). D-05 pede "reusar, nao criar terceira regua". Recomendacao: reusar `analysis_outcomes._avaliar_entry` (e pura e ja tem a ancoragem de gatilho) e mapear `expirou_pos|expirou_neg` para o texto unico "expirou" do card. Registrar essa decisao no plano.
5. **`PUSH_RADAR` nao tem espelho em `copy.js`.** `server/app/skill_ref.py:350-354` define `titulo`, `corpo_destaques`, `corpo_vazio`, mas `grep PUSH_RADAR web/src/copy.js` retorna vazio. O UI-SPEC pede paridade byte a byte para o push. Como o push nao e renderizado no front, a paridade util e um guardiao de vocabulario no lado Python (ver `server/tests/test_push_registro_evento.py:81,110` como exemplo de uso de `PUSH_RADAR`). Decidir: (a) so guardiao Python para o push, ou (b) espelhar tambem em `copy.js`.
6. **Acao "decidir nao entrar" nao existe (P-7).** Confirmado fora da v1. Nenhuma tarefa deve criar esse caminho.
7. **`radar_daily.get_stored` devolve `None` depois de um pregao fechar** (`radar_daily.py`, funcao `get_stored`, e `esta_vencida`). O "e se" de D-03 precisa de arquivo proprio por data (`radarDailyArquivo:<data>`), senao a leitura do dia anterior some. `store_result` (L84) hoje sobrescreve `radarDaily:<period>` (`_key`, L80).
8. **`radar_result_opened` so leva `{ticker}`** (App.jsx:8589). D-03 exige `setup` para o registro de "visto". Mudanca de payload (um campo a mais) no evento existente, com atualizacao do guardiao de `EVENTOS` se necessario.
9. **Analytics vive num banco separado** (`analytics.db`, `server/app/analytics.py:42-47`, `main.py:71` `_analytics_conn`). O WAU exato (`COUNT(DISTINCT user_id)` de `session_start`) tem de ler `analytics_events` desse banco, nao `_conn`. `analytics_daily` NAO guarda `user_id` (`analytics.py:81-100`), entao o WAU exato so vem do bruto (90 dias). Persistir a serie em `obs_daily_metrics` (ver Pattern Assignments).
10. **Guardiao de prefs de push e de semantica opt-out.** `web/tests/test_push_prefs_classes.mjs:45` (`CLASSES = ["radar","execucao","protecao"]`) exige `k: n.k !== false` nos dois stores (contagem `=== 2`). `fechamento` e opt-in: NAO entra nessa lista. Precisa de guardiao proprio.
11. **Streak usa UTC e `Date` local, nao BRT.** `App.jsx:10942` (`d.toISOString().slice(0,10)`) e o bug de D-17. Substituir por `hojeBRT()` de `web/src/evolucaoPosicao.js:38` (importado em App.jsx:21). O "ontem" tambem precisa ser calculado em BRT.

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `server/app/dia_na_bolsa.py` (novo, job + montagem do payload) | service / job | batch + request-response | `server/app/snapshot_diario.py` | exact (job diario idempotente) |
| `server/app/dia_na_bolsa_regras.py` (novo, opcional: regras puras de raridade) | utility (puro) | transform | `server/app/timing_watch.py` (`avaliar_usuario`, nucleo puro) | role-match |
| `server/app/radar_daily.py` (modificado: arquivo por data, linha do "e se" no push, `_quer_radar`) | service / job | event-driven | `server/app/radar_daily.py` (proprio) | exact |
| `server/app/push.py` (modificado: pref `fechamento`) | service | request-response | `server/app/push.py` (pref `gatilho`, L101-110) | exact |
| `server/app/agent.py` (modificado: hook no `scheduler_loop` + metrica WAU) | controller (laco) | event-driven | `agent.py` hook do snapshot (L1655-1656) | exact |
| `server/app/main.py` (modificado: `GET /api/dia-na-bolsa`, rota de convite, rota de decisao) | controller | request-response | `main.py` `POST /api/push/register-token` (L5703) e `GET /api/analytics/summary` (L1065) | exact |
| `server/app/analytics.py` (modificado: `METRICAS_CONHECIDAS` + `wau`) | service | batch | `analytics.py` `METRICAS_CONHECIDAS` (L233) | exact |
| `server/app/skill_ref.py` (modificado: templates `DIA_NA_BOLSA`, `PUSH_RADAR` com linha do "e se") | config / vocabulary | transform | `skill_ref.HISTORICO` (L368) + `historico_txt` (L699) | exact |
| `server/app/conceitos.py` (modificado: novos conceitos "amplitude/capitulacao", "maxima 52 semanas") | config / didatica | transform | `conceitos.CONCEITOS["gatilho"]` (L187+) e `SETORES` (L800) | role-match |
| `server/app/kb.py` (modificado: verbetes novos se optar por KB) | config / didatica | transform | `kb.py` verbete `estr-gap` (L615), `ind-atr` (L243) | exact |
| `web/src/copy.js` (modificado: espelho `DIA_NA_BOLSA`) | config / vocabulary | transform | `copy.js` `historico` (L593, L2064) + `historicoTxt` (L2992) | exact |
| `web/src/diaNaBolsa.jsx` (novo, componente do card + convite + faixa de streak) | component | request-response | `web/src/entendimento.jsx` (`SetorAlvo` L89, `ConceitoSheet` L182) e `App.jsx` `OperadorIACard` (L6088) | role-match |
| `web/src/App.jsx` (modificado: slot no `EvolucaoScreen`, streak L10938-10951, `track` novos, `setup` no `radar_result_opened`) | component (tela) | request-response | `EvolucaoScreen` (L2347), efeito do snapshot (L10921-10937) | exact |
| `web/src/persistence.js` (modificado: `getDiaNaBolsa`, `registrarVisto`, `fechamento` em `_pushPrefsLocais`, `decision_day` no config) | store | CRUD | `deviceStore.putWatchlist` (L977) / `serverStore.putWatchlist` (L227) e `_pushPrefsLocais` (L722) | exact |
| `web/src/analytics.js` (sem mudanca de API; uso de `track`) | utility | event-driven | `analytics.js` `track` | exact |
| `web/src/api.js` (modificado: `getDiaNaBolsa`, `diaNaBolsaConvite`) | service (cliente HTTP) | request-response | `api.js` `pushRegisterToken` / `analyticsSummary` | exact |
| `web/src/glossario.js` (modificado se houver `ANCORAS_KB` nova) | config | transform | `glossario.js:42` `ANCORAS_KB` | exact |
| `web-admin/src/App.jsx` (modificado: secao "Engajamento do fechamento" em `Comportamento`) | component (portal) | request-response | `Comportamento()` (L266) | exact |
| `web-admin/src/api.js` (modificado: `analyticsEngajamento`) | service | request-response | `api.js:55` `analyticsSummary` | exact |
| `server/tests/test_dia_na_bolsa*.py` (novo) | test | - | `server/tests/test_snapshot_diario.py` (J1-J8) e `server/tests/test_estrutura_card_vocab.py` | exact |
| `web/tests/test_dia_na_bolsa_espelho.mjs` (novo) | test (guardiao de espelho) | - | `web/tests/test_vocabulario_espelho.mjs` (DICTS L126) | exact |
| `web/tests/test_analytics_instrumentacao.mjs` (modificado: `EVENTOS` + 4 eventos novos) | test | - | o proprio arquivo (L22-25 `EVENTOS`) | exact |
| `web/tests/test_dia_na_bolsa_push_prefs.mjs` (novo, guardiao do `fechamento` opt-in) | test | - | `web/tests/test_push_prefs_classes.mjs` | role-match (semantica invertida) |
| `server/tests/test_radar_daily.py` (ampliar: linha do "e se") | test | - | o proprio arquivo | exact |

---

## Pattern Assignments

### `server/app/dia_na_bolsa.py` (service/job, batch + request-response)

**Analogo:** `server/app/snapshot_diario.py` (job diario idempotente por dia, janela de horario, kv de estado, nunca levanta).

**Imports e constantes** (`snapshot_diario.py`, cabecalho do modulo):
```python
from . import db, obslog, pregao, store
JOB_NOME = "snapshotDiario"
K_LAST_RUN = "snapshotDiarioLastRun"      # kv global: data do dia FECHADO
K_FEITAS = "snapshotDiarioFeitas"         # kv global: {"data", "escopos": [...]}
FIM = (17, 15)                            # = brapi_budget._ORCAMENTO_FIM
BRT = timezone(timedelta(hours=-3))
```
Usar: `JOB_NOME = "diaNaBolsa"`, `K_LAST_RUN = "diaNaBolsaLastRun"`, `K_FEITAS`/`K_TENTATIVA` no mesmo formato. Nao importar `agent` no modulo (regra de ciclo, comentada no proprio arquivo).

**Gate puro de janela** (`snapshot_diario.py`, `should_run` / `deve_fechar`):
```python
def should_run(now=None, last_date=None) -> bool:
    now = now or _agora()
    if not pregao.is_trading_day(now.date()):
        return False
    return _alvo(now) <= now < _fim(now) and last_date != now.date().isoformat()

def deve_fechar(now=None, last_date=None) -> bool:
    now = now or _agora()
    if not pregao.is_trading_day(now.date()):
        return False
    return now >= _fim(now) and last_date != now.date().isoformat()
```
Para o card: horario-alvo 17:05 ou 17:15 BRT (o card precisa do snapshot das 17:05 e do EOD em cache; ver D-12). Gate de "dia de pregao" = `pregao.is_trading_day`, NUNCA `is_holiday` sozinho.

**Entrega idempotente com `maybe_run` que nunca propaga** (`snapshot_diario.py`, `maybe_run`):
```python
async def maybe_run(conn, quotes_getter, now=None) -> Optional[dict]:
    try:
        now = now or _agora()
        if not enabled():
            return None
        last = last_run_date(conn)
        if deve_fechar(now, last):
            return _fechar_dia(conn, now)
        if not should_run(now, last):
            return None
        ...
        db.marcar_job(conn, JOB_NOME, LAST_RUN)
        if res["pendentesRestantes"] == 0 and res["erro"] is None:
            db.kv_set(conn, K_LAST_RUN, now.date().isoformat(), user_id=None)
        return res
    except Exception as e:  # noqa: BLE001 — nunca derruba o laco do agente
        LAST_RUN["erro"] = str(e)[:200]
        print(f"[snapshot-diario] rodada falhou: {type(e).__name__}")
        return None
```
Copiar o formato. `enabled()` e `B3_<JOB>_OFF`, como `radar_daily.enabled` (`not os.environ.get("B3_RADAR_DAILY_OFF")`).

**Por conta, sem brapi:** o job NAO chama o getter de cotacoes para o card. Usar `candle_cache.peek(symbol, "1d")` (`server/app/candle_cache.py:147`, "leitura do cache SEM rede") para candles do dia, e `benchmark.serie_ibov()` (`server/app/benchmark.py:39`, async, levanta `BenchmarkIndisponivel`) para o IBOV. Atr: `indicators.atr(highs, lows, closes, p=14)` (`server/app/indicators.py:155`).

**Persistencia do resultado por conta** (padrao `timing_watch`, kv por escopo com dia):
```python
db.kv_get(conn, "timingWatch", None, user_id=uid) or {"dia": "", "ultimo": {}, "avisados": []}
db.kv_set(conn, "timingWatch", tw_estado, user_id=scope)
```
(`server/app/agent.py:794` e `:893`). Para o card usar kv por escopo com `{"data": "AAAA-MM-DD", ...}` e `_zera_se_virou_o_dia`-like (`timing_watch.py`, `_zera_se_virou_o_dia`).

**Telemetria de job:** `db.marcar_job(conn, JOB_NOME, LAST_RUN)` (`db.py:481`) + `db.ler_job` (`db.py:499`), mesmo espelho que `status_snapshot` le (`agent.py`, funcao `status_snapshot`, linha nao conferida). `obslog.log("agent", "...", level="warn")` para perda.

**Escopo de dados:** iterar contas com `store.scopes_com_carteira(conn)` (`store.py:713`) para o card de carteira (familia 2), igual `snapshot_diario.run_tick`.

**Ordem da familia do payload por modo** (D-09): calcular `ordem` no servidor, `modo` vem de `push.prefs_for(conn, uid)["modo"]` ou da config do escopo. Front so renderiza na ordem recebida (UI-SPEC, "Corpo").

---

### `server/app/dia_na_bolsa_regras.py` (utility puro, transform) [opcional; decisao do planner: modulo proprio ou dentro de dia_na_bolsa.py]

**Analogo:** `server/app/timing_watch.py` `avaliar_usuario` (nucleo puro, sem I/O):
```python
def avaliar_usuario(radar_stored, intra_stored, universo, estado: dict,
                    hoje: str, agora=None) -> tuple:
    """NUCLEO PURO: decide o que notificar. Devolve `(tickers, estado_novo)`.
    Sem I/O, sem rede, sem kv — da para testar a regra inteira sem servidor."""
```
Regras de raridade (D-07/D-08) devem seguir o mesmo formato: funcoes puras, injetadas com series, retornam dict ou `None`. Limiar de mercado: percentil 95 de `|retorno diario|` em 12 meses sobre a serie de fechamento do IBOV (`serie_ibov` so tem `{date, close}`, sem ATR; D-08). Limiar de ativo: `movimento > 2 * ATR(14)`.

Regra de nulo: `null` para desconhecido, nunca `0` (CONTEXT, "Established Patterns"; ex.: `"use null (nunca 0.0"` em `server/tests`).

---

### `server/app/radar_daily.py` (modificado: arquivo por data + linha do "e se")

**Analogo:** o proprio arquivo.

**Chave e armazenamento atuais** (`radar_daily.py:80-92`):
```python
def _key(period: str) -> str:
    return "radarDaily:" + period

def store_result(conn, period: str, payload: dict, origem: str) -> dict:
    now = datetime.now(BRT)
    annotated = dict(payload)
    annotated["scanAt"] = now.isoformat()
    ...
    db.kv_set(conn, _key(period), annotated, user_id=None)
```
Adicionar ao lado uma chave `radarDailyArquivo:<AAAA-MM-DD>` com retencao maior que 90 dias (CONTEXT, Claude's Discretion). Nao mudar `radarDaily:<period>` (a aba Radar depende dele).

**Push: linha extra "Ontem: {TICKER} {chegaria ao alvo | teve o stop atingido}."** Ponto de encaixe: `push_body` (`radar_daily.py:218`) envelopa `skill_ref.PUSH_RADAR["corpo_destaques"]`. Acrescentar a linha so se o "e se" de ontem existir (sem placeholder). Nao criar push novo (D-14).

**Gate do push com preferencia, fail-open hoje:** `radar_daily.py:300-312` (dentro de `run_daily`):
```python
try:
    _quer_radar = push.prefs_for(conn, uid).get("radar", True)
except Exception:  # noqa: BLE001 — na duvida, avisa
    _quer_radar = True
if not _quer_radar:
    continue
```
Para `fechamento` (opt-in) o `except` deve ser FAIL-CLOSED (`False`). Nao copiar o `True` do `radar`.

**Teto de 2 engajamentos/dia:** o Radar 08:45 conta 1. O job de fechamento precisa consultar o mesmo contador. Nao existe contador de "push de engajamento" hoje (`MAX_POR_DIA = 6` em `timing_watch.py:56` e teto por usuario/ticker/dia no kv `timingWatch`, `avisados`). Criar contador kv diario, no mesmo formato de `timingWatch` (`dia` + lista).

---

### `server/app/push.py` (modificado: pref `fechamento`)

**Analogo:** pref `gatilho` (opt-in, nasce `False`), `push.py:101-110`.
```python
PREFS_PADRAO = {"gatilho": False, "radar": True, "execucao": True,
                "protecao": True, "modo": "estudo", "universo": [], "at": None}
PREFS_BOOLS = ("gatilho", "radar", "execucao", "protecao")

def prefs_for(conn, user_id: str) -> dict:
    p = db.kv_get(conn, "pushPrefs", None, user_id=user_id)
    if not isinstance(p, dict):
        return dict(PREFS_PADRAO)
    return {**PREFS_PADRAO, **p}
```
Mudanca: `"fechamento": False` em `PREFS_PADRAO`; `"fechamento"` em `PREFS_BOOLS` (a allowlist de `set_prefs`, L118, e o `register_token` em `main.py:5715` passam a aceitar a chave sem mais codigo). Como o default vale para conta sem registro, a conta nova precisa de gravacao explicita na criacao (ex.: `set_prefs(conn, uid, {"fechamento": True})` em `insert_user`/criacao de conta) ou de um marcador `fechamentoDecidido`. Decisao do planner (ver Divergencia 1).

**Sem `CLASSE_POR_TAG`:** o push de fechamento NAO passa por funil de evento (como o Radar, `push.py:156-166` comenta isso). Nao acrescentar em `CLASSE_POR_TAG`.

**Envio:** `push.send_to_user(conn, user_id, title, body, som=..., prioridade=..., extra=...)` (`push.py` L237): usar `prioridade="5"` e `som=False` para informativo (mesmo criterio de `send_to_user` docstring: "conteudo informativo"). `extra` com `{"kind": "fechamento"}` NAO leva ticker (regra de `radar_daily.py` L260-270: o `extra` com `t` ativaria o roteamento de ticker).

---

### `server/app/agent.py` (modificado: hook no `scheduler_loop` + metrica WAU)

**Analogo:** hook do snapshot (`agent.py:1655-1658`), `try/except` proprio, fora do kill-switch.
```python
try:
    from . import snapshot_diario  # import local: sem ciclo de import
    await snapshot_diario.maybe_run(conn, quotes_getter)
except Exception as e:  # noqa: BLE001 — o snapshot nunca derruba o laco
    print(f"[snapshot-diario] hook do scheduler falhou: {e}")
```
Inserir o hook `dia_na_bolsa.maybe_run(conn, quotes_getter)` DEPOIS do bloco do snapshot (L1655-1658) e ANTES do bloco de pregao aberto (`if not kill_switch_on() and in_market_hours():`, logo apos o hook), como pede CONTEXT "Integration Points".

**Metrica diaria WAU:** `_coletar_metricas_diarias` (`agent.py:96-120`) monta o dict; `_maybe_registrar_metricas_diarias` (L123-128) grava 1x/dia via `analytics.registrar_metricas_diarias`. Adicionar a chave `"wau_dia": ...` calculada a partir de `analytics_events` (`COUNT(DISTINCT user_id)` de `session_start` nos 7 dias), e registrar o nome em `METRICAS_CONHECIDAS` (ver `analytics.py`). Como `_coletar_metricas_diarias` nao recebe `analytics_conn`, o WAU deve ser calculado por funcao em `analytics.py` chamada com `analytics_conn` dentro de `_maybe_registrar_metricas_diarias` (que ja recebe `analytics_conn`).

---

### `server/app/analytics.py` (modificado: `METRICAS_CONHECIDAS` + funcao WAU)

**Analogo:** `analytics.py:233-237` e `registrar_metricas_diarias` (L240-251):
```python
METRICAS_CONHECIDAS = (
    "custo_ia_tokens_dia", "ia_analises_gerenciadas_dia",
    "brapi_requisicoes_janela3d", "brapi_erros_janela3d",
    "cache_candles_series", "push_automatico_falhas_dia", "radar_diario_duracao_s",
)
```
Adicionar `"wau_7d"` e (opcional) `"exploracao_card_dia"`. `serie_metrica` (L254) e `series_metricas` (L264) ja servem a serie para o portal, alem dos 90 dias. Para o WAU exato, usar a funcao no padrao de `funil` (L348): SQL sobre `analytics_events` com `day >= ?`.

Chaves proibidas: `_CHAVES_PROIBIDAS` (L35) e `_chave_proibida` (L140). Os 4 eventos novos devem usar apenas `modo`, `tipo`, `familia`, `origem`, `setup` (sem ticker de carteira, sem valor monetario, D-18/UI-SPEC "Interacao e analytics").

---

### `server/app/main.py` (modificado: rotas)

**Analogo de GET autenticado com escopo:** `main.py:1065` `analytics_summary`, e `POST /api/push/register-token` (L5703):
```python
@app.post("/api/push/register-token")
async def push_register(body: dict = Body(default={}), user: dict = Depends(require_user)):
    uid = user["id"]
    b = body or {}
    ...
    if any(k in b for k in ("prefs", "modo", "universo")):
        prefs = dict(b.get("prefs") or {})
        ...
        push.set_prefs(_conn, uid, prefs)
```
Para o convite (aceite/recusa), rota nova com o mesmo `Depends(require_user)` e `push.set_prefs` (patch parcial, L118). Nao reaproveitar `register-token` para isso sem cuidado (ele tambem aceita token vazio e grava prefs inteiras).

**Rota do card:** `GET /api/dia-na-bolsa` (CONTEXT, Claude's Discretion). Escopo: `user = Depends(require_user)`; `user_id=None` nao deve ser usado para dados de conta. Ver `current_scope()` (`main.py`, linha nao conferida) para o balde anonimo.

**Rota do portal:** `GET /api/analytics/engajamento` (nome a confirmar) com `Depends(require_permission("..."))`, no padrao de `analytics_ia_eficiencia` (`main.py:1086-1090`, `require_permission("operador_ia.ver")` + `analytics.get_cache` / `set_cache`). Permissao nova em `rbac.py` (GRUPOS) ou reuso de uma existente de analytics; checar `rbac.py`.

**Envelope de erro:** `HTTPException(status, "mensagem PT-BR")` (CLAUDE.md, "Error Handling").

---

### `server/app/skill_ref.py` (modificado: templates)

**Analogo:** `HISTORICO` (`skill_ref.py:368`) + `historico_txt` (L699). Modo resolvido por `modo if modo in HISTORICO else "educacional"`, chave ausente cai no estado de falha fechada.
```python
def historico_txt(modo: str, estado: str, janela: str = "", medido_ate: str = "") -> str:
    h = HISTORICO.get(modo if modo in HISTORICO else "educacional", HISTORICO["educacional"])
    frase = h.get(estado) or h["nunca_medido"]
    return frase.replace("{janela}", janela or "?").replace("{medidoAte}", medido_ate or "?")
```
Padrao para o novo: `DIA_NA_BOLSA = {"educacional": {familia: {regra: [variantes...]}}, "operador": {...}}` + `dia_na_bolsa_txt(modo, regra, hash_seed, **vals)`, onde a variante e `variantes[hash(uid+dia) % len]` (D-10: determinista). Placeholders como `{T}`, `{R}`, `{N}`, `{n}` (mesmo estilo de `PUSH_RADAR`, L350). Estudo: sem verbo de ordem.

Titulo fixo do push: `"Seu dia na bolsa"` (UI-SPEC). Nao usar emoji no card/push.

**`PUSH_RADAR`** (`skill_ref.py:350-354`): adicionar chave `corpo_ontem` (linha "Ontem: {TICKER} chegaria ao alvo / teve o stop atingido."). Ver Divergencia 5 sobre espelho.

---

### `web/src/copy.js` (modificado: espelho)

**Analogo:** bloco `historico` por modo (`copy.js:593` estudo, `2064` operador) e `historicoTxt` (L2992):
```js
export function historicoTxt(mode, estado, vals) {
  const h = copyFor(mode).historico;
  const frase = h[estado] || h.nunca_medido;
  return frase
    .replace("{janela}", (vals && vals.janela) || "?")
    .replace("{medidoAte}", (vals && vals.medidoAte) || "?");
}
```
`copyFor(mode)` (L2938): `COPY[mode === "operador" ? "operador" : "estudo"]`. Espelho com a MESMA chave e o MESMO texto byte a byte de `skill_ref.DIA_NA_BOLSA`. Novo export `diaNaBolsaTxt(mode, regra, seed, vals)` com a mesma forma. O front nunca compoe frase: so chama o espelho (CLAUDE.md, "Paridade").

---

### `server/app/conceitos.py` e `server/app/kb.py` (modificados: conceitos novos)

**Analogo de conceito:** `conceitos.CONCEITOS["gatilho"]` (L187+), com `titulo` por modo (`educacional`/`operador`), `campos`, `naoAcontece`, `oQueE`, `oQueAcontece`. Conceitos novos ("amplitude/capitulacao", "maxima/minima de 52 semanas") seguem esse formato. Setor: `conceitos.SETORES` (L800). Redacao pela skill `didatica-boris` (CONTEXT, "Claude's Discretion").

**Analogo de verbete KB** (ja existe, reusar por id): `kb.py:243` `ind-atr`, `kb.py:449` `ind-volatilidade-historica`, `kb.py:615` `estr-gap`. Abrir via `A.abrirVerbeteKb(vid)` (App.jsx:10645), que resolve do catalogo ja em memoria (sincrono). Para o Operador, o mesmo conceito com texto de mesa.

Guardiao de espelho KB: `server/tests/test_kb_espelho.py` e `web/tests/test_kb_ancoras.mjs` (ver "Testing").

---

### `web/src/diaNaBolsa.jsx` (novo componente, role component)

**Analogo de componente de card com estados:** `OperadorIACard` (`App.jsx:6088`) para o padrao de chamada de API e estados; `SetorAlvo` (`entendimento.jsx:89`) para toque em conceito; `ConceitoSheet` (`entendimento.jsx:182`) para a folha.

**Padrao de exportacao de componentes didaticos** (`entendimento.jsx`):
```jsx
export function SetorAlvo({ setorId, dados, rotulo, A, didatica, ativo = true, style, children }) {
  const cid = (didatica && didatica.ligada && didatica.setores) ? didatica.setores[setorId] : null;
  if (!cid || !A || !ativo) return <div style={style}>{children}</div>;
  const abrir = (origem) => A.abrirSetor(setorId, cid, dados, origem);
  ...
}
```
Gate didatico do link (App.jsx, `EvolucaoScreen`, ~L2404-2407):
```jsx
{ctx.didatica && ctx.didatica.ligada && verbeteDoCatalogo(ctx.kbCatalogo, ANCORAS_KB.evolucao) && (
  <button type="button" onClick={() => A.abrirVerbeteKb(ANCORAS_KB.evolucao)} ...>{cp.saibaMais}</button>
)}
```
Usar o mesmo portao para "Ver {conceito} →".

**Superficie do card:** `const card = { background: T.bgCard, border: \`1px solid ${T.borderSubtle}\`, borderRadius: "12px" };` (`App.jsx:395`) mais `borderLeft: 3px solid T.accent`. Tokens somente via `T.*` (UI-SPEC "Design System"). Estilo inline, sem lib.

**Data:** `hojeBRT()` de `web/src/evolucaoPosicao.js:38` (ja importado no App.jsx L21). Carimbo "Fechamento de {DD/MM}" usa `dataBRT` / funcao de formatacao existente em `evolucaoPosicao.js` (linhas ~25-37, parse `DD/MM/AAAA`).

**Numeros:** `Intl.NumberFormat("pt-BR")` (ja usado no app), `null` -> `—`.

**Estados completos:** seguir a tabela UI-SPEC "Estados completos" (carregando/erro/dado atrasado/sem card=0px). Sem card = `return null` (nenhum placeholder).

---

### `web/src/App.jsx` (modificado: slot, streak, eventos)

**Slot no Acompanhar:** `EvolucaoScreen` (`App.jsx:2347`). Ponto exato: depois do bloco do h1 e do `MarketStatusBadge`/`cp.resumoDia` (L2395-2411) e ANTES de `<OperadorIACard ctx={ctx} />` (L2412). Renderizar `<DiaNaBolsaCard ctx={ctx} />` nesse ponto.

**Streak, estado atual** (`App.jsx:10938-10951`) e o bug D-17:
```jsx
const streakRanRef = useRef(false);
useEffect(() => {
  if (!data || !data.config || streakRanRef.current) return;
  streakRanRef.current = true;
  const ymd = (d) => d.toISOString().slice(0, 10);   // UTC: D-17
  const st = data.config.streak || { days: 0, last: "" };
  const today = ymd(new Date());
  if (st.last === today) return;
  const y = new Date(); y.setDate(y.getDate() - 1);
  const next = st.last === ymd(y) ? (st.days || 0) + 1 : 1;
  const ns = { days: next, last: today };
  setData((d) => (d ? { ...d, config: { ...d.config, streak: ns } } : d));
  store.putConfig({ streak: ns }).catch(() => { /* silencioso */ });
}, [data]);
```
Mudanca: o efeito deixa de contar abertura. O streak passa a ser "dias de decisao" gravado por `decision_day` (um por dia BRT). Usar `hojeBRT()` (`evolucaoPosicao.js:38`) em vez de `toISOString`. Persistir por `store.putConfig` (L210 `serverStore`, L799 `deviceStore`) para paridade.

**Eventos existentes:**
- `radar_result_opened` (L8589): `track("radar_result_opened", { ticker: t });`. D-03 exige `setup`. Acrescentar o campo; ver Divergencia 8.
- `session_start` (L9906, L9927, L9935): usado pelo WAU. Nao mudar.
- `notification_tapped` (L9962): `track("notification_tapped", { ticker: t, kind })`. O toque do push de fechamento abre o Acompanhar (UI-SPEC); reusar o evento com `kind: "fechamento"`.

**Gancho de `decision_day` (card, plano, stop):**
- `card`: primeiro toque no card do dia (mesma origem de `daily_card_opened`).
- `plano`: pedir abertura do plano a partir do card (`daily_card_explored` tipo plano) ou revisar plano.
- `stop`: ajuste de stop/alvo. Ponto existente: `setStop: async (t, v) => { ... store.putPosition(t, { stop: v }) ... }` (`App.jsx:10387`), e o popup de `stopAlvoFor` (L9732-9733, L10352). Track com `origem: "stop"` apos sucesso.
- "Decidir nao entrar": FORA da v1 (P-7).

**Tipos de `track`:** `track(evento, props)` de `web/src/analytics.js` (sem alteracao de API). Todos os eventos novos levam `modo` (D-18).

---

### `web/src/persistence.js` (modificado: paridade dos dois stores)

**Analogo de metodo novo nos dois stores:** `putWatchlist` (`serverStore` L227 em `sync.mutate`; `deviceStore` L977 async). Regra da paridade (CLAUDE.md, "Paridade obrigatoria"): metodo ou campo novo entra nos DOIS, com o mesmo contrato. Testado em `web/tests/test_api_parity.mjs`.

**Fonte de verdade por plataforma:** `persistence.js:6-28` (comentario) e `export const store = isNative ? deviceStore() : serverStore();` (L1171).

**Preferencia `fechamento`:** estender `_pushPrefsLocais` (L722-735) com o campo SOMENTE quando o usuario decidiu no aparelho, como D-13 + Divergencia 2. Padrao de `serverStore.syncPushPrefs` (L1261) e `registerPushToken` (L1256). Nao usar `n.fechamento !== false` (isso e opt-out e liga para todos).

**Registro de visto (D-03):** `registrarVisto(ticker, setup)` nos dois stores. `serverStore` chama API; `deviceStore` grava local e sincroniza no proximo `api.*` (padrao de `putConfig` com `optConfig`, L210). Watchlist no iOS: `deviceStore.putWatchlist` (L977) so grava local (CONTEXT). Decidir com o planner: `pushPrefs.universo` (`push.py` `set_prefs` L118-136, validade 7 dias via `universo_valido` (numero da linha nao conferido)) OU o front mandar a lista no registro de visto.

---

### `web/src/api.js` (modificado: clientes HTTP)

**Analogo:** `api.js:55` `analyticsSummary` e `pushRegisterToken` (padrao `req("GET"|"POST", path, body)`):
```js
analyticsSummary: (dias) => req("GET", "/api/analytics/summary" + (dias ? "?dias=" + encodeURIComponent(dias) : "")),
```
Novos: `diaNaBolsa: () => req("GET", "/api/dia-na-bolsa")`, `diaNaBolsaConvite: (aceite) => req("POST", "/api/dia-na-bolsa/convite", { aceite })`. Respostas lidas como texto (`readBody`), nunca `.json()` direto (CLAUDE.md, "Error Handling").

---

### `web-admin/src/App.jsx` (modificado: painel do portal)

**Analogo:** `Comportamento()` (`web-admin/src/App.jsx:266`):
```jsx
function Comportamento() {
  const [dias, setDias] = useState(30);
  const { loading, error, data, reload } = useFetch(() => api.analyticsSummary(dias), [dias]);
  ...
  return (
    <>
      {data && (
        <ResumoExecutivo>
          <Kpi label="EVENTOS NO PERÍODO" value={...} />
          ...
        </ResumoExecutivo>
      )}
      <Card title="Adoção por feature" right={<select value={dias} ...>...</select>}>
        <Estado loading={loading} error={error} empty={...}>
          {data && (...).map((r) => <EventoComSerie key={r.event} label={r.event} value={...} serie={serieMap[r.event]} />)}
        </Estado>
      </Card>
```
Componentes existentes (todos em `web-admin/src/App.jsx`): `Kv` (L23), `Card` (L37), `Estado` (L51), `ResumoExecutivo` (L81), `EventoComSerie` (L256), `Kpi` (L366). Tokens `T` (L14-19): `card`, `border`, `text`, `muted`, `faint`, `accent` (dourado), `positive`/`negative` (NAO usar nesta fase, UI-SPEC "Portal").

Regras do painel (UI-SPEC "Portal"): sem meta, sem linha de 30%, sem `tone` nos KPIs do engajamento, sem alerta. Grafico de exploracao e de `trade_simulated` com a MESMA cor (`T.muted`), mesma altura e largura. Denominador sempre visivel (`usuarios` vs total).

**Modo do funil como guia:** o comentario do proprio `Comportamento` (L305-307) explica por que o funil NAO tem serie de tendencia: depende de ordem por usuario, so existe no bruto. Usar a mesma justificativa para WAU diario (ver `analytics.py` `funil` L348-352).

`web-admin/src/api.js:55` (`analyticsSummary`): novo `analyticsEngajamento(dias)`.

---

### Testes

**Guardiao de espelho de vocabulario (copiar):** `web/tests/test_vocabulario_espelho.mjs`. Le o `skill_ref.py` como TEXTO (sem import Python), recorta o bloco `NOME = {...}` com `blocoDoDict`, separa modo com `blocoDoModo`, extrai pares `"chave": "valor"` com `paresDoModo`, e compara byte a byte com `COPY[modo]`. Lista `DICTS` em L126; `MODO_JS = { educacional: "estudo", operador: "operador" }`. Adicionar `"DIA_NA_BOLSA"` na lista e `CHAVE_JS` correspondente.
```js
const DICTS = ["HISTORICO", "HISTORICO_ROTULO", ..., "MARCOS_PLANO"];
const MODO_JS = { educacional: "estudo", operador: "operador" };
```
Regra do guardiao (CLAUDE.md, "Guardioes de teste nao se apagam"): NAO apagar; so ampliar.

**Guardiao de vocabulario proibido (novo, Python):** o padrao de `server/tests/test_estrutura_card_vocab.py` (chaves esperadas + funcao por chave) e `test_anatomia_perna.py:288` (lista de `proibido in fonte`). Criar `server/tests/test_dia_na_bolsa_vocab.py` com a lista do UI-SPEC "Vocabulario" (`perdeu`, `perdeste`, `oportunidade`, `imperdivel`, `ultima chance`, `so hoje`, `agora!`, `entre agora`, `garantid*`, `lucro certo`, `nao perca`, `fique rico`, `rapido`, contagem regressiva) aplicada a TODAS as variantes de `DIA_NA_BOLSA` e `PUSH_RADAR` (inclusive `corpo_ontem`). Regex para `garantid\w*` e superlativo.

**Guardiao do `EVENTOS` de analytics:** `web/tests/test_analytics_instrumentacao.mjs` L22-25:
```js
const EVENTOS = [
  "onboarding_step_completed", "portfolio_view", "radar_scan_run", "radar_result_opened",
  ...
  "notification_tapped", "session_start", "session_end",
];
for (const ev of EVENTOS) {
  ok(`evento "${ev}" tem track() no codigo`, new RegExp(`track\\("${ev}"`).test(src));
}
```
Adicionar `daily_card_shown`, `daily_card_opened`, `daily_card_explored`, `decision_day` (D-18). Cada um precisa de `track("...` real em `App.jsx` ou `diaNaBolsa.jsx`: se o `src` lido for so `App.jsx`, os eventos devem ficar em `App.jsx`, ou o guardiao deve ler os dois arquivos.

**Guardiao de prefs de push (NAO copiar a lista CLASSES):** `web/tests/test_push_prefs_classes.mjs:45-60` usa `k: n.k !== false` em dois stores com contagem `=== 2`. `fechamento` tem semantica invertida (opt-in). Novo guardiao `web/tests/test_dia_na_bolsa_push_prefs.mjs`: (a) `PREFS_PADRAO["fechamento"] is False` em `push.py`; (b) `fechamento` ausente de `_pushPrefsLocais` quando nao decidido; (c) nenhuma ocorrencia de `fechamento: n.fechamento !== false`.

**Job (copiar):** `server/tests/test_snapshot_diario.py`: casos J1 (sabado nao roda), J2 (feriado em dia util nao roda), J3 (antes do horario nao roda), J4 (lastRun do dia no kv nao roda), J5 (apos o fim fecha sem chamar getter), J6 (um getter por tick), J7 (ponto com origem/fonte/hora), J8 (ativo sem cotacao nao grava). Relogio entra por `now`; banco via `db.connect(tmpfile)` (`_fresh_db`). Reutilizar o formato para `dia_na_bolsa`: sabado, feriado, fim da janela, idempotencia por dia, sem card quando nao ha regra.

**Radar push (ampliar):** `server/tests/test_radar_daily.py` (ja existe) para a linha "Ontem: ...".

**Mesa do push do Radar:** `server/tests/test_push_registro_evento.py:81,110` para o padrao de guardiao de `PUSH_RADAR`.

---

## Shared Patterns

### Job diario idempotente (nunca levanta, gate por dia util, kv de ultimo dia)
**Fonte:** `server/app/snapshot_diario.py` (`maybe_run`, `should_run`, `deve_fechar`, `last_run_date`); mesmo formato em `radar_daily.py` (`maybe_run`, L~320-330) e `analysis_outcomes.py:657` (`maybe_run`, `last_run_date` L649).
**Aplicar a:** `dia_na_bolsa.py`, mudancas em `radar_daily.py`.
```python
async def maybe_run(conn, ...):
    try:
        if not enabled(): return None
        if not should_run(last_date=last_run_date(conn)): return None
        ...
    except Exception as e:  # noqa: BLE001 — nunca derruba o laco do agente
        LAST_X["erro"] = str(e)[:200]
        print(f"[...] falhou: {type(e).__name__}")
        return None
```
Hook em `agent.py` com `try/except` PROPRIO (L1655-1658).

### Fuso e data de pregao
**Fonte:** `pregao.is_trading_day` (`pregao.py:108`), `BRT = timezone(timedelta(hours=-3))`, `hojeBRT()` (`web/src/evolucaoPosicao.js:38`).
**Aplicar a:** todo gate de job, streak (D-17), carimbo de data do card.
Nunca `toISOString().slice(0,10)` (App.jsx:10942) nem `new Date()` para data de negocio.

### Preferencia de push + envio
**Fonte:** `server/app/push.py` (`PREFS_PADRAO` L101, `prefs_for` L111, `set_prefs` L118, `send_to_user`).
**Aplicar a:** `fechamento`. Gate direto no job (como o Radar, `radar_daily.py` ~L300-312), nunca `CLASSE_POR_TAG`. Fail-closed para pref opt-in.

### Vocabulario por modo: backend canonico, front espelha, guardiao
**Fonte:** `skill_ref.py` (`HISTORICO` L368, `PUSH_RADAR` L350) e `web/src/copy.js` (`COPY.estudo`/`COPY.operador`, `historicoTxt` L2992); guardiao `web/tests/test_vocabulario_espelho.mjs`.
**Aplicar a:** card (Familias 1-3), push, linha do Radar, convite (texto igual nos dois modos, P-10).
O front NUNCA compoe frase; so chama `diaNaBolsaTxt(mode, regra, seed, vals)`.

### Paridade `deviceStore` x `serverStore`
**Fonte:** `web/src/persistence.js` (L172 `serverStore`, L461 `deviceStore`, L1171 `export const store`); `web/tests/test_api_parity.mjs`.
**Aplicar a:** `registrarVisto`, `getDiaNaBolsa`, `decision_day` (streak no config), `fechamento` em prefs.

### Relogio injetado para teste
**Fonte:** `snapshot_diario._agora()` (patchavel), `now=` em `should_run`/`deve_fechar`/`ultimo_fechamento` (`radar_daily.py`).
**Aplicar a:** todo gate novo.

### Eventos de analytics: sem PII, com `modo`
**Fonte:** `web/src/analytics.js` `track()`; `server/app/analytics.py:35` (`_CHAVES_PROIBIDAS`), L140 (`_chave_proibida`). Ingest sem whitelist (`analytics.py` L148).
**Aplicar a:** `daily_card_shown|opened|explored`, `decision_day`. Payload so com `modo`, `tipo`, `familia`, `origem`, `setup`. Sem ticker de carteira nem valor monetario em `daily_card_explored` (UI-SPEC).

### Null, nunca zero
**Fonte:** CONTEXT "Established Patterns"; `test_m3_format_pede_null_nunca_zero` (citado em CLAUDE.md, "Return Values").
**Aplicar a:** IBOV indisponivel (`—`), preco de gatilho/stop/alvo ausente (campo some), R ausente.

### Erro de fonte: nao inventar
**Fonte:** `benchmark.serie_ibov` levanta `BenchmarkIndisponivel` (`benchmark.py:39-45`); job de snapshot pula conta sem cotacao (`snapshot_diario.py`, `puladasSemCotacao`).
**Aplicar a:** IBOV e cotacoes do card. "IBOV indisponivel hoje" (UI-SPEC), nunca 0%.

### Orcamento brapi
**Fonte:** `server/app/brapi_budget.py:90` (`_ORCAMENTO_FIM = 17*60+15`). O job roda <= 17:15 e NAO chama brapi; usa `candle_cache.peek` (`candle_cache.py:147`).
**Aplicar a:** `dia_na_bolsa.py`.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| Regra de raridade por percentil 95 de `|retorno diario|` do IBOV em 12 meses (dentro de `dia_na_bolsa_regras.py`) | utility | transform | Nao existe percentil/rolling sobre serie de retorno no codigo. `indicators.py` tem `atr` (L155) e medias, nao percentil. Usar biblioteca stdlib (`statistics.quantiles`) e testar com serie sintetica. |
| Contador de "push de engajamento por dia" (teto de 2) | service | event-driven | Nao existe teto global de engajamento. O analogo mais proximo e o `timingWatch` (`MAX_POR_DIA`, `timing_watch.py:56`), mas e por usuario+ticker. Criar kv diario proprio. |
| Arquivo diario do Radar com retencao (`radarDailyArquivo:<data>`) | store | CRUD | O Radar hoje e sobrescrito (`radar_daily.py:80-92`). Nao ha arquivo por data. Criar a chave e a poda de retencao (nao existe poda para `radarDaily*`). |

---

## Metadata

**Analog search scope:** `server/app/` (snapshot_diario, radar_daily, push, timing_watch, signal_ledger, analysis_outcomes, signal_replay, analytics, agent, main, skill_ref, conceitos, kb, pregao, candle_cache, benchmark, indicators, db, store); `server/tests/` (test_snapshot_diario, test_estrutura_card_vocab, test_analytics, test_push_prefs_classes, test_radar_daily, test_timing_watch); `web/src/` (App.jsx por grep e leitura parcial, copy.js, persistence.js, entendimento.jsx, evolucaoPosicao.js, analytics.js, disclaimers.js); `web/tests/` (test_vocabulario_espelho, test_analytics_instrumentacao, test_push_prefs_classes, test_snapshot_diario_front); `web-admin/src/` (App.jsx L14-22 tokens, L37-81 e L256-366 componentes, L266 `Comportamento`; api.js L55).
**Arquivos lidos integralmente:** `snapshot_diario.py`, `radar_daily.py`, `push.py` (trechos 90-315), `timing_watch.py` (trechos), `signal_ledger.py` (1-110), `analysis_outcomes.py` (90-165, 505-660), `analytics.py` (25-60, 81-100, 183-270, 300-365), `persistence.js` (718-735, 250-262).
**Arquivos parciais (grep + leitura por faixa):** `App.jsx` (leitura pontual: 2347-2362, 2395-2412, 10928-10952, grep de `track`, `streak`, `setStop`, `EvolucaoScreen`, `OperadorIACard`), `copy.js` (grep + 2938-3002), `skill_ref.py` (grep + 340-360, 699-705), `web-admin/src/App.jsx` (14-22, 262-304).
**Nao lido (fora do escopo deste mapeamento, ou so por grep):** `kb.py` (apenas ancoras por grep), `conceitos.py` (apenas estrutura de `gatilho`, L187-215), `rbac.py`, `candle_cache.py` alem de `peek`, `benchmark.py` alem de `serie_ibov`.
**Arquivos nao verificados que o planner deve checar antes de codar:** `web/src/glossario.js` (`ANCORAS_KB`, L42); `server/app/rbac.py` (permissoes de analytics); `server/tests/test_radar_daily.py` (guardioes de `push_body`); `web/tests/test_api_parity.mjs`.
**Analise de tamanho:** `App.jsx` (~11600 linhas) e `persistence.js` (2466 linhas) foram lidos apenas por faixa; nenhum arquivo de mais de 2000 linhas foi lido por inteiro.
**Pattern extraction date:** 2026-11-17
