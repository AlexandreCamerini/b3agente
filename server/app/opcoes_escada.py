"""Fase 48, Plano 04 (2026-10-05) — motor PURO do caminho B da aba Opções
(objetivo -> escada de degraus -> gráfico -> confirmar).

PURO por desenho: sem rede, sem banco, sem LLM, sem relógio. Recebe candidatos
já prontos de `opcoes_curadoria` (escada grátis) ou itens da cadeia do serviço
MCP (matriz paga, plano 48-07) e devolve, por degrau, TODA a leitura financeira
e textual da tela 3. O front só desenha: não soma, não subtrai, não compõe frase
(princípio 5 do CLAUDE.md — conta sempre determinística, nunca da IA).

Três pré-condições do UI-SPEC, verificadas no código em 2026-10-05:
  (1) `cartao_posicao.cenarios_da_estrutura` exige EXATAMENTE 1 breakeven (put
      protetora, call coberta e collar têm 1; senão devolve None e o degrau sai
      "sem gráfico", mantendo os números). Uma chamada por estrutura: este
      módulo chama 1x por degrau, só para obter a GRADE de preços.
  (2) `/mcp/possibilidades` NÃO devolve degraus (1 estrutura por vencimento por
      tese): os degraus vêm de um seletor determinístico do Boris, aqui, sobre
      a cadeia. A matriz paga usa `celulas_da_cadeia`, mantendo o custo 2N+1.
  (3) `opcoes_payoff` é por estrutura: um degrau = uma estrutura. TODA
      aritmética de payoff passa por `opcoes_payoff`.

Decisão de discricionariedade: os degraus da escada GRÁTIS vêm de
`opcoes_curadoria.candidatos_da_posicao`, o mesmo motor que as rotas de execução
re-derivam — escada e execução não divergem (defeito da quick 260915-ndt).

Convenções: valor indeterminável é `None` com motivo, nunca `0.0`. `perdaMaxima`
e `ganhoMaximo` são MAGNITUDES (>= 0); resultados em pontos de série e
marcadores são com sinal. Todo texto vem de `skill_ref.opcoes_escada_txt`.
"""
from __future__ import annotations

import copy
import re
from typing import Any

from . import cartao_posicao, opcoes_payoff, skill_ref, store
from .opcoes_curadoria import STRIKES_POR_POSICAO, id_candidato

OBJETIVOS = ("proteger", "renda", "collar")
TIPO_DO_OBJETIVO = {"proteger": "put_protecao", "renda": "call_coberta", "collar": "collar"}
DEGRAUS = 3
MAX_PONTOS_GRAFICO = 241
LOTE_MINIMO = 100

# Termos tocáveis por objetivo: (rótulo no texto, setor, verbete KB). O front só
# sublinha a 1ª ocorrência do `rotulo` no texto vindo do backend.
TERMOS_OBJETIVO = {
    "proteger": [("prêmio", "opc_premio", None), ("piso", None, "opc-piso"),
                 ("put protetora", "opc_put_protetora", None)],
    "renda": [("prêmio", "opc_premio", None), ("teto", None, "opc-teto"),
              ("venda coberta", None, "opc-call-coberta"), ("lastro", None, "opc-lastro")],
    "collar": [("prêmio", "opc_premio", None), ("piso", None, "opc-piso"),
               ("teto", None, "opc-teto"), ("collar", "opc_collar", None)],
}

# Marcadores do gráfico: numeração FIXA 1-5 (a legenda mantém o número mesmo
# quando um marcador está ausente), com o termo tocável de cada um.
_MARCADORES = (
    (1, "piso", None, "opc-piso"),
    (2, "equilibrio", None, "opc-equilibrio"),
    (3, "teto", None, "opc-teto"),
    (4, "perda_maxima", "opc_perda_maxima", None),
    (5, "ganho_maximo", None, None),
)
_AUSENTE_TXT = {"piso": "ausente_piso", "teto": "ausente_teto",
                "ganho_maximo": "ausente_ganho_maximo"}


# ───────────────────────────── utilitários

def _num(v: Any) -> float | None:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _positivo(v: Any) -> float | None:
    n = _num(v)
    return n if n is not None and n > 0 else None


def _t(modo: str, chave: str, **dados: Any) -> str | None:
    return skill_ref.opcoes_escada_txt(modo, chave, **{k: str(v) for k, v in dados.items()})


def _br(v: Any) -> str:
    return skill_ref.num_br(v)


def _r2(v: Any) -> float | None:
    n = _num(v)
    return None if n is None else round(n, 2) + 0.0


def _ddmm(iso: Any) -> str | None:
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", str(iso or ""))
    return f"{m.group(3)}/{m.group(2)}" if m else None


def _par(total: Any, por_acao: Any) -> dict:
    return {"total": _r2(total), "porAcao": _r2(por_acao)}


# ───────────────────────────── objetivos

def objetivos(posicao: Any, modo: str) -> list[dict]:
    """Três objetivos, na ordem proteger/renda/collar, com disponibilidade pelo
    lastro livre (mesmo critério do motor de execução: `store.qty_livre >= 100`)."""
    motivo_chave, motivo = None, None
    if not isinstance(posicao, dict) or not posicao.get("qty"):
        motivo_chave = "hub_vazio_titulo"
        motivo = _t(modo, motivo_chave)
    else:
        livres = store.qty_livre(posicao)
        if livres < LOTE_MINIMO:
            if int(posicao.get("qtyTravada") or 0) > 0:
                motivo_chave, motivo = "lastro_travado", _t(modo, "lastro_travado")
            else:
                motivo_chave = "lastro_insuficiente"
                motivo = _t(modo, motivo_chave, livres=livres, necessarias=LOTE_MINIMO)
    out = []
    for oid in OBJETIVOS:
        out.append({
            "id": oid,
            "titulo": _t(modo, f"objetivo_{oid}_titulo"),
            "descricao": _t(modo, f"objetivo_{oid}_desc"),
            "perde": _t(modo, f"objetivo_{oid}_perde"),
            "disponivel": motivo is None,
            "motivo": motivo,
            "motivoChave": motivo_chave,
            "termos": [{"rotulo": r, "setor": s, "kb": k} for r, s, k in TERMOS_OBJETIVO[oid]],
        })
    return out


# ───────────────────────────── seleção de degraus

def _strike_put(c: dict) -> float | None:
    if _num(c.get("strikePut")) is not None:
        return float(c["strikePut"])
    for p in c.get("pernasContratos") or []:
        if str(p.get("optionType")).lower() == "put":
            return _num(p.get("strike"))
    return None


def _strike_call(c: dict) -> float | None:
    if _num(c.get("strikeCall")) is not None:
        return float(c["strikeCall"])
    for p in c.get("pernasContratos") or []:
        if str(p.get("optionType")).lower() == "call":
            return _num(p.get("strike"))
    return None


def _indices_dos_degraus(n: int) -> list[int]:
    """0, meio, último quando há mais de 3; senão todos."""
    return list(range(n)) if n <= DEGRAUS else [0, n // 2, n - 1]


def escolher_degraus(candidatos: Any, objetivo: str, vencimento: Any) -> list[dict]:
    """Até 3 candidatos do objetivo e vencimento pedidos. Ordem: proteger e collar
    por strike da put DECRESCENTE (perto do spot = "mais protegido"); renda por
    strike da call CRESCENTE. Dedupe por `idCandidato`."""
    tipo = TIPO_DO_OBJETIVO.get(objetivo)
    chaveados = []
    for c in candidatos or []:
        if not isinstance(c, dict) or c.get("tipo") != tipo or c.get("expiration") != vencimento:
            continue
        if objetivo == "renda":
            k = _num(c.get("strike"))
            ordem = k
        elif objetivo == "proteger":
            k = _num(c.get("strike"))
            ordem = None if k is None else -k
        else:
            k = _strike_put(c)
            ordem = None if k is None else -k
        if ordem is not None:
            chaveados.append((ordem, c))
    chaveados.sort(key=lambda x: x[0])
    vistos, unicos = set(), []
    for _, c in chaveados:
        cid = c.get("idCandidato")
        if cid in vistos:
            continue
        vistos.add(cid)
        unicos.append(c)
    return [unicos[i] for i in _indices_dos_degraus(len(unicos))]


def pernas_do_candidato(cand: dict) -> list[dict]:
    """Pernas de OPÇÃO (por unidade) do candidato. `premioUnitario` da put e do
    call/put isolados é fluxo de caixa (negativo = paga): aqui vira magnitude."""
    tipo = cand.get("tipo")
    if tipo == "collar":
        out = []
        for p in cand.get("pernasContratos") or []:
            ot = str(p.get("optionType")).lower()
            out.append({"tipo": "CALL" if ot == "call" else "PUT",
                        "lado": p.get("lado"), "strike": p.get("strike"),
                        "premio": p.get("premioUnitario"), "contrato": p.get("contractSymbol")})
        return out
    prem = _num(cand.get("premioUnitario"))
    prem = None if prem is None else abs(prem)
    if tipo == "call_coberta":
        return [{"tipo": "CALL", "lado": "venda", "strike": cand.get("strike"),
                 "premio": prem, "contrato": cand.get("contractSymbol")}]
    return [{"tipo": "PUT", "lado": "compra", "strike": cand.get("strike"),
             "premio": prem, "contrato": cand.get("contractSymbol")}]


# ───────────────────────────── números (tudo via opcoes_payoff)

def _legs_validas(pernas: list[dict]) -> bool:
    return bool(pernas) and all(
        _positivo(p.get("premio")) is not None and _positivo(p.get("strike")) is not None
        and p.get("lado") in ("compra", "venda") and p.get("tipo") in ("CALL", "PUT")
        for p in pernas)


def _entradas(pernas: list[dict], qtd: int, pm: float) -> tuple[list, list, list, list]:
    def op(q):
        return [{"tipo": p["tipo"], "lado": p["lado"], "strike": float(p["strike"]),
                 "premio": float(p["premio"]), "quantidade": q, "contrato": p.get("contrato")}
                for p in pernas]
    acao_t = {"tipo": "ACAO", "lado": "compra", "strike": 0, "premio": pm, "quantidade": qtd}
    acao_u = dict(acao_t, quantidade=1)
    return [acao_t] + op(qtd), [acao_u] + op(1), [acao_t], [acao_u]


def _numeros(pernas: list[dict], qtd: Any, pm: Any) -> dict | None:
    """Núcleo financeiro. `None` quando qualquer insumo é indeterminável."""
    q, pmv = _positivo(qtd), _positivo(pm)
    if q is None or pmv is None or not _legs_validas(pernas):
        return None
    q = int(q)
    ent_t, ent_u, acoes_t, acoes_u = _entradas(pernas, q, pmv)
    try:
        perfil_t = opcoes_payoff.perfil_da_estrutura(ent_t)
        perfil_u = opcoes_payoff.perfil_da_estrutura(ent_u)
    except ValueError:
        return None
    pago_u = sum(float(p["premio"]) for p in pernas if p["lado"] == "compra")
    receb_u = sum(float(p["premio"]) for p in pernas if p["lado"] == "venda")
    tem_c = any(p["lado"] == "compra" for p in pernas)
    tem_v = any(p["lado"] == "venda" for p in pernas)
    put_c = next((float(p["strike"]) for p in pernas if p["tipo"] == "PUT" and p["lado"] == "compra"), None)
    call_v = next((float(p["strike"]) for p in pernas if p["tipo"] == "CALL" and p["lado"] == "venda"), None)

    def bloco(perfil, f):
        return {"perdaMaxima": _r2(perfil["perda_maxima"]), "ganhoMaximo": _r2(perfil["ganho_maximo"]),
                "premioPago": _r2(pago_u * f) if tem_c else None,
                "premioRecebido": _r2(receb_u * f) if tem_v else None,
                "liquido": _r2((receb_u - pago_u) * f)}
    bes = perfil_u["breakevens"]
    return {
        "q": q, "pm": pmv, "perfil_t": perfil_t, "perfil_u": perfil_u,
        "ent": (ent_t, ent_u, acoes_t, acoes_u),
        "total": bloco(perfil_t, q), "porAcao": bloco(perfil_u, 1),
        "equilibrio": _r2(bes[0]) if len(bes) == 1 else None,
        "piso": put_c, "teto": call_v,
        "ilimitado": {"perda": bool(perfil_u["perda_ilimitada"]), "ganho": bool(perfil_u["ganho_ilimitado"])},
    }


def _vazio() -> dict:
    chaves = ("perdaMaxima", "ganhoMaximo", "premioPago", "premioRecebido", "liquido")
    return {k: None for k in chaves}


def _colunas(objetivo: str, total: dict, por_acao: dict, piso: Any, modo: str) -> list[dict]:
    def col(chave, rotulo_chave, t, a, sinal):
        return {"chave": chave, "rotulo": _t(modo, rotulo_chave),
                "valor": {"total": t, "porAcao": a}, "sinal": sinal, "fracao": None}
    perda = col("perda_maxima", "col_perda_maxima", total["perdaMaxima"], por_acao["perdaMaxima"], "negativo")
    ganho = col("ganho_maximo", "col_ganho_maximo", total["ganhoMaximo"], por_acao["ganhoMaximo"], "positivo")
    if objetivo == "proteger":
        return [perda, col("custo_protecao", "col_custo_protecao", total["premioPago"],
                           por_acao["premioPago"], "negativo")]
    if objetivo == "renda":
        nota = {"chave": "nota_sem_piso", "rotulo": _t(modo, "nota_sem_piso"),
                "valor": {"total": None, "porAcao": None}, "sinal": None, "fracao": None}
        return [ganho, col("premio_recebido", "col_premio_recebido", total["premioRecebido"],
                           por_acao["premioRecebido"], "positivo"), nota]
    lt, la = total["liquido"], por_acao["liquido"]
    custa = lt is not None and lt < 0
    liq = col("liquido", "col_liquido_custa" if custa else "col_liquido_recebe",
              None if lt is None else abs(lt), None if la is None else abs(la),
              "negativo" if custa else "positivo")
    return [perda, ganho, liq]


def _frase_risco(modo: str, n: dict, venc_iso: Any) -> str:
    t, a = n["total"], n["porAcao"]
    if t["perdaMaxima"] is None and not n["ilimitado"]["perda"]:
        return _t(modo, "dado_insuficiente")
    q = n["q"]
    premio = abs(a["liquido"])
    if n["piso"] is not None:
        pior = _t(modo, "risco_pior", perdaTotal=_br(t["perdaMaxima"]), qtd=skill_ref.num_br_inteiro(q),
                  perdaAcao=_br(a["perdaMaxima"]), piso=_br(n["piso"]))
    else:
        pior = _t(modo, "risco_pior_sem_piso", perdaTotal=_br(t["perdaMaxima"]), premio=_br(premio))
    if n["ilimitado"]["ganho"]:
        melhor = _t(modo, "risco_melhor_sem_teto")
    elif t["ganhoMaximo"] is not None and n["teto"] is not None:
        melhor = _t(modo, "risco_melhor", ganhoTotal=_br(t["ganhoMaximo"]), qtd=skill_ref.num_br_inteiro(q),
                    ganhoAcao=_br(a["ganhoMaximo"]), teto=_br(n["teto"]))
    else:
        melhor = _t(modo, "dado_insuficiente")
    if n["equilibrio"] is not None:
        eq = _t(modo, "risco_equilibrio", be=_br(n["equilibrio"]), venc=_ddmm(venc_iso) or "")
    else:
        eq = _t(modo, "risco_sem_equilibrio")
    return " ".join(x for x in (pior, melhor, eq) if x)


def _termos(n: dict, ticker: str, venc_iso: Any) -> dict:
    t, a, q = n["total"], n["porAcao"], n["q"]
    venc = _ddmm(venc_iso)
    liq_t, liq_a = t["liquido"], a["liquido"]
    estado = "pago" if liq_t < 0 else ("recebido" if liq_t > 0 else None)
    strike = n["strikes_ref"] if "strikes_ref" in n else None
    premio = {"ticker": ticker, "strike": strike, "premio": abs(liq_a), "premioTotal": abs(liq_t),
              "qtd": q, "venc": venc, "estado": estado}
    perda = {"ticker": ticker, "piso": n["piso"], "perdaTotal": t["perdaMaxima"],
             "perdaAcao": a["perdaMaxima"], "premio": abs(liq_a), "qtd": q, "venc": venc,
             "estado": "com_piso" if n["piso"] is not None else "sem_piso"}
    # chave sem valor sai do dicionário: o conceito descarta o parágrafo em vez de mentir
    return {"opc_premio": {k: v for k, v in premio.items() if v is not None},
            "opc_perda_maxima": {k: v for k, v in perda.items() if v is not None}}


# ───────────────────────────── gráfico

def _reamostrar(precos: set, manter: set, limite: int) -> list[float]:
    ordenados = sorted(precos)
    if len(ordenados) <= limite:
        return ordenados
    resto = [p for p in ordenados if p not in manter]
    vagas = max(limite - len(manter), 2)
    n = len(resto)
    escolhidos = {resto[round(i * (n - 1) / (vagas - 1))] for i in range(vagas)}
    return sorted(escolhidos | manter)


def _resultado(entrada: list, preco: float) -> float:
    return round(opcoes_payoff.resultado_no_vencimento(entrada, preco), 2) + 0.0


def _linha(n: dict, preco: float) -> dict:
    ent_t, ent_u, acoes_t, acoes_u = n["ent"]
    so_t, so_u = _resultado(acoes_t, preco), _resultado(acoes_u, preco)
    com_t, com_u = _resultado(ent_t, preco), _resultado(ent_u, preco)
    d_t, d_u = round(com_t - so_t, 2), round(com_u - so_u, 2)
    return {"preco": preco, "soAcoes": {"total": so_t, "porAcao": so_u},
            "comEstrutura": {"total": com_t, "porAcao": com_u},
            "diferenca": {"total": abs(d_t), "porAcao": abs(d_u)},
            "efeito": "melhora" if d_t > 0 else ("reduz" if d_t < 0 else "igual")}


def _y(n: dict, preco: float) -> dict:
    ent_t, ent_u, _, _ = n["ent"]
    return {"total": _resultado(ent_t, preco), "porAcao": _resultado(ent_u, preco)}


def _grafico(n: dict, objetivo: str, spot: Any, ticker: str, venc_iso: Any, modo: str):
    """(grafico|None, motivo_sem_grafico|None)."""
    sem = _t(modo, "sem_grafico", motivo=_t(modo, "dado_insuficiente"))
    pt, pu = n["perfil_t"], n["perfil_u"]
    faixa = {"breakevens": pt["breakevens"], "teto": n["teto"], "piso": n["piso"],
             "ganhoMaximo": pt["ganho_maximo"], "perdaMaxima": pt["perda_maxima"]}
    try:
        cen = cartao_posicao.cenarios_da_estrutura(
            n["ent"][0], faixa, TIPO_DO_OBJETIVO[objetivo], spot, venc_iso, ticker, "educacional")
    except ValueError:
        cen = None
    sim = (cen or {}).get("simulador")
    if not sim or not sim.get("pontos"):
        return None, sem
    xmin, xmax = float(sim["min"]), float(sim["max"])
    hoje = _r2(spot)
    nomeados = {round(x, 2) for x in (n["piso"], n["equilibrio"], n["teto"], hoje, n["pm"])
                if x is not None and xmin <= x <= xmax}
    precos = {float(p["preco"]) for p in sim["pontos"]} | nomeados | {xmin, xmax}
    serie = _reamostrar(precos, nomeados | {xmin, xmax}, MAX_PONTOS_GRAFICO)
    pontos = [_linha(n, p) for p in serie]

    t, a = n["total"], n["porAcao"]
    presentes: dict[str, dict] = {}
    if n["piso"] is not None:
        y = _y(n, n["piso"])
        presentes["piso"] = {"preco": n["piso"], "y": y, "valor": y}
    if n["equilibrio"] is not None:
        z = {"total": 0.0, "porAcao": 0.0}
        presentes["equilibrio"] = {"preco": n["equilibrio"], "y": z, "valor": z}
    if n["teto"] is not None:
        y = _y(n, n["teto"])
        presentes["teto"] = {"preco": n["teto"], "y": y, "valor": y}
    if t["perdaMaxima"] is not None:
        x = n["piso"] if n["piso"] is not None else serie[0]
        presentes["perda_maxima"] = {"preco": x, "y": _y(n, x),
                                     "valor": _par(-t["perdaMaxima"], -a["perdaMaxima"])}
    if t["ganhoMaximo"] is not None and n["teto"] is not None:
        presentes["ganho_maximo"] = {"preco": n["teto"], "y": _y(n, n["teto"]),
                                     "valor": _par(t["ganhoMaximo"], a["ganhoMaximo"])}
    marcadores, legenda, ausentes = [], [], []
    for num, chave, setor, kb in _MARCADORES:
        m = presentes.get(chave)
        if m is None:
            if chave in _AUSENTE_TXT:
                ausentes.append({"n": num, "chave": chave, "texto": _t(modo, _AUSENTE_TXT[chave])})
            continue
        marcadores.append({"n": num, "chave": chave, **m})
        if chave in ("perda_maxima", "ganho_maximo"):
            frase = _t(modo, f"legenda_{chave}", valor=_br(abs(m["valor"]["total"])))
        else:
            frase = _t(modo, f"legenda_{chave}", preco=_br(m["preco"]))
        legenda.append({"n": num, "chave": chave, "rotulo": _t(modo, f"marcador_{chave}"),
                        "setor": setor, "kb": kb, "valor": m["valor"], "frase": frase})

    venc = _ddmm(venc_iso) or ""
    q = skill_ref.num_br_inteiro(n["q"])
    pior = f"R$ {_br(t['perdaMaxima'])}" if t["perdaMaxima"] is not None else _t(modo, "dado_insuficiente")
    pior_a = f"R$ {_br(a['perdaMaxima'])}" if a["perdaMaxima"] is not None else _t(modo, "dado_insuficiente")
    if t["ganhoMaximo"] is not None:
        melhor, melhor_a = f"R$ {_br(t['ganhoMaximo'])}", f"R$ {_br(a['ganhoMaximo'])}"
    elif n["ilimitado"]["ganho"]:
        melhor = melhor_a = _t(modo, "ausente_ganho_maximo")
    else:
        melhor = melhor_a = _t(modo, "dado_insuficiente")
    be = f"R$ {_br(n['equilibrio'])}" if n["equilibrio"] is not None else _t(modo, "dado_insuficiente")
    aria = {
        "total": _t(modo, "grafico_aria", ticker=ticker, venc=venc, pior=pior, melhor=melhor, be=be,
                    unidade=_t(modo, "unidade_total", qtd=q)),
        "porAcao": _t(modo, "grafico_aria", ticker=ticker, venc=venc, pior=pior_a, melhor=melhor_a,
                      be=be, unidade=_t(modo, "unidade_acao")),
    }
    ys_t = [v for p in pontos for v in (p["soAcoes"]["total"], p["comEstrutura"]["total"])]
    ys_a = [v for p in pontos for v in (p["soAcoes"]["porAcao"], p["comEstrutura"]["porAcao"])]
    grafico = {
        "xMin": serie[0], "xMax": serie[-1], "hoje": hoje, "precoMedio": _r2(n["pm"]),
        "y": {"total": {"min": min(ys_t), "max": max(ys_t)},
              "porAcao": {"min": min(ys_a), "max": max(ys_a)}},
        "pontos": pontos, "marcadores": marcadores, "ausentes": ausentes,
        "legenda": legenda, "aria": aria,
    }
    return grafico, None


def _tabela(n: dict, grafico: dict | None, spot: Any) -> list[dict]:
    precos = {round(x, 2) for x in (n["piso"], n["equilibrio"], n["teto"], _r2(spot), n["pm"])
              if x is not None}
    if grafico:
        precos |= {grafico["xMin"], grafico["xMax"]}
    linhas = []
    for p in sorted(precos):
        l = _linha(n, p)
        linhas.append({"preco": p, "soAcoes": l["soAcoes"], "comEstrutura": l["comEstrutura"]})
    return linhas


# ───────────────────────────── leitura / degrau

def leitura(pernas: list[dict], qtd: Any, preco_medio: Any, spot: Any, ticker: str,
            objetivo: str, vencimento_iso: Any, indice: int, modo: str) -> dict:
    """Leitura completa de UM degrau. Insumo indeterminável (prêmio ausente ou
    <= 0, PM ausente...) devolve os números `None` com `motivo` — nunca 0.0."""
    nome = f"degrau_{objetivo}_{indice}"
    strikes = {
        "put": next((_num(p.get("strike")) for p in pernas if p.get("tipo") == "PUT"), None),
        "call": next((_num(p.get("strike")) for p in pernas if p.get("tipo") == "CALL"), None),
    }
    base = {"nome": nome, "rotulo": _t(modo, nome), "objetivo": objetivo, "vencimento": vencimento_iso,
            "vencimentoTexto": _ddmm(vencimento_iso), "strikes": strikes,
            "qtdAcoes": int(qtd) if _positivo(qtd) is not None else None}
    n = _numeros(pernas, qtd, preco_medio)
    if n is None:
        motivo = _t(modo, "dado_insuficiente")
        return {**base, "total": _vazio(), "porAcao": _vazio(), "equilibrio": None, "piso": None,
                "teto": None, "ilimitado": {"perda": None, "ganho": None},
                "colunas": _colunas(objetivo, _vazio(), _vazio(), None, modo),
                "fraseRisco": motivo, "termos": {"opc_premio": None, "opc_perda_maxima": None},
                "grafico": None, "motivoSemGrafico": _t(modo, "sem_grafico", motivo=motivo),
                "tabela": [], "motivo": motivo}
    n["strikes_ref"] = strikes["put"] if n["total"]["liquido"] < 0 else strikes["call"]
    grafico, sem = _grafico(n, objetivo, spot, ticker, vencimento_iso, modo)
    return {**base, "precoMedio": _r2(n["pm"]), "total": n["total"], "porAcao": n["porAcao"],
            "equilibrio": n["equilibrio"], "piso": n["piso"], "teto": n["teto"],
            "ilimitado": n["ilimitado"], "colunas": _colunas(objetivo, n["total"], n["porAcao"], n["piso"], modo),
            "fraseRisco": _frase_risco(modo, n, vencimento_iso),
            "termos": _termos(n, ticker, vencimento_iso),
            "grafico": grafico, "motivoSemGrafico": sem, "tabela": _tabela(n, grafico, spot),
            "motivo": None}


def degrau_do_candidato(cand: dict, indice: int, objetivo: str, posicao: Any, spot: Any,
                        ticker: str, modo: str) -> dict:
    """Degrau da escada GRÁTIS: a leitura + id/execução/liquidez COPIADOS do
    candidato (a execução re-deriva o mesmo candidato; nada é recalculado)."""
    pm = posicao.get("avg") if isinstance(posicao, dict) else None
    d = leitura(pernas_do_candidato(cand), cand.get("qtyAcoes"), pm, spot, ticker, objetivo,
                cand.get("expiration"), indice, modo)
    d["id"] = cand.get("idCandidato")
    d["execucao"] = {
        "executavel": True, "tipo": cand.get("tipo"), "contractSymbol": cand.get("contractSymbol"),
        "expiration": cand.get("expiration"), "contratos": cand.get("contratos"),
        "qtyAcoes": cand.get("qtyAcoes"), "idCandidato": cand.get("idCandidato"),
        "pernasContratos": copy.deepcopy(cand.get("pernasContratos")),
    }
    d["liquidez"] = copy.deepcopy(cand.get("liquidez"))
    return d


# ───────────────────────────── matriz (cadeia do serviço MCP)

def _itens_validos(itens: Any) -> list[dict]:
    return [i for i in itens or [] if isinstance(i, dict)
            and _positivo(i.get("strike")) is not None and _positivo(i.get("premio")) is not None]


def celulas_da_cadeia(puts: Any, calls: Any, spot: Any, posicao: Any, objetivo: str,
                      vencimento: Any, ticker: str, modo: str) -> list[dict]:
    """3 células (sem gráfico) de um vencimento, na MESMA régua da escada.
    A peneira de negociabilidade é do CHAMADOR (rota 48-07): este módulo puro
    não importa o cliente do serviço. Contrato sem prêmio é pulado."""
    s = _positivo(spot)
    pm = posicao.get("avg") if isinstance(posicao, dict) else None
    qtd = (store.qty_livre(posicao) // LOTE_MINIMO) * LOTE_MINIMO if isinstance(posicao, dict) else 0
    ps = sorted((i for i in _itens_validos(puts) if s is not None and float(i["strike"]) <= s),
                key=lambda i: -float(i["strike"]))[:STRIKES_POR_POSICAO]
    cs = sorted((i for i in _itens_validos(calls) if s is not None and float(i["strike"]) > s),
                key=lambda i: float(i["strike"]))[:STRIKES_POR_POSICAO]
    if objetivo == "renda":
        fontes = cs
    else:
        fontes = ps
    if objetivo == "collar" and not cs:
        fontes = []
    if qtd <= 0:
        fontes = []
    escolhidas = [fontes[i] for i in _indices_dos_degraus(len(fontes))]

    out = []
    for i in range(DEGRAUS):
        nome = f"degrau_{objetivo}_{i}"
        vazio = {"indice": i, "nome": nome, "id": None, "pernas": None, "total": None,
                 "porAcao": None, "equilibrio": None, "ilimitado": None, "colunas": None,
                 "motivo": _t(modo, "sem_estrutura", ticker=ticker)}
        if i >= len(escolhidas):
            out.append(vazio)
            continue
        it = escolhidas[i]
        k, pr = float(it["strike"]), float(it["premio"])
        if objetivo == "proteger":
            pernas = [{"tipo": "PUT", "lado": "compra", "strike": k, "premio": pr, "contrato": it.get("contrato")}]
            cid = id_candidato("put_protecao", ticker, vencimento, it.get("contrato"))
        elif objetivo == "renda":
            pernas = [{"tipo": "CALL", "lado": "venda", "strike": k, "premio": pr, "contrato": it.get("contrato")}]
            cid = id_candidato("call_coberta", ticker, vencimento, it.get("contrato"))
        else:
            c0 = cs[0]
            pernas = [{"tipo": "CALL", "lado": "venda", "strike": float(c0["strike"]),
                       "premio": float(c0["premio"]), "contrato": c0.get("contrato")},
                      {"tipo": "PUT", "lado": "compra", "strike": k, "premio": pr,
                       "contrato": it.get("contrato")}]
            cid = id_candidato("collar", ticker, vencimento, None,
                               strike_call=float(c0["strike"]), strike_put=k)
        n = _numeros(pernas, qtd, pm)
        if n is None:
            out.append(vazio)
            continue
        out.append({"indice": i, "nome": nome, "id": cid, "pernas": pernas, "total": n["total"],
                    "porAcao": n["porAcao"], "equilibrio": n["equilibrio"], "ilimitado": n["ilimitado"],
                    "colunas": _colunas(objetivo, n["total"], n["porAcao"], n["piso"], modo),
                    "motivo": None})
    return out


def normalizar_barras(degraus: list[dict]) -> list[dict]:
    """Preenche `colunas[i].fracao` em [0,1] = |valor| / max |valor| da mesma
    coluna entre os degraus (por `chave`). Valor `None` -> fracao `None`."""
    maximos: dict[str, float] = {}
    for d in degraus:
        for c in (d or {}).get("colunas") or []:
            v = _num(((c.get("valor") or {}).get("total")))
            if v is not None:
                maximos[c["chave"]] = max(maximos.get(c["chave"], 0.0), abs(v))
    for d in degraus:
        for c in (d or {}).get("colunas") or []:
            v = _num(((c.get("valor") or {}).get("total")))
            m = maximos.get(c["chave"])
            c["fracao"] = None if v is None or m is None else (abs(v) / m if m > 0 else 0.0)
    return degraus
