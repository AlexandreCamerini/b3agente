"""qa/42 (FinOps) — guardiões dos fixes de custo/RAM.

Contexto: o custo do projeto hoje é SÓ o container Railway (B3_MANAGED_LLM_KEY
ausente => 100% BYOK => custo de LLM do dono = zero). Estes testes travam:
  • _SCAN_CACHE com TETO e chave normalizada (era OOM dirigido pelo cliente num
    endpoint sem auth — derrubar o container derruba o Operador IA);
  • cota da IA gerenciada com `custo` (o /api/scan/deep checava 1 e gastava N);
  • teto GLOBAL de gasto (não existia: gasto = nº usuários × cota, sem topo);
  • candlePeriod preservado na config gerenciada (quem paga mandava o prompt
    mais caro: sempre 252 candles);
  • telemetria de tokens (nenhum caller lia `usage` — custo imensurável);
  • gates diários PERSISTIDOS (deploy re-executava o job).
"""
import os
import pathlib
import tempfile

from app import db, llm, managed, metering, scanner


def _fresh_db():
    d = tempfile.mkdtemp(prefix="b3_qa42_")
    return db.connect(os.path.join(d, "b3_agente.db"))


# --- _SCAN_CACHE: teto + chave normalizada (RAM do container) ---------------

def test_scan_cache_key_ignora_ordem_dos_tickers():
    """`?tickers=A,B` e `?tickers=B,A` pedem a MESMA varredura: UMA entrada.
    Antes eram duas — N tickers davam até N! chaves de ~150 KB, sem teto, num
    endpoint sem auth. Ordenar é correto porque run_scan ordena o `results`
    por confluência (o payload não depende da ordem de entrada)."""
    assert scanner._cache_key("1y", ["PETR4", "VALE3"]) == scanner._cache_key("1y", ["VALE3", "PETR4"])
    # período continua discriminando
    assert scanner._cache_key("1mo", ["PETR4"]) != scanner._cache_key("1y", ["PETR4"])


def test_scan_cache_tem_teto():
    """O dict não pode crescer sem limite: era o vetor de OOM."""
    scanner.reset()
    for i in range(scanner.SCAN_CACHE_MAX * 3):
        scanner._cache_put("1y|T%d" % i, 1000.0 + i, {"results": []})
    assert len(scanner._SCAN_CACHE) <= scanner.SCAN_CACHE_MAX, "cache do scan sem teto = OOM"
    scanner.reset()


def test_scan_cache_evicta_a_mais_antiga_e_mantem_a_recente():
    scanner.reset()
    for i in range(scanner.SCAN_CACHE_MAX + 5):
        scanner._cache_put("k%d" % i, 1000.0 + i, {"results": [], "i": i})
    assert "k0" not in scanner._SCAN_CACHE, "a mais antiga deveria ter saído"
    ultima = "k%d" % (scanner.SCAN_CACHE_MAX + 4)
    assert ultima in scanner._SCAN_CACHE, "a mais recente tem que sobreviver"
    scanner.reset()


def test_scan_cache_put_esta_ligado_no_run_scan():
    """Ancoragem: run_scan tem que usar as duas funções (senão o teto não vale)."""
    src = (pathlib.Path(__file__).resolve().parents[1] / "app" / "scanner.py").read_text(encoding="utf-8")
    assert src.count("_cache_put(ck, now_m, payload)") == 1, "run_scan não guarda via _cache_put"
    assert src.count("ck = _cache_key(p, uni)") == 1, "run_scan não monta a chave via _cache_key"
    assert src.count('ck = p + "|" + ",".join(uni)') == 0, "sobrou a chave antiga (sensível à ordem)"


# --- cota da IA gerenciada: `custo` fecha o furo do /api/scan/deep ----------

def test_cota_reserva_o_custo_do_request():
    """O deep dispara até 10 análises num request. Com count=19 e quota=20 o
    check passava (19 < 20) e o consume era chamado 10x → terminava em 29."""
    conn = _fresh_db()
    uid = "u1"
    for _ in range(19):
        metering.consume(conn, uid)
    ok, reason = metering.check(conn, uid, quota=20, rate_per_min=100, custo=10)
    assert ok is False, "cota tem que reservar o custo do request inteiro"
    assert "restante" in reason and "10" in reason, "a mensagem deve dizer o custo e o que resta"
    # e o mesmo usuário ainda consegue UMA análise (resta 1)
    ok, _ = metering.check(conn, uid, quota=20, rate_per_min=100, custo=1)
    assert ok is True, "custo=1 ainda cabe em 19/20"


def test_custo_default_preserva_comportamento_antigo():
    """custo=1 (default) => `count + 1 > quota` ≡ `count >= quota`: idêntico ao
    de antes. O fix não pode mudar o caminho de 1 análise."""
    conn = _fresh_db()
    uid = "u1"
    for _ in range(3):
        ok, _ = metering.check(conn, uid, quota=3, rate_per_min=100)
        assert ok
        metering.consume(conn, uid)
    ok, reason = metering.check(conn, uid, quota=3, rate_per_min=100)
    assert ok is False and "limite diário" in reason


def test_rate_limit_conta_request_nao_analises():
    """O rate limit existe para impedir MARTELAR: 1 slot por request. Reservar
    `custo` slots faria todo deep (10) estourar um teto de 6/min e o produto
    pararia — o custo pertence à COTA, não ao rate."""
    conn = _fresh_db()
    ok, _ = metering.check(conn, "u1", quota=None, rate_per_min=6, custo=10)
    assert ok is True, "custo alto não pode ser barrado pelo rate limit"


# --- teto GLOBAL de gasto ---------------------------------------------------

def test_teto_global_bloqueia_somando_todos_os_usuarios():
    """Não existia contador agregado: o gasto era (nº usuários) × cota, sem
    topo. Usuários DIFERENTES agora somam no mesmo teto."""
    conn = _fresh_db()
    for uid in ("u1", "u2", "u3"):
        metering.consume(conn, uid)
    assert metering.global_snapshot(conn, 10)["used"] == 3, "o global soma todos os escopos"
    ok, reason = metering.check(conn, "u4", quota=100, rate_per_min=100, cap_global=3)
    assert ok is False and "limite de uso de hoje" in reason
    # a cota individual de u4 está zerada, mas o teto global manda
    ok, _ = metering.check(conn, "u4", quota=100, rate_per_min=100, cap_global=None)
    assert ok is True, "cap_global=None (default) = ilimitado = comportamento anterior"


def test_teto_global_default_e_ilimitado():
    """Aditivo: sem a env, nada muda em produção."""
    os.environ.pop("B3_MANAGED_GLOBAL_DAILY_CAP", None)
    assert managed.global_daily_cap() is None
    os.environ["B3_MANAGED_GLOBAL_DAILY_CAP"] = "500"
    assert managed.global_daily_cap() == 500
    os.environ["B3_MANAGED_GLOBAL_DAILY_CAP"] = "lixo"     # inválido => ilimitado, nunca 0
    assert managed.global_daily_cap() is None
    os.environ["B3_MANAGED_GLOBAL_DAILY_CAP"] = "0"        # 0 não pode significar "bloqueie tudo"
    assert managed.global_daily_cap() is None
    os.environ.pop("B3_MANAGED_GLOBAL_DAILY_CAP", None)


# --- candlePeriod na config gerenciada (7x tokens na chave do servidor) -----

def test_config_gerenciada_preserva_candle_period():
    """`_ai_apply_managed` substituía a config e o candlePeriod sumia →
    normalize_period(None) → default '1y' = 252 candles, mesmo com '1mo'
    escolhido: ~7x mais input JUSTO no caminho que gasta a chave do servidor."""
    src = (pathlib.Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")
    assert src.count('"candlePeriod": (config or {}).get("candlePeriod")') == 1, \
        "a config gerenciada tem que carregar o candlePeriod do usuário"
    assert src.count("_ai_apply_managed(scope, config, custo=n)") == 1, \
        "/api/scan/deep tem que reservar custo=n (1 chamada de LLM por ticker do top-N)"


# --- telemetria de tokens ---------------------------------------------------

def test_record_usage_normaliza_os_tres_provedores():
    """Nenhum caller lia `usage` — era impossível medir custo real."""
    llm.USAGE.update(day=None, calls=0, inputTokens=0, outputTokens=0, porModelo={})
    llm.record_usage({"model": "claude-haiku-4-5"}, {"usage": {"input_tokens": 100, "output_tokens": 20}})
    llm.record_usage({"model": "gpt-4o-mini"}, {"usage": {"prompt_tokens": 50, "completion_tokens": 10}})
    llm.record_usage({"model": "gemini"}, {"usageMetadata": {"promptTokenCount": 7, "candidatesTokenCount": 3}})
    snap = llm.usage_snapshot()
    assert snap["calls"] == 3
    assert snap["inputTokens"] == 157 and snap["outputTokens"] == 33
    assert snap["porModelo"]["claude-haiku-4-5"]["inputTokens"] == 100
    assert snap["porModelo"]["gpt-4o-mini"]["outputTokens"] == 10


def test_record_usage_nunca_quebra_a_analise():
    """Best-effort TOTAL: provedor sem `usage`, corpo lixo ou None → ignora."""
    llm.USAGE.update(day=None, calls=0, inputTokens=0, outputTokens=0, porModelo={})
    for lixo in (None, {}, {"usage": "nao-e-dict"}, {"usage": {"input_tokens": "x"}}, {"choices": []}):
        llm.record_usage({"model": "m"}, lixo)      # não pode levantar
    assert llm.usage_snapshot()["calls"] == 0, "corpo sem usage não conta chamada"


def test_record_usage_esta_ligado_nos_tres_calls():
    """Ancoragem: sem a chamada nos _call_*, a telemetria fica morta."""
    src = (pathlib.Path(__file__).resolve().parents[1] / "app" / "llm.py").read_text(encoding="utf-8")
    assert src.count("record_usage(config, data)  # qa/42 (FinOps)") == 3, \
        "record_usage tem que estar nos 3 provedores (anthropic, openai-compat, google)"


# --- gates diários persistidos (deploy re-executava o job) ------------------

def test_gates_diarios_sao_persistidos_nao_so_memoria():
    """LAST_EVAL/LAST_WARM zeram a cada deploy: o job inteiro rodava de novo.
    O warm são 60 req/dia contra o free tier de 200 da bolsai — 4 deploys num
    dia estouravam a cota. radar_daily já persistia; os outros dois, não."""
    app_dir = pathlib.Path(__file__).resolve().parents[1] / "app"
    ao = (app_dir / "analysis_outcomes.py").read_text(encoding="utf-8")
    assert ao.count('db.kv_set(conn, "analysisOutcomesLastRun"') == 1
    assert ao.count("last_run_date(conn) == _hoje()") == 1, "maybe_run tem que consultar o gate persistido"
    fu = (app_dir / "fundamentals.py").read_text(encoding="utf-8")
    assert fu.count('db.kv_set(conn, "fundamentalsLastWarm"') == 1
    assert fu.count("last_warm_date(conn) == _hoje_iso()") == 1, "maybe_warm tem que consultar o gate persistido"


def test_gate_persistido_do_warm_sobrevive_ao_restart():
    """Simula o deploy: LAST_WARM (memória) zera, mas o kv segura o job."""
    from app import fundamentals as fu
    conn = _fresh_db()
    assert fu.last_warm_date(conn) is None
    db.kv_set(conn, "fundamentalsLastWarm", fu._hoje_iso(), user_id=None)
    fu.LAST_WARM.update(date=None, aquecidos=0, erro=None)   # "restart"
    assert fu.last_warm_date(conn) == fu._hoje_iso(), "o gate tem que sobreviver ao restart"
