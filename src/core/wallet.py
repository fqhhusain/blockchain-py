"""
core/wallet.py
--------------
ECDSA key generation, signing, and verification using the SECP256K1 curve
(the same curve used by Bitcoin).

Public/private keys are stored as PEM strings for easy serialisation.
Signatures are returned as lowercase hex strings.
"""
import binascii
import json

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec


def public_key_to_address(public_key_pem: str, length: int = 40) -> str:
    """
    Derive a short address fingerprint from a PEM public key.

    Address format is consistent with /wallet/new:
    - remove PEM header/footer lines
    - join base64 body lines
    - keep first *length* characters
    """
    raw_b64 = "".join(
        line.strip()
        for line in public_key_pem.splitlines()
        if line and not line.startswith("-----")
    )
    return raw_b64[:length]


def generate_keys() -> tuple[str, str]:
    """
    Generate a new SECP256K1 key pair.

    Returns:
        (private_key_pem, public_key_pem) as UTF-8 strings.
    """
    private_key = ec.generate_private_key(ec.SECP256K1(), default_backend())
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    return private_pem, public_pem


def sign(private_key_pem: str, data: dict) -> str:
    """
    Sign *data* with *private_key_pem*.

    The dict is serialised deterministically (sorted keys) before signing.

    Returns:
        DER-encoded signature as a lowercase hex string.
    """
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode("utf-8"),
        password=None,
        backend=default_backend(),
    )
    message = json.dumps(data, sort_keys=True).encode("utf-8")
    signature_bytes = private_key.sign(message, ec.ECDSA(hashes.SHA256()))
    return binascii.hexlify(signature_bytes).decode("utf-8")


def verify(public_key_pem: str, data: dict, signature_hex: str) -> bool:
    """
    Verify that *signature_hex* was produced by the private key corresponding
    to *public_key_pem* over *data*.

    Returns:
        True if valid, False for any failure (bad key, bad sig, tampered data).
    """
    try:
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode("utf-8"),
            backend=default_backend(),
        )
        message = json.dumps(data, sort_keys=True).encode("utf-8")
        signature_bytes = binascii.unhexlify(signature_hex)
        public_key.verify(signature_bytes, message, ec.ECDSA(hashes.SHA256()))
        return True
    except (InvalidSignature, Exception):
        return False