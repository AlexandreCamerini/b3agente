"""Fase 46.1-01 — vocabulário novo (G-08/AL-02/MD-02/MD-05) e correções do motor do card
(AL-01 equilíbrio do collar, MD-02 aria teto parcial, MD-03a nota de PM)."""
import re

from app import cartao_posicao as cp
from app import opcoes_payoff, skill_ref

VENC = "2026-10-16"
PROIBIDO = re.compile(r"\bcomprar\b|\bvender\b|trava protetora|abate o custo|\bgarante|\bcerto\b|\bsempre\b",
                      re.I)

NEUTRAS = {
    "motivo_lendo": "atualizando",
    "motivo_leitura_indisponivel": "leitura indisponível",
    "chip_desatualizado": "desatualizado",
    "tentar_de_novo": "↻ Tentar de novo",
    "legenda_resultado_so_acoes": "resultado · só ações",
}
POR_MODO = ["leitura_falhou", "leitura_desatualizada", "causa_sem_cotacao", "causa_fora_da_cadeia",
            "causa_sem_negocio", "causa_fonte_indisponivel", "payoff_aria_teto_parcial"]
DIDATICAS = ["caso_equilibrio_collar", "caso_equilibrio_collar_sem_hoje"]


def test_vocabulario_461():
    for k, v in NEUTRAS.items():
        for modo in ("operador", "educacional"):
            assert skill_ref.cartao_posicao_txt(modo, k) == v
    for modo, trecho in (("educacional", "Sem cotação da opção UGPAK42 nesta fonte"),
                         ("operador", "Sem cotação de UGPAK42 nesta fonte")):
        assert trecho in skill_ref.cartao_posicao_txt(modo, "causa_sem_cotacao", contratos="UGPAK42")
    for modo in ("operador", "educacional"):
        for k in list(NEUTRAS) + POR_MODO:
            t = skill_ref.cartao_posicao_txt(modo, k)
            assert t, (modo, k)
            assert not PROIBIDO.search(t), (modo, k, t)
    for k in DIDATICAS:
        assert not PROIBIDO.search(skill_ref.cartao_didatica_txt(k))
    got = skill_ref.cartao_didatica_txt("caso_equilibrio_collar", be="34,60", pm="35,00",
                                        premioCall="1,00", premioPut="0,60", hoje="36,00")
    assert got == ("R$ 34,60 = preço médio R$ 35,00 menos o prêmio recebido na call R$ 1,00 "
                   "mais o prêmio pago na put R$ 0,60; hoje a ação está a R$ 36,00.")


# ------------------------------------------------------------------ helpers
def _acao(qtd, pm):
    return {"tipo": "ACAO", "lado": "compra", "strike": 0, "premio": pm, "quantidade": qtd}


def _perna(tipo, lado, k, premio, qtd):
    return {"tipo": tipo, "lado": lado, "strike": k, "premio": premio, "quantidade": qtd,
            "vencimento": VENC}


def _faixa(entrada):
    perfil = opcoes_payoff.perfil_da_estrutura(entrada)
    puts = [p["strike"] for p in entrada if p["tipo"] == "PUT" and p["lado"] == "compra"]
    calls = [p["strike"] for p in entrada if p["tipo"] == "CALL" and p["lado"] == "venda"]
    return {"piso": max(puts) if puts else None, "teto": min(calls) if calls else None,
            "perdaMaxima": None if perfil["perda_maxima"] is None else round(perfil["perda_maxima"], 2),
            "ganhoMaximo": None if perfil["ganho_maximo"] is None else round(perfil["ganho_maximo"], 2),
            "breakevens": [round(b, 2) for b in perfil["breakevens"]],
            "qtdBase": entrada[0]["quantidade"], "qtdPut": 0, "textos": []}


def _equilibrio(nome, entrada, spot=36.0, ajuste_be=0.0):
    f = _faixa(entrada)
    c = cp.cenarios_da_estrutura(entrada, f, nome, spot, VENC, "UGPA3", "educacional")
    assert c is not None
    c = {**c, "be": round(c["be"] + ajuste_be, 2)}
    pernas = [p for p in entrada if p["tipo"] != "ACAO"]
    acoes = {"quantidade": entrada[0]["quantidade"], "precoMedio": entrada[0]["premio"]}
    d = cp.didatica_estrutura(nome, f, entrada, c, acoes, pernas, "UGPA3", "educacional")
    casos = {s["termo"]: s["noSeuCaso"] for s in d["paragrafo"] if "termo" in s}
    return c, casos["equilibrio"]


AG = skill_ref.cartao_didatica_txt("caso_aguardando")
COLLAR = [_acao(100, 35.0), _perna("PUT", "compra", 30, 0.60, 100), _perna("CALL", "venda", 40, 1.00, 100)]


def test_collar_equilibrio_cita_a_conta_que_fecha():
    c, txt = _equilibrio("collar", COLLAR)
    assert c["be"] == 34.60
    assert txt == skill_ref.cartao_didatica_txt(
        "caso_equilibrio_collar", be="34,60", pm="35,00", premioCall="1,00", premioPut="0,60",
        hoje=skill_ref.num_br(36.0))
    assert "menos o prêmio R$ 1,00;" not in txt


def test_collar_sem_hoje():
    _, txt = _equilibrio("collar", COLLAR, spot=None)
    assert txt == skill_ref.cartao_didatica_txt(
        "caso_equilibrio_collar_sem_hoje", be="34,60", pm="35,00", premioCall="1,00", premioPut="0,60")


def test_collar_put_parcial_vira_aguardando():
    e = [_acao(100, 35.0), _perna("PUT", "compra", 30, 0.60, 50), _perna("CALL", "venda", 40, 1.00, 100)]
    _, txt = _equilibrio("collar", e)
    assert txt == AG


def test_call_coberta_regressao_e_adulterada():
    e = [_acao(1000, 39.50), _perna("CALL", "venda", 42.25, 1.49, 1000)]
    _, txt = _equilibrio("call_coberta", e, spot=40.10)
    assert txt == skill_ref.cartao_didatica_txt("caso_equilibrio", be="38,01", pm="39,50",
                                                premio="1,49", hoje="40,10")
    _, txt2 = _equilibrio("call_coberta", e, spot=40.10, ajuste_be=0.50)
    assert txt2 == AG


def test_put_protecao_segue_aguardando():
    e = [_acao(100, 35.0), _perna("PUT", "compra", 30, 0.60, 100)]
    _, txt = _equilibrio("put_protecao", e)
    assert txt == AG


# ------------------------------------------------------------------ MD-02
def test_aria_teto_parcial():
    e = [_acao(100, 35.0), _perna("CALL", "venda", 40, 1.00, 50)]
    f = _faixa(e)
    assert f["teto"] is not None
    f_parcial = {**f, "ganhoMaximo": None}
    c = cp.cenarios_da_estrutura(e, f_parcial, "call_coberta", 36.0, VENC, "UGPA3", "operador")
    assert "cobre só parte das ações" in c["payoff"]["aria"]
    assert "sem teto" not in c["payoff"]["aria"]
    f_sem = {**f, "teto": None, "ganhoMaximo": None}
    c2 = cp.cenarios_da_estrutura(e, f_sem, "call_coberta", 36.0, VENC, "UGPA3", "operador")
    assert "cobre só parte" not in c2["payoff"]["aria"]
    assert "sem teto" in c2["payoff"]["aria"]
    f_ok = _faixa([_acao(100, 35.0), _perna("CALL", "venda", 40, 1.00, 100)])
    c3 = cp.cenarios_da_estrutura([_acao(100, 35.0), _perna("CALL", "venda", 40, 1.00, 100)], f_ok,
                                  "call_coberta", 36.0, VENC, "UGPA3", "operador")
    assert "cobre só parte" not in c3["payoff"]["aria"] and "sem teto" not in c3["payoff"]["aria"]


# ------------------------------------------------------------------ MD-03a
POS = {"avg": 30.0, "qty": 100}


def _nota(compras, avg=30.0, qty=100):
    return cp._nota_pm(avg, qty, compras, "operador")


def test_nota_pm_reconcilia():
    assert _nota([{"qty": 60, "price": 29}, {"qty": 40, "price": 32}]) is None
    assert _nota([{"qty": 60, "price": 29}, {"qty": 40, "price": 31.5}]) is not None
    ok = [{"qty": 60, "price": 29}, {"qty": 40, "price": 31.5}]
    assert _nota(ok + [{"qty": "a", "price": 1}]) is None
    assert _nota(ok + ["x"]) is None
