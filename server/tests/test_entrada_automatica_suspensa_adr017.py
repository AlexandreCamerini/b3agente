"""ADR-017 (Decisão 3, 2026-08-20) — entrada automática do Modo Operador
suspensa até a seleção dinâmica (Bloco 1b) existir: nenhum setup hoje
sustenta operação automática com confiança (ADR-016: motor perde para o
acaso; IFR2, o único positivo, é modesto demais sozinho).

Guarda as DUAS pontas: a flag nasce ligada por padrão, e mesmo com
`entradaAuto=True` + Modo Operador + gatilho de compra pronto, nenhuma
posição é aberta enquanto a flag estiver ligada. `test_entrada_automatica.py`
cobre a mecânica em si (desliga a flag via fixture, com nota).
"""
import asyncio
import os
import tempfile
from datetime import datetime

from app import agent, candles, db, intraday, radar_daily, store

HOJE = "2026-08-07"
AGORA = datetime(2026, 8, 7, 14, 30, tzinfo=intraday.BRT)


def test_flag_nasce_ligada():
    assert agent.ENTRADA_AUTO_SUSPENSA_ADR017 is True


def test_suspensa_nao_executa_mesmo_com_gatilho_pronto():
    d = tempfile.mkdtemp(prefix="b3_entrada_auto_suspensa_")
    c = db.connect(os.path.join(d, "b3.db"))
    store.ensure_defaults(c, user_id="u1")
    db.kv_set(c, "positions", [], user_id="u1")
    store.set_config(c, {"operadorTermo": {"aceitoEm": "2026-01-01", "versao": "1"},
                          "appMode": "operador"}, user_id="u1")
    db.kv_set(c, "cash", 100000.0, user_id="u1")

    period = candles.normalize_period(None)
    radar_daily.store_result(c, period, {"results": [{
        "ticker": "PETR4", "veredito": "Estudar",
        "plano": {"decisao": "COMPRAR", "lado": "alta", "entrada": 38.5,
                  "stop": 36.2, "riscoPorAcao": 2.3, "setup": "rompimento"},
    }]}, "manual")
    db.kv_set(c, intraday.CHAVE, {
        "at": AGORA.isoformat(), "asOf": f"{HOJE} 14:15", "atLabel": "14:15",
        "universo": 1, "ativos": 1, "comLacuna": 0,
        "resultados": [{"ticker": "PETR4", "close": 39.0, "asOf": f"{HOJE} 14:15",
                         "cobertura": 1.0, "lacuna": False, "barraEmFormacao": False}],
        "erros": [],
    }, user_id=None)

    ag = {"entradaAuto": True, "allocPct": 5, "maxOpsDia": 3, "maxValorOp": 0}
    par = agent.agent_params(ag, app_mode="operador")
    events = []
    ex = asyncio.run(agent._avaliar_entradas(c, "u1", ag, par, "operador", [],
                                              0, events, agora=AGORA))
    assert ex == 0
    assert events == []
    assert store.get(c, "positions", user_id="u1") == []
