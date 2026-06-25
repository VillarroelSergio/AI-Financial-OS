import dataclasses
from datetime import datetime
from pathlib import Path
from typing import List

import pandas as pd

from models.base import AdapterResult, ProviderRecord

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
