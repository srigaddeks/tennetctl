---
source_file: "backend/02_features/04_audit/sub_features/03_outbox/repository.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# audit.outbox.repository — poll_outbox, latest_outbox_id (used by notify worker)

## Connections
- [[DB table 61_evt_audit_outbox (append-only, BIGINT cursor)]] - `references` [EXTRACTED]
- [[DB view v_audit_events]] - `references` [EXTRACTED]
- [[Outbox polling pattern (since_id BIGINT cursor, oldest-first, optional org_id filter)]] - `implements` [EXTRACTED]
- [[audit outbox service (current_cursor, poll)]] - `calls` [EXTRACTED]
- [[audit.outbox schemas (AuditEventRowSlim, AuditTailResponse, AuditOutboxCursorResponse)]] - `shares_data_with` [INFERRED]
- [[node audit.events.subscribe (control node — polling outbox consumer)]] - `calls` [EXTRACTED]
- [[notify.worker — Subscription worker polls audit outbox, matches subscriptions, enqueues deliveries]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation