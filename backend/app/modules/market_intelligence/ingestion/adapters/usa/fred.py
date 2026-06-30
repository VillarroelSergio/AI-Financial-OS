"""FRED adapter - macro indicators plus Treasury yield fallback series."""
import csv
import io
import logging
import time
from datetime import datetime, timezone

import requests

from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.models import YieldCurvePoint
from app.modules.market_intelligence.ingestion.models import AdapterResult, ProviderMetadata
from app.modules.market_intelligence.ingestion.models import MacroIndicator

logger = logging.getLogger("market_intelligence.adapters.fred")

_HEADERS = {"User-Agent": "MarketDataPOC/0.1 contact@example.com"}
_UNRATE_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=UNRATE"
_FEDFUNDS_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=FEDFUNDS"
_YIELD_SERIES = {
    "DGS1MO": "1M",
    "DGS3MO": "3M",
    "DGS6MO": "6M",
    "DGS1": "1Y",
    "DGS2": "2Y",
    "DGS5": "5Y",
    "DGS10": "10Y",
    "DGS30": "30Y",
}

# Mapping: catalog_item_id → which FRED series to fetch
# Indicators not listed here are served by other primary providers; FRED is fallback
_INDICATOR_SERIES: dict[str, list[str]] = {
    "unemployment_usa": ["UNRATE"],
    "cpi_usa": [],           # primary: BLS; FRED fallback serves generic CPI not modelled here
    "core_cpi_usa": [],      # primary: BLS
    "gdp_usa": [],           # primary: BEA
    "nfp_usa": [],           # primary: BLS
    "retail_sales_usa": [],  # primary: Census
    "housing_starts_usa": [],  # primary: Census
    "fed_funds_rate": ["FEDFUNDS"],
    "industrial_production_usa": ["INDPRO"],  # FRED INDPRO series
    "consumer_sentiment_usa": ["UMCSENT"],    # U of Michigan via FRED
    "m2_usa": ["M2SL"],                       # M2 Money Supply
}

# URLs for the extra series (not available via the simple fredgraph.csv endpoint in all cases)
_SERIES_URLS: dict[str, str] = {
    "UNRATE": _UNRATE_URL,
    "FEDFUNDS": _FEDFUNDS_URL,
    "INDPRO": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=INDPRO",
    "UMCSENT": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=UMCSENT",
    "M2SL": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=M2SL",
}

# Yield series are only fetched when indicator_id is None (health check) or a bond catalog item
_BOND_INDICATOR_IDS: set[str] = {
    "us_treasury_1m", "us_treasury_3m", "us_treasury_6m",
    "us_treasury_1y", "us_treasury_2y", "us_treasury_5y",
    "us_treasury_10y", "us_treasury_30y",
}


def _metadata() -> ProviderMetadata:
    return ProviderMetadata(
        name="FRED",
        id="fred",
        category="macro",
        region="USA",
        method="api",
        base_url="https://fred.stlouisfed.org",
        requires_api_key=False,
        declared_update_frequency="daily",
        declared_historical_depth_years=70,
        license="Public Domain (St. Louis Fed)",
        notes="FRED public CSV endpoint, no API key required.",
        capabilities=("macro", "bonds", "historical"),
        priority="primary",
    )


def _parse_fred_csv(text: str, indicator_id: str, name: str, source_url: str, n: int = 3) -> list[MacroIndicator]:
    reader = csv.DictReader(io.StringIO(text))
    records: list[MacroIndicator] = []
    fields = [field for field in (reader.fieldnames or []) if field and field.upper() != "DATE"]
    value_columns = ["VALUE"] if "VALUE" in fields else fields
    for row in reader:
        date_str = row.get("DATE", "")
        for column in value_columns:
            raw = row.get(column, "")
            if not raw or raw.strip() == ".":
                continue
            try:
                value = float(raw)
            except ValueError:
                continue
            series_id = indicator_id if column == "VALUE" else column
            records.append(
                MacroIndicator(
                    provider="FRED",
                    source=source_url,
                    retrieved_at=datetime.now(timezone.utc),
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


def _parse_yield_csv(text: str, series_id: str, maturity: str, source_url: str) -> list[YieldCurvePoint]:
    reader = csv.DictReader(io.StringIO(text))
    field = series_id if series_id in (reader.fieldnames or []) else "VALUE"
    last: YieldCurvePoint | None = None
    for row in reader:
        date_str = row.get("DATE", "")
        raw = row.get(field, "")
        if not raw or raw.strip() == ".":
            continue
        try:
            value = float(raw)
        except ValueError:
            continue
        last = YieldCurvePoint(
            provider="FRED",
            source=source_url,
            retrieved_at=datetime.now(timezone.utc),
            country="US",
            region="USA",
            confidence_score=0.95,
            maturity=maturity,
            yield_value=value,
            date=datetime.fromisoformat(date_str).date() if date_str else None,
            currency="USD",
        )
    return [last] if last else []


class FREDAdapter(BaseAdapter):
    name = "FRED"
    category = "macro"
    region = "USA"
    requires_api_key = False
    capabilities = ("macro", "bonds", "historical")
    priority = "primary"

    def fetch(self, indicator_id: str | None = None) -> AdapterResult:
        metadata = _metadata()
        t0 = time.perf_counter()
        records: list = []
        raw_sample: dict | None = None
        errors: list[str] = []

        if indicator_id is None:
            # Health-check / legacy path: fetch both macro series + yield curve
            macro_series = [
                (_UNRATE_URL, "US_UNRATE", "US Unemployment Rate"),
                (_FEDFUNDS_URL, "US_FEDFUNDS", "US Federal Funds Rate"),
            ]
            for url, sid, name in macro_series:
                try:
                    response = requests.get(url, headers=_HEADERS, timeout=10)
                    response.raise_for_status()
                    raw_sample = raw_sample or {"macro_preview": response.text[:500]}
                    records.extend(_parse_fred_csv(response.text, sid, name, url))
                except Exception as exc:
                    errors.append(f"{sid}: {exc}")

            for series_id, maturity in _YIELD_SERIES.items():
                url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
                try:
                    response = requests.get(url, headers=_HEADERS, timeout=10)
                    response.raise_for_status()
                    raw_sample = raw_sample or {"yield_preview": response.text[:500]}
                    records.extend(_parse_yield_csv(response.text, series_id, maturity, url))
                except Exception as exc:
                    errors.append(f"{series_id}: {exc}")

        elif indicator_id in _BOND_INDICATOR_IDS:
            # Fetch only the matching yield curve series for this catalog item
            for series_id, maturity in _YIELD_SERIES.items():
                url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
                try:
                    response = requests.get(url, headers=_HEADERS, timeout=10)
                    response.raise_for_status()
                    raw_sample = raw_sample or {"yield_preview": response.text[:500]}
                    records.extend(_parse_yield_csv(response.text, series_id, maturity, url))
                except Exception as exc:
                    errors.append(f"{series_id}: {exc}")

        else:
            # Fetch only the FRED series relevant for this indicator
            series_list = _INDICATOR_SERIES.get(indicator_id, [])
            if not series_list:
                logger.info(
                    "FRED adapter: indicator '%s' not mapped to a FRED series; skipping",
                    indicator_id,
                )
                return AdapterResult(
                    provider=self.name,
                    success=False,
                    records=[],
                    error=f"No FRED series mapped for indicator '{indicator_id}'",
                    latency_ms=(time.perf_counter() - t0) * 1000,
                    raw_sample=None,
                    metadata=metadata,
                )

            name_map = {
                "UNRATE": "US Unemployment Rate",
                "FEDFUNDS": "US Federal Funds Rate",
                "INDPRO": "US Industrial Production Index",
                "UMCSENT": "US Consumer Sentiment (UMich)",
                "M2SL": "US M2 Money Supply",
            }

            for series_id in series_list:
                url = _SERIES_URLS.get(series_id, f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}")
                name = name_map.get(series_id, f"FRED {series_id}")
                try:
                    response = requests.get(url, headers=_HEADERS, timeout=10)
                    response.raise_for_status()
                    raw_sample = raw_sample or {"preview": response.text[:500]}
                    records.extend(_parse_fred_csv(response.text, series_id, name, url))
                except Exception as exc:
                    logger.warning("FRED fetch error for %s (%s): %s", indicator_id, series_id, exc)
                    errors.append(f"{series_id}: {exc}")

        latency_ms = (time.perf_counter() - t0) * 1000
        return AdapterResult(
            provider=self.name,
            success=bool(records),
            records=records,
            error="; ".join(errors) if errors and not records else ("; ".join(errors) if errors else None),
            latency_ms=latency_ms,
            raw_sample=raw_sample,
            metadata=metadata,
        )


Adapter = FREDAdapter
