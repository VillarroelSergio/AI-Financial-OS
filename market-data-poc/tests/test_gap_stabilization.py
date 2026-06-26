from datetime import datetime, timezone

from adapters.global_.frankfurter import FrankfurterAdapter
from adapters.global_.opencorporates import OpenCorporatesAdapter
from adapters.europe.eurostat import _parse_jsonstat
from adapters.usa.fred import _parse_yield_csv
from adapters.usa.treasury import _parse_fiscaldata_bond_yields, _parse_treasury_payload
from models.base import ProviderStatus


class DummyResponse:
    url = "https://api.frankfurter.app/latest?from=EUR&to=USD"

    def raise_for_status(self):
        return None

    def json(self):
        return {"base": "EUR", "date": "2026-06-24", "rates": {"USD": 1.17, "GBP": 0.86}}


def test_frankfurter_latest_parser(monkeypatch):
    monkeypatch.setattr("adapters.global_.frankfurter.requests.get", lambda *args, **kwargs: DummyResponse())

    result = FrankfurterAdapter().fetch()

    assert result.success is True
    assert len(result.records) == 2
    assert result.records[0].base_currency == "EUR"


def test_treasury_xml_parser_extracts_curve_points():
    payload = """
    <feed><entry><content><properties>
      <NEW_DATE>2026-06-24T00:00:00</NEW_DATE>
      <BC_1MONTH>4.30</BC_1MONTH>
      <BC_10YEAR>4.25</BC_10YEAR>
      <BC_30YEAR>4.80</BC_30YEAR>
    </properties></content></entry></feed>
    """

    records = _parse_treasury_payload(payload, datetime.now(timezone.utc))

    assert {record.maturity for record in records} == {"1M", "10Y", "30Y"}
    assert records[0].currency == "USD"


def test_treasury_fiscaldata_fallback_extracts_bond_yields():
    data = {
        "data": [
            {
                "record_date": "2026-05-31",
                "security_type_desc": "Marketable",
                "security_desc": "Treasury Bills",
                "avg_interest_rate_amt": "3.690",
            }
        ]
    }

    records = _parse_fiscaldata_bond_yields(data, datetime.now(timezone.utc))

    assert len(records) == 1
    assert records[0].maturity == "Treasury Bills"
    assert records[0].yield_value == 3.69


def test_fred_yield_csv_parser_extracts_latest_value():
    csv_text = "DATE,DGS10\n2026-06-23,.\n2026-06-24,4.25\n"

    records = _parse_yield_csv(csv_text, "DGS10", "10Y", "https://fred.test/DGS10")

    assert len(records) == 1
    assert records[0].maturity == "10Y"
    assert records[0].yield_value == 4.25


def test_missing_opencorporates_key_is_unavailable(monkeypatch):
    monkeypatch.delenv("OPENCORPORATES_API_KEY", raising=False)

    health = OpenCorporatesAdapter().health_check()

    assert health.status == ProviderStatus.OFFLINE
    assert "API key" in (health.error or "")


def test_eurostat_jsonstat_periods_are_parsed():
    data = {
        "id": ["geo", "time"],
        "size": [1, 3],
        "dimension": {
            "geo": {"category": {"index": {"EA20": 0}}},
            "time": {"category": {"index": {"2025": 0, "2025-Q1": 1, "2025M01": 2}}},
        },
        "value": {"0": 1.0, "1": 0.2, "2": 2.4},
    }

    records = _parse_jsonstat(data, "https://eurostat.test", "TEST", "Test", "monthly", datetime.now(timezone.utc))

    assert [record.period for record in records] == ["2025", "2025-Q1", "2025M01"]
    assert [record.value for record in records] == [1.0, 0.2, 2.4]
