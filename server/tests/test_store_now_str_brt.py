"""Guardião (260909-oyu): produção roda no Railway com o container em UTC.
Antes desta correção, `store.now_str()`/`main.now_str()`/`obslog.log()` usavam
`datetime.now()` NAIVE — o carimbo do histórico de compra/venda saía 3h à
frente do horário real de Brasília e, na janela das 21:00 às 23:59 BRT, saía
com o DIA seguinte (porque UTC já tinha virado a meia-noite). Este teste
crava o relógio num instante dentro dessa janela — UTC e BRT em dias
diferentes — para provar HORA e DIA ao mesmo tempo, não só a hora.

Se alguém reverter para `datetime.now()` naive, este teste falha mostrando
"09/09/2026 23:30" (o defeito real) em vez de "09/09/2026 20:30" (esperado).
"""
import re
from datetime import datetime, timezone

from app import obslog, store


class _RelogioFixo(datetime):
    """Substitui `datetime` nos módulos sob teste. Herda de `datetime` (não
    um objeto solto) para que `strftime`/`astimezone` funcionem sem
    reimplementação.

    O ramo `tz is None` devolve o instante NAIVE em UTC — exatamente o que
    `datetime.now()` devolveria hoje no container do Railway. É esse ramo
    que reproduz o defeito se o código for revertido.
    """

    @classmethod
    def now(cls, tz=None):
        instante = datetime(2026, 9, 9, 23, 30, tzinfo=timezone.utc)
        return instante.astimezone(tz) if tz is not None else instante.replace(tzinfo=None)


def test_store_now_str_e_hora_e_dia_de_brasilia(monkeypatch):
    monkeypatch.setattr(store, "datetime", _RelogioFixo)
    assert store.now_str() == "09/09/2026 20:30"


def test_main_now_str_delega_para_store_e_nao_reimplementa_a_regra(monkeypatch):
    """Guardião da DELEGAÇÃO: se alguém reintroduzir uma cópia do strftime em
    main.py (em vez de `return store.now_str()`), o patch em `store` deixa de
    alcançar `main.now_str()` e este teste quebra."""
    from app import main

    monkeypatch.setattr(store, "datetime", _RelogioFixo)
    assert main.now_str() == "09/09/2026 20:30"


def test_obslog_ts_e_hora_e_dia_de_brasilia(monkeypatch):
    monkeypatch.setattr(obslog, "datetime", _RelogioFixo)
    obslog.log("teste_brt", "carimbo")
    entradas = obslog.recent(5, cat="teste_brt")
    assert entradas
    assert entradas[0]["ts"].startswith("09/09 20:30")


def test_formatos_de_string_nao_mudaram(monkeypatch):
    """O front exibe `history[].date` e `obslog.ts` como string opaca — mudar
    o formato quebraria a leitura sem nenhum ganho."""
    monkeypatch.setattr(store, "datetime", _RelogioFixo)
    monkeypatch.setattr(obslog, "datetime", _RelogioFixo)
    obslog.log("teste_fmt", "carimbo")
    ts = obslog.recent(5, cat="teste_fmt")[0]["ts"]

    assert re.match(r"^\d{2}/\d{2}/\d{4} \d{2}:\d{2}$", store.now_str())
    assert re.match(r"^\d{2}/\d{2} \d{2}:\d{2}:\d{2}$", ts)
