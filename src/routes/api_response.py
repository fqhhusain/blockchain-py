"""Shared API response helpers for consistent JSON payloads."""
from flask import jsonify


def error_response(code: str, message: str, status: int = 400, details: dict | None = None):
    """Return standardized error payload.

    Shape:
        {
            "error": {
                "code": "...",
                "message": "...",
                "details": {...}  # optional
            }
        }
    """
    payload = {
        "error": {
            "code": code,
            "message": message,
        }
    }
    if details is not None:
        payload["error"]["details"] = details
    return jsonify(payload), status
