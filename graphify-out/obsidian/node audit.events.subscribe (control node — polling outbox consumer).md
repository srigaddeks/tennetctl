---
source_file: "backend/02_features/04_audit/sub_features/01_events/nodes/subscribe_events.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# node: audit.events.subscribe (control node — polling outbox consumer)

## Connections
- [[Catalog Node Base Class]] - `implements` [EXTRACTED]
- [[audit.outbox.repository — poll_outbox, latest_outbox_id (used by notify worker)]] - `calls` [EXTRACTED]
- [[node audit.events.emit (effect node — canonical audit writer to 60_evt_audit)]] - `conceptually_related_to` [INFERRED]
- [[node audit.events.query (control node — read-only cursor-paginated event lookup)]] - `conceptually_related_to` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation