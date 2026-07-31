"""Objetivo 4 — seleção de período de candles."""
from app import candles as cm
from app import technical_models as tm


def test_normalize_period():
    assert cm.normalize_period("6mo") == "6mo"
    assert cm.normalize_period("6MO") == "6mo"
    assert cm.normalize_period(" 1y ") == "1y"
    assert cm.normalize_period("xpto") == cm.DEFAULT_PERIOD
    assert cm.normalize_period(None) == cm.DEFAULT_PERIOD


def test_resolve_keep():
    assert cm.resolve_keep("1mo") == 22
    assert cm.resolve_keep("3mo") == 66
    assert cm.resolve_keep("6mo") == 126
    assert cm.resolve_keep("1y") == 252
    assert cm.resolve_keep("2y") == 504
    assert cm.resolve_keep(None) == cm.PERIOD_BARS[cm.DEFAULT_PERIOD]
    assert cm.resolve_keep("lixo") == cm.PERIOD_BARS[cm.DEFAULT_PERIOD]


def test_period_to_range():
    assert cm.period_to_range("3mo") == "3mo"
    assert cm.period_to_range("1y") == "1y"
    assert cm.period_to_range("invalido") == cm.PERIOD_RANGE[cm.DEFAULT_PERIOD]


def test_interval():
    assert cm.normalize_interval("1wk") == "1wk"
    assert cm.normalize_interval("1d") == "1d"
    assert cm.normalize_interval("mensal") == cm.DEFAULT_INTERVAL


def _mk_candles(n):
    out = []
    base = 10.0
    for i in range(n):
        base += (0.1 if i % 2 == 0 else -0.05)
        out.append({"date": f"2026-01-{(i % 28) + 1:02d}", "open": base, "high": base + 0.2,
                    "low": base - 0.2, "close": base, "volume": 1000 + i})
    return out


def test_build_context_tail_n_recorta_janela():
    candles = _mk_candles(400)
    ctx_small = tm.build_context("PETR4", {"price": candles[-1]["close"]}, candles, "completo", None, tail_n=22)
    ctx_big = tm.build_context("PETR4", {"price": candles[-1]["close"]}, candles, "completo", None, tail_n=252)
    # a janela enviada à IA respeita o período (com piso de 20)
    assert ctx_small["historyStats"]["candlesSentToLLM"] == 22
    assert ctx_big["historyStats"]["candlesSentToLLM"] == 252
    assert len(ctx_small["candles"]) == 22
    assert len(ctx_big["candles"]) == 252
    # indicadores de média longa continuam calculados (warmup na série cheia):
    # com 400 candles, SMA50 do resumo não é None nos dois casos
    assert ctx_small["trend"]["sma50"] is not None
    assert ctx_big["trend"]["sma50"] is not None


def test_build_context_tail_n_piso():
    candles = _mk_candles(100)
    ctx = tm.build_context("VALE3", None, candles, "completo", None, tail_n=1)
    assert ctx["historyStats"]["candlesSentToLLM"] >= 20  # piso protege o contexto


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("TODOS OS TESTES DE PERIODO DE CANDLES PASSARAM")


# ---------------------------------------------------------------------------
# ADR-002 (Decisão 3) — a janela é contada em VELAS DO INTERVALO, não em pregões
# ---------------------------------------------------------------------------

def test_resolve_keep_diario_inalterado():
    """Compatibilidade dura: o diário é o caminho de produção de hoje."""
    for p, esperado in (("1mo", 22), ("3mo", 66), ("6mo", 126), ("1y", 252), ("2y", 504)):
        assert cm.resolve_keep(p) == esperado
        assert cm.resolve_keep(p, "1d") == esperado
        assert cm.resolve_keep(p, None) == esperado


def test_resolve_keep_intraday_conta_velas_e_nao_pregoes():
    """A armadilha medida: com 15m, 'ver 1mo' entregava 22 velas de 15 minutos
    — 5,5 HORAS de contexto para quem pediu um mês, sem erro nenhum."""
    assert cm.resolve_keep("1mo", "15m") == 22 * 29     # 638 velas, não 22
    assert cm.resolve_keep("1mo", "5m") == 22 * 85
    assert cm.resolve_keep("1mo", "30m") == 22 * 15
    assert cm.resolve_keep("6mo", "60m") == 126 * 8
    # 22 velas de 15m seriam menos de um pregão — o bug em uma linha
    assert cm.resolve_keep("1mo", "15m") > cm.bars_per_session("15m")


def test_bars_per_session_bate_com_a_medicao():
    """Medido no Yahoo em 30/07/2026 (PETR4, pregão 10:00–17:00 BRT)."""
    assert cm.bars_per_session("1m") == 418
    assert cm.bars_per_session("15m") == 29
    assert cm.bars_per_session("1d") == 1
    assert cm.bars_per_session("60m") == cm.bars_per_session("1h") == 8
    assert cm.bars_per_session("desconhecido") == 1     # degrada como diário


# ---------------------------------------------------------------------------
# ADR-001 (item 1d) — LACUNA na série intraday.
# Em 31/07/2026 o feed de B3 do Yahoo ficou 3h sem publicar e, ao voltar às
# 13:02, NÃO preencheu a manhã. A série ficou com um buraco de 2h45 e nada no
# app percebia: a instrumentação via série VAZIA, não série FURADA.
# ---------------------------------------------------------------------------

def _velas(horarios, dia="2026-07-31"):
    return [{"date": f"{dia} {h}", "open": 1, "high": 2, "low": 1, "close": 1.5, "volume": 10}
            for h in horarios]


def test_serie_integra_nao_acusa_lacuna():
    """Pregão cheio de 15m: 10:00 → 16:45, sem buraco."""
    horas = [f"{10 + (i * 15) // 60:02d}:{(i * 15) % 60:02d}" for i in range(28)]
    r = cm.detectar_lacunas(_velas(horas), "15m")
    assert r["temLacuna"] is False
    assert r["velasFaltando"] == 0 and r["cobertura"] == 1.0


def test_inicio_tardio_e_o_caso_de_31_07():
    """A manhã inteira faltando: série começa às 12:45 em vez de 10:00."""
    r = cm.detectar_lacunas(_velas(["12:45", "13:00", "13:15", "13:30"]), "15m")
    assert r["temLacuna"] is True
    assert r["inicioTardio"] == "2026-07-31 12:45"
    assert r["velasFaltando"] == 11          # 10:00 → 12:45 em passos de 15 min
    assert r["cobertura"] < 0.5


def test_buraco_no_meio_do_pregao():
    r = cm.detectar_lacunas(_velas(["10:00", "10:15", "11:30", "11:45"]), "15m")
    assert r["temLacuna"] is True
    assert r["buracos"] == [{"de": "2026-07-31 10:15", "ate": "2026-07-31 11:30",
                             "velasFaltando": 4}]
    assert r["velasFaltando"] == 4


def test_tolerancia_da_vela_em_formacao():
    """A vela em formação chega com o timestamp do ÚLTIMO NEGÓCIO, fora da
    grade (medido: 14:42 numa série de 15m). Isso não pode virar falso buraco."""
    r = cm.detectar_lacunas(_velas(["10:00", "10:15", "10:30", "10:42"]), "15m")
    assert r["temLacuna"] is False


def test_diario_nao_e_avaliado():
    """No diário a grade tem feriado e pregão curto — cobrar regularidade daria
    falso positivo sem valor."""
    diario = [{"date": "2026-07-2%d" % i, "close": 1} for i in range(1, 6)]
    assert cm.detectar_lacunas(diario, "1d")["temLacuna"] is False
    assert cm.detectar_lacunas(diario, None)["temLacuna"] is False


def test_olha_so_o_ultimo_pregao():
    """A lacuna que importa para a decisão é a do pregão corrente; buraco de
    ontem não deve contaminar a leitura de hoje."""
    ontem = _velas(["10:00", "14:00"], dia="2026-07-30")     # buraco enorme
    hoje = _velas([f"{10 + (i * 15) // 60:02d}:{(i * 15) % 60:02d}" for i in range(28)])
    r = cm.detectar_lacunas(ontem + hoje, "15m")
    assert r["temLacuna"] is False


def test_bordas_nao_explodem():
    assert cm.detectar_lacunas([], "15m")["temLacuna"] is False
    assert cm.detectar_lacunas(None, "15m")["temLacuna"] is False
    assert cm.detectar_lacunas([{"date": "lixo"}], "15m")["temLacuna"] is False
    assert cm.detectar_lacunas(_velas(["10:00"]), "15m")["temLacuna"] is False
