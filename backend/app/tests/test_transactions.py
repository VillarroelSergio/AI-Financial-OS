import io


def _import_monefy(client, csv: str) -> None:
    preview = client.post(
        "/api/imports/preview",
        data={"source_type": "monefy"},
        files={"file": ("monefy.csv", io.BytesIO(csv.encode()), "text/csv")},
    ).json()
    client.post(f"/api/imports/{preview['import_batch_id']}/confirm", json={"mapping": preview["mapping"]})


CSV_USD = (
    "﻿date,account,category,amount,currency,converted amount,currency.1,description\n"
    "22/6/2026,Efectivo,Comida,-12.50,USD,-12.50,USD,Café\n"
    "23/6/2026,Efectivo,Salario,2000,USD,2000,USD,Nómina\n"
)


def test_list_transactions_respects_limit_and_offset(client):
    acc = client.post(
        "/api/accounts", json={"name": "Test", "type": "checking", "currency": "EUR"}
    ).json()
    for i in range(5):
        client.post(
            "/api/transactions",
            json={
                "account_id": acc["id"],
                "date": f"2026-03-0{i + 1}",
                "description": f"tx{i}",
                "amount": "-1.00",
                "type": "expense",
            },
        )
    assert len(client.get("/api/transactions?limit=2").json()) == 2
    page2 = client.get("/api/transactions?limit=2&offset=2").json()
    assert len(page2) == 2
    assert page2[0]["description"] != client.get("/api/transactions?limit=2").json()[0]["description"]


def test_transactions_include_account_name_even_if_account_inactive(client):
    _import_monefy(client, CSV_USD)
    accounts = client.get("/api/accounts").json()
    account_id = accounts[0]["id"]
    client.delete(f"/api/accounts/{account_id}")  # soft-delete

    txs = client.get("/api/transactions").json()
    assert txs and all(tx["account_name"] == "Efectivo" for tx in txs)


def test_currency_reassign_preview_and_apply(client, monkeypatch):
    _import_monefy(client, CSV_USD)
    monkeypatch.setattr(
        "app.modules.transactions.routes.create_backup", lambda: {"filename": "test.db"}
    )

    preview = client.post(
        "/api/transactions/currency-reassign",
        json={"from_currency": "USD", "to_currency": "EUR", "preview": True},
    ).json()
    assert preview == {"affected": 2, "applied": False, "from_currency": "USD", "to_currency": "EUR"}

    applied = client.post(
        "/api/transactions/currency-reassign",
        json={"from_currency": "USD", "to_currency": "EUR", "preview": False},
    ).json()
    assert applied["applied"] and applied["affected"] == 2

    txs = client.get("/api/transactions").json()
    assert all(tx["currency"] == "EUR" for tx in txs)


def test_currency_reassign_rejects_invalid_codes(client):
    resp = client.post(
        "/api/transactions/currency-reassign",
        json={"from_currency": "USD", "to_currency": "usd", "preview": True},
    )
    assert resp.status_code == 422


def test_import_confirm_currency_override(client):
    preview = client.post(
        "/api/imports/preview",
        data={"source_type": "monefy"},
        files={"file": ("monefy.csv", io.BytesIO(CSV_USD.encode()), "text/csv")},
    ).json()
    client.post(
        f"/api/imports/{preview['import_batch_id']}/confirm",
        json={"mapping": preview["mapping"], "currency_override": "eur"},
    )
    txs = client.get("/api/transactions").json()
    assert txs and all(tx["currency"] == "EUR" for tx in txs)
