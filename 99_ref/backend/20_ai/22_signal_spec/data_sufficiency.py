"""
Data Sufficiency Checker for Signal Specs
==========================================
Two-phase verification that dataset JSON structure is sufficient to build a signal.

Phase 1 (Primary): LLM analyzes spec requirements against actual dataset records
Phase 2 (Verifier): Independent LLM check with different prompt to confirm/challenge

Output: Structured DataSufficiencyReport with clear pass/fail per field, per record.
"""
from __future__ import annotations

import json
from importlib import import_module

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.signal_spec.data_sufficiency")


SUFFICIENCY_CHECK_PROMPT = """You are a strict data structure auditor for compliance signal development.

You must verify that the dataset records contain ALL the JSON fields needed to implement a signal.

CRITICAL RULES:
- NEVER invent or assume fields that don't exist in the records
- ONLY mark a field as "present" if you can see it in the actual record data
- If a field is nested (e.g., "default_branch_ref.branch_protection_rule.required_approving_review_count"), verify the FULL path exists
- If a field has different names in different records, flag it as "inconsistent"

Signal Requirements:
{signal_requirements}

Dataset Records (with their short names):
{dataset_records}

Return ONLY valid JSON:
{{
  "overall_status": "sufficient|partial|insufficient",
  "confidence": "high|medium|low",
  "field_checks": [
    {{
      "field_path": "exact.field.path",
      "required": true,
      "status": "present|missing|inconsistent|partial",
      "found_in_records": ["record_name1", "record_name2"],
      "missing_from_records": ["record_name3"],
      "sample_values": ["example1", "example2"],
      "notes": ""
    }}
  ],
  "record_coverage": [
    {{
      "record_name": "short_name",
      "has_all_required_fields": true,
      "missing_fields": [],
      "extra_fields_available": ["field1", "field2"]
    }}
  ],
  "blocking_issues": [],
  "recommendations": [],
  "summary": "One paragraph explaining the data sufficiency status"
}}"""


VERIFIER_CHECK_PROMPT = """You are an INDEPENDENT verifier reviewing a data sufficiency assessment.

A primary checker has already assessed whether a dataset has enough data to build a signal.
Your job is to VERIFY their assessment — confirm or challenge it.

Primary Assessment:
{primary_assessment}

Signal Requirements:
{signal_requirements}

Actual Dataset Records:
{dataset_records}

Verify each field_check:
1. Is the field ACTUALLY present in the records? Check the raw JSON carefully.
2. Did the primary checker miss any issues?
3. Did the primary checker incorrectly mark something as missing when it exists?

Return ONLY valid JSON:
{{
  "verification_status": "confirmed|challenged|partial_agreement",
  "overall_status": "sufficient|partial|insufficient",
  "disagreements": [
    {{
      "field_path": "...",
      "primary_said": "present|missing",
      "verifier_says": "present|missing",
      "evidence": "Why the verifier disagrees",
      "resolution": "Which assessment is correct and why"
    }}
  ],
  "additional_issues": [],
  "final_confidence": "high|medium|low",
  "summary": "Verifier's independent assessment"
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


async def check_data_sufficiency(
    *,
    provider,
    signal_requirements: dict,
    dataset_records: list[dict],
    record_names: list[str],
) -> dict:
    """
    Run two-phase data sufficiency check.

    Args:
        provider: LLM provider instance
        signal_requirements: What fields the signal needs (from spec or user description)
        dataset_records: Actual JSON records from the dataset
        record_names: Short names for each record (matching order)

    Returns:
        Combined sufficiency report with primary + verifier assessments
    """
    # Build records context with names
    records_context = ""
    for i, (rec, name) in enumerate(zip(dataset_records[:20], record_names[:20])):
        label = name or f"record_{i+1}"
        records_context += f"\n--- {label} ---\n{json.dumps(rec, indent=2, default=str)[:2000]}\n"

    requirements_text = json.dumps(signal_requirements, indent=2, default=str)[:3000]

    # Phase 1: Primary check
    _logger.info("data_sufficiency: running primary check")
    primary_prompt = SUFFICIENCY_CHECK_PROMPT.format(
        signal_requirements=requirements_text,
        dataset_records=records_context,
    )

    try:
        primary_response = await provider.chat_completion(
            messages=[
                {"role": "system", "content": primary_prompt},
                {"role": "user", "content": "Check data sufficiency now. Be strict — only mark fields as present if you can see them in the actual record JSON."},
            ],
            temperature=1,
            max_tokens=None,
        )
        primary_result = _parse_json(primary_response.content)
    except Exception as exc:
        _logger.warning("data_sufficiency: primary check failed: %s", exc)
        primary_result = {
            "overall_status": "insufficient",
            "confidence": "low",
            "field_checks": [],
            "record_coverage": [],
            "blocking_issues": [f"Primary check failed: {exc}"],
            "recommendations": [],
            "summary": "Primary data sufficiency check could not be completed.",
        }

    # Phase 2: Verifier check
    _logger.info("data_sufficiency: running verifier check")
    verifier_prompt = VERIFIER_CHECK_PROMPT.format(
        primary_assessment=json.dumps(primary_result, indent=2)[:4000],
        signal_requirements=requirements_text,
        dataset_records=records_context,
    )

    try:
        verifier_response = await provider.chat_completion(
            messages=[
                {"role": "system", "content": verifier_prompt},
                {"role": "user", "content": "Verify the primary assessment. Check each field against the actual JSON records."},
            ],
            temperature=1,
            max_tokens=None,
        )
        verifier_result = _parse_json(verifier_response.content)
    except Exception as exc:
        _logger.warning("data_sufficiency: verifier check failed: %s", exc)
        verifier_result = {
            "verification_status": "partial_agreement",
            "overall_status": primary_result.get("overall_status", "insufficient"),
            "disagreements": [],
            "additional_issues": [f"Verifier check failed: {exc}"],
            "final_confidence": "low",
            "summary": "Verifier check could not be completed — relying on primary assessment only.",
        }

    # Combine results
    final_status = verifier_result.get("overall_status", primary_result.get("overall_status", "insufficient"))
    final_confidence = verifier_result.get("final_confidence", primary_result.get("confidence", "low"))

    return {
        "status": final_status,
        "confidence": final_confidence,
        "is_sufficient": final_status == "sufficient",
        "primary_check": primary_result,
        "verifier_check": verifier_result,
        "field_checks": primary_result.get("field_checks", []),
        "record_coverage": primary_result.get("record_coverage", []),
        "blocking_issues": primary_result.get("blocking_issues", []) + verifier_result.get("additional_issues", []),
        "disagreements": verifier_result.get("disagreements", []),
        "recommendations": primary_result.get("recommendations", []),
        "summary": f"Primary: {primary_result.get('summary', '')} | Verifier: {verifier_result.get('summary', '')}",
    }
