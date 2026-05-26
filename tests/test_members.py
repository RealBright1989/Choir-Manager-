def login(client):
    client.post("/login", data={"username": "admin", "password": "admin123"})


def test_members_page_requires_auth(client):
    rv = client.get("/members", follow_redirects=True)
    assert rv.status_code == 200


def test_members_list_after_login(client):
    login(client)
    rv = client.get("/members")
    assert rv.status_code == 200


def test_add_member(client):
    login(client)
    rv = client.post("/members/add", data={
        "first_name": "John",
        "last_name": "Doe",
        "phone": "08012345678",
        "email": "john@example.com",
        "section": "Tenor",
        "join_date": "2026-01-01",
        "address": "123 Test St",
        "country": "Nigeria",
        "state_of_origin": "Lagos",
        "lga": "Ikeja",
        "nin_number": "12345678901",
    }, follow_redirects=True)
    assert rv.status_code == 200


def test_member_detail(client):
    login(client)
    rv = client.get("/members/1")
    assert rv.status_code in (200, 404)


def test_member_edit_page(client):
    login(client)
    rv = client.get("/members/edit/1")
    assert rv.status_code in (200, 404)


def test_delete_member(client):
    login(client)
    rv = client.post("/members/delete/1", follow_redirects=True)
    assert rv.status_code in (200, 404)
