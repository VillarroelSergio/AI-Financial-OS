"""US Treasury adapter — daily yield curve (focus: 10Y yield)."""
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import requests

from app.modules.market_intelligence.ingestion.adapters.base import BaseAdapter
from app.modules.market_intelligence.ingestion.models import (
    AdapterResult,
    BondYield,
    ProviderMetadata,
    YieldCurvePoint,
)

_HEADERS = {"User-Agent": "MarketDataPOC/0.1 contact@example.com"}

_TREASURY_URL = (
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml"
    "?data=daily_treasury_yield_curve&field_tdr_date_value=202401"
)
_FISCALDATA_URL = (
    "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates"
    "?sort=-record_date&page[size]=10"
)

# Mapping from Treasury XML element suffixes to maturity labels
_MATURITY_MAP = {
    "BC_1MONTH": ("1M", "US Treasury 1-Month Yield"),
    "BC_3MONTH": ("3M", "US Treasury 3-Month Yield"),
    "BC_6MONTH": ("6M", "US Treasury 6-Month Yield"),
    "BC_1YEAR":  ("1Y", "US Treasury 1-Year Yield"),
    "BC_2YEAR":  ("2Y", "US Treasury 2-Year Yield"),
    "BC_5YEAR":  ("5Y", "US Treasury 5-Year Yield"),
    "BC_10YEAR": ("10Y", "US Treasury 10-Year Yield"),
    "BC_30YEAR": ("30Y", "US Treasury 30-Year Yield"),
}


def _metadata() -> ProviderMetadata:
    return ProviderMetadata(
        name="US Treasury",
        id="us_treasury",
        category="macro",
        region="USA",
        method="api",
        base_url="https://home.treasury.gov",
        requires_api_key=False,
        declared_update_frequency="daily",
        declared_historical_depth_years=30,
        license="Public Domain (US Treasury)",
        notes="US Treasury yield curve XML feed; FiscalData average interest rates fallback.",
        capabilities=("macro", "bonds"),
        priority="secondary",
    )


def _parse_treasury_payload(text: str, retrieved_at: datetime) -> list[YieldCurvePoint]:
    """Parse Treasury XML/JSON/HTML-ish payloads into yield curve points."""
    text = text.strip()
    if not text:
        return []
    if text.startswith("{") or text.startswith("["):
        try:
            return _parse_treasury_json(json.loads(text), retrieved_at)
        except Exception:
            return []
    try:
        return _parse_treasury_xml(text, retrieved_at)
    except ET.ParseError:
        return _parse_treasury_html(text, retrieved_at)


def _parse_fiscaldata_bond_yields(data: dict, retrieved_at: datetime) -> list[BondYield]:
    records: list[BondYield] = []
    for row in data.get("data", [])[:8]:
        raw = row.get("avg_interest_rate_amt")
        if raw in (None, ""):
            continue
        try:
            value = float(raw)
        except ValueError:
            continue
        security = row.get("security_desc", "Treasury securities")
        records.append(
            BondYield(
                provider="US Treasury",
                source=_FISCALDATA_URL,
                retrieved_at=retrieved_at,
                country="US",
                region="USA",
                confidence_score=0.85,
                maturity=security,
                yield_value=value,
                date=datetime.fromisoformat(row["record_date"]).date() if row.get("record_date") else None,
                currency="USD",
                issuer="US Treasury",
                instrument_type=row.get("security_type_desc", "government_bond"),
            )
        )
    return records


def _parse_treasury_xml(text: str, retrieved_at: datetime) -> list[YieldCurvePoint]:
    records: list[YieldCurvePoint] = []
    root = ET.fromstring(text)

    # Namespace handling — Treasury XML uses Atom/custom namespace
    ns_map: dict[str, str] = {}
    for elem in root.iter():
        tag = elem.tag
        if tag.startswith("{") and "}" in tag:
            ns_uri = tag[1:tag.index("}")]
            # Register all namespaces found
            if ns_uri not in ns_map.values():
                ns_map[f"ns{len(ns_map)}"] = ns_uri

    # Find the last <entry> or <content> with yield data
    # Treasury XML structure: feed > entry > content > properties > BC_* fields
    all_entries: list[ET.Element] = []
    for elem in root.iter():
        local = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if local == "entry":
            all_entries.append(elem)

    if not all_entries:
        return records

    # Use the last entry (most recent date)
    last_entry = all_entries[-1]
    period = ""
    maturity_values: dict[str, float] = {}

    for child in last_entry.iter():
        local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if local == "NEW_DATE" and child.text:
            period = child.text.strip()[:10]  # YYYY-MM-DD
        for key in _MATURITY_MAP:
            if local == key and child.text:
                try:
                    maturity_values[key] = float(child.text.strip())
                except ValueError:
                    pass

    for key, (maturity_label, name) in _MATURITY_MAP.items():
        val = maturity_values.get(key)
        if val is None:
            continue
        records.append(
            YieldCurvePoint(
                provider="US Treasury",
                source=_TREASURY_URL,
                retrieved_at=retrieved_at,
                country="US",
                region="USA",
                confidence_score=1.0,
                maturity=maturity_label,
                yield_value=val,
                date=datetime.fromisoformat(period).date() if period else None,
                currency="USD",
            )
        )

    return records


def _parse_treasury_json(data: dict | list, retrieved_at: datetime) -> list[YieldCurvePoint]:
    items = data.get("data") if isinstance(data, dict) else data
    if not isinstance(items, list) or not items:
        return []
    return _records_from_mapping(items[-1], retrieved_at)


def _parse_treasury_html(text: str, retrieved_at: datetime) -> list[YieldCurvePoint]:
    # Last-resort parser for embedded tables: look for BC_* field/value pairs.
    values: dict[str, float] = {}
    for key in _MATURITY_MAP:
        match = re.search(rf"{key}[^0-9.-]+([0-9]+(?:\.[0-9]+)?)", text, re.IGNORECASE)
        if match:
            values[key] = float(match.group(1))
    date_match = re.search(r"(20\d{2}-\d{2}-\d{2})", text)
    row = {"NEW_DATE": date_match.group(1) if date_match else ""}
    row.update(values)
    return _records_from_mapping(row, retrieved_at)


def _records_from_mapping(row: dict, retrieved_at: datetime) -> list[YieldCurvePoint]:
    period = str(row.get("NEW_DATE") or row.get("record_date") or row.get("date") or "")[:10]
    records: list[YieldCurvePoint] = []
    for key, (maturity_label, _name) in _MATURITY_MAP.items():
        raw = row.get(key) or row.get(key.lower()) or row.get(key.replace("BC_", "bc_"))
        if raw in (None, ""):
            continue
        try:
            val = float(raw)
        except (TypeError, ValueError):
            continue
        records.append(
            YieldCurvePoint(
                provider="US Treasury",
                source=_TREASURY_URL,
                retrieved_at=retrieved_at,
                country="US",
                region="USA",
                confidence_score=1.0,
                maturity=maturity_label,
                yield_value=val,
                date=datetime.fromisoformat(period).date() if period else None,
                currency="USD",
            )
        )
    return records


class TreasuryAdapter(BaseAdapter):
    name = "US Treasury"
    category = "macro"
    region = "USA"
    requires_api_key = False
    timeout_seconds = int(os.getenv("US_TREASURY_TIMEOUT", "10"))
    retries = int(os.getenv("US_TREASURY_RETRIES", "2"))

    def fetch(self) -> AdapterResult:
        metadata = _metadata()
        t0 = time.time()
        retrieved_at = datetime.now(timezone.utc)

        try:
            fallback = requests.get(_FISCALDATA_URL, headers=_HEADERS, timeout=self.timeout_seconds)
            fallback.raise_for_status()
            records = _parse_fiscaldata_bond_yields(fallback.json(), retrieved_at)
            raw_sample = {"fiscaldata_preview": fallback.text[:500]}

            r = None
            for attempt in range(1 if records else self.retries + 1):
                try:
                    r = requests.get(_TREASURY_URL, headers=_HEADERS, timeout=self.timeout_seconds)
                    r.raise_for_status()
                    break
                except Exception:
                    if not records and attempt >= self.retries:
                        raise
                    time.sleep(0.5 * (attempt + 1))
            curve_records = _parse_treasury_payload(r.text, retrieved_at) if r is not None else []
            if curve_records:
                records = curve_records + records
                raw_sample = {"treasury_preview": r.text[:500], **raw_sample}

            latency_ms = (time.time() - t0) * 1000
            return AdapterResult(
                provider=self.name,
                success=bool(records),
                records=records,
                error=None if records else "No yield data parsed from Treasury payload or FiscalData fallback",
                latency_ms=latency_ms,
                raw_sample=raw_sample,
                metadata=metadata,
            )

        except Exception as exc:
            latency_ms = (time.time() - t0) * 1000
            return AdapterResult(
                provider=self.name,
                success=False,
                records=[],
                error=str(exc),
                latency_ms=latency_ms,
                raw_sample=None,
                metadata=metadata,
            )
