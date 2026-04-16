from __future__ import annotations

from typing import TypedDict


class SignalGenState(TypedDict, total=False):
    # ── inputs ──────────────────────────────────────────────────────────────
    prompt: str
    connector_type: str
    dataset_schema: dict          # rich schema: {field_path: {type, example, nullable}}
    sample_dataset: dict | None   # actual dataset record for execution tests
    asset_version_code: str | None
    signal_id: str | None         # set when updating an existing signal
    signal_spec: dict | None      # spec JSON if spec-driven codegen (24_signal_codegen)
    configurable_args: dict       # default arg values to pass during test execution
    max_iterations: int           # default 10

    # ── working state ────────────────────────────────────────────────────────
    generated_code: str | None
    compile_error: str | None
    test_result: dict | None      # full ExecutionResult as dict
    iteration: int
    fix_history: list[dict]       # [{iteration, error_type, fix_summary}]

    # ── output ───────────────────────────────────────────────────────────────
    caep_event_type: str | None
    risc_event_type: str | None
    custom_event_uri: str | None  # full URI e.g. https://kcontrol.io/events/sandbox/signal-fired
    final_code: str | None
    signal_args_schema: list[dict] | None   # [{key, label, type, default, description, min, max, options}]
    signal_name_suggestion: str | None
    signal_description_suggestion: str | None
    ssf_mapping: dict | None      # full ssf_mapping block matching signal spec format
    is_complete: bool
    error: str | None
    iterations_used: int          # how many fix iterations were consumed
