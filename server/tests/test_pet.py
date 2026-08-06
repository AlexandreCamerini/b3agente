"""O PET — resumo determinístico da tela e a allowlist `tela: "pet:<id>"`.

O que estes guardiões travam, e por quê:

  • CUSTO ZERO E LEI DO VOCABULÁRIO. Toda frase do resumo sai pronta do
    servidor: as de estado são as canônicas de `timing.montar` (skill_ref) e
    as conectivas moram na rota. Se o front um dia compuser texto, este
    arquivo não pega — mas se a ROTA vazar verbo de ordem no Estudo, pega.
  • "O QUE O APP NÃO FAZ" VEM PRIMEIRO — a mesma regra da folha de conceito:
    quem abre o assistente pergunta antes de tudo se o app comprou algo.
  • A allowlist do assistente: `pet:<tela>` desconhecida é 400 ANTES de
    gastar; `pet:mercado` passa.
  • Chave de desligamento: B3_DIDATICA_OFF desliga o pet junto do resto.
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


# ------------------------------------------------------------------ o resumo
def test_resumo_nao_faz_vem_primeiro_e_sem_verbo_de_ordem(cli):
    b = cli.get("/api/pet/resumo?modo=estudo").json()
    assert b["ligada"] is True and b["modo"] == "educacional"
    fala = b["fala"]
    assert fala and "não compra nem vende" in fala[0]
    corpo = " ".join(fala)
    for verbo in ("COMPRAR", "VENDER", "compre", "venda agora", "entre agora"):
        assert verbo not in corpo, f"verbo de ordem vazou no Estudo: {verbo!r}"


def test_resumo_sem_planos_explica_em_vez_de_inventar(cli):
    """Sem radar armazenado (banco do teste), `itens` é vazio e a fala diz
    isso — nunca inventa estado nem número (Princípio 1)."""
    b = cli.get("/api/pet/resumo?modo=estudo").json()
    if not b["itens"]:
        assert any("ainda não tem planos" in f for f in b["fala"])


def test_resumo_desligado_com_a_camada(cli):
    os.environ["B3_DIDATICA_OFF"] = "1"
    b = cli.get("/api/pet/resumo").json()
    assert b == {"ligada": False}


def test_resumo_e_anonimo_por_desenho(cli):
    """A camada grátis serve o anônimo — o pet não pode exigir conta para o
    resumo determinístico (só a pergunta LLM exige)."""
    assert cli.get("/api/pet/resumo").status_code == 200


# ------------------------------------------------- allowlist no /api/assistente
def test_pet_tela_desconhecida_e_400_antes_de_gastar(cli):
    app.dependency_overrides[require_user] = lambda: {"id": "u1"}
    try:
        r = cli.post("/api/assistente", json={
            "tela": "pet:inexistente", "pergunta": "o que é isto?",
        })
        assert r.status_code == 400
        assert "Tela" in r.json()["detail"]
    finally:
        app.dependency_overrides.pop(require_user, None)


def test_pet_tela_valida_passa_da_validacao(cli):
    app.dependency_overrides[require_user] = lambda: {"id": "u-pet"}
    try:
        r = cli.post("/api/assistente", json={
            "tela": "pet:mercado", "pergunta": "o que esta tela mostra?",
        })
        assert r.status_code != 400 or "Tela" not in str(r.json())
    finally:
        app.dependency_overrides.pop(require_user, None)


def test_pet_telas_registradas_sao_validas():
    assert "mercado" in conceitos.PET_TELAS
