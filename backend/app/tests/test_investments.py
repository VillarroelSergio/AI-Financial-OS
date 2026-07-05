from sqlalchemy import inspect


def test_investment_tables_are_created(client):
    from app.core.database import engine
    tables = inspect(engine).get_table_names()
    assert "investment_assets" in tables
    assert "holdings" in tables
    assert "investment_operations" in tables


def test_assets_crud(client):
    r = client.post("/api/investments/assets", json={
        "name": "Apple Inc.", "ticker": "AAPL", "asset_type": "stock",
        "currency": "USD", "price_source": "yfinance",
    })
    assert r.status_code == 201
    asset = r.json()
    assert asset["name"] == "Apple Inc."
    asset_id = asset["id"]

    r = client.get("/api/investments/assets")
    assert r.status_code == 200
    assert any(a["id"] == asset_id for a in r.json())

    r = client.patch(f"/api/investments/assets/{asset_id}", json={"sector": "Technology"})
    assert r.status_code == 200
    assert r.json()["sector"] == "Technology"

    r = client.delete(f"/api/investments/assets/{asset_id}")
    assert r.status_code == 204

    r = client.get("/api/investments/assets")
    assert all(a["id"] != asset_id for a in r.json())


def test_asset_not_found_returns_404(client):
    r = client.patch("/api/investments/assets/nonexistent", json={"sector": "X"})
    assert r.status_code == 404


def _setup_account_and_asset(client):
    account = client.post("/api/accounts", json={
        "name": "Trade Republic", "type": "broker", "currency": "EUR",
    }).json()
    asset = client.post("/api/investments/assets", json={
        "name": "Telefónica", "ticker": "TEF.MC", "asset_type": "stock",
        "currency": "EUR", "price_source": "yfinance",
    }).json()
    return account["id"], asset["id"]


def test_holdings_crud_and_enrichment(client):
    account_id, asset_id = _setup_account_and_asset(client)

    r = client.post("/api/investments/holdings", json={
        "account_id": account_id, "asset_id": asset_id,
        "quantity": "100", "average_price": "3.95",
    })
    assert r.status_code == 201
    h = r.json()
    assert h["cost_basis"] == "395.0000"
    assert h["return_absolute"] is None
    assert h["asset"]["ticker"] == "TEF.MC"
    holding_id = h["id"]

    r = client.get("/api/investments/holdings")
    assert any(x["id"] == holding_id for x in r.json())

    r = client.patch(f"/api/investments/holdings/{holding_id}", json={"current_price": "4.21"})
    assert r.status_code == 200
    h = r.json()
    assert h["market_value"] == "421.00"
    assert h["return_absolute"] == "26.00"
    assert abs(h["return_percent"] - 6.58) < 0.1

    r = client.delete(f"/api/investments/holdings/{holding_id}")
    assert r.status_code == 204


def test_holdings_savings_account_accrued_interest(client):
    account = client.post("/api/accounts", json={
        "name": "TR Ahorro", "type": "savings", "currency": "EUR",
    }).json()
    asset = client.post("/api/investments/assets", json={
        "name": "Cuenta Remunerada TR", "asset_type": "savings_account",
        "currency": "EUR", "price_source": "manual",
    }).json()
    r = client.post("/api/investments/holdings", json={
        "account_id": account["id"], "asset_id": asset["id"],
        "quantity": "5000", "average_price": "1",
        "interest_rate": "0.04", "inception_date": "2025-01-01",
        "market_value": "5000",
    })
    assert r.status_code == 201
    h = r.json()
    assert h["accrued_interest"] is not None
    assert float(h["accrued_interest"]) > 0


def test_price_refresh_updates_holdings(client, monkeypatch):
    import app.modules.investments.price_service as ps

    prices = {"AAPL": 192.5, "EURUSD=X": 1.08}

    class MockFastInfo:
        def __init__(self, ticker):
            self.last_price = prices.get(ticker)

    class MockTicker:
        def __init__(self, ticker):
            self.fast_info = MockFastInfo(ticker)

    monkeypatch.setattr(ps.yf, "Ticker", MockTicker)

    account = client.post("/api/accounts", json={
        "name": "TR", "type": "broker", "currency": "EUR",
    }).json()
    asset = client.post("/api/investments/assets", json={
        "name": "Apple", "ticker": "AAPL", "asset_type": "stock",
        "currency": "USD", "price_source": "yfinance",
    }).json()
    holding = client.post("/api/investments/holdings", json={
        "account_id": account["id"], "asset_id": asset["id"],
        "quantity": "10", "average_price": "140.00",
    }).json()

    r = client.post("/api/investments/prices/refresh")
    assert r.status_code == 200
    data = r.json()
    assert data["updated"] == 1
    assert data["failed"] == []

    holdings = client.get("/api/investments/holdings").json()
    h = next(x for x in holdings if x["id"] == holding["id"])
    assert float(h["current_price"]) == 192.5
    expected_mv = round(10 * 192.5 / 1.08, 2)
    assert abs(float(h["market_value"]) - expected_mv) < 0.05


def test_fx_failure_marks_holding_manual_instead_of_rate_1(client, monkeypatch):
    from decimal import Decimal

    from app.modules.investments.price_service import PriceService

    def fake_fetch(ticker: str):
        if ticker.startswith("EUR"):  # FX caído
            return None
        return Decimal("100")

    monkeypatch.setattr(PriceService, "fetch_ticker_price", staticmethod(fake_fetch))

    account = client.post("/api/accounts", json={
        "name": "IBKR", "type": "broker", "currency": "EUR",
    }).json()
    asset = client.post("/api/investments/assets", json={
        "name": "Apple", "ticker": "AAPL", "asset_type": "stock",
        "currency": "USD", "price_source": "yfinance",
    }).json()
    holding = client.post("/api/investments/holdings", json={
        "account_id": account["id"], "asset_id": asset["id"],
        "quantity": "10", "average_price": "90.00",
    }).json()

    data = client.post("/api/investments/prices/refresh").json()
    assert any(item["reason"] == "fx_unavailable" for item in data["manual_required"])
    assert holding["id"] in data["needs_manual_nav"]

    h = next(x for x in client.get("/api/investments/holdings").json() if x["id"] == holding["id"])
    # No se valora con un tipo inventado: no hay market_value calculado con rate 1.0.
    assert h["current_price"] is None


def test_price_refresh_marks_manual_assets(client, monkeypatch):
    import app.modules.investments.price_service as ps

    class MockFastInfo:
        last_price = 576.19

    class MockTicker:
        def __init__(self, ticker):
            self.fast_info = MockFastInfo()

    monkeypatch.setattr(ps.yf, "Ticker", MockTicker)

    account = client.post("/api/accounts", json={
        "name": "Finizens", "type": "investment", "currency": "EUR",
    }).json()
    asset = client.post("/api/investments/assets", json={
        "name": "Vanguard US 500", "asset_type": "fund",
        "currency": "EUR", "price_source": "manual",
    }).json()
    holding = client.post("/api/investments/holdings", json={
        "account_id": account["id"], "asset_id": asset["id"],
        "quantity": "4.59", "average_price": "420.00",
    }).json()

    r = client.post("/api/investments/prices/refresh")
    assert r.status_code == 200
    data = r.json()
    assert holding["id"] in data["needs_manual_nav"]
    assert data["manual_required"][0]["holding_id"] == holding["id"]
    assert data["manual_required"][0]["reason"] == "missing_price_provider"


def test_refresh_prices_skips_savings_accounts(client):
    account = client.post("/api/accounts", json={
        "name": "TR Ahorro", "type": "savings", "currency": "EUR",
    }).json()
    asset = client.post("/api/investments/assets", json={
        "name": "Cuenta Remunerada TR", "asset_type": "savings_account",
        "currency": "EUR", "price_source": "manual",
    }).json()
    holding = client.post("/api/investments/holdings", json={
        "account_id": account["id"], "asset_id": asset["id"],
        "quantity": "5000", "average_price": "1", "market_value": "5000",
    }).json()

    r = client.post("/api/investments/prices/refresh")
    assert r.status_code == 200
    data = r.json()
    assert holding["id"] not in data["needs_manual_nav"]
    assert data["manual_required"] == []
    assert data["skipped"][0]["holding_id"] == holding["id"]
    assert data["skipped"][0]["reason"] == "cash_uses_account_balance"


def test_refresh_prices_does_not_request_nav_for_cash(client):
    account = client.post("/api/accounts", json={
        "name": "Efectivo", "type": "cash", "currency": "EUR",
    }).json()
    asset = client.post("/api/investments/assets", json={
        "name": "Efectivo cartera", "asset_type": "cash",
        "currency": "EUR", "price_source": "manual",
    }).json()
    client.post("/api/investments/holdings", json={
        "account_id": account["id"], "asset_id": asset["id"],
        "quantity": "1000", "average_price": "1", "market_value": "1000",
    })

    data = client.post("/api/investments/prices/refresh").json()
    assert data["needs_manual_nav"] == []
    assert data["manual_required"] == []
    assert len(data["skipped"]) == 1


def test_no_duplicate_cash_holdings_in_refresh_modal(client):
    account = client.post("/api/accounts", json={
        "name": "TR Ahorro", "type": "savings", "currency": "EUR",
    }).json()
    asset = client.post("/api/investments/assets", json={
        "name": "Cuenta Remunerada TR", "asset_type": "savings_account",
        "currency": "EUR", "price_source": "manual",
    }).json()
    for _ in range(2):
        client.post("/api/investments/holdings", json={
            "account_id": account["id"], "asset_id": asset["id"],
            "quantity": "1000", "average_price": "1", "market_value": "1000",
        })

    data = client.post("/api/investments/prices/refresh").json()
    assert data["manual_required"] == []
    assert data["needs_manual_nav"] == []


# ── Sprint INV-1: integridad de datos ─────────────────────────────────────────

def test_summary_excludes_unvalued_holdings_from_return(client):
    """BUG-INV-1: un fondo sin valoración (market_value None) no debe inflar el
    aportado ni romper la rentabilidad global; se reporta como pendiente aparte."""
    account_id, asset_id = _setup_account_and_asset(client)
    # Posición valorada: 100 * 4.00 = 400 valor, coste 100*3.00 = 300
    valued = client.post("/api/investments/holdings", json={
        "account_id": account_id, "asset_id": asset_id,
        "quantity": "100", "average_price": "3.00", "current_price": "4.00",
    }).json()
    assert valued["market_value"] == "400.00"

    # Fondo sin precio: coste 66000, market_value None → NO entra en la rentabilidad
    fund = client.post("/api/investments/assets", json={
        "name": "Vanguard US 500", "asset_type": "fund", "currency": "EUR", "price_source": "manual",
    }).json()
    client.post("/api/investments/holdings", json={
        "account_id": account_id, "asset_id": fund["id"],
        "quantity": "20", "average_price": "3300",
    })

    s = client.get("/api/investments/summary").json()
    assert s["total_value"] == "400.00"
    assert s["total_invested"] == "300.00"      # 66000 del fondo excluido
    assert s["return_absolute"] == "100.00"
    assert abs(s["return_percent"] - 33.33) < 0.1
    assert s["pending_valuation_count"] == 1
    assert s["pending_valuation_invested"] == "66000.00"


def test_merge_duplicate_holdings(client):
    """BUG-INV-1: fusionar dos posiciones del mismo activo suma cantidades, promedia
    el precio de entrada ponderado y deja una sola posición."""
    account_id, asset_id = _setup_account_and_asset(client)
    a = client.post("/api/investments/holdings", json={
        "account_id": account_id, "asset_id": asset_id,
        "quantity": "200", "average_price": "18.00", "current_price": "22.00",
    }).json()
    b = client.post("/api/investments/holdings", json={
        "account_id": account_id, "asset_id": asset_id,
        "quantity": "14.22", "average_price": "18.39", "current_price": "22.00",
    }).json()

    r = client.post("/api/investments/holdings/merge", json={"source_id": b["id"], "target_id": a["id"]})
    assert r.status_code == 200
    merged = r.json()
    assert merged["id"] == a["id"]
    assert abs(float(merged["quantity"]) - 214.22) < 1e-6
    # media ponderada: (200*18 + 14.22*18.39) / 214.22 ≈ 18.0259
    assert abs(float(merged["average_price"]) - 18.0259) < 0.001
    # valor combinado 200*22 + 14.22*22 = 4712.84
    assert merged["market_value"] == "4712.84"

    # el origen ya no existe
    assert client.delete(f"/api/investments/holdings/{b['id']}").status_code == 404
    assert len(client.get("/api/investments/holdings").json()) == 1


def test_merge_same_holding_rejected(client):
    account_id, asset_id = _setup_account_and_asset(client)
    h = client.post("/api/investments/holdings", json={
        "account_id": account_id, "asset_id": asset_id,
        "quantity": "10", "average_price": "1", "current_price": "1",
    }).json()
    r = client.post("/api/investments/holdings/merge", json={"source_id": h["id"], "target_id": h["id"]})
    assert r.status_code == 422


def test_performance_falls_back_to_stored_history(client):
    """BUG-INV-5: sin ticker/proveedor, /performance usa el histórico guardado."""
    account = client.post("/api/accounts", json={
        "name": "Finizens", "type": "investment", "currency": "EUR",
    }).json()
    fund = client.post("/api/investments/assets", json={
        "name": "Cleome Index", "asset_type": "fund", "currency": "EUR", "price_source": "manual",
    }).json()
    h = client.post("/api/investments/holdings", json={
        "account_id": account["id"], "asset_id": fund["id"],
        "quantity": "10", "average_price": "100",
    }).json()
    client.post(f"/api/investments/holdings/{h['id']}/history", json={"price": "100", "recorded_at": "2026-01-01T00:00:00Z"})
    client.post(f"/api/investments/holdings/{h['id']}/history", json={"price": "120", "recorded_at": "2026-06-01T00:00:00Z"})

    r = client.get(f"/api/investments/holdings/{h['id']}/performance")
    assert r.status_code == 200
    perf = r.json()
    assert perf["entry_source"] == "history"
    assert len(perf["series"]) == 2
    assert perf["current_price"] == 120.0
    assert perf["change_pct"] == 20.0


# ── INV-2: modelo de dominio (fondos, cuentas remuneradas, tipo de referencia) ──

def test_inv2_tables_created(client):
    from app.core.database import engine
    tables = inspect(engine).get_table_names()
    assert "fund_valuation_snapshots" in tables
    assert "savings_account_configs" in tables
    assert "reference_rate_observations" in tables


def _create_holding(client):
    account_id, asset_id = _setup_account_and_asset(client)
    return client.post("/api/investments/holdings", json={
        "account_id": account_id, "asset_id": asset_id,
        "quantity": "10", "average_price": "5.00",
    }).json()["id"]


def test_fund_snapshot_unique_per_holding_and_date(client):
    from datetime import date
    from decimal import Decimal
    from sqlalchemy.exc import IntegrityError
    from app.core.database import get_db
    from app.models.investment import FundValuationSnapshot

    holding_id = _create_holding(client)
    db = next(get_db())
    db.add(FundValuationSnapshot(
        holding_id=holding_id, date=date(2026, 1, 31), market_value=Decimal("100.00"),
    ))
    db.commit()
    db.add(FundValuationSnapshot(
        holding_id=holding_id, date=date(2026, 1, 31), market_value=Decimal("110.00"),
    ))
    raised = False
    try:
        db.commit()
    except IntegrityError:
        raised = True
        db.rollback()
    assert raised, "segundo snapshot en la misma fecha debe violar el constraint único"


def test_dfr_csv_parsing_offline(client):
    from datetime import date
    from decimal import Decimal
    from app.modules.investments import reference_rate_service as rrs

    ecb_csv = (
        "KEY,TIME_PERIOD,OBS_VALUE\n"
        "FM..DFR,2024-06-12,3.75\n"
        "FM..DFR,2024-09-18,3.50\n"
        "FM..DFR,2024-10-23,3.25\n"
    )
    parsed = rrs._parse_ecb(ecb_csv)
    assert parsed[date(2024, 6, 12)] == Decimal("3.75")
    assert parsed[date(2024, 10, 23)] == Decimal("3.25")

    fred_csv = "DATE,ECBDFR\n2024-06-12,3.75\n2024-09-18,.\n2024-09-19,3.50\n"
    fred = rrs._parse_fred(fred_csv)
    assert fred[date(2024, 9, 19)] == Decimal("3.50")
    assert date(2024, 9, 18) not in fred  # "." se ignora


def test_get_rate_on_effective_date_lookup(client):
    from datetime import date, datetime, timezone
    from decimal import Decimal
    from app.core.database import get_db
    from app.models.investment import ReferenceRateObservation
    from app.modules.investments import reference_rate_service as rrs

    db = next(get_db())
    for d, v in [("2024-06-12", "3.75"), ("2024-09-18", "3.50"), ("2024-10-23", "3.25")]:
        db.add(ReferenceRateObservation(
            rate_id=rrs.ECB_DFR, effective_date=date.fromisoformat(d), rate=Decimal(v),
            source="ecb", retrieved_at=datetime.now(timezone.utc),
        ))
    db.commit()

    assert rrs.get_rate_on(db, date(2024, 1, 1)) is None            # antes del primero
    assert rrs.get_rate_on(db, date(2024, 6, 12)) == Decimal("3.75")  # fecha exacta
    assert rrs.get_rate_on(db, date(2024, 9, 30)) == Decimal("3.50")  # entre cambios → previo
    assert rrs.get_rate_on(db, date(2025, 1, 1)) == Decimal("3.25")   # después del último


# ── INV-3/INV-4: flujos de fondos y motor de cuentas remuneradas ──────────────

def test_fund_flow_snapshots_and_performance(client):
    account = client.post("/api/accounts", json={"name": "Finizens", "type": "investment", "currency": "EUR"}).json()
    fund = client.post("/api/investments/funds", json={
        "name": "Vanguard US 500", "account_id": account["id"],
        "contributed": "10000.00", "value": "10000.00", "date": "2025-01-15",
    })
    assert fund.status_code == 201
    hid = fund.json()["id"]

    # segundo snapshot: sube el valor
    r = client.post(f"/api/investments/funds/{hid}/snapshots", json={"date": "2025-06-15", "market_value": "11000.00"})
    assert r.status_code == 201

    snaps = client.get(f"/api/investments/funds/{hid}/snapshots").json()
    assert len(snaps) == 2

    perf = client.get(f"/api/investments/holdings/{hid}/performance").json()
    assert perf["entry_source"] == "fund_snapshot"
    assert perf["current_price"] == 11000.0
    assert perf["change_pct"] == 10.0


def test_savings_engine_fixed_compounding():
    from datetime import date
    from decimal import Decimal
    from app.modules.investments.savings_service import SavingsInputs, compute_schedule

    inp = SavingsInputs(date(2025, 1, 1), Decimal("1000"), "fixed", Decimal("12"), 0, None)
    sch = compute_schedule(None, inp, as_of=date(2025, 12, 1))
    assert len(sch.points) == 12
    # 1000 * 1.01^12 ≈ 1126.83
    assert abs(sch.current_balance - Decimal("1126.83")) < Decimal("0.05")
    assert sch.total_interest > Decimal("126")


def test_savings_engine_mid_period_rate_change(client):
    from datetime import date, datetime, timezone
    from decimal import Decimal
    from app.core.database import get_db
    from app.models.investment import ReferenceRateObservation
    from app.modules.investments import reference_rate_service as rrs
    from app.modules.investments.savings_service import SavingsInputs, compute_schedule

    db = next(get_db())
    for d, v in [("2025-01-01", "4.00"), ("2025-07-01", "2.00")]:
        db.add(ReferenceRateObservation(
            rate_id=rrs.ECB_DFR, effective_date=date.fromisoformat(d), rate=Decimal(v),
            source="ecb", retrieved_at=datetime.now(timezone.utc),
        ))
    db.commit()

    inp = SavingsInputs(date(2025, 1, 1), Decimal("10000"), "ecb_deposit_facility", None, 0, None)
    sch = compute_schedule(db, inp, as_of=date(2025, 12, 1))
    # Primer mes usa 4%, un mes posterior a julio usa 2%: los tipos cambian mid-period.
    rates = {p.month: p.annual_rate for p in sch.points}
    assert rates["2025-01"] == Decimal("4.00")
    assert rates["2025-08"] == Decimal("2.00")


def test_savings_contributions_from_transactions(client):
    from datetime import date
    from decimal import Decimal
    from app.core.database import get_db
    from app.models.transaction import Transaction
    from app.modules.investments.savings_service import SavingsInputs, compute_schedule

    account = client.post("/api/accounts", json={"name": "Ahorro", "type": "savings", "currency": "EUR"}).json()
    db = next(get_db())
    db.add(Transaction(
        account_id=account["id"], date="2025-03-10", description="Aporte", amount=Decimal("500.00"),
        type="transfer",
    ))
    db.commit()

    inp = SavingsInputs(date(2025, 1, 1), Decimal("1000"), "fixed", Decimal("0"), 0, account["id"])
    sch = compute_schedule(db, inp, as_of=date(2025, 6, 1))
    assert sch.total_contributions == Decimal("500.00")
    # sin interés (0%) el saldo final = 1000 + 500
    assert sch.current_balance == Decimal("1500.00")


def test_savings_reverse_start_balance():
    from datetime import date
    from decimal import Decimal
    from app.modules.investments.savings_service import SavingsInputs, compute_schedule, estimate_start_balance

    inp = SavingsInputs(date(2025, 1, 1), Decimal("1000"), "fixed", Decimal("12"), 0, None)
    final = compute_schedule(None, inp, as_of=date(2025, 12, 1)).current_balance
    start = estimate_start_balance(None, inp, final, as_of=date(2025, 12, 1))
    assert abs(start - Decimal("1000")) < Decimal("0.05")


# ── INV-6: agregación de evolución y clasificación de calidad ─────────────────

def test_portfolio_evolution_forward_fills_and_sums(client):
    account = client.post("/api/accounts", json={"name": "Finizens", "type": "investment", "currency": "EUR"}).json()
    fund = client.post("/api/investments/funds", json={
        "name": "Fondo A", "account_id": account["id"],
        "contributed": "10000.00", "value": "10000.00", "date": "2025-01-15",
    }).json()
    client.post(f"/api/investments/funds/{fund['id']}/snapshots", json={"date": "2025-03-10", "market_value": "10500.00"})

    fund2 = client.post("/api/investments/funds", json={
        "name": "Fondo B", "account_id": account["id"],
        "contributed": "2000.00", "value": "2000.00", "date": "2025-02-20",
    }).json()
    assert fund2["id"]

    data = client.get("/api/investments/holdings/portfolio-evolution").json()
    series = {p["month"]: p["value"] for p in data["series"]}
    # ene: solo Fondo A (10000). feb: A(10000)+B(2000)=12000 (A forward-filled).
    # mar: A sube a 10500 + B 2000 = 12500.
    assert series["2025-01"] == 10000.0
    assert series["2025-02"] == 12000.0
    assert series["2025-03"] == 12500.0


def test_reconciliation_classifies_funds_manual_savings_confirmed(client):
    account = client.post("/api/accounts", json={"name": "Finizens", "type": "investment", "currency": "EUR"}).json()
    fund = client.post("/api/investments/funds", json={
        "name": "Fondo C", "account_id": account["id"],
        "contributed": "1000.00", "value": "1000.00", "date": "2025-01-15",
    }).json()
    savings = client.post("/api/investments/savings", json={
        "new_account_name": "Ahorro X", "opened_at": "2025-01-01", "balance": "5000.00",
        "rate_source": "fixed", "fixed_rate": "3.00",
    })
    assert savings.status_code == 201

    report = client.get("/api/investments/reconciliation").json()
    states = {h["display_name"]: h["quality_state"] for h in report["holdings"]}
    assert states["Fondo C"] == "manual"
    assert states["Ahorro X"] == "confirmed"
