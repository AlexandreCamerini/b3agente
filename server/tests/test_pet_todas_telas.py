"""Fase F4 — o pet (Boris) existe em TODAS as telas do app, não só na
Watchlist. O que estes guardiões travam, e por quê:

  • `conceitos.PET_TELAS` tem as 7 abas do plano (F4) — se uma sumir daqui,
    o `/api/assistente` volta a recusar `tela: "pet:<aba>"` com 400 e o Boris
    fica mudo naquela tela sem ninguém perceber em código.
  • A ALLOWLIST é a fronteira (D7 do plano): para CADA tela registrada, uma
    pergunta que a KB cobre (grátis, sem conta) precisa passar da checagem de
    `tela` — nunca cair no 400 "Tela desconhecida.". `pet:invalida` continua
    fora, sempre.
  • `/api/pet/resumo?tela=<aba>` — a variação por tela (F4) não pode quebrar:
    para as 7 abas, a rota devolve 200, `ligada: True` e pelo menos uma frase
    em `fala` (nunca lista vazia, nunca 500) — mesmo com o banco do teste
    vazio (sem posições, sem radar, sem agentLog).
"""
import os

import pytest
from fastapi.testclient import TestClient

from app import conceitos
from app.main import app, require_user

PERGUNTA_KB = "o que é ATR?"  # a mesma pergunta canônica de test_assistente_kb.py


@pytest.fixture
def cli():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def _sem_flags():
    chaves = ("B3_DIDATICA_OFF", "B3_ASSISTENTE_OFF")
    for k in chaves:
        os.environ.pop(k, None)
    yield
    for k in chaves:
        os.environ.pop(k, None)


def test_pet_telas_tem_as_7_abas_do_plano():
    esperado = {"mercado", "carteira", "evolucao", "radar", "agente", "historico", "perfil"}
    assert set(conceitos.PET_TELAS) == esperado


# ------------------------------------------------- allowlist no /api/assistente
@pytest.mark.parametrize("aba", conceitos.PET_TELAS)
def test_cada_tela_registrada_passa_da_allowlist(cli, aba):
    r = cli.post("/api/assistente", json={"tela": f"pet:{aba}", "pergunta": PERGUNTA_KB})
    assert r.status_code != 400, f"pet:{aba} foi recusado pela allowlist: {r.json()}"
    assert r.json().get("fonte") == "kb"


def test_tela_invalida_continua_recusada(cli):
    r = cli.post("/api/assistente", json={"tela": "pet:invalida", "pergunta": PERGUNTA_KB})
    assert r.status_code == 400
    assert "Tela" in r.json()["detail"]


def test_tela_invalida_continua_recusada_mesmo_logado(cli):
    """A allowlist barra ANTES de exigir conta — tela ruim é 400, não 401."""
    app.dependency_overrides[require_user] = lambda: {"id": "u-pet-f4"}
    try:
        r = cli.post("/api/assistente", json={"tela": "pet:invalida", "pergunta": PERGUNTA_KB})
        assert r.status_code == 400
    finally:
        app.dependency_overrides.pop(require_user, None)


# ---------------------------------------------------- /api/pet/resumo por tela
@pytest.mark.parametrize("aba", conceitos.PET_TELAS)
def test_resumo_de_cada_tela_e_coerente(cli, aba):
    r = cli.get("/api/pet/resumo", params={"modo": "estudo", "tela": aba})
    assert r.status_code == 200
    b = r.json()
    assert b["ligada"] is True
    assert b.get("tela") == aba
    fala = b.get("fala")
    assert isinstance(fala, list) and len(fala) >= 1
    assert all(isinstance(f, str) and f.strip() for f in fala)
    # "o que o app NÃO faz" continua vindo primeiro em toda tela nova.
    assert "não compra nem vende" in fala[0]


def test_resumo_tela_desconhecida_cai_em_mercado(cli):
    """`tela` fora da allowlist não quebra a rota — ela nunca é gate aqui (só
    no /api/assistente); o resumo cai no comportamento de antes da F4."""
    r = cli.get("/api/pet/resumo", params={"tela": "nao-existe"})
    assert r.status_code == 200
    assert r.json().get("tela") == "mercado"


def test_resumo_mercado_mantem_chave_itens(cli):
    """F4: `pet:mercado` não muda de formato — `itens` continua existindo."""
    b = cli.get("/api/pet/resumo", params={"tela": "mercado"}).json()
    assert "itens" in b and isinstance(b["itens"], list)
