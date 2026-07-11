"""FRED adapter - macro indicators plus Treasury yield fallback series."""
import csv
import io
import logging
import time
from datetime import datetime, timezone

import requests

from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.models import (
    AdapterResult,
    MacroIndicator,
    ProviderMetadata,
    YieldCurvePoint,
)

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

# Mapping: catalog_item_id → which FRED series to fetch.
# ECO-2: cpi/core_cpi/gdp/nfp/retail/housing se cubren aquí (BLS/BEA/Census no emiten
# valor). Series y unidades verificadas contra fredgraph.csv en vivo (2026-07-06).
# CPI/Core-CPI usan la transformación pc1 (variación % interanual) → unidad "%".
_INDICATOR_SERIES: dict[str, list[str]] = {
    "unemployment_usa": ["UNRATE"],
    "cpi_usa": ["CPIAUCSL_PC1"],       # YoY % (transformation=pc1)
    "core_cpi_usa": ["CPILFESL_PC1"],  # YoY % (transformation=pc1)
    "gdp_usa": ["GDP"],                # nivel, USD bn, trimestral
    "nfp_usa": ["PAYEMS"],             # nóminas no agrícolas, miles (nivel)
    "retail_sales_usa": ["RSAFS"],     # ventas minoristas, USD mn
    "housing_starts_usa": ["HOUST"],   # viviendas iniciadas, miles
    "fed_funds_rate": ["FEDFUNDS"],
    "industrial_production_usa": ["INDPRO"],  # FRED INDPRO series
    "consumer_sentiment_usa": ["UMCSENT"],    # U of Michigan via FRED
    "m2_usa": ["M2SL"],                       # M2 Money Supply
}

# Unidad real de cada serie FRED (INDPRO/UMCSENT son índices, no porcentajes)
_SERIES_UNITS: dict[str, str] = {
    "UNRATE": "%",
    "FEDFUNDS": "%",
    "INDPRO": "index",
    "UMCSENT": "index",
    "M2SL": "USD bn",
    "CPIAUCSL_PC1": "%",
    "CPILFESL_PC1": "%",
    "GDP": "USD bn",
    "PAYEMS": "thousands",
    "RSAFS": "USD mn",
    "HOUST": "thousands",
}

# Frecuencia real por serie (default mensual); GDP es trimestral.
_SERIES_FREQ: dict[str, str] = {"GDP": "quarterly"}

_FREDGRAPH = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="

# URLs for the extra series (not available via the simple fredgraph.csv endpoint in all cases)
_SERIES_URLS: dict[str, str] = {
    "UNRATE": _UNRATE_URL,
    "FEDFUNDS": _FEDFUNDS_URL,
    "INDPRO": f"{_FREDGRAPH}INDPRO",
    "UMCSENT": f"{_FREDGRAPH}UMCSENT",
    "M2SL": f"{_FREDGRAPH}M2SL",
    "CPIAUCSL_PC1": f"{_FREDGRAPH}CPIAUCSL&transformation=pc1",
    "CPILFESL_PC1": f"{_FREDGRAPH}CPILFESL&transformation=pc1",
    "GDP": f"{_FREDGRAPH}GDP",
    "PAYEMS": f"{_FREDGRAPH}PAYEMS",
    "RSAFS": f"{_FREDGRAPH}RSAFS",
    "HOUST": f"{_FREDGRAPH}HOUST",
}

# Yield series are only fetched when indicator_id is None (health check) or a bond catalog item
_BOND_INDICATOR_IDS: set[str] = {
    "us_treasury_1m", "us_treasury_3m", "us_treasury_6m",
    "us_treasury_1y", "us_treasury_2y", "us_treasury_5y",
    "us_treasury_10y", "us_treasury_30y",
}

# Mapping catalog IDs (bonds.yaml) → (FRED series, maturity label)
_CATALOG_TO_FRED_SERIES: dict[str, tuple[str, str]] = {
    "us_2y":  ("DGS2",  "2Y"),
    "us_5y":  ("DGS5",  "5Y"),
    "us_10y": ("DGS10", "10Y"),
    "us_30y": ("DGS30", "30Y"),
    # Deuda soberana euro vía FRED (OCDE): ecb no la sirve y bde la baja como macro.
    "spain_10y":   ("IRLTLT01ESM156N", "10Y"),
    "germany_10y": ("IRLTLT01DEM156N", "10Y"),
}
# País por catalog id para no etiquetar como US los bonos europeos.
_YIELD_COUNTRY: dict[str, str] = {"spain_10y": "ES", "germany_10y": "DE"}


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


def _parse_fred_csv(
    text: str, indicator_id: str, name: str, source_url: str, n: int = 3,
    unit: str = "%", frequency: str = "monthly",
) -> list[MacroIndicator]:
    reader = csv.DictReader(io.StringIO(text))
    records: list[MacroIndicator] = []
    # ECO-3: la columna de fecha de fredgraph.csv es `observation_date` (no `DATE`).
    # Leerla mal dejaba period="" y colaba la fecha como columna de valor. Se detecta
    # el nombre real para que period salga poblado (luego el repository lo normaliza).
    fieldnames = [f for f in (reader.fieldnames or []) if f]
    date_col = next((f for f in fieldnames if f.lower() in ("date", "observation_date")),
                    fieldnames[0] if fieldnames else "observation_date")
    value_fields = [f for f in fieldnames if f != date_col]
    value_columns = ["VALUE"] if "VALUE" in value_fields else value_fields
    for row in reader:
        date_str = row.get(date_col, "")
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
                    unit=unit,
                    period=date_str,
                    frequency=frequency,
                )
            )
    return records[-n:]


def _parse_yield_csv(
    text: str, series_id: str, maturity: str, source_url: str, country: str = "US"
) -> list[YieldCurvePoint]:
    reader = csv.DictReader(io.StringIO(text))
    field = series_id if series_id in (reader.fieldnames or []) else "VALUE"
    last: YieldCurvePoint | None = None
    for row in reader:
        date_str = row.get("DATE") or row.get("observation_date") or ""
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
            country=country,
            region="USA" if country == "US" else "Europe",
            confidence_score=0.95,
            maturity=maturity,
            yield_value=value,
            date=datetime.fromisoformat(date_str).date() if date_str else None,
            currency="USD" if country == "US" else "EUR",
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
                    records.extend(_parse_fred_csv(response.text, sid, name, url, unit="%"))
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

        elif indicator_id in _CATALOG_TO_FRED_SERIES:
            series_id, maturity = _CATALOG_TO_FRED_SERIES[indicator_id]
            url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
            try:
                response = requests.get(url, headers=_HEADERS, timeout=10)
                response.raise_for_status()
                raw_sample = {"yield_preview": response.text[:500]}
                records.extend(_parse_yield_csv(
                    response.text, series_id, maturity, url,
                    country=_YIELD_COUNTRY.get(indicator_id, "US"),
                ))
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
                    records.extend(
                        _parse_fred_csv(
                            response.text, series_id, name, url,
                            unit=_SERIES_UNITS.get(series_id, "%"),
                            frequency=_SERIES_FREQ.get(series_id, "monthly"),
                        )
                    )
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
