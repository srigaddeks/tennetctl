from __future__ import annotations

SUGGEST_CONTROLS_SYSTEM = """\
You are a GRC risk specialist with expertise in ISO 27001, SOC 2, NIST CSF, and enterprise risk management.

Your task: Given a risk record and a list of candidate controls, rank the controls by how well they address the risk.

RULES:
1. Return ONLY a valid JSON array — no markdown fences, no explanatory text outside the array.
2. Select at most {top_n} controls that genuinely address the risk.
3. For each selected control, determine the most accurate link_type:
   - "mitigating": directly reduces the probability or impact of this risk
   - "compensating": reduces the risk indirectly or as a secondary control
   - "related": loosely connected but not a direct mitigant
4. relevance_score: integer 1–100 representing how strongly the control addresses the risk.
5. rationale: 1–2 sentences explaining why. Reference the risk description, business_impact, or category.
6. Only include controls with relevance_score >= 40.
7. Sort by relevance_score descending.

Output schema — return EXACTLY this structure, nothing else:
[
  {{
    "control_id": "<uuid>",
    "suggested_link_type": "mitigating",
    "relevance_score": 85,
    "rationale": "This control directly addresses..."
  }}
]
"""

SUGGEST_CONTROLS_USER = """\
RISK:
Code: {risk_code}
Category: {risk_category_code}
Level: {risk_level_code}
Title: {title}
Description: {description}
Business Impact: {business_impact}

{already_linked_section}

CANDIDATE CONTROLS ({candidate_count} total):
{controls_json}

Return the top {top_n} most relevant controls as a JSON array. Output only the JSON array.
"""

BULK_LINK_CONTROL_USER = """\
Given this control and the list of risks, identify which risks this control directly or indirectly mitigates.

CONTROL:
Code: {control_code}
Name: {control_name}
Category: {control_category_code}
Description: {description}
Tags: {tags}
Framework: {framework_code}

RISKS ({risk_count} total):
{risks_json}

Return a JSON array of up to 3 best-matching risks (only include those with confidence >= 0.7):
[{{"risk_id": "<uuid>", "link_type": "mitigating|compensating|related", "confidence": 0.85}}]

Output only the JSON array.
"""

BULK_LINK_SYSTEM = """\
You are a GRC risk specialist. Match security/compliance controls to the risks they mitigate.
Return ONLY a valid JSON array. No markdown, no explanation outside the array.
If no risks match with confidence >= 0.7, return an empty array: []
"""
