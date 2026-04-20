"""
Port index builder: bulk registry walk to resolve all node ports.

Single entry point for the canvas renderer to get live input/output port
definitions from the node registry without per-node round trips.
"""

from typing import Any, Literal, TypedDict


class ResolvedPort(TypedDict):
    """A single input or output port of a node."""
    key: str
    type: str


class ResolvedPorts(TypedDict):
    """All input and output ports for a node."""
    inputs: list[ResolvedPort]
    outputs: list[ResolvedPort]
    unresolved: bool


def build_port_index(
    node_keys: list[str],
    registry: Any,
) -> dict[str, ResolvedPorts]:
    """
    Bulk registry walk to resolve all node ports at once.

    Given a list of node keys and a registry instance, returns a map
    of node_key -> {inputs, outputs, unresolved}.

    Deduplicates keys before walk. Missing keys return sentinel unresolved=true.

    Args:
        node_keys: List of node keys (may contain duplicates)
        registry: The in-process node registry (from backend.01_catalog.registry)

    Returns:
        dict[node_key -> {inputs: [Port], outputs: [Port], unresolved: bool}]
    """
    # Dedup keys
    unique_keys = list(set(node_keys))

    result: dict[str, ResolvedPorts] = {}

    # Single registry walk
    for node_key in unique_keys:
        try:
            # Try to resolve the node from the registry
            node_def = registry.get(node_key)
            if not node_def:
                result[node_key] = {
                    "inputs": [],
                    "outputs": [],
                    "unresolved": True,
                }
                continue

            # Resolve input and output ports from node schemas
            inputs = _extract_ports(node_def.get("input_schema", {}))
            outputs = _extract_ports(node_def.get("output_schema", {}))

            result[node_key] = {
                "inputs": inputs,
                "outputs": outputs,
                "unresolved": False,
            }
        except Exception:
            # If anything goes wrong, mark as unresolved
            result[node_key] = {
                "inputs": [],
                "outputs": [],
                "unresolved": True,
            }

    return result


def _extract_ports(schema: dict[str, Any]) -> list[ResolvedPort]:
    """
    Extract ports from a JSON Schema (input_schema or output_schema).

    Scans the schema properties and yields ports with their types.
    Handles simple types (string, number, boolean) and refs.
    """
    ports: list[ResolvedPort] = []

    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        return ports

    for key, prop_schema in properties.items():
        port_type = _infer_port_type(prop_schema)
        ports.append({
            "key": key,
            "type": port_type,
        })

    return ports


def _infer_port_type(prop_schema: dict[str, Any]) -> str:
    """
    Infer a simple port type from a JSON Schema property.

    Maps JSON Schema types to canvas port types:
    - string -> "string"
    - number, integer -> "number"
    - boolean -> "boolean"
    - object -> "object"
    - array -> "array"
    - null or unknown -> "any"
    """
    if not isinstance(prop_schema, dict):
        return "any"

    schema_type = prop_schema.get("type")

    if schema_type == "string":
        return "string"
    elif schema_type in ("number", "integer"):
        return "number"
    elif schema_type == "boolean":
        return "boolean"
    elif schema_type == "object":
        return "object"
    elif schema_type == "array":
        return "array"
    elif schema_type == "null":
        return "any"
    else:
        # Unknown type defaults to any
        return "any"
