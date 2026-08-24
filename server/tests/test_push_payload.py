"""Quick task 260824-i45 (itens 1, 2 e 3) — o PAYLOAD do push do Operador.

Três defeitos distintos, um arquivo de guardiões:

  1. **Destino.** `main._notify` não aceitava `extra`, então todo push do funil
     D chegava sem `data.t`. `web/src/notify.js:382` valida o ticker contra
     `^[A-Z]{4}\\d{1,2}$` e DESCARTA EM SILÊNCIO o que não casa — sem `t` no
     payload o toque abria o app sem destino. O mecanismo de navegação do lado
     do app já existia e não muda; ele só passa a ser alimentado.
  2. **Marco.** `agent.py` mandava o literal `"Agente Boris+ (simulado)"` como
     título dos dois funis (ordem pendente e ciclo do Operador). O `tag` do
     evento estruturado existia e era jogado fora.
  3. **Resultado.** `store.sell` DEVOLVE o `pnl` (`store.py:650`) e o call site
     do stop/alvo descartava o retorno.

REGRA TRANSVERSAL desta suíte: **asserção de conteúdo nunca mora dentro de uma
corrotina que o código de produção aguarda sob `except Exception`.** Os dois
funis de push em `agent.py` (`:1225`, `:1262`) engolem qualquer exceção do
`notify_push` — e `AssertionError` é subclasse de `Exception`. Todo espião
aqui SÓ COLETA; as asserções ficam depois do `asyncio.run(...)`.
"""
import asyncio
import os
import pathlib
import re
import tempfile
from datetime import datetime

import pytest

from app import agent, candles, db, intraday, pending_orders, radar_daily, signal_ledger, skill_ref, store

HOJE = "2026-08-07"
AGORA = datetime(2026, 8, 7, 14, 30, tzinfo=intraday.BRT)   # pregão aberto
SETUP = "IFR2 (alta)"  # nome real do catálogo (server/app/setups.py)

TICKER_RE = re.compile(r"^[A-Z]{4}\d{1,2}$")   # o MESMO de web/src/notify.js:382

_SRC_AGENT = (pathlib.Path(__file__).resolve().parents[1] / "app" / "agent.py").read_text(encoding="utf-8")


# --------------------------------------------------------------- fixtures ---
def _conn(app_mode="operador"):
    d = tempfile.mkdtemp(prefix="b3_push_payload_")
    c = db.connect(os.path.join(d, "b3.db"))
    store.ensure_defaults(c, user_id="u1")
    db.kv_set(c, "positions", [], user_id="u1")
    store.set_config(c, {"operadorTermo": {"aceitoEm": "2026-01-01", "versao": "1"},
                         "appMode": app_mode}, user_id="u1")
    return c


def _seed(c, positions, ag):
    db.kv_set(c, "positions", positions, user_id="u1")
    db.kv_set(c, "cash", 100000.0, user_id="u1")
    db.kv_set(c, "agent", {"autonomous": True, **ag}, user_id="u1")


def _quotes(prices):
    async def getter(tickers):
        return {t: {"price": prices.get(t)} for t in tickers}
    return getter


def _run(c, prices):
    return asyncio.run(agent.run_cycle_for(c, "u1", _quotes(prices)))


class _Espiao:
    """Espião de 4 argumentos que SÓ COLETA (ver docstring do módulo)."""

    def __init__(self):
        self.pushes = []

    async def __call__(self, uid, title, body, extra=None):
        self.pushes.append({"uid": uid, "title": title, "body": body, "extra": extra})


# ---------------------------------------------- item 2: vocabulário do título
def test_push_titulo_nomeia_o_marco_nos_dois_modos():
    for tag in ("stop", "alvo", "entrada-auto", "pendente-executada", "pendente-cancelada"):
        op = skill_ref.push_titulo("operador", tag, "PETR4")
        ed = skill_ref.push_titulo("educacional", tag, "PETR4")
        assert "PETR4" in op and "PETR4" in ed
        assert op != skill_ref.PUSH_TITULOS["operador"]["generico"]
        assert ed != skill_ref.PUSH_TITULOS["educacional"]["generico"]
    # vozes distintas onde o vocabulário do produto exige (mesa × professor)
    assert skill_ref.push_titulo("operador", "stop", "PETR4") \
        != skill_ref.push_titulo("educacional", "stop", "PETR4")


def test_push_titulo_degrada_sem_frase_quebrada():
    """Degradação definida, no mesmo idioma de `timing_txt`: nunca KeyError,
    nunca `{t}` cru, nunca sufixo pendurado (`"Stop acionado (simulado) · "`)."""
    for modo in ("operador", "educacional"):
        generico = skill_ref.PUSH_TITULOS[modo]["generico"]
        assert skill_ref.push_titulo(modo, "tag-que-nao-existe", "PETR4") == generico
        assert skill_ref.push_titulo(modo, None, "PETR4") == generico
        assert skill_ref.push_titulo(modo, "", "PETR4") == generico
        # evento sem ticker (contrato de opção filtrado): título INTEIRO
        assert skill_ref.push_titulo(modo, "stop", "") == generico
        assert "{t}" not in skill_ref.push_titulo(modo, "stop", "PETR4")


def test_push_titulo_modo_desconhecido_cai_no_educacional():
    assert skill_ref.push_titulo("marciano", "stop", "PETR4") \
        == skill_ref.push_titulo("educacional", "stop", "PETR4")
    assert skill_ref.push_titulo(None, "alvo", "VALE3") \
        == skill_ref.push_titulo("educacional", "alvo", "VALE3")


def test_todo_titulo_declara_que_a_operacao_e_simulada():
    """CLAUDE.md princípio 1. Os corpos de entrada automática
    (`agent.py:697-699`) e de ordem pendente (`pending_orders.py:289-290`) NÃO
    dizem "simulado" — o título é o único lugar que sustenta a declaração na
    tela de bloqueio."""
    for modo, d in skill_ref.PUSH_TITULOS.items():
        for tag, frase in d.items():
            assert "simulad" in frase.lower(), f"{modo}/{tag} não declara simulação: {frase!r}"


def test_titulos_nao_carregam_imperativo_de_operacao():
    """Mesmo guardrail regulatório do `push_body` do Radar
    (`test_push_body_respeita_o_guardrail_regulatorio`): o título descreve o que
    o SIMULADOR fez, nunca o que a pessoa deve fazer."""
    for d in skill_ref.PUSH_TITULOS.values():
        for frase in d.values():
            baixo = frase.lower()
            for pat in (r"\bcompre\b", r"\bvenda\s+(agora|j[áa])", r"\bentre\s+agora\b",
                        r"\bdeve\s+comprar\b", r"\brecomendo\s+(comprar|vender)\b"):
                assert not re.search(pat, baixo), f"título com imperativo: {frase!r}"


# --------------------------------- itens 1+2+3: o evento do ciclo do Operador
def test_ciclo_no_stop_carrega_ticker_tag_e_pnl_do_motor():
    c = _conn()
    _seed(c, [{"t": "PETR4", "qty": 100, "avg": 40.0, "stop": 38.0, "alvo": 45.0}],
          {"serverEnabled": True, "mode": "executar", "maxOpsDia": 3})
    r = _run(c, {"PETR4": 37.5})
    assert r["executed"] == 1
    ev = next(e for e in r["events"] if e.get("kind") == "buy")
    assert ev["t"] == "PETR4"
    assert ev["tag"] == "stop"
    # o número é o MESMO que store.sell gravou no histórico — motor
    # determinístico, CLAUDE.md princípio 5
    historico = store.get(c, "history", user_id="u1")
    assert ev["pnl"] == historico[0]["pnl"]
    assert "Resultado realizado" in ev["text"]
    assert f"R$ {historico[0]['pnl']:+.2f}" in ev["text"]


def test_ciclo_no_alvo_marca_a_tag_do_alvo():
    c = _conn()
    _seed(c, [{"t": "VALE3", "qty": 100, "avg": 40.0, "stop": 30.0, "alvo": 45.0}],
          {"serverEnabled": True, "mode": "executar", "maxOpsDia": 3})
    r = _run(c, {"VALE3": 46.0})
    ev = next(e for e in r["events"] if e.get("kind") == "buy")
    assert ev["t"] == "VALE3" and ev["tag"] == "alvo"
    assert ev["pnl"] is not None and ev["pnl"] > 0


def test_ciclo_devolve_o_appmode_para_o_funil_de_push():
    """O modo já era lido dentro do ciclo (`_run_cycle_inner`) e morria ali —
    o funil D3 precisaria de uma leitura de kv extra por usuário por tick."""
    c = _conn("operador")
    _seed(c, [], {"serverEnabled": True, "mode": "executar"})
    r = _run(c, {})
    assert r["appMode"] == "operador"


def test_pnl_vem_do_RETORNO_de_store_sell_nao_de_recomposicao():
    """Âncora de PROVENIÊNCIA (idioma de `test_run_daily_usa_o_push_body`).

    A igualdade numérica do teste acima NÃO prova origem: este call site vende
    sempre TOTAL (sem `qty=`), então um `round((price - pos["avg"]) * pos["qty"], 2)`
    recomposto daria exatamente o mesmo número e passaria. O princípio 5 do
    CLAUDE.md precisa de âncora de FONTE, e ela tem que rodar DENTRO da suíte —
    um `grep` no critério de aceite não roda no CI."""
    assert _SRC_AGENT.count("pnl = store.sell(") == 1, \
        "o pnl tem que vir do RETORNO de store.sell (store.py:650)"
    assert "Resultado realizado: R$ {pnl:+.2f}" in _SRC_AGENT, \
        "o texto formata o pnl recebido, não um recomposto"
    entre = _SRC_AGENT.split("pnl = store.sell(")[1].split("events.append")[0]
    assert 'pos["avg"]' not in entre, \
        "nada de recompor (price - avg) * qty entre a venda e o evento (CLAUDE.md princípio 5)"


def test_agent_nao_manda_mais_o_titulo_generico_literal():
    """Âncora de fonte do item 2: o literal migrou para
    `skill_ref.PUSH_TITULOS["educacional"]["generico"]` e nenhum `notify_push`
    de `agent.py` volta a escrevê-lo à mão."""
    assert "Agente Boris+ (simulado)" not in _SRC_AGENT
    assert _SRC_AGENT.count("skill_ref.push_titulo(") == 2, \
        "os DOIS funis (ordem pendente e ciclo do Operador) derivam o título do evento"


# --------------------------------------------- item 1: entrada automática
@pytest.fixture
def _setup_elegivel(monkeypatch):
    """ADR-017 Adendo 2: `_avaliar_entradas` só executa com o setup medido como
    elegível. Mesmo stub de `test_entrada_automatica.py` — aqui o objeto sob
    teste é o EVENTO (t/tag), não o gate."""
    signal_ledger.reset_cache()
    monkeypatch.setattr(
        signal_ledger, "historico_snapshot",
        lambda conn, **kw: {SETUP: {"expR": 0.072, "n": 2934, "medidoAte": "2026-08-20",
                                    "elegivel": True, "insuficiente": False,
                                    "expRJanela": 0.072, "nJanela": 2934,
                                    "janelaRef": "2025", "calculadoEm": "2026-08-21"}})


def test_entrada_automatica_carrega_ticker_e_tag(_setup_elegivel):
    c = _conn("operador")
    db.kv_set(c, "cash", 100000.0, user_id="u1")
    db.kv_set(c, "watchlist", ["PETR4"], user_id="u1")
    period = candles.normalize_period(None)
    radar_daily.store_result(c, period, {"results": [
        {"ticker": "PETR4", "veredito": "Estudar",
         "plano": {"decisao": "COMPRAR", "lado": "alta", "entrada": 38.5,
                   "stop": 36.2, "riscoPorAcao": 2.3, "setup": SETUP}}]}, "manual")
    as_of = f"{HOJE} 14:15"
    db.kv_set(c, intraday.CHAVE, {
        "at": AGORA.isoformat(), "asOf": as_of, "atLabel": "14:15",
        "universo": 1, "ativos": 1, "comLacuna": 0,
        "resultados": [{"ticker": "PETR4", "close": 39.0, "asOf": as_of,
                        "cobertura": 1.0, "lacuna": False, "barraEmFormacao": False}],
        "erros": []}, user_id=None)
    ag = {"entradaAuto": True, "allocPct": 5, "maxOpsDia": 3, "maxValorOp": 0}
    par = agent.agent_params(ag, app_mode="operador")
    events = []
    ex = asyncio.run(agent._avaliar_entradas(c, "u1", ag, par, "operador", [], 0, events,
                                             agora=AGORA))
    assert ex == 1
    ev = next(e for e in events if e.get("kind") == "buy")
    assert ev["t"] == "PETR4" and ev["tag"] == "entrada-auto"
    assert "Entrada automática" in ev["text"]   # texto de hoje preservado


# --------------------------------------- item 1: a FIAÇÃO real do scheduler
def test_scheduler_push_do_operador_leva_marco_e_destino(monkeypatch):
    """Guardião do caminho REAL: `scheduler_loop` → `notify_push`. Título com o
    marco, `extra["t"]` no formato que o cliente valida. O espião SÓ COLETA."""
    c = _conn()
    _seed(c, [{"t": "PETR4", "qty": 100, "avg": 40.0, "stop": 38.0, "alvo": 45.0}],
          {"serverEnabled": True, "mode": "executar", "maxOpsDia": 3, "intervalMin": 1})
    monkeypatch.setattr(agent, "in_market_hours", lambda *a, **k: True)
    monkeypatch.setattr(agent, "kill_switch_on", lambda: False)
    agent.LAST_USER_RUN.clear()
    espiao = _Espiao()

    asyncio.run(agent.scheduler_loop(c, _quotes({"PETR4": 37.5}),
                                     notify_push=espiao, once=True))

    assert len(espiao.pushes) == 1
    p = espiao.pushes[0]
    assert p["title"] != "Agente Boris+ (simulado)"
    assert "PETR4" in p["title"] and "simulad" in p["title"].lower()
    assert p["extra"] and TICKER_RE.match(p["extra"]["t"] or ""), \
        "sem `t` no formato de notify.js:382 o cliente descarta em silêncio"
    assert p["extra"]["kind"] == "operador"
    assert "Resultado realizado" in p["body"]


def test_scheduler_evento_sem_ticker_valido_nao_manda_t_morto(monkeypatch):
    """Um `t` fora de `^[A-Z]{4}\\d{1,2}$` (contrato de opção, por ex.) seria
    descartado pelo cliente — mandar é peso morto no payload e ruído no
    diagnóstico. O `extra` sai, o `t` não."""
    c = _conn()
    _seed(c, [], {"serverEnabled": True, "mode": "executar", "intervalMin": 1})
    monkeypatch.setattr(agent, "in_market_hours", lambda *a, **k: True)
    monkeypatch.setattr(agent, "kill_switch_on", lambda: False)
    agent.LAST_USER_RUN.clear()

    async def _fake_cycle(conn, uid, *a, **kw):
        return {"events": [{"time": "07/08 14:30", "kind": "buy",
                            "t": "PETRJ350", "tag": "alvo",
                            "text": "Opção fechada (simulado)."}],
                "executed": 1, "appMode": "operador"}

    monkeypatch.setattr(agent, "run_cycle_for", _fake_cycle)
    espiao = _Espiao()
    asyncio.run(agent.scheduler_loop(c, _quotes({}), notify_push=espiao, once=True))

    assert len(espiao.pushes) == 1
    extra = espiao.pushes[0]["extra"]
    assert "t" not in extra, "ticker fora do formato do cliente não vai no payload"
    assert extra["kind"] == "operador"


# ------------------------------------------------ item 1: ordens pendentes
def test_eventos_de_ordem_pendente_carregam_o_ticker():
    """`pending_orders` já tinha `tag` nos 3 eventos e não tinha `t` — o ticker
    ficava só no texto, e o funil de push não tem como extraí-lo de lá."""
    c = _conn()
    db.kv_set(c, "cash", 100000.0, user_id="u1")
    pending_orders.criar_compra(c, "u1", "EEEE3", 100, 10.0)

    def _price(t):
        return {"price": 10.5}

    eventos = asyncio.run(pending_orders.executar_pendentes(c, "u1", _price))
    assert eventos and all(e.get("t") == "EEEE3" for e in eventos)
    assert eventos[0]["tag"] == "pendente-executada"
