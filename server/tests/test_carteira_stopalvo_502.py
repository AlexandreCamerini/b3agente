"""Debug 2026-10-14 — `POST /api/carteira-stopalvo/{ticker}` devolvia 502 em
produção 4 de 4 vezes (BRAP4, BPAC11, UGPA3, ITUB4), sempre logo após um
`POST /api/buy`, e a causa ficou INVISÍVEL: o `except` em volta de
`llm.analyze_carteira` convertia a exceção em 502 sem registrar nada no
servidor. As rotas N2 têm fallback determinístico (FIX-C01) e mascaram a mesma
falha — o N3 é a única superfície que a expõe, e mesmo assim só ao cliente.

Guardiões:
  (1) a falha da IA no N3 deixa UMA linha `[ia-falha]` no log do servidor,
      com tipo/código/provedor/modelo — e sem segredo (chave, token na URL);
  (2) o 502 continua 502 (contrato do popup do cliente intacto);
  (3) cotação com `change=None` (brapi sem variação, provedor degradado) não
      derruba a montagem do prompt do N3 — o `:+.2f` sobre None levantava
      TypeError antes de qualquer chamada ao provedor;
  (4) o caminho feliz com modelo vazio usa o fallback do provedor e chega ao
      provedor com o ID `claude-haiku-4-5` (ativo na API em 2026-10-14).
"""
import asyncio
import importlib
import os
import sys
import tempfile

import httpx
import pytest
from fastapi.testclient import TestClient

CONFIG_ENV_SEM_MODELO = {"provider": "anthropic", "model": "", "keySource": "env",
                         "appMode": "operador"}
SEGREDO = "sk-ant-api03-SEGREDOQUENAOPODEVAZAR123"


@pytest.fixture(autouse=True)
def _isolado():
    from app import agent, brapi_budget, managed
    original = sys.modules.get("app.main")
    brapi_budget.reset()
    agent.reset_kill_switch_cache()
    managed.reset_cache()
    yield
    brapi_budget.reset()
    agent.reset_kill_switch_cache()
    managed.reset_cache()
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


def _client(monkeypatch):
    d = tempfile.mkdtemp(prefix="b3_stopalvo_502_test_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    monkeypatch.setenv("ANTHROPIC_API_KEY", SEGREDO)
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")

    async def _quote(t):
        return {"t": t, "price": 20.15, "change": -1.2, "source": "brapi"}

    async def _snap_falha(*_a, **_k):
        raise ValueError("sem histórico (teste)")
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote)
    monkeypatch.setattr(main.technical_snapshot, "get", _snap_falha)
    return TestClient(main.app), main


@pytest.mark.parametrize("erro_factory, esperado", [
    (lambda llm: llm._provider_error({"provider": "anthropic", "model": "claude-haiku-4-5",
                                      "keySource": "env"}, 401, "invalid x-api-key"),
     "provider_http_401"),
    (lambda llm: RuntimeError("falhou https://x.test/v1?key=" + SEGREDO + " com " + SEGREDO),
     "RuntimeError"),
])
def test_falha_da_ia_no_n3_vira_502_e_deixa_rastro_sem_segredo(monkeypatch, capsys, erro_factory, esperado):
    c, main = _client(monkeypatch)

    async def _falha(*_a, **_k):
        raise erro_factory(main.llm)
    monkeypatch.setattr(main.llm, "analyze_carteira", _falha)

    r = c.post("/api/carteira-stopalvo/BRAP4", json={"config": dict(CONFIG_ENV_SEM_MODELO)})
    assert r.status_code == 502, r.text

    log = capsys.readouterr().out
    linhas = [ln for ln in log.splitlines() if ln.startswith("[ia-falha]")]
    assert len(linhas) == 1, log
    assert "rota=carteira-stopalvo" in linhas[0] and "t=BRAP4" in linhas[0]
    assert esperado in linhas[0], linhas[0]
    assert SEGREDO not in log, "segredo vazou no log do servidor"


def test_resumo_de_falha_redige_chave_em_url_e_token_solto():
    from app import llm
    txt = llm.resumo_falha_ia(RuntimeError(
        "GET https://generativelanguage.googleapis.com/v1beta/models/x:gen?key=AIzaSyFAKEFAKEFAKE123&alt=json "
        "token " + SEGREDO))
    assert "AIzaSyFAKEFAKEFAKE123" not in txt
    assert SEGREDO not in txt
    assert "key=***" in txt


def test_prompt_do_n3_aguenta_cotacao_sem_variacao():
    from app import llm
    user = llm._build_user_prompt("BRAP4", {"price": 20.15, "change": None}, {"candles": []})
    assert "R$ 20.15" in user
    assert "None" not in user


def test_n3_com_modelo_vazio_chega_ao_provedor_com_haiku_e_devolve_proposta(monkeypatch):
    from app import llm
    monkeypatch.setenv("ANTHROPIC_API_KEY", SEGREDO)
    enviado = {}

    class _Cliente:  # sem rede e sem SSL (o AsyncClient real carrega certifi no init)
        def __init__(self, *_a, **_k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_a):
            return False

        async def post(self, url, headers=None, json=None, **_k):
            enviado.update(json or {})
            texto = '[{"ativo":"BRAP4","stop":19.4,"alvo":21.6,"operar":true,"explicacao":"ok"}]'
            return httpx.Response(200, json={"content": [{"type": "text", "text": texto}],
                                             "usage": {"input_tokens": 1, "output_tokens": 1},
                                             "stop_reason": "end_turn"},
                                  request=httpx.Request("POST", url))
    monkeypatch.setattr(llm.httpx, "AsyncClient", _Cliente)

    res = asyncio.run(llm.analyze_carteira(dict(CONFIG_ENV_SEM_MODELO), {}, {"cash": 1000.0},
                                           "BRAP4", {"price": 20.15, "change": None},
                                           {"candles": []}, "prompt"))
    assert enviado["model"] == "claude-haiku-4-5"
    assert res["proposal"] == {"stop": 19.4, "alvo": 21.6}
