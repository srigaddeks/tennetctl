"""
Signal-Specific Test Dataset Generator
=======================================
Given a signal spec + data sufficiency result, generates a comprehensive test dataset
that covers ALL scenarios for that specific signal.

Two-phase process:
  Phase 1: AI generates varied test records using ONLY the JSON structure from the
           data sufficiency check (never invents fields)
  Phase 2: Structural verification — confirms generated test records match the exact
           schema of the live/source dataset records (no drift)

Key principles:
  - Only uses record_names from data sufficiency as templates
  - Every generated record has: _scenario_name, _expected_result, _explanation, _source_record_ref
  - Covers: all-pass, all-fail, mixed, edge cases, boundary values, empty data
  - Structure verification catches any field name/type/nesting mismatches
"""
from __future__ import annotations

import json
from importlib import import_module

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.signal_spec.test_dataset_gen")


GENERATE_TEST_DATA_PROMPT = """You are a compliance test data engineer. Your job is to generate a comprehensive
test dataset for a SPECIFIC signal, using ONLY the JSON structure from the source records.

CRITICAL RULES:
1. NEVER invent new field names — only use fields that exist in the source records
2. NEVER change the nesting structure — if a field is nested 3 levels deep, keep it 3 levels deep
3. Every test record must reference which source record it was based on (_source_record_ref)
4. Generate varied VALUES but keep the exact same STRUCTURE
5. Cover ALL these scenario types:
   - fully_compliant: everything correct, signal should PASS
   - fully_non_compliant: everything wrong, signal should FAIL
   - mixed_partial: some things right, some wrong, signal should FAIL or WARNING
   - edge_empty: empty arrays, null values, missing optional fields
   - edge_minimal: minimum viable data that still passes
   - edge_boundary: values right at thresholds (if configurable args exist)
   - edge_large_scale: many items (10+ repos, 50+ members) to test iteration
   - regression_specific: records targeting the specific detection logic steps

Signal Specification:
{signal_spec}

Data Sufficiency Result (which records and fields are needed):
{sufficiency_result}

Source Records (use these as structural templates — NEVER invent fields):
{source_records}

Generate 12-18 test records. Return ONLY valid JSON:
{{
  "signal_code": "{signal_code}",
  "dataset_name": "Test Dataset: {signal_display_name}",
  "generated_from_spec_version": "1.0",
  "total_scenarios": <count>,
  "scenario_coverage": {{
    "pass_scenarios": <count>,
    "fail_scenarios": <count>,
    "warning_scenarios": <count>,
    "edge_case_scenarios": <count>
  }},
  "records": [
    {{
      "_scenario_name": "descriptive_snake_case_name",
      "_expected_result": "pass|fail|warning",
      "_explanation": "Why this scenario produces this result — reference specific detection logic steps",
      "_source_record_ref": "name_of_source_record_used_as_template",
      "_scenario_type": "fully_compliant|fully_non_compliant|mixed_partial|edge_empty|edge_minimal|edge_boundary|edge_large_scale|regression_specific",
      ...actual fields matching source record structure...
    }}
  ]
}}"""


STRUCTURE_VERIFY_PROMPT = """You are a JSON structure auditor. Compare generated test records against source records
and find ANY structural differences.

Check for:
1. Missing fields (in test but not in source, or vice versa)
2. Different nesting (field at wrong depth)
3. Type mismatches (string vs number vs boolean vs array vs object)
4. Array element structure differences
5. Extra fields in test records not present in source (except _scenario_name, _expected_result, _explanation, _source_record_ref, _scenario_type)

Source Records (ground truth):
{source_records}

Generated Test Records:
{test_records}

Return ONLY valid JSON:
{{
  "verification_status": "match|mismatch|partial_match",
  "structural_issues": [
    {{
      "test_record_name": "...",
      "issue_type": "missing_field|extra_field|type_mismatch|nesting_error",
      "field_path": "...",
      "expected": "what it should be",
      "actual": "what it is in test record",
      "severity": "critical|warning|info"
    }}
  ],
  "field_coverage": {{
    "total_source_fields": <count>,
    "covered_in_tests": <count>,
    "coverage_percentage": <float>
  }},
  "summary": "One paragraph assessment"
}}"""


def _parse_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        end = len(lines) - 1
        while end > 0 and lines[end].strip() in ("```", ""):
            end -= 1
        text = "\n".join(lines[1:end + 1])
    return json.loads(text)


async def generate_signal_test_dataset(
    *,
    provider,
    signal_spec: dict,
    sufficiency_result: dict,
    source_records: list[dict],
    record_names: list[str],
) -> dict:
    """
    Phase 1: Generate comprehensive test dataset from signal spec + data sufficiency.

    Uses only the source records identified in sufficiency as templates.
    """
    # Filter source records to only those referenced in sufficiency
    referenced_names = set()
    for fc in sufficiency_result.get("field_checks", []):
        referenced_names.update(fc.get("found_in_records", []))
    for rc in sufficiency_result.get("record_coverage", []):
        referenced_names.add(rc.get("record_name", ""))

    # Build source records context — only include referenced ones
    source_parts = []
    for rec, name in zip(source_records, record_names):
        if not referenced_names or name in referenced_names:
            rec_json = json.dumps(rec, indent=2, default=str)[:3000]
            source_parts.append(f"--- {name} ---\n{rec_json}")
    source_records_str = "\n\n".join(source_parts) if source_parts else "(No matching source records)"

    signal_code = signal_spec.get("signal_code", "unknown")
    signal_name = signal_spec.get("display_name", signal_code)

    prompt = GENERATE_TEST_DATA_PROMPT.format(
        signal_spec=json.dumps(signal_spec, indent=2, default=str)[:4000],
        sufficiency_result=json.dumps(sufficiency_result, indent=2, default=str)[:3000],
        source_records=source_records_str,
        signal_code=signal_code,
        signal_display_name=signal_name,
    )

    _logger.info("generate_signal_test_dataset: generating for %s", signal_code)

    try:
        response = await provider.chat_completion(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Generate a comprehensive test dataset for the '{signal_name}' signal. Use EXACTLY the same JSON field structure as the source records."},
            ],
            temperature=1.0,
            max_tokens=None,
        )
        result = _parse_json(response.content)
        result["generation_status"] = "success"
        return result
    except Exception as exc:
        _logger.warning("generate_signal_test_dataset: failed for %s: %s", signal_code, exc)
        return {
            "signal_code": signal_code,
            "generation_status": "failed",
            "error": str(exc),
            "records": [],
        }


def verify_structure_with_code(
    *,
    source_records: list[dict],
    record_names: list[str],
    test_records: list[dict],
) -> dict:
    """
    CODE-BASED structural verification (not AI). Fully deterministic.
    Compares JSON structure between source and test records.
    Checks: field names, nesting depth, types, array element structure.
    Works with ANY JSON structure — no assumptions.
    """
    METADATA_KEYS = {"_scenario_name", "_expected_result", "_explanation", "_source_record_ref", "_scenario_type"}

    def _extract_schema(obj, prefix="", depth=0):
        """Recursively extract flat schema: {field.path: type_name}"""
        if depth > 10:
            return {}
        schema = {}
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in METADATA_KEYS:
                    continue
                path = f"{prefix}.{k}" if prefix else k
                if v is None:
                    schema[path] = "NoneType"
                elif isinstance(v, bool):
                    schema[path] = "bool"
                elif isinstance(v, int):
                    schema[path] = "int"
                elif isinstance(v, float):
                    schema[path] = "float"
                elif isinstance(v, str):
                    schema[path] = "str"
                elif isinstance(v, list):
                    schema[path] = "list"
                    if v and isinstance(v[0], dict):
                        schema.update(_extract_schema(v[0], f"{path}[]", depth + 1))
                    elif v and isinstance(v[0], str):
                        schema[f"{path}[]"] = "str"
                elif isinstance(v, dict):
                    schema[path] = "dict"
                    schema.update(_extract_schema(v, path, depth + 1))
                else:
                    schema[path] = type(v).__name__
        return schema

    # Build source schema as UNION of all source records
    source_schema: dict[str, set[str]] = {}
    for rec in source_records:
        for path, ttype in _extract_schema(rec).items():
            source_schema.setdefault(path, set()).add(ttype)

    # Flatten: pick most common type for each field
    source_flat: dict[str, str] = {}
    for path, types in source_schema.items():
        types_no_none = types - {"NoneType"}
        source_flat[path] = next(iter(types_no_none)) if types_no_none else "NoneType"

    # Check each test record — deduplicate issues per field (not per record)
    issues_seen: set[tuple] = set()
    issues = []
    field_coverage = set()

    for test_rec in test_records:
        scenario = test_rec.get("_scenario_name", "unnamed")
        test_schema = _extract_schema(test_rec)

        for path, ttype in test_schema.items():
            field_coverage.add(path)

            if path not in source_flat:
                key = ("extra_field", path)
                if key not in issues_seen:
                    issues_seen.add(key)
                    issues.append({
                        "test_record_name": scenario,
                        "issue_type": "extra_field",
                        "field_path": path,
                        "expected": "not in source",
                        "actual": ttype,
                        "severity": "info",
                    })
            elif ttype != "NoneType" and ttype != source_flat[path]:
                # Allow int/float mismatch (JSON numbers)
                if {ttype, source_flat[path]} <= {"int", "float"}:
                    continue
                # Allow bool/int (JSON booleans sometimes parsed as int)
                if {ttype, source_flat[path]} <= {"bool", "int"}:
                    continue
                key = ("type_mismatch", path, source_flat[path], ttype)
                if key not in issues_seen:
                    issues_seen.add(key)
                    issues.append({
                        "test_record_name": scenario,
                        "issue_type": "type_mismatch",
                        "field_path": path,
                        "expected": source_flat[path],
                        "actual": ttype,
                        "severity": "critical",
                    })

    # Check missing fields (only report once per field, not per record)
    for path in source_flat:
        if path not in field_coverage:
            issues.append({
                "test_record_name": "(all)",
                "issue_type": "missing_field",
                "field_path": path,
                "expected": source_flat[path],
                "actual": "never present in test records",
                "severity": "warning",
            })

    # Determine status
    critical_count = sum(1 for i in issues if i["severity"] == "critical")
    total_source = len(source_flat)
    covered = len(field_coverage & set(source_flat.keys()))
    pct = round(covered / total_source * 100, 1) if total_source else 100.0

    if critical_count == 0 and pct >= 80:
        status = "match"
    elif critical_count <= 2 and pct >= 60:
        status = "partial_match"
    else:
        status = "mismatch"

    return {
        "verification_status": status,
        "verification_method": "code",
        "structural_issues": issues,
        "field_coverage": {
            "total_source_fields": total_source,
            "covered_in_tests": covered,
            "coverage_percentage": pct,
        },
        "critical_issues": critical_count,
        "source_schema": source_flat,
        "summary": (
            f"Code-based verification: {covered}/{total_source} fields covered ({pct}%), "
            f"{critical_count} critical type mismatches, {len(issues)} total issues."
        ),
    }


async def verify_test_dataset_structure(
    *,
    provider,
    source_records: list[dict],
    record_names: list[str],
    test_records: list[dict],
) -> dict:
    """
    Phase 2: Verify that generated test records match the structural schema
    of the source/live records exactly.
    """
    # Build source context
    source_parts = []
    for rec, name in zip(source_records[:5], record_names[:5]):
        source_parts.append(f"--- {name} ---\n{json.dumps(rec, indent=2, default=str)[:2000]}")
    source_str = "\n\n".join(source_parts)

    # Build test records context
    test_parts = []
    for rec in test_records[:10]:
        name = rec.get("_scenario_name", "unnamed")
        test_parts.append(f"--- {name} ---\n{json.dumps(rec, indent=2, default=str)[:2000]}")
    test_str = "\n\n".join(test_parts)

    prompt = STRUCTURE_VERIFY_PROMPT.format(
        source_records=source_str,
        test_records=test_str,
    )

    _logger.info("verify_test_dataset_structure: checking %d test records against %d source records",
                 len(test_records), len(source_records))

    try:
        response = await provider.chat_completion(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": "Verify the structural match now. Be strict — every field name, nesting level, and type must match."},
            ],
            temperature=1.0,
            max_tokens=None,
        )
        result = _parse_json(response.content)
        return result
    except Exception as exc:
        _logger.warning("verify_test_dataset_structure: failed: %s", exc)
        return {
            "verification_status": "error",
            "structural_issues": [{"issue_type": "verification_failed", "field_path": "", "expected": "", "actual": str(exc), "severity": "critical"}],
            "field_coverage": {},
            "summary": f"Structure verification failed: {exc}",
        }


async def generate_and_verify(
    *,
    provider,
    signal_spec: dict,
    sufficiency_result: dict,
    source_records: list[dict],
    record_names: list[str],
) -> dict:
    """
    Full end-to-end: generate test dataset + verify structure match.

    Verification is CODE-BASED (deterministic), not AI-based.
    This ensures the JSON structure is EXACTLY the same as the source data.
    """
    # Phase 1: Generate test records via AI
    gen_result = await generate_signal_test_dataset(
        provider=provider,
        signal_spec=signal_spec,
        sufficiency_result=sufficiency_result,
        source_records=source_records,
        record_names=record_names,
    )

    if gen_result.get("generation_status") != "success" or not gen_result.get("records"):
        return {
            "generation": gen_result,
            "verification": {"verification_status": "skipped", "summary": "Generation failed — no records to verify"},
            "overall_status": "failed",
            "ready_for_codegen": False,
        }

    # Phase 2: CODE-BASED structural verification (deterministic, no AI)
    verify_result = verify_structure_with_code(
        source_records=source_records,
        record_names=record_names,
        test_records=gen_result["records"],
    )

    # Determine readiness based on code verification
    critical_count = verify_result.get("critical_issues", 0)
    match_status = verify_result.get("verification_status", "mismatch")
    ready = match_status in ("match", "partial_match") and critical_count == 0

    return {
        "generation": gen_result,
        "verification": verify_result,
        "overall_status": "ready" if ready else "needs_fixes",
        "ready_for_codegen": ready,
        "test_record_count": len(gen_result.get("records", [])),
        "scenario_coverage": gen_result.get("scenario_coverage", {}),
    }
