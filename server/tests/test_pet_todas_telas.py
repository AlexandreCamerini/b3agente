"""Fase F4 — o pet (Boris) existe em TODAS as telas do app, não só na
Watchlist. O que estes guardiões travam, e por quê:

  • `conceitos.PET_TELAS` tem as 8 abas do app (7 da F4 + "opcoes", que entrou
    em 2026-09-12 pelo achado A1 da Fase 26) — se uma sumir daqui,
    o `/api/assistente` volta a recusar `tela: "pet:<aba>"` com 400 e o Boris
    fica mudo naquela tela sem ninguém perceber em código.
  • A ALLOWLIST é a fronteira (D7 do plano): para CADA tela registrada, uma
    pergunta que a KB cobre (grátis, sem conta) precisa passar da checagem de
    `tela` — nunca cair no 400 "Tela desconhecida.". `pet:invalida` continua
    fora, sempre.
  • `/api/pet/resumo?tela=<aba>` — a variação por tela (F4) não pode quebrar:
    para as 8 abas, a rota devolve 200, `ligada: True` e pelo menos uma frase
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


def test_pet_telas_tem_as_8_abas_do_plano():
    """A trava é de IGUALDADE EXATA e continua sendo — o conjunto só CRESCEU.

    2026-09-12 (Fase 26, achado A1): "opcoes" entrou como oitava tela. A aba
    Opções nasceu na Fase 24 (`aba-opcoes F2`) já no `BottomNav` do front e
    nunca foi registrada em `conceitos.PET_TELAS`; o efeito foi exatamente o
    que este guardião existe para impedir — `/api/assistente` recusando
    `pet:opcoes` com 400 e `/api/pet/resumo?tela=opcoes` caindo no fallback
    de "mercado", os dois em silêncio. O guardião não pegou porque a trava
    era sobre as telas que EXISTIAM quando ele foi escrito (F4), e uma tela
    nova não faz este assert falhar — só a remoção de uma antiga faz.
    Registrado em `26-CONTEXT.md` como causa-raiz C3 (cinco listas paralelas
    de tela no front, sem teste amarrando uma na outra).
    """
    esperado = {"mercado", "carteira", "evolucao", "radar", "agente", "historico",
                "perfil", "opcoes"}
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


def test_resumo_opcoes_nao_e_o_de_mercado(cli):
    """Fase 26 / A1 — o defeito era SILENCIOSO: `tela=opcoes` caía na allowlist
    e voltava o resumo de "mercado", que é a Watchlist. Um 200 com o conteúdo
    da tela errada. Este guardião trava as DUAS pontas: o carimbo (`tela`) e o
    corpo (a aba Opções não tem `itens` de timing de watchlist; tem o universo
    e a contagem de posições de opção)."""
    b = cli.get("/api/pet/resumo", params={"tela": "opcoes"}).json()
    assert b.get("tela") == "opcoes"
    assert "itens" not in b, "resumo de opcoes veio com o corpo de pet:mercado"
    assert isinstance(b.get("universo"), list)
    assert isinstance(b.get("posicoesOpcoes"), int)
    # Princípio 4: a rota diz o que NÃO sabe em vez de inventar o ativo aberto.
    assert any("não sei qual ativo" in f for f in b["fala"])


def test_resumo_opcoes_nao_chama_o_servico_de_opcoes(cli, monkeypatch):
    """A família /api/pet/* é custo-zero por contrato. Se um dia alguém puxar a
    leitura do `mcp.semente.dev` para dentro deste resumo, o orçamento de
    chamadas passa a ser gasto por ABRIR a aba, sem clique de ninguém
    (ADR-027). O guardião injeta uma bomba na porta ÚNICA de saída para o
    serviço (`mcp_client.call_tool`), não numa rota específica: assim ela
    continua valendo se a chamada de cima mudar de nome."""
    from app import mcp_client

    def _bomba(*a, **k):
        raise AssertionError("/api/pet/resumo?tela=opcoes chamou o serviço de opções")

    monkeypatch.setattr(mcp_client, "call_tool", _bomba)
    r = cli.get("/api/pet/resumo", params={"tela": "opcoes"})
    assert r.status_code == 200
    assert r.json().get("tela") == "opcoes"


def test_resumo_mercado_mantem_chave_itens(cli):
    """F4: `pet:mercado` não muda de formato — `itens` continua existindo."""
    b = cli.get("/api/pet/resumo", params={"tela": "mercado"}).json()
    assert "itens" in b and isinstance(b["itens"], list)
