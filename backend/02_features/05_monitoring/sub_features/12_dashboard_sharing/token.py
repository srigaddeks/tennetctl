"""Token minting and verification for dashboard share tokens.

Pure HMAC-SHA256 stateless verification with Vault key rotation support.
Format: v{key_version}.{payload_b64}.{sig_b64} (base64url, no padding).
Plaintext token NEVER stored; only hash is persisted.
"""

import base64
import hashlib
import hmac
import json
import struct
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class ShareClaim:
    """Verified share token claim."""

    share_id: str
    exp: float
    key_version: int


class InvalidToken(Exception):
    """Token verification failed."""

    pass


def _b64url_encode(data: bytes) -> str:
    """Base64url encode without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    """Base64url decode, adding padding as needed."""
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data)


def mint(
    share_id: str, exp: float, key_version: int, secret_bytes: bytes
) -> str:
    """Mint a share token.

    Args:
        share_id: UUID of the share grant
        exp: Unix timestamp of expiration
        key_version: Vault key version for rotation
        secret_bytes: Signing secret (32+ bytes for HMAC-SHA256)

    Returns:
        Token string in format v{key_version}.{payload_b64}.{sig_b64}
    """
    # Payload: share_id (UUID as bytes, 16 bytes) + exp (double, 8 bytes) + key_version (uint16, 2 bytes)
    payload = share_id.encode("utf-8")[:36] + struct.pack(">d", exp) + struct.pack(
        ">H", key_version
    )
    payload_b64 = _b64url_encode(payload)

    # Signature over version.payload
    message = f"v{key_version}.{payload_b64}".encode("utf-8")
    sig = hmac.new(secret_bytes, message, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(sig)

    return f"v{key_version}.{payload_b64}.{sig_b64}"


def verify(
    token_str: str, secret_resolver: Callable[[int], bytes]
) -> ShareClaim:
    """Verify a share token.

    Args:
        token_str: Token string
        secret_resolver: Callable(key_version) -> secret_bytes

    Returns:
        ShareClaim if valid

    Raises:
        InvalidToken if verification fails
    """
    try:
        parts = token_str.split(".")
        if len(parts) != 3 or parts[0] != "v1":
            raise ValueError("Invalid format")

        key_version = 1
        payload_b64 = parts[1]
        sig_b64 = parts[2]

        # Decode payload
        payload = _b64url_decode(payload_b64)
        if len(payload) < 26:  # 36 (share_id) + 8 (exp) + 2 (key_version) minimum
            raise ValueError("Payload too short")

        share_id = payload[:36].decode("utf-8", errors="ignore").rstrip("\x00")
        exp = struct.unpack(">d", payload[36:44])[0]
        payload_key_version = struct.unpack(">H", payload[44:46])[0]

        # Resolve secret and verify signature
        secret = secret_resolver(payload_key_version)
        message = f"v{key_version}.{payload_b64}".encode("utf-8")
        expected_sig = hmac.new(secret, message, hashlib.sha256).digest()
        actual_sig = _b64url_decode(sig_b64)

        if not hmac.compare_digest(expected_sig, actual_sig):
            raise ValueError("Signature mismatch")

        return ShareClaim(share_id=share_id, exp=exp, key_version=payload_key_version)

    except Exception as e:
        raise InvalidToken(f"Token verification failed: {e}") from e


def hash_token(token: str) -> str:
    """Hash token for storage (SHA256, hex)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
