def test_household_bill_crud_and_summary(client):
    payloads = [
        {
            "provider": "Iberdrola",
            "service_type": "electricity",
            "period_start": "2026-04-01",
            "period_end": "2026-04-30",
            "amount": "80.00",
            "currency": "EUR",
            "is_recurring": True,
        },
        {
            "provider": "Iberdrola",
            "service_type": "electricity",
            "period_start": "2026-05-01",
            "period_end": "2026-05-31",
            "amount": "110.00",
            "currency": "EUR",
            "is_recurring": True,
        },
    ]
    created_ids = []
    for payload in payloads:
        resp = client.post("/api/household-bills", json=payload)
        assert resp.status_code == 201
        created_ids.append(resp.json()["id"])

    list_resp = client.get("/api/household-bills?service_type=electricity")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 2

    summary_resp = client.get("/api/household-bills/summary")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["total_monthly_estimate"] == 110.0
    assert summary["items"][0]["provider"] == "Iberdrola"
    assert summary["items"][0]["change_pct"] == 37.5
    assert summary["items"][0]["anomaly"] is True

    update_resp = client.put(f"/api/household-bills/{created_ids[1]}", json={"amount": "95.00"})
    assert update_resp.status_code == 200
    assert update_resp.json()["amount"] == "95.00"

    assert client.delete(f"/api/household-bills/{created_ids[0]}").status_code == 204
