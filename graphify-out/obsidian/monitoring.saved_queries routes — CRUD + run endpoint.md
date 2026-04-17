---
source_file: "backend/02_features/05_monitoring/sub_features/04_saved_queries/routes.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# monitoring.saved_queries routes — CRUD + /run endpoint

## Connections
- [[monitoring admin + health routes — worker pool health, DLQ replay (lives in saved_queries package)]] - `conceptually_related_to` [EXTRACTED]
- [[monitoring.saved_queries Pydantic schemas — SavedQueryCreateRequest, SavedQueryUpdateRequest, SavedQueryResponse]] - `references` [EXTRACTED]
- [[monitoring.saved_queries service — CRUD + run, delegates to logsmetricstraces services]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation