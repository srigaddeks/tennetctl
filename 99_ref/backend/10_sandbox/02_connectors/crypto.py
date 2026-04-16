from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def encrypt_value(plaintext: str, key: bytes) -> str:
    """Encrypt with AES-256-GCM. Returns base64(nonce + ciphertext + tag)."""
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ct).decode()


def decrypt_value(encrypted: str, key: bytes) -> str:
    """Decrypt AES-256-GCM. Input: base64(nonce + ciphertext + tag)."""
    raw = base64.b64decode(encrypted)
    nonce, ct = raw[:12], raw[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None).decode()


def parse_encryption_key(key_str: str) -> bytes:
    """Parse base64-encoded 32-byte key."""
    key = base64.b64decode(key_str)
    if len(key) != 32:
        raise ValueError("Encryption key must be 32 bytes")
    return key
