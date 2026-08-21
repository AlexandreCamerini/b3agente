"""FASE 2 (Revisão Total) — Portfólio: meta de entrada na compra (setup do STU)
e venda PARCIAL, nos moldes de test_persistence (db temporário, sem fixtures).

Cobre o aceite da fase: histórico persiste, escopado por usuário; venda parcial
mantém o preço médio; venda total preserva o comportamento original.
"""
import os
import tempfile

from app import db, store


def _fresh_db():
    d = tempfile.mkdtemp(prefix="b3_f2_")
    path = os.path.join(d, "b3_agente.db")
    conn = db.connect(path)
    store.ensure_defaults(conn)
    _zera(conn)  # o seed demo traz posições (PETR4 etc.) — zera para o teste
    return conn, path


def _zera(conn, user_id=None):
    db.kv_set(conn, "positions", [], user_id=user_id)
    db.kv_set(conn, "history", [], user_id=user_id)
    db.kv_set(conn, "cash", 100000.0, user_id=user_id)


META = {"setup": "Setup 9.2 (alta)", "lado": "alta", "veredito": "Estudar alta",
        "snapshotId": "abc12345", "gatilho": 38.5, "invalidacao": 36.9, "confluencia": 86}


def test_buy_registra_setup_de_entrada_na_posicao_e_no_historico():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 200, 38.0, meta=META)
    pos = store.get(conn, "positions")[0]
    assert pos["setupEntrada"]["setup"] == "Setup 9.2 (alta)"
    assert pos["setupEntrada"]["gatilho"] == 38.5
    assert pos["setupEntrada"]["snapshotId"] == "abc12345"
    assert pos.get("abertaEm")  # tempo em operação parte daqui
    h = store.get(conn, "history")[0]
    assert h["type"] == "COMPRA" and h["setup"] == "Setup 9.2 (alta)" and h["snapshotId"] == "abc12345"
    conn.close()


def test_buy_meta_e_sanitizada_campos_desconhecidos_e_tipos_errados():
    conn, _ = _fresh_db()
    store.buy(conn, "VALE3", 100, 60.0, meta={"setup": "PFR (alta)", "gatilho": "não-número",
                                              "malicioso": "x" * 500, "confluencia": 70})
    m = store.get(conn, "positions")[0]["setupEntrada"]
    assert m == {"setup": "PFR (alta)", "confluencia": 70}  # só o válido passa
    conn.close()


def test_buy_sem_meta_preserva_shape_original():
    conn, _ = _fresh_db()
    store.buy(conn, "ITUB4", 100, 30.0)
    pos = store.get(conn, "positions")[0]
    assert "setupEntrada" not in pos
    h = store.get(conn, "history")[0]
    assert "setup" not in h
    conn.close()


def test_sell_total_comportamento_original():
    conn, _ = _fresh_db()
    cash0 = store.get(conn, "cash")
    store.buy(conn, "PETR4", 200, 38.0)
    pnl = store.sell(conn, "PETR4", 40.0)  # sem qty = total (original)
    assert pnl == 400.0                     # (40-38) × 200
    assert store.get(conn, "positions") == []
    assert store.get(conn, "cash") == round(cash0 + 400.0, 2)
    h = store.get(conn, "history")[0]
    assert h["type"] == "VENDA" and h["qty"] == 200 and h["pnl"] == 400.0
    conn.close()


def test_sell_parcial_reduz_qty_e_preserva_preco_medio():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 300, 38.0)
    pnl = store.sell(conn, "PETR4", 40.0, qty=100)
    assert pnl == 200.0                     # (40-38) × 100
    pos = store.get(conn, "positions")[0]
    assert pos["qty"] == 200 and pos["avg"] == 38.0   # avg intocado
    h = store.get(conn, "history")[0]
    assert h["type"] == "VENDA" and h["qty"] == 100 and h["pnl"] == 200.0
    conn.close()


def test_sell_parcial_arredonda_para_lote_e_qty_maior_vira_total():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 300, 38.0)
    store.sell(conn, "PETR4", 40.0, qty=130)          # lote → 100
    assert store.get(conn, "positions")[0]["qty"] == 200
    store.sell(conn, "PETR4", 40.0, qty=9999)          # >= posição → total
    assert store.get(conn, "positions") == []
    conn.close()


def test_sell_motivo_default_manual_paridade_com_sell_option():
    """ADR15-04: sell() ganha `motivo`, mesmo contrato de sell_option (ADR-005)."""
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 200, 38.0, user_id="u1")
    store.sell(conn, "PETR4", 40.0, user_id="u1")   # sem motivo/origem = default
    h = store.get(conn, "history", user_id="u1")[0]
    assert h["motivo"] == "manual" and h["origem"] == "manual"
    conn.close()


def test_sell_motivo_e_origem_sao_eixos_independentes():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 200, 38.0, user_id="u1")
    store.sell(conn, "PETR4", 35.0, user_id="u1", motivo="stop", origem="automatico")
    h = store.get(conn, "history", user_id="u1")[0]
    assert h["motivo"] == "stop" and h["origem"] == "automatico"
    conn.close()


def test_sell_parcial_grava_motivo_sem_alterar_avg_nem_pnl():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 300, 38.0, user_id="u1")
    pnl = store.sell(conn, "PETR4", 40.0, user_id="u1", qty=100, motivo="alvo", origem="automatico")
    assert pnl == 200.0
    pos = store.get(conn, "positions", user_id="u1")[0]
    assert pos["qty"] == 200 and pos["avg"] == 38.0
    h = store.get(conn, "history", user_id="u1")[0]
    assert h["motivo"] == "alvo" and h["qty"] == 100 and h["pnl"] == 200.0
    conn.close()


def test_sell_sem_posicao_continua_devolvendo_none_sem_gravar():
    conn, _ = _fresh_db()
    assert store.sell(conn, "PETR4", 40.0, user_id="u1", motivo="stop") is None
    assert store.get(conn, "history", user_id="u1") == []
    conn.close()


def test_historico_persiste_apos_reinicio_e_escopado_por_usuario():
    conn, path = _fresh_db()
    store.ensure_defaults(conn, user_id="u1")
    store.ensure_defaults(conn, user_id="u2")
    _zera(conn, "u1")
    _zera(conn, "u2")
    store.buy(conn, "PETR4", 100, 38.0, user_id="u1", meta=META)
    store.sell(conn, "PETR4", 40.0, user_id="u1", qty=100)
    conn.close()

    conn2 = db.connect(path)                           # "reinício do servidor"
    h1 = store.get(conn2, "history", user_id="u1")
    h2 = store.get(conn2, "history", user_id="u2")
    assert len(h1) == 2 and h1[0]["type"] == "VENDA" and h1[1]["setup"] == "Setup 9.2 (alta)"
    assert h2 == []                                    # isolamento entre usuários
    conn2.close()


# ---------------------------------------------------------------------------
# Mini-runner para ambientes SEM pytest (padrão do projeto).
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    fails = 0
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("ok " + name)
            except AssertionError as e:
                fails += 1
                print("FALHOU " + name + " :: " + str(e))
            except Exception as e:  # noqa: BLE001
                fails += 1
                print("ERRO " + name + " :: " + repr(e))
    print()
    print("TODOS OS TESTES DO PORTFÓLIO F2 PASSARAM" if fails == 0 else str(fails) + " TESTE(S) FALHARAM")
    sys.exit(0 if fails == 0 else 1)
