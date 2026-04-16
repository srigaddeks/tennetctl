from __future__ import annotations

from dataclasses import dataclass
import hashlib
import secrets

from importlib import import_module


_telemetry_module = import_module("backend.01_core.telemetry")
instrument_class_methods = _telemetry_module.instrument_class_methods


@dataclass(frozen=True, slots=True)
class RefreshTokenParts:
    session_id: str
    secret: str


@instrument_class_methods(namespace="auth.refresh_tokens", logger_name="backend.auth.tokens.instrumentation")
class RefreshTokenManager:
    def generate(self, session_id: str) -> str:
        return f"{session_id}.{secrets.token_urlsafe(32)}"

    def parse(self, refresh_token: str) -> RefreshTokenParts:
        try:
            session_id, secret = refresh_token.split(".", 1)
        except ValueError as exc:
            raise ValueError("invalid refresh token format") from exc
        if not session_id or not secret:
            raise ValueError("invalid refresh token format")
        return RefreshTokenParts(session_id=session_id, secret=secret)

    def hash_secret(self, secret: str) -> str:
        return hashlib.sha256(secret.encode("utf-8")).hexdigest()
