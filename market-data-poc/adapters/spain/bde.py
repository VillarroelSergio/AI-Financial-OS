"""Banco de España adapter — Euribor 12M from BDE statistics CSV."""
import io
import time
import requests
from datetime import datetime, timezone

from adapters.base import BaseAdapter
from models.base import AdapterResult, ProviderMetadata
from models.macro import MacroIndicator

_PRIMARY_URL = "https://www.bde.es/webbde/es/estadis/infoest/Series/si_1_1.csv"
_FALLBACK_URL = (
    "https://www.bde.es/f/webbde/SES/Secciones/Publicaciones/InformesBoletinesRevistas"
    "/BoletinEstadistico/25/T01/Fich/be_1-1.csv"
)


class BDEAdapter(BaseAdapter):
    name = "Banco de España"
    category = "macro"
    region = "Spain"
    requires_api_key = False

    def is_available(self) -> bool:
        try:
            r = requests.head(_PRIMARY_URL, timeout=10)
            return r.status_code < 500
        except Exception:
            return False

    def fetch(self) -> AdapterResult:
        metadata = self._make_metadata(base_url=_PRIMARY_URL)
        t0 = time.time()
        try:
            response = self._get_csv(t0)
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

        raw_text, latency_ms, used_url = response
        metadata = self._make_metadata(base_url=used_url)

        try:
            records = self._parse_csv(raw_text)
        except Exception as exc:
            return AdapterResult(
                provider=self.name,
                success=False,
                records=[],
                error=f"Parse error: {exc}",
                latency_ms=latency_ms,
                raw_sample=None,
                metadata=metadata,
            )

        raw_sample = {"raw_preview": raw_text[:500]} if raw_text else None
        return AdapterResult(
            provider=self.name,
            success=True,
            records=records,
            error=None,
            latency_ms=latency_ms,
            raw_sample=raw_sample,
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    def _get_csv(self, t0: float):
        """Try primary URL first, then fallback. Returns (text, latency_ms, url)."""
        for url in (_PRIMARY_URL, _FALLBACK_URL):
            try:
                r = requests.get(url, timeout=10)
                latency_ms = (time.time() - t0) * 1000
                r.raise_for_status()
                return r.text, latency_ms, url
            except Exception:
                pass
        raise RuntimeError("Both BDE CSV URLs failed")

    def _parse_csv(self, raw_text: str) -> list:
        import csv

        retrieved_at = datetime.now(timezone.utc)
        lines = raw_text.splitlines()

        # Skip header/comment rows (lines that don't start with a digit or date-like)
        data_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            first_char = stripped[0]
            if first_char.isdigit() or (len(stripped) > 4 and stripped[1:5].isdigit()):
                data_lines.append(stripped)

        # Take last 3 rows
        rows = list(csv.reader(data_lines[-3:], delimiter=";"))
        if not rows:
            # Retry with comma delimiter
            rows = list(csv.reader(data_lines[-3:], delimiter=","))

        records: list[MacroIndicator] = []
        for row in rows:
            if len(row) < 2:
                continue
            period = row[0].strip()
            try:
                value = float(row[1].strip().replace(",", "."))
            except (ValueError, IndexError):
                continue
            records.append(
                MacroIndicator(
                    provider=self.name,
                    source=_PRIMARY_URL,
                    retrieved_at=retrieved_at,
                    country="Spain",
                    region=self.region,
                    confidence_score=0.9,
                    indicator_id="EURIBOR_12M",
                    name="Euribor 12 meses",
                    value=value,
                    unit="%",
                    period=period,
                    frequency="monthly",
                )
            )
        return records
