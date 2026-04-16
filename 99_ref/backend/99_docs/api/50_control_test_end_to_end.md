# Control Test End-to-End Guide

How to build a production-ready control test from scratch in K-Control Sandbox, test it with live data, and distribute it via the Global Library or deploy directly to a workspace.

---

## Pipeline Overview

```
Connector → Collection Run → Asset Inventory → Dataset → Signal Spec → Test Dataset → Code Gen → Threat Type → Control Test
                                                                                                                      ↓                ↓
                                                                                                              Deploy to Workspace    Publish to Global Library
```

Each step feeds into the next. Steps 4-6 (Test Dataset, Code Gen, Threat Composer) run automatically via the Pipeline Queue after a signal spec is approved. Steps 1-3 and 7-10 are manual.

---

## Step 1: Create a Connector

**What:** A connector integrates with an external system (GitHub, AWS, Azure, etc.) to collect asset data. The connector type (e.g., `github`) propagates automatically through the entire pipeline — datasets, signals, threat types, and control tests all inherit it.

**Where:** Sandbox → Connectors → Create Connector

**How:**

1. Select a provider and connector type (e.g., GitHub)
2. Provide a name and instance code (e.g., "Kreesalis GitHub", `kreesalis-github`)
3. Enter credentials:
   - **GitHub:** Classic PAT with scopes: `read:org`, `repo`, `admin:org`, `read:user`
   - Fine-grained PATs do NOT work (Steampipe requires GraphQL queries)
   - **Azure Storage:** Storage account name + access key or SAS token
4. Click "Test Connection" to verify credentials work
5. Click "Save" to create the connector

**Result:** A configured connector ready to collect assets.

**Important:**
- Connectors are **org-scoped** — configured once per org, shared across workspaces
- The connector type automatically propagates to all downstream entities (datasets, signals, threat types, control tests, global library entries)

---

## Step 2: Collect Assets

**What:** Trigger a collection run to discover and inventory assets from the connector. Uses Steampipe under the hood to query the external system.

**Where:** Sandbox → Connectors → click on connector → "Collect Assets" button

**How:**

1. Go to Connectors page
2. Click on the connector card to expand details
3. Click "Collect Assets" to trigger a collection run
4. Monitor progress in the Collection Runs section

**What gets collected (GitHub example):**

| Asset Type | Fields | Example |
|-----------|--------|---------|
| `github_repo` | name, visibility, is_private, is_fork, is_archived, description, pushed_at | Repository metadata |
| `github_workflow` | name, path, state, repository_full_name | CI/CD workflow configs |
| `github_org_member` | login, role, has_two_factor_enabled | Org membership + MFA status |
| `github_org` | name, two_factor_requirement_enabled, default_repo_permission | Org-level security settings |

**Result:** Assets stored in the asset inventory, available for dataset building.

---

## Step 3: Build a Dataset

**What:** A dataset is a collection of JSON records that signals evaluate against. Built from collected assets with automatic diversity sampling across asset types.

**Where:** Sandbox → Datasets → "Compose from Assets"

**How:**

1. Click "Compose from Assets"
2. Select the connector (data source)
3. The system automatically:
   - Pulls records across all asset types from that connector
   - Applies diversity sampling to ensure coverage
   - Creates a "Smart Dataset" with representative records
4. Review the dataset — click on records to inspect fields

**Dataset record example (github_repo):**

```json
{
  "name": "kp-gateway",
  "is_fork": "False",
  "pushed_at": "2025-04-09T07:17:16Z",
  "is_private": "True",
  "visibility": "PRIVATE",
  "is_archived": "False",
  "description": "",
  "owner_login": "kreesalis",
  "_asset_type": "github_repo",
  "_external_id": "kreesalis/kp-gateway",
  "_diversity_group": "is_archived=false | is_fork=false | is_private=true"
}
```

**Key fields:**
- `_asset_type` — identifies the record type (used by signals to filter)
- `_external_id` — unique identifier from the source system
- `_diversity_group` — diversity sampling key (ensures coverage of different configurations)

**Result:** A dataset with real collected records ready for signal evaluation.

---

## Step 4: Create a Signal Spec

**What:** A signal spec defines WHAT compliance check to perform. The AI generates a structured specification from a natural language description, then verifies the dataset has the required fields.

**Where:** Sandbox → Signals → "Spec Builder"

**Connector type auto-detection:** The connector type is automatically inferred from the dataset's `_asset_type` fields (e.g., `github_repo` → `github`). You never need to manually specify the connector type.

**How:**

1. Select the dataset created in Step 3
2. Describe the compliance check in plain English:
   - *"Detect GitHub repos that are archived"*
   - *"Check if repos have a description set"*
   - *"Detect org members without MFA enabled"*
   - *"Flag repos that haven't been pushed to in 180 days"*
3. Click "Generate Signal Spec" — the AI analyzes the dataset schema and produces:
   - **Signal Code** — unique snake_case identifier (e.g., `github_repo_missing_description`)
   - **Intent** — why this check matters for compliance/security
   - **Dataset Fields Used** — which fields the signal reads, with types and required/optional
   - **Detection Logic** — step-by-step algorithm in plain English
   - **Configurable Args** — tunable parameters (e.g., `stale_days_threshold = 180`)
   - **Test Scenarios** — expected outcomes for different inputs (all_pass, all_fail, mixed, empty, boundary)
   - **SSF Mapping** — CAEP/RISC event type and severity for signal transmission
4. Review the spec in the center panel — the left panel highlights which dataset fields are used
5. Optionally refine via the AI chat (e.g., "make the threshold configurable")
6. Click "Approve & Build" — queues the signal for automated pipeline processing

**What the signal checks:**

Each signal is a Python `evaluate(dataset: dict) -> dict` function that examines a single record:

| Check Type | Field | Condition | Result |
|-----------|-------|-----------|--------|
| Public visibility | `visibility` | `== "PUBLIC"` | fail |
| Archived repo | `is_archived` | `== "True"` | fail/warning |
| Missing description | `description` | empty string | fail |
| No MFA | `has_two_factor_enabled` | `== "False"` | fail |
| Forked repo | `is_fork` | `== "True"` | warning |
| Stale repo | `pushed_at` | older than N days | warning |
| Unrestricted repo creation | `members_allowed_repository_creation_type` | `== "all"` | warning |

**Result:** An approved signal spec queued in the Pipeline Queue for automated processing.

---

## Step 5: Test Dataset Generation (Automated)

**What:** AI generates 18 synthetic test cases covering all spec scenarios. Each test case has realistic input data and verified expected output.

**Where:** Pipeline Queue → "Test Dataset" stage (runs automatically after spec approval)

**How (automatic):**

1. AI reads the signal spec + real dataset schema
2. Generates 18+ test records with realistic field values matching the real data shape
3. Validates each record structurally (no missing fields, correct types)
4. Cross-verifies expected outputs against the spec logic using a separate LLM call
5. Corrections are applied if the verifier disagrees with the generator
6. Stores test cases as a new dataset linked to the signal

**Test case structure:**

```json
{
  "case_id": "tc_001",
  "scenario_name": "all_compliant",
  "description": "All repos have descriptions",
  "dataset_input": { "name": "my-repo", "description": "A web app", "_asset_type": "github_repo" },
  "expected_output": { "result": "pass" }
}
```

**Monitoring:** Click the "Test Dataset" badge in Pipeline Queue to see progress. Click to view generated test cases after completion.

**Result:** 18 validated test cases stored as an AI-generated test dataset.

---

## Step 6: Code Generation (Automated)

**What:** AI writes the Python `evaluate()` function based on the signal spec, then iteratively tests and fixes it until all 18 test cases pass.

**Where:** Pipeline Queue → "Code Gen" stage (runs automatically after test dataset)

**How (automatic):**

1. AI generates Python code implementing the detection logic from the spec
2. Runs the code against all 18 test cases in a **sandboxed subprocess** (RestrictedPython + resource limits)
3. If any tests fail, AI receives the failure details and generates improved code
4. Iterates up to 5 times until all tests pass
5. Extracts configurable argument schema from the code
6. Updates signal status to `Validated`
7. Auto-enqueues the Threat Composer job

**Execution safety:**
- RestrictedPython compile-time checks (no imports, no file access, no network)
- Subprocess isolation with `resource.setrlimit` (CPU time, memory caps)
- Allowed modules only: `json`, `re`, `datetime`, `math`, `statistics`, `collections`, `ipaddress`, `hashlib`

**Monitoring:** Click the "Code Gen" badge in Pipeline Queue to see iteration progress, test results per iteration, and pass rate.

**Result:** A validated Python signal with all tests passing. Signal status: `Validated`.

---

## Step 7: Create Threat Types

**What:** A threat type composes one or more signals into a boolean expression tree. It defines WHEN a threat is detected based on signal outcomes.

**Where:** Sandbox → Threat Types → "Create Threat Type"

**Note:** The Pipeline Queue's Threat Composer can auto-create threat types after codegen. It typically generates multiple threat types per signal at different severity levels (e.g., "archived repo present" at Medium, "potential secret exposure in archived repo" at High).

**How (manual):**

1. Click "Create Threat Type"
2. Set a name (e.g., "Archived Repository Legacy Code Risk")
3. Set a unique threat code (e.g., `archived_repo_legacy_code_risk`)
4. Choose severity: Informational / Low / Medium / High / Critical
5. Build the expression tree using the JSON editor:

**Simple (single signal):**

```json
{
  "signal_code": "github_repositories_archived_detection",
  "expected_result": "fail"
}
```

**Composite (AND — all signals must match):**

```json
{
  "operator": "AND",
  "conditions": [
    { "signal_code": "github_repo_public_visibility_check", "expected_result": "fail" },
    { "signal_code": "github_repo_missing_description", "expected_result": "fail" }
  ]
}
```

**Composite (OR — any signal triggers):**

```json
{
  "operator": "OR",
  "conditions": [
    { "signal_code": "github_repo_stale_check", "expected_result": "warning" },
    { "signal_code": "github_repo_archived_check", "expected_result": "fail" }
  ]
}
```

6. Use "Quick insert" buttons to add available signal codes
7. Click "Create Threat Type"

**Result:** Threat types that trigger when specific signal conditions are met.

---

## Step 8: Create Control Tests

**What:** A control test (policy) binds a threat type to automated response actions. It defines WHAT HAPPENS when a threat is detected.

**Where:** Sandbox → Control Tests → "Create Control Test"

**How:**

1. Click "Create Control Test"
2. Set a name (e.g., "Archived Repository Detection")
3. Set a unique policy code (e.g., `archived_repo_detection`)
4. Select the threat type from Step 7
5. Configure one or more actions:

| Action Type | Purpose | Config Example |
|------------|---------|----------------|
| Notification | Send alerts to users | `{"channel": "#security-alerts"}` |
| Evidence Report | Generate compliance evidence doc | `{}` |
| RCA Agent | Trigger root cause analysis | `{}` |
| Escalate | Route to higher authority | `{"escalation_level": "manager"}` |
| Create Task | Auto-create remediation task | `{"assignee": "security-team"}` |
| Webhook | Call external API | `{"url": "https://...", "method": "POST"}` |
| Disable Access | Revoke access to resource | `{}` |
| Quarantine | Isolate affected resource | `{}` |

6. Toggle "Enabled on Create" (default: enabled)
7. Optionally set a cooldown period (minutes between re-triggers)
8. Click "Create Control Test"

**Result:** An enabled control test ready for live testing and deployment.

---

## Step 9: Test with Live Execution

**What:** Run signals against real collected data to verify they work correctly in production conditions before deploying.

**Where:** Two options available:

### Option A: Execute Live (single signal)

1. Go to Sandbox → Signals
2. Click "Execute Live" on any validated/promoted signal
3. Click "Execute Live" in the dialog
4. Review results: result (pass/fail/warning), row count, execution time, detail JSON

### Option B: Dry-run Test (single control test)

1. Go to Sandbox → Control Tests
2. Click "Dry-run test" on any enabled control test
3. The system evaluates the threat type's expression tree against the latest collected data
4. Review which signals passed/failed and whether the threat would trigger

### Option C: Live Session (multiple signals, fresh collection)

1. Go to Sandbox → Live Sessions
2. Click "New Live Test"
3. Select a connector (data source)
4. Select which signals to evaluate
5. Click "Collect & Test" — system collects fresh data and runs all selected signals
6. Review aggregated results

**Result:** Verified signal behavior against real production data. Confidence that the control test works correctly before deployment.

---

## Step 10: Deploy or Publish

After testing, you have two paths to put control tests into production:

### Path A: Deploy to Workspace (direct)

**What:** Deploy the control test directly into the current org/workspace's GRC system. Shows up immediately in K-Control → Control Tests.

**Where:** Sandbox → Control Tests → "Deploy to Workspace" button

**How:**

1. Go to Control Tests page
2. Click "Deploy to Workspace" on the control test
3. Select a connector to link as the live data source
4. The control test appears in K-Control → Control Tests with "Live" status

**Best for:** Deploying to your own org/workspace for immediate use.

### Path B: Publish to Global Library (reusable)

**What:** Publish the control test as a reusable bundle that any org/workspace in the platform can deploy. The system automatically bundles the signal, threat type, policy, and test dataset.

**Where:** Sandbox → Control Tests → "Publish to Global Library" button

**How:**

1. Go to Control Tests page
2. Click "Publish to Global Library" on the control test
3. The system bundles:
   - Signal code + Python source + configurable args
   - Linked threat type + expression tree
   - Control test policy + actions + cooldown
   - AI-generated test dataset (18 test cases)
   - Dataset template for the connector type
4. The bundle appears in Sandbox → Global Library

**Deploying from Global Library (by other orgs):**

1. Go to Sandbox → Global Library
2. Browse available control tests (filter by connector type, category)
3. Click "Deploy" on a control test
4. Select target org/workspace
5. System creates all entities (signal, threat type, policy, test dataset) in the target workspace

**Best for:** Sharing validated control tests across teams, orgs, or as a marketplace.

---

## Architecture: Entity Relationships

```
Connector (org-scoped)
  └── Collection Run → Asset Inventory
       └── Dataset (records with _asset_type)
            └── Signal (Python evaluate function)
                 ├── Test Dataset (18 AI-generated test cases)
                 └── Threat Type (expression tree referencing signals)
                      └── Control Test / Policy (actions + cooldown)
                           ├── Deploy to Workspace → GRC Control Test (live)
                           └── Publish to Global Library → Global Bundle (reusable)
```

**Scoping:**
- Connectors: **org-scoped** (shared across workspaces)
- Signals, Threat Types, Policies: **workspace-scoped** (built per workspace)
- Global Library: **platform-scoped** (available to all orgs)
- GRC Control Tests: **org + workspace scoped** (deployed per workspace)

---

## Signal Contract Reference

```python
def evaluate(dataset: dict) -> dict:
    """
    Evaluate a single dataset record for compliance.

    Args:
        dataset: Dict with fields from the collected asset.
                 Always includes:
                   _asset_type  — e.g., "github_repo", "github_org_member"
                   _external_id — unique ID from source system
                 Other fields vary by asset type.

    Returns:
        {
            "result": "pass" | "fail" | "warning",
            "summary": "Human-readable one-line summary",
            "details": [
                {
                    "check": "check_name",
                    "status": "pass" | "fail",
                    "message": "Detailed explanation"
                }
            ],
            "metadata": {}  # optional extra data
        }

    Rules:
        - "pass"    = record is fully compliant
        - "fail"    = record has critical compliance violations
        - "warning" = record has minor issues but not critical
        - Always filter by _asset_type first (skip non-applicable records)
        - Return "pass" for non-applicable asset types (not "fail")
    """
```

**Allowed modules:** `json`, `re`, `datetime`, `math`, `statistics`, `collections`, `ipaddress`, `hashlib`

**Execution safety:** RestrictedPython compile-time checks + subprocess isolation with `resource.setrlimit` (CPU time limit, memory cap, no filesystem/network access).

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Pipeline stuck on "Test Dataset" | Job failed with coroutine/pool error | Click Retry on the stage. If "not found", restart backend server |
| "No signals with Python source" in Live Test | Codegen hasn't completed yet | Check Pipeline Queue for codegen status |
| Spec generation returns empty spec panel | LLM returned invalid JSON | Retry — the JSON parser now handles trailing commas and single quotes |
| Spec generation says "not feasible" | Required fields not in dataset | Use fields visible in the Dataset Schema panel (left side) |
| Codegen exhausted 5 iterations | AI couldn't write code passing all tests | Simplify the signal spec detection logic, or edit the test cases |
| Threat composer failed | `created` is a reserved logging key | Fixed — uses `threats_created` now |
| Retry button returns "not found" | Job is in completed/running state, not failed | Fixed — retry now searches failed, running, and completed states |
| "Signal has no linked connector type" on publish | Connector type not set in signal properties | Fixed — auto-detected from signal spec `asset_types` field |
| Control test shows in GRC without deploying | "Deploy to Workspace" was clicked (creates GRC test directly) | This is expected — "Deploy to Workspace" is direct deployment |

---

## API Endpoints Reference

| Action | Method | Endpoint |
|--------|--------|----------|
| List signals | GET | `/api/v1/sb/signals/?org_id=...` |
| Create signal | POST | `/api/v1/sb/signals/?org_id=...` |
| Bulk import signals | POST | `/api/v1/sb/signals/bulk-import?org_id=...` |
| Execute signal live | POST | `/api/v1/sb/signals/{id}/execute-live?org_id=...` |
| Create spec session | POST | `/api/v1/ai/signal-spec/sessions?org_id=...` |
| Generate spec (SSE) | POST | `/api/v1/ai/signal-spec/sessions/{id}/generate` |
| Approve spec | POST | `/api/v1/ai/signal-spec/sessions/{id}/approve` |
| Retry pipeline step | POST | `/api/v1/ai/signal-spec/pipelines/{signal_id}/retry-step` |
| List threat types | GET | `/api/v1/sb/threat-types/?org_id=...` |
| Create threat type | POST | `/api/v1/sb/threat-types/?org_id=...` |
| List control tests | GET | `/api/v1/sb/policies/?org_id=...` |
| Create control test | POST | `/api/v1/sb/policies/?org_id=...` |
| Test control test | POST | `/api/v1/sb/policies/{id}/test?org_id=...` |
| Promote signal | POST | `/api/v1/sb/promotions/signals/{id}/promote` |
| Publish to global library | POST | `/api/v1/sb/global-tests/publish?org_id=...` |
| Deploy from global library | POST | `/api/v1/sb/global-tests/{id}/deploy` |
| List global library | GET | `/api/v1/sb/global-tests?publish_status=published` |
