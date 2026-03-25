"""
tests/functional/test_api_chain.py
------------------------------------
Functional tests for GET /chain, GET /chain/validate,
GET /balance/<address>, GET /wallet/new endpoints.
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


@pytest.fixture()
def mined_client(client):
    """Client with one mined block containing a signed transaction."""
    priv, pub = generate_keys()
    tx = Transaction(public_key_to_address(pub), "Bob", 10.0, public_key=pub)
    tx.sign_transaction(priv)
    client.post("/transactions/new", json=tx.to_full_dict())
    client.post("/mine", json={"miner_address": "MinerA"})
    return client


# ── GET /chain ────────────────────────────────────────────────────────
class TestGetChain:
    def test_returns_200(self, client):
        assert client.get("/chain").status_code == 200

    def test_chain_has_genesis(self, client):
        data = client.get("/chain").get_json()
        assert data["length"] == 1
        assert data["chain"][0]["index"] == 0
        assert data["chain"][0]["previous_hash"] == "0"

    def test_chain_grows_after_mine(self, mined_client):
        data = mined_client.get("/chain").get_json()
        assert data["length"] == 2

    def test_chain_blocks_have_required_keys(self, mined_client):
        data = mined_client.get("/chain").get_json()
        block = data["chain"][1]
        required = {"index", "transactions", "previous_hash", "timestamp", "nonce", "hash"}
        assert required.issubset(block.keys())

    def test_transactions_stored_in_chain(self, mined_client):
        data = mined_client.get("/chain").get_json()
        block = data["chain"][1]
        senders = {t["sender"] for t in block["transactions"]}
        assert "NETWORK" in senders
        assert len(senders) >= 2

    def test_signatures_stored_in_chain(self, mined_client):
        data = mined_client.get("/chain").get_json()
        block = data["chain"][1]
        user_txs = [t for t in block["transactions"] if t["sender"] != "NETWORK"]
        for tx in user_txs:
            assert tx["signature"] is not None
            assert tx["public_key"] is not None


# ── GET /chain/validate ───────────────────────────────────────────────
class TestValidateChain:
    def test_fresh_chain_is_valid(self, client):
        data = client.get("/chain/validate").get_json()
        assert data["valid"] is True

    def test_mined_chain_is_valid(self, mined_client):
        data = mined_client.get("/chain/validate").get_json()
        assert data["valid"] is True

    def test_validate_returns_length(self, mined_client):
        data = mined_client.get("/chain/validate").get_json()
        assert data["length"] == 2


# ── GET /balance/<address> ────────────────────────────────────────────
class TestGetBalance:
    def test_unknown_address_is_zero(self, client):
        data = client.get("/balance/Nobody").get_json()
        assert data["balance"] == 0.0

    def test_receiver_gets_balance(self, mined_client):
        data = mined_client.get("/balance/Bob").get_json()
        assert data["balance"] == 10.0

    def test_balance_response_has_address(self, client):
        data = client.get("/balance/Alice").get_json()
        assert data["address"] == "Alice"


# ── GET /wallet/new ───────────────────────────────────────────────────
class TestWalletNew:
    def test_returns_200(self, client):
        assert client.get("/wallet/new").status_code == 200

    def test_returns_private_and_public_key(self, client):
        data = client.get("/wallet/new").get_json()
        assert "private_key" in data
        assert "public_key" in data

    def test_private_key_is_pem(self, client):
        data = client.get("/wallet/new").get_json()
        assert "PRIVATE KEY" in data["private_key"]

    def test_public_key_is_pem(self, client):
        data = client.get("/wallet/new").get_json()
        assert "PUBLIC KEY" in data["public_key"]

    def test_keys_are_unique_per_call(self, client):
        d1 = client.get("/wallet/new").get_json()
        d2 = client.get("/wallet/new").get_json()
        assert d1["private_key"] != d2["private_key"]
        assert d1["public_key"] != d2["public_key"]

    def test_generated_key_can_sign_valid_tx(self, client):
        """Key from /wallet/new must work end-to-end in /transactions/new."""
        wallet = client.get("/wallet/new").get_json()
        priv, pub = wallet["private_key"], wallet["public_key"]
        tx = Transaction(wallet["address"], "Bob", 5.0, public_key=pub)
        tx.sign_transaction(priv)
        resp = client.post("/transactions/new", json=tx.to_full_dict())
        assert resp.status_code == 201