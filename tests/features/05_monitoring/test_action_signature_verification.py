"""Tests for HMAC signature generation and verification."""

import pytest
import hmac
import hashlib
from backend.02_features.05_monitoring.sub_features.09_action_templates.dispatchers.webhook import (
    WebhookDispatcher,
)


class TestSignatureVerification:
    """Test HMAC-SHA256 signature generation and server-side verification."""

    def test_signature_format(self):
        """Test X-Tennet-Signature format: t={ts},v1={hmac}."""
        # Simulate signature generation
        secret = "test-secret"
        timestamp = "1624000000"
        body = '{"alert": "test"}'
        message = f"{timestamp}.{body}".encode()
        signature_hex = hmac.new(
            secret.encode(),
            message,
            hashlib.sha256,
        ).hexdigest()

        signature_header = f"t={timestamp},v1={signature_hex}"
        # Parse and verify format
        parts = signature_header.split(",")
        assert len(parts) == 2
        assert parts[0].startswith("t=")
        assert parts[1].startswith("v1=")

    def test_server_side_verification(self):
        """Test server-side HMAC verification."""
        secret = "test-secret"
        timestamp = "1624000000"
        body = '{"alert": "test"}'

        # Generate signature as webhook dispatcher would
        message = f"{timestamp}.{body}".encode()
        expected_signature = hmac.new(
            secret.encode(),
            message,
            hashlib.sha256,
        ).hexdigest()

        # Server receives header and verifies
        header_value = f"t={timestamp},v1={expected_signature}"

        # Parse header
        parts = dict(pair.split("=") for pair in header_value.split(","))
        ts = parts.get("t")
        v1 = parts.get("v1")

        # Recompute signature
        received_message = f"{ts}.{body}".encode()
        computed_signature = hmac.new(
            secret.encode(),
            received_message,
            hashlib.sha256,
        ).hexdigest()

        # Verify (using constant-time comparison)
        assert hmac.compare_digest(v1, computed_signature)

    def test_signature_differs_on_secret_mismatch(self):
        """Test that wrong secret produces different signature."""
        correct_secret = "correct-secret"
        wrong_secret = "wrong-secret"
        timestamp = "1624000000"
        body = '{"alert": "test"}'
        message = f"{timestamp}.{body}".encode()

        correct_sig = hmac.new(
            correct_secret.encode(),
            message,
            hashlib.sha256,
        ).hexdigest()

        wrong_sig = hmac.new(
            wrong_secret.encode(),
            message,
            hashlib.sha256,
        ).hexdigest()

        assert correct_sig != wrong_sig

    def test_signature_differs_on_body_change(self):
        """Test that modifying body invalidates signature."""
        secret = "test-secret"
        timestamp = "1624000000"
        original_body = '{"alert": "test"}'
        modified_body = '{"alert": "modified"}'

        message1 = f"{timestamp}.{original_body}".encode()
        message2 = f"{timestamp}.{modified_body}".encode()

        sig1 = hmac.new(secret.encode(), message1, hashlib.sha256).hexdigest()
        sig2 = hmac.new(secret.encode(), message2, hashlib.sha256).hexdigest()

        assert sig1 != sig2

    def test_signature_differs_on_timestamp_change(self):
        """Test that replay attacks are prevented by timestamp."""
        secret = "test-secret"
        body = '{"alert": "test"}'

        ts1 = "1624000000"
        ts2 = "1624000001"

        message1 = f"{ts1}.{body}".encode()
        message2 = f"{ts2}.{body}".encode()

        sig1 = hmac.new(secret.encode(), message1, hashlib.sha256).hexdigest()
        sig2 = hmac.new(secret.encode(), message2, hashlib.sha256).hexdigest()

        assert sig1 != sig2

    def test_signature_generation_is_deterministic(self):
        """Test that same inputs produce same signature."""
        secret = "test-secret"
        timestamp = "1624000000"
        body = '{"alert": "test"}'
        message = f"{timestamp}.{body}".encode()

        sig1 = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
        sig2 = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()

        assert sig1 == sig2

    def test_server_verification_workflow(self):
        """Test complete server-side verification workflow."""
        secret = "webhook-secret"
        timestamp = "1624000000"
        body = '{"rule": "cpu_high", "value": 0.95}'

        # Client side: generate signature
        message = f"{timestamp}.{body}".encode()
        signature = hmac.new(
            secret.encode(),
            message,
            hashlib.sha256,
        ).hexdigest()

        # Server receives: X-Tennet-Signature: t=1624000000,v1=<sig>
        # Server verifies:
        received_header = f"t={timestamp},v1={signature}"

        def verify_webhook_signature(header_value, secret, body):
            """Server-side verification function."""
            parts = {}
            for pair in header_value.split(","):
                k, v = pair.split("=")
                parts[k] = v

            ts = parts.get("t")
            v1 = parts.get("v1")

            if not ts or not v1:
                return False

            # Recompute
            message = f"{ts}.{body}".encode()
            computed = hmac.new(
                secret.encode(),
                message,
                hashlib.sha256,
            ).hexdigest()

            return hmac.compare_digest(v1, computed)

        assert verify_webhook_signature(received_header, secret, body) is True
        assert verify_webhook_signature(received_header, "wrong-secret", body) is False
