"""
app.py
------
Flask application factory.  Each call to create_app() produces an isolated
Flask instance with its own Blockchain and Node – this makes it trivial to
run multiple nodes in the same process during testing.
"""
from __future__ import annotations

import argparse
import os

from flask import Flask

from config import BLOCKCHAIN_DATA_DIR, DEFAULT_HOST, DEFAULT_PORT, PERSIST_BLOCKCHAIN
from core.blockchain import Blockchain
from network.node import Node
from routes.chain import chain_bp
from routes.mine import mine_bp
from routes.nodes import nodes_bp
from routes.transactions import transactions_bp
from routes.wallet import wallet_bp


def create_app(port: int = DEFAULT_PORT) -> Flask:
    """
    Create and configure a Flask application for a single blockchain node.

    Args:
        port: The port this node will listen on (used to initialise the Node).
    """
    app = Flask(__name__)

    # Attach per-node state to the app object
    storage_path = None
    if PERSIST_BLOCKCHAIN:
        storage_path = os.path.join(BLOCKCHAIN_DATA_DIR, f"node_{port}.json")
    app.blockchain = Blockchain(storage_path=storage_path)
    app.node = Node(port=port)

    # Register route blueprints
    app.register_blueprint(transactions_bp)
    app.register_blueprint(mine_bp)
    app.register_blueprint(chain_bp)
    app.register_blueprint(nodes_bp)
    app.register_blueprint(wallet_bp)

    return app


# ------------------------------------------------------------------
# Entry point: python app.py --port 5000
# ------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start a blockchain node")
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="Port to listen on (default: 5000)",
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help="Host to bind to (default: 0.0.0.0)",
    )
    args = parser.parse_args()

    node_app = create_app(port=args.port)
    print(f"🔗 Blockchain node starting on http://{args.host}:{args.port}")
    node_app.run(host=args.host, port=args.port, debug=False, threaded=False)