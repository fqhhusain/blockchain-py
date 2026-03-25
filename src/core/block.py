"""
core/block.py
-------------
Block model.  Each block contains an ordered list of transactions, a link
to the previous block via its hash, a timestamp, and a nonce used during
Proof-of-Work mining.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import time


class Block:
    def __init__(
        self,
        index: int,
        transactions: list,
        previous_hash: str,
        timestamp: str | None = None,
        nonce: int = 0,
        hash: str | None = None,
    ):
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.timestamp = timestamp or str(datetime.datetime.now(datetime.UTC))
        self.nonce = nonce
        # Compute hash lazily; if provided (e.g. deserialised) use it directly
        self.hash = hash if hash is not None else self.calculate_hash()

    # ------------------------------------------------------------------
    # Hashing
    # ------------------------------------------------------------------

    def _tx_to_dict(self, tx) -> dict:
        """Normalise a transaction to a plain dict for hashing."""
        if isinstance(tx, dict):
            return tx
        return tx.to_full_dict()

    def calculate_hash(self) -> str:
        """Compute SHA-256 hash of the block's contents."""
        payload = {
            "index": self.index,
            "transactions": [self._tx_to_dict(t) for t in self.transactions],
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
        }
        raw = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    # ------------------------------------------------------------------
    # Proof-of-Work
    # ------------------------------------------------------------------

    def mine_block(self, difficulty: int) -> str:
        """
        Increment nonce until the block hash starts with *difficulty* zeros.

        Returns the final valid hash.
        """
        target = "0" * difficulty
        start = time.time()

        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()

        elapsed = time.time() - start
        print(
            f"  [Mine] Block #{self.index} | hash={self.hash[:16]}... "
            f"nonce={self.nonce} | {elapsed:.2f}s"
        )
        return self.hash

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "transactions": [self._tx_to_dict(t) for t in self.transactions],
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Block:
        from core.transaction import Transaction

        transactions = [Transaction.from_dict(t) for t in data["transactions"]]
        return cls(
            index=data["index"],
            transactions=transactions,
            previous_hash=data["previous_hash"],
            timestamp=data["timestamp"],
            nonce=data["nonce"],
            hash=data["hash"],
        )

    def __repr__(self) -> str:  # pragma: no cover
        return f"Block(index={self.index}, hash={self.hash[:12]}...)"