"""Testes do cadastro de ativo: normalizacao da entrada e classificacao da
validacao (Yahoo como fonte de verdade). Puro/stdlib, sem rede."""
from app import tickers


def test_normaliza_espacos_e_minusculas():
    assert tickers.normalize_ticker("petr4 ") == "PETR4"
    assert tickers.normalize_ticker("  vale3 ") == "VALE3"
    assert tickers.normalize_ticker("itub4") == "ITUB4"


def test_sufixo_sa_nao_duplica_nem_falta():
    assert tickers.normalize_ticker("PETR4.SA") == "PETR4"   # remove .SA da entrada
    assert tickers.yahoo_symbol("petr4 ") == "PETR4.SA"       # aplica 1x
    assert tickers.yahoo_symbol("PETR4.SA") == "PETR4.SA"     # nao duplica
    assert tickers.yahoo_symbol("") == ""


def test_ticker_valido_e_aceito():
    # Yahoo retornou cotacao real -> aceito
    q = {"t": "PETR4", "name": "Petroleo Brasileiro", "price": 38.42, "change": 1.1}
    res = tickers.validation_outcome(q)
    assert res["status"] == "ok"
    assert res["t"] == "PETR4" and res["price"] == 38.42 and res["n"]


def test_ticker_inexistente_e_rejeitado():
    # Yahoo respondeu, mas sem preco real -> nao encontrado
    assert tickers.validation_outcome(None)["status"] == "not_found"
    assert tickers.validation_outcome({"t": "XXXX9", "price": None})["status"] == "not_found"


def test_falha_transitoria_nao_vira_inexistente():
    # 429/timeout etc. -> indisponivel (e nao 'inexistente')
    assert tickers.validation_outcome(None, transient_error=True)["status"] == "unavailable"


def test_formato_b3_para_mensagens():
    assert tickers.looks_like_b3("PETR4")
    assert tickers.looks_like_b3("BPAC11")
    assert not tickers.looks_like_b3("PETROLEO")
    assert not tickers.looks_like_b3("AAPL")


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(name, "OK")
