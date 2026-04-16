"""
Agent graph compiler — RestrictedPython compilation + graph structure validation.

Compiles user-written Python into a validated graph definition.
The user's code defines handler functions and a build_graph(ctx) function
that returns a declarative graph structure.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CompileResult:
    success: bool
    graph_definition: dict | None = None
    handler_names: list[str] | None = None
    errors: list[str] | None = None


@dataclass(frozen=True)
class GraphDefinition:
    nodes: dict[str, dict]  # {name: {"handler": callable, "transitions": {label: target}}}
    entry_point: str


class AgentCompiler:
    """Compiles user graph_source code and validates the graph structure."""

    _ALLOWED_MODULES = {
        "json", "re", "datetime", "math", "statistics",
        "collections", "ipaddress", "hashlib",
    }

    def compile_graph_source(self, graph_source: str) -> CompileResult:
        """Compile graph source and extract graph definition.

        Returns CompileResult with success=True and graph_definition if valid,
        or success=False with errors if compilation fails.
        """
        errors: list[str] = []

        # Try RestrictedPython first, fallback for dev
        try:
            from RestrictedPython import compile_restricted, safe_globals
            from RestrictedPython.Eval import default_guarded_getiter, default_guarded_getitem
            from RestrictedPython.Guards import guarded_unpack_sequence, safer_getattr

            byte_code = compile_restricted(graph_source, filename="<agent>", mode="exec")
            if byte_code.errors:
                return CompileResult(success=False, errors=list(byte_code.errors))
            compiled = byte_code.code

            restricted_globals = safe_globals.copy()
            restricted_globals["_getiter_"] = default_guarded_getiter
            restricted_globals["_getitem_"] = default_guarded_getitem
            restricted_globals["_unpack_sequence_"] = guarded_unpack_sequence
            restricted_globals["_getattr_"] = safer_getattr
        except ImportError:
            # Dev fallback — allow full Python
            try:
                compiled = compile(graph_source, "<agent>", "exec")
            except SyntaxError as e:
                return CompileResult(success=False, errors=[f"SyntaxError: {e}"])
            restricted_globals = {"__builtins__": __builtins__}

        # Inject allowed modules
        import json, re, datetime, math, statistics, collections, ipaddress, hashlib
        allowed = {
            "json": json, "re": re, "datetime": datetime, "math": math,
            "statistics": statistics, "collections": collections,
            "ipaddress": ipaddress, "hashlib": hashlib,
        }
        restricted_globals.update(allowed)

        # Execute to populate namespace
        local_ns: dict = {}
        try:
            exec(compiled, restricted_globals, local_ns)
        except Exception as e:
            return CompileResult(success=False, errors=[f"Execution error: {e}"])

        # Must define build_graph
        if "build_graph" not in local_ns:
            errors.append("Agent code must define a 'build_graph(ctx)' function")
            return CompileResult(success=False, errors=errors)

        if not callable(local_ns["build_graph"]):
            errors.append("'build_graph' must be a callable function")
            return CompileResult(success=False, errors=errors)

        return CompileResult(
            success=True,
            graph_definition=None,  # Resolved at runtime with ctx
            handler_names=[k for k in local_ns if callable(local_ns.get(k)) and k != "build_graph"],
        )

    def build_graph_runtime(
        self,
        graph_source: str,
        ctx: object,
    ) -> GraphDefinition:
        """Build the graph at runtime by calling build_graph(ctx).

        This is called during execution, not during compilation.
        """
        # Compile
        try:
            from RestrictedPython import compile_restricted, safe_globals
            from RestrictedPython.Eval import default_guarded_getiter, default_guarded_getitem
            from RestrictedPython.Guards import guarded_unpack_sequence, safer_getattr

            byte_code = compile_restricted(graph_source, filename="<agent>", mode="exec")
            compiled = byte_code.code
            restricted_globals = safe_globals.copy()
            restricted_globals["_getiter_"] = default_guarded_getiter
            restricted_globals["_getitem_"] = default_guarded_getitem
            restricted_globals["_unpack_sequence_"] = guarded_unpack_sequence
            restricted_globals["_getattr_"] = safer_getattr
        except ImportError:
            compiled = compile(graph_source, "<agent>", "exec")
            restricted_globals = {"__builtins__": __builtins__}

        import json, re, datetime, math, statistics, collections, ipaddress, hashlib
        restricted_globals.update({
            "json": json, "re": re, "datetime": datetime, "math": math,
            "statistics": statistics, "collections": collections,
            "ipaddress": ipaddress, "hashlib": hashlib,
        })

        local_ns: dict = {}
        exec(compiled, restricted_globals, local_ns)

        build_fn = local_ns["build_graph"]
        graph_dict = build_fn(ctx)

        # Validate structure
        if not isinstance(graph_dict, dict):
            raise ValueError("build_graph(ctx) must return a dict")
        if "nodes" not in graph_dict:
            raise ValueError("Graph must have 'nodes' key")
        if "entry_point" not in graph_dict:
            raise ValueError("Graph must have 'entry_point' key")

        nodes = graph_dict["nodes"]
        entry = graph_dict["entry_point"]

        if entry not in nodes:
            raise ValueError(f"entry_point '{entry}' not found in nodes")

        # Validate each node
        for name, node_def in nodes.items():
            if "handler" not in node_def:
                raise ValueError(f"Node '{name}' must have a 'handler' key")
            if not callable(node_def["handler"]):
                raise ValueError(f"Node '{name}' handler must be callable")
            transitions = node_def.get("transitions", {})
            for label, target in transitions.items():
                if target != "__end__" and target not in nodes:
                    raise ValueError(
                        f"Node '{name}' transition '{label}' -> '{target}' not found in nodes"
                    )

        return GraphDefinition(nodes=nodes, entry_point=entry)
