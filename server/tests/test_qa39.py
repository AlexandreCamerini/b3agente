"""qa/39 — Guardiões da revisão final de QA (operador sênior).

Cada teste tranca um bug CONFIRMADO na revisão pré-release (3 revisores +
verificação adversarial). Reproduções originais no relatório qa/39.
"""
import asyncio

from app import analysis_outcomes as ao
from app import indicators, kpi, llm, setups


# ===== setups.py — geometria do plano =====

def test_plano_rejeita_alvo_do_lado_errado():
    """P1: abs() no R:R mascarava COMPRA com alvo2 ABAIXO do stop (rr2 1,6
    'positivo' para plano absurdo)."""
    s = {"nome": "X", "lado": "alta", "gatilho": 100.0, "invalidacao": 95.0,
         "alvoSugerido": 92.0}
    p = setups.plano_operacional(s)
    assert p["decisao"] == setups.DECISAO_NAO_OPERAR
    assert "incoerente" in p["motivo"]


def test_plano_rejeita_alvo_negativo_na_venda():
    """P2: venda com stop largo em papel barato projetava alvo2 NEGATIVO
    (gatilho 2,00 / stop 3,50 → alvo2 −1,00) — número fisicamente impossível."""
    s = {"nome": "X", "lado": "baixa", "gatilho": 2.0, "invalidacao": 3.5}
    p = setups.plano_operacional(s)
    assert p["decisao"] == setups.DECISAO_NAO_OPERAR


def test_plano_alvo1_e_1r_da_entrada_real():
    """P2: na entrada a mercado o alvo1 ficava ancorado no gatilho (0,43R da
    entrada real) enquanto o motivo prometia 'parcial em 1R'."""
    s = {"nome": "X", "lado": "alta", "gatilho": 100.0, "invalidacao": 95.0,
         "alvoSugerido": 115.0}
    p = setups.plano_operacional(s, close=102.0)  # rompido, dentro da zona
    assert p["decisao"] == setups.DECISAO_COMPRAR
    assert p["entrada"] == 102.0
    assert p["alvo1"] == 109.0            # entrada + risco_real (102−95=7)
    assert abs(p["rr1"] - 1.0) < 1e-9      # a promessa "1R" agora é verdadeira
    # e sem close (entrada no gatilho) o comportamento clássico se mantém:
    p2 = setups.plano_operacional(s)
    assert p2["alvo1"] == 105.0 and abs(p2["rr1"] - 1.0) < 1e-9


def test_plano_do_resultado_prefere_direcional_com_niveis():
    """P2: setup legado sem gatilho no topo do ranking derrubava o plano em
    NÃO OPERAR mesmo havendo um 9.1 executável logo abaixo."""
    sres = {"setups": [
        {"nome": "Pullback à média", "lado": "alta", "confluencia": 100},  # sem níveis
        {"nome": "Setup 9.1", "lado": "alta", "confluencia": 86,
         "gatilho": 100.0, "invalidacao": 95.0, "alvoSugerido": 112.0},
    ]}
    p = setups.plano_do_resultado(sres)
    assert p["decisao"] == setups.DECISAO_COMPRAR and p["setup"] == "Setup 9.1"


# ===== indicators.py =====

def test_rsi_serie_flat_e_neutro():
    """P2: série flat (ganho=0 e perda=0) marcava RSI 100 ('sobrecomprado')
    num papel parado — convenção correta é neutro (50)."""
    out = indicators.rsi([100.0] * 20, 14)
    assert out[-1] == 50.0
    # só ganhos continua 100; só perdas continua 0 (comportamento clássico)
    sobe = [100.0 + i for i in range(20)]
    desce = [100.0 - i for i in range(20)]
    assert indicators.rsi(sobe, 14)[-1] == 100.0
    assert indicators.rsi(desce, 14)[-1] == 0.0


# ===== analysis_outcomes.py =====

def test_avaliar_entry_expiracao_sem_close_mantem_pendente():
    """P2 robustez: candle de expiração sem close (dado sujo) levantava
    TypeError — agora mantém pendente."""
    entry = {"criadoEm": "2026-07-01T12:00:00+00:00", "prazoPregoes": 3,
             "stopProposto": 95.0, "alvoProposto": 110.0, "precoNaAnalise": 100.0}
    candles = [
        {"date": f"2026-07-0{d}", "high": 101.0, "low": 99.0, "close": 100.0}
        for d in (2, 3)
    ] + [{"date": "2026-07-04", "high": 101.0, "low": 99.0, "close": None}]
    assert ao._avaliar_entry(entry, candles) is None  # pendente, sem crash


# ===== llm.py / kpi.py — enforcement dos prompts =====

def _fake_llm(raw):
    async def call(config, key, system, user, max_tokens):
        return raw
    return call


def test_n2_operador_vocabulario_da_mesa(monkeypatch):
    """P1-1: FORMAT_PRO pedia COMPRAR/VENDER/AGUARDAR CONFIRMAÇÃO mas a
    normalização educacional reescrevia/derrubava — a decisão da mesa nunca
    chegava à UI."""
    raw = ('{"direcao":"Alta","conviccao":"Baixo","qualidade":"Boa",'
           '"recomendacao":"AGUARDAR CONFIRMAÇÃO","resumo":"x","corpo":"x",'
           '"stopSugerido":10.0,"alvoSugerido":12.0}')
    monkeypatch.setattr(llm, "_call_llm", _fake_llm(raw))
    monkeypatch.setattr(llm, "resolve_key", lambda cfg: "k")
    r = asyncio.run(llm.analyze_structured({}, {"text": "s"}, {}, {}, "PETR4",
                                           {"dataQuality": {"multiTimeframe": False}},
                                           modo="operador"))
    assert r["kpis"]["recomendacao"] == "AGUARDAR CONFIRMAÇÃO"
    # e COMPRAR não vira mais "Estudar alta" na mesa:
    raw2 = raw.replace("AGUARDAR CONFIRMAÇÃO", "COMPRAR")
    monkeypatch.setattr(llm, "_call_llm", _fake_llm(raw2))
    r2 = asyncio.run(llm.analyze_structured({}, {"text": "s"}, {}, {}, "PETR4",
                                            {"dataQuality": {"multiTimeframe": False}},
                                            modo="operador"))
    assert r2["kpis"]["recomendacao"] == "COMPRAR"


def test_n2_teto_de_conviccao_sem_segundo_timeframe(monkeypatch):
    """P1-2: 'Muito Alto' passava direto no N2 — o teto só existia no N1."""
    raw = ('{"direcao":"Alta","conviccao":"Muito Alto","qualidade":"Boa",'
           '"recomendacao":"Estudar alta","resumo":"x","corpo":"x",'
           '"stopSugerido":10.0,"alvoSugerido":12.0}')
    monkeypatch.setattr(llm, "_call_llm", _fake_llm(raw))
    monkeypatch.setattr(llm, "resolve_key", lambda cfg: "k")
    r = asyncio.run(llm.analyze_structured({}, {"text": "s"}, {}, {}, "PETR4",
                                           {"dataQuality": {"multiTimeframe": False}},
                                           modo="estudo"))
    assert r["kpis"]["conviccao"] == "Médio"


def test_parse_carteira_recomputa_rr():
    """P1-3: o gate de R:R usava o valor DECLARADO pelo modelo — declarar 2,0
    com números que dão 1,0 passava limpo."""
    raw = ('[{"ativo":"PETR4","precoAtual":100.0,"stop":95.0,"alvo":105.0,'
           '"explicacao":"x","operar":true,'
           '"cenarios":[{"perfil":"moderado","stop":95.0,"alvo":105.0,'
           '"riscoRetorno":2.0,"memoriaCalculo":"m"}]}]')
    r = llm.parse_carteira(raw, "PETR4")
    c = r["cenarios"][0]
    assert c["riscoRetorno"] == 1.0        # recomputado: |105−100|/|100−95|
    assert c["rrDesfavoravel"] is True     # < 1,5 → gate acende


def test_n3_estudo_tem_guardrails_e_maps_conhecem_enum_pro():
    """P1-4 (estático): o system do N3 estudo ganha GUARDRAILS do servidor;
    e o mapa intermediário conhece 'aguardar confirmacao'."""
    import inspect
    src = inspect.getsource(llm.analyze_carteira)
    assert 'else ("\\n\\n" + GUARDRAILS)' in src
    assert kpi._MAPS["recomendacao"]["aguardar confirmacao"] == "Aguardar"
    # default seguro da confiança no N1 é "baixa" (teto não é piso)
    src2 = inspect.getsource(llm.analyze_deep)
    assert 'else "baixa"' in src2


if __name__ == "__main__":
    import sys
    ok = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                if "monkeypatch" in fn.__code__.co_varnames:
                    continue  # precisa do pytest
                fn()
                ok += 1
                print("ok", name)
            except Exception as e:  # noqa: BLE001
                print("FALHOU", name, e)
                sys.exit(1)
    print(f"{ok} teste(s) puros ok (os de monkeypatch rodam via pytest)")
