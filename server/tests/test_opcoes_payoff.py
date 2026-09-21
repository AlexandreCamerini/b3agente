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


# --------------------------- Parte 2b: vencimento por perna e calendário (D-03, Fase 36) ---------------------------

def test_validar_perna_sem_vencimento_normaliza_para_none():
    p = m._validar_perna({"tipo": "CALL", "lado": "compra", "strike": 40, "premio": 1}, 1)
    assert p["vencimento"] is None


def test_validar_perna_vencimento_preservado_verbatim():
    p = m._validar_perna(
        {"tipo": "CALL", "lado": "compra", "strike": 40, "premio": 1,
         "vencimento": "2026-10-16"}, 1)
    assert p["vencimento"] == "2026-10-16"


def test_perfil_sem_vencimento_em_nenhuma_perna_mantem_resultado_e_declara_nao_divergente():
    r = m.perfil_da_estrutura([
        {"tipo": "CALL", "lado": "compra", "strike": 49.17, "premio": 0.40},
        {"tipo": "CALL", "lado": "venda", "strike": 49.67, "premio": 0.15},
    ])
    assert r["custo_liquido"] == 0.25
    assert r["breakevens"] == [49.42]
    assert r["ganho_maximo"] == 0.25
    assert r["perda_maxima"] == 0.25
    assert r["vencimentos"] == {"divergentes": False, "distintos": [], "motivo": None}


def test_perfil_mesmo_vencimento_nas_duas_pernas_identico_a_sem_vencimento():
    pernas_sem = [
        {"tipo": "CALL", "lado": "compra", "strike": 49.17, "premio": 0.40},
        {"tipo": "CALL", "lado": "venda", "strike": 49.67, "premio": 0.15},
    ]
    pernas_com = [
        {**pernas_sem[0], "vencimento": "2026-10-16"},
        {**pernas_sem[1], "vencimento": "2026-10-16"},
    ]
    r_sem = m.perfil_da_estrutura(pernas_sem)
    r_com = m.perfil_da_estrutura(pernas_com)
    for chave in r_sem:
        if chave == "pernas":
            continue
        assert r_com[chave] == r_sem[chave], f"campo {chave} divergiu"


def test_perfil_vencimento_omitido_em_uma_perna_nao_e_divergencia():
    r = m.perfil_da_estrutura([
        {"tipo": "CALL", "lado": "compra", "strike": 49.17, "premio": 0.40,
         "vencimento": "2026-10-16"},
        {"tipo": "CALL", "lado": "venda", "strike": 49.67, "premio": 0.15},
    ])
    assert r["vencimentos"]["divergentes"] is False
    assert r["breakevens"] == [49.42]


def test_perfil_vencimentos_divergentes_degrada_sem_curva():
    r = m.perfil_da_estrutura([
        {"tipo": "CALL", "lado": "compra", "strike": 49.17, "premio": 0.40,
         "vencimento": "2026-10-16"},
        {"tipo": "CALL", "lado": "venda", "strike": 49.67, "premio": 0.15,
         "vencimento": "2026-11-20"},
    ])
    assert r["vencimentos"]["divergentes"] is True
    assert "vencimentos diferentes" in r["vencimentos"]["motivo"]
    assert r["vencimentos"]["distintos"] == ["2026-10-16", "2026-11-20"]
    assert r["curva"] == []
    assert r["breakevens"] == []
    assert r["ganho_maximo"] is None
    assert r["perda_maxima"] is None
    assert r["ganho_ilimitado"] is False
    assert r["perda_ilimitada"] is False
    assert r["custo_liquido"] == 0.25


# --------------------------- Parte 2c: entrada degenerada e S=0 espurio (D-04, Fase 36) ---------------------------

def test_perfil_entrada_degenerada_recusa_citando_sem_exposicao():
    with pytest.raises(ValueError) as exc:
        m.perfil_da_estrutura([
            {"tipo": "CALL", "lado": "compra", "strike": 50, "premio": 1},
            {"tipo": "CALL", "lado": "venda", "strike": 50, "premio": 1},
        ])
    assert "sem exposição" in str(exc.value)


def test_perfil_call_premio_zero_nao_e_degenerada_breakeven_so_no_strike():
    r = m.perfil_da_estrutura([{"tipo": "CALL", "lado": "compra", "strike": 50, "premio": 0}])
    assert r["breakevens"] == [50.0]
    assert r["ganho_ilimitado"] is True


def test_perfil_box_travado_em_zero_custo_nao_zero_nao_e_degenerada_sem_breakevens():
    r = m.perfil_da_estrutura([
        {"tipo": "CALL", "lado": "compra", "strike": 50, "premio": 6},
        {"tipo": "CALL", "lado": "venda", "strike": 55, "premio": 3},
        {"tipo": "PUT", "lado": "compra", "strike": 55, "premio": 4},
        {"tipo": "PUT", "lado": "venda", "strike": 50, "premio": 2},
    ])
    assert r["custo_liquido"] == 5.0
    assert r["breakevens"] == []


def test_perfil_ratio_1x2_custo_zero_breakevens_sem_zero_espurio():
    r = m.perfil_da_estrutura([
        {"tipo": "CALL", "lado": "compra", "strike": 50, "premio": 3},
        {"tipo": "CALL", "lado": "venda", "strike": 55, "premio": 1.5, "quantidade": 2},
    ])
    assert r["breakevens"] == [50.0, 60.0]
    assert r["perda_ilimitada"] is True


def test_perfil_divergencia_de_vencimento_tem_precedencia_sobre_guarda_degenerada():
    # Estrutura simultaneamente degenerada (mesma perna comprada e vendida no
    # mesmo strike/premio, custo zero, inclinação zero) E com vencimentos
    # divergentes: a divergência (fato sobre a ENTRADA) vence e devolve o
    # dicionário degradado de D-03 — nunca levanta ValueError de D-04.1.
    r = m.perfil_da_estrutura([
        {"tipo": "CALL", "lado": "compra", "strike": 50, "premio": 1,
         "vencimento": "2026-10-16"},
        {"tipo": "CALL", "lado": "venda", "strike": 50, "premio": 1,
         "vencimento": "2026-11-20"},
    ])
    assert r["vencimentos"]["divergentes"] is True
    assert r["curva"] == []


def test_perfil_breakevens_regressao_apos_correcao_de_s_zero_espurio():
    assert m.perfil_da_estrutura([
        {"tipo": "ACAO", "lado": "compra", "premio": 30},
        {"tipo": "CALL", "lado": "venda", "strike": 32, "premio": 1.5},
    ])["breakevens"] == [28.5]
    assert m.perfil_da_estrutura(
        [{"tipo": "CALL", "lado": "compra", "strike": 40, "premio": 2}])["breakevens"] == [42.0]
    borboleta = m.perfil_da_estrutura([
        {"tipo": "CALL", "lado": "compra", "strike": 45, "premio": 6},
        {"tipo": "CALL", "lado": "venda", "strike": 50, "premio": 3, "quantidade": 2},
        {"tipo": "CALL", "lado": "compra", "strike": 55, "premio": 1.5},
    ])
    assert borboleta["breakevens"] == [46.5, 53.5]
    condor = m.perfil_da_estrutura([
        {"tipo": "CALL", "lado": "compra", "strike": 45, "premio": 6},
        {"tipo": "CALL", "lado": "venda", "strike": 50, "premio": 3},
        {"tipo": "CALL", "lado": "venda", "strike": 55, "premio": 1.5},
        {"tipo": "CALL", "lado": "compra", "strike": 60, "premio": 0.5},
    ])
    assert condor["breakevens"] == [47.0, 58.0]


# --------------------------- Parte 3: casos-limite de PAYOFF-02 (D-07, Fase 36) ---------------------------
#
# Checklist de PAYOFF-02 (.planning/REQUIREMENTS.md), cada item mapeado a um
# teste nomeado (ou a um teste pré-existente citado, para o checklist ficar
# rastreável inteiro por leitura):
#   - compra/venda seca (1 perna)              -> test_perfil_call_seca_comprada_ganho_ilimitado /
#                                                  test_perfil_call_seca_vendida_perda_ilimitada (Parte 2, já existentes)
#   - venda descoberta (perda ilimitada)        -> test_perfil_call_seca_vendida_perda_ilimitada (Parte 2, já existente — NÃO duplicado)
#   - ratio spread (perda ilimitada)            -> test_perfil_ratio_1x2_custo_zero_breakevens_sem_zero_espurio (Parte 2c) +
#                                                  test_perfil_quantidades_assimetricas_ratio_1x2_lote_fora_do_motor (abaixo)
#   - trava de alta com calls                   -> test_perfil_trava_de_alta_com_calls_caso_golden (abaixo)
#   - trava de baixa com puts                   -> test_perfil_trava_de_baixa_com_puts_ganho_e_perda_finitos_um_breakeven (abaixo)
#   - borboleta/condor (2 breakevens + platô)   -> test_perfil_breakevens_regressao_apos_correcao_de_s_zero_espurio (Parte 2c) +
#                                                  test_perfil_borboleta_platô_e_extremos_nomeados / test_perfil_condor_plato_central_mesmo_resultado (abaixo)
#   - straddle/strangle                         -> test_perfil_straddle_comprado_dois_breakevens /
#                                                  test_perfil_strangle_comprado_dois_breakevens (abaixo)
#   - covered call/collar (perna ACAO)          -> test_perfil_venda_coberta_ganho_limitado / test_perfil_collar_travado_dos_dois_lados (Parte 2, já existentes)
#   - box (curva plana não-zero)                -> test_perfil_box_resultado_constante_nao_zero_sem_breakevens (abaixo)
#   - lotSize/quantidades assimétricas          -> test_perfil_quantidades_assimetricas_ratio_1x2_lote_fora_do_motor (abaixo)
#   - entrada degenerada (recusa, nunca NaN)    -> test_perfil_entrada_degenerada_recusa_citando_sem_exposicao (Parte 2c, já existente)

def test_perfil_trava_de_alta_com_calls_caso_golden():
    r = m.perfil_da_estrutura([
        {"tipo": "CALL", "lado": "compra", "strike": 49.17, "premio": 0.40},
        {"tipo": "CALL", "lado": "venda", "strike": 49.67, "premio": 0.15},
    ])
    assert r["custo_liquido"] == 0.25
    assert r["breakevens"] == [49.42]
    assert r["ganho_maximo"] == 0.25
    assert r["perda_maxima"] == 0.25
    assert r["ganho_ilimitado"] is False
    assert r["perda_ilimitada"] is False


def test_perfil_trava_de_baixa_com_puts_ganho_e_perda_finitos_um_breakeven():
    r = m.perfil_da_estrutura([
        {"tipo": "PUT", "lado": "compra", "strike": 50, "premio": 3},
        {"tipo": "PUT", "lado": "venda", "strike": 45, "premio": 1},
    ])
    assert r["ganho_ilimitado"] is False
    assert r["perda_ilimitada"] is False
    assert r["ganho_maximo"] == 3.0
    assert r["perda_maxima"] == 2.0
    assert r["breakevens"] == [48.0]


def test_perfil_straddle_comprado_dois_breakevens():
    r = m.perfil_da_estrutura([
        {"tipo": "CALL", "lado": "compra", "strike": 50, "premio": 1},
        {"tipo": "PUT", "lado": "compra", "strike": 50, "premio": 1},
    ])
    assert r["breakevens"] == [48.0, 52.0]
    assert len(r["breakevens"]) == 2
    assert r["ganho_ilimitado"] is True


def test_perfil_strangle_comprado_dois_breakevens():
    r = m.perfil_da_estrutura([
        {"tipo": "PUT", "lado": "compra", "strike": 45, "premio": 1},
        {"tipo": "CALL", "lado": "compra", "strike": 55, "premio": 1},
    ])
    assert len(r["breakevens"]) == 2
    inferior, superior = r["breakevens"]
    assert inferior < 45
    assert superior > 55


def test_perfil_borboleta_plato_e_extremos_nomeados():
    r = m.perfil_da_estrutura([
        {"tipo": "CALL", "lado": "compra", "strike": 45, "premio": 6},
        {"tipo": "CALL", "lado": "venda", "strike": 50, "premio": 3, "quantidade": 2},
        {"tipo": "CALL", "lado": "compra", "strike": 55, "premio": 1.5},
    ])
    assert r["custo_liquido"] == 1.5
    assert r["breakevens"] == [46.5, 53.5]
    assert r["ganho_maximo"] == 3.5
    assert r["perda_maxima"] == 1.5
    assert r["ganho_ilimitado"] is False
    assert r["perda_ilimitada"] is False


def test_perfil_condor_plato_central_mesmo_resultado():
    r = m.perfil_da_estrutura([
        {"tipo": "CALL", "lado": "compra", "strike": 45, "premio": 6},
        {"tipo": "CALL", "lado": "venda", "strike": 50, "premio": 3},
        {"tipo": "CALL", "lado": "venda", "strike": 55, "premio": 1.5},
        {"tipo": "CALL", "lado": "compra", "strike": 60, "premio": 0.5},
    ])
    assert r["breakevens"] == [47.0, 58.0]
    assert r["ganho_maximo"] == 3.0
    assert r["perda_maxima"] == 2.0
    pontos_platô = {p["preco_objeto"]: p["resultado"] for p in r["curva"]
                    if p["preco_objeto"] in (50.0, 55.0)}
    assert pontos_platô[50.0] == pontos_platô[55.0] == 3.0


def test_perfil_box_resultado_constante_nao_zero_sem_breakevens():
    # Diferente do degenerado (D-04.1): custo != 0, e o resultado travado é
    # um valor fixo NÃO-zero em qualquer preço — existe exposição real, só
    # que ela não varia. Guarda a distinção de três partes da D-04.1 de nunca
    # degenerar para duas.
    r = m.perfil_da_estrutura([
        {"tipo": "CALL", "lado": "compra", "strike": 50, "premio": 6},
        {"tipo": "CALL", "lado": "venda", "strike": 55, "premio": 3},
        {"tipo": "PUT", "lado": "compra", "strike": 55, "premio": 3.5},
        {"tipo": "PUT", "lado": "venda", "strike": 50, "premio": 2},
    ])
    assert r["custo_liquido"] == 4.5
    assert all(p["resultado"] == 0.5 for p in r["curva"])
    assert r["breakevens"] == []
    assert r["ganho_maximo"] == 0.5
    assert r["perda_maxima"] == 0.0
    assert r["ganho_ilimitado"] is False
    assert r["perda_ilimitada"] is False


def test_perfil_quantidades_assimetricas_ratio_1x2_lote_fora_do_motor():
    # Quantidade é número de CONTRATOS, nenhum fator de lote entra no motor
    # (D-02) — a perna vendida tem o dobro de contratos da comprada.
    r = m.perfil_da_estrutura([
        {"tipo": "CALL", "lado": "compra", "strike": 50, "premio": 3},
        {"tipo": "CALL", "lado": "venda", "strike": 55, "premio": 1.5, "quantidade": 2},
    ])
    assert r["custo_liquido"] == 0.0
    assert r["perda_ilimitada"] is True
    assert r["ganho_maximo"] == 5.0
