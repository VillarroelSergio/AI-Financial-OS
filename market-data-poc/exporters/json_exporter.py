import json
import dataclasses
from datetime import datetime, date
from pathlib import Path
from typing import List

from models.base import AdapterResult

_OUTPUT_DIR = Path(__file__).parent.parent / "output" / "json"


def _default_serializer(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    return str(obj)


def export_results(results: List[AdapterResult], timestamp: str | None = None) -> List[Path]:
    """
    Write each AdapterResult to output/json/{timestamp}_{provider}.json.

    Returns the list of written file paths.
    """
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = timestamp or datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    written: List[Path] = []

    for result in results:
        safe_name = result.provider.replace(" ", "_").replace("/", "-")
        path = _OUTPUT_DIR / f"{ts}_{safe_name}.json"
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(dataclasses.asdict(result), fh, default=_default_serializer, indent=2, ensure_ascii=False)
        written.append(path)

    return written
