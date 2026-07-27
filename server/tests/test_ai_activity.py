"""qa/45 — Atividade da IA: custo estimado (R$) + ledger por chamada + captura
isolada por operação (llm.collect_usage)."""
import sqlite3

from app import ai_activity as A
from app import llm


def _db():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE kv (key TEXT PRIMARY KEY, value TEXT)")
    return c


def test_custo_por_modelo_e_fallback():
    # sonnet: (3+15) USD/Mi * 1Mi in + 1Mi out * câmbio
    esperado = round((3.0 + 15.0) * A.USD_BRL, 4)
    assert A.custo_estimado("claude-sonnet-5", 1_000_000, 1_000_000) == esperado
    # opus é mais caro que sonnet
    assert A.custo_estimado("claude-opus-5", 1000, 1000) > A.custo_estimado("claude-sonnet-5", 1000, 1000)
    # modelo desconhecido usa fallback (não zera)
    assert A.custo_estimado("modelo-x", 1_000_000, 0) == round(A._FALLBACK_USD_POR_MI[0] * A.USD_BRL, 4)
    # sem tokens = sem custo
    assert A.custo_estimado("claude-sonnet-5", 0, 0) == 0.0


def test_registrar_acumula_e_capa_historico():
    conn = _db()
    A.registrar(conn, scope=None, ticker="PETR4", tipo="Análise", model="claude-sonnet-5", in_tok=1000, out_tok=500)
    A.registrar(conn, scope=None, ticker="VALE3", tipo="Radar", model="claude-opus-5", in_tok=2000, out_tok=800)
    snap = A.snapshot(conn, None)
    assert snap["total"]["calls"] == 2
    assert snap["total"]["inTok"] == 3000 and snap["total"]["outTok"] == 1300
    assert snap["total"]["custo"] > 0 and snap["total"]["desde"]
    # mais recente primeiro
    assert snap["recentes"][0]["ticker"] == "VALE3"
    assert snap["usdBrl"] == A.USD_BRL


def test_registrar_ignora_zero_tokens():
    conn = _db()
    A.registrar(conn, scope=None, ticker="X", tipo="Análise", model="claude-sonnet-5", in_tok=0, out_tok=0)
    assert A.snapshot(conn, None)["total"]["calls"] == 0


def test_acumulado_isolado_por_escopo():
    conn = _db()
    A.registrar(conn, scope="u1", ticker="PETR4", tipo="Análise", model="claude-sonnet-5", in_tok=100, out_tok=50)
    A.registrar(conn, scope="u2", ticker="VALE3", tipo="Radar", model="claude-sonnet-5", in_tok=100, out_tok=50)
    assert A.snapshot(conn, "u1")["total"]["calls"] == 1
    assert A.snapshot(conn, "u2")["total"]["calls"] == 1
    assert A.snapshot(conn, None)["total"]["calls"] == 0


def test_collect_usage_isola_e_soma():
    # o coletor por-operação (ContextVar) captura só o que roda dentro do `with`
    llm.record_usage({"model": "x"}, {"usage": {"input_tokens": 5, "output_tokens": 5}})  # fora → ignorado
    with llm.collect_usage() as u:
        llm.record_usage({"model": "claude-sonnet-5"}, {"usage": {"input_tokens": 100, "output_tokens": 50}})
        llm.record_usage({"model": "claude-sonnet-5"}, {"usage": {"input_tokens": 200, "output_tokens": 80}})
    assert u == [(100, 50, "claude-sonnet-5"), (200, 80, "claude-sonnet-5")]
    conn = _db()
    A.registrar_uso(conn, scope=None, ticker="ITUB4", tipo="Análise", usos=u)
    snap = A.snapshot(conn, None)
    assert snap["total"]["calls"] == 1  # UMA linha, tokens somados
    assert snap["recentes"][0]["inTok"] == 300 and snap["recentes"][0]["outTok"] == 130


def test_registrar_uso_vazio_noop():
    conn = _db()
    A.registrar_uso(conn, scope=None, ticker="X", tipo="Análise", usos=[])
    assert A.snapshot(conn, None)["total"]["calls"] == 0


def test_backend_liga_atividade_nas_rotas():
    """As 4 rotas de análise capturam uso e registram atividade."""
    import pathlib
    main_src = (pathlib.Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")
    assert main_src.count("with llm.collect_usage() as _uso") >= 4
    assert main_src.count("ai_activity.registrar_uso(") >= 4
    assert '@app.get("/api/ai-activity")' in main_src


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); print("ok", name)
    print("TODOS OS TESTES DE AI_ACTIVITY PASSARAM")
