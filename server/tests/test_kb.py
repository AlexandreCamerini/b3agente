"""Fase F2 — base de conhecimento determinística (`app/kb.py`).

Guardiões deste arquivo:
  • Todo verbete tem `id` não vazio e ÚNICO, pelo menos 1 termo de busca e
    texto não vazio nos dois modos (educacional/operador).
  • NENHUM texto usa as expressões proibidas (o mesmo vocabulário de
    `assistente.py`/`test_assistente.py`: 'sinal de compra', 'sinal de
    entrada', 'hora de agir', 'chegou o momento') fora de negação — a mesma
    ideia de `conceitos.py:245` ("Fundamento A não é sinal de compra"), que é
    a forma PERMITIDA porque nega a expressão em vez de afirmá-la.
  • Todo `id` citado em `veja` de algum verbete existe de fato no catálogo
    (sem link morto — a mesma regra que `conceitos.montar` já aplica).

`test_kb_espelho.py` é o guardião irmão: verifica que a KB não fica para trás
quando `MODELS`/`setups.py`/`kpi._MAPS`/`conceitos.CONCEITOS` ganham entradas
novas.
"""
import os
import re
import unicodedata

import pytest

from app import kb


@pytest.fixture(autouse=True)
def _flags_limpas():
    """A KB deriva parte do texto de `conceitos.montar(...)`, que respeita
    `B3_DIDATICA_OFF`. Isolado aqui como o resto da suíte já faz em
    `test_conceitos.py`/`test_assistente.py`, para nenhum teste de outro
    arquivo vazar a flag e apagar texto em silêncio."""
    antes = {k: os.environ.get(k) for k in ("B3_DIDATICA_OFF", "B3_ASSISTENTE_OFF")}
    for k in antes:
        os.environ.pop(k, None)
    yield
    for k, v in antes.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


# --------------------------------------------------------------- vocabulário
# Mesma lista de `assistente.py` (`_regras`) / `test_assistente.py`
# (`test_prefixo_proibe_enquadrar_condicao_como_convocacao`): as expressões
# que transformam uma condição do plano em convocação de operar.
EXPRESSOES_PROIBIDAS = ("sinal de compra", "sinal de entrada", "hora de agir",
                        "chegou o momento")
NEGACOES = ("não", "nao", "nunca", "jamais")


def _normalizar(s) -> str:
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower().strip()


def _ocorrencias_fora_de_negacao(texto: str, expressao: str) -> list:
    """Ocorrências de `expressao` em `texto` cuja oração (até o último
    terminador de frase antes dela) NÃO contém uma negação. Mesmo critério
    que já vale em prosa no catálogo hoje — ex. `conceitos.py`: "Fundamento A
    não é sinal de compra" é permitido porque 'não' antecede a expressão na
    mesma oração; uma frase que afirmasse 'é sinal de compra' sem negativa
    não seria."""
    low = _normalizar(texto)
    exp = _normalizar(expressao)
    hits = []
    start = 0
    while True:
        i = low.find(exp, start)
        if i == -1:
            break
        fim_oracao_anterior = -1
        for term in (".", "!", "?", "\n"):
            pos = low.rfind(term, 0, i)
            if pos > fim_oracao_anterior:
                fim_oracao_anterior = pos
        oracao = low[fim_oracao_anterior + 1:i]
        tem_negacao = any(re.search(r"\b" + neg + r"\b", oracao) for neg in NEGACOES)
        if not tem_negacao:
            hits.append(i)
        start = i + 1
    return hits


def test_negacao_detecta_a_forma_permitida_e_a_proibida():
    """Guardião do próprio guardião: sem isso, um bug na função de negação
    passaria os dois lados do contrato em silêncio."""
    assert _ocorrencias_fora_de_negacao(
        "Fundamento A não é sinal de compra, nunca.", "sinal de compra") == []
    assert len(_ocorrencias_fora_de_negacao(
        "Isto é um sinal de compra.", "sinal de compra")) == 1


# ------------------------------------------------------------------ catálogo
def test_catalogo_nao_vazio():
    cat = kb.catalogo()
    assert len(cat) > 30, "catálogo da KB parece incompleto"


def test_todo_verbete_tem_id_nao_vazio_e_unico():
    cat = kb.catalogo()
    ids = [v["id"] for v in cat]
    assert all(isinstance(i, str) and i.strip() for i in ids), "id vazio no catálogo"
    dup = {i for i in ids if ids.count(i) > 1}
    assert not dup, f"ids duplicados na KB: {dup}"


def test_todo_verbete_tem_pelo_menos_um_termo():
    for v in kb.catalogo():
        termos = v.get("termos") or ()
        assert len(termos) >= 1, f"{v['id']} sem termo de busca"
        assert all(isinstance(t, str) and t.strip() for t in termos), \
            f"{v['id']} tem termo vazio"


def test_todo_verbete_tem_familia_das_9_categorias():
    familias_validas = {"indicadores", "estrutura", "familias", "modelos", "setups",
                        "plano_risco", "fundamentos", "mercado_b3", "estados_app"}
    for v in kb.catalogo():
        assert v.get("familia") in familias_validas, \
            f"{v['id']} com família fora do catálogo: {v.get('familia')}"


def test_todo_verbete_tem_texto_nos_dois_modos():
    for v in kb.catalogo():
        texto = v.get("texto") or {}
        for modo in ("educacional", "operador"):
            t = texto.get(modo)
            assert isinstance(t, str) and t.strip(), \
                f"{v['id']} sem texto no modo {modo!r}"


def test_veja_nunca_e_link_morto():
    cat = kb.catalogo()
    ids = {v["id"] for v in cat}
    for v in cat:
        for alvo in v.get("veja") or []:
            assert alvo in ids, f"{v['id']} referencia '{alvo}' em veja, que não existe"
        assert v["id"] not in (v.get("veja") or []), f"{v['id']} referencia a si mesmo"


# ---------------------------------------------------------- vocabulário: F2
def test_nenhum_texto_usa_expressao_proibida_fora_de_negacao():
    falhas = []
    for v in kb.catalogo():
        for modo, texto in (v.get("texto") or {}).items():
            for exp in EXPRESSOES_PROIBIDAS:
                if _ocorrencias_fora_de_negacao(texto, exp):
                    falhas.append((v["id"], modo, exp))
    assert falhas == [], f"expressão proibida fora de negação: {falhas}"


def test_modo_educacional_sem_verbo_de_ordem_obvio():
    """Checagem leve, redundante com `test_guardrail_imperativo.py` (que varre
    os textos determinísticos do app inteiro): garante que a KB nova não
    introduz o erro mais barato — 'compre'/'venda agora' em modo Estudo."""
    padroes = (r"\bcompre\b", r"\bcomprem\b", r"\bvenda\s+(agora|j[áa])\b",
              r"\bentre\s+agora\b")
    for v in kb.catalogo():
        texto = _normalizar((v.get("texto") or {}).get("educacional") or "")
        for pat in padroes:
            assert not re.search(pat, texto), \
                f"{v['id']} (educacional) usa verbo de ordem: {pat}"


def test_buscar_e_verbete_funcionam():
    achado = kb.verbete("gatilho")
    assert achado is not None and achado["id"] == "gatilho"
    assert kb.verbete("id-que-nao-existe-jamais") is None

    resultado = kb.buscar("o que é RSI?")
    assert resultado and resultado[0]["id"] == "ind-rsi"

    resultado_setup = kb.buscar("como funciona o setup IFR2")
    assert any(v["id"] == "setup-ifr2" for v in resultado_setup)

    assert kb.buscar("") == []
    assert kb.buscar("   ") == []
