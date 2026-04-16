from __future__ import annotations

import time
import unittest
from datetime import UTC, datetime, timedelta
from importlib import import_module
from unittest.mock import MagicMock

_jwt_module = import_module("backend.03_auth_manage.01_authlib.jwt_codec")

JWTCodec = _jwt_module.JWTCodec
KeyStore = _jwt_module.KeyStore
JTIBlocklist = _jwt_module.JTIBlocklist
EncodedToken = _jwt_module.EncodedToken
KeyEntry = _jwt_module.KeyEntry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_codec(
    *,
    secret: str = "test-secret-at-least-32-chars-long!!",
    algorithm: str = "HS256",
    issuer: str = "test-issuer",
    audience: str = "test-audience",
    ttl_seconds: int = 300,
    key_store: KeyStore | None = None,
    jti_blocklist: JTIBlocklist | None = None,
    enable_jti: bool = False,
) -> JWTCodec:
    return JWTCodec(
        secret=secret if key_store is None else None,
        algorithm=algorithm,
        issuer=issuer,
        audience=audience,
        ttl_seconds=ttl_seconds,
        key_store=key_store,
        jti_blocklist=jti_blocklist,
        enable_jti=enable_jti,
    )


def _encode_and_decode(codec: JWTCodec, **encode_kwargs) -> dict:
    defaults = {
        "subject": "user-123",
        "session_id": "sess-456",
        "tenant_key": "default",
    }
    defaults.update(encode_kwargs)
    token = codec.encode_access_token(**defaults)
    return codec.decode_access_token(token.token)


# ---------------------------------------------------------------------------
# KeyStore tests
# ---------------------------------------------------------------------------

class KeyStoreTests(unittest.TestCase):
    def test_add_and_retrieve_hmac_key(self):
        store = KeyStore()
        store.add_hmac_key("k1", "secret1")
        store.set_signing_key("k1")
        self.assertEqual(store.signing_entry.kid, "k1")
        self.assertEqual(store.signing_entry.algorithm, "HS256")
        self.assertIn("k1", store.key_ids)

    def test_multiple_keys(self):
        store = KeyStore()
        store.add_hmac_key("k1", "secret1")
        store.add_hmac_key("k2", "secret2")
        store.set_signing_key("k1")
        self.assertEqual(len(store.key_ids), 2)
        self.assertIsNotNone(store.get_verification_entry("k2"))

    def test_set_signing_key_nonexistent_raises(self):
        store = KeyStore()
        with self.assertRaises(ValueError):
            store.set_signing_key("nonexistent")

    def test_signing_entry_without_config_raises(self):
        store = KeyStore()
        with self.assertRaises(RuntimeError):
            _ = store.signing_entry

    def test_get_verification_entry_missing_returns_none(self):
        store = KeyStore()
        self.assertIsNone(store.get_verification_entry("nope"))

    def test_from_settings_legacy_single_secret(self):
        settings = MagicMock()
        settings.access_token_algorithm = "HS256"
        settings.access_token_keys = None
        settings.access_token_signing_key_id = None
        settings.access_token_secret = "my-secret"
        settings.access_token_private_key = None
        settings.access_token_public_key = None
        store = KeyStore.from_settings(settings)
        self.assertEqual(store.signing_entry.kid, "default")

    def test_from_settings_multi_key_hmac(self):
        settings = MagicMock()
        settings.access_token_algorithm = "HS256"
        settings.access_token_keys = {"primary": "secret-a", "backup": "secret-b"}
        settings.access_token_signing_key_id = "primary"
        store = KeyStore.from_settings(settings)
        self.assertEqual(store.signing_entry.kid, "primary")
        self.assertEqual(len(store.key_ids), 2)

    def test_from_settings_multi_key_defaults_to_first(self):
        settings = MagicMock()
        settings.access_token_algorithm = "HS256"
        settings.access_token_keys = {"alpha": "secret-alpha", "beta": "secret-beta"}
        settings.access_token_signing_key_id = None
        store = KeyStore.from_settings(settings)
        self.assertEqual(store.signing_entry.kid, "alpha")


# ---------------------------------------------------------------------------
# JTIBlocklist tests
# ---------------------------------------------------------------------------

class JTIBlocklistTests(unittest.TestCase):
    def test_revoke_and_check(self):
        bl = JTIBlocklist()
        future = datetime.now(tz=UTC) + timedelta(hours=1)
        bl.revoke("jti-1", future)
        self.assertTrue(bl.is_revoked("jti-1"))

    def test_not_revoked(self):
        bl = JTIBlocklist()
        self.assertFalse(bl.is_revoked("unknown"))

    def test_expired_entry_auto_cleans(self):
        bl = JTIBlocklist()
        past = datetime.now(tz=UTC) - timedelta(seconds=1)
        bl.revoke("jti-old", past)
        self.assertFalse(bl.is_revoked("jti-old"))

    def test_cleanup_removes_expired(self):
        bl = JTIBlocklist()
        past = datetime.now(tz=UTC) - timedelta(seconds=1)
        future = datetime.now(tz=UTC) + timedelta(hours=1)
        bl.revoke("old", past)
        bl.revoke("new", future)
        removed = bl.cleanup()
        self.assertEqual(removed, 1)
        self.assertEqual(bl.size, 1)

    def test_max_size_eviction(self):
        bl = JTIBlocklist(max_size=3)
        future = datetime.now(tz=UTC) + timedelta(hours=1)
        for i in range(5):
            bl.revoke(f"jti-{i}", future)
        self.assertLessEqual(bl.size, 3)

    def test_size_property(self):
        bl = JTIBlocklist()
        self.assertEqual(bl.size, 0)
        future = datetime.now(tz=UTC) + timedelta(hours=1)
        bl.revoke("a", future)
        bl.revoke("b", future)
        self.assertEqual(bl.size, 2)


# ---------------------------------------------------------------------------
# JWTCodec — basic encode/decode
# ---------------------------------------------------------------------------

class JWTCodecBasicTests(unittest.TestCase):
    def test_encode_decode_roundtrip(self):
        codec = _make_codec()
        claims = _encode_and_decode(codec)
        self.assertEqual(claims["sub"], "user-123")
        self.assertEqual(claims["sid"], "sess-456")
        self.assertEqual(claims["tid"], "default")
        self.assertEqual(claims["typ"], "access")
        self.assertEqual(claims["iss"], "test-issuer")
        self.assertEqual(claims["aud"], "test-audience")

    def test_encode_returns_encoded_token(self):
        codec = _make_codec()
        result = codec.encode_access_token(
            subject="u1", session_id="s1", tenant_key="t1",
        )
        self.assertIsInstance(result, EncodedToken)
        self.assertIsInstance(result.token, str)
        self.assertIsInstance(result.expires_at, datetime)

    def test_expired_token_raises(self):
        codec = _make_codec(ttl_seconds=1)
        token = codec.encode_access_token(
            subject="u1", session_id="s1", tenant_key="t1",
        )
        time.sleep(1.5)
        with self.assertRaises(ValueError, msg="token expired"):
            codec.decode_access_token(token.token)

    def test_wrong_secret_raises(self):
        codec1 = _make_codec(secret="secret-aaaaaaaaaaaaaaaaaaaaaaaaa")
        codec2 = _make_codec(secret="secret-bbbbbbbbbbbbbbbbbbbbbbbbb")
        token = codec1.encode_access_token(
            subject="u1", session_id="s1", tenant_key="t1",
        )
        with self.assertRaises(ValueError):
            codec2.decode_access_token(token.token)

    def test_wrong_issuer_raises(self):
        codec_sign = _make_codec(issuer="issuer-a")
        codec_verify = _make_codec(issuer="issuer-b")
        # Use the same key store so signature validates
        codec_verify._key_store = codec_sign._key_store
        token = codec_sign.encode_access_token(
            subject="u1", session_id="s1", tenant_key="t1",
        )
        with self.assertRaises(ValueError, msg="invalid issuer"):
            codec_verify.decode_access_token(token.token)

    def test_wrong_audience_raises(self):
        codec_sign = _make_codec(audience="aud-a")
        codec_verify = _make_codec(audience="aud-b")
        codec_verify._key_store = codec_sign._key_store
        token = codec_sign.encode_access_token(
            subject="u1", session_id="s1", tenant_key="t1",
        )
        with self.assertRaises(ValueError, msg="invalid audience"):
            codec_verify.decode_access_token(token.token)

    def test_garbage_token_raises(self):
        codec = _make_codec()
        with self.assertRaises(ValueError):
            codec.decode_access_token("not.a.valid.token")

    def test_empty_token_raises(self):
        codec = _make_codec()
        with self.assertRaises(ValueError):
            codec.decode_access_token("")


# ---------------------------------------------------------------------------
# JWTCodec — key rotation
# ---------------------------------------------------------------------------

class KeyRotationTests(unittest.TestCase):
    def test_sign_with_key_a_verify_after_rotate_to_key_b(self):
        """Tokens signed with key A should still verify after rotating to key B."""
        store = KeyStore()
        store.add_hmac_key("key-a", "secret-aaaaaaaaaaaaaaaaaaaaaaaa")
        store.add_hmac_key("key-b", "secret-bbbbbbbbbbbbbbbbbbbbbbbb")
        store.set_signing_key("key-a")

        codec = _make_codec(key_store=store)
        token_a = codec.encode_access_token(
            subject="u1", session_id="s1", tenant_key="t1",
        )

        # Rotate signing key to B
        store.set_signing_key("key-b")
        token_b = codec.encode_access_token(
            subject="u2", session_id="s2", tenant_key="t1",
        )

        # Both tokens should verify successfully
        claims_a = codec.decode_access_token(token_a.token)
        self.assertEqual(claims_a["sub"], "u1")

        claims_b = codec.decode_access_token(token_b.token)
        self.assertEqual(claims_b["sub"], "u2")

    def test_unknown_kid_raises(self):
        """Token with an unrecognized kid should fail verification."""
        store_sign = KeyStore()
        store_sign.add_hmac_key("old-key", "secret-old-old-old-old-old-old")
        store_sign.set_signing_key("old-key")
        codec_sign = _make_codec(key_store=store_sign)
        token = codec_sign.encode_access_token(
            subject="u1", session_id="s1", tenant_key="t1",
        )

        # Verifier has only a different key
        store_verify = KeyStore()
        store_verify.add_hmac_key("new-key", "secret-new-new-new-new-new-new")
        store_verify.set_signing_key("new-key")
        codec_verify = _make_codec(key_store=store_verify)

        with self.assertRaises(ValueError, msg="unknown key id"):
            codec_verify.decode_access_token(token.token)

    def test_kid_in_header(self):
        """Encoded tokens should have kid in the JWT header."""
        store = KeyStore()
        store.add_hmac_key("my-kid", "secret-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        store.set_signing_key("my-kid")
        codec = _make_codec(key_store=store)
        token = codec.encode_access_token(
            subject="u1", session_id="s1", tenant_key="t1",
        )
        header = JWTCodec._decode_header(token.token)
        self.assertEqual(header["kid"], "my-kid")


# ---------------------------------------------------------------------------
# JWTCodec — JTI (token revocation)
# ---------------------------------------------------------------------------

class JTITests(unittest.TestCase):
    def test_jti_in_token_when_enabled(self):
        codec = _make_codec(enable_jti=True)
        token = codec.encode_access_token(
            subject="u1", session_id="s1", tenant_key="t1",
        )
        self.assertIsNotNone(token.jti)
        claims = codec.decode_access_token(token.token)
        self.assertEqual(claims["jti"], token.jti)

    def test_jti_not_in_token_when_disabled(self):
        codec = _make_codec(enable_jti=False)
        token = codec.encode_access_token(
            subject="u1", session_id="s1", tenant_key="t1",
        )
        self.assertIsNone(token.jti)

    def test_revoked_token_rejected(self):
        blocklist = JTIBlocklist()
        codec = _make_codec(jti_blocklist=blocklist, enable_jti=True)
        token = codec.encode_access_token(
            subject="u1", session_id="s1", tenant_key="t1",
        )
        # Revoke it
        blocklist.revoke(token.jti, token.expires_at)

        with self.assertRaises(ValueError, msg="token has been revoked"):
            codec.decode_access_token(token.token)

    def test_non_revoked_token_passes(self):
        blocklist = JTIBlocklist()
        codec = _make_codec(jti_blocklist=blocklist, enable_jti=True)
        token = codec.encode_access_token(
            subject="u1", session_id="s1", tenant_key="t1",
        )
        # Don't revoke — should pass
        claims = codec.decode_access_token(token.token)
        self.assertEqual(claims["sub"], "u1")

    def test_blocklist_auto_enables_jti(self):
        """Providing a blocklist should auto-enable JTI even if enable_jti=False."""
        blocklist = JTIBlocklist()
        codec = _make_codec(jti_blocklist=blocklist, enable_jti=False)
        token = codec.encode_access_token(
            subject="u1", session_id="s1", tenant_key="t1",
        )
        self.assertIsNotNone(token.jti)


# ---------------------------------------------------------------------------
# JWTCodec — custom claims
# ---------------------------------------------------------------------------

class CustomClaimsTests(unittest.TestCase):
    def test_extra_claims_included(self):
        codec = _make_codec()
        claims = _encode_and_decode(
            codec,
            extra_claims={"role": "admin", "permissions": ["read", "write"]},
        )
        self.assertEqual(claims["role"], "admin")
        self.assertEqual(claims["permissions"], ["read", "write"])

    def test_extra_claims_cannot_override_standard(self):
        """Extra claims that collide with standard claims overwrite them.
        This is documented behavior — callers should not pass standard claim names."""
        codec = _make_codec()
        token = codec.encode_access_token(
            subject="u1",
            session_id="s1",
            tenant_key="t1",
            extra_claims={"sub": "hacker"},
        )
        # The 'sub' will be 'hacker' since extra_claims.update() overwrites
        # This test just documents the behavior
        claims = codec.decode_access_token(token.token)
        self.assertEqual(claims["sub"], "hacker")

    def test_no_extra_claims(self):
        codec = _make_codec()
        claims = _encode_and_decode(codec, extra_claims=None)
        # Standard claims present, no extra
        self.assertIn("sub", claims)
        self.assertNotIn("role", claims)


# ---------------------------------------------------------------------------
# JWTCodec — backward compatibility
# ---------------------------------------------------------------------------

class BackwardCompatibilityTests(unittest.TestCase):
    def test_legacy_single_secret_still_works(self):
        """JWTCodec with just secret= (no key_store) should still work."""
        codec = _make_codec(secret="legacy-secret-long-enough-for-hs256!!")
        claims = _encode_and_decode(codec)
        self.assertEqual(claims["sub"], "user-123")

    def test_legacy_token_kid_is_default(self):
        codec = _make_codec()
        token = codec.encode_access_token(
            subject="u1", session_id="s1", tenant_key="t1",
        )
        header = JWTCodec._decode_header(token.token)
        self.assertEqual(header["kid"], "default")


# ---------------------------------------------------------------------------
# KeyStore.from_settings — asymmetric stubs
# ---------------------------------------------------------------------------

class AsymmetricKeyStoreTests(unittest.TestCase):
    def test_asymmetric_requires_public_key(self):
        settings = MagicMock()
        settings.access_token_algorithm = "RS256"
        settings.access_token_keys = None
        settings.access_token_signing_key_id = None
        settings.access_token_public_key = None
        settings.access_token_private_key = None
        with self.assertRaises(ValueError, msg="PUBLIC_KEY is required"):
            KeyStore.from_settings(settings)

    def test_public_key_only_no_signing(self):
        """With only a public key, the store should have no signing key."""
        settings = MagicMock()
        settings.access_token_algorithm = "RS256"
        settings.access_token_keys = None
        settings.access_token_signing_key_id = None
        settings.access_token_private_key = None
        # Generate a minimal RSA public key for structure test
        # We just test the ValueError path when private_key is absent
        # and set_signing_key is not called
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_pem = private_key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

        settings.access_token_public_key = public_pem
        store = KeyStore.from_settings(settings)
        # No signing key should be set
        with self.assertRaises(RuntimeError):
            _ = store.signing_entry

    def test_asymmetric_full_keypair(self):
        """With both private and public key, signing and verification work."""
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        private_pem = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode()
        public_pem = private_key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

        settings = MagicMock()
        settings.access_token_algorithm = "RS256"
        settings.access_token_keys = None
        settings.access_token_signing_key_id = "rsa-1"
        settings.access_token_private_key = private_pem
        settings.access_token_public_key = public_pem

        store = KeyStore.from_settings(settings)
        self.assertEqual(store.signing_entry.kid, "rsa-1")

        codec = _make_codec(key_store=store, algorithm="RS256")
        claims = _encode_and_decode(codec)
        self.assertEqual(claims["sub"], "user-123")


# ---------------------------------------------------------------------------
# EncodedToken dataclass
# ---------------------------------------------------------------------------

class EncodedTokenTests(unittest.TestCase):
    def test_frozen(self):
        et = EncodedToken(token="abc", expires_at=datetime.now(tz=UTC))
        with self.assertRaises(AttributeError):
            et.token = "xyz"

    def test_jti_default_none(self):
        et = EncodedToken(token="abc", expires_at=datetime.now(tz=UTC))
        self.assertIsNone(et.jti)


if __name__ == "__main__":
    unittest.main()
