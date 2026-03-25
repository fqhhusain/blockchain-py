"""
tests/functional/test_api_mine.py
----------------------------------
Functional tests for POST /mine using Flask's built-in test client.
"""
import pytest

from app import create_app
from core.transaction import Transaction
from core.wallet import generate_keys, public_key_to_address
from config import MINING_REWARD


@pytest.fixture()
def client():
    app = create_app(port=5000)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _add_signed_tx(client, sender=None, receiver="Bob", amount=5.0):
    priv, pub = generate_keys()
    sender_addr = sender or public_key_to_address(pub)
    tx = Transaction(sender_addr, receiver, amount, public_key=pub)
    tx.sign_transaction(priv)
    client.post("/transactions/new", json=tx.to_full_dict())


# ── Happy path ────────────────────────────────────────────────────────
class TestMineSuccess:
    def test_mine_returns_200(self, client):
        resp = client.post("/mine", json={"miner_address": "MinerA"})
        assert resp.status_code == 200

    def test_mine_response_has_block(self, client):
        resp = client.post("/mine", json={"miner_address": "MinerA"})
        data = resp.get_json()
        assert "block" in data

    def test_mine_response_has_miner(self, client):
        resp = client.post("/mine", json={"miner_address": "MinerA"})
        data = resp.get_json()
        assert data["miner"] == "MinerA"

    def test_chain_grows_after_mine(self, client):
        resp = client.post("/mine", json={"miner_address": "MinerA"})
        data = resp.get_json()
        assert data["chain_length"] == 2  # genesis + 1 mined

    def test_mine_multiple_times_grows_chain(self, client):
        client.post("/mine", json={"miner_address": "MinerA"})
        resp = client.post("/mine", json={"miner_address": "MinerA"})
        data = resp.get_json()
        assert data["chain_length"] == 3

    def test_mine_with_pending_transactions(self, client):
        _add_signed_tx(client, receiver="Bob", amount=10.0)
        _add_signed_tx(client, receiver="Charlie", amount=3.0)
        resp = client.post("/mine", json={"miner_address": "MinerA"})
        assert resp.status_code == 200
        data = resp.get_json()
        # block should have 2 user txs + 1 reward = 3 total
        assert len(data["block"]["transactions"]) == 3


# ── Reward transaction ─────────────────────────────────────────────────
class TestMiningReward:
    def test_reward_tx_in_block(self, client):
        resp = client.post("/mine", json={"miner_address": "MinerA"})
        block = resp.get_json()["block"]
        reward_txs = [
            t for t in block["transactions"]
            if t["sender"] == "NETWORK" and t["receiver"] == "MinerA"
        ]
        assert len(reward_txs) == 1

    def test_reward_amount_correct(self, client):
        resp = client.post("/mine", json={"miner_address": "MinerA"})
        block = resp.get_json()["block"]
        reward_tx = next(
            t for t in block["transactions"] if t["sender"] == "NETWORK"
        )
        assert reward_tx["amount"] == MINING_REWARD

    def test_miner_balance_after_mine(self, client):
        client.post("/mine", json={"miner_address": "MinerA"})
        resp = client.get("/balance/MinerA")
        data = resp.get_json()
        assert data["balance"] == MINING_REWARD

    def test_anonymous_miner_gets_reward(self, client):
        resp = client.post("/mine", json={})
        data = resp.get_json()
        assert data["miner"] == "anonymous"
        block = data["block"]
        reward_txs = [
            t for t in block["transactions"]
            if t["sender"] == "NETWORK" and t["receiver"] == "anonymous"
        ]
        assert len(reward_txs) == 1

    def test_multiple_mines_accumulate_rewards(self, client):
        client.post("/mine", json={"miner_address": "MinerA"})
        client.post("/mine", json={"miner_address": "MinerA"})
        resp = client.get("/balance/MinerA")
        data = resp.get_json()
        assert data["balance"] == MINING_REWARD * 2


# ── Chain integrity after mining ───────────────────────────────────────
class TestChainAfterMine:
    def test_chain_valid_after_mine(self, client):
        _add_signed_tx(client)
        client.post("/mine", json={"miner_address": "MinerA"})
        resp = client.get("/chain/validate")
        assert resp.get_json()["valid"] is True

    def test_pending_pool_cleared_after_mine(self, client):
        _add_signed_tx(client)
        client.post("/mine", json={"miner_address": "MinerA"})
        # Adding a new tx should reset pending_count to 1
        priv, pub = generate_keys()
        tx = Transaction(public_key_to_address(pub), "B", 1.0, public_key=pub)
        tx.sign_transaction(priv)
        resp = client.post("/transactions/new", json=tx.to_full_dict())
        assert resp.get_json()["pending_count"] == 1