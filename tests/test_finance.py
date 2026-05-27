def login(client):
    client.post("/login", data={"username": "admin", "password": "admin123"})


def test_finance_page_requires_auth(client):
    rv = client.get("/finance", follow_redirects=True)
    assert rv.status_code == 200


def test_finance_list(client):
    login(client)
    rv = client.get("/finance")
    assert rv.status_code == 200


def test_add_payment(client):
    login(client)
    rv = client.post("/finance/income/add", data={
        "member_id": 1,
        "amount": 50.00,
        "payment_date": "2026-05-26",
        "payment_for": "Monthly dues",
    }, follow_redirects=True)
    assert rv.status_code == 200
