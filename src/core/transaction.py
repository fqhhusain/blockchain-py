"""
core/transaction.py
-------------------
Transaction model.  Every transaction sent by a user must be signed with the
sender's private key.  Reward (coinbase) transactions issued by the network
are exempt from signature requirements.
"""
from __future__ import annotations

from config import MINING_REWARD, MINER_ADDRESS
from core.wallet import public_key_to_address, sign, verify


class Transaction:
    def __init__(
        self,
        sender: str,
        receiver: str,
        amount: float,
        signature: str | None = None,
        public_key: str | None = None,
    ):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.signature = signature
        self.public_key = public_key

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Minimal dict used as the signing payload (no signature/key)."""
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
        }

    def to_full_dict(self) -> dict:
        """Complete dict including signature and public key for storage."""
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
            "signature": self.signature,
            "public_key": self.public_key,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Transaction:
        return cls(
            sender=data["sender"],
            receiver=data["receiver"],
            amount=data["amount"],
            signature=data.get("signature"),
            public_key=data.get("public_key"),
        )

    # ------------------------------------------------------------------
    # Signing & validation
    # ------------------------------------------------------------------

    def sign_transaction(self, private_key_pem: str) -> None:
        """Sign this transaction in-place using *private_key_pem*."""
        if self.sender == MINER_ADDRESS:
            return  # Coinbase transactions don't need a signature
        self.signature = sign(private_key_pem, self.to_dict())

    def is_valid(self) -> bool:
        """
        Return True if the transaction is authentic.

        Coinbase transactions (sender == MINER_ADDRESS) are always valid.
        All other transactions require a valid ECDSA signature.
        """
        if self.sender == MINER_ADDRESS:
            return True
        if not self.signature or not self.public_key:
            return False

        # Enforce sender ownership: sender address must be derived
        # from the submitted public key.
        if self.sender != public_key_to_address(self.public_key):
            return False

        return verify(self.public_key, self.to_dict(), self.signature)

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @staticmethod
    def create_reward_transaction(miner_address: str) -> Transaction:
        """Create the coinbase reward transaction for a miner."""
        return Transaction(
            sender=MINER_ADDRESS,
            receiver=miner_address,
            amount=MINING_REWARD,
        )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"Transaction(sender={self.sender!r}, receiver={self.receiver!r}, "
            f"amount={self.amount})"
        )