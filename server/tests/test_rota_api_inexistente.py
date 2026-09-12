"""Rota de API que não existe responde 404 explicativo, nunca 405.

**Por que este arquivo existe** (achado ao vivo, 2026-09-11): o mount
catch-all que serve o front (`app.mount("/", StaticFiles(...))`) aceita só
GET/HEAD, então todo POST para um path não reconhecido voltava como
**405 Method Not Allowed**. O sintoma aparece exatamente na situação mais
comum do desenvolvimento — app à frente do servidor, entre o merge e a
publicação — e manda quem investiga procurar verbo HTTP errado no cliente em
vez da rota que o servidor ainda não tem. Custou uma sessão inteira: a aba
Opções dizia "method not allowed" porque a Fase 24 não tinha sido publicada.

O que estes testes travam, em uma frase cada:
  - POST para `/api/*` inexistente é 404, não 405;
  - o corpo diz o código, o método e o BUILD do servidor (a pergunta seguinte
    é sempre "qual build está no ar?");
  - o handler NÃO sombreia rota real nenhuma — inclusive as que respondem 401
    por falta de sessão, que são a maioria;
  - fora de `/api/`, o catch-all do SPA continua intacto.
"""
from __future__ import annotations

import importlib
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def cliente(monkeypatch):
    monkeypatch.delenv("B3_ADMIN_EMAILS", raising=False)
    d = tempfile.mkdtemp(prefix="b3_rota_inexistente_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    original = sys.modules.get("app.main")
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    yield TestClient(main.app), main
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


@pytest.mark.parametrize("metodo", ["post", "put", "patch", "delete"])
def test_metodo_de_escrita_em_rota_inexistente_e_404(cliente, metodo):
    c, _ = cliente
    # `request(metodo, ...)` e não `c.delete(json=...)`: o `delete` do
    # TestClient não aceita corpo nesta versão do httpx, e o que se mede aqui
    # é o MÉTODO, não o corpo.
    r = c.request(metodo.upper(), "/api/isto/nao/existe")
    assert r.status_code == 404, (
        f"{metodo.upper()} devolveu {r.status_code}; 405 aqui é o defeito que "
        f"este guardião existe para impedir — ele manda procurar verbo errado "
        f"no cliente em vez de rota ausente no servidor")


def test_corpo_diz_o_codigo_o_metodo_e_o_build(cliente):
    c, main = cliente
    d = c.post("/api/isto/nao/existe", json={}).json()["detail"]
    assert d["code"] == "rota_inexistente"
    assert d["metodo"] == "POST"
    # O build é o que separa "rota não existe" de "rota não foi publicada".
    assert d["build"] == main.SERVER_BUILD_ID
    assert "/api/isto/nao/existe" in d["message"]


def test_get_inexistente_tambem_e_404_com_o_mesmo_corpo(cliente):
    c, _ = cliente
    r = c.get("/api/isto/nao/existe")
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "rota_inexistente"


@pytest.mark.parametrize("rota,esperado", [
    ("/api/health", 200),
    ("/api/options/mcp/status", 401),
    ("/api/options/mcp/leitura/PETR4", 401),
    ("/api/options/mcp/cadeia/PETR4", 401),
])
def test_handler_nao_sombreia_rota_real(cliente, rota, esperado):
    """A regressão que este handler poderia causar é a pior de todas: engolir
    a API inteira com 404. As rotas de sessão (401) são a prova mais forte —
    elas passam pelo roteador ANTES de qualquer gate."""
    c, _ = cliente
    assert c.get(rota).status_code == esperado


def test_post_em_rota_real_nao_vira_404(cliente):
    c, _ = cliente
    # 401 (falta sessão), jamais 404: a rota existe e o handler não a cobriu.
    assert c.post("/api/options/mcp/setups/compilar", json={}).status_code == 401
