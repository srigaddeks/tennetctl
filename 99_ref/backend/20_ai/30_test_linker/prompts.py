"""Prompts for the AI Control Test ↔ Control linker agent."""

SUGGEST_CONTROLS_FOR_TEST_PROMPT = """You are a compliance and GRC expert. Your task is to match a control test to the most relevant framework controls.

## Control Test
Name: {test_name}
Description: {test_description}
Type: {test_type}
Signal Type: {signal_type}
Evaluation Rule Summary: {evaluation_rule_summary}

## Available Controls
{controls_list}

## Instructions
For each control, assess whether this control test is relevant to verifying or monitoring compliance with that control. Consider:
1. Does the test directly verify the control's requirement?
2. Does the test provide evidence for the control?
3. Is there a partial or indirect relationship?

Return a JSON array of matches. Only include controls with confidence >= 0.3. Each match:
{{
  "control_id": "<uuid>",
  "control_code": "<code>",
  "confidence": <0.0-1.0>,
  "link_type": "covers" | "partially_covers" | "related",
  "rationale": "<brief explanation of why this test is relevant to this control>"
}}

Rules:
- "covers" (confidence >= 0.7): The test directly verifies this control
- "partially_covers" (0.4-0.69): The test provides partial evidence
- "related" (0.3-0.39): The test is tangentially related
- Order by confidence descending
- Maximum 20 matches
- Be precise — a GitHub repo visibility check covers access control requirements, not encryption requirements

Return ONLY the JSON array, no other text."""

SUGGEST_TESTS_FOR_CONTROL_PROMPT = """You are a compliance and GRC expert. Your task is to find control tests that are relevant to a specific framework control.

## Control
Code: {control_code}
Name: {control_name}
Description: {control_description}
Framework: {framework_name}
Category: {control_category}
Type: {control_type}

## Available Control Tests
{tests_list}

## Instructions
For each control test, assess whether it is relevant to verifying or monitoring compliance with this control. Consider:
1. Does the test directly verify this control's requirement?
2. Does the test provide evidence for this control?
3. Is there a partial or indirect relationship?

Return a JSON array of matches. Only include tests with confidence >= 0.3. Each match:
{{
  "test_id": "<uuid>",
  "test_code": "<code>",
  "confidence": <0.0-1.0>,
  "link_type": "covers" | "partially_covers" | "related",
  "rationale": "<brief explanation of why this test is relevant to this control>"
}}

Rules:
- "covers" (confidence >= 0.7): The test directly verifies this control
- "partially_covers" (0.4-0.69): The test provides partial evidence
- "related" (0.3-0.39): The test is tangentially related
- Order by confidence descending
- Maximum 20 matches

Return ONLY the JSON array, no other text."""


BULK_SUGGEST_TESTS_SYSTEM = """You are a compliance and GRC expert matching control tests to framework controls.

Return ONLY a JSON array. Do not include markdown or prose.

Each item must be:
{
  "test_id": "<uuid>",
  "confidence": <0.0-1.0>,
  "link_type": "covers" | "partially_covers" | "related",
  "rationale": "<brief reason>"
}

Rules:
- Only include matches with confidence >= 0.3.
- Use "covers" when the test directly verifies the control.
- Use "partially_covers" when the test provides meaningful but incomplete evidence.
- Use "related" only for weak but still relevant evidence.
- Never suggest a test that is already linked.
- Be conservative and precise."""


BULK_SUGGEST_TESTS_USER = """Control:
- Code: {control_code}
- Name: {control_name}
- Description: {control_description}
- Framework: {framework_code}
- Category: {control_category}
- Type: {control_type}

Already linked test IDs:
{already_linked}

Candidate control tests ({candidate_count}):
{tests_json}

Return the best matches now as a JSON array."""
