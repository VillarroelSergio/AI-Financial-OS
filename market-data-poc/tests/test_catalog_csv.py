import dataclasses
from pathlib import Path
from models.catalog import CatalogIndicator, CatalogFetchResult
from models.base import AdapterResult, ProviderMetadata
from models.macro import MacroIndicator
from datetime import datetime, timezone
from exporters.csv_exporter import export_catalog_results


def _make_metadata():
    return ProviderMetadata(
        name="BDE", id="bde", category="macro", region="Spain",
        method="sdmx", base_url="", requires_api_key=False,
        declared_update_frequency="monthly", declared_historical_depth_years=10,
        license="open",
    )


def _make_cfr(indicator_id="euribor_3m", success=True, n_records=2):
    ind = CatalogIndicator(
        id=indicator_id, name="Test", category="macro", subcategory="rates",
        country="ES", region="Spain", frequency="daily", priority="critical",
        dashboard=True, ai=True, historical="10y", retention="5y",
        unit="%", description="", provider_primary="bde",
    )
    now = datetime.now(timezone.utc)
    records = [
        MacroIndicator(
            provider="BDE", source="url", retrieved_at=now,
            country="ES", region="Spain", confidence_score=0.95,
            indicator_id=indicator_id, name="Test", value=3.5 + i,
            unit="%", period=f"2024-0{i+1}", frequency="monthly",
        )
        for i in range(n_records)
    ]
    return CatalogFetchResult(
        indicator=ind,
        adapter_result=AdapterResult(
            provider="BDE", success=success, records=records,
            error=None, latency_ms=50.0, raw_sample=None, metadata=_make_metadata(),
        ),
        provider_used="bde",
        fallback_used=False,
        catalog_id=indicator_id,
    )


def test_export_catalog_results_creates_file(tmp_path):
    results = [_make_cfr("euribor_3m"), _make_cfr("eur_usd", n_records=1)]
    path = export_catalog_results(results, timestamp="20260626T000000", output_dir=tmp_path)
    assert path.exists()
    assert path.suffix == ".csv"


def test_export_catalog_results_includes_catalog_fields(tmp_path):
    import pandas as pd
    results = [_make_cfr("euribor_3m")]
    path = export_catalog_results(results, timestamp="20260626T000001", output_dir=tmp_path)
    df = pd.read_csv(path)
    assert "catalog_id" in df.columns
    assert "priority" in df.columns
    assert "dashboard" in df.columns
    assert "ai" in df.columns
    assert "provider_used" in df.columns
    assert "fallback_used" in df.columns
    assert df["catalog_id"].iloc[0] == "euribor_3m"
    assert df["priority"].iloc[0] == "critical"
    assert df["dashboard"].iloc[0] == True


def test_export_catalog_results_row_count(tmp_path):
    import pandas as pd
    results = [_make_cfr("euribor_3m", n_records=2), _make_cfr("eur_usd", n_records=1)]
    path = export_catalog_results(results, timestamp="20260626T000002", output_dir=tmp_path)
    df = pd.read_csv(path)
    assert len(df) == 3  # 2 + 1 records
