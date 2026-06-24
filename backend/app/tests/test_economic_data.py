"""Tests for Fase 5 — Economic Intelligence."""
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest


# ── FredProvider ──────────────────────────────────────────────────────────────

class TestFredProvider:
    def _make_fred(self, api_key="test_key"):
        from app.modules.economic_data.providers.fred_provider import FredProvider
        return FredProvider(api_key=api_key)

    def _make_response(self, observations):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"observations": observations}
        return mock_resp

    def test_available_with_key(self):
        provider = self._make_fred("abc123")
        assert provider.available is True

    def test_unavailable_without_key(self):
        provider = self._make_fred("")
        assert provider.available is False

    def test_fetch_series_returns_none_without_key(self):
        provider = self._make_fred("")
        result = provider.fetch_series("UNRATE")
        assert result is None

    def test_fetch_series_parses_observations(self):
        provider = self._make_fred("abc")
        obs = [
            {"date": "2026-05-01", "value": "4.1"},
            {"date": "2026-04-01", "value": "4.0"},
        ]
        with patch("requests.get", return_value=self._make_response(obs)):
            result = provider.fetch_series("UNRATE")
        assert result is not None
        assert result["value"] == 4.1
        assert result["prev_value"] == 4.0
        assert result["observation_date"] == "2026-05-01"

    def test_fetch_series_skips_missing_values(self):
        provider = self._make_fred("abc")
        obs = [
            {"date": "2026-05-01", "value": "."},
            {"date": "2026-04-01", "value": "4.0"},
        ]
        with patch("requests.get", return_value=self._make_response(obs)):
            result = provider.fetch_series("UNRATE")
        # dots filtered out, only one observation remains
        assert result is not None
        assert result["value"] == 4.0

    def test_fetch_series_handles_network_error(self):
        provider = self._make_fred("abc")
        with patch("requests.get", side_effect=Exception("timeout")):
            result = provider.fetch_series("UNRATE")
        assert result is None

    def test_fetch_all_returns_non_empty_list(self):
        provider = self._make_fred("abc")
        obs = [{"date": "2026-05-01", "value": "3.2"}, {"date": "2026-04-01", "value": "3.1"}]
        with patch("requests.get", return_value=self._make_response(obs)):
            results = provider.fetch_all()
        assert isinstance(results, list)
        assert len(results) > 0
        assert all("series_id" in r for r in results)

    def test_format_period(self):
        from app.modules.economic_data.providers.fred_provider import _format_period
        assert _format_period("2026-05-01") == "mayo 2026"
        assert _format_period("2026-01-01") == "enero 2026"
        assert _format_period("2026-12-01") == "diciembre 2026"


# ── Repository ────────────────────────────────────────────────────────────────

@pytest.fixture
def temp_repo(monkeypatch):
    """Returns a fresh repository instance backed by an in-memory DuckDB."""
    import app.modules.economic_data.repository as repo_mod

    # Force a fresh in-memory connection for each test
    import duckdb
    in_mem_conn = duckdb.connect(":memory:")
    # Pre-create the table
    in_mem_conn.execute(repo_mod._DDL)

    monkeypatch.setattr(repo_mod, "_conn", in_mem_conn)
    yield repo_mod
    try:
        in_mem_conn.close()
    except Exception:
        pass
    monkeypatch.setattr(repo_mod, "_conn", None)


def test_repo_upsert_and_get_latest(temp_repo):
    temp_repo.upsert_indicator(
        series_id="UNRATE",
        region="US",
        indicator="unemployment",
        name="Tasa de paro EEUU",
        value=4.1,
        prev_value=4.0,
        period="mayo 2026",
        unit="%",
        source="FRED",
        observation_date="2026-05-01",
    )
    row = temp_repo.get_latest("UNRATE")
    assert row is not None
    assert row["value"] == 4.1
    assert row["region"] == "US"


def test_repo_get_latest_returns_none_for_unknown(temp_repo):
    row = temp_repo.get_latest("NONEXISTENT")
    assert row is None


def test_repo_get_all_latest_empty(temp_repo):
    rows = temp_repo.get_all_latest()
    assert rows == []


def test_repo_is_stale_for_missing(temp_repo):
    stale = temp_repo.is_stale("NONEXISTENT", "inflation")
    assert stale is True


def test_repo_upsert_replaces_same_key(temp_repo):
    for value in (4.1, 4.5):
        temp_repo.upsert_indicator(
            series_id="UNRATE", region="US", indicator="unemployment",
            name="Tasa de paro", value=value, prev_value=None,
            period="mayo 2026", unit="%", source="FRED",
            observation_date="2026-05-01",
        )
    row = temp_repo.get_latest("UNRATE")
    assert row["value"] == 4.5


# ── Service / Routes ──────────────────────────────────────────────────────────

_EMPTY_SNAPSHOT = {
    "spain": {"region": "ES", "indicators": []},
    "eurozone": {"region": "EA", "indicators": []},
    "us": {"region": "US", "indicators": []},
    "last_refreshed": "2026-06-24T00:00:00+00:00",
}

_EMPTY_IMPACT = {
    "inflation_vs_savings": {
        "title": "Inflación vs tu tasa de ahorro",
        "macro_value": None, "personal_value": None, "delta": None,
        "interpretation": "no_data", "description": "Sin datos.",
    },
    "rates_vs_liquidity": {
        "title": "Tipo BCE vs rentabilidad de tu liquidez",
        "macro_value": None, "personal_value": None, "delta": None,
        "interpretation": "no_data", "description": "Sin datos.",
    },
    "market_vs_portfolio": {
        "title": "Mercado vs rentabilidad de tu cartera",
        "macro_value": None, "personal_value": None, "delta": None,
        "interpretation": "no_data", "description": "Sin datos.",
    },
    "purchasing_power": {
        "title": "Poder adquisitivo",
        "macro_value": None, "personal_value": None, "delta": None,
        "interpretation": "no_data", "description": "Sin datos.",
    },
}


class TestEconomyRoutes:
    def test_snapshot_endpoint_returns_200(self, client):
        with patch("app.modules.economic_data.service.get_snapshot", return_value=MagicMock(**_EMPTY_SNAPSHOT)):
            with patch("app.modules.economic_data.routes.service.get_snapshot") as mock_snap:
                from app.modules.economic_data.schemas import MacroSnapshotOut, RegionSnapshotOut
                mock_snap.return_value = MacroSnapshotOut(
                    spain=RegionSnapshotOut(region="ES", indicators=[]),
                    eurozone=RegionSnapshotOut(region="EA", indicators=[]),
                    us=RegionSnapshotOut(region="US", indicators=[]),
                    last_refreshed="2026-06-24T00:00:00+00:00",
                )
                r = client.get("/api/economy/snapshot")
        assert r.status_code == 200
        data = r.json()
        assert "spain" in data
        assert "eurozone" in data
        assert "us" in data

    def test_indicators_endpoint_returns_list(self, client):
        with patch("app.modules.economic_data.routes.service.get_indicators", return_value=[]):
            r = client.get("/api/economy/indicators")
        assert r.status_code == 200
        assert r.json() == []

    def test_refresh_endpoint_returns_200(self, client):
        from app.modules.economic_data.schemas import MacroSnapshotOut, RegionSnapshotOut
        snap = MacroSnapshotOut(
            spain=RegionSnapshotOut(region="ES", indicators=[]),
            eurozone=RegionSnapshotOut(region="EA", indicators=[]),
            us=RegionSnapshotOut(region="US", indicators=[]),
            last_refreshed="2026-06-24T00:00:00+00:00",
        )
        with patch("app.modules.economic_data.routes.service.refresh_snapshot", return_value=snap):
            r = client.post("/api/economy/refresh")
        assert r.status_code == 200

    def test_refresh_409_when_locked(self, client):
        with patch("app.modules.economic_data.routes.service.refresh_snapshot", return_value=None):
            r = client.post("/api/economy/refresh")
        assert r.status_code == 409

    def test_impact_endpoint_returns_200(self, client):
        from app.modules.economic_data.schemas import PersonalImpactOut, ImpactItem
        no_data = ImpactItem(
            title="T", macro_value=None, personal_value=None,
            delta=None, interpretation="no_data", description="Sin datos.",
        )
        mock_impact = PersonalImpactOut(
            inflation_vs_savings=no_data,
            rates_vs_liquidity=no_data,
            market_vs_portfolio=no_data,
            purchasing_power=no_data,
        )
        with patch("app.modules.economic_data.routes.service.get_personal_impact", return_value=mock_impact):
            r = client.get("/api/economy/impact")
        assert r.status_code == 200
        data = r.json()
        for key in ("inflation_vs_savings", "rates_vs_liquidity", "market_vs_portfolio", "purchasing_power"):
            assert key in data


# ── PersonalImpact calculations ───────────────────────────────────────────────

class TestPersonalImpactCalcs:
    def _make_db(self, income: float, expense: float, month_prefix: str = "2026-05"):
        mock_tx_income = MagicMock(type="income", amount=Decimal(str(income)))
        mock_tx_expense = MagicMock(type="expense", amount=Decimal(str(-expense)))
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_tx_income, mock_tx_expense,
        ]
        return mock_db

    def test_inflation_vs_savings_favorable(self):
        from app.modules.economic_data.service import _calc_inflation_vs_savings
        db = self._make_db(income=3000, expense=2100)  # savings_rate = 30%

        with patch("app.modules.economic_data.service.repo.get_latest") as mock_get:
            mock_get.return_value = {"value": 3.0}
            result = _calc_inflation_vs_savings(db)

        assert result.interpretation in ("favorable", "adverse", "neutral", "no_data")
        assert result.title == "Inflación vs tu tasa de ahorro"

    def test_inflation_vs_savings_no_macro_data(self):
        from app.modules.economic_data.service import _calc_inflation_vs_savings
        db = self._make_db(income=3000, expense=2100)

        with patch("app.modules.economic_data.service.repo.get_latest", return_value=None):
            result = _calc_inflation_vs_savings(db)

        assert result.interpretation == "no_data"
        assert result.macro_value is None

    def test_rates_vs_liquidity_no_savings_accounts(self):
        from app.modules.economic_data.service import _calc_rates_vs_liquidity
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        with patch("app.modules.economic_data.service.repo.get_latest") as mock_get:
            mock_get.return_value = {"value": 3.25}
            result = _calc_rates_vs_liquidity(mock_db)

        assert result.interpretation == "no_data"
        assert result.personal_value is None

    def test_market_vs_portfolio_no_holdings(self):
        from app.modules.economic_data.service import _calc_market_vs_portfolio
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch("app.modules.economic_data.service.repo.get_latest") as mock_get:
            mock_get.return_value = {"value": 5000, "prev_value": 4800}
            result = _calc_market_vs_portfolio(mock_db)

        assert result.interpretation == "no_data"
        assert result.personal_value is None

    def test_impact_interpretation_values_are_valid(self):
        valid = {"favorable", "neutral", "adverse", "no_data"}
        from app.modules.economic_data.schemas import ImpactItem
        item = ImpactItem(
            title="Test", macro_value=3.0, personal_value=5.0, delta=2.0,
            interpretation="favorable", description="OK",
        )
        assert item.interpretation in valid
