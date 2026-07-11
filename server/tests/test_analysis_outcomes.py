"""qa/30 (Fase A) — testes da autoavaliação da IA (analysis_outcomes.py).
Puro/testável: candles injetados em _avaliar_entry, fetch injetado em
avaliar_pendentes (mesmo padrão de scan_deep/radar_daily). Stdlib; roda
standalone e via pytest.
"""
import asyncio
import os
import tempfile
from datetime import datetime, timedelta, timezone

from app import analysis_outcomes as ao
from app import db


def _fresh_db():
    d = tempfile.mkdtemp(prefix="b3_outcomes_")
    return db.connect(os.path.join(d, "b3_agente.db"))


def _candles(dias):
    """Gera `dias` candles diários crescentes a partir de amanhã, todos com
    high/low/close = valor informado (sem gap) — testes ajustam pontos
    específicos quando precisam de um high/low diferente do close."""
    base = datetime.now(timezone.utc).date() + timedelta(days=1)
    out = []
    for i, v in enumerate(dias):
        out.append({"date": (base + timedelta(days=i)).isoformat(),
                     "open": v, "high": v, "low": v, "close": v, "volume": 1000})
    return out


# ===== registrar() =====
def test_registrar_grava_entrada_valida():
    conn = _fresh_db()
    ao.registrar(conn, ticker="PETR4", modo="operador", tipo="n1", modelo="anthropic:claude",
                 setup="IFR2", recomendacao="COMPRAR", stop=37.60, alvo=40.05, preco=38.57,
                 snapshot_id="snap1", user_id="u1")
    outcomes = db.kv_get(conn, "analysisOutcomes", [], user_id="u1")
    assert len(outcomes) == 1
    o = outcomes[0]
    assert o["ticker"] == "PETR4" and o["resultado"] == "pendente"
    assert o["stopProposto"] == 37.60 and o["alvoProposto"] == 40.05
    assert o["prazoPregoes"] == ao.HORIZON_PREGOES
    conn.close()


def test_registrar_descarta_sem_stop_alvo_ou_preco():
    conn = _fresh_db()
    ao.registrar(conn, ticker="PETR4", modo="estudo", tipo="n2", modelo="x", setup=None,
                 recomendacao="Monitorar", stop=None, alvo=40.0, preco=38.0,
                 snapshot_id=None, user_id="u1")
    ao.registrar(conn, ticker="PETR4", modo="estudo", tipo="n2", modelo="x", setup=None,
                 recomendacao="Monitorar", stop=37.0, alvo=37.0, preco=38.0,   # stop == alvo
                 snapshot_id=None, user_id="u1")
    assert db.kv_get(conn, "analysisOutcomes", [], user_id="u1") == []
    conn.close()


def test_registrar_prune_por_quantidade():
    conn = _fresh_db()
    cap_original = ao.CAP
    ao.CAP = 3
    try:
        for i in range(5):
            ao.registrar(conn, ticker=f"T{i}", modo="estudo", tipo="n1", modelo="x", setup=None,
                         recomendacao="COMPRAR", stop=9.0, alvo=11.0, preco=10.0,
                         snapshot_id=None, user_id="u1")
        outcomes = db.kv_get(conn, "analysisOutcomes", [], user_id="u1")
        assert len(outcomes) == 3
        assert [o["ticker"] for o in outcomes] == ["T2", "T3", "T4"]  # mantém os mais recentes
    finally:
        ao.CAP = cap_original
    conn.close()


# ===== _avaliar_entry (pura, sem I/O) =====
def _entry(stop=37.60, alvo=40.05, preco=38.57, prazo=10):
    return {"ticker": "PETR4", "criadoEm": datetime.now(timezone.utc).isoformat(),
            "prazoPregoes": prazo, "stopProposto": stop, "alvoProposto": alvo, "precoNaAnalise": preco}


def test_avaliar_entry_ainda_pendente_poucos_candles():
    r = ao._avaliar_entry(_entry(), _candles([38.6] * 3))
    assert r is None


def test_avaliar_entry_bate_alvo_compra():
    candles = _candles([38.6, 38.8, 39.0, 39.4, 39.8, 40.10, 40.2, 40.3, 40.4, 40.5])
    r = ao._avaliar_entry(_entry(stop=37.60, alvo=40.05), candles)
    assert r["resultado"] == "alvo"
    assert r["precoResolucao"] == 40.05
    assert r["rMultiple"] > 0


def test_avaliar_entry_bate_stop_compra():
    candles = _candles([38.3, 38.0, 37.9, 37.55, 39.0, 39.0, 39.0, 39.0, 39.0, 39.0])
    r = ao._avaliar_entry(_entry(stop=37.60, alvo=40.05), candles)
    assert r["resultado"] == "stop"
    assert r["precoResolucao"] == 37.60
    assert r["rMultiple"] == -1.0  # stop = -1R por definição do plano


def test_avaliar_entry_expira_positivo_e_negativo():
    candles_pos = _candles([38.6, 38.7, 38.8, 38.9, 39.0, 39.0, 39.0, 39.0, 39.0, 39.1])
    r_pos = ao._avaliar_entry(_entry(stop=37.60, alvo=40.05), candles_pos)
    assert r_pos["resultado"] == "expirou_pos"

    candles_neg = _candles([38.5, 38.4, 38.3, 38.2, 38.1, 38.0, 37.9, 37.8, 37.7, 37.65])
    r_neg = ao._avaliar_entry(_entry(stop=37.60, alvo=40.05), candles_neg)
    assert r_neg["resultado"] == "expirou_neg"


def test_avaliar_entry_lado_venda_geometria_invertida():
    # alvo < stop => short (mesma geometria de setups.plano_operacional p/ VENDER)
    candles = _candles([59.0, 58.0, 57.0, 55.5, 60.0, 60.0, 60.0, 60.0, 60.0, 60.0])
    r = ao._avaliar_entry(_entry(stop=61.10, alvo=55.80, preco=59.80), candles)
    assert r["resultado"] == "alvo"
    assert r["rMultiple"] > 0


# ===== compute_stats (pura) =====
def _outcome(resultado, r_multiple=None, modo="estudo", tipo="n1", setup="IFR2"):
    return {"resultado": resultado, "rMultiple": r_multiple, "modo": modo, "tipo": tipo, "setup": setup}


def test_compute_stats_taxa_acerto_e_r_medio():
    outcomes = [
        _outcome("alvo", 1.0), _outcome("alvo", 0.8), _outcome("stop", -1.0),
        _outcome("expirou_pos", 0.3), _outcome("expirou_neg", -0.4),
        _outcome("pendente"),
    ]
    st = ao.compute_stats(outcomes)
    assert st["totalAnalises"] == 6
    assert st["pendentes"] == 1
    assert st["avaliadas"] == 5
    assert st["taxaAcerto"] == 60.0  # 3 sucesso (alvo, alvo, expirou_pos) / 5
    assert st["rMedio"] == round((1.0 + 0.8 - 1.0 + 0.3 - 0.4) / 5, 2)


def test_compute_stats_filtra_por_modo_e_recorte_por_setup():
    outcomes = [
        _outcome("alvo", 1.0, modo="operador", setup="IFR2"),
        _outcome("stop", -1.0, modo="operador", setup="IFR2"),
        _outcome("alvo", 1.0, modo="estudo", setup="Stormer"),
    ]
    st_op = ao.compute_stats(outcomes, modo="operador")
    assert st_op["totalAnalises"] == 2
    assert st_op["porSetup"]["IFR2"] == {"acerto": 1, "total": 2}
    st_all = ao.compute_stats(outcomes)
    assert st_all["totalAnalises"] == 3


# ===== qa/35 (P2): expectância + calibração + CSV (puras) =====
def _outcome_conf(resultado, r, confianca=None, recomendacao="Estudar alta"):
    return {"resultado": resultado, "rMultiple": r, "modo": "estudo", "tipo": "n1",
            "setup": "IFR2", "confianca": confianca, "recomendacao": recomendacao}


def test_normalizar_confianca_escala_unica():
    # N1 (confianca) e N2 (conviccao) caem na MESMA escala
    assert ao.normalizar_confianca("moderada") == "moderada"
    assert ao.normalizar_confianca("baixa") == "baixa"
    assert ao.normalizar_confianca("Muito Alto") == "alta"
    assert ao.normalizar_confianca("Alto") == "alta"
    assert ao.normalizar_confianca("Médio") == "moderada"
    assert ao.normalizar_confianca("Baixo") == "baixa"
    assert ao.normalizar_confianca(None) is None
    assert ao.normalizar_confianca("banana") is None


def test_registrar_guarda_confianca_normalizada():
    conn = _fresh_db()
    ao.registrar(conn, ticker="PETR4", modo="estudo", tipo="n2", modelo="x", setup=None,
                 recomendacao="Estudar alta", stop=9.0, alvo=11.0, preco=10.0,
                 snapshot_id=None, confianca="Muito Alto", user_id=None)
    outcomes = db.kv_get(conn, "analysisOutcomes", [], user_id=None)
    assert outcomes[0]["confianca"] == "alta"
    conn.close()


def test_compute_stats_expectancia_e_profit_factor():
    # 12 avaliadas (>= MIN_N=10): 8 ganhos de +1R, 4 perdas de -1R
    outcomes = [_outcome_conf("alvo", 1.0) for _ in range(8)] + \
               [_outcome_conf("stop", -1.0) for _ in range(4)]
    st = ao.compute_stats(outcomes)
    assert st["expectanciaInsuficiente"] is False
    assert st["expectancia"] == round((8 - 4) / 12, 2)
    assert st["profitFactor"] == 2.0  # 8 / |-4|
    assert st["minN"] == ao.MIN_N


def test_compute_stats_expectancia_n_insuficiente():
    # 5 avaliadas (< MIN_N): nada de % enganosa — regra do produto
    outcomes = [_outcome_conf("alvo", 1.0) for _ in range(5)]
    st = ao.compute_stats(outcomes)
    assert st["expectanciaInsuficiente"] is True
    assert st["expectancia"] is None
    assert st["profitFactor"] is None


def test_compute_stats_profit_factor_sem_perdas_vira_inf():
    outcomes = [_outcome_conf("alvo", 1.0) for _ in range(10)]
    st = ao.compute_stats(outcomes)
    assert st["profitFactor"] == "inf"  # serializável em JSON (não float inf)


def test_compute_stats_calibracao_por_confianca_e_decisao():
    # 10 de confiança alta (7 acertos) + 3 de baixa (célula insuficiente)
    outcomes = [_outcome_conf("alvo" if i < 7 else "stop", 1.0 if i < 7 else -1.0, "alta")
                for i in range(10)] + \
               [_outcome_conf("stop", -1.0, "baixa", recomendacao="Não operar") for _ in range(3)]
    st = ao.compute_stats(outcomes)
    alta = st["porConfianca"]["alta"]
    assert alta["n"] == 10 and alta["insuficiente"] is False and alta["taxaAcerto"] == 70.0
    baixa = st["porConfianca"]["baixa"]
    assert baixa["n"] == 3 and baixa["insuficiente"] is True and baixa["taxaAcerto"] is None
    assert st["porDecisao"]["Estudar alta"]["n"] == 10
    assert st["porDecisao"]["Não operar"]["insuficiente"] is True


def test_compute_stats_sem_confianca_cai_no_bucket_sem_declaracao():
    outcomes = [_outcome_conf("alvo", 1.0, None) for _ in range(10)]
    st = ao.compute_stats(outcomes)
    assert st["porConfianca"]["—"]["n"] == 10


def test_to_csv_colunas_fixas_e_escape():
    outcomes = [{"id": "a1", "ticker": "PETR4", "modo": "estudo", "tipo": "n1",
                 "modelo": "prov:mod", "setup": 'IFR2 "clássico", B', "recomendacao": None,
                 "confianca": "alta", "stopProposto": 9.0, "alvoProposto": 11.0,
                 "precoNaAnalise": 10.0, "snapshotId": None, "criadoEm": "2026-07-10T12:00:00+00:00",
                 "prazoPregoes": 10, "resultado": "alvo", "precoResolucao": 11.0,
                 "rMultiple": 1.0, "resolvidoEm": "2026-07-15"}]
    csv = ao.to_csv(outcomes)
    linhas = csv.strip().split("\n")
    assert linhas[0].startswith("id,ticker,modo,tipo,modelo,setup,recomendacao,confianca,")
    assert '"IFR2 ""clássico"", B"' in linhas[1]   # vírgula+aspas escapadas
    assert ",," in linhas[1]                        # None vira célula VAZIA (nunca inferida)
    assert ao.to_csv([]) .startswith("id,ticker")   # só cabeçalho quando vazio


# ===== avaliar_pendentes (fetch injetado) =====
def test_avaliar_pendentes_atualiza_e_isola_por_escopo():
    conn = _fresh_db()
    ao.registrar(conn, ticker="PETR4", modo="operador", tipo="n1", modelo="x", setup="IFR2",
                 recomendacao="COMPRAR", stop=37.60, alvo=40.05, preco=38.57,
                 snapshot_id=None, user_id="u1")
    ao.registrar(conn, ticker="VALE3", modo="estudo", tipo="n1", modelo="x", setup="Stormer",
                 recomendacao="COMPRAR", stop=59.80, alvo=63.90, preco=61.10,
                 snapshot_id=None, user_id="u2")

    candles_petr = _candles([38.6, 38.8, 39.0, 39.4, 39.8, 40.10, 40.2, 40.3, 40.4, 40.5])
    candles_vale = _candles([61.2] * 10)  # nem alvo nem stop -> expira

    async def fetch(ticker, rng="6mo"):
        return {"candles": candles_petr if ticker == "PETR4" else candles_vale}

    n = asyncio.run(ao.avaliar_pendentes(conn, fetch))
    assert n == 2
    u1 = db.kv_get(conn, "analysisOutcomes", [], user_id="u1")
    u2 = db.kv_get(conn, "analysisOutcomes", [], user_id="u2")
    assert u1[0]["resultado"] == "alvo"
    assert u2[0]["resultado"] in ("expirou_pos", "expirou_neg")
    # escopos não se misturam: u1 não tem VALE3, u2 não tem PETR4
    assert {o["ticker"] for o in u1} == {"PETR4"}
    assert {o["ticker"] for o in u2} == {"VALE3"}
    conn.close()


def test_avaliar_pendentes_mantem_pendente_sem_candles_suficientes():
    conn = _fresh_db()
    ao.registrar(conn, ticker="PETR4", modo="operador", tipo="n1", modelo="x", setup=None,
                 recomendacao="COMPRAR", stop=37.60, alvo=40.05, preco=38.57,
                 snapshot_id=None, user_id="u1")

    async def fetch(ticker, rng="6mo"):
        return {"candles": _candles([38.6, 38.8])}  # só 2 pregões -- prazo é 10

    n = asyncio.run(ao.avaliar_pendentes(conn, fetch))
    assert n == 0
    outcomes = db.kv_get(conn, "analysisOutcomes", [], user_id="u1")
    assert outcomes[0]["resultado"] == "pendente"
    conn.close()


def test_scopes_com_outcomes_ve_escopo_legado_e_por_usuario():
    conn = _fresh_db()
    ao.registrar(conn, ticker="PETR4", modo="estudo", tipo="n1", modelo="x", setup=None,
                 recomendacao="COMPRAR", stop=9.0, alvo=11.0, preco=10.0,
                 snapshot_id=None, user_id=None)   # escopo legado/global
    ao.registrar(conn, ticker="VALE3", modo="estudo", tipo="n1", modelo="x", setup=None,
                 recomendacao="COMPRAR", stop=9.0, alvo=11.0, preco=10.0,
                 snapshot_id=None, user_id="u1")
    scopes = ao._scopes_com_outcomes(conn)
    assert None in scopes and "u1" in scopes
    conn.close()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("TODOS OS TESTES DE ANALYSIS_OUTCOMES PASSARAM")
