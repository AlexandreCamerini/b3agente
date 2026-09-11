"""Guardião (260911-dcq, achado D-2 parte 1): os três carimbos de "quando isto
foi apurado" que a interface EXIBE — `scanner.timestamp` (o mais visível: a
tela mostra ao lado de "N/M ativos varridos", `App.jsx:6980`),
`scan_deep.timestamp` e `technical_snapshot.generatedAt` — usavam
`time.strftime("%Y-%m-%dT%H:%M:%S")` sem fuso. Em produção (Railway, container
em UTC) o carimbo saía 3h à frente do horário real de Brasília; na janela das
21:00 às 23:59 BRT saía com o DIA seguinte, porque UTC já tinha virado a meia-
noite.

`scan_deep._day()` já tinha ganhado BRT em 260911-15a (achado A-10) — mas o
`timestamp` da linha 155 do MESMO arquivo ficou de fora, prova de que a
correção anterior foi por sintoma (a chave do cache), não por classe (todo
carimbo naive do módulo). Este teste crava o relógio num instante em que UTC e
BRT caem em DIAS diferentes — 01:30 UTC = 22:30 BRT do dia anterior — porque é
o DIA que prova a correção; um teste que só confere a hora passaria com o
código defeituoso. Mesmo padrão de `test_store_now_str_brt.py` e
`test_fuso_candle_provider_scan_deep_brt.py`.

Se alguém reverter para o relógio local/naive, estes testes falham mostrando
"2026-09-10T01:30:00" (o defeito real, dia UTC) em vez de
"2026-09-09T22:30:00" (esperado, dia e hora de Brasília).

Decisão de formato (justificada no comentário de cada módulo corrigido):
manter `%Y-%m-%dT%H:%M:%S` sem sufixo de fuso. A tela (`App.jsx:6980`) imprime
`res.timestamp` como string crua — acrescentar `-03:00` mudaria o que o
usuário lê e exigiria tocar o front, fora do escopo desta correção (só a
FONTE do relógio muda, não a string).
"""
from datetime import datetime, timezone

from app import scan_deep, scanner, technical_snapshot


class _RelogioViradoEmUtc(datetime):
    """Substitui `datetime` nos módulos sob teste. Herda de `datetime` (não
    um objeto solto) para que `strftime`/`astimezone` funcionem sem
    reimplementação.

    01:30 UTC do dia 10 é 22:30 BRT do dia 9 — o instante que de fato separa
    os dois dias. Com o relógio naive (UTC, o defeito) o carimbo sai
    "2026-09-10T01:30:00"; com BRT (a correção) sai "2026-09-09T22:30:00".
    """

    @classmethod
    def now(cls, tz=None):
        instante = datetime(2026, 9, 10, 1, 30, tzinfo=timezone.utc)
        return instante.astimezone(tz) if tz is not None else instante.replace(tzinfo=None)


def test_scanner_now_iso_e_hora_e_dia_de_brasilia(monkeypatch):
    monkeypatch.setattr(scanner, "datetime", _RelogioViradoEmUtc)
    assert scanner._now_iso() == "2026-09-09T22:30:00", (
        "22:30 BRT do dia 9 é 01:30 UTC do dia 10 — o carimbo não pode "
        "adiantar nem o dia nem a hora")


def test_scan_deep_now_iso_e_hora_e_dia_de_brasilia(monkeypatch):
    monkeypatch.setattr(scan_deep, "datetime", _RelogioViradoEmUtc)
    assert scan_deep._now_iso() == "2026-09-09T22:30:00"


def test_technical_snapshot_now_iso_e_hora_e_dia_de_brasilia(monkeypatch):
    monkeypatch.setattr(technical_snapshot, "datetime", _RelogioViradoEmUtc)
    assert technical_snapshot._now_iso() == "2026-09-09T22:30:00"


def test_scan_deep_day_e_timestamp_concordam_no_mesmo_instante(monkeypatch):
    """Guardião de CLASSE (não sintoma): o defeito original era `_day()`
    corrigido e `timestamp` esquecido no MESMO arquivo — os dois têm de
    concordar no dia para o mesmo instante, ou a correção voltou a ser
    parcial."""
    monkeypatch.setattr(scan_deep, "datetime", _RelogioViradoEmUtc)
    assert scan_deep._now_iso().startswith(scan_deep._day())


def test_formato_das_strings_nao_mudou(monkeypatch):
    """O front exibe `res.timestamp` como string crua (`App.jsx:6980`) —
    mudar o formato (ex.: acrescentar sufixo de fuso) mudaria o que o
    usuário lê sem tocar o front. Decisão registrada: manter o formato."""
    import re

    monkeypatch.setattr(scanner, "datetime", _RelogioViradoEmUtc)
    monkeypatch.setattr(scan_deep, "datetime", _RelogioViradoEmUtc)
    monkeypatch.setattr(technical_snapshot, "datetime", _RelogioViradoEmUtc)

    padrao = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$"
    assert re.match(padrao, scanner._now_iso())
    assert re.match(padrao, scan_deep._now_iso())
    assert re.match(padrao, technical_snapshot._now_iso())
