"""tests/unit/test_blockchain.py — Unit tests for the Blockchain model."""
import pytest

from config import MINING_REWARD
from core.blockchain import Blockchain
from core.transaction import Transaction
from core.wallet import generate_keys, public_key_to_address


# ── Helpers ──────────────────────────────────────────────────────────

def make_signed_tx(sender="Alice", receiver="Bob", amount=5.0) -> Transaction:
    priv, pub = generate_keys()
    tx = Transaction(public_key_to_address(pub), receiver, amount, public_key=pub)
    tx.sign_transaction(priv)
    return tx


@pytest.fixture()
def blockchain():
    return Blockchain()


@pytest.fixture()
def mined_blockchain():
    bc = Blockchain()
    bc.add_transaction(make_signed_tx("Alice", "Bob", 10))
    bc.mine_pending_transactions("MinerA")
    return bc


# ── Genesis block ─────────────────────────────────────────────────────
class TestGenesisBlock:
    def test_chain_starts_with_one_block(self, blockchain):
        assert len(blockchain.chain) == 1

    def test_genesis_index_is_zero(self, blockchain):
        assert blockchain.chain[0].index == 0

    def test_genesis_previous_hash_is_zero(self, blockchain):
        assert blockchain.chain[0].previous_hash == "0"

    def test_genesis_has_no_transactions(self, blockchain):
        assert blockchain.chain[0].transactions == []


# ── Transaction pool ──────────────────────────────────────────────────
class TestTransactionPool:
    def test_add_valid_transaction(self, blockchain):
        tx = make_signed_tx()
        assert blockchain.add_transaction(tx) is True
        assert tx in blockchain.pending_transactions

    def test_reject_unsigned_transaction(self, blockchain):
        _, pub = generate_keys()
        tx = Transaction(public_key_to_address(pub), "Bob", 5, public_key=pub)  # no signature
        assert blockchain.add_transaction(tx) is False
        assert blockchain.pending_transactions == []

    def test_multiple_transactions_queued(self, blockchain):
        for _ in range(3):
            blockchain.add_transaction(make_signed_tx())
        assert len(blockchain.pending_transactions) == 3

    def test_reject_duplicate_pending_transaction(self, blockchain):
        tx = make_signed_tx()
        assert blockchain.add_transaction(tx) is True
        assert blockchain.add_transaction(tx) is False
        assert len(blockchain.pending_transactions) == 1


# ── Mining ────────────────────────────────────────────────────────────
class TestMining:
    def test_mine_appends_block(self, blockchain):
        blockchain.add_transaction(make_signed_tx())
        blockchain.mine_pending_transactions("MinerA")
        assert len(blockchain.chain) == 2

    def test_mine_clears_pending_pool(self, blockchain):
        blockchain.add_transaction(make_signed_tx())
        blockchain.mine_pending_transactions("MinerA")
        assert blockchain.pending_transactions == []

    def test_mined_block_contains_reward_tx(self, mined_blockchain):
        block = mined_blockchain.chain[-1]
        reward_txs = [
            t for t in block.transactions
            if t.receiver == "MinerA" and t.sender == "NETWORK"
        ]
        assert len(reward_txs) == 1

    def test_reward_amount_correct(self, mined_blockchain):
        block = mined_blockchain.chain[-1]
        reward_tx = next(
            t for t in block.transactions if t.receiver == "MinerA"
        )
        assert reward_tx.amount == MINING_REWARD

    def test_multiple_mines_grow_chain(self, blockchain):
        for _ in range(3):
            blockchain.add_transaction(make_signed_tx())
            blockchain.mine_pending_transactions("MinerA")
        assert len(blockchain.chain) == 4  # genesis + 3 mined

    def test_mine_empty_pool_still_produces_block(self, blockchain):
        """Mining with no user transactions still adds the reward block."""
        blockchain.mine_pending_transactions("MinerA")
        assert len(blockchain.chain) == 2


# ── Validation ────────────────────────────────────────────────────────
class TestValidation:
    def test_fresh_chain_is_valid(self, blockchain):
        assert blockchain.is_chain_valid() is True

    def test_chain_valid_after_mining(self, mined_blockchain):
        assert mined_blockchain.is_chain_valid() is True

    def test_tampered_hash_invalidates(self, mined_blockchain):
        mined_blockchain.chain[1].hash = "0" * 64
        assert mined_blockchain.is_chain_valid() is False

    def test_tampered_previous_hash_invalidates(self, mined_blockchain):
        mined_blockchain.chain[1].previous_hash = "deadbeef" * 8
        assert mined_blockchain.is_chain_valid() is False

    def test_tampered_transaction_amount_invalidates(self, mined_blockchain):
        # Modify a non-reward transaction's amount
        for tx in mined_blockchain.chain[1].transactions:
            if tx.sender != "NETWORK":
                tx.amount = 9999
                break
        assert mined_blockchain.is_chain_valid() is False


# ── Balance ───────────────────────────────────────────────────────────
class TestBalance:
    def test_receiver_gets_credited(self, mined_blockchain):
        # Bob received 10 coins in the mined block
        assert mined_blockchain.get_balance("Bob") == 10.0

    def test_miner_gets_reward(self, mined_blockchain):
        assert mined_blockchain.get_balance("MinerA") == MINING_REWARD

    def test_unknown_address_balance_is_zero(self, mined_blockchain):
        assert mined_blockchain.get_balance("Nobody") == 0.0


# ── Serialisation ─────────────────────────────────────────────────────
class TestSerialisation:
    def test_to_dict_has_chain_and_length(self, blockchain):
        d = blockchain.to_dict()
        assert "chain" in d
        assert "length" in d
        assert d["length"] == 1

    def test_from_dict_roundtrip(self, mined_blockchain):
        data = mined_blockchain.to_dict()
        bc2 = Blockchain.from_dict(data)
        assert len(bc2.chain) == len(mined_blockchain.chain)
        assert bc2.is_chain_valid() is True