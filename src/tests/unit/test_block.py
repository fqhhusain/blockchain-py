"""tests/unit/test_block.py — Unit tests for the Block model."""
import pytest

from core.block import Block
from core.transaction import Transaction


@pytest.fixture()
def sample_block():
    tx = Transaction("NETWORK", "Alice", 10)
    return Block(index=1, transactions=[tx], previous_hash="0" * 64)


# ── Hash calculation ─────────────────────────────────────────────────
class TestCalculateHash:
    def test_hash_is_64_hex_chars(self, sample_block):
        assert len(sample_block.hash) == 64
        int(sample_block.hash, 16)  # must be valid hex

    def test_hash_is_deterministic(self, sample_block):
        h1 = sample_block.calculate_hash()
        h2 = sample_block.calculate_hash()
        assert h1 == h2

    def test_hash_changes_when_nonce_changes(self, sample_block):
        original = sample_block.calculate_hash()
        sample_block.nonce += 1
        assert sample_block.calculate_hash() != original

    def test_hash_changes_when_tx_tampered(self, sample_block):
        original_hash = sample_block.hash
        sample_block.transactions[0].amount = 9999
        assert sample_block.calculate_hash() != original_hash


# ── Proof-of-Work ────────────────────────────────────────────────────
class TestMineBlock:
    def test_mined_hash_meets_difficulty(self):
        block = Block(1, [], "0" * 64)
        block.mine_block(difficulty=2)
        assert block.hash.startswith("00")

    def test_nonce_increases_after_mining(self):
        block = Block(1, [], "0" * 64)
        block.mine_block(difficulty=2)
        assert block.nonce > 0

    def test_hash_is_consistent_after_mining(self):
        block = Block(1, [], "0" * 64)
        mined_hash = block.mine_block(difficulty=2)
        assert mined_hash == block.calculate_hash()


# ── Serialisation ────────────────────────────────────────────────────
class TestSerialisation:
    def test_to_dict_has_required_keys(self, sample_block):
        d = sample_block.to_dict()
        required = {"index", "transactions", "previous_hash", "timestamp", "nonce", "hash"}
        assert required.issubset(d.keys())

    def test_from_dict_preserves_index(self, sample_block):
        d = sample_block.to_dict()
        b2 = Block.from_dict(d)
        assert b2.index == sample_block.index

    def test_from_dict_preserves_hash(self, sample_block):
        d = sample_block.to_dict()
        b2 = Block.from_dict(d)
        assert b2.hash == sample_block.hash

    def test_from_dict_hash_verifiable(self, sample_block):
        """Reconstructed block must reproduce the same hash."""
        d = sample_block.to_dict()
        b2 = Block.from_dict(d)
        assert b2.hash == b2.calculate_hash()

    def test_genesis_block_serialisation(self):
        genesis = Block(0, [], "0")
        d = genesis.to_dict()
        g2 = Block.from_dict(d)
        assert g2.index == 0
        assert g2.previous_hash == "0"
        assert g2.transactions == []