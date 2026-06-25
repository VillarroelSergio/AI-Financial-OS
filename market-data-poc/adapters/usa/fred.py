"""FRED (Federal Reserve Economic Data) adapter — unemployment rate and fed funds rate."""
import csv
import io
import time
import requests
from datetime import datetime, timezone

from adapters.base import BaseAdapter
from models.base import AdapterResult, ProviderMetadata
from models.macro import MacroIndicator

_HEADERS = {"User-Agent": "MarketDataPOC/0.1 contact@example.com"}

_UNRATE_URL = (
    "https://fred.stlouisfed.org/graph/fredgraph.csv"
    "?id=UNRATE&vintage_date=2024-01-01"
)
_FEDFUNDS_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=FEDFUNDS"


def _metadata() -> ProviderMetadata:
    return ProviderMetadata(
        name="FRED",
        id="fred",
        category="macro",
        region="USA",
        method="api",
        base_url="https://fred.stlouisfed.org",
        requires_api_key=False,
        declared_update_frequency="monthly",
        declared_historical_depth_years=70,
        license="Public Domain (St. Louis Fed)",
        notes="FRED public CSV endpoint — no API key required",
    )


def _parse_fred_csv(text: str, indicator_id: str, name: str, source_url: str, n: int = 3) -> list[MacroIndicator]:
    """Parse FRED CSV and return last n non-null rows.

    Supports both single-series exports (DATE,VALUE) and multi-series exports
    (DATE,UNRATE,FEDFUNDS,...).
    """
    retrieved_at = datetime.now(timezone.utc)
    reader = csv.DictReader(io.StringIO(text))
    records: list[MacroIndicator] = []
    fieldnames = [field for field in (reader.fieldnames or []) if field and field.upper() != "DATE"]
    value_columns = ["VALUE"] if "VALUE" in fieldnames else fieldnames
    for row in reader:
        date_str = row.get("DATE", "")
        for column in value_columns:
            val_str = row.get(column, "")
            if not val_str or val_str.strip() == ".":
                continue
            try:
                value = float(val_str)
            except ValueError:
                continue
            series_id = indicator_id if column == "VALUE" else column
            records.append(
                MacroIndicator(
                    provider="FRED",
                    source=source_url,
                    retrieved_at=retrieved_at,
                    country="US",
                    region="USA",
                    confidence_score=1.0,
                    indicator_id=series_id,
                    name=name if column == "VALUE" else f"FRED {column}",
                    value=value,
                    unit="%",
                    period=date_str,
                    frequency="monthly",
                )
            )
    return records[-n:]


class FREDAdapter(BaseAdapter):
    name = "FRED"
    category = "macro"
    region = "USA"
    requires_api_key = False

    def fetch(self) -> AdapterResult:
        metadata = _metadata()
        t0 = time.time()
        retrieved_at = datetime.now(timezone.utc)
        records: list[MacroIndicator] = []
        raw_sample: dict | None = None
        errors: list[str] = []

        # Unemployment Rate
        try:
            r = requests.get(_UNRATE_URL, headers=_HEADERS, timeout=10)
            r.raise_for_status()
            raw_sample = {"unrate_preview": r.text[:500]}
            records.extend(_parse_fred_csv(r.text, "US_UNRATE", "US Unemployment Rate", _UNRATE_URL))
        except Exception as exc:
            errors.append(f"UNRATE: {exc}")

        # Federal Funds Rate
        try:
            r2 = requests.get(_FEDFUNDS_URL, headers=_HEADERS, timeout=10)
            r2.raise_for_status()
            if raw_sample is None:
                raw_sample = {"fedfunds_preview": r2.text[:500]}
            records.extend(_parse_fred_csv(r2.text, "US_FEDFUNDS", "US Federal Funds Rate", _FEDFUNDS_URL))
        except Exception as exc:
            errors.append(f"FEDFUNDS: {exc}")

        latency_ms = (time.time() - t0) * 1000
        success = bool(records)
        error = "; ".join(errors) if errors and not records else ("; ".join(errors) if errors else None)
        return AdapterResult(
            provider=self.name,
            success=success,
            records=records,
            error=error,
            latency_ms=latency_ms,
            raw_sample=raw_sample,
            metadata=metadata,
        )
