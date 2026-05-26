def test_landing_page(client):
    rv = client.get("/")
    assert rv.status_code == 200
    assert b"Choir" in rv.data or b"choir" in rv.data or b"Eton" in rv.data


def test_join_guidelines(client):
    rv = client.get("/join/guidelines")
    assert rv.status_code == 200


def test_terms_page(client):
    rv = client.get("/terms")
    assert rv.status_code == 200


def test_user_manual_page(client):
    rv = client.get("/user-manual")
    assert rv.status_code == 200
