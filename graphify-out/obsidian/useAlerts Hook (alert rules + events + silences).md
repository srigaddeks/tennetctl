---
source_file: "frontend/src/features/monitoring/hooks/use-alerts.ts"
type: "code"
community: "Alerts UI & IAM Users"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alerts_UI_&_IAM_Users
---

# useAlerts Hook (alert rules + events + silences)

## Connections
- [[API Endpoint v1monitoringalert-rules (CRUD + pauseunpause)]] - `calls` [EXTRACTED]
- [[API Endpoint v1monitoringalerts (events + silence-from-event)]] - `calls` [EXTRACTED]
- [[API Endpoint v1monitoringsilences (CRUD)]] - `calls` [EXTRACTED]
- [[Alert Severity Levels (infowarnerrorcritical)]] - `shares_data_with` [INFERRED]
- [[Alert State (firingresolved) + Silenced overlay]] - `shares_data_with` [INFERRED]
- [[AlertList Component]] - `calls` [EXTRACTED]
- [[SilenceDialog Component]] - `calls` [EXTRACTED]
- [[useAlertRules Hook (re-export facade)]] - `references` [EXTRACTED]
- [[useSilences Hook (re-export facade)]] - `references` [EXTRACTED]
- [[useUsers Hook (IAM Users CRUD)]] - `conceptually_related_to` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/Alerts_UI_&_IAM_Users