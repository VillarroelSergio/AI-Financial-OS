def test_requests_without_token_rejected_when_token_set(client, monkeypatch):
    monkeypatch.setenv("FINOS_API_TOKEN", "secreto123")
    assert client.get("/api/accounts").status_code == 401
    assert client.get("/health").status_code == 200  # health queda abierto para el launcher
    ok = client.get("/api/accounts", headers={"X-Api-Token": "secreto123"})
    assert ok.status_code == 200


def test_requests_allowed_when_no_token_configured(client, monkeypatch):
    monkeypatch.delenv("FINOS_API_TOKEN", raising=False)
    assert client.get("/api/accounts").status_code == 200
