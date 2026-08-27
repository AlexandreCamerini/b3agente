"""Leitura diária do arquivo COTAHIST publicado pela B3.

A página pública da B3 aponta para uma série diária cujo arquivo tem URL
determinística e contém um TXT de posições fixas dentro de um ZIP. Este módulo
mantém a ingestão separada dos provedores de cotação: o arquivo é um acervo
histórico da própria B3, não um fallback silencioso de spot/intraday.

Contrato operacional:
  * um arquivo por dia de pregão, salvo em ``b3_daily_imports``;
  * as linhas ``01`` são normalizadas em ``b3_daily_quotes``;
  * SHA-256 + chave de data tornam a execução idempotente;
  * 404 significa "arquivo ainda não publicado / não há série para esta data",
    não um erro técnico para a UI;
  * nenhum valor é completado por inferência.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import io
import json
import os
import re
import zipfile
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Callable, Optional

import httpx

from . import db

SOURCE_PAGE_URL = (
    "https://www.b3.com.br/en_us/market-data-and-indices/data-services/"
    "market-data/historical-data/equities/historical-quotes/"
)
DOWNLOAD_BASE_URL = "https://bvmf.bmfbovespa.com.br/InstDados/SerHist/"
TIMEOUT_S = 45.0
MAX_ZIP_BYTES = 50 * 1024 * 1024
MAX_TEXT_BYTES = 100 * 1024 * 1024
MAX_ROWS = 250_000
HHMM_DEFAULT = "20:30"
RETRY_MIN_DEFAULT = 60
BRT = timezone(timedelta(hours=-3))
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

LAST_DAILY = {
    "date": None,
    "at": None,
    "status": None,
    "rows": 0,
    "error": None,
}


class B3DailyError(RuntimeError):
    """Erro de transporte ou de integridade do arquivo publicado pela B3."""


class B3DailyNotAvailable(B3DailyError):
    """A B3 ainda não publicou um arquivo para a data informada."""


def normalize_trade_date(value: Optional[object] = None) -> str:
    """Normaliza uma data para ``AAAA-MM-DD`` e rejeita datas impossíveis."""
    if value is None or value == "":
        return datetime.now(BRT).date().isoformat()
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    raw = str(value).strip()
    if not _DATE_RE.fullmatch(raw):
        raise ValueError("data deve estar no formato AAAA-MM-DD")
    try:
        return date.fromisoformat(raw).isoformat()
    except ValueError as exc:
        raise ValueError("data inválida") from exc


def archive_filename(trade_date: object) -> str:
    day = date.fromisoformat(normalize_trade_date(trade_date))
    return f"COTAHIST_D{day:%d%m%Y}.ZIP"


def archive_url(trade_date: object) -> str:
    return DOWNLOAD_BASE_URL + archive_filename(trade_date)


def _scaled_number(raw: str, scale: int) -> Optional[float]:
    value = raw.strip()
    if not value:
        return None
    try:
        return float(Decimal(value) / (Decimal(10) ** scale))
    except InvalidOperation as exc:
        raise B3DailyError(f"campo numérico inválido: {raw!r}") from exc


def _integer(raw: str) -> Optional[int]:
    value = raw.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise B3DailyError(f"campo inteiro inválido: {raw!r}") from exc


def _slice(line: str, start: int, end: int) -> str:
    """Corte 0-based, com fim exclusivo; os offsets seguem o layout COTAHIST."""
    return line[start:end]


def parse_cotahist_text(text: str, expected_date: object) -> list[dict]:
    """Valida e converte um TXT COTAHIST em registros normalizados.

    O layout oficial usa registros ``00`` (header), ``01`` (cotação) e ``99``
    (trailer), com 245 caracteres por linha sem o CRLF.
    """
    trade_date = normalize_trade_date(expected_date)
    lines = text.splitlines()
    if len(lines) < 3 or not lines[0].startswith("00") or not lines[-1].startswith("99"):
        raise B3DailyError("TXT COTAHIST sem header/trailer esperados")

    rows: list[dict] = []
    for number, line in enumerate(lines[1:-1], start=2):
        if not line.startswith("01"):
            continue
        if len(line) < 245:
            raise B3DailyError(f"registro {number} menor que 245 caracteres")
        row_date = _slice(line, 2, 10)
        try:
            parsed_date = date.fromisoformat(
                f"{row_date[:4]}-{row_date[4:6]}-{row_date[6:8]}"
            ).isoformat()
        except ValueError as exc:
            raise B3DailyError(f"data inválida no registro {number}") from exc
        if parsed_date != trade_date:
            raise B3DailyError(
                f"registro {number} pertence a {parsed_date}, esperado {trade_date}"
            )

        ticker = _slice(line, 12, 24).strip()
        if not ticker:
            raise B3DailyError(f"registro {number} sem código do ativo")
        rows.append(
            {
                "trade_date": parsed_date,
                "source_row": number,
                "bdi_code": _slice(line, 10, 12).strip(),
                "ticker": ticker,
                "market_type": _slice(line, 24, 27).strip(),
                "name": _slice(line, 27, 39).strip(),
                "specification": _slice(line, 39, 49).strip(),
                "reference_term": _slice(line, 49, 52).strip(),
                "reference_currency": _slice(line, 52, 56).strip(),
                "open": _scaled_number(_slice(line, 56, 69), 2),
                "high": _scaled_number(_slice(line, 69, 82), 2),
                "low": _scaled_number(_slice(line, 82, 95), 2),
                "average": _scaled_number(_slice(line, 95, 108), 2),
                "close": _scaled_number(_slice(line, 108, 121), 2),
                "bid": _scaled_number(_slice(line, 121, 134), 2),
                "ask": _scaled_number(_slice(line, 134, 147), 2),
                "total_trades": _integer(_slice(line, 147, 152)),
                "total_quantity": _integer(_slice(line, 152, 170)),
                "total_volume": _scaled_number(_slice(line, 170, 188), 2),
                "exercise_price": _scaled_number(_slice(line, 188, 201), 2),
                "isin": _slice(line, 230, 242).strip(),
            }
        )
        if len(rows) > MAX_ROWS:
            raise B3DailyError(f"TXT excede o limite de {MAX_ROWS:,} registros")
    if not rows:
        raise B3DailyError("TXT COTAHIST sem registros de cotação")
    return rows


def _download_zip(url: str) -> bytes:
    headers = {
        "User-Agent": "Boris+ historical-data collector/1.0",
        "Accept": "application/zip,application/octet-stream;q=0.9,*/*;q=0.1",
    }
    try:
        with httpx.Client(
            timeout=TIMEOUT_S, follow_redirects=True, headers=headers
        ) as client:
            response = client.get(url)
    except httpx.HTTPError as exc:
        raise B3DailyError(f"B3 inacessível: {exc}") from exc
    if response.status_code == 404:
        raise B3DailyNotAvailable("arquivo diário ainda não publicado pela B3")
    if response.status_code >= 400:
        raise B3DailyError(f"B3 respondeu HTTP {response.status_code}")
    payload = response.content
    if len(payload) > MAX_ZIP_BYTES:
        raise B3DailyError(f"ZIP excede o limite de {MAX_ZIP_BYTES // 1024 // 1024} MB")
    return payload


def _read_zip_text(payload: bytes) -> str:
    if len(payload) > MAX_ZIP_BYTES or not zipfile.is_zipfile(io.BytesIO(payload)):
        raise B3DailyError("resposta da B3 não é um ZIP válido")
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            members = [
                info
                for info in archive.infolist()
                if not info.is_dir() and info.filename.upper().endswith(".TXT")
            ]
            if len(members) != 1:
                raise B3DailyError("ZIP deve conter exatamente um TXT COTAHIST")
            member = members[0]
            if member.file_size > MAX_TEXT_BYTES:
                raise B3DailyError("TXT COTAHIST excede o limite de tamanho")
            raw = archive.read(member)
    except zipfile.BadZipFile as exc:
        raise B3DailyError("ZIP COTAHIST corrompido") from exc
    try:
        return raw.decode("latin-1")
    except UnicodeDecodeError as exc:
        raise B3DailyError("TXT COTAHIST não pôde ser decodificado") from exc


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _status_row(row) -> Optional[dict]:
    if row is None:
        return None
    keys = (
        "trade_date",
        "source_url",
        "status",
        "checked_at",
        "imported_at",
        "source_sha256",
        "file_name",
        "row_count",
        "error",
    )
    return dict(zip(keys, row))


def get_status(conn, trade_date: Optional[object] = None) -> Optional[dict]:
    if trade_date is not None:
        day = normalize_trade_date(trade_date)
        row = conn.execute(
            "SELECT trade_date, source_url, status, checked_at, imported_at, "
            "source_sha256, file_name, row_count, error "
            "FROM b3_daily_imports WHERE trade_date = ?",
            (day,),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT trade_date, source_url, status, checked_at, imported_at, "
            "source_sha256, file_name, row_count, error "
            "FROM b3_daily_imports ORDER BY trade_date DESC LIMIT 1"
        ).fetchone()
    return _status_row(row)


def list_quotes(
    conn,
    trade_date: Optional[object] = None,
    ticker: Optional[str] = None,
    limit: int = 100,
) -> list[dict]:
    day = normalize_trade_date(trade_date) if trade_date is not None else None
    try:
        safe_limit = max(1, min(1000, int(limit)))
    except (TypeError, ValueError):
        safe_limit = 100
    clauses, params = [], []
    if day:
        clauses.append("trade_date = ?")
        params.append(day)
    if ticker:
        clauses.append("ticker = ?")
        params.append(str(ticker).strip().upper())
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    rows = conn.execute(
        "SELECT trade_date, source_row, bdi_code, ticker, market_type, name, "
        "reference_currency, open, high, low, average, close, bid, ask, "
        "total_trades, total_quantity, total_volume, isin "
        "FROM b3_daily_quotes" + where + " ORDER BY trade_date DESC, ticker LIMIT ?",
        [*params, safe_limit],
    ).fetchall()
    fields = (
        "trade_date", "source_row", "bdi_code", "ticker", "market_type", "name",
        "reference_currency", "open", "high", "low", "average", "close",
        "bid", "ask", "total_trades", "total_quantity", "total_volume", "isin",
    )
    return [dict(zip(fields, row)) for row in rows]


def _upsert_status(conn, day: str, status: str, *, checked_at: str,
                   imported_at: Optional[str] = None,
                   source_sha256: Optional[str] = None,
                   row_count: int = 0, error: Optional[str] = None) -> None:
    conn.execute(
        "INSERT INTO b3_daily_imports "
        "(trade_date, source_url, status, checked_at, imported_at, source_sha256, "
        "file_name, row_count, error) VALUES (?,?,?,?,?,?,?,?,?) "
        "ON CONFLICT(trade_date) DO UPDATE SET source_url=excluded.source_url, "
        "status=excluded.status, checked_at=excluded.checked_at, "
        "imported_at=excluded.imported_at, source_sha256=excluded.source_sha256, "
        "file_name=excluded.file_name, row_count=excluded.row_count, error=excluded.error",
        (
            day, archive_url(day), status, checked_at, imported_at, source_sha256,
            archive_filename(day), row_count, error,
        ),
    )


def import_daily(
    conn,
    trade_date: Optional[object] = None,
    *,
    fetch_bytes: Optional[Callable[[str], bytes]] = None,
    force: bool = False,
) -> dict:
    """Baixa, valida e grava uma data; segura para repetir quantas vezes quiser."""
    day = normalize_trade_date(trade_date)
    previous = get_status(conn, day)
    if previous and previous.get("status") == "imported" and not force:
        return {**previous, "skipped": True}

    checked_at = _now_iso()
    downloader = fetch_bytes or _download_zip
    try:
        payload = downloader(archive_url(day))
        if not isinstance(payload, (bytes, bytearray)):
            raise B3DailyError("downloader não retornou bytes")
        payload = bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        rows = parse_cotahist_text(_read_zip_text(payload), day)
    except B3DailyNotAvailable as exc:
        _upsert_status(conn, day, "not_available", checked_at=checked_at, error=str(exc))
        conn.commit()
        result = get_status(conn, day) or {"trade_date": day, "status": "not_available"}
        LAST_DAILY.update(date=day, at=checked_at, status="not_available", rows=0, error=str(exc))
        return result
    except Exception as exc:  # noqa: BLE001 — status persistido para diagnóstico
        message = str(exc)[:500] or type(exc).__name__
        _upsert_status(conn, day, "failed", checked_at=checked_at, error=message)
        conn.commit()
        LAST_DAILY.update(date=day, at=checked_at, status="failed", rows=0, error=message)
        raise B3DailyError(message) from exc

    imported_at = _now_iso()
    try:
        conn.execute("DELETE FROM b3_daily_quotes WHERE trade_date = ?", (day,))
        conn.executemany(
            "INSERT INTO b3_daily_quotes "
            "(trade_date, source_row, bdi_code, ticker, market_type, name, specification, "
            "reference_term, reference_currency, open, high, low, average, close, "
            "bid, ask, total_trades, total_quantity, total_volume, exercise_price, isin) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [
                (
                    row["trade_date"], row["source_row"], row["bdi_code"], row["ticker"], row["market_type"],
                    row["name"], row["specification"], row["reference_term"],
                    row["reference_currency"], row["open"], row["high"], row["low"],
                    row["average"], row["close"], row["bid"], row["ask"],
                    row["total_trades"], row["total_quantity"], row["total_volume"],
                    row["exercise_price"], row["isin"],
                )
                for row in rows
            ],
        )
        _upsert_status(
            conn, day, "imported", checked_at=checked_at, imported_at=imported_at,
            source_sha256=digest, row_count=len(rows), error=None,
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    result = get_status(conn, day) or {"trade_date": day, "status": "imported"}
    LAST_DAILY.update(date=day, at=imported_at, status="imported", rows=len(rows), error=None)
    return result


def _hhmm() -> tuple[int, int]:
    raw = (os.environ.get("B3_COTAHIST_DAILY_HHMM") or HHMM_DEFAULT).strip()
    try:
        hour, minute = (int(part) for part in raw.split(":", 1))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return hour, minute
    except (TypeError, ValueError):
        pass
    return tuple(int(part) for part in HHMM_DEFAULT.split(":"))


def _retry_minutes() -> int:
    try:
        return max(5, int(os.environ.get("B3_COTAHIST_RETRY_MIN") or RETRY_MIN_DEFAULT))
    except (TypeError, ValueError):
        return RETRY_MIN_DEFAULT


def enabled() -> bool:
    return not os.environ.get("B3_COTAHIST_DAILY_OFF")


def should_run(conn, now: Optional[datetime] = None) -> bool:
    """Gate puro do job: só depois do fechamento, em dia de pregão e com retry."""
    from . import pregao

    now = now or datetime.now(BRT)
    if not enabled() or not pregao.is_trading_day(now.date()):
        return False
    hour, minute = _hhmm()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if now < target:
        return False
    day = now.date().isoformat()
    status = get_status(conn, day)
    if status and status.get("status") == "imported":
        return False
    if status and status.get("checked_at"):
        try:
            checked = datetime.fromisoformat(status["checked_at"])
            if checked.tzinfo is None:
                checked = checked.replace(tzinfo=timezone.utc)
            if (datetime.now(timezone.utc) - checked.astimezone(timezone.utc)).total_seconds() < _retry_minutes() * 60:
                return False
        except (TypeError, ValueError):
            pass
    return True


async def maybe_run(conn, now: Optional[datetime] = None) -> Optional[dict]:
    if not should_run(conn, now=now):
        return None
    day = (now or datetime.now(BRT)).date().isoformat()
    try:
        return await asyncio.to_thread(import_daily, conn, day)
    except Exception as exc:  # noqa: BLE001 — ingestão nunca derruba o scheduler
        LAST_DAILY.update(date=day, at=_now_iso(), status="failed", error=str(exc)[:500])
        print(f"[b3-cotahist] importação diária falhou: {exc}")
        return get_status(conn, day)


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Importa o COTAHIST diário da B3")
    parser.add_argument("--date", dest="trade_date", help="Data AAAA-MM-DD; default: hoje BRT")
    parser.add_argument("--db", dest="db_path", help="Caminho do SQLite; default: B3_DB_PATH/app")
    parser.add_argument("--status", action="store_true", help="Mostra o status sem baixar")
    parser.add_argument("--force", action="store_true", help="Rebaixa uma data já importada")
    args = parser.parse_args()
    conn = db.connect(args.db_path)
    day = normalize_trade_date(args.trade_date)
    if args.status:
        print(json.dumps(get_status(conn, day), ensure_ascii=False, indent=2))
        return 0
    try:
        result = import_daily(conn, day, force=args.force)
    except B3DailyError as exc:
        print(json.dumps({"trade_date": day, "status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
