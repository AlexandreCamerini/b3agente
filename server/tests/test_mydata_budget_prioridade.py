"""Quick 261006-oav (2026-10-06) — classes de prioridade do orçamento mydata.

Incidente: rajada de GET /api/options/gate/* consumiu o minuto e o
POST /api/options/buy do usuário levou 502. Aqui se trava: reserva do usuário,
fatia de descoberta, teto total inalterado e o log de recusa com limite de taxa.
"""
from datetime import datetime

import pytest

from app import mydata_budget as b
from app import obslog

T = datetime(2026, 10, 6, 10, 0, tzinfo=b.BRT)


@pytest.fixture(autouse=True)
def _limpo(monkeypatch):
    b.reset()
    obslog.reset()
    b.configure_db(None, enabled=False)
    for k in ("MYDATA_QUOTA_MIN", "MYDATA_QUOTA_DIA",
              "MYDATA_RESERVA_MIN", "MYDATA_RESERVA_DIA"):
        monkeypatch.delenv(k, raising=False)
    yield
    b.reset()
    obslog.reset()


def test_fundo_para_na_reserva_e_usuario_gasta_a_reserva():
    b.debita(n=44, now=T)
    assert b.pode_gastar(1, now=T) is False
    with b.contexto(prioridade="usuario"):
        assert b.pode_gastar(2, now=T) is True
        assert b.reservar(2, now=T) is True
    assert b.snapshot(now=T)["gastoMinuto"] == 46
    assert b.pode_gastar(1, now=T) is False


def test_usuario_nao_passa_do_teto_total():
    b.debita(n=54, now=T)
    with b.contexto(prioridade="usuario"):
        assert b.pode_gastar(1, now=T) is False


def test_dia_fundo_para_em_1650_usuario_em_1800():
    T2 = datetime(2026, 10, 6, 10, 5, tzinfo=b.BRT)   # minuto limpo, mesmo dia
    b.debita(n=1650, now=T)
    assert b.pode_gastar(1, now=T2) is False
    with b.contexto(prioridade="usuario"):
        assert b.pode_gastar(1, now=T2) is True
    b.debita(n=150, now=T)
    with b.contexto(prioridade="usuario"):
        assert b.pode_gastar(1, now=T2) is False
    assert b.pode_gastar(1, now=T2) is False


def test_descoberta_limitada_a_21_por_minuto():
    with b.contexto(prioridade="descoberta"):
        for _ in range(21):
            assert b.reservar(1, now=T) is True
        assert b.reservar(1, now=T) is False
    assert b.snapshot(now=T)["gastoMinuto"] == 21
    # a rajada de descoberta não come a reserva do usuário
    with b.contexto(prioridade="usuario"):
        assert b.pode_gastar(2, now=T) is True


def test_outras_classes_nao_contam_na_fatia_de_descoberta():
    b.debita(n=30, now=T)   # fundo
    with b.contexto(prioridade="descoberta"):
        assert b.pode_gastar(1, now=T) is True
        assert b.reservar(1, now=T) is True
    assert b.snapshot(now=T)["gastoDescobertaMinuto"] == 1


def test_reserva_clamp_e_env_invalido(monkeypatch):
    monkeypatch.setenv("MYDATA_RESERVA_MIN", "100")
    assert b.reserva_min() == 54
    assert b.pode_gastar(1, now=T) is False       # fundo 0
    with b.contexto(prioridade="usuario"):
        assert b.pode_gastar(54, now=T) is True
    monkeypatch.setenv("MYDATA_RESERVA_MIN", "abc")
    assert b.reserva_min() == 10


def test_contexto_invalido_e_restaura_prioridade():
    with pytest.raises(ValueError):
        with b.contexto(prioridade="xyz"):
            pass
    assert b.prioridade_atual() == "fundo"
    with pytest.raises(RuntimeError):
        with b.contexto(prioridade="usuario", origem="x"):
            assert b.prioridade_atual() == "usuario"
            raise RuntimeError()
    assert b.prioridade_atual() == "fundo"
    assert b.origem_atual() is None


def test_reservar_com_prioridade_explicita_nao_vaza():
    b.debita(n=44, now=T)
    assert b.reservar(1, now=T) is False
    assert b.reservar(1, now=T, prioridade="usuario") is True
    assert b.prioridade_atual() == "fundo"


def test_compat_com_lambdas_monkeypatchados(monkeypatch):
    chamadas = []
    monkeypatch.setattr(b, "pode_gastar", lambda n=1, now=None: True)
    monkeypatch.setattr(b, "debita", lambda n=1, now=None: chamadas.append(n))
    assert b.reservar(1) is True
    assert chamadas == [1]


def test_log_de_recusa_com_limite_de_taxa():
    b.debita(n=44, now=T)
    for _ in range(50):
        b.registrar_recusa(2, now=T, agora=1000.0, origem="GET /x")
    ev = obslog.recent(cat="cota")
    assert len(ev) == 1
    e = ev[0]
    assert e["level"] == "warn"
    assert e["extra"]["janela"] == "minuto"
    assert e["extra"]["classe"] == "fundo"
    assert e["extra"]["origem"] == "GET /x"
    b.registrar_recusa(2, now=T, agora=1061.0, origem="GET /x")
    ev = obslog.recent(cat="cota")
    assert len(ev) == 2
    assert ev[0]["extra"]["suprimidas"] == "49"
    txt = repr(ev)
    assert "X-API-Key" not in txt and "MYDATA_API_KEY" not in txt


def test_log_indeterminada_nunca_levanta(monkeypatch):
    monkeypatch.setattr(b, "pode_gastar", lambda n=1, now=None: False)
    b.registrar_recusa(1, now=T, agora=5.0)
    ev = obslog.recent(cat="cota")
    assert ev[0]["extra"]["janela"] == "indeterminada"


def test_snapshot_mantem_chaves_e_ganha_novas():
    s = b.snapshot(now=T)
    for k in ("dia", "quotaMin", "quotaDia", "gastoMinuto", "gastoDia",
              "headerQuota", "degradado"):
        assert k in s
    assert s["reservaUsuarioMin"] == 10 and s["reservaUsuarioDia"] == 150
    assert s["tetoFundoMin"] == 44 and s["tetoFundoDia"] == 1650
    assert s["tetoDescobertaMin"] == 21 and s["gastoDescobertaMinuto"] == 0
