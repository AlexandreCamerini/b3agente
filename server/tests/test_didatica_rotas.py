"""Camada de entendimento — as ROTAS, exercitadas de verdade.

Os demais guardiões chamam `conceitos.montar` direto e não cobrem a resolução
de modo, a serialização, nem o contrato de erro. Este exercita o endpoint —
inclusive o congelamento de `/api/timing`, que antes era verificado sobre a
FUNÇÃO e não sobre a rota que o app realmente chama.

Também trava o "vai silencioso" do push (Fase 0a): som e prioridade viraram
parâmetros porque uma mesa não aprova alerta de mercado em priority 10 com som
num simulador. Isso era promessa lida, não verificada.
"""
import asyncio
import json
import os

import pytest
from fastapi.testclient import TestClient

from app import conceitos, push
from app.main import app

CHAVES_TIMING = {
    "ticker", "modo", "estado", "frase", "ressalvas", "contexto15m",
    "vereditoDiario", "lado", "decisaoDiaria", "entrada", "stop",
    "riscoPorAcao", "setup", "fechamento15m", "asOf", "barraEmFormacao",
    "lacuna", "cobertura", "distancia", "distanciaEmR", "excedente",
    "excedenteEmR", "motivo", "foraDoPregao", "barraDeOutroDia",
}


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


# ------------------------------------------- o contrato de /api/timing na ROTA
@pytest.mark.parametrize("modo", ["operador", "estudo"])
def test_rota_timing_nao_ganhou_campo_com_a_didatica(cli, modo):
    r = cli.get("/api/timing/PETR4?appMode=" + modo)
    assert r.status_code == 200
    extras = set(r.json()) - CHAVES_TIMING
    assert extras == set(), f"campo novo vazou para a rota /api/timing: {extras}"


# --------------------------------------------------------- catálogo e conceito
def test_rota_catalogo_responde_com_flags_e_texto_generico(cli):
    b = cli.get("/api/conceitos?modo=estudo").json()
    assert b["ligada"] is True and b["assistente"] is True
    assert b["modo"] == "educacional"
    ids = [c["id"] for c in b["conceitos"]]
    assert "gatilho" in ids
    # catálogo genérico não carrega número de ativo nenhum
    assert "R$" not in json.dumps(b, ensure_ascii=False)


def test_rota_conceito_ancora_nos_numeros_enviados(cli):
    b = cli.post("/api/conceito/gatilho", json={
        "modo": "estudo",
        "dados": {"ticker": "PETR4", "entrada": 38.5, "stop": 36.2,
                  "estado": "armado", "distancia": 0.45, "distanciaEmR": 0.9},
    }).json()
    corpo = json.dumps(b, ensure_ascii=False)
    assert b["ligada"] is True
    assert "R$ 38,50" in corpo and "0,9R" in corpo


def test_rota_conceito_respeita_o_modo_do_corpo(cli):
    edu = json.dumps(cli.post("/api/conceito/gatilho", json={"modo": "estudo"}).json(), ensure_ascii=False)
    ope = json.dumps(cli.post("/api/conceito/gatilho", json={"modo": "operador"}).json(), ensure_ascii=False)
    assert "CONDIÇÃO ARMADA" in edu and "PLANO ARMADO" not in edu
    assert "PLANO ARMADO" in ope and "CONDIÇÃO ARMADA" not in ope


def test_camada_desligada_NAO_e_404(cli):
    """404 nos dois casos deixava o front sem como distinguir 'some a
    afordância' de 'id errado' — e o comportamento certo é oposto em cada."""
    os.environ["B3_DIDATICA_OFF"] = "1"
    r = cli.post("/api/conceito/gatilho", json={"modo": "estudo"})
    assert r.status_code == 200 and r.json()["ligada"] is False
    cat = cli.get("/api/conceitos").json()
    assert cat["ligada"] is False and cat["conceitos"] == []


def test_id_inexistente_continua_404(cli):
    assert cli.post("/api/conceito/nao-existe", json={}).status_code == 404


def test_dados_hostis_nao_derrubam_a_rota(cli):
    for dados in ({"entrada": "lixo"}, {"entrada": None}, {"rotuloArmado": "COMPRE"},
                  {"estado": 123}, []):
        r = cli.post("/api/conceito/gatilho", json={"dados": dados})
        assert r.status_code == 200
        assert "COMPRE" not in json.dumps(r.json(), ensure_ascii=False)


# ------------------------------------- Fase 0a: a classe de aviso vai silenciosa
class _ClienteFake:
    """Grava o que foi enviado e responde 200 — sem tocar a rede."""

    def __init__(self):
        self.chamadas = []

    async def post(self, url, headers=None, content=None):
        self.chamadas.append({"url": url, "headers": headers or {},
                              "body": json.loads(content or "{}")})

        class _R:
            status_code = 200

            def json(self):
                return {}
        return _R()


def _apns_configurado(monkeypatch):
    for k, v in (("APNS_TEAM_ID", "T"), ("APNS_KEY_ID", "K"),
                 ("APNS_AUTH_KEY", "x"), ("APNS_TOPIC", "com.exemplo")):
        monkeypatch.setenv(k, v)
    monkeypatch.setattr(push, "_jwt", lambda: "jwt-falso")


def test_aviso_de_condicao_vai_silencioso_e_em_prioridade_baixa(monkeypatch, tmp_path):
    from app import db
    conn = db.connect(str(tmp_path / "b3.db"))
    _apns_configurado(monkeypatch)
    push.register_token(conn, "u1", "tok-1")
    cli = _ClienteFake()
    r = asyncio.run(push.send_to_user(conn, "u1", "titulo", "corpo",
                                      som=False, prioridade="5", client=cli))
    assert r["sent"] == 1
    envio = cli.chamadas[0]
    assert "sound" not in envio["body"]["aps"], "alerta de mercado com som num simulador"
    assert envio["headers"]["apns-priority"] == "5"
    conn.close()


def test_acao_do_operador_segue_com_som_e_prioridade_alta(monkeypatch, tmp_path):
    """O padrão NÃO mudou: quem já usava send_to_user continua igual."""
    from app import db
    conn = db.connect(str(tmp_path / "b3.db"))
    _apns_configurado(monkeypatch)
    push.register_token(conn, "u1", "tok-1")
    cli = _ClienteFake()
    asyncio.run(push.send_to_user(conn, "u1", "t", "c", client=cli))
    assert cli.chamadas[0]["body"]["aps"]["sound"] == "default"
    assert cli.chamadas[0]["headers"]["apns-priority"] == "10"
    conn.close()


def test_payload_carrega_o_ticker_fora_do_aps(monkeypatch, tmp_path):
    """Sem `t` no payload o toque abre o app na aba inicial e não há nada sobre
    o ativo em lugar nenhum — interrupção sem destino."""
    from app import db
    conn = db.connect(str(tmp_path / "b3.db"))
    _apns_configurado(monkeypatch)
    push.register_token(conn, "u1", "tok-1")
    cli = _ClienteFake()
    asyncio.run(push.send_to_user(conn, "u1", "t", "c", client=cli,
                                  extra={"t": "PETR4", "kind": "timing"}))
    corpo = cli.chamadas[0]["body"]
    assert corpo["t"] == "PETR4" and corpo["kind"] == "timing"
    assert "t" not in corpo["aps"], "dados do app não vão dentro do aps"
    conn.close()


def test_extra_nao_sobrescreve_o_aps(monkeypatch, tmp_path):
    from app import db
    conn = db.connect(str(tmp_path / "b3.db"))
    _apns_configurado(monkeypatch)
    push.register_token(conn, "u1", "tok-1")
    cli = _ClienteFake()
    asyncio.run(push.send_to_user(conn, "u1", "titulo", "corpo", client=cli,
                                  extra={"aps": {"alert": "sequestrado"}, "t": None}))
    assert cli.chamadas[0]["body"]["aps"]["alert"]["title"] == "titulo"
    assert "t" not in cli.chamadas[0]["body"], "valor None não vira chave"
    conn.close()


def test_cliente_injetado_e_reusado_sem_abrir_conexao_nova(monkeypatch, tmp_path):
    """O parâmetro existe para o fan-out do laço: N usuários não podem abrir N
    conexões HTTP/2 em série."""
    from app import db
    conn = db.connect(str(tmp_path / "b3.db"))
    _apns_configurado(monkeypatch)
    push.register_token(conn, "u1", "tok-1")
    push.register_token(conn, "u1", "tok-2")
    import httpx

    def _proibido(*a, **k):
        raise AssertionError("abriu AsyncClient novo mesmo recebendo um cliente")
    monkeypatch.setattr(httpx, "AsyncClient", _proibido)
    cli = _ClienteFake()
    r = asyncio.run(push.send_to_user(conn, "u1", "t", "c", client=cli))
    assert r["sent"] == 2 and len(cli.chamadas) == 2
    conn.close()
