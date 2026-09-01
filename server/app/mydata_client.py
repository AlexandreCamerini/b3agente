"""Cliente HTTP do hub `mydata.semente.dev` (~/dev/cvm-financas), Fase 9
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
from datetime import date, timedelta
from urllib.parse import urlsplit

import httpx

from .tickers import normalize_ticker

# Domínio canônico confirmado pelo Alex em 2026-09-01; o nome antigo era
# alias do MESMO serviço Railway (mesmo edge/trace), segue vivo mas não é
# o nome a usar. Produção não seta MYDATA_URL, logo depende deste default.
BASE_DEFAULT = "https://mydata.semente.dev"
TIMEOUT_S = 20
PAGINAS_MAX = 8
LIMITE_MAX = 2000

INTERVALO_UNICO = "1d"
# Dias CORRIDOS por range — folgados de propósito: o pregão só tem ~21 dias
# úteis/mês; apertar cortaria candles no início da série. "1d": 5 cobre
# feriado prolongado.
RANGE_DIAS = {
    "1d": 5, "5d": 12, "1mo": 45, "3mo": 110, "6mo": 200,
    "1y": 400, "2y": 790, "5y": 1900, "max": 3700,
}

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


def _round(x):
    return round(x, 2) if isinstance(x, (int, float)) else None


def valida_fatia(rng: str, interval: str) -> None:
    """Guarda client-side, espelho de `brapi.valida_plano`. Nunca toca a
    rede: é o que mantém o Yahoo dono do intraday sem gastar cota para
    descobrir (ADR-001 intocada)."""
    if interval != INTERVALO_UNICO:
        raise MydataForaDaFatia(
            f"Intervalo '{interval}' fora da fatia do mydata — o COTAHIST só "
            "publica candle diário, após o fechamento do pregão. Intraday "
            "continua sendo do Yahoo por decisão do ADR-001."
        )
    if rng not in RANGE_DIAS:
        raise MydataForaDaFatia(
            f"Range '{rng}' desconhecido para o mydata (permitidos: "
            f"{', '.join(sorted(RANGE_DIAS))})."
        )


async def get_history(ticker: str, rng: str = "1mo", interval: str = "1d",
                       *, fetch_json=None) -> dict:
    """Contrato de `CandleProvider.history()`:
    {"t", "currency", "candles": [{date, open, high, low, close, volume}]}.

    `volume` vem de `quantidade_negociada` (papéis), NUNCA do notional em R$
    (outro campo da linha). `hv21`/`hv63`/`preco_medio`/`proveniencia`
    existem na linha e são deliberadamente ignorados — o contrato
    `CandleProvider` é fechado. `fetch_json` é injetável para teste offline.
    """
    valida_fatia(rng, interval)
    if not _token():
        raise RuntimeError(
            "MYDATA_TOKEN ausente no ambiente. Sem ela o provedor mydata não "
            "opera — defina a variável no Railway/local ou aponte "
            "B3_CANDLE_PROVIDER de volta para 'brapi'."
        )

    symbol = normalize_ticker(ticker)
    de = (date.today() - timedelta(days=RANGE_DIAS[rng])).isoformat()
    linhas = await _paginar(
        f"/v1/cotacoes/{symbol}", {"de": de, "limite": LIMITE_MAX},
        fetch_json=fetch_json)

    candles = []
    for row in linhas:
        close = row.get("preco_fechamento")
        if close is None:
            continue
        candles.append({
            "date": row.get("dt_pregao"),
            "open": _round(row.get("preco_abertura")),
            "high": _round(row.get("preco_maximo")),
            "low": _round(row.get("preco_minimo")),
            "close": _round(close),
            "volume": row.get("quantidade_negociada"),
        })
    return {"t": symbol, "currency": "BRL", "candles": candles}


# Sem `pregao`, o hub responde o ÚLTIMO pregão publicado DAQUELE papel (não o
# último pregão da base) — é o que impede um papel que parou de negociar de
# parecer "sem dado" quando na verdade só está atrasado em relação ao resto
# do universo. `get_vencimentos`/`get_options_chain` NÃO remapeiam campos: o
# vocabulário de `gold_opcoes` é falado cru até o adaptador (Plano 09-03,
# Task 2) — o cliente só sabe buscar, não interpretar.
async def get_vencimentos(ticker: str, pregao: str = None, *, fetch_json=None) -> list:
    """`GET /v1/opcoes/{ticker}/vencimentos`. NÃO usa `_paginar`: este
    endpoint não devolve `proximo_cursor`. Papel sem nenhum pregão publicado
    devolve `{"dados": []}` — ausência de negócio, não erro."""
    if not _token():
        raise RuntimeError(
            "MYDATA_TOKEN ausente no ambiente. Sem ela o provedor mydata não "
            "opera — defina a variável no Railway/local."
        )
    symbol = normalize_ticker(ticker)
    fetch = fetch_json or _fetch_json
    params = {"pregao": pregao} if pregao else {}
    resp = await fetch(f"/v1/opcoes/{symbol}/vencimentos", params)
    if not isinstance(resp, dict) or not isinstance(resp.get("dados"), list):
        raise MydataIndisponivel(
            f"mydata: resposta inesperada em /v1/opcoes/{symbol}/vencimentos")
    return resp["dados"]


async def get_options_chain(ticker: str, vencimento: str = None, pregao: str = None,
                             tipo: str = None, *, fetch_json=None) -> list:
    """`GET /v1/opcoes/{ticker}`, paginado por `proximo_cursor`. Devolve as
    linhas cruas de `gold_opcoes` — o mapeamento para o contrato do ADR-004 é
    responsabilidade do adaptador (`options_provider_mydata.py`), não deste
    cliente. Propaga `MydataIndisponivel` sem engolir: quem decide degradar é
    o adaptador (D-04), não o cliente."""
    if not _token():
        raise RuntimeError(
            "MYDATA_TOKEN ausente no ambiente. Sem ela o provedor mydata não "
            "opera — defina a variável no Railway/local."
        )
    symbol = normalize_ticker(ticker)
    params = {"limite": LIMITE_MAX}
    if vencimento:
        params["vencimento"] = vencimento
    if pregao:
        params["pregao"] = pregao
    if tipo:
        params["tipo"] = tipo
    return await _paginar(f"/v1/opcoes/{symbol}", params, fetch_json=fetch_json)
