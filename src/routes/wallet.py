"""routes/wallet.py — Wallet utility endpoints

Endpoints:
  GET  /wallet/new           → Generate a fresh ECDSA key pair
  POST /transactions/verify  → Verify a transaction signature without adding it
"""
from flask import Blueprint, jsonify, request

from core.transaction import Transaction
from core.wallet import generate_keys, public_key_to_address
from routes.api_response import error_response

wallet_bp = Blueprint("wallet", __name__)


@wallet_bp.route("/wallet/new", methods=["GET"])
def new_wallet():
    """
    Generate a new SECP256K1 key pair.

    The `address` field is a short fingerprint derived from the public key
    (first 40 Base64 characters after stripping PEM headers) — it uniquely
    identifies a wallet without exposing the full key.

    Response JSON:
        private_key  – PEM string  (keep secret — used for signing)
        public_key   – PEM string  (shared with everyone — used for verify)
        address      – short wallet identifier
    """
    private_key, public_key = generate_keys()

    address = public_key_to_address(public_key)

    return (
        jsonify(
            {
                "private_key": private_key,
                "public_key": public_key,
                "address": address,
            }
        ),
        200,
    )


@wallet_bp.route("/transactions/verify", methods=["POST"])
def verify_transaction():
    """
    Verify the digital signature of a transaction WITHOUT adding it to
    the pending pool.  Useful for testing and demonstrating signature
    validation.

    Expected JSON body:
        sender      – sender address
        receiver    – receiver address
        amount      – positive number
        signature   – hex-encoded ECDSA signature
        public_key  – PEM-encoded sender public key

    Response JSON:
        valid        – true / false
        message      – human-readable explanation
    """
    data = request.get_json(silent=True) or {}

    required = {"sender", "receiver", "amount", "signature", "public_key"}
    missing = required - data.keys()
    if missing:
        return error_response(
            code="MISSING_FIELDS",
            message="Missing required fields",
            status=400,
            details={"missing": sorted(missing)},
        )

    try:
        amount = float(data["amount"])
        if amount <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return error_response(
            code="INVALID_AMOUNT",
            message="amount must be a positive number",
            status=400,
        )

    tx = Transaction.from_dict(data)
    valid = tx.is_valid()

    return (
        jsonify(
            {
                "valid": valid,
                "message": (
                    "Signature is VALID — transaction is authentic."
                    if valid
                    else "Signature is INVALID — transaction rejected."
                ),
                "transaction": tx.to_dict(),
            }
        ),
        200,
    )
