def login(client):
    client.post("/login", data={"username": "admin", "password": "admin123"})


def test_reports_page_requires_auth(client):
    rv = client.get("/reports", follow_redirects=True)
    assert rv.status_code == 200


def test_reports_list(client):
    login(client)
    rv = client.get("/reports")
    assert rv.status_code == 200
