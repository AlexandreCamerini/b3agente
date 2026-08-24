"""Quick task 260824-i45 (itens 4 e 6) — o evento de mercado vira RASTRO.

Item 4 (S4 do brief): existiam três estruturas que não conversavam — `history`,
`agent.events` ("EVENTOS E AVISOS RECENTES", `App.jsx:4301-4309`) e `agentLog`
(tela técnica "Logs & Debug"). O gatilho e o Radar não escreviam em nenhuma das
duas primeiras: o único rastro do gatilho era a linha de ENTREGA
(`agent.py:1034`, "Aviso enviado a 1/1 aparelho(s)"), que registra o ENVIO e
não o evento de mercado, e o Radar era fire-and-forget com `except: pass`.
Decisão D3: o "log" fecha em `agent.events`, que já existe e já tem tela —
central de notificações recebidas foi explicitamente descartada.

Item 6: o job do Radar às 08:45 é prévia PRÉ-ABERTURA por desenho (decisão D1,
`agent.py:1104-1107` documenta a escolha de `is_trading_day` em vez de
`in_market_hours`). O horário FICA; o defeito era o texto não dizer isso, o que
fazia o push ler como alerta fora de hora.

REGRA TRANSVERSAL desta suíte: **asserção de conteúdo nunca mora dentro de uma
corrotina que o código de produção aguarda sob `except Exception`.** Prova:
`radar_daily.run_daily` e `agent._avisar_gatilhos` aguardam o `notify_push`
dentro de `except Exception`, e `AssertionError` é subclasse de `Exception`.
Todo fake aqui SÓ COLETA — exceto o de `test_..._push_que_levanta`, onde o
levantamento É o comportamento sob teste, não uma asserção engolida.
"""
import asyncio
import os
import pathlib
import sqlite3
import tempfile

import pytest

from app import agent, db, push, radar_daily, skill_ref, store, timing_watch

_SRC_RADAR = (pathlib.Path(__file__).resolve().parents[1] / "app" / "radar_daily.py").read_text(encoding="utf-8")
_SRC_AGENT = (pathlib.Path(__file__).resolve().parents[1] / "app" / "agent.py").read_text(encoding="utf-8")

CORPO_GATILHO = ("A condição de estudo foi atingida na vela de 14:15 — o nível do plano "
                 "de estudo foi alcançado. Nada foi comprado.")


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def _conn_mem():
    c = sqlite3.connect(":memory:")
    db.init_db(c)
    return c


def _conn_arquivo():
    d = tempfile.mkdtemp(prefix="b3_registro_evento_")
    return db.connect(os.path.join(d, "b3.db"))


def _fake_fetch(symbol, rng):
    async def go():
        base = 10.0 + (hash(symbol) % 7)
        closes = [base + i * 0.1 for i in range(260)]
        candles = [{"time": 1700000000 + i * 86400, "open": v, "high": v * 1.01,
                    "low": v * 0.99, "close": v, "volume": 1000000} for i, v in enumerate(closes)]
        return {"candles": candles, "currency": "BRL"}
    return go()


@pytest.fixture
def _universo():
    os.environ["B3_SCAN_UNIVERSE"] = "AAAA3,BBBB3"
    yield
    os.environ.pop("B3_SCAN_UNIVERSE", None)


def _eventos(conn, uid):
    return (store.get(conn, "agent", user_id=uid) or {}).get("events") or []


# ======================================================= item 6: o TEXTO ====
def test_titulo_do_radar_diz_que_e_previa_pre_abertura():
    """D1: o horário das 08:45 é deliberado (pré-abertura, candle da véspera
    fechado). O que faltava era o texto assumir isso."""
    titulo = skill_ref.PUSH_RADAR["titulo"].lower()
    assert "prévia" in titulo or "previa" in titulo
    assert "pré-abertura" in titulo or "pre-abertura" in titulo


def test_corpo_do_radar_envelopa_o_texto_qa43_sem_perder_nada():
    """O texto novo ENVELOPA o de hoje — não substitui. Os guardiões de qa/43
    (`test_radar_daily.py:133-184`) continuam valendo palavra por palavra."""
    corpo = radar_daily.push_body({"results": [
        {"ticker": "VALE3", "confluencia": 100, "veredito": "Estudar baixa"},
        {"ticker": "PETR4", "confluencia": 86, "veredito": "Estudar alta"}]})
    baixo = corpo.lower()
    assert "pré-abertura" in baixo and "não abriu" in baixo
    assert "VALE3 100% estudar baixa" in corpo    # veredito junto do percentual
    assert "2 ativos analisados" in corpo


def test_corpo_vazio_do_radar_tambem_diz_pre_abertura():
    corpo = radar_daily.push_body({"results": [
        {"ticker": "VALE3", "confluencia": 0, "veredito": "Sem setup no momento"}]})
    baixo = corpo.lower()
    assert "pré-abertura" in baixo and "não abriu" in baixo
    assert "nenhum setup em destaque" in corpo
    assert "1 ativo(s) analisados" in corpo
    assert "VALE3" not in corpo                   # confluência 0 não é destaque


def test_radar_nao_tem_mais_o_titulo_literal_antigo():
    """Âncora de fonte: o título saiu de `radar_daily.py` e passou a vir de
    `skill_ref.PUSH_RADAR` — fonte única, como todo vocabulário do produto."""
    assert "Radar do dia" not in _SRC_RADAR
    assert _SRC_RADAR.count("corpo = push_body(payload)") == 1, \
        "guardião de ancoragem qa/43 preservado"


# ========================================= item 4: registro do Radar ========
def test_run_daily_registra_o_evento_em_agent_events(_universo):
    c = _conn_mem()
    c.execute("INSERT INTO users(id, provider, provider_sub, created_at) VALUES ('u1','t','s1','2026-01-01')")
    c.execute("INSERT INTO users(id, provider, provider_sub, created_at) VALUES ('u2','t','s2','2026-01-01')")
    db.kv_set(c, "pushTokens", ["tok"], user_id="u1")   # só u1 ativou push
    enviados = []

    async def fake_push(uid, title, body):
        enviados.append((uid, title, body))             # SÓ COLETA

    r = _run(radar_daily.run_daily(c, _fake_fetch, notify_push=fake_push))

    assert [u for u, _t, _b in enviados] == ["u1"]
    evs = [e for e in _eventos(c, "u1") if e.get("tag") == "radar-diario"]
    assert len(evs) == 1
    assert evs[0]["text"] == radar_daily.push_body(r)
    assert evs[0]["text"] == enviados[0][2], "mesmo corpo no push e no rastro"
    assert evs[0]["kind"] == "info" and evs[0].get("time")
    # limite deliberado: o evento vai para a MESMA audiência do push
    assert [e for e in _eventos(c, "u2") if e.get("tag") == "radar-diario"] == []


def test_run_daily_registra_o_evento_mesmo_com_push_que_levanta(_universo):
    """Prova da separação dos dois `try`: o registro é o rastro DURÁVEL (a tela
    "EVENTOS E AVISOS RECENTES"); a entrega é efêmera. Um `except` só, como
    antes, fazia a falha de um matar o outro.

    Único fake do plano que LEVANTA de propósito — aqui o levantamento é o
    comportamento sob teste, não uma asserção engolida."""
    c = _conn_mem()
    c.execute("INSERT INTO users(id, provider, provider_sub, created_at) VALUES ('u1','t','s1','2026-01-01')")
    db.kv_set(c, "pushTokens", ["tok"], user_id="u1")

    async def push_quebrado(uid, title, body):
        raise RuntimeError("APNs fora do ar")

    r = _run(radar_daily.run_daily(c, _fake_fetch, notify_push=push_quebrado))

    evs = [e for e in _eventos(c, "u1") if e.get("tag") == "radar-diario"]
    assert len(evs) == 1 and evs[0]["text"] == radar_daily.push_body(r)


# ======================================== item 4: registro do gatilho =======
def _gatilho(monkeypatch, conn, tickers, sent=1):
    """Exercita a closure `_enviar` de `_avisar_gatilhos` — o objeto sob teste.
    `timing_watch.maybe_run` é substituído porque a varredura em si já tem
    suíte própria (`test_timing_watch.py`); o que muda aqui é o que `_enviar`
    faz com o aviso."""
    enviados = []

    async def fake_send(conn_, uid, titulo, corpo, **kw):
        enviados.append({"uid": uid, "titulo": titulo, "corpo": corpo, "extra": kw.get("extra")})
        return {"sent": sent, "total": 1, "detalhes": [] if sent else ["aparelho sem token"]}

    async def fake_maybe_run(conn_, radar_stored, intra_stored, notificar, agora=None):
        titulo = (f"{tickers[0]} · condição atingida na barra de 14:15" if len(tickers) == 1
                  else f"{len(tickers)} ativos · condição atingida na barra de 14:15")
        await notificar("u1", titulo, CORPO_GATILHO, list(tickers))
        return 1

    monkeypatch.setattr(push, "send_to_user", fake_send)
    monkeypatch.setattr(timing_watch, "maybe_run", fake_maybe_run)
    monkeypatch.delenv("B3_TIMING_PUSH_KILL", raising=False)
    _run(agent._avisar_gatilhos(conn))
    return enviados


def test_gatilho_de_um_ativo_registra_evento_com_o_ticker(monkeypatch):
    c = _conn_arquivo()
    store.ensure_defaults(c, user_id="u1")
    _gatilho(monkeypatch, c, ["PETR4"])

    evs = [e for e in _eventos(c, "u1") if e.get("tag") == "timing-gatilho"]
    assert len(evs) == 1
    assert evs[0]["t"] == "PETR4"
    assert evs[0]["text"] == CORPO_GATILHO, "o corpo canônico do push, sem redação nova"
    assert evs[0]["kind"] == "info"


def test_gatilho_agregado_nao_elege_um_ticker(monkeypatch):
    """Mesma intenção de `agent.py:1008-1015`: no agregado de N ativos, fixar
    `tickers[0]` seria o erro de ticker trocado que a reserva existe para
    evitar."""
    c = _conn_arquivo()
    store.ensure_defaults(c, user_id="u1")
    assert timing_watch.AGREGA_A_PARTIR_DE == 2
    _gatilho(monkeypatch, c, ["PETR4", "VALE3", "ITUB4"])

    evs = [e for e in _eventos(c, "u1") if e.get("tag") == "timing-gatilho"]
    assert len(evs) == 1 and evs[0]["t"] is None


def test_gatilho_sem_entrega_registra_o_evento_assim_mesmo(monkeypatch):
    """`send_to_user` devolvendo `sent=0` (APNs não configurado, aparelho sem
    token) é FALHA DE ENTREGA, não ausência de evento de mercado. As duas
    estruturas coexistem: o evento em `agent.events`, a entrega em `agentLog`."""
    c = _conn_arquivo()
    store.ensure_defaults(c, user_id="u1")
    _gatilho(monkeypatch, c, ["PETR4"], sent=0)

    evs = [e for e in _eventos(c, "u1") if e.get("tag") == "timing-gatilho"]
    assert len(evs) == 1 and evs[0]["t"] == "PETR4"
    log = store.get(c, "agentLog", user_id="u1") or []
    assert any("NÃO entregue" in e.get("text", "") for e in log), \
        "a linha de ENTREGA continua sendo escrita, sem alteração"


def test_agent_registra_o_evento_do_gatilho_na_fonte():
    """Âncora de fonte: `store.push_events` é chamado DENTRO de
    `_avisar_gatilhos`, não só no ciclo do Operador."""
    corpo = _SRC_AGENT.split("async def _avisar_gatilhos(")[1].split("\nasync def ")[0]
    assert "store.push_events(" in corpo
    assert '"tag": "timing-gatilho"' in corpo