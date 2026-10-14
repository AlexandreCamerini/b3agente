"""Relógio injetado para os testes do ciclo (quick 261013-vai, 2026-10-13).

O ciclo do agente não executa nada fora do pregão (`agent._run_cycle_inner`
→ `agent.in_market_hours()` → `pregao.in_market_hours()`). Teste que exercita
EXECUÇÃO precisa, portanto, de um relógio de pregão aberto determinístico —
senão o resultado depende da hora em que a suíte roda.

NUNCA usar `B3_DEV_MERCADO_ABERTO` como muleta: a flag é do ambiente de
staging e só é testada como flag (A2 de test_execucao_fora_pregao.py).

`injetar_relogio` troca SÓ `app.pregao.in_market_hours`: quem chama sem `now`
(o wrapper de agent, as rotas de main) recebe o instante injetado, com o
calendário, o after-market e a dev flag REAIS; quem passa `now` explícito segue
a função original (os testes de calendário continuam válidos).
`injetar_data` fixa também `agent._agora_brt` (data/hora do Diário e do
vencimento) — separado de propósito: testes antigos usam datas relativas ao
relógio real e não podem ter a data movida pelo fixture de pregão aberto.
"""
from datetime import datetime

from app import agent, pregao

QUARTA_ABERTA = datetime(2026, 10, 14, 14, 0, tzinfo=pregao.BRT)
SABADO_FECHADO = datetime(2026, 10, 17, 14, 0, tzinfo=pregao.BRT)


def injetar_relogio(monkeypatch, instante: datetime) -> None:
    original = pregao.in_market_hours

    def _in_market_hours(now=None):
        return original(now if now is not None else instante)

    monkeypatch.setattr(pregao, "in_market_hours", _in_market_hours)


def injetar_data(monkeypatch, instante: datetime) -> None:
    """Fixa data/hora BRT lidas por `agent._today/_now_str` e pelo vencimento."""
    monkeypatch.setattr(agent, "_agora_brt", lambda: instante)


def fixar_instante(monkeypatch, instante: datetime) -> None:
    injetar_relogio(monkeypatch, instante)
    injetar_data(monkeypatch, instante)


def abrir_pregao(monkeypatch) -> None:
    """Quarta 2026-10-14 14:00 BRT (dia útil, dentro do pregão)."""
    injetar_relogio(monkeypatch, QUARTA_ABERTA)


def fechar_pregao(monkeypatch) -> None:
    """Sábado 2026-10-17 14:00 BRT."""
    injetar_relogio(monkeypatch, SABADO_FECHADO)
