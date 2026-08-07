"""Fase B do plano (docs/plano-operador-entrada-e-modos.md) — entrada
automática: compra 1 lote quando o TIMING do dia confirma gatilho de entrada,
dentro do % do caixa configurado (`allocPct`), só em Modo Operador com
`entradaAuto` ligado.

Testa `agent._avaliar_entradas` diretamente (núcleo da Fase B), no mesmo
espírito de `test_timing_watch.py`: sem passar pelo scheduler/relógio real,
com `agora` explícito. `radar_stored`/`intra_stored` são gravados no kv
(via `radar_daily.store_result`/`intraday.CHAVE`) porque a função os carrega
ela mesma internamente — só roda essa leitura quando `entradaAuto` já é True
(early-return-guard), então os testes que NÃO ligam a feature nem precisam
semear esses dados.
"""
import asyncio
import os
import tempfile
from datetime import datetime

from app import agent, candles, db, intraday, radar_daily, store, timing_watch

HOJE = "2026-08-07"
AGORA = datetime(2026, 8, 7, 14, 30, tzinfo=intraday.BRT)   # pregão aberto


def _conn(app_mode="operador"):
    d = tempfile.mkdtemp(prefix="b3_entrada_auto_")
    c = db.connect(os.path.join(d, "b3.db"))
    store.ensure_defaults(c, user_id="u1")
    # limpa as posições de exemplo do default_state — os testes controlam
    # `positions` explicitamente (passado como parâmetro para a função).
    db.kv_set(c, "positions", [], user_id="u1")
    if app_mode == "operador":
        store.set_config(c, {"operadorTermo": {"aceitoEm": "2026-01-01", "versao": "1"},
                              "appMode": "operador"}, user_id="u1")
    elif app_mode is not None:
        store.set_config(c, {"appMode": app_mode}, user_id="u1")
    return c


def _seed_radar(c, planos):
    """`planos`: [(ticker, decisao, entrada, stop, risco), ...] ou tuplas
    curtas (ticker, decisao) com a geometria padrão (gatilho em close=39.0)."""
    period = candles.normalize_period(None)
    results = []
    for item in planos:
        if len(item) == 2:
            t, decisao = item
            entrada, stop, risco = 38.5, 36.2, 2.3
        else:
            t, decisao, entrada, stop, risco = item
        lado = "alta" if decisao == "COMPRAR" else "baixa"
        results.append({"ticker": t, "veredito": "Estudar",
                        "plano": {"decisao": decisao, "lado": lado, "entrada": entrada,
                                  "stop": stop, "riscoPorAcao": risco, "setup": "rompimento"}})
    return radar_daily.store_result(c, period, {"results": results}, "manual")


def _seed_intra(c, closes: dict, hora="14:15", dia=HOJE, at=None):
    as_of = f"{dia} {hora}"
    payload = {"at": (at or AGORA).isoformat(), "asOf": as_of, "atLabel": hora,
               "universo": len(closes), "ativos": len(closes), "comLacuna": 0,
               "resultados": [{"ticker": t, "close": v, "asOf": as_of, "cobertura": 1.0,
                               "lacuna": False, "barraEmFormacao": False}
                              for t, v in closes.items()],
               "erros": []}
    db.kv_set(c, intraday.CHAVE, payload, user_id=None)
    return payload


def _run(c, ag, app_mode, positions=None, executed=0, agora=AGORA):
    par = agent.agent_params(ag, app_mode=app_mode)
    events = []
    ex = asyncio.run(agent._avaliar_entradas(c, "u1", ag, par, app_mode, positions or [],
                                             executed, events, agora=agora))
    return ex, events


# ---------------------------------------------------------------------------
# entradaAuto=False (default) — nenhuma mudança de comportamento.
# ---------------------------------------------------------------------------
def test_entrada_auto_desligada_nao_executa():
    c = _conn("operador")
    db.kv_set(c, "cash", 100000.0, user_id="u1")
    _seed_radar(c, [("PETR4", "COMPRAR")])
    _seed_intra(c, {"PETR4": 39.0})
    ag = {"entradaAuto": False, "allocPct": 5, "maxOpsDia": 3}
    ex, events = _run(c, ag, "operador")
    assert ex == 0
    assert events == []
    assert store.get(c, "positions", user_id="u1") == []


# ---------------------------------------------------------------------------
# Defesa em profundidade: fora do Modo Operador, mesmo com entradaAuto=True
# salvo (a trava de `set_agent` já impede isso na escrita — este teste cobre
# a LEITURA/execução direto, caso o dado tenha chegado salvo de outra via).
# ---------------------------------------------------------------------------
def test_entrada_auto_ligada_fora_do_operador_nao_executa():
    c = _conn("estudo")
    db.kv_set(c, "cash", 100000.0, user_id="u1")
    _seed_radar(c, [("PETR4", "COMPRAR")])
    _seed_intra(c, {"PETR4": 39.0})
    ag = {"entradaAuto": True, "allocPct": 5, "maxOpsDia": 3}
    ex, events = _run(c, ag, "estudo")
    assert ex == 0
    assert events == []
    assert store.get(c, "positions", user_id="u1") == []


# ---------------------------------------------------------------------------
# Caminho feliz: Operador, entradaAuto=True, gatilho COMPRAR, caixa suficiente.
# ---------------------------------------------------------------------------
def test_executa_1_lote_no_gatilho_de_compra():
    c = _conn("operador")
    db.kv_set(c, "cash", 100000.0, user_id="u1")
    _seed_radar(c, [("PETR4", "COMPRAR")])
    _seed_intra(c, {"PETR4": 39.0})
    ag = {"entradaAuto": True, "allocPct": 5, "maxOpsDia": 3, "maxValorOp": 0}
    ex, events = _run(c, ag, "operador")
    assert ex == 1
    positions = store.get(c, "positions", user_id="u1")
    assert len(positions) == 1
    pos = positions[0]
    assert pos["t"] == "PETR4"
    # orçamento = 5% de 100000 = 5000; 5000 // 39.0 // 100 * 100 = 100 (1 lote)
    assert pos["qty"] == 100
    assert pos["avg"] == 39.0
    assert store.get(c, "cash", user_id="u1") == round(100000.0 - 100 * 39.0, 2)
    assert any(e["kind"] == "buy" and "Entrada automática" in e["text"] for e in events)
    # dedupe com o vigia do gatilho (timing_watch): ticker marcado avisado hoje
    tw = db.kv_get(c, "timingWatch", None, user_id="u1")
    assert tw is not None
    assert "PETR4" in tw["avisados"]
    assert tw["ultimo"]["PETR4"] == "gatilho"


# ---------------------------------------------------------------------------
# D5 — lado VENDER nunca executa automaticamente, mesmo com gatilho batido.
# ---------------------------------------------------------------------------
def test_lado_vender_nunca_executa():
    c = _conn("operador")
    db.kv_set(c, "cash", 100000.0, user_id="u1")
    # decisao VENDER, alta=False: cruzou quando close <= entrada; excedente
    # 0,5 fica dentro da zona de perseguição (0,5 * risco 2,3 = 1,15) => gatilho
    _seed_radar(c, [("PETR4", "VENDER", 38.5, 40.8, 2.3)])
    _seed_intra(c, {"PETR4": 38.0})
    ag = {"entradaAuto": True, "allocPct": 5, "maxOpsDia": 3}
    ex, events = _run(c, ag, "operador")
    assert ex == 0
    assert store.get(c, "positions", user_id="u1") == []
    assert not any(e["kind"] == "buy" for e in events)


# ---------------------------------------------------------------------------
# Orçamento insuficiente para 1 lote — NUNCA arredonda para cima.
# ---------------------------------------------------------------------------
def test_orcamento_insuficiente_nao_arredonda_pra_cima():
    c = _conn("operador")
    db.kv_set(c, "cash", 10000.0, user_id="u1")
    _seed_radar(c, [("PETR4", "COMPRAR")])
    _seed_intra(c, {"PETR4": 39.0})
    # allocPct baixo: orçamento = 1% de 10000 = 100; 100 // 39 // 100 * 100 = 0
    ag = {"entradaAuto": True, "allocPct": 1, "maxOpsDia": 3}
    ex, events = _run(c, ag, "operador")
    assert ex == 0
    assert store.get(c, "positions", user_id="u1") == []
    assert any(e["kind"] == "warn" and "não cobre 1 lote" in e["text"] for e in events)


# ---------------------------------------------------------------------------
# Teto diário de operações — COMPARTILHADO com o lado de saída (D2): uma
# venda já executada no mesmo ciclo (`executed=1`) conta para o teto.
# ---------------------------------------------------------------------------
def test_max_ops_dia_combinado_com_saida_do_mesmo_ciclo():
    c = _conn("operador")
    db.kv_set(c, "cash", 100000.0, user_id="u1")
    _seed_radar(c, [("PETR4", "COMPRAR")])
    _seed_intra(c, {"PETR4": 39.0})
    ag = {"entradaAuto": True, "allocPct": 5, "maxOpsDia": 2}
    # 1 operação já contabilizada hoje (fora deste ciclo) + 1 já executada
    # NESTE ciclo (a venda que rodou antes, no mesmo `_run_cycle_inner`) = 2,
    # já no teto — a entrada não deve rodar.
    ag["opsToday"] = 1
    ag["opsDate"] = agent._today()
    ex, events = _run(c, ag, "operador", executed=1)
    assert ex == 1  # não incrementou (nenhuma execução nova)
    assert store.get(c, "positions", user_id="u1") == []
    assert any(e["kind"] == "warn" and "Teto diário" in e["text"] for e in events)


def test_max_ops_dia_nao_atingido_ainda_executa():
    """Guardião: o mesmo cenário, com folga no teto, executa normalmente."""
    c = _conn("operador")
    db.kv_set(c, "cash", 100000.0, user_id="u1")
    _seed_radar(c, [("PETR4", "COMPRAR")])
    _seed_intra(c, {"PETR4": 39.0})
    ag = {"entradaAuto": True, "allocPct": 5, "maxOpsDia": 5}
    ex, events = _run(c, ag, "operador", executed=1)
    assert ex == 2
    assert len(store.get(c, "positions", user_id="u1")) == 1


# ---------------------------------------------------------------------------
# Teto por valor de operação.
# ---------------------------------------------------------------------------
def test_max_valor_op_excedido_nao_executa():
    c = _conn("operador")
    db.kv_set(c, "cash", 100000.0, user_id="u1")
    _seed_radar(c, [("PETR4", "COMPRAR")])
    _seed_intra(c, {"PETR4": 39.0})
    # orçamento = 20% de 100000 = 20000; qty = 500 (lotes de 100); valor_op = 19500
    ag = {"entradaAuto": True, "allocPct": 20, "maxOpsDia": 3, "maxValorOp": 1000.0}
    ex, events = _run(c, ag, "operador")
    assert ex == 0
    assert store.get(c, "positions", user_id="u1") == []
    assert any(e["kind"] == "warn" and "Teto por operação" in e["text"] for e in events)


# ---------------------------------------------------------------------------
# Ticker já em posição é excluído do universo avaliado (não duplica entrada).
# ---------------------------------------------------------------------------
def test_ticker_ja_em_posicao_e_excluido():
    c = _conn("operador")
    db.kv_set(c, "cash", 100000.0, user_id="u1")
    _seed_radar(c, [("PETR4", "COMPRAR")])
    _seed_intra(c, {"PETR4": 39.0})
    ag = {"entradaAuto": True, "allocPct": 5, "maxOpsDia": 3}
    ja_posicionado = [{"t": "PETR4", "qty": 100, "avg": 35.0, "stop": None, "alvo": None}]
    ex, events = _run(c, ag, "operador", positions=ja_posicionado)
    assert ex == 0
    assert not any(e["kind"] == "buy" for e in events)
    assert store.get(c, "cash", user_id="u1") == 100000.0  # não mexeu no caixa


# ---------------------------------------------------------------------------
# Dedupe real: depois da entrada automática, o vigia do gatilho não reavisa
# o mesmo ticker no mesmo dia (o push "condição atingida" não compete com a
# compra já feita).
# ---------------------------------------------------------------------------
def test_apos_entrada_automatica_vigia_nao_reavisa_o_mesmo_ticker():
    c = _conn("operador")
    db.kv_set(c, "cash", 100000.0, user_id="u1")
    radar = _seed_radar(c, [("PETR4", "COMPRAR")])
    intra = _seed_intra(c, {"PETR4": 39.0})
    ag = {"entradaAuto": True, "allocPct": 5, "maxOpsDia": 3}
    ex, events = _run(c, ag, "operador")
    assert ex == 1

    hoje = AGORA.date().isoformat()
    estado = db.kv_get(c, "timingWatch", None, user_id="u1")
    novos, _ = timing_watch.avaliar_usuario(radar, intra, ["PETR4"], estado, hoje, agora=AGORA)
    assert novos == [], "o vigia reavisaria um ticker que a entrada automática já comprou"
