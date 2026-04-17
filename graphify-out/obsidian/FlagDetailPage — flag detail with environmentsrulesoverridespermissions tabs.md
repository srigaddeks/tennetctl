---
source_file: "frontend/src/app/(dashboard)/feature-flags/[flagId]/page.tsx"
type: "code"
community: "Architecture Decision Records"
location: "line 34"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Architecture_Decision_Records
---

# FlagDetailPage — flag detail with environments/rules/overrides/permissions tabs

## Connections
- [[EvaluatePage — flag evaluation sandbox]] - `references` [EXTRACTED]
- [[FlagEnvironmentsPanel — per-env toggle management]] - `calls` [EXTRACTED]
- [[FlagOverridesPanel — per-entity override management]] - `calls` [EXTRACTED]
- [[FlagPermissionsPanel — role-based flag permissions]] - `calls` [EXTRACTED]
- [[FlagRulesPanel — targeting rules management]] - `calls` [EXTRACTED]
- [[use-flags hooks — feature flag CRUD]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Architecture_Decision_Records