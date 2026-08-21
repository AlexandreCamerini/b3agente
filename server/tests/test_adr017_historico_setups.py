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
