"""aba-opcoes F1 (ADR-027) — teste AO VIVO contra `mcp.semente.dev`, opt-in.

Roda só com credencial real no ambiente:

    MCP_CLIENT_ID=... MCP_CLIENT_SECRET=... \\
      .venv/bin/python -m pytest -q tests/test_mcp_vivo.py -s

Sem `MCP_CLIENT_SECRET` o arquivo inteiro faz `skip` — nunca `fail`. Ele
existe para responder três perguntas que só o ambiente real responde:
(1) o emissor aceita a credencial de máquina e devolve o token esperado;
(2) o serviço responde `get_option_chain` com `trading_date`;
(3) qual é a FORMA real do `check_data_freshness` — é dela que a Fase 2 tira
o parser de frescor, e é por isso que o teste IMPRIME o `structured_content`
cru em vez de afirmar campo.

Nenhuma asserção sobre NÚMERO de mercado: o dado muda todo pregão, e um
teste que afirma preço seria vermelho no dia seguinte por estar certo. E
nada aqui imprime o segredo nem o token — o token só aparece pelo TAMANHO.
"""
from __future__ import annotations

import asyncio
import os

import pytest

from app import mcp_client

pytestmark = pytest.mark.skipif(
    not os.environ.get("MCP_CLIENT_SECRET"),
    reason="teste ao vivo: exige MCP_CLIENT_SECRET no ambiente",
)


@pytest.fixture(autouse=True)
def _limpo():
    mcp_client.reset_cache()
    yield
    mcp_client.reset_cache()


def test_vivo_emissor_devolve_access_token():
    token = asyncio.run(mcp_client._access_token())
    assert isinstance(token, str) and token
    # SÓ o tamanho. Imprimir o valor deixaria a credencial no log do CI e no
    # scrollback do terminal.
    print(f"\naccess_token obtido: {len(token)} caracteres; "
          f"exp em {int(mcp_client._TOKEN['exp'] - mcp_client._relogio())}s")


def test_vivo_get_option_chain_traz_trading_date():
    r = asyncio.run(mcp_client.call_tool("get_option_chain",
                                         {"ticker": "PETR4", "limit": 1}))
    print("\ntrading_date:", r.dados.get("trading_date"))
    assert isinstance(r.dados.get("trading_date"), str)
    assert r.cache is False


def test_vivo_check_data_freshness_forma_crua():
    """A FORMA da resposta é o entregável deste teste. A Fase 2 lê o que for
    impresso aqui e escreve o parser em cima do real, em vez de adivinhar."""
    r = asyncio.run(mcp_client.call_tool("check_data_freshness", {}))
    print("\nstructured_content cru de check_data_freshness:")
    print(r.dados)
    assert isinstance(r.dados, dict) and r.dados, \
        "check_data_freshness devolveu conteúdo vazio — sem isso a Decisão 8 " \
        "do ADR-027 (bloqueio por frescor) não tem em que se apoiar"
