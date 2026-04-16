from __future__ import annotations


def get_transmitter_config(base_url: str) -> dict:
    """Generate the .well-known/ssf-configuration discovery document."""
    return {
        "issuer": base_url,
        "jwks_uri": f"{base_url}/.well-known/jwks.json",
        "delivery_methods_supported": [
            "urn:ietf:rfc:8935",  # push
            "urn:ietf:rfc:8936",  # poll
        ],
        "configuration_endpoint": f"{base_url}/api/v1/sb/ssf/streams",
        "status_endpoint": f"{base_url}/api/v1/sb/ssf/streams/{{stream_id}}/status",
        "add_subject_endpoint": f"{base_url}/api/v1/sb/ssf/streams/{{stream_id}}/subjects",
        "remove_subject_endpoint": f"{base_url}/api/v1/sb/ssf/streams/{{stream_id}}/subjects",
        "verification_endpoint": f"{base_url}/api/v1/sb/ssf/streams/{{stream_id}}/verify",
        "critical_subject_members": [],
        "authorization_schemes": [{"spec_urn": "urn:ietf:rfc:6749"}],
    }
