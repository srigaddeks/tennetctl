"""Prompts for the Signal Code Generator agent."""

from __future__ import annotations

CODEGEN_SYSTEM_PROMPT = """You are an expert Python developer writing a compliance policy detection function.

## YOUR TASK
Write a Python function called `evaluate` that checks a SINGLE JSON record and returns a detailed compliance verdict with justification.

## FUNCTION CONTRACT
```python
def evaluate(dataset: dict) -> dict:
    # dataset = one JSON record (e.g. one GitHub repo, one workflow, one org member)
    #
    # MUST return this exact structure:
    return {{
        "result": "pass" | "fail" | "warning",
        "summary": "Clear 1-2 sentence explanation a non-technical auditor can understand",
        "details": [
            {{
                "check": "check_name",
                "status": "pass" | "fail" | "warning",
                "message": "Specific justification referencing actual values from the input — e.g. 'Repository kreesalis/kp-gateway is private (visibility=PRIVATE), meeting security policy requirements'"
            }}
        ],
        "metadata": {{}}
    }}
```

## JUSTIFICATION IS CRITICAL
The output is shown to compliance auditors. Every detail message MUST:
- Reference the ACTUAL VALUES from the input record (repo name, visibility value, etc.)
- Explain WHY this check passed or failed in plain English
- Be specific enough that someone can act on it without seeing the raw JSON
- Example GOOD: "Repository 'kreesalis/kp-gateway' is publicly accessible (visibility=PUBLIC, is_private=False), violating the source code exposure policy"
- Example BAD: "Check failed" or "Visibility is wrong"

## SANDBOX CONSTRAINTS (CRITICAL — violations crash the function)
- **NO import statements** — modules are pre-injected into globals: json, re, datetime, math, statistics, collections, ipaddress, hashlib
- Use `datetime.datetime.now(datetime.timezone.utc)` for current time
- **NO** file I/O, network, subprocess, exec(), eval(), __import__
- **String booleans**: Dataset values are STRINGS like "True", "False", "PRIVATE", "PUBLIC" — NOT Python booleans
  - CORRECT: `dataset.get("is_private", "").lower() == "true"`
  - WRONG: `dataset.get("is_private") == True`
- Always use `.get()` with defaults — fields may be missing or None
- No classes, no decorators — just a plain function

## WORKING EXAMPLE
Here is an example of a CORRECT evaluate function for a different signal:

```python
def evaluate(dataset: dict) -> dict:
    details = []
    name = dataset.get("name", "unknown")
    is_private = dataset.get("is_private", "").lower() == "true"
    visibility = dataset.get("visibility", "").upper()

    if visibility == "PUBLIC" or not is_private:
        details.append({{
            "check": "public_visibility",
            "status": "fail",
            "message": f"Repository '{{name}}' is publicly accessible (visibility={{visibility}}, is_private={{dataset.get('is_private', 'N/A')}}), violating source code exposure policy"
        }})
    else:
        details.append({{
            "check": "public_visibility",
            "status": "pass",
            "message": f"Repository '{{name}}' is private (visibility={{visibility}}), meeting security requirements"
        }})

    has_failures = any(d["status"] == "fail" for d in details)
    has_warnings = any(d["status"] == "warning" for d in details)
    result = "fail" if has_failures else "warning" if has_warnings else "pass"
    fail_count = sum(1 for d in details if d["status"] == "fail")

    return {{
        "result": result,
        "summary": f"Repository '{{name}}': {{fail_count}} policy violation(s) detected" if has_failures else f"Repository '{{name}}': all checks passed",
        "details": details,
        "metadata": {{}}
    }}
```

## SIGNAL SPECIFICATION
{spec}

## COMPLETE TEST SUITE — your code MUST pass ALL of these
Each test case shows the input JSON and the expected result. Study them carefully before writing code.

{test_records}

## OUTPUT RULES
- Return ONLY the Python function code
- No markdown fences (no ```), no backticks, no explanation text
- Just `def evaluate(dataset: dict) -> dict:` and the function body
- Make sure every detail message references actual values from the input
"""

CODEGEN_FIX_PROMPT = """The signal code needs fixing. Here is exactly what went wrong.

## CURRENT CODE
```python
{failing_code}
```

## TEST RESULTS — {passed_count}/{total_count} passing ({pass_pct}%)

### PASSING TESTS (keep these working):
{passing_tests}

### FAILING TESTS (fix these):
{failing_tests}

## ERROR DETAILS
{error_details}

## PREVIOUS FIX ATTEMPTS
{fix_history}

## INSTRUCTIONS
1. Analyze WHY the failing tests fail — look at the expected vs actual result
2. Fix the code to handle those cases WITHOUT breaking the passing tests
3. Remember: string booleans ("True"/"False"), use .get() with defaults, no imports
4. Every detail message MUST reference actual values from the input for justification
5. Return ONLY the corrected Python function — no markdown, no explanation
"""

ARGS_SCHEMA_PROMPT = """Given this Python signal function, extract keyword arguments as JSON.

```python
{code}
```

Return ONLY a JSON array (no markdown):
[{{"key": "arg_name", "label": "Label", "type": "integer"|"string"|"boolean", "default": value, "description": "...", "required": false}}]

If no keyword arguments, return []
"""
