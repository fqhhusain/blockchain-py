"""tests/unit/test_transaction.py — Unit tests for the Transaction model."""
import pytest

from config import MINER_ADDRESS, MINING_REWARD
from core.transaction import Transaction
from core.wallet import generate_keys, public_key_to_address


@pytest.fixture()
def signed_tx():
    priv, pub = generate_keys()
    tx = Transaction(public_key_to_address(pub), "Bob", 5, public_key=pub)
    tx.sign_transaction(priv)
    return tx


# ── Serialisation ────────────────────────────────────────────────────
class TestSerialisation:
    def test_to_dict_has_required_keys(self):
        tx = Transaction("Alice", "Bob", 10)
        d = tx.to_dict()
        assert set(d.keys()) == {"sender", "receiver", "amount"}

    def test_to_full_dict_has_all_keys(self, signed_tx):
        d = signed_tx.to_full_dict()
        assert set(d.keys()) == {"sender", "receiver", "amount", "signature", "public_key"}

    def test_from_dict_roundtrip(self, signed_tx):
        d = signed_tx.to_full_dict()
        tx2 = Transaction.from_dict(d)
        assert tx2.sender == signed_tx.sender
        assert tx2.receiver == signed_tx.receiver
        assert tx2.amount == signed_tx.amount
        assert tx2.signature == signed_tx.signature
        assert tx2.public_key == signed_tx.public_key

    def test_from_dict_roundtrip_is_valid(self, signed_tx):
        tx2 = Transaction.from_dict(signed_tx.to_full_dict())
        assert tx2.is_valid() is True


# ── Validation ───────────────────────────────────────────────────────
class TestValidation:
    def test_signed_transaction_is_valid(self, signed_tx):
        assert signed_tx.is_valid() is True

    def test_unsigned_transaction_is_invalid(self):
        _, pub = generate_keys()
        tx = Transaction(public_key_to_address(pub), "Bob", 5, public_key=pub)
        assert tx.is_valid() is False

    def test_missing_public_key_is_invalid(self):
        priv, _ = generate_keys()
        tx = Transaction("sender", "Bob", 5)
        tx.sign_transaction(priv)  # signature set but no public_key
        assert tx.is_valid() is False

    def test_sender_not_matching_public_key_is_invalid(self):
        priv, pub = generate_keys()
        tx = Transaction("Alice", "Bob", 5, public_key=pub)
        tx.sign_transaction(priv)
        assert tx.is_valid() is False

    def test_tampered_amount_invalidates(self, signed_tx):
        signed_tx.amount = 9999
        assert signed_tx.is_valid() is False

    def test_tampered_receiver_invalidates(self, signed_tx):
        signed_tx.receiver = "Eve"
        assert signed_tx.is_valid() is False
    def test_invalid_amount_rejected_at_core_level():
        tx = Transaction(sender="Alice", receiver="Bob", amount=-10)
        # tanpa perlu signature — is_valid() harus return False lebih awal
        assert tx.is_valid() is False


# ── Reward transaction ───────────────────────────────────────────────
class TestRewardTransaction:
    def test_sender_is_network(self):
        tx = Transaction.create_reward_transaction("MinerX")
        assert tx.sender == MINER_ADDRESS

    def test_correct_amount(self):
        tx = Transaction.create_reward_transaction("MinerX")
        assert tx.amount == MINING_REWARD

    def test_reward_is_always_valid(self):
        tx = Transaction.create_reward_transaction("MinerX")
        assert tx.is_valid() is True

    def test_sign_coinbase_is_noop(self):
        priv, _ = generate_keys()
        tx = Transaction.create_reward_transaction("MinerX")
        tx.sign_transaction(priv)
        # Signature must remain None (coinbase doesn't get signed)
        assert tx.signature is None