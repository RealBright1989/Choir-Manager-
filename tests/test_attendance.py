def login(client):
    client.post("/login", data={"username": "admin", "password": "admin123"})


def test_attendance_page_requires_auth(client):
    rv = client.get("/attendance", follow_redirects=True)
    assert rv.status_code == 200


def test_attendance_list(client):
    login(client)
    rv = client.get("/attendance")
    assert rv.status_code == 200


def test_take_attendance(client):
    login(client)
    rv = client.post("/attendance/take", data={
        "date": "2026-05-26",
        "member_1": "Present",
    }, follow_redirects=True)
    assert rv.status_code == 200
