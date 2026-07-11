import io

from app.modules.imports.auto_categorizer import auto_category

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


def _import_csv(client, filename, csv_text, mapping):
    # mapping explícito: el detector genérico solo mapea date + 2ª columna.
    preview = client.post(
        "/api/imports/preview",
        files={"file": (filename, csv_text.encode(), "text/csv")},
    )
    batch_id = preview.json()["import_batch_id"]
    confirm = client.post(f"/api/imports/{batch_id}/confirm", json={"mapping": mapping})
    return confirm.json()


_MIX_MAPPING = {"date": "date", "amount": "amount", "account": "account", "description": "description"}


def test_opposite_amounts_without_transfer_hint_stay_income_expense(client):
    # Cuenta A: nómina. Cuenta B: alquiler del mismo importe. NO es un traspaso.
    result = _import_csv(
        client,
        "mix.csv",
        "date,amount,account,description\n"
        "01/03/2026,1200.00,Banco A,Nomina empresa SL\n"
        "02/03/2026,-1200.00,Banco B,Alquiler marzo piso\n",
        _MIX_MAPPING,
    )
    assert result["transfers_detected"] == 0


def test_opposite_amounts_with_transfer_hint_are_paired(client):
    result = _import_csv(
        client,
        "traspaso.csv",
        "date,amount,account,description\n"
        "01/03/2026,-500.00,Banco A,Traspaso a Revolut\n"
        "01/03/2026,500.00,Revolut,Recarga desde Banco A\n",
        _MIX_MAPPING,
    )
    assert result["transfers_detected"] == 1


def test_manual_recategorization_teaches_importer(client):
    mapping = {"date": "date", "amount": "amount", "description": "description"}
    csv = "date,amount,description\n01/03/2026,-25.00,GIMNASIO MISTERIOSO SL\n"
    _import_csv(client, "gym1.csv", csv, mapping)
    txs = client.get("/api/transactions?source=csv").json()
    tx = next(t for t in txs if "MISTERIOSO" in t["description"])
    assert tx["category_id"] is None  # ninguna keyword lo conoce

    deportes = next(c for c in client.get("/api/categories").json() if c["name"] == "Deportes")
    client.patch(f"/api/transactions/{tx['id']}", json={"category_id": deportes["id"]})

    # Mismo comercio en un archivo nuevo (fecha distinta para no ser duplicado)
    csv2 = "date,amount,description\n05/04/2026,-25.00,GIMNASIO MISTERIOSO SL\n"
    _import_csv(client, "gym2.csv", csv2, mapping)
    txs = client.get("/api/transactions?source=csv").json()
    learned = [t for t in txs if "MISTERIOSO" in t["description"]]
    assert any(t["category_id"] == deportes["id"] for t in learned if t["date"] == "2026-04-05")


def test_preview_warns_when_file_already_imported(client):
    csv = "date,amount,description\n01/03/2026,-10.00,Mercadona\n"
    files = {"file": ("compra.csv", csv.encode(), "text/csv")}
    first = client.post("/api/imports/preview", files=files).json()
    client.post(f"/api/imports/{first['import_batch_id']}/confirm", json={})

    second = client.post("/api/imports/preview", files=files).json()
    assert second["already_imported_at"] is not None

    fresh = client.post(
        "/api/imports/preview",
        files={"file": ("otro.csv", csv.replace("Mercadona", "Lidl").encode(), "text/csv")},
    ).json()
    assert fresh["already_imported_at"] is None


def test_short_keywords_require_exact_token():
    # Falsos positivos actuales por prefijo
    assert auto_category("Centro de diagnostico medico") != "Alimentación"
    assert auto_category("Sumario judicial") != "Alimentación"
    assert auto_category("Hotel Barcelona Centro") == "Ocio"  # "hotel" gana, no "bar"
    assert auto_category("Barbería Paco") != "Restaurante"
    # Los aciertos existentes no se rompen
    assert auto_category("SUPERMERCADOS DIA MADRID") == "Alimentación"
    assert auto_category("Bar Manolo") == "Restaurante"
    assert auto_category("Cinesur Nervion") == "Ocio"
    assert auto_category("Pizzeria Napoli") == "Restaurante"


def test_rollback_removes_household_bills(client):
    csv = (
        "date,amount,description\n"
        "01/03/2026,-55.30,Adeudo recibo Iberdrola electricidad\n"
    )
    preview = client.post(
        "/api/imports/preview",
        files={"file": ("recibos.csv", csv.encode(), "text/csv")},
    )
    assert preview.status_code == 200
    batch_id = preview.json()["import_batch_id"]

    mapping = {"date": "date", "amount": "amount", "description": "description"}
    confirm = client.post(f"/api/imports/{batch_id}/confirm", json={"mapping": mapping})
    assert confirm.status_code == 200
    assert confirm.json()["bills_created"] == 1
    assert len(client.get("/api/household-bills").json()) == 1

    rollback = client.post(f"/api/imports/{batch_id}/rollback")
    assert rollback.status_code == 200
    assert client.get("/api/household-bills").json() == []


_CAFE_HEADER = (
    "﻿date,account,category,amount,currency,converted amount,currency.1,description\n"
)
_CAFE_ROW = "01/03/2026,Efectivo,Comida,-1.50,EUR,-1.50,EUR,Cafeteria Sol\n"


def _preview_monefy(client, filename, csv_text):
    return client.post(
        "/api/imports/preview",
        data={"source_type": "monefy"},
        files={"file": (filename, csv_text.encode(), "text/csv")},
    ).json()


def test_repeated_identical_rows_import_both(client):
    # Dos cafés idénticos el mismo día son dos movimientos reales, no un duplicado.
    two = _CAFE_HEADER + _CAFE_ROW + _CAFE_ROW
    preview = _preview_monefy(client, "cafes.csv", two)
    assert preview["rows_valid"] == 2
    confirm = client.post(
        f"/api/imports/{preview['import_batch_id']}/confirm",
        json={"mapping": preview["mapping"]},
    )
    assert confirm.json()["rows_imported"] == 2

    # Reimportar el mismo archivo: ambas ocurrencias ya existen → 2 duplicados.
    again = _preview_monefy(client, "cafes2.csv", two)
    assert sum(1 for r in again["preview_rows"] if r["status"] == "duplicate") == 2

    # Un tercer café idéntico es nuevo: la 3ª ocurrencia no colisiona con las 2 previas.
    three = two + _CAFE_ROW
    third = _preview_monefy(client, "cafes3.csv", three)
    statuses = [r["status"] for r in third["preview_rows"]]
    assert statuses.count("duplicate") == 2
    assert statuses.count("valid") == 1


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
