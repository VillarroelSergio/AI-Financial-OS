"""Regresiones INS-1 (integridad de cálculo/formato) e INS-2 (taxonomía/dedupe).

Cifras de las capturas: ingresos 3915,00 / gastos 1501,25 / ahorro 2413,75 → tasa 61,7%.
"""
from decimal import Decimal

from app.modules.insights.formatting import fmt_eur, fmt_pct, round_dec, savings_rate_dec
from app.modules.insights.schemas import InsightOut, InsightSeverity, InsightType
from app.modules.insights.service import _dedupe


def _seed_month(client, period="2026-06"):
    acc = client.post("/api/accounts", json={"name": "Banco", "type": "bank", "currency": "EUR", "current_balance": "2413.75"})
    account_id = acc.json()["id"]
    client.post("/api/transactions", json={"account_id": account_id, "date": f"{period}-01", "description": "Sueldo", "amount": "3915.00", "type": "income"})
    client.post("/api/transactions", json={"account_id": account_id, "date": f"{period}-10", "description": "Gastos", "amount": "-1501.25", "type": "expense"})
    return account_id


# ---- INS-1: cifra única y determinista ----

def test_savings_rate_single_figure():
    assert savings_rate_dec(Decimal("3915.00"), Decimal("1501.25")) == Decimal("61.7")
    assert round_dec("61.65", 1) == Decimal("61.7")  # half-up, no banker's rounding


def test_es_formatting():
    assert fmt_pct(Decimal("61.7")) == "61,7 %"
    assert fmt_eur(Decimal("2413.75")) == "2.413,75 €"
    assert fmt_eur(Decimal("42100")) == "42.100,00 €"


def test_review_and_card_agree_on_savings_rate(client):
    _seed_month(client)
    review = client.get("/api/insights/monthly-review?period=2026-06").json()
    assert review["savings_rate"] == 61.7
    assert "61,7 %" in review["summary"]  # copy en es-ES, misma cifra (INS-B1/F1)

    ins = client.get("/api/insights?period=2026-06&limit=50&include_dismissed=true").json()["insights"]
    card = next(i for i in ins if i["type"] == "savings_rate")
    assert card["primary_metric"]["value"] == 61.7           # métrica == review
    assert "61,7 %" in card["summary"]                        # copy == métrica (INS-B2)


# ---- INS-2: taxonomía y deduplicación ----

def test_savings_rate_is_context(client):
    _seed_month(client)
    ins = client.get("/api/insights?period=2026-06&limit=50&include_dismissed=true").json()["insights"]
    card = next(i for i in ins if i["type"] == "savings_rate")
    assert card["insight_class"] == "context"  # reclasificada (INS-B6)


def test_dedupe_keeps_highest_priority():
    a = InsightOut(id="a", type=InsightType.investment_allocation, dedupe_key="k",
                   severity=InsightSeverity.info, title="Sin precio", summary="", period="2026-06",
                   impact_area="inversiones", confidence=0.6, priority=40.0, data_status="partial")
    b = InsightOut(id="b", type=InsightType.data_quality, dedupe_key="k",
                   severity=InsightSeverity.info, title="Sin precio", summary="", period="2026-06",
                   impact_area="calidad", confidence=0.6, priority=55.0, data_status="partial")
    out = _dedupe([a, b])
    assert len(out) == 1 and out[0].id == "b"  # conserva mayor prioridad (INS-B3)


def test_no_duplicate_dedupe_keys_in_response(client):
    _seed_month(client)
    ins = client.get("/api/insights?period=2026-06&limit=50&include_dismissed=true").json()["insights"]
    keys = [i["dedupe_key"] for i in ins if i["dedupe_key"]]
    assert len(keys) == len(set(keys))  # cero duplicados por clave canónica
