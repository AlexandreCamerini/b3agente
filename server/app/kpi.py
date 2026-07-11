"""Extrai os KPIs estruturados da resposta da LLM e separa do texto.

Saida: (kpis | None, texto). KPIs sao normalizados (acento/caixa) para os
valores canonicos exatos exigidos pela UI.
"""
from typing import Optional
import json
import re
import unicodedata


def _strip(s) -> str:
    s = "" if s is None else str(s)
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower().strip()


_MAPS = {
    "direcao": {"alta": "Alta", "baixa": "Baixa", "lateral": "Lateral"},
    "conviccao": {
        "muito alto": "Muito Alto", "muito alta": "Muito Alto",
        "alto": "Alto", "alta": "Alto",
        "medio": "Médio", "media": "Médio",
        "baixo": "Baixo", "baixa": "Baixo",
    },
    "qualidade": {
        "excelente": "Excelente", "boa": "Boa", "bom": "Boa",
        "regular": "Regular", "ruim": "Ruim",
    },
    "recomendacao": {
        "estudar alta": "Estudar alta",
        "estudo de alta": "Estudar alta",
        "estudar baixa": "Estudar baixa",
        "estudo de baixa": "Estudar baixa",
        "monitorar": "Monitorar",
        "aguardar": "Aguardar",
        # qa/39 (P1-1): valor do enum PRO (FORMAT_PRO) — normaliza para o
        # intermediário educacional; o analyze_structured re-mapeia p/ mesa.
        "aguardar confirmacao": "Aguardar",
        "nao operar": "Não operar",
        "não operar": "Não operar",
        "reduzir risco": "Reduzir risco",
        # compatibilidade com respostas antigas: normaliza para plano educacional
        "comprar": "Estudar alta",
        "comprar parcialmente": "Estudar alta",
        "realizar lucro": "Reduzir risco",
        "reduzir exposicao": "Reduzir risco",
        "vender": "Estudar baixa",
    },
}


def _norm(field: str, value) -> Optional[str]:
    return _MAPS[field].get(_strip(value))


def normalize_kpis(obj) -> Optional[dict]:
    if not isinstance(obj, dict):
        return None
    out = {
        "direcao": _norm("direcao", obj.get("direcao")),
        "conviccao": _norm("conviccao", obj.get("conviccao")),
        "qualidade": _norm("qualidade", obj.get("qualidade")),
        "recomendacao": _norm("recomendacao", obj.get("recomendacao")),
    }
    if any(out.values()):
        return out
    return None


def _first_json(raw: str):
    """Extrai o primeiro objeto JSON balanceado (respeita strings/escapes)."""
    start = raw.find("{")
    while start != -1:
        depth = 0
        in_str = False
        esc = False
        for i in range(start, len(raw)):
            ch = raw[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    blob = raw[start:i + 1]
                    try:
                        return json.loads(blob), start, i + 1
                    except (ValueError, TypeError):
                        break
        start = raw.find("{", start + 1)
    return None, -1, -1


def _num(v) -> Optional[float]:
    if isinstance(v, (int, float)):
        return round(float(v), 2)
    if isinstance(v, str):
        m = re.search(r"-?\d+(?:[.,]\d+)?", v)
        if m:
            try:
                return round(float(m.group(0).replace(",", ".")), 2)
            except ValueError:
                return None
    return None


def _str_list(v) -> list:
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    if isinstance(v, str) and v.strip():
        return [v.strip()]
    return []


def _synth_markdown(detail: dict) -> str:
    """Monta um corpo em markdown a partir dos campos estruturados (fallback
    quando a IA nao mandou 'corpo')."""
    lines = []
    if detail.get("resumo"):
        lines.append(detail["resumo"])
    for title, key in (("Confirmações", "confirmacoes"), ("Invalidações", "invalidacoes"), ("Cuidados", "cuidados")):
        items = detail.get(key) or []
        if items:
            lines.append("")
            lines.append("**" + title + "**")
            lines.extend("- " + str(it) for it in items)
    return "\n".join(lines).strip()


def parse_rich(raw: str) -> dict:
    """Resposta estruturada da IA: KPIs + resumo + listas + corpo (markdown) +
    stop/alvo sugeridos. SEMPRE devolve o mesmo formato; nunca levanta excecao.
    O campo `markdown` nunca vem vazio — o cliente renderiza esse corpo."""
    raw = raw or ""
    obj, s, e = _first_json(raw)
    kpis = normalize_kpis(obj) if obj else None
    detail = {"resumo": "", "confirmacoes": [], "invalidacoes": [], "cuidados": [], "fatos": []}
    proposal = {"stop": None, "alvo": None}
    corpo = ""
    text = raw
    if isinstance(obj, dict):
        detail["resumo"] = str(obj.get("resumo") or "").strip()
        detail["confirmacoes"] = _str_list(obj.get("confirmacoes"))
        detail["invalidacoes"] = _str_list(obj.get("invalidacoes"))
        detail["cuidados"] = _str_list(obj.get("cuidados"))
        detail["fatos"] = _str_list(obj.get("fatosRelevantes") or obj.get("fatos"))
        proposal["stop"] = _num(obj.get("stopSugerido"))
        proposal["alvo"] = _num(obj.get("alvoSugerido"))
        corpo = str(obj.get("corpo") or obj.get("markdown") or obj.get("analise") or "").strip()
        # remove cercas de markdown que a IA as vezes embrulha em volta do corpo
        corpo = re.sub(r"^```[a-zA-Z]*\n?", "", corpo)
        corpo = re.sub(r"\n?```$", "", corpo).strip()
        text = (raw[:s] + raw[e:])
    text = text.replace("```json", "").replace("```", "").strip()
    # corpo final (markdown), sempre nao-vazio:
    markdown = corpo or _synth_markdown(detail) or text or "_A IA não retornou um corpo de análise legível._"
    return {"kpis": kpis, "detail": detail, "proposal": proposal, "markdown": markdown, "text": text}


def parse_analysis(raw: str):
    """Compatibilidade: (kpis | None, texto)."""
    r = parse_rich(raw)
    fallback = r["text"] or r["detail"]["resumo"] or (raw or "").strip()
    return r["kpis"], fallback
