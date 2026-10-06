"""Fase 48, Plano 04 (2026-10-05) — guardião do motor puro `opcoes_escada`.

Contas de referência (feitas à mão, por AÇÃO, depois x300):

  Put protetora — 300 ações, PM 38,00, put strike 36,00 prêmio 0,85:
    pior resultado = (36 - 38) - 0,85 = -2,85  -> perda máxima 2,85 (total 855,00)
    equilíbrio = 38,00 + 0,85 = 38,85 · piso 36,00 · teto None · ganho ilimitado
    prêmio pago = 0,85 x 300 = 255,00

  Call coberta — 300 ações, PM 38,00, call strike 40,00 prêmio 0,60:
    ganho máximo = (40 - 38) + 0,60 = 2,60 (total 780,00)
    equilíbrio = 38,00 - 0,60 = 37,40
    sem piso: ação a zero = -38 + 0,60 = -37,40 -> perda máxima 37,40 (total 11.220,00)
    prêmio recebido = 0,60 x 300 = 180,00

  Collar — 300 ações, PM 38,00, put 36,00 (0,85) + call 40,00 (0,60):
    líquido das opções = 0,60 - 0,85 = -0,25 por ação (custa 75,00 no total)
    perda máxima = 2,00 + 0,25 = 2,25 (675,00) · ganho máximo = 2,00 - 0,25 = 1,75 (525,00)
    equilíbrio = 38,00 + 0,25 = 38,25
"""
from __future__ import annotations

import pytest

from app import cartao_posicao, conceitos, kb, opcoes_curadoria, opcoes_escada, skill_ref

VENC = "2026-11-20"
POS = {"t": "PETR4", "qty": 300, "qtyTravada": 0, "avg": 38.0}

PUT_36 = {"tipo": "PUT", "lado": "compra", "strike": 36.0, "premio": 0.85, "contrato": "PETRW36"}
CALL_40 = {"tipo": "CALL", "lado": "venda", "strike": 40.0, "premio": 0.60, "contrato": "PETRK40"}


def _cand_put(strike=36.0, prem=0.85, exp=VENC):
    sym = f"PETRW{int(round(strike * 100))}"
    return {
        "tipo": "put_protecao", "ticker": "PETR4", "contractSymbol": sym, "optionType": "put",
        "strike": strike, "expiration": exp, "diasParaVencimento": 40, "contratos": 3,
        "qtyAcoes": 300, "premioUnitario": -prem, "premioTotal": -round(prem * 300, 2),
        "liquidez": {"score": 70, "negociavel": True},
        "idCandidato": opcoes_curadoria.id_candidato("put_protecao", "PETR4", exp, sym),
    }


def _cand_call(strike=40.0, prem=0.60, exp=VENC):
    sym = f"PETRK{int(round(strike * 100))}"
    return {
        "tipo": "call_coberta", "ticker": "PETR4", "contractSymbol": sym, "optionType": "call",
        "strike": strike, "expiration": exp, "diasParaVencimento": 40, "contratos": 3,
        "qtyAcoes": 300, "premioUnitario": prem, "premioTotal": round(prem * 300, 2),
        "liquidez": {"score": 60, "negociavel": True},
        "idCandidato": opcoes_curadoria.id_candidato("call_coberta", "PETR4", exp, sym),
    }


def _cand_collar(sp=36.0, pp=0.85, sc=40.0, pc=0.60, exp=VENC):
    return {
        "tipo": "collar", "ticker": "PETR4", "contractSymbol": None, "optionType": None,
        "strike": None, "strikeCall": sc, "strikePut": sp,
        "pernasContratos": [
            {"contractSymbol": "PETRK4000", "optionType": "call", "lado": "venda",
             "strike": sc, "premioUnitario": pc},
            {"contractSymbol": f"PETRW{int(sp * 100)}", "optionType": "put", "lado": "compra",
             "strike": sp, "premioUnitario": pp},
        ],
        "expiration": exp, "diasParaVencimento": 40, "contratos": 3, "qtyAcoes": 300,
        "premioUnitario": round(pc - pp, 2), "premioTotal": round((pc - pp) * 300, 2),
        "liquidez": {"score": 55, "negociavel": True},
        "idCandidato": opcoes_curadoria.id_candidato(
            "collar", "PETR4", exp, None, strike_call=sc, strike_put=sp),
    }


def _leitura(pernas, objetivo, modo="educacional", spot=38.0, indice=0):
    return opcoes_escada.leitura(pernas, 300, 38.0, spot, "PETR4", objetivo, VENC, indice, modo)


# ───────────────────────────── objetivos

def test_objetivos_tres_na_ordem_com_termos_no_texto():
    out = opcoes_escada.objetivos({"qty": 300, "qtyTravada": 0}, "educacional")
    assert [o["id"] for o in out] == ["proteger", "renda", "collar"]
    assert all(o["disponivel"] is True and o["motivo"] is None for o in out)
    for o in out:
        assert o["titulo"] == skill_ref.opcoes_escada_txt("educacional", f"objetivo_{o['id']}_titulo")
        assert o["perde"] == skill_ref.opcoes_escada_txt("educacional", f"objetivo_{o['id']}_perde")
        assert o["termos"], o["id"]
        for t in o["termos"]:
            assert set(t) == {"rotulo", "setor", "kb"}
            assert t["rotulo"] in o["descricao"], (o["id"], t["rotulo"])
            assert (t["setor"] is None) != (t["kb"] is None)
            if t["setor"] == "opc_premio":
                assert t["setor"] in conceitos.SETORES
            if t["kb"]:
                assert kb.verbete(t["kb"]) is not None, t["kb"]


def test_objetivos_lastro_travado_insuficiente_e_sem_posicao():
    travado = opcoes_escada.objetivos({"qty": 300, "qtyTravada": 300}, "educacional")
    assert all(o["disponivel"] is False for o in travado)
    assert all(o["motivo"] == skill_ref.opcoes_escada_txt("educacional", "lastro_travado")
               for o in travado)
    pouco = opcoes_escada.objetivos({"qty": 50, "qtyTravada": 0}, "operador")
    assert all(o["disponivel"] is False for o in pouco)
    assert pouco[0]["motivo"] == skill_ref.opcoes_escada_txt(
        "operador", "lastro_insuficiente", livres="50", necessarias="100")
    vazio = opcoes_escada.objetivos(None, "educacional")
    assert len(vazio) == 3 and all(o["disponivel"] is False for o in vazio)
    assert vazio[0]["motivo"] == skill_ref.opcoes_escada_txt("educacional", "hub_vazio_titulo")


# ───────────────────────────── escolher_degraus

def test_escolher_degraus_cinco_puts_pega_0_meio_ultimo():
    cands = [_cand_put(s) for s in (35.0, 36.5, 37.0, 35.5, 36.0)]  # fora de ordem de propósito
    out = opcoes_escada.escolher_degraus(cands, "proteger", VENC)
    assert [c["strike"] for c in out] == [37.0, 36.0, 35.0]  # perto do spot -> longe


def test_escolher_degraus_poucos_filtra_vencimento_e_tipo():
    assert len(opcoes_escada.escolher_degraus([_cand_put(36.0), _cand_put(35.0)], "proteger", VENC)) == 2
    mistos = [_cand_put(36.0), _cand_put(35.0, exp="2026-12-18"), _cand_call(40.0), _cand_collar()]
    out = opcoes_escada.escolher_degraus(mistos, "proteger", VENC)
    assert [c["tipo"] for c in out] == ["put_protecao"] and out[0]["strike"] == 36.0
    # dedupe por idCandidato
    assert len(opcoes_escada.escolher_degraus([_cand_put(36.0), _cand_put(36.0)], "proteger", VENC)) == 1
    assert opcoes_escada.escolher_degraus([], "renda", VENC) == []


def test_escolher_degraus_ordem_renda_crescente_collar_put_decrescente():
    calls = [_cand_call(s) for s in (42.0, 40.0, 41.0)]
    assert [c["strike"] for c in opcoes_escada.escolher_degraus(calls, "renda", VENC)] == [40.0, 41.0, 42.0]
    collars = [_cand_collar(sp=s) for s in (35.0, 37.0, 36.0)]
    out = opcoes_escada.escolher_degraus(collars, "collar", VENC)
    assert [c["strikePut"] for c in out] == [37.0, 36.0, 35.0]


# ───────────────────────────── leitura: contas de referência

def test_leitura_put_protetora_bate_com_a_conta_a_mao():
    r = _leitura([PUT_36], "proteger")
    assert r["nome"] == "degrau_proteger_0" and r["objetivo"] == "proteger"
    assert r["vencimentoTexto"] == "20/11" and r["qtdAcoes"] == 300
    assert r["total"]["perdaMaxima"] == 855.00 and r["porAcao"]["perdaMaxima"] == 2.85
    assert r["total"]["premioPago"] == 255.00 and r["porAcao"]["premioPago"] == 0.85
    assert r["total"]["ganhoMaximo"] is None and r["ilimitado"] == {"perda": False, "ganho": True}
    assert r["equilibrio"] == 38.85 and r["piso"] == 36.0 and r["teto"] is None
    assert r["total"]["premioRecebido"] is None
    assert r["total"]["liquido"] == -255.00
    assert r["strikes"] == {"put": 36.0, "call": None}


def test_leitura_call_coberta_bate_com_a_conta_a_mao():
    r = _leitura([CALL_40], "renda")
    assert r["total"]["ganhoMaximo"] == 780.00 and r["porAcao"]["ganhoMaximo"] == 2.60
    assert r["total"]["perdaMaxima"] == 11220.00 and r["porAcao"]["perdaMaxima"] == 37.40
    assert r["total"]["premioRecebido"] == 180.00 and r["total"]["liquido"] == 180.00
    assert r["equilibrio"] == 37.40 and r["piso"] is None and r["teto"] == 40.0
    assert r["ilimitado"] == {"perda": False, "ganho": False}


def test_leitura_collar_bate_com_a_conta_a_mao():
    r = _leitura([CALL_40, PUT_36], "collar")
    assert r["total"]["perdaMaxima"] == 675.00 and r["porAcao"]["perdaMaxima"] == 2.25
    assert r["total"]["ganhoMaximo"] == 525.00 and r["porAcao"]["ganhoMaximo"] == 1.75
    assert r["porAcao"]["liquido"] == -0.25 and r["total"]["liquido"] == -75.00
    assert r["equilibrio"] == 38.25 and r["piso"] == 36.0 and r["teto"] == 40.0


def test_colunas_por_objetivo():
    prot = _leitura([PUT_36], "proteger")["colunas"]
    assert [c["chave"] for c in prot] == ["perda_maxima", "custo_protecao"]
    assert prot[0]["valor"] == {"total": 855.00, "porAcao": 2.85}
    assert prot[1]["valor"] == {"total": 255.00, "porAcao": 0.85}
    renda = _leitura([CALL_40], "renda")["colunas"]
    assert [c["chave"] for c in renda] == ["ganho_maximo", "premio_recebido", "nota_sem_piso"]
    assert renda[2]["rotulo"] == skill_ref.opcoes_escada_txt("educacional", "nota_sem_piso")
    col = _leitura([CALL_40, PUT_36], "collar")["colunas"]
    assert [c["chave"] for c in col] == ["perda_maxima", "ganho_maximo", "liquido"]
    assert col[2]["rotulo"] == skill_ref.opcoes_escada_txt("educacional", "col_liquido_custa")
    assert col[2]["valor"]["total"] == 75.00  # magnitude; o rótulo diz custa/recebe


# ───────────────────────────── gráfico, marcadores, textos

def test_marcadores_put_presentes_e_ausentes_explicados():
    g = _leitura([PUT_36], "proteger")["grafico"]
    por_chave = {m["chave"]: m for m in g["marcadores"]}
    assert {c: m["n"] for c, m in por_chave.items()} == {"piso": 1, "equilibrio": 2, "perda_maxima": 4}
    assert por_chave["piso"]["preco"] == 36.0 and por_chave["piso"]["valor"]["total"] == -855.00
    assert por_chave["equilibrio"]["preco"] == 38.85 and por_chave["equilibrio"]["valor"]["total"] == 0
    assert por_chave["perda_maxima"]["preco"] == 36.0
    aus = {a["chave"]: a["texto"] for a in g["ausentes"]}
    assert set(aus) == {"teto", "ganho_maximo"}
    assert aus["teto"] == skill_ref.opcoes_escada_txt("educacional", "ausente_teto")
    assert aus["ganho_maximo"] == skill_ref.opcoes_escada_txt("educacional", "ausente_ganho_maximo")
    assert [l["n"] for l in g["legenda"]] == [1, 2, 4]
    assert {l["chave"]: (l["setor"], l["kb"]) for l in g["legenda"]} == {
        "piso": (None, "opc-piso"), "equilibrio": (None, "opc-equilibrio"),
        "perda_maxima": ("opc_perda_maxima", None)}


def test_call_coberta_sem_piso_perda_maxima_no_xmin():
    r = _leitura([CALL_40], "renda")
    g = r["grafico"]
    por_chave = {m["chave"]: m for m in g["marcadores"]}
    assert por_chave["perda_maxima"]["preco"] == g["xMin"]
    assert por_chave["perda_maxima"]["valor"]["total"] == -11220.00
    assert por_chave["ganho_maximo"]["preco"] == 40.0 and por_chave["ganho_maximo"]["n"] == 5
    assert {a["chave"]: a["texto"] for a in g["ausentes"]} == {
        "piso": skill_ref.opcoes_escada_txt("educacional", "ausente_piso")}
    assert r["fraseRisco"].startswith(skill_ref.opcoes_escada_txt(
        "educacional", "risco_pior_sem_piso", perdaTotal="11.220,00", premio="0,60"))


def test_grafico_pontos_magnitude_efeito_e_nomeados():
    r = _leitura([PUT_36], "proteger", spot=38.5)
    g = r["grafico"]
    pts = g["pontos"]
    assert 2 < len(pts) <= 241
    for p in pts:
        assert set(p) >= {"preco", "soAcoes", "comEstrutura", "diferenca", "efeito"}
        for k in ("soAcoes", "comEstrutura", "diferenca"):
            assert set(p[k]) == {"total", "porAcao"}
        assert p["diferenca"]["total"] >= 0 and p["diferenca"]["porAcao"] >= 0
        delta = round(p["comEstrutura"]["total"] - p["soAcoes"]["total"], 2)
        assert p["efeito"] == ("melhora" if delta > 0 else "reduz" if delta < 0 else "igual")
        assert p["diferenca"]["total"] == abs(delta)
    precos = [p["preco"] for p in pts]
    assert precos == sorted(set(precos))
    for nomeado in (36.0, 38.85, 38.5, 38.0):  # piso, equilíbrio, hoje, PM
        assert nomeado in precos, nomeado
    assert g["xMin"] == precos[0] and g["xMax"] == precos[-1]
    em_30 = next(p for p in pts if p["preco"] == 30.0)
    assert em_30["soAcoes"]["total"] == -2400.00 and em_30["comEstrutura"]["total"] == -855.00
    assert em_30["diferenca"]["total"] == 1545.00 and em_30["efeito"] == "melhora"
    assert pts[-1]["efeito"] == "reduz" and pts[-1]["diferenca"]["total"] == 255.00  # o prêmio


def test_grafico_reamostra_ate_241_pontos_preservando_nomeados(monkeypatch):
    grade = [round(20 + i * 0.05, 2) for i in range(1000)]
    real = cartao_posicao.cenarios_da_estrutura

    def fake(entrada, faixa, nome, spot, venc, ticker, modo):
        out = real(entrada, faixa, nome, spot, venc, ticker, modo)
        out["simulador"]["pontos"] = [{"preco": p, "resultado": 0.0, "zona": "ganho"} for p in grade]
        out["simulador"]["min"], out["simulador"]["max"] = grade[0], grade[-1]
        return out
    monkeypatch.setattr(cartao_posicao, "cenarios_da_estrutura", fake)
    g = _leitura([PUT_36], "proteger", spot=38.5)["grafico"]
    precos = [p["preco"] for p in g["pontos"]]
    assert len(precos) <= 241
    assert precos[0] == grade[0] and precos[-1] == grade[-1]
    for nomeado in (36.0, 38.85, 38.5, 38.0):
        assert nomeado in precos


def test_sem_grafico_quando_cenarios_devolve_none_mantem_numeros(monkeypatch):
    monkeypatch.setattr(cartao_posicao, "cenarios_da_estrutura", lambda *a, **k: None)
    r = _leitura([PUT_36], "proteger")
    assert r["grafico"] is None and r["motivoSemGrafico"]
    assert r["total"]["perdaMaxima"] == 855.00 and r["equilibrio"] == 38.85
    assert r["tabela"]  # alternativa textual continua nos preços nomeados


def test_premio_ausente_ou_nao_positivo_vira_none_com_motivo_nunca_zero():
    for premio in (None, 0, -0.5):
        p = dict(PUT_36, premio=premio)
        r = _leitura([p], "proteger")
        assert r["motivo"]
        assert r["total"]["perdaMaxima"] is None and r["porAcao"]["perdaMaxima"] is None
        assert r["total"]["premioPago"] is None and r["equilibrio"] is None
        assert r["grafico"] is None and r["motivoSemGrafico"]
        assert all(v is None for v in r["total"].values())


@pytest.mark.parametrize("modo", ["educacional", "operador"])
def test_frase_de_risco_traz_pior_e_melhor_caso_em_par(modo):
    for pernas, obj in (([PUT_36], "proteger"), ([CALL_40], "renda"), ([CALL_40, PUT_36], "collar")):
        f = _leitura(pernas, obj, modo=modo)["fraseRisco"]
        assert "Pior caso" in f and "Melhor caso" in f and "Equilíbrio" in f, (obj, f)
    f = _leitura([CALL_40, PUT_36], "collar", modo=modo)["fraseRisco"]
    assert "675,00" in f and "525,00" in f and "38,25" in f and "20/11" in f
    assert skill_ref.opcoes_escada_txt(modo, "risco_melhor_sem_teto") in _leitura(
        [PUT_36], "proteger", modo=modo)["fraseRisco"]


def test_termos_e_aria_e_tabela():
    r = _leitura([PUT_36], "proteger")
    t = r["termos"]
    assert t["opc_premio"] == {"ticker": "PETR4", "strike": 36.0, "premio": 0.85,
                               "premioTotal": 255.0, "qtd": 300, "venc": "20/11", "estado": "pago"}
    assert t["opc_perda_maxima"] == {"ticker": "PETR4", "piso": 36.0, "perdaTotal": 855.0,
                                     "perdaAcao": 2.85, "premio": 0.85, "qtd": 300,
                                     "venc": "20/11", "estado": "com_piso"}
    assert set(t["opc_premio"]) <= set(conceitos.CONCEITOS["opc-premio"]["campos"])
    assert set(t["opc_perda_maxima"]) <= set(conceitos.CONCEITOS["opc-perda-maxima"]["campos"])
    aria = r["grafico"]["aria"]
    assert set(aria) == {"total", "porAcao"}
    assert "PETR4" in aria["total"] and "300" in aria["total"] and "855,00" in aria["total"]
    assert "Por ação" in aria["porAcao"]
    precos = [l["preco"] for l in r["tabela"]]
    assert precos == sorted(set(precos)) and 36.0 in precos and 38.85 in precos
    sem_piso = _leitura([CALL_40], "renda")["termos"]["opc_perda_maxima"]
    assert sem_piso["estado"] == "sem_piso" and "piso" not in sem_piso


# ───────────────────────────── degrau_do_candidato

def test_degrau_do_candidato_copia_execucao_sem_recalcular():
    for cand, obj in ((_cand_put(), "proteger"), (_cand_call(), "renda"), (_cand_collar(), "collar")):
        d = opcoes_escada.degrau_do_candidato(cand, 1, obj, POS, 38.0, "PETR4", "educacional")
        assert d["id"] == cand["idCandidato"]
        assert d["nome"] == f"degrau_{obj}_1"
        assert d["rotulo"] == skill_ref.opcoes_escada_txt("educacional", f"degrau_{obj}_1")
        ex = d["execucao"]
        assert ex["executavel"] is True and ex["tipo"] == cand["tipo"]
        assert ex["contractSymbol"] == cand["contractSymbol"] and ex["expiration"] == VENC
        assert ex["contratos"] == 3 and ex["qtyAcoes"] == 300
        assert ex["idCandidato"] == cand["idCandidato"]
        assert ex["pernasContratos"] == cand.get("pernasContratos")
        assert d["liquidez"] == cand["liquidez"]
    d = opcoes_escada.degrau_do_candidato(_cand_collar(), 0, "collar", POS, 38.0, "PETR4", "operador")
    assert d["total"]["perdaMaxima"] == 675.00 and d["strikes"] == {"put": 36.0, "call": 40.0}


def test_pernas_do_candidato():
    assert opcoes_escada.pernas_do_candidato(_cand_call()) == [
        {"tipo": "CALL", "lado": "venda", "strike": 40.0, "premio": 0.60, "contrato": "PETRK4000"}]
    assert opcoes_escada.pernas_do_candidato(_cand_put()) == [
        {"tipo": "PUT", "lado": "compra", "strike": 36.0, "premio": 0.85, "contrato": "PETRW3600"}]
    c = opcoes_escada.pernas_do_candidato(_cand_collar())
    assert {(p["tipo"], p["lado"]) for p in c} == {("CALL", "venda"), ("PUT", "compra")}


# ───────────────────────────── matriz (celulas_da_cadeia) e barras

def _cadeia():
    puts = [{"contrato": f"PETRW{int(s * 100)}", "tipo": "put", "strike": s, "premio": p}
            for s, p in ((39.0, 1.9), (37.0, 1.1), (36.5, 0.95), (36.0, 0.85), (35.5, 0.7),
                         (35.0, 0.55), (34.0, 0.3))]
    calls = [{"contrato": f"PETRK{int(s * 100)}", "tipo": "call", "strike": s, "premio": p}
             for s, p in ((40.0, 0.6), (41.0, 0.35), (42.0, 0.2), (37.0, 1.4))]
    return puts, calls


def test_celulas_da_cadeia_proteger_mesma_regua():
    puts, calls = _cadeia()
    cel = opcoes_escada.celulas_da_cadeia(puts, calls, 38.0, POS, "proteger", VENC, "PETR4", "educacional")
    assert len(cel) == 3
    # puts <= spot, decrescente, 5: 37; 36,5; 36; 35,5; 35 -> índices 0, 2, 4
    assert [c["id"] for c in cel] == [
        opcoes_curadoria.id_candidato("put_protecao", "PETR4", VENC, f"PETRW{s}")
        for s in (3700, 3600, 3500)]
    assert [c["nome"] for c in cel] == ["degrau_proteger_0", "degrau_proteger_1", "degrau_proteger_2"]
    c = cel[1]
    assert c["total"]["perdaMaxima"] == 855.00 and c["porAcao"]["perdaMaxima"] == 2.85
    assert c["equilibrio"] == 38.85 and c["ilimitado"]["ganho"] is True and c["motivo"] is None
    assert "grafico" not in c


def test_celulas_da_cadeia_renda_collar_pula_sem_premio_e_faltantes():
    puts, calls = _cadeia()
    ren = opcoes_escada.celulas_da_cadeia(puts, calls, 38.0, POS, "renda", VENC, "PETR4", "educacional")
    assert [c["total"]["ganhoMaximo"] for c in ren] == [780.00, 1005.00, 1260.00]
    assert ren[0]["id"].endswith("PETRK4000")  # call OTM de menor strike (37 é ITM, fora)
    col = opcoes_escada.celulas_da_cadeia(puts, calls, 38.0, POS, "collar", VENC, "PETR4", "educacional")
    assert col[1]["id"] == opcoes_curadoria.id_candidato(
        "collar", "PETR4", VENC, None, strike_call=40.0, strike_put=36.0)
    assert col[1]["total"]["perdaMaxima"] == 675.00
    # contrato sem prêmio é pulado; < 3 -> posições faltantes None com motivo
    so_um = [dict(puts[3]), dict(puts[2], premio=None)]
    cel = opcoes_escada.celulas_da_cadeia(so_um, calls, 38.0, POS, "proteger", VENC, "PETR4", "operador")
    assert len(cel) == 3 and cel[0]["id"] and cel[1]["id"] is None and cel[2]["id"] is None
    assert cel[1]["motivo"] and cel[1]["total"] is None and cel[2]["porAcao"] is None
    # qtd = (livres // 100) * 100
    pos2 = {"t": "PETR4", "qty": 350, "qtyTravada": 0, "avg": 38.0}
    c2 = opcoes_escada.celulas_da_cadeia(puts, calls, 38.0, pos2, "proteger", VENC, "PETR4", "educacional")
    assert c2[1]["total"]["perdaMaxima"] == 855.00


def test_normalizar_barras_fracao_por_coluna():
    d = [{"colunas": [{"chave": "perda_maxima", "valor": {"total": 400.0, "porAcao": 4.0}},
                      {"chave": "custo_protecao", "valor": {"total": 100.0, "porAcao": 1.0}}]},
         {"colunas": [{"chave": "perda_maxima", "valor": {"total": 200.0, "porAcao": 2.0}},
                      {"chave": "custo_protecao", "valor": {"total": None, "porAcao": None}}]}]
    out = opcoes_escada.normalizar_barras(d)
    assert out is d
    assert [c["fracao"] for c in d[0]["colunas"]] == [1.0, 1.0]
    assert d[1]["colunas"][0]["fracao"] == 0.5 and d[1]["colunas"][1]["fracao"] is None


def test_constantes_e_pureza():
    assert opcoes_escada.OBJETIVOS == ("proteger", "renda", "collar")
    assert opcoes_escada.TIPO_DO_OBJETIVO == {
        "proteger": "put_protecao", "renda": "call_coberta", "collar": "collar"}
    a = _leitura([CALL_40, PUT_36], "collar")
    assert a == _leitura([CALL_40, PUT_36], "collar")  # determinístico


# ───────────────────────────── Fase 48 gap G-01 (2026-10-05)
# motivo_sem_candidato: distingue "nenhum vencimento lido na janela 15-60 dias"
# de "há vencimento elegível mas sem estrutura montável". Piso/teto não mudam.
import datetime as _dt

_HOJE = _dt.date(2026, 10, 5)


def _iso(dias):
    return (_HOJE + _dt.timedelta(days=dias)).isoformat()


def test_motivo_vencimentos_curtos_sem_vencimento_elegivel():
    r = opcoes_escada.motivo_sem_candidato([_iso(4), _iso(11)], _HOJE, "educacional", "ITUB4")
    assert r["chave"] == "sem_vencimento_elegivel"
    assert "ITUB4" in r["texto"] and "09/10, 16/10" in r["texto"]
    assert "15" in r["texto"] and "60" in r["texto"]
    assert r["dica"] == skill_ref.opcoes_escada_txt("educacional", "sem_vencimento_elegivel_dica")


def test_motivo_com_vencimento_elegivel_mantem_sem_estrutura():
    r = opcoes_escada.motivo_sem_candidato([_iso(4), _iso(30)], _HOJE, "educacional", "ITUB4")
    assert r["chave"] == "sem_estrutura"
    assert r["texto"] == skill_ref.opcoes_escada_txt("educacional", "sem_estrutura", ticker="ITUB4")
    assert r["dica"] == skill_ref.opcoes_escada_txt("educacional", "sem_estrutura_dica")


def test_motivo_acima_do_teto():
    r = opcoes_escada.motivo_sem_candidato([_iso(75)], _HOJE, "educacional", "ITUB4")
    assert r["chave"] == "sem_vencimento_elegivel"


@pytest.mark.parametrize("dias", [15, 60])
def test_motivo_limites_inclusivos(dias):
    r = opcoes_escada.motivo_sem_candidato([_iso(dias)], _HOJE, "educacional", "ITUB4")
    assert r["chave"] == "sem_estrutura"


@pytest.mark.parametrize("entrada", [[], None, ["xx", 3]])
def test_motivo_entrada_malformada_nunca_levanta(entrada):
    r = opcoes_escada.motivo_sem_candidato(entrada, _HOJE, "educacional", "ITUB4")
    assert r["chave"] == "sem_vencimento_elegivel"
    assert "—" in r["texto"]


def test_motivo_modo_operador_e_desconhecido():
    r = opcoes_escada.motivo_sem_candidato([_iso(4)], _HOJE, "operador", "ITUB4")
    assert r["texto"] == skill_ref.opcoes_escada_txt(
        "operador", "sem_vencimento_elegivel", ticker="ITUB4", vencimentos="09/10", min=15, max=60)
    r2 = opcoes_escada.motivo_sem_candidato([_iso(4)], _HOJE, "xyz", "ITUB4")
    assert r2["chave"] == "sem_vencimento_elegivel" and r2["texto"]
