"""Provider mydata para cadeias de opcoes (Fase 9, Plano 03 — qa/09).

Substitui a fonte por trás do MESMO contrato `providerStatus` que o ADR-004
já define (D-02): a UI e `options_api.liquidity_gate` não mudam de forma.
IV, gregas e preço teórico vêm PRONTOS do hub (Black-Scholes resolvido do
lado do mydata, `nucleos.py:182-223`) — este módulo NÃO recalcula nada
localmente.

D-04 é explícita e vale para TODO ramo deste arquivo: se o mydata falhar
(quota, 5xx, resposta imprestável), o resultado vai DIRETO para
`providerStatus="degraded"` — NUNCA um fallback para o provedor anterior.
Reintroduzi-lo como fallback anularia o ganho desta migração: aquele
endpoint de opções é não-oficial e responde 401/403/429, exatamente a fonte
instável que esta migração elimina. O provedor anterior fica como código
histórico — alavanca de rollback manual via `options_provider.py` (Task 3),
não caminho automático.

Gate de orçamento (Fase 0/Plano 02 — achado WR-01 do `09-REVIEW.md`,
requirement OPTGATE-01): antes de qualquer chamada de rede, `_gate()`
consulta `mydata_budget.pode_gastar()` — a MESMA cota compartilhada
(60/min · 2.000/dia) que `candle_provider.py` já respeita para candles.
Três decisões divergem deliberadamente do padrão que `candle_provider`
aplica ao seu último elo (registradas em `00-02-PLAN.md`, decisões
A-05/A-06/A-07):
  • recusa DURA, nunca mole — este caminho tem UM elo só (D-04 proíbe
    fallback pro Yahoo), então "último elo" é sempre verdadeiro; se a
    recusa fosse mole aqui, o gate nunca protegeria nada, só existiria por
    existir;
  • nunca dorme esperando a janela do minuto liberar — este caminho roda
    dentro do laço assíncrono único do agente (`scheduler_loop`) e dentro
    de requisição HTTP do usuário; dormir ali é o mesmo risco concreto que
    o incidente do kill-switch já expôs (execução travada por dias com o
    heartbeat mascarando o problema);
  • a recusa por cota NUNCA é escrita em `_cache` — a janela do minuto
    libera em até 60s; cachear a recusa pelo TTL de erro (60s) ou de
    sucesso (300s) estenderia a indisponibilidade muito além da causa real.
"""
from __future__ import annotations

import time
from typing import Optional

from . import mydata_budget, mydata_client
from .tickers import normalize_ticker

_OPTIONS_TTL = 300
_ERROR_TTL = 60
_cache: dict[str, tuple[float, dict]] = {}


MYDATA_OPTIONS_WARNING = (
    "A cadeia de opções vem do acervo oficial da B3 (COTAHIST), publicado "
    "após o fechamento do pregão. Neste momento o hub de dados não "
    "respondeu — tente novamente mais tarde."
)

MYDATA_ORCAMENTO_WARNING = (
    "A consulta à cadeia de opções foi adiada para respeitar o limite de "
    "requisições do hub de dados da B3. Tente novamente em instantes."
)


def _empty_payload(ticker: str, expiration: Optional[str], warning: str, error: Optional[str] = None) -> dict:
    symbol = normalize_ticker(ticker)
    payload = {
        "ticker": ticker,
        "symbol": symbol,
        "expirations": [],
        "expiration": expiration,
        "calls": [],
        "puts": [],
        "source": "mydata",
        "providerStatus": "degraded",
        "warning": warning,
    }
    if error:
        payload["providerError"] = error
    return payload


def _clean_contract(raw: dict, spot: Optional[float]) -> dict:
    """Mapeia uma linha crua de `gold_opcoes` para o contrato do ADR-004,
    mais os campos ADITIVOS que o contrato antigo não tinha (gregas, preço
    teórico, status da IV, proveniência do vencimento). Aditivo, nunca
    substitutivo: nenhuma chave do contrato antigo é removida."""
    strike = raw.get("strike")
    option_type = str(raw.get("tipo") or "").lower()
    dist = None
    if isinstance(spot, (int, float)) and spot > 0 and isinstance(strike, (int, float)):
        dist = round((float(strike) - float(spot)) / float(spot) * 100, 2)
    in_the_money = False
    if isinstance(spot, (int, float)) and spot > 0 and isinstance(strike, (int, float)):
        if option_type == "call":
            in_the_money = spot > strike
        elif option_type == "put":
            in_the_money = spot < strike
    return {
        "contractSymbol": raw.get("contrato"),
        "optionType": option_type,
        "strike": strike,
        "lastPrice": raw.get("premio"),
        "bid": raw.get("melhor_oferta_compra"),
        "ask": raw.get("melhor_oferta_venda"),
        "change": None,  # COTAHIST não publica variação do contrato
        "percentChange": None,
        "volume": raw.get("quantidade_negociada") or 0,
        "openInterest": None,  # SEM FONTE — B3/gold_opcoes não publicam
        "impliedVolatility": raw.get("volatilidade_implicita"),  # nulo é legítimo
        "inTheMoney": in_the_money,
        "currency": "BRL",
        "distancePct": dist,
        # -- aditivos (ganho da migração; nenhum existia no contrato Yahoo) --
        "ivStatus": raw.get("situacao_sigma"),
        "theoreticalPrice": raw.get("preco_teorico"),
        "greeks": {
            "delta": raw.get("delta"),
            "gamma": raw.get("gamma"),
            "vega": raw.get("vega"),
            "theta": raw.get("theta"),
            "rho": raw.get("rho"),
        },
        "expiration": raw.get("dt_vencimento"),
        "riskFreeRate": raw.get("taxa_livre_risco"),
        "exerciseStyle": raw.get("estilo_exercicio"),
    }


def _gate(n: int = 2) -> Optional[str]:
    """Decide, SEM tocar a rede, se há cota para gastar `n` agora.

    Devolve `None` quando há vaga; devolve a string `"sem cota"` quando não
    há. WR-01 (`09-REVIEW.md`) / decisão A-05 (`00-02-PLAN.md`): aqui a
    recusa é DURA — ao contrário do último elo de `candle_provider._gate`,
    que serve mesmo sem cota porque tem alternativa nenhuma sobrando. Em
    opções não existe alternativa (D-04 proíbe fallback pro Yahoo) e o
    caminho tem UM elo só, então "último elo" é sempre verdadeiro: se a
    recusa fosse mole aqui, o gate nunca protegeria nada — seria escrevê-lo
    e desligá-lo na mesma linha. Sem cota, o resultado correto é degradar
    (o mesmo estado que `agent._avaliar_opcoes` já ignora sem travar o
    ciclo), não servir.
    """
    if not mydata_budget.pode_gastar(n):
        return "sem cota"
    return None


def _debita(n: int = 1) -> None:
    """Debita `n` imediatamente antes de CADA requisição de rede — mesma
    posição que `candle_provider._debita` ocupa (nunca depois da chamada).
    Existe com este nome/forma só para dar um ponto único de monkeypatch em
    teste, espelhando `candle_provider`."""
    mydata_budget.debita(n)


async def get_options(ticker: str, expiration: Optional[str] = None) -> dict:
    t = normalize_ticker(ticker)
    key = f"{t}:{expiration or 'first'}"
    hit = _cache.get(key)
    if hit and (time.time() - hit[0]) < _OPTIONS_TTL:
        return hit[1]

    motivo = _gate(2)
    if motivo is not None:
        # A-07: recusa por cota NÃO é escrita em `_cache` — a janela do
        # minuto libera em até 60s; cachear pelo TTL de sucesso (300s) ou
        # de erro (60s) estenderia a indisponibilidade além da causa real.
        # Um leitor futuro tenderia a "consertar" essa ausência de cache —
        # não é esquecimento, é a decisão A-07.
        return _empty_payload(
            ticker, expiration, MYDATA_ORCAMENTO_WARNING,
            error="sem cota mydata (60/min · 2.000/dia)")

    try:
        _debita()
        venc = await mydata_client.get_vencimentos(t)
        if not venc:
            payload = _empty_payload(
                ticker, expiration,
                "Nenhum pregão publicado com opções para este ativo no "
                "acervo oficial da B3.")
            _cache[key] = (time.time() - (_OPTIONS_TTL - _ERROR_TTL), payload)
            return payload

        expirations = [v.get("dt_vencimento") for v in venc]

        if expiration:
            if expiration not in expirations:
                # Saída antecipada: só a requisição de vencimentos saiu —
                # o contador não infla o que não foi gasto (decisão A-08).
                payload = _empty_payload(
                    ticker, expiration,
                    f"Vencimento {expiration} não está disponível para este "
                    "ativo no pregão atual — a lista de vencimentos vem do "
                    "endpoint dedicado do mydata.")
                _cache[key] = (time.time() - (_OPTIONS_TTL - _ERROR_TTL), payload)
                return payload
            escolhido = expiration
        else:
            nao_vence_hoje = [v for v in venc if not v.get("vence_no_pregao")]
            escolhido = (nao_vence_hoje[0] if nao_vence_hoje else venc[0]).get("dt_vencimento")

        _debita()
        linhas = await mydata_client.get_options_chain(t, vencimento=escolhido)

        spot = None
        for row in linhas:
            if row.get("preco_objeto") is not None:
                spot = row.get("preco_objeto")
                break
        pregao = linhas[0].get("dt_pregao") if linhas else None
        provenance = linhas[0].get("proveniencia") if linhas else None

        calls = []
        puts = []
        for row in linhas:
            contrato = _clean_contract(row, spot)
            if contrato["optionType"] == "call":
                calls.append(contrato)
            elif contrato["optionType"] == "put":
                puts.append(contrato)

        payload = {
            "ticker": ticker,
            "symbol": t,
            "source": "mydata",
            "providerStatus": "ok",
            "underlyingPrice": spot,
            "currency": "BRL",
            "expirations": expirations,
            "expiration": escolhido,
            "calls": calls,
            "puts": puts,
            "pregao": pregao,
        }
        if provenance:
            payload["provenance"] = provenance
        _cache[key] = (time.time(), payload)
        return payload
    except Exception as e:  # noqa: BLE001 — D-04: falha vira degradado, NUNCA Yahoo
        payload = _empty_payload(ticker, expiration, MYDATA_OPTIONS_WARNING, str(e))
        _cache[key] = (time.time() - (_OPTIONS_TTL - _ERROR_TTL), payload)
        return payload
