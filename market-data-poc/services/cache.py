import dataclasses
import hashlib
import json
import time
from datetime import date, datetime
from pathlib import Path
from typing import Callable

from models.base import AdapterResult


class LocalTTLCache:
    def __init__(self, cache_dir: Path | None = None, ttl_seconds: int = 900):
        self.cache_dir = cache_dir or Path(__file__).parent.parent / "output" / "cache"
        self.ttl_seconds = ttl_seconds
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_or_set(self, key: str, fetcher: Callable[[], AdapterResult]) -> AdapterResult:
        path = self._path_for(key)
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
            if time.time() - payload.get("created_at", 0) <= self.ttl_seconds:
                return _result_from_dict(payload["result"])

        result = fetcher()
        path.write_text(
            json.dumps(
                {"created_at": time.time(), "result": dataclasses.asdict(result)},
                default=_json_default,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return result

    def clear(self) -> int:
        count = 0
        for path in self.cache_dir.glob("*.json"):
            path.unlink()
            count += 1
        return count

    def _path_for(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{digest}.json"


def _json_default(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return str(obj)


def _result_from_dict(payload: dict) -> AdapterResult:
    from models.base import ProviderMetadata

    metadata = ProviderMetadata(**payload["metadata"])
    return AdapterResult(
        provider=payload["provider"],
        success=payload["success"],
        records=payload.get("records", []),
        error=payload.get("error"),
        latency_ms=payload.get("latency_ms", 0.0),
        raw_sample=payload.get("raw_sample"),
        metadata=metadata,
    )
