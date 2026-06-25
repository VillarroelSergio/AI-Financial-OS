import io

CSV = (
    "\ufeffdate,account,category,amount,currency,converted amount,currency.1,description\n"
    "22/6/2026,Efectivo,Comida,-12.50,EUR,-12.50,EUR,Café\n"
    "23/6/2026,Banco,Salario,2000,EUR,2000,EUR,Nómina\n"
)


def test_monefy_preview_confirm_duplicate_and_rollback(client):
    response = client.post(
        "/api/imports/preview",
        data={"source_type": "monefy"},
        files={"file": ("monefy.csv", io.BytesIO(CSV.encode()), "text/csv")},
    )
    assert response.status_code == 200
    preview = response.json()
    assert preview["rows_total"] == 2
    assert preview["preview_rows"][0]["date"] == "2026-06-22"
    batch_id = preview["import_batch_id"]
    assert (
        client.post(
            f"/api/imports/{batch_id}/confirm", json={"mapping": preview["mapping"]}
        ).json()["rows_imported"]
        == 2
    )
    second = client.post(
        "/api/imports/preview",
        data={"source_type": "monefy"},
        files={"file": ("again.csv", CSV.encode(), "text/csv")},
    ).json()
    assert all(row["status"] == "duplicate" for row in second["preview_rows"])
    assert client.post(f"/api/imports/{batch_id}/rollback").json()["rows_removed"] == 2


def test_invalid_rows_are_reported(client):
    bad = "date,amount,currency\n99/99/2026,abc,EURO\n"
    response = client.post(
        "/api/imports/preview",
        data={"source_type": "monefy"},
        files={"file": ("bad.csv", bad.encode(), "text/csv")},
    )
    assert response.status_code == 200
    assert response.json()["rows_invalid"] == 1


def test_duplicate_currency_header_is_normalized(client):
    csv_with_duplicate_header = (
        "date,account,category,amount,currency,converted amount,currency,description\n"
        "4/12/2023,Efectivo,Salario,1828,USD,1828,USD,\n"
    )
    response = client.post(
        "/api/imports/preview",
        data={"source_type": "monefy"},
        files={"file": ("monefy.csv", csv_with_duplicate_header.encode(), "text/csv")},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["columns"].count("currency") == 1
    assert "currency.1" in result["columns"]
    assert result["preview_rows"][0]["converted_currency"] == "USD"
