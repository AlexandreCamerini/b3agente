"""server/tests/test_put_lifecycle_decisao.py — guardião da máquina de
decisão PURA de `put_lifecycle.py` (Fase 11, Plano 01, Task 2).

Prova de comportamento: `decidir` cobre as 5 transições do ROADMAP, todo
estado que devolve é destino válido em `put_suggestions.TRANSICOES`, os 5
estados são alcançáveis por construção, o intrínseco vem de
`agent.intrinseco_opcao` (não de fórmula paralela), e `forma_adr003` é
estruturalmente incapaz de virar posição real (sem `qty`).
"""
from app import put_lifecycle, put_suggestions


def _linha(**overrides):
    linha = {
        "id": 1,
        "estado": "armada",
        "contrato": "PETRR100",
        "ticker": "PETR4",
        "strike": 30.0,
        "vencimento": "2026-09-19",
        "estiloExercicio": "americano",
        "precoEntrada": None,
        "premio": 1.2,
    }
    linha.update(overrides)
    return linha


# --------------------------------------------------------------------------- #
# forma_adr003
# --------------------------------------------------------------------------- #

def test_forma_adr003_mapeia_campos_e_forca_option_type_put():
    linha = _linha()
    forma = put_lifecycle.forma_adr003(linha)
    assert forma["id"] == "PETRR100"
    assert forma["underlying"] == "PETR4"
    assert forma["optionType"] == "put"
    assert forma["strike"] == 30.0
    assert forma["expiration"] == "2026-09-19"


def test_forma_adr003_nunca_contem_qty():
    linha = _linha(precoEntrada=1.2)
    forma = put_lifecycle.forma_adr003(linha)
    assert "qty" not in forma


def test_forma_adr003_option_type_forcado_mesmo_se_linha_disser_outro():
    linha = _linha()
    linha["optionType"] = "call"  # nunca lido — optionType é sempre "put"
    forma = put_lifecycle.forma_adr003(linha)
    assert forma["optionType"] == "put"


# --------------------------------------------------------------------------- #
# intrinseco — reuso literal de agent.intrinseco_opcao (PUTLIFE-03)
# --------------------------------------------------------------------------- #

def test_intrinseco_reusa_agent_intrinseco_opcao_strike_maior_que_spot():
    assert put_lifecycle.intrinseco({"strike": 30.0}, 28.0) == 2.0


def test_intrinseco_nunca_negativo_quando_spot_maior_que_strike():
    assert put_lifecycle.intrinseco({"strike": 30.0}, 33.0) == 0.0


def test_intrinseco_none_com_strike_ou_spot_invalidos():
    assert put_lifecycle.intrinseco({"strike": None}, 28.0) is None
    assert put_lifecycle.intrinseco({"strike": 30.0}, None) is None
    assert put_lifecycle.intrinseco({"strike": -5.0}, 28.0) is None
    assert put_lifecycle.intrinseco({"strike": 30.0}, -1.0) is None


# --------------------------------------------------------------------------- #
# resolver_spots
# --------------------------------------------------------------------------- #

def test_resolver_spots_sem_candles_devolve_tudo_none():
    spots = put_lifecycle.resolver_spots([], "2026-09-19", "2026-09-10")
    assert spots == {
        "spotAtual": None, "dataSpotAtual": None,
        "spotLiquidacao": None, "dataSpotLiquidacao": None,
    }


def test_resolver_spots_spot_atual_e_o_ultimo_candle_ate_hoje():
    candles = [
        {"date": "2026-09-08", "close": 29.0},
        {"date": "2026-09-09", "close": 28.5},
        {"date": "2026-09-10", "close": 28.0},
        {"date": "2026-09-11", "close": 27.5},  # depois de "hoje", não conta
    ]
    spots = put_lifecycle.resolver_spots(candles, "2026-09-19", "2026-09-10")
    assert spots["spotAtual"] == 28.0
    assert spots["dataSpotAtual"] == "2026-09-10"


def test_resolver_spots_liquidacao_e_o_primeiro_candle_apos_vencimento_feriado():
    candles = [
        {"date": "2026-09-18", "close": 27.0},
        {"date": "2026-09-21", "close": 26.5},  # 1º pregão após vencimento 19/09 (fds)
        {"date": "2026-09-22", "close": 26.0},
    ]
    spots = put_lifecycle.resolver_spots(candles, "2026-09-19", "2026-09-22")
    assert spots["spotLiquidacao"] == 26.5
    assert spots["dataSpotLiquidacao"] == "2026-09-21"


def test_resolver_spots_sem_candle_alcancando_vencimento_devolve_none():
    candles = [{"date": "2026-09-10", "close": 28.0}]
    spots = put_lifecycle.resolver_spots(candles, "2026-09-19", "2026-09-10")
    assert spots["spotLiquidacao"] is None
    assert spots["dataSpotLiquidacao"] is None


def test_resolver_spots_pula_candle_malformado_sem_abortar():
    candles = [
        "nao é dict",
        {"close": 28.0},              # sem date
        {"date": "2026-09-10", "close": "ruim"},  # close não numérico
        {"date": "2026-09-11", "close": -1.0},    # close <= 0
        {"date": "2026-09-12", "close": 27.0},
    ]
    spots = put_lifecycle.resolver_spots(candles, "2026-09-19", "2026-09-12")
    assert spots["spotAtual"] == 27.0
    assert spots["dataSpotAtual"] == "2026-09-12"


# --------------------------------------------------------------------------- #
# decidir — as 5 transições do ROADMAP
# --------------------------------------------------------------------------- #

def test_decidir_linha_terminal_nunca_avanca():
    for estado in put_suggestions.TERMINAIS:
        estado_novo, campos, motivo = put_lifecycle.decidir(
            _linha(estado=estado), "2026-09-10", {}
        )
        assert estado_novo is None
        assert campos == {}
        assert motivo == "terminal"


def test_decidir_armada_vencida_expira_sem_uso():
    linha = _linha(estado="armada", vencimento="2026-09-10")
    estado_novo, campos, motivo = put_lifecycle.decidir(linha, "2026-09-10", {})
    assert estado_novo == "expirada_sem_uso"
    assert campos == {}
    assert motivo == "venceu sem execução"
    assert "pnl_por_acao" not in campos
    assert "motivo_fechamento" not in campos


def test_decidir_armada_com_premio_executa_simulada():
    linha = _linha(estado="armada", vencimento="2026-09-19", premio=1.2)
    estado_novo, campos, motivo = put_lifecycle.decidir(linha, "2026-09-10", {})
    assert estado_novo == "executada_simulada"
    assert campos == {"executada_em": "2026-09-10", "preco_entrada": 1.2}
    assert motivo == ""


def test_decidir_armada_sem_premio_nunca_inventa_preco():
    for premio_ruim in (None, 0, -1.5, "ruim"):
        linha = _linha(estado="armada", vencimento="2026-09-19", premio=premio_ruim)
        estado_novo, campos, motivo = put_lifecycle.decidir(linha, "2026-09-10", {})
        assert estado_novo is None
        assert campos == {}
        assert motivo == "sem prêmio de entrada"


def test_decidir_executada_vencida_com_liquidacao_fecha():
    linha = _linha(estado="executada_simulada", vencimento="2026-09-19",
                    strike=30.0, precoEntrada=1.2)
    spots = {"spotLiquidacao": 28.0, "dataSpotLiquidacao": "2026-09-19"}
    estado_novo, campos, motivo = put_lifecycle.decidir(linha, "2026-09-19", spots)
    assert estado_novo == "fechada"
    assert campos["preco_fechamento"] == 2.0
    assert campos["motivo_fechamento"] == "vencimento"
    assert campos["pnl_por_acao"] == 0.8  # 2.0 - 1.2
    assert campos["spot_marcacao"] == 28.0
    assert campos["intrinseco_marcacao"] == 2.0
    assert campos["marcada_em"] == "2026-09-19"
    assert campos["fechada_em"] == "2026-09-19"
    assert campos["pendente_desde"] is None
    assert motivo == ""


def test_decidir_monitorada_vencida_com_liquidacao_fecha_tambem():
    linha = _linha(estado="monitorada", vencimento="2026-09-19",
                    strike=30.0, precoEntrada=1.2)
    spots = {"spotLiquidacao": 33.0, "dataSpotLiquidacao": "2026-09-19"}
    estado_novo, campos, motivo = put_lifecycle.decidir(linha, "2026-09-19", spots)
    assert estado_novo == "fechada"
    assert campos["preco_fechamento"] == 0.0
    assert campos["pnl_por_acao"] == -1.2  # perda total do prêmio (ADR-005)


def test_decidir_executada_vencida_sem_liquidacao_pendencia():
    linha = _linha(estado="executada_simulada", vencimento="2026-09-19", precoEntrada=1.2)
    estado_novo, campos, motivo = put_lifecycle.decidir(
        linha, "2026-09-19", {"spotLiquidacao": None, "dataSpotLiquidacao": None}
    )
    assert estado_novo is None
    assert campos == {}
    assert motivo == "sem preço de liquidação"


def test_decidir_executada_nao_vencida_com_spot_marca_monitorada():
    linha = _linha(estado="executada_simulada", vencimento="2026-09-19",
                    strike=30.0, precoEntrada=1.2)
    spots = {"spotAtual": 29.0, "dataSpotAtual": "2026-09-10"}
    estado_novo, campos, motivo = put_lifecycle.decidir(linha, "2026-09-10", spots)
    assert estado_novo == "monitorada"
    assert campos["spot_marcacao"] == 29.0
    assert campos["intrinseco_marcacao"] == 1.0
    assert campos["marcada_em"] == "2026-09-10"
    assert motivo == ""


def test_decidir_monitorada_nao_vencida_sem_spot_pendencia():
    linha = _linha(estado="monitorada", vencimento="2026-09-19", precoEntrada=1.2)
    estado_novo, campos, motivo = put_lifecycle.decidir(
        linha, "2026-09-10", {"spotAtual": None, "dataSpotAtual": None}
    )
    assert estado_novo is None
    assert campos == {}
    assert motivo == "sem preço do ativo-objeto"


def test_decidir_nunca_levanta_com_strike_premio_vencimento_malformados():
    linha = _linha(estado="armada", vencimento=None, premio="ruim", strike=None)
    estado_novo, campos, motivo = put_lifecycle.decidir(linha, "2026-09-10", {})
    assert estado_novo is None
    assert isinstance(campos, dict)
    assert isinstance(motivo, str)


# --------------------------------------------------------------------------- #
# Alcançabilidade dos 5 estados + validade contra TRANSICOES
# --------------------------------------------------------------------------- #

def test_todo_estado_devolvido_por_decidir_e_destino_valido_em_transicoes():
    casos = [
        (_linha(estado="armada", vencimento="2026-09-10"), "2026-09-10", {}),
        (_linha(estado="armada", vencimento="2026-09-19", premio=1.2), "2026-09-10", {}),
        (_linha(estado="executada_simulada", vencimento="2026-09-19", strike=30.0,
                 precoEntrada=1.2), "2026-09-19",
         {"spotLiquidacao": 28.0, "dataSpotLiquidacao": "2026-09-19"}),
        (_linha(estado="executada_simulada", vencimento="2026-09-19", strike=30.0,
                 precoEntrada=1.2), "2026-09-10", {"spotAtual": 29.0, "dataSpotAtual": "2026-09-10"}),
        (_linha(estado="monitorada", vencimento="2026-09-19", strike=30.0,
                 precoEntrada=1.2), "2026-09-10", {"spotAtual": 29.0, "dataSpotAtual": "2026-09-10"}),
    ]
    for linha, hoje, spots in casos:
        estado_novo, _campos, _motivo = put_lifecycle.decidir(linha, hoje, spots)
        assert estado_novo in put_suggestions.ESTADOS
        assert estado_novo in put_suggestions.TRANSICOES[linha["estado"]]


def test_os_5_estados_do_roadmap_sao_todos_alcancaveis():
    alcancados = set()

    _, _, _ = put_lifecycle.decidir(
        _linha(estado="armada", vencimento="2026-09-10"), "2026-09-10", {})
    alcancados.add("expirada_sem_uso")

    estado_novo, _, _ = put_lifecycle.decidir(
        _linha(estado="armada", vencimento="2026-09-19", premio=1.2), "2026-09-10", {})
    assert estado_novo == "executada_simulada"
    alcancados.add("executada_simulada")

    estado_novo, _, _ = put_lifecycle.decidir(
        _linha(estado="executada_simulada", vencimento="2026-09-19", strike=30.0,
               precoEntrada=1.2), "2026-09-10",
        {"spotAtual": 29.0, "dataSpotAtual": "2026-09-10"})
    assert estado_novo == "monitorada"
    alcancados.add("monitorada")

    estado_novo, _, _ = put_lifecycle.decidir(
        _linha(estado="monitorada", vencimento="2026-09-19", strike=30.0,
               precoEntrada=1.2), "2026-09-19",
        {"spotLiquidacao": 28.0, "dataSpotLiquidacao": "2026-09-19"})
    assert estado_novo == "fechada"
    alcancados.add("fechada")

    # "armada" é o estado inicial de toda linha (put_suggestions.ESTADO_INICIAL)
    alcancados.add(put_suggestions.ESTADO_INICIAL)

    assert alcancados == set(put_suggestions.ESTADOS)
