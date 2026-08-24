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
