import os
import pytest
from fastapi.testclient import TestClient

# Ensure test DB is used
TEST_DB_PATH = "test_auth.db"
os.environ["DATABASE_PATH"] = TEST_DB_PATH

from src.database import init_db
from src.api import app

client = TestClient(app)

@pytest.fixture(autouse=True, scope="module")
def setup_test_db():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    init_db(TEST_DB_PATH)
    yield
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass

def test_register_success():
    resp = client.post("/register", json={"email": "newuser@test.com", "password": "password123"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "newuser@test.com"
    assert "id" in data

def test_register_duplicate_email():
    resp = client.post("/register", json={"email": "newuser@test.com", "password": "password123"})
    assert resp.status_code == 400
    assert "already exists" in resp.json()["detail"].lower()

def test_login_success():
    resp = client.post("/login", json={"email": "newuser@test.com", "password": "password123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["email"] == "newuser@test.com"

def test_login_invalid_password():
    resp = client.post("/login", json={"email": "newuser@test.com", "password": "wrongpassword"})
    assert resp.status_code == 401

def test_get_me():
    # Login first
    login_resp = client.post("/login", json={"email": "newuser@test.com", "password": "password123"})
    token = login_resp.json()["access_token"]

    resp = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "newuser@test.com"

def test_unauthorized_access():
    resp = client.get("/me")
    assert resp.status_code in [401, 403]
