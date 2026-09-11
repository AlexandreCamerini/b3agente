"""Guardião (260911-15a, achado A-10): os dois módulos que ficaram FORA da
correção de fuso de 260909-oyu.

Produção roda no Railway com o container em UTC. `candle_provider._hoje()`
usava `time.localtime()` e `scan_deep._day()` usava `time.strftime` sem
timezone — os dois, em produção, eram o dia UTC. Na janela das 21:00 às 23:59
BRT o dia já virou em UTC e não em Brasília, então:

- `candle_provider`: a requisição das 21:30 de segunda entrava no balde de
  TERÇA do anel de observabilidade. Esse anel é o gatilho declarado de troca de
  fonte (taxa de falha numa janela de 3 pregões, ADR-008/ADR-001) — a janela
  media pregões que não eram os pregões.
- `scan_deep`: o fallback de chave do cache pulava para o dia seguinte e a
  mesma varredura era reaprofundada, uma chamada de LLM por ativo do top-N.

Este teste crava o relógio num instante DENTRO dessa janela — UTC e BRT em
DIAS diferentes — porque é o dia que prova a correção; um teste que só confere
a hora passaria com o código defeituoso. Mesmo padrão de
`test_store_now_str_brt.py`.

Se alguém reverter para o relógio local, estes testes falham mostrando
"2026-09-10" (o defeito real) em vez de "2026-09-09" (esperado).
"""
from datetime import datetime, timezone

from app import candle_provider, scan_deep


class _RelogioFixo(datetime):
    """Substitui `datetime` nos módulos sob teste. Herda de `datetime` para que
    `strftime`/`astimezone` funcionem sem reimplementação.

    O ramo `tz is None` devolve o instante NAIVE em UTC — exatamente o que o
    relógio local devolve hoje no container do Railway, e o que reproduz o
    defeito se o código for revertido."""

    @classmethod
    def now(cls, tz=None):
        # 09/09/2026 23:30 UTC == 09/09/2026 20:30 BRT.
        # Em UTC o dia JÁ é 09; o defeito aparece no outro sentido (abaixo,
        # `_RelogioViradoEmUtc`), mas este instante também trava a hora.
        instante = datetime(2026, 9, 9, 23, 30, tzinfo=timezone.utc)
        return instante.astimezone(tz) if tz is not None else instante.replace(tzinfo=None)


class _RelogioViradoEmUtc(datetime):
    """O instante que de fato separa os dois dias: 01:30 UTC do dia 10 é
    22:30 BRT do dia 9. Com o relógio local (UTC) a chave sai "2026-09-10";
    com BRT sai "2026-09-09". É este caso que o defeito errava."""

    @classmethod
    def now(cls, tz=None):
        instante = datetime(2026, 9, 10, 1, 30, tzinfo=timezone.utc)
        return instante.astimezone(tz) if tz is not None else instante.replace(tzinfo=None)


def test_candle_provider_hoje_usa_o_dia_de_brasilia(monkeypatch):
    monkeypatch.setattr(candle_provider, "datetime", _RelogioViradoEmUtc)
    assert candle_provider._hoje() == "2026-09-09", (
        "22:30 BRT do dia 9 é 01:30 UTC do dia 10 — o balde do anel é do dia 9")


def test_candle_provider_hoje_na_borda_das_21h(monkeypatch):
    monkeypatch.setattr(candle_provider, "datetime", _RelogioFixo)
    assert candle_provider._hoje() == "2026-09-09"


def test_scan_deep_day_usa_o_dia_de_brasilia(monkeypatch):
    monkeypatch.setattr(scan_deep, "datetime", _RelogioViradoEmUtc)
    assert scan_deep._day() == "2026-09-09", (
        "22:30 BRT do dia 9 — a chave do cache não pode pular para o dia 10")


def test_scan_deep_day_na_borda_das_21h(monkeypatch):
    monkeypatch.setattr(scan_deep, "datetime", _RelogioFixo)
    assert scan_deep._day() == "2026-09-09"


def test_registra_joga_no_balde_do_dia_brt(monkeypatch):
    """Guardião de EFEITO, não só da função: o anel de observabilidade é
    indexado por `_hoje()` em dois lugares (`_uso` e `_uso_prov`). Prova que a
    requisição das 22:30 BRT do dia 9 cai no balde do dia 9 nos DOIS."""
    candle_provider._uso.clear()
    candle_provider._uso_prov.clear()
    monkeypatch.setattr(candle_provider, "datetime", _RelogioViradoEmUtc)

    candle_provider._registra("1d", 12.0, 21, erro=False, provedor="brapi")

    assert list(candle_provider._uso.keys()) == ["2026-09-09"]
    assert list(candle_provider._uso_prov.keys()) == ["2026-09-09"]
    assert candle_provider._uso["2026-09-09"]["1d"]["req"] == 1
    assert candle_provider._uso_prov["2026-09-09"]["brapi"]["req"] == 1

    candle_provider._uso.clear()
    candle_provider._uso_prov.clear()


def test_chave_do_cache_do_deep_cai_no_dia_brt(monkeypatch):
    """Guardião de EFEITO do `scan_deep`: o `_day()` só entra na chave como
    FALLBACK de item sem `snapshotId` — é esse caminho que precisa do dia
    certo (item com snapshotId não depende do relógio)."""
    monkeypatch.setattr(scan_deep, "datetime", _RelogioViradoEmUtc)

    chave = scan_deep._key({"ticker": "PETR4"}, "1y", modo="estudo", leitor="abc")
    assert chave[2] == "2026-09-09"

    # com snapshotId o relógio é irrelevante — contrato preservado
    chave_stu = scan_deep._key({"ticker": "PETR4", "snapshotId": "stu-123"}, "1y")
    assert chave_stu[2] == "stu-123"


def test_formato_da_chave_nao_mudou():
    """As duas chaves são string `AAAA-MM-DD` e indexam dicionários em memória
    (`_uso`, `_DEEP_CACHE`) — mudar o formato quebraria `/api/obs/usage` e
    invalidaria todo cache vivo sem nenhum ganho."""
    import re

    assert re.match(r"^\d{4}-\d{2}-\d{2}$", candle_provider._hoje())
    assert re.match(r"^\d{4}-\d{2}-\d{2}$", scan_deep._day())
