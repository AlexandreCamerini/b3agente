"""FASE 1 — Setups testados do mercado BR (setups.py, detectores puros).

Cobre cada setup em dois níveis:
  • regra (ctx sintético): o critério objetivo dispara/não dispara como
    documentado em qa/SETUPS.md, com gatilho/invalidação/alvo corretos;
  • ponta a ponta (candles reais sintéticos): detect_setups encontra o padrão
    depois de indicators.compute, provando a integração com o motor.
Guardrail inegociável: nenhum nome/critério com verbo de ordem.
"""
import re

from app import indicators as ind
from app import setups

IMPERATIVE = re.compile(r"\b(compre|venda|entre agora|deve comprar|deve vender)\b", re.I)


# ------------------------------ helpers -------------------------------------

def _ctx(**over):
    """ctx mínimo hand-made para testar a REGRA de um detector isolado."""
    base = {
        "closes": [], "highs": [], "lows": [], "last": {}, "close": None,
        "sma20": None, "sma50": None, "rsi": 50.0, "bbu": None, "bbl": None,
        "pos_in_candle": None, "vol_ratio": None, "ind": {},
        "candles": [], "ema9_arr": [], "ema21": None, "sma200": None,
        "rsi2": None, "adx": None, "di_plus": None, "di_minus": None, "atr": 1.0,
    }
    base.update(over)
    return base


def _candles(closes, vols=None, spread=0.3):
    out = []
    for i, c in enumerate(closes):
        out.append({"date": f"2026-{(i // 28) + 1:02d}-{(i % 28) + 1:02d}",
                    "open": c - 0.05, "high": c + spread, "low": c - spread,
                    "close": c, "volume": (vols[i] if vols else 1000)})
    return out


def _obrigatorios_ok(s):
    return all(c["ok"] for c in s["criterios"] if c["obrigatorio"])


# ------------------------------ família 9.x ---------------------------------

def test_9_1_alta_dispara_na_virada_da_mme9():
    c = _ctx(ema9_arr=[10.5, 10.2, 10.4], close=10.8,
             last={"high": 11.0, "low": 10.0, "close": 10.8}, vol_ratio=1.2)
    s = setups._setup_9_1(c, "alta")
    assert _obrigatorios_ok(s) and s["confluencia"] == 100
    assert s["gatilho"] == 11.0 and s["invalidacao"] == 10.0
    assert s["alvoSugerido"] == 13.0  # gatilho + 2×risco (R:R 2:1)
    assert s["backtestavel"] is True and s["referencia"]


def test_9_1_nao_dispara_sem_virada():
    c = _ctx(ema9_arr=[10.0, 10.2, 10.4], close=10.8,
             last={"high": 11.0, "low": 10.0, "close": 10.8})
    s = setups._setup_9_1(c, "alta")
    assert not _obrigatorios_ok(s)


def test_9_2_alta_correcao_de_um_candle():
    c = _ctx(ema9_arr=[10.0, 10.2], closes=[10.5, 11.0, 10.8], close=10.8,
             last={"high": 10.9, "low": 10.6, "close": 10.8}, rsi=55)
    s = setups._setup_9_2(c, "alta")
    assert _obrigatorios_ok(s)
    assert s["gatilho"] == 10.9 and s["invalidacao"] == 10.6


def test_9_3_alta_retomada_apos_correcao():
    c = _ctx(ema9_arr=[10.0, 10.2], closes=[11.0, 10.7, 10.9],
             lows=[10.4, 10.5, 10.6], highs=[11.2, 10.9, 11.0], close=10.9,
             last={"high": 11.0, "low": 10.6, "close": 10.9})
    s = setups._setup_9_3(c, "alta")
    assert _obrigatorios_ok(s)
    assert s["gatilho"] == 11.0
    assert s["invalidacao"] == 10.5  # mínima da correção (2 últimos candles)


def test_9_2_baixa_espelhado():
    c = _ctx(ema9_arr=[10.4, 10.2], closes=[10.0, 9.6, 9.8], close=9.8,
             last={"high": 9.9, "low": 9.5, "close": 9.8}, rsi=45)
    s = setups._setup_9_2(c, "baixa")
    assert _obrigatorios_ok(s)
    assert s["gatilho"] == 9.5 and s["invalidacao"] == 9.9


# ------------------------------ IFR2 ----------------------------------------

def test_ifr2_ponta_a_ponta_sobrevenda_acima_da_mma200():
    closes = [10 + i * 0.05 for i in range(210)]      # tendência longa de alta
    closes += [closes[-1] - 0.8, closes[-1] - 1.5]    # 2 quedas fortes → RSI(2)≈0
    cs = _candles(closes)
    comp = ind.compute(cs)
    r = setups.detect_setups(cs, comp["indicators"])
    nomes = [s["nome"] for s in r["setups"]]
    assert "IFR2 (alta)" in nomes
    s = next(x for x in r["setups"] if x["nome"] == "IFR2 (alta)")
    assert s["alvoSugerido"] is not None            # máxima dos 2 candles anteriores
    assert s["gatilho"] is not None                 # setup de fechamento


def test_ifr2_nao_dispara_abaixo_da_mma200():
    closes = [30 - i * 0.05 for i in range(210)]      # tendência longa de BAIXA
    closes += [closes[-1] - 0.8, closes[-1] - 1.5]
    cs = _candles(closes)
    comp = ind.compute(cs)
    r = setups.detect_setups(cs, comp["indicators"])
    assert "IFR2 (alta)" not in [s["nome"] for s in r["setups"]]


# ------------------------------ PFR -----------------------------------------

def test_pfr_alta_ponta_a_ponta():
    closes = [10.0] * 40
    cs = _candles(closes)
    cs[-3].update({"low": 9.6, "close": 9.9, "high": 10.1, "open": 10.0})
    cs[-2].update({"low": 9.5, "close": 9.8, "high": 10.0, "open": 9.9})
    cs[-1].update({"low": 9.2, "close": 10.0, "high": 10.1, "open": 9.4})  # mínima + força
    comp = ind.compute(cs)
    r = setups.detect_setups(cs, comp["indicators"])
    s = next((x for x in r["setups"] if x["nome"].startswith("PFR (alta)")), None)
    assert s is not None and _obrigatorios_ok(s)
    assert s["gatilho"] == 10.1 and s["invalidacao"] == 9.2


# ------------------------------ 123 -----------------------------------------

def test_123_alta_estrutura_e_gatilho_no_topo_2():
    candles = [
        {"low": 10.0, "high": 11.0}, {"low": 9.0, "high": 10.5},   # fundo 1 (9.0)
        {"low": 9.8, "high": 11.0}, {"low": 10.5, "high": 12.0},   # topo 2 (12.0)
        {"low": 10.0, "high": 11.5}, {"low": 9.6, "high": 10.8},   # fundo 3 (9.6 > 9.0)
        {"low": 10.1, "high": 11.0},
    ]
    c = _ctx(candles=candles, close=10.9, sma20=10.6, sma50=10.2)
    s = setups._setup_123(c, "alta")
    assert _obrigatorios_ok(s)
    assert s["gatilho"] == 12.0 and s["invalidacao"] == 9.6


def test_123_nao_dispara_com_fundo_3_mais_baixo():
    candles = [
        {"low": 10.0, "high": 11.0}, {"low": 9.0, "high": 10.5},
        {"low": 9.8, "high": 11.0}, {"low": 10.5, "high": 12.0},
        {"low": 10.0, "high": 11.5}, {"low": 8.5, "high": 10.8},   # fundo 3 ABAIXO do 1
        {"low": 10.1, "high": 11.0},
    ]
    c = _ctx(candles=candles, close=10.9)
    s = setups._setup_123(c, "alta")
    assert not _obrigatorios_ok(s)


# ------------------------------ Ponto Contínuo ------------------------------

def test_ponto_continuo_alta_toque_na_mme21_com_adx():
    c = _ctx(adx=30.0, di_plus=25.0, di_minus=15.0, ema21=10.0, close=10.1,
             last={"low": 9.9, "high": 10.4, "close": 10.1})
    s = setups._setup_ponto_continuo(c, "alta")
    assert _obrigatorios_ok(s) and s["confluencia"] == 100
    assert s["gatilho"] == 10.4 and s["invalidacao"] == 9.9


def test_ponto_continuo_nao_dispara_sem_tendencia():
    c = _ctx(adx=15.0, di_plus=25.0, di_minus=15.0, ema21=10.0, close=10.1,
             last={"low": 9.9, "high": 10.4, "close": 10.1})
    assert not _obrigatorios_ok(setups._setup_ponto_continuo(c, "alta"))


# ------------------------------ Inside Bar ----------------------------------

def test_inside_bar_alta_gatilho_no_candle_mae():
    candles = [{"low": 10.0, "high": 12.0}, {"low": 10.5, "high": 11.5}]
    c = _ctx(candles=candles, sma20=11.0, sma50=10.0)
    s = setups._setup_inside_bar(c)
    assert _obrigatorios_ok(s) and s["lado"] == "alta"
    assert s["gatilho"] == 12.0 and s["invalidacao"] == 10.0


def test_inside_bar_nao_conta_sem_tendencia_definida():
    candles = [{"low": 10.0, "high": 12.0}, {"low": 10.5, "high": 11.5}]
    c = _ctx(candles=candles, sma20=None, sma50=None)
    assert not _obrigatorios_ok(setups._setup_inside_bar(c))


# ------------------------------ 9.4 Larry Williams --------------------------

def test_9_4_lw_alta_gatilho_na_maxima_do_candle_da_minima():
    candles = [
        {"low": 10.0, "high": 10.8}, {"low": 9.8, "high": 10.5},
        {"low": 9.5, "high": 10.3},   # mínima mais baixa (referência)
        {"low": 9.9, "high": 10.2}, {"low": 10.0, "high": 10.25},
    ]
    c = _ctx(candles=candles, sma20=10.5, sma50=10.0, close=10.1)
    s = setups._setup_9_4_lw(c, "alta")
    assert _obrigatorios_ok(s)
    assert s["gatilho"] == 10.3 and s["invalidacao"] == 9.5


# ------------------------------ integração/guardrail ------------------------

def test_todos_os_detectores_br_respeitam_shape_e_guardrail():
    closes = [10 + i * 0.05 for i in range(80)]
    cs = _candles(closes)
    comp = ind.compute(cs)
    c = setups._ctx(cs, comp["indicators"])
    for s in setups._setups_br(c):
        assert set(("nome", "lado", "criterios", "confluencia",
                    "gatilho", "invalidacao", "alvoSugerido",
                    "referencia", "backtestavel")) <= set(s)
        assert 0 <= s["confluencia"] <= 100
        assert not IMPERATIVE.search(s["nome"]), s["nome"]
        for crit in s["criterios"]:
            assert set(crit) == {"criterio", "ok", "peso", "obrigatorio"}
            assert not IMPERATIVE.search(crit["criterio"]), crit["criterio"]


def test_detect_setups_inclui_setups_br_e_mantem_vocabulario():
    closes = [10 + i * 0.05 for i in range(210)] 
    closes += [closes[-1] - 0.8, closes[-1] - 1.5]
    cs = _candles(closes)
    comp = ind.compute(cs)
    r = setups.detect_setups(cs, comp["indicators"])
    assert r["veredito"] in ("Estudar alta", "Estudar baixa", "Monitorar", "Sem setup no momento")
    assert any(s.get("backtestavel") for s in r["setups"])  # ao menos 1 setup BR ativo


# ---------------------------------------------------------------------------
# Mini-runner para ambientes SEM pytest (padrão do projeto).
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    fails = 0
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("ok " + name)
            except AssertionError as e:
                fails += 1
                print("FALHOU " + name + " :: " + str(e))
            except Exception as e:  # noqa: BLE001
                fails += 1
                print("ERRO " + name + " :: " + repr(e))
    print()
    print("TODOS OS TESTES DOS SETUPS BR PASSARAM" if fails == 0 else str(fails) + " TESTE(S) FALHARAM")
    sys.exit(0 if fails == 0 else 1)
