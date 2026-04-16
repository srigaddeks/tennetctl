"""Prompts for the Test Dataset Generator agent."""

from __future__ import annotations

TEST_DATASET_SYSTEM_PROMPT = """
You are generating test datasets for a security signal. The dataset schema below shows the EXACT
structure produced by the live collection system — same keys, same nesting, same array/object patterns.

RULES (non-negotiable):
1. Vary ONLY the VALUES to create different test scenarios — never change the STRUCTURE
2. NEVER add keys not in the schema
3. NEVER remove required keys
4. NEVER change an object to an array or vice versa
5. NEVER change field names (case-sensitive)
6. Keep the same nesting depth
7. Generate realistic-looking values for the connector type

Signal spec:
{spec}

Dataset schema (the EXACT structure — do not deviate):
{rich_schema}

Generate {num_cases} test cases. Return ONLY a JSON array — no markdown, no explanation:
[
  {{
    "case_id": "tc_001",
    "scenario_name": "all_compliant",
    "description": "All items pass all checks",
    "dataset_input": {{ ...exact same structure as schema... }},
    "expected_output": {{
      "result": "pass",
      "summary": "Human readable summary matching the signal's expected output format",
      "details": [{{ "check": "check_name", "status": "pass", "message": "..." }}]
    }},
    "configurable_args_override": {{}}
  }}
]

Test scenarios to cover (from spec):
{test_scenarios}

Additional edge cases to always include:
- Empty dataset (all collections empty)
- Single-item collection
- Boundary value for each configurable arg (at min, at max)
- Mixed result (some pass, some fail)
"""

STRUCTURAL_DIFF_PROMPT = """
A test case was generated but its structure deviates from the expected schema.
Fix ONLY the structural issues — keep the values as close to the original as possible.

Expected structure (reference schema):
{rich_schema}

Generated (broken) dataset_input:
{broken_input}

Structural violations:
{violations}

Return ONLY the corrected dataset_input as valid JSON. No markdown, no explanation.
"""
