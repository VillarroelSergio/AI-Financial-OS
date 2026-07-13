"""Repository DuckDB para el Market Intelligence Layer."""
from __future__ import annotations

import hashlib
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.modules.market_intelligence.catalog.loader import CatalogLoader
from app.modules.market_intelligence.ingestion.models import (
    BondYield,
    Commodity,
    CurrencyRate,
    HistoricalPrice,
    MacroIndicator,
    MarketQuote,
    NewsItem,
)
from app.modules.market_intelligence.ingestion.orchestrator import CatalogFetchResult
from app.modules.market_intelligence.quality.schemas import QualityResult
from app.modules.market_intelligence.storage.db import get_conn

logger = logging.getLogger("market_intelligence.repository")

_catalog = CatalogLoader()

# Tipos de registro admisibles por categoría de catálogo. Evita que un fallback
# genérico (p. ej. FRED devolviendo Fed Funds) persista macro bajo un bono o commodity.
_ALLOWED_MODELS_BY_CATEGORY: dict[str, set[str]] = {
    "macro": {"MacroIndicator"},
    "bonds": {"BondYield", "YieldCurvePoint"},
    "commodities": {"Commodity", "MarketQuote", "HistoricalPrice"},
    "indices": {"MarketQuote", "HistoricalPrice"},
    "crypto": {"MarketQuote", "HistoricalPrice"},
    "forex": {"CurrencyRate"},
    "news": {"NewsItem"},
}


_Q_RE = re.compile(r"^(\d{4})-Q([1-4])$", re.IGNORECASE)
_YM_RE = re.compile(r"^\d{4}-\d{2}$")
_Y_RE = re.compile(r"^\d{4}$")
_YM_EUROSTAT_RE = re.compile(r"^(\d{4})M(\d{2})$")
_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")


def normalize_period(period: str | None, frequency: str | None = None) -> str:
    """Canoniza `period` a YYYY-MM / YYYY-Qn / YYYY (o YYYY-MM-DD si es diario).

    ECO-3: validación en ESCRITURA. Antes cada adapter escribía su formato (FRED fechas
    sueltas, Eurostat 'YYYY-Qn', BCE 'YYYY-MM') y la lectura parcheaba con regex defensivos.
    Con la canonización aquí, la lectura confía en el formato. Forma desconocida → se
    devuelve intacta (no destruir dato)."""
    if not period:
        return ""
    p = str(period).strip()
    freq = (frequency or "").lower()
    if _Y_RE.match(p) or _YM_RE.match(p):
        return p
    m = _Q_RE.match(p)
    if m:
        return f"{m.group(1)}-Q{m.group(2)}"
    m = _YM_EUROSTAT_RE.match(p)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    m = _DATE_RE.match(p)
    if m:
        year, month, day = m.group(1), int(m.group(2)), int(m.group(3))
        if freq in ("annual", "yearly", "year"):
            return year
        if freq == "quarterly":
            return f"{year}-Q{(month - 1) // 3 + 1}"
        if freq == "daily":
            return f"{year}-{month:02d}-{day:02d}"
        return f"{year}-{month:02d}"
    return p


def _expected_maturity(catalog_item_id: str) -> str | None:
    """us_2y → '2Y', spain_10y → '10Y'. None si el id no codifica maturity."""
    match = re.search(r"_(\d+)y$", catalog_item_id)
    return f"{match.group(1)}Y" if match else None


def _record_matches_catalog(catalog_item_id: str, record) -> bool:
    item = _catalog.get_by_id(catalog_item_id)
    if item is None or not item.category:
        return True  # item desconocido: no bloquear
    allowed = _ALLOWED_MODELS_BY_CATEGORY.get(item.category)
    if allowed is None:
        return True
    if type(record).__name__ not in allowed:
        return False
    # Los adapters de bonos devuelven la curva completa: solo la maturity del item
    if item.category == "bonds":
        expected = _expected_maturity(catalog_item_id)
        maturity = getattr(record, "maturity", None)
        if expected and maturity and maturity.upper() != expected:
            return False
    return True


def _conn():
    return get_conn()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uid() -> str:
    return str(uuid.uuid4())


def _checksum(payload: str) -> str:
    return hashlib.md5(payload.encode()).hexdigest()


# ── Persist fetch result ──────────────────────────────────────────────────────

def persist_fetch_result(
    result: CatalogFetchResult,
    quality: QualityResult,
    run_id: str,
) -> None:
    """Persiste raw record + normalized record + log de salud."""
    conn = _conn()
    now = _now()
    catalog_item_id = result.catalog_id
    provider_id = result.provider_used

    # Raw record — idempotente por checksum
    raw_payload = json.dumps(result.adapter_result.raw_sample or {})
    checksum = _checksum(raw_payload)
    existing = conn.execute(
        "SELECT id FROM mi_raw_records WHERE catalog_item_id = ? AND checksum = ? LIMIT 1",
        [catalog_item_id, checksum],
    ).fetchone()
    if existing is None:
        conn.execute(
            """
            INSERT INTO mi_raw_records (id, catalog_item_id, provider_id, raw_payload_json,
                source_url, retrieved_at, ingestion_run_id, checksum)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [_uid(), catalog_item_id, provider_id, raw_payload,
             result.adapter_result.metadata.base_url, now, run_id, checksum],
        )

    # Normalized records por tipo de modelo
    for record in result.adapter_result.records:
        if not _record_matches_catalog(catalog_item_id, record):
            logger.debug(
                "Descartado %s para '%s': tipo incompatible con la categoría del catálogo",
                type(record).__name__, catalog_item_id,
            )
            continue
        _persist_normalized(conn, catalog_item_id, provider_id, record, quality, now)

    # Health log
    log_provider_health(
        provider_id=provider_id,
        catalog_item_id=catalog_item_id,
        status="success",
        latency_ms=int(result.adapter_result.latency_ms),
    )


def _persist_normalized(conn, catalog_item_id, provider_id, record, quality, now):
    model_type = type(record).__name__
    observed_at = getattr(record, "retrieved_at", now)

    # Idempotency: skip if same record already exists
    existing = conn.execute(
        "SELECT id FROM mi_normalized_records WHERE catalog_item_id = ? AND provider_id = ? AND model_type = ? AND observed_at = ? LIMIT 1",
        [catalog_item_id, provider_id, model_type, observed_at],
    ).fetchone()
    if existing:
        return

    def _first_not_none(*vals):
        for v in vals:
            if v is not None:
                return v
        return None

    value_numeric = _first_not_none(
        getattr(record, "value", None),
        getattr(record, "rate", None),
        getattr(record, "price", None),
        getattr(record, "yield_value", None),
    )
    conn.execute(
        """
        INSERT INTO mi_normalized_records
            (id, catalog_item_id, provider_id, model_type, observed_at, value_numeric,
             unit, period, frequency, source_url, retrieved_at, confidence_score, quality_score, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            _uid(), catalog_item_id, provider_id, model_type,
            observed_at,
            value_numeric,
            getattr(record, "unit", ""),
            normalize_period(getattr(record, "period", ""), getattr(record, "frequency", "")),
            getattr(record, "frequency", ""),
            getattr(record, "source", ""),
            now,
            getattr(record, "confidence_score", 1.0),
            quality.final_score,
            now,
        ],
    )

    # Tablas especializadas
    if isinstance(record, MacroIndicator):
        _upsert_macro(conn, catalog_item_id, provider_id, record, quality)
    elif isinstance(record, CurrencyRate):
        _upsert_currency(conn, catalog_item_id, provider_id, record, quality)
    elif isinstance(record, BondYield):
        _upsert_bond(conn, catalog_item_id, provider_id, record, quality)
    elif isinstance(record, MarketQuote):
        _upsert_quote(conn, catalog_item_id, provider_id, record, quality)
    elif isinstance(record, HistoricalPrice):
        _upsert_historical(conn, catalog_item_id, provider_id, record, quality)
    elif isinstance(record, Commodity):
        _upsert_commodity(conn, catalog_item_id, provider_id, record, quality)
    elif isinstance(record, NewsItem):
        _insert_news(conn, provider_id, record)


def _upsert_macro(conn, catalog_item_id, provider_id, record: MacroIndicator, quality):
    period = normalize_period(record.period, record.frequency)  # ECO-3: canoniza en escritura
    # DuckDB does not support INSERT OR REPLACE; use DELETE + INSERT
    conn.execute(
        "DELETE FROM mi_macro_observations WHERE catalog_item_id = ? AND period = ?",
        [catalog_item_id, period],
    )
    conn.execute(
        """
        INSERT INTO mi_macro_observations
            (id, catalog_item_id, indicator_id, country, period, frequency,
             value, unit, provider_id, quality_score, source_url, retrieved_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [_uid(), catalog_item_id, record.indicator_id, record.country,
         period, record.frequency, record.value, record.unit,
         provider_id, quality.final_score, record.source, record.retrieved_at],
    )


def _upsert_currency(conn, catalog_item_id, provider_id, record: CurrencyRate, quality):
    conn.execute(
        "DELETE FROM mi_currency_rates WHERE catalog_item_id = ? AND date = ?",
        [catalog_item_id, record.date],
    )
    conn.execute(
        """
        INSERT INTO mi_currency_rates
            (id, catalog_item_id, base_currency, quote_currency, rate, date, provider_id, quality_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [_uid(), catalog_item_id, record.base_currency, record.quote_currency,
         record.rate, record.date, provider_id, quality.final_score],
    )


def _upsert_bond(conn, catalog_item_id, provider_id, record: BondYield, quality):
    conn.execute(
        "DELETE FROM mi_bond_yields WHERE catalog_item_id = ? AND date = ? AND maturity = ?",
        [catalog_item_id, record.date, record.maturity],
    )
    conn.execute(
        """
        INSERT INTO mi_bond_yields
            (id, catalog_item_id, country, maturity, yield_value, date, currency,
             issuer, instrument_type, provider_id, quality_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [_uid(), catalog_item_id, record.country, record.maturity, record.yield_value,
         record.date, record.currency, record.issuer, record.instrument_type,
         provider_id, quality.final_score],
    )


def _upsert_quote(conn, catalog_item_id, provider_id, record: MarketQuote, quality):
    conn.execute(
        "DELETE FROM mi_market_quotes WHERE catalog_item_id = ?",
        [catalog_item_id],
    )
    conn.execute(
        """
        INSERT INTO mi_market_quotes
            (id, catalog_item_id, symbol, asset_type, price, change_pct, currency,
             market_status, observed_at, provider_id, quality_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [_uid(), catalog_item_id, record.symbol, record.asset_type, record.price,
         record.change_pct, record.currency, record.market_status,
         record.retrieved_at, provider_id, quality.final_score],
    )


def _upsert_historical(conn, catalog_item_id, provider_id, record: HistoricalPrice, quality):
    conn.execute(
        "DELETE FROM mi_historical_prices WHERE catalog_item_id = ? AND symbol = ? AND date = ?",
        [catalog_item_id, record.symbol, record.date],
    )
    conn.execute(
        """INSERT INTO mi_historical_prices
            (id, catalog_item_id, symbol, date, open, high, low, close, volume, currency, provider_id, quality_score)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [_uid(), catalog_item_id, record.symbol, record.date,
         record.open, record.high, record.low, record.close, record.volume,
         getattr(record, 'currency', 'USD'), provider_id, quality.final_score],
    )


def _upsert_commodity(conn, catalog_item_id, provider_id, record: Commodity, quality):
    conn.execute(
        "DELETE FROM mi_commodities WHERE catalog_item_id = ?",
        [catalog_item_id],
    )
    conn.execute(
        """
        INSERT INTO mi_commodities
            (id, catalog_item_id, symbol, name, price, unit, currency, observed_at, provider_id, quality_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [_uid(), catalog_item_id, record.symbol, record.name, record.price,
         record.unit, record.currency, record.retrieved_at, provider_id, quality.final_score],
    )


def _insert_news(conn, provider_id, record: NewsItem):
    conn.execute(
        """
        INSERT INTO mi_news_items (id, title, published_at, source_name, url, category, related_asset, provider_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [_uid(), record.title, record.published_at, record.source_name,
         record.url, record.category, record.related_asset, provider_id],
    )


def log_provider_health(
    provider_id: str,
    catalog_item_id: str,
    status: str,
    latency_ms: int = 0,
    error_message: str | None = None,
) -> None:
    conn = _conn()
    conn.execute(
        """
        INSERT INTO mi_provider_health_logs (id, provider_id, catalog_item_id, status, latency_ms, error_message)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [_uid(), provider_id, catalog_item_id, status, latency_ms, error_message],
    )


# ── Read functions ────────────────────────────────────────────────────────────

def get_latest_macro(catalog_item_id: str) -> Optional[dict]:
    conn = _conn()
    row = conn.execute(
        """
        SELECT catalog_item_id, indicator_id, country, period, value, unit, provider_id, quality_score, retrieved_at
        FROM mi_macro_observations
        WHERE catalog_item_id = ?
        ORDER BY retrieved_at DESC
        LIMIT 1
        """,
        [catalog_item_id],
    ).fetchone()
    if row is None:
        return None
    cols = ["catalog_item_id", "indicator_id", "country", "period", "value", "unit",
            "provider_id", "quality_score", "retrieved_at"]
    return dict(zip(cols, row))


def normalize_stored_periods() -> dict[str, int]:
    """ECO-3: canoniza los `period` ya almacenados (datos escritos antes del validador).

    Devuelve nº de filas cambiadas por tabla. En `mi_macro_observations` la clave lógica
    es (catalog_item_id, period): si dos filas colapsan al mismo period canónico, se
    conserva la más reciente (retrieved_at) y se borra la otra. En `mi_normalized_records`
    el period no es clave → actualización in situ.
    """
    conn = _conn()

    # ── mi_macro_observations (con colapso de duplicados) ────────────────────
    rows = conn.execute(
        "SELECT id, catalog_item_id, period, frequency, retrieved_at FROM mi_macro_observations"
    ).fetchall()
    best: dict[tuple[str, str], tuple[str, object]] = {}  # (cat,newp) → (id, retrieved_at)
    losers: list[str] = []
    for row_id, cat, period, freq, retrieved_at in rows:
        newp = normalize_period(period, freq)
        key = (cat, newp)
        prev = best.get(key)
        if prev is None:
            best[key] = (row_id, retrieved_at)
        elif retrieved_at is not None and (prev[1] is None or retrieved_at >= prev[1]):
            losers.append(prev[0])
            best[key] = (row_id, retrieved_at)
        else:
            losers.append(row_id)
    for lid in losers:
        conn.execute("DELETE FROM mi_macro_observations WHERE id = ?", [lid])
    macro_changed = len(losers)
    for (_cat, newp), (row_id, _ret) in best.items():
        updated = conn.execute(
            "UPDATE mi_macro_observations SET period = ? WHERE id = ? AND period != ?",
            [newp, row_id, newp],
        ).rowcount
        macro_changed += updated or 0

    # ── mi_normalized_records (in situ) ──────────────────────────────────────
    norm_rows = conn.execute(
        "SELECT id, period, frequency FROM mi_normalized_records"
    ).fetchall()
    norm_changed = 0
    for row_id, period, freq in norm_rows:
        newp = normalize_period(period, freq)
        if newp != (period or ""):
            conn.execute(
                "UPDATE mi_normalized_records SET period = ? WHERE id = ?", [newp, row_id]
            )
            norm_changed += 1

    logger.info("normalize_stored_periods: macro=%d normalized=%d", macro_changed, norm_changed)
    return {"macro_observations": macro_changed, "normalized_records": norm_changed}


def purge_mismatched_macro_observations() -> int:
    """Elimina observaciones macro estampadas bajo items que no son macro.

    Limpia la contaminación histórica del fallback FRED (Fed Funds persistido
    bajo us_2y/us_5y/us_10y/us_30y/wti...). Idempotente; se ejecuta al arrancar la ingesta.
    """
    non_macro_ids = [i.id for i in _catalog.load_all() if i.category and i.category != "macro"]
    if not non_macro_ids:
        return 0
    conn = _conn()
    placeholders = ", ".join("?" for _ in non_macro_ids)
    count = conn.execute(
        f"SELECT COUNT(*) FROM mi_macro_observations WHERE catalog_item_id IN ({placeholders})",
        non_macro_ids,
    ).fetchone()[0]
    if count:
        conn.execute(
            f"DELETE FROM mi_macro_observations WHERE catalog_item_id IN ({placeholders})",
            non_macro_ids,
        )
        logger.warning("Purgadas %d observaciones macro contaminadas (items no-macro)", count)

    # Bonos: elimina filas cuya maturity no coincide con la codificada en el id
    # (los adapters de curva persistían las 8 maturities bajo cada item).
    bond_purged = 0
    for item in _catalog.get_by_category("bonds"):
        expected = _expected_maturity(item.id)
        if not expected:
            continue
        mismatched = conn.execute(
            "SELECT COUNT(*) FROM mi_bond_yields WHERE catalog_item_id = ? AND upper(maturity) != ?",
            [item.id, expected],
        ).fetchone()[0]
        if mismatched:
            conn.execute(
                "DELETE FROM mi_bond_yields WHERE catalog_item_id = ? AND upper(maturity) != ?",
                [item.id, expected],
            )
            bond_purged += mismatched
    if bond_purged:
        logger.warning("Purgadas %d filas de bonos con maturity incorrecta", bond_purged)
    return int(count) + int(bond_purged)


def get_latest_macro_all() -> list[dict]:
    conn = _conn()
    rows = conn.execute("""
        SELECT catalog_item_id, indicator_id, country, period, value, unit, provider_id, quality_score, retrieved_at
        FROM (
            SELECT catalog_item_id, indicator_id, country, period, value, unit, provider_id, quality_score, retrieved_at,
                   ROW_NUMBER() OVER (PARTITION BY catalog_item_id ORDER BY retrieved_at DESC) rn
            FROM mi_macro_observations
        ) WHERE rn = 1
    """).fetchall()
    cols = ["catalog_item_id", "indicator_id", "country", "period", "value", "unit",
            "provider_id", "quality_score", "retrieved_at"]
    return [dict(zip(cols, r)) for r in rows]


def get_macro_history(max_points: int = 13) -> dict[str, list[tuple[str, float]]]:
    """Serie (period, value) por indicador macro, ordenada por periodo ascendente.

    Devuelve como máximo `max_points` puntos por indicador (suficiente para
    sparkline de 12 meses + delta vs periodo anterior).
    """
    conn = _conn()
    rows = conn.execute("""
        SELECT catalog_item_id, period, value FROM (
            SELECT catalog_item_id, period, value,
                   ROW_NUMBER() OVER (PARTITION BY catalog_item_id, period ORDER BY retrieved_at DESC) rn
            FROM mi_macro_observations
            WHERE value IS NOT NULL AND period IS NOT NULL AND period != ''
        ) WHERE rn = 1
        ORDER BY catalog_item_id, period
    """).fetchall()
    history: dict[str, list[tuple[str, float]]] = {}
    for catalog_item_id, period, value in rows:
        history.setdefault(str(catalog_item_id), []).append((str(period), float(value)))
    return {cid: points[-max_points:] for cid, points in history.items()}


def get_latest_quotes() -> list[dict]:
    conn = _conn()
    rows = conn.execute("""
        SELECT catalog_item_id, symbol, asset_type, price, change_pct, currency, observed_at, provider_id, quality_score
        FROM (
            SELECT catalog_item_id, symbol, asset_type, price, change_pct, currency, observed_at, provider_id, quality_score,
                   ROW_NUMBER() OVER (PARTITION BY catalog_item_id ORDER BY observed_at DESC) rn
            FROM mi_market_quotes
        ) WHERE rn = 1
    """).fetchall()
    cols = ["catalog_item_id", "symbol", "asset_type", "price", "change_pct",
            "currency", "observed_at", "provider_id", "quality_score"]
    return [dict(zip(cols, r)) for r in rows]


def get_latest_forex() -> list[dict]:
    conn = _conn()
    rows = conn.execute("""
        SELECT catalog_item_id, base_currency, quote_currency, rate, date, provider_id, quality_score
        FROM (
            SELECT catalog_item_id, base_currency, quote_currency, rate, date, provider_id, quality_score,
                   ROW_NUMBER() OVER (PARTITION BY catalog_item_id ORDER BY date DESC) rn
            FROM mi_currency_rates
        ) WHERE rn = 1
    """).fetchall()
    cols = ["catalog_item_id", "base_currency", "quote_currency", "rate", "date",
            "provider_id", "quality_score"]
    return [dict(zip(cols, r)) for r in rows]


def get_latest_bonds() -> list[dict]:
    conn = _conn()
    rows = conn.execute("""
        SELECT catalog_item_id, country, maturity, yield_value, date, provider_id, quality_score
        FROM (
            SELECT catalog_item_id, country, maturity, yield_value, date, provider_id, quality_score,
                   ROW_NUMBER() OVER (PARTITION BY catalog_item_id ORDER BY date DESC) rn
            FROM mi_bond_yields
        ) WHERE rn = 1
    """).fetchall()
    cols = ["catalog_item_id", "country", "maturity", "yield_value", "date",
            "provider_id", "quality_score"]
    return [dict(zip(cols, r)) for r in rows]


def get_latest_commodities() -> list[dict]:
    conn = _conn()
    rows = conn.execute("""
        SELECT catalog_item_id, symbol, name, price, unit, currency, observed_at, provider_id, quality_score
        FROM (
            SELECT catalog_item_id, symbol, name, price, unit, currency, observed_at, provider_id, quality_score,
                   ROW_NUMBER() OVER (PARTITION BY catalog_item_id ORDER BY observed_at DESC) rn
            FROM mi_commodities
        ) WHERE rn = 1
    """).fetchall()
    cols = ["catalog_item_id", "symbol", "name", "price", "unit", "currency",
            "observed_at", "provider_id", "quality_score"]
    return [dict(zip(cols, r)) for r in rows]


def get_price_change_1y(catalog_item_id: str) -> float | None:
    """ECO-4: variación % a ~12 meses desde el histórico diario de precios.

    Antes vivía como SQL crudo en impact.py. Requiere >=270 días de histórico para que la
    comparación sea análoga a "1 año"; si no, None (no se afirma nada con datos insuficientes).
    """
    from datetime import timedelta

    conn = _conn()
    try:
        rows = conn.execute(
            "SELECT date, close FROM mi_historical_prices "
            "WHERE catalog_item_id = ? AND close IS NOT NULL ORDER BY date",
            [catalog_item_id],
        ).fetchall()
    except Exception:
        return None
    if len(rows) < 2:
        return None
    last_date, last_close = rows[-1]
    target = last_date - timedelta(days=365)
    base = min(rows, key=lambda r: abs((r[0] - target).days))
    if (last_date - base[0]).days < 270 or not base[1]:
        return None
    return (float(last_close) - float(base[1])) / float(base[1]) * 100


def read_historical(catalog_item_id: str) -> list[dict]:
    """MKT-6: serie EOD completa de un instrumento, ascendente por fecha. Solo lectura
    (un GET nunca ingesta). `date` vuelve como objeto date (converter DATE de db.py)."""
    conn = _conn()
    rows = conn.execute(
        "SELECT date, open, high, low, close, volume, currency, provider_id, quality_score "
        "FROM mi_historical_prices WHERE catalog_item_id = ? AND close IS NOT NULL "
        "ORDER BY date",
        [catalog_item_id],
    ).fetchall()
    cols = ["date", "open", "high", "low", "close", "volume", "currency",
            "provider_id", "quality_score"]
    return [dict(zip(cols, r)) for r in rows]


def historical_counts() -> dict[str, int]:
    """MKT-6: nº de filas EOD por instrumento. Para el backfill 'solo faltantes' en arranque."""
    rows = _conn().execute(
        "SELECT catalog_item_id, COUNT(*) FROM mi_historical_prices GROUP BY catalog_item_id"
    ).fetchall()
    return {cid: n for cid, n in rows}


def read_sparklines(catalog_item_ids: list[str], points: int = 30) -> dict[str, list[float]]:
    """MKT-8: últimos N cierres por instrumento en una sola consulta (window function),
    ascendentes por fecha. Para las mini-gráficas de fila. Solo lectura."""
    if not catalog_item_ids:
        return {}
    placeholders = ",".join("?" * len(catalog_item_ids))
    rows = _conn().execute(
        f"""SELECT catalog_item_id, close FROM (
              SELECT catalog_item_id, date, close,
                ROW_NUMBER() OVER (PARTITION BY catalog_item_id ORDER BY date DESC) rn
              FROM mi_historical_prices
              WHERE catalog_item_id IN ({placeholders}) AND close IS NOT NULL
            ) WHERE rn <= ? ORDER BY catalog_item_id, date""",
        [*catalog_item_ids, points],
    ).fetchall()
    out: dict[str, list[float]] = {}
    for cid, close in rows:
        out.setdefault(cid, []).append(float(close))
    return out


def persist_historical_prices(
    catalog_item_id: str, provider_id: str,
    records: list[HistoricalPrice], quality_score: float = 1.0,
) -> int:
    """MKT-6: backfill idempotente de precios EOD (DELETE+INSERT por (item, symbol, date))."""
    conn = _conn()
    n = 0
    for rec in records:
        conn.execute(
            "DELETE FROM mi_historical_prices WHERE catalog_item_id = ? AND symbol = ? AND date = ?",
            [catalog_item_id, rec.symbol, rec.date],
        )
        conn.execute(
            """INSERT INTO mi_historical_prices
                (id, catalog_item_id, symbol, date, open, high, low, close, volume, currency, provider_id, quality_score)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [_uid(), catalog_item_id, rec.symbol, rec.date,
             rec.open, rec.high, rec.low, rec.close, rec.volume,
             getattr(rec, "currency", "USD"), provider_id, quality_score],
        )
        n += 1
    return n


_RETENTION_RE = re.compile(r"^(\d+)\s*y$", re.IGNORECASE)


def _retention_years(retention: str | None) -> int | None:
    m = _RETENTION_RE.match((retention or "").strip())
    return int(m.group(1)) if m else None


def apply_retention(now: datetime | None = None) -> dict[str, int]:
    """ECO-5: poda observaciones más antiguas que la `retention` de cada item del catálogo.

    macro/normalized se podan por el año del `period` (prefijo YYYY, canónico desde ECO-3);
    los precios históricos por `date`. Backfill queda fuera: los adapters públicos solo
    devuelven los últimos puntos, no hay de dónde reconstruir histórico.
    """
    from datetime import timedelta

    now = now or datetime.now(timezone.utc)
    conn = _conn()
    macro_deleted = 0
    price_deleted = 0
    for item in _catalog.load_all():
        years = _retention_years(item.retention)
        if not years:
            continue
        cutoff_year = now.year - years
        for table in ("mi_macro_observations", "mi_normalized_records"):
            # SQLite (ECO-3b): .rowcount es fiable en DELETE; GLOB reemplaza a regexp_matches.
            macro_deleted += conn.execute(
                f"DELETE FROM {table} WHERE catalog_item_id = ? "
                f"AND period GLOB '[0-9][0-9][0-9][0-9]*' "
                f"AND CAST(substr(period, 1, 4) AS INTEGER) < ?",
                [item.id, cutoff_year],
            ).rowcount
        cutoff_date = (now - timedelta(days=365 * years)).date()
        price_deleted += conn.execute(
            "DELETE FROM mi_historical_prices WHERE catalog_item_id = ? AND date < ?",
            [item.id, cutoff_date],
        ).rowcount
    logger.info("apply_retention: macro/normalized=%d prices=%d", macro_deleted, price_deleted)
    return {"macro_rows": macro_deleted, "price_rows": price_deleted}


def record_ingest_result(
    catalog_item_id: str, frequency: str, status: str, provider_used: str,
    fallback_used: bool, run_id: str, at: datetime,
) -> None:
    """ECO-5: registra el resultado de ingesta de un item. `last_success_at` solo avanza
    en éxito (un fallo no lo pisa, para que el scheduler no lo dé por refrescado)."""
    conn = _conn()
    prev = conn.execute(
        "SELECT last_success_at FROM mi_ingest_state WHERE catalog_item_id = ?",
        [catalog_item_id],
    ).fetchone()
    last_success = at if status == "ok" else (prev[0] if prev else None)
    conn.execute("DELETE FROM mi_ingest_state WHERE catalog_item_id = ?", [catalog_item_id])
    conn.execute(
        """
        INSERT INTO mi_ingest_state
            (catalog_item_id, frequency, last_status, provider_used, fallback_used,
             last_run_id, last_run_at, last_success_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [catalog_item_id, frequency, status, provider_used, fallback_used,
         run_id, at, last_success],
    )


def get_ingest_state() -> dict[str, dict]:
    """catalog_item_id → última ingesta (status, provider, timestamps)."""
    conn = _conn()
    rows = conn.execute(
        "SELECT catalog_item_id, frequency, last_status, provider_used, fallback_used, "
        "last_run_id, last_run_at, last_success_at FROM mi_ingest_state"
    ).fetchall()
    cols = ["catalog_item_id", "frequency", "last_status", "provider_used", "fallback_used",
            "last_run_id", "last_run_at", "last_success_at"]
    return {r[0]: dict(zip(cols, r)) for r in rows}


def get_latest_news(limit: int = 20) -> list[dict]:
    conn = _conn()
    rows = conn.execute(
        """
        SELECT id, title, published_at, source_name, url, category, related_asset, provider_id
        FROM mi_news_items
        ORDER BY published_at DESC NULLS LAST
        LIMIT ?
        """,
        [limit],
    ).fetchall()
    cols = ["id", "title", "published_at", "source_name", "url", "category", "related_asset", "provider_id"]
    return [dict(zip(cols, r)) for r in rows]


def save_ai_datasheet(scope: str, datasheet_json: str, quality_score: float) -> None:
    conn = _conn()
    conn.execute(
        """
        INSERT INTO mi_ai_datasheets (id, snapshot_date, scope, datasheet_json, quality_score)
        VALUES (?, current_date, ?, ?, ?)
        """,
        [_uid(), scope, datasheet_json, quality_score],
    )


def get_latest_ai_datasheet(scope: str = "daily") -> Optional[dict]:
    conn = _conn()
    row = conn.execute(
        """
        SELECT scope, datasheet_json, quality_score, generated_at
        FROM mi_ai_datasheets
        WHERE scope = ?
        ORDER BY generated_at DESC
        LIMIT 1
        """,
        [scope],
    ).fetchone()
    if row is None:
        return None
    return {"scope": row[0], "datasheet_json": row[1], "quality_score": row[2], "generated_at": row[3]}
