from __future__ import annotations

# Re-export sandbox crypto for AI module — same AES-256-GCM approach
from importlib import import_module

_sandbox_crypto = import_module("backend.10_sandbox.02_connectors.crypto")

encrypt_value = _sandbox_crypto.encrypt_value
decrypt_value = _sandbox_crypto.decrypt_value
parse_encryption_key = _sandbox_crypto.parse_encryption_key
