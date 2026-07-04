def test_purge_inactive_removes_only_unreferenced(client):
    keep = client.post("/api/accounts", json={"name": "BBVA", "type": "bank"}).json()
    orphan = client.post("/api/accounts", json={"name": "Duplicada", "type": "broker"}).json()
    referenced = client.post("/api/accounts", json={"name": "Efectivo", "type": "cash"}).json()
    client.post("/api/transactions", json={
        "account_id": referenced["id"], "date": "2026-06-01",
        "description": "Compra", "amount": "-5.00", "type": "expense",
    })
    client.delete(f"/api/accounts/{orphan['id']}")
    client.delete(f"/api/accounts/{referenced['id']}")

    preview = client.post("/api/accounts/purge-inactive?preview=true").json()
    assert preview == {"affected": 1, "names": ["Duplicada"], "applied": False}

    result = client.post("/api/accounts/purge-inactive?preview=false").json()
    assert result["applied"] and result["affected"] == 1

    # La cuenta activa y la referenciada siguen existiendo
    active_ids = {a["id"] for a in client.get("/api/accounts").json()}
    assert keep["id"] in active_ids
    txs = client.get("/api/transactions").json()
    assert txs[0]["account_name"] == "Efectivo"
