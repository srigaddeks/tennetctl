"""
AES-256-GCM envelope encryption for vault secrets.

Every secret has its own 32-byte DEK (data encryption key). The DEK encrypts
the plaintext with a fresh 12-byte nonce. The root key (TENNETCTL_VAULT_ROOT_KEY)
encrypts the DEK with its own fresh 12-byte nonce. What we persist per row is:

    ciphertext    = AESGCM(dek).encrypt(data_nonce, plaintext)
    wrapped_dek   = wrap_nonce || AESGCM(root_key).encrypt(wrap_nonce, dek)
    nonce         = data_nonce

See ADR-028 for the full rationale. Primitives come from PyCA `cryptography`.
Do not roll your own.
"""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_KEY_BYTES = 32      # AES-256
_NONCE_BYTES = 12    # GCM recommended


@dataclass(frozen=True)
class Envelope:
    """Persisted shape for an encrypted secret — these three go into fct_vault_entries."""
    ciphertext: bytes
    wrapped_dek: bytes   # wrap_nonce (12 bytes) || AESGCM(root_key).encrypt(wrap_nonce, dek)
    nonce: bytes         # data nonce (12 bytes)


def load_root_key() -> bytes:
    """Read + validate TENNETCTL_VAULT_ROOT_KEY. Raises RuntimeError if missing/malformed."""
    b64 = os.environ.get("TENNETCTL_VAULT_ROOT_KEY")
    if not b64:
        raise RuntimeError(
            "TENNETCTL_VAULT_ROOT_KEY is required. Generate one: "
            "python -c 'import os,base64; print(base64.b64encode(os.urandom(32)).decode())'"
        )
    try:
        raw = base64.b64decode(b64, validate=True)
    except Exception as exc:
        raise RuntimeError(
            "TENNETCTL_VAULT_ROOT_KEY is not valid base64."
        ) from exc
    if len(raw) != _KEY_BYTES:
        raise RuntimeError(
            f"TENNETCTL_VAULT_ROOT_KEY must decode to {_KEY_BYTES} bytes; got {len(raw)}."
        )
    return raw


def encrypt(plaintext: str, root_key: bytes) -> Envelope:
    """Envelope-encrypt a plaintext string. Fresh DEK + fresh nonce per call."""
    if not plaintext:
        raise ValueError("vault rejects empty plaintext")
    if len(root_key) != _KEY_BYTES:
        raise ValueError(f"root_key must be {_KEY_BYTES} bytes; got {len(root_key)}")

    dek = os.urandom(_KEY_BYTES)
    data_nonce = os.urandom(_NONCE_BYTES)
    ciphertext = AESGCM(dek).encrypt(data_nonce, plaintext.encode("utf-8"), None)

    wrap_nonce = os.urandom(_NONCE_BYTES)
    wrapped = AESGCM(root_key).encrypt(wrap_nonce, dek, None)
    return Envelope(
        ciphertext=ciphertext,
        wrapped_dek=wrap_nonce + wrapped,
        nonce=data_nonce,
    )


def decrypt(env: Envelope, root_key: bytes) -> str:
    """Reverse of encrypt. Raises cryptography.exceptions.InvalidTag on any tamper."""
    if len(root_key) != _KEY_BYTES:
        raise ValueError(f"root_key must be {_KEY_BYTES} bytes; got {len(root_key)}")
    if len(env.nonce) != _NONCE_BYTES:
        raise ValueError(f"nonce must be {_NONCE_BYTES} bytes")
    if len(env.wrapped_dek) < _NONCE_BYTES + _KEY_BYTES:
        raise ValueError("wrapped_dek too short")

    wrap_nonce = env.wrapped_dek[:_NONCE_BYTES]
    wrapped = env.wrapped_dek[_NONCE_BYTES:]
    dek = AESGCM(root_key).decrypt(wrap_nonce, wrapped, None)
    try:
        plaintext = AESGCM(dek).decrypt(env.nonce, env.ciphertext, None)
        return plaintext.decode("utf-8")
    finally:
        del dek
