"""
Unit tests for backend.02_features.02_vault.crypto — AES-256-GCM envelope encryption.

AC-2 (plan 07-01): round-trip, tamper-ciphertext, tamper-wrapped-dek, wrong-key,
two-calls-produce-different-ciphertexts.

Pure-compute tests; no DB, no pool. Runs under the default pytest config.
"""

from __future__ import annotations

import os
from importlib import import_module
from typing import Any

import pytest
from cryptography.exceptions import InvalidTag

_crypto: Any = import_module("backend.02_features.02_vault.crypto")


def _fresh_root_key() -> bytes:
    return os.urandom(32)


def test_round_trip() -> None:
    root = _fresh_root_key()
    env = _crypto.encrypt("hunter2", root)
    assert _crypto.decrypt(env, root) == "hunter2"


def test_tamper_ciphertext_fails() -> None:
    root = _fresh_root_key()
    env = _crypto.encrypt("hunter2", root)
    flipped = bytearray(env.ciphertext)
    flipped[0] ^= 0x01
    tampered = _crypto.Envelope(
        ciphertext=bytes(flipped),
        wrapped_dek=env.wrapped_dek,
        nonce=env.nonce,
    )
    with pytest.raises(InvalidTag):
        _crypto.decrypt(tampered, root)


def test_tamper_wrapped_dek_fails() -> None:
    root = _fresh_root_key()
    env = _crypto.encrypt("hunter2", root)
    flipped = bytearray(env.wrapped_dek)
    # Flip a byte in the encrypted-dek portion (after the 12-byte wrap_nonce).
    flipped[20] ^= 0x01
    tampered = _crypto.Envelope(
        ciphertext=env.ciphertext,
        wrapped_dek=bytes(flipped),
        nonce=env.nonce,
    )
    with pytest.raises(InvalidTag):
        _crypto.decrypt(tampered, root)


def test_wrong_root_key_fails() -> None:
    right = _fresh_root_key()
    wrong = _fresh_root_key()
    env = _crypto.encrypt("hunter2", right)
    with pytest.raises(InvalidTag):
        _crypto.decrypt(env, wrong)


def test_two_encrypts_differ() -> None:
    root = _fresh_root_key()
    a = _crypto.encrypt("hunter2", root)
    b = _crypto.encrypt("hunter2", root)
    # Fresh DEK + fresh nonce per call -> ciphertext + wrapped_dek + nonce all differ.
    assert a.ciphertext != b.ciphertext
    assert a.wrapped_dek != b.wrapped_dek
    assert a.nonce != b.nonce
    # Both still decrypt to the same plaintext.
    assert _crypto.decrypt(a, root) == "hunter2"
    assert _crypto.decrypt(b, root) == "hunter2"


def test_empty_plaintext_rejected() -> None:
    root = _fresh_root_key()
    with pytest.raises(ValueError):
        _crypto.encrypt("", root)


def test_load_root_key_missing() -> None:
    saved = os.environ.pop("TENNETCTL_VAULT_ROOT_KEY", None)
    try:
        with pytest.raises(RuntimeError, match="required"):
            _crypto.load_root_key()
    finally:
        if saved is not None:
            os.environ["TENNETCTL_VAULT_ROOT_KEY"] = saved


def test_load_root_key_wrong_length() -> None:
    import base64
    saved = os.environ.get("TENNETCTL_VAULT_ROOT_KEY")
    os.environ["TENNETCTL_VAULT_ROOT_KEY"] = base64.b64encode(os.urandom(16)).decode()
    try:
        with pytest.raises(RuntimeError, match="32 bytes"):
            _crypto.load_root_key()
    finally:
        if saved is not None:
            os.environ["TENNETCTL_VAULT_ROOT_KEY"] = saved
        else:
            os.environ.pop("TENNETCTL_VAULT_ROOT_KEY", None)


def test_load_root_key_not_base64() -> None:
    saved = os.environ.get("TENNETCTL_VAULT_ROOT_KEY")
    os.environ["TENNETCTL_VAULT_ROOT_KEY"] = "not!valid!base64!"
    try:
        with pytest.raises(RuntimeError, match="base64"):
            _crypto.load_root_key()
    finally:
        if saved is not None:
            os.environ["TENNETCTL_VAULT_ROOT_KEY"] = saved
        else:
            os.environ.pop("TENNETCTL_VAULT_ROOT_KEY", None)
