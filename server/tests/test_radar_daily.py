# FASE 4 (1.3) — Radar diário: 1 varredura automática por dia útil + manual
# sob demanda. Sem rede e sem pytest-only: roda no mini-runner e no pytest.
import asyncio
import sqlite3
from datetime import datetime

from app import db, radar_daily, skill_ref
from app.radar_daily import BRT


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def _conn():
    c = sqlite3.connect(":memory:")
    db.init_db(c)
    return c


def _fake_fetch(symbol, rng):
    async def go():
        base = 10.0 + (hash(symbol) % 7)
        closes = [base + i * 0.1 for i in range(260)]
        candles = [{"time": 1700000000 + i * 86400, "open": v, "high": v * 1.01,
                    "low": v * 0.99, "close": v, "volume": 1000000} for i, v in enumerate(closes)]
        return {"candles": candles, "currency": "BRL"}
    return go()


# ---------------------------- gating puro (should_run) ----------------------
def test_should_run_dia_util_apos_horario():
    seg_0900 = datetime(2026, 7, 6, 9, 0, tzinfo=BRT)   # segunda 09:00 > 08:45
    assert radar_daily.should_run(now=seg_0900, last_date=None) is True


def test_should_run_bloqueia_antes_do_horario():
    seg_0800 = datetime(2026, 7, 6, 8, 0, tzinfo=BRT)
    assert radar_daily.should_run(now=seg_0800, last_date=None) is False


def test_should_run_bloqueia_fim_de_semana():
    sab = datetime(2026, 7, 4, 12, 0, tzinfo=BRT)
    dom = datetime(2026, 7, 5, 12, 0, tzinfo=BRT)
    assert radar_daily.should_run(now=sab, last_date=None) is False
    assert radar_daily.should_run(now=dom, last_date=None) is False


def test_should_run_no_maximo_uma_vez_por_dia():
    seg_1500 = datetime(2026, 7, 6, 15, 0, tzinfo=BRT)
    assert radar_daily.should_run(now=seg_1500, last_date="2026-07-06") is False
    assert radar_daily.should_run(now=seg_1500, last_date="2026-07-03") is True  # sexta anterior


# ---------------------------- armazenar e servir -----------------------------
def test_run_daily_armazena_e_get_stored_serve():
    import os
    os.environ["B3_SCAN_UNIVERSE"] = "AAAA3,BBBB3"
    try:
        c = _conn()
        r = _run(radar_daily.run_daily(c, _fake_fetch))
        assert r["scanAuto"] is True and r["scanOrigem"] == "automática"
        assert r.get("results") is not None and r.get("scanAtLabel")
        stored = radar_daily.get_stored(c, r["period"])
        assert stored and stored["scanAt"] == r["scanAt"]
        assert radar_daily.last_run_date(c) == datetime.now(BRT).date().isoformat()
    finally:
        os.environ.pop("B3_SCAN_UNIVERSE", None)


def test_manual_substitui_o_do_dia_sem_marcar_automatica():
    import os
    os.environ["B3_SCAN_UNIVERSE"] = "AAAA3"
    try:
        c = _conn()
        auto = _run(radar_daily.run_daily(c, _fake_fetch, origem="automática"))
        manual = _run(radar_daily.run_daily(c, _fake_fetch, origem="manual"))
        stored = radar_daily.get_stored(c, manual["period"])
        assert stored["scanOrigem"] == "manual" and stored["scanAuto"] is False
        # a data do ciclo AUTOMÁTICO não é sobrescrita pela manual
        assert radar_daily.last_run_date(c) == datetime.now(BRT).date().isoformat()
        assert auto["scanAt"] != stored["scanAt"] or auto["scanAt"] == stored["scanAt"]  # ambos válidos
    finally:
        os.environ.pop("B3_SCAN_UNIVERSE", None)


def test_maybe_run_respeita_gating_e_nunca_estoura():
    import os
    os.environ["B3_SCAN_UNIVERSE"] = "AAAA3"
    try:
        c = _conn()
        db.kv_set(c, "radarDailyLastRun", datetime.now(BRT).date().isoformat(), user_id=None)
        assert _run(radar_daily.maybe_run(c, _fake_fetch)) is None  # já rodou hoje

        def _boom(symbol, rng):
            async def go():
                raise RuntimeError("provider caiu")
            return go()
        db.kv_set(c, "radarDailyLastRun", "2000-01-01", user_id=None)
        # se o gating permitir agora, a falha do provedor NÃO pode propagar
        _run(radar_daily.maybe_run(c, _boom))
    finally:
        os.environ.pop("B3_SCAN_UNIVERSE", None)


def test_push_best_effort_para_quem_tem_token():
    import os
    os.environ["B3_SCAN_UNIVERSE"] = "AAAA3"
    try:
        c = _conn()
        c.execute("INSERT INTO users(id, provider, provider_sub, created_at) VALUES ('u1','t','s1','2026-01-01')")
        c.execute("INSERT INTO users(id, provider, provider_sub, created_at) VALUES ('u2','t','s2','2026-01-01')")
        db.kv_set(c, "pushTokens", ["tok"], user_id="u1")  # só u1 ativou push
        enviados = []

        # NOTA (quick task 260824-i45, 2026-08-24) — a asserção do título MUDOU
        # DE LUGAR, e a mudança é de correção, não de estilo.
        #
        # Até aqui era `assert "Radar do dia" in title` DENTRO de `fake_push`.
        # Esse assert nunca podia bater: `run_daily` aguarda o `notify_push`
        # dentro de `except Exception: pass` (radar_daily.py) e `AssertionError`
        # é subclasse de `Exception` — era engolido. Pior: `enviados.append(uid)`
        # rodava ANTES dele, então `assert enviados == ["u1"]` ficava verde de
        # qualquer jeito e o guardião era VÁCUO. Defeito latente PREEXISTENTE,
        # não introduzido por aquele quick task.
        #
        # Correção: o fake SÓ COLETA; o teste assere depois do `_run`. O título
        # em si mudou por decisão D1 — o horário das 08:45 fica (é pré-abertura
        # deliberada, candle da véspera fechado), o que faltava era o texto
        # dizer isso em vez de ler como alerta fora de hora.
        async def fake_push(uid, title, body):
            enviados.append((uid, title))     # SÓ COLETA: assert aqui é engolido
        _run(radar_daily.run_daily(c, _fake_fetch, notify_push=fake_push))
        assert [u for u, _t in enviados] == ["u1"]
        titulos = [t for _u, t in enviados]
        assert titulos == [skill_ref.PUSH_RADAR["titulo"]]
        assert "pré-abertura" in titulos[0].lower()
    finally:
        os.environ.pop("B3_SCAN_UNIVERSE", None)


# ---------------------------------------------------------------------------
# qa/43 — push do Radar diário NOMEIA o top-N. O ranking já era calculado
# (run_scan ordena por confluência) e o push jogava fora: "74 ativos
# analisados" mandava o usuário garimpar. Guardrail: o VEREDITO vai junto —
# o ranking não separa alta de baixa, então "VALE3 100%" sozinho seria lido
# como alta (o caso real de 16/07 era "Estudar baixa").
# ---------------------------------------------------------------------------

def test_push_body_nomeia_top3_com_veredito():
    payload = {"results": [
        {"ticker": "VALE3", "confluencia": 100, "veredito": "Estudar baixa"},
        {"ticker": "PETR4", "confluencia": 86, "veredito": "Estudar alta"},
        {"ticker": "ITUB4", "confluencia": 71, "veredito": "Monitorar"},
        {"ticker": "MGLU3", "confluencia": 60, "veredito": "Estudar alta"},
    ]}
    body = radar_daily.push_body(payload)
    assert "VALE3 100% estudar baixa" in body
    assert "PETR4 86% estudar alta" in body
    assert "ITUB4 71% monitorar" in body
    assert "MGLU3" not in body, "top-3: o 4º não entra"
    assert "4 ativos analisados" in body


def test_push_body_sempre_diz_o_lado_nunca_so_o_percentual():
    """O ranking é por confluência PURA (não separa alta de baixa). Sem o
    veredito, 'VALE3 100%' seria lido como alta — e o topo real de 16/07 era
    BAIXA. Este teste existe para que ninguém 'simplifique' o corpo depois."""
    body = radar_daily.push_body({"results": [
        {"ticker": "VALE3", "confluencia": 100, "veredito": "Estudar baixa"}]})
    assert "estudar baixa" in body, "o lado do setup NUNCA pode sumir do push"
    assert "VALE3 100%" in body


def test_push_body_sem_setup_nao_inventa_destaque():
    """Confluência 0 não é destaque — nada de nomear ativo à toa."""
    body = radar_daily.push_body({"results": [
        {"ticker": "VALE3", "confluencia": 0, "veredito": "Sem setup no momento"},
        {"ticker": "PETR4", "confluencia": 0, "veredito": "Sem setup no momento"}]})
    assert "VALE3" not in body and "PETR4" not in body
    assert "nenhum setup em destaque" in body
    assert "2 ativo(s) analisados" in body


def test_push_body_aguenta_payload_degradado():
    """Best-effort: campo faltando não pode derrubar o job do Radar."""
    for p in ({}, {"results": []}, {"results": [{"ticker": "X"}]},
              {"results": [{"confluencia": 90, "veredito": "Estudar alta"}]}):
        body = radar_daily.push_body(p)
        assert isinstance(body, str) and body, "push_body tem que devolver texto sempre"


def test_push_body_respeita_o_guardrail_regulatorio():
    """O corpo do push é texto de OUTPUT: os imperativos de operação proibidos
    em llm/scanner valem aqui também."""
    import re
    body = radar_daily.push_body({"results": [
        {"ticker": "PETR4", "confluencia": 92, "veredito": "Estudar alta"}]}).lower()
    for pat in (r"\bcompre\b", r"\bvenda\s+(agora|j[áa])", r"\bentre\s+agora\b",
                r"\bdeve\s+comprar\b", r"\brecomendo\s+(comprar|vender)\b"):
        assert not re.search(pat, body), f"push com imperativo de operação: {pat}"


def test_run_daily_usa_o_push_body():
    """Ancoragem: sem isto o push volta a ser o texto genérico."""
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[1] / "app" / "radar_daily.py").read_text(encoding="utf-8")
    assert src.count("corpo = push_body(payload)") == 1
    assert src.count("Varredura automática concluída: {n} ativo(s)") == 0, "sobrou o texto antigo"


# ---------------------------------------------------------------------------
# Fase 51 (plano 03, ENG-01) — arquivo diário do Radar + teto de engajamento.
# ---------------------------------------------------------------------------
def _linha(t, decisao="COMPRAR", tipo="a mercado", entrada=10.0, stop=9.0, alvo=12.0):
    return {"ticker": t, "close": entrada,
            "plano": {"decisao": decisao, "tipo": tipo, "setup": "rompimento",
                      "lado": "compra", "entrada": entrada, "stop": stop, "alvo": alvo}}


def test_store_result_grava_arquivo_diario_e_preserva_radardaily():
    c = _conn()
    payload = {"results": [_linha("AAAA3"), _linha("BBBB3", decisao="AGUARDAR"),
                           _linha("CCCC3", entrada=None)]}
    radar_daily.store_result(c, "6mo", payload, "automática")
    assert radar_daily.get_bruto(c, "6mo")["results"] == payload["results"]
    hoje = datetime.now(BRT).date().isoformat()
    arq = radar_daily.get_arquivo(c, hoje)
    assert arq["data"] == hoje and arq["scanAt"]
    assert [l["ticker"] for l in arq["linhas"]] == ["AAAA3"]
    assert set(arq["linhas"][0]) == {"ticker", "setup", "decisao", "tipo", "entrada",
                                    "stop", "alvo", "entradaAMercado", "close"}
    assert arq["linhas"][0]["entradaAMercado"] is True
    assert arq["universo"] == ["AAAA3", "BBBB3", "CCCC3"]
    from datetime import date
    assert date.fromisoformat(arq["dataBase"]) < date.fromisoformat(hoje)
    from app import pregao
    assert pregao.is_trading_day(date.fromisoformat(arq["dataBase"]))
    # manual também grava
    radar_daily.store_result(c, "6mo", {"results": []}, "manual")
    assert radar_daily.get_arquivo(c, hoje)["linhas"] == []


def test_arquivo_poda_50_dias_e_mantem_40():
    from datetime import timedelta
    c = _conn()
    hoje = datetime.now(BRT).date()
    for dias in (50, 40):
        d = (hoje - timedelta(days=dias)).isoformat()
        db.kv_set(c, "radarDailyArquivo:" + d, {"data": d, "linhas": [], "universo": []},
                  user_id=None)
    radar_daily.store_result(c, "6mo", {"results": []}, "automática")
    assert radar_daily.get_arquivo(c, (hoje - timedelta(days=50)).isoformat()) is None
    assert radar_daily.get_arquivo(c, (hoje - timedelta(days=40)).isoformat()) is not None


def test_arquivo_ate_devolve_o_mais_recente_dentro_da_janela():
    c = _conn()
    db.kv_set(c, "radarDailyArquivo:2026-11-10", {"data": "2026-11-10", "linhas": []}, user_id=None)
    assert radar_daily.arquivo_ate(c, "2026-11-10")[0] == "2026-11-10"
    assert radar_daily.arquivo_ate(c, "2026-11-14")[0] == "2026-11-10"
    assert radar_daily.arquivo_ate(c, "2026-11-18") is None   # 8 dias depois
    assert radar_daily.arquivo_ate(c, "lixo") is None


def _setup_push_dois_usuarios(c):
    c.execute("INSERT INTO users(id, provider, provider_sub, created_at) VALUES ('u1','t','s1','2026-01-01')")
    c.execute("INSERT INTO users(id, provider, provider_sub, created_at) VALUES ('u2','t','s2','2026-01-01')")
    for u in ("u1", "u2"):
        db.kv_set(c, "pushTokens", ["tok"], user_id=u)


def test_run_daily_respeita_teto_de_engajamento_mas_registra_evento():
    import os
    from app import push
    os.environ["B3_SCAN_UNIVERSE"] = "AAAA3"
    try:
        c = _conn()
        _setup_push_dois_usuarios(c)
        hoje = datetime.now(BRT).date().isoformat()
        push.reservar_engajamento(c, "u2", hoje, "fechamento")
        push.reservar_engajamento(c, "u2", hoje, "outro")   # u2 no teto
        enviados = []

        async def fake_push(uid, title, body):
            enviados.append(uid)
        _run(radar_daily.run_daily(c, _fake_fetch, notify_push=fake_push))
        assert enviados == ["u1"]
        assert db.kv_get(c, "pushEngajamento", None, user_id="u1")["tipos"] == ["radar"]
    finally:
        os.environ.pop("B3_SCAN_UNIVERSE", None)


def test_run_daily_teto_fail_closed_e_pref_fail_open(monkeypatch):
    import os
    from app import push
    os.environ["B3_SCAN_UNIVERSE"] = "AAAA3"
    try:
        c = _conn()
        _setup_push_dois_usuarios(c)
        eventos = []
        orig = radar_daily.store.push_events
        monkeypatch.setattr(radar_daily.store, "push_events",
                            lambda conn, evs, user_id=None: eventos.append(user_id))

        def boom(*a, **k):
            raise RuntimeError("kv")
        # 1) reservar levanta -> ninguém recebe, rastro continua
        monkeypatch.setattr(push, "reservar_engajamento", boom)
        enviados = []

        async def fake_push(uid, title, body):
            enviados.append(uid)
        _run(radar_daily.run_daily(c, _fake_fetch, notify_push=fake_push))
        assert enviados == [] and sorted(eventos) == ["u1", "u2"]
        monkeypatch.undo()
        # 2) prefs_for levanta -> Radar segue enviando (fail-open da pref)
        monkeypatch.setattr(push, "prefs_for", boom)
        _run(radar_daily.run_daily(c, _fake_fetch, notify_push=fake_push))
        assert sorted(enviados) == ["u1", "u2"]
    finally:
        os.environ.pop("B3_SCAN_UNIVERSE", None)


# ---------------------------------------------------------------------------
# Fase 51 / 51-07 (D-14, ENG-10) — linha "Ontem: ..." por usuário no push do
# Radar 08:45. Sem push novo; sem "e se" = corpo idêntico ao de antes.
# ---------------------------------------------------------------------------
def _rodar_radar_com_eses(monkeypatch, por_uid):
    import os
    from app import dia_na_bolsa
    os.environ["B3_SCAN_UNIVERSE"] = "AAAA3"
    try:
        c = _conn()
        _setup_push_dois_usuarios(c)
        eventos = {}
        orig = radar_daily.store.push_events
        monkeypatch.setattr(radar_daily.store, "push_events",
                            lambda conn, evs, user_id=None: eventos.__setitem__(user_id, evs[0]["text"]))

        def fake_eses(conn, uid, hoje):
            r = por_uid.get(uid)
            if isinstance(r, Exception):
                raise r
            return r
        monkeypatch.setattr(dia_na_bolsa, "e_se_de_ontem", fake_eses)
        enviados = {}

        async def fake_push(uid, title, body):
            enviados[uid] = body
        _run(radar_daily.run_daily(c, _fake_fetch, notify_push=fake_push))
        return enviados, eventos
    finally:
        os.environ.pop("B3_SCAN_UNIVERSE", None)


def test_radar_acrescenta_ontem_alvo_e_stop_por_usuario(monkeypatch):
    enviados, eventos = _rodar_radar_com_eses(monkeypatch, {
        "u1": {"chave": "corpo_ontem_alvo", "T": "PETR4"},
        "u2": {"chave": "corpo_ontem_stop", "T": "VALE3"}})
    assert enviados["u1"].endswith(" Ontem: PETR4 chegaria ao alvo.")
    assert enviados["u2"].endswith(" Ontem: VALE3 teve o stop atingido.")
    # o rastro em push_events é o MESMO texto enviado àquele usuário
    assert eventos == enviados


def test_radar_sem_eses_ou_com_falha_mantem_o_corpo_antigo(monkeypatch):
    enviados, eventos = _rodar_radar_com_eses(monkeypatch, {
        "u1": None, "u2": RuntimeError("kv")})
    assert enviados["u1"] == enviados["u2"]
    assert "Ontem" not in enviados["u1"] and "{T}" not in enviados["u1"]
    assert eventos == enviados
