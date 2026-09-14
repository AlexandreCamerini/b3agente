"""Fase 30, Plano 03 — a etapa de IA da curadoria: `curadoria_narrativa.narrar`
(Task 1, camada fina de LLM) e `POST /api/options/curadoria/narrativa`
(Task 2, rota sob o gate de análise).

O que a Task 1 prova aqui, e por quê:

- **`narrar` é estruturalmente incapaz de receber um pool não rankeado.**
  Lista com mais de `TOPO` itens, fora de ordem, ou vazia levanta
  `ValueError` ANTES de qualquer chamada ao modelo — provado contando
  chamadas ao `_call_llm` fake, não só por leitura de código
  (`test_narrar_recusa_lista_maior_que_topo`,
  `test_narrar_recusa_lista_fora_de_ordem`, `test_narrar_recusa_top_vazio`).
- **Contabilidade nunca derruba a resposta**
  (`test_narrar_registro_de_uso_falhando_nao_derruba_resposta`).
- **O módulo não toca o motor determinístico nem o provedor de mercado**
  (`test_modulo_nao_importa_motor_nem_provider`).

A Task 2 (rota `POST /api/options/curadoria/narrativa`) estende este mesmo
arquivo — ver o bloco de testes correspondente logo abaixo do de Task 1.
"""
import asyncio
import os
import tempfile

import pytest

from app import ai_activity, curadoria_narrativa, db, llm, opcoes_curadoria

_EXP_DIAS = 30


# ─────────────────────────────────────────────────────────────────────────
# Fixtures/helpers
# ─────────────────────────────────────────────────────────────────────────

@pytest.fixture
def conn():
    with tempfile.TemporaryDirectory() as d:
        c = db.connect(os.path.join(d, "b3.db"))
        yield c
        c.close()


CFG = {"provider": "anthropic", "model": "claude-opus-5", "keySource": "manual",
       "apiKey": "sk-falsa", "appMode": "estudo"}


def _estrutura(ganho=500.0, perda=2000.0, breakevens=(28.5,)):
    return {"ganho_maximo": ganho, "perda_maxima": perda, "breakevens": list(breakevens)}


def _item(symbol, razao, posicao, premio_unitario=1.5, ticker="PETR4", strike=30):
    return {
        "tipo": "call_coberta", "ticker": ticker, "contractSymbol": symbol,
        "optionType": "call", "strike": strike, "expiration": "2099-01-01",
        "diasParaVencimento": _EXP_DIAS, "contratos": 2, "qtyAcoes": 200,
        "premioUnitario": premio_unitario, "premioTotal": premio_unitario * 200,
        "liquidez": {"faixa": "negociavel"}, "estrutura": _estrutura(),
        "razao": razao, "manchete": "manchete", "didatica": "didatica",
        "precoObjeto": 29.0, "posicaoNoRanking": posicao,
    }


def _top_valido(n=4):
    """Top já rankeado e válido: razão não-crescente, posicaoNoRanking 1..n —
    exatamente o formato que `opcoes_curadoria.rankear` produziria."""
    return [_item(f"PETR4C{30 + i}", razao=round(1.0 - i * 0.1, 6), posicao=i + 1)
            for i in range(n)]


# ─────────────────────────────────────────────────────────────────────────
# Task 1 — `curadoria_narrativa.narrar` (unitário, sem HTTP)
# ─────────────────────────────────────────────────────────────────────────

def test_narrar_com_top_valido_devolve_texto_e_registra_uso(conn, monkeypatch):
    chamadas = []

    async def _fake(config, key, system, user, max_tokens):
        chamadas.append((system, user, max_tokens))
        llm.record_usage(config, {"usage": {"input_tokens": 100, "output_tokens": 50}})
        return "  Parágrafo sobre a estrutura.  \n"
    monkeypatch.setattr(llm, "_call_llm", _fake)

    top = _top_valido()
    r = asyncio.run(curadoria_narrativa.narrar(conn, CFG, "u1", "estudo", top))

    assert r["texto"] == "Parágrafo sobre a estrutura."  # markdown normalizado (trim)
    assert r["estruturas"] == [it["contractSymbol"] for it in top]
    assert len(chamadas) == 1
    assert chamadas[0][2] == curadoria_narrativa.MAX_TOKENS

    snap = ai_activity.snapshot(conn, "u1")
    assert snap["hoje"]["custo"] > 0, "uso deveria ter sido registrado sob tipo Curadoria"


def test_narrar_recusa_lista_maior_que_topo(conn, monkeypatch):
    chamadas = []

    async def _fake(*a, **k):
        chamadas.append(1)
        return "nunca deveria rodar"
    monkeypatch.setattr(llm, "_call_llm", _fake)

    top_grande = _top_valido(n=opcoes_curadoria.TOPO + 1)
    with pytest.raises(ValueError):
        asyncio.run(curadoria_narrativa.narrar(conn, CFG, "u1", "estudo", top_grande))
    assert chamadas == [], "ValueError precisa vir ANTES de qualquer chamada ao modelo"


def test_narrar_recusa_lista_fora_de_ordem(conn, monkeypatch):
    chamadas = []

    async def _fake(*a, **k):
        chamadas.append(1)
        return "nunca deveria rodar"
    monkeypatch.setattr(llm, "_call_llm", _fake)

    top = _top_valido()
    # inverte a ordem: razao crescente é inválido (rankear produz decrescente)
    top_invertido = list(reversed(top))
    top_invertido = [{**it, "posicaoNoRanking": i + 1} for i, it in enumerate(top_invertido)]
    with pytest.raises(ValueError):
        asyncio.run(curadoria_narrativa.narrar(conn, CFG, "u1", "estudo", top_invertido))
    assert chamadas == []


def test_narrar_recusa_top_vazio(conn, monkeypatch):
    chamadas = []

    async def _fake(*a, **k):
        chamadas.append(1)
        return "nunca deveria rodar"
    monkeypatch.setattr(llm, "_call_llm", _fake)

    with pytest.raises(ValueError):
        asyncio.run(curadoria_narrativa.narrar(conn, CFG, "u1", "estudo", []))
    assert chamadas == []


def test_narrar_registro_de_uso_falhando_nao_derruba_resposta(conn, monkeypatch):
    async def _fake(config, key, system, user, max_tokens):
        return "texto ok"
    monkeypatch.setattr(llm, "_call_llm", _fake)

    def _explode(*a, **k):
        raise RuntimeError("ledger fora do ar")
    monkeypatch.setattr(ai_activity, "registrar_uso", _explode)

    r = asyncio.run(curadoria_narrativa.narrar(conn, CFG, "u1", "estudo", _top_valido()))
    assert r["texto"] == "texto ok"


def test_modulo_nao_importa_motor_nem_provider():
    """Inspeção de fonte: o módulo não importa o motor de opções, não chama
    a enumeração de candidatos por posição nem a ordenação, e não toca o
    provedor de mercado — o guardrail estrutural declarado no docstring."""
    src = open(curadoria_narrativa.__file__).read()
    linhas_sem_comentario = [l for l in src.splitlines() if not l.lstrip().startswith("#")]
    blob = "\n".join(linhas_sem_comentario)
    for banido in ("opcoes_motor", "candidatos_da_posicao", "rankear(", "options_provider", "get_options"):
        assert banido not in blob, f"{banido!r} não pode aparecer no corpo do módulo"
