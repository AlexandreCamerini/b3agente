"""Fase F2 — o guardião que impede a KB de envelhecer em silêncio.

Cada teste aqui casa uma fonte de verdade do CÓDIGO (que pode ganhar uma
chave nova a qualquer PR) contra o catálogo de `app/kb.py`. Sem isto, alguém
adiciona um modelo, um setup ou um campo de KPI novo e a KB fica desatualizada
sem nenhum teste avisar — o mesmo motivo de existir de
`test_vocabulario_espelho.mjs` (web) para o rótulo de estado do timing.

Critério de match, um por fonte (documentado aqui porque cada fonte tem um
shape diferente):

  1. `technical_models.MODELS` — toda chave `k` precisa ter um verbete com
     `id == "modelo-" + k` e `familia == "modelos"`.
  2. `setups.py` — os 9 NOMES BASE que `_mk(...)` produz (o literal antes do
     `%s` de lado/direção, lido diretamente do código-fonte) precisam
     aparecer, normalizados (acento/caixa), como um termo EXATO de algum
     verbete de família "setups".
  3. `kpi._MAPS` — este dict é sobre normalização de VALOR (acento/caixa →
     rótulo canônico), não uma lista de conceitos; mas as 4 CHAVES que ele
     normaliza (`direcao`, `conviccao`, `qualidade`, `recomendacao`) SÃO os
     campos que a UI expõe como chips do card de análise — o "campo do app"
     que a spec pede para não ficar sem conceito. Critério: verbete com
     `id == "kpi-" + campo`.
  4. `conceitos.CONCEITOS` — cada id precisa ter verbete com o MESMO id na KB
     (a KB deriva o texto de `conceitos.montar(...)`, então isto também prova
     que a derivação não perdeu nenhuma chave).

Verificação manual de que este arquivo REALMENTE denuncia lacuna (feita ao
escrever a KB, não deixada como código): adicionar uma chave fake em
`technical_models.MODELS` (`"fake_temp": {...}`) faz `test_modelos_...`
falhar citando `modelo-fake_temp`; removida a chave, o teste volta a passar.
O mesmo vale para uma entrada fake em `setups._mk(...)` e em `kpi._MAPS`.
"""
import inspect
import re
import unicodedata

from app import conceitos, kb, kpi, setups
from app.technical_models import MODELS


def _ids(cat):
    return {v["id"] for v in cat}


def _normalizar(s) -> str:
    """Mesma normalização de `kb._normalizar` (acento fora, caixa baixa) —
    reescrita aqui para o teste não depender de função privada de kb.py.
    Importante: só remove ACENTO (categoria Unicode 'Mn'), nunca outro
    caractere — um `.encode('ascii', 'ignore')` também comeria o travessão
    de 'Máx/Mín de Larry Williams — 9.4' e o teste "bateria" comparando uma
    string que o catálogo nunca tem."""
    s = unicodedata.normalize("NFD", str(s or ""))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower().strip()


def _normalizar_termos(v):
    return {_normalizar(t) for t in (v.get("termos") or ())}


# ------------------------------------------------------------------ modelos
def test_todo_modelo_de_technical_models_tem_verbete():
    cat = kb.catalogo()
    ids = _ids(cat)
    faltando = []
    for chave in MODELS:
        vid = "modelo-" + chave
        v = next((x for x in cat if x["id"] == vid), None)
        if vid not in ids:
            faltando.append(vid)
        elif v.get("familia") != "modelos":
            faltando.append(vid + " (família errada: " + str(v.get("familia")) + ")")
    assert faltando == [], f"MODELS sem verbete correspondente: {faltando}"


# ------------------------------------------------------------------- setups
# Nomes-base extraídos DINAMICAMENTE do código-fonte de `setups.py` — não uma
# lista fixa. Toda chamada a `_mk(...)` tem como 1º argumento um literal de
# string (às vezes com `% lado` ou `% (...)` colado, às vezes hardcoded como
# em `_setup_ifr2`); o regex pega o literal, e removemos só o SUFIXO de
# lado/direção (`" (%s)"`, `" de %s"`, `" (alta)"`/`" (baixa)"`) para chegar
# no nome-base. Assim, um setup NOVO em `setups.py` entra automaticamente na
# lista que este teste verifica — sem precisar editar este arquivo também.
_MK_NOME_RE = re.compile(r'_mk\(\s*"([^"]+)"')
_SUFIXO_LADO_RE = re.compile(r'(\s*\(%s\)|\s+de\s+%s|\s*\((?:alta|baixa)\))$')


def _nomes_base_de_setups() -> list:
    src = inspect.getsource(setups)
    bases = []
    for literal in _MK_NOME_RE.findall(src):
        base = _SUFIXO_LADO_RE.sub("", literal)
        if base not in bases:
            bases.append(base)
    return bases


# Documenta o resultado esperado HOJE (9 setups) — não é a fonte da verdade
# (essa é `_nomes_base_de_setups()`), é uma trava extra: se `_mk(...)` for
# chamado num lugar novo do arquivo, ou um nome mudar de forma inesperada, a
# diferença aparece aqui ANTES de chegar no teste de espelho contra a KB.
_ESPERADO_HOJE = (
    "Setup 9.1", "Setup 9.2", "Setup 9.3", "IFR2", "PFR", "123",
    "Ponto Contínuo", "Inside Bar", "Máx/Mín de Larry Williams — 9.4",
)


def test_extracao_dinamica_bate_com_o_esperado_hoje():
    assert _nomes_base_de_setups() == list(_ESPERADO_HOJE)


def test_todo_setup_tem_verbete_de_familia_setups():
    """Verificação manual feita ao escrever esta fase (e desfeita depois):
    adicionar em `setups.py` uma chamada `_mk("Setup Fake Temp (%s)" % lado,
    ...)` faz `_nomes_base_de_setups()` incluir "Setup Fake Temp", e este
    teste falha citando exatamente esse nome — sem precisar tocar neste
    arquivo de teste."""
    cat = kb.catalogo()
    setups_kb = [v for v in cat if v["familia"] == "setups"]
    termos_por_verbete = {v["id"]: _normalizar_termos(v) for v in setups_kb}
    faltando = []
    for base in _nomes_base_de_setups():
        alvo = _normalizar(base)
        achou = any(alvo in termos for termos in termos_por_verbete.values())
        if not achou:
            faltando.append(base)
    assert faltando == [], f"setups sem verbete correspondente (família 'setups'): {faltando}"


# ------------------------------------------------------------------ kpi
def test_campos_de_kpi_maps_tem_verbete():
    """`kpi._MAPS` normaliza VALOR, não é uma lista de conceitos — mas as 4
    chaves (`direcao`, `conviccao`, `qualidade`, `recomendacao`) são os
    campos que o card expõe como chip. Critério: `id == "kpi-" + campo`."""
    cat = kb.catalogo()
    ids = _ids(cat)
    faltando = [c for c in kpi._MAPS if ("kpi-" + c) not in ids]
    assert faltando == [], f"campos de kpi._MAPS sem verbete kpi-<campo>: {faltando}"


# -------------------------------------------------------------- conceitos
def test_todo_conceito_tem_verbete_com_o_mesmo_id():
    cat = kb.catalogo()
    ids = _ids(cat)
    faltando = [cid for cid in conceitos.CONCEITOS if cid not in ids]
    assert faltando == [], f"conceitos.CONCEITOS sem verbete correspondente na KB: {faltando}"
