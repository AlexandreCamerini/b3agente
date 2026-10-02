"""Motor puro de leitura de estrutura de opções por ativo (Fase 44, Plano 02).

Módulo PURO — sem rede, sem banco, sem LLM, sem leitura de relógio (`hoje`
entra por argumento) — mesma disciplina de `opcoes_payoff.py` e
`opcoes_lastreadas.py`. Toda frase do payload vem de `skill_ref`
(`estrutura_posicao_txt` / `opcoes_lastreadas_txt`); nenhum texto de usuário
é escrito aqui.

Decisões (44-CONTEXT):
- D-01/D-03: recebe TODAS as `optionPositions` do escopo, filtra pelo
  underlying, lista todas as pernas e classifica o CONJUNTO (call coberta,
  put de proteção, collar). Qualquer outro conjunto: nome None, pernas ainda
  listadas.
- D-02: cálculo só no servidor; o front recebe o payload pronto (sem espelho).
- D-04: perna vendida é marcada pelo ASK (o que custa recomprar), comprada
  pelo BID (o que rende vender); lado ausente cai no `lastPrice` com origem
  "last" explícita; nenhum → None. Nunca mid, nunca estimado.
- D-05: com perna (ou ação) sem cotação o total é None e `incompleto` True;
  as partes conhecidas aparecem separadas. Nunca 0 no lugar de desconhecido.
- D-08: vencimentos divergentes → sem faixa (o payoff recusa aproximar), todas
  as pernas listadas, estado pelo vencimento mais próximo.
- D-09: faixa só na parte coberta (`qtdBase`); call vendida acima das ações →
  sem faixa (perda ilimitada); put excedente → `descoberta`.
- ESTR-04 (discrição documentada): dias em CORRIDOS, mesma convenção de
  `opcoes_lastreadas._dias_ate`. "Exercício provável" = dentro do dinheiro
  por qualquer valor, estrito (CALL spot > strike, PUT spot < strike), porque
  a B3 exerce automaticamente a opção ITM no vencimento — leitura "se
  vencesse hoje". Precedência: vencida > premio_indisponivel >
  exercicio_provavel > ate_5_dias > vigente.
- D-07/ESTR-05: `abertaSemProposta` é eixo SEPARADO do estado — a estrutura
  nunca some. `encerrar` exige `lastPrice` numérico > 0 porque é o preço que
  `options_lastreada_fechar` (main.py) executa; permitir um encerramento que
  a rota recusaria seria afirmar algo falso.
- Fase 46 (D-01/D-04): `ler_estrutura` ganha as chaves ADITIVAS `cenarios` e
  `didatica` (motor puro `cartao_posicao`, sobre a MESMA `entrada` do payoff);
  nenhuma chave anterior muda. Falha no cálculo → ambas None.
"""
from __future__ import annotations

import datetime as _dt
from typing import Any, Optional

from . import cartao_posicao, options_quant, opcoes_payoff, skill_ref

_CALL, _PUT = "CALL", "PUT"


def _num(v: Any) -> Optional[float]:
    """Número > 0; bool, texto, None, zero e negativo → None (T-44-03)."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    v = float(v)
    return v if v == v and v > 0 else None


def _num_nn(v: Any) -> Optional[float]:
    """Número >= 0 (prêmio de entrada pode, em tese, ser 0)."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    v = float(v)
    return v if v == v and v >= 0 else None


def _r2(v: Optional[float]) -> Optional[float]:
    return None if v is None else round(v, 2)


# 46.1 (G-08): causa determinística da falta de prêmio atual (enum fechado).
MOTIVOS_SEM_COTACAO = ("fonte_indisponivel", "fora_da_cadeia", "sem_negocio", "sem_cotacao")


def _motivo_sem_cotacao(p: dict, contrato, status_cadeias) -> Optional[str]:
    """None se cotada ou sem lado; senão um de MOTIVOS_SEM_COTACAO."""
    if p["premioAtual"] is not None or p["lado"] is None:
        return None
    if isinstance(contrato, dict):
        return "sem_negocio"
    st = status_cadeias.get(p["vencimento"]) if isinstance(status_cadeias, dict) else None
    if st == "falha":
        return "fonte_indisponivel"
    if st == "ok":
        return "fora_da_cadeia"
    return "sem_cotacao"


def _perna(op: dict) -> dict:
    """Normaliza uma `optionPosition`. `side` ausente = comprada (modelo antigo).

    WR-04 (review Fase 44): `side` presente mas fora de {vendida, comprada}
    ("short", "sell"...) vira `lado=None` — o sinal não é adivinhado. Sem lado
    não há marcação, o resultado da perna é None e a estrutura sai incompleta.
    """
    bruto = op.get("side")
    lado_txt = str(bruto).strip().lower() if bruto is not None else ""
    if lado_txt == "vendida":
        lado = "venda"
    elif lado_txt in ("", "comprada"):
        lado = "compra"
    else:
        lado = None
    return {
        "id": op.get("id"),
        "tipo": str(op.get("optionType") or "").upper(),
        "lado": lado,
        "strike": _num(op.get("strike")),
        "vencimento": op.get("expiration"),
        "quantidade": _num(op.get("qty")),
        "premioEntrada": _num_nn(op.get("avg")),
    }


def _marcar(perna: dict, contrato: Optional[dict], modo: str) -> tuple:
    """(premioAtual, origem, origemTexto) — D-04."""
    if not isinstance(contrato, dict) or perna["lado"] is None:
        return None, None, None
    principal, origem = ((contrato.get("ask"), "ask") if perna["lado"] == "venda"
                         else (contrato.get("bid"), "bid"))
    v = _num(principal)
    if v is not None:
        return v, origem, None
    v = _num(contrato.get("lastPrice"))
    if v is not None:
        return v, "last", skill_ref.estrutura_posicao_txt(
            modo, "origem_last", perna=perna["id"])
    return None, None, None


def _classificar(pernas: list) -> Optional[str]:
    conj = {(p["tipo"], p["lado"]) for p in pernas}
    if conj == {(_CALL, "venda")}:
        return "call_coberta"
    if conj == {(_PUT, "compra")}:
        return "put_protecao"
    if conj == {(_CALL, "venda"), (_PUT, "compra")}:
        return "collar"
    return None


def _sem_dados(p: dict) -> bool:
    return p["lado"] is None or p["premioEntrada"] is None or p["quantidade"] is None


def _resultado_perna(p: dict) -> Optional[float]:
    atual, entrada, qtd = p["premioAtual"], p["premioEntrada"], p["quantidade"]
    if atual is None or entrada is None or qtd is None:
        return None
    dif = entrada - atual if p["lado"] == "venda" else atual - entrada
    return round(dif * qtd, 2)


def _data(v: Any) -> Optional[_dt.date]:
    if not isinstance(v, str):
        return None
    try:
        return _dt.date.fromisoformat(v[:10])
    except ValueError:
        return None


def _venc_norm(v: Any) -> Any:
    d = _data(v)
    return d if d else v


def _venc_iso(v: Any) -> Any:
    d = _data(v)
    return d.isoformat() if d else v


def _br(d: _dt.date) -> str:
    return d.strftime("%d/%m/%Y")


def _liquidez(contrato: Optional[dict]) -> Optional[dict]:
    if not isinstance(contrato, dict):
        return None
    sc = options_quant.liquidity_score(
        _num(contrato.get("volume")), _num(contrato.get("openInterest")),
        _num(contrato.get("bid")), _num(contrato.get("ask")))["score"]
    return {"score": sc, "faixa": options_quant.faixa_de_liquidez(sc)}


def _faixa(pernas, acoes, nome, underlying, modo):
    """(faixa|None, motivo|None, motivoTexto|None, descoberta, descobertaTexto, entrada|None)."""
    t = lambda k, **d: skill_ref.estrutura_posicao_txt(modo, k, **d)  # noqa: E731
    if nome is None:
        return None, "fora_da_biblioteca", t("nome_fora_da_biblioteca"), False, None, None
    if acoes is None:
        return None, "sem_acoes", t("faixa_sem_acoes", ticker=underlying), False, None, None
    s = acoes["quantidade"]
    q_call = sum(p["quantidade"] or 0 for p in pernas if p["tipo"] == _CALL)
    q_put = sum(p["quantidade"] or 0 for p in pernas if p["tipo"] == _PUT)
    if q_call > s:
        txt = t("faixa_perna_sem_lastro", quantidade=skill_ref.num_br_inteiro(q_call - s))
        return None, "perna_vendida_sem_lastro", txt, True, txt, None
    # WR-03: `descoberta` (put excedente) é fato das quantidades, independe de
    # vencimento/dados de preço — calculada antes e devolvida em todo retorno.
    base = min(s, max(q_call, q_put))
    escala = s / q_put if q_put > s else 1.0
    descoberta = q_put > s
    desc_txt = t("descoberta_put", quantidade=skill_ref.num_br_inteiro(q_put - s),
                 qtdBase=skill_ref.num_br_inteiro(base)) if descoberta else None
    # WR-06: "2026-10-16" e "2026-10-16T00:00:00" são o mesmo dia — compara
    # pela data parseada (dado não parseável segue opaco, comparado cru).
    divergem = {_venc_norm(p["vencimento"]) for p in pernas if p["vencimento"] is not None}
    if len(divergem) > 1:
        ordem = sorted(divergem, key=str)
        txt = t("faixa_vencimentos_diferentes", vencimentos=" e ".join(
            _br(v) if isinstance(v, _dt.date) else str(v) for v in ordem))
        return None, "vencimentos_diferentes", txt, descoberta, desc_txt, None
    pm = acoes["precoMedio"]
    if pm is None or any(p["strike"] is None or p["quantidade"] is None
                         or p["premioEntrada"] is None for p in pernas):
        return None, "dados_insuficientes", t("faixa_dados_insuficientes"), descoberta, desc_txt, None
    entrada = [{"tipo": "ACAO", "lado": "compra", "strike": 0, "premio": pm, "quantidade": base}]
    for p in pernas:
        entrada.append({
            "tipo": p["tipo"], "lado": p["lado"], "strike": p["strike"],
            "premio": p["premioEntrada"], "vencimento": _venc_iso(p["vencimento"]),
            "quantidade": p["quantidade"] * (escala if p["tipo"] == _PUT else 1.0),
            "contrato": p["id"]})
    try:
        perfil = opcoes_payoff.perfil_da_estrutura(entrada)
    except ValueError:
        return None, "dados_insuficientes", t("faixa_dados_insuficientes"), descoberta, desc_txt, None
    puts = [p["strike"] for p in pernas if p["tipo"] == _PUT and p["lado"] == "compra"]
    calls = [p["strike"] for p in pernas if p["tipo"] == _CALL and p["lado"] == "venda"]
    piso, teto = (max(puts) if puts else None), (min(calls) if calls else None)
    perda, ganho = _r2(perfil["perda_maxima"]), _r2(perfil["ganho_maximo"])
    # WR-01/WR-02 (review Fase 44): a quantidade citada em cada texto é a que a
    # PRÓPRIA perna cobre (nunca a base inteira) e cada caso indeterminável tem
    # frase própria — proteção/limite só é afirmado onde existe de fato.
    qtd_put = min(q_put, s)
    qtd_call = min(q_call, s)
    textos = []
    if piso is not None and perda is not None:
        textos.append(t("faixa_piso", piso=skill_ref.num_br(piso),
                        perdaMaxima=skill_ref.num_br(perda),
                        qtd=skill_ref.num_br_inteiro(qtd_put)))
    elif piso is not None:
        textos.append(t("faixa_piso_sem_perda", piso=skill_ref.num_br(piso),
                        qtd=skill_ref.num_br_inteiro(qtd_put)))
    elif perda is not None:
        textos.append(t("faixa_sem_piso", perdaMaxima=skill_ref.num_br(perda)))
    if teto is None:
        textos.append(t("faixa_sem_teto"))
    elif ganho is not None:
        textos.append(t("faixa_teto", teto=skill_ref.num_br(teto),
                        ganhoMaximo=skill_ref.num_br(ganho),
                        qtd=skill_ref.num_br_inteiro(qtd_call)))
    else:
        textos.append(t("faixa_teto_parcial", teto=skill_ref.num_br(teto),
                        qtd=skill_ref.num_br_inteiro(qtd_call),
                        qtdBase=skill_ref.num_br_inteiro(base)))
    faixa = {"piso": piso, "teto": teto, "perdaMaxima": perda, "ganhoMaximo": ganho,
             "breakevens": [round(b, 2) for b in perfil["breakevens"]],
             "qtdBase": base, "qtdPut": qtd_put, "textos": textos}
    return faixa, None, None, descoberta, desc_txt, entrada


def _encerrar_perna(p: dict, modo: str) -> dict:
    if p["dias"] is not None and p["dias"] < 0:
        return {"permitido": False, "motivo": "vencida",
                "texto": skill_ref.estrutura_posicao_txt(
                    modo, "encerrar_vencida", vencimento=_br(_data(p["vencimento"])))}
    if p["lado"] is None:
        return {"permitido": False, "motivo": "dados_invalidos",
                "texto": skill_ref.estrutura_posicao_txt(
                    modo, "resultado_dados_invalidos", pernas=str(p["id"]))}
    if p["premioAtual"] is None or not p["lastOk"]:
        return {"permitido": False, "motivo": "premio_indisponivel",
                "texto": skill_ref.estrutura_posicao_txt(
                    modo, "encerrar_premio_indisponivel", pernas=str(p["id"]))}
    return {"permitido": True, "motivo": None, "texto": None}


def _estado(pernas: list, spot: Optional[float], hoje, modo: str) -> dict:
    """ESTR-04 — precedência vencida > premio_indisponivel > exercicio_provavel
    > ate_5_dias > vigente. Referência = menor vencimento parseável.

    Decisão (WR-06, Fase 44): UMA perna vencida marca a estrutura inteira como
    `vencida` (conservador — a leitura agregada nunca finge vigência) e bloqueia
    o `encerrar` da estrutura; o `encerrar` de cada perna continua individual,
    então as pernas ainda vigentes seguem encerráveis pela lista `pernas`."""
    t = lambda k, **d: skill_ref.estrutura_posicao_txt(modo, k, **d)  # noqa: E731
    datas = [d for d in (_data(p["vencimento"]) for p in pernas) if d]
    ref = min(datas) if datas else None
    dias = (ref - hoje).days if ref else None
    ref_txt = _br(ref) if ref else None

    def out(estado, texto):
        return {"estado": estado, "texto": texto, "referencia": ref.isoformat() if ref else None,
                "dias": dias, "vencimentoTexto": ref_txt}

    if dias is not None and dias < 0:
        return out("vencida", t("estado_vencida", vencimento=ref_txt))
    sem_premio = [str(p["id"]) for p in pernas
                  if p["premioAtual"] is None and p["lado"] is not None]
    if sem_premio:
        return out("premio_indisponivel", t("estado_premio_indisponivel", pernas=", ".join(sem_premio)))
    if spot is not None:
        for p in pernas:
            if p["strike"] is None or (p["dias"] is not None and p["dias"] < 0):
                continue
            itm = spot > p["strike"] if p["tipo"] == _CALL else spot < p["strike"]
            if itm:
                return out("exercicio_provavel", t(
                    "estado_exercicio_provavel",
                    strike=skill_ref.num_br(p["strike"]), spot=skill_ref.num_br(spot)))
    if dias is None:
        return out("vigente", t("estado_vigente_sem_data"))
    if dias <= 5:
        return out("ate_5_dias", t("estado_perto_vencimento", dias=dias, vencimento=ref_txt))
    return out("vigente", t("estado_vigente", dias=dias, vencimento=ref_txt))


def ler_estrutura(option_positions, underlying, posicao, spot, contratos_por_id,
                  hoje, modo, motivo_sem_proposta=None,
                  status_cadeias=None) -> Optional[dict]:
    """Leitura determinística da estrutura aberta de `underlying`.

    `status_cadeias` (46.1, G-08): mapa vencimento bruto -> "ok"|"falha" vindo
    da rota; None = desconhecido (causa cai em "sem_cotacao").

    `None` quando não há nenhuma perna do ativo. Números arredondados a 2
    casas; None = desconhecido, nunca 0.0.
    """
    ops = [o for o in (option_positions or [])
           if isinstance(o, dict) and o.get("underlying") == underlying]
    if not ops:
        return None
    spot = _num(spot)
    contratos = contratos_por_id if isinstance(contratos_por_id, dict) else {}

    pernas = []
    for op in ops:
        p = _perna(op)
        p["premioAtual"], p["origemPremio"], p["origemTexto"] = _marcar(
            p, contratos.get(p["id"]), modo)
        p["resultado"] = _resultado_perna(p)
        ct = contratos.get(p["id"])
        p["motivoSemCotacao"] = _motivo_sem_cotacao(p, ct, status_cadeias)  # 46.1 (G-08)
        p["liquidez"] = _liquidez(ct)
        p["lastOk"] = isinstance(ct, dict) and _num(ct.get("lastPrice")) is not None
        d = _data(p["vencimento"])
        p["dias"] = (d - hoje).days if d else None
        pernas.append(p)

    nome = _classificar(pernas)

    # --- ações ---
    qtd_acoes = _num(posicao.get("qty")) if isinstance(posicao, dict) else None
    acoes = None
    if qtd_acoes is not None:
        pm = _num(posicao.get("avg"))
        res_acoes = None if (spot is None or pm is None) else round((spot - pm) * qtd_acoes, 2)
        acoes = {"quantidade": qtd_acoes, "precoMedio": _r2(pm), "preco": _r2(spot),
                 "resultado": res_acoes}

    # --- resultado total (D-05) ---
    # WR-05: resultado None tem duas causas distintas — sem cotação (premioAtual
    # None) ou dado da própria perna inválido (lado, quantidade, prêmio de entrada).
    sem_dados = [p["id"] for p in pernas if _sem_dados(p)]
    sem_cotacao = [p["id"] for p in pernas if p["resultado"] is None and not _sem_dados(p)]
    cotadas = [p["resultado"] for p in pernas if p["resultado"] is not None]
    acao_falta = acoes is not None and acoes["resultado"] is None
    incompleto = bool(sem_cotacao) or bool(sem_dados) or acao_falta
    total, texto = None, None
    if not incompleto:
        total = round(sum(cotadas) + (acoes["resultado"] if acoes else 0.0), 2)
    else:
        partes = []
        if sem_cotacao:
            partes.append(skill_ref.estrutura_posicao_txt(
                modo, "resultado_incompleto", pernas=", ".join(str(i) for i in sem_cotacao)))
        if sem_dados:
            partes.append(skill_ref.estrutura_posicao_txt(
                modo, "resultado_dados_invalidos", pernas=", ".join(str(i) for i in sem_dados)))
        if acao_falta:
            partes.append(skill_ref.estrutura_posicao_txt(modo, "acao_sem_cotacao"))
        texto = " ".join(t for t in partes if t)
    resultado = {
        "total": total,
        "acoes": acoes["resultado"] if acoes else None,
        "pernasCotadas": round(sum(cotadas), 2) if cotadas else None,
        "incompleto": incompleto,
        "pernasSemCotacao": sem_cotacao,
        "pernasSemDados": sem_dados,
        "texto": texto,
    }

    saida_pernas = [{
        "id": p["id"], "tipo": p["tipo"], "lado": p["lado"], "strike": p["strike"],
        "vencimento": p["vencimento"], "quantidade": p["quantidade"],
        "premioEntrada": _r2(p["premioEntrada"]), "premioAtual": _r2(p["premioAtual"]),
        "origemPremio": p["origemPremio"], "origemTexto": p["origemTexto"],
        "resultado": p["resultado"], "diasParaVencimento": p["dias"],
        "liquidez": p["liquidez"], "encerrar": _encerrar_perna(p, modo),
        "motivoSemCotacao": p["motivoSemCotacao"],
    } for p in pernas]

    faixa, motivo_faixa, motivo_faixa_txt, descoberta, descoberta_txt, entrada_payoff = _faixa(
        pernas, acoes, nome, underlying, modo)
    estado = _estado(pernas, spot, hoje, modo)

    # Fase 46, D-01: cenários/didática do card v6. Falha aqui nunca derruba a
    # estrutura (princípio 4) — cai para None e o resto do payload segue igual.
    # `modo` chega como "estudo"/"operador"; o motor do card fala "educacional".
    try:
        modo_card = "operador" if modo == "operador" else "educacional"
        cenarios = cartao_posicao.cenarios_da_estrutura(
            entrada_payoff, faixa, nome, spot, estado["referencia"], underlying, modo_card)
        didatica = cartao_posicao.didatica_estrutura(
            nome, faixa, entrada_payoff, cenarios, acoes, saida_pernas, underlying, modo_card)
    except Exception:
        cenarios = didatica = None

    # --- eixo aberta_sem_proposta (D-07) ---
    motivo_sp = None
    if any(p["liquidez"] and p["liquidez"]["faixa"] == options_quant.FAIXA_SEM_MERCADO
           for p in pernas):
        motivo_sp = "sem_mercado"
    elif motivo_sem_proposta:
        motivo_sp = motivo_sem_proposta
    motivo_sp_txt = None
    if motivo_sp:
        motivo_sp_txt = skill_ref.estrutura_posicao_txt(
            modo, "aberta_sem_proposta",
            motivo=skill_ref.opcoes_lastreadas_txt(modo, motivo_sp, ticker=underlying))

    # --- encerrar da estrutura ---
    if estado["estado"] == "vencida":
        enc = {"permitido": False, "motivo": "vencida",
               "texto": skill_ref.estrutura_posicao_txt(
                   modo, "encerrar_vencida", vencimento=estado["vencimentoTexto"])}
    else:
        invalidas = [str(p["id"]) for p in pernas if p["lado"] is None]
        faltam = [str(p["id"]) for p in pernas if p["premioAtual"] is None or not p["lastOk"]]
        if invalidas:
            enc = {"permitido": False, "motivo": "dados_invalidos",
                   "texto": skill_ref.estrutura_posicao_txt(
                       modo, "resultado_dados_invalidos", pernas=", ".join(invalidas))}
        elif faltam:
            enc = {"permitido": False, "motivo": "premio_indisponivel",
                   "texto": skill_ref.estrutura_posicao_txt(
                       modo, "encerrar_premio_indisponivel", pernas=", ".join(faltam))}
        else:
            enc = {"permitido": True, "motivo": None, "texto": None}

    piso = faixa["piso"] if faixa else None
    return {
        "underlying": underlying,
        "nome": nome,
        "nomeTexto": skill_ref.estrutura_posicao_txt(
            modo, f"nome_{nome}" if nome else "nome_fora_da_biblioteca"),
        "pernas": saida_pernas,
        "acoes": acoes,
        "resultado": resultado,
        "faixa": faixa,
        "motivoFaixa": motivo_faixa,
        "motivoFaixaTexto": motivo_faixa_txt,
        "descoberta": descoberta,
        "descobertaTexto": descoberta_txt,
        "estado": estado["estado"],
        "estadoTexto": estado["texto"],
        "vencimentoReferencia": estado["referencia"],
        "diasParaVencimento": estado["dias"],
        "abertaSemProposta": motivo_sp is not None,
        "motivoSemProposta": motivo_sp,
        "motivoSemPropostaTexto": motivo_sp_txt,
        "encerrar": enc,
        "stopTexto": (skill_ref.estrutura_posicao_txt(
            modo, "stop_protegida", piso=skill_ref.num_br(piso))
            if piso is not None and acoes and faixa["qtdPut"] >= acoes["quantidade"] else None),
        "incompleto": incompleto,
        # Fase 46, contrato aditivo
        "cenarios": cenarios,
        "didatica": didatica,
    }
