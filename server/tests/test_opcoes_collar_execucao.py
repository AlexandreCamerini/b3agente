"""Fase 17, Plano 01 (FLOW-03) — caminho de EXECUÇÃO da trava protetora
(collar): `store.abrir_collar`.

O que este arquivo protege — invariante "execução tudo-ou-nada por desenho"
do CLAUDE.md ("store.buy/store.sell executam 100% da ordem ou rejeitam
inteira... o motor não produz esse estado"), aqui aplicado a nível de
ESTRUTURA (2 pernas), não só de ordem única: uma trava protetora de 2 pernas
abre as DUAS juntas ou NENHUMA. Encadear `abrir_call_coberta` +
`comprar_put_protecao` não serve nem no caminho feliz — a primeira chamada
trava `qtyTravada`, a segunda vê `qty_livre` reduzido e recusa por lastro
insuficiente, com o prêmio da call JÁ creditado e a posição vendida JÁ
gravada. Isso é EXATAMENTE a execução de meia estrutura que esta fase existe
para impedir.

Task 1: comportamento (RED antes de `abrir_collar` existir — todos os testes
abaixo devem FALHAR por `AttributeError: module 'app.store' has no attribute
'abrir_collar'` até a implementação entrar).
Task 2: guardiões de ESTRUTURA — provam, por inspeção de fonte, que
`abrir_collar` não compõe as funções single-leg e que nenhuma escrita
antecede uma validação.

Guardiões de teste não se apagam (guardrail do repositório, CLAUDE.md) —
reversão deliberada de qualquer um dos três guardiões estruturais abaixo
exige nota explícita no commit/SUMMARY que remove ou afrouxa.

Padrão da casa: `_fresh_db()` com SQLite temp por teste, sem conftest (mesmo
padrão de `test_opcoes_lastreadas_store.py`).
"""
import inspect
import os
import tempfile

import pytest

from app import db, store


def _fresh_db():
    d = tempfile.mkdtemp(prefix="b3_test_opcoes_collar_execucao_")
    path = os.path.join(d, "b3_agente.db")
    conn = db.connect(path)
    store.ensure_defaults(conn)
    return conn, path


def _contract_call(id_="PETR4O123", underlying="PETR4", strike=42.0, expiration="2026-09-18"):
    return {"id": id_, "underlying": underlying, "optionType": "call", "strike": strike,
            "expiration": expiration, "ivEntrada": 0.35, "deltaEntrada": 0.5, "hv21Entrada": 0.3}


def _contract_put(id_="PETR4P456", underlying="PETR4", strike=34.0, expiration="2026-09-18"):
    return {"id": id_, "underlying": underlying, "optionType": "put", "strike": strike,
            "expiration": expiration, "ivEntrada": 0.30, "deltaEntrada": -0.4, "hv21Entrada": 0.28}


def _snapshot(conn):
    return (store.get(conn, "cash"), store.get(conn, "positions"), store.get(conn, "optionPositions"))


# --------------------------------------------------------------------------
# Task 1 — comportamento
# --------------------------------------------------------------------------

def test_abrir_collar_caminho_feliz_lastro_exato_abre_as_duas_pernas():
    """Lastro livre EXATAMENTE `contratos*100` — a composição sequencial das
    funções single-leg falharia aqui (a call travaria o lote inteiro e a put
    recusaria por lastro insuficiente)."""
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 200, 38.0)  # qty_livre == 200 == contratos(2)*100
    cash_antes = store.get(conn, "cash")
    store.abrir_collar(conn, _contract_call(), _contract_put(), 2, 1.50, 1.00)
    cash_depois = store.get(conn, "cash")
    assert cash_depois == round(cash_antes + 2 * 100 * 1.50 - 2 * 100 * 1.00, 2)

    opts = store.get(conn, "optionPositions")
    call_pos = next(p for p in opts if p["id"] == "PETR4O123")
    put_pos = next(p for p in opts if p["id"] == "PETR4P456")
    assert call_pos["side"] == "vendida"
    assert put_pos["side"] == "comprada"
    assert call_pos["lastro"] == {"t": "PETR4", "qty": 200}
    assert put_pos["lastro"] == {"t": "PETR4", "qty": 200}

    positions = store.get(conn, "positions")
    pos_acao = next(p for p in positions if p["t"] == "PETR4")
    assert pos_acao["qtyTravada"] == 200  # travado UMA vez só (a call trava; a put não)

    history = store.get(conn, "history")
    entrada_call = next(h for h in history if h.get("t") == "PETR4O123")
    entrada_put = next(h for h in history if h.get("t") == "PETR4P456")
    assert entrada_call["type"] == "VENDA"
    assert entrada_put["type"] == "COMPRA"


def test_abrir_collar_rejeicao_tipo_call_trocado_nao_escreve_nada():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 200, 38.0)
    antes = _snapshot(conn)
    contrato_call_invalido = _contract_put(id_="PETR4O123")  # optionType errado (put no lugar de call)
    with pytest.raises(ValueError):
        store.abrir_collar(conn, contrato_call_invalido, _contract_put(), 2, 1.50, 1.00)
    assert _snapshot(conn) == antes


def test_abrir_collar_rejeicao_tipo_put_trocado_nao_escreve_nada():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 200, 38.0)
    antes = _snapshot(conn)
    contrato_put_invalido = _contract_call(id_="PETR4P456")  # optionType errado (call no lugar de put)
    with pytest.raises(ValueError):
        store.abrir_collar(conn, _contract_call(), contrato_put_invalido, 2, 1.50, 1.00)
    assert _snapshot(conn) == antes


def test_abrir_collar_underlying_divergente_nao_escreve_nada():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 200, 38.0)
    antes = _snapshot(conn)
    put_outro_ativo = _contract_put(underlying="VALE3")
    with pytest.raises(ValueError):
        store.abrir_collar(conn, _contract_call(), put_outro_ativo, 2, 1.50, 1.00)
    assert _snapshot(conn) == antes


def test_abrir_collar_mesmo_contrato_id_nao_escreve_nada():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 200, 38.0)
    antes = _snapshot(conn)
    put_mesmo_id = _contract_put(id_="PETR4O123")
    with pytest.raises(ValueError):
        store.abrir_collar(conn, _contract_call(), put_mesmo_id, 2, 1.50, 1.00)
    assert _snapshot(conn) == antes


def test_abrir_collar_sem_posicao_no_underlying_nao_escreve_nada():
    conn, _ = _fresh_db()
    antes = _snapshot(conn)
    with pytest.raises(ValueError):
        store.abrir_collar(conn, _contract_call(), _contract_put(), 2, 1.50, 1.00)
    assert _snapshot(conn) == antes


def test_abrir_collar_lastro_insuficiente_nao_escreve_nada():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 100, 38.0)  # só 100 ações livres, contratos=2 precisa de 200
    antes = _snapshot(conn)
    with pytest.raises(ValueError):
        store.abrir_collar(conn, _contract_call(), _contract_put(), 2, 1.50, 1.00)
    assert _snapshot(conn) == antes


def test_abrir_collar_caixa_insuficiente_no_debito_liquido_nao_escreve_nada():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 200, 38.0)
    store.put(conn, "cash", 10.0)  # zera o caixa disponível para o débito líquido
    antes = _snapshot(conn)
    # premio_put > premio_call => débito líquido positivo, exige caixa
    with pytest.raises(ValueError):
        store.abrir_collar(conn, _contract_call(), _contract_put(), 2, 1.00, 5.00)
    assert _snapshot(conn) == antes


def test_abrir_collar_credito_liquido_nao_tem_porta_de_caixa():
    """premio_call >= premio_put é crédito/neutro líquido — o lastro financia,
    não há checagem de caixa mesmo com caixa zerado."""
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 200, 38.0)
    store.put(conn, "cash", 0.0)
    store.abrir_collar(conn, _contract_call(), _contract_put(), 2, 5.00, 1.00)
    cash_depois = store.get(conn, "cash")
    assert cash_depois == round(0.0 + 2 * 100 * 5.00 - 2 * 100 * 1.00, 2)


def test_abrir_collar_contratos_menor_que_1_levanta_value_error():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 200, 38.0)
    antes = _snapshot(conn)
    with pytest.raises(ValueError):
        store.abrir_collar(conn, _contract_call(), _contract_put(), 0, 1.50, 1.00)
    assert _snapshot(conn) == antes


@pytest.mark.parametrize("premio_call,premio_put", [(0, 1.0), (-1.0, 1.0), (1.0, 0), (1.0, -1.0), (True, 1.0)])
def test_abrir_collar_premio_invalido_levanta_value_error(premio_call, premio_put):
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 200, 38.0)
    antes = _snapshot(conn)
    with pytest.raises(ValueError):
        store.abrir_collar(conn, _contract_call(), _contract_put(), 2, premio_call, premio_put)
    assert _snapshot(conn) == antes


def test_abrir_collar_reabertura_faz_merge_de_avg_ponderado_e_soma_qty():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 400, 38.0)
    store.abrir_collar(conn, _contract_call(), _contract_put(), 2, 1.50, 1.00)
    store.abrir_collar(conn, _contract_call(), _contract_put(), 2, 2.50, 2.00)

    opts = store.get(conn, "optionPositions")
    call_pos = next(p for p in opts if p["id"] == "PETR4O123")
    put_pos = next(p for p in opts if p["id"] == "PETR4P456")
    assert call_pos["qty"] == 400
    assert put_pos["qty"] == 400
    assert call_pos["avg"] == round((1.50 * 200 + 2.50 * 200) / 400, 2)
    assert put_pos["avg"] == round((1.00 * 200 + 2.00 * 200) / 400, 2)
    assert call_pos["lastro"]["qty"] == 400
    assert put_pos["lastro"]["qty"] == 400

    positions = store.get(conn, "positions")
    pos_acao = next(p for p in positions if p["t"] == "PETR4")
    assert pos_acao["qtyTravada"] == 400


# --------------------------------------------------------------------------
# Task 2 — guardiões de ESTRUTURA (não se apagam; ver docstring do módulo)
# --------------------------------------------------------------------------

def test_abrir_collar_nao_compoe_as_funcoes_single_leg():
    """`ORDER_LOCK` é `RLock` — chamar `abrir_call_coberta`/
    `comprar_put_protecao` de dentro de `abrir_collar` NÃO deadlockaria, mas a
    PRIMEIRA chamada já teria gravado caixa/posição/qtyTravada antes de a
    validação da SEGUNDA perna rodar. Isso é exatamente a execução de meia
    estrutura que esta fase existe para impedir — proibido por desenho, não
    só por convenção."""
    fonte = inspect.getsource(store.abrir_collar)
    assert "abrir_call_coberta(" not in fonte
    assert "comprar_put_protecao(" not in fonte


def test_abrir_collar_valida_tudo_antes_de_qualquer_kv_set():
    """Guardião de ORDEM DE CÓDIGO: a última validação (`raise ValueError(`)
    precisa vir ANTES da primeira escrita (`db.kv_set(`) no texto-fonte da
    função — pega o dia em que alguém mover uma validação para depois de uma
    escrita."""
    fonte = inspect.getsource(store.abrir_collar)
    ultimo_raise = fonte.rfind("raise ValueError(")
    primeiro_kv_set = fonte.find("db.kv_set(")
    assert ultimo_raise != -1 and primeiro_kv_set != -1
    assert ultimo_raise < primeiro_kv_set


def test_abrir_collar_rejeicao_de_caixa_nao_move_nada():
    conn, _ = _fresh_db()
    store.buy(conn, "PETR4", 200, 38.0)
    store.put(conn, "cash", 10.0)
    cash_antes = store.get(conn, "cash")
    positions_antes = store.get(conn, "positions")
    opts_antes = store.get(conn, "optionPositions")
    with pytest.raises(ValueError):
        store.abrir_collar(conn, _contract_call(), _contract_put(), 2, 1.00, 5.00)
    assert store.get(conn, "cash") == cash_antes
    assert store.get(conn, "positions") == positions_antes
    assert store.get(conn, "optionPositions") == opts_antes
    history = store.get(conn, "history")
    rejeitadas = [h for h in history if h.get("status") == "rejeitada"]
    assert len(rejeitadas) == 1
