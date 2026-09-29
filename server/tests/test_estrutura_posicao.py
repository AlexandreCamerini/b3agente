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


# ------------------------------ ESTR-03: faixa no vencimento ------------------------------

def _txt(chave, modo="estudo", **d):
    return skill_ref.estrutura_posicao_txt(modo, chave, **d)


def test_faixa_collar_ugpa3_bate_com_a_conta_pelos_strikes():
    r = _ler()
    f = r["faixa"]
    assert r["motivoFaixa"] is None
    assert f["piso"] == 38.0 and f["teto"] == 42.0
    assert f["perdaMaxima"] == 1400.0 and f["ganhoMaximo"] == 2600.0
    assert f["breakevens"] == [39.4]
    assert f["qtdBase"] == 1000
    assert len(f["textos"]) == 2
    assert "38,00" in r["stopTexto"]
    assert r["descoberta"] is False


def test_faixa_call_coberta_sem_piso():
    r = _ler(ops=[_call()])
    f = r["faixa"]
    assert f["piso"] is None and f["teto"] == 42.0
    assert f["perdaMaxima"] == round((39.50 - 0.90) * 1000, 2)
    assert _txt("faixa_sem_piso", perdaMaxima=skill_ref.num_br(f["perdaMaxima"])) in f["textos"]
    assert r["stopTexto"] is None


def test_faixa_put_protecao_sem_teto():
    r = _ler(ops=[_put()])
    f = r["faixa"]
    assert f["teto"] is None and f["ganhoMaximo"] is None and f["piso"] == 38.0
    assert _txt("faixa_sem_teto") in f["textos"]


def test_fora_da_biblioteca_sem_faixa():
    r = _ler(ops=[_call(side=None)])
    assert r["faixa"] is None and r["motivoFaixa"] == "fora_da_biblioteca"
    assert r["motivoFaixaTexto"]


def test_vencimentos_divergentes_sem_faixa_e_estado_pelo_mais_proximo():
    v2 = V + dt.timedelta(days=30)
    r = _ler(ops=[_call(venc=V), _put(venc=v2)])
    assert r["faixa"] is None and r["motivoFaixa"] == "vencimentos_diferentes"
    assert len(r["pernas"]) == 2
    assert V.strftime("%d/%m/%Y") in r["motivoFaixaTexto"] and v2.strftime("%d/%m/%Y") in r["motivoFaixaTexto"]
    assert r["vencimentoReferencia"] == V.isoformat()
    assert r["diasParaVencimento"] == 20


def test_descoberta_put_excedente_faixa_na_parte_coberta():
    r = _ler(ops=[_put(qty=1000)], posicao=_acao(qty=500))
    assert r["descoberta"] is True
    assert r["faixa"]["qtdBase"] == 500
    assert r["faixa"]["perdaMaxima"] == round((39.5 - 38 + 0.8) * 500, 2)
    assert "500" in r["descobertaTexto"]


def test_call_vendida_acima_das_acoes_perna_sem_lastro():
    r = _ler(ops=[_call(qty=1000)], posicao=_acao(qty=500))
    assert r["faixa"] is None and r["motivoFaixa"] == "perna_vendida_sem_lastro"
    assert r["descoberta"] is True and r["descobertaTexto"]
    assert "500" in r["motivoFaixaTexto"]


def test_sem_acoes_sem_faixa_e_total_e_soma_das_pernas():
    r = _ler(ops=[_put()], posicao=None)
    assert r["faixa"] is None and r["motivoFaixa"] == "sem_acoes"
    assert r["acoes"] is None and r["resultado"]["total"] == -200.00


def test_perfil_levantando_valueerror_vira_dados_insuficientes():
    r = _ler(posicao=_acao(avg=0))
    assert r["faixa"] is None and r["motivoFaixa"] == "dados_insuficientes"


# ------------------------------ ESTR-04: estados ------------------------------

def test_estado_vigente():
    r = _ler()
    assert r["estado"] == "vigente" and r["diasParaVencimento"] == 20
    assert r["estadoTexto"] == _txt("estado_vigente", vencimento=V.strftime("%d/%m/%Y"), dias=20)


def test_estado_vigente_sem_data():
    o1, o2 = _call(), _put()
    o1["expiration"] = o2["expiration"] = None
    r = _ler(ops=[o1, o2])
    assert r["estado"] == "vigente" and r["diasParaVencimento"] is None
    assert r["vencimentoReferencia"] is None
    assert r["estadoTexto"] == _txt("estado_vigente_sem_data")


def test_estado_ate_5_dias_inclui_o_dia_do_vencimento():
    assert _ler(hoje=V - dt.timedelta(days=5))["estado"] == "ate_5_dias"
    assert _ler(hoje=V)["estado"] == "ate_5_dias"
    assert _ler(hoje=V - dt.timedelta(days=6))["estado"] == "vigente"


def test_estado_exercicio_provavel_call_e_put_estrito():
    r = _ler(spot=43.0)
    assert r["estado"] == "exercicio_provavel"
    assert "42,00" in r["estadoTexto"] and "43,00" in r["estadoTexto"]
    assert _ler(spot=37.0)["estado"] == "exercicio_provavel"
    assert _ler(spot=42.0)["estado"] == "vigente"   # estrito
    assert _ler(spot=38.0)["estado"] == "vigente"   # estrito


def test_estado_exercicio_provavel_vence_ate_5_dias():
    assert _ler(spot=43.0, hoje=V - dt.timedelta(days=2))["estado"] == "exercicio_provavel"


def test_estado_premio_indisponivel_vence_exercicio_e_prazo():
    ch = _cadeia()
    del ch[PUT_ID]
    r = _ler(contratos=ch, spot=43.0, hoje=V - dt.timedelta(days=2))
    assert r["estado"] == "premio_indisponivel"
    assert PUT_ID in r["estadoTexto"]


def test_estado_vencida_vence_tudo():
    ch = _cadeia()
    del ch[PUT_ID]
    r = _ler(contratos=ch, spot=43.0, hoje=V + dt.timedelta(days=1))
    assert r["estado"] == "vencida" and r["diasParaVencimento"] == -1
    assert r["estadoTexto"] == _txt("estado_vencida", vencimento=V.strftime("%d/%m/%Y"))


def test_estado_precedencia_ate_5_dias_sobre_vigente_sem_itm():
    assert _ler(hoje=V - dt.timedelta(days=1), spot=40.0)["estado"] == "ate_5_dias"


# ------------------------------ ESTR-05: aberta_sem_proposta e encerrar ------------------------------

def test_aberta_sem_proposta_por_sem_mercado():
    ch = _cadeia()
    ch[CALL_ID].update(volume=0, openInterest=0, bid=None)
    r = _ler(contratos=ch)
    assert r["abertaSemProposta"] is True and r["motivoSemProposta"] == "sem_mercado"
    assert r["nome"] == "collar" and len(r["pernas"]) == 2   # a estrutura nunca some
    assert r["estado"] == "vigente"                            # eixo separado


def test_aberta_sem_proposta_por_motivo_informado_pela_rota():
    r = _ler(motivo="premio_indisponivel", modo="operador")
    assert r["abertaSemProposta"] is True
    assert r["motivoSemProposta"] == "premio_indisponivel"
    frase = skill_ref.opcoes_lastreadas_txt("operador", "premio_indisponivel", ticker="UGPA3")
    assert r["motivoSemPropostaTexto"] == _txt("aberta_sem_proposta", modo="operador", motivo=frase)


def test_sem_motivo_e_com_mercado_nao_e_aberta_sem_proposta():
    r = _ler()
    assert r["abertaSemProposta"] is False and r["motivoSemProposta"] is None


def test_encerrar_permitido_no_caso_base():
    r = _ler()
    assert r["encerrar"] == {"permitido": True, "motivo": None, "texto": None}
    assert all(p["encerrar"]["permitido"] for p in r["pernas"])


def test_encerrar_vencida():
    r = _ler(hoje=V + dt.timedelta(days=1))
    assert r["encerrar"]["permitido"] is False and r["encerrar"]["motivo"] == "vencida"
    assert r["encerrar"]["texto"]
    assert all(p["encerrar"]["motivo"] == "vencida" for p in r["pernas"])


def test_encerrar_bloqueado_sem_premio_cita_o_id():
    ch = _cadeia()
    del ch[PUT_ID]
    r = _ler(contratos=ch)
    assert r["encerrar"]["permitido"] is False and r["encerrar"]["motivo"] == "premio_indisponivel"
    assert PUT_ID in r["encerrar"]["texto"]
    assert _perna(r, PUT_ID)["encerrar"]["permitido"] is False
    assert _perna(r, CALL_ID)["encerrar"]["permitido"] is True


def test_encerrar_exige_last_mesmo_com_bid_ask():
    ch = _cadeia()
    ch[CALL_ID]["lastPrice"] = None   # a rota de fechar executa pelo lastPrice
    r = _ler(contratos=ch)
    assert r["encerrar"]["permitido"] is False and r["encerrar"]["motivo"] == "premio_indisponivel"
    assert _perna(r, CALL_ID)["premioAtual"] == 1.10   # marcação segue por ask


def test_liquidez_por_perna_usa_a_escala_do_gate():
    r = _ler()
    liq = _perna(r, CALL_ID)["liquidez"]
    assert set(liq) == {"score", "faixa"} and liq["faixa"] == "NEGOCIÁVEL"
    ch = _cadeia()
    del ch[PUT_ID]
    assert _perna(_ler(contratos=ch), PUT_ID)["liquidez"] is None


# ------------------------------ modo ------------------------------

def test_modo_estudo_e_operador_usam_ramos_distintos():
    e, o = _ler(modo="estudo"), _ler(modo="operador")
    d = V.strftime("%d/%m/%Y")
    assert e["estadoTexto"] == _txt("estado_vigente", "educacional", vencimento=d, dias=20)
    assert o["estadoTexto"] == _txt("estado_vigente", "operador", vencimento=d, dias=20)
    assert e["estadoTexto"] != o["estadoTexto"]
