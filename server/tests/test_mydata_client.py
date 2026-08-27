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


# ---------------------------------------------------------------------------
# valida_fatia() — recusa de intraday ANTES de tocar a rede
# ---------------------------------------------------------------------------
def test_valida_fatia_recusa_intraday_citando_adr001_e_yahoo():
    with pytest.raises(m.MydataForaDaFatia, match="ADR-001"):
        m.valida_fatia("1mo", "15m")
    with pytest.raises(m.MydataForaDaFatia, match="Yahoo"):
        m.valida_fatia("1mo", "15m")


def test_valida_fatia_aceita_diario():
    m.valida_fatia("1mo", "1d")   # não levanta


def test_valida_fatia_recusa_range_desconhecido():
    with pytest.raises(m.MydataForaDaFatia):
        m.valida_fatia("banana", "1d")


# ---------------------------------------------------------------------------
# get_history() — contrato CandleProvider, mapeamento gold_cotacoes→candle
# ---------------------------------------------------------------------------
def test_get_history_recusa_intraday_sem_tocar_a_rede(monkeypatch):
    monkeypatch.setenv("MYDATA_TOKEN", "tok-teste")
    fake = _fake_get_history({"dados": [], "proximo_cursor": None})
    with pytest.raises(m.MydataForaDaFatia):
        asyncio.run(m.get_history("PETR4", rng="1mo", interval="15m",
                                   fetch_json=fake))
    assert fake.chamadas == []


def test_get_history_sem_token_levanta_runtime_error(monkeypatch):
    monkeypatch.delenv("MYDATA_TOKEN", raising=False)
    fake = _fake_get_history({"dados": [], "proximo_cursor": None})
    with pytest.raises(RuntimeError) as e:
        asyncio.run(m.get_history("PETR4", rng="1mo", interval="1d",
                                   fetch_json=fake))
    assert "MYDATA_TOKEN" in str(e.value)


def test_get_history_normaliza_ticker_e_chama_path_correto(monkeypatch):
    monkeypatch.setenv("MYDATA_TOKEN", "tok-teste")
    fake = _fake_get_history({"dados": [], "proximo_cursor": None})
    asyncio.run(m.get_history("petr4.sa", rng="1mo", fetch_json=fake))
    assert fake.chamadas[0][0] == "/v1/cotacoes/PETR4"


def test_get_history_params_tem_de_e_limite_sem_ate(monkeypatch):
    monkeypatch.setenv("MYDATA_TOKEN", "tok-teste")
    fake = _fake_get_history({"dados": [], "proximo_cursor": None})
    asyncio.run(m.get_history("PETR4", rng="1mo", fetch_json=fake))
    params = fake.chamadas[0][1]
    assert "de" in params and "ate" not in params
    assert params["limite"] == m.LIMITE_MAX


def test_get_history_mapeia_gold_cotacoes_para_candle(monkeypatch):
    monkeypatch.setenv("MYDATA_TOKEN", "tok-teste")
    linha = {"dt_pregao": "2026-08-25", "preco_abertura": 37.1,
             "preco_maximo": 37.5, "preco_minimo": 36.9,
             "preco_fechamento": 37.26, "quantidade_negociada": 1234500,
             "volume_financeiro": 999999999, "hv21": 0.31, "hv63": 0.29}
    fake = _fake_get_history({"dados": [linha], "proximo_cursor": None})
    out = asyncio.run(m.get_history("PETR4", rng="1mo", fetch_json=fake))
    assert out == {"t": "PETR4", "currency": "BRL", "candles": [{
        "date": "2026-08-25", "open": 37.1, "high": 37.5, "low": 36.9,
        "close": 37.26, "volume": 1234500,
    }]}


def test_get_history_descarta_linha_sem_fechamento(monkeypatch):
    monkeypatch.setenv("MYDATA_TOKEN", "tok-teste")
    linha = {"dt_pregao": "2026-08-25", "preco_abertura": 37.1,
             "preco_maximo": 37.5, "preco_minimo": 36.9,
             "preco_fechamento": None, "quantidade_negociada": 1234500}
    fake = _fake_get_history({"dados": [linha], "proximo_cursor": None})
    out = asyncio.run(m.get_history("PETR4", rng="1mo", fetch_json=fake))
    assert out["candles"] == []


def test_get_history_resposta_vazia_devolve_candles_vazio(monkeypatch):
    monkeypatch.setenv("MYDATA_TOKEN", "tok-teste")
    fake = _fake_get_history({"dados": [], "proximo_cursor": None})
    out = asyncio.run(m.get_history("PETR4", rng="1mo", fetch_json=fake))
    assert out["candles"] == []


def test_range_dias_cobre_os_ranges_do_candle_cache():
    assert {"1mo", "1y", "2y"} <= set(m.RANGE_DIAS)


# ---------------------------------------------------------------------------
# get_vencimentos() — endpoint dedicado, sem paginação
# ---------------------------------------------------------------------------
def _fake_fetch_json(payload):
    async def fetch_json(path, params):
        fetch_json.chamadas.append((path, dict(params)))
        return payload
    fetch_json.chamadas = []
    return fetch_json


def test_get_vencimentos_chama_path_correto_e_normaliza_ticker(monkeypatch):
    monkeypatch.setenv("MYDATA_TOKEN", "tok-teste")
    fake = _fake_fetch_json({"dados": []})
    asyncio.run(m.get_vencimentos("petr4.sa", fetch_json=fake))
    assert fake.chamadas[0][0] == "/v1/opcoes/PETR4/vencimentos"


def test_get_vencimentos_com_pregao_inclui_param(monkeypatch):
    monkeypatch.setenv("MYDATA_TOKEN", "tok-teste")
    fake = _fake_fetch_json({"dados": []})
    asyncio.run(m.get_vencimentos("PETR4", pregao="2026-08-25", fetch_json=fake))
    assert fake.chamadas[0][1]["pregao"] == "2026-08-25"


def test_get_vencimentos_sem_pregao_nao_inclui_a_chave(monkeypatch):
    monkeypatch.setenv("MYDATA_TOKEN", "tok-teste")
    fake = _fake_fetch_json({"dados": []})
    asyncio.run(m.get_vencimentos("PETR4", fetch_json=fake))
    assert "pregao" not in fake.chamadas[0][1]


def test_get_vencimentos_resposta_vazia_devolve_lista_vazia_sem_levantar(monkeypatch):
    monkeypatch.setenv("MYDATA_TOKEN", "tok-teste")
    fake = _fake_fetch_json({"dados": []})
    out = asyncio.run(m.get_vencimentos("PETR4", fetch_json=fake))
    assert out == []


def test_get_vencimentos_devolve_dados_crus_sem_remapear(monkeypatch):
    monkeypatch.setenv("MYDATA_TOKEN", "tok-teste")
    linha = {"dt_vencimento": "2026-09-19", "contratos": 40, "com_sigma": 35,
              "vence_no_pregao": 0, "menor_strike": 30.0, "maior_strike": 45.0}
    fake = _fake_fetch_json({"dados": [linha]})
    out = asyncio.run(m.get_vencimentos("PETR4", fetch_json=fake))
    assert out == [linha]


def test_get_vencimentos_nao_usa_paginar(monkeypatch):
    """O endpoint de vencimentos não devolve proximo_cursor — usar _paginar
    aqui quebraria silenciosamente ou faria 1 chamada supérflua a mais."""
    monkeypatch.setenv("MYDATA_TOKEN", "tok-teste")
    fake = _fake_fetch_json({"dados": [{"dt_vencimento": "2026-09-19"}]})
    asyncio.run(m.get_vencimentos("PETR4", fetch_json=fake))
    assert len(fake.chamadas) == 1


def test_get_vencimentos_resposta_nao_dict_levanta_mydata_indisponivel(monkeypatch):
    monkeypatch.setenv("MYDATA_TOKEN", "tok-teste")

    async def fetch_json(path, params):
        return None
    with pytest.raises(m.MydataIndisponivel):
        asyncio.run(m.get_vencimentos("PETR4", fetch_json=fetch_json))


# ---------------------------------------------------------------------------
# get_options_chain() — cadeia paginada
# ---------------------------------------------------------------------------
def test_get_options_chain_chama_path_e_params_corretos(monkeypatch):
    monkeypatch.setenv("MYDATA_TOKEN", "tok-teste")
    fake = _fake_fetch_json({"dados": [], "proximo_cursor": None})
    asyncio.run(m.get_options_chain("PETR4", vencimento="2026-09-19", fetch_json=fake))
    assert fake.chamadas[0][0] == "/v1/opcoes/PETR4"
    assert fake.chamadas[0][1]["vencimento"] == "2026-09-19"
    assert fake.chamadas[0][1]["limite"] == m.LIMITE_MAX


def test_get_options_chain_percorre_proximo_cursor(monkeypatch):
    monkeypatch.setenv("MYDATA_TOKEN", "tok-teste")
    paginas = [
        {"dados": [{"contrato": "PETRA100"}], "proximo_cursor": "cur-2"},
        {"dados": [{"contrato": "PETRA200"}], "proximo_cursor": None},
    ]

    async def fetch_json(path, params):
        fetch_json.chamadas.append((path, dict(params)))
        return paginas[len(fetch_json.chamadas) - 1]
    fetch_json.chamadas = []
    out = asyncio.run(m.get_options_chain("PETR4", fetch_json=fetch_json))
    assert out == [{"contrato": "PETRA100"}, {"contrato": "PETRA200"}]
    assert len(fetch_json.chamadas) == 2


def test_get_options_chain_sem_token_levanta_runtime_error(monkeypatch):
    monkeypatch.delenv("MYDATA_TOKEN", raising=False)
    fake = _fake_fetch_json({"dados": [], "proximo_cursor": None})
    with pytest.raises(RuntimeError) as e:
        asyncio.run(m.get_options_chain("PETR4", fetch_json=fake))
    assert "MYDATA_TOKEN" in str(e.value)


def test_get_options_chain_propaga_mydata_indisponivel(monkeypatch):
    monkeypatch.setenv("MYDATA_TOKEN", "tok-teste")

    async def fetch_json(path, params):
        raise m.MydataIndisponivel("mydata inacessível")
    with pytest.raises(m.MydataIndisponivel):
        asyncio.run(m.get_options_chain("PETR4", fetch_json=fetch_json))


def test_get_options_chain_params_omitem_campos_falsy(monkeypatch):
    monkeypatch.setenv("MYDATA_TOKEN", "tok-teste")
    fake = _fake_fetch_json({"dados": [], "proximo_cursor": None})
    asyncio.run(m.get_options_chain("PETR4", fetch_json=fake))
    params = fake.chamadas[0][1]
    assert "vencimento" not in params
    assert "pregao" not in params
    assert "tipo" not in params
