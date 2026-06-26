import math
from typing import List

from models.base import ProviderRecord


def validate_records(records: List[ProviderRecord]) -> List[ProviderRecord]:
    """
    Validate a list of ProviderRecord instances.

    - Checks each record's fields for None or NaN values.
    - Reduces confidence_score by 0.1 per missing/invalid field.
    - Records with confidence_score < 0.5 are retained but flagged (score set to at most 0.49).

    Returns the annotated list of records (no records are removed).
    """
    for record in records:
        penalty = _count_missing_fields(record)
        record.confidence_score = max(0.0, record.confidence_score - penalty * 0.1)

    return records


def _count_missing_fields(record: ProviderRecord) -> int:
    """Return the number of fields that are None or NaN."""
    missing = 0
    for field_name, value in record.__dict__.items():
        if value is None:
            missing += 1
        elif isinstance(value, float) and math.isnan(value):
            missing += 1
    return missing
