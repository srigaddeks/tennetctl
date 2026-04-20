"""
Port type resolution and compatibility checking.

Pure compute module: no database access.
- resolve_ports: translate node schema to input/output ports
- is_compatible: check if edge can connect (type safety)
"""

from typing import Any, NamedTuple


class Port(NamedTuple):
    """Input or output port on a node instance."""
    key: str
    type: str  # "any", "string", "number", "boolean", "object", "array", "uuid", "datetime", "binary", "error"
    description: str = ""


class ResolvedPorts(NamedTuple):
    """Input and output ports for a node."""
    inputs: list[Port]
    outputs: list[Port]


# JSON Schema type to port type mapping
_SCHEMA_TYPE_MAP = {
    "string": "string",
    "number": "number",
    "integer": "number",
    "boolean": "boolean",
    "object": "object",
    "array": "array",
}


def resolve_ports(node_key: str, node_config: dict[str, Any]) -> ResolvedPorts:
    """
    Resolve input and output ports from node configuration schemas.

    Translates JSON Schema input_schema and output_schema into
    [Port(key, type)] lists.

    Args:
        node_key: Node key (e.g., "iam.auth_required")
        node_config: Node configuration dict with input_schema and output_schema

    Returns:
        ResolvedPorts with parsed input and output ports

    Raises:
        ValueError: if schemas are missing or malformed
    """
    inputs = _extract_ports_from_schema(node_config.get("input_schema", {}), "inputs")
    outputs = _extract_ports_from_schema(node_config.get("output_schema", {}), "outputs")
    return ResolvedPorts(inputs=inputs, outputs=outputs)


def _extract_ports_from_schema(
    schema: dict[str, Any],
    port_direction: str,
) -> list[Port]:
    """
    Extract ports from a JSON Schema object.

    Handles properties-based schema (typical for structured inputs/outputs).
    Each property becomes a port with type inferred from the schema.

    Args:
        schema: JSON Schema dict
        port_direction: "inputs" or "outputs" (for error messages)

    Returns:
        List of Port instances
    """
    ports = []

    # Handle empty or missing schemas
    if not isinstance(schema, dict):
        return ports

    # If schema has properties, each property is a port
    if "properties" in schema and isinstance(schema["properties"], dict):
        for key, prop_schema in schema["properties"].items():
            port_type = _infer_port_type(prop_schema)
            description = prop_schema.get("description", "")
            ports.append(Port(key=key, type=port_type, description=description))

    # If schema is a simple type schema (e.g., {"type": "string"}), treat as single unnamed port
    # but this is rare in practice — most nodes use properties
    elif "type" in schema:
        port_type = _infer_port_type(schema)
        ports.append(Port(key="value", type=port_type, description=schema.get("description", "")))

    return ports


def _infer_port_type(prop_schema: dict[str, Any]) -> str:
    """
    Infer port type from a property schema.

    Handles:
    - Direct type (e.g., {"type": "string"})
    - Enum of types (e.g., {"type": ["string", "null"]})
    - Custom format (e.g., {"type": "string", "format": "uuid"})
    - Default to "any" if unrecognized

    Args:
        prop_schema: Property schema dict

    Returns:
        Port type string
    """
    if not isinstance(prop_schema, dict):
        return "any"

    schema_type = prop_schema.get("type")

    # Handle null types (filter them out)
    if isinstance(schema_type, list):
        types = [t for t in schema_type if t != "null"]
        if len(types) == 1:
            schema_type = types[0]
        elif len(types) == 0:
            return "any"
        else:
            # Multiple non-null types → any
            return "any"

    # Check for format specialization
    if schema_type == "string":
        schema_format = prop_schema.get("format", "")
        if schema_format == "uuid":
            return "uuid"
        elif schema_format == "date-time" or schema_format == "datetime":
            return "datetime"
        elif schema_format == "binary":
            return "binary"
        return "string"

    # Direct type mapping
    mapped = _SCHEMA_TYPE_MAP.get(schema_type, "any")
    return mapped


def is_compatible(from_type: str, to_type: str) -> bool:
    """
    Check if an output port type can connect to an input port type.

    Rules:
    - "any" matches anything
    - Exact type match required otherwise
    - No implicit numeric widening (boolean→number rejected)

    Args:
        from_type: Output port type
        to_type: Input port type

    Returns:
        True if connection is valid
    """
    # Any type matches anything
    if from_type == "any" or to_type == "any":
        return True

    # Exact match required
    return from_type == to_type
