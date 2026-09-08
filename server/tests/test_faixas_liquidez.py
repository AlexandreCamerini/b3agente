"""Quick 260908-ldg (2026-09-08) — gate de liquidez em três faixas
(NEGOCIÁVEL >=55 / DIFÍCIL 30-54 / SEM MERCADO <30), com consentimento do
usuário quando a pior perna é DIFÍCIL.

Este arquivo é o guardião NOVO do bloco `<behavior>` da Task 1: a escala
centralizada (`options_quant.faixa_de_liquidez`), a seleção em duas passadas
(`opcoes_motor.rastrear`) e o bloco `proposta.liquidez` completo
(`opcoes_lastreadas.propor`/`_propor_collar`). Os testes de FÓRMULA
(`liquidity_score`) continuam em `test_liquidity_score_mydata.py`; os de
SELEÇÃO pré-existente (strike extremo, n, exclusões) continuam em
`test_opcoes_motor.py`. Aqui é só o que É NOVO: a régua de três faixas.

Fixtures reais de contratos: `contractSymbol` no comentário, valores
congelados da cadeia de produção de 2026-09-08 (os 20 JSONs originais NÃO são
versionados — só os números literais entram aqui, como em
`test_liquidity_score_mydata.py`)."""
import datetime as dt

from app import opcoes_lastreadas, opcoes_motor, skill_ref
from app.options_quant import faixa_de_liquidez, liquidity_score

_HOJE = dt.date(2026, 8, 31)
_SPOT = 30.0


# ─────────────────────────────────────────────────────────────────────────
# Parte A: options_quant.faixa_de_liquidez — a escala em si
# ─────────────────────────────────────────────────────────────────────────

def test_faixa_de_liquidez_fronteiras_exatas():
    assert faixa_de_liquidez(66.5) == "NEGOCIÁVEL"
    assert faixa_de_liquidez(55.0) == "NEGOCIÁVEL"
    assert faixa_de_liquidez(54.9) == "DIFÍCIL"
    assert faixa_de_liquidez(30.0) == "DIFÍCIL"
    assert faixa_de_liquidez(29.6) == "SEM MERCADO"


def test_faixa_de_liquidez_score_invalido_nunca_levanta_excecao():
    assert faixa_de_liquidez(None) == "SEM MERCADO"
    assert faixa_de_liquidez(-1) == "SEM MERCADO"
    assert faixa_de_liquidez("nao-e-numero") == "SEM MERCADO"
    assert faixa_de_liquidez(True) == "SEM MERCADO"  # bool é subclasse de int — exclusão explícita


def test_fixtures_reais_2026_09_08_batem_com_a_escala():
    """Sete contratos reais medidos pelo planner (measured_facts) — prova de
    que a escala não regrediu para nenhum deles."""
    casos = [
        ("ABEVI147W2", (21100, None, 1.04, 0.0), 66.5, "NEGOCIÁVEL"),
        ("PRIOI650W2", (5700, None, 0.0, 1.59), 55.1, "NEGOCIÁVEL"),
        ("ABEVI160W2", (4800, None, 0.01, 0.16), 48.6, "DIFÍCIL"),
        ("ABEVI165W2", (2000, None, 0.0, 0.0), 46.0, "DIFÍCIL"),
        ("ITSAI137W2", (400, None, 0.0, 0.0), 32.1, "DIFÍCIL"),
        ("B3SAI167W2", (300, None, 0.0, 0.0), 29.6, "SEM MERCADO"),
        ("RADLU194W2", (100, None, 0.0, 0.0), 20.1, "SEM MERCADO"),
    ]
    for symbol, args, score_esperado, faixa_esperada in casos:
        r = liquidity_score(*args)
        assert r["score"] == score_esperado, symbol
        assert faixa_de_liquidez(r["score"]) == faixa_esperada, symbol


# ─────────────────────────────────────────────────────────────────────────
# Parte B: opcoes_motor.rastrear — seleção em DUAS PASSADAS
# ─────────────────────────────────────────────────────────────────────────

def _ctr(symbol, strike, volume=5000, oi=None, bid=1.48, ask=1.52, price=1.5):
    return {"contractSymbol": symbol, "optionType": "call", "strike": strike,
            "lastPrice": price, "bid": bid, "ask": ask, "volume": volume,
            "openInterest": oi, "expiration": "2026-09-30"}


def test_rastrear_negociavel_vence_dificil_de_strike_melhor():
    """DIFÍCIL (48,6, strike 30 — o "melhor" por `criterio=min`) perde para
    NEGOCIÁVEL (66,5, strike 34) — a segunda passada nem roda."""
    dificil = _ctr("ABEVI160W2", 30, volume=4800, bid=0.01, ask=0.16)  # 48,6
    negociavel = _ctr("ABEVI147W2", 34, volume=21100, bid=1.04, ask=0.0)  # 66,5
    cadeia = {"providerStatus": "ok", "calls": [dificil, negociavel], "puts": []}
    r = opcoes_motor.rastrear(cadeia, {"tipo": "call", "criterio": "min"})
    assert [c["contractSymbol"] for c in r] == ["ABEVI147W2"]


def test_rastrear_cadeia_so_com_dificil_seleciona_pelo_criterio_de_strike():
    """Fixture "RADL3" do measured_facts: 0 NEGOCIÁVEL, 3 DIFÍCIL (46,0 /
    43,5 / 32,1) — sem a segunda passada, a cadeia inteira devolveria `[]`
    (o defeito que a Task 1 corrige). Volumes escolhidos para reproduzir os
    scores exatos reportados (sem bid/ask — mesmo caminho "sem livro" real)."""
    c46 = _ctr("RADL46", 30, volume=2000, bid=None, ask=None)   # 46,0
    c43 = _ctr("RADL43", 32, volume=1487, bid=None, ask=None)   # 43,5
    c32 = _ctr("RADL32", 34, volume=400, bid=None, ask=None)    # 32,1
    for c in (c46, c43, c32):
        assert faixa_de_liquidez(liquidity_score(c["volume"], None, None, None)["score"]) == "DIFÍCIL"
    cadeia = {"providerStatus": "ok", "calls": [c43, c32, c46], "puts": []}
    r = opcoes_motor.rastrear(cadeia, {"tipo": "call", "criterio": "min"})
    assert [c["contractSymbol"] for c in r] == ["RADL46"]  # strike 30, o menor


def test_rastrear_n3_cadeia_mista_devolve_so_os_negociaveis():
    """`n=3` numa cadeia com 2 NEGOCIÁVEL + 1 DIFÍCIL devolve só os 2 —
    NUNCA completa a lista com o DIFÍCIL, mesmo sobrando vaga."""
    n1 = _ctr("N1", 30, volume=21100, bid=1.04, ask=0.0)   # 66,5 NEGOCIÁVEL
    n2 = _ctr("N2", 32, volume=5700, bid=0.0, ask=1.59)    # 55,1 NEGOCIÁVEL
    d1 = _ctr("D1", 34, volume=4800, bid=0.01, ask=0.16)   # 48,6 DIFÍCIL
    cadeia = {"providerStatus": "ok", "calls": [n1, n2, d1], "puts": []}
    r = opcoes_motor.rastrear(cadeia, {"tipo": "call", "criterio": "min", "n": 3})
    assert [c["contractSymbol"] for c in r] == ["N1", "N2"]


def test_rastrear_cadeia_so_com_sem_mercado_devolve_lista_vazia():
    c1 = _ctr("B3SAI167W2", 30, volume=300, bid=None, ask=None)   # 29,6
    c2 = _ctr("RADLU194W2", 32, volume=100, bid=None, ask=None)   # 20,1
    cadeia = {"providerStatus": "ok", "calls": [c1, c2], "puts": []}
    r = opcoes_motor.rastrear(cadeia, {"tipo": "call", "criterio": "min"})
    assert r == []


def test_rastrear_liquidez_minima_explicita_continua_uma_passada_no_piso():
    """Override explícito NÃO vira duas passadas — mesma semântica de
    sempre, só a fonte do default que mudou."""
    c = _ctr("X", 30)  # volume 5000/1.48/1.52 => score ~79,0 (NEGOCIÁVEL)
    cadeia = {"providerStatus": "ok", "calls": [c], "puts": []}
    r = opcoes_motor.rastrear(cadeia, {"tipo": "call", "criterio": "min", "liquidez_minima": 99})
    assert r == []


# ─────────────────────────────────────────────────────────────────────────
# Parte C: opcoes_lastreadas.propor — o bloco `proposta.liquidez` completo
# ─────────────────────────────────────────────────────────────────────────

def _contrato(strike, symbol, kind, price=1.5, volume=5000, oi=None, bid=1.48, ask=1.52):
    return {"contractSymbol": symbol, "optionType": kind, "strike": strike,
            "lastPrice": price, "bid": bid, "ask": ask, "volume": volume, "openInterest": oi}


def _cadeia(calls=None, puts=None):
    exp = (_HOJE + dt.timedelta(days=30)).isoformat()
    return {"providerStatus": "ok", "underlyingPrice": _SPOT, "expiration": exp,
            "expirations": [exp], "calls": calls or [], "puts": puts or []}


def _posicao(qty=300):
    return {"t": "PETR4", "qty": qty, "qtyTravada": 0}


_PLANO_NAO_OPERAR = {"decisao": "NÃO OPERAR", "lado": None}


def test_propor_contrato_dificil_traz_as_5_chaves_com_aviso_nao_vazio():
    # ABEVI165W2 real: 2000 unidades, sem livro — score 46,0, DIFÍCIL.
    call = _contrato(32.0, "ABEVI165W2", "call", volume=2000, bid=None, ask=None)
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=[call]), _SPOT, _PLANO_NAO_OPERAR,
                                  _posicao(), 100000, "operador", _HOJE)
    liq = r["proposta"]["liquidez"]
    assert set(liq.keys()) == {"score", "faixa", "volume", "spreadPct", "aviso"}
    assert liq["faixa"] == "DIFÍCIL"
    assert liq["score"] == 46.0
    assert isinstance(liq["aviso"], str) and liq["aviso"]
    assert "46" in liq["aviso"]        # score arredondado
    assert "2.000" in liq["aviso"]     # volume pt-BR


def test_propor_contrato_negociavel_aviso_e_none_nunca_string_vazia():
    # ABEVI147W2 real: 21.100 unidades — score 66,5, NEGOCIÁVEL.
    call = _contrato(32.0, "ABEVI147W2", "call", volume=21100, bid=1.04, ask=0.0)
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=[call]), _SPOT, _PLANO_NAO_OPERAR,
                                  _posicao(), 100000, "operador", _HOJE)
    liq = r["proposta"]["liquidez"]
    assert liq["faixa"] == "NEGOCIÁVEL"
    assert liq["aviso"] is None


def test_propor_spread_pct_none_aviso_diz_sem_livro_nunca_0_por_cento():
    # ABEVI165W2 (sem livro): spreadPct é None — aviso não pode dizer "0%".
    call = _contrato(32.0, "ABEVI165W2", "call", volume=2000, bid=None, ask=None)
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=[call]), _SPOT, _PLANO_NAO_OPERAR,
                                  _posicao(), 100000, "operador", _HOJE)
    liq = r["proposta"]["liquidez"]
    assert liq["spreadPct"] is None
    assert "sem livro publicado" in liq["aviso"]
    assert "0%" not in liq["aviso"]


def test_propor_volume_zero_com_oi_alto_aviso_diz_sem_negocio_nunca_0_unidades():
    """Caminho Yahoo (rollback): `volume` ausente mas `openInterest` alto —
    "0 unidades negociadas hoje" seria FALSO (o contrato pode ter negociado
    em pregões anteriores; hoje não sabemos)."""
    call = _contrato(32.0, "YAHOO_OI", "call", volume=None, oi=3000, bid=None, ask=None)
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=[call]), _SPOT, _PLANO_NAO_OPERAR,
                                  _posicao(), 100000, "operador", _HOJE)
    liq = r["proposta"]["liquidez"]
    assert liq["faixa"] == "DIFÍCIL"
    assert "sem negócio registrado hoje" in liq["aviso"]
    assert "0 unidades" not in liq["aviso"]


def test_propor_collar_liquidez_e_volume_spread_da_perna_pior():
    """Collar cuja call é NEGOCIÁVEL e a put é DIFÍCIL: `liquidez.faixa` é a
    da PIOR perna (put), e `volume`/`spreadPct` também são os da PUT — não
    uma média nem os da call."""
    call = _contrato(32.0, "PETR4F32", "call", price=1.0, volume=10000, oi=10000,
                      bid=0.95, ask=1.05)  # 67,0 NEGOCIÁVEL
    put = _contrato(28.0, "PETR4F28", "put", price=0.9, volume=2000, oi=2000,
                     bid=0.85, ask=0.95)   # 53,0 DIFÍCIL
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=[call], puts=[put]), _SPOT,
                                  {"decisao": "VENDER", "lado": "baixa"}, _posicao(), 50,
                                  "operador", _HOJE, multiperna=True)
    colar = next(c for c in r["candidatos"] if c["tipo"] == "collar")
    liq_put_real = liquidity_score(2000, 2000, put["bid"], put["ask"])
    assert colar["liquidez"]["faixa"] == "DIFÍCIL"
    assert colar["liquidez"]["score"] == liq_put_real["score"]
    assert colar["liquidez"]["volume"] == 2000          # volume da PUT, não da call
    assert colar["liquidez"]["spreadPct"] == liq_put_real["spreadPct"]


# ─────────────────────────────────────────────────────────────────────────
# Parte D: skill_ref — paridade da frase de consentimento
# ─────────────────────────────────────────────────────────────────────────

def test_liquidez_dificil_existe_nos_dois_modos_e_difere():
    operador = skill_ref.OPCOES_LASTREADAS["operador"]["liquidez_dificil"]
    educacional = skill_ref.OPCOES_LASTREADAS["educacional"]["liquidez_dificil"]
    assert operador != educacional
    assert operador != skill_ref.OPCOES_LASTREADAS["operador"]["sem_setup"]
    assert educacional != skill_ref.OPCOES_LASTREADAS["educacional"]["sem_setup"]


def test_liquidez_dificil_operador_pergunta_continuar_educacional_nao():
    operador = skill_ref.opcoes_lastreadas_txt(
        "operador", "liquidez_dificil", score="46", atividade="2.000 unidades negociadas hoje",
        livro="sem livro publicado")
    educacional = skill_ref.opcoes_lastreadas_txt(
        "educacional", "liquidez_dificil", score="46", atividade="2.000 unidades negociadas hoje",
        livro="sem livro publicado")
    assert operador.endswith("Continuar?")
    assert "Continuar?" not in educacional
    assert "{" not in operador and "}" not in operador
    assert "{" not in educacional and "}" not in educacional


# ─────────────────────────────────────────────────────────────────────────
# Parte E: guardião de ÂNCORA — o texto do consentimento nasce SÓ em skill_ref
# ─────────────────────────────────────────────────────────────────────────

import ast
from pathlib import Path

_STRINGS_ANCORA_LIQUIDEZ = ("sem livro publicado", "poderia não ser atendida")
_RAIZ_APP = Path(__file__).resolve().parent.parent / "app"


def _docstring_ids_de(arvore):
    ids = set()

    def marcar(body):
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            ids.add(id(body[0].value))

    marcar(arvore.body)
    for node in ast.walk(arvore):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            marcar(node.body)
    return ids


def _strings_literais_de_codigo(caminho):
    arvore = ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))
    ids_doc = _docstring_ids_de(arvore)
    out = []
    for node in ast.walk(arvore):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in ids_doc:
            out.append(node.value)
    return out


def test_nenhum_modulo_backend_fora_do_skill_ref_compoe_aviso_de_liquidez():
    for caminho in sorted(_RAIZ_APP.glob("*.py")):
        if caminho.name == "skill_ref.py":
            continue
        for literal in _strings_literais_de_codigo(caminho):
            for ancora in _STRINGS_ANCORA_LIQUIDEZ:
                assert ancora not in literal, (
                    f"{caminho.name}: o texto de consentimento de liquidez vem SÓ de "
                    f"skill_ref.py — string proibida '{ancora}' encontrada: {literal!r}"
                )


def test_guardiao_de_ancora_nao_protege_texto_que_nao_existe_mais():
    texto = (_RAIZ_APP / "skill_ref.py").read_text(encoding="utf-8")
    for ancora in _STRINGS_ANCORA_LIQUIDEZ:
        assert ancora in texto
