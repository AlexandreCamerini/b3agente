"""ADR-017 (Bloco 1) — o motor consome a evidência medida.

Task 1: `detect_setups` anexa o campo informativo `historico` por setup,
lido de um provedor injetado (`set_historico_provider`), sem alterar
`_vale`/`melhor`/`veredito`/`confluencia` e sem esconder nenhum setup.

Task 2: `regime.ranquear` consome `elegivel` da janela fechada anterior como
termo novo do `radarScore` e da ordenação, sem inverter o eixo de
regime/momentum validado no ADR-016.

Sem rede, sem banco — candles sintéticos (mesmo estilo de test_setups.py /
test_setups_br.py) e dicts de setup hand-made (mesmo estilo de
test_adr017_setups_aposentados.py).
"""
from datetime import date, timedelta

import pytest

from app import indicators, regime, setups


# ------------------------------ fixtures ------------------------------------- #

@pytest.fixture(autouse=True)
def _sem_provedor_vazando_entre_testes():
    """Garante que nenhum teste herda provedor de outro (estado global)."""
    setups.set_historico_provider(None)
    yield
    setups.set_historico_provider(None)


# ------------------------------ helpers (candles) ----------------------------- #

def _mk(closes, vols=None, last_close_pos=0.9):
    """Candles sintéticos — mesmo helper de test_setups.py."""
    out = []
    d0 = date.fromisoformat("2024-01-01")
    for i, c in enumerate(closes):
        lo, hi = c * 0.985, c * 1.015
        close = c
        if i == len(closes) - 1:
            close = lo + (hi - lo) * last_close_pos
        out.append({"date": (d0 + timedelta(days=i)).isoformat(),
                    "open": round(c * 0.998, 4), "high": round(hi, 4),
                    "low": round(lo, 4), "close": round(close, 4),
                    "volume": (vols[i] if vols else 1000)})
    return out


def _detect(candles):
    cs = indicators.sanitize_candles(candles)
    full = indicators.compute(cs)
    return setups.detect_setups(cs, full["indicators"])


def _candles_rompimento():
    """Dispara 'Rompimento com volume (alta)' — setup OPERÁVEL (não aposentado)."""
    closes = [50 + (0.02 if i % 2 else -0.02) for i in range(80)] + [53.0]
    vols = [1000] * 80 + [2500]  # 2,5x a média
    return _mk(closes, vols, last_close_pos=0.95)


def _candles_setup_9_2_aposentado():
    """Dispara 'Setup 9.2 (alta)' — setup APOSENTADO (ADR-017 Bloco 0)."""
    closes = [10 + i * 0.1 for i in range(60)]
    closes.append(closes[-1] + 0.05)
    closes.append(closes[-1] - 0.15)  # correção de 1 candle
    return _mk(closes, last_close_pos=0.4)


# ------------------------------ Task 1: detect_setups ------------------------- #

def test_sem_provedor_nao_cria_chave_historico():
    r = _detect(_candles_rompimento())
    assert r["setups"], "cenário precisa detectar ao menos um setup"
    for s in r["setups"]:
        assert "historico" not in s


def test_com_provedor_anexa_historico_do_setup_correspondente():
    mapa = {"Rompimento com volume (alta)": {
        "expR": 0.18, "n": 62, "medidoAte": "2025-12-31",
        "elegivel": True, "insuficiente": False,
        "expRJanela": 0.21, "nJanela": 45, "janelaRef": "2025",
        "calculadoEm": "2026-01-05",
    }}
    setups.set_historico_provider(lambda: mapa)
    r = _detect(_candles_rompimento())
    por_nome = {s["nome"]: s for s in r["setups"]}
    assert por_nome["Rompimento com volume (alta)"]["historico"] == mapa["Rompimento com volume (alta)"]


def test_com_provedor_setup_sem_entrada_no_mapa_recebe_historico_none():
    mapa = {"Um Setup Que Não Existe": {"expR": 1.0, "n": 999}}
    setups.set_historico_provider(lambda: mapa)
    r = _detect(_candles_rompimento())
    for s in r["setups"]:
        assert s["historico"] is None  # nenhum nome detectado bate com o mapa


def test_setup_aposentado_tambem_recebe_historico():
    mapa = {"Setup 9.2 (alta)": {
        "expR": -0.22, "n": 140, "medidoAte": "2025-12-31",
        "elegivel": False, "insuficiente": False,
        "expRJanela": -0.30, "nJanela": 55, "janelaRef": "2025",
        "calculadoEm": "2026-01-05",
    }}
    setups.set_historico_provider(lambda: mapa)
    r = _detect(_candles_setup_9_2_aposentado())
    por_nome = {s["nome"]: s for s in r["setups"]}
    alvo = por_nome["Setup 9.2 (alta)"]
    assert alvo["aposentado"] is True
    assert alvo["historico"] == mapa["Setup 9.2 (alta)"]


def test_provedor_que_levanta_nao_propaga_e_setups_saem_sem_historico():
    def _boom():
        raise RuntimeError("provedor indisponível")
    setups.set_historico_provider(_boom)
    r = _detect(_candles_rompimento())  # não pode levantar
    for s in r["setups"]:
        assert "historico" not in s


def test_provedor_que_devolve_nao_dict_e_ignorado():
    setups.set_historico_provider(lambda: ["não", "é", "dict"])
    r = _detect(_candles_rompimento())
    for s in r["setups"]:
        assert "historico" not in s


def test_melhor_veredito_confluencia_identicos_com_e_sem_provedor():
    sem = _detect(_candles_rompimento())
    mapa = {"Rompimento com volume (alta)": {
        "expR": -0.10, "n": 80, "medidoAte": "2025-12-31",
        "elegivel": False, "insuficiente": False,
        "expRJanela": -0.05, "nJanela": 41, "janelaRef": "2025",
        "calculadoEm": "2026-01-05",
    }}
    setups.set_historico_provider(lambda: mapa)
    com = _detect(_candles_rompimento())
    assert sem["melhor"] == com["melhor"]
    assert sem["veredito"] == com["veredito"]
    assert sem["confluencia"] == com["confluencia"]


def test_nao_ocultacao_setup_com_elegivel_false_permanece_na_lista():
    mapa = {"Rompimento com volume (alta)": {
        "expR": -0.10, "n": 80, "medidoAte": "2025-12-31",
        "elegivel": False, "insuficiente": False,
        "expRJanela": -0.05, "nJanela": 41, "janelaRef": "2025",
        "calculadoEm": "2026-01-05",
    }}
    setups.set_historico_provider(lambda: mapa)
    r = _detect(_candles_rompimento())
    nomes = [s["nome"] for s in r["setups"]]
    assert "Rompimento com volume (alta)" in nomes


def test_set_historico_provider_none_restaura_default():
    setups.set_historico_provider(lambda: {"Rompimento com volume (alta)": {"n": 1}})
    setups.set_historico_provider(None)
    r = _detect(_candles_rompimento())
    for s in r["setups"]:
        assert "historico" not in s


# ------------------------------ Task 2: regime.ranquear ----------------------- #

def _snap(close, sma200=None, sma50=None, adx=None, c63=None, c252=None, n=260,
          setups=None):
    """Mesmo shape do helper de test_regime.py."""
    return {
        "close": close,
        "summary": {"sma200": sma200, "sma50": sma50, "adx14": adx},
        "context": {"historyStats": {
            "candlesAvailable": n, "change63dPct": c63, "change252dPct": c252,
        }},
        "setups": setups or [],
    }


def _setup_regime(nome, lado, confluencia, aposentado=False, historico=None):
    s = {"nome": nome, "lado": lado, "confluencia": confluencia, "aposentado": aposentado}
    if historico is not None:
        s["historico"] = historico
    return s


_HIST_ELEGIVEL = {"expR": 0.20, "n": 60, "medidoAte": "2025-12-31",
                   "elegivel": True, "insuficiente": False,
                   "expRJanela": 0.25, "nJanela": 50, "janelaRef": "2025",
                   "calculadoEm": "2026-01-05"}
_HIST_INELEGIVEL = {"expR": -0.20, "n": 60, "medidoAte": "2025-12-31",
                     "elegivel": False, "insuficiente": False,
                     "expRJanela": -0.25, "nJanela": 50, "janelaRef": "2025",
                     "calculadoEm": "2026-01-05"}
_HIST_INSUFICIENTE = {"expR": None, "n": 12, "medidoAte": "2025-12-31",
                       "elegivel": None, "insuficiente": True,
                       "expRJanela": None, "nJanela": 12, "janelaRef": "2025",
                       "calculadoEm": "2026-01-05"}


def test_ranquear_anexa_setup_historico_e_elegivel_true():
    s = [_setup_regime("Pullback à média (alta)", "alta", 70, historico=_HIST_ELEGIVEL)]
    snap = _snap(30, sma200=25, adx=30, c63=10, c252=10, setups=s)
    r = [{"ticker": "AAAA3", "confluencia": 70, "setups": s}]
    out = regime.ranquear(r, {"AAAA3": snap})
    assert out[0]["setupElegivel"] is True
    assert out[0]["setupHistorico"] == _HIST_ELEGIVEL


def test_elegivel_soma_dez_ao_radar_score():
    s = [_setup_regime("Pullback à média (alta)", "alta", 70, historico=_HIST_ELEGIVEL)]
    snap = _snap(30, sma200=25, adx=30, c63=10, c252=10, setups=s)
    sem_hist = [_setup_regime("Pullback à média (alta)", "alta", 70)]
    snap_sem = _snap(30, sma200=25, adx=30, c63=10, c252=10, setups=sem_hist)
    com = regime.ranquear([{"ticker": "A1", "confluencia": 70, "setups": s}], {"A1": snap})
    sem = regime.ranquear([{"ticker": "A2", "confluencia": 70, "setups": sem_hist}], {"A2": snap_sem})
    assert round(com[0]["radarScore"] - sem[0]["radarScore"], 1) == 10.0


def test_inelegivel_soma_menos_dez_ao_radar_score():
    s = [_setup_regime("Pullback à média (alta)", "alta", 70, historico=_HIST_INELEGIVEL)]
    snap = _snap(30, sma200=25, adx=30, c63=10, c252=10, setups=s)
    sem_hist = [_setup_regime("Pullback à média (alta)", "alta", 70)]
    snap_sem = _snap(30, sma200=25, adx=30, c63=10, c252=10, setups=sem_hist)
    com = regime.ranquear([{"ticker": "A1", "confluencia": 70, "setups": s}], {"A1": snap})
    sem = regime.ranquear([{"ticker": "A2", "confluencia": 70, "setups": sem_hist}], {"A2": snap_sem})
    assert round(com[0]["radarScore"] - sem[0]["radarScore"], 1) == -10.0


def test_insuficiente_nunca_penaliza():
    s = [_setup_regime("Pullback à média (alta)", "alta", 70, historico=_HIST_INSUFICIENTE)]
    snap = _snap(30, sma200=25, adx=30, c63=10, c252=10, setups=s)
    r = regime.ranquear([{"ticker": "A1", "confluencia": 70, "setups": s}], {"A1": snap})
    assert r[0]["setupElegivel"] is None


def test_setup_sem_historico_soma_zero_e_elegivel_none():
    s = [_setup_regime("Pullback à média (alta)", "alta", 70)]
    snap = _snap(30, sma200=25, adx=30, c63=10, c252=10, setups=s)
    r = regime.ranquear([{"ticker": "A1", "confluencia": 70, "setups": s}], {"A1": snap})
    assert r[0]["setupElegivel"] is None
    assert r[0]["setupHistorico"] is None


def test_ordem_elegivel_antes_de_sem_historico_antes_de_inelegivel_mesmo_tier_e_momentum():
    # Tickers em ordem alfabética INVERSA da elegibilidade esperada — se a
    # ordenação nova não existir, o desempate por ticker (critério atual)
    # produziria a ordem alfabética (AAAA/MMMM/ZZZZ), não a de elegibilidade.
    s_eleg = [_setup_regime("Pullback à média (alta)", "alta", 70, historico=_HIST_ELEGIVEL)]
    s_none = [_setup_regime("Pullback à média (alta)", "alta", 70)]
    s_inel = [_setup_regime("Pullback à média (alta)", "alta", 70, historico=_HIST_INELEGIVEL)]
    r = [
        {"ticker": "AAAA3", "confluencia": 70, "setups": s_inel},
        {"ticker": "MMMM3", "confluencia": 70, "setups": s_none},
        {"ticker": "ZZZZ3", "confluencia": 70, "setups": s_eleg},
    ]
    snaps = {
        "AAAA3": _snap(30, sma200=25, adx=30, c63=10, c252=10, setups=s_inel),
        "MMMM3": _snap(30, sma200=25, adx=30, c63=10, c252=10, setups=s_none),
        "ZZZZ3": _snap(30, sma200=25, adx=30, c63=10, c252=10, setups=s_eleg),
    }
    out = regime.ranquear(r, snaps)
    assert [x["ticker"] for x in out] == ["ZZZZ3", "MMMM3", "AAAA3"]


def test_momentum_maior_vence_elegibilidade_eixo_adr016_preservado():
    # Ativo com momentum MAIOR mas setup INELEGÍVEL continua à frente do
    # ativo com momentum MENOR e setup ELEGÍVEL — o eixo de regime/momentum
    # validado no ADR-016 não pode ser invertido pela evidência de setup.
    s_inel = [_setup_regime("Pullback à média (alta)", "alta", 70, historico=_HIST_INELEGIVEL)]
    s_eleg = [_setup_regime("Pullback à média (alta)", "alta", 70, historico=_HIST_ELEGIVEL)]
    r = [
        {"ticker": "FORTE3", "confluencia": 70, "setups": s_inel},
        {"ticker": "FRACO3", "confluencia": 70, "setups": s_eleg},
    ]
    snaps = {
        "FORTE3": _snap(30, sma200=25, adx=30, c63=60, c252=60, setups=s_inel),  # momentum alto
        "FRACO3": _snap(30, sma200=25, adx=30, c63=1, c252=1, setups=s_eleg),    # momentum baixo
    }
    out = regime.ranquear(r, snaps)
    assert out[0]["ticker"] == "FORTE3"


def test_resultado_sem_setups_operaveis_nao_levanta():
    snap = _snap(30, sma200=25, adx=30, c63=10, c252=10, setups=[])
    r = regime.ranquear([{"ticker": "A1", "confluencia": 0, "setups": []}], {"A1": snap})
    assert r[0]["setupElegivel"] is None
    assert r[0]["setupHistorico"] is None


def test_resultado_so_com_aposentado_setupElegivel_none():
    s = [_setup_regime("Setup 9.2 (alta)", "alta", 100, aposentado=True, historico=_HIST_ELEGIVEL)]
    snap = _snap(30, sma200=25, adx=30, c63=10, c252=10, setups=s)
    r = regime.ranquear([{"ticker": "A1", "confluencia": 100, "setups": s}], {"A1": snap})
    assert r[0]["setupElegivel"] is None
    assert r[0]["setupHistorico"] is None


def test_nada_e_removido_len_preservado():
    s_eleg = [_setup_regime("Pullback à média (alta)", "alta", 70, historico=_HIST_ELEGIVEL)]
    s_inel = [_setup_regime("Pullback à média (alta)", "alta", 70, historico=_HIST_INELEGIVEL)]
    r = [
        {"ticker": "AAAA3", "confluencia": 70, "setups": s_eleg},
        {"ticker": "BBBB3", "confluencia": 70, "setups": s_inel},
    ]
    snaps = {
        "AAAA3": _snap(30, sma200=25, adx=30, c63=10, c252=10, setups=s_eleg),
        "BBBB3": _snap(30, sma200=25, adx=30, c63=10, c252=10, setups=s_inel),
    }
    out = regime.ranquear(r, snaps)
    assert len(out) == len(r)
