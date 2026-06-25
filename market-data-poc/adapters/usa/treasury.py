"""US Treasury adapter — daily yield curve (focus: 10Y yield)."""
import time
import requests
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from adapters.base import BaseAdapter
from models.base import AdapterResult, ProviderMetadata
from models.macro import MacroIndicator

_HEADERS = {"User-Agent": "MarketDataPOC/0.1 contact@example.com"}

_TREASURY_URL = (
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml"
    "?data=daily_treasury_yield_curve&field_tdr_date_value=202401"
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
        notes="US Treasury yield curve XML feed — daily updates on business days",
    )


def _parse_treasury_xml(text: str, retrieved_at: datetime) -> list[MacroIndicator]:
    """Parse Treasury XML and return MacroIndicator records for each maturity."""
    records: list[MacroIndicator] = []
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
            MacroIndicator(
                provider="US Treasury",
                source=_TREASURY_URL,
                retrieved_at=retrieved_at,
                country="US",
                region="USA",
                confidence_score=1.0,
                indicator_id=f"US_T{maturity_label}",
                name=name,
                value=val,
                unit="%",
                period=period,
                frequency="daily",
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
            last_exc = None
            for attempt in range(self.retries + 1):
                try:
                    r = requests.get(_TREASURY_URL, headers=_HEADERS, timeout=self.timeout_seconds)
                    r.raise_for_status()
                    break
                except Exception as exc:
                    last_exc = exc
                    if attempt >= self.retries:
                        raise
                    time.sleep(0.5 * (attempt + 1))
            raw_sample = {"preview": r.text[:500]}

            records = _parse_treasury_xml(r.text, retrieved_at)

            latency_ms = (time.time() - t0) * 1000
            return AdapterResult(
                provider=self.name,
                success=bool(records),
                records=records,
                error=None if records else "No yield data parsed from XML",
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
