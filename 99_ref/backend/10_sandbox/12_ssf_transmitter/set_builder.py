from __future__ import annotations

import uuid
import time

import jwt


class SETBuilder:
    """Builds and signs Security Event Tokens (SETs) per RFC 8417."""

    def __init__(
        self,
        *,
        issuer: str,
        signing_key: str,
        key_id: str,
        algorithm: str = "RS256",
    ) -> None:
        self._issuer = issuer
        self._signing_key = signing_key
        self._key_id = key_id
        self._algorithm = algorithm

    def build_set(
        self,
        *,
        audience: str,
        subject_id: dict,
        event_uri: str,
        event_claims: dict,
        txn: str | None = None,
    ) -> tuple[str, str]:
        """Build and sign a SET JWT.

        Returns (token, jti).
        """
        jti = str(uuid.uuid4())
        payload = {
            "iss": self._issuer,
            "jti": jti,
            "iat": int(time.time()),
            "aud": audience,
            "txn": txn or jti,
            "sub_id": subject_id,
            "events": {
                event_uri: event_claims,
            },
        }
        headers = {"typ": "secevent+jwt", "kid": self._key_id}
        token = jwt.encode(
            payload,
            self._signing_key,
            algorithm=self._algorithm,
            headers=headers,
        )
        return token, jti
