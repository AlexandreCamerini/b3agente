"""Fase 44, Plano 02 — motor puro de leitura de estrutura por ativo.

Módulo sob teste: `server/app/estrutura_posicao.py` (`ler_estrutura`).
Sem rede, sem banco; fixtures sintéticas do caso de referência UGPA3
(collar: 1000 ações + call vendida 42 + put comprada 38).
"""
import datetime as dt

from app import estrutura_posicao as m
from app import skill_ref

V = dt.date(2026, 10, 16)
HOJE = V - dt.timedelta(days=20)
CALL_ID = "UGPAJ420"
PUT_ID = "UGPAV380"


def _acao(qty=1000, avg=39.50):
    return {"t": "UGPA3", "qty": qty, "avg": avg}


def _call(venc=V, qty=1000, avg=0.90, side="vendida", strike=42.0, id_=CALL_ID, und="UGPA3"):
    return {"id": id_, "underlying": und, "optionType": "call", "strike": strike,
            "expiration": venc.isoformat(), "qty": qty, "avg": avg, "side": side}


def _put(venc=V, qty=1000, avg=0.80, side="comprada", strike=38.0, id_=PUT_ID):
    return {"id": id_, "underlying": "UGPA3", "optionType": "put", "strike": strike,
            "expiration": venc.isoformat(), "qty": qty, "avg": avg, "side": side}


def _cadeia():
    return {
        CALL_ID: {"contractSymbol": CALL_ID, "optionType": "call", "strike": 42.0,
                  "bid": 1.00, "ask": 1.10, "lastPrice": 1.05, "volume": 50000, "openInterest": 90000},
        PUT_ID: {"contractSymbol": PUT_ID, "optionType": "put", "strike": 38.0,
                 "bid": 0.60, "ask": 0.70, "lastPrice": 0.65, "volume": 50000, "openInterest": 90000},
    }


def _ler(ops=None, posicao="default", spot=40.0, contratos=None, hoje=HOJE, modo="estudo", motivo=None):
    return m.ler_estrutura(
        [_call(), _put()] if ops is None else ops,
        "UGPA3",
        _acao() if posicao == "default" else posicao,
        spot,
        _cadeia() if contratos is None else contratos,
        hoje, modo, motivo)


def _perna(r, id_):
    return next(p for p in r["pernas"] if p["id"] == id_)


# ------------------------------ ESTR-01: pernas e classificação ------------------------------

def test_collar_ugpa3_pernas_marcacao_e_resultado():
    r = _ler()
    assert r["nome"] == "collar"
    assert len(r["pernas"]) == 2
    c, p = _perna(r, CALL_ID), _perna(r, PUT_ID)
    assert (c["tipo"], c["lado"], c["strike"], c["quantidade"]) == ("CALL", "venda", 42.0, 1000)
    assert c["vencimento"] == V.isoformat()
    assert c["premioAtual"] == 1.10 and c["origemPremio"] == "ask"
    assert p["premioAtual"] == 0.60 and p["origemPremio"] == "bid"
    assert r["acoes"]["resultado"] == 500.00
    assert c["resultado"] == -200.00
    assert p["resultado"] == -200.00
    assert r["resultado"]["total"] == 100.00
    assert r["resultado"]["incompleto"] is False
    assert r["incompleto"] is False


def test_sem_pernas_do_underlying_devolve_none_e_outro_underlying_e_ignorado():
    assert _ler(ops=[]) is None
    assert _ler(ops=[_call(und="PETR4")]) is None
    r = _ler(ops=[_call(), _call(und="PETR4", id_="PETRX")])
    assert [p["id"] for p in r["pernas"]] == [CALL_ID]


def test_classificacao_call_coberta_e_put_protecao():
    r = _ler(ops=[_call()])
    assert r["nome"] == "call_coberta"
    assert r["nomeTexto"] == skill_ref.estrutura_posicao_txt("estudo", "nome_call_coberta")
    r = _ler(ops=[_put()])
    assert r["nome"] == "put_protecao"


def test_call_comprada_fica_fora_da_biblioteca_mas_lista_pernas():
    r = _ler(ops=[_call(side=None)])  # side ausente = comprada (modelo antigo)
    assert r["nome"] is None
    assert r["nomeTexto"] == skill_ref.estrutura_posicao_txt("estudo", "nome_fora_da_biblioteca")
    assert len(r["pernas"]) == 1 and r["pernas"][0]["lado"] == "compra"


# ------------------------------ D-04: marcação ------------------------------

def test_venda_sem_ask_usa_last_com_origem_explicita():
    ch = _cadeia()
    ch[CALL_ID]["ask"] = None
    c = _perna(_ler(contratos=ch), CALL_ID)
    assert c["premioAtual"] == 1.05 and c["origemPremio"] == "last"
    assert c["origemTexto"]


def test_sem_ask_e_sem_last_premio_none_sem_mid():
    ch = _cadeia()
    ch[CALL_ID]["ask"] = None
    ch[CALL_ID]["lastPrice"] = None
    r = _ler(contratos=ch)
    c = _perna(r, CALL_ID)
    assert c["premioAtual"] is None and c["origemPremio"] is None and c["resultado"] is None
    assert r["resultado"]["total"] is None


def test_zero_negativo_e_bool_contam_como_ausentes():
    ch = _cadeia()
    ch[CALL_ID]["ask"] = 0
    ch[CALL_ID]["lastPrice"] = True
    ch[PUT_ID]["bid"] = -1.0
    ch[PUT_ID]["lastPrice"] = 0
    r = _ler(contratos=ch)
    assert _perna(r, CALL_ID)["premioAtual"] is None
    assert _perna(r, PUT_ID)["premioAtual"] is None
    assert r["incompleto"] is True


# ------------------------------ D-05: incompleto ------------------------------

def test_put_sem_contrato_na_cadeia_resultado_incompleto_sem_zero():
    ch = _cadeia()
    del ch[PUT_ID]
    r = _ler(contratos=ch)
    res = r["resultado"]
    assert res["total"] is None and res["incompleto"] is True
    assert res["pernasSemCotacao"] == [PUT_ID]
    assert res["acoes"] == 500.00
    assert res["pernasCotadas"] == -200.00
    assert res["texto"]
    assert r["incompleto"] is True


def test_spot_none_suspende_acoes_e_total():
    r = _ler(spot=None)
    assert r["acoes"]["resultado"] is None
    assert r["resultado"]["total"] is None and r["resultado"]["incompleto"] is True
    assert r["resultado"]["texto"] == skill_ref.estrutura_posicao_txt("estudo", "acao_sem_cotacao")


def test_spot_bool_ou_zero_tratado_como_none():
    assert _ler(spot=True)["resultado"]["total"] is None
    assert _ler(spot=0)["resultado"]["total"] is None


def test_sem_posicao_em_acoes_total_e_soma_das_pernas():
    r = _ler(ops=[_put()], posicao=None)
    assert r["acoes"] is None
    assert r["resultado"]["total"] == -200.00
    assert r["resultado"]["incompleto"] is False


def test_nenhum_desconhecido_vira_zero():
    ch = _cadeia()
    del ch[PUT_ID]
    ch[CALL_ID]["ask"] = ch[CALL_ID]["lastPrice"] = None
    r = _ler(contratos=ch, spot=None)
    assert r["resultado"]["total"] is None
    assert r["resultado"]["acoes"] is None
    assert r["resultado"]["pernasCotadas"] is None
    assert r["acoes"]["resultado"] is None
