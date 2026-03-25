"""
core/blockchain.py
------------------
Blockchain: manages the chain of blocks, the pending transaction pool,
Proof-of-Work mining (with automatic reward), chain validation, and
balance queries.
"""
from __future__ import annotations

import json
import os

from config import DIFFICULTY
from core.block import Block
from core.transaction import Transaction


class Blockchain:
    def __init__(self, storage_path: str | None = None):
        self.storage_path = storage_path
        self.chain: list[Block] = []
        self.pending_transactions: list[Transaction] = []
        self.difficulty: int = DIFFICULTY

        # Restore state from disk when persistence is enabled.
        if self.storage_path and self._load_state():
            return

        self.chain = [self._create_genesis_block()]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _create_genesis_block() -> Block:
        return Block(index=0, transactions=[], previous_hash="0")

    def _load_state(self) -> bool:
        """Load chain and pending transactions from JSON storage."""
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                raw = json.load(f)

            chain_data = raw.get("chain")
            if not isinstance(chain_data, list) or not chain_data:
                return False

            candidate_chain = [Block.from_dict(block) for block in chain_data]
            if not self.is_chain_valid(candidate_chain):
                return False

            pending_data = raw.get("pending_transactions", [])
            pending = [Transaction.from_dict(tx) for tx in pending_data]
            self.chain = candidate_chain
            # Keep only valid pending transactions when reloading.
            self.pending_transactions = [tx for tx in pending if tx.is_valid()]
            return True
        except (OSError, ValueError, TypeError, KeyError):
            return False

    def _save_state(self) -> None:
        """Persist current chain and pending pool to JSON storage."""
        if not self.storage_path:
            return

        directory = os.path.dirname(self.storage_path) or "."
        os.makedirs(directory, exist_ok=True)

        payload = {
            "chain": [block.to_dict() for block in self.chain],
            "pending_transactions": [tx.to_full_dict() for tx in self.pending_transactions],
        }

        tmp_path = f"{self.storage_path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        os.replace(tmp_path, self.storage_path)

    def replace_chain(self, new_chain: list[Block]) -> None:
        """Replace local chain after consensus and persist the new state."""
        self.chain = new_chain
        self.pending_transactions = []
        self._save_state()

    def get_latest_block(self) -> Block:
        return self.chain[-1]

    # ------------------------------------------------------------------
    # Transaction management
    # ------------------------------------------------------------------

    def add_transaction(self, transaction: Transaction) -> bool:
        """
        Validate and add *transaction* to the pending pool.

        Returns True on success, False if the transaction is invalid.
        """
        if not transaction.is_valid():
            return False
        self.pending_transactions.append(transaction)
        self._save_state()
        return True

    # ------------------------------------------------------------------
    # Mining
    # ------------------------------------------------------------------

    def mine_pending_transactions(self, miner_address: str) -> Block:
        """
        Bundle all pending transactions plus a coinbase reward into a new
        block, mine it with Proof-of-Work, append it to the chain, and
        clear the pending pool.

        Returns the newly mined Block.
        """
        # Append the mining reward before sealing the block
        reward_tx = Transaction.create_reward_transaction(miner_address)
        transactions_to_include = list(self.pending_transactions) + [reward_tx]

        block = Block(
            index=len(self.chain),
            transactions=transactions_to_include,
            previous_hash=self.get_latest_block().hash,
        )
        block.mine_block(self.difficulty)

        self.chain.append(block)
        self.pending_transactions = []
        self._save_state()
        return block

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def is_chain_valid(self, chain: list[Block] | None = None) -> bool:
        """
        Verify the integrity of *chain* (defaults to self.chain).

        Checks:
        - Each block's stored hash matches its recalculated hash.
        - Each block's previous_hash matches the preceding block's hash.
        - Every transaction in every block has a valid signature.
        """
        target_chain = chain if chain is not None else self.chain

        for i in range(1, len(target_chain)):
            current = target_chain[i]
            previous = target_chain[i - 1]

            if current.hash != current.calculate_hash():
                return False

            if current.previous_hash != previous.hash:
                return False

            for tx in current.transactions:
                if not tx.is_valid():
                    return False

        return True

    # ------------------------------------------------------------------
    # Balance
    # ------------------------------------------------------------------

    def get_balance(self, address: str) -> float:
        """Return the confirmed balance for *address* across the whole chain."""
        balance = 0.0
        for block in self.chain:
            for tx in block.transactions:
                if tx.receiver == address:
                    balance += tx.amount
                if tx.sender == address:
                    balance -= tx.amount
        return balance

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "chain": [block.to_dict() for block in self.chain],
            "length": len(self.chain),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Blockchain:
        """Reconstruct a Blockchain from the JSON returned by /chain."""
        bc = cls.__new__(cls)
        bc.storage_path = None
        bc.difficulty = DIFFICULTY
        bc.pending_transactions = []
        bc.chain = [Block.from_dict(b) for b in data["chain"]]
        return bc