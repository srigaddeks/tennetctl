---
source_file: "backend/02_features/04_audit/sub_features/01_events/nodes/audit_emit.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# node: audit.events.emit (effect node — canonical audit writer to 60_evt_audit)

## Connections
- [[Catalog Node Base Class]] - `implements` [EXTRACTED]
- [[DB table 04_audit.60_evt_audit (append-only audit events)]] - `references` [EXTRACTED]
- [[audit.events FastAPI routes (list, stats, keys, funnel, retention, tail, outbox-cursor, get)]] - `calls` [EXTRACTED]
- [[node audit.events.query (control node — read-only cursor-paginated event lookup)]] - `conceptually_related_to` [INFERRED]
- [[node audit.events.subscribe (control node — polling outbox consumer)]] - `conceptually_related_to` [INFERRED]
- [[vault.configs service (createlistgetupdatedelete config)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation