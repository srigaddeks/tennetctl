---
source_file: "frontend/src/app/(dashboard)/feature-flags/evaluate/page.tsx"
type: "code"
community: "Architecture Decision Records"
location: "line 294"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Architecture_Decision_Records
---

# EvaluatePage — flag evaluation sandbox

## Connections
- [[EvaluateRequest — flag evaluation input]] - `shares_data_with` [EXTRACTED]
- [[EvaluateResponse — flag resolution result + trace]] - `shares_data_with` [EXTRACTED]
- [[Flag — feature flag type]] - `shares_data_with` [INFERRED]
- [[FlagDetailPage — flag detail with environmentsrulesoverridespermissions tabs]] - `references` [EXTRACTED]
- [[FlagsListPage — feature flags list with scope filter]] - `references` [EXTRACTED]
- [[use-evaluate hook — flag evaluation mutation]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Architecture_Decision_Records