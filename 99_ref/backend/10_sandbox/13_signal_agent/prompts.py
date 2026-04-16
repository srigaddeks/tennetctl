from __future__ import annotations

# ---------------------------------------------------------------------------
# Core signal generation prompt
# ---------------------------------------------------------------------------

SIGNAL_SYSTEM_PROMPT = """You are a senior security signal engineer writing Python compliance checks for the K-Control Sandbox.

Rules:
1. Function name MUST be `evaluate` — never `run`, `check`, `main`, or anything else
2. Signature: `def evaluate(dataset: dict, <named_kwargs_with_defaults>) -> dict`
   - Named kwargs MUST have sensible defaults so evaluate(dataset) works with no kwargs
   - Use explicit named params (e.g. min_count: int = 2), NOT **kwargs
3. Return EXACTLY this structure:
   {{"result": "pass" | "fail" | "warning", "summary": "<human-readable summary>",
     "details": [{{"check": "<name>", "status": "pass" | "fail" | "warning", "message": "<detail>"}}],
     "metadata": {{}}}}
4. Allowed modules (already injected, do NOT import): json, re, datetime, math, statistics, collections, ipaddress, hashlib
5. Allowed builtins: len, range, enumerate, zip, map, filter, sorted, reversed, min, max, sum, abs, round, all, any, isinstance, type, str, int, float, bool, list, dict, tuple, set, frozenset, print, hasattr, getattr
6. Forbidden: import statements, file I/O, network, os, sys, subprocess, eval, exec, __import__
7. Use ONLY fields that exist in the dataset schema below — never invent field names
8. Return "warning" for borderline cases, "fail" for clear violations, "pass" when fully compliant
9. Include one details entry per entity checked (per repo, per user, per policy, etc.)

Dataset schema:
{dataset_schema}

Examples for {connector_type}:
{examples}
"""

# ---------------------------------------------------------------------------
# Code fix prompt
# ---------------------------------------------------------------------------

SIGNAL_FIX_PROMPT = """A security signal has a code error. Fix it exactly as described below.

Error type: {error_type}
Error message: {error_message}

Failing code:
```python
{failing_code}
```

Fix history (previous attempts):
{fix_history}

Rules:
1. Return ONLY valid Python code — no markdown fences, no explanation, no comments about the fix
2. Keep the same evaluate() signature and named kwargs with defaults
3. Fix exactly the described error — do not refactor or restructure beyond what is needed
4. If the error is about a missing field: check for the field with .get() and handle None gracefully
"""

# ---------------------------------------------------------------------------
# Name/description suggestion prompt
# ---------------------------------------------------------------------------

SIGNAL_NAME_PROMPT = """Given a security signal function and its original intent, suggest a display name and description.

Original intent: {prompt}

Signal code:
```python
{code}
```

Return ONLY a JSON object — no markdown fences, no explanation:
{{"name": "short_snake_case_identifier", "description": "One-sentence description of what this signal checks and why it matters"}}
"""

# ---------------------------------------------------------------------------
# Args schema extraction prompt
# ---------------------------------------------------------------------------

SIGNAL_ARGS_SCHEMA_PROMPT = """Extract all named keyword arguments from this Python signal function and describe them.

Signal code:
```python
{code}
```

Return ONLY a JSON array — no markdown fences, no explanation.
If there are no keyword arguments (beyond dataset), return [].

[
  {{
    "key": "arg_name",
    "label": "Human Readable Label",
    "type": "integer" | "string" | "boolean" | "enum",
    "default": <the_default_value>,
    "description": "One-sentence description of what this argument controls",
    "min": <number_or_null>,
    "max": <number_or_null>,
    "options": ["option1", "option2"]
  }}
]

Notes:
- "type" must be exactly one of: integer, string, boolean, enum
- "options" is only required when type is "enum"
- "min" and "max" are only for integer/number types
"""

# ---------------------------------------------------------------------------
# SSF mapping prompt
# ---------------------------------------------------------------------------

SIGNAL_SSF_MAPPING_PROMPT = """Map this security signal to the appropriate SSF/CAEP/RISC event standard.

Signal name: {signal_name}
Signal description: {description}
Connector type: {connector_type}

CAEP event types (use one if applicable):
- session-revoked, token-claims-change, credential-change, assurance-level-change,
  device-compliance-change, session-established, session-presented

RISC event types (use one if applicable):
- credential-compromise, account-disabled, account-enabled, account-credential-change-required,
  account-purged, identifier-changed, identifier-recycled, recovery-activated, recovery-information-changed

Subject types: repository, user, organization, device, service_account, team

Return ONLY a JSON object — no markdown fences, no explanation:
{{
  "standard": "caep" | "risc" | "custom",
  "event_type": "<caep_or_risc_event_type_or_null>",
  "event_uri": "<full_schema_uri_or_null>",
  "custom_event_uri": "<custom_kcontrol_uri_or_null>",
  "signal_severity": "critical" | "high" | "medium" | "low" | "info",
  "subject_type": "<subject_type>"
}}

If no CAEP or RISC event type fits, set standard to "custom" and set custom_event_uri to:
"https://kcontrol.io/events/sandbox/<connector_type>/<signal_slug>"
"""

# ---------------------------------------------------------------------------
# Few-shot connector examples
# ---------------------------------------------------------------------------

CONNECTOR_EXAMPLES: dict[str, list[dict[str, str]]] = {
    "aws_iam": [
        {
            "name": "MFA Disabled Check",
            "code": (
                'def evaluate(dataset: dict, require_mfa: bool = True) -> dict:\n'
                '    users = dataset.get("users", [])\n'
                '    if not require_mfa:\n'
                '        return {"result": "pass", "summary": "MFA check disabled by config", "details": [], "metadata": {}}\n'
                '    no_mfa = [u for u in users if not u.get("mfa_enabled", False)]\n'
                '    return {\n'
                '        "result": "fail" if no_mfa else "pass",\n'
                '        "summary": f"{len(no_mfa)}/{len(users)} users without MFA",\n'
                '        "details": [\n'
                '            {"check": "mfa_enabled", "status": "fail" if not u.get("mfa_enabled") else "pass",\n'
                '             "message": u.get("username", "unknown")}\n'
                '            for u in users\n'
                '        ],\n'
                '        "metadata": {}\n'
                '    }'
            ),
        },
        {
            "name": "Password Policy Strength",
            "code": (
                'def evaluate(dataset: dict, min_length: int = 14) -> dict:\n'
                '    policy = dataset.get("password_policy", {})\n'
                '    checks = []\n'
                '    length = policy.get("minimum_length", 0)\n'
                '    checks.append({"check": "min_length", "status": "pass" if length >= min_length else "fail",\n'
                '                   "message": f"Minimum length: {length} (required: {min_length})"})\n'
                '    checks.append({"check": "require_uppercase",\n'
                '                   "status": "pass" if policy.get("require_uppercase") else "fail",\n'
                '                   "message": "Uppercase required" if policy.get("require_uppercase") else "Uppercase NOT required"})\n'
                '    failed = [c for c in checks if c["status"] == "fail"]\n'
                '    return {\n'
                '        "result": "fail" if failed else "pass",\n'
                '        "summary": f"{len(failed)}/{len(checks)} password policy checks failed",\n'
                '        "details": checks,\n'
                '        "metadata": {}\n'
                '    }'
            ),
        },
    ],
    "github": [
        {
            "name": "Branch Protection Review Count",
            "code": (
                'def evaluate(dataset: dict, min_review_count: int = 2) -> dict:\n'
                '    repos = dataset.get("repositories", [])\n'
                '    details = []\n'
                '    for repo in repos:\n'
                '        bp = repo.get("branch_protections", {})\n'
                '        enabled = bp.get("enabled", False)\n'
                '        count = bp.get("required_approving_review_count", 0)\n'
                '        if not enabled:\n'
                '            status = "fail"\n'
                '            msg = "Branch protection disabled"\n'
                '        elif count < min_review_count:\n'
                '            status = "fail"\n'
                '            msg = f"{count} reviewers (min: {min_review_count})"\n'
                '        elif count == min_review_count:\n'
                '            status = "warning"\n'
                '            msg = f"Exactly at minimum ({count} reviewers)"\n'
                '        else:\n'
                '            status = "pass"\n'
                '            msg = f"{count} reviewers"\n'
                '        details.append({"check": "branch_protection_review_count",\n'
                '                        "status": status, "message": f\'{repo.get(\"name\", \"unknown\")}: {msg}\'})\n'
                '    failed = [d for d in details if d["status"] != "pass"]\n'
                '    return {\n'
                '        "result": "fail" if any(d["status"] == "fail" for d in details) else\n'
                '                  "warning" if failed else "pass",\n'
                '        "summary": f"{len(failed)}/{len(repos)} repos with insufficient reviewer requirements",\n'
                '        "details": details,\n'
                '        "metadata": {}\n'
                '    }'
            ),
        },
        {
            "name": "Secret Scanning Enabled",
            "code": (
                'def evaluate(dataset: dict) -> dict:\n'
                '    repos = dataset.get("repositories", [])\n'
                '    disabled = [r.get("name", "unknown") for r in repos\n'
                '                if not r.get("secret_scanning_enabled", False)]\n'
                '    return {\n'
                '        "result": "fail" if disabled else "pass",\n'
                '        "summary": f"{len(disabled)}/{len(repos)} repos without secret scanning",\n'
                '        "details": [\n'
                '            {"check": "secret_scanning", "status": "fail", "message": name}\n'
                '            for name in disabled\n'
                '        ],\n'
                '        "metadata": {}\n'
                '    }'
            ),
        },
    ],
    "kubernetes": [
        {
            "name": "Privileged Containers Check",
            "code": (
                'def evaluate(dataset: dict) -> dict:\n'
                '    pods = dataset.get("pods", [])\n'
                '    privileged = []\n'
                '    for pod in pods:\n'
                '        for container in pod.get("containers", []):\n'
                '            if container.get("security_context", {}).get("privileged", False):\n'
                '                privileged.append(f\'{pod.get("name", "?")}:{container.get("name", "?")}\')\n'
                '    return {\n'
                '        "result": "fail" if privileged else "pass",\n'
                '        "summary": f"{len(privileged)} privileged containers found",\n'
                '        "details": [{"check": "privileged", "status": "fail", "message": c} for c in privileged],\n'
                '        "metadata": {}\n'
                '    }'
            ),
        },
    ],
    "azure_ad": [
        {
            "name": "Conditional Access Policies",
            "code": (
                'def evaluate(dataset: dict) -> dict:\n'
                '    policies = dataset.get("conditional_access_policies", [])\n'
                '    disabled = [p.get("name", "unknown") for p in policies if p.get("state") != "enabled"]\n'
                '    return {\n'
                '        "result": "warning" if disabled else "pass",\n'
                '        "summary": f"{len(disabled)}/{len(policies)} conditional access policies not enabled",\n'
                '        "details": [{"check": "ca_policy", "status": "fail", "message": n} for n in disabled],\n'
                '        "metadata": {}\n'
                '    }'
            ),
        },
    ],
    "gcp": [
        {
            "name": "Public Storage Buckets",
            "code": (
                'def evaluate(dataset: dict) -> dict:\n'
                '    buckets = dataset.get("storage_buckets", [])\n'
                '    public = [b.get("name", "unknown") for b in buckets if b.get("is_public", False)]\n'
                '    return {\n'
                '        "result": "fail" if public else "pass",\n'
                '        "summary": f"{len(public)}/{len(buckets)} buckets publicly accessible",\n'
                '        "details": [{"check": "public_access", "status": "fail", "message": n} for n in public],\n'
                '        "metadata": {}\n'
                '    }'
            ),
        },
    ],
    "azure_storage": [
        {
            "name": "Blob Container Public Access",
            "code": (
                'def evaluate(dataset: dict) -> dict:\n'
                '    containers = dataset.get("blob_containers", [])\n'
                '    public = [c.get("name", "unknown") for c in containers\n'
                '              if c.get("public_access") not in (None, "None", "none", "")]\n'
                '    return {\n'
                '        "result": "fail" if public else "pass",\n'
                '        "summary": f"{len(public)}/{len(containers)} containers with public access",\n'
                '        "details": [{"check": "public_access", "status": "fail", "message": n} for n in public],\n'
                '        "metadata": {}\n'
                '    }'
            ),
        },
    ],
}
