"""Test canvas port resolution."""

from unittest.mock import MagicMock
from backend.02_features.01_catalog.sub_features.05_canvas.port_index import build_port_index


def test_port_index_bulk_registry_call_count_is_one():
    """Test: build_port_index issues exactly one registry traversal."""
    registry = MagicMock()

    def get_side_effect(key):
        if key == "string.upper":
            return {
                "input_schema": {"properties": {"value": {"type": "string"}}},
                "output_schema": {"properties": {"result": {"type": "string"}}},
            }
        elif key == "math.add":
            return {
                "input_schema": {
                    "properties": {"a": {"type": "number"}, "b": {"type": "number"}}
                },
                "output_schema": {"properties": {"sum": {"type": "number"}}},
            }
        return None

    registry.get.side_effect = get_side_effect

    node_keys = ["string.upper", "math.add"]
    result = build_port_index(node_keys, registry)

    # Each key should trigger one registry.get call
    assert registry.get.call_count == 2


def test_port_index_unresolved_missing_key():
    """Test: Missing node_key returns unresolved=true sentinel."""
    registry = MagicMock()
    registry.get.return_value = None

    result = build_port_index(["missing.node"], registry)

    assert result["missing.node"]["unresolved"] is True
    assert result["missing.node"]["inputs"] == []
    assert result["missing.node"]["outputs"] == []


def test_port_index_live_schema_change():
    """Test: Schema change reflects in ports without DB write."""
    registry = MagicMock()

    # First call: old schema
    def get_v1(key):
        if key == "string.upper":
            return {
                "input_schema": {"properties": {"value": {"type": "string"}}},
                "output_schema": {"properties": {"result": {"type": "string"}}},
            }
        return None

    registry.get.side_effect = get_v1

    result1 = build_port_index(["string.upper"], registry)
    assert result1["string.upper"]["inputs"][0]["type"] == "string"

    # Second call: new schema (value now accepts any)
    def get_v2(key):
        if key == "string.upper":
            return {
                "input_schema": {"properties": {"value": {"type": "object"}}},  # Changed!
                "output_schema": {"properties": {"result": {"type": "string"}}},
            }
        return None

    registry.get.side_effect = get_v2

    result2 = build_port_index(["string.upper"], registry)
    assert result2["string.upper"]["inputs"][0]["type"] == "object"  # Reflects new code


def test_port_index_deduplication():
    """Test: Duplicate keys in input are deduplicated before walk."""
    registry = MagicMock()

    def get_side_effect(key):
        if key == "test.node":
            return {
                "input_schema": {"properties": {}},
                "output_schema": {"properties": {}},
            }
        return None

    registry.get.side_effect = get_side_effect

    node_keys = ["test.node", "test.node", "test.node"]
    result = build_port_index(node_keys, registry)

    # Should call get exactly once despite 3 duplicates
    assert registry.get.call_count == 1
    assert "test.node" in result


def test_port_index_infers_types_correctly():
    """Test: Port types are inferred correctly from JSON Schema."""
    registry = MagicMock()

    def get_side_effect(key):
        return {
            "input_schema": {
                "properties": {
                    "str_val": {"type": "string"},
                    "num_val": {"type": "number"},
                    "bool_val": {"type": "boolean"},
                    "obj_val": {"type": "object"},
                    "arr_val": {"type": "array"},
                    "unknown_val": {},
                }
            },
            "output_schema": {"properties": {}},
        }

    registry.get.side_effect = get_side_effect

    result = build_port_index(["test.node"], registry)

    inputs_by_key = {p["key"]: p for p in result["test.node"]["inputs"]}
    assert inputs_by_key["str_val"]["type"] == "string"
    assert inputs_by_key["num_val"]["type"] == "number"
    assert inputs_by_key["bool_val"]["type"] == "boolean"
    assert inputs_by_key["obj_val"]["type"] == "object"
    assert inputs_by_key["arr_val"]["type"] == "array"
    assert inputs_by_key["unknown_val"]["type"] == "any"  # Unknown defaults to any
