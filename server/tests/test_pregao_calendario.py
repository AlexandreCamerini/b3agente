"""Guardião da janela de negociação da B3 (`app/pregao.py`, 2026-08-17).

O QUE ISTO PROTEGE: antes, `in_market_hours` era `seg–sex, 10 <= hora < 18` e
tratava como pregão o call de fechamento (16:55–17:00), a zona morta até 17:30,
o after-market e TODOS os feriados. Cada uma dessas janelas custava uma passada
intraday (65 ativos) e consulta de cotação por usuário sem dado novo — ~13
passadas/dia no rabo da tarde e ~83 num feriado, 10 a 12 vezes por ano.

AFTER-MARKET FICA DE FORA por decisão explícita do Alex (2026-08-17): regras
próprias (só ativos do pregão regular, oscilação ±2% do fechamento) que a fonte
de cotação pode não refletir. `B3_AFTER_MARKET=1` liga para quem assumir isso.
"""
from datetime import date, datetime

import pytest

from app import agent, pregao

BRT = pregao.BRT


def em(ano, mes, dia, h, m):
    return datetime(ano, mes, dia, h, m, tzinfo=BRT)


# ------------------------------ fronteiras de horário -----------------------
# 2026-08-17 é uma segunda-feira comum, sem feriado.
@pytest.mark.parametrize("h,m,aberto", [
    (9, 44, False),   # antes do cancelamento de ofertas
    (9, 45, False),   # cancelamento de ofertas — não negocia
    (9, 59, False),   # pré-abertura — não negocia
    (10, 0, True),    # abre a negociação contínua
    (10, 1, True),
    (16, 54, True),   # último minuto de negociação
    (16, 55, False),  # call de fechamento começa — NÃO é negociação contínua
    (17, 0, False),   # zona morta
    (17, 29, False),
    (17, 30, False),  # after-market: excluído por decisão
    (17, 59, False),
    (18, 0, False),
    (23, 59, False),
])
def test_fronteiras_do_dia_util(h, m, aberto):
    assert pregao.in_market_hours(em(2026, 8, 17, h, m)) is aberto


def test_agent_delega_para_pregao():
    """`agent.in_market_hours` é o ponto único que intraday/timing/timing_watch
    consomem — se parar de delegar, a correção vaza por eles."""
    assert agent.in_market_hours(em(2026, 8, 17, 16, 54)) is True
    assert agent.in_market_hours(em(2026, 8, 17, 17, 45)) is False


# ------------------------------ fim de semana -------------------------------
def test_sabado_e_domingo_fechados():
    assert pregao.in_market_hours(em(2026, 8, 15, 11, 0)) is False  # sábado
    assert pregao.in_market_hours(em(2026, 8, 16, 11, 0)) is False  # domingo


# ------------------------------ feriados ------------------------------------
def test_pascoa_conhecida():
    """Base dos móveis — se este cálculo errar, Carnaval/Corpus Christi erram
    junto e o app abre em feriado."""
    assert pregao._pascoa(2025) == date(2025, 4, 20)
    assert pregao._pascoa(2026) == date(2026, 4, 5)
    assert pregao._pascoa(2027) == date(2027, 3, 28)


@pytest.mark.parametrize("d,nome", [
    (date(2026, 1, 1), "Confraternização"),
    (date(2026, 2, 16), "Carnaval (segunda)"),
    (date(2026, 2, 17), "Carnaval (terça)"),
    (date(2026, 4, 3), "Sexta-feira Santa"),
    (date(2026, 4, 21), "Tiradentes"),
    (date(2026, 5, 1), "Dia do Trabalho"),
    (date(2026, 6, 4), "Corpus Christi"),
    (date(2026, 9, 7), "Independência"),
    (date(2026, 10, 12), "Aparecida"),
    (date(2026, 11, 2), "Finados"),
    (date(2026, 11, 20), "Consciência Negra"),
    (date(2026, 12, 25), "Natal"),
])
def test_feriados_de_2026(d, nome):
    assert pregao.is_holiday(d), nome
    assert pregao.is_trading_day(d) is False, nome


def test_feriado_movel_acompanha_o_ano():
    """Ano diferente, data diferente — o cálculo não pode estar chumbado."""
    assert pregao.is_holiday(date(2025, 3, 3))   # Carnaval 2025 (segunda)
    assert pregao.is_holiday(date(2027, 2, 8))   # Carnaval 2027 (segunda)
    assert not pregao.is_holiday(date(2027, 2, 16))  # é Carnaval só em 2026


def test_feriado_nao_negocia_nem_no_meio_do_pregao():
    assert pregao.in_market_hours(em(2026, 12, 25, 11, 0)) is False


def test_24_e_31_de_dezembro_fechados_quando_dia_util():
    assert pregao.is_holiday(date(2026, 12, 24))  # quinta
    assert pregao.is_holiday(date(2026, 12, 31))  # quinta


def test_dia_util_comum_negocia():
    assert pregao.is_trading_day(date(2026, 8, 17)) is True
    assert pregao.in_market_hours(em(2026, 8, 17, 11, 0)) is True


# ------------------------------ escapes ------------------------------------
def test_env_fecha_um_dia_sem_deploy(monkeypatch):
    monkeypatch.setenv("B3_FERIADOS_EXTRA", "2026-08-17,2026-08-18")
    assert pregao.is_trading_day(date(2026, 8, 17)) is False
    assert pregao.in_market_hours(em(2026, 8, 17, 11, 0)) is False


def test_env_malformada_nao_derruba(monkeypatch):
    monkeypatch.setenv("B3_FERIADOS_EXTRA", "lixo,,2026-13-99,2026-08-18")
    assert pregao.is_trading_day(date(2026, 8, 17)) is True   # segue funcionando
    assert pregao.is_trading_day(date(2026, 8, 18)) is False  # a válida vale


def test_after_market_so_com_opt_in(monkeypatch):
    quinze_e_meia = em(2026, 8, 17, 17, 45)
    assert pregao.in_market_hours(quinze_e_meia) is False
    monkeypatch.setenv("B3_AFTER_MARKET", "1")
    assert pregao.in_market_hours(quinze_e_meia) is True
    # nem com o opt-in a zona morta abre
    assert pregao.in_market_hours(em(2026, 8, 17, 17, 10)) is False
    # e feriado continua fechado
    assert pregao.in_market_hours(em(2026, 12, 25, 17, 45)) is False
