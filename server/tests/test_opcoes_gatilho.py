"""Fase 15, Plano 02 — `opcoes_gatilho.do_plano()`: plano do Radar vira
decisão de avaliar estrutura de opções (ENG-06).

Parte 1 (Task 1): comportamento de `do_plano` — um teste por item do
`<behavior>` do plano, incluindo entrada ausente/malformada/desconhecida.

Parte 2 (Task 2): dois guardiões.
  - GUARDIÃO de paridade: o mapeamento de `do_plano` concorda com o
    mapeamento hoje embutido em `opcoes_lastreadas.propor()` (linhas 75-88)
    — os dois caminhos não podem divergir enquanto a Fase 16 não os
    unificar.
  - GUARDIÃO b-mcp: nenhum módulo de opções do app importa, referencia por
    string ou embute a DSL de setups declarativa do repositório externo
    b-mcp (~/dev/MCP) — proibição estrutural do ENG-06/ADR-016/017, testada
    via `ast`, não por busca textual (que reprovaria o próprio comentário
    que documenta a proibição).
"""
import ast
import datetime as dt
from pathlib import Path

from app import opcoes_lastreadas
from app.opcoes_gatilho import do_plano, VIES_PROTECAO, VIES_PREMIO


# ------------------------------ Parte 1: comportamento ------------------------------

def test_vender_lado_baixa_avalia_protecao():
    r = do_plano({"decisao": "VENDER", "lado": "baixa"})
    assert r == {"avaliar": True, "vies": VIES_PROTECAO, "motivo": VIES_PROTECAO}


def test_lado_baixa_sozinho_ja_avalia_protecao():
    """`lado == "baixa"` sozinho já aciona proteção, mesma condição `or` de
    `propor()` hoje — mesmo com decisão COMPRAR."""
    r = do_plano({"decisao": "COMPRAR", "lado": "baixa"})
    assert r["vies"] == VIES_PROTECAO


def test_decisao_aguardar_vence_lado_alta_avalia_premio():
    """A decisão de aguardar confirmação vence o lado, mesma ordem de
    avaliação de `propor()`."""
    r = do_plano({"decisao": "AGUARDAR CONFIRMAÇÃO", "lado": "alta"})
    assert r["vies"] == VIES_PREMIO


def test_decisao_nao_operar_lado_none_avalia_premio():
    r = do_plano({"decisao": "NÃO OPERAR", "lado": None})
    assert r["vies"] == VIES_PREMIO


def test_lado_neutro_avalia_premio():
    r = do_plano({"decisao": "COMPRAR", "lado": "neutro"})
    assert r["vies"] == VIES_PREMIO


def test_decisao_comprar_lado_alta_nao_avalia_nenhuma_estrutura():
    r = do_plano({"decisao": "COMPRAR", "lado": "alta"})
    assert r == {"avaliar": False, "vies": None, "motivo": "sem_setup"}


def test_plano_vazio_nao_avalia():
    r = do_plano({})
    assert r["avaliar"] is False
    assert r["motivo"] == "sem_setup"


def test_plano_none_nao_avalia():
    r = do_plano(None)
    assert r["avaliar"] is False
    assert r["motivo"] == "sem_setup"


def test_plano_texto_nao_levanta_excecao_e_nao_avalia():
    r = do_plano("texto")
    assert r["avaliar"] is False
    assert r["motivo"] == "sem_setup"


def test_plano_numero_nao_levanta_excecao_e_nao_avalia():
    r = do_plano(42)
    assert r["avaliar"] is False
    assert r["motivo"] == "sem_setup"


def test_decisao_e_lado_inventados_nao_caem_em_vies_por_default():
    r = do_plano({"decisao": "decisão inventada", "lado": "lado inventado"})
    assert r["avaliar"] is False
    assert r["motivo"] == "sem_setup"


def test_retorno_tem_exatamente_tres_chaves_e_avaliar_coerente_com_vies():
    casos = [
        {"decisao": "VENDER", "lado": "baixa"},
        {"decisao": "COMPRAR", "lado": "baixa"},
        {"decisao": "AGUARDAR CONFIRMAÇÃO", "lado": "alta"},
        {"decisao": "NÃO OPERAR", "lado": None},
        {"decisao": "COMPRAR", "lado": "neutro"},
        {"decisao": "COMPRAR", "lado": "alta"},
        {},
        None,
        "texto",
        42,
        {"decisao": "x", "lado": "y"},
    ]
    for plano in casos:
        r = do_plano(plano)
        assert sorted(r.keys()) == ["avaliar", "motivo", "vies"]
        assert (r["avaliar"] is True) == (r["vies"] is not None)


# ------------------------- Parte 2: GUARDIÃO de paridade -------------------------

_SPOT = 30.0
_HOJE = dt.date(2026, 8, 31)


def _contrato(strike, symbol, kind, price=1.0, volume=1000, oi=1000):
    return {"contractSymbol": symbol, "optionType": kind, "strike": strike, "lastPrice": price,
            "bid": round(price - 0.05, 2), "ask": round(price + 0.05, 2), "volume": volume,
            "openInterest": oi, "impliedVolatility": 0.3}


def _cadeia():
    exp = (_HOJE + dt.timedelta(days=30)).isoformat()
    calls = [_contrato(32.0, "PETR4F32", "call"), _contrato(34.0, "PETR4F34", "call")]
    puts = [_contrato(28.0, "PETR4F28", "put"), _contrato(26.0, "PETR4F26", "put")]
    return {"providerStatus": "ok", "underlyingPrice": _SPOT, "expiration": exp,
            "expirations": [exp], "calls": calls, "puts": puts}


def _posicao():
    return {"t": "PETR4", "qty": 100, "qtyTravada": 0}


_COMBOS_DECISAO_LADO = [
    {"decisao": "VENDER", "lado": "baixa"},
    {"decisao": "COMPRAR", "lado": "baixa"},
    {"decisao": "AGUARDAR CONFIRMAÇÃO", "lado": "alta"},
    {"decisao": "NÃO OPERAR", "lado": None},
    {"decisao": "COMPRAR", "lado": "neutro"},
    {"decisao": "COMPRAR", "lado": "alta"},
]

_VIES_POR_MOTIVO_DO_PROPOR = {"put_protecao": VIES_PROTECAO, "call_coberta": VIES_PREMIO}


def test_paridade_gatilho_com_motor_em_producao():
    """Para cada combinação decisao×lado do bloco de comportamento, o motivo
    que `opcoes_lastreadas.propor()` já devolve em produção tem de
    corresponder ao viés que `do_plano()` devolve. Falha se um dos dois
    lados mudar isoladamente — a unificação real só acontece na Fase 16."""
    for plano in _COMBOS_DECISAO_LADO:
        r_propor = opcoes_lastreadas.propor(
            "PETR4", _cadeia(), _SPOT, plano, _posicao(), 100000, "operador", _HOJE)
        r_gatilho = do_plano(plano)
        motivo_propor = r_propor["motivo"]
        if motivo_propor in _VIES_POR_MOTIVO_DO_PROPOR:
            assert r_gatilho["avaliar"] is True, plano
            assert r_gatilho["vies"] == _VIES_POR_MOTIVO_DO_PROPOR[motivo_propor], plano
        else:
            assert r_gatilho["avaliar"] is False, plano
            assert r_gatilho["motivo"] == motivo_propor, plano


# --------------------------- Parte 2: GUARDIÃO b-mcp ---------------------------

_MODULOS_OPCOES = ["opcoes_gatilho.py", "opcoes_payoff.py", "opcoes_lastreadas.py"]
_RAIZES_IMPORT_PROIBIDAS = {"mcp", "setups_json"}
_SUBSTRINGS_NOME_PROIBIDAS = ("b_mcp", "bmcp")
_STRINGS_LITERAL_PROIBIDAS = ("b-mcp", "setups.json", "semente.dev")


def _arvore_de(nome_arquivo):
    caminho = Path(__file__).resolve().parent.parent / "app" / nome_arquivo
    if not caminho.exists():
        return None
    return ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))


def test_modulos_de_opcoes_nao_importam_a_dsl_de_setups_do_bmcp():
    for nome in _MODULOS_OPCOES:
        arvore = _arvore_de(nome)
        if arvore is None:
            continue
        for node in ast.walk(arvore):
            nomes_modulo = []
            if isinstance(node, ast.Import):
                nomes_modulo = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                nomes_modulo = [node.module or ""]
            for modulo in nomes_modulo:
                raiz = modulo.split(".")[0]
                assert raiz not in _RAIZES_IMPORT_PROIBIDAS, f"{nome}: import proibido de '{modulo}'"
                assert not any(s in modulo for s in _SUBSTRINGS_NOME_PROIBIDAS), \
                    f"{nome}: import proibido de '{modulo}'"


def test_modulos_de_opcoes_nao_embutem_constante_de_string_da_dsl_do_bmcp():
    for nome in _MODULOS_OPCOES:
        arvore = _arvore_de(nome)
        if arvore is None:
            continue
        for node in ast.walk(arvore):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                for proibida in _STRINGS_LITERAL_PROIBIDAS:
                    assert proibida not in node.value, \
                        f"{nome}: string proibida contendo '{proibida}': {node.value!r}"


def test_dsl_declarativa_setups_json_do_bmcp_nao_existe_dentro_do_app():
    caminho = Path(__file__).resolve().parent.parent / "app" / "setups.json"
    assert not caminho.exists()
