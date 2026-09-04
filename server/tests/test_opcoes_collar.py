"""Fase 16, Plano 03 (LIB-03) — collar (trava protetora) como terceira
composição do motor comum de N-pernas.

Parte 1 (Task 1): gatilho de oferta do collar (parâmetro `multiperna`,
somente-nomeado) e seleção das duas pernas — quando o collar entra e quando
continua caindo em `caixa_insuficiente`/`put_protecao`/`call_coberta` de
sempre.

Parte 2 (Task 2): forma completa da proposta de collar — payoff consolidado
de 3 pernas, movimento de caixa, pernas nomeadas e manchete/didática vindas
só de `skill_ref`.

Parte 3 (Task 3): guardiões de não-regressão do default e de forma (nunca
uma estrutura de 2 pernas cabe no caminho de execução de 1 perna só).

Fixtures locais espelham `_contrato`/`_cadeia`/`_posicao` de
`test_opcoes_lastreadas_proposta.py` — mesmo padrão, arquivo novo porque o
assunto (collar) é novo.
"""
import datetime as dt
import inspect

from app import opcoes_lastreadas, skill_ref
from app.options_quant import liquidity_score

_HOJE = dt.date(2026, 8, 31)
_SPOT = 30.0


def _contrato(strike, symbol, kind, price=1.0, volume=1000, oi=1000, bid=None, ask=None):
    bid = round(price - 0.05, 2) if bid is None else bid
    ask = round(price + 0.05, 2) if ask is None else ask
    return {"contractSymbol": symbol, "optionType": kind, "strike": strike, "lastPrice": price,
            "bid": bid, "ask": ask, "volume": volume, "openInterest": oi, "impliedVolatility": 0.3}


def _cadeia(expiration=None, calls=None, puts=None, status="ok"):
    exp = expiration or (_HOJE + dt.timedelta(days=30)).isoformat()
    return {"providerStatus": status, "underlyingPrice": _SPOT, "expiration": exp,
            "expirations": [exp], "calls": calls or [], "puts": puts or []}


def _posicao(qty=300, qty_travada=0):
    return {"t": "PETR4", "qty": qty, "qtyTravada": qty_travada}


_PLANO_VENDER = {"decisao": "VENDER", "lado": "baixa"}
_PLANO_NAO_OPERAR = {"decisao": "NÃO OPERAR", "lado": None}
_PLANO_COMPRAR = {"decisao": "COMPRAR", "lado": "alta"}


# ------------------------ Parte 1: gatilho e seleção ------------------------

def test_multiperna_e_parametro_somente_nomeado_com_default_false():
    sig = inspect.signature(opcoes_lastreadas.propor)
    p = sig.parameters["multiperna"]
    assert p.kind.name == "KEYWORD_ONLY"
    assert p.default is False


def test_propor_sem_multiperna_devolve_caixa_insuficiente_como_hoje():
    calls = [_contrato(32.0, "PETR4F32", "call", price=1.0)]
    puts = [_contrato(28.0, "PETR4F28", "put", price=0.9)]
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=calls, puts=puts), _SPOT, _PLANO_VENDER,
                                  _posicao(), 50, "operador", _HOJE)
    assert r == {"proposta": None, "motivo": "caixa_insuficiente"}


def test_propor_multiperna_true_oferece_collar_quando_put_nao_cabe():
    calls = [_contrato(32.0, "PETR4F32", "call", price=1.0)]
    puts = [_contrato(28.0, "PETR4F28", "put", price=0.9)]
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=calls, puts=puts), _SPOT, _PLANO_VENDER,
                                  _posicao(), 50, "operador", _HOJE, multiperna=True)
    assert r["motivo"] == "collar"
    assert r["proposta"]["tipo"] == "collar"


def test_propor_multiperna_true_com_caixa_folgado_mantem_put_protecao():
    """O collar não rouba o caso em que a put isolada cabe no caixa.

    Re-verificado sob MULTI-01 (Fase 19): esta cadeia não tem `calls`
    (`_cadeia(puts=puts)`), então `_propor_collar()` continua devolvendo
    `None` (nenhuma call líquida acima do spot) mesmo com a chamada agora
    incondicional a `contratos < 1` — não existe segundo candidato aqui, e
    o guardião segue válido sem alteração na asserção."""
    puts = [_contrato(28.0, "PETR4F28", "put", price=0.9)]
    r = opcoes_lastreadas.propor("PETR4", _cadeia(puts=puts), _SPOT, _PLANO_VENDER,
                                  _posicao(), 100000, "operador", _HOJE, multiperna=True)
    assert r["motivo"] == "put_protecao"


def test_propor_multiperna_true_vies_de_premio_mantem_call_coberta():
    """O collar não é oferecido no viés de prêmio (plano de NÃO OPERAR)."""
    calls = [_contrato(32.0, "PETR4F32", "call", price=1.0)]
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=calls), _SPOT, _PLANO_NAO_OPERAR,
                                  _posicao(), 50, "operador", _HOJE, multiperna=True)
    assert r["motivo"] == "call_coberta"


def test_propor_multiperna_true_sem_call_liquida_volta_a_caixa_insuficiente():
    """Caixa curto e nenhuma call líquida acima do spot: nunca uma trava de
    uma perna só — volta a `caixa_insuficiente`."""
    puts = [_contrato(28.0, "PETR4F28", "put", price=0.9)]
    calls_iliquidas = [_contrato(32.0, "PETR4F32", "call", volume=0, oi=0, bid=0, ask=0)]
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=calls_iliquidas, puts=puts), _SPOT,
                                  _PLANO_VENDER, _posicao(), 50, "operador", _HOJE, multiperna=True)
    assert r == {"proposta": None, "motivo": "caixa_insuficiente"}


def test_propor_collar_credito_liquido_contratos_pelo_lastro_nao_pelo_caixa():
    """put 0,90 / call 1,00 -> -0,10 por ação (crédito): contratos vem do
    lastro (qty_livre // 100), não do caixa — sem call para financiar não
    caberia nenhum contrato com cash=50."""
    calls = [_contrato(32.0, "PETR4F32", "call", price=1.0)]
    puts = [_contrato(28.0, "PETR4F28", "put", price=0.9)]
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=calls, puts=puts), _SPOT, _PLANO_VENDER,
                                  _posicao(qty=300), 50, "operador", _HOJE, multiperna=True)
    assert r["motivo"] == "collar"
    assert r["proposta"]["contratos"] == 3
    assert r["proposta"]["qtyAcoes"] == 300


def test_propor_collar_debito_liquido_teto_do_caixa_contratos_2():
    """put 3,00 / call 2,00 -> +1,00 por ação (débito): a put isolada já
    falha com cash=250 (250 < 100*3,00), e o collar trava em 2 contratos, não
    nos 3 que o lastro permitiria (teto real do caixa, não só o caminho
    feliz do crédito)."""
    calls = [_contrato(32.0, "PETR4F32", "call", price=2.0)]
    puts = [_contrato(28.0, "PETR4F28", "put", price=3.0)]
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=calls, puts=puts), _SPOT, _PLANO_VENDER,
                                  _posicao(qty=300), 250, "operador", _HOJE, multiperna=True)
    assert r["motivo"] == "collar"
    assert r["proposta"]["contratos"] == 2
    assert r["proposta"]["qtyAcoes"] == 200


def test_propor_collar_debito_liquido_caixa_50_devolve_caixa_insuficiente():
    calls = [_contrato(32.0, "PETR4F32", "call", price=0.5)]
    puts = [_contrato(28.0, "PETR4F28", "put", price=1.5)]
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=calls, puts=puts), _SPOT, _PLANO_VENDER,
                                  _posicao(qty=300), 50, "operador", _HOJE, multiperna=True)
    assert r == {"proposta": None, "motivo": "caixa_insuficiente"}


def test_propor_collar_janela_de_prazo_continua_valendo():
    exp = (_HOJE + dt.timedelta(days=5)).isoformat()
    calls = [_contrato(32.0, "PETR4F32", "call", price=1.0)]
    puts = [_contrato(28.0, "PETR4F28", "put", price=0.9)]
    r = opcoes_lastreadas.propor("PETR4", _cadeia(expiration=exp, calls=calls, puts=puts), _SPOT,
                                  _PLANO_VENDER, _posicao(), 50, "operador", _HOJE, multiperna=True)
    assert r == {"proposta": None, "motivo": "sem_vencimento_elegivel"}


def test_propor_collar_expiration_da_proposta_e_da_cadeia():
    """As duas pernas compartilham o `expiration` da cadeia (a cadeia
    ADR-004 carrega um vencimento só)."""
    calls = [_contrato(32.0, "PETR4F32", "call", price=1.0)]
    puts = [_contrato(28.0, "PETR4F28", "put", price=0.9)]
    cadeia = _cadeia(calls=calls, puts=puts)
    r = opcoes_lastreadas.propor("PETR4", cadeia, _SPOT, _PLANO_VENDER,
                                  _posicao(qty=300), 50, "operador", _HOJE, multiperna=True)
    assert r["proposta"]["expiration"] == cadeia["expiration"]


# ------------------- Fase 19, MULTI-01: coexistência e não-regressão --------
# `propor()` deixou de escolher UMA estrutura por posição: quando put E
# collar cabem, os DOIS aparecem em `candidatos`. Esta seção prova
# coexistência, ordem travada, candidato único quando só uma estrutura cabe,
# ausência da chave `candidatos` nos negativos (compat. com os ~15 guardiões
# de igualdade exata de dict) e manchete própria por candidato (guardrail
# CVM — nenhuma composição no motor).

def test_propor_multiperna_true_com_caixa_e_call_liquida_ambos_coexistem():
    """MULTI-01: quando put E collar cabem, os DOIS aparecem em candidatos,
    put_protecao primeiro (índice 0, compat. com consumidor antigo de
    `.proposta`)."""
    calls = [_contrato(32.0, "PETR4F32", "call", price=1.0)]
    puts = [_contrato(28.0, "PETR4F28", "put", price=0.9)]
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=calls, puts=puts), _SPOT, _PLANO_VENDER,
                                  _posicao(), 100000, "operador", _HOJE, multiperna=True)
    assert [c["tipo"] for c in r["candidatos"]] == ["put_protecao", "collar"]
    assert r["proposta"] is r["candidatos"][0]  # mesmo objeto, nunca recalculado à parte
    assert r["proposta"]["tipo"] == "put_protecao"
    assert r["motivo"] == "put_protecao"


def test_propor_multiperna_false_nunca_traz_collar_mesmo_com_os_dois_cabendo():
    """A mesma cadeia/caixa do teste de coexistência acima, mas sem
    `multiperna`: a negociação de capacidade da Fase 16 continua valendo —
    `multiperna=False` nunca vê o collar, mesmo quando ele caberia."""
    calls = [_contrato(32.0, "PETR4F32", "call", price=1.0)]
    puts = [_contrato(28.0, "PETR4F28", "put", price=0.9)]
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=calls, puts=puts), _SPOT, _PLANO_VENDER,
                                  _posicao(), 100000, "operador", _HOJE)
    assert [c["tipo"] for c in r["candidatos"]] == ["put_protecao"]
    assert r["motivo"] == "put_protecao"


def test_propor_call_coberta_tem_candidato_unico():
    """O viés de prêmio (venda coberta) segue candidato único — o collar só
    é tentado no ramo `put_protecao`, nunca no de `call_coberta`."""
    calls = [_contrato(32.0, "PETR4F32", "call", price=1.0)]
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=calls), _SPOT, _PLANO_NAO_OPERAR,
                                  _posicao(), 100000, "operador", _HOJE, multiperna=True)
    assert [c["tipo"] for c in r["candidatos"]] == ["call_coberta"]
    assert r["motivo"] == "call_coberta"


def test_propor_collar_sozinho_quando_a_put_nao_cabe_no_caixa():
    """Comportamento da Fase 16 preservado, agora expresso como lista de
    um: quando a put não cabe mas o collar cabe, `candidatos` tem só o
    collar."""
    calls = [_contrato(32.0, "PETR4F32", "call", price=1.0)]
    puts = [_contrato(28.0, "PETR4F28", "put", price=0.9)]
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=calls, puts=puts), _SPOT, _PLANO_VENDER,
                                  _posicao(), 50, "operador", _HOJE, multiperna=True)
    assert [c["tipo"] for c in r["candidatos"]] == ["collar"]
    assert r["proposta"]["tipo"] == "collar"
    assert r["motivo"] == "collar"


def test_propor_negativos_nao_ganham_chave_candidatos():
    """Toda porta fechada continua dict de DOIS campos — a ausência de
    `candidatos` é DELIBERADA (compatibilidade com os ~15 guardiões de
    igualdade exata de dict em `server/tests/test_opcoes_*.py`; acrescentar
    `"candidatos": []` neles quebraria todos por nada)."""
    casos = [
        # sem_setup: leitura de alta não gera proposta de proteção nem prêmio.
        ("PETR4", _cadeia(calls=[_contrato(32.0, "PETR4F32", "call")],
                           puts=[_contrato(28.0, "PETR4F28", "put")]),
         _SPOT, _PLANO_COMPRAR, _posicao(), 100000, "sem_setup"),
        # caixa_insuficiente: put não cabe e a cadeia não tem call líquida
        # para financiar um collar (`_propor_collar` devolve None).
        ("PETR4", _cadeia(puts=[_contrato(28.0, "PETR4F28", "put", price=0.9)]),
         _SPOT, _PLANO_VENDER, _posicao(), 10, "caixa_insuficiente"),
        # sem_contrato_liquido: nenhuma put líquida na cadeia — cai antes de
        # `colar` ser sequer tentado.
        ("PETR4", _cadeia(puts=[_contrato(28.0, "PETR4F28", "put", volume=0, oi=0, bid=0, ask=0)]),
         _SPOT, _PLANO_VENDER, _posicao(), 100000, "sem_contrato_liquido"),
    ]
    for underlying, chain, spot, plano, posicao, cash, motivo_esperado in casos:
        r = opcoes_lastreadas.propor(underlying, chain, spot, plano, posicao, cash,
                                      "operador", _HOJE, multiperna=True)
        assert r["motivo"] == motivo_esperado, (motivo_esperado, r)
        assert r["proposta"] is None
        assert "candidatos" not in r


def test_cada_candidato_tem_manchete_propria_do_skill_ref():
    """Guardrail CVM: cada candidato carrega a manchete do motor verbatim —
    nenhuma composição, nenhuma manchete reaproveitada entre candidatos."""
    calls = [_contrato(32.0, "PETR4F32", "call", price=1.0)]
    puts = [_contrato(28.0, "PETR4F28", "put", price=0.9)]
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=calls, puts=puts), _SPOT, _PLANO_VENDER,
                                  _posicao(), 100000, "operador", _HOJE, multiperna=True)
    assert [c["tipo"] for c in r["candidatos"]] == ["put_protecao", "collar"]
    put_c, collar_c = r["candidatos"]

    dados_put = {
        "n": str(put_c["contratos"]), "ticker": "PETR4",
        "strike": skill_ref.num_br(put_c["strike"]),
        "premioTotal": skill_ref.num_br(put_c["premioTotal"]),
        "qtyAcoes": str(put_c["qtyAcoes"]),
    }
    dados_collar = {
        "n": str(collar_c["contratos"]), "ticker": "PETR4",
        "strikeCall": skill_ref.num_br(collar_c["strikeCall"]),
        "strikePut": skill_ref.num_br(collar_c["strikePut"]),
        "qtyAcoes": str(collar_c["qtyAcoes"]),
    }
    esperado_put = skill_ref.opcoes_lastreadas_txt("operador", "put_protecao", **dados_put)
    esperado_collar = skill_ref.opcoes_lastreadas_txt("operador", "collar", **dados_collar)

    assert put_c["manchete"] == esperado_put
    assert collar_c["manchete"] == esperado_collar
    assert put_c["manchete"] and collar_c["manchete"]
    assert put_c["manchete"] != collar_c["manchete"]


# ------------------- Parte 2: forma completa da proposta ---------------------

def _cenario_canonico(cash=50):
    calls = [_contrato(32.0, "PETR4F32", "call", price=1.0)]
    puts = [_contrato(28.0, "PETR4F28", "put", price=0.9)]
    return opcoes_lastreadas.propor("PETR4", _cadeia(calls=calls, puts=puts), _SPOT, _PLANO_VENDER,
                                     _posicao(qty=300), cash, "operador", _HOJE, multiperna=True)


def test_propor_collar_canonico_travado_dos_dois_lados():
    estrutura = _cenario_canonico()["proposta"]["estrutura"]
    assert estrutura["ganho_ilimitado"] is False
    assert estrutura["perda_ilimitada"] is False


def test_propor_collar_canonico_ganho_e_perda_maximos():
    estrutura = _cenario_canonico()["proposta"]["estrutura"]
    assert estrutura["ganho_maximo"] == 2.1
    assert estrutura["perda_maxima"] == 1.9


def test_propor_collar_canonico_breakeven():
    estrutura = _cenario_canonico()["proposta"]["estrutura"]
    assert estrutura["breakevens"] == [29.9]


def test_propor_collar_canonico_pernas_da_estrutura_3_entradas_ordem():
    pernas = _cenario_canonico()["proposta"]["estrutura"]["pernas"]
    assert len(pernas) == 3
    assert [p["tipo"] for p in pernas] == ["ACAO", "CALL", "PUT"]
    assert [p["lado"] for p in pernas] == ["compra", "venda", "compra"]


def test_propor_collar_canonico_caixa():
    r = _cenario_canonico()
    assert r["proposta"]["caixa"] == {
        "custoLiquidoUnitario": -0.1, "custoLiquidoTotal": -30.0, "fluxo": "credito",
    }


def test_propor_collar_canonico_identidade_de_contrato_unico_e_nula():
    p = _cenario_canonico()["proposta"]
    assert p["contractSymbol"] is None
    assert p["optionType"] is None
    assert p["strike"] is None
    assert p["premioUnitario"] is None
    assert p["premioTotal"] is None


def test_propor_collar_canonico_strikes_das_duas_pernas():
    p = _cenario_canonico()["proposta"]
    assert p["strikeCall"] == 32.0
    assert p["strikePut"] == 28.0


def test_propor_collar_canonico_pernas_contratos_nomeadas():
    pernas = _cenario_canonico()["proposta"]["pernasContratos"]
    assert len(pernas) == 2
    call_leg = next(p for p in pernas if p["optionType"] == "call")
    put_leg = next(p for p in pernas if p["optionType"] == "put")
    assert call_leg["contractSymbol"] == "PETR4F32"
    assert put_leg["contractSymbol"] == "PETR4F28"
    assert call_leg["lado"] == "venda"
    assert put_leg["lado"] == "compra"
    assert call_leg["strike"] == 32.0
    assert put_leg["strike"] == 28.0
    assert call_leg["premioUnitario"] == 1.0
    assert put_leg["premioUnitario"] == 0.9


def test_propor_collar_canonico_manchete_vem_do_skill_ref():
    manchete = _cenario_canonico()["proposta"]["manchete"]
    esperado = skill_ref.opcoes_lastreadas_txt(
        "operador", "collar", n="3", ticker="PETR4",
        strikeCall="32,00", strikePut="28,00", qtyAcoes="300")
    assert manchete == esperado
    assert "{" not in manchete and "}" not in manchete


def test_propor_collar_canonico_didatica_sempre_educacional():
    calls = [_contrato(32.0, "PETR4F32", "call", price=1.0)]
    puts = [_contrato(28.0, "PETR4F28", "put", price=0.9)]
    r_operador = _cenario_canonico()
    r_educacional = opcoes_lastreadas.propor(
        "PETR4", _cadeia(calls=calls, puts=puts), _SPOT, _PLANO_VENDER,
        _posicao(qty=300), 50, "educacional", _HOJE, multiperna=True)
    esperado = skill_ref.opcoes_lastreadas_txt(
        "educacional", "collar", n="3", ticker="PETR4",
        strikeCall="32,00", strikePut="28,00", qtyAcoes="300")
    assert r_operador["proposta"]["didatica"] == esperado
    assert r_educacional["proposta"]["didatica"] == esperado


def test_propor_collar_canonico_liquidez_eh_a_menor_das_duas_pernas():
    calls = [_contrato(32.0, "PETR4F32", "call", price=1.0, volume=1000, oi=1000)]
    puts = [_contrato(28.0, "PETR4F28", "put", price=0.9, volume=100, oi=100)]
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=calls, puts=puts), _SPOT, _PLANO_VENDER,
                                  _posicao(qty=300), 50, "operador", _HOJE, multiperna=True)
    liq_call = liquidity_score(1000, 1000, calls[0]["bid"], calls[0]["ask"])
    liq_put = liquidity_score(100, 100, puts[0]["bid"], puts[0]["ask"])
    menor = min(liq_call["score"], liq_put["score"])
    assert liq_put["score"] < liq_call["score"]  # a fixture escolhida realmente diferencia
    assert r["proposta"]["liquidez"]["score"] == menor


def test_propor_collar_canonico_chips_tem_4_entradas_credito():
    chaves = [c["k"] for c in _cenario_canonico()["proposta"]["chips"]]
    assert chaves == ["prazo", "strikes", "crédito líquido", "liquidez"]


def test_propor_collar_debito_usa_chip_de_custo_liquido():
    calls = [_contrato(32.0, "PETR4F32", "call", price=2.0)]
    puts = [_contrato(28.0, "PETR4F28", "put", price=3.0)]
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=calls, puts=puts), _SPOT, _PLANO_VENDER,
                                  _posicao(qty=300), 250, "operador", _HOJE, multiperna=True)
    chaves = [c["k"] for c in r["proposta"]["chips"]]
    assert "custo líquido" in chaves
    assert "crédito líquido" not in chaves


def test_propor_collar_canonico_campos_de_lote_e_prazo():
    p = _cenario_canonico()["proposta"]
    assert p["precoObjeto"] == 30.0
    assert p["qtyAcoes"] == 300
    assert p["contratos"] == 3
    assert p["diasParaVencimento"] == 30


# --------------------------- Parte 3: guardiões ------------------------------

def test_propor_multiperna_false_e_ausente_sao_identicos_em_todos_os_cenarios_ja_cobertos():
    """Nenhuma diferença silenciosa entre a chamada de hoje (sem `multiperna`)
    e a chamada explícita `multiperna=False`, em todos os cenários já
    cobertos por `test_opcoes_lastreadas_proposta.py`."""
    casos = [
        ("PETR4", {"providerStatus": "degraded"}, _SPOT, _PLANO_NAO_OPERAR,
         _posicao(), 100000, "operador", _HOJE),
        ("PETR4", _cadeia(calls=[_contrato(32.0, "PETR4F32", "call")]), _SPOT, _PLANO_NAO_OPERAR,
         None, 100000, "operador", _HOJE),
        ("PETR4", _cadeia(calls=[_contrato(32.0, "PETR4F32", "call")],
                           puts=[_contrato(28.0, "PETR4F28", "put")]), _SPOT, _PLANO_COMPRAR,
         _posicao(), 100000, "operador", _HOJE),
        ("PETR4", _cadeia(puts=[_contrato(28.0, "PETR4F28", "put")]), _SPOT, _PLANO_VENDER,
         _posicao(), 100000, "operador", _HOJE),
        ("PETR4", _cadeia(calls=[_contrato(32.0, "PETR4F32", "call")]), _SPOT, _PLANO_NAO_OPERAR,
         _posicao(), 100000, "operador", _HOJE),
        ("PETR4", _cadeia(calls=[_contrato(32.0, "PETR4F32", "call", volume=0, oi=0, bid=0, ask=0)]),
         _SPOT, _PLANO_NAO_OPERAR, _posicao(), 100000, "operador", _HOJE),
        ("PETR4", _cadeia(expiration=(_HOJE + dt.timedelta(days=5)).isoformat(),
                           calls=[_contrato(32.0, "PETR4F32", "call")]), _SPOT, _PLANO_NAO_OPERAR,
         _posicao(), 100000, "operador", _HOJE),
        ("PETR4", _cadeia(puts=[_contrato(28.0, "PETR4F28", "put")]), _SPOT, _PLANO_VENDER,
         _posicao(), 10.0, "operador", _HOJE),
    ]
    for args in casos:
        r_default = opcoes_lastreadas.propor(*args)
        r_explicito = opcoes_lastreadas.propor(*args, multiperna=False)
        assert r_default == r_explicito, args


def test_propor_collar_forma_nunca_perna_unica_quando_motivo_e_collar():
    """Guardião de forma: impede que uma estrutura de duas pernas volte a
    caber no caminho de execução de uma perna só."""
    r = _cenario_canonico()
    assert r["motivo"] == "collar"
    p = r["proposta"]
    assert p["contractSymbol"] is None
    assert len(p["pernasContratos"]) == 2
    assert len(p["estrutura"]["pernas"]) == 3
