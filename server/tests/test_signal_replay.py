"""ADR-017 (Decisão 2, "Reprodutibilidade") — o replay determinístico e a
barreira tripla (promovidos de `scripts/backtest_sinal.py`) vivem AGORA em
`server/app/signal_replay.py`, fonte única que o bootstrap (Plano 03) e o
hook diário (Plano 04) vão consumir.

`sinais_do_ticker` orquestra `indicators`/`regime`/`setups` — a mecânica de
DETECÇÃO de setup já é travada em `test_setups.py`; aqui `setups.detect_setups`
e `setups.plano_do_resultado` são monkeypatchados para tornar a orquestração
determinística sem reengenhar uma série que dispare um setup real (redundante
com o que test_setups.py já garante). A barreira tripla (`avaliar`) é testada
com sinais e candles construídos diretamente — é a lógica NOVA/promovida que
este arquivo precisa travar.

Tudo offline, candles sintéticos construídos no próprio teste.
"""
from datetime import date, timedelta

import pytest

from app import setups, signal_replay


# --------------------------------------------------------------------------- #
# sinais_do_ticker
# --------------------------------------------------------------------------- #

def _serie_trending(n=115, start=50.0, passo=0.1):
    out = []
    d0 = date.fromisoformat("2024-01-01")
    for i in range(n):
        close = start + i * passo
        out.append({"date": (d0 + timedelta(days=i)).isoformat(),
                    "open": round(close - passo / 2, 4), "high": round(close + 0.3, 4),
                    "low": round(close - 0.3, 4), "close": round(close, 4),
                    "volume": 1000 + i})
    return out


def _fake_detect(bloco, ind_slice):
    return {"veredito": "Estudar alta", "confluencia": 80,
            "setups": [{"nome": "Setup Fake", "lado": "alta", "confluencia": 80}]}


def _fake_plano(sres, close=None):
    return {"decisao": setups.DECISAO_COMPRAR, "setup": "Setup Fake", "lado": "alta",
            "tipo": "a mercado (fake)", "entrada": close, "stop": close - 1.0,
            "alvo1": close + 1.0, "alvo2": close + 2.0, "rr2": 2.0}


def test_sinais_do_ticker_com_tendencia_devolve_sinal_com_todas_as_chaves(monkeypatch):
    monkeypatch.setattr(setups, "detect_setups", _fake_detect)
    monkeypatch.setattr(setups, "plano_do_resultado", _fake_plano)
    cs = _serie_trending()
    sinais = signal_replay.sinais_do_ticker("TESTE", cs, dias=5, horizonte=10, janela=90)
    assert len(sinais) >= 1
    esperado = {"ticker", "data", "t", "setup", "lado", "confluencia", "tipo",
                "entrada", "stop", "alvo1", "alvo2", "rr2", "regime"}
    for s in sinais:
        assert esperado <= set(s.keys())
        assert s["ticker"] == "TESTE"
        assert s["setup"] == "Setup Fake"
        assert s["lado"] == "alta"


def test_serie_curta_demais_devolve_lista_vazia():
    cs = _serie_trending(n=50)  # bem abaixo de janela(90)+horizonte(10)+10
    sinais = signal_replay.sinais_do_ticker("TESTE", cs, dias=5, horizonte=10, janela=90)
    assert sinais == []


# --------------------------------------------------------------------------- #
# avaliar — barreira tripla
# --------------------------------------------------------------------------- #

def _candle(d, high, low, close):
    return {"date": d, "high": high, "low": low, "close": close}


def _janela_dias(n, d0="2024-06-01"):
    base = date.fromisoformat(d0)
    return [(base + timedelta(days=i)).isoformat() for i in range(n)]


def test_avaliar_toca_alvo_antes_do_stop():
    dias = _janela_dias(6)
    sinal = {"entrada": 100.0, "stop": 95.0, "alvo1": 110.0, "lado": "alta",
             "tipo": "a mercado (fake)", "t": 0}
    cs = [
        _candle(dias[0], 101, 99, 100),      # t=0, sinal
        _candle(dias[1], 108, 99, 105),      # sem toque
        _candle(dias[2], 111, 98, 109),      # bate alvo (hi>=110), stop nao (lo>95)
        _candle(dias[3], 112, 90, 91),
        _candle(dias[4], 112, 90, 91),
        _candle(dias[5], 112, 90, 91),
    ]
    r = signal_replay.avaliar(sinal, cs, "alvo1", horizonte=5)
    assert r["resultado"] == "alvo"
    assert r["r"] == round(10.0 / 5.0, 3)
    assert r["dataResolucao"] == dias[2]


def test_avaliar_toca_stop():
    dias = _janela_dias(6)
    sinal = {"entrada": 100.0, "stop": 95.0, "alvo1": 110.0, "lado": "alta",
             "tipo": "a mercado (fake)", "t": 0}
    cs = [
        _candle(dias[0], 101, 99, 100),
        _candle(dias[1], 108, 99, 105),
        _candle(dias[2], 109, 94, 96),   # bate stop (lo<=95)
        _candle(dias[3], 112, 90, 91),
        _candle(dias[4], 112, 90, 91),
        _candle(dias[5], 112, 90, 91),
    ]
    r = signal_replay.avaliar(sinal, cs, "alvo1", horizonte=5)
    assert r["resultado"] == "stop"
    assert r["r"] == -1.0
    assert r["dataResolucao"] == dias[2]


def test_avaliar_mesma_barra_toca_stop_e_alvo_resolve_a_favor_do_stop():
    dias = _janela_dias(6)
    sinal = {"entrada": 100.0, "stop": 95.0, "alvo1": 110.0, "lado": "alta",
             "tipo": "a mercado (fake)", "t": 0}
    cs = [
        _candle(dias[0], 101, 99, 100),
        _candle(dias[1], 112, 93, 100),  # bate stop E alvo na MESMA barra
        _candle(dias[2], 112, 90, 91),
        _candle(dias[3], 112, 90, 91),
        _candle(dias[4], 112, 90, 91),
        _candle(dias[5], 112, 90, 91),
    ]
    r = signal_replay.avaliar(sinal, cs, "alvo1", horizonte=5)
    assert r["resultado"] == "stop"
    assert r["r"] == -1.0


def test_avaliar_plano_nao_a_mercado_sem_toque_do_gatilho_devolve_sem_gatilho():
    dias = _janela_dias(6)
    sinal = {"entrada": 100.0, "stop": 95.0, "alvo1": 110.0, "lado": "alta",
             "tipo": "no rompimento do gatilho", "t": 0}
    cs = [
        _candle(dias[0], 99, 97, 98),
        _candle(dias[1], 99, 97, 98),   # nunca toca 100 (entrada/gatilho)
        _candle(dias[2], 99, 97, 98),
        _candle(dias[3], 99, 97, 98),
        _candle(dias[4], 99, 97, 98),
        _candle(dias[5], 99, 97, 98),
    ]
    r = signal_replay.avaliar(sinal, cs, "alvo1", horizonte=5)
    assert r == {"resultado": "sem_gatilho", "r": None, "dataResolucao": None}


def test_avaliar_a_mercado_abre_barreira_na_primeira_barra_sem_exigir_toque():
    dias = _janela_dias(6)
    # entrada NUNCA tocada pelos highs da janela (todos < 100) — se exigisse
    # toque do gatilho (como o ramo não-a-mercado), seria sem_gatilho; sendo
    # "a mercado", abre mesmo assim e resolve pelo close final (expira, pois
    # os preços ficam sempre entre o stop e o alvo).
    sinal = {"entrada": 100.0, "stop": 90.0, "alvo1": 130.0, "lado": "alta",
             "tipo": "a mercado (gatilho já rompido, dentro da zona)", "t": 0}
    cs = [
        _candle(dias[0], 96, 94, 95),
        _candle(dias[1], 97, 95, 96),
        _candle(dias[2], 98, 96, 97),
        _candle(dias[3], 99, 97, 98),
        _candle(dias[4], 99.5, 97.5, 98.5),
        _candle(dias[5], 99.8, 97.8, 99),   # ultimo candle da janela
    ]
    r = signal_replay.avaliar(sinal, cs, "alvo1", horizonte=5)
    assert r["resultado"] == "expirou"  # nunca toca stop(90) nem alvo(130)
    assert r["dataResolucao"] == dias[5]


def test_avaliar_expira_sem_tocar_nada():
    dias = _janela_dias(6)
    sinal = {"entrada": 100.0, "stop": 90.0, "alvo1": 130.0, "lado": "alta",
             "tipo": "a mercado (fake)", "t": 0}
    cs = [
        _candle(dias[0], 101, 99, 100),
        _candle(dias[1], 103, 100, 102),
        _candle(dias[2], 104, 101, 103),
        _candle(dias[3], 105, 102, 104),
        _candle(dias[4], 106, 103, 105),
        _candle(dias[5], 107, 104, 105),  # close final = 105
    ]
    r = signal_replay.avaliar(sinal, cs, "alvo1", horizonte=5)
    assert r["resultado"] == "expirou"
    assert r["r"] == round((105.0 - 100.0) / 10.0, 3)
    assert r["dataResolucao"] == dias[5]


def test_avaliar_lado_vendido_inverte_sinal_do_r_na_expiracao():
    dias = _janela_dias(6)
    sinal = {"entrada": 100.0, "stop": 110.0, "alvo1": 70.0, "lado": "baixa",
             "tipo": "a mercado (fake)", "t": 0}
    cs = [
        _candle(dias[0], 101, 99, 100),
        _candle(dias[1], 103, 97, 99),
        _candle(dias[2], 104, 96, 98),
        _candle(dias[3], 105, 95, 97),
        _candle(dias[4], 106, 94, 96),
        _candle(dias[5], 107, 93, 95),  # close final = 95 (abaixo da entrada)
    ]
    r = signal_replay.avaliar(sinal, cs, "alvo1", horizonte=5)
    assert r["resultado"] == "expirou"
    # venda: ganho = entrada - fim = 100 - 95 = 5; risco = |100-110| = 10
    assert r["r"] == round(5.0 / 10.0, 3)


def test_avaliar_sem_horizonte_cheio_devolve_none():
    dias = _janela_dias(3)
    sinal = {"entrada": 100.0, "stop": 95.0, "alvo1": 110.0, "lado": "alta",
             "tipo": "a mercado (fake)", "t": 0}
    cs = [_candle(d, 101, 99, 100) for d in dias]  # só 2 barras após t=0, horizonte pede 5
    r = signal_replay.avaliar(sinal, cs, "alvo1", horizonte=5)
    assert r == {"resultado": None, "r": None, "dataResolucao": None}


def test_avaliar_alvo_ausente_devolve_none():
    sinal = {"entrada": 100.0, "stop": 95.0, "alvo1": None, "lado": "alta",
             "tipo": "a mercado (fake)", "t": 0}
    r = signal_replay.avaliar(sinal, [], "alvo1", horizonte=5)
    assert r == {"resultado": None, "r": None, "dataResolucao": None}


# --------------------------------------------------------------------------- #
# agregar
# --------------------------------------------------------------------------- #

def test_agregar_mantem_sem_gatilho_fora_do_denominador():
    linhas = [
        {"resultado": "alvo", "r": 2.0},
        {"resultado": "stop", "r": -1.0},
        {"resultado": "stop", "r": -1.0},
        {"resultado": "expirou", "r": 0.3},
        {"resultado": "sem_gatilho", "r": None},
        {"resultado": "sem_gatilho", "r": None},
    ]
    agg = signal_replay.agregar(linhas)
    assert agg["n"] == 4
    assert agg["naoAcionados"] == 2
    assert agg["stops"] == 2
    assert agg["alvos"] == 1
    assert agg["expirou"] == 1
    assert agg["expectanciaR"] == round((2.0 - 1.0 - 1.0 + 0.3) / 4, 3)


def test_agregar_lista_vazia():
    assert signal_replay.agregar([]) == {"n": 0, "naoAcionados": 0}


# --------------------------------------------------------------------------- #
# replay — ponto de entrada único
# --------------------------------------------------------------------------- #

def test_replay_devolve_uma_linha_por_sinal_avaliavel(monkeypatch):
    dias = _janela_dias(20)
    cs = [_candle(d, 101 + i, 99 + i, 100 + i) for i, d in enumerate(dias)]

    def _fake_sinais(ticker, candles, dias_, horizonte=10, janela=252):
        return [
            # sinal 1: resolve como "alvo" — deve aparecer no replay
            {"ticker": ticker, "data": dias[0], "t": 0, "setup": "S", "lado": "alta",
             "confluencia": 80, "tipo": "a mercado (fake)", "entrada": 100.0,
             "stop": 95.0, "alvo1": 108.0, "alvo2": 120.0, "rr2": 2.0, "regime": "x"},
            # sinal 2: t no fim da série, sem horizonte cheio — avaliar devolve
            # resultado None e replay precisa descartar essa linha
            {"ticker": ticker, "data": dias[-1], "t": len(candles) - 1, "setup": "S",
             "lado": "alta", "confluencia": 80, "tipo": "a mercado (fake)",
             "entrada": 100.0, "stop": 95.0, "alvo1": 108.0, "alvo2": 120.0,
             "rr2": 2.0, "regime": "x"},
        ]

    monkeypatch.setattr(signal_replay, "sinais_do_ticker", _fake_sinais)
    out = signal_replay.replay("TESTE", cs, dias=5, horizonte=5, janela=10, alvo_campo="alvo1")
    assert len(out) == 1
    assert out[0]["resultado"] in ("alvo", "stop", "expirou", "sem_gatilho")
    assert out[0]["ticker"] == "TESTE"
    assert "dataResolucao" in out[0]
