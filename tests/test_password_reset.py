def test_forgot_password_page(client):
    rv = client.get("/forgot-password")
    assert rv.status_code == 200


def test_forgot_password_submit(client):
    rv = client.post("/forgot-password", data={"username": "admin"}, follow_redirects=True)
    assert rv.status_code == 200


def test_forgot_password_nonexistent(client):
    rv = client.post("/forgot-password", data={"username": "nobody"}, follow_redirects=True)
    assert rv.status_code == 200


def test_reset_password_page_with_bad_token(client):
    rv = client.get("/reset-password/badtoken", follow_redirects=True)
    assert rv.status_code == 200
