"""Catalogo fixo de 20 blue chips da B3. Yahoo usa o sufixo .SA."""

CATALOG = [
    {"t": "PETR4", "n": "Petrobras PN"},
    {"t": "PETR3", "n": "Petrobras ON"},
    {"t": "VALE3", "n": "Vale ON"},
    {"t": "ITUB4", "n": "Itau Unibanco PN"},
    {"t": "BBDC4", "n": "Bradesco PN"},
    {"t": "BBAS3", "n": "Banco do Brasil ON"},
    {"t": "B3SA3", "n": "B3 ON"},
    {"t": "ABEV3", "n": "Ambev ON"},
    {"t": "WEGE3", "n": "WEG ON"},
    {"t": "ELET3", "n": "Eletrobras ON"},
    {"t": "RENT3", "n": "Localiza ON"},
    {"t": "PRIO3", "n": "PRIO ON"},
    {"t": "SUZB3", "n": "Suzano ON"},
    {"t": "EQTL3", "n": "Equatorial ON"},
    {"t": "RADL3", "n": "Raia Drogasil ON"},
    {"t": "VIVT3", "n": "Telefonica Brasil (Vivo) ON"},
    {"t": "ITSA4", "n": "Itausa PN"},
    {"t": "JBSS3", "n": "JBS ON"},
    {"t": "BPAC11", "n": "BTG Pactual UNT"},
    {"t": "RDOR3", "n": "Rede D'Or ON"},
]

CATALOG_TICKERS = [c["t"] for c in CATALOG]


def is_catalog_ticker(t: str) -> bool:
    return t in CATALOG_TICKERS


def name_of(t: str) -> str:
    for c in CATALOG:
        if c["t"] == t:
            return c["n"]
    return t


def yahoo_symbol(t: str) -> str:
    t = (t or "").upper().replace(".SA", "").strip()
    return t + ".SA" if t else ""
