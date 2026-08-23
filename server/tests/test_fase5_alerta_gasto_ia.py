"""Fase 5 (FIX-C38) — alerta PREVENTIVO de gasto de IA, complementar ao hard
stop já existente em `metering.check`/`cap_global` (esse bloqueia; o novo
avisa ANTES de bater o teto).

Task 2 (este bloco): testes UNITÁRIOS PUROS de `metering.alerta_gasto` — a
função não faz I/O (sem `conn`), então roda sem banco/TestClient.

Task 3 adiciona abaixo os testes de ROTA (`GET /api/obs/usage`,
`PUT /api/admin/config/ia`) — só esses usam banco temporário/TestClient.

Regra de produto inegociável (CLAUDE.md item 4): a função NUNCA devolve um
falso "dentro do normal" quando não há base para avaliar — `avaliavel`
sempre distinto de `acima`. É o que os testes (c)/(d) abaixo travam.
"""
from app import metering


# ---------------------------------------------------------------------------
# (a) limiar não configurado / inválido — nunca avaliável
# ---------------------------------------------------------------------------

def test_sem_limiar_configurado_none_nao_e_avaliavel():
    r = metering.alerta_gasto(140, [], None, 7)
    assert r["configurado"] is False
    assert r["avaliavel"] is False
    assert r["acima"] is False


def test_limiar_string_vazia_nao_e_avaliavel():
    r = metering.alerta_gasto(140, [], "", 7)
    assert r["configurado"] is False
    assert r["avaliavel"] is False
    assert r["acima"] is False


def test_limiar_zero_nao_e_avaliavel():
    r = metering.alerta_gasto(140, [], 0, 7)
    assert r["configurado"] is False
    assert r["avaliavel"] is False
    assert r["acima"] is False


def test_limiar_negativo_nao_e_avaliavel():
    r = metering.alerta_gasto(140, [], -10, 7)
    assert r["configurado"] is False
    assert r["avaliavel"] is False
    assert r["acima"] is False


# ---------------------------------------------------------------------------
# (b) histórico insuficiente — configurado, mas não avaliável
# ---------------------------------------------------------------------------

def test_menos_de_tres_dias_passados_configurado_mas_nao_avaliavel():
    serie = [{"day": "2026-08-21", "value": 10}, {"day": "2026-08-22", "value": 12}]
    r = metering.alerta_gasto(140, serie, 30, 7, hoje="2026-08-23")
    assert r["configurado"] is True
    assert r["avaliavel"] is False
    assert r["acima"] is False
    assert "insuficiente" in (r["motivo"] or "").lower()


# ---------------------------------------------------------------------------
# (c) média zero — configurado, mas não avaliável (nunca dividir por zero)
# ---------------------------------------------------------------------------

def test_media_zero_configurado_mas_nao_avaliavel():
    serie = [
        {"day": "2026-08-19", "value": 0}, {"day": "2026-08-20", "value": 0},
        {"day": "2026-08-21", "value": 0}, {"day": "2026-08-22", "value": 0},
    ]
    r = metering.alerta_gasto(5, serie, 30, 7, hoje="2026-08-23")
    assert r["configurado"] is True
    assert r["avaliavel"] is False
    assert r["acima"] is False
    assert "zero" in (r["motivo"] or "").lower()


# ---------------------------------------------------------------------------
# (d)-(e) desvio percentual e comparação com o limiar
# ---------------------------------------------------------------------------

def _serie_media_100(hoje="2026-08-23"):
    dias = ["2026-08-19", "2026-08-20", "2026-08-21", "2026-08-22"]
    return [{"day": d, "value": 100} for d in dias]


def test_hoje_acima_do_limiar_marca_acima_true():
    r = metering.alerta_gasto(140, _serie_media_100(), 30, 7, hoje="2026-08-23")
    assert r["avaliavel"] is True
    assert r["media"] == 100.0
    assert r["desvioPct"] == 40.0
    assert r["acima"] is True


def test_hoje_abaixo_do_limiar_marca_acima_false():
    r = metering.alerta_gasto(120, _serie_media_100(), 30, 7, hoje="2026-08-23")
    assert r["avaliavel"] is True
    assert r["media"] == 100.0
    assert r["desvioPct"] == 20.0
    assert r["acima"] is False


# ---------------------------------------------------------------------------
# (f) o dia de HOJE, se estiver na série, é excluído da média
# ---------------------------------------------------------------------------

def test_dia_de_hoje_na_serie_e_excluido_do_calculo_da_media():
    serie = _serie_media_100() + [{"day": "2026-08-23", "value": 999}]  # hoje, valor absurdo
    r = metering.alerta_gasto(140, serie, 30, 7, hoje="2026-08-23")
    assert r["media"] == 100.0  # não contaminado pelo próprio "hoje"
    assert r["desvioPct"] == 40.0


# ---------------------------------------------------------------------------
# (g) janela respeita janela_dias — só os N dias passados mais recentes
# ---------------------------------------------------------------------------

def test_janela_dias_limita_a_media_aos_n_dias_passados_mais_recentes():
    # 30 pontos, valores crescentes de 1 a 30; hoje é um 31º dia fora da série
    serie = [{"day": f"2026-07-{d:02d}" if d <= 31 else f"2026-08-{d-31:02d}", "value": float(d)}
             for d in range(1, 31)]
    # os 7 dias mais recentes (24..30) têm média (24+25+26+27+28+29+30)/7 = 27.0
    r = metering.alerta_gasto(27, serie, 10, janela_dias=7, hoje="2026-09-01")
    assert r["janelaDias"] == 7
    assert r["media"] == 27.0
    assert r["desvioPct"] == 0.0
    assert r["acima"] is False


# ---------------------------------------------------------------------------
# (h) janela ausente cai no padrão do módulo
# ---------------------------------------------------------------------------

def test_janela_ausente_usa_padrao_do_modulo():
    serie = [{"day": f"2026-08-{d:02d}", "value": 100.0} for d in range(10, 20)]
    r = metering.alerta_gasto(100, serie, 30, None, hoje="2026-08-23")
    assert r["janelaDias"] == metering.ALERTA_JANELA_PADRAO
