"""
tests/integration/test_multi_node.py
--------------------------------------
Integration test simulating a 3-node blockchain network entirely in-process.
No real HTTP ports are opened; network calls are intercepted via mocking.

Scenarios covered:
  1. Mine on Node A → sync to Node B and Node C
  2. Concurrent mining on two nodes → consensus picks the longer chain
  3. Transaction broadcast across all nodes
  4. Digital signature validation during sync
"""
import json
import pytest
from unittest.mock import patch, call

from app import create_app
from core.transaction import Transaction
from core.wallet import generate_keys, public_key_to_address
from config import MINING_REWARD


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture()
def three_nodes():
    """Three independent Flask test clients (nodes A, B, C)."""
    apps = [create_app(port=5000 + i) for i in range(3)]
    for app in apps:
        app.config["TESTING"] = True

    # Avoid manual __enter__/__exit__ juggling across multiple clients.
    # Flask 3.x context handling is stricter and can raise context pop errors.
    clients = [app.test_client() for app in apps]
    yield clients, apps


@pytest.fixture()
def linked_three_nodes(three_nodes):
    """Three nodes with full peer connections (each knows the other two)."""
    clients, apps = three_nodes
    ca, cb, cc = clients

    # Register full mesh of peers
    ca.post("/nodes/register", json={"nodes": ["localhost:5001", "localhost:5002"]})
    cb.post("/nodes/register", json={"nodes": ["localhost:5000", "localhost:5002"]})
    cc.post("/nodes/register", json={"nodes": ["localhost:5000", "localhost:5001"]})

    return ca, cb, cc, apps


def _signed_tx(receiver="Bob", amount=5.0) -> dict:
    priv, pub = generate_keys()
    tx = Transaction(public_key_to_address(pub), receiver, amount, public_key=pub)
    tx.sign_transaction(priv)
    return tx.to_full_dict()


# ── Scenario 1: Mine on A, sync B and C ───────────────────────────────

class TestMineSyncThreeNodes:
    def test_all_nodes_start_with_genesis(self, linked_three_nodes):
        ca, cb, cc, _ = linked_three_nodes
        for client in (ca, cb, cc):
            data = client.get("/chain").get_json()
            assert data["length"] == 1

    def test_sync_after_mine_on_a(self, linked_three_nodes):
        """After mining on A, B and C resolve and adopt A's chain."""
        ca, cb, cc, _ = linked_three_nodes

        # Add a transaction and mine on A
        ca.post("/transactions/new", json=_signed_tx("Bob", 10.0))
        ca.post("/mine", json={"miner_address": "MinerA"})
        chain_a = ca.get("/chain").get_json()
        assert chain_a["length"] == 2

        # Simulate B and C calling /nodes/resolve and fetching A's chain
        with patch("network.consensus.fetch_chain") as mock_fetch:
            mock_fetch.return_value = chain_a

            resp_b = cb.get("/nodes/resolve").get_json()
            assert resp_b["replaced"] is True
            assert resp_b["chain"]["length"] == 2

            resp_c = cc.get("/nodes/resolve").get_json()
            assert resp_c["replaced"] is True
            assert resp_c["chain"]["length"] == 2

    def test_reward_visible_after_sync(self, linked_three_nodes):
        """MinerA's reward should be present on B's chain after sync."""
        ca, cb, cc, _ = linked_three_nodes

        ca.post("/mine", json={"miner_address": "MinerA"})
        chain_a = ca.get("/chain").get_json()

        with patch("network.consensus.fetch_chain", return_value=chain_a):
            cb.get("/nodes/resolve")

        synced_chain = cb.get("/chain").get_json()
        block = synced_chain["chain"][1]
        reward_txs = [
            t for t in block["transactions"]
            if t["sender"] == "NETWORK" and t["receiver"] == "MinerA"
        ]
        assert len(reward_txs) == 1
        assert reward_txs[0]["amount"] == MINING_REWARD


# ── Scenario 2: Concurrent mining → consensus ─────────────────────────

class TestConcurrentMiningConsensus:
    def test_longer_chain_wins(self, linked_three_nodes):
        """Node A mines 3 blocks, Node B mines 1 block → A's chain wins."""
        ca, cb, cc, _ = linked_three_nodes

        # A mines 3 blocks
        for _ in range(3):
            ca.post("/mine", json={"miner_address": "MinerA"})
        chain_a = ca.get("/chain").get_json()
        assert chain_a["length"] == 4

        # B mines 1 block
        cb.post("/mine", json={"miner_address": "MinerB"})
        chain_b = cb.get("/chain").get_json()
        assert chain_b["length"] == 2

        # C resolves: when it fetches both peers, it should get A's chain
        def fetch_side_effect(peer):
            if "5000" in peer:
                return chain_a
            if "5001" in peer:
                return chain_b
            return None

        with patch("network.consensus.fetch_chain", side_effect=fetch_side_effect):
            resp = cc.get("/nodes/resolve").get_json()

        assert resp["replaced"] is True
        assert resp["chain"]["length"] == 4

    def test_valid_chain_required_for_replacement(self, linked_three_nodes):
        """A tampered chain must not replace the local chain during consensus."""
        ca, cb, cc, _ = linked_three_nodes

        ca.post("/mine", json={"miner_address": "MinerA"})
        chain_a = ca.get("/chain").get_json()

        # Tamper with the chain data before returning it to the resolver
        tampered = json.loads(json.dumps(chain_a))
        tampered["chain"][1]["transactions"][0]["amount"] = 999999

        with patch("network.consensus.fetch_chain", return_value=tampered):
            resp = cc.get("/nodes/resolve").get_json()

        # C should NOT replace its chain with the invalid one
        assert resp["replaced"] is False


# ── Scenario 3: Transaction broadcast ────────────────────────────────

class TestTransactionBroadcast:
    def test_valid_tx_accepted_by_all_nodes(self, linked_three_nodes):
        """A signed transaction should be accepted by every node independently."""
        ca, cb, cc, _ = linked_three_nodes
        tx = _signed_tx("Bob", 20.0)
        for client in (ca, cb, cc):
            resp = client.post("/transactions/new", json=tx)
            assert resp.status_code == 201

    def test_tampered_tx_rejected_by_all_nodes(self, linked_three_nodes):
        """A tampered transaction (bad signature) must be rejected everywhere."""
        ca, cb, cc, _ = linked_three_nodes
        tx = _signed_tx("Bob", 5.0)
        tx["amount"] = 9999.0  # tamper after signing

        for client in (ca, cb, cc):
            resp = client.post("/transactions/new", json=tx)
            assert resp.status_code == 400


# ── Scenario 4: Digital signature validation during sync ─────────────

class TestSignatureValidationDuringSync:
    def test_signed_tx_survives_chain_roundtrip(self, linked_three_nodes):
        """Transaction signatures remain valid after chain serialisation/deserialisation."""
        ca, cb, cc, _ = linked_three_nodes

        tx = _signed_tx("Bob", 7.0)
        ca.post("/transactions/new", json=tx)
        ca.post("/mine", json={"miner_address": "MinerA"})

        chain_a = ca.get("/chain").get_json()

        # Validate the chain on A
        validate_resp = ca.get("/chain/validate").get_json()
        assert validate_resp["valid"] is True

        # After B syncs, chain validation must still pass
        with patch("network.consensus.fetch_chain", return_value=chain_a):
            cb.get("/nodes/resolve")

        validate_b = cb.get("/chain/validate").get_json()
        assert validate_b["valid"] is True

    def test_three_nodes_full_scenario(self, linked_three_nodes):
        """
        Full end-to-end integration:
        1. Alice signs & submits a tx to Node A
        2. Node A mines the block
        3. Nodes B and C sync from Node A
        4. All three nodes validate their chain
        5. All three see Alice's transaction in the chain
        """
        ca, cb, cc, _ = linked_three_nodes

        # Step 1 & 2: tx + mine on A
        tx = _signed_tx("Bob", 15.0)
        ca.post("/transactions/new", json=tx)
        ca.post("/mine", json={"miner_address": "MinerA"})
        chain_a = ca.get("/chain").get_json()
        assert chain_a["length"] == 2

        # Step 3: B and C sync
        with patch("network.consensus.fetch_chain", return_value=chain_a):
            cb.get("/nodes/resolve")
            cc.get("/nodes/resolve")

        # Step 4: All nodes' chains are valid
        for client in (ca, cb, cc):
            assert client.get("/chain/validate").get_json()["valid"] is True

        # Step 5: Alice's tx is in all three chains
        for client in (ca, cb, cc):
            chain = client.get("/chain").get_json()
            all_senders = [
                t["sender"]
                for block in chain["chain"]
                for t in block["transactions"]
            ]
            assert "NETWORK" in all_senders
            assert len(all_senders) >= 2