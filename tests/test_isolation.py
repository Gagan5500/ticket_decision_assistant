import os
import pytest
from fastapi.testclient import TestClient

TEST_DB_PATH = "test_isolation.db"
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

def test_alice_cannot_access_bobs_ticket():
    """
    Demonstrate that multi-tenant authorization prevents Alice from retrieving
    Bob's ticket and vice-versa, fulfilling the core assignment security requirement.
    """
    # 1. Register Alice and log in
    client.post("/register", json={"email": "alice@example.com", "password": "alicepassword"})
    alice_login = client.post("/login", json={"email": "alice@example.com", "password": "alicepassword"})
    assert alice_login.status_code == 200
    alice_token = alice_login.json()["access_token"]
    alice_headers = {"Authorization": f"Bearer {alice_token}"}

    # 2. Register Bob and log in
    client.post("/register", json={"email": "bob@example.com", "password": "bobpassword"})
    bob_login = client.post("/login", json={"email": "bob@example.com", "password": "bobpassword"})
    assert bob_login.status_code == 200
    bob_token = bob_login.json()["access_token"]
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    # 3. Alice creates a ticket
    alice_ticket_resp = client.post(
        "/tickets",
        headers=alice_headers,
        json={"message": "Alice's jacket arrived torn (Order #9901, ₹4,500)."}
    )
    assert alice_ticket_resp.status_code == 201
    alice_ticket_id = alice_ticket_resp.json()["ticket_id"]

    # 4. Bob creates a ticket
    bob_ticket_resp = client.post(
        "/tickets",
        headers=bob_headers,
        json={"message": "Bob wants to return a shirt (Order #7701, ₹900)."}
    )
    assert bob_ticket_resp.status_code == 201
    bob_ticket_id = bob_ticket_resp.json()["ticket_id"]

    # 5. Alice can successfully fetch her own ticket
    alice_fetch_own = client.get(f"/tickets/{alice_ticket_id}", headers=alice_headers)
    assert alice_fetch_own.status_code == 200
    assert alice_fetch_own.json()["ticket_id"] == alice_ticket_id

    # 6. CRITICAL SECURITY TEST: Bob attempts to access Alice's ticket
    # Must be forbidden (403)
    bob_fetch_alice = client.get(f"/tickets/{alice_ticket_id}", headers=bob_headers)
    assert bob_fetch_alice.status_code == 403
    assert "forbidden" in bob_fetch_alice.json()["detail"].lower()

    # 7. CRITICAL SECURITY TEST: Alice attempts to access Bob's ticket
    # Must be forbidden (403)
    alice_fetch_bob = client.get(f"/tickets/{bob_ticket_id}", headers=alice_headers)
    assert alice_fetch_bob.status_code == 403
    assert "forbidden" in alice_fetch_bob.json()["detail"].lower()

    # 8. List endpoint test: Bob's list only contains Bob's tickets
    bob_list = client.get("/tickets", headers=bob_headers)
    assert bob_list.status_code == 200
    bob_tickets = bob_list.json()
    assert len(bob_tickets) == 1
    assert bob_tickets[0]["ticket_id"] == bob_ticket_id
    assert all(t["user_id"] != alice_fetch_own.json()["user_id"] for t in bob_tickets)
