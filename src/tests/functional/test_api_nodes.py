"""
tests/functional/test_api_nodes.py
------------------------------------
Functional tests for POST /nodes/register and GET /nodes/resolve.
The resolve test uses two in-process Flask apps to simulate a 2-node network
without opening real ports.
"""
import json
import pytest
from unittest.mock import patch

from app import create_app
from core.transaction import Transaction
from core.wallet import generate_keys


@pytest.fixture()
def client():
    app = create_app(port=5000)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture()
def two_clients():
    """Two independent blockchain nodes."""
    app_a = create_app(port=5000)
    app_b = create_app(port=5001)
    app_a.config["TESTING"] = True
    app_b.config["TESTING"] = True
    ca = app_a.test_client()
    cb = app_b.test_client()
    yield ca, cb, app_a, app_b


# ── GET /nodes ────────────────────────────────────────────────────────
class TestListNodes:
    def test_returns_200(self, client):
        assert client.get("/nodes").status_code == 200

    def test_has_node_id(self, client):
        data = client.get("/nodes").get_json()
        assert "node_id" in data
        assert len(data["node_id"]) == 32

    def test_empty_peers_initially(self, client):
        data = client.get("/nodes").get_json()
        assert data["peers"] == []


# ── POST /nodes/register ──────────────────────────────────────────────
class TestRegisterNodes:
    def test_returns_201(self, client):
        resp = client.post("/nodes/register", json={"nodes": ["localhost:5001"]})
        assert resp.status_code == 201

    def test_peer_is_registered(self, client):
        client.post("/nodes/register", json={"nodes": ["localhost:5001"]})
        data = client.get("/nodes").get_json()
        assert "localhost:5001" in data["peers"]

    def test_multiple_peers(self, client):
        peers = ["localhost:5001", "localhost:5002"]
        client.post("/nodes/register", json={"nodes": peers})
        data = client.get("/nodes").get_json()
        for p in peers:
            assert p in data["peers"]

    def test_empty_list_returns_400(self, client):
        resp = client.post("/nodes/register", json={"nodes": []})
        assert resp.status_code == 400

    def test_missing_key_returns_400(self, client):
        resp = client.post("/nodes/register", json={})
        assert resp.status_code == 400

    def test_duplicate_peer_not_duplicated(self, client):
        client.post("/nodes/register", json={"nodes": ["localhost:5001"]})
        client.post("/nodes/register", json={"nodes": ["localhost:5001"]})
        data = client.get("/nodes").get_json()
        assert data["peers"].count("localhost:5001") == 1


# ── GET /nodes/resolve ─────────────────────────────────────────────────
class TestResolveConsensus:
    def test_resolve_no_peers_returns_200(self, client):
        resp = client.get("/nodes/resolve")
        assert resp.status_code == 200

    def test_resolve_no_peers_not_replaced(self, client):
        data = client.get("/nodes/resolve").get_json()
        assert data["replaced"] is False

    def test_resolve_adopts_longer_chain(self, two_clients):
        """Node A (short chain) should adopt Node B's longer chain."""
        ca, cb, app_a, app_b = two_clients

        # Mine 2 blocks on Node B so it has the longer chain
        cb.post("/mine", json={"miner_address": "MinerB"})
        cb.post("/mine", json={"miner_address": "MinerB"})
        chain_b = cb.get("/chain").get_json()

        # Register Node B as peer of Node A, then mock fetch_chain
        ca.post("/nodes/register", json={"nodes": ["localhost:5001"]})

        with patch("network.consensus.fetch_chain") as mock_fetch:
            mock_fetch.return_value = chain_b
            resp = ca.get("/nodes/resolve")
            data = resp.get_json()

        assert data["replaced"] is True
        assert data["chain"]["length"] == chain_b["length"]

    def test_resolve_keeps_own_longer_chain(self, two_clients):
        """Node A (longer) should not be replaced by Node B (shorter)."""
        ca, cb, app_a, app_b = two_clients

        # Mine 2 blocks on Node A
        ca.post("/mine", json={"miner_address": "MinerA"})
        ca.post("/mine", json={"miner_address": "MinerA"})

        # Node B has only genesis
        chain_b = cb.get("/chain").get_json()

        ca.post("/nodes/register", json={"nodes": ["localhost:5001"]})

        with patch("network.consensus.fetch_chain") as mock_fetch:
            mock_fetch.return_value = chain_b
            data = ca.get("/nodes/resolve").get_json()

        assert data["replaced"] is False