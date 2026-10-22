"""Fase 50 (50-07) — D-10/D-18: a IA explica os marcos do motor; nenhum número
dela vira proposta aplicável e ela não recebe número concorrente."""
from app import kpi, llm


def test_format_sem_stop_alvo_da_ia():
    for fmt in (llm.FORMAT, llm.FORMAT_PRO):
        assert "stopSugerido" not in fmt and "alvoSugerido" not in fmt
        assert "MARCOS DO MOTOR" in fmt


def test_parse_carteira_legado_descarta_numeros():
    raw = ('[{"ativo":"PETR4","precoAtual":100.0,"stop":95.0,"alvo":105.0,'
           '"explicacao":"x","operar":false,'
           '"cenarios":[{"perfil":"moderado","stop":95.0,"alvo":105.0}]}]')
    r = llm.parse_carteira(raw, "PETR4")
    assert r["proposal"] is None
    assert r["numerosIaDescartados"] is True
    assert r["operar"] is False          # parecer preservado, nunca veto
    assert "cenarios" not in r


def test_parse_carteira_novo_formato_nao_marca_descarte():
    raw = '[{"ativo":"PETR4","operar":true,"explicacao":"e","riscos":["r"],"quandoRevisar":"q"}]'
    r = llm.parse_carteira(raw, "PETR4")
    assert r["numerosIaDescartados"] is False
    assert r["riscos"] == ["r"] and r["quandoRevisar"] == "q"


def test_parse_rich_ignora_stop_alvo_da_ia():
    r = kpi.parse_rich('{"recomendacao":"Estudar alta","corpo":"x",'
                       '"stopSugerido":36.0,"alvoSugerido":43.0}')
    assert r["proposal"] == {"stop": None, "alvo": None}
