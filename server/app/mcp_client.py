"""Fronteira ÚNICA do serviço MCP autenticado (`mcp.semente.dev`) — ADR-027,
Decisão 1. Espelha a forma de `mydata_client.py` (URL validada, timeout
explícito, nunca eco de segredo) com as diferenças que o SDK do MCP impõe.

O que este módulo É: o único lugar de `server/app/` que importa `mcp` e
`httpx2`; quem pede o token ao emissor, quem abre a sessão MCP, quem traduz
falha do serviço em exceção de domínio e quem guarda o cache L1 de resposta.
O guardião `test_guardiao_b_um_unico_modulo_importa_mcp_e_httpx2`
(`test_opcoes_fronteira.py`) prova a exclusividade por igualdade de conjunto.

O que este módulo NÃO faz: nenhuma rota HTTP, nenhum cap de usuário, nenhum
texto voltado ao usuário final. Isso é `options_mcp_api.py`. As mensagens das
exceções aqui são para LOG e para quem depura — quem fala com o usuário é a
rota, que reescreve tudo sem número interno e sem nome de variável de
ambiente sensível.

**Por que o token é pedido à mão**, em vez de usar o
`ClientCredentialsOAuthProvider` que o contrato mostra primeiro: o
`async_auth_flow` do provider segura um lock DURANTE O ROUND-TRIP INTEIRO, o
que serializaria todas as chamadas MCP do processo — um usuário esperando a
resposta do serviço bloquearia todos os outros. O próprio contrato documenta
o caminho alternativo ("peça o token você mesmo... e renove quando faltar
uns cinco minutos para o `exp`"), e é o que está implementado aqui: lock só
na RENOVAÇÃO, com double-check, e um semáforo separado limitando a
concorrência de chamadas.
"""
from __future__ import annotations

import asyncio
import base64
import contextvars
import json
import os
import time
from typing import Any, NamedTuple
from urllib.parse import urlsplit

from . import obslog

# Endereços do contrato (`~/dev/MCP/docs/contrato-mcp-servico.md`, seção
# "Endereços"). São os DOIS únicos literais de endereço permitidos neste
# arquivo — o guardião (ii) de `test_mcp_guardioes.py` reprova qualquer
# outro. `MCP_URL` pode apontar para outro lugar, mas só por env e só sob TLS.
URL_CONTRATO = "https://mcp.semente.dev/mcp"
URL_TOKEN = "https://id.semente.dev/token"

TIMEOUT_S = 30.0
# Semáforo, não pool: o teto do serviço é diário e compartilhado por toda a
# base do Boris; 4 chamadas simultâneas é o que a rota `/possibilidades`
# (2×N+1 tools) precisa para não serializar, sem virar um martelo.
CONCORRENCIA = 4
# O token vale 1 h e não há refresh. Renovar 5 min antes do `exp` é o que o
# contrato pede: quem só renova ao tomar 401 perde uma chamada a cada virada.
MARGEM_RENOVACAO_S = 300
TTL_DEFAULT_S = 900
# Frescor tem TTL menor que o resto de propósito: é o dado que decide se a
# tela pode operar (ADR-027, Decisão 8), e servir "em dia" velho seria
# exatamente o erro que a decisão existe para impedir.
TTL_FRESCOR_S = 600
# Prompt e resource são texto de protocolo, não mudam por pregão, e são de
# graça no teto do serviço — 1 h de cache é conservador.
TTL_ESTATICO_S = 3600
# Erro JSON-RPC de teto diário. Chega como HTTP 200 com erro no corpo (não
# como 429) — decisão deliberada do serviço, documentada no contrato.
#
# **COLISÃO DE NÚMERO** (achado A-01 da auditoria de 2026-09-10): este é o
# MESMO valor que o `CONNECTION_CLOSED` do SDK (`mcp_types`, mcp 2.2.0). Ou
# seja: o código, sozinho, NÃO distingue "você gastou suas 2.000 chamadas" de
# "a conexão caiu". Até esta data uma conexão caída virava HTTP 402 "atingiu o
# teto de chamadas do dia" — um número de consumo que ninguém mediu, contra o
# princípio 4 do CLAUDE.md, e mandando o usuário esperar até a meia-noite sem
# motivo. Quem decide agora é `_prova_de_teto()`, não o número.
CODIGO_TETO = -32000
# Tamanho máximo do texto do serviço que entra na mensagem de exceção/log.
# A mensagem é de PROTOCOLO (vem do serviço ou é constante do SDK), mas ela é
# entrada externa: limitar o trecho é o que impede uma resposta patológica de
# inundar o ring buffer do obslog.
MAX_TRECHO = 200


# --------------------------------------------------------------------------
# Exceções de domínio. Quem chama decide como degradar; nenhuma delas carrega
# segredo, corpo de resposta do emissor, nem header.
# --------------------------------------------------------------------------
class McpErro(RuntimeError):
    """Base de tudo que este módulo levanta por conta do serviço."""


class McpNaoConfigurado(McpErro):
    """Falta credencial no ambiente (ou o SDK não está instalado). Não tocou
    a rede — é estado de configuração, não falha do serviço."""


class McpNaoAutorizado(McpErro):
    """O emissor ou o serviço recusou a credencial."""


class McpIndisponivel(McpErro):
    """Falha transitória: timeout, 5xx, transporte, erro de protocolo."""


class McpTetoAtingido(McpErro):
    """Teto diário de chamadas do serviço (JSON-RPC -32000). `data` traz
    `cliente`/`escopo`/`chamadas_hoje`/`teto`/`reinicia` como o serviço
    mandou — a rota repassa `reinicia` e `escopo` ao usuário."""

    def __init__(self, msg: str, data: dict | None = None) -> None:
        super().__init__(msg)
        self.data = dict(data or {})


class McpErroDeTool(McpErro):
    """A requisição deu certo e a TOOL disse não (ticker sem cadeia,
    vencimento inexistente). É erro do pedido, não do serviço: repetir o
    mesmo pedido não muda o resultado."""

    def __init__(self, msg: str, available=None, hint=None) -> None:
        super().__init__(msg)
        self.available = available
        self.hint = hint


# --------------------------------------------------------------------------
# Configuração — tudo lido do ambiente A CADA chamada (nunca congelado no
# import), para o Railway poder mudar env sem redeploy do código e para o
# teste poder usar `monkeypatch.setenv`.
# --------------------------------------------------------------------------
def _client_id() -> str:
    return (os.environ.get("MCP_CLIENT_ID") or "").strip()


def _client_secret() -> str:
    return (os.environ.get("MCP_CLIENT_SECRET") or "").strip()


def configurado() -> bool:
    return bool(_client_id() and _client_secret())


def url() -> str:
    """Lê `MCP_URL` (default: o endereço do contrato). VALIDA o esquema: só
    TLS. Mesma justificativa de `mydata_client.base_url` — esta função é o
    ÚNICO ponto que decide para onde o access token viaja, e `MCP_URL` é
    entrada de operador (mitigação de T-waw-02)."""
    raw = (os.environ.get("MCP_URL") or "").strip().rstrip("/")
    if not raw:
        return URL_CONTRATO
    parsed = urlsplit(raw)
    if parsed.scheme != "https":
        raise ValueError(
            f"MCP_URL com esquema {parsed.scheme!r} não permitido — o access "
            f"token do serviço de opções só trafega por TLS (esquema https). "
            f"Não há exceção para localhost aqui: o token é emitido para a "
            f"audiência do serviço remoto e não serve a nada local."
        )
    return raw


def _ttl_default() -> int:
    """`B3_MCP_CACHE_S`, lido a cada chamada. Valor torto (não numérico, zero
    ou negativo) cai no default em vez de desligar o cache — cache desligado
    por env inválida queimaria o teto do serviço em silêncio."""
    try:
        v = int(os.environ.get("B3_MCP_CACHE_S") or TTL_DEFAULT_S)
    except (TypeError, ValueError):
        return TTL_DEFAULT_S
    return v if v > 0 else TTL_DEFAULT_S


# --------------------------------------------------------------------------
# Relógios injetáveis. TODO uso de tempo neste módulo passa por uma destas
# duas funções, nunca por `time.*` direto no corpo — é o que permite ao teste
# fixar o relógio com `monkeypatch.setattr` sem `freezegun`.
# --------------------------------------------------------------------------
def _relogio() -> float:
    """Relógio de PAREDE — expiração do token (`exp` é epoch absoluto)."""
    return time.time()


def _mono() -> float:
    """Relógio MONOTÔNICO — idade das entradas do cache L1. Separado do de
    parede de propósito: ajuste de NTP não pode ressuscitar nem envelhecer
    cache."""
    return time.monotonic()


# --------------------------------------------------------------------------
# Cliente HTTP compartilhado. `httpx2` e o SDK entram por import TARDIO, de
# dentro das funções: `main.py` importa este módulo na cadeia de boot, e um
# SDK ausente/quebrado no ambiente derrubaria o APP INTEIRO em vez de só a
# aba Opções. Isto NÃO fura o guardião B — o `_imports()` dele usa
# `ast.walk`, que visita o corpo das funções (a própria docstring do helper
# diz isso).
# --------------------------------------------------------------------------
_HTTP = None
_TOKEN: dict = {}
_LOCK = asyncio.Lock()
_SEM = asyncio.Semaphore(CONCORRENCIA)

# Status HTTP não-2xx MEDIDO no cliente compartilhado (achado A-02).
#
# Por que isto existe: o transporte streamable-http do SDK **apaga o status**.
# Qualquer não-2xx que não seja 404 vira um único
# `ErrorData(code=INTERNAL_ERROR, message="Server returned an error response")`
# (mcp 2.2.0, `mcp/client/streamable_http.py:383-411`, verificado). Então 401
# (credencial recusada PELO SERVIÇO), 403, 500 e 502 chegam aqui idênticos, e
# o ramo `except Exception: e.response.status_code` nunca dispara neste
# transporte — era código morto, e por isso "credencial recusada" aparecia no
# log como "serviço fora do ar".
#
# Por que NÃO foi resolvido pelo texto da mensagem, como a auditoria sugeriu:
# a mensagem do SDK é uma CONSTANTE para todos esses casos. Ler texto não
# recupera informação que o texto não tem; classificar 502 como "credencial
# recusada" seria cometer o mesmo erro do A-01 em outro lugar. O que dá para
# fazer é MEDIR: o cliente HTTP é nosso, então um event hook anota o status
# antes de o SDK traduzir. Status não medido fica `None` e a classificação
# cai em "indisponível" — nunca num status chutado.
#
# ContextVar (e não variável de módulo) porque são até `CONCORRENCIA` chamadas
# simultâneas: um slot global seria lido por uma corrotina e escrito por
# outra, o mesmo racy que a docstring de `ResultadoTool` descreve. A lista é
# criada por `_chamar` ANTES de abrir a sessão, então as tasks-filhas do
# task group do SDK herdam a MESMA lista (contexto é copiado na criação da
# task) e escrevem no lugar certo.
_STATUS_HTTP: contextvars.ContextVar = contextvars.ContextVar("mcp_status_http", default=None)


async def _anotar_status_http(resposta) -> None:
    """Event hook de resposta do `httpx2`. Roda com os headers já recebidos e
    ANTES de o corpo ser lido (verificado contra um servidor local, inclusive
    em resposta streaming, que é o modo do transporte). Nunca levanta: hook
    que estoura derruba a requisição que ele só deveria observar."""
    try:
        alvo = _STATUS_HTTP.get()
        if alvo is None:
            return
        status = getattr(resposta, "status_code", None)
        if isinstance(status, int) and status >= 400:
            alvo.append(status)
    except Exception:  # noqa: BLE001 — observação não pode quebrar o fluxo
        return


def _cliente_http():
    """Um único `AsyncClient` por processo. O header `Authorization` é
    escrito NELE na renovação do token (e não por requisição) porque o token
    é de MÁQUINA: é o mesmo para todo o processo, independente de qual
    usuário do Boris disparou a chamada."""
    global _HTTP
    if _HTTP is None:
        try:
            import httpx2
        except ImportError:
            raise McpNaoConfigurado(
                "SDK do serviço de opções não instalado neste ambiente."
            ) from None
        _HTTP = httpx2.AsyncClient(
            timeout=TIMEOUT_S,
            event_hooks={"response": [_anotar_status_http]},
        )
    return _HTTP


async def _access_token() -> str:
    """Token `client_credentials` do emissor, em memória, renovado
    `MARGEM_RENOVACAO_S` antes do `exp`."""
    tok = _TOKEN.get("access_token")
    exp = _TOKEN.get("exp")
    if tok and isinstance(exp, (int, float)) and (exp - MARGEM_RENOVACAO_S) > _relogio():
        return tok

    async with _LOCK:
        # Double-check DENTRO do lock: sem isto, N corrotinas que chegaram
        # juntas na virada pedem N tokens ao emissor, cada uma invalidando o
        # header que a anterior acabou de escrever.
        tok = _TOKEN.get("access_token")
        exp = _TOKEN.get("exp")
        if tok and isinstance(exp, (int, float)) and (exp - MARGEM_RENOVACAO_S) > _relogio():
            return tok

        cid, seg = _client_id(), _client_secret()
        if not cid or not seg:
            raise McpNaoConfigurado("Serviço de opções não configurado no servidor.")

        http = _cliente_http()
        basico = base64.b64encode(f"{cid}:{seg}".encode()).decode()
        # FORA do try, de propósito: `url()` levanta ValueError quando
        # `MCP_URL` tem esquema inválido, e isso é ERRO DE CONFIGURAÇÃO, não
        # indisponibilidade. Avaliado como argumento dentro do try, ele seria
        # capturado pelo `except Exception` abaixo e a rota diria "o serviço
        # não respondeu" para um problema que nenhum retry resolve.
        recurso = url()
        try:
            r = await http.post(
                URL_TOKEN,
                headers={
                    "Authorization": "Basic " + basico,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                # `resource` (RFC 8707) é OBRIGATÓRIO e vira o `aud` do token
                # — é ele que impede um token emitido para outro serviço do
                # portfólio de abrir este (mitigação de T-waw-06).
                data={"grant_type": "client_credentials", "resource": recurso},
            )
        except McpErro:
            raise
        except Exception as e:  # noqa: BLE001 — transporte
            raise McpIndisponivel(
                f"emissor de credencial inacessível: {type(e).__name__}"
            ) from None

        status = getattr(r, "status_code", None)
        if status in (400, 401, 403):
            # SEM corpo da resposta na mensagem: o emissor não distingue as
            # causas de propósito, e ecoar o corpo só arriscaria arrastar
            # credencial para o log (T-waw-01).
            raise McpNaoAutorizado(
                "o emissor recusou a credencial do serviço de opções "
                "(confira MCP_CLIENT_ID/MCP_CLIENT_SECRET e o registro do "
                "client)."
            )
        if not isinstance(status, int) or not (200 <= status < 300):
            # Inclui 5xx e qualquer 3xx: um redirect na rota de token é
            # anomalia de configuração, não um caminho a seguir com o segredo
            # em mãos.
            raise McpIndisponivel(
                f"emissor de credencial respondeu status inesperado: {status}"
            )

        try:
            corpo = r.json()
        except Exception:  # noqa: BLE001 — corpo não-JSON
            raise McpIndisponivel(
                "emissor de credencial respondeu num formato inesperado."
            ) from None

        at = (corpo or {}).get("access_token")
        if not at:
            raise McpIndisponivel(
                "emissor de credencial não devolveu access_token."
            )
        try:
            validade = int((corpo or {}).get("expires_in") or 0)
        except (TypeError, ValueError):
            validade = 0
        # Sem `expires_in` legível, trata como já vencido além da margem: a
        # próxima chamada renova. Nunca assume 1 h por conta própria.
        _TOKEN["access_token"] = at
        _TOKEN["exp"] = _relogio() + max(validade, MARGEM_RENOVACAO_S + 1)
        http.headers["Authorization"] = "Bearer " + at
        return at


# --------------------------------------------------------------------------
# Núcleo de chamada.
# --------------------------------------------------------------------------
def _trecho(texto) -> str:
    """Texto de protocolo pronto para log: uma linha, sem segredo, e limitado.

    A mensagem do erro JSON-RPC passou a viajar para o log e para a exceção
    (achado A-02), e ela é ENTRADA EXTERNA: quem escolhe o texto é o outro
    lado. Um serviço mal-comportado que ecoasse o header `Authorization` na
    mensagem arrastaria o access token para dentro do nosso log (T-waw-01).
    Redigir aqui faz a propriedade "nenhuma mensagem ecoa segredo" valer POR
    CONSTRUÇÃO, e não por confiança no outro lado. A redação vem ANTES do
    corte: cortar primeiro deixaria um pedaço do segredo sobrevivendo.
    """
    s = " ".join(str(texto or "").split())
    for segredo in (_TOKEN.get("access_token"), _client_secret()):
        segredo = str(segredo or "")
        # Piso de tamanho para não transformar um valor curto/torto de env num
        # `replace` que picaria o texto inteiro.
        if len(segredo) >= 8:
            s = s.replace(segredo, "[redigido]")
    return s if len(s) <= MAX_TRECHO else s[:MAX_TRECHO] + "…"


def _numero(v):
    """`None` quando não é número de verdade. `bool` é rejeitado de propósito:
    `True` é `int` em Python e passaria como 'medição'."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return v


def _prova_de_teto(dados) -> bool:
    """Decide se um `-32000` é teto diário DE VERDADE (achado A-01).

    O critério é a PROVA NUMÉRICA, nunca o código: o serviço sempre manda
    `data` com `cliente`/`escopo`/`chamadas_hoje`/`teto`/`reinicia` (contrato
    do MCP, seção "Erro JSON-RPC -32000"), enquanto o `CONNECTION_CLOSED` do
    SDK — o mesmo -32000 — vem sem `data`. Sem os dois números, "você atingiu
    o teto" é afirmação sem medição.

    Falso-negativo é o lado seguro do erro: um teto real sem os números viraria
    503 "não respondeu agora" (que convida a tentar mais tarde) em vez de 402
    com uma contagem inventada.
    """
    if not isinstance(dados, dict):
        return False
    return (_numero(dados.get("chamadas_hoje")) is not None
            and _numero(dados.get("teto")) is not None)


async def _recusa_do_servico(rotulo: str, executar, status, motivo: str, renovou: bool):
    """Credencial recusada PELO SERVIÇO (achado A-05). Invalida o token e
    tenta UMA renovação — uma só.

    Por que invalidar: `_TOKEN` só era limpo por `reset_cache()`, que nada
    chama em runtime. Um token recusado ficava em memória até o `exp`, então
    uma recusa pontual (virada de chave no serviço, allowlist atualizada)
    virava falha permanente por até ~55 min.

    Por que UMA: o contrato é explícito — "não fique tentando em laço: nenhuma
    repetição transforma 401 em 200". A renovação existe para o caso em que o
    token em mãos é que estava velho/errado; se o novo também é recusado, a
    causa é configuração (audiência, allowlist) e repetir só queima chamada.
    """
    _TOKEN.clear()
    if not renovou:
        obslog.log("mcp", "credencial recusada pelo serviço; renovando o token UMA vez",
                   level="warn", rotulo=rotulo, status=status, motivo=_trecho(motivo))
        return await _chamar(rotulo, executar, _renovou=True)
    obslog.log("mcp", "credencial recusada pelo serviço mesmo após renovar", level="error",
               rotulo=rotulo, status=status, motivo=_trecho(motivo))
    raise McpNaoAutorizado(
        f"o serviço de opções recusou a credencial mesmo depois de renovar o "
        f"token (status={status}; audiência errada, ou client fora da lista "
        f"do serviço): {_trecho(motivo)}"
    ) from None


async def _chamar(rotulo: str, executar, *, _renovou: bool = False):
    """Abre a sessão MCP e roda `executar(sessao)`, traduzindo TODA falha em
    exceção de domínio. `rotulo` só entra em log/telemetria. `_renovou` é
    interno: marca a segunda e ÚLTIMA tentativa depois de o serviço recusar a
    credencial (ver `_recusa_do_servico`)."""
    await _access_token()          # escreve o header no cliente compartilhado
    http = _cliente_http()
    u = url()                      # FORA do try: env torta é ValueError, não
                                   # indisponibilidade (comportamento 6)

    try:
        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client
        from mcp.shared.exceptions import MCPError
        # Importados, e não cravados como número: `CONNECTION_CLOSED` é o
        # mesmo -32000 do teto do contrato, e `INTERNAL_ERROR` é no que o
        # transporte colapsa todo não-2xx. Se o SDK renomear ou mover
        # qualquer um dos dois, isto quebra ALTO no import em vez de
        # classificar errado em silêncio (achado A-01).
        from mcp.types import CONNECTION_CLOSED, INTERNAL_ERROR
    except ImportError:
        raise McpNaoConfigurado(
            "SDK do serviço de opções não instalado neste ambiente."
        ) from None

    # Lista criada AQUI, antes de qualquer task-filha existir: é o que faz o
    # hook de status escrever no balde desta chamada e não no de outra.
    medido: list = []
    marca = _STATUS_HTTP.set(medido)
    try:
        async with _SEM:
            # Tupla de DOIS (leitura, escrita) — versões antigas do SDK
            # devolviam três, e desempacotar em três quebra (contrato,
            # "Três armadilhas do SDK").
            async with streamable_http_client(u, http_client=http) as (leitura, escrita):
                async with ClientSession(leitura, escrita) as sessao:
                    await sessao.initialize()
                    return await executar(sessao)
    except McpErro:
        raise
    except MCPError as e:
        erro = getattr(e, "error", None)
        codigo = getattr(erro, "code", None)
        mensagem = getattr(erro, "message", None) or str(e)
        dados = getattr(erro, "data", None) or {}
        dados = dados if isinstance(dados, dict) else {}
        status = medido[-1] if medido else None

        # ORDEM IMPORTA: teto-com-prova primeiro, porque `CODIGO_TETO` e
        # `CONNECTION_CLOSED` são o mesmo número e só a prova separa os dois.
        if codigo == CODIGO_TETO and _prova_de_teto(dados):
            obslog.log(
                "mcp", "teto do serviço atingido", level="error",
                rotulo=rotulo, escopo=dados.get("escopo"),
                chamadas_hoje=dados.get("chamadas_hoje"), teto=dados.get("teto"),
            )
            raise McpTetoAtingido(_trecho(mensagem), dados) from None

        if status in (401, 403):
            return await _recusa_do_servico(rotulo, executar, status, mensagem, _renovou)

        if codigo == CONNECTION_CLOSED:
            causa = ("conexão fechada (CONNECTION_CLOSED — o MESMO -32000 do "
                     "teto, mas sem `chamadas_hoje`/`teto` em `data`, então "
                     "NÃO é teto)")
        elif codigo == INTERNAL_ERROR:
            causa = ("o serviço devolveu resposta de erro HTTP; o transporte "
                     "do SDK não preserva o status")
        else:
            causa = "erro de protocolo"
        # O log ganha o MOTIVO (achado A-02): antes só o `code=` sobrevivia, e
        # o diagnóstico da falha de produção travou justamente nisso.
        obslog.log("mcp", "serviço de opções falhou", level="warn", rotulo=rotulo,
                   code=codigo, status=status, causa=causa, motivo=_trecho(mensagem))
        raise McpIndisponivel(
            f"serviço de opções devolveu erro de protocolo (code={codigo}, "
            f"status={status}): {causa}: {_trecho(mensagem)}"
        ) from None
    except Exception as e:  # noqa: BLE001 — transporte/HTTP
        # MANTIDO de propósito, apesar de o A-02 ter provado que o status não
        # chega aqui no transporte streamable-http: (i) o `.response` pode vir
        # de uma exceção levantada pelo NOSSO cliente httpx2 antes de o SDK
        # traduzir (p.ex. `raise_for_status` num redirect não seguido), e (ii)
        # o hook já pode ter medido o status mesmo quando a falha sobe como
        # exceção crua. Remover o ramo tiraria a classificação certa desses
        # dois casos para economizar três linhas — e o teste
        # `test_nenhuma_mensagem_de_erro_ecoa_o_segredo_nem_o_token` exercita
        # o caminho. O que ele NÃO faz mais é ser a ÚNICA porta: quem pega o
        # 401 deste transporte é o ramo `MCPError` acima.
        status = getattr(getattr(e, "response", None), "status_code", None)
        if status is None and medido:
            status = medido[-1]
        if status in (401, 403):
            return await _recusa_do_servico(
                rotulo, executar, status, type(e).__name__, _renovou)
        # SÓ `type(e).__name__`, nunca `{e!r}` — diferença deliberada em
        # relação a `mydata_client._fetch_json`, que usa repr: o repr de um
        # erro do stack HTTP do SDK pode arrastar headers da requisição, e o
        # header que este módulo escreve é o `Authorization` (T-waw-01).
        obslog.log("mcp", "serviço de opções inacessível", level="warn",
                   rotulo=rotulo, status=status, erro=type(e).__name__)
        raise McpIndisponivel(
            f"serviço de opções inacessível: {type(e).__name__} (status={status})"
        ) from None
    finally:
        _STATUS_HTTP.reset(marca)


# --------------------------------------------------------------------------
# Cache L1.
# --------------------------------------------------------------------------
_CACHE: dict = {}


def _chave(rotulo: str, args) -> tuple:
    return (rotulo, json.dumps(args or {}, sort_keys=True, ensure_ascii=False, default=str))


def _cache_get(chave: tuple, ttl: int):
    """`None` = miss (ou expirado). Nenhum valor cacheado por este módulo é
    `None` por construção — `call_tool` guarda um dict e os estáticos guardam
    o objeto do SDK —, então o sentinela extra seria peso morto."""
    item = _CACHE.get(chave)
    if item is None:
        return None
    at, valor = item
    if (_mono() - at) > ttl:
        _CACHE.pop(chave, None)
        return None
    return valor


def _cache_put(chave: tuple, valor) -> None:
    """Chamado SÓ no sucesso — decisão A-07 do ADR-020: cachear falha
    transforma uma indisponibilidade de 1 s numa de 15 min, e cachear erro de
    tool esconderia a correção do pedido do usuário."""
    _CACHE[chave] = (_mono(), valor)


def reset_cache() -> None:
    """Limpa o cache L1 **e o token**. O token é cache como qualquer outro:
    depois de trocar `MCP_CLIENT_ID`/`MCP_CLIENT_SECRET` em runtime, deixá-lo
    para trás faria o processo seguir usando a credencial antiga até o `exp`.
    Os testes chamam isto entre casos."""
    _CACHE.clear()
    _TOKEN.clear()


# --------------------------------------------------------------------------
# API pública.
# --------------------------------------------------------------------------
class ResultadoTool(NamedTuple):
    """`cache` diz se a chamada TOCOU a rede. Não é cosmético: é o que o cap
    por usuário usa para não cobrar por um acerto de cache. Um flag global de
    módulo ("a última chamada foi cache?") seria racy sob concorrência — duas
    corrotinas na mesma janela leriam o flag uma da outra.

    `dados` é `Any` e não `dict` porque `call_tool` devolve o
    `structured_content` (dict) enquanto `get_prompt`/`read_resource`
    devolvem o objeto do SDK — anotar `dict` seria mentira para dois dos três.
    """

    dados: Any
    cache: bool


async def call_tool(nome: str, args: dict | None = None, *,
                    read_timeout_seconds: float = TIMEOUT_S) -> ResultadoTool:
    """Chama uma tool e devolve o `structured_content`. Levanta
    `McpErroDeTool` quando a tool recusou o pedido — CHECANDO AS DUAS COISAS
    que o contrato manda checar (`is_error` E a presença da chave `error`):
    um cliente que olha só `is_error` trata mensagem de erro como dado bom."""
    args = dict(args or {})
    ttl = TTL_FRESCOR_S if nome == "check_data_freshness" else _ttl_default()
    rotulo = "tools/call:" + nome
    chave = _chave(rotulo, args)

    em_cache = _cache_get(chave, ttl)
    if em_cache is not None:
        obslog.log("mcp", f"tool {nome}", tool=nome, cache=True)
        return ResultadoTool(em_cache, True)

    t0 = _relogio()

    async def _executar(sessao):
        return await sessao.call_tool(nome, args, read_timeout_seconds=read_timeout_seconds)

    r = await _chamar(rotulo, _executar)
    sc = getattr(r, "structured_content", None) or {}
    if getattr(r, "is_error", False) or (isinstance(sc, dict) and "error" in sc):
        erro = sc.get("error") if isinstance(sc, dict) else None
        raise McpErroDeTool(
            str(erro or "a tool recusou o pedido"),
            available=sc.get("available") if isinstance(sc, dict) else None,
            hint=sc.get("hint") if isinstance(sc, dict) else None,
        )

    _cache_put(chave, sc)
    obslog.log("mcp", f"tool {nome}", tool=nome, cache=False,
               ms=int((_relogio() - t0) * 1000))
    return ResultadoTool(sc, False)


async def get_prompt(nome: str, args: dict | None = None) -> ResultadoTool:
    """`prompts/get`. NÃO conta no teto do serviço (é protocolo, como
    `initialize` e `tools/list`), então também não entra no cap por usuário.
    O SDK exige `arguments: dict[str, str]` — valor não-string é convertido
    aqui, não no chamador."""
    argumentos = {str(k): str(v) for k, v in (args or {}).items()}
    rotulo = "prompts/get"
    chave = _chave(rotulo + ":" + nome, argumentos)

    em_cache = _cache_get(chave, TTL_ESTATICO_S)
    if em_cache is not None:
        obslog.log("mcp", f"prompt {nome}", prompt=nome, cache=True)
        return ResultadoTool(em_cache, True)

    t0 = _relogio()

    async def _executar(sessao):
        return await sessao.get_prompt(nome, argumentos)

    r = await _chamar(rotulo, _executar)
    _cache_put(chave, r)
    obslog.log("mcp", f"prompt {nome}", prompt=nome, cache=False,
               ms=int((_relogio() - t0) * 1000))
    return ResultadoTool(r, False)


async def read_resource(uri: str) -> ResultadoTool:
    """`resources/read`. `uri` é **str** neste SDK (não `AnyUrl`). De graça
    no teto do serviço, como `get_prompt`."""
    rotulo = "resources/read"
    chave = _chave(rotulo, {"uri": uri})

    em_cache = _cache_get(chave, TTL_ESTATICO_S)
    if em_cache is not None:
        obslog.log("mcp", "resource", uri=uri, cache=True)
        return ResultadoTool(em_cache, True)

    t0 = _relogio()

    async def _executar(sessao):
        return await sessao.read_resource(uri)

    r = await _chamar(rotulo, _executar)
    _cache_put(chave, r)
    obslog.log("mcp", "resource", uri=uri, cache=False,
               ms=int((_relogio() - t0) * 1000))
    return ResultadoTool(r, False)
