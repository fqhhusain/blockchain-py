"""routes/chain.py — chain inspection endpoints"""
from flask import Blueprint, current_app, jsonify, request

chain_bp = Blueprint("chain", __name__)


@chain_bp.route("/chain", methods=["GET"])
def get_chain():
    """Return the full blockchain as JSON."""
    return jsonify(current_app.blockchain.to_dict()), 200


@chain_bp.route("/chain/validate", methods=["GET"])
def validate_chain():
    """Check whether the local chain is internally consistent."""
    valid = current_app.blockchain.is_chain_valid()
    return (
        jsonify(
            {
                "valid": valid,
                "length": len(current_app.blockchain.chain),
            }
        ),
        200,
    )


@chain_bp.route("/balance/<address>", methods=["GET"])
def get_balance(address: str):
    """Return the confirmed balance for *address*."""
    balance = current_app.blockchain.get_balance(address)
    return jsonify({"address": address, "balance": balance}), 200