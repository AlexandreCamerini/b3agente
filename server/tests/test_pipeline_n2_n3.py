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
    # Fase 50 / D-10: stop/alvo/cenarios da IA são DESCARTADOS (o motor é a
    # fonte do número). Segue extraído: modelosUtilizados e a marca de descarte.
    assert res["proposal"] is None
    assert "cenarios" not in res and res["numerosIaDescartados"] is True
    assert res["modelosUtilizados"][0]["nome"] == "ATR"


def test_parse_carteira_sem_cenarios_segue_compativel():
    raw = '[{"ativo":"VALE3","operar":true,"stop":60.0,"alvo":66.0,"explicacao":"x"}]'
    res = llm.parse_carteira(raw, "VALE3")
    # Fase 50 / D-10: número da IA não vira proposta.
    assert res["proposal"] is None and res["numerosIaDescartados"] is True


def test_parse_carteira_operar_false_NAO_apaga_os_niveis_de_protecao():
    """Decisão do Alex (10/08/2026): o usuário nunca é proibido de usar stop.

    Antes, `operar: false` fazia o parse ZERAR stop/alvo — e o N3 roda sobre
    posição que a pessoa já carrega: sair do modal sem o nível de proteção
    deixa a posição MAIS exposta. O parecer da IA continua no payload
    (`operar`), mas os números passam sempre.
    """
    raw = ('[{"ativo":"PETR4","operar":false,"stop":36.3,"alvo":41.1,'
           '"precoAtual":38.3,"explicacao":"R:R abaixo do minimo — aguardar"}]')
    res = llm.parse_carteira(raw, "PETR4")
    assert res["operar"] is False, "o parecer da IA tem que continuar visível"
    # Fase 50 / D-10: o parser não carrega mais número; a garantia "operar=false
    # não veta o stop" passa a ser da ROTA, que devolve os marcos do motor
    # sempre (ver test_marcos_ia.py). Aqui: o parecer segue visível.
    assert res["proposal"] is None and res["numerosIaDescartados"] is True


def test_ui_do_stop_alvo_nunca_bloqueia_o_aplicar_pelo_parecer():
    """Guardião da camada de UI (mesmo padrão dos demais guardiões de fonte)."""
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[2] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")
    # Nota (Fase 50, D-17, plano 50-09): `canApply` deixou de existir — o
    # Aplicar do StopAlvoModal ficou SEM `disabled` nenhum (sempre habilitado;
    # recusa de geometria vem do motor e aparece no modal). A garantia que este
    # guardião protege — o parecer da IA nunca bloqueia o Aplicar — fica mais
    # forte: o botão `onClick={apply}` não pode ganhar `disabled=`.
    import re as _re
    botoes = _re.findall(r"<button onClick=\{apply\}[^>]*>", src)
    assert botoes, "botão Aplicar do StopAlvoModal não encontrado"
    assert all("disabled=" not in b for b in botoes), \
        "o Aplicar voltou a ser desabilitado pelo parecer da IA"
    assert "aguardar ? null :" not in src, \
        "os números voltaram a ser suprimidos quando a IA desaconselha"
    assert "definir stop é sempre uma opção sua" in src, \
        "o parecer tem que virar AVISO visível, não bloqueio silencioso"
