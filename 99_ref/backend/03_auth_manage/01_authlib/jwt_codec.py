from __future__ import annotations

from base64 import urlsafe_b64decode
from collections import OrderedDict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import json
import threading
import time
from uuid import uuid4

from authlib.jose import JoseError, jwt, JsonWebKey

from importlib import import_module


_telemetry_module = import_module("backend.01_core.telemetry")
_logging_module = import_module("backend.01_core.logging_utils")
instrument_class_methods = _telemetry_module.instrument_class_methods
get_logger = _logging_module.get_logger

_LOGGER = get_logger("backend.auth.jwt")


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class EncodedToken:
    token: str
    expires_at: datetime
    jti: str | None = None


@dataclass(frozen=True, slots=True)
class KeyEntry:
    """A single key in the key store."""
    kid: str
    algorithm: str
    sign_key: object  # str for HMAC, private key object for RSA/EC
    verify_key: object  # str for HMAC, public key object for RSA/EC


# ---------------------------------------------------------------------------
# Key Store — manages signing/verification keys with rotation support
# ---------------------------------------------------------------------------

class KeyStore:
    """
    Holds multiple named keys for JWT signing and verification.

    - One key is designated as the *signing key* (used for new tokens).
    - All keys are available for *verification* (so old tokens signed with
      a rotated-out key can still be validated until they expire).
    """

    def __init__(self) -> None:
        self._keys: dict[str, KeyEntry] = {}
        self._signing_kid: str | None = None

    def add_hmac_key(self, kid: str, secret: str, *, algorithm: str = "HS256") -> None:
        self._keys[kid] = KeyEntry(kid=kid, algorithm=algorithm, sign_key=secret, verify_key=secret)

    def add_asymmetric_key(
        self,
        kid: str,
        *,
        algorithm: str,
        private_key_pem: str | None = None,
        public_key_pem: str,
    ) -> None:
        verify_key = JsonWebKey.import_key(public_key_pem, {"kty": "RSA" if algorithm == "RS256" else "EC"})
        sign_key = None
        if private_key_pem:
            sign_key = JsonWebKey.import_key(private_key_pem, {"kty": "RSA" if algorithm == "RS256" else "EC"})
        self._keys[kid] = KeyEntry(kid=kid, algorithm=algorithm, sign_key=sign_key, verify_key=verify_key)

    def set_signing_key(self, kid: str) -> None:
        if kid not in self._keys:
            raise ValueError(f"Key '{kid}' not found in key store.")
        entry = self._keys[kid]
        if entry.sign_key is None:
            raise ValueError(f"Key '{kid}' has no signing key (public-key only).")
        self._signing_kid = kid

    @property
    def signing_entry(self) -> KeyEntry:
        if self._signing_kid is None:
            raise RuntimeError("No signing key configured.")
        return self._keys[self._signing_kid]

    def get_verification_entry(self, kid: str) -> KeyEntry | None:
        return self._keys.get(kid)

    @property
    def key_ids(self) -> list[str]:
        return list(self._keys.keys())

    @classmethod
    def from_settings(cls, settings) -> KeyStore:
        """
        Build a KeyStore from Settings.

        Supports three modes:
        1. Multi-key HMAC: AUTH_ACCESS_TOKEN_KEYS={"kid1":"secret1","kid2":"secret2"}
           with AUTH_ACCESS_TOKEN_SIGNING_KEY_ID=kid1
        2. Asymmetric: AUTH_ACCESS_TOKEN_PRIVATE_KEY + AUTH_ACCESS_TOKEN_PUBLIC_KEY
        3. Legacy single-secret: AUTH_ACCESS_TOKEN_SECRET (auto-assigned kid="default")
        """
        store = cls()
        algorithm = settings.access_token_algorithm

        if settings.access_token_keys:
            for kid, secret in settings.access_token_keys.items():
                store.add_hmac_key(kid, secret, algorithm=algorithm)
            signing_kid = settings.access_token_signing_key_id
            if signing_kid is None:
                signing_kid = next(iter(settings.access_token_keys))
            store.set_signing_key(signing_kid)
        elif algorithm in ("RS256", "ES256"):
            kid = settings.access_token_signing_key_id or "default"
            if not settings.access_token_public_key:
                raise ValueError("AUTH_ACCESS_TOKEN_PUBLIC_KEY is required for asymmetric algorithms.")
            store.add_asymmetric_key(
                kid,
                algorithm=algorithm,
                private_key_pem=settings.access_token_private_key,
                public_key_pem=settings.access_token_public_key,
            )
            if settings.access_token_private_key:
                store.set_signing_key(kid)
        else:
            kid = settings.access_token_signing_key_id or "default"
            store.add_hmac_key(kid, settings.access_token_secret, algorithm=algorithm)
            store.set_signing_key(kid)

        return store


# ---------------------------------------------------------------------------
# JTI Blocklist — in-memory revoked token tracker
# ---------------------------------------------------------------------------

class JTIBlocklist:
    """
    In-memory blocklist for revoked JWT IDs (jti claims).

    Entries auto-expire based on the token's original expiration time.
    Thread-safe via a lock.
    """

    def __init__(self, *, max_size: int = 100_000) -> None:
        self._entries: OrderedDict[str, float] = OrderedDict()
        self._max_size = max_size
        self._lock = threading.Lock()

    def revoke(self, jti: str, expires_at: datetime) -> None:
        exp_ts = expires_at.timestamp()
        with self._lock:
            self._entries[jti] = exp_ts
            if len(self._entries) > self._max_size:
                self._entries.popitem(last=False)

    def is_revoked(self, jti: str) -> bool:
        with self._lock:
            exp_ts = self._entries.get(jti)
            if exp_ts is None:
                return False
            if time.time() > exp_ts:
                del self._entries[jti]
                return False
            return True

    def cleanup(self) -> int:
        """Remove expired entries. Returns count removed."""
        now = time.time()
        removed = 0
        with self._lock:
            expired = [jti for jti, exp in self._entries.items() if now > exp]
            for jti in expired:
                del self._entries[jti]
                removed += 1
        return removed

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._entries)


# ---------------------------------------------------------------------------
# JWT Codec — encode/decode with multi-key, asymmetric, JTI support
# ---------------------------------------------------------------------------

@instrument_class_methods(namespace="auth.jwt_codec", logger_name="backend.auth.jwt.instrumentation")
class JWTCodec:
    def __init__(
        self,
        *,
        secret: str | None = None,
        algorithm: str = "HS256",
        issuer: str,
        audience: str,
        ttl_seconds: int,
        key_store: KeyStore | None = None,
        jti_blocklist: JTIBlocklist | None = None,
        enable_jti: bool = False,
    ) -> None:
        self._algorithm = algorithm
        self._issuer = issuer
        self._audience = audience
        self._ttl_seconds = ttl_seconds
        self._jti_blocklist = jti_blocklist
        self._enable_jti = enable_jti or (jti_blocklist is not None)

        if key_store is not None:
            self._key_store = key_store
        else:
            self._key_store = KeyStore()
            if secret:
                self._key_store.add_hmac_key("default", secret, algorithm=algorithm)
                self._key_store.set_signing_key("default")

    @property
    def jti_blocklist(self) -> JTIBlocklist | None:
        return self._jti_blocklist

    def encode_access_token(
        self,
        *,
        subject: str,
        session_id: str,
        tenant_key: str,
        extra_claims: dict[str, object] | None = None,
        ttl_override: int | None = None,
    ) -> EncodedToken:
        issued_at = datetime.now(tz=UTC)
        ttl = ttl_override if ttl_override is not None else self._ttl_seconds
        expires_at = issued_at + timedelta(seconds=ttl)

        signing_entry = self._key_store.signing_entry
        jti = str(uuid4()) if self._enable_jti else None

        claims: dict[str, object] = {
            "sub": subject,
            "sid": session_id,
            "tid": tenant_key,
            "typ": "access",
            "iss": self._issuer,
            "aud": self._audience,
            "iat": int(issued_at.timestamp()),
            "exp": int(expires_at.timestamp()),
        }
        if jti is not None:
            claims["jti"] = jti
        if extra_claims:
            claims.update(extra_claims)

        header = {"alg": signing_entry.algorithm, "typ": "JWT", "kid": signing_entry.kid}
        token = jwt.encode(header, claims, signing_entry.sign_key)
        return EncodedToken(
            token=token.decode("utf-8") if isinstance(token, bytes) else str(token),
            expires_at=expires_at,
            jti=jti,
        )

    def decode_access_token(self, token: str) -> dict[str, object]:
        header = self._decode_header(token)
        kid = header.get("kid")
        alg = header.get("alg")

        if header.get("typ") != "JWT":
            raise ValueError("invalid jwt header type")

        # Resolve the verification key
        if kid is not None:
            entry = self._key_store.get_verification_entry(str(kid))
            if entry is None:
                raise ValueError(f"unknown key id: {kid}")
            if alg != entry.algorithm:
                raise ValueError("algorithm mismatch for key")
            verify_key = entry.verify_key
        else:
            # Fallback: legacy tokens without kid — use signing key
            entry = self._key_store.signing_entry
            if alg != entry.algorithm:
                raise ValueError("invalid algorithm")
            verify_key = entry.verify_key

        try:
            claims = dict(jwt.decode(token, verify_key))
        except JoseError as exc:
            raise ValueError("invalid access token") from exc

        now = int(datetime.now(tz=UTC).timestamp())
        if claims.get("typ") != "access":
            raise ValueError("invalid token type")
        if claims.get("iss") != self._issuer:
            raise ValueError("invalid issuer")
        if claims.get("aud") != self._audience:
            raise ValueError("invalid audience")
        exp = claims.get("exp")
        if not isinstance(exp, int) or exp <= now:
            raise ValueError("token expired")

        # JTI blocklist check
        jti = claims.get("jti")
        if jti is not None and self._jti_blocklist is not None:
            if self._jti_blocklist.is_revoked(str(jti)):
                raise ValueError("token has been revoked")

        return claims

    @staticmethod
    def _decode_header(token: str) -> dict[str, object]:
        try:
            encoded_header = token.split(".", 1)[0]
            padding = "=" * (-len(encoded_header) % 4)
            raw_header = urlsafe_b64decode(f"{encoded_header}{padding}".encode("utf-8"))
            header = json.loads(raw_header.decode("utf-8"))
        except (IndexError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("invalid token header") from exc
        if not isinstance(header, dict):
            raise ValueError("invalid token header")
        return header
