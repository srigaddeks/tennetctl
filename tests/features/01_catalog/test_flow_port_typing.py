"""Port type resolution and compatibility tests."""

import pytest
from backend.02_features.01_catalog.sub_features.04_flows.port_resolver import (
    is_compatible,
    resolve_ports,
)


def test_exact_type_match():
    """Test that exact types match."""
    assert is_compatible("string", "string")
    assert is_compatible("number", "number")
    assert is_compatible("boolean", "boolean")
    assert is_compatible("object", "object")
    assert is_compatible("array", "array")
    assert is_compatible("uuid", "uuid")
    assert is_compatible("datetime", "datetime")
    assert is_compatible("binary", "binary")
    assert is_compatible("error", "error")


def test_any_matches_anything():
    """Test that 'any' type matches any other type."""
    assert is_compatible("any", "string")
    assert is_compatible("any", "number")
    assert is_compatible("any", "object")
    assert is_compatible("string", "any")
    assert is_compatible("any", "any")


def test_incompatible_types():
    """Test that mismatched types are rejected (except 'any')."""
    assert not is_compatible("string", "number")
    assert not is_compatible("boolean", "number")
    assert not is_compatible("array", "string")
    assert not is_compatible("object", "boolean")
    assert not is_compatible("uuid", "string")
    assert not is_compatible("datetime", "number")


def test_resolve_ports_from_properties_schema():
    """Test resolving ports from properties-based JSON Schema."""
    node_config = {
        "input_schema": {
            "type": "object",
            "properties": {
                "username": {"type": "string", "description": "Username"},
                "password": {"type": "string", "description": "Password"},
            },
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "token": {"type": "string", "format": "uuid", "description": "Auth token"},
                "user_id": {"type": "string", "format": "uuid"},
            },
        },
    }

    ports = resolve_ports("iam.auth_required", node_config)

    # Check inputs
    assert len(ports.inputs) == 2
    assert any(p.key == "username" for p in ports.inputs)
    assert any(p.key == "password" for p in ports.inputs)

    # Check outputs
    assert len(ports.outputs) == 2
    uuid_port = next(p for p in ports.outputs if p.key == "token")
    assert uuid_port.type == "uuid"


def test_resolve_ports_with_format():
    """Test format-specific type inference (uuid, datetime)."""
    node_config = {
        "input_schema": {},
        "output_schema": {
            "type": "object",
            "properties": {
                "created_at": {"type": "string", "format": "date-time"},
                "id": {"type": "string", "format": "uuid"},
                "data": {"type": "string", "format": "binary"},
            },
        },
    }

    ports = resolve_ports("event.logger", node_config)

    assert any(p.key == "created_at" and p.type == "datetime" for p in ports.outputs)
    assert any(p.key == "id" and p.type == "uuid" for p in ports.outputs)
    assert any(p.key == "data" and p.type == "binary" for p in ports.outputs)


def test_resolve_ports_with_nullable_types():
    """Test handling of nullable types (["string", "null"])."""
    node_config = {
        "input_schema": {},
        "output_schema": {
            "type": "object",
            "properties": {
                "optional_name": {
                    "type": ["string", "null"],
                    "description": "Optional name",
                },
                "nullable_count": {
                    "type": ["number", "null"],
                },
            },
        },
    }

    ports = resolve_ports("optional.node", node_config)

    # Should resolve to non-null type
    assert any(p.key == "optional_name" and p.type == "string" for p in ports.outputs)
    assert any(p.key == "nullable_count" and p.type == "number" for p in ports.outputs)


def test_resolve_ports_empty_schema():
    """Test handling of empty or missing schemas."""
    node_config = {
        "input_schema": {},
        "output_schema": {},
    }

    ports = resolve_ports("empty.node", node_config)

    assert ports.inputs == []
    assert ports.outputs == []


def test_resolve_ports_multiple_types():
    """Test that multiple non-null types resolve to 'any'."""
    node_config = {
        "input_schema": {},
        "output_schema": {
            "type": "object",
            "properties": {
                "mixed": {
                    "type": ["string", "number", "null"],
                },
            },
        },
    }

    ports = resolve_ports("multi.type", node_config)

    assert any(p.key == "mixed" and p.type == "any" for p in ports.outputs)


def test_compatibility_matrix():
    """Test full compatibility matrix."""
    matrix = [
        # (from_type, to_type, expected_compatible)
        ("string", "string", True),
        ("string", "number", False),
        ("number", "number", True),
        ("boolean", "boolean", True),
        ("boolean", "number", False),
        ("array", "array", True),
        ("array", "string", False),
        ("object", "object", True),
        ("uuid", "uuid", True),
        ("uuid", "string", False),
        ("datetime", "datetime", True),
        ("datetime", "string", False),
        ("any", "string", True),
        ("string", "any", True),
        ("any", "any", True),
    ]

    for from_type, to_type, expected in matrix:
        result = is_compatible(from_type, to_type)
        assert result == expected, f"{from_type} -> {to_type} should be {expected}"


def test_resolve_ports_complex_node():
    """Test resolving ports for a complex node."""
    node_config = {
        "input_schema": {
            "type": "object",
            "properties": {
                "endpoint": {"type": "string", "description": "API endpoint"},
                "method": {"type": "string", "enum": ["GET", "POST", "PUT"], "description": "HTTP method"},
                "headers": {"type": "object", "description": "HTTP headers"},
                "timeout": {"type": "number", "description": "Request timeout in seconds"},
            },
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "status": {"type": "number", "description": "HTTP status code"},
                "body": {"type": "object", "description": "Response body"},
                "headers": {"type": "object", "description": "Response headers"},
                "error": {"type": "string", "description": "Error message if any"},
            },
        },
    }

    ports = resolve_ports("http.request", node_config)

    # Verify input ports
    assert len(ports.inputs) == 4
    assert any(p.key == "endpoint" and p.type == "string" for p in ports.inputs)
    assert any(p.key == "headers" and p.type == "object" for p in ports.inputs)
    assert any(p.key == "timeout" and p.type == "number" for p in ports.inputs)

    # Verify output ports
    assert len(ports.outputs) == 4
    assert any(p.key == "status" and p.type == "number" for p in ports.outputs)
    assert any(p.key == "body" and p.type == "object" for p in ports.outputs)
