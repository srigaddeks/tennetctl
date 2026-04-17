---
source_file: "backend/02_features/04_audit/sub_features/01_events/repository.py"
type: "rationale"
community: "Audit Events & Saved Views"
location: "L233"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Audit_Events_&_Saved_Views
---

# Simplified funnel: each step is a separate fetchval call with explicit params.

## Connections
- [[funnel_analysis()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Audit_Events_&_Saved_Views