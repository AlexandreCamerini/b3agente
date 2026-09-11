"""aba-opcoes F1 (ADR-027) — comportamento do `mcp_client`, OFFLINE.

Nenhum teste deste arquivo toca a rede: a sessão MCP é falsa (monkeypatch de
`mcp.ClientSession` e de `mcp.client.streamable_http.streamable_http_client`,
que o `_chamar` importa TARDE e portanto lê no momento da chamada) e o
cliente HTTP do emissor também. Isso é de propósito: a tradução de erro do
`_chamar` — que é o miolo do módulo — só é exercitada de verdade se a falha
subir de dentro da sessão, e não se `_chamar` for substituído por um duble.

O teste ao vivo (opt-in, exige `MCP_CLIENT_SECRET`) mora em
`test_mcp_vivo.py`; aqui nada depende de credencial real.
"""
from __future__ import annotations

import asyncio

import pytest

from app import mcp_client

SEGREDO_DE_TESTE = "segredo-de-teste-nao-e-real-0000"
TOKEN_DE_TESTE = "token-de-teste-nao-e-real-1111"


@pytest.fixture(autouse=True)
def _estado_limpo(monkeypatch):
    mcp_client.reset_cache()
    mcp_client._HTTP = None
    monkeypatch.delenv("MCP_URL", raising=False)
    monkeypatch.delenv("B3_MCP_CACHE_S", raising=False)
    yield
    mcp_client.reset_cache()
    mcp_client._HTTP = None


# ---------------------------------------------------------------- dubles ---
class _Resposta:
    """Espelha o que o SDK devolve de `call_tool`: snake_case, `is_error` e
    `structured_content` (o contrato avisa que quem copia exemplo antigo
    escreve `serverInfo`/`structuredContent` e toma AttributeError)."""

    def __init__(self, structured_content=None, is_error=False):
        self.structured_content = structured_content
        self.is_error = is_error


class _SessaoFalsa:
    def __init__(self, resultado=None, erro=None):
        self.resultado = resultado
        self.erro = erro
        self.chamadas: list = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def initialize(self):
        return object()

    def _responde(self):
        if self.erro is not None:
            raise self.erro
        return self.resultado

    async def call_tool(self, nome, arguments=None, read_timeout_seconds=None):
        self.chamadas.append(("tools/call", nome, arguments, read_timeout_seconds))
        return self._responde()

    async def get_prompt(self, nome, arguments=None):
        self.chamadas.append(("prompts/get", nome, arguments))
        return self._responde()

    async def read_resource(self, uri):
        self.chamadas.append(("resources/read", uri))
        return self._responde()

    async def list_tools(self):
        self.chamadas.append(("tools/list",))
        return self._responde()


class _CtxFalso:
    def __init__(self, valor):
        self._valor = valor

    async def __aenter__(self):
        return self._valor

    async def __aexit__(self, *a):
        return False


class _RespHttp:
    def __init__(self, status_code=200, payload=None, json_quebra=False):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self._json_quebra = json_quebra

    def json(self):
        if self._json_quebra:
            raise ValueError("corpo não é JSON")
        return self._payload


class _HttpFalso:
    def __init__(self, resposta=None, erro=None):
        self.resposta = resposta
        self.erro = erro
        self.posts: list = []
        self.headers: dict = {}

    async def post(self, url, headers=None, data=None):
        self.posts.append({"url": url, "data": dict(data or {})})
        if self.erro is not None:
            raise self.erro
        return self.resposta


def _liga_sessao(monkeypatch, sessao):
    """Fia a sessão falsa nos dois pontos que `_chamar` importa tarde, e
    dispensa o token (o caminho de token tem testes próprios abaixo)."""
    import mcp
    import mcp.client.streamable_http as transporte

    monkeypatch.setattr(transporte, "streamable_http_client",
                        lambda u, **kw: _CtxFalso(("leitura", "escrita")))
    monkeypatch.setattr(mcp, "ClientSession", lambda leitura, escrita: sessao)

    async def _token_falso():
        return TOKEN_DE_TESTE

    monkeypatch.setattr(mcp_client, "_access_token", _token_falso)
    monkeypatch.setattr(mcp_client, "_cliente_http", lambda: _HttpFalso())
    return sessao


# ------------------------------------------------------- 1. erro de tool ---
def test_error_no_structured_content_vira_erro_de_tool_mesmo_com_is_error_falso(monkeypatch):
    """O contrato manda checar AS DUAS coisas: `is_error` E a chave `error`.
    O serviço devolve `is_error: false` com `error` no conteúdo justamente
    neste caso, e um cliente que olha só `is_error` trata a mensagem de erro
    como dado bom."""
    sessao = _liga_sessao(monkeypatch, _SessaoFalsa(_Resposta(
        {"error": "could not read the option chain for XXXX9",
         "available": ["PETR4", "VALE3"], "hint": "use o ativo-objeto"},
        is_error=False,
    )))

    with pytest.raises(mcp_client.McpErroDeTool) as exc:
        asyncio.run(mcp_client.call_tool("get_option_chain", {"ticker": "XXXX9"}))

    assert "XXXX9" in str(exc.value)
    assert exc.value.available == ["PETR4", "VALE3"]
    assert exc.value.hint == "use o ativo-objeto"

    # e NÃO cacheia: repetir o pedido tem de tocar a sessão de novo, senão a
    # correção do ticker pelo usuário ficaria 15 min presa ao erro anterior.
    with pytest.raises(mcp_client.McpErroDeTool):
        asyncio.run(mcp_client.call_tool("get_option_chain", {"ticker": "XXXX9"}))
    assert len(sessao.chamadas) == 2


# ------------------------------------------------------------- 2. -32000 ---
def test_mcperror_32000_vira_teto_atingido_com_reinicia_preservado(monkeypatch):
    from mcp.shared.exceptions import MCPError

    erro = MCPError(
        code=-32000,
        message="teto diário de 2000 chamadas atingido para boris; reinicia às 00:00 America/Sao_Paulo",
        data={"cliente": "boris", "escopo": "cliente", "chamadas_hoje": 2000,
              "teto": 2000, "reinicia": "00:00 America/Sao_Paulo"},
    )
    _liga_sessao(monkeypatch, _SessaoFalsa(erro=erro))

    with pytest.raises(mcp_client.McpTetoAtingido) as exc:
        asyncio.run(mcp_client.call_tool("get_option_chain", {"ticker": "PETR4"}))

    assert exc.value.data["reinicia"] == "00:00 America/Sao_Paulo"
    assert exc.value.data["escopo"] == "cliente"
    assert exc.value.data["chamadas_hoje"] == 2000


def test_mcperror_de_outro_codigo_vira_indisponivel(monkeypatch):
    from mcp.shared.exceptions import MCPError

    _liga_sessao(monkeypatch, _SessaoFalsa(
        erro=MCPError(code=-32601, message="method not found")))

    with pytest.raises(mcp_client.McpIndisponivel):
        asyncio.run(mcp_client.call_tool("tool_que_nao_existe"))


# ------------------------------------- 2b. -32000 sem prova (achado A-01) ---
def test_conexao_fechada_nao_vira_teto_mesmo_tendo_o_mesmo_32000(monkeypatch):
    """O CASO QUE MENTIA. `CONNECTION_CLOSED` do SDK é o MESMO -32000 que o
    contrato usa para teto diário, e até 2026-09-10 uma conexão caída saía da
    rota como HTTP 402 "o serviço atingiu o teto de chamadas do dia": um
    número de consumo que ninguém mediu (princípio 4 do CLAUDE.md) e um
    convite a esperar até a meia-noite sem motivo.

    A régua é a PROVA, não o código: teto de verdade vem com
    `chamadas_hoje`/`teto` em `data` (contrato, seção "Erro JSON-RPC -32000").
    """
    from mcp.shared.exceptions import MCPError
    from mcp.types import CONNECTION_CLOSED

    # o valor do SDK e o do contrato são o mesmo número — é daqui que nasce o
    # defeito, e o teste fixa isso para que a colisão não volte a passar batida
    assert CONNECTION_CLOSED == mcp_client.CODIGO_TETO

    _liga_sessao(monkeypatch, _SessaoFalsa(
        erro=MCPError(code=CONNECTION_CLOSED, message="Connection closed")))

    with pytest.raises(mcp_client.McpIndisponivel) as exc:
        asyncio.run(mcp_client.call_tool("get_option_chain", {"ticker": "PETR4"}))
    # e a mensagem do serviço chega a quem depura (achado A-02): antes só o
    # `code=` sobrevivia à tradução
    assert "Connection closed" in str(exc.value)


@pytest.mark.parametrize("dados", [
    None,
    {},
    {"escopo": "cliente", "reinicia": "00:00 America/Sao_Paulo"},   # sem números
    {"chamadas_hoje": 2000},                                        # só metade
    {"teto": 2000},                                                 # só a outra
    {"chamadas_hoje": "muitas", "teto": "2000"},                    # texto, não medição
    {"chamadas_hoje": True, "teto": True},                          # bool não é número
])
def test_32000_sem_os_dois_numeros_nunca_vira_teto(monkeypatch, dados):
    """Falso-negativo é o lado seguro: teto real sem os números vira 503
    ("tente em alguns minutos") em vez de 402 com contagem inventada."""
    from mcp.shared.exceptions import MCPError

    _liga_sessao(monkeypatch, _SessaoFalsa(
        erro=MCPError(code=-32000, message="algo aconteceu", data=dados)))

    with pytest.raises(mcp_client.McpIndisponivel):
        asyncio.run(mcp_client.call_tool("get_option_chain", {"ticker": "PETR4"}))


# --------------------- 2c. recusa PELO SERVIÇO (achados A-02 e A-05) ---
class _SessaoQueRecusa(_SessaoFalsa):
    """Imita o que o transporte FAZ diante de um 401 do serviço: o hook de
    status enxerga o 401 (o cliente HTTP é NOSSO, e o hook roda com os headers
    em mãos), e o SDK entrega `INTERNAL_ERROR` com uma mensagem CONSTANTE — o
    status não sobrevive à tradução (mcp 2.2.0,
    `mcp/client/streamable_http.py:383-411`). O duble chama o hook de verdade,
    e não uma imitação dele, porque hook + ContextVar é exatamente o mecanismo
    que a correção do A-02 introduziu: dublá-lo testaria o duble."""

    def __init__(self, recusas: int, resultado=None):
        super().__init__(resultado=resultado)
        self.recusas = recusas

    async def call_tool(self, nome, arguments=None, read_timeout_seconds=None):
        from mcp.shared.exceptions import MCPError
        from mcp.types import INTERNAL_ERROR

        self.chamadas.append(("tools/call", nome, arguments, read_timeout_seconds))
        if len(self.chamadas) <= self.recusas:
            await mcp_client._anotar_status_http(_RespHttp(401))
            raise MCPError(code=INTERNAL_ERROR,
                           message="Server returned an error response")
        return self.resultado


def _liga_sessao_com_token_real(monkeypatch, sessao):
    """Como `_liga_sessao`, mas SEM dispensar o token: o emissor é um duble
    que devolve token a cada POST, e o teste conta os POSTs para saber quantas
    renovações houve."""
    import mcp
    import mcp.client.streamable_http as transporte

    monkeypatch.setattr(transporte, "streamable_http_client",
                        lambda u, **kw: _CtxFalso(("leitura", "escrita")))
    monkeypatch.setattr(mcp, "ClientSession", lambda leitura, escrita: sessao)
    monkeypatch.setenv("MCP_CLIENT_ID", "boris")
    monkeypatch.setenv("MCP_CLIENT_SECRET", SEGREDO_DE_TESTE)
    monkeypatch.setattr(mcp_client, "_relogio", lambda: 1_000_000.0)
    http = _HttpFalso(_RespHttp(200, {"access_token": TOKEN_DE_TESTE,
                                      "expires_in": 3600}))
    monkeypatch.setattr(mcp_client, "_cliente_http", lambda: http)
    mcp_client._TOKEN.clear()
    return http


def test_401_do_servico_e_classificado_como_recusa_e_nao_como_fora_do_ar(monkeypatch):
    """A-02. O status 401 não chega na exceção do SDK — só o hook o mede. Sem
    essa medição, credencial recusada PELO SERVIÇO era registrada como
    "serviço fora do ar", e foi isso que travou o diagnóstico da falha de
    produção."""
    sessao = _SessaoQueRecusa(recusas=99)
    http = _liga_sessao_com_token_real(monkeypatch, sessao)

    with pytest.raises(mcp_client.McpNaoAutorizado) as exc:
        asyncio.run(mcp_client.call_tool("get_option_chain", {"ticker": "PETR4"}))
    assert "401" in str(exc.value)
    # A-05: UMA renovação, não um laço — o contrato é explícito ("nenhuma
    # repetição transforma 401 em 200"). 2 POSTs = emissão inicial + 1 renovação.
    assert len(http.posts) == 2, f"renovou {len(http.posts) - 1}x, não 1x"
    assert len(sessao.chamadas) == 2, "tentou o serviço mais de duas vezes"


def test_recusa_pontual_renova_o_token_uma_vez_e_a_chamada_chega_ao_chamador(monkeypatch):
    """A-05. `_TOKEN` só era limpo por `reset_cache()`, que nada chama em
    runtime: um token recusado ficava em memória até o `exp` e uma recusa
    pontual virava falha permanente por até ~55 min."""
    sessao = _SessaoQueRecusa(recusas=1, resultado=_Resposta({"matched": 7}))
    http = _liga_sessao_com_token_real(monkeypatch, sessao)

    r = asyncio.run(mcp_client.call_tool("get_option_chain", {"ticker": "PETR4"}))

    assert r.dados == {"matched": 7} and r.cache is False
    assert len(http.posts) == 2, "não renovou o token depois da recusa"
    assert len(sessao.chamadas) == 2
    assert mcp_client._TOKEN.get("access_token") == TOKEN_DE_TESTE


def test_internal_error_sem_status_medido_nao_afirma_recusa_de_credencial(monkeypatch):
    """Contra-guardião do A-02: `INTERNAL_ERROR` é no que o transporte
    colapsa 401, 403, 500 E 502. Classificar todos como "credencial recusada"
    pelo texto da mensagem (que é constante) repetiria o erro do A-01 em outro
    lugar. Sem status medido, é indisponibilidade — e o texto do serviço vai
    junto para quem depura."""
    from mcp.shared.exceptions import MCPError
    from mcp.types import INTERNAL_ERROR

    _liga_sessao(monkeypatch, _SessaoFalsa(
        erro=MCPError(code=INTERNAL_ERROR,
                      message="Server returned an error response")))

    with pytest.raises(mcp_client.McpIndisponivel) as exc:
        asyncio.run(mcp_client.call_tool("get_option_chain", {"ticker": "PETR4"}))
    assert "Server returned an error response" in str(exc.value)
    assert "status=None" in str(exc.value), (
        "status não medido tem de aparecer como None — status chutado é o "
        "defeito que o A-01 e o A-02 têm em comum")


def test_hook_de_status_ignora_2xx_e_nao_escreve_fora_da_chamada():
    """O hook só anota não-2xx, e nunca escreve quando não há chamada em
    curso (`ContextVar` sem valor) — um hook que estoura derrubaria a
    requisição que ele só deveria observar."""
    asyncio.run(mcp_client._anotar_status_http(_RespHttp(200)))  # sem contexto
    balde: list = []
    marca = mcp_client._STATUS_HTTP.set(balde)
    try:
        asyncio.run(mcp_client._anotar_status_http(_RespHttp(200)))
        asyncio.run(mcp_client._anotar_status_http(_RespHttp(204)))
        assert balde == []
        asyncio.run(mcp_client._anotar_status_http(_RespHttp(503)))
        asyncio.run(mcp_client._anotar_status_http(object()))  # sem status_code
        assert balde == [503]
    finally:
        mcp_client._STATUS_HTTP.reset(marca)


# ------------------------------------------------- 3. sem credencial ------
def test_sem_credencial_e_nao_configurado_e_nao_toca_a_rede(monkeypatch):
    monkeypatch.delenv("MCP_CLIENT_ID", raising=False)
    monkeypatch.delenv("MCP_CLIENT_SECRET", raising=False)

    construiu = []

    def _nao_deveria():
        construiu.append(True)
        raise AssertionError("cliente HTTP construído sem credencial no ambiente")

    monkeypatch.setattr(mcp_client, "_cliente_http", _nao_deveria)

    assert mcp_client.configurado() is False
    with pytest.raises(mcp_client.McpNaoConfigurado):
        asyncio.run(mcp_client._access_token())
    assert construiu == []


# ------------------------------------------------------ 4. token/relógio ---
def _prepara_token(monkeypatch, agora, exp_em, payload=None, status=200):
    monkeypatch.setenv("MCP_CLIENT_ID", "boris")
    monkeypatch.setenv("MCP_CLIENT_SECRET", SEGREDO_DE_TESTE)
    monkeypatch.setattr(mcp_client, "_relogio", lambda: agora)
    http = _HttpFalso(_RespHttp(status, payload if payload is not None else
                                {"access_token": "token-novo", "expires_in": 3600}))
    monkeypatch.setattr(mcp_client, "_cliente_http", lambda: http)
    mcp_client._TOKEN.clear()
    if exp_em is not None:
        mcp_client._TOKEN.update({"access_token": "token-antigo", "exp": agora + exp_em})
    return http


def test_token_e_reusado_quando_falta_mais_que_a_margem(monkeypatch):
    # 10 min para o `exp`, margem de 5 min => reusa.
    http = _prepara_token(monkeypatch, agora=1_000_000.0, exp_em=600)
    assert asyncio.run(mcp_client._access_token()) == "token-antigo"
    assert http.posts == [], "pediu token novo com 10 min de validade restante"


def test_token_e_renovado_quando_falta_menos_que_a_margem(monkeypatch):
    # 4 min para o `exp`, margem de 5 min => renova ANTES de tomar 401.
    http = _prepara_token(monkeypatch, agora=1_000_000.0, exp_em=240)
    assert asyncio.run(mcp_client._access_token()) == "token-novo"
    assert len(http.posts) == 1
    corpo = http.posts[0]["data"]
    assert corpo["grant_type"] == "client_credentials"
    # `resource` (RFC 8707) é obrigatório e vira o `aud` — sem ele o emissor
    # responde `invalid_target`.
    assert corpo["resource"] == mcp_client.URL_CONTRATO
    assert http.headers["Authorization"].endswith("token-novo")
    assert mcp_client._TOKEN["exp"] == 1_000_000.0 + 3600


def test_token_sem_expires_in_legivel_nao_assume_uma_hora(monkeypatch):
    http = _prepara_token(monkeypatch, agora=1_000_000.0, exp_em=None,
                          payload={"access_token": "token-novo"})
    assert asyncio.run(mcp_client._access_token()) == "token-novo"
    assert len(http.posts) == 1
    # margem + 1s: a próxima chamada renova, em vez de fingir 1 h de validade
    assert mcp_client._TOKEN["exp"] == 1_000_000.0 + mcp_client.MARGEM_RENOVACAO_S + 1


# ------------------------------------------------------------- 5. cache ---
def test_segunda_chamada_igual_nao_toca_a_sessao_e_volta_com_cache_true(monkeypatch):
    sessao = _liga_sessao(monkeypatch, _SessaoFalsa(
        _Resposta({"trading_date": "2026-09-08", "matched": 12})))

    primeira = asyncio.run(mcp_client.call_tool("get_option_chain", {"ticker": "PETR4"}))
    segunda = asyncio.run(mcp_client.call_tool("get_option_chain", {"ticker": "PETR4"}))

    assert primeira.cache is False and segunda.cache is True
    assert segunda.dados == {"trading_date": "2026-09-08", "matched": 12}
    assert len(sessao.chamadas) == 1, "cache não segurou a 2ª chamada idêntica"

    # argumento diferente é OUTRA chave — o cache não pode colapsar tickers
    asyncio.run(mcp_client.call_tool("get_option_chain", {"ticker": "VALE3"}))
    assert len(sessao.chamadas) == 2


def test_ttl_zerado_por_env_torta_cai_no_default_em_vez_de_desligar_o_cache(monkeypatch):
    monkeypatch.setenv("B3_MCP_CACHE_S", "banana")
    assert mcp_client._ttl_default() == mcp_client.TTL_DEFAULT_S
    monkeypatch.setenv("B3_MCP_CACHE_S", "0")
    assert mcp_client._ttl_default() == mcp_client.TTL_DEFAULT_S


def test_frescor_tem_ttl_proprio_menor_que_o_default(monkeypatch):
    """`check_data_freshness` decide se a tela pode operar; servir "em dia"
    velho é exatamente o erro que a Decisão 8 do ADR-027 existe para impedir."""
    sessao = _liga_sessao(monkeypatch, _SessaoFalsa(_Resposta({"classes": []})))
    asyncio.run(mcp_client.call_tool("check_data_freshness", {}))

    # relógio monotônico à frente do TTL do frescor, mas dentro do default
    base = mcp_client._mono()
    monkeypatch.setattr(mcp_client, "_mono",
                        lambda: base + mcp_client.TTL_FRESCOR_S + 1)
    asyncio.run(mcp_client.call_tool("check_data_freshness", {}))
    assert len(sessao.chamadas) == 2, "frescor foi servido do cache além do TTL próprio"


# --------------------------------------------------------------- 6. URL ---
def test_url_default_e_a_do_contrato(monkeypatch):
    monkeypatch.delenv("MCP_URL", raising=False)
    assert mcp_client.url() == mcp_client.URL_CONTRATO


def test_url_com_esquema_diferente_de_https_levanta_value_error(monkeypatch):
    for torta in ("http://mcp.exemplo.invalido/mcp",
                  "ftp://mcp.exemplo.invalido/mcp",
                  "http://localhost:8000/mcp"):
        monkeypatch.setenv("MCP_URL", torta)
        with pytest.raises(ValueError):
            mcp_client.url()


# ------------------------------------------------------------ 7. segredo ---
def test_nenhuma_mensagem_de_erro_ecoa_o_segredo_nem_o_token(monkeypatch):
    """T-waw-01. Três caminhos de falha, um assert só: nem o segredo do
    ambiente nem o access token podem aparecer no texto que vai para o log."""
    monkeypatch.setenv("MCP_CLIENT_ID", "boris")
    monkeypatch.setenv("MCP_CLIENT_SECRET", SEGREDO_DE_TESTE)
    monkeypatch.setattr(mcp_client, "_relogio", lambda: 1_000_000.0)

    # (a) emissor recusa a credencial
    http_401 = _HttpFalso(_RespHttp(401, {"error": "invalid_client",
                                          "segredo_ecoado": SEGREDO_DE_TESTE}))
    monkeypatch.setattr(mcp_client, "_cliente_http", lambda: http_401)
    mcp_client._TOKEN.clear()
    with pytest.raises(mcp_client.McpNaoAutorizado) as exc_a:
        asyncio.run(mcp_client._access_token())

    # (b) transporte quebra ao falar com o serviço, já com token em mãos
    class _ErroDeTransporte(Exception):
        def __repr__(self):  # o repr de um erro do stack HTTP arrasta headers
            return f"<ErroDeTransporte Authorization='Bearer {TOKEN_DE_TESTE}'>"

    _liga_sessao(monkeypatch, _SessaoFalsa(erro=_ErroDeTransporte("falhou")))
    with pytest.raises(mcp_client.McpIndisponivel) as exc_b:
        asyncio.run(mcp_client.call_tool("get_option_chain", {"ticker": "PETR4"}))

    # (c) serviço recusa a credencial (401 vindo do transporte)
    class _ErroComResposta(Exception):
        def __init__(self):
            super().__init__("401")
            self.response = _RespHttp(401)

    _liga_sessao(monkeypatch, _SessaoFalsa(erro=_ErroComResposta()))
    with pytest.raises(mcp_client.McpNaoAutorizado) as exc_c:
        asyncio.run(mcp_client.call_tool("get_option_chain", {"ticker": "PETR4"}))

    # (d) o SERVIÇO devolve um erro de protocolo cuja MENSAGEM ecoa o header
    # `Authorization` e o segredo. Caso novo de 2026-09-10: desde o A-02 a
    # mensagem do serviço viaja para a exceção e para o log, e ela é entrada
    # externa — quem escolhe o texto é o outro lado. `_trecho()` redige.
    from mcp.shared.exceptions import MCPError

    mcp_client._TOKEN.update({"access_token": TOKEN_DE_TESTE,
                              "exp": 1_000_000.0 + 3600})
    _liga_sessao(monkeypatch, _SessaoFalsa(erro=MCPError(
        code=-32603,
        message=(f"upstream rejected Authorization: Bearer {TOKEN_DE_TESTE} "
                 f"(client_secret={SEGREDO_DE_TESTE})"))))
    with pytest.raises(mcp_client.McpIndisponivel) as exc_d:
        asyncio.run(mcp_client.call_tool("get_option_chain", {"ticker": "PETR4"}))
    assert "[redigido]" in str(exc_d.value), (
        "a mensagem do serviço entrou crua — um serviço mal-comportado "
        "escreveria o nosso access token no nosso log")

    for rotulo, exc in (("emissor 401", exc_a), ("transporte", exc_b),
                        ("serviço 401", exc_c), ("mensagem do serviço", exc_d)):
        texto = str(exc.value)
        assert SEGREDO_DE_TESTE not in texto, f"{rotulo}: mensagem ecoa MCP_CLIENT_SECRET"
        assert TOKEN_DE_TESTE not in texto, f"{rotulo}: mensagem ecoa o access token"


def test_indisponivel_do_transporte_usa_so_o_nome_da_classe(monkeypatch):
    """Diferença deliberada em relação a `mydata_client._fetch_json`, que usa
    `{e!r}`: aqui o repr pode arrastar o header `Authorization`."""
    class _ConnectTimeout(Exception):
        def __repr__(self):
            return "<ConnectTimeout headers={'Authorization': 'Bearer XYZ'}>"

    _liga_sessao(monkeypatch, _SessaoFalsa(erro=_ConnectTimeout("estourou")))
    with pytest.raises(mcp_client.McpIndisponivel) as exc:
        asyncio.run(mcp_client.call_tool("get_option_chain", {"ticker": "PETR4"}))
    assert "_ConnectTimeout" in str(exc.value)
    assert "Authorization" not in str(exc.value)


# ------------------------------------------------- estáticos (de graça) ---
def test_get_prompt_e_read_resource_cacheiam_e_devolvem_o_objeto_do_sdk(monkeypatch):
    marcador = object()
    sessao = _liga_sessao(monkeypatch, _SessaoFalsa(marcador))

    p1 = asyncio.run(mcp_client.get_prompt("veredito", {"ticker": "PETR4", "lote": 100}))
    p2 = asyncio.run(mcp_client.get_prompt("veredito", {"ticker": "PETR4", "lote": 100}))
    assert p1.dados is marcador and p1.cache is False and p2.cache is True

    r1 = asyncio.run(mcp_client.read_resource("mydata://glossario"))
    r2 = asyncio.run(mcp_client.read_resource("mydata://glossario"))
    assert r1.dados is marcador and r1.cache is False and r2.cache is True

    # 2 chamadas de rede no total (1 prompt + 1 resource), o resto foi cache
    assert len(sessao.chamadas) == 2
    # o SDK exige `arguments: dict[str, str]` — o int virou str aqui, não no
    # chamador
    assert sessao.chamadas[0][2] == {"ticker": "PETR4", "lote": "100"}


def test_list_tools_cacheia_por_uma_hora_e_devolve_o_objeto_do_sdk(monkeypatch):
    """F5: `tools/list` é PROTOCOLO (não `tools/call`), então é de graça no
    teto do serviço — e é a fonte do `inputSchema` de `create_setup` que o
    compilador usa em runtime, em vez de uma cópia da DSL dentro do Boris
    (ENG-06)."""
    marcador = object()
    sessao = _liga_sessao(monkeypatch, _SessaoFalsa(marcador))

    t1 = asyncio.run(mcp_client.list_tools())
    t2 = asyncio.run(mcp_client.list_tools())

    assert t1.dados is marcador and t1.cache is False and t2.cache is True
    assert len(sessao.chamadas) == 1, "cache não segurou a 2ª chamada de tools/list"
    assert sessao.chamadas[0] == ("tools/list",)

    # TTL de estático (1 h), não o default de tool: passado o default, ainda
    # é cache — o catálogo de tools não muda por pregão.
    base = mcp_client._mono()
    monkeypatch.setattr(mcp_client, "_mono",
                        lambda: base + mcp_client.TTL_DEFAULT_S + 1)
    assert asyncio.run(mcp_client.list_tools()).cache is True
    monkeypatch.setattr(mcp_client, "_mono",
                        lambda: base + mcp_client.TTL_ESTATICO_S + 1)
    assert asyncio.run(mcp_client.list_tools()).cache is False


def test_reset_cache_limpa_tambem_o_token(monkeypatch):
    """O token É cache: depois de trocar a credencial em runtime, deixá-lo
    para trás faria o processo seguir com a credencial antiga até o `exp`."""
    mcp_client._TOKEN.update({"access_token": "x", "exp": 1.0})
    mcp_client._CACHE[("t", "{}")] = (0.0, {"a": 1})
    mcp_client.reset_cache()
    assert mcp_client._TOKEN == {} and mcp_client._CACHE == {}
