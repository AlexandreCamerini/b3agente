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


# O front renderiza um SUBCONJUNTO de markdown (App.jsx `Markdown`/`MdInline`):
# títulos ## , **negrito**, *itálico*, `código`, listas - / * / • e numeradas,
# parágrafos. Cada LLM emite um dialeto diferente — GPT/Gemini mandam ***triplo***,
# __underscore__, [links](url), > citações, tabelas | a | b |, --- e cercas ```
# internas — que o renderizador cospe LITERAIS. Normalizar aqui (na origem, no
# servidor) conserta para QUALQUER modelo de uma vez, sem tocar o front.
_HR_RE = re.compile(r"^\s*([-*_])(?:\s*\1){2,}\s*$")          # ---  ***  ___  - - -
_FENCE_RE = re.compile(r"^\s*```+[a-zA-Z0-9]*\s*$")            # cerca de bloco de código
_QUOTE_RE = re.compile(r"^\s*>+\s?")                           # > citação
_TABLE_SEP_RE = re.compile(r"^\s*\|?[\s:|-]*-[\s:|-]*\|?\s*$")  # |---|:--:|
_LINK_RE = re.compile(r"\[([^\]]+)\]\((?:[^)]*)\)")           # [texto](url) -> texto
_AUTOLINK_RE = re.compile(r"<(https?://[^>\s]+)>")             # <url> -> url
_STRIKE_RE = re.compile(r"~~([^~]+)~~")                        # ~~riscado~~ -> riscado
_TRIPLE_RE = re.compile(r"(?:\*\*\*|___)([^*_]+?)(?:\*\*\*|___)")  # ***x*** / ___x___ -> **x**
_UBOLD_RE = re.compile(r"__([^_]+?)__")                        # __x__ -> **x**
_UITALIC_RE = re.compile(r"(?<![\w_])_([^_]+?)_(?![\w_])")     # _x_ (emphasis) -> *x*


def _norm_inline(s: str) -> str:
    """Converte ênfases/links de dialetos variados para o subconjunto do front."""
    s = _LINK_RE.sub(r"\1", s)
    s = _AUTOLINK_RE.sub(r"\1", s)
    s = _STRIKE_RE.sub(r"\1", s)
    s = _TRIPLE_RE.sub(r"**\1**", s)   # negrito-itálico -> negrito (front não aninha)
    s = _UBOLD_RE.sub(r"**\1**", s)
    s = _UITALIC_RE.sub(r"*\1*", s)
    return s


def _row_cells(line: str) -> list:
    """Células de uma linha de tabela markdown, sem os pipes das bordas."""
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def normalize_markdown(md: str) -> str:
    """Reduz o corpo ao dialeto que o front sabe renderizar. Model-agnostic:
    o mesmo texto sai igual venha de qualquer LLM. Nunca levanta exceção."""
    if not md:
        return md
    src = str(md).replace("\r\n", "\n").replace("\r", "\n")
    # qa/44: modelos que escapam a quebra devolvem \n / \t LITERAIS (dois
    # caracteres) — sem desescapar, o corpo inteiro vira UMA linha ("texto
    # completamente desformatado"). Model-agnostic: conserta na origem.
    if "\\n" in src or "\\t" in src:
        src = src.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\t", "  ")
    lines = src.split("\n")
    out = []
    in_fence = False
    for i, raw in enumerate(lines):
        # cercas ``` : entra/sai de bloco de código; a marca some, o miolo vira texto
        if _FENCE_RE.match(raw):
            in_fence = not in_fence
            continue
        if in_fence:
            out.append(raw.rstrip())
            continue
        # setext: linha só de === logo abaixo de texto vira título ATX. (--- fica
        # como régua: converter arriscaria comer uma régua legítima em título.)
        if out and out[-1].strip() and not out[-1].lstrip().startswith(("#", "-", "*", "•")) \
                and re.match(r"^\s*=+\s*$", raw):
            out[-1] = "## " + out[-1].strip(); continue
        # régua horizontal isolada -> linha em branco (separa blocos)
        if _HR_RE.match(raw):
            out.append(""); continue
        # tabela: cabeçalho + separador + linhas -> cada linha em texto legível,
        # o separador some (o front não tem tabela).
        if "|" in raw and i + 1 < len(lines) and _TABLE_SEP_RE.match(lines[i + 1]) \
                and raw.strip().count("|") >= 1:
            out.append(" — ".join(c for c in _row_cells(raw) if c)); continue
        if _TABLE_SEP_RE.match(raw) and "|" in raw:
            continue  # linha separadora da tabela
        if raw.strip().startswith("|") and raw.strip().endswith("|") and "|" in raw.strip()[1:-1]:
            out.append(" — ".join(c for c in _row_cells(raw) if c)); continue
        # citação: tira o "> " e mantém a linha
        line = _QUOTE_RE.sub("", raw)
        out.append(_norm_inline(line.rstrip()))
    # colapsa 3+ linhas em branco em no máximo uma
    txt = "\n".join(out)
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    return txt.strip()


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
        # qa/40 (regra do produto: modelo NÃO inventa número): sanidade dos
        # níveis devolvidos — preço <= 0 (o "0.0" do template passava como
        # proposta!), stop==alvo, ou geometria incoerente com a direção
        # declarada (alta exige alvo>stop; baixa o inverso) ⇒ níveis viram
        # None ("sem dado" > número inventado).
        st, av = proposal["stop"], proposal["alvo"]
        if st is not None and st <= 0:
            proposal["stop"] = st = None
        if av is not None and av <= 0:
            proposal["alvo"] = av = None
        if st is not None and av is not None:
            rec = str(obj.get("recomendacao") or "")
            dr = str(obj.get("direcao") or "")
            # O LADO vem da recomendação quando ela é DIRECIONAL; senão (Monitorar/
            # Aguardar/Não operar/vazio) cai na `direcao`. Antes só caía na direcao
            # com rec vazio, então um 'Monitorar' com direcao=Baixa e alvo ACIMA do
            # stop passava incoerente (achado do masstest-agentes-llm: MGLU3).
            _dir = ("Estudar alta", "Estudar baixa", "COMPRAR", "VENDER")
            alta = rec in ("Estudar alta", "COMPRAR") or (rec not in _dir and dr == "Alta")
            baixa = rec in ("Estudar baixa", "VENDER") or (rec not in _dir and dr == "Baixa")
            if st == av or (alta and av <= st) or (baixa and av >= st):
                proposal["stop"] = proposal["alvo"] = None
        corpo = str(obj.get("corpo") or obj.get("markdown") or obj.get("analise") or "").strip()
        # remove cercas de markdown que a IA as vezes embrulha em volta do corpo
        corpo = re.sub(r"^```[a-zA-Z]*\n?", "", corpo)
        corpo = re.sub(r"\n?```$", "", corpo).strip()
        text = (raw[:s] + raw[e:])
    text = text.replace("```json", "").replace("```", "").strip()
    # corpo final (markdown), sempre nao-vazio. Normalizado ao subconjunto que o
    # front renderiza — blindagem model-agnostic contra a troca de LLM (cada
    # modelo formata diferente); cobre corpo, síntese e texto bruto.
    markdown = normalize_markdown(
        corpo or _synth_markdown(detail) or text
    ) or "_A IA não retornou um corpo de análise legível._"
    return {"kpis": kpis, "detail": detail, "proposal": proposal, "markdown": markdown, "text": text}


def parse_analysis(raw: str):
    """Compatibilidade: (kpis | None, texto)."""
    r = parse_rich(raw)
    fallback = r["text"] or r["detail"]["resumo"] or (raw or "").strip()
    return r["kpis"], fallback
