"""Debug 2026-10-23 — "duas fontes para o mesmo ativo".

Em produção, PETR3 mostrava no card o plano do Setup 9.3 (entrada 66,46 /
stop 63,26 / alvo 72,86) e o modal de proteção da posição devolvia, via
`marcos_para_posicao`, 64,74 / 67,62 (suporte), além de "Aplicar" poder
sobrescrever o plano gravado na compra. A posição agora lê a MESMA fonte:
gravado na posição > plano do setup do card > suporte (só sem plano).
"""
from app import marcos_servico, setups

_NIV = {"atr": 1.82, "suportes": [64.9], "resistencias": [66.0, 80.0]}
_SETUP = {"nome": "Setup 9.3 (alta)", "lado": "alta", "gatilho": 66.46, "invalidacao": 63.44}


def _snap(setups_list=None, close=65.58):
    return {"snapshotId": "x", "asOf": "2026-10-23", "close": close,
            "setups": {"setups": setups_list if setups_list is not None else [_SETUP], "niveis": _NIV}}


def test_posicao_sem_marcos_usa_o_plano_do_card():
    snap = _snap()
    card = setups.plano_do_resultado(snap["setups"], close=snap["close"])
    m = marcos_servico.marcos_para_posicao(snap, 65.16, avg=65.16)
    assert m["valido"] and m["fonte"] == "setup"
    assert (m["stop"], m["alvo"]) == (card["stop"], card["alvo"])
    assert m["setup"] == "Setup 9.3 (alta)"


def test_posicao_com_marcos_gravados_devolve_os_gravados():
    pos = {"t": "PETR3", "qty": 1100, "avg": 65.16, "stop": 63.26, "alvo": 72.86}
    m = marcos_servico.marcos_para_posicao(_snap(), 65.16, avg=65.16, pos=pos)
    assert m["valido"] and m["fonte"] == "posicao_gravada"
    assert (m["stop"], m["alvo"]) == (63.26, 72.86)


def test_marcos_gravados_com_geometria_vencida_caem_no_plano():
    # stop gravado acima do preço atual (o preço caiu): não é plano em vigor
    pos = {"stop": 66.0, "alvo": 72.86}
    m = marcos_servico.marcos_para_posicao(_snap(), 65.16, avg=65.16, pos=pos)
    assert m["fonte"] == "setup"


def test_sem_setup_de_compra_cai_no_suporte():
    m = marcos_servico.marcos_para_posicao(_snap(setups_list=[]), 65.16, avg=65.16)
    assert m["fonte"] == "posicao"
    assert m == {**setups.marcos_da_posicao(65.16, _NIV, avg=65.16), **marcos_servico._carimbo(_snap(), "posicao")}


def test_gravado_invalido_avisa_no_parecer():
    # review WR-05: alvo gravado abaixo do PM não some calado
    pos = {"stop": 60.0, "alvo": 66.0}
    m = marcos_servico.marcos_para_posicao(_snap(), 65.16, avg=70.0, pos=pos)
    assert "marcos gravados na posição não valem mais" in m.get("parecer", "")


def test_plano_superado_pelo_preco_avisa_e_cai_no_suporte():
    # review WR-04: preço ao vivo acima do alvo do plano do card
    m = marcos_servico.marcos_para_posicao(_snap(), 81.0, avg=81.0)
    assert m["fonte"] == "posicao"
    assert "não serve para esta posição agora" in m.get("parecer", "")


def test_reaplicar_mesmo_stop_nao_reancora(tmp_path, monkeypatch):
    # review WR-01: "Aplicar" do marco já gravado não mexe no 1R da gestão
    from app import db, store
    conn = db.connect(str(tmp_path / "t.db"))
    store.buy(conn, "PETR3", 100, 65.16, user_id="u", marcos={"stop": 63.26, "alvo": 72.86})
    store.set_position(conn, "PETR3", stop=64.0, has_stop=True, user_id="u")  # trailing do agente (manual=False)
    store.set_position(conn, "PETR3", stop=64.0, alvo=72.86, has_stop=True, has_alvo=True, user_id="u", manual=True)
    p = store.get(conn, "positions", user_id="u")[0]
    assert p["stopInicial"] == 63.26
