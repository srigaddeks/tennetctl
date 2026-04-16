# Roadmap

tennetctl is built feature by feature, with each feature carrying its own ordered sub-feature backlog.

The main roadmap stays intentionally short. It answers only:

- which features matter now
- what order they should be tackled in
- why they exist

Detailed planning belongs inside each feature's `01_sub_features.md` and `feature.manifest.yaml`.

---

## Current Build Priorities

| Priority | Feature | Why it exists | Status |
|---|---|---|---|
| P0 | Core Platform | Project scaffold, node contract model, node registry, flow definitions, visual canvas API, module gating, compiler boundaries, shared runtime contracts | ACTIVE |
| P1 | API Gateway | Route composition, auth placement, feature flag checks, rate limiting, handler boundaries | PLANNED |
| P1 | IAM | Users, sessions, org/workspace ownership, access decisions, IAM-specific reports | PLANNED |
| P1 | Audit | Durable audit trail for mutating actions and policy decisions | PLANNED |
| P1 | Feature Flags | Runtime gating for flows, handlers, and routes | PLANNED |
| P2 | Monitoring | Logs, traces, metrics, and feature-owned operational views | PLANNED |
| P3 | Notifications | Delivery side effects and outbound message workflows | PLANNED |

These priorities are enough to start. Additional features can be accepted later without bloating this file.

---

## How Planning Works

### Feature-level planning

The main roadmap tracks only feature-level priority and status.

### Sub-feature planning

Every feature owns its own ordered sub-feature backlog in:

- `03_docs/features/{nn}_{feature}/01_sub_features.md`
- `03_docs/features/{nn}_{feature}/feature.manifest.yaml`

That is the canonical place for day-to-day planning.

### Node planning

Reusable nodes are planned as part of the feature that owns them or in the shared node catalog if they are intentionally cross-feature.

---

## Roadmap Principles

1. Build the smallest stable feature boundary first.
2. Build sub-features one at a time.
3. Promote repeated behavior into reusable nodes only after the owning feature boundary is clear.
4. Keep dashboards and reports inside the feature that owns the behavior.
5. Keep the top-level roadmap short enough to stay useful.

---

## Definition of Done

### A sub-feature is done when:

- its scope is stable
- its design is documented
- its contracts are explicit
- its implementation and tests match the contracts
- its manifest status is `DONE`

### A feature is done when:

- its required feature docs are present and current
- its ordered sub-feature backlog is current
- every active public contract has implementation and tests
- its feature manifest status is `DONE`

---

## Out of Scope for This File

This roadmap does not try to list every future sub-feature, every dashboard, or every node. Those belong closer to the feature that owns them.
