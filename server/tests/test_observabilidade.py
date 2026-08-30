"""Fase 4 do ADR-23 — GET /observabilidade, contrato mínimo publicado para
o console admin.semente.dev agregar depois.

O que estes testes protegem:
  - a resposta tem exatamente as quatro chaves de topo, sem envelope;
  - `situacao` é coerente com `alertas` (derivada da própria lista, nunca
    uma segunda regra paralela que possa discordar dela);
  - `ultimas_execucoes`/`proximas` são SEMPRE listas (vazias, nunca null);
  - sem chave de máquina e sem sessão: 401. Sessão sem `observabilidade.ver`:
    403. Chave de máquina correta: 200. `B3_OBSERVABILIDADE_CHAVE` ausente
    desliga o caminho de máquina (fail-closed — chave errada/vazia continua
    401, nunca cai para público);
  - a rota é declarada ANTES do mount catch-all '/' (mesma classe de defeito
    que test_admin_portal.py já guarda para '/admin');
  - nenhuma identidade de usuário (e-mail, user_id) aparece no payload.
"""
import importlib
import os
import pathlib
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _isolado():
    from app import agent, brapi_budget, managed, obslog, timing_watch
    original = sys.modules.get("app.main")
    brapi_budget.reset()
    agent.reset_kill_switch_cache()
    timing_watch.reset_kill_switch_cache()
    managed.reset_cache()
    # obslog.stats() acumula desde o BOOT do processo (contador global,
    # `_counters`/`_buffer` em memória) — sem reset aqui, o teste "zero
    # alertas" fica dependente da ordem de execução: qualquer teste de
    # OUTRO módulo que rode antes e gere um "err"/"warn" no mesmo processo
    # pytest infla `erros_desde_boot` e quebra este cenário (achado real ao
    # rodar a suíte inteira via scripts/executar.sh --testes).
    obslog.reset()
    yield
    brapi_budget.reset()
    agent.reset_kill_switch_cache()
    timing_watch.reset_kill_switch_cache()
    managed.reset_cache()
    obslog.reset()
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


def _client(monkeypatch, chave_maquina=None):
    monkeypatch.delenv("B3_ADMIN_EMAILS", raising=False)
    if chave_maquina is None:
        monkeypatch.delenv("B3_OBSERVABILIDADE_CHAVE", raising=False)
    else:
        monkeypatch.setenv("B3_OBSERVABILIDADE_CHAVE", chave_maquina)
    d = tempfile.mkdtemp(prefix="b3_observabilidade_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    return TestClient(main.app), main


def _registra(c, email, senha="senhaboa123"):
    r = c.post("/api/auth/register", json={"email": email, "password": senha})
    assert r.status_code == 200, r.text
    return r.json()


def _auth(token):
    return {"authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# contrato de dado
# ---------------------------------------------------------------------------
def test_resposta_tem_exatamente_as_quatro_chaves(monkeypatch):
    c, _ = _client(monkeypatch, chave_maquina="chave-teste")
    r = c.get("/observabilidade", headers={"X-Observabilidade-Chave": "chave-teste"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body.keys()) == {"situacao", "alertas", "ultimas_execucoes", "proximas"}
    assert body["situacao"] in ("ok", "atencao", "critico")
    assert isinstance(body["ultimas_execucoes"], list)
    assert isinstance(body["proximas"], list)
    for a in body["alertas"]:
        assert set(a.keys()) == {"severidade", "titulo", "detalhe", "acao"}


def test_situacao_ok_sem_alerta_nenhum(monkeypatch):
    import time

    from app import agent, db as db_mod, timing_watch
    agent.reset_kill_switch_cache()
    timing_watch.reset_kill_switch_cache()
    monkeypatch.delenv("B3_AGENT_KILL", raising=False)
    monkeypatch.delenv("B3_TIMING_PUSH_KILL", raising=False)
    c, main = _client(monkeypatch, chave_maquina="chave-teste")
    # sem heartbeat persistido -> lacoVivo é False por padrão (hb vazio);
    # isso por si geraria alerta crítico — grava um heartbeat recente para
    # isolar o cenário "zero alertas" do resto do estado do agente.
    db_mod.kv_set(main._conn, "agentHeartbeat", {"ts": time.time(), "atBRT": "x", "pregaoAberto": False}, user_id=None)
    r = c.get("/observabilidade", headers={"X-Observabilidade-Chave": "chave-teste"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["alertas"] == []
    assert body["situacao"] == "ok"


def test_situacao_critico_com_kill_switch_ligado(monkeypatch):
    monkeypatch.setenv("B3_AGENT_KILL", "1")
    c, _ = _client(monkeypatch, chave_maquina="chave-teste")
    r = c.get("/observabilidade", headers={"X-Observabilidade-Chave": "chave-teste"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["situacao"] == "critico"
    assert any(a["severidade"] == "critico" for a in body["alertas"])


# ---------------------------------------------------------------------------
# autenticação — nunca público
# ---------------------------------------------------------------------------
def test_sem_chave_e_sem_sessao_responde_401(monkeypatch):
    c, _ = _client(monkeypatch, chave_maquina="chave-teste")
    r = c.get("/observabilidade")
    assert r.status_code == 401


def test_chave_errada_responde_401(monkeypatch):
    c, _ = _client(monkeypatch, chave_maquina="chave-teste")
    r = c.get("/observabilidade", headers={"X-Observabilidade-Chave": "errada"})
    assert r.status_code == 401


def test_sem_variavel_configurada_caminho_de_maquina_fica_desligado(monkeypatch):
    """B3_OBSERVABILIDADE_CHAVE ausente = fail-closed, NUNCA 'qualquer chave
    passa'. Mandar qualquer valor de header ainda deve dar 401."""
    c, _ = _client(monkeypatch, chave_maquina=None)
    r = c.get("/observabilidade", headers={"X-Observabilidade-Chave": "qualquercoisa"})
    assert r.status_code == 401


def test_sessao_sem_permissao_responde_403(monkeypatch):
    c, _ = _client(monkeypatch, chave_maquina="chave-teste")
    _registra(c, "dono@teste.com")  # 1º usuário: bootstrap admin (role_admin)
    comum = _registra(c, "comum@teste.com")  # sem nenhum papel
    r = c.get("/observabilidade", headers=_auth(comum["token"]))
    assert r.status_code == 403


def test_sessao_com_observabilidade_ver_responde_200(monkeypatch):
    from app import rbac
    c, main = _client(monkeypatch, chave_maquina="chave-teste")
    _registra(c, "dono@teste.com")  # 1º usuário: bootstrap admin
    u = _registra(c, "obs@teste.com")
    rbac.grant_role(main._conn, u["user"]["id"], "observabilidade")
    r = c.get("/observabilidade", headers=_auth(u["token"]))
    assert r.status_code == 200, r.text


def test_chave_de_maquina_correta_responde_200_sem_sessao(monkeypatch):
    c, _ = _client(monkeypatch, chave_maquina="chave-teste")
    r = c.get("/observabilidade", headers={"X-Observabilidade-Chave": "chave-teste"})
    assert r.status_code == 200, r.text


def test_nenhum_email_ou_user_id_no_payload(monkeypatch):
    c, _ = _client(monkeypatch, chave_maquina="chave-teste")
    _registra(c, "dono@teste.com")
    r = c.get("/observabilidade", headers={"X-Observabilidade-Chave": "chave-teste"})
    corpo_bruto = r.text
    assert "dono@teste.com" not in corpo_bruto


# ---------------------------------------------------------------------------
# ordem de registro — mesma classe de defeito que test_admin_portal.py guarda
# ---------------------------------------------------------------------------
def test_observabilidade_registrada_antes_do_mount_raiz():
    src = (pathlib.Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")
    i_obs = src.find('app.get("/observabilidade")')
    i_raiz = src.find('app.mount("/"')
    assert i_obs > 0, "rota /observabilidade não encontrada"
    assert i_raiz > 0, "mount de '/' não encontrado"
    assert i_obs < i_raiz, "/observabilidade precisa ser registrada ANTES do mount catch-all '/'"
