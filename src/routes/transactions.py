"""routes/transactions.py — POST /transactions/new"""
from flask import Blueprint, current_app, jsonify, request

from core.transaction import Transaction
from network.network_utils import broadcast_transaction
from routes.api_response import error_response

transactions_bp = Blueprint("transactions", __name__)

REQUIRED_FIELDS = {"sender", "receiver", "amount", "signature", "public_key"}


@transactions_bp.route("/transactions/new", methods=["POST"])
def new_transaction():
    """
    Add a signed transaction to the pending pool.

    Expected JSON body:
        sender      – sender's address (arbitrary string / public key fingerprint)
        receiver    – receiver's address
        amount      – positive number
        signature   – hex-encoded ECDSA signature
        public_key  – PEM-encoded sender public key
    """
    data = request.get_json(silent=True) or {}

    missing = REQUIRED_FIELDS - data.keys()
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
    if not tx.is_valid():
        return error_response(
            code="INVALID_TRANSACTION_SIGNATURE",
            message="Invalid signature or sender/public_key ownership mismatch",
            status=400,
        )

    added = current_app.blockchain.add_transaction(tx)
    if not added:
        return error_response(
            code="TRANSACTION_REJECTED",
            message="Transaction could not be added",
            status=400,
        )

    peers = current_app.node.get_peers()
    if peers:
        broadcast_transaction(peers, tx.to_full_dict())

    return (
        jsonify(
            {
                "message": "Transaction added to the pending pool",
                "pending_count": len(current_app.blockchain.pending_transactions),
            }
        ),
        201,
    )