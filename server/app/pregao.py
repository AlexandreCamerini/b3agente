"""Calendário e janela de negociação da B3 — fonte ÚNICA de "a bolsa está
aberta agora?".

POR QUE EXISTE (2026-08-17, pedido do Alex): `agent.in_market_hours` era
`seg–sex, 10 <= hora < 18` e o próprio docstring assumia ser "aproximada".
Custava requisição à toa em duas janelas, contra a tabela oficial de horários
do mercado a vista:

  • 16:55 → 18:00 — o pregão contínuo fecha às 16:55. O que vem depois é call
    de fechamento (16:55–17:00), zona morta e after-market. Com o laço a 300s
    e a passada intraday varrendo 65 ativos, era ~13 passadas/dia jogadas fora.
  • FERIADOS — só sábado e domingo eram excluídos. Um feriado com o portão
    aberto o dia inteiro são ~83 passadas × 65 ativos, e a B3 tem 10 a 12 por
    ano.

AFTER-MARKET (17:30–18:00) FICA DE FORA, decisão explícita do Alex: as regras
lá são outras (só ativos que negociaram no pregão regular, oscilação limitada
a ±2% do fechamento) e a fonte de cotação pode não refletir aquilo — simular
execução ali ensinaria um comportamento que não generaliza. `B3_AFTER_MARKET=1`
liga, para quem quiser assumir a diferença.

Os feriados MÓVEIS são derivados da Páscoa, então o calendário vale para
qualquer ano sem manutenção anual e sem dependência nova. O que a B3 anuncia
caso a caso (24/12 e 31/12, luto oficial, etc.) entra em `_EXCECOES` ou na env
`B3_FERIADOS_EXTRA`.
"""
import os
from datetime import date, datetime, timedelta, timezone

BRT = timezone(timedelta(hours=-3))

# Mercado a vista, fracionário, balcão organizado e fundos (tabela da B3).
ABERTURA = (10, 0)      # início da negociação contínua
FECHAMENTO = (16, 55)   # fim da negociação contínua (o call de fechamento não negocia)
AFTER_INICIO = (17, 30)
AFTER_FIM = (18, 0)

# Feriados nacionais de data fixa em que a B3 não abre.
_FIXOS = {
    (1, 1),    # Confraternização Universal
    (4, 21),   # Tiradentes
    (5, 1),    # Dia do Trabalho
    (9, 7),    # Independência
    (10, 12),  # Nossa Senhora Aparecida
    (11, 2),   # Finados
    (11, 15),  # Proclamação da República
    (11, 20),  # Consciência Negra (nacional desde 2024)
    (12, 25),  # Natal
}

# Datas que NÃO saem de regra — a B3 anuncia por ofício. Manter à mão, por ano.
# 24/12 e 31/12: sem pregão quando caem em dia útil (prática consolidada).
_EXCECOES = set()


def _pascoa(ano: int) -> date:
    """Domingo de Páscoa (algoritmo anônimo/Meeus). Base dos feriados móveis."""
    a = ano % 19
    b, c = divmod(ano, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    lo = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * lo) // 451
    mes, dia = divmod(h + lo - 7 * m + 114, 31)
    return date(ano, mes, dia + 1)


def _extra_da_env() -> set:
    """`B3_FERIADOS_EXTRA=2026-12-24,2026-12-31` — fecha um dia sem deploy."""
    out = set()
    for pedaco in (os.environ.get("B3_FERIADOS_EXTRA") or "").split(","):
        pedaco = pedaco.strip()
        if not pedaco:
            continue
        try:
            a, m, d = pedaco.split("-")
            out.add(date(int(a), int(m), int(d)))
        except (ValueError, TypeError):
            continue  # entrada malformada nunca derruba o laço
    return out


def feriados(ano: int) -> set:
    """Todos os feriados da B3 no ano: fixos + móveis + exceções + env."""
    p = _pascoa(ano)
    moveis = {
        p - timedelta(days=48),  # Carnaval (segunda)
        p - timedelta(days=47),  # Carnaval (terça)
        p - timedelta(days=2),   # Sexta-feira Santa
        p + timedelta(days=60),  # Corpus Christi
    }
    fixos = {date(ano, m, d) for (m, d) in _FIXOS}
    # 24/12 e 31/12 só contam como fechado quando caem em dia útil.
    fim_de_ano = {d for d in (date(ano, 12, 24), date(ano, 12, 31)) if d.weekday() < 5}
    return fixos | moveis | fim_de_ano | {d for d in _EXCECOES if d.year == ano} | {
        d for d in _extra_da_env() if d.year == ano}


def is_holiday(d: date) -> bool:
    return d in feriados(d.year)


def is_trading_day(d: date = None) -> bool:
    """Dia com pregão: útil e não feriado. Usado também pelos jobs DIÁRIOS
    (radar, aquecimento de fundamentos, avaliação de análises) — eles rodam
    fora da janela de horário de propósito (o radar é 8h45, pré-abertura),
    mas não faz sentido nenhum rodarem em sábado ou feriado."""
    d = d or datetime.now(BRT).date()
    return d.weekday() < 5 and not is_holiday(d)


def _dentro(agora: datetime, ini, fim) -> bool:
    hm = (agora.hour, agora.minute)
    return ini <= hm < fim


def after_market_ligado() -> bool:
    return (os.environ.get("B3_AFTER_MARKET") or "").strip() in ("1", "true", "TRUE", "yes")


def in_market_hours(now: datetime = None) -> bool:
    """A bolsa está negociando AGORA? Fonte única — `agent.in_market_hours`
    delega para cá, e com ele intraday/timing/timing_watch inteiros.

    Fora: pré-abertura (09:45–10:00), call de fechamento (16:55–17:00), a zona
    morta até 17:30 e o after-market (salvo `B3_AFTER_MARKET=1`).
    """
    agora = now or datetime.now(BRT)
    if not is_trading_day(agora.date()):
        return False
    if _dentro(agora, ABERTURA, FECHAMENTO):
        return True
    return after_market_ligado() and _dentro(agora, AFTER_INICIO, AFTER_FIM)
