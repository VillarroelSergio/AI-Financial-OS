import dataclasses
from datetime import datetime
from pathlib import Path
from typing import List

import pandas as pd

from models.base import AdapterResult, ProviderRecord
from models.catalog import CatalogFetchResult

_OUTPUT_DIR = Path(__file__).parent.parent / "output" / "csv"


def export_records(results: List[AdapterResult], timestamp: str | None = None) -> Path:
    """
    Flatten all ProviderRecord instances from all results and write to a single CSV.

    Returns the path of the written file.
    """
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = timestamp or datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    path = _OUTPUT_DIR / f"{ts}_all_records.csv"

    rows = []
    for result in results:
        for record in result.records:
            if dataclasses.is_dataclass(record) and not isinstance(record, type):
                rows.append(dataclasses.asdict(record))
            elif isinstance(record, dict):
                rows.append(record)

    df = pd.DataFrame(rows) if rows else pd.DataFrame()
    df.to_csv(path, index=False, encoding="utf-8")
    return path


def export_catalog_results(
    results: list,
    timestamp: str | None = None,
    output_dir: Path | None = None,
) -> Path:
    """
    Export catalog fetch results to CSV with catalog metadata fields.

    Returns the path of the written file.
    """
    out_dir = output_dir or _OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = timestamp or datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    path = out_dir / f"{ts}_catalog_records.csv"

    rows = []
    for cfr in results:
        catalog_meta = {
            "catalog_id": cfr.catalog_id,
            "priority": cfr.indicator.priority,
            "dashboard": cfr.indicator.dashboard,
            "ai": cfr.indicator.ai,
            "provider_used": cfr.provider_used,
            "fallback_used": cfr.fallback_used,
        }
        for record in cfr.adapter_result.records:
            if dataclasses.is_dataclass(record) and not isinstance(record, type):
                row = dataclasses.asdict(record)
                row.update(catalog_meta)
                rows.append(row)
            elif isinstance(record, dict):
                row = dict(record)
                row.update(catalog_meta)
                rows.append(row)

    df = pd.DataFrame(rows) if rows else pd.DataFrame()
    df.to_csv(path, index=False, encoding="utf-8")
    return path
