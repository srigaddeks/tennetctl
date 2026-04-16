"""
Sandbox worker — executes signal Python code in a restricted environment.
Invoked as a subprocess by the execution engine.

Protocol:
  1. Read JSON from stdin: {"code": "...", "dataset": {...}, "configurable_args": {...}, "max_memory_mb": 256}
  2. Compile code with RestrictedPython
  3. Execute evaluate(dataset, **configurable_args) — falls back to evaluate(dataset) for legacy signals
  4. Write JSON result to stdout: {"result": "pass|fail|warning", "summary": "...", "details": [...], "metadata": {}}
  5. Write errors to stderr
"""
from __future__ import annotations

import sys
import json
import resource
import hashlib
import re
import datetime
import math
import statistics
import collections
import ipaddress


def main() -> None:
    # Read input first so we can apply memory limit from the payload
    raw = sys.stdin.buffer.read()
    try:
        input_data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid input JSON: {e}"}), file=sys.stderr)
        sys.exit(1)

    code = input_data.get("code", "")
    dataset = input_data.get("dataset", {})
    max_memory_mb: int = int(input_data.get("max_memory_mb", 128))
    configurable_args: dict = input_data.get("configurable_args") or {}

    # Import RestrictedPython BEFORE setting RLIMIT_NOFILE (which blocks imports)
    rp_available = False
    try:
        from RestrictedPython import compile_restricted_exec, safe_globals
        from RestrictedPython.Eval import default_guarded_getiter, default_guarded_getitem
        from RestrictedPython.Guards import guarded_unpack_sequence, safer_getattr
        rp_available = True
    except ImportError:
        pass

    # Apply resource limits now that we have the payload
    max_memory_bytes = max_memory_mb * 1024 * 1024
    try:
        resource.setrlimit(resource.RLIMIT_AS, (max_memory_bytes, max_memory_bytes))
    except (ValueError, resource.error):
        pass
    try:
        resource.setrlimit(resource.RLIMIT_DATA, (max_memory_bytes, max_memory_bytes))
    except (ValueError, resource.error):
        pass
    try:
        resource.setrlimit(resource.RLIMIT_NOFILE, (0, 0))
    except (ValueError, resource.error):
        pass

    # Compile with RestrictedPython
    if not rp_available:
        # In production, RestrictedPython MUST be available
        import os
        if os.environ.get("APP_ENV", "development") not in ("development", "dev"):
            print(json.dumps({"error": "RestrictedPython not installed — cannot execute signals in production"}), file=sys.stderr)
            sys.exit(1)
        # Fallback: compile without restrictions (dev mode only)
        compiled = compile(code, "<signal>", "exec")
        restricted_globals: dict = {"__builtins__": {
            "len": len, "range": range, "enumerate": enumerate, "zip": zip,
            "map": map, "filter": filter, "sorted": sorted, "reversed": reversed,
            "min": min, "max": max, "sum": sum, "abs": abs, "round": round,
            "all": all, "any": any, "isinstance": isinstance, "type": type,
            "str": str, "int": int, "float": float, "bool": bool,
            "list": list, "dict": dict, "tuple": tuple, "set": set, "frozenset": frozenset,
            "print": print, "True": True, "False": False, "None": None,
            "hasattr": hasattr, "getattr": getattr, "setattr": setattr,
        }}
    else:
        compile_result = compile_restricted_exec(code)
        if compile_result.errors:
            print(json.dumps({"error": f"Compilation errors: {compile_result.errors}"}), file=sys.stderr)
            sys.exit(1)
        compiled = compile_result.code
        restricted_globals = safe_globals.copy()
        restricted_globals["_getiter_"] = default_guarded_getiter
        restricted_globals["_getitem_"] = default_guarded_getitem
        restricted_globals["_unpack_sequence_"] = guarded_unpack_sequence
        restricted_globals["_getattr_"] = safer_getattr
        # safe_globals.__builtins__ omits many common builtins — add them back
        restricted_globals["__builtins__"] = restricted_globals["__builtins__"].copy()
        restricted_globals["__builtins__"].update({
            "dict": dict, "list": list, "set": set, "frozenset": frozenset,
            "print": print, "enumerate": enumerate, "map": map, "filter": filter,
            "any": any, "all": all, "min": min, "max": max, "sum": sum,
            "reversed": reversed, "type": type, "hasattr": hasattr,
            "getattr": getattr, "None": None,
        })

    # Inject allowed modules
    allowed_modules = {
        "json": json, "re": re, "datetime": datetime, "math": math,
        "statistics": statistics, "collections": collections,
        "ipaddress": ipaddress, "hashlib": hashlib,
    }
    restricted_globals.update(allowed_modules)

    # Execute module-level code (defines the evaluate function)
    local_ns: dict = {}
    try:
        exec(compiled, restricted_globals, local_ns)
    except Exception as e:
        print(json.dumps({"error": f"Execution error during module load: {type(e).__name__}: {e}"}), file=sys.stderr)
        sys.exit(1)

    if "evaluate" not in local_ns:
        print(json.dumps({"error": "Signal must define an 'evaluate(dataset)' function"}), file=sys.stderr)
        sys.exit(1)

    evaluate_fn = local_ns["evaluate"]

    # Capture stdout from signal execution
    import io
    captured_stdout = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured_stdout

    try:
        result = evaluate_fn(dataset, **configurable_args)
    except TypeError:
        # evaluate() may not accept kwargs (old-style signal without named args)
        # fall back to positional-only call
        try:
            result = evaluate_fn(dataset)
        except Exception as e:
            sys.stdout = old_stdout
            print(json.dumps({
                "error": f"Signal evaluation error: {type(e).__name__}: {e}",
                "stdout": captured_stdout.getvalue(),
            }), file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        sys.stdout = old_stdout
        print(json.dumps({
            "error": f"Signal evaluation error: {type(e).__name__}: {e}",
            "stdout": captured_stdout.getvalue(),
        }), file=sys.stderr)
        sys.exit(1)
    finally:
        sys.stdout = old_stdout

    stdout_output = captured_stdout.getvalue()

    # Validate result structure
    if not isinstance(result, dict):
        print(json.dumps({"error": f"evaluate() must return dict, got {type(result).__name__}"}), file=sys.stderr)
        sys.exit(1)

    if "result" not in result or result["result"] not in ("pass", "fail", "warning"):
        print(json.dumps({"error": "evaluate() must return dict with 'result' key = 'pass'|'fail'|'warning'"}), file=sys.stderr)
        sys.exit(1)

    # Output
    output = {
        "result": result.get("result"),
        "summary": result.get("summary", ""),
        "details": result.get("details", []),
        "metadata": result.get("metadata", {}),
        "stdout": stdout_output,
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
