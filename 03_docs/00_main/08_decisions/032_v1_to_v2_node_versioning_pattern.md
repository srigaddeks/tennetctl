# ADR-032: v1→v2 Node Versioning Pattern

**Status:** Accepted  
**Date:** 2026-04-20  
**Phase:** 39-ncp-v1-maturity, Plan 39-03  
**Deciders:** TennetCTL architecture  

## Context

NCP v1 §13 (Node Versioning) documents the escape hatch for breaking changes: ship both v1 and v2 keys in parallel, mark v1 as `deprecated_at`, add `replaced_by`, and callers migrate one at a time. However, until someone actually executes the pattern end-to-end, claims about "non-disruptive evolution" are untested.

This ADR documents the worked example: `iam.orgs.get` → `iam.orgs.get_v2`, which adds a required output field (`workspace_count: int`), making it breaking per §13 terms. The v1 node stays live (marked deprecated) and both coexist.

## Decision

When a node's input or output schema must change in a breaking way (new required fields, type changes, field removal):

1. **Create a new node class** with suffix `_v2`, `_v3`, etc. (file: `<name>_v2.py`)
   - Copy the v1 implementation
   - Update the `key` to `iam.orgs.get_v2`
   - Increment `version` in the class from 1 → 2
   - Change Input or Output schema as needed
   - Update docstring to link to ADR-032

2. **Register both in the manifest** (feature.manifest.yaml, nodes block)
   - Keep the v1 entry unchanged, except:
     - Add `deprecated_at: <ISO date>` field
     - Add `tags: [..., deprecated, replaced_by=iam.orgs.get_v2]`
     - Update description to note "DEPRECATED — replaced by iam.orgs.get_v2 on <date>"
   - Add a NEW entry for v2:
     - `key: iam.orgs.get_v2`
     - `handler: sub_features.01_orgs.nodes.iam_orgs_get_v2.OrgsGetV2`
     - `version: 2`
     - `tags: [..., replaces=iam.orgs.get]`
     - No `deprecated_at`

3. **Callers migrate independently**
   - No forced breaking change; old code can continue calling v1
   - New flows invoke v2 directly
   - In-progress flows upgrade at their own pace

4. **Archive the v1 key** (future phase, after `deprecated_at + N days`)
   - Add `archived_at` to the manifest entry
   - Remove the node class file (optional; can also keep for reference)
   - This is a hard cutover only after sufficient migration window

## Example: iam.orgs.get → get_v2

**v1 (deprecated, live):**
```python
class Output(BaseModel):
    org: dict | None
```

**v2 (new, breaking):**
```python
class Output(BaseModel):
    org: dict | None
    workspace_count: int  # new required field
```

**Manifest:**
```yaml
- key: iam.orgs.get
  version: 1
  deprecated_at: 2026-04-20T00:00:00Z
  tags: [..., deprecated, replaced_by=iam.orgs.get_v2]
  description: "DEPRECATED — replaced by iam.orgs.get_v2 on 2026-04-20"

- key: iam.orgs.get_v2
  version: 2
  tags: [..., replaces=iam.orgs.get]
  # no deprecated_at; this is the live version
```

## Rationale

- **Parallel coexistence** prevents hard breaks. Services consuming old and new nodes can coexist during migration.
- **Version in manifest** allows runners to warn/"deprecated endpoint" responses without code changes.
- **Explicit `replaced_by` tag** documents intent and helps tooling identify migration chains.
- **Archived v1 only after N days** gives callers a grace period; no surprise hard cutover.

## Consequences

- **Caller overhead:** Services must choose which version to invoke (mitigated by default-to-latest advice in service docs).
- **Manifest growth:** Accumulates archived entries; can be pruned after archive + retention window.
- **Migration burden:** Each major version bump requires callers to evaluate whether to upgrade.
  - Mitigated by: keeping breaking changes rare, batching them into planned feature releases, and providing migration guides (like this ADR).

## References

- NCP v1 §13: Node Versioning
- Phase 39-03 (first real v1→v2 migration)
- backend/02_features/03_iam/sub_features/01_orgs/nodes/iam_orgs_get_v2.py (worked example)
