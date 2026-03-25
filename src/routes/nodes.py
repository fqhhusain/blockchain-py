"""routes/nodes.py — peer registration and consensus endpoints"""
from flask import Blueprint, current_app, jsonify, request

from network.consensus import resolve_conflicts
from routes.api_response import error_response

nodes_bp = Blueprint("nodes", __name__)


@nodes_bp.route("/nodes", methods=["GET"])
def list_nodes():
    """Return all known peers of this node."""
    return jsonify({"node_id": current_app.node.node_id, "peers": current_app.node.get_peers()}), 200


@nodes_bp.route("/nodes/register", methods=["POST"])
def register_nodes():
    """
    Register one or more peer addresses.

    Expected JSON body:
        nodes – list of "host:port" strings, e.g. ["localhost:5001", "localhost:5002"]
    """
    data = request.get_json(silent=True) or {}
    peers = data.get("nodes", [])

    if not peers:
        return error_response(
            code="INVALID_NODES_PAYLOAD",
            message="Provide a non-empty list under the key 'nodes'",
            status=400,
        )

    for peer in peers:
        current_app.node.register_peer(str(peer))

    return (
        jsonify(
            {
                "message": f"{len(peers)} peer(s) registered",
                "peers": current_app.node.get_peers(),
            }
        ),
        201,
    )


@nodes_bp.route("/nodes/resolve", methods=["GET"])
def resolve():
    """
    Run Nakamoto consensus against all known peers.

    If a longer valid chain is found, replace the local chain with it.
    """
    replaced = resolve_conflicts(current_app.blockchain, current_app.node.get_peers())

    if replaced:
        msg = "Chain replaced – adopted a longer chain from a peer"
    else:
        msg = "Chain is authoritative – no longer chain found"

    return (
        jsonify(
            {
                "message": msg,
                "replaced": replaced,
                "chain": current_app.blockchain.to_dict(),
            }
        ),
        200,
    )