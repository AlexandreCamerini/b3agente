"""FASE 1.4 — guardrail regulatório: NENHUM texto fixo ou prompt do sistema
pode conter verbo de ordem de operação. Varre os módulos com output/instrução
de IA. Cuidado com falsos positivos: 'sobrevenda'/'sobrevendido' são estados
técnicos válidos — os padrões usam fronteira de palavra."""
import re

from app import assistente, conceitos, llm, scan_deep, scanner, setups, skill_ref

PROIBIDOS = [
    r"\bcompre\b", r"\bcomprem\b", r"\bvenda\s+(agora|j[áa]|imediata)",
    r"\bentre\s+agora\b", r"\bdeve\s+comprar\b", r"\bdeve\s+vender\b",
    r"\brecomendo\s+(comprar|vender)\b", r"\bcompra\s+recomendada\b",
    r"\bvenda\s+recomendada\b", r"\bordem\s+de\s+compra\s+agora\b",
]

FONTES = {
    "llm.GUARDRAILS": llm.GUARDRAILS,
    "llm.FORMAT": llm.FORMAT,
    "llm.OPERADOR_EDUCACIONAL": llm.OPERADOR_EDUCACIONAL,
    "llm.DEEP_FORMAT": llm.DEEP_FORMAT,
    "scanner.DISCLAIMER": scanner.DISCLAIMER,
    # FASE 8B (B3): a mesa usa RÓTULOS de decisão ('COMPRAR'/'VENDER'), mas os
    # imperativos de pressão ("compre", "venda agora", "deve comprar",
    # "recomendo comprar") seguem PROIBIDOS também no modo operador —
    # mesmos padrões, fontes novas.
    "llm.OPERADOR_PRO": llm.OPERADOR_PRO,
    "llm.GUARDRAILS_PRO": llm.GUARDRAILS_PRO,
    "llm.FORMAT_PRO": llm.FORMAT_PRO,
    "llm.PRO_DEEP_FORMAT": llm.PRO_DEEP_FORMAT,
    # 2026-08-05 (revisão do supervisor): faltavam aqui justamente os textos que
    # chegam ao usuário SEM passar por LLM nenhuma — as frases canônicas de
    # timing e, agora, o catálogo de conceitos. Texto determinístico é o que
    # mais precisa desta varredura: ninguém o revisa em runtime.
    "skill_ref.TIMING": "\n".join(f for m in skill_ref.TIMING.values() for f in m.values()),
    # Parágrafo condicional é `(estados, texto)` — a varredura pega o texto dos
    # dois formatos, senão o texto de um estado inteiro escaparia do guardião.
    # O prefixo do assistente é texto FIXO que vira instrução de sistema numa
    # LLM aberta a pergunta livre — é o que mais precisa da varredura.
    "assistente.system_prefixo(estudo)": assistente.system_prefixo("educacional"),
    "assistente.system_prefixo(operador)": assistente.system_prefixo("operador"),
    "conceitos.CONCEITOS": "\n".join(
        (p[1] if isinstance(p, tuple) else p)
        for c in conceitos.CONCEITOS.values()
        for p in (list(c["naoAcontece"]) + list(c["oQueE"]) + list(c["oQueAcontece"])
                  + list(c["titulo"].values()))),
}


def _scan(nome, texto):
    hits = []
    # Linhas que DECLARAM a proibição citam os termos proibidos de propósito
    # (ex.: "PROIBIDO verbo de ordem (compre/venda/entre agora)") — são meta-
    # texto de instrução, não output; ficam fora da varredura.
    linhas = [l for l in (texto or "").lower().splitlines() if "proibido" not in l and "nao use 'comprar'" not in l and "não use 'comprar'" not in l]
    low = "\n".join(linhas)
    for pat in PROIBIDOS:
        if re.search(pat, low):
            hits.append((nome, pat))
    return hits


def test_textos_fixos_sem_verbo_de_ordem():
    hits = []
    for nome, texto in FONTES.items():
        hits += _scan(nome, texto)
    assert hits == [], f"verbo de ordem encontrado: {hits}"


def test_vocabulario_fixo_presente_nos_prompts():
    for termo in ("Estudar alta", "Estudar baixa", "Monitorar", "Não operar"):
        assert termo in llm.OPERADOR_EDUCACIONAL or termo in llm.DEEP_FORMAT


def test_setups_e_deep_disclaimer_educacionais():
    # rótulos dos setups e vereditos vêm de setups.py — varre o fonte do módulo
    import inspect
    src = inspect.getsource(setups).lower()
    hits = _scan("setups.py", src)
    assert hits == [], f"verbo de ordem em setups.py: {hits}"
    # disclaimer do deep declara ausência de recomendação
    import asyncio

    async def fake(item):
        return {"resumo": "x"}
    r = asyncio.run(scan_deep.run_deep({"results": [{"ticker": "T1234", "confluencia": 1, "condicoes_detectadas": ["a"]}]}, 1, "1y", fake))
    assert "sem qualquer recomendação de investimento" in r["disclaimer"].lower() or "recomendação de investimento" in r["disclaimer"]


def test_sobrevenda_nao_e_falso_positivo():
    assert _scan("x", "RSI em sobrevenda; estocástico sobrevendido; venda coberta é conceito") == []
