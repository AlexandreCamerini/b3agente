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

from . import brapi, brapi_budget, mydata_budget, mydata_client, yahoo

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
    nomes_ativos = (provider_name(), *fallback_names())
    return {
        "provedor": provider_name(),
        "fallback": fallback_name() or None,
        "fallbacks": fallback_names(),
        "porDia": {d: {iv: {**r, "msMedio": round(r["ms"] / r["req"]) if r["req"] else 0}
                       for iv, r in _uso[d].items()} for d in dias},
        "porProvedor": por_prov,
        "orcamentoBrapi": brapi_budget.snapshot() if provider_name() == "brapi" else None,
        "orcamentoMydata": mydata_budget.snapshot() if "mydata" in nomes_ativos else None,
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


class MydataProvider(CandleProvider):
    """Hub `mydata.acamerini.app` (`~/dev/cvm-financas`), fonte do acervo
    diário oficial COTAHIST da B3 (ADR-019/09-CONTEXT.md). Cobre SÓ a fatia
    DIÁRIA: o COTAHIST só publica após o fechamento do pregão — o intraday
    continua sendo do Yahoo por decisão do ADR-001, que esta fase não reabre.

    `valida_fatia`/`get_history` (mydata_client.py) recusam intraday ANTES de
    tocar a rede; o gate do roteador (`_gate`, abaixo) já garante isso, mas a
    guarda vive nos dois lugares por defesa em profundidade."""

    nome = "mydata"

    async def history(self, ticker: str, rng: str, interval: str = "1d") -> dict:
        return await mydata_client.get_history(ticker, rng=rng, interval=interval)


_PROVEDORES = {"yahoo": YahooProvider, "brapi": BrapiProvider, "mydata": MydataProvider}
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


# -- backup (ADR-008, cadeia de N saltos desde a Fase 9/Plano 02) -----------
_fallbacks: list = []
_fb_injetado = False

# Default por primário quando `B3_CANDLE_FALLBACK` está ausente. mydata é o
# elo mais "caro" de configurar errado (cota pequena) — por isso cai em DOIS
# saltos (brapi, depois yahoo); brapi preserva o salto único de hoje; yahoo
# preserva o comportamento pré-ADR-008 (sem backup).
_FALLBACK_DEFAULT = {"mydata": ["brapi", "yahoo"], "brapi": ["yahoo"], "yahoo": []}


def fallback_names() -> list:
    """Cadeia de nomes de backup, na ordem de tentativa. Env
    `B3_CANDLE_FALLBACK` (lista separada por vírgula); ausente usa o default
    por primário (`_FALLBACK_DEFAULT`). Filtra fora o próprio primário e
    nomes desconhecidos (backup mal configurado não derruba o app), e
    deduplica preservando ordem. `B3_CANDLE_FALLBACK=""` desliga — vazio
    continua sendo o contrato de "sem backup"."""
    fb = os.environ.get("B3_CANDLE_FALLBACK")
    if fb is None:
        brutos = _FALLBACK_DEFAULT.get(provider_name(), [])
    else:
        brutos = [n.strip().lower() for n in fb.split(",") if n.strip()]
    prim = provider_name()
    out: list = []
    for n in brutos:
        if n == prim or n not in _PROVEDORES or n in out:
            continue
        out.append(n)
    return out


def fallback_name() -> str:
    """Compat: primeiro nome da cadeia, ou `""`. `snapshot()` e os guardiões
    existentes dependem desta assinatura de string única — não remover."""
    nomes = fallback_names()
    return nomes[0] if nomes else ""


def get_fallbacks() -> list:
    """Cadeia de provedores de backup instanciados, na ordem de
    `fallback_names()`. Memoiza comparando os nomes já instanciados com a
    cadeia atual — reconstrói só quando a env muda entre chamadas."""
    global _fallbacks
    if _fb_injetado:
        return _fallbacks
    nomes = fallback_names()
    atuais = [p.nome for p in _fallbacks]
    if atuais != nomes:
        novos = []
        for n in nomes:
            cls = _PROVEDORES.get(n)
            if cls is None:      # backup mal configurado não pode derrubar o app
                continue
            novos.append(cls())
        _fallbacks = novos
    return _fallbacks


def get_fallback() -> Optional[CandleProvider]:
    """Compat: primeiro elo da cadeia, ou `None`. Preserva o contrato atual
    para quem ainda chama a versão singular."""
    fbs = get_fallbacks()
    return fbs[0] if fbs else None


def set_fallback(p: Optional[CandleProvider]) -> None:
    """Injeção para testes com UM provedor. `None` volta ao resolvido por
    env (cadeia inteira recalculada por `fallback_names()`)."""
    global _fallbacks, _fb_injetado
    _fallbacks = [p] if p is not None else []
    _fb_injetado = p is not None


def set_fallbacks(ps: list) -> None:
    """Injeção para testes com a CADEIA inteira. `[]`/`None` volta ao
    resolvido por env."""
    global _fallbacks, _fb_injetado
    _fallbacks = list(ps or [])
    _fb_injetado = bool(ps)


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


# -- gate de fatia/plano/cota, por elo (ADR-008, generalizado na Fase 9) ----
# Dois tipos de recusa, com efeito DIFERENTE quando o elo é o ÚLTIMO da
# cadeia (sem próximo pra tentar):
#   • PLANO/FATIA (pedido que o provedor não cobre, ex.: intraday na brapi ou
#     no mydata): recusa DURA — levanta a exceção original. Não existe modo
#     degradado de "servir mesmo assim" quando o provedor não sabe responder
#     aquele pedido.
#   • ORÇAMENTO/COTA (sem saldo agora): recusa MOLE — no último elo, a
#     proteção de cota não pode virar "sem dado" quando não há alternativa;
#     a chamada segue SEM debitar (mesma regra que `get_history` já aplicava
#     para o caso de um salto só, generalizada aqui para N elos).
_MOTIVOS_ORCAMENTO = {"sem orçamento", "sem cota"}


def _gate(p: CandleProvider, rng: str, interval: str):
    """Decide, SEM tocar a rede e SEM debitar, se `p` pode ser chamado agora.

    Devolve `(None, None)` quando pode. Quando não pode, devolve
    `(motivo: str, erro: Optional[Exception])` — `erro` só vem preenchido
    para recusa de PLANO/FATIA (a exceção original, para o chamador relançar
    se este for o último elo); recusa de ORÇAMENTO/COTA vem com `erro=None`.
    """
    if p.nome == "brapi":
        try:
            brapi.valida_plano(rng, interval)
        except brapi.ForaDoPlano as e:
            return "fora do plano", e
        if not brapi_budget.pode_gastar("delta"):
            return "sem orçamento", None
        return None, None
    if p.nome == "mydata":
        try:
            mydata_client.valida_fatia(rng, interval)
        except mydata_client.MydataForaDaFatia as e:
            return "fora da fatia", e
        if not mydata_budget.pode_gastar():
            return "sem cota", None
        return None, None
    return None, None


def _debita(p: CandleProvider) -> None:
    """Debita o orçamento do provedor imediatamente antes da chamada de
    rede. `yahoo` (e qualquer provedor sem orçamento próprio) não faz nada."""
    if p.nome == "brapi":
        brapi_budget.debita("delta")
    elif p.nome == "mydata":
        mydata_budget.debita()


async def get_history(ticker: str, rng: str = "1mo", interval: str = "1d") -> dict:
    """Ponto ÚNICO de entrada de candles do app. Mesma assinatura de
    `yahoo.get_history`; o payload ganha `source` = provedor que serviu.

    Roteamento (ADR-008 + Fase 9/Plano 02 — cadeia de N elos, nesta ordem
    para CADA elo `[get_provider(), *get_fallbacks()]`):
      1. PLANO/FATIA — pedido que o elo não cobre (intraday na brapi/mydata,
         range fora do plano gratuito da brapi) PULA o elo sem tocar a rede
         nem a cota; se for o ÚLTIMO elo, relança a exceção original (não há
         modo degradado de "servir mesmo assim" sem saber responder).
      2. ORÇAMENTO/COTA — sem saldo agora PULA o elo; se for o ÚLTIMO,
         a chamada segue SEM debitar (proteção de cota não pode virar
         "sem dado" quando não há alternativa).
      3. FALHA — exceção OU série vazia (o modo de 31/07) avança para o
         PRÓXIMO elo, na MESMA requisição.
    Esgotada a cadeia: uma série vazia de algum elo vale mais que erro (é o
    comportamento de hoje, generalizado); sem isso, relança o último erro de
    REDE; sem erro nem vazio (cadeia inteira recusada pelo gate), levanta
    `RuntimeError` citando os motivos — é configuração errada, e falhar alto
    explicando o que falta é a postura já declarada em `BrapiProvider`.
    """
    cadeia = [get_provider(), *get_fallbacks()]

    melhor_vazio = None    # (nome, out) do primeiro vazio encontrado na cadeia
    ultimo_erro = None     # última exceção de REDE (não de gate)
    motivos: list = []     # diagnóstico de todo pulo por gate

    for idx, p in enumerate(cadeia):
        eh_ultimo = idx == len(cadeia) - 1
        motivo, erro_gate = _gate(p, rng, interval)
        if motivo is not None:
            if eh_ultimo and erro_gate is not None:
                raise erro_gate
            if eh_ultimo and motivo in _MOTIVOS_ORCAMENTO:
                pass   # último elo, só falta cota: serve mesmo assim, sem debitar
            else:
                motivos.append(f"{p.nome}: {motivo}")
                continue
        else:
            _debita(p)
        try:
            out = await _chama(p, ticker, rng, interval)
        except Exception as e:
            ultimo_erro = e
            continue
        if not (out.get("candles") or []):
            if melhor_vazio is None:
                melhor_vazio = (p.nome, out)
            continue
        out["source"] = p.nome
        return out

    if melhor_vazio is not None:
        nome, out = melhor_vazio
        out["source"] = nome
        return out
    if ultimo_erro is not None:
        raise ultimo_erro
    raise RuntimeError(
        "candle_provider: cadeia inteira recusada pelo gate, sem erro nem "
        "série vazia — motivos: "
        f"{'; '.join(motivos) if motivos else 'nenhum provedor configurado'}."
    )


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
    Payload no contrato de `yahoo.get_quote` + `source`.

    C-12 (REPORT-01): antes desta correção, o spot SINGULAR não tinha o
    try/except que `get_quotes` (plural, abaixo) já tem há mais tempo —
    exceção crua do Yahoo (URL completa + parâmetro `crumb`) subia até
    virar HTTP 500 na resposta de `POST /api/buy`, reproduzido ao vivo com
    `{"t":"XXXXX9"}`. `QuoteUnavailable` continua sendo relançada sem
    alteração — é o contrato de indisponibilidade transitória (503) que os
    chamadores já tratam; só a exceção crua do provedor vira preço nulo."""
    if provider_name() == "brapi":
        q = await _quote_brapi(ticker)
        if q is not None:
            return q
        fb = get_fallback()
        if fb is None:
            raise QuoteUnavailable(
                "Cotação indisponível: brapi sem token/orçamento e nenhum backup configurado.")
        try:
            out = await yahoo.get_quote(ticker)
        except QuoteUnavailable:
            raise
        except Exception as e:  # noqa: BLE001 — nunca vaza detalhe técnico do provedor (C-12)
            print(f"[candle_provider] get_quote({ticker}) via yahoo (backup) falhou: {e}")
            return {"t": ticker, "price": None, "change": None,
                    "error": "sem cotação (falha do provedor de dados)"}
        return {**out, "source": "yahoo"} if isinstance(out, dict) else out
    try:
        out = await yahoo.get_quote(ticker)
    except QuoteUnavailable:
        raise
    except Exception as e:  # noqa: BLE001 — nunca vaza detalhe técnico do provedor (C-12)
        print(f"[candle_provider] get_quote({ticker}) via yahoo falhou: {e}")
        return {"t": ticker, "price": None, "change": None,
                "error": "sem cotação (falha do provedor de dados)"}
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
                out[t] = {"t": t, "price": None, "change": None,
                          "error": "sem cotação (brapi sem orçamento, backup desligado)"}
    return out


# ---------------------------------------------------------------------------
# Fonte EXCLUSIVA do ciclo do agente (decisão do Alex, 11/08)
# ---------------------------------------------------------------------------
# O motor de execução (agent.py: run_cycle_for/scheduler_loop) decide
# compra/venda/stop/alvo a partir da cotação — é o consumidor mais crítico do
# app. `get_quote`/`get_quotes` acima fazem primário+backup (bom para
# tela/watchlist: sempre mostra ALGUM preço). Para o ciclo isso é ERRADO: se a
# base de preço trocar de fonte NO MEIO da avaliação das posições, o mesmo
# ciclo mistura preços de duas origens diferentes — inconsistência que o
# CLAUDE.md proíbe ("cálculos determinísticos", "não invente valores").
#
# Por isso o agente usa uma fonte ÚNICA e EXCLUSIVA (`B3_AGENT_QUOTE_SOURCE`,
# "brapi" xor "yahoo" — nunca os dois). Falha na fonte escolhida NÃO cai para
# a outra: vira marcador de erro por ticker, no mesmo formato que
# `yahoo.get_quotes` já usa para falha parcial — o agente já sabe pular
# posição sem preço (agent.py: `if price is None: continue`), então essa
# resiliência é reaproveitada, só sem cruzar fonte.
AGENT_QUOTE_SOURCES = ("brapi", "yahoo")


def agent_quote_source() -> str:
    """Fonte configurada para o ciclo do agente. Default `brapi` — decisão do
    Alex de 11/08: 'daqui pra frente usaremos brapi [nesse ponto] se os testes
    derem certo'. `B3_AGENT_QUOTE_SOURCE=yahoo` volta para a fonte antiga."""
    s = (os.environ.get("B3_AGENT_QUOTE_SOURCE") or "brapi").strip().lower()
    if s not in AGENT_QUOTE_SOURCES:
        raise ValueError(
            f"B3_AGENT_QUOTE_SOURCE='{s}' desconhecido. Opções: {', '.join(AGENT_QUOTE_SOURCES)}.")
    return s


async def _quote_brapi_or_raise(ticker: str) -> dict:
    """Como `_quote_brapi`, mas NUNCA engole a falha — o chamador (modo
    exclusivo) decide se ela vira marcador de erro por ticker. Reusa cache
    compartilhado, orçamento (fatia `spot`) e o acervo (`atualiza_vela_do_dia`)
    — mesma infraestrutura da fronteira com backup, sem duplicar."""
    if not brapi.tem_token():
        raise QuoteUnavailable(f"brapi sem BRAPI_TOKEN — fonte exclusiva do agente para {ticker}.")
    q = brapi.quote_cached(ticker, _spot_ttl())
    if q is not None:
        return {**q, "source": "brapi"}
    if not brapi_budget.pode_gastar("spot"):
        raise QuoteUnavailable(f"orçamento da brapi esgotado — sem cota p/ {ticker} agora.")
    brapi_budget.debita("spot")
    q = await brapi.fetch_quote(ticker)   # propaga BrapiIndisponivel se falhar
    from . import candle_cache
    candle_cache.atualiza_vela_do_dia(ticker, q.get("price"), src="brapi",
                                      currency=q.get("currency"))
    return {**q, "source": "brapi"}


async def get_quotes_exclusive(tickers: list, source: Optional[str] = None) -> dict:
    """Cotações do CICLO DO AGENTE. Uma fonte só, do início ao fim do lote —
    nunca cai para a outra em caso de falha. `source` explícito é só para
    teste; em produção sempre vem de `agent_quote_source()`.

    Payload no mesmo contrato de `yahoo.get_quotes`
    ({t: {price, change, previousClose, currency, source, ...}}); ticker cuja
    fonte falhou vem com `price: None` e `error` — o agente já pula posição
    sem preço, então nada muda no motor de regras além de QUEM serviu o dado.
    """
    src = source or agent_quote_source()
    if src == "yahoo":
        got = await yahoo.get_quotes(tickers)
        return {t: ({**q, "source": "yahoo"} if isinstance(q, dict) else q)
                for t, q in got.items()}
    out = {}
    for t in tickers:
        try:
            out[t] = await _quote_brapi_or_raise(t)
        except Exception as e:  # noqa: BLE001 — vira marcador; NUNCA tenta o yahoo
            out[t] = {"t": t, "price": None, "change": None, "source": "brapi",
                      "error": f"fonte exclusiva (brapi) sem cotação: {e}"}
    return out
