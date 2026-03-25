"""tests/unit/test_wallet.py — Unit tests for ECDSA wallet functions."""
import pytest

from core.wallet import generate_keys, sign, verify


# ── Key generation ──────────────────────────────────────────────────
class TestGenerateKeys:
    def test_returns_two_strings(self):
        priv, pub = generate_keys()
        assert isinstance(priv, str)
        assert isinstance(pub, str)

    def test_private_key_is_pem(self):
        priv, _ = generate_keys()
        assert "PRIVATE KEY" in priv

    def test_public_key_is_pem(self):
        _, pub = generate_keys()
        assert "PUBLIC KEY" in pub

    def test_keys_are_unique(self):
        priv1, pub1 = generate_keys()
        priv2, pub2 = generate_keys()
        assert priv1 != priv2
        assert pub1 != pub2


# ── Signing ─────────────────────────────────────────────────────────
class TestSign:
    def test_returns_hex_string(self):
        priv, _ = generate_keys()
        data = {"sender": "Alice", "receiver": "Bob", "amount": 10}
        sig = sign(priv, data)
        assert isinstance(sig, str)
        # Must be valid hex
        int(sig, 16)

    def test_different_data_different_signature(self):
        priv, _ = generate_keys()
        data1 = {"sender": "Alice", "receiver": "Bob", "amount": 10}
        data2 = {"sender": "Alice", "receiver": "Bob", "amount": 99}
        assert sign(priv, data1) != sign(priv, data2)


# ── Verification ─────────────────────────────────────────────────────
class TestVerify:
    @pytest.fixture()
    def key_pair_and_sig(self):
        priv, pub = generate_keys()
        data = {"sender": "Alice", "receiver": "Bob", "amount": 10}
        sig = sign(priv, data)
        return pub, data, sig

    def test_valid_signature(self, key_pair_and_sig):
        pub, data, sig = key_pair_and_sig
        assert verify(pub, data, sig) is True

    def test_tampered_amount(self, key_pair_and_sig):
        pub, data, sig = key_pair_and_sig
        tampered = {**data, "amount": 9999}
        assert verify(pub, tampered, sig) is False

    def test_wrong_public_key(self, key_pair_and_sig):
        _, data, sig = key_pair_and_sig
        _, other_pub = generate_keys()
        assert verify(other_pub, data, sig) is False

    def test_invalid_hex_signature(self, key_pair_and_sig):
        pub, data, _ = key_pair_and_sig
        assert verify(pub, data, "not_a_hex_string") is False

    def test_empty_signature(self, key_pair_and_sig):
        pub, data, _ = key_pair_and_sig
        assert verify(pub, data, "") is False

    def test_dict_key_order_independent(self):
        """Signing is deterministic regardless of Python dict insertion order."""
        priv, pub = generate_keys()
        data_a = {"sender": "Alice", "receiver": "Bob", "amount": 5}
        data_b = {"amount": 5, "receiver": "Bob", "sender": "Alice"}
        sig = sign(priv, data_a)
        assert verify(pub, data_b, sig) is True