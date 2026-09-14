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

Correção 260914-b6p — seleção de vencimento por DATA, não pelo flag de
vencimento-no-pregão da fonte: medição de produção em 2026-09-14 (`railway
run`) achou esse flag zerado (falsy) em 100% dos itens de BBAS3 (27/27) e
PETR4 (31/31), inclusive no vencimento já passado — o filtro antigo não
filtrava nada e `escolhido` virava o primeiro item cru da lista, sem nenhuma
comparação contra hoje. Efeito: em 2026-09-14 a função escolhia `2026-09-11`
(3 dias no passado), o que fazia `_dias_ate` (`opcoes_lastreadas.py`)
computar dias NEGATIVOS e zerava toda proposta de venda coberta (Fase 14) e a
curadoria de 4 melhores (Fase 30). Decisões:
  D-01 `hoje` entra por argumento opcional, default `hoje_brt()` (offset BRT
       fixo, não `date.today()` — o container Railway roda em UTC);
  D-02 o flag de vencimento-no-pregão sai da decisão — campo não confiável
       (100% zerado em produção), mas permanece no payload cru/`_clean_contract`
       sob o mesmo nome de chave de sempre;
  D-03 `expiration` EXPLÍCITO continua honrado mesmo vencido (fechar posição
       vencida não pode ser bloqueado);
  D-04 sem nenhum vencimento futuro → degrada ANTES da segunda perna de rede
       (`get_options_chain` nunca chamado, cota não gasta à toa);
  D-05 `sorted()` defensivo — a ordem da lista é contrato de terceiro não
       documentado; "o primeiro futuro" só é o mais próximo se ordenado.
"""
from __future__ import annotations

import datetime as dt
import time
from typing import Optional

from . import mydata_budget, mydata_client
from .tickers import normalize_ticker

_OPTIONS_TTL = 300
_ERROR_TTL = 60
_cache: dict[str, tuple[float, dict]] = {}

# Fase 31 (Plano 02, Task 3): cache DEDICADO da LISTA de vencimentos,
# separado de `_cache` (que guarda payload de CADEIA). A varredura de 2
# vencimentos (D-01) chamaria `get_vencimentos` duas vezes para o MESMO
# ticker no MESMO dia — a lista é idêntica nas duas buscas — então cachear
# derruba o custo por posição de 4 para 3 requisições mydata, a diferença
# entre caber e não caber no teto de 60/min numa carteira de 15-20
# posições. Mesmo TTL de `_OPTIONS_TTL` (reusado, não um número novo).
_VENC_TTL = _OPTIONS_TTL
_venc_cache: dict[str, tuple[float, list]] = {}

# Precedente: options_provider_mock.py:31-42 (decisão 260911-dtx) — offset BRT
# fixo, nunca `dt.date.today()`: o container Railway roda em UTC e o dia
# naive vira às 21:00 BRT, desalinhando a cadeia do que o usuário vê.
BRT = dt.timezone(dt.timedelta(hours=-3))


def hoje_brt() -> dt.date:
    return dt.datetime.now(BRT).date()


MYDATA_OPTIONS_WARNING = (
    "A cadeia de opções vem do acervo oficial da B3 (COTAHIST), publicado "
    "após o fechamento do pregão. Neste momento o hub de dados não "
    "respondeu — tente novamente mais tarde."
)

MYDATA_ORCAMENTO_WARNING = (
    "A consulta à cadeia de opções foi adiada para respeitar o limite de "
    "requisições do hub de dados da B3. Tente novamente em instantes."
)

MYDATA_SEM_VENCIMENTO_FUTURO_WARNING = (
    "Não há vencimento futuro publicado para este ativo no acervo oficial "
    "da B3 — o último vencimento disponível já venceu."
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


def _primeiro_vencimento_futuro(venc: list, hoje: dt.date) -> Optional[str]:
    """Escolhe o vencimento ESTRITAMENTE futuro mais próximo de `hoje`,
    espelhando `opcoes_lastreadas._dias_ate` (mesmo padrão `dt.date.
    fromisoformat` + `try/except (TypeError, ValueError)`, item malformado é
    ignorado, nunca levanta). O flag de vencimento-no-pregão da fonte NÃO
    participa (D-02 — 100% zerado na amostra de produção). `sorted()`
    defensivo (D-05): a ordem da lista é contrato de terceiro não
    documentado."""
    candidatos: list[tuple[dt.date, str]] = []
    for v in venc:
        raw = v.get("dt_vencimento")
        try:
            d = dt.date.fromisoformat(raw)
        except (TypeError, ValueError):
            continue
        if d > hoje:
            candidatos.append((d, raw))
    if not candidatos:
        return None
    candidatos.sort(key=lambda item: item[0])
    return candidatos[0][1]


def _debita(n: int = 1) -> bool:
    """Debita `n` imediatamente antes de CADA requisição de rede — mesma
    posição que `candle_provider._debita` ocupa (nunca depois da chamada).
    Existe com este nome/forma só para dar um ponto único de monkeypatch em
    teste, espelhando `candle_provider`.

    WR-01 (09-REVIEW.md, fechado nesta correção): usa `mydata_budget.
    reservar()` — check+debit ATÔMICO — em vez de `debita()` sozinho. `_gate`
    acima é só um pré-filtro otimista (sem lock, pode ficar desatualizado
    entre threads concorrentes); este é o ponto de COMMIT de verdade, e
    devolve `False` sem debitar quando outra thread já gastou a cota entre
    o pré-filtro e agora — o chamador trata como `sem cota`, nunca prossegue
    pra rede quando `False`."""
    return mydata_budget.reservar(n)


async def _vencimentos(t: str, hoje_efetivo: dt.date) -> Optional[list]:
    """Lista de vencimentos (formato CRU do mydata, mesma forma que
    `mydata_client.get_vencimentos` devolve) cacheada por ticker/dia — Fase
    31 (Plano 02, Task 3), ver comentário de `_venc_cache` acima.

    Devolve a lista do cache quando fresca (SEM `_debita`, SEM rede);
    caso contrário reserva cota (`_debita`) e chama `mydata_client.
    get_vencimentos`. Só grava no cache quando a lista volta NÃO-vazia —
    mesma postura A-07 (`_gate`, acima): indisponibilidade não se estende
    além da causa; uma lista vazia por falha temporária não pode "travar"
    vazia pelos próximos `_VENC_TTL` segundos.

    Devolve `None` para "não consegui reservar cota" (o chamador degrada
    exatamente como o WR-01 já fazia no ponto de `_debita()` original) e
    `[]` para "fonte não publicou vencimento" (o chamador cai no
    `_empty_payload` que já existe para esse caso)."""
    key = f"{t}@{hoje_efetivo.isoformat()}"
    hit = _venc_cache.get(key)
    if hit and (time.time() - hit[0]) < _VENC_TTL:
        return hit[1]
    if not _debita():
        return None
    venc = await mydata_client.get_vencimentos(t)
    if venc:
        _venc_cache[key] = (time.time(), venc)
    return venc


async def get_options(ticker: str, expiration: Optional[str] = None,
                       hoje: Optional[dt.date] = None) -> dict:
    hoje_efetivo = hoje or hoje_brt()
    t = normalize_ticker(ticker)
    # Chave carrega o dia (D-01/D-05): "primeiro vencimento" agora depende de
    # `hoje_efetivo` — sem isso, um payload cacheado às 23:58 BRT poderia
    # servir por até 5min (TTL 300s) um vencimento que virou passado à
    # meia-noite. `expiration` explícito não muda com o dia, então mantém a
    # chave antiga (D-03).
    key = f"{t}:{expiration}" if expiration else f"{t}:first@{hoje_efetivo.isoformat()}"
    hit = _cache.get(key)
    if hit and (time.time() - hit[0]) < _OPTIONS_TTL:
        return hit[1]

    # Fase 31: o pré-filtro precisa prever quantas requisições de rede ESTA
    # chamada ainda vai fazer, não um número fixo — `_gate(1)` quando a
    # lista de vencimentos já está em cache fresco (só falta
    # `get_options_chain`), `_gate(2)` quando não está
    # (`get_vencimentos` + `get_options_chain`). Continua sendo só um
    # pré-filtro otimista (sem lock); o commit atômico continua sendo
    # `_debita()`/`reservar()`, dentro de `_vencimentos()` e antes de
    # `get_options_chain`, exatamente como antes (WR-01).
    venc_fresco_hit = _venc_cache.get(f"{t}@{hoje_efetivo.isoformat()}")
    venc_fresco = venc_fresco_hit is not None and (time.time() - venc_fresco_hit[0]) < _VENC_TTL
    motivo = _gate(1 if venc_fresco else 2)
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
        venc = await _vencimentos(t, hoje_efetivo)
        if venc is None:
            # WR-01: pré-filtro passou, mas outra thread esgotou a cota
            # entre o pré-filtro e o commit dentro de `_vencimentos()` —
            # degrada aqui, nunca toca a rede sem cota reservada de
            # verdade.
            return _empty_payload(
                ticker, expiration, MYDATA_ORCAMENTO_WARNING,
                error="sem cota mydata (60/min · 2.000/dia)")
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
            escolhido = _primeiro_vencimento_futuro(venc, hoje_efetivo)
            if escolhido is None:
                # D-04: sem nenhum vencimento futuro, degrada ANTES da
                # segunda perna de rede — a requisição de vencimentos já
                # saiu, mas `get_options_chain`/segundo `_debita()` nunca
                # rodam (o contador não infla o que não foi gasto, A-08).
                payload = _empty_payload(
                    ticker, expiration, MYDATA_SEM_VENCIMENTO_FUTURO_WARNING)
                _cache[key] = (time.time() - (_OPTIONS_TTL - _ERROR_TTL), payload)
                return payload

        if not _debita():
            # WR-01: mesma degradação do primeiro ponto de commit — a
            # requisição de vencimentos já saiu, mas a segunda perna não tem
            # cota reservada de verdade.
            return _empty_payload(
                ticker, expiration, MYDATA_ORCAMENTO_WARNING,
                error="sem cota mydata (60/min · 2.000/dia)")
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
