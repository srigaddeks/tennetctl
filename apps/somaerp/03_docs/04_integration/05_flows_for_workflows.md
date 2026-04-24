# Flows for Multi-Step Workflows

> When somaerp needs a multi-step, branching, retry-aware workflow, it composes a tennetctl flow rather than building its own workflow engine. Per ADR-008 and the office-hours design doc.

## When to use a flow vs a service-layer function

Default: a single mutation lives in the service layer as plain Python. One transaction, one audit emission, one response.

A tennetctl flow earns its complexity when ALL three conditions hold:

1. Multiple steps, each with its own audit / notify / retry semantics.
2. Branching on outcome (success vs failure vs partial).
3. The chain MUST be observable — operator wants to see "step 3 of 5 is currently retrying."

If only one or two of those hold, keep it in the service layer.

## How somaerp composes a flow

tennetctl ships flows/canvas in Phases 42-44 (per `01_architecture.md` ADR-016 reference). A flow is a DAG of typed nodes with edges (`next` / `success` / `failure` / `true` / `false`). somaerp owns its flow definitions in versioned YAML at `apps/somaerp/flows/*.yaml`; each is registered with tennetctl flows at boot, exactly like notify templates.

Node implementations are either:
- **Generic tennetctl nodes** — `audit.events.emit`, `notify.send`, `vault.read`, `vault.write`, branching control nodes.
- **somaerp-owned nodes** — registered under `somaerp.{layer}.{action}` keys; the implementation is a reference to a Python handler in `apps/somaerp/backend/02_features/{layer}/nodes/`.

somaerp-owned nodes follow the same NodeContract shape as tennetctl primitive nodes: typed input schema, typed output schema, handler reference, kind=`effect`.

## somaerp-owned flow keys (v0.9.0)

These are the flows somaerp ships at v0.9.0. Detailed node graphs are spec-only here; node implementations come in downstream plans.

### Flow: `somaerp.production.batch_complete_to_dispatch`

**Trigger:** operator marks a batch as completed in the production UI (`somaerp.production.batches.completed` event).

**Purpose:** orchestrate the post-batch chain that turns a completed batch into shipped bottles to customers, with the right side-effects.

```text
[start]
   ↓
[run_node: somaerp.quality.aggregate_batch_qc]      (effect — confirm all required QC checks passed)
   ↓ success                              ↓ failure
   ↓                                      ↓
[run_node: somaerp.production.compute_yield]    [run_node: somaerp.production.mark_qc_failed]
   ↓                                                       ↓
[run_node: somaerp.production.label_print_request]   [run_node: notify.send "operator.qc.batch_failed"]
   ↓                                                       ↓
[run_node: somaerp.delivery.assign_to_routes]            [end-failure]
   ↓
[run_node: notify.send (batch) "operator.production.batch_completed"]
   ↓
[run_node: audit.events.emit "somaerp.production.batches.completed"]
   ↓
[end-success]
```

Why a flow, not a service function: the QC aggregate / compute yield / route assignment chain has 5+ steps with branching on QC failure that triggers a different downstream subgraph (notify operator, hold the batch, do NOT assign to routes). Operator wants to see this run on the canvas — "we are at step 4 of 6 and route assignment is in retry."

### Flow: `somaerp.delivery.run_dispatch_to_complete`

**Trigger:** delivery lead marks a delivery run as dispatched (`somaerp.delivery.runs.dispatched`).

**Purpose:** track each stop, send per-stop customer notifications, watch for cold-chain breaches, finalize the run.

```text
[start]
   ↓
[fanout: for each stop]
   ↓
[run_node: notify.send "customer.delivery.dispatched" (per stop)]
   ↓
[wait_for: somaerp.delivery.stops.recorded (per stop)]
   ↓ success                              ↓ timeout (>30 min)
   ↓                                      ↓
[branch: stop.cold_chain_temp > 12°C ?]   [run_node: notify.send "operator.delivery.rider_late"]
   ↓ false        ↓ true
   ↓              ↓
[run_node: notify "customer.delivery.delivered"]   [run_node: notify "operator.delivery.cold_chain_breach"]
   ↓                                                         ↓
   ↓                                                  [run_node: audit.events.emit "somaerp.delivery.stops.failed" (category=critical)]
   ↓
[merge after all stops]
   ↓
[run_node: audit.events.emit "somaerp.delivery.runs.completed"]
   ↓
[end]
```

Why a flow: per-stop fanout + wait-for-event + branching on temperature + merge is an obvious DAG. The operator dashboard can render this flow live so the delivery lead sees "12 of 15 stops complete, 1 cold-chain breach at stop 7."

### Flow: `somaerp.customers.subscription_pause_workflow`

**Trigger:** customer-success operator initiates a pause (`PATCH /v1/somaerp/customers/subscriptions/{id}` body `{"status":"paused"}`).

**Purpose:** confirm the pause window, update the production demand projection, send the customer confirmation, schedule the auto-resume reminder.

```text
[start]
   ↓
[run_node: somaerp.customers.compute_pause_window_validity]
   ↓ valid               ↓ invalid (>7 days, etc.)
   ↓                     ↓
[run_node: somaerp.customers.write_pause_event]   [run_node: notify "operator.subscription.pause_invalid"]
   ↓                                                      ↓
[run_node: somaerp.production.recompute_projection]    [end-failure]
   ↓
[run_node: notify "customer.subscription.paused"]
   ↓
[schedule: at pause_end_date → send "customer.subscription.resumed"]
   ↓
[run_node: audit.events.emit "somaerp.customers.subscriptions.paused"]
   ↓
[end-success]
```

### Flow: `somaerp.procurement.daily_planner`

**Trigger:** scheduled job (4 AM IST per kitchen).

**Purpose:** compute the next 3 days' projected raw-material need from active subscriptions, current inventory, and recipes; send the operator a procurement reminder.

```text
[start]
   ↓
[run_node: somaerp.customers.list_active_demand_for_window (next 3 days)]
   ↓
[run_node: somaerp.recipes.expand_to_raw_material_need]
   ↓
[run_node: somaerp.procurement.read_current_inventory]
   ↓
[run_node: somaerp.procurement.compute_shortfall]
   ↓ shortfall > 0    ↓ shortfall = 0
   ↓                  ↓
[notify "operator.procurement.reminder"]    [end-no-action]
   ↓
[run_node: audit.events.emit "somaerp.procurement.planner.run"]
   ↓
[end]
```

### Flow: `somaerp.compliance.fssai_license_expiry_check`

**Trigger:** scheduled daily at 8 AM IST (per workspace).

**Purpose:** check vault for FSSAI license expiry; warn at 30 / 14 / 7 / 1 days remaining.

```text
[start]
   ↓
[run_node: vault.read "somaerp.tenants.{ws}.fssai_license_expiry"]
   ↓
[run_node: somaerp.compliance.compute_days_until_expiry]
   ↓
[branch: days <= 30 ?]
   ↓ false       ↓ true
   ↓             ↓
[end]    [branch: days in {30, 14, 7, 1}]
              ↓ true
              ↓
         [notify "operator.compliance.fssai_expiring"]
              ↓
         [audit.events.emit "somaerp.compliance.license_expiring" (category=compliance)]
              ↓
         [end]
```

## Flow versioning and publish

Per ADR-020 (tennetctl): flow definitions are draft → publish → immutable. somaerp follows:

- New flow definition lands as draft.
- Operator (or test environment) executes the draft.
- When validated, the flow is promoted to `active` (atomic; demotes prior active to `archived`).
- Running flows continue on the version they started with; new triggers use the active version.

This is the same versioning shape as recipes (per ADR-004) — a deliberate echo.

## What somaerp does NOT do

- Never builds a workflow engine internally. No celery, no rq, no dramatiq, no internal DAG runner.
- Never embeds branching logic in service-layer functions when a flow is the right shape.
- Never runs flows on its own runtime — the flow runner is tennetctl's. somaerp emits the trigger; tennetctl drives execution; somaerp implements the somaerp-owned nodes invoked along the way.

## Operator visibility

Every flow registered above shows up in the tennetctl canvas UI scoped to the somaerp application. The Soma Delights operator can:
- See the flow graph as a diagram.
- Watch live executions step-by-step.
- Replay or rewind a flow run for debugging.
- See per-step audit events linked from the flow run page.

This is the central reason flows beat service-layer chains for these specific cases: visibility for non-technical operators.

## Boundary with simple service-layer chains

Counter-examples — these stay in service.py, NOT a flow:

- A single PATCH endpoint that updates a row and emits one audit event.
- A POST endpoint that creates one row plus one nested join.
- A delete endpoint that soft-deletes one row.

Adding flow ceremony to these would be over-engineering. Reserve flows for the multi-step, branching, observability-critical cases listed above.

## Related documents

- `00_tennetctl_proxy_pattern.md` — proxy client (flows trigger via the same client; method signature added in plan 56-02)
- `01_auth_iam_consumption.md` — flow steps that need actor scope read it from the trigger context
- `02_audit_emission.md` — every flow step emits its own audit row
- `04_notify_integration.md` — notify is the most common flow step
- `../00_main/01_architecture.md` — references ADR-016 (node-first), ADR-017 (flow execution), ADR-020 (flow versioning)
- `../00_main/08_decisions/008_tennetctl_primitive_consumption.md`
