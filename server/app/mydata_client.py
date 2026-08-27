"""Cliente HTTP do hub `mydata.acamerini.app` (~/dev/cvm-financas), Fase 9
(qa/09) — fronteira única de acervo diário oficial COTAHIST. Espelha a forma
de `server/app/brapi.py` (async httpx, retry curto, kwarg `fetch_json`
injetável) com uma diferença deliberada: o hub autentica por header
`X-API-Key` (NÃO é Bearer — confirmado contra
`~/dev/cvm-financas/app/api/main.py:135-137`, `exigir_chave`).

O que este módulo NÃO faz: fiação em `candle_provider`/`options_api` (Planos
09-02/09-03) e nenhuma chamada real neste plano — só o cliente e seus
guardiões offline.
"""
import asyncio
import os
from urllib.parse import urlsplit

import httpx

BASE_DEFAULT = "https://mydata.acamerini.app"
TIMEOUT_S = 20
PAGINAS_MAX = 8
LIMITE_MAX = 2000

# Última leitura de X-Quota-Limite/X-Quota-Restante — verdade > previsão do
# orçamento local (mydata_budget.snapshot() expõe ao lado do contador local).
LAST_QUOTA: dict = {}


class MydataIndisponivel(RuntimeError):
    """Falha transitória ou resposta imprestável — quem chama decide degradar."""


class MydataForaDaFatia(ValueError):
    """Pedido que a fatia do COTAHIST não cobre (ex.: intraday). Levantada SEM
    tocar a rede — espelho de `brapi.ForaDoPlano`."""


def base_url() -> str:
    """Lê `MYDATA_URL` (default `BASE_DEFAULT`). VALIDA o esquema: só
    `https://`, ou `http://` quando o host é `localhost`/`127.0.0.1` (dev).
    Qualquer outra coisa levanta `ValueError` — mitigação de T-09-02:
    `MYDATA_URL` é entrada de operador e é o único ponto que decide para onde
    a chave viaja."""
    raw = (os.environ.get("MYDATA_URL") or "").strip().rstrip("/")
    if not raw:
        return BASE_DEFAULT
    parsed = urlsplit(raw)
    if parsed.scheme == "https":
        return raw
    if parsed.scheme == "http" and parsed.hostname in ("localhost", "127.0.0.1"):
        return raw
    raise ValueError(
        f"MYDATA_URL com esquema '{parsed.scheme}' não permitido — a chave "
        "do mydata só trafega por TLS (https://); http:// só é aceito para "
        "localhost/127.0.0.1 em desenvolvimento local."
    )


def _token() -> str:
    return (os.environ.get("MYDATA_TOKEN") or "").strip()


def tem_token() -> bool:
    return bool(_token())


async def _fetch_json(path: str, params: dict) -> dict:
    """GET com `X-API-Key` e retry curto (2 tentativas em timeout/5xx).
    429/401/403 NUNCA fazem retry — 429 porque retry gastaria mais cota
    (o oposto do que se quer); 401/403 porque a chave não vai ficar boa na
    segunda tentativa."""
    headers = {"X-API-Key": _token(), "User-Agent": "Boris+/mydata"}
    last = None
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
                r = await client.get(base_url() + path, params=params, headers=headers)
        except httpx.HTTPError as e:
            last = MydataIndisponivel(f"mydata inacessível: {e!r}")
            await asyncio.sleep(0.4 * (attempt + 1))
            continue

        for h in ("X-Quota-Limite", "X-Quota-Restante"):
            if h in r.headers:
                LAST_QUOTA[h] = r.headers[h]

        if r.status_code == 429:
            retry_after = r.headers.get("Retry-After")
            corpo = None
            try:
                corpo = r.json()
            except ValueError:
                corpo = None
            erro = (corpo or {}).get("erro") if isinstance(corpo, dict) else None
            codigo = (erro or {}).get("codigo") if isinstance(erro, dict) else None
            mensagem = (erro or {}).get("mensagem") if isinstance(erro, dict) else None
            detalhe = f": {codigo} — {mensagem}" if (codigo or mensagem) else ""
            raise MydataIndisponivel(
                f"mydata quota excedida (Retry-After={retry_after}s){detalhe}")

        if r.status_code in (401, 403):
            # NUNCA incluir o valor do token na mensagem (T-09-01).
            raise MydataIndisponivel(
                "mydata recusou a chave (chave_invalida) — verifique "
                "MYDATA_TOKEN no ambiente.")

        if r.status_code >= 500:
            last = MydataIndisponivel(f"mydata HTTP {r.status_code}")
            await asyncio.sleep(0.4 * (attempt + 1))
            continue

        try:
            return r.json()
        except ValueError:
            raise MydataIndisponivel(
                f"mydata HTTP {r.status_code} com corpo não-JSON")
    raise last


async def _paginar(path: str, params: dict, *, fetch_json=None) -> list:
    """Percorre o envelope `{"dados": [...], "proximo_cursor": <str|null>}`,
    acumulando `dados` e repassando `cursor` na chamada seguinte. Para quando
    `proximo_cursor` for falsy OU ao atingir `PAGINAS_MAX` (teto anti-loop
    contra cursor que não avança) — nesse caso não levanta: dado parcial
    rotulado é melhor que exceção."""
    fetch = fetch_json or _fetch_json
    dados: list = []
    cursor = None
    pagina = 0
    while True:
        pagina += 1
        p = dict(params)
        if cursor:
            p["cursor"] = cursor
        resp = await fetch(path, p)
        if not isinstance(resp, dict) or not isinstance(resp.get("dados"), list):
            raise MydataIndisponivel(f"mydata: resposta inesperada em {path}")
        dados.extend(resp["dados"])
        cursor = resp.get("proximo_cursor")
        if not cursor:
            break
        if pagina >= PAGINAS_MAX:
            print(f"[mydata] paginação parou no teto de {PAGINAS_MAX} páginas em {path}")
            break
    return dados
