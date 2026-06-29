"""Testa o parser de KPIs (item 1): extrai os 4 campos estruturados do JSON
que a LLM devolve, normaliza acentos/caixa e separa o texto."""
from app.kpi import parse_rich, parse_analysis, normalize_kpis


def test_extrai_kpis_e_separa_texto():
    raw = (
        '{"direcao":"Alta","conviccao":"Médio","qualidade":"Boa",'
        '"recomendacao":"Estudar alta"}\n\n'
        "A leitura mostra tendencia de alta com volume crescente..."
    )
    kpis, text = parse_analysis(raw)
    assert kpis == {
        "direcao": "Alta",
        "conviccao": "Médio",
        "qualidade": "Boa",
        "recomendacao": "Estudar alta",
    }
    assert "tendencia de alta" in text
    assert "{" not in text  # o JSON nao vaza para o texto


def test_normaliza_acento_e_caixa():
    kpis = normalize_kpis({
        "direcao": "BAIXA",
        "conviccao": "muito alto",
        "qualidade": "RUIM",
        "recomendacao": "reduzir risco",
    })
    assert kpis["direcao"] == "Baixa"
    assert kpis["conviccao"] == "Muito Alto"
    assert kpis["qualidade"] == "Ruim"
    assert kpis["recomendacao"] == "Reduzir risco"


def test_sem_json_retorna_texto_puro():
    kpis, text = parse_analysis("Cenario lateral, melhor aguardar.")
    assert kpis is None
    assert text.startswith("Cenario lateral")


def test_json_invalido_nao_quebra():
    kpis, text = parse_analysis("{ quebrado :: } analise segue aqui")
    assert kpis is None
    assert "analise segue" in text



def test_parse_rich_fatos_relevantes():
    raw = ('{"direcao":"Alta","conviccao":"Alto","qualidade":"Boa",'
           '"recomendacao":"Aguardar","resumo":"ok","fatosRelevantes":'
           '["Resultado do 2T acima do esperado","Pagamento de dividendos anunciado"],'
           '"corpo":"## Analise"}')
    r = parse_rich(raw)
    assert r["detail"]["fatos"] == ["Resultado do 2T acima do esperado", "Pagamento de dividendos anunciado"]
    # ausencia => lista vazia (compat backend antigo)
    r2 = parse_rich('{"direcao":"Alta","resumo":"x","corpo":"y"}')
    assert r2["detail"]["fatos"] == []


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("TODOS OS TESTES DE KPI PASSARAM")

def test_parse_rich_estruturado():
    raw = (
        'Prefixo {"direcao":"alta","conviccao":"media","qualidade":"boa",'
        '"recomendacao":"estudar alta",'
        '"resumo":"Alta de curto prazo.",'
        '"confirmacoes":["Acima da SMA20","MACD positivo"],'
        '"invalidacoes":["Perde 38,50"],'
        '"cuidados":["Liquidez baixa"],'
        '"stopSugerido":37.9,"alvoSugerido":"R$ 44,20"} sufixo'
    )
    from app.kpi import parse_rich
    r = parse_rich(raw)
    assert r["kpis"]["direcao"] == "Alta"
    assert r["kpis"]["recomendacao"] == "Estudar alta"
    assert r["detail"]["resumo"].startswith("Alta de curto")
    assert r["detail"]["confirmacoes"] == ["Acima da SMA20", "MACD positivo"]
    assert r["detail"]["invalidacoes"] == ["Perde 38,50"]
    assert r["detail"]["cuidados"] == ["Liquidez baixa"]
    assert r["proposal"]["stop"] == 37.9
    assert r["proposal"]["alvo"] == 44.2          # "R$ 44,20" -> 44.2
    assert "{" not in r["text"]                   # JSON nao vaza


def test_parse_rich_json_com_chaves_aninhadas():
    # garante que a extracao respeita objeto balanceado (nao corta no 1o '}')
    raw = '{"direcao":"baixa","conviccao":"alto","qualidade":"regular","recomendacao":"vender","extra":{"a":1,"b":2},"resumo":"ok"}'
    from app.kpi import parse_rich
    r = parse_rich(raw)
    assert r["kpis"]["direcao"] == "Baixa"
    assert r["detail"]["resumo"] == "ok"

def test_parse_rich_markdown_robusto():
    from app.kpi import parse_rich
    # JSON embrulhado em cercas + texto ao redor (o caso do bug do mobile)
    raw = ('Segue a analise: ```json\n'
           '{"direcao":"alta","conviccao":"alto","qualidade":"boa","recomendacao":"comprar",'
           '"corpo":"## Leitura\\n- ponto 1"}\n``` fim')
    r = parse_rich(raw)
    assert r["kpis"]["direcao"] == "Alta"
    assert r["markdown"].startswith("## Leitura")
    # sem 'corpo' -> markdown sintetizado a partir de resumo/listas, nunca vazio
    r2 = parse_rich('{"recomendacao":"aguardar","resumo":"Indefinido.","cuidados":["risco"]}')
    assert "Indefinido." in r2["markdown"] and "risco" in r2["markdown"]
    # sem JSON algum -> markdown = texto bruto, nunca vazio, sem quebrar
    r3 = parse_rich("texto solto")
    assert r3["markdown"] == "texto solto" and r3["kpis"] is None
    # lixo total -> ainda devolve estrutura com markdown nao-vazio
    r4 = parse_rich("")
    assert isinstance(r4["markdown"], str) and len(r4["markdown"]) > 0
