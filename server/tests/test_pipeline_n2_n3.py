"""FASE 1.4 — N2 (famílias/padrões/dataQuality no contexto) e N3 (cenários)."""
from app import llm, technical_models


def _candles(n=80, up=True):
    out = []
    for i in range(n):
        base = 10 + (i * 0.1 if up else -i * 0.05)
        out.append({"date": f"2026-01-{(i % 28) + 1:02d}", "open": base, "high": base + 0.3,
                    "low": base - 0.2, "close": base + 0.1, "volume": 1000 + i})
    return out


def test_build_context_tem_familias_padroes_e_dataquality():
    ctx = technical_models.build_context("TESTE3", None, _candles(80), model="completo", tail_n=80)
    fam = ctx.get("families")
    assert fam and all(k in fam for k in ("tendencia", "momentum", "volatilidade", "priceAction", "volume"))
    conf = fam["confluenciaEntreFamilias"]
    assert conf["viesDominante"] in ("alta", "baixa", "neutro") and "sintese" in conf
    assert fam["tendencia"].get("adx14") is not None                  # ADX integrado (1.2)
    assert isinstance(ctx.get("priceActionPatterns"), list)
    dq = ctx["dataQuality"]
    assert dq["multiTimeframe"] is False and dq["tetoConfianca"] == "moderada"


def test_dataquality_serie_curta_baixa_confianca():
    ctx = technical_models.build_context("TESTE3", None, _candles(15), model="completo", tail_n=15)
    assert ctx["dataQuality"]["serieCurta"] and ctx["dataQuality"]["estruturaSemConfianca"]
    assert ctx["dataQuality"]["tetoConfianca"] == "baixa"


def test_padrao_engolfo_alta_detectado():
    cs = _candles(30)
    cs[-2].update({"open": 12.0, "close": 11.6, "high": 12.1, "low": 11.5})   # baixa
    cs[-1].update({"open": 11.55, "close": 12.2, "high": 12.3, "low": 11.5})  # alta que envolve
    pats = technical_models._candle_patterns(cs)
    assert any(p["padrao"] == "Engolfo de alta" for p in pats)


def test_parse_carteira_extrai_cenarios_e_marca_rr_desfavoravel():
    raw = """[{"ativo":"PETR4","operar":true,"stop":36.3,"alvo":41.1,"precoAtual":38.3,
      "explicacao":"leitura de estudo",
      "cenarios":[
        {"perfil":"conservador","stop":37.0,"alvo":40.0,"riscoRetorno":1.31,
         "memoriaCalculo":"stop = minima local 37,50 - 0,5xATR"},
        {"perfil":"moderado","stop":36.3,"alvo":41.1,"riscoRetorno":1.4},
        {"perfil":"agressivo","stop":35.8,"alvo":43.0,"riscoRetorno":1.88},
        {"perfil":"invalido","stop":1,"alvo":2}],
      "modelosUtilizados":[{"nome":"ATR","oQueE":"amplitude media","oQueMede":"volatilidade","limitacoes":"defasado"}]}]"""
    res = llm.parse_carteira(raw, "PETR4")
    assert res["proposal"] == {"stop": 36.3, "alvo": 41.1}
    assert len(res["cenarios"]) == 3                                   # perfil inválido descartado
    cons = next(c for c in res["cenarios"] if c["perfil"] == "conservador")
    assert cons["rrDesfavoravel"] is True and "minima local" in cons["memoriaCalculo"]
    agr = next(c for c in res["cenarios"] if c["perfil"] == "agressivo")
    assert agr["rrDesfavoravel"] is False
    assert res["modelosUtilizados"][0]["nome"] == "ATR"


def test_parse_carteira_sem_cenarios_segue_compativel():
    raw = '[{"ativo":"VALE3","operar":true,"stop":60.0,"alvo":66.0,"explicacao":"x"}]'
    res = llm.parse_carteira(raw, "VALE3")
    assert res["proposal"] == {"stop": 60.0, "alvo": 66.0} and res["cenarios"] == []
