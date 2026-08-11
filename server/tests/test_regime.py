"""Testes do módulo regime (FASE 2 / A). Puro — sem rede, sem relógio."""
from app import regime


def _snap(close, sma200=None, sma50=None, adx=None, c63=None, c252=None, n=260,
          setups=None):
    return {
        "close": close,
        "summary": {"sma200": sma200, "sma50": sma50, "adx14": adx},
        "context": {"historyStats": {
            "candlesAvailable": n, "change63dPct": c63, "change252dPct": c252,
        }},
        "setups": setups or [],
    }


# ------------------------------ classificar --------------------------------- #

def test_tendencia_alta_confiavel():
    r = regime.classificar(_snap(30, sma200=25, adx=30))
    assert r["regime"] == "tendencia_alta"
    assert r["base"] == "sma200" and r["confiavel"] is True


def test_tendencia_baixa():
    r = regime.classificar(_snap(20, sma200=25, adx=28))
    assert r["regime"] == "tendencia_baixa"


def test_lateral_por_adx_fraco():
    r = regime.classificar(_snap(30, sma200=25, adx=15))
    assert r["regime"] == "lateral" and r["forca"] == "fraca"


def test_transicao_vira_lateral_conservador():
    r = regime.classificar(_snap(30, sma200=25, adx=22))
    assert r["regime"] == "lateral" and r["forca"] == "transicao"


def test_degrada_para_sma50_sem_janela_de_200():
    r = regime.classificar(_snap(30, sma200=None, sma50=28, adx=30, n=120))
    assert r["base"] == "sma50" and r["confiavel"] is False
    assert r["regime"] == "tendencia_alta"


def test_indefinido_sem_media_nem_adx():
    r = regime.classificar(_snap(30))
    assert r["regime"] == "indefinido"


# ------------------------------ ranquear ------------------------------------ #

def test_percentil_cross_sectional_ordena_por_momentum():
    res = [
        {"ticker": "AAAA3", "confluencia": 90, "setups": []},
        {"ticker": "BBBB3", "confluencia": 10, "setups": []},
    ]
    snaps = {
        "AAAA3": _snap(30, sma200=25, adx=30, c63=1, c252=1),    # momentum baixo
        "BBBB3": _snap(30, sma200=25, adx=30, c63=40, c252=60),  # momentum alto
    }
    out = regime.ranquear(res, snaps)
    # BBBB3 tem momentum MUITO maior — sobe, apesar da confluência menor.
    # É a inversão do eixo: aderência (confluência) não manda mais no ranking.
    assert out[0]["ticker"] == "BBBB3"


def test_gatilho_alinhado_desempata_e_pontua():
    reg_snap = _snap(30, sma200=25, adx=30, c63=10, c252=10,
                     setups=[{"nome": "Pullback à média (alta)", "lado": "alta", "confluencia": 70}])
    r = [{"ticker": "CCCC3", "confluencia": 70,
          "setups": reg_snap["setups"]}]
    out = regime.ranquear(r, {"CCCC3": reg_snap})
    assert out[0]["gatilhoAlinhado"] is True
    assert out[0]["radarScore"] >= out[0]["momentumRelPct"]


def test_setup_contra_o_regime_nao_pontua():
    reg_snap = _snap(30, sma200=25, adx=30, c63=10, c252=10,
                     setups=[{"nome": "Reversão de sobrecompra", "lado": "baixa", "confluencia": 80}])
    r = [{"ticker": "DDDD3", "confluencia": 80, "setups": reg_snap["setups"]}]
    out = regime.ranquear(r, {"DDDD3": reg_snap})
    # regime é tendência de alta; setup de baixa NÃO alinha.
    assert out[0]["gatilhoAlinhado"] is False


def test_reversao_so_alinha_em_lateral():
    reg_snap = _snap(30, sma200=25, adx=15, c63=0, c252=0,
                     setups=[{"nome": "Reversão de sobrevenda", "lado": "alta", "confluencia": 80}])
    r = [{"ticker": "EEEE3", "confluencia": 80, "setups": reg_snap["setups"]}]
    out = regime.ranquear(r, {"EEEE3": reg_snap})
    assert out[0]["regime"]["regime"] == "lateral"
    assert out[0]["gatilhoAlinhado"] is True
