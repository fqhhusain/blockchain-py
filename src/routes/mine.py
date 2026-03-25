"""routes/mine.py — POST /mine"""
from flask import Blueprint, current_app, jsonify, request

from network.network_utils import broadcast_new_block

mine_bp = Blueprint("mine", __name__)


@mine_bp.route("/mine", methods=["POST"])
def mine():
    """
    Mine all pending transactions into a new block.

    Expected JSON body (optional):
        miner_address – address that receives the block reward

    Even if there are no user transactions the miner still receives the
    coinbase reward, so a block is always produced.
    """
    data = request.get_json(silent=True) or {}
    miner_address = data.get("miner_address", "anonymous").strip()

    if not miner_address:
        miner_address = "anonymous"

    print(f"\n[Mine] Starting PoW for miner={miner_address!r} ...")
    block = current_app.blockchain.mine_pending_transactions(miner_address)

    # Notify peers so they can sync their chain
    peers = current_app.node.get_peers()
    if peers:
        broadcast_new_block(peers)

    return (
        jsonify(
            {
                "message": "Block mined successfully",
                "miner": miner_address,
                "block": block.to_dict(),
                "chain_length": len(current_app.blockchain.chain),
            }
        ),
        200,
    )