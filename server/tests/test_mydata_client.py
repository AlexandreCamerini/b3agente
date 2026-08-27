"""Fase 9, Plano 01 — cliente HTTP do mydata (`mydata.acamerini.app`).

O que estes testes protegem:
  • autenticação é SEMPRE por header `X-API-Key` — o hub NÃO usa Bearer
    (`~/dev/cvm-financas/app/api/main.py:135-137`, `exigir_chave`);
  • `MYDATA_URL` só aceita `https://` (ou `http://localhost`/`127.0.0.1` em
    dev) — é o único ponto onde o operador decide para onde a chave viaja
    (T-09-02 do threat model do plano);
  • 429/401 NUNCA fazem retry (retry em 429 queimaria cota que já acabou);
    5xx tenta 2 vezes;
  • a cota real (`X-Quota-Limite`/`X-Quota-Restante`) é capturada de TODA
    resposta em `LAST_QUOTA` — verdade > previsão local do orçamento;
  • paginação por `proximo_cursor` percorre até o fim ou até `PAGINAS_MAX`,
    sem loop infinito quando o servidor nunca zera o cursor;
  • pedido de intraday é recusado ANTES de tocar a rede (o COTAHIST não
    publica intraday, ADR-001 intocada) e o mapeamento gold_cotacoes→candle
    nunca troca `quantidade_negociada` (papéis) por `volume_financeiro` (R$).
Offline: `fetch_json` é injetável para `_paginar`/`get_history`; para os
ramos de status HTTP de `_fetch_json`, `httpx.AsyncClient` é substituído por
um fake que nunca toca a rede.
"""
import asyncio

import httpx
import pytest

from app import mydata_client as m


# ---------------------------------------------------------------------------
# Fake de transporte HTTP — só para os testes de `_fetch_json` (ramos de
# status). `_paginar`/`get_history` usam o `fetch_json` injetável, não isto.
# ---------------------------------------------------------------------------
class _FakeResponse:
    def __init__(self, status_code, headers=None, json_body=None, json_error=False):
        self.status_code = status_code
        self.headers = headers or {}
        self._json_body = json_body
        self._json_error = json_error

    def json(self):
        if self._json_error:
            raise ValueError("corpo não é JSON")
        return self._json_body


class _FakeAsyncClient:
    """Substitui `httpx.AsyncClient`. Consome uma fila de respostas
    pré-programada (`_FILA`), uma por chamada `.get()`, e registra o que foi
    chamado em `_CHAMADAS` para asserção."""

    _FILA: list = []
    _CHAMADAS: list = []

    def __init__(self, timeout=None):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def get(self, url, params=None, headers=None):
        _FakeAsyncClient._CHAMADAS.append(
            {"url": url, "params": params, "headers": headers})
        return _FakeAsyncClient._FILA.pop(0)


async def _no_sleep(_):
    return None


@pytest.fixture(autouse=True)
def _limpo(monkeypatch):
    _FakeAsyncClient._FILA = []
    _FakeAsyncClient._CHAMADAS = []
    m.LAST_QUOTA.clear()
    monkeypatch.delenv("MYDATA_URL", raising=False)
    monkeypatch.delenv("MYDATA_TOKEN", raising=False)
    yield
    _FakeAsyncClient._FILA = []
    _FakeAsyncClient._CHAMADAS = []
    m.LAST_QUOTA.clear()


def _fake_get_history(payload):
    async def fetch_json(path, params):
        fetch_json.chamadas.append((path, dict(params)))
        return payload
    fetch_json.chamadas = []
    return fetch_json


# ---------------------------------------------------------------------------
# base_url()
# ---------------------------------------------------------------------------
def test_base_url_sem_env_usa_default():
    assert m.base_url() == "https://mydata.acamerini.app"


def test_base_url_http_fora_de_localhost_levanta(monkeypatch):
    monkeypatch.setenv("MYDATA_URL", "http://exemplo.com")
    with pytest.raises(ValueError):
        m.base_url()


def test_base_url_https_remove_barra_final(monkeypatch):
    monkeypatch.setenv("MYDATA_URL", "https://outro.host/")
    assert m.base_url() == "https://outro.host"


def test_base_url_http_localhost_e_permitido_para_dev(monkeypatch):
    monkeypatch.setenv("MYDATA_URL", "http://localhost:8000")
    assert m.base_url() == "http://localhost:8000"


# ---------------------------------------------------------------------------
# tem_token()
# ---------------------------------------------------------------------------
def test_tem_token_ausente_ou_so_espacos_e_false(monkeypatch):
    monkeypatch.delenv("MYDATA_TOKEN", raising=False)
    assert m.tem_token() is False
    monkeypatch.setenv("MYDATA_TOKEN", "   ")
    assert m.tem_token() is False


def test_tem_token_com_valor_e_true(monkeypatch):
    monkeypatch.setenv("MYDATA_TOKEN", "f00b4554-segredo")
    assert m.tem_token() is True


# ---------------------------------------------------------------------------
# _fetch_json — header, cota, ramos de status
# ---------------------------------------------------------------------------
def test_fetch_json_monta_header_x_api_key_nunca_authorization(monkeypatch):
    monkeypatch.setenv("MYDATA_TOKEN", "tok-teste")
    monkeypatch.setattr(httpx, "AsyncClient", _FakeAsyncClient)
    _FakeAsyncClient._FILA = [
        _FakeResponse(200, json_body={"dados": [], "proximo_cursor": None})]
    asyncio.run(m._fetch_json("/v1/cotacoes/PETR4", {"de": "2026-01-01"}))
    headers = _FakeAsyncClient._CHAMADAS[0]["headers"]
    assert headers["X-API-Key"] == "tok-teste"
    assert "Authorization" not in headers


def test_quota_headers_populam_last_quota(monkeypatch):
    monkeypatch.setenv("MYDATA_TOKEN", "tok-teste")
    monkeypatch.setattr(httpx, "AsyncClient", _FakeAsyncClient)
    _FakeAsyncClient._FILA = [_FakeResponse(
        200,
        headers={"X-Quota-Limite": "2000", "X-Quota-Restante": "1990"},
        json_body={"dados": [], "proximo_cursor": None})]
    asyncio.run(m._fetch_json("/v1/cotacoes/PETR4", {}))
    assert m.LAST_QUOTA["X-Quota-Limite"] == "2000"
    assert m.LAST_QUOTA["X-Quota-Restante"] == "1990"


def test_429_nao_faz_retry_e_cita_janela_e_quota(monkeypatch):
    monkeypatch.setenv("MYDATA_TOKEN", "tok-teste")
    monkeypatch.setattr(httpx, "AsyncClient", _FakeAsyncClient)
    _FakeAsyncClient._FILA = [_FakeResponse(
        429,
        headers={"Retry-After": "60"},
        json_body={"erro": {"codigo": "quota_excedida",
                             "mensagem": "Quota por minuto esgotada."}})]
    with pytest.raises(m.MydataIndisponivel, match="60"):
        asyncio.run(m._fetch_json("/v1/cotacoes/PETR4", {}))
    assert len(_FakeAsyncClient._CHAMADAS) == 1   # sem retry: retry queimaria cota


def test_401_nao_faz_retry_e_cita_chave_invalida(monkeypatch):
    monkeypatch.setenv("MYDATA_TOKEN", "tok-errado")
    monkeypatch.setattr(httpx, "AsyncClient", _FakeAsyncClient)
    _FakeAsyncClient._FILA = [_FakeResponse(401, json_body={
        "erro": {"codigo": "chave_invalida", "mensagem": "Chave inválida."}})]
    with pytest.raises(m.MydataIndisponivel, match="chave_invalida") as exc:
        asyncio.run(m._fetch_json("/v1/cotacoes/PETR4", {}))
    assert len(_FakeAsyncClient._CHAMADAS) == 1
    assert "tok-errado" not in str(exc.value)  # nunca no log/erro


def test_5xx_tenta_duas_vezes_e_depois_levanta(monkeypatch):
    monkeypatch.setenv("MYDATA_TOKEN", "tok-teste")
    monkeypatch.setattr(httpx, "AsyncClient", _FakeAsyncClient)
    monkeypatch.setattr(m.asyncio, "sleep", _no_sleep)
    _FakeAsyncClient._FILA = [_FakeResponse(502), _FakeResponse(503)]
    with pytest.raises(m.MydataIndisponivel):
        asyncio.run(m._fetch_json("/v1/cotacoes/PETR4", {}))
    assert len(_FakeAsyncClient._CHAMADAS) == 2


def test_corpo_nao_json_vira_mydata_indisponivel(monkeypatch):
    monkeypatch.setenv("MYDATA_TOKEN", "tok-teste")
    monkeypatch.setattr(httpx, "AsyncClient", _FakeAsyncClient)
    _FakeAsyncClient._FILA = [_FakeResponse(200, json_error=True)]
    with pytest.raises(m.MydataIndisponivel):
        asyncio.run(m._fetch_json("/v1/cotacoes/PETR4", {}))


# ---------------------------------------------------------------------------
# _paginar — cursor
# ---------------------------------------------------------------------------
def test_paginar_uma_pagina_sem_cursor_faz_1_chamada():
    fake = _fake_get_history({"dados": [{"a": 1}, {"a": 2}], "proximo_cursor": None})
    out = asyncio.run(m._paginar("/v1/cotacoes/PETR4", {"de": "2026-01-01"},
                                  fetch_json=fake))
    assert out == [{"a": 1}, {"a": 2}]
    assert len(fake.chamadas) == 1


def test_paginar_duas_paginas_encadeia_cursor():
    paginas = [
        {"dados": [{"a": 1}], "proximo_cursor": "cur-2"},
        {"dados": [{"a": 2}], "proximo_cursor": None},
    ]

    async def fetch_json(path, params):
        fetch_json.chamadas.append((path, dict(params)))
        return paginas[len(fetch_json.chamadas) - 1]
    fetch_json.chamadas = []

    out = asyncio.run(m._paginar("/v1/cotacoes/PETR4", {"de": "2026-01-01"},
                                  fetch_json=fetch_json))
    assert out == [{"a": 1}, {"a": 2}]
    assert len(fetch_json.chamadas) == 2
    assert "cursor" not in fetch_json.chamadas[0][1]
    assert fetch_json.chamadas[1][1]["cursor"] == "cur-2"


def test_paginar_teto_de_paginas_nao_trava():
    async def fetch_json(path, params):
        fetch_json.chamadas.append((path, dict(params)))
        return {"dados": [{"n": len(fetch_json.chamadas)}],
                "proximo_cursor": "sempre-mais"}
    fetch_json.chamadas = []

    out = asyncio.run(m._paginar("/v1/cotacoes/PETR4", {"de": "2026-01-01"},
                                  fetch_json=fetch_json))
    assert len(fetch_json.chamadas) == m.PAGINAS_MAX
    assert len(out) == m.PAGINAS_MAX
