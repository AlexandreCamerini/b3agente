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

**O que NÃO está aqui.** A brapi Pro (R$ 116,66/mês, intraday 1m–90m, 20 tickers
por requisição, delay ~5 min) está documentada e deliberadamente NÃO
implementada: implementar um provedor que ninguém exercita é código morto que
apodrece. `_BrapiProvider` existe como esqueleto que falha alto, para que o dia
de acioná-lo comece com um erro claro em vez de uma busca no histórico do git.

Stdlib + httpx via `yahoo.py`. Testável offline (o provedor é injetável).
"""
import os
import time
from typing import Optional

from . import yahoo

# ---------------------------------------------------------------------------
# Instrumentação (ADR-001, Decisão 5)
# ---------------------------------------------------------------------------
# "Custo cresce em silêncio" é risco declarado no checkout (§7). A IA já tem
# contador; o fetch de candles não tinha. Anel por dia, em memória: zera no
# deploy, como o `llm.usage_snapshot()`. Persistir isso custaria escrita em
# disco para observar uma coisa que o próprio deploy reinicia.
_JANELA_DIAS = 3          # a janela do gatilho do plano B
_LIMIAR_ERRO = 0.02       # 2% de não-200 aciona a decisão

_uso: dict = {}           # "AAAA-MM-DD" -> {intervalo: {req, erros, ms, velas}}


def _hoje() -> str:
    return time.strftime("%Y-%m-%d", time.localtime())


def _registra(interval: str, ms: float, velas: int, erro: bool) -> None:
    dia = _uso.setdefault(_hoje(), {})
    r = dia.setdefault(interval or "1d", {"req": 0, "erros": 0, "ms": 0.0, "velas": 0})
    r["req"] += 1
    r["ms"] += ms
    r["velas"] += velas
    if erro:
        r["erros"] += 1
    # mantém só a janela do gatilho (+1 dia de folga para virada de data)
    for d in sorted(_uso.keys())[:-(_JANELA_DIAS + 1)]:
        del _uso[d]


def reset() -> None:
    """Para testes."""
    _uso.clear()


def snapshot() -> dict:
    """Uso do fetch de candles, por dia e por intervalo, + o gatilho do plano B.

    `alerta=True` significa: a taxa de erro passou do limiar na janela — hora de
    reabrir a Decisão 1 do ADR-001, com número na mão.
    """
    dias = sorted(_uso.keys())[-_JANELA_DIAS:]
    req = sum(r["req"] for d in dias for r in _uso[d].values())
    erros = sum(r["erros"] for d in dias for r in _uso[d].values())
    taxa = (erros / req) if req else 0.0
    return {
        "provedor": provider_name(),
        "porDia": {d: {iv: {**r, "msMedio": round(r["ms"] / r["req"]) if r["req"] else 0}
                       for iv, r in _uso[d].items()} for d in dias},
        "janelaDias": _JANELA_DIAS,
        "requisicoes": req,
        "erros": erros,
        "taxaErro": round(taxa, 4),
        "limiarAlerta": _LIMIAR_ERRO,
        "alerta": bool(req >= 50 and taxa > _LIMIAR_ERRO),
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
    """PLANO B documentado, NÃO implementado (ADR-001, Decisão 1).

    brapi Pro: R$ 116,66/mês no anual, intraday 1m–90m, 20 tickers por
    requisição, delay ~5 min, 500k requisições/mês. No volume do Radar isso é
    1,7% da cota. Exige `BRAPI_TOKEN`.

    Falha ALTO de propósito: se alguém apontar o provedor para cá sem
    implementar, o erro diz exatamente o que falta — melhor que um provedor
    meia-boca que nunca foi exercitado contra a API real.
    """

    nome = "brapi"

    async def history(self, ticker: str, rng: str, interval: str = "1d") -> dict:
        raise NotImplementedError(
            "Provedor brapi não implementado. É o plano B do ADR-001 e exige: "
            "assinar a brapi Pro, definir BRAPI_TOKEN, mapear o payload para o "
            "formato interno (inclusive a chave da vela com horário no fuso da "
            "bolsa) e validar contra a API real antes de virar a chave."
        )


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


async def get_history(ticker: str, rng: str = "1mo", interval: str = "1d") -> dict:
    """Ponto ÚNICO de entrada de candles do app. Mesma assinatura de
    `yahoo.get_history`, para os chamadores trocarem sem cerimônia.

    A INSTRUMENTAÇÃO mora aqui, na fronteira — não dentro de um provedor. Se
    vivesse no `YahooProvider`, trocar de fonte (que é justamente o momento em
    que se quer medir) apagaria o contador e o gatilho do plano B pararia de
    existir sem ninguém notar.
    """
    t0 = time.perf_counter()
    try:
        out = await get_provider().history(ticker, rng, interval)
    except Exception:
        _registra(interval, (time.perf_counter() - t0) * 1000, 0, erro=True)
        raise
    _registra(interval, (time.perf_counter() - t0) * 1000, len(out.get("candles") or []), erro=False)
    return out
