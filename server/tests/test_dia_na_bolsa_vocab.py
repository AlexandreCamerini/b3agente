"""Guardião de vocabulário do card "Seu dia na bolsa" (Fase 51, D-02/D-04/ENG-07).

Trava `skill_ref.DIA_NA_BOLSA` e as chaves `corpo_ontem_*` de `PUSH_RADAR`:
sem linguagem de perda/urgência, Estudo sem verbo de ordem, alvo e stop com o
mesmo número de variantes, placeholder ausente vira "—" e o corpo cabe no push.
"""
import re

from app import skill_ref as sr

MODOS = ("educacional", "operador")

PROIBIDO = re.compile(
    r"perdeu|perdeste|perda|prejuízo|oportunidade|imperdível|última chance|só hoje"
    r"|agora!|entre agora|garantid\w*|lucro certo|não perca|fique rico|rápido|corra"
    r"|faltam \d+",
    re.IGNORECASE,
)
ORDEM = re.compile(r"\bcompre\b|\bvenda\b|\bcomprar\b|\bvender\b", re.IGNORECASE)

VALS_MAX = {
    "T": "PETR4", "R": "+10,0R", "N": "10", "stop": "100,00", "pct": "10,0%",
    "meses": "14", "multiplo": "10,0", "fracao": "100%", "direcao": "subiram",
    "setup": "Rompimento", "n": "10",
}


def _todos_textos():
    for modo in MODOS:
        for k, v in sr.DIA_NA_BOLSA[modo].items():
            yield f"DIA_NA_BOLSA[{modo}].{k}", v
    for k, v in sr.PUSH_RADAR.items():
        yield f"PUSH_RADAR.{k}", v


def _bases_com_variantes():
    return sorted({re.sub(r"_\d+$", "", k) for k in sr.DIA_NA_BOLSA["educacional"] if re.search(r"_\d+$", k)})


def test_mesmas_chaves_nos_dois_modos():
    assert set(sr.DIA_NA_BOLSA["educacional"]) == set(sr.DIA_NA_BOLSA["operador"])


def test_sem_vocabulario_proibido():
    for nome, texto in _todos_textos():
        assert not PROIBIDO.search(texto), f"{nome}: {texto!r}"


def test_estudo_sem_verbo_de_ordem():
    for k, v in sr.DIA_NA_BOLSA["educacional"].items():
        assert not ORDEM.search(v), f"{k}: {v!r}"


def test_push_radar_ontem_alvo_stop_equilibrados():
    a, s = sr.PUSH_RADAR["corpo_ontem_alvo"], sr.PUSH_RADAR["corpo_ontem_stop"]
    assert "{T}" in a and "{T}" in s
    assert "{R}" not in a and "{R}" not in s  # sem R no push
    assert abs(len(a) - len(s)) <= 8


def test_alvo_e_stop_mesmo_numero_de_variantes_e_formato():
    for modo in MODOS:
        na = sr.dia_na_bolsa_n_variantes("f1_alvo", modo)
        ns = sr.dia_na_bolsa_n_variantes("f1_stop", modo)
        assert na == ns and 3 <= na <= 4
        for i in range(1, na + 1):
            a = sr.DIA_NA_BOLSA[modo][f"f1_alvo_{i}"]
            s = sr.DIA_NA_BOLSA[modo][f"f1_stop_{i}"]
            assert "{R}" in a and "{R}" in s
            assert abs(len(a) - len(s)) <= 25, (modo, i)


def test_toda_regra_com_variantes_tem_3_ou_4():
    bases = _bases_com_variantes()
    assert bases
    for modo in MODOS:
        for b in bases:
            assert 3 <= sr.dia_na_bolsa_n_variantes(b, modo) <= 4, (modo, b)


def test_sem_aspas_ascii_nem_quebra_de_linha():
    for nome, texto in _todos_textos():
        assert '"' not in texto and "\n" not in texto, nome


def test_placeholder_ausente_vira_travessao_nunca_zero():
    t = sr.dia_na_bolsa_txt("operador", "f2_alvo_executado", 0, {})
    assert "—" in t and "0" not in t
    assert sr.dia_na_bolsa_txt("estudo", "f1_alvo", 0, {"T": "VALE3"}).count("—") == 1
    assert sr.dia_na_bolsa_txt("operador", "f2_carteira_ibov", 0, {"carteira": "+0,4%"}) == "Carteira +0,4% × IBOV — no dia"


def test_variante_modular_e_chave_inexistente():
    n = sr.dia_na_bolsa_n_variantes("f1_alvo", "estudo")
    assert sr.dia_na_bolsa_txt("estudo", "f1_alvo", 0, VALS_MAX) == sr.dia_na_bolsa_txt("estudo", "f1_alvo", n, VALS_MAX)
    assert sr.dia_na_bolsa_txt("estudo", "nao_existe", 0, VALS_MAX) == ""
    assert sr.dia_na_bolsa_txt("estudo", "titulo") == "Seu dia na bolsa"


def test_corpo_cabe_em_110_caracteres_com_valores_maximos():
    for modo in MODOS:
        d = sr.DIA_NA_BOLSA[modo]
        bases = {re.sub(r"_\d+$", "", k) for k in d if k.startswith(("f1_", "f2_", "f3_", "chamada_")) and re.search(r"_\d+$", k)}
        bases |= {k for k in d if k.startswith("f3_pergunta_")}
        bases -= {"f2_carteira_ibov", "f2_ibov_indisponivel"}
        for b in bases:
            n = sr.dia_na_bolsa_n_variantes(b, modo) or 1
            for i in range(n):
                t = sr.dia_na_bolsa_txt(modo, b, i, VALS_MAX)
                assert len(t) <= 110, (modo, b, i, len(t), t)
