"""qa/40 — reporte do Alex: "continua mostrando Estudar alta/baixa no perfil
operador" + "modelos proibidos de inventar textos ou números".

Tranca: (a) o caminho legado /api/analyze também fala a língua da mesa;
(b) sanidade dos números devolvidos pelo modelo (nível <=0, stop==alvo ou
geometria incoerente com a direção declarada → None, nunca número inventado).
O lado do CLIENTE (pills de veredito → decisão do plano) tem guardião próprio
em web/tests/test_decisao_modo.mjs.
"""
import asyncio

from app import kpi, llm


def _fake_llm(raw):
    async def call(config, key, system, user, max_tokens):
        return raw
    return call


RAW_EDU = ('{"direcao":"Alta","conviccao":"Muito Alto","qualidade":"Boa",'
           '"recomendacao":"Estudar alta","resumo":"x","corpo":"x",'
           '"stopSugerido":36.0,"alvoSugerido":43.0}')


def test_analyze_legado_fala_a_lingua_da_mesa(monkeypatch):
    """O /api/analyze (Watchlist/Mercado) era SEMPRE educacional — no operador
    devolvia 'Estudar alta'. Agora re-mapeia pro enum PRO e usa FORMAT_PRO."""
    monkeypatch.setattr(llm, "_call_llm", _fake_llm(RAW_EDU))
    monkeypatch.setattr(llm, "resolve_key", lambda cfg: "k")
    r = asyncio.run(llm.analyze({"appMode": "operador"}, {"text": "s"}, {}, {},
                                "PETR4", {"price": 38.0}, {"candles": []}))
    assert r["kpis"]["recomendacao"] == "COMPRAR"        # nunca "Estudar alta"
    assert r["kpis"]["conviccao"] == "Médio"             # teto imposto
    # e no estudo o vocabulário educacional se mantém:
    r2 = asyncio.run(llm.analyze({"appMode": "estudo"}, {"text": "s"}, {}, {},
                                 "PETR4", {"price": 38.0}, {"candles": []}))
    assert r2["kpis"]["recomendacao"] == "Estudar alta"


def test_analyze_legado_prompt_pro_no_system(monkeypatch):
    """O system do operador leva GUARDRAILS_PRO/FORMAT_PRO (piso do servidor,
    independente da skill que o cliente mandar)."""
    seen = {}

    async def spy(config, key, system, user, max_tokens):
        seen["system"] = system
        return RAW_EDU
    monkeypatch.setattr(llm, "_call_llm", spy)
    monkeypatch.setattr(llm, "resolve_key", lambda cfg: "k")
    asyncio.run(llm.analyze({"appMode": "operador"}, {"text": "skill-edu"}, {}, {},
                            "PETR4", {}, {"candles": []}))
    assert "DECISAO da mesa" in seen["system"]           # FORMAT_PRO presente
    assert "REGRAS DO SISTEMA" in seen["system"]


def test_proposta_rejeita_numeros_inventados():
    """Sanidade dos níveis do modelo: 0.0 do template, stop==alvo e geometria
    incoerente com a direção declarada viram None (sem dado, nunca inventado)."""
    # o "0.0" literal do template de FORMAT passava como proposta válida:
    r = kpi.parse_rich('{"recomendacao":"Estudar alta","direcao":"Alta",'
                       '"corpo":"x","stopSugerido":0.0,"alvoSugerido":0.0}')
    assert r["proposal"] == {"stop": None, "alvo": None}
    # alta com alvo ABAIXO do stop = número incoerente/inventado:
    r2 = kpi.parse_rich('{"recomendacao":"Estudar alta","corpo":"x",'
                        '"stopSugerido":40.0,"alvoSugerido":35.0}')
    assert r2["proposal"] == {"stop": None, "alvo": None}
    # baixa com geometria certa (alvo < stop) PASSA:
    r3 = kpi.parse_rich('{"recomendacao":"Estudar baixa","corpo":"x",'
                        '"stopSugerido":40.0,"alvoSugerido":35.0}')
    assert r3["proposal"] == {"stop": 40.0, "alvo": 35.0}
    # alta coerente PASSA:
    r4 = kpi.parse_rich('{"recomendacao":"Estudar alta","corpo":"x",'
                        '"stopSugerido":36.0,"alvoSugerido":43.0}')
    assert r4["proposal"] == {"stop": 36.0, "alvo": 43.0}


if __name__ == "__main__":
    test_proposta_rejeita_numeros_inventados()
    print("ok test_proposta_rejeita_numeros_inventados (os demais rodam via pytest)")
