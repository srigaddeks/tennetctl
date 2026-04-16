# Rules

These are hard rules. They define the architecture, not just coding style.

If a rule becomes wrong, replace it with a new ADR and update this file. Do not work around it silently.

---

## Architecture Rules

### R-001: Features own bounded domains

Every feature owns one bounded area of the product. Its docs, handlers, reports, dashboards, and contracts live with that feature.

### R-002: Sub-features are the smallest shippable units

A sub-feature must be small enough to scope, design, implement, test, and review independently. If a sub-feature cannot be explained clearly in one scope doc and one design doc, split it.

### R-003: Dependencies are allowed only through declared public contracts

No feature or sub-feature may depend on another feature's internal tables, internal services, or private helper code. Cross-boundary usage must go through declared contracts.

### R-004: Nodes are registered backend contracts, not ad hoc glue

Every public node is a backend-defined runtime contract. In most cases the implementation is a Python function, but a public node is not just a callable. It must also define:

- config schema
- input schema
- output schema
- runtime class
- editor metadata

### R-005: Request-path logic and effect logic stay separate

Nodes that decide the live request path stay in the request path. Nodes that emit side effects run as effects. Do not force everything into one async model.

Examples:

- request-path: auth, feature flags, input validation, rate limiting, handler execution
- effect: audit, logs, traces, metrics, notifications

### R-006: Backend code is the source of truth

The frontend may compose, visualize, and configure flows, but backend contracts and backend execution semantics are authoritative.

### R-007: Feature dashboards belong to the feature

IAM dashboards belong to IAM. Audit dashboards belong to Audit. Monitoring dashboards belong to Monitoring. Reporting surfaces are owned by the same feature that owns the underlying behavior and data.

### R-008: Cross-cutting decisions go in ADRs; local decisions stay local

Use ADRs only for repo-wide or cross-feature decisions. Feature-specific or sub-feature-specific design choices belong in feature docs, sub-feature docs, or node docs.

---

## Documentation Rules

### R-009: Every feature uses the same minimal doc pack

Every feature must have exactly these required docs:

- `00_overview.md`
- `01_sub_features.md`
- `04_architecture/01_architecture.md`
- `feature.manifest.yaml`

Additional docs are optional.

### R-010: Every sub-feature uses the same minimal doc pack

Every sub-feature must have exactly these required docs:

- `01_scope.md`
- `02_design.md`
- `sub_feature.manifest.yaml`

Add `05_api_contract.yaml` only when the sub-feature exposes an external interface worth documenting separately.

### R-011: Every doc must declare ownership and boundaries

Every feature and sub-feature must say:

- what it owns
- what it does not own
- what it depends on
- what contracts it exposes

If those boundaries are unclear, the design is not ready.

---

## Runtime and Code Rules

### R-012: Raw SQL remains the default data access model

All persistent data access uses explicit SQL. If this changes, it requires a new ADR.

### R-013: No silent error swallowing

Errors are handled explicitly or propagated. Logging an error and continuing without a clear contract is not acceptable in production code.

### R-014: Validate at the boundary

Requests, node config, node inputs, and node outputs are validated at their boundaries. Untyped dict-based composition is not the public architecture.

### R-015: No feature ships without tests that match its declared contracts

If a feature, sub-feature, or node publishes a contract, tests must verify that contract.

### R-016: Every mutating operation emits or records an auditable trace

The exact storage path may vary by feature, but write operations cannot disappear into the system without an auditable trail.
