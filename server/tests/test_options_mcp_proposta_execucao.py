"""Quick 260923-ndy, Task 1 — `_execucao_da_proposta(estruturas, lote)`.

Função PURA (zero I/O) que deriva o bloco `execucao` da rota
`POST /api/options/mcp/proposta`: candidato a execução manual quando (e só
quando) a estrutura montada tem exatamente 1 perna, contrato e vencimento
conhecidos, proporção 1:1, um par side×kind executável no simulador, e um
lote múltiplo de 100. Qualquer outra forma vira `executavel: False` com um
motivo nomeado — nunca um corpo parcial (T-NDY-01 do threat model da quick).

Por que a derivação fica no backend, não no front: `contratos` é em
CONTRATOS e o lote do Analisar é em AÇÕES — converter no cliente seria a
segunda versão da mesma conta que `_em_reais`/D-24.2 já proíbem (princípio 5
do CLAUDE.md).
"""
from __future__ import annotations

import pytest

from app.options_mcp_api import (
    MOTIVO_EXEC_INCOMPLETA,
    MOTIVO_EXEC_LOTE_CENTENA,
    MOTIVO_EXEC_MULTIPERNA,
    MOTIVO_EXEC_PROPORCAO,
    MOTIVO_EXEC_SEM_LOTE,
    MOTIVO_EXEC_VARIAS,
    MOTIVO_EXEC_VENDA_PUT,
    _execucao_da_proposta,
)


def _perna(contract="PETRI400", side="sell", kind="CALL", quantity=1,
           strike=40.0, premium=0.58, delta=0.34, expiration=None):
    perna = {"contract": contract, "side": side, "kind": kind,
             "quantity": quantity, "strike": strike, "premium": premium,
             "delta": delta}
    if expiration is not None:
        perna["expiration"] = expiration
    return perna


def _estrutura(legs, expiration="2026-09-19", kind="venda_coberta", name="x"):
    d = {"kind": kind, "name": name, "legs": legs}
    if expiration is not None:
        d["expiration"] = expiration
    return d


# ------------------------------------------------------------- vazio/várias
def test_sem_estrutura_devolve_none():
    assert _execucao_da_proposta([], 100) is None


def test_duas_estruturas_nao_executavel_varias():
    estruturas = [_estrutura([_perna()]), _estrutura([_perna()])]
    assert _execucao_da_proposta(estruturas, 100) == {
        "executavel": False, "motivo": MOTIVO_EXEC_VARIAS,
    }


# ----------------------------------------------------------------- pernas
def test_estrutura_com_duas_pernas_nao_executavel_multiperna():
    # Mesma fixture de `_setup()` em test_options_mcp_api.py: trava de alta,
    # 2 pernas (buy CALL 38 + sell CALL 40).
    legs = [
        {"contract": "PETRI380", "side": "buy", "quantity": 1,
         "kind": "CALL", "strike": 38.0, "premium": 1.2, "delta": 0.62},
        {"contract": "PETRI400", "side": "sell", "quantity": 1,
         "kind": "CALL", "strike": 40.0, "premium": 0.58, "delta": 0.34},
    ]
    estruturas = [_estrutura(legs, expiration="2026-09-19", kind="trava_de_alta")]
    assert _execucao_da_proposta(estruturas, 100) == {
        "executavel": False, "motivo": MOTIVO_EXEC_MULTIPERNA,
    }


# ------------------------------------------------------- tipo por side×kind
def test_sell_call_vira_call_coberta_lote_200():
    estruturas = [_estrutura([_perna(contract="PETRI400", side="sell", kind="CALL")],
                             expiration="2026-09-19")]
    assert _execucao_da_proposta(estruturas, 200) == {
        "executavel": True,
        "tipo": "call_coberta",
        "contractSymbol": "PETRI400",
        "expiration": "2026-09-19",
        "contratos": 2,
        "qtyAcoes": 200,
    }


def test_buy_put_vira_put_protecao_lote_100():
    estruturas = [_estrutura([_perna(contract="PETRI350", side="buy", kind="PUT",
                                      strike=35.0)], expiration="2026-09-19")]
    r = _execucao_da_proposta(estruturas, 100)
    assert r["executavel"] is True
    assert r["tipo"] == "put_protecao"
    assert r["contratos"] == 1
    assert r["qtyAcoes"] == 100


def test_buy_call_vira_opcao_a_descoberto_lote_100():
    estruturas = [_estrutura([_perna(contract="PETRI400", side="buy", kind="CALL")],
                             expiration="2026-09-19")]
    r = _execucao_da_proposta(estruturas, 100)
    assert r["executavel"] is True
    assert r["tipo"] == "opcao_a_descoberto"
    assert r["contratos"] == 1
    assert r["qtyAcoes"] == 100


def test_sell_put_nao_executavel_venda_put():
    estruturas = [_estrutura([_perna(contract="PETRI350", side="sell", kind="PUT",
                                      strike=35.0)], expiration="2026-09-19")]
    assert _execucao_da_proposta(estruturas, 100) == {
        "executavel": False, "motivo": MOTIVO_EXEC_VENDA_PUT,
    }


def test_normaliza_caixa_de_side_e_kind():
    """`"SELL"`/`"call"` (caixa diferente do contrato do serviço) precisam
    dar o MESMO resultado de `"sell"`/`"CALL"` — o servidor não garante
    caixa uniforme."""
    estruturas = [_estrutura([_perna(contract="PETRI400", side="SELL", kind="call")],
                             expiration="2026-09-19")]
    r = _execucao_da_proposta(estruturas, 200)
    assert r["executavel"] is True
    assert r["tipo"] == "call_coberta"


# ----------------------------------------------------------- vencimento/perna
def test_expiration_ausente_na_estrutura_usa_a_da_perna():
    estruturas = [_estrutura(
        [_perna(contract="PETRI400", side="sell", kind="CALL", expiration="2026-10-17")],
        expiration=None)]
    r = _execucao_da_proposta(estruturas, 100)
    assert r["executavel"] is True
    assert r["expiration"] == "2026-10-17"


def test_sem_contract_e_sem_vencimento_algum_nao_executavel_incompleta():
    estruturas = [_estrutura(
        [_perna(contract=None, side="sell", kind="CALL", expiration=None)],
        expiration=None)]
    assert _execucao_da_proposta(estruturas, 100) == {
        "executavel": False, "motivo": MOTIVO_EXEC_INCOMPLETA,
    }


def test_sem_contract_mas_com_vencimento_tambem_incompleta():
    estruturas = [_estrutura([_perna(contract=None, side="sell", kind="CALL")],
                             expiration="2026-09-19")]
    assert _execucao_da_proposta(estruturas, 100) == {
        "executavel": False, "motivo": MOTIVO_EXEC_INCOMPLETA,
    }


# --------------------------------------------------------------- proporção
def test_quantity_diferente_de_1_nao_executavel_proporcao():
    estruturas = [_estrutura([_perna(quantity=2)], expiration="2026-09-19")]
    assert _execucao_da_proposta(estruturas, 100) == {
        "executavel": False, "motivo": MOTIVO_EXEC_PROPORCAO,
    }


def test_quantity_booleana_true_nao_executavel_proporcao():
    """`True == 1` em Python — mesma armadilha que `_lote`/`_vezes_lote` já
    tratam em outras funções deste módulo; booleano NÃO é quantidade."""
    estruturas = [_estrutura([_perna(quantity=True)], expiration="2026-09-19")]
    assert _execucao_da_proposta(estruturas, 100) == {
        "executavel": False, "motivo": MOTIVO_EXEC_PROPORCAO,
    }


# ------------------------------------------------------------------- lote
def test_lote_none_nao_executavel_sem_lote():
    estruturas = [_estrutura([_perna()], expiration="2026-09-19")]
    assert _execucao_da_proposta(estruturas, None) == {
        "executavel": False, "motivo": MOTIVO_EXEC_SEM_LOTE,
    }


def test_lote_150_nao_arredonda_nao_executavel_lote_centena():
    estruturas = [_estrutura([_perna()], expiration="2026-09-19")]
    assert _execucao_da_proposta(estruturas, 150) == {
        "executavel": False, "motivo": MOTIVO_EXEC_LOTE_CENTENA,
    }
