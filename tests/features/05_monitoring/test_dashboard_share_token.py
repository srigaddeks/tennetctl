"""Tests for token minting and verification."""

import hashlib
import struct
import time

import pytest

from backend.02_features.05_monitoring.sub_features.12_dashboard_sharing.token import (
    InvalidToken,
    ShareClaim,
    hash_token,
    mint,
    verify,
)


class TestTokenMinting:
    """Test token minting."""

    def test_mint_token(self):
        """Mint a valid token."""
        share_id = "test-share-uuid-v7"
        exp = time.time() + 86400
        key_version = 1
        secret = b"test-secret-32-bytes-minimum-key"

        token = mint(share_id, exp, key_version, secret)

        assert token is not None
        assert token.startswith("v1.")
        parts = token.split(".")
        assert len(parts) == 3

    def test_hash_token(self):
        """Hash token for storage."""
        token = "v1.test.payload"
        token_hash = hash_token(token)

        assert len(token_hash) == 64  # SHA256 hex
        assert token_hash == hashlib.sha256(token.encode()).hexdigest()

    def test_token_format(self):
        """Token format is v{version}.{payload_b64}.{sig_b64}."""
        share_id = "test-share-id"
        exp = time.time() + 3600
        key_version = 1
        secret = b"test-secret-32-bytes-minimum-key"

        token = mint(share_id, exp, key_version, secret)

        parts = token.split(".")
        assert parts[0] == "v1"
        # payload_b64 and sig_b64 should be base64url
        assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in parts[1])
        assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in parts[2])


class TestTokenVerification:
    """Test token verification."""

    def test_verify_valid_token(self):
        """Verify a valid token."""
        share_id = "test-share-id"
        exp = time.time() + 3600
        key_version = 1
        secret = b"test-secret-32-bytes-minimum-key"

        token = mint(share_id, exp, key_version, secret)

        def secret_resolver(kv: int) -> bytes:
            if kv == 1:
                return secret
            raise ValueError(f"Unknown key version {kv}")

        claim = verify(token, secret_resolver)

        assert isinstance(claim, ShareClaim)
        assert claim.share_id == share_id
        assert claim.key_version == 1
        assert claim.exp == exp

    def test_verify_expired_token(self):
        """Verify accepts expired token (expiry check is caller's responsibility)."""
        share_id = "test-share-id"
        exp = time.time() - 3600  # Expired
        key_version = 1
        secret = b"test-secret-32-bytes-minimum-key"

        token = mint(share_id, exp, key_version, secret)

        def secret_resolver(kv: int) -> bytes:
            if kv == 1:
                return secret
            raise ValueError(f"Unknown key version {kv}")

        claim = verify(token, secret_resolver)
        assert claim.exp < time.time()  # Expired

    def test_verify_invalid_signature(self):
        """Reject token with invalid signature."""
        share_id = "test-share-id"
        exp = time.time() + 3600
        key_version = 1
        secret = b"test-secret-32-bytes-minimum-key"

        token = mint(share_id, exp, key_version, secret)

        # Corrupt the signature
        parts = token.split(".")
        corrupted = f"{parts[0]}.{parts[1]}.invalid_signature"

        def secret_resolver(kv: int) -> bytes:
            if kv == 1:
                return secret
            raise ValueError(f"Unknown key version {kv}")

        with pytest.raises(InvalidToken):
            verify(corrupted, secret_resolver)

    def test_verify_wrong_secret(self):
        """Reject token verified with wrong secret."""
        share_id = "test-share-id"
        exp = time.time() + 3600
        key_version = 1
        secret1 = b"test-secret-32-bytes-minimum-key"
        secret2 = b"wrong-secret-32-bytes-minimum-key"

        token = mint(share_id, exp, key_version, secret1)

        def secret_resolver(kv: int) -> bytes:
            if kv == 1:
                return secret2  # Wrong secret
            raise ValueError(f"Unknown key version {kv}")

        with pytest.raises(InvalidToken):
            verify(token, secret_resolver)

    def test_verify_malformed_token(self):
        """Reject malformed token."""

        def secret_resolver(kv: int) -> bytes:
            return b"test-secret"

        with pytest.raises(InvalidToken):
            verify("not.a.valid.token.format", secret_resolver)

        with pytest.raises(InvalidToken):
            verify("v1.only_two_parts", secret_resolver)
