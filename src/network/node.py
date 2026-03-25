"""
network/node.py
---------------
Represents a single node in the peer-to-peer network.
Manages the node's unique identifier and its list of known peers.
"""
from __future__ import annotations
import uuid


class Node:
    def __init__(self, port: int):
        self.node_id: str = str(uuid.uuid4()).replace("-", "")
        self.port: int = port
        self._peers: set[str] = set()  # "host:port" strings

    def register_peer(self, address: str) -> None:
        """Add *address* (e.g. 'localhost:5001') to the peer set."""
        address = address.strip().rstrip("/")
        self._peers.add(address)

    def get_peers(self) -> list[str]:
        return sorted(self._peers)

    def __repr__(self) -> str:  # pragma: no cover
        return f"Node(id={self.node_id[:8]}, port={self.port}, peers={len(self._peers)})"