from decimal import Decimal


def test_goal_crud(client):
    created = client.post(
        "/api/goals",
        json={"name": "Fondo de emergencia", "type": "emergency_fund", "target_amount": "12000.00", "current_amount": "1500.00", "target_date": "2027-06-01", "monthly_contribution": "350.00", "priority": "high"},
    )
    assert created.status_code == 201
    goal = created.json()
    assert Decimal(goal["target_amount"]) == Decimal("12000.00")
    assert [item["id"] for item in client.get("/api/goals").json()] == [goal["id"]]
    updated = client.patch(f"/api/goals/{goal['id']}", json={"current_amount": "2000.00", "status": "paused"})
    assert updated.status_code == 200
    assert updated.json()["current_amount"] == "2000.00"
    assert updated.json()["status"] == "paused"
    deleted = client.delete(f"/api/goals/{goal['id']}")
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert client.get("/api/goals").json() == []


def test_goal_validation_and_missing_goal(client):
    assert client.post("/api/goals", json={"name": "", "target_amount": "0"}).status_code == 422
    assert client.patch("/api/goals/missing", json={"status": "paused"}).status_code == 404
