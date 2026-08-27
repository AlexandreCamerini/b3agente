import io
import zipfile
from datetime import datetime, timezone, timedelta

import pytest

from app import b3_historical, db


BRT = timezone(timedelta(hours=-3))


def _put(line, start, value, width=None):
    value = str(value)
    if width is not None:
        value = value.rjust(width, "0")
    line[start : start + len(value)] = value.encode("ascii")


def _record(day="20260825", ticker="PETR4", close=37.26):
    line = bytearray(b" " * 245)
    _put(line, 0, "01")
    _put(line, 2, day)
    _put(line, 10, "02")
    _put(line, 12, ticker.ljust(12))
    _put(line, 24, "010")
    _put(line, 27, "PETROBRAS".ljust(12))
    _put(line, 39, "PN".ljust(10))
    _put(line, 49, "".ljust(7))
    _put(line, 56, str(round(36.0 * 100)), 13)
    _put(line, 69, str(round(38.0 * 100)), 13)
    _put(line, 82, str(round(35.0 * 100)), 13)
    _put(line, 95, str(round(37.0 * 100)), 13)
    _put(line, 108, str(round(close * 100)), 13)
    _put(line, 121, str(round(37.20 * 100)), 13)
    _put(line, 134, str(round(37.30 * 100)), 13)
    _put(line, 147, "12345", 5)
    _put(line, 152, "987654", 18)
    _put(line, 170, str(round(123456.78 * 100)), 18)
    _put(line, 188, "0", 13)
    _put(line, 230, "BRPETRACNOR9".ljust(12))
    return line.decode("ascii")


def _zip_for(day="2026-08-25", *records):
    compact = day.replace("-", "")
    text = "00COTAHIST.2026BOVESPA".ljust(245) + "\r\n"
    text += "\r\n".join(records) + "\r\n"
    text += "99".ljust(245) + "\r\n"
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(f"COTAHIST_D{compact[6:8]}{compact[4:6]}{compact[:4]}.TXT", text)
    return output.getvalue()


def test_archive_url_and_fixed_width_parser():
    assert b3_historical.archive_filename("2026-08-25") == "COTAHIST_D25082026.ZIP"
    assert b3_historical.archive_url("2026-08-25").endswith("/COTAHIST_D25082026.ZIP")

    rows = b3_historical.parse_cotahist_text(
        "00header\n" + _record() + "\n99trailer\n", "2026-08-25"
    )
    assert len(rows) == 1
    assert rows[0]["ticker"] == "PETR4"
    assert rows[0]["close"] == pytest.approx(37.26)
    assert rows[0]["total_trades"] == 12345
    assert rows[0]["total_volume"] == pytest.approx(123456.78)


def test_import_is_idempotent_and_persists_provenance(tmp_path):
    conn = db.connect(str(tmp_path / "b3.db"))
    payload = _zip_for("2026-08-25", _record())
    calls = []

    def fetch(url):
        calls.append(url)
        return payload

    first = b3_historical.import_daily(conn, "2026-08-25", fetch_bytes=fetch)
    second = b3_historical.import_daily(conn, "2026-08-25", fetch_bytes=fetch)

    assert first["status"] == "imported"
    assert first["row_count"] == 1
    assert len(first["source_sha256"]) == 64
    assert second["skipped"] is True
    assert len(calls) == 1
    assert b3_historical.list_quotes(conn, "2026-08-25", "PETR4")[0]["close"] == pytest.approx(37.26)

    forced = b3_historical.import_daily(conn, "2026-08-25", fetch_bytes=fetch, force=True)
    assert forced["status"] == "imported"
    assert len(calls) == 2


def test_import_preserves_multiple_rows_with_same_ticker_and_market(tmp_path):
    conn = db.connect(str(tmp_path / "b3.db"))
    payload = _zip_for(
        "2026-08-25",
        _record(close=37.26),
        _record(close=37.40),
    )
    result = b3_historical.import_daily(
        conn, "2026-08-25", fetch_bytes=lambda _url: payload
    )
    assert result["row_count"] == 2
    assert len(b3_historical.list_quotes(conn, "2026-08-25", "PETR4", limit=10)) == 2


def test_not_available_is_recorded_without_fabricating_quotes(tmp_path):
    conn = db.connect(str(tmp_path / "b3.db"))

    def missing(_url):
        raise b3_historical.B3DailyNotAvailable("não publicado")

    result = b3_historical.import_daily(conn, "2026-08-25", fetch_bytes=missing)
    assert result["status"] == "not_available"
    assert result["row_count"] == 0
    assert b3_historical.list_quotes(conn, "2026-08-25") == []


def test_daily_gate_waits_for_configured_time_and_stops_after_import(tmp_path, monkeypatch):
    conn = db.connect(str(tmp_path / "b3.db"))
    monkeypatch.setenv("B3_COTAHIST_DAILY_HHMM", "20:30")
    before = datetime(2026, 8, 25, 20, 29, tzinfo=BRT)
    after = datetime(2026, 8, 25, 20, 31, tzinfo=BRT)
    assert b3_historical.should_run(conn, before) is False
    assert b3_historical.should_run(conn, after) is True

    payload = _zip_for("2026-08-25", _record())
    b3_historical.import_daily(conn, "2026-08-25", fetch_bytes=lambda _url: payload)
    assert b3_historical.should_run(conn, after) is False
