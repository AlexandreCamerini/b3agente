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
import datetime as dt
import os
import tempfile
import uuid

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import ai_activity, curadoria_narrativa, db, llm, opcoes_curadoria, options_provider, store
import app.main as main_mod
from app.main import app, _conn

_EXP_DIAS = 30
_EXP = (dt.date.today() + dt.timedelta(days=_EXP_DIAS)).isoformat()


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
        "razao": razao,
        # Fase 39/D-08/D-09 (2026-09-24): `premioAnualizado` espelha `razao`
        # (mesma monotonicidade que os testes de ordem desta fixture já
        # exercitam) e `probOtm` fixo acima do piso — `exigir_ranking`
        # (chamada dentro de `curadoria_narrativa.narrar`) exige os dois
        # agora, reversão deliberada da métrica de admissão+ordem.
        "premioAnualizado": razao, "probOtm": 0.65, "volatilidadeFonte": "implicita",
        "manchete": "manchete", "didatica": "didatica",
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


# ─────────────────────────────────────────────────────────────────────────
# Task 2 — `POST /api/options/curadoria/narrativa` (via TestClient)
# ─────────────────────────────────────────────────────────────────────────

def _contrato(symbol, strike, price=1.5, volume=5000, oi=1000, bid=1.48, ask=1.52):
    return {
        "contractSymbol": symbol, "optionType": "call", "strike": strike,
        "lastPrice": price, "bid": bid, "ask": ask, "volume": volume,
        "openInterest": oi, "impliedVolatility": 0.3, "inTheMoney": False,
        "currency": "BRL", "distancePct": None,
        "greeks": {"delta": None, "gamma": None, "vega": None, "theta": None, "rho": None},
        "expiration": _EXP,
    }


def _cadeia(underlying, n_strikes=1, provider_status="ok", spot=29.0):
    base = 30
    calls = [_contrato(f"{underlying}C{base + i}", base + i, price=3.0 - i * 0.1) for i in range(n_strikes)]
    return {
        "providerStatus": provider_status, "underlyingPrice": spot,
        "expiration": _EXP, "expirations": [_EXP],
        "calls": calls, "puts": [], "source": "teste",
    }


@pytest.fixture(autouse=True)
def _quote_fake(monkeypatch):
    from app import candle_provider

    async def _fake(t, *a, **k):
        return {"t": t, "price": 29.0, "source": "teste"}
    monkeypatch.setattr(candle_provider, "get_quote", _fake)


@pytest.fixture
def cli():
    with TestClient(app) as c:
        yield c


def _novo_escopo(cli, slug):
    email = f"curnar-{slug}-{uuid.uuid4().hex[:10]}@teste.com"
    r = cli.post("/api/auth/register", json={"email": email, "password": "senhaboa123"})
    assert r.status_code == 200, r.text
    body = r.json()
    return body["user"]["id"], {"Authorization": "Bearer " + body["token"]}


def _seed_uma_posicao_elegivel(uid, ticker="PETR4"):
    store.buy(_conn, ticker, 200, 25.0, user_id=uid)


def _get_options_fake(chains):
    async def _fake(t, *a, **k):
        return chains.get(t, _cadeia(t, provider_status="degraded"))
    return _fake


def _fake_call_llm_fixo(chamadas, texto="Parágrafo sobre a estrutura."):
    async def _fake(config, key, system, user, max_tokens):
        chamadas.append((system, user))
        return texto
    return _fake


def test_post_com_cota_disponivel_devolve_200_e_consome_uma_vez(cli, monkeypatch):
    uid, headers = _novo_escopo(cli, "01")
    _seed_uma_posicao_elegivel(uid)
    monkeypatch.setattr(options_provider, "get_options", _get_options_fake({"PETR4": _cadeia("PETR4", n_strikes=1)}))
    chamadas = []
    monkeypatch.setattr(llm, "_call_llm", _fake_call_llm_fixo(chamadas))

    consumos = []
    monkeypatch.setattr(main_mod, "_gate_analise",
                         lambda scope, config, custo=1: (config, lambda: consumos.append(1)))

    r = cli.post("/api/options/curadoria/narrativa", json={}, headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["texto"]
    assert body["top"]
    assert len(chamadas) == 1
    assert consumos == [1], "consume() precisa ser chamado EXATAMENTE uma vez"


def test_post_com_402_do_gate_propaga_e_nao_chama_llm(cli, monkeypatch):
    uid, headers = _novo_escopo(cli, "02")
    _seed_uma_posicao_elegivel(uid)
    monkeypatch.setattr(options_provider, "get_options", _get_options_fake({"PETR4": _cadeia("PETR4", n_strikes=1)}))
    chamadas = []
    monkeypatch.setattr(llm, "_call_llm", _fake_call_llm_fixo(chamadas))

    def _nega(scope, config, custo=1):
        raise HTTPException(402, "Você atingiu o limite de análises do seu plano.")
    monkeypatch.setattr(main_mod, "_gate_analise", _nega)

    r = cli.post("/api/options/curadoria/narrativa", json={}, headers=headers)
    assert r.status_code == 402, r.text
    assert "limite" in r.json()["detail"].lower()
    assert chamadas == []


def test_post_sem_estrutura_elegivel_200_sem_chamar_llm_nem_consumir(cli, monkeypatch):
    uid, headers = _novo_escopo(cli, "03")
    # carteira vazia: nenhuma posição elegível, `top` vem vazio
    chamadas = []
    monkeypatch.setattr(llm, "_call_llm", _fake_call_llm_fixo(chamadas))
    consumos = []
    monkeypatch.setattr(main_mod, "_gate_analise",
                         lambda scope, config, custo=1: (config, lambda: consumos.append(1)))

    r = cli.post("/api/options/curadoria/narrativa", json={}, headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["texto"] is None
    assert body["motivo"] == "sem_estrutura"
    assert body["top"] == []
    assert chamadas == []
    assert consumos == [], "cota não pode ser gasta quando não há o que narrar"


def test_post_com_llm_falhando_502_e_nao_consome(cli, monkeypatch):
    uid, headers = _novo_escopo(cli, "04")
    _seed_uma_posicao_elegivel(uid)
    monkeypatch.setattr(options_provider, "get_options", _get_options_fake({"PETR4": _cadeia("PETR4", n_strikes=1)}))

    async def _explode(*a, **k):
        raise RuntimeError("provedor de LLM fora do ar")
    monkeypatch.setattr(llm, "_call_llm", _explode)

    consumos = []
    monkeypatch.setattr(main_mod, "_gate_analise",
                         lambda scope, config, custo=1: (config, lambda: consumos.append(1)))

    r = cli.post("/api/options/curadoria/narrativa", json={}, headers=headers)
    assert r.status_code == 502, r.text
    assert consumos == []


def test_corpo_da_requisicao_nao_influencia_a_ordem(cli, monkeypatch):
    """T-30-12: corpo adulterado (`top`/`candidatos` de 9 itens invertidos)
    não muda a resposta — a rota recomputa no servidor e ignora o corpo."""
    uid, headers = _novo_escopo(cli, "05")
    _seed_uma_posicao_elegivel(uid)
    monkeypatch.setattr(options_provider, "get_options", _get_options_fake({"PETR4": _cadeia("PETR4", n_strikes=3)}))
    chamadas = []
    monkeypatch.setattr(llm, "_call_llm", _fake_call_llm_fixo(chamadas))
    monkeypatch.setattr(main_mod, "_gate_analise",
                         lambda scope, config, custo=1: (config, lambda: None))

    r_vazio = cli.post("/api/options/curadoria/narrativa", json={}, headers=headers)
    assert r_vazio.status_code == 200, r_vazio.text

    pool_adulterado = [_item(f"XXXX{i}", razao=float(i), posicao=9 - i) for i in range(9)]
    r_adulterado = cli.post(
        "/api/options/curadoria/narrativa",
        json={"top": list(reversed(pool_adulterado)), "candidatos": pool_adulterado},
        headers=headers)
    assert r_adulterado.status_code == 200, r_adulterado.text

    a = [c["contractSymbol"] for c in r_vazio.json()["top"]]
    b = [c["contractSymbol"] for c in r_adulterado.json()["top"]]
    assert a == b, "corpo adulterado não pode mudar a ordem/composição do top"
    assert len(a) <= opcoes_curadoria.TOPO


def test_estruturas_da_resposta_casa_com_top_na_ordem(cli, monkeypatch):
    uid, headers = _novo_escopo(cli, "06")
    _seed_uma_posicao_elegivel(uid)
    monkeypatch.setattr(options_provider, "get_options", _get_options_fake({"PETR4": _cadeia("PETR4", n_strikes=2)}))
    chamadas = []
    monkeypatch.setattr(llm, "_call_llm", _fake_call_llm_fixo(chamadas))
    monkeypatch.setattr(main_mod, "_gate_analise",
                         lambda scope, config, custo=1: (config, lambda: None))

    r = cli.post("/api/options/curadoria/narrativa", json={}, headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["estruturas"] == [it["contractSymbol"] for it in body["top"]]


def test_ia_nunca_recebe_pool_nao_rankeado(cli, monkeypatch):
    """T-30-13: `narrar` é chamada com EXATAMENTE o que a ordenação do motor
    determinístico produziu — capturado no call site real da rota — e
    passar uma lista de 9 itens desordenados direto para `narrar` levanta
    `ValueError`."""
    uid, headers = _novo_escopo(cli, "07")
    _seed_uma_posicao_elegivel(uid)
    monkeypatch.setattr(options_provider, "get_options", _get_options_fake({"PETR4": _cadeia("PETR4", n_strikes=3)}))
    monkeypatch.setattr(main_mod, "_gate_analise",
                         lambda scope, config, custo=1: (config, lambda: None))

    vistos = {}
    real_narrar = curadoria_narrativa.narrar

    async def _espiao(conn, config, scope, modo, top):
        vistos["top"] = top
        return await real_narrar(conn, config, scope, modo, top)
    monkeypatch.setattr(main_mod.curadoria_narrativa, "narrar", _espiao)

    async def _fake_llm(config, key, system, user, max_tokens):
        return "texto"
    monkeypatch.setattr(llm, "_call_llm", _fake_llm)

    r = cli.post("/api/options/curadoria/narrativa", json={}, headers=headers)
    assert r.status_code == 200, r.text
    top_recebido = vistos["top"]

    modo_scope = (store.get(_conn, "config", user_id=uid) or {}).get("appMode") or "estudo"
    top_esperado, _meta = asyncio.run(main_mod._curadoria_top(uid, modo_scope))
    assert [c["contractSymbol"] for c in top_recebido] == [c["contractSymbol"] for c in top_esperado]
    assert len(top_recebido) <= opcoes_curadoria.TOPO
    razoes = [c["razao"] for c in top_recebido]
    assert razoes == sorted(razoes, reverse=True)

    pool_desordenado = [_item(f"YYYY{i}", razao=float(9 - i), posicao=i + 1) for i in range(9)]
    with pytest.raises(ValueError):
        asyncio.run(real_narrar(_conn, CFG, uid, "estudo", pool_desordenado))


# ─────────────────────────────────────────────────────────────────────────
# `_gate_analise` REAL (não mockado) — BYOK/plano mensal, precedência D6
#
# Os testes acima mockam `_gate_analise` para isolar o comportamento da
# ROTA (402 propaga, consume só no sucesso, top vazio não gasta). Os
# testes abaixo exercitam o gate de VERDADE, sem mock nenhum — a mesma
# função que decide a cota de `/api/analyze` — para provar que a
# narração usa exatamente essa precedência (BYOK → plano mensal), não uma
# reimplementação paralela.
# ─────────────────────────────────────────────────────────────────────────

CONFIG_BYOK = {"provider": "anthropic", "model": "claude-opus-5",
               "apiKey": "sk-chave-propria-de-teste", "appMode": "estudo"}


def test_gate_real_byok_ignora_ledger_estourado_e_nao_consome_mensal(cli, monkeypatch):
    """BYOK real: mesmo com o ledger mensal MUITO acima do limite do FREE
    (30), a chave própria destrava a rota (gate real, sem mock) e o ledger
    mensal não muda — BYOK não é o recurso que ele mede."""
    uid, headers = _novo_escopo(cli, "gate-byok")
    _seed_uma_posicao_elegivel(uid)
    monkeypatch.setattr(options_provider, "get_options", _get_options_fake({"PETR4": _cadeia("PETR4", n_strikes=1)}))
    chamadas = []
    monkeypatch.setattr(llm, "_call_llm", _fake_call_llm_fixo(chamadas))
    from app import metering
    metering.consume(_conn, uid, custo=100)
    assert metering.month_used(_conn, uid) == 100

    r = cli.post("/api/options/curadoria/narrativa", json={"config": CONFIG_BYOK}, headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["texto"]
    assert len(chamadas) == 1
    assert metering.month_used(_conn, uid) == 100, "BYOK não escreve no ledger mensal"


def test_gate_real_402_do_plano_mensal_propaga_sem_byok(cli, monkeypatch):
    """Sem chave própria e ledger mensal estourado: o gate REAL nega com
    402 (plan.can_analyze), a rota propaga (não mascara em 200), e o
    modelo de linguagem nunca é chamado."""
    uid, headers = _novo_escopo(cli, "gate-402")
    _seed_uma_posicao_elegivel(uid)
    monkeypatch.setattr(options_provider, "get_options", _get_options_fake({"PETR4": _cadeia("PETR4", n_strikes=1)}))
    chamadas = []
    monkeypatch.setattr(llm, "_call_llm", _fake_call_llm_fixo(chamadas))
    from app import metering
    metering.consume(_conn, uid, custo=100)

    r = cli.post("/api/options/curadoria/narrativa", json={}, headers=headers)
    assert r.status_code == 402, r.text
    assert chamadas == [], "o gate real negou; o modelo não pode ter sido chamado"
    assert metering.month_used(_conn, uid) == 100, "negado: ledger não muda"


def test_gate_real_managed_consome_ledger_mensal_so_no_sucesso(cli, monkeypatch):
    """Sem BYOK, sem IA gerenciada habilitada no ambiente de teste (nenhuma
    env `B3_MANAGED_LLM_*`): o gate real segue o ramo "sem BYOK e sem
    gerenciada" de `_ai_apply_managed` (config intacta, consume no-op) —
    aqui o que se prova é que ESSA é a config que chega em `narrar` (a
    mesma que `/api/analyze` usaria no mesmo ambiente), não uma cópia
    paralela composta pela rota de narração."""
    uid, headers = _novo_escopo(cli, "gate-managed")
    _seed_uma_posicao_elegivel(uid)
    monkeypatch.setattr(options_provider, "get_options", _get_options_fake({"PETR4": _cadeia("PETR4", n_strikes=1)}))
    vistos = {}

    async def _fake(config, key, system, user, max_tokens):
        vistos["config"] = config
        return "texto"
    monkeypatch.setattr(llm, "_call_llm", _fake)
    from app import metering
    antes = metering.month_used(_conn, uid)

    r = cli.post("/api/options/curadoria/narrativa",
                 json={"config": {"provider": "anthropic", "model": "claude-opus-5", "appMode": "estudo"}},
                 headers=headers)
    assert r.status_code == 200, r.text
    assert vistos["config"].get("appMode") == "estudo"
    # sem gerenciada configurada no ambiente, `_ai_apply_managed` devolve
    # consume no-op (comentário da própria função: "llm dará erro
    # acionável") — o ledger mensal não é o que este ramo mede.
    assert metering.month_used(_conn, uid) == antes


def test_body_get_top_ou_candidatos_nao_existe_em_main():
    """Guardião estático (T-30-12): a rota não lê `top`/`candidatos`/
    `estruturas` do corpo em lugar nenhum de `main.py` — só `config` sai do
    corpo. Comentários filtrados antes de contar."""
    src = open(main_mod.__file__).read()
    linhas_sem_comentario = [l for l in src.splitlines() if not l.lstrip().startswith("#")]
    blob = "\n".join(linhas_sem_comentario)
    for proibido in ('body.get("top")', 'body.get("candidatos")', 'body.get("estruturas")'):
        assert proibido not in blob, f"{proibido!r} não pode aparecer em main.py"
