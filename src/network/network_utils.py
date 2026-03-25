"""
network/network_utils.py
------------------------
Thin HTTP wrappers for peer-to-peer communication between nodes.
All functions are fire-and-forget; failures are silently swallowed so that
one unreachable peer doesn't interrupt the local node.
"""
from __future__ import annotations

import requests

TIMEOUT = 3  # seconds


def fetch_chain(peer: str) -> dict | None:
    """
    GET /chain from *peer*.

    Returns the parsed JSON dict, or None on any error.
    """
    try:
        resp = requests.get(f"http://{peer}/chain", timeout=TIMEOUT)
        if resp.status_code == 200:
            return resp.json()
    except requests.exceptions.RequestException:
        pass
    return None


def broadcast_transaction(peers: list[str], tx_data: dict) -> None:
    """POST a transaction payload to every peer's /transactions/new."""
    for peer in peers:
        try:
            requests.post(
                f"http://{peer}/transactions/new",
                json=tx_data,
                timeout=TIMEOUT,
            )
        except requests.exceptions.RequestException:
            pass


def broadcast_new_block(peers: list[str]) -> None:
    """
    Notify peers that a new block was mined so they can resolve their chain.
    Peers respond by calling GET /nodes/resolve on themselves.
    """
    for peer in peers:
        try:
            requests.get(f"http://{peer}/nodes/resolve", timeout=TIMEOUT)
        except requests.exceptions.RequestException:
            pass