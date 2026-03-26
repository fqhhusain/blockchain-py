"""
tests/functional/test_api_transactions.py
-----------------------------------------
Functional tests for POST /transactions/new using Flask's built-in test client.
No real ports are opened; the WSGI app is called in-process.
"""
import pytest

from app import create_app
from core.transaction import Transaction
from core.wallet import generate_keys, public_key_to_address


@pytest.fixture()
def client():
    app = create_app(port=5000)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _make_payload(sender=None, receiver="Bob", amount=5.0) -> dict:
    priv, pub = generate_keys()
    sender_addr = sender or public_key_to_address(pub)
    tx = Transaction(sender_addr, receiver, amount, public_key=pub)
    tx.sign_transaction(priv)
    return tx.to_full_dict()


# ── Happy path ────────────────────────────────────────────────────────
class TestNewTransactionSuccess:
    def test_returns_201(self, client):
        resp = client.post("/transactions/new", json=_make_payload())
        assert resp.status_code == 201

    def test_response_has_message(self, client):
        resp = client.post("/transactions/new", json=_make_payload())
        data = resp.get_json()
        assert "message" in data

    def test_pending_count_increases(self, client):
        client.post("/transactions/new", json=_make_payload())
        resp = client.post("/transactions/new", json=_make_payload())
        data = resp.get_json()
        assert data["pending_count"] == 2


# ── Validation errors ─────────────────────────────────────────────────
class TestNewTransactionValidation:
    def test_missing_fields_returns_400(self, client):
        resp = client.post("/transactions/new", json={"sender": "Alice"})
        assert resp.status_code == 400

    def test_missing_fields_lists_missing_keys(self, client):
        resp = client.post("/transactions/new", json={"sender": "Alice"})
        data = resp.get_json()
        assert "error" in data
        assert "details" in data["error"]
        assert "missing" in data["error"]["details"]

    def test_invalid_signature_returns_400(self, client):
        payload = _make_payload()
        payload["signature"] = "00" * 32  # wrong signature
        resp = client.post("/transactions/new", json=payload)
        assert resp.status_code == 400

    def test_tampered_amount_returns_400(self, client):
        """Changing amount after signing invalidates the signature."""
        payload = _make_payload(amount=5.0)
        payload["amount"] = 9999.0  # tamper after signing
        resp = client.post("/transactions/new", json=payload)
        assert resp.status_code == 400

    def test_tampered_receiver_returns_400(self, client):
        payload = _make_payload()
        payload["receiver"] = "Eve"
        resp = client.post("/transactions/new", json=payload)
        assert resp.status_code == 400

    def test_sender_not_owned_by_public_key_returns_400(self, client):
        payload = _make_payload()
        payload["sender"] = "Alice"
        resp = client.post("/transactions/new", json=payload)
        assert resp.status_code == 400

    def test_zero_amount_returns_400(self, client):
        payload = _make_payload()
        payload["amount"] = 0
        resp = client.post("/transactions/new", json=payload)
        assert resp.status_code == 400

    def test_negative_amount_returns_400(self, client):
        payload = _make_payload()
        payload["amount"] = -1
        resp = client.post("/transactions/new", json=payload)
        assert resp.status_code == 400

    def test_empty_body_returns_400(self, client):
        resp = client.post("/transactions/new", json={})
        assert resp.status_code == 400

    def test_duplicate_transaction_returns_400(self, client):
        payload = _make_payload()
        first = client.post("/transactions/new", json=payload)
        assert first.status_code == 201

        second = client.post("/transactions/new", json=payload)
        assert second.status_code == 400