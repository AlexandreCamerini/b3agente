"""qa/44 (reporte do Alex) — a análise vinha "completamente desformatada" com
outra LLM. Causa: normalize_markdown só era aplicado no N2; deep/carteira
saíam no dialeto cru, e \n LITERAL virava um bloco só. Guardião: normalização
model-agnostic aplicada em TODOS os caminhos + \n/\t literais desescapados.
"""
from app import kpi


def test_normalize_desescapa_n_literal():
    # \n LITERAL (dois caracteres) → quebra real (senão vira um bloco só)
    raw = "Resumo executivo.\\n\\n## Cenários\\n- alta\\n- baixa"
    out = kpi.normalize_markdown(raw)
    assert "\\n" not in out
    assert out.count("\n") >= 3
    assert "## Cenários" in out


def test_normalize_dialetos_de_qualquer_llm():
    # ***triplo*** e __bold__ → **bold**; link → texto; ~~riscado~~ → texto
    assert kpi.normalize_markdown("***x***") == "**x**"
    assert kpi.normalize_markdown("__y__") == "**y**"
    assert kpi.normalize_markdown("veja [aqui](http://x)") == "veja aqui"
    assert kpi.normalize_markdown("~~z~~") == "z"


def test_normalize_nao_quebra_texto_limpo():
    limpo = "## Título\n\nParágrafo com **negrito** e *itálico*.\n- item"
    assert kpi.normalize_markdown(limpo) == limpo


def test_deep_normaliza_campos_de_texto(monkeypatch):
    """analyze_deep agora normaliza resumo/leitura/cenários/riscos/invalidação
    (antes só o N2 passava por normalize_markdown)."""
    import asyncio
    from app import llm
    raw = ('{"resumo":"Decisão.\\\\n\\\\n__forte__","planoEstudo":"Monitorar",'
           '"confianca":"baixa","leituraSetups":[{"setup":"IFR2","leitura":"***vira***"}],'
           '"cenarios":{"alta":"[x](http://y)","baixa":"b","neutro":"n"},'
           '"riscos":["~~r~~"],"invalidacao":"abaixo de 10"}')

    async def fake(config, key, system, user, max_tokens):
        return raw
    monkeypatch.setattr(llm, "_call_llm", fake)
    monkeypatch.setattr(llm, "resolve_key", lambda c: "k")
    d = asyncio.run(llm.analyze_deep({}, {}, "PETR4", {"snapshotId": "x"}, {}, modo="estudo"))
    assert "\\n" not in d["resumo"] and "**forte**" in d["resumo"]
    assert d["leituraSetups"][0]["leitura"] == "**vira**"
    assert d["cenarios"]["alta"] == "x"        # link virou texto
    assert d["riscos"][0] == "r"               # strike removido


def test_carteira_normaliza_explicacao():
    from app import llm
    raw = '[{"ativo":"PETR4","explicacao":"Base.\\\\n\\\\n__ok__","operar":true,"stop":9,"alvo":11}]'
    r = llm.parse_carteira(raw, "PETR4")
    assert "\\n" not in r["explicacao"] and "**ok**" in r["explicacao"]


if __name__ == "__main__":
    test_normalize_desescapa_n_literal()
    test_normalize_dialetos_de_qualquer_llm()
    test_normalize_nao_quebra_texto_limpo()
    test_carteira_normaliza_explicacao()
    print("ok (deep test precisa de pytest/monkeypatch)")
