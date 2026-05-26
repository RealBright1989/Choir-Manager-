import os
import sys
import tempfile

os.environ["DATABASE_URL"] = "sqlite:///" + tempfile.mktemp(suffix=".db").replace("\\", "/")
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["PORT"] = "5000"
os.environ["FLASK_ENV"] = "testing"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        with app.app_context():
            yield c
