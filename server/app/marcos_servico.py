"""Fase 50: I/O fino em volta do motor puro de marcos (setups.marcos_*).
Nenhuma aritmética aqui.

Busca o snapshot canônico (mesmo das rotas de Opções/Radar), escolhe o setup
DO SERVIDOR e delega a conta a `setups.marcos_do_plano`/`marcos_da_posicao`.
Números de gatilho/invalidação vindos do cliente nunca entram (T-50-13).
"""
from . import candle_provider, setups, skill_ref, technical_snapshot
from . import candles as candles_mod


async def snapshot_canonico(t):
    """Snapshot no período canônico; qualquer falha -> None (nunca inventa)."""
    try:
        p = candles_mod.normalize_period(None)
        return await technical_snapshot.get(t, p, lambda rng: candle_provider.get_history(t, rng=rng))
    except Exception:
        return None


def _carimbo(snap, fonte):
    return {"snapshotId": snap.get("snapshotId"), "snapshotAt": snap.get("asOf") or snap.get("generatedAt"),
            "fonte": fonte}


def _niveis(snap):
    return ((snap or {}).get("setups") or {}).get("niveis") or {}


def marcos_de_setup(snap, nome_setup, preco):
    """Marcos do setup `nome_setup` (compra) medidos no PREÇO EXECUTADO."""
    achado = next((s for s in ((snap.get("setups") or {}).get("setups") or [])
                   if s.get("nome") == nome_setup and s.get("lado") == "alta" and not s.get("aposentado")), None)
    if not achado:
        data = str(snap.get("asOf") or snap.get("generatedAt") or "")[:10] or "data desconhecida"
        m = {**setups._marcos_vazio("O setup %s não está ativo no snapshot de %s — sem plano do motor para gravar." % (nome_setup, data), "alta"),
             "gatilho": None, "invalidacao": None}
    else:
        m = setups.marcos_do_plano("alta", achado.get("gatilho"), achado.get("invalidacao"),
                                   close=preco, niveis=_niveis(snap))
        m = {**m, "gatilho": achado.get("gatilho"), "invalidacao": achado.get("invalidacao")}
    return {**m, **_carimbo(snap, "setup")}


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v == v and v > 0


def marcos_para_posicao(snap, preco, avg=None, pos=None):
    """Proteção de posição aberta — UMA fonte por ativo (debug 2026-10-23).

    Antes, o card mostrava o plano do setup (PETR3: stop 63,26 / alvo 72,86) e
    este ramo recalculava por suporte (64,74 / 67,62): dois motores, dois
    números para o mesmo ativo, e "Aplicar" sobrescrevia o plano gravado na
    compra. Precedência, nesta ordem:
      1. marcos já gravados na posição (servidor, nunca o corpo) se a
         geometria ainda vale no preço atual — é o plano em vigor;
      2. o plano do setup em vigor, o MESMO de `plano_do_resultado` que o
         card exibe (fechamento do snapshot, como o card);
      3. só sem plano: proteção por suporte (`marcos_da_posicao`).
    """
    avisos = []
    motivo_gravado = None
    if pos and _num(pos.get("stop")) and _num(pos.get("alvo")) and _num(preco):
        motivo_gravado = setups.validar_marcos(pos["stop"], pos["alvo"], preco=preco, avg=avg)
        if motivo_gravado:
            # review WR-05: o número do usuário não some calado
            avisos.append("Os marcos gravados na posição não valem mais no preço atual (%s)" % motivo_gravado.rstrip("."))
    if pos and _num(pos.get("stop")) and _num(pos.get("alvo")) and _num(preco) and motivo_gravado is None:
        stop, alvo = round(float(pos["stop"]), 2), round(float(pos["alvo"]), 2)
        m = {**setups._marcos_vazio("", "alta"), "valido": True, "entrada": round(float(preco), 2),
             "tipoEntrada": "plano gravado na posição", "stop": stop, "alvo": alvo,
             "rr": setups.rr_da_entrada(preco, stop, alvo), "riscoPorAcao": round(preco - stop, 2),
             "origemStop": "gravado", "origemAlvo": "gravado", "atr": _niveis(snap).get("atr")}
        return {**m, **_carimbo(snap, "posicao_gravada")}
    plano = setups.plano_do_resultado((snap or {}).get("setups"), close=(snap or {}).get("close"))
    motivo_plano = None
    if plano.get("decisao") == setups.DECISAO_COMPRAR and _num(preco) \
            and _num(plano.get("stop")) and _num(plano.get("alvo")):
        motivo_plano = setups.validar_marcos(plano["stop"], plano["alvo"], preco=preco, avg=avg)
        if motivo_plano:
            # review WR-04: o plano do card foi superado pelo preço — dizer, não trocar calado
            avisos.append("O plano do %s (stop R$ %s, alvo R$ %s) não serve para esta posição agora (%s)"
                          % (plano.get("setup") or "setup", skill_ref.num_br(plano["stop"]),
                             skill_ref.num_br(plano["alvo"]), motivo_plano.rstrip(".")))
    if plano.get("decisao") == setups.DECISAO_COMPRAR and _num(preco) \
            and _num(plano.get("stop")) and _num(plano.get("alvo")) and motivo_plano is None:
        m = {**setups._marcos_vazio("", "alta"), "valido": True, "entrada": plano.get("entrada"),
             "tipoEntrada": plano.get("tipo"), "stop": plano["stop"], "alvo": plano["alvo"],
             "rr": plano.get("rr2"), "riscoPorAcao": plano.get("riscoPorAcao"), "alvo1R": plano.get("alvo1"),
             "origemStop": plano.get("origemStop"), "origemAlvo": plano.get("origemAlvo"), "atr": plano.get("atr"),
             "setup": plano.get("setup")}
        return _com_avisos({**m, **_carimbo(snap, "setup")}, avisos)
    m = setups.marcos_da_posicao(preco, _niveis(snap), avg=avg)
    if avisos and m.get("valido"):
        avisos.append("por isso os números abaixo são a proteção por suporte, calculada a partir do preço atual")
    return _com_avisos({**m, **_carimbo(snap, "posicao")}, avisos)


def _com_avisos(m, avisos):
    """Avisos de troca de fonte entram no `parecer` (texto do motor que o modal
    já exibe), antes do parecer de R:R quando houver."""
    if not avisos:
        return m
    texto = "; ".join(avisos) + "."
    return {**m, "parecer": (texto + " " + m["parecer"]) if m.get("parecer") else texto}


def marcos_para_compra(snap, setup_nome, preco):
    """Fonte única dos marcos de uma COMPRA manual (quick 261026-epr).

    A prévia do BuyModal (`/api/marcos` com `compra`) e a gravação em
    `/api/buy` (`protecao: "motor"`) chamam ESTA função — mesmo snapshot,
    mesmos números. Precedência: (1) plano do setup escolhido, julgado no preço
    executado (`revalidar_na_execucao` com gatilho/invalidação do servidor);
    (2) proteção por suporte/plano do card (`marcos_para_posicao`, sem posição
    gravada, `avg=preco`), também revalidada. Nada serviu -> `valido: False`
    com o motivo; a compra manual nunca é recusada por isso (D-06).
    """
    motivo_setup = None
    if isinstance(setup_nome, str) and setup_nome.strip():
        ps = marcos_de_setup(snap, setup_nome.strip(), preco)
        if ps.get("valido"):
            rv = setups.revalidar_na_execucao(ps["stop"], ps["alvo"], preco,
                                              gatilho=ps.get("gatilho"), invalidacao=ps.get("invalidacao"))
            if rv["ok"]:
                return {**ps, "rr": rv["rr"]}
            motivo_setup = rv["motivo"]
        else:
            motivo_setup = ps.get("motivo")
    pp = marcos_para_posicao(snap, preco, avg=preco, pos=None)
    motivo_pos = pp.get("motivo")
    if pp.get("valido"):
        rv = setups.revalidar_na_execucao(pp["stop"], pp["alvo"], preco)
        if rv["ok"]:
            if motivo_setup:
                aviso = "O plano do setup não serviu (%s)." % motivo_setup.rstrip(".")
                pp = {**pp, "parecer": aviso + (" " + pp["parecer"] if pp.get("parecer") else "")}
            return {**pp, "rr": rv["rr"]}
        motivo_pos = rv["motivo"]
        # quick 261026-epr R5: o plano do card (fonte "setup") foi reprovado na
        # execução; a proteção por suporte pode servir — tenta antes de desistir.
        if pp.get("fonte") == "setup":
            ps2 = setups.marcos_da_posicao(preco, _niveis(snap), avg=preco)
            if ps2.get("valido"):
                rv2 = setups.revalidar_na_execucao(ps2["stop"], ps2["alvo"], preco)
                if rv2["ok"]:
                    avisos = [m for m in (motivo_setup and "O plano do setup não serviu (%s)" % motivo_setup.rstrip("."),
                                          "o plano do card não serviu na execução (%s)" % motivo_pos.rstrip(".")) if m]
                    out = _com_avisos({**ps2, **_carimbo(snap, "posicao"), "rr": rv2["rr"]}, avisos)
                    return out
    motivo = motivo_setup or motivo_pos or "O motor não traçou proteção agora."
    base = pp if not pp.get("valido") else {**setups._marcos_vazio(motivo, "alta")}
    return {**base, "valido": False, "motivo": motivo, "stop": None, "alvo": None,
            "rr": None, **_carimbo(snap, "compra")}
