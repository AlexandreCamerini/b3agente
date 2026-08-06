"""Toque longo — o REGISTRO DE SETORES e a allowlist de `tela: "setor:<id>"`.

O que estes guardiões travam, e por quê:

  • O registro mora no BACKEND. O front declara regiões; o que cada uma
    explica decide-se aqui — repontear um setor é deploy do Railway, não build
    de iOS. Setor apontando para conceito fantasma viraria folha 404 na cara
    do usuário, então a integridade é testada sobre o catálogo real.
  • `tela: "setor:<id>"` é ALLOWLIST no /api/assistente. Id que o backend não
    conhece é 400 ANTES de qualquer gasto — nunca vira contexto de prompt.
  • A cadeia do setor "analise" alcança o fundamento. O chip do fundamento é o
    alvo mais interno (pequeno); sem o elo confluencia→fundamento no "veja
    também", errar o dedo deixaria o conceito inalcançável pelo gesto.
  • Camada desligada devolve registro VAZIO — é a ausência que o front usa
    para não armar o gesto (mesma chave B3_DIDATICA_OFF de sempre).
"""
import os

import pytest
from fastapi.testclient import TestClient

from app import conceitos
from app.main import app, require_user


@pytest.fixture
def cli():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def _sem_flags():
    for k in ("B3_DIDATICA_OFF", "B3_ASSISTENTE_OFF"):
        os.environ.pop(k, None)
    yield
    for k in ("B3_DIDATICA_OFF", "B3_ASSISTENTE_OFF"):
        os.environ.pop(k, None)


# ----------------------------------------------------- integridade do registro
def test_todo_setor_aponta_para_conceito_que_existe():
    for setor, cid in conceitos.SETORES.items():
        assert cid in conceitos.CONCEITOS, f"setor {setor!r} aponta para conceito fantasma {cid!r}"


def test_regua_tem_dois_setores_stop_e_alvo():
    """Régua só com alvo É o setor alvo — herda o guardião 'a régua com só
    alvo não oferece um ? que explica o stop'."""
    assert conceitos.SETORES["risco"] == "stop"
    assert conceitos.SETORES["alvo"] == "alvo"


def test_cadeia_da_analise_alcanca_o_fundamento():
    cid = conceitos.SETORES["analise"]
    veja = conceitos.CONCEITOS[cid]["veja"]
    assert "fundamento" in veja, "sem este elo o fundamento só sai acertando o chip pequeno"


def test_setores_desligados_com_a_camada():
    os.environ["B3_DIDATICA_OFF"] = "1"
    assert conceitos.setores() == {}


# --------------------------------------------------------------- rota catálogo
def test_rota_catalogo_serve_o_registro(cli):
    b = cli.get("/api/conceitos?modo=estudo").json()
    assert b["setores"] == conceitos.setores()
    assert b["setores"]["timing"] == "gatilho"


def test_rota_catalogo_com_camada_desligada_serve_registro_vazio(cli):
    os.environ["B3_DIDATICA_OFF"] = "1"
    b = cli.get("/api/conceitos").json()
    assert b["ligada"] is False and b["setores"] == {}


# ------------------------------------------- allowlist no /api/assistente
def test_setor_desconhecido_e_400_antes_de_gastar(cli):
    app.dependency_overrides[require_user] = lambda: {"id": "u1"}
    try:
        r = cli.post("/api/assistente", json={
            "tela": "setor:inexistente", "pergunta": "o que é isto?",
        })
        assert r.status_code == 400
        assert "Setor" in r.json()["detail"]
    finally:
        app.dependency_overrides.pop(require_user, None)


def test_setor_valido_passa_da_validacao(cli):
    """Com setor conhecido a rota segue adiante — sem modelo configurado o
    erro vem DEPOIS da validação (não 400 de setor)."""
    app.dependency_overrides[require_user] = lambda: {"id": "u-setor-ok"}
    try:
        r = cli.post("/api/assistente", json={
            "tela": "setor:timing", "pergunta": "o que é isto?",
        })
        assert r.status_code != 400 or "Setor" not in str(r.json())
    finally:
        app.dependency_overrides.pop(require_user, None)


def test_setor_sem_conta_e_401(cli):
    r = cli.post("/api/assistente", json={
        "tela": "setor:timing", "pergunta": "o que é isto?",
    })
    assert r.status_code in (401, 403)


def test_tela_conceito_continua_valendo(cli):
    """O caminho antigo (`conceito:<cid>`) não ganhou validação nova — a
    allowlist é só do prefixo `setor:`."""
    app.dependency_overrides[require_user] = lambda: {"id": "u1"}
    try:
        r = cli.post("/api/assistente", json={
            "tela": "conceito:gatilho", "pergunta": "?",
        })
        assert r.status_code != 400 or "Setor" not in str(r.json())
    finally:
        app.dependency_overrides.pop(require_user, None)
