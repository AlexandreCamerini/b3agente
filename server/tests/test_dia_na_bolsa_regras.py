"""server/tests/test_dia_na_bolsa_regras.py — guardião do núcleo puro do card
"Seu dia na bolsa" (Fase 51, plano 51-01). Séries sintéticas, sem I/O."""
import random
from datetime import date, timedelta

import pytest

from app import dia_na_bolsa_regras as R


def dias_uteis(n, inicio=date(2025, 1, 2)):
    out, d = [], inicio
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def candle(d, o=10.0, h=10.5, l=9.5, c=10.0):
    return {"date": d, "open": o, "high": h, "low": l, "close": c}


def serie_visto(n=12, sobre=None):
    """n candles planos (dia 0 = dataBase). `sobre`: {idx: {campo: valor}}."""
    ds = dias_uteis(n)
    cs = [candle(d) for d in ds]
    for idx, campos in (sobre or {}).items():
        cs[idx].update(campos)
    return ds, cs


def visto(ds, **extra):
    v = {"ticker": "PETR4", "setup": "rompimento", "dataBase": ds[0], "entrada": 10.0,
         "stop": 9.0, "alvo": 12.0, "entradaAMercado": True, "precoBase": 10.0}
    v.update(extra)
    return v


# ---------------------------------------------------------------- família 1
def test_stop_no_segundo_pregao_resolve_naquele_dia():
    ds, cs = serie_visto(12, {2: {"low": 8.9}})
    e = R.estado_do_visto(visto(ds), cs, ds[2])
    assert e["resultado"] == "stop"
    assert e["resolvidoHoje"] is True
    assert e["resolvidoEm"] == ds[2]
    assert e["r"] == pytest.approx(-1.0, abs=0.05)
    assert e["aberto"] is False


def test_stop_resolvido_antes_nao_e_resolvido_hoje():
    ds, cs = serie_visto(12, {2: {"low": 8.9}})
    e = R.estado_do_visto(visto(ds), cs, ds[4])
    assert e["resultado"] == "stop" and e["resolvidoHoje"] is False


def test_alvo_no_terceiro_pregao():
    ds, cs = serie_visto(12, {3: {"high": 12.5}})
    e = R.estado_do_visto(visto(ds), cs, ds[3])
    assert e["resultado"] == "alvo" and e["resolvidoHoje"] is True
    assert e["r"] > 0
    antes = R.estado_do_visto(visto(ds), cs, ds[2])
    assert antes["aberto"] is True and antes["resultado"] is None


def test_cinco_pregoes_sem_toque_segue_aberto_nao_expirou():
    ds, cs = serie_visto(12)
    e = R.estado_do_visto(visto(ds), cs, ds[5])
    assert e == {"resultado": None, "resultadoBruto": None, "r": None, "resolvidoEm": None,
                 "resolvidoHoje": False, "aberto": True, "decorridos": 5}


def test_dez_pregoes_sem_gatilho():
    ds, cs = serie_visto(12)
    v = visto(ds, entrada=11.0, entradaAMercado=False)
    assert R.estado_do_visto(v, cs, ds[9])["aberto"] is True
    e = R.estado_do_visto(v, cs, ds[10])
    assert e["resultado"] == "sem_gatilho" and e["r"] is None
    assert e["resolvidoHoje"] is True and e["aberto"] is False


def test_dez_pregoes_expirou_guarda_rotulo_bruto():
    ds, cs = serie_visto(12, {10: {"close": 10.2}})
    e = R.estado_do_visto(visto(ds), cs, ds[10])
    assert e["resultado"] == "expirou"
    assert e["resultadoBruto"] == "expirou_pos"
    assert e["resolvidoHoje"] is True
    ds2, cs2 = serie_visto(12, {10: {"close": 9.8}})
    e2 = R.estado_do_visto(visto(ds2), cs2, ds2[10])
    assert e2["resultado"] == "expirou" and e2["resultadoBruto"] == "expirou_neg"


def test_visto_sem_dados_devolve_none():
    ds, cs = serie_visto(12)
    assert R.estado_do_visto(visto(ds), [], ds[3]) is None
    assert R.estado_do_visto(visto(ds, stop=None), cs, ds[3]) is None
    assert R.estado_do_visto(visto(ds, alvo=None), cs, ds[3]) is None
    assert R.estado_do_visto(visto(ds, entrada=None, precoBase=None), cs, ds[3]) is None
    assert R.estado_do_visto(None, cs, ds[3]) is None


def test_candles_futuros_ao_hoje_sao_ignorados():
    ds, cs = serie_visto(12, {8: {"low": 8.0}})
    e = R.estado_do_visto(visto(ds), cs, ds[5])
    assert e["aberto"] is True


def test_placar_semanal_sempre_com_quatro_contadores():
    assert R.placar_semanal([]) == {"vistos": 0, "alvo": 0, "stop": 0, "abertos": 0}
    est = [{"resultado": "alvo"}, {"resultado": "stop"}, {"resultado": None, "aberto": True},
           {"resultado": "expirou"}, {"resultado": "sem_gatilho"}, None]
    assert R.placar_semanal(est) == {"vistos": 5, "alvo": 1, "stop": 1, "abertos": 3}


def test_eventos_motor_do_dia():
    ev = [
        {"time": "17/11/2026 10:05", "kind": "buy", "t": "VALE3", "tag": "alvo", "text": "x"},
        {"time": "17/11/2026 09:30", "kind": "buy", "t": "PETR4", "tag": "stop", "text": "y"},
        {"time": "16/11/2026 15:00", "kind": "buy", "t": "ITUB4", "tag": "stop"},
        {"time": "17/11/2026 11:00", "kind": "buy", "t": "ABEV3", "tag": "entrada-auto"},
        {"time": "17/11/2026 12:00", "kind": "buy", "t": "BBAS3", "tag": "pendente-executada"},
        {"time": "17/11/2026 13:00", "marcoMotor": {"tipo": "stop_subiu", "ticker": "WEGE3",
                                                    "stop": 31.5, "motivo": "trailing"}},
        {"time": "17/11/2026 14:00", "marcoMotor": {"tipo": "breakeven", "ticker": "MGLU3",
                                                    "stop": 2.1, "motivo": "be"}},
        {"time": "17/11/2026 14:30", "kind": "buy", "tag": "stop"},          # sem ticker
        {"time": "17/11/2026 14:40", "kind": "info", "t": "VALE3", "text": "stop alvo"},  # sem tag
    ]
    out = R.eventos_motor_do_dia(ev, "17/11/2026")
    assert [(o["hora"], o["chave"], o["ticker"]) for o in out] == [
        ("09:30", "f2_stop_executado", "PETR4"),
        ("10:05", "f2_alvo_executado", "VALE3"),
        ("11:00", "f2_entrada_auto", "ABEV3"),
        ("12:00", "f2_pendente_executada", "BBAS3"),
        ("13:00", "f2_stop_subiu", "WEGE3"),
        ("14:00", "f2_breakeven", "MGLU3"),
    ]
    assert out[4]["stop"] == 31.5 and out[0]["stop"] is None
    assert R.eventos_motor_do_dia([], "17/11/2026") == []


def test_retorno_dia():
    s = [{"date": "2026-11-16", "close": 100.0}, {"date": "2026-11-17", "close": 102.0}]
    assert R.retorno_dia(s, "2026-11-17", "close") == pytest.approx(2.0)
    assert R.retorno_dia(s, "2026-11-18", "close") is None
    assert R.retorno_dia(s[1:], "2026-11-17", "close") is None
    eq = [{"data": "2026-11-16", "patrimonio": 1000.0}, {"data": "2026-11-17", "patrimonio": 990.0}]
    assert R.retorno_dia(eq, "2026-11-17", "patrimonio") == pytest.approx(-1.0)
    assert R.retorno_dia([], "2026-11-17", "close") is None


# ---------------------------------------------------------------- família 3
def serie_close(n, hoje_ret, seed=7, amp=0.01):
    """n fechamentos com |r| <= amp, e último retorno = hoje_ret."""
    rnd = random.Random(seed)
    ds = dias_uteis(n)
    c, out = 100.0, [{"date": ds[0], "close": 100.0}]
    for d in ds[1:-1]:
        c *= 1 + rnd.uniform(-amp, amp)
        out.append({"date": d, "close": c})
    c *= 1 + hoje_ret
    out.append({"date": ds[-1], "close": c})
    return ds[-1], out


def test_ibov_raro_dispara_com_queda_forte():
    hoje, s = serie_close(262, -0.038)
    f = R.regra_ibov_raro(s, hoje)
    assert f["regra"] == "ibov_raro"
    assert f["pct"] == pytest.approx(-3.8, abs=0.01)
    assert f["percentil"] >= 0.95
    assert f["conceito"] == {"fonte": "kb", "id": "ind-volatilidade-historica"}
    assert f["mesesDesde"] is None  # nunca houve |r| >= 3,8% na série


def test_ibov_comum_ou_curto_ou_defasado_devolve_none():
    hoje, s = serie_close(262, 0.005)
    assert R.regra_ibov_raro(s, hoje) is None
    hoje2, s2 = serie_close(150, -0.05)
    assert R.regra_ibov_raro(s2, hoje2) is None
    hoje3, s3 = serie_close(262, -0.05)
    assert R.regra_ibov_raro(s3, "2099-01-01") is None


def serie_ativo(n, mov_hoje, **hoje_campos):
    """Candles com range ~1,0 e fechamento oscilando; último com movimento dado."""
    ds = dias_uteis(n)
    cs, c = [], 50.0
    for i, d in enumerate(ds[:-1]):
        c2 = c + (0.2 if i % 2 else -0.2)
        cs.append({"date": d, "open": c, "high": max(c, c2) + 0.4, "low": min(c, c2) - 0.4, "close": c2})
        c = c2
    c2 = c + mov_hoje
    ult = {"date": ds[-1], "open": c, "high": max(c, c2) + 0.1, "low": min(c, c2) - 0.1, "close": c2}
    ult.update(hoje_campos)
    cs.append(ult)
    return ds[-1], cs


def _atr_prev(cs):
    from app import indicators
    return indicators.atr([c["high"] for c in cs], [c["low"] for c in cs],
                          [c["close"] for c in cs], 14)[-2]


def test_atr_ativo_tres_atr_dispara_e_um_e_meio_nao():
    hoje, cs = serie_ativo(280, 0.0)
    a = _atr_prev(cs)
    hoje, cs3 = serie_ativo(280, 3 * a)
    f = R.regra_atr_ativo(cs3, hoje, "PETR4")
    assert f["regra"] == "atr_ativo" and f["ticker"] == "PETR4"
    assert f["multiplo"] == pytest.approx(3.0, abs=0.15)
    assert f["conceito"]["id"] == "ind-atr"
    hoje, cs15 = serie_ativo(280, 1.5 * a)
    assert R.regra_atr_ativo(cs15, hoje, "PETR4") is None
    assert R.regra_atr_ativo(cs3, "2099-01-01", "PETR4") is None
    assert R.regra_atr_ativo(cs3[:10], cs3[9]["date"], "PETR4") is None


def test_gap_dispara_e_gap_fechado_nao():
    hoje, cs = serie_ativo(280, 0.0)
    a = _atr_prev(cs)
    prev_close = cs[-2]["close"]
    abre = prev_close + 2 * a
    hoje, cs_ok = serie_ativo(280, 0.0, open=abre, close=abre + 0.3, high=abre + 0.5, low=abre - 0.1)
    # reconstrói com prev_close igual (a série é determinística)
    f = R.regra_gap(cs_ok, hoje, "VALE3")
    assert f["regra"] == "gap" and f["direcao"] == "alta"
    assert f["conceito"]["id"] == "estr-gap"
    hoje, cs_fech = serie_ativo(280, 0.0, open=abre, close=prev_close - 0.2, high=abre + 0.1, low=prev_close - 0.3)
    assert R.regra_gap(cs_fech, hoje, "VALE3") is None
    hoje, cs_peq = serie_ativo(280, 0.0, open=prev_close + 0.05, close=prev_close + 0.1)
    assert R.regra_gap(cs_peq, hoje, "VALE3") is None


def test_extremo_52s():
    ds = dias_uteis(260)
    base = [{"date": d, "close": 100.0 + (i % 7)} for i, d in enumerate(ds[:-1])]
    mx = base + [{"date": ds[-1], "close": 120.0}]
    f = R.regra_extremo_52s(mx, ds[-1], "ITUB4", "close")
    assert f["regra"] == "max52" and f["percentil"] == 1.0
    assert f["conceito"] == {"fonte": "conceito", "id": "extremo-52-semanas"}
    mn = base + [{"date": ds[-1], "close": 90.0}]
    assert R.regra_extremo_52s(mn, ds[-1], "ITUB4", "close")["regra"] == "min52"
    meio = base + [{"date": ds[-1], "close": 103.0}]
    assert R.regra_extremo_52s(meio, ds[-1], "ITUB4", "close") is None
    assert R.regra_extremo_52s(mx[:100] + [{"date": ds[-1], "close": 999.0}], ds[-1], None, "close") is None


def universo(n_ativos, n_dias, frac_hoje_alta):
    ds = dias_uteis(n_dias)
    rnd = random.Random(3)
    u = {}
    for k in range(n_ativos):
        cs, c = [], 20.0
        for i, d in enumerate(ds):
            if i == len(ds) - 1:
                c = c + (0.5 if k < int(n_ativos * frac_hoje_alta) else -0.5)
            else:
                c = c + rnd.choice([-0.3, 0.3])
            cs.append({"date": d, "open": c, "high": c + 0.2, "low": c - 0.2, "close": c})
        u[f"T{k:02d}"] = cs
    return ds[-1], u


def test_amplitude():
    hoje, u = universo(40, 120, 0.95)
    f = R.regra_amplitude(u, hoje)
    assert f["regra"] == "amplitude" and f["direcao"] == "alta"
    assert f["n"] == 40 and f["fracao"] >= R.AMPLITUDE_MIN
    assert f["conceito"] == {"fonte": "conceito", "id": "amplitude"}
    hoje, u2 = universo(40, 120, 0.6)
    assert R.regra_amplitude(u2, hoje) is None
    hoje, u3 = universo(10, 120, 1.0)
    assert R.regra_amplitude(u3, hoje) is None


def test_escolher_fato():
    assert R.escolher_fato([]) is None
    a = {"regra": "ibov_raro", "ticker": None, "percentil": 0.97}
    b = {"regra": "atr_ativo", "ticker": "VALE3", "percentil": 0.99}
    assert R.escolher_fato([a, b]) is b
    c = {"regra": "atr_ativo", "ticker": "PETR4", "percentil": 0.97, "doUsuario": True}
    assert R.escolher_fato([a, c]) is c  # empate: do usuário antes de mercado
    d1 = {"regra": "gap", "ticker": "ZZZZ3", "percentil": 0.9}
    d2 = {"regra": "gap", "ticker": "AAAA3", "percentil": 0.9}
    assert R.escolher_fato([d1, d2]) is d2  # empate total: ticker alfabético
    sem = {"regra": "amplitude", "ticker": None, "percentil": None}
    assert R.escolher_fato([sem, d1]) is d1


def test_ordem_familias_por_modo():
    assert R.ordem_familias("estudo") == [1, 3, 2]
    assert R.ordem_familias("educacional") == [1, 3, 2]
    assert R.ordem_familias("operador") == [2, 1, 3]
    assert R.ordem_familias("operador", [1, 3]) == [1, 3]
    assert R.ordem_familias("estudo", []) == []


def test_variante_deterministica_por_sha256():
    import hashlib
    v = R.variante("u1", "2026-11-17", "f1_alvo", 5)
    assert v == R.variante("u1", "2026-11-17", "f1_alvo", 5)
    assert 0 <= v < 5
    esperado = int.from_bytes(hashlib.sha256(b"u1|2026-11-17|f1_alvo").digest()[:8], "big") % 5
    assert v == esperado
    indices = {R.variante("u1", d, "f1_alvo", 7) for d in dias_uteis(40)}
    assert len(indices) > 1
    assert R.variante("u1", "2026-11-17", "k", 1) == 0
    assert R.variante("u1", "2026-11-17", "k", 0) is None


def test_modulo_sem_io_nem_regua_paralela():
    import re
    from pathlib import Path
    src = Path(R.__file__).read_text(encoding="utf-8")
    code = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("#"))
    assert "_avaliar_entry(" in code
    assert not re.search(r"bateu_stop|bateu_alvo", code)
    assert not re.search(r"^\s*(import random|.*\brandom\.)", code, re.M)
    assert not re.search(r"(^|[^_.a-z])hash\(", code)
    imports = [l for l in code.splitlines() if re.match(r"\s*(from|import) ", l)]
    assert not [l for l in imports if re.search(r"db|httpx|candle_provider|brapi|yahoo", l)]
    assert "IBOV_PERCENTIL = 0.95" in src and "ATR_MULT_ATIVO = 2.0" in src
    for cid in ("ind-volatilidade-historica", "ind-atr", "estr-gap", "amplitude", "extremo-52-semanas"):
        assert cid in src
