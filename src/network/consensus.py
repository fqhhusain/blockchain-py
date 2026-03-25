"""
network/consensus.py
--------------------
Nakamoto Consensus: the longest *valid* chain wins.

When a node calls resolve_conflicts(), it fetches the chains of all known
peers and replaces its own chain if it finds a longer valid one.
"""
from __future__ import annotations

from core.blockchain import Blockchain
from network.network_utils import fetch_chain


def resolve_conflicts(blockchain: Blockchain, peers: list[str]) -> bool:
    """
    Compare the local chain against all peers and adopt the longest valid one.

    Args:
        blockchain: The local Blockchain instance to potentially replace.
        peers:      List of "host:port" peer addresses.

    Returns:
        True  – local chain was replaced.
        False – local chain is already the longest valid chain.
    """
    max_length = len(blockchain.chain)
    new_chain = None

    for peer in peers:
        data = fetch_chain(peer)
        if data is None:
            continue

        peer_length: int = data.get("length", 0)
        if peer_length <= max_length:
            continue

        # Deserialise and validate before accepting
        candidate = Blockchain.from_dict(data)
        if candidate.is_chain_valid():
            max_length = peer_length
            new_chain = candidate.chain

    if new_chain is not None:
        blockchain.replace_chain(new_chain)
        return True

    return False