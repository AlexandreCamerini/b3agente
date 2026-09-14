"""Fase 30, Plano 01 — guardiões unitários do motor puro de curadoria
(`server/app/opcoes_curadoria.py`).

Módulo PURO sob teste: sem rede, sem banco, sem LLM. Cadeia sintética montada
no próprio teste, mesmo padrão de `test_opcoes_motor.py`.
"""
import datetime as dt
import random

import pytest

from app import opcoes_curadoria, opcoes_motor, skill_ref

_SPOT = 29.0
_HOJE = dt.date(2026, 9, 13)
_EXPIRATION_OK = "2026-10-05"  # 22 dias de _HOJE — dentro de 15..60


def _contrato(symbol, kind, strike, price=1.5, volume=5000, oi=1000,
              bid=1.48, ask=1.52, **extra):
    """Contrato ADR-004, líquido por padrão (score >= 55)."""
    d = {
        "contractSymbol": symbol, "optionType": kind, "strike": strike,
        "lastPrice": price, "bid": bid, "ask": ask, "volume": volume,
        "openInterest": oi, "impliedVolatility": 0.3, "inTheMoney": False,
        "currency": "BRL", "distancePct": None,
        "greeks": {"delta": None, "gamma": None, "vega": None, "theta": None, "rho": None},
        "expiration": _EXPIRATION_OK,
    }
    d.update(extra)
    return d


def _cadeia(calls=None, puts=None, expiration=_EXPIRATION_OK, provider_status="ok"):
    return {
        "providerStatus": provider_status, "underlyingPrice": _SPOT,
        "expiration": expiration, "expirations": [expiration],
        "calls": calls if calls is not None else [], "puts": puts if puts is not None else [],
    }


def _cadeia_6_calls_liquidas():
    strikes = (30, 31, 32, 33, 34, 35)
    calls = [_contrato(f"C{s}", "call", s) for s in strikes]
    return _cadeia(calls=calls)


def _cadeia_calls_e_puts_liquidas():
    """Fase 31, Plano 01 (Task 2): cadeia com calls OTM acima do spot e puts
    OTM abaixo do spot, todas líquidas por padrão de `_contrato`."""
    calls = [_contrato(f"C{s}", "call", s, price=1.5) for s in (30, 31, 32)]
    puts = [_contrato(f"P{s}", "put", s, price=1.0) for s in (26, 27, 28)]
    return _cadeia(calls=calls, puts=puts)


def _posicao(qty=200, qty_travada=0):
    return {"t": "PETR4", "qty": qty, "qtyTravada": qty_travada, "pm": 25.0}


# ─────────────────────────────────────────────────────────────────────────
# Pureza — nenhuma chamada de rede
# ─────────────────────────────────────────────────────────────────────────

def test_modulo_nao_importa_camadas_de_rede():
    src = open(opcoes_curadoria.__file__).read()
    for banido in ("options_provider", "httpx", "candle_provider", "import db", "mcp_client"):
        assert banido not in src, f"{banido!r} não pode aparecer em opcoes_curadoria.py"


def test_filtro_de_put_existe_desde_a_fase_31_d04():
    # ATUALIZADO Fase 31, Plano 01 (D-04, 2026-09-14): este guardião se
    # chamava `test_nenhum_filtro_put_no_arquivo` e provava o OPOSTO — Fase
    # 30/D1 proibia qualquer filtro de PUT, porque o universo era só venda
    # coberta. A Fase 31 reverteu essa decisão de propósito (put de proteção
    # e collar entram na varredura) — reversão deliberada atualiza o
    # guardião com nota, não apaga a história (mesma disciplina já usada
    # noutros pontos desta base). Este teste agora prova que o filtro de put
    # PRECISA existir.
    src = open(opcoes_curadoria.__file__).read()
    linhas_sem_comentario = [l for l in src.splitlines() if not l.strip().startswith("#")]
    assert any('"tipo": "put"' in l for l in linhas_sem_comentario)


# ─────────────────────────────────────────────────────────────────────────
# candidatos_da_posicao() — portas fechadas e enumeração
# ─────────────────────────────────────────────────────────────────────────

def test_seis_calls_liquidas_n5_devolve_5_um_vencimento_strikes_distintos():
    chain = _cadeia_6_calls_liquidas()
    candidatos = opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, _SPOT, _posicao(), "operador", _HOJE, n=5)
    assert len(candidatos) == 5
    assert all(c["expiration"] == chain["expiration"] for c in candidatos)
    strikes = [c["strike"] for c in candidatos]
    assert strikes == sorted(strikes)
    assert len(set(strikes)) == len(strikes)


def test_provider_status_degradado_devolve_lista_vazia():
    chain = _cadeia_6_calls_liquidas()
    chain["providerStatus"] = "degradado"
    assert opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, _SPOT, _posicao(), "operador", _HOJE) == []


def test_chain_nao_dict_devolve_lista_vazia():
    assert opcoes_curadoria.candidatos_da_posicao(
        "PETR4", None, _SPOT, _posicao(), "operador", _HOJE) == []


@pytest.mark.parametrize("qty,esperado_vazio", [(99, True), (100, False)])
def test_qty_livre_no_limite_de_um_contrato(qty, esperado_vazio):
    chain = _cadeia_6_calls_liquidas()
    candidatos = opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, _SPOT, _posicao(qty=qty), "operador", _HOJE, n=1)
    if esperado_vazio:
        assert candidatos == []
    else:
        assert len(candidatos) == 1
        assert candidatos[0]["contratos"] == 1
        assert candidatos[0]["qtyAcoes"] == 100


def test_posicao_nao_dict_devolve_lista_vazia():
    chain = _cadeia_6_calls_liquidas()
    assert opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, _SPOT, None, "operador", _HOJE) == []


@pytest.mark.parametrize("spot_ruim", [None, 0, -5.0, True])
def test_spot_invalido_nunca_typeerror_devolve_vazio(spot_ruim):
    chain = _cadeia_6_calls_liquidas()
    assert opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, spot_ruim, _posicao(), "operador", _HOJE) == []


@pytest.mark.parametrize("dias,expiration", [
    (10, "2026-09-23"),  # 10 dias de _HOJE — abaixo de 15
    (90, "2026-12-12"),  # 90 dias de _HOJE — acima de 60
])
def test_vencimento_fora_da_janela_devolve_vazio(dias, expiration):
    chain = _cadeia(calls=[_contrato("C30", "call", 30, expiration=expiration)], expiration=expiration)
    assert opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, _SPOT, _posicao(), "operador", _HOJE) == []


def test_piso_liquidez_explicito_nao_cai_para_dificil():
    # score ~45 (DIFÍCIL, entre 30 e 55): volume baixo, spread apertado.
    contrato_dificil = _contrato("C30", "call", 30, volume=100, oi=0, bid=1.48, ask=1.52)
    chain = _cadeia(calls=[contrato_dificil])
    from app.options_quant import liquidity_score
    score = liquidity_score(contrato_dificil["volume"], contrato_dificil["openInterest"],
                             contrato_dificil["bid"], contrato_dificil["ask"])["score"]
    assert 30 <= score < 55, f"fixture não está na faixa DIFÍCIL (score={score})"
    candidatos = opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, _SPOT, _posicao(), "operador", _HOJE)
    assert candidatos == [], (
        "com liquidez_minima explícito (D5), rastrear() NÃO deve cair para a "
        "segunda passada DIFÍCIL — um contrato DIFÍCIL não pode entrar no ranking")


def test_perda_maxima_zero_descarta_candidato_sem_razao_infinita():
    # Strike muito acima do spot com prêmio alto o bastante para que a venda
    # coberta nunca feche no negativo em nenhum ponto simulado (perda_maxima
    # 0.0) — opcoes_payoff classifica isso quando o pior resultado é >= 0.
    contrato_sem_perda = _contrato("C1000", "call", 1000.0, price=950.0)
    chain = _cadeia(calls=[contrato_sem_perda])
    candidatos = opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, _SPOT, _posicao(), "operador", _HOJE)
    assert candidatos == []


def test_razao_e_o_arredondamento_esperado():
    chain = _cadeia(calls=[_contrato("C30", "call", 30, price=1.5)])
    candidatos = opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, _SPOT, _posicao(), "operador", _HOJE)
    assert len(candidatos) == 1
    c = candidatos[0]
    assert c["razao"] == round(c["premioUnitario"] / c["estrutura"]["perda_maxima"], 6)


def test_manchete_byte_igual_a_skill_ref():
    chain = _cadeia(calls=[_contrato("C30", "call", 30, price=1.5)])
    candidatos = opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, _SPOT, _posicao(), "operador", _HOJE)
    c = candidatos[0]
    dados = {
        "n": str(c["contratos"]), "ticker": "PETR4", "strike": skill_ref.num_br(c["strike"]),
        "premioTotal": skill_ref.num_br(c["premioTotal"]), "qtyAcoes": str(c["qtyAcoes"]),
    }
    esperado = skill_ref.opcoes_lastreadas_txt("operador", "call_coberta", **dados)
    assert c["manchete"] == esperado


def test_nenhuma_chamada_de_rede_cadeia_em_memoria_basta():
    # Se este teste passar sem monkeypatch/mocks de rede, a garantia de
    # pureza está satisfeita empiricamente, não só por inspeção de import.
    chain = _cadeia_6_calls_liquidas()
    candidatos = opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, _SPOT, _posicao(), "operador", _HOJE, n=3)
    assert len(candidatos) == 3


# ─────────────────────────────────────────────────────────────────────────
# put_protecao / collar — Fase 31, Plano 01, Task 2 (D-04)
# ─────────────────────────────────────────────────────────────────────────

def test_cadeia_com_puts_gera_put_protecao_e_collar_alem_de_call_coberta():
    chain = _cadeia_calls_e_puts_liquidas()
    candidatos = opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, _SPOT, _posicao(qty=200), "operador", _HOJE)
    tipos = {c["tipo"] for c in candidatos}
    assert tipos == {"call_coberta", "put_protecao", "collar"}


def test_put_protecao_tem_premio_e_razao_negativos_e_permanece_na_lista():
    chain = _cadeia_calls_e_puts_liquidas()
    candidatos = opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, _SPOT, _posicao(qty=200), "operador", _HOJE)
    puts = [c for c in candidatos if c["tipo"] == "put_protecao"]
    assert puts, "cadeia com puts líquidas precisa gerar candidatos put_protecao"
    for c in puts:
        assert c["premioUnitario"] < 0
        assert c["razao"] < 0
        assert c["premioTotal"] < 0
        # D-06: rankeado mal, mas NUNCA filtrado por prêmio negativo.
        assert isinstance(c["razao"], float)


def test_collar_tem_contractsymbol_none_strikes_pernas_e_id():
    chain = _cadeia_calls_e_puts_liquidas()
    candidatos = opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, _SPOT, _posicao(qty=200), "operador", _HOJE)
    collars = [c for c in candidatos if c["tipo"] == "collar"]
    assert collars, "cadeia com calls e puts líquidas precisa gerar candidatos collar"
    for c in collars:
        assert c["contractSymbol"] is None
        assert c["optionType"] is None
        assert c["strike"] is None
        assert c["strikeCall"] is not None
        assert c["strikePut"] is not None
        assert len(c["pernasContratos"]) == 2
        for perna in c["pernasContratos"]:
            assert perna["contractSymbol"] is not None
            assert perna["lado"] in ("venda", "compra")
        assert c["idCandidato"]
        assert c["idCandidato"] == opcoes_curadoria.id_candidato(
            "collar", "PETR4", chain["expiration"], None,
            strike_call=c["strikeCall"], strike_put=c["strikePut"])


def test_sem_put_liquida_nao_gera_put_protecao_nem_collar_mas_call_coberta_sim():
    chain = _cadeia_6_calls_liquidas()  # só calls, sem puts
    candidatos = opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, _SPOT, _posicao(qty=200), "operador", _HOJE)
    tipos = {c["tipo"] for c in candidatos}
    assert "put_protecao" not in tipos
    assert "collar" not in tipos
    assert "call_coberta" in tipos


def test_put_com_optiontype_invalido_e_pulada_demais_sobrevivem():
    # `rastrear()` só filtra por preço/liquidez, não por `optionType` — um
    # contrato com `optionType` corrompido passa a seleção e só falha dentro
    # de `perna_de_contrato` (ValueError), exatamente o cenário que o
    # try/except deste ramo precisa tolerar sem derrubar os demais
    # candidatos (mesma postura do ramo call_coberta, Task 1).
    put_ruim = _contrato("P26", "put", 26, price=1.0, optionType="invalido")
    put_boa = _contrato("P27", "put", 27, price=1.0)
    calls = [_contrato("C30", "call", 30, price=1.5)]
    chain = _cadeia(calls=calls, puts=[put_ruim, put_boa])
    candidatos = opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, _SPOT, _posicao(qty=200), "operador", _HOJE)
    puts_gerados = [c for c in candidatos if c["tipo"] == "put_protecao"]
    assert len(puts_gerados) == 1
    assert puts_gerados[0]["strike"] == 27


def test_ramo_put_protecao_e_collar_usam_a_mesma_porta_de_perda_maxima():
    # Estrutural, não numérico: a porta `perda_maxima <= 0` (mesmo código de
    # `test_perda_maxima_zero_descarta_candidato_sem_razao_infinita`) precisa
    # se repetir por ramo — call_coberta, put_protecao, collar — nunca
    # reescrita como validação frouxa/duplicada por caminho.
    src = open(opcoes_curadoria.__file__).read()
    linhas_sem_comentario = [l for l in src.splitlines() if not l.strip().startswith("#")]
    ocorrencias = sum(1 for l in linhas_sem_comentario if "perda_maxima <= 0" in l)
    assert ocorrencias >= 3


def test_nenhum_parametro_de_caixa_em_candidatos_da_posicao():
    import inspect
    assinatura = inspect.signature(opcoes_curadoria.candidatos_da_posicao)
    assert "cash" not in assinatura.parameters
    assert "caixa" not in assinatura.parameters


# ─────────────────────────────────────────────────────────────────────────
# premio_liquido_unitario() — Fase 31, Plano 01 (D-06): sinal do prêmio
# líquido, positivo quando o usuário RECEBE e negativo quando PAGA.
# ─────────────────────────────────────────────────────────────────────────

def test_premio_liquido_unitario_call_vendida_credito_positivo():
    perna = opcoes_motor.perna_de_contrato(_contrato("C30", "call", 30, price=1.5), "venda", quantidade=1)
    assert opcoes_curadoria.premio_liquido_unitario([perna]) == 1.5


def test_premio_liquido_unitario_put_comprada_debito_negativo():
    perna = opcoes_motor.perna_de_contrato(_contrato("P25", "put", 25, price=0.8), "compra", quantidade=1)
    assert opcoes_curadoria.premio_liquido_unitario([perna]) == -0.8


def test_premio_liquido_unitario_collar_sinal_da_diferenca_call_menos_put():
    perna_call = opcoes_motor.perna_de_contrato(_contrato("C30", "call", 30, price=1.5), "venda", quantidade=1)
    perna_put = opcoes_motor.perna_de_contrato(_contrato("P25", "put", 25, price=0.8), "compra", quantidade=1)
    assert opcoes_curadoria.premio_liquido_unitario([perna_call, perna_put]) == round(1.5 - 0.8, 2)


def test_premio_liquido_unitario_collar_de_debito_fica_negativo():
    # put mais cara que a call: crédito da call não cobre o débito da put —
    # resultado tem de sair negativo, e D-06 exige que isso NÃO seja filtrado.
    perna_call = opcoes_motor.perna_de_contrato(_contrato("C30", "call", 30, price=0.5), "venda", quantidade=1)
    perna_put = opcoes_motor.perna_de_contrato(_contrato("P25", "put", 25, price=1.2), "compra", quantidade=1)
    assert opcoes_curadoria.premio_liquido_unitario([perna_call, perna_put]) == round(0.5 - 1.2, 2)


def test_premio_liquido_unitario_call_coberta_refatorada_bate_com_numero_antigo():
    # A refatoração do ramo call_coberta (Task 1c) precisa devolver o MESMO
    # número que `round(contrato["lastPrice"], 2)` dava antes desta fase.
    chain = _cadeia(calls=[_contrato("C30", "call", 30, price=1.5)])
    candidatos = opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, _SPOT, _posicao(), "operador", _HOJE)
    assert candidatos[0]["premioUnitario"] == 1.5


# ─────────────────────────────────────────────────────────────────────────
# proximos_vencimentos() — Fase 31, Plano 01 (D-01): teto de vencimentos
# futuros por posição elegível.
# ─────────────────────────────────────────────────────────────────────────

def test_proximos_vencimentos_feliz_descarta_passado_ordena_teto_2():
    expirations = ["2026-09-11", "2026-10-16", "2026-11-20"]
    assert opcoes_curadoria.proximos_vencimentos(expirations, dt.date(2026, 9, 14)) == \
        ["2026-10-16", "2026-11-20"]


def test_proximos_vencimentos_tolera_item_malformado_none_e_data_invalida():
    expirations = ["2026-10-16", None, "nao-e-data", "2026-11-20"]
    assert opcoes_curadoria.proximos_vencimentos(expirations, dt.date(2026, 9, 14)) == \
        ["2026-10-16", "2026-11-20"]


def test_proximos_vencimentos_lista_vazia_devolve_vazio():
    assert opcoes_curadoria.proximos_vencimentos([], dt.date(2026, 9, 14)) == []


def test_proximos_vencimentos_entrada_nao_lista_devolve_vazio():
    assert opcoes_curadoria.proximos_vencimentos(None, dt.date(2026, 9, 14)) == []
    assert opcoes_curadoria.proximos_vencimentos("2026-10-16", dt.date(2026, 9, 14)) == []


def test_proximos_vencimentos_respeita_teto_customizado():
    expirations = ["2026-10-16", "2026-11-20", "2026-12-18"]
    assert opcoes_curadoria.proximos_vencimentos(expirations, dt.date(2026, 9, 14), teto=1) == ["2026-10-16"]


def test_proximos_vencimentos_hoje_nunca_entra_estritamente_futuro():
    expirations = ["2026-09-14", "2026-10-16"]
    assert opcoes_curadoria.proximos_vencimentos(expirations, dt.date(2026, 9, 14)) == ["2026-10-16"]


def test_proximos_vencimentos_e_funcao_pura_default_teto_bate_com_constante():
    assert opcoes_curadoria.VENCIMENTOS_POR_POSICAO == 2


# ─────────────────────────────────────────────────────────────────────────
# id_candidato() — Fase 31, Plano 01: identidade estável e total do
# candidato (desempate do collar sem contractSymbol, chave de React estável).
# ─────────────────────────────────────────────────────────────────────────

def test_id_candidato_com_contract_symbol():
    assert opcoes_curadoria.id_candidato("call_coberta", "PETR4", "2026-10-16", "C30") == \
        "call_coberta:PETR4:2026-10-16:C30"


def test_id_candidato_sem_contract_symbol_usa_par_de_strikes():
    assert opcoes_curadoria.id_candidato(
        "collar", "PETR4", "2026-10-16", None, strike_call=30.0, strike_put=25.0) == \
        "collar:PETR4:2026-10-16:30.0/25.0"


def test_id_candidato_presente_e_estavel_em_call_coberta():
    chain = _cadeia(calls=[_contrato("C30", "call", 30, price=1.5)])
    candidatos = opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, _SPOT, _posicao(), "operador", _HOJE)
    c = candidatos[0]
    esperado = opcoes_curadoria.id_candidato("call_coberta", "PETR4", chain["expiration"], "C30")
    assert c["idCandidato"] == esperado
    # estabilidade: mesma chamada, mesma entrada, mesmo resultado.
    assert opcoes_curadoria.id_candidato("call_coberta", "PETR4", chain["expiration"], "C30") == esperado


# ─────────────────────────────────────────────────────────────────────────
# opcao_a_descoberto — frase canônica em skill_ref (Fase 31, Plano 01)
# ─────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("modo", ["operador", "educacional"])
def test_opcao_a_descoberto_existe_nos_dois_registros_e_nao_cai_no_fallback(modo):
    dados = {
        "n": "1", "ticker": "PETR4", "strike": skill_ref.num_br(30.0),
        "premioTotal": skill_ref.num_br(150.0), "qtyAcoes": "100",
    }
    frase = skill_ref.opcoes_lastreadas_txt(modo, "opcao_a_descoberto", **dados)
    sem_setup = skill_ref.opcoes_lastreadas_txt(modo, "sem_setup", ticker="PETR4")
    assert frase != sem_setup
    assert "{" not in frase, f"marcador não interpolado sobrou na frase: {frase!r}"


def test_opcao_a_descoberto_chave_existe_literalmente_nos_dois_dicts():
    assert "opcao_a_descoberto" in skill_ref.OPCOES_LASTREADAS["operador"]
    assert "opcao_a_descoberto" in skill_ref.OPCOES_LASTREADAS["educacional"]


# ─────────────────────────────────────────────────────────────────────────
# rankear() — ordem total, determinística
# ─────────────────────────────────────────────────────────────────────────

def _candidato_sintetico(symbol, razao, premio_unitario=1.0):
    return {
        "tipo": "call_coberta", "ticker": "PETR4", "contractSymbol": symbol,
        "optionType": "call", "strike": 30.0, "expiration": _EXPIRATION_OK,
        "diasParaVencimento": 22, "contratos": 1, "qtyAcoes": 100,
        "premioUnitario": premio_unitario, "premioTotal": premio_unitario * 100,
        "liquidez": {"score": 60, "faixa": "NEGOCIÁVEL", "volume": 100, "spreadPct": 0.01, "aviso": None},
        "estrutura": {"ganho_maximo": 5.0, "perda_maxima": round(premio_unitario / razao, 4),
                      "breakevens": [29.0], "custo_liquido": 0, "fluxo": "credito"},
        "razao": razao, "manchete": f"manchete {symbol}", "didatica": f"didatica {symbol}",
        "precoObjeto": _SPOT,
    }


def test_rankear_9_candidatos_devolve_4_em_ordem_decrescente():
    candidatos = [_candidato_sintetico(f"C{i}", razao=float(i)) for i in range(1, 10)]
    top = opcoes_curadoria.rankear(candidatos)
    assert len(top) == opcoes_curadoria.TOPO
    razoes = [c["razao"] for c in top]
    assert razoes == sorted(razoes, reverse=True)
    assert [c["contractSymbol"] for c in top] == ["C9", "C8", "C7", "C6"]


def test_rankear_permuta_entrada_nao_muda_saida():
    base = [_candidato_sintetico(f"C{i}", razao=float(i) * 0.37 % 5 + 0.01) for i in range(1, 12)]
    esperado = [c["contractSymbol"] for c in opcoes_curadoria.rankear(base)]
    rnd = random.Random(20260913)
    for _ in range(20):
        embaralhado = list(base)
        rnd.shuffle(embaralhado)
        top = opcoes_curadoria.rankear(embaralhado)
        assert [c["contractSymbol"] for c in top] == esperado


def test_rankear_empate_desempata_por_premio_depois_contractsymbol():
    a = _candidato_sintetico("ZZZ", razao=1.0, premio_unitario=1.0)
    b = _candidato_sintetico("AAA", razao=1.0, premio_unitario=1.0)
    c = _candidato_sintetico("MMM", razao=1.0, premio_unitario=2.0)
    top = opcoes_curadoria.rankear([a, b, c])
    # c tem premioUnitario maior (2.0) -> vem primeiro; entre a e b (mesma
    # razão e mesmo prêmio), desempate por contractSymbol ascendente: AAA < ZZZ.
    assert [x["contractSymbol"] for x in top] == ["MMM", "AAA", "ZZZ"]


def test_rankear_posicao_no_ranking_sequencial_e_nao_altera_outros_campos():
    candidatos = [_candidato_sintetico(f"C{i}", razao=float(i)) for i in range(1, 6)]
    top = opcoes_curadoria.rankear(candidatos)
    assert [c["posicaoNoRanking"] for c in top] == [1, 2, 3, 4]
    originais_por_symbol = {c["contractSymbol"]: c for c in candidatos}
    for item in top:
        original = originais_por_symbol[item["contractSymbol"]]
        sem_posicao = {k: v for k, v in item.items() if k != "posicaoNoRanking"}
        assert sem_posicao == original


def test_rankear_lista_vazia():
    assert opcoes_curadoria.rankear([]) == []


# ─────────────────────────────────────────────────────────────────────────
# exigir_ranking() — recusa estrutural de pool não rankeado
# ─────────────────────────────────────────────────────────────────────────

def test_exigir_ranking_aceita_saida_de_rankear():
    candidatos = [_candidato_sintetico(f"C{i}", razao=float(i)) for i in range(1, 6)]
    top = opcoes_curadoria.rankear(candidatos)
    opcoes_curadoria.exigir_ranking(top)  # não levanta


def test_exigir_ranking_recusa_mais_de_topo_itens():
    candidatos = [_candidato_sintetico(f"C{i}", razao=float(i), ) for i in range(1, 6)]
    pool_nao_rankeado = [{**c, "posicaoNoRanking": i} for i, c in enumerate(candidatos, start=1)]
    with pytest.raises(ValueError):
        opcoes_curadoria.exigir_ranking(pool_nao_rankeado)


def test_exigir_ranking_recusa_razao_crescente():
    top = [
        {**_candidato_sintetico("A", razao=1.0), "posicaoNoRanking": 1},
        {**_candidato_sintetico("B", razao=2.0), "posicaoNoRanking": 2},
    ]
    with pytest.raises(ValueError):
        opcoes_curadoria.exigir_ranking(top)


def test_exigir_ranking_recusa_posicao_fora_de_ordem():
    top = [
        {**_candidato_sintetico("A", razao=2.0), "posicaoNoRanking": 2},
        {**_candidato_sintetico("B", razao=1.0), "posicaoNoRanking": 1},
    ]
    with pytest.raises(ValueError):
        opcoes_curadoria.exigir_ranking(top)


def test_exigir_ranking_recusa_item_sem_razao():
    item = {**_candidato_sintetico("A", razao=1.0), "posicaoNoRanking": 1}
    del item["razao"]
    with pytest.raises(ValueError):
        opcoes_curadoria.exigir_ranking([item])


def test_exigir_ranking_recusa_entrada_que_nao_e_lista():
    with pytest.raises(ValueError):
        opcoes_curadoria.exigir_ranking({"nao": "e lista"})


# ─────────────────────────────────────────────────────────────────────────
# narrativa_system() / narrativa_user()
# ─────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("modo", ["operador", "estudo"])
def test_narrativa_system_contem_principios_e_disclaimer(modo):
    texto = opcoes_curadoria.narrativa_system(modo)
    assert skill_ref.PRINCIPIOS in texto
    assert skill_ref.DISCLAIMER in texto


def test_narrativa_user_recusa_lista_fora_de_ordem_antes_de_montar_texto():
    top = [
        {**_candidato_sintetico("A", razao=1.0), "posicaoNoRanking": 2},
        {**_candidato_sintetico("B", razao=2.0), "posicaoNoRanking": 1},
    ]
    with pytest.raises(ValueError):
        opcoes_curadoria.narrativa_user(top, "operador")


def test_narrativa_user_inclui_contractsymbol_razao_e_instrucao_de_nao_reordenar():
    candidatos = [_candidato_sintetico(f"C{i}", razao=float(i)) for i in range(1, 5)]
    top = opcoes_curadoria.rankear(candidatos)
    texto = opcoes_curadoria.narrativa_user(top, "operador")
    for item in top:
        assert item["contractSymbol"] in texto
        assert skill_ref.num_br(item["razao"]) in texto
    assert "não reordene" in texto.lower() or "nao reordene" in texto.lower()
