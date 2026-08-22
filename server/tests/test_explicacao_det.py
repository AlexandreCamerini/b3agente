"""Guardião do compositor determinístico da explicação do Passo 7 (FIX-C01).

O que estes testes travam:
  • O veredito exibido é o MESMO literal de `context["setupsRadar"]["veredito"]`
    (guardrail CVM: manchete só do motor determinístico, nunca parafraseada).
  • Princípio 1 (nenhum número inventado): campo ausente (ex. `atr14 = None`)
    faz a linha inteira sumir — nunca vira "0,0"/"0.0".
  • Degradação sem dado: nem setup nem indicador utilizável ⇒ `semDados=True`
    e `markdown == ""` (quem decide o texto de fallback é a rota/UI).
  • `fonte == "deterministico"` sempre, e nenhum `verbetes` aponta pra id
    fantasma na KB.
  • Módulo puro: zero rede, zero IA, zero persistência.
  • Vocabulário: modo educacional nunca usa verbo de ordem, mesmo crivo do
    resto do produto (`test_kb.py::test_modo_educacional_sem_verbo_de_ordem_obvio`).
"""
import inspect
import re

from app import explicacao_det, kb

SNAP_COMPLETO = {
    "asOf": "2026-08-20T17:00:00",
    "barraEmFormacao": None,
    "context": {
        "trend": {"bias": "alta"},
        "volatility": {"atr14": 1.23, "atr14Pct": 3.5,
                        "bollingerUpper": 40.5, "bollingerLower": 36.2},
        "levels": {"nearestSupport": 37.0, "nearestResistance": 39.5},
        "setupsRadar": {
            "veredito": "Estudar alta",
            "confluencia": 72,
            "melhorSetup": "Setup 9.1 (alta)",
            "setups": [{
                "nome": "Setup 9.1 (alta)", "lado": "alta", "confluencia": 72,
                "gatilho": 38.0, "invalidacao": 36.5,
            }],
        },
    },
}

SNAP_SO_INDICADORES = {
    "asOf": "2026-08-20T17:00:00",
    "barraEmFormacao": None,
    "context": {
        "trend": {"bias": "baixa"},
        "volatility": {"atr14": 0.87, "atr14Pct": 2.1},
        "levels": {},
        "setupsRadar": {"veredito": "Sem setup no momento", "confluencia": 0,
                         "melhorSetup": None, "setups": []},
    },
}

SNAP_VAZIO = {"asOf": None, "context": {}}

SNAP_ATR_NONE = {
    "asOf": "2026-08-20T17:00:00",
    "context": {
        "trend": {"bias": "alta"},
        "volatility": {"atr14": None, "atr14Pct": None},
        "levels": {},
        "setupsRadar": {"veredito": "Monitorar", "confluencia": 0,
                         "melhorSetup": None, "setups": []},
    },
}


def test_veredito_e_o_literal_do_motor_nunca_parafraseado():
    r = explicacao_det.montar("PETR4", SNAP_COMPLETO, "educacional")
    esperado = SNAP_COMPLETO["context"]["setupsRadar"]["veredito"]
    assert esperado in r["markdown"]


def test_atr_none_nao_vira_zero_e_a_linha_some():
    r = explicacao_det.montar("PETR4", SNAP_ATR_NONE, "educacional")
    assert "0,0" not in r["markdown"]
    assert "0.0" not in r["markdown"]
    assert "ATR" not in r["markdown"]


def test_sem_setup_e_sem_indicador_degrada_sem_inventar():
    r = explicacao_det.montar("PETR4", SNAP_VAZIO, "educacional")
    assert r["semDados"] is True
    assert r["markdown"] == ""
    assert r["fonte"] == "deterministico"


def test_fonte_e_sempre_deterministico():
    for snap in (SNAP_COMPLETO, SNAP_SO_INDICADORES, SNAP_VAZIO, SNAP_ATR_NONE):
        r = explicacao_det.montar("PETR4", snap, "educacional")
        assert r["fonte"] == "deterministico"


def test_verbetes_nao_apontam_para_link_morto():
    for snap in (SNAP_COMPLETO, SNAP_SO_INDICADORES):
        r = explicacao_det.montar("PETR4", snap, "educacional")
        assert r["verbetes"], "esperava ao menos um verbete usado"
        for vid in r["verbetes"]:
            assert kb.verbete(vid) is not None, f"verbete fantasma: {vid}"


def test_modo_operador_tambem_produz_explicacao():
    r = explicacao_det.montar("PETR4", SNAP_COMPLETO, "operador")
    assert r["semDados"] is False
    assert r["markdown"] != ""
    assert "Estudar alta" in r["markdown"]


def test_modo_educacional_sem_verbo_de_ordem_obvio():
    padroes = (r"\bcompre\b", r"\bcomprem\b", r"\bvenda\s+(agora|j[áa])\b",
               r"\bentre\s+agora\b")
    for snap in (SNAP_COMPLETO, SNAP_SO_INDICADORES):
        r = explicacao_det.montar("PETR4", snap, "educacional")
        low = r["markdown"].lower()
        for pat in padroes:
            assert not re.search(pat, low), f"verbo de ordem encontrado: {pat}"


def test_asof_e_barra_em_formacao_aparecem_na_secao_de_idade():
    snap = {**SNAP_COMPLETO, "barraEmFormacao": "2026-08-20T17:15:00"}
    r = explicacao_det.montar("PETR4", snap, "educacional")
    assert "2026-08-20T17:00:00" in r["markdown"]
    assert "2026-08-20T17:15:00" in r["markdown"]
    assert r["asOf"] == "2026-08-20T17:00:00"


def test_modulo_e_puro_sem_rede_ia_ou_persistencia():
    src = inspect.getsource(explicacao_det)
    for proibido in ("llm", "httpx", "requests", "db.", "store."):
        assert proibido not in src, f"módulo não é puro: contém '{proibido}'"
