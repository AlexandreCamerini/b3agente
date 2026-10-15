"""quick 261014-upj — o rebaixamento do Operador na saída do modo não é mais
silencioso.

Sair do Modo Operador (store.set_config) troca `agent.mode` "executar" →
"sinalizar" e zera `entradaAuto`; voltar NÃO restaura (guardião
test_entrar_no_operador_nao_mexe_no_mode_sinalizar, em
test_agent_modo_estudo.py — intacto). Aqui se trava o rastro: um `warn` no
Diário (só quando algo mudou, sem duplicar) e o marcador
`agent.rebaixadoOperador`, exposto em /api/agent/status para o aviso da tela.
"""
import importlib
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

from app import db, skill_ref, store

OPERADOR = {"operadorTermo": {"aceitoEm": "2026-01-01", "versao": "1"}, "appMode": "operador"}


def _conn():
    d = tempfile.mkdtemp(prefix="b3_rebaixamento_")
    c = db.connect(os.path.join(d, "b3.db"))
    store.ensure_defaults(c, user_id="u1")
    store.set_config(c, OPERADOR, user_id="u1")
    return c


def _warns(c):
    return [e for e in (db.kv_get(c, "agentLog", [], user_id="u1") or [])
            if e.get("tag") == "rebaixamento-operador"]


def _agent(c):
    return db.kv_get(c, "agent", user_id="u1")


@pytest.mark.parametrize("armado, chave, execucao, entrada", [
    ({"mode": "executar", "entradaAuto": True}, "diario_ambos", True, True),
    ({"mode": "executar"}, "diario_execucao", True, False),
    ({"mode": "sinalizar", "entradaAuto": True}, "diario_entrada", False, True),
])
def test_saida_do_operador_grava_warn_e_marcador(armado, chave, execucao, entrada):
    c = _conn()
    store.set_agent(c, armado, user_id="u1")
    store.set_config(c, {"appMode": "estudo"}, user_id="u1")
    ws = _warns(c)
    assert len(ws) == 1
    assert ws[0]["kind"] == "warn"
    assert ws[0]["text"] == skill_ref.rebaixamento_operador_txt("educacional", chave)
    reb = _agent(c)["rebaixadoOperador"]
    assert reb["execucao"] is execucao and reb["entradaAuto"] is entrada
    assert reb["em"]
    # a migração em si segue igual (guardiões da Fase A/B)
    assert _agent(c).get("mode") != "executar" and not _agent(c).get("entradaAuto")


def test_saida_sem_nada_armado_nao_grava_nada():
    c = _conn()
    store.set_agent(c, {"mode": "sinalizar"}, user_id="u1")
    store.set_config(c, {"appMode": "estudo"}, user_id="u1")
    assert _warns(c) == []
    assert "rebaixadoOperador" not in _agent(c)


def test_saida_repetida_nao_duplica_evento():
    c = _conn()
    store.set_agent(c, {"mode": "executar"}, user_id="u1")
    store.set_config(c, {"appMode": "estudo"}, user_id="u1")
    store.set_config(c, {"appMode": "estudo"}, user_id="u1")
    store.set_config(c, OPERADOR, user_id="u1")       # volta sem religar
    store.set_config(c, {"appMode": "estudo"}, user_id="u1")  # sai de novo: nada a desligar
    assert len(_warns(c)) == 1


def test_volta_ao_operador_mantem_sinalizar_e_marcador():
    """Complementa o guardião travado: voltar não religa E o marcador fica
    (é ele que acende o aviso na tela)."""
    c = _conn()
    store.set_agent(c, {"mode": "executar"}, user_id="u1")
    store.set_config(c, {"appMode": "estudo"}, user_id="u1")
    store.set_config(c, OPERADOR, user_id="u1")
    ag = _agent(c)
    assert ag["mode"] == "sinalizar"
    assert ag["rebaixadoOperador"]["execucao"] is True


def test_escolha_explicita_no_operador_limpa_por_campo():
    c = _conn()
    store.set_agent(c, {"mode": "executar", "entradaAuto": True}, user_id="u1")
    store.set_config(c, {"appMode": "estudo"}, user_id="u1")
    store.set_config(c, OPERADOR, user_id="u1")
    # mexer só na entrada não esconde a execução ainda desligada
    store.set_agent(c, {"entradaAuto": False}, user_id="u1")
    reb = _agent(c)["rebaixadoOperador"]
    assert reb["execucao"] is True and reb["entradaAuto"] is False
    # religar Executar fecha o marcador
    store.set_agent(c, {"mode": "executar"}, user_id="u1")
    assert "rebaixadoOperador" not in _agent(c)
    assert _agent(c)["mode"] == "executar"


def test_manter_sinalizar_tambem_limpa():
    c = _conn()
    store.set_agent(c, {"mode": "executar"}, user_id="u1")
    store.set_config(c, {"appMode": "estudo"}, user_id="u1")
    store.set_config(c, OPERADOR, user_id="u1")
    store.set_agent(c, {"mode": "sinalizar"}, user_id="u1")
    assert "rebaixadoOperador" not in _agent(c)


def test_fora_do_operador_set_agent_nao_limpa():
    c = _conn()
    store.set_agent(c, {"mode": "executar"}, user_id="u1")
    store.set_config(c, {"appMode": "estudo"}, user_id="u1")
    store.set_agent(c, {"mode": "sinalizar"}, user_id="u1")
    assert _agent(c)["rebaixadoOperador"]["execucao"] is True


def test_copy_tem_os_dois_modos_com_as_mesmas_chaves():
    op, edu = skill_ref.REBAIXAMENTO_OPERADOR["operador"], skill_ref.REBAIXAMENTO_OPERADOR["educacional"]
    assert set(op) == set(edu)
    assert all(v and "{" not in v for v in list(op.values()) + list(edu.values()))
    with pytest.raises(KeyError):
        skill_ref.rebaixamento_operador_txt("operador", "nao_existe")


# ----------------------------------------------------------- /api/agent/status
@pytest.fixture
def cliente(monkeypatch):
    original = sys.modules.get("app.main")
    d = tempfile.mkdtemp(prefix="b3_rebaixamento_rota_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    sys.modules.pop("app.main", None)
    m = importlib.import_module("app.main")
    yield TestClient(m.app), m
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


def test_status_expoe_modo_e_rebaixamento(cliente):
    client, m = cliente
    r = client.post("/api/auth/register", json={"email": "reb@x.com", "password": "senhaboa123"})
    assert r.status_code == 200, r.text
    uid, h = r.json()["user"]["id"], {"authorization": "Bearer " + r.json()["token"]}
    store.set_config(m._conn, OPERADOR, user_id=uid)
    store.set_agent(m._conn, {"mode": "executar", "entradaAuto": True}, user_id=uid)

    st = client.get("/api/agent/status", headers=h).json()
    assert st["meuModo"] == "executar" and st["minhaEntradaAuto"] is True
    assert st["meuRebaixamento"] is None

    store.set_config(m._conn, {"appMode": "estudo"}, user_id=uid)
    store.set_config(m._conn, OPERADOR, user_id=uid)
    st = client.get("/api/agent/status", headers=h).json()
    assert st["meuModo"] == "sinalizar" and st["minhaEntradaAuto"] is False
    assert st["meuRebaixamento"]["execucao"] is True and st["meuRebaixamento"]["entradaAuto"] is True

    store.set_agent(m._conn, {"mode": "executar", "entradaAuto": True}, user_id=uid)
    st = client.get("/api/agent/status", headers=h).json()
    assert st["meuRebaixamento"] is None and st["meuModo"] == "executar"
