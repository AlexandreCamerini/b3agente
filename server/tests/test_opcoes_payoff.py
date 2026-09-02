"""Fase 15, Plano 01 — aritmética pura de payoff de N pernas (ENG-02).

Portado de `~/dev/MCP/servers/mydata/calculos.py` (linhas 255-464), fonte
externa read-only. Módulo sob teste: `server/app/opcoes_payoff.py`.

Parte 1 (Task 1): normalização de perna (`_validar_perna`), custo líquido
(`custo_liquido`) e resultado em um preço qualquer (`resultado_no_vencimento`).

Parte 2 (Task 2): perfil completo da estrutura (`perfil_da_estrutura`) —
extremos (ganho/perda máximos, ilimitado), breakevens e delta somado.
"""
import pytest

from app import opcoes_payoff as m


# --------------------------- Parte 1: normalização e custo ---------------------------

def test_validar_perna_normaliza_sinal_e_quantidade_default():
    p = m._validar_perna({"tipo": "CALL", "lado": "compra", "strike": 40, "premio": 1.5}, 1)
    assert p["sinal"] == 1.0
    assert p["quantidade"] == 1.0
    assert p["tipo"] == "CALL"
    assert p["strike"] == 40.0
    assert p["premio"] == 1.5


def test_validar_perna_lado_venda_produz_sinal_negativo():
    p = m._validar_perna({"tipo": "CALL", "lado": "venda", "strike": 40, "premio": 1.5}, 1)
    assert p["sinal"] == -1.0


def test_validar_perna_acao_strike_omitido_normaliza_para_zero():
    p = m._validar_perna({"tipo": "ACAO", "lado": "compra", "premio": 30}, 1)
    assert p["strike"] == 0.0


def test_validar_perna_acao_strike_diferente_de_zero_recusa_citando_indice_e_acao():
    with pytest.raises(ValueError) as exc:
        m._validar_perna({"tipo": "ACAO", "lado": "compra", "strike": 5, "premio": 30}, 3)
    msg = str(exc.value)
    assert "3" in msg
    assert "ACAO" in msg


def test_validar_perna_acao_premio_nao_positivo_recusa():
    with pytest.raises(ValueError):
        m._validar_perna({"tipo": "ACAO", "lado": "compra", "premio": 0}, 1)


def test_validar_perna_strike_booleano_recusa():
    with pytest.raises(ValueError):
        m._validar_perna({"tipo": "CALL", "lado": "compra", "strike": True, "premio": 1}, 1)


def test_validar_perna_tipo_invalido_recusa_citando_indice_e_campo():
    with pytest.raises(ValueError) as exc:
        m._validar_perna({"tipo": "SWAP", "lado": "compra", "strike": 40, "premio": 1}, 2)
    msg = str(exc.value)
    assert "2" in msg
    assert "tipo" in msg


def test_validar_perna_lado_invalido_recusa_citando_indice_e_campo():
    with pytest.raises(ValueError) as exc:
        m._validar_perna({"tipo": "CALL", "lado": "alugar", "strike": 40, "premio": 1}, 4)
    msg = str(exc.value)
    assert "4" in msg
    assert "lado" in msg


def test_validar_perna_premio_negativo_recusa():
    with pytest.raises(ValueError):
        m._validar_perna({"tipo": "CALL", "lado": "compra", "strike": 40, "premio": -1}, 1)


def test_validar_perna_quantidade_nao_positiva_recusa():
    with pytest.raises(ValueError):
        m._validar_perna({"tipo": "CALL", "lado": "compra", "strike": 40, "premio": 1, "quantidade": 0}, 1)


def test_custo_liquido_venda_coberta():
    pernas = [
        m._validar_perna({"tipo": "ACAO", "lado": "compra", "premio": 30}, 1),
        m._validar_perna({"tipo": "CALL", "lado": "venda", "strike": 32, "premio": 1.5}, 2),
    ]
    assert m.custo_liquido(pernas) == 28.5


def test_custo_liquido_call_vendida_seca_e_credito():
    pernas = [m._validar_perna({"tipo": "CALL", "lado": "venda", "strike": 40, "premio": 1.5}, 1)]
    assert m.custo_liquido(pernas) == -1.5


def test_resultado_no_vencimento_call_comprada():
    assert m.resultado_no_vencimento(
        [{"tipo": "CALL", "lado": "compra", "strike": 40, "premio": 2}], 45) == 3.0


def test_resultado_no_vencimento_put_comprada():
    assert m.resultado_no_vencimento(
        [{"tipo": "PUT", "lado": "compra", "strike": 40, "premio": 2}], 35) == 3.0


def test_resultado_no_vencimento_acao_preco_arbitrario_entre_strikes():
    assert m.resultado_no_vencimento(
        [{"tipo": "ACAO", "lado": "compra", "premio": 30}], 41.03) == 11.03


def test_resultado_no_vencimento_sem_pernas_recusa_citando_sem_pernas():
    with pytest.raises(ValueError) as exc:
        m.resultado_no_vencimento([], 10)
    assert "sem pernas" in str(exc.value)


def test_resultado_no_vencimento_preco_invalido_recusa():
    with pytest.raises(ValueError):
        m.resultado_no_vencimento([{"tipo": "CALL", "lado": "compra", "strike": 40, "premio": 2}], -1)


# --------------------------- Parte 2: perfil da estrutura ---------------------------

def test_perfil_call_seca_comprada_ganho_ilimitado():
    r = m.perfil_da_estrutura([{"tipo": "CALL", "lado": "compra", "strike": 40, "premio": 2}])
    assert r["ganho_ilimitado"] is True
    assert r["ganho_maximo"] is None
    assert r["perda_maxima"] == 2.0
    assert r["breakevens"] == [42.0]
    assert r["fluxo"] == "debito"


def test_perfil_call_seca_vendida_perda_ilimitada():
    r = m.perfil_da_estrutura([{"tipo": "CALL", "lado": "venda", "strike": 40, "premio": 2}])
    assert r["perda_ilimitada"] is True
    assert r["perda_maxima"] is None
    assert r["ganho_maximo"] == 2.0
    assert r["fluxo"] == "credito"


def test_perfil_venda_coberta_ganho_limitado():
    r = m.perfil_da_estrutura([
        {"tipo": "ACAO", "lado": "compra", "premio": 30},
        {"tipo": "CALL", "lado": "venda", "strike": 32, "premio": 1.5},
    ])
    assert r["ganho_ilimitado"] is False
    assert r["perda_ilimitada"] is False
    assert r["ganho_maximo"] == 3.5
    assert r["breakevens"] == [28.5]


def test_perfil_put_de_protecao_perda_limitada():
    r = m.perfil_da_estrutura([
        {"tipo": "ACAO", "lado": "compra", "premio": 30},
        {"tipo": "PUT", "lado": "compra", "strike": 28, "premio": 1},
    ])
    assert r["perda_ilimitada"] is False
    assert r["perda_maxima"] == 3.0
    assert r["ganho_ilimitado"] is True
    assert r["ganho_maximo"] is None


def test_perfil_collar_travado_dos_dois_lados():
    r = m.perfil_da_estrutura([
        {"tipo": "ACAO", "lado": "compra", "premio": 30},
        {"tipo": "CALL", "lado": "venda", "strike": 33, "premio": 1},
        {"tipo": "PUT", "lado": "compra", "strike": 28, "premio": 0.8},
    ])
    assert r["ganho_ilimitado"] is False
    assert r["perda_ilimitada"] is False
    assert r["ganho_maximo"] is not None
    assert r["perda_maxima"] is not None


def test_delta_total_soma_pernas_com_delta():
    pernas = [
        m._validar_perna({"tipo": "CALL", "lado": "compra", "strike": 40, "premio": 2, "delta": 0.5}, 1),
        m._validar_perna({"tipo": "CALL", "lado": "venda", "strike": 45, "premio": 1, "delta": 0.3}, 2),
    ]
    assert m._delta_total(pernas) == {"valor": 0.2, "pernas_sem_delta": 0, "motivo": None}


def test_delta_total_perna_sem_delta_declara_soma_parcial():
    pernas = [
        m._validar_perna({"tipo": "CALL", "lado": "compra", "strike": 40, "premio": 2, "delta": 0.5}, 1),
        m._validar_perna({"tipo": "CALL", "lado": "venda", "strike": 45, "premio": 1}, 2),
    ]
    r = m._delta_total(pernas)
    assert r["pernas_sem_delta"] == 1
    assert r["motivo"] is not None


def test_curva_avalia_conjunto_ordenado_sem_repeticao_de_zero():
    r = m.perfil_da_estrutura([
        {"tipo": "ACAO", "lado": "compra", "premio": 30},
        {"tipo": "CALL", "lado": "venda", "strike": 32, "premio": 1.5},
    ])
    precos = [ponto["preco_objeto"] for ponto in r["curva"]]
    assert precos == sorted(set(precos))
    assert precos.count(0.0) == 1


def test_perfil_da_estrutura_sem_pernas_recusa():
    with pytest.raises(ValueError) as exc:
        m.perfil_da_estrutura([])
    assert "sem pernas" in str(exc.value)


def test_perfil_da_estrutura_unidade_menciona_por_acao_e_lote():
    r = m.perfil_da_estrutura([{"tipo": "CALL", "lado": "compra", "strike": 40, "premio": 2}])
    assert "unidade" in r
    assert "ação" in r["unidade"] or "acao" in r["unidade"].lower()


def test_resultado_no_vencimento_coincide_com_ponto_da_curva_no_strike():
    pernas = [
        {"tipo": "ACAO", "lado": "compra", "premio": 30},
        {"tipo": "CALL", "lado": "venda", "strike": 32, "premio": 1.5},
    ]
    perfil = m.perfil_da_estrutura(pernas)
    ponto_32 = next(p for p in perfil["curva"] if p["preco_objeto"] == 32.0)
    assert m.resultado_no_vencimento(pernas, 32.0) == ponto_32["resultado"]
