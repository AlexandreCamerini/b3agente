"""server/tests/test_put_lifecycle_diario.py — varredura diária do ciclo de
vida das sugestões de put (Fase 11, Plano 02, Task 1).

Prova de COMPORTAMENTO: banco temporário real, `candle_cache.peek` é a
ÚNICA fonte de preço — monkeypatchada por controle explícito do teste, nunca
rede real. `options_provider`/`candle_provider` ficam com um fake que FALHA
o teste se chamado (asserção negativa de custo zero de rede, A-11-07).
"""
from __future__ import annotations

import asyncio

import pytest

from app import candle_cache, db, put_lifecycle, put_suggestions


def _conn(tmp_path, nome="t.db"):
    return db.connect(str(tmp_path / nome))


def _linha_valida(**overrides):
    linha = {
        "user_id": "u1",
        "ticker": "PETR4",
        "data_pregao": "2026-08-28",
        "setup": "IFR2 (baixa)",
        "lado": "baixa",
        "contrato": "PETRR100",
        "strike": 34.5,
        "vencimento": "2026-09-19",
        "estilo_exercicio": "americano",
        "iv": 0.32,
        "delta": -0.42,
        "premio": 1.15,
        "volume": 250,
        "spot": 36.2,
        "fonte": "mydata",
        "as_of": "2026-08-28",
        "prov_sha256": "abc123",
        "prov_dt_captura": "2026-08-28T20:05:00Z",
        "prov_captura": "COTAHIST_D28082026.TXT",
    }
    linha.update(overrides)
    return linha


def _registrar(conn, **overrides):
    put_suggestions.registrar(conn, _linha_valida(**overrides))
    return put_suggestions.listar(conn)[0]["id"]


def _candle(date, close):
    return {"date": date, "close": close}


@pytest.fixture(autouse=True)
def _cache_limpo():
    candle_cache.reset()
    yield
    candle_cache.reset()


@pytest.fixture(autouse=True)
def _sem_env(monkeypatch):
    monkeypatch.delenv("B3_PUT_LIFECYCLE_HHMM", raising=False)
    monkeypatch.delenv("B3_PUT_LIFECYCLE_OFF", raising=False)


def _popula_cache(ticker, candles, interval="1d"):
    candle_cache._CACHE[candle_cache._key(ticker, interval)] = {
        "candles": candles, "at": "2026-08-28T09:45:00Z",
    }


def _fake_provider_falha(*a, **k):
    raise AssertionError("options_provider/candle_provider NUNCA deve ser chamado por run_diario")


# --------------------------------------------------------------------------- #
# Custo zero de rede + isolamento de linha terminal
# --------------------------------------------------------------------------- #

def test_linha_terminal_nunca_e_lida(tmp_path):
    conn = _conn(tmp_path)
    id_fechada = _registrar(conn, ticker="VALE3", contrato="VALER1")
    put_suggestions.transicionar(conn, id_fechada, "executada_simulada")
    put_suggestions.transicionar(conn, id_fechada, "fechada", {
        "preco_fechamento": 0.0, "motivo_fechamento": "vencimento", "pnl_por_acao": -1.0,
    })
    id_armada = _registrar(conn, ticker="PETR4", contrato="PETRR100")

    resumo = put_lifecycle.run_diario(conn, now=_dt("2026-08-29"))

    assert resumo["linhas"] == 1  # só a armada, a fechada é terminal e nunca aparece
    saida_fechada = [l for l in put_suggestions.listar(conn) if l["id"] == id_fechada][0]
    assert saida_fechada["estado"] == "fechada"
    assert saida_fechada["pnlPorAcao"] == -1.0  # nunca recalculada


def test_custo_zero_de_rede_por_asserção_negativa(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    linha_id = _registrar(conn, ticker="PETR4", contrato="PETRR100", premio=1.15, vencimento="2026-09-19")
    put_suggestions.transicionar(conn, linha_id, "executada_simulada", {
        "executada_em": "2026-08-28", "preco_entrada": 1.15,
    })

    import app.options_provider as options_provider
    import app.candle_provider as candle_provider
    monkeypatch.setattr(options_provider, "get_options", _fake_provider_falha)
    monkeypatch.setattr(candle_provider, "get_history", _fake_provider_falha)

    # cache frio (nenhum peek populado) — vira pendência, nunca busca na rede
    resumo = put_lifecycle.run_diario(conn, now=_dt("2026-08-29"))
    assert resumo["pendentes"] == 1
    assert resumo["erros"] == []


# --------------------------------------------------------------------------- #
# Trajetória completa: armada → executada_simulada → monitorada → fechada
# --------------------------------------------------------------------------- #

def _dt(data_iso):
    from datetime import datetime
    return datetime.fromisoformat(data_iso + "T10:00:00-03:00")


def test_armada_com_premio_vira_executada_simulada(tmp_path):
    conn = _conn(tmp_path)
    linha_id = _registrar(conn, ticker="PETR4", contrato="PETRR100", premio=1.15, vencimento="2026-09-19")

    resumo = put_lifecycle.run_diario(conn, now=_dt("2026-08-29"))

    saida = put_suggestions.listar(conn)[0]
    assert saida["estado"] == "executada_simulada"
    assert saida["precoEntrada"] == 1.15
    assert saida["executadaEm"] == "2026-08-29"
    assert resumo == {
        "linhas": 1, "avancos": 1, "pendentes": 0,
        "porEstado": {"executada_simulada": 1}, "erros": [],
    }


def test_executada_simulada_com_candle_vira_monitorada(tmp_path):
    conn = _conn(tmp_path)
    linha_id = _registrar(conn, ticker="PETR4", contrato="PETRR100", premio=1.15, vencimento="2026-09-19", strike=34.5)
    put_suggestions.transicionar(conn, linha_id, "executada_simulada", {
        "executada_em": "2026-08-28", "preco_entrada": 1.15,
    })
    _popula_cache("PETR4", [_candle("2026-08-29", 33.0)])

    resumo = put_lifecycle.run_diario(conn, now=_dt("2026-08-29"))

    saida = put_suggestions.listar(conn)[0]
    assert saida["estado"] == "monitorada"
    assert saida["spotMarcacao"] == 33.0
    assert saida["intrinsecoMarcacao"] == 1.5  # max(0, 34.5-33.0)
    assert saida["marcadaEm"] == "2026-08-29"
    assert resumo["avancos"] == 1
    assert resumo["porEstado"] == {"monitorada": 1}


def test_monitorada_remarca_com_candle_mais_novo_e_continua_monitorada(tmp_path):
    conn = _conn(tmp_path)
    linha_id = _registrar(conn, ticker="PETR4", contrato="PETRR100", premio=1.15, vencimento="2026-09-19", strike=34.5)
    put_suggestions.transicionar(conn, linha_id, "executada_simulada", {
        "executada_em": "2026-08-28", "preco_entrada": 1.15,
    })
    _popula_cache("PETR4", [_candle("2026-08-29", 33.0)])
    put_lifecycle.run_diario(conn, now=_dt("2026-08-29"))

    _popula_cache("PETR4", [_candle("2026-08-29", 33.0), _candle("2026-08-30", 32.0)])
    resumo = put_lifecycle.run_diario(conn, now=_dt("2026-08-30"))

    saida = put_suggestions.listar(conn)[0]
    assert saida["estado"] == "monitorada"
    assert saida["spotMarcacao"] == 32.0
    assert saida["intrinsecoMarcacao"] == 2.5
    assert saida["marcadaEm"] == "2026-08-30"
    assert resumo["porEstado"] == {"monitorada": 1}


def test_vencimento_alcancado_fecha_com_pnl_positivo(tmp_path):
    conn = _conn(tmp_path)
    linha_id = _registrar(conn, ticker="PETR4", contrato="PETRR100", premio=1.15, vencimento="2026-09-19", strike=34.5)
    put_suggestions.transicionar(conn, linha_id, "executada_simulada", {
        "executada_em": "2026-08-28", "preco_entrada": 1.15,
    })
    _popula_cache("PETR4", [_candle("2026-09-19", 30.0)])

    resumo = put_lifecycle.run_diario(conn, now=_dt("2026-09-19"))

    saida = put_suggestions.listar(conn)[0]
    assert saida["estado"] == "fechada"
    assert saida["motivoFechamento"] == "vencimento"
    assert saida["precoFechamento"] == 4.5  # max(0, 34.5-30.0)
    assert saida["pnlPorAcao"] == round(4.5 - 1.15, 2)
    assert resumo["porEstado"] == {"fechada": 1}


def test_put_expira_fora_do_dinheiro_fecha_com_perda_total_do_premio(tmp_path):
    conn = _conn(tmp_path)
    linha_id = _registrar(conn, ticker="PETR4", contrato="PETRR100", premio=1.15, vencimento="2026-09-19", strike=30.0)
    put_suggestions.transicionar(conn, linha_id, "executada_simulada", {
        "executada_em": "2026-08-28", "preco_entrada": 1.15,
    })
    _popula_cache("PETR4", [_candle("2026-09-19", 33.0)])  # spot ACIMA do strike

    resumo = put_lifecycle.run_diario(conn, now=_dt("2026-09-19"))

    saida = put_suggestions.listar(conn)[0]
    assert saida["estado"] == "fechada"
    assert saida["precoFechamento"] == 0.0
    assert saida["pnlPorAcao"] == -1.15
    assert resumo["porEstado"] == {"fechada": 1}


def test_armada_sem_execucao_ate_vencimento_vira_expirada_sem_uso(tmp_path):
    conn = _conn(tmp_path)
    linha_id = _registrar(conn, ticker="PETR4", contrato="PETRR100", premio=None, vencimento="2026-09-19")

    resumo = put_lifecycle.run_diario(conn, now=_dt("2026-09-20"))

    saida = put_suggestions.listar(conn)[0]
    assert saida["estado"] == "expirada_sem_uso"
    assert saida["pnlPorAcao"] is None
    assert resumo["porEstado"] == {"expirada_sem_uso": 1}


# --------------------------------------------------------------------------- #
# Pendência: falta de candle não é exceção, nunca inventa valor
# --------------------------------------------------------------------------- #

def test_cache_vazio_registra_pendencia_sem_avancar_nem_levantar(tmp_path):
    conn = _conn(tmp_path)
    linha_id = _registrar(conn, ticker="PETR4", contrato="PETRR100", premio=1.15, vencimento="2026-09-19", strike=34.5)
    put_suggestions.transicionar(conn, linha_id, "executada_simulada", {
        "executada_em": "2026-08-28", "preco_entrada": 1.15,
    })
    # nenhum candle populado para PETR4 — peek devolve []

    resumo = put_lifecycle.run_diario(conn, now=_dt("2026-08-29"))

    saida = put_suggestions.listar(conn)[0]
    assert saida["estado"] == "executada_simulada"  # não avançou
    assert saida["pendenteDesde"] == "2026-08-29"
    assert resumo["pendentes"] == 1
    assert resumo["avancos"] == 0
    assert resumo["erros"] == []


def test_pendente_desde_nao_e_sobrescrito_e_e_limpo_ao_fechar(tmp_path):
    conn = _conn(tmp_path)
    linha_id = _registrar(conn, ticker="PETR4", contrato="PETRR100", premio=1.15, vencimento="2026-09-19", strike=34.5)
    put_suggestions.transicionar(conn, linha_id, "executada_simulada", {
        "executada_em": "2026-08-28", "preco_entrada": 1.15,
    })

    put_lifecycle.run_diario(conn, now=_dt("2026-08-29"))  # 1ª pendência
    put_lifecycle.run_diario(conn, now=_dt("2026-08-30"))  # 2ª rodada pendente

    saida = put_suggestions.listar(conn)[0]
    assert saida["pendenteDesde"] == "2026-08-29"  # primeira data vale

    # candle finalmente chega, vencido — linha fecha e a pendência é limpa
    _popula_cache("PETR4", [_candle("2026-09-19", 30.0)])
    put_lifecycle.run_diario(conn, now=_dt("2026-09-19"))

    saida = put_suggestions.listar(conn)[0]
    assert saida["estado"] == "fechada"
    assert saida["pendenteDesde"] is None


# --------------------------------------------------------------------------- #
# Isolamento por linha: uma exceção não aborta as demais
# --------------------------------------------------------------------------- #

def test_excecao_em_uma_linha_nao_aborta_as_demais(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    id_a = _registrar(conn, ticker="PETR4", contrato="PETRR100", premio=1.15, vencimento="2026-09-19")
    id_b = _registrar(conn, ticker="VALE3", contrato="VALER100", premio=1.20, vencimento="2026-09-19")
    id_c = _registrar(conn, ticker="ITUB4", contrato="ITUBR100", premio=1.30, vencimento="2026-09-19")

    original_decidir = put_lifecycle.decidir

    def _decidir_espiao(linha, hoje, spots):
        if linha["id"] == id_b:
            raise RuntimeError("boom linha do meio")
        return original_decidir(linha, hoje, spots)

    monkeypatch.setattr(put_lifecycle, "decidir", _decidir_espiao)

    resumo = put_lifecycle.run_diario(conn, now=_dt("2026-08-29"))

    saida = {l["id"]: l for l in put_suggestions.listar(conn)}
    assert saida[id_a]["estado"] == "executada_simulada"
    assert saida[id_b]["estado"] == "armada"  # não avançou, erro isolado
    assert saida[id_c]["estado"] == "executada_simulada"
    assert len(resumo["erros"]) == 1
    assert str(id_b) in resumo["erros"][0]


# --------------------------------------------------------------------------- #
# Idempotência: rodar duas vezes no mesmo dia não retrocede nem recalcula
# --------------------------------------------------------------------------- #

def test_rodar_duas_vezes_no_mesmo_dia_e_idempotente(tmp_path):
    conn = _conn(tmp_path)
    linha_id = _registrar(conn, ticker="PETR4", contrato="PETRR100", premio=1.15, vencimento="2026-09-19", strike=34.5)
    put_suggestions.transicionar(conn, linha_id, "executada_simulada", {
        "executada_em": "2026-08-28", "preco_entrada": 1.15,
    })
    _popula_cache("PETR4", [_candle("2026-09-19", 30.0)])

    put_lifecycle.run_diario(conn, now=_dt("2026-09-19"))
    saida_1 = put_suggestions.listar(conn)[0]
    assert saida_1["estado"] == "fechada"
    assert saida_1["pnlPorAcao"] == round(4.5 - 1.15, 2)

    resumo_2 = put_lifecycle.run_diario(conn, now=_dt("2026-09-19"))
    saida_2 = put_suggestions.listar(conn)[0]
    assert saida_2["estado"] == "fechada"  # não retrocede
    assert saida_2["pnlPorAcao"] == saida_1["pnlPorAcao"]  # não recalcula
    assert resumo_2["linhas"] == 0  # terminal não aparece mais em listar_abertas


# --------------------------------------------------------------------------- #
# maybe_run — gate diário, marcador só no sucesso, nunca propaga
# --------------------------------------------------------------------------- #

def test_maybe_run_nao_roda_com_env_off(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    monkeypatch.setenv("B3_PUT_LIFECYCLE_OFF", "1")
    resultado = asyncio.run(put_lifecycle.maybe_run(conn))
    assert resultado is None
    assert db.kv_get(conn, put_lifecycle.K_LAST_RUN, user_id=None) is None


def test_maybe_run_nao_roda_duas_vezes_no_mesmo_dia(tmp_path):
    conn = _conn(tmp_path)
    hoje = put_lifecycle.datetime.now(put_lifecycle.BRT).date().isoformat()
    db.kv_set(conn, put_lifecycle.K_LAST_RUN, hoje, user_id=None)
    chamado = []
    original = put_lifecycle.run_diario
    put_lifecycle.run_diario = lambda c, now=None: (chamado.append(1) or {"linhas": 0, "avancos": 0, "pendentes": 0, "porEstado": {}, "erros": []})
    try:
        resultado = asyncio.run(put_lifecycle.maybe_run(conn))
    finally:
        put_lifecycle.run_diario = original
    assert resultado is None
    assert chamado == []


def test_maybe_run_grava_marcador_so_no_sucesso(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    monkeypatch.setattr(put_lifecycle, "should_run", lambda now=None, last_date=None: True)
    monkeypatch.setattr(put_lifecycle, "run_diario", lambda c, now=None: {
        "linhas": 0, "avancos": 0, "pendentes": 0, "porEstado": {}, "erros": [],
    })
    resultado = asyncio.run(put_lifecycle.maybe_run(conn))
    assert resultado is not None
    assert db.kv_get(conn, put_lifecycle.K_LAST_RUN, user_id=None) is not None


def test_maybe_run_nunca_propaga_excecao_e_nao_grava_marcador(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    monkeypatch.setattr(put_lifecycle, "should_run", lambda now=None, last_date=None: True)

    def _explode(c, now=None):
        raise RuntimeError("boom put-lifecycle")

    monkeypatch.setattr(put_lifecycle, "run_diario", _explode)
    resultado = asyncio.run(put_lifecycle.maybe_run(conn))
    assert resultado is None
    assert db.kv_get(conn, put_lifecycle.K_LAST_RUN, user_id=None) is None
    assert put_lifecycle.LAST_RUN["erro"] is not None
