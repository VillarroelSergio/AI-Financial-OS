"""OECD adapter — Spain GDP QoQ growth from OECD QNA data."""
import csv
import io
import time
import requests
from datetime import datetime, timezone

from adapters.base import BaseAdapter
from models.base import AdapterResult, ProviderMetadata
from models.macro import MacroIndicator

_HEADERS = {"User-Agent": "MarketDataPOC/0.1 contact@example.com"}

_PRIMARY_URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA,1.1/"
    "Q.ESP+USA+EA19.B1GQ.....V.....?"
    "startPeriod=2023-Q1&endPeriod=2024-Q4"
    "&dimensionAtObservation=AllDimensions&format=csvfile"
)
_FALLBACK_URL = (
    "https://stats.oecd.org/SDMX-JSON/data/QNA/ESP.B1_GE.DOBSA.Q/all"
    "?startTime=2023-Q1&endTime=2024-Q4"
)


def _metadata() -> ProviderMetadata:
    return ProviderMetadata(
        name="OECD",
        id="oecd",
        category="macro",
        region="Global",
        method="api",
        base_url="https://sdmx.oecd.org",
        requires_api_key=False,
        declared_update_frequency="quarterly",
        declared_historical_depth_years=40,
        license="OECD Open Data",
        notes="OECD SDMX REST API — QNA quarterly national accounts",
    )


def _parse_csv_for_spain(text: str) -> list[MacroIndicator]:
    """Parse OECD csvfile format, filter for Spain (ESP), return last 3 rows."""
    retrieved_at = datetime.now(timezone.utc)
    reader = csv.DictReader(io.StringIO(text))
    rows = [r for r in reader if "ESP" in str(r.get("REF_AREA", "")) or "ESP" in str(r.get("LOCATION", ""))]
    records: list[MacroIndicator] = []
    for row in rows[-3:]:
        period = row.get("TIME_PERIOD", row.get("Time", ""))
        obs_val = row.get("OBS_VALUE", row.get("Value", ""))
        if not obs_val:
            continue
        try:
            value = float(obs_val)
        except ValueError:
            continue
        records.append(
            MacroIndicator(
                provider="OECD",
                source=_PRIMARY_URL,
                retrieved_at=retrieved_at,
                country="ESP",
                region="Global",
                confidence_score=1.0,
                indicator_id="OECD_ESP_GDP",
                name="Spain GDP QoQ (OECD)",
                value=value,
                unit="%",
                period=period,
                frequency="quarterly",
            )
        )
    return records


def _parse_json_for_spain(data: dict) -> list[MacroIndicator]:
    """Parse OECD SDMX-JSON format for Spain GDP."""
    retrieved_at = datetime.now(timezone.utc)
    records: list[MacroIndicator] = []
    try:
        payload = data.get("data", data)
        series = payload.get("dataSets", [{}])[0].get("series", {})
        structures = payload.get("structures") or [payload.get("structure", {})]
        structure = structures[0] if structures else {}
        time_dims = (
            structure.get("dimensions", {})
                     .get("observation", [{}])
        )
        # Find the time dimension index
        time_index = next(
            (i for i, d in enumerate(time_dims) if d.get("id") == "TIME_PERIOD"),
            None,
        )
        time_labels: list[str] = []
        if time_index is not None:
            time_labels = [
                v.get("id", "") for v in time_dims[time_index].get("values", [])
            ]

        for _key, series_data in series.items():
            observations = series_data.get("observations", {})
            for obs_idx_str, obs_list in observations.items():
                obs_idx = int(obs_idx_str)
                period = time_labels[obs_idx] if obs_idx < len(time_labels) else obs_idx_str
                val = obs_list[0] if obs_list else None
                if val is None:
                    continue
                records.append(
                    MacroIndicator(
                        provider="OECD",
                        source=_FALLBACK_URL,
                        retrieved_at=retrieved_at,
                        country="ESP",
                        region="Global",
                        confidence_score=0.9,
                        indicator_id="OECD_ESP_GDP",
                        name="Spain GDP QoQ (OECD)",
                        value=float(val),
                        unit="%",
                        period=period,
                        frequency="quarterly",
                    )
                )
    except Exception:
        pass
    return records[-3:]


class OECDAdapter(BaseAdapter):
    name = "OECD"
    category = "macro"
    region = "Global"
    requires_api_key = False

    def fetch(self) -> AdapterResult:
        metadata = _metadata()
        t0 = time.time()
        raw_sample: dict | None = None

        # Try primary CSV endpoint
        try:
            r = requests.get(_PRIMARY_URL, headers=_HEADERS, timeout=10)
            r.raise_for_status()
            raw_sample = {"preview": r.text[:500]}
            records = _parse_csv_for_spain(r.text)
            if records:
                latency_ms = (time.time() - t0) * 1000
                return AdapterResult(
                    provider=self.name,
                    success=True,
                    records=records,
                    error=None,
                    latency_ms=latency_ms,
                    raw_sample=raw_sample,
                    metadata=metadata,
                )
        except Exception:
            pass

        # Try fallback JSON endpoint
        try:
            r2 = requests.get(_FALLBACK_URL, headers=_HEADERS, timeout=10)
            r2.raise_for_status()
            data = r2.json()
            raw_sample = {"preview": str(data)[:500]}
            records = _parse_json_for_spain(data)
            latency_ms = (time.time() - t0) * 1000
            return AdapterResult(
                provider=self.name,
                success=bool(records),
                records=records,
                error=None if records else "No data parsed from fallback",
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
                raw_sample=raw_sample,
                metadata=metadata,
            )
