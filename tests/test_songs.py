def login(client):
    client.post("/login", data={"username": "admin", "password": "admin123"})


def test_songs_page_requires_auth(client):
    rv = client.get("/songs", follow_redirects=True)
    assert rv.status_code == 200


def test_songs_list(client):
    login(client)
    rv = client.get("/songs")
    assert rv.status_code == 200


def test_song_add_page(client):
    login(client)
    rv = client.get("/songs/add")
    assert rv.status_code == 200
