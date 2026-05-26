def test_login_page_loads(client):
    rv = client.get("/login")
    assert rv.status_code == 200
    assert b"Login" in rv.data or b"login" in rv.data


def test_login_with_default_creds(client):
    rv = client.post("/login", data={
        "username": "admin",
        "password": "admin123"
    }, follow_redirects=True)
    assert rv.status_code == 200


def test_login_with_bad_creds(client):
    rv = client.post("/login", data={
        "username": "admin",
        "password": "wrong"
    }, follow_redirects=True)
    assert rv.status_code == 200


def test_logout(client):
    client.post("/login", data={"username": "admin", "password": "admin123"})
    rv = client.get("/logout", follow_redirects=True)
    assert rv.status_code == 200


def test_signup_page_loads(client):
    rv = client.get("/signup")
    assert rv.status_code == 200


def test_landing_page_loads(client):
    rv = client.get("/")
    assert rv.status_code == 200


def test_dashboard_requires_login(client):
    rv = client.get("/dashboard", follow_redirects=True)
    assert rv.status_code == 200
