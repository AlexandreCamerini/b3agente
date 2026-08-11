"""ADR-001 (Decisões 1 e 5) — de onde vêm os candles, e quanto isso custa.

**Por que existe.** O orçamento aprovado é US$ 0, então a fonte é o Yahoo. Mas o
Yahoo é gratuito, sem contrato, sem SLA, e seus termos vedam uso comercial: a
medição diz que ele sustenta o volume do Radar, nada diz que continuará
permitindo. Esta interface é o que transforma "trocar de fonte" em CONFIGURAÇÃO
em vez de refatoração — a mesma postura que `options_provider_yahoo.py` adotou
depois do incidente do 401.

**Gatilho declarado do plano B** (sem número, "temos plano B" é conversa):
taxa de não-200 acima de 2% numa janela de 3 pregões, lida por `snapshot()` e
exposta em `/api/obs/usage`. Nesse ponto a decisão volta para o Alex COM DADO.

**ADR-008 (11/08/2026) inverteu o primário.** A brapi (plano GRATUITO) é a
fonte master de candles DIÁRIOS; o Yahoo é o backup — e continua dono do
intraday e do histórico longo, que o plano gratuito não cobre (só `1d`, range
até `3mo`, medição em `docs/MEDICAO-Brapi-2026-08-11.md`). O roteamento aqui
decide por plano (fora do plano → backup direto, sem rede nem cota), por
orçamento (`brapi_budget`, hard stop → backup) e por falha (exceção ou série
vazia → backup na mesma requisição). O payload sai com `source` dizendo quem
serviu — no DIÁRIO as fontes entregam o MESMO print bruto da B3 (validado em
11/08: 21 pregões idênticos), então o cache (Fase 4) funde warmup Yahoo com
delta brapi e registra a fonte da última escrita como metadado.

Stdlib + httpx via `yahoo.py`/`brapi.py`. Testável offline (primário e backup
são injetáveis).
"""
import os
import time
from typing import Optional

from . import brapi, brapi_budget, yahoo

# ---------------------------------------------------------------------------
# Instrumentação (ADR-001, Decisão 5)
# ---------------------------------------------------------------------------
# "Custo cresce em silêncio" é risco declarado no checkout (§7). A IA já tem
# contador; o fetch de candles não tinha. Anel por dia, em memória: zera no
# deploy, como o `llm.usage_snapshot()`. Persistir isso custaria escrita em
# disco para observar uma coisa que o próprio deploy reinicia.
_JANELA_DIAS = 3          # a janela do gatilho do plano B
_LIMIAR_ERRO = 0.02       # 2% de FALHA aciona a decisão

# LIÇÃO DE 31/07/2026 — a primeira versão disto contava falha como "não-200" e
# era CEGA para o que de fato aconteceu. Naquele pregão o Yahoo devolveu
# HTTP 200 em 360 requisições seguidas, `marketState: REGULAR`, e ZERO velas de
# B3 durante 2 horas de mercado aberto — enquanto entregava AAPL em tempo real.
# A taxa de erro ficou em 0,00 e o alerta em `false`: o alarme detectava
# bloqueio e não via a falha mais provável desta fonte, que é sumir em silêncio.
# Resposta vazia agora CONTA como falha. Não existe caso legítimo em que o app
# pede candles e zero candles está certo — ticker inexistente vem como 404, que
# já era contado.
_uso: dict = {}   # "AAAA-MM-DD" -> {intervalo: {req, erros, vazios, ms, velas, ultimaVela}}
# ADR-008: com dois provedores ativos, a média dos dois cegaria o gatilho —
# esta dimensão paralela guarda o agregado POR PROVEDOR, e o `alerta` passa a
# ser calculado sobre o PRIMÁRIO.
_uso_prov: dict = {}   # "AAAA-MM-DD" -> {provedor: {req, erros, vazios}}


def _hoje() -> str:
    return time.strftime("%Y-%m-%d", time.localtime())


def _registra(interval: str, ms: float, velas: int, erro: bool, ultima=None,
              provedor: str = "?") -> None:
    dia = _uso.setdefault(_hoje(), {})
    r = dia.setdefault(interval or "1d",
                       {"req": 0, "erros": 0, "vazios": 0, "ms": 0.0, "velas": 0, "ultimaVela": None})
    r["req"] += 1
    r["ms"] += ms
    r["velas"] += velas
    p = _uso_prov.setdefault(_hoje(), {}).setdefault(
        provedor, {"req": 0, "erros": 0, "vazios": 0})
    p["req"] += 1
    if erro:
        r["erros"] += 1
        p["erros"] += 1
    elif velas == 0:
        r["vazios"] += 1          # 200 sem série: o modo de falha de 31/07
        p["vazios"] += 1
    if ultima:
        # Idade da série é diagnóstico direto: uma última vela de ontem durante
        # o pregão é feed morto, qualquer que seja o status HTTP.
        r["ultimaVela"] = ultima
    # mantém só a janela do gatilho (+1 dia de folga para virada de data)
    for d in sorted(_uso.keys())[:-(_JANELA_DIAS + 1)]:
        del _uso[d]
    for d in sorted(_uso_prov.keys())[:-(_JANELA_DIAS + 1)]:
        del _uso_prov[d]


def reset() -> None:
    """Para testes."""
    _uso.clear()
    _uso_prov.clear()


def snapshot() -> dict:
    """Uso do fetch de candles, por dia e por intervalo, + o gatilho do plano B.

    FALHA = não-200 (bloqueio, 404, timeout) **ou** 200 com série vazia (o feed
    sumiu em silêncio). `alerta=True` significa que a taxa passou do limiar na
    janela — hora de reabrir a Decisão 1 do ADR-001, com número na mão.
    """
    dias = sorted(_uso.keys())[-_JANELA_DIAS:]
    req = sum(r["req"] for d in dias for r in _uso[d].values())
    erros = sum(r["erros"] for d in dias for r in _uso[d].values())
    vazios = sum(r["vazios"] for d in dias for r in _uso[d].values())
    falhas = erros + vazios
    taxa = (falhas / req) if req else 0.0

    # Agregado POR PROVEDOR na mesma janela (ADR-008): o `alerta` mede o
    # PRIMÁRIO — com failover ativo, a média global esconderia o primário
    # caindo atrás de um backup saudável.
    por_prov: dict = {}
    for d in sorted(_uso_prov.keys())[-_JANELA_DIAS:]:
        for nome, p in _uso_prov[d].items():
            acc = por_prov.setdefault(nome, {"req": 0, "erros": 0, "vazios": 0})
            for k in ("req", "erros", "vazios"):
                acc[k] += p[k]
    for nome, acc in por_prov.items():
        f = acc["erros"] + acc["vazios"]
        acc["falhas"] = f
        acc["taxaFalha"] = round(f / acc["req"], 4) if acc["req"] else 0.0
    prim = por_prov.get(provider_name(), {"req": req, "falhas": falhas,
                                          "taxaFalha": round(taxa, 4)})
    return {
        "provedor": provider_name(),
        "fallback": fallback_name() or None,
        "porDia": {d: {iv: {**r, "msMedio": round(r["ms"] / r["req"]) if r["req"] else 0}
                       for iv, r in _uso[d].items()} for d in dias},
        "porProvedor": por_prov,
        "orcamentoBrapi": brapi_budget.snapshot() if provider_name() == "brapi" else None,
        "janelaDias": _JANELA_DIAS,
        "requisicoes": req,
        "erros": erros,          # não-200
        "vazios": vazios,        # 200 com zero velas
        "falhas": falhas,
        "taxaFalha": round(taxa, 4),
        "limiarAlerta": _LIMIAR_ERRO,
        "alerta": bool(prim["req"] >= 50 and prim["taxaFalha"] > _LIMIAR_ERRO),
    }


# ---------------------------------------------------------------------------
# Provedores
# ---------------------------------------------------------------------------
class CandleProvider:
    """Contrato mínimo. Uma operação só — é tudo que o app pede de candles."""

    nome = "abstrato"

    async def history(self, ticker: str, rng: str, interval: str = "1d") -> dict:
        """{"t", "currency", "candles": [{date, open, high, low, close, volume}]}.

        `date` identifica a vela: "AAAA-MM-DD" no diário, "AAAA-MM-DD HH:MM" no
        fuso da bolsa no intraday (ADR-001, item 5). Falha transitória levanta
        exceção — quem chama decide degradar.
        """
        raise NotImplementedError


class YahooProvider(CandleProvider):
    """O provedor de hoje. Reusa `yahoo.get_history` (sessão, crumb, retry,
    rotação de host) — esta classe é fronteira e instrumentação, não um segundo
    cliente HTTP."""

    nome = "yahoo"

    async def history(self, ticker: str, rng: str, interval: str = "1d") -> dict:
        return await yahoo.get_history(ticker, rng=rng, interval=interval)


class BrapiProvider(CandleProvider):
    """Era o plano B do ADR-001; implementado como fonte MASTER de diário/spot
    pelo ADR-008 (plano GRATUITO — limites medidos em 11/08/2026, ver
    `docs/MEDICAO-Brapi-2026-08-11.md`): só `1d`, range até 3mo, 1 ticker/req.

    A postura de falhar ALTO permanece nos dois casos que importam: pedido fora
    do plano (`brapi.ForaDoPlano`, SEM tocar a rede — recusa debita cota) e
    `BRAPI_TOKEN` ausente (RuntimeError explicando o que falta)."""

    nome = "brapi"

    async def history(self, ticker: str, rng: str, interval: str = "1d") -> dict:
        return await brapi.get_history(ticker, rng=rng, interval=interval)


_PROVEDORES = {"yahoo": YahooProvider, "brapi": BrapiProvider}
_ativo: Optional[CandleProvider] = None


def provider_name() -> str:
    return (os.environ.get("B3_CANDLE_PROVIDER") or "yahoo").strip().lower()


def get_provider() -> CandleProvider:
    """Provedor ativo (env `B3_CANDLE_PROVIDER`, default yahoo). Memoizado."""
    global _ativo
    nome = provider_name()
    if _ativo is None or _ativo.nome != nome:
        cls = _PROVEDORES.get(nome)
        if cls is None:
            raise ValueError(
                f"B3_CANDLE_PROVIDER='{nome}' desconhecido. Opções: {', '.join(sorted(_PROVEDORES))}.")
        _ativo = cls()
    return _ativo


def set_provider(p: Optional[CandleProvider]) -> None:
    """Injeção para testes. `None` volta ao resolvido por env."""
    global _ativo
    _ativo = p


# -- backup (ADR-008) -------------------------------------------------------
_fallback: Optional[CandleProvider] = None
_fb_injetado = False


def fallback_name() -> str:
    """Env `B3_CANDLE_FALLBACK`; vazio desliga. Default: `yahoo` quando o
    primário NÃO é o Yahoo (a inversão do ADR-008 nasce com backup), nada
    quando o primário é o Yahoo (comportamento pré-ADR-008 preservado)."""
    fb = os.environ.get("B3_CANDLE_FALLBACK")
    if fb is None:
        return "yahoo" if provider_name() != "yahoo" else ""
    return fb.strip().lower()


def get_fallback() -> Optional[CandleProvider]:
    global _fallback
    if _fb_injetado:
        return _fallback
    nome = fallback_name()
    if not nome or nome == provider_name():
        return None
    if _fallback is None or _fallback.nome != nome:
        cls = _PROVEDORES.get(nome)
        if cls is None:      # backup mal configurado não pode derrubar o app
            return None
        _fallback = cls()
    return _fallback


def set_fallback(p: Optional[CandleProvider]) -> None:
    """Injeção para testes. `None` volta ao resolvido por env."""
    global _fallback, _fb_injetado
    _fallback = p
    _fb_injetado = p is not None


async def _chama(p: CandleProvider, ticker: str, rng: str, interval: str) -> dict:
    """Uma chamada instrumentada. A INSTRUMENTAÇÃO mora aqui, na fronteira —
    não dentro de um provedor. Se vivesse no `YahooProvider`, trocar de fonte
    (que é justamente o momento em que se quer medir) apagaria o contador e o
    gatilho do plano B pararia de existir sem ninguém notar."""
    t0 = time.perf_counter()
    try:
        out = await p.history(ticker, rng, interval)
    except Exception:
        _registra(interval, (time.perf_counter() - t0) * 1000, 0, erro=True,
                  provedor=p.nome)
        raise
    velas = out.get("candles") or []
    _registra(interval, (time.perf_counter() - t0) * 1000, len(velas), erro=False,
              ultima=(velas[-1].get("date") if velas else None), provedor=p.nome)
    return out


async def get_history(ticker: str, rng: str = "1mo", interval: str = "1d") -> dict:
    """Ponto ÚNICO de entrada de candles do app. Mesma assinatura de
    `yahoo.get_history`; o payload ganha `source` = provedor que serviu.

    Roteamento (ADR-008, nesta ordem):
      1. PLANO — pedido que o plano gratuito da brapi não cobre (intraday,
         range longo) vai DIRETO ao backup: sem rede, sem cota, sem falsa
         falha no gatilho.
      2. ORÇAMENTO — sem saldo na fatia/fora da janela de pregão, o backup
         assume; sem backup configurado, a chamada segue (proteção de cota
         não pode virar "sem dado" quando não há alternativa).
      3. FALHA — exceção OU série vazia (o modo de 31/07) → backup na mesma
         requisição.
    """
    prim = get_provider()
    fb = get_fallback()

    if prim.nome == "brapi":
        try:
            brapi.valida_plano(rng, interval)
        except brapi.ForaDoPlano:
            if fb is None:
                raise
            out = await _chama(fb, ticker, rng, interval)
            out["source"] = fb.nome
            return out
        if brapi_budget.pode_gastar("delta"):
            brapi_budget.debita("delta")
        elif fb is not None:
            out = await _chama(fb, ticker, rng, interval)
            out["source"] = fb.nome
            return out

    try:
        out = await _chama(prim, ticker, rng, interval)
    except Exception:
        if fb is None:
            raise
        out = await _chama(fb, ticker, rng, interval)
        out["source"] = fb.nome
        return out

    if not (out.get("candles") or []) and fb is not None:
        try:
            alt = await _chama(fb, ticker, rng, interval)
        except Exception:
            alt = None
        if alt and (alt.get("candles") or []):
            alt["source"] = fb.nome
            return alt
    out["source"] = prim.nome
    return out


# ---------------------------------------------------------------------------
# Spot (ADR-008, Fase 5) — mesma fronteira, mesmo roteamento
# ---------------------------------------------------------------------------
# Contrato de erro preservado: os chamadores já tratam `yahoo.QuoteUnavailable`
# como indisponibilidade transitória (503) — a fronteira levanta a MESMA classe
# quando nem primário nem backup servem.
QuoteUnavailable = yahoo.QuoteUnavailable


def _spot_ttl() -> float:
    """TTL do spot = intervalo configurado (controle de utilização); o soft
    stop continua alongando (3×) quando a fatia passa de 80%."""
    base = brapi_budget.spot_intervalo_s()
    return base * 3 if brapi_budget.degradado("spot") else base


async def _quote_brapi(ticker: str):
    """Spot pela brapi respeitando cache compartilhado e orçamento.
    Devolve o payload ou None (sem token / sem orçamento / falha) — quem
    decide o backup é a fronteira."""
    if not brapi.tem_token():
        return None
    q = brapi.quote_cached(ticker, _spot_ttl())
    if q is not None:
        return {**q, "source": "brapi"}
    if not brapi_budget.pode_gastar("spot"):
        return None
    brapi_budget.debita("spot")
    try:
        q = await brapi.fetch_quote(ticker)
    except Exception:  # noqa: BLE001 — falha do spot brapi degrada p/ backup
        return None
    # NADA buscado se perde: o spot pago em cota alimenta a vela do dia no
    # acervo próprio (import tardio; candle_cache não importa este módulo).
    from . import candle_cache
    candle_cache.atualiza_vela_do_dia(ticker, q.get("price"), src="brapi",
                                      currency=q.get("currency"))
    return {**q, "source": "brapi"}


async def get_quote(ticker: str) -> dict:
    """Ponto único do spot. Primário brapi → cache/orçamento → backup Yahoo.
    Payload no contrato de `yahoo.get_quote` + `source`."""
    if provider_name() == "brapi":
        q = await _quote_brapi(ticker)
        if q is not None:
            return q
        fb = get_fallback()
        if fb is None:
            raise QuoteUnavailable(
                "Cotação indisponível: brapi sem token/orçamento e nenhum backup configurado.")
        out = await yahoo.get_quote(ticker)
        return {**out, "source": "yahoo"} if isinstance(out, dict) else out
    out = await yahoo.get_quote(ticker)
    return {**out, "source": "yahoo"} if isinstance(out, dict) else out


async def get_quotes(tickers: list) -> dict:
    """Lote de spots. No free da brapi é 1 ticker/req — o cache compartilhado
    absorve a maior parte; o que faltar e couber no orçamento vai à brapi, o
    resto desce em lote único para o backup (batch do Yahoo)."""
    if provider_name() != "brapi":
        got = await yahoo.get_quotes(tickers)
        return {t: ({**q, "source": "yahoo"} if isinstance(q, dict) else q)
                for t, q in got.items()}

    out, faltam = {}, []
    for t in tickers:
        q = await _quote_brapi(t) if brapi.tem_token() else None
        if q is not None:
            out[t] = q
        else:
            faltam.append(t)
    if faltam:
        fb = get_fallback()
        if fb is not None:
            got = await yahoo.get_quotes(faltam)
            for t, q in got.items():
                out[t] = {**q, "source": "yahoo"} if isinstance(q, dict) else q
        else:
            for t in faltam:
                out[t] = {"t": t, "price": None, "change": 0,
                          "error": "sem cotação (brapi sem orçamento, backup desligado)"}
    return out
