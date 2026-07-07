"""Normalizacao e validacao de tickers da B3 — logica PURA e testavel.

Sem dependencia de FastAPI/httpx, para rodar no pytest do container. A EXISTENCIA
do ticker e sempre confirmada pelo Yahoo Finance (camada yahoo.py); aqui ficam
apenas a normalizacao da entrada do usuario e a classificacao do resultado.
"""
import re

# Formato tipico da B3: 4 letras + 1 a 2 digitos (PETR4, VALE3, BPAC11, TAEE11).
_B3_SHAPE = re.compile(r"^[A-Z]{4}\d{1,2}$")


def normalize_ticker(s: str) -> str:
    """Remove espacos, deixa MAIUSCULO e retira o sufixo .SA, mantendo so A-Z0-9.
    Ex.: 'petr4 ' -> 'PETR4'; 'PETR4.SA' -> 'PETR4'; '  vale3 ' -> 'VALE3'."""
    s = re.sub(r"\s+", "", (s or "").upper())
    s = s.replace(".SA", "")
    return re.sub(r"[^A-Z0-9]", "", s)


def yahoo_symbol(t: str) -> str:
    """Aplica o sufixo .SA UMA unica vez (entrada ja normalizada, sem .SA)."""
    t = normalize_ticker(t)
    return t + ".SA" if t else ""


def looks_like_b3(t: str) -> bool:
    """Heuristica de formato (nao e a fonte de verdade; so melhora mensagens)."""
    return bool(_B3_SHAPE.match(t or ""))


def validation_outcome(quote, transient_error: bool = False) -> dict:
    """Classifica o resultado da consulta ao Yahoo.
    - transient_error=True  -> {'status': 'unavailable'} (429/timeout/etc.)
    - cotacao com preco real -> {'status': 'ok', t, n, price, change}
    - caso contrario         -> {'status': 'not_found'}
    """
    if transient_error:
        return {"status": "unavailable"}
    if quote and quote.get("price") is not None:
        t = normalize_ticker(quote.get("t") or "")
        return {
            "status": "ok",
            "t": t,
            "n": (quote.get("name") or "").strip() or t,
            "price": quote.get("price"),
            "change": quote.get("change"),
        }
    return {"status": "not_found"}
