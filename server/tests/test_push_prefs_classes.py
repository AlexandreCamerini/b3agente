"""Quick task 260824-kc2 — preferência de push POR CLASSE de evento.

Até 2026-08-24 a preferência server-side tinha UM booleano (`gatilho`) e três
classes que não consultavam nada: quem registrou token recebia prévia do Radar,
execução de ordem e proteção (stop/alvo) sem controle nenhum. Este arquivo trava
o CONTROLE que nasceu aqui — e, principalmente, trava que ele não tire
notificação de ninguém.

DECISÃO TRAVADA (Alex, 2026-08-24), o eixo de tudo o que está aqui:
**quem já usa o app não perde notificação nenhuma.** `execucao`, `protecao` e
`radar` nascem LIGADAS; `gatilho` continua DESLIGADA (opt-in). A tensão com o
comentário de opt-in em `push.py` é declarada e resolvida lá: as três classes
não são alertas NOVOS, já chegavam a todo mundo com token — o que nasce é o
CONTROLE. Ver a NOTA ao lado de `PREFS_PADRAO`.

DOIS INVARIANTES, com teste próprio cada um:

  1. **Dois mestres, não um.** `config.notif.enabled` é o mestre das
     notificações LOCAIS do front; o mestre do push do SERVIDOR é o token
     registrado (ato explícito e separado). As três classes refinam o SEGUNDO,
     por isso não são conjunção com `enabled` — se fossem, todo usuário com
     token e `enabled` desligado pararia de receber execução e proteção.
  2. **Ninguém perde o `gatilho`.** O web não escreve essa chave (ver
     `web/tests/test_push_prefs_classes.mjs`), e do lado do servidor o que
     sustenta isso é a PARCIALIDADE do patch de `set_prefs`: chave ausente do
     patch fica exatamente como estava. Tem teste próprio aqui
     (`test_patch_parcial_nao_toca_chave_ausente`).

REGRA TRANSVERSAL desta suíte (mesma de `test_push_payload.py`, e ela custou um
guardião VÁCUO no quick task irmão): **asserção de conteúdo nunca mora dentro de
uma corrotina que o código de produção aguarda sob `except Exception`.**
`radar_daily.run_daily` e os dois funis de `agent.py` engolem qualquer exceção
do `notify_push`, e `AssertionError` é subclasse de `Exception`. Todo fake aqui
SÓ COLETA; as asserções ficam depois do `asyncio.run(...)`.
"""
import asyncio
import os
import pathlib
import sqlite3

import pytest

from app import agent, db, pending_orders, push, radar_daily, skill_ref, store
# Fixtures REUSADAS (não reimplementadas): `_conn` já monta banco temp com
# `u1` em Modo Operador com termo aceito, `_seed` semeia posição/caixa/agente e
# `_Espiao` é o espião de 4 argumentos que SÓ COLETA.
from tests.test_push_payload import _Espiao, _conn, _quotes, _seed

_SRC_AGENT = (pathlib.Path(__file__).resolve().parents[1] / "app" / "agent.py").read_text(encoding="utf-8")
_SRC_TIMING_WATCH = (pathlib.Path(__file__).resolve().parents[1] / "app" / "timing_watch.py").read_text(encoding="utf-8")


# --------------------------------------------------------------- fixtures ---
@pytest.fixture
def _universo():
    """Mesmo padrão de `test_push_registro_evento.py`: universo mínimo para a
    varredura do Radar rodar sem rede."""
    os.environ["B3_SCAN_UNIVERSE"] = "AAAA3,BBBB3"
    yield
    os.environ.pop("B3_SCAN_UNIVERSE", None)


def _fake_fetch(symbol, rng):
    async def go():
        base = 10.0 + (hash(symbol) % 7)
        closes = [base + i * 0.1 for i in range(260)]
        candles = [{"time": 1700000000 + i * 86400, "open": v, "high": v * 1.01,
                    "low": v * 0.99, "close": v, "volume": 1000000} for i, v in enumerate(closes)]
        return {"candles": candles, "currency": "BRL"}
    return go()


def _conn_radar():
    """Banco com a tabela `users` populada — `radar_daily._push_audience` varre
    `SELECT id FROM users` e cruza com quem tem `pushTokens`."""
    c = sqlite3.connect(":memory:")
    db.init_db(c)
    c.execute("INSERT INTO users(id, provider, provider_sub, created_at) VALUES ('u1','t','s1','2026-01-01')")
    db.kv_set(c, "pushTokens", ["tok"], user_id="u1")
    return c


def _coletor():
    """Fake de `notify_push` de 3 argumentos (assinatura do Radar) que SÓ
    COLETA — as asserções ficam fora da corrotina, ver docstring do módulo."""
    recebidos = []

    async def fake(uid, title, body):
        recebidos.append({"uid": uid, "title": title, "body": body})
    return fake, recebidos


def _eventos(conn, uid):
    return (store.get(conn, "agent", user_id=uid) or {}).get("events") or []


def _pregao_aberto(monkeypatch, sem_operador=False):
    monkeypatch.setattr(agent, "in_market_hours", lambda *a, **k: True)
    monkeypatch.setattr(agent, "kill_switch_on", lambda: False)
    if sem_operador:
        # Isola o funil de ORDEM PENDENTE: sem ninguém no laço do Operador, o
        # único push possível é o do bloco de pendentes (padrão de
        # `test_ordens_pendentes_scheduler._sem_operador`).
        monkeypatch.setattr(agent, "list_server_users", lambda conn: [])
    agent.LAST_USER_RUN.clear()


def _seed_opcao(c, stop=0.5):
    db.kv_set(c, "optionPositions", [{"id": "PETRH340", "underlying": "PETR4",
                                      "optionType": "call", "strike": 34.0,
                                      "expiration": "2099-01-01", "qty": 100,
                                      "avg": 1.0, "stop": stop, "alvo": None}], user_id="u1")
    db.kv_set(c, "positions", [], user_id="u1")
    db.kv_set(c, "cash", 100000.0, user_id="u1")
    db.kv_set(c, "agent", {"autonomous": True, "serverEnabled": True, "mode": "executar",
                           "maxOpsDia": 5, "intervalMin": 1}, user_id="u1")


def _option_getter(last_price=0.4, spot=32.0):
    async def getter(underlying, expiration):
        return {"providerStatus": "ok", "underlyingPrice": spot, "expiration": expiration,
                "calls": [{"contractSymbol": "PETRH340", "optionType": "call",
                           "strike": 34.0, "lastPrice": last_price}], "puts": []}
    return getter


# ===========================================================================
# O INVARIANTE — a razão de este arquivo existir. Os três casos passam pelos
# caminhos REAIS (run_daily / scheduler_loop), não por chamada direta ao gate:
# um teste que chamasse `classe_do_evento` sozinho ficaria verde mesmo se o
# call site nunca consultasse a preferência.
# ===========================================================================
def test_conta_sem_prefs_gravadas_continua_recebendo_a_previa_do_radar(_universo):
    """Ninguém perde notificação: prefs NUNCA gravadas herdam `radar: True` do
    `PREFS_PADRAO` pelo merge de `prefs_for`. Fica VERMELHO se o default for
    invertido — é a prova de mutação registrada no SUMMARY."""
    c = _conn_radar()
    assert db.kv_get(c, "pushPrefs", None, user_id="u1") is None, \
        "o cenário é justamente NÃO ter preferência gravada"
    fake, recebidos = _coletor()

    asyncio.run(radar_daily.run_daily(c, _fake_fetch, notify_push=fake))

    assert [r["uid"] for r in recebidos] == ["u1"]
    assert recebidos[0]["title"] == skill_ref.PUSH_RADAR["titulo"]


def test_conta_sem_prefs_gravadas_continua_recebendo_o_aviso_de_protecao(monkeypatch):
    """Caminho real do stop: `scheduler_loop` → ciclo do Operador → funil D3."""
    c = _conn()
    assert db.kv_get(c, "pushPrefs", None, user_id="u1") is None
    _seed(c, [{"t": "PETR4", "qty": 100, "avg": 40.0, "stop": 38.0, "alvo": 45.0}],
          {"serverEnabled": True, "mode": "executar", "maxOpsDia": 3, "intervalMin": 1})
    _pregao_aberto(monkeypatch)
    espiao = _Espiao()

    asyncio.run(agent.scheduler_loop(c, _quotes({"PETR4": 37.5}), notify_push=espiao, once=True))

    assert len(espiao.pushes) == 1
    assert "PETR4" in espiao.pushes[0]["title"]


def test_conta_sem_prefs_gravadas_continua_recebendo_a_execucao_de_ordem(monkeypatch):
    """Caminho real da ordem pendente: `scheduler_loop` → funil D2."""
    c = _conn()
    assert db.kv_get(c, "pushPrefs", None, user_id="u1") is None
    db.kv_set(c, "cash", 100000.0, user_id="u1")
    pending_orders.criar_compra(c, "u1", "EEEE3", 100, 10.0)
    _pregao_aberto(monkeypatch, sem_operador=True)
    espiao = _Espiao()

    asyncio.run(agent.scheduler_loop(c, _quotes({"EEEE3": 10.0}), notify_push=espiao, once=True))

    assert len(espiao.pushes) == 1
    assert "EEEE3" in espiao.pushes[0]["title"]


# ===========================================================================
# ISOLAMENTO — desligar uma classe silencia SÓ ela, e silencia a INTERRUPÇÃO,
# nunca o RASTRO.
# ===========================================================================
def test_radar_desligado_silencia_o_push_e_preserva_o_rastro(_universo):
    """A preferência mora sobre o `notify_push`, nunca sobre `store.push_events`
    nem sobre `_push_audience`: quem desligou o banner da prévia continua
    encontrando a leitura do dia em "EVENTOS E AVISOS RECENTES" (o rastro que o
    260824-i45 criou). Filtrar a audiência apagaria os dois de uma vez."""
    c = _conn_radar()
    push.set_prefs(c, "u1", {"radar": False})
    fake, recebidos = _coletor()

    r = asyncio.run(radar_daily.run_daily(c, _fake_fetch, notify_push=fake))

    assert recebidos == [], "com `radar` desligado o push da prévia não sai"
    evs = [e for e in _eventos(c, "u1") if e.get("tag") == "radar-diario"]
    assert len(evs) == 1 and evs[0]["text"] == radar_daily.push_body(r), \
        "o rastro em agent.events NÃO é gated pela preferência"


def test_protecao_desligada_silencia_o_stop_e_preserva_o_rastro(monkeypatch):
    c = _conn()
    push.set_prefs(c, "u1", {"protecao": False})
    _seed(c, [{"t": "PETR4", "qty": 100, "avg": 40.0, "stop": 38.0, "alvo": 45.0}],
          {"serverEnabled": True, "mode": "executar", "maxOpsDia": 3, "intervalMin": 1})
    _pregao_aberto(monkeypatch)
    espiao = _Espiao()

    asyncio.run(agent.scheduler_loop(c, _quotes({"PETR4": 37.5}), notify_push=espiao, once=True))

    assert espiao.pushes == []
    assert any(e.get("tag") == "stop" for e in _eventos(c, "u1")), \
        "a venda aconteceu e ficou registrada — o que sumiu foi só a interrupção"
    assert store.get(c, "positions", user_id="u1") == [], "o stop EXECUTOU do mesmo jeito"


def test_protecao_desligada_nao_silencia_a_execucao_de_ordem(monkeypatch):
    """Isolamento entre classes: `protecao` desligado, `execucao` intocado."""
    c = _conn()
    push.set_prefs(c, "u1", {"protecao": False})
    db.kv_set(c, "cash", 100000.0, user_id="u1")
    pending_orders.criar_compra(c, "u1", "EEEE3", 100, 10.0)
    _pregao_aberto(monkeypatch, sem_operador=True)
    espiao = _Espiao()

    asyncio.run(agent.scheduler_loop(c, _quotes({"EEEE3": 10.0}), notify_push=espiao, once=True))

    assert len(espiao.pushes) == 1, "desligar Proteção não pode calar Execução"


def test_execucao_desligada_silencia_a_ordem_pendente(monkeypatch):
    c = _conn()
    push.set_prefs(c, "u1", {"execucao": False})
    db.kv_set(c, "cash", 100000.0, user_id="u1")
    pending_orders.criar_compra(c, "u1", "EEEE3", 100, 10.0)
    _pregao_aberto(monkeypatch, sem_operador=True)
    espiao = _Espiao()

    asyncio.run(agent.scheduler_loop(c, _quotes({"EEEE3": 10.0}), notify_push=espiao, once=True))

    assert espiao.pushes == []
    assert pending_orders.listar(c, user_id="u1") == [], "a ordem executou; só o aviso calou"


# ===========================================================================
# FAIL-OPEN — tag desconhecida ENVIA. Unitário e comportamental: sem o
# comportamental, um "cleanup" futuro que fizesse a função cair num default
# silenciaria evento sem nada ficar vermelho.
# ===========================================================================
def test_classe_do_evento_degrada_para_none():
    assert push.classe_do_evento(None) is None
    assert push.classe_do_evento("") is None
    assert push.classe_do_evento("tag-inexistente") is None
    assert push.classe_do_evento("stop") == "protecao"
    assert push.classe_do_evento("protecao-opcao") == "protecao"
    assert push.classe_do_evento("pendente-cancelada") == "execucao"


def test_evento_sem_tag_continua_notificando_com_tudo_desligado(monkeypatch):
    """FAIL-OPEN comportamental. Uma tag que ninguém mapeou não é uma classe
    que o usuário desligou — silenciar por omissão de tabela seria perder aviso
    SEM consentimento. O preço desse desenho está escrito em
    `push.classe_do_evento`: todo evento que vira push precisa de `tag`."""
    c = _conn()
    push.set_prefs(c, "u1", {"radar": False, "execucao": False, "protecao": False})
    _seed(c, [], {"serverEnabled": True, "mode": "executar", "intervalMin": 1})
    _pregao_aberto(monkeypatch)

    async def _fake_cycle(conn, uid, *a, **kw):
        return {"events": [{"time": "07/08 14:30", "kind": "buy", "t": "PETR4",
                            "text": "Evento sem tag nenhuma."}],
                "executed": 1, "appMode": "operador"}

    monkeypatch.setattr(agent, "run_cycle_for", _fake_cycle)
    espiao = _Espiao()
    asyncio.run(agent.scheduler_loop(c, _quotes({}), notify_push=espiao, once=True))

    assert len(espiao.pushes) == 1, "sem classe conhecida, o push SAI (fail-open)"


# ===========================================================================
# PROTEÇÃO DE OPÇÃO — o evento que escapava pelo fail-open. Sem a `tag`, o
# usuário desligaria "Proteção" e continuaria recebendo proteção de opção: o
# controle MENTIRIA para ele.
# ===========================================================================
def test_venda_de_opcao_carrega_a_tag_de_protecao():
    c = _conn()
    _seed_opcao(c)
    r = asyncio.run(agent.run_cycle_for(c, "u1", _quotes({}),
                                        option_quotes_getter=_option_getter()))
    assert r["executed"] == 1
    ev = next(e for e in r["events"] if e.get("kind") == "buy")
    assert ev["tag"] == "protecao-opcao"
    assert "Proteção simulada" in ev["text"], "o texto de hoje fica intacto"


def test_titulo_do_push_de_opcao_nao_muda_com_a_tag_nova():
    """A tag é de CONSENTIMENTO, não de vocabulário: `push_titulo` devolve o
    genérico do modo para tag sem frase, que é exatamente o título que este
    push já tinha. Guardião contra "completar" `PUSH_TITULOS` sem necessidade."""
    for modo in ("operador", "educacional"):
        assert skill_ref.push_titulo(modo, "protecao-opcao", "") \
            == skill_ref.PUSH_TITULOS[modo]["generico"]


def test_protecao_desligada_silencia_tambem_a_opcao(monkeypatch):
    c = _conn()
    push.set_prefs(c, "u1", {"protecao": False})
    _seed_opcao(c)
    _pregao_aberto(monkeypatch)
    espiao = _Espiao()

    asyncio.run(agent.scheduler_loop(c, _quotes({}), notify_push=espiao, once=True,
                                     option_quotes_getter=_option_getter()))

    assert espiao.pushes == []
    assert store.get(c, "optionPositions", user_id="u1") == [], "a opção foi vendida do mesmo jeito"


def test_protecao_ligada_deixa_a_opcao_avisar(monkeypatch):
    c = _conn()
    _seed_opcao(c)
    _pregao_aberto(monkeypatch)
    espiao = _Espiao()

    asyncio.run(agent.scheduler_loop(c, _quotes({}), notify_push=espiao, once=True,
                                     option_quotes_getter=_option_getter()))

    assert len(espiao.pushes) == 1


# ===========================================================================
# PATCH PARCIAL — o mecanismo em que o invariante do `gatilho` se apoia.
# ===========================================================================
def test_patch_parcial_nao_toca_chave_ausente():
    """É isto que permite ao web escrever SÓ as três classes sem encostar em
    `gatilho`/`modo`/`universo` — as chaves de autoridade do APARELHO. Se
    `set_prefs` passar a reescrever o objeto inteiro, o `gatilho: true` do
    iPhone vira `false` na primeira vez que a pessoa abrir o app no navegador,
    em silêncio."""
    c = _conn()
    push.set_prefs(c, "u1", {"gatilho": True, "modo": "operador", "universo": ["PETR4"]})

    p = push.set_prefs(c, "u1", {"radar": False})

    assert p["gatilho"] is True, "chave ausente do patch fica como estava"
    assert p["universo"] == ["PETR4"]
    assert p["modo"] == "operador"
    assert p["radar"] is False
    lido = push.prefs_for(c, "u1")
    assert lido["gatilho"] is True and lido["universo"] == ["PETR4"]


# ===========================================================================
# MIGRAÇÃO DE GRAÇA — o default É a migração; nenhuma migração de dado escrita.
# ===========================================================================
def test_prefs_no_formato_antigo_herdam_as_classes_ligadas():
    c = _conn()
    db.kv_set(c, "pushPrefs", {"gatilho": True, "modo": "operador",
                               "universo": ["VALE3"], "at": "2026-08-01T12:00:00"},
              user_id="u1")

    p = push.prefs_for(c, "u1")

    assert p["radar"] is True and p["execucao"] is True and p["protecao"] is True
    assert p["gatilho"] is True and p["universo"] == ["VALE3"]


def test_set_prefs_aceita_as_classes_novas_e_coage_para_bool():
    c = _conn()
    p = push.set_prefs(c, "u1", {"radar": 0, "execucao": "sim", "protecao": None})
    assert p["radar"] is False and p["execucao"] is True and p["protecao"] is False
    assert all(isinstance(p[k], bool) for k in push.PREFS_BOOLS)


def test_set_prefs_continua_descartando_chave_desconhecida():
    c = _conn()
    p = push.set_prefs(c, "u1", {"protecao": False, "admin": True, "radarr": False})
    assert "admin" not in p and "radarr" not in p
    assert p["protecao"] is False and p["radar"] is True


# ===========================================================================
# SEM REGRESSÃO DO `gatilho` — não é classe nova, não muda, e nenhum caminho
# desta entrega pode desligá-lo.
# ===========================================================================
def test_gatilho_continua_nascendo_desligado():
    assert push.PREFS_PADRAO["gatilho"] is False, \
        "a regra do opt-in continua valendo para classe de alerta genuinamente nova"


def test_timing_watch_continua_com_as_duas_leituras_de_sempre():
    """Âncora de FONTE: o call site do gatilho não foi tocado por esta entrega —
    duas chamadas `prefs_for(conn, uid)`, exatamente como antes."""
    assert _SRC_TIMING_WATCH.count("prefs_for(conn, uid)") == 2


# ===========================================================================
# KILL-SWITCH — exceção declarada: aviso operacional por RBAC não tem
# interruptor de usuário final.
# ===========================================================================
def test_kill_switch_nao_consulta_preferencia_nenhuma():
    """Âncora sobre a CHAMADA, nunca sobre a palavra: o docstring escreve
    `push.prefs_for` SEM parêntese de propósito (a decisão fica registrada no
    código), então asserir sobre a palavra solta ficaria vermelho pela própria
    explicação."""
    corpo = _SRC_AGENT.split("async def _alertar_kill_switch")[1].split("\nasync def ")[0]
    assert "prefs_for(" not in corpo, \
        "preferência de usuário final não pode silenciar aviso operacional de admin"
    assert "prefs_for" in corpo, \
        "e a decisão continua ESCRITA no docstring — se sumiu, alguém apagou a exceção"


# ===========================================================================
# COBERTURA ESTRUTURAL — SUPERCONJUNTO, não igualdade.
# ===========================================================================
def test_toda_tag_com_titulo_de_push_tem_classe_de_consentimento():
    """Com igualdade, `protecao-opcao` (tag de consentimento SEM título próprio,
    por decisão) seria impossível sem inventar vocabulário. Com superconjunto,
    uma tag que ganhe título e esqueça a classe fica vermelha — que é o defeito
    que importa: evento notificável fora do controle do usuário."""
    com_titulo = set(skill_ref.PUSH_TITULOS["operador"]) - {"generico"}
    faltando = com_titulo - set(push.CLASSE_POR_TAG)
    assert not faltando, f"tag com título de push e sem classe de consentimento: {sorted(faltando)}"


def test_toda_classe_da_tabela_existe_no_prefs_padrao():
    for classe in set(push.CLASSE_POR_TAG.values()):
        assert classe in push.PREFS_PADRAO, \
            f"a tabela aponta para '{classe}', que ninguém consegue ligar/desligar"
