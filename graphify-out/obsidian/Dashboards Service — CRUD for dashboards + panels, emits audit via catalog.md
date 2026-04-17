---
source_file: "backend/02_features/05_monitoring/sub_features/05_dashboards/service.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# Dashboards Service — CRUD for dashboards + panels, emits audit via catalog

## Connections
- [[CreateDashboard — node key monitoring.dashboards.create (effect kind, emits_audit=True)]] - `calls` [EXTRACTED]
- [[Dashboards Repository — raw SQL against 10_fct_monitoring_dashboards + 11_fct_monitoring_panels]] - `calls` [EXTRACTED]
- [[Dashboards Routes — full CRUD v1monitoringdashboards + nested panels]] - `calls` [EXTRACTED]
- [[DeleteDashboard — node key monitoring.dashboards.delete (effect kind, emits_audit=True)]] - `calls` [EXTRACTED]
- [[GetDashboard — node key monitoring.dashboards.get (request kind, emits_audit=False)]] - `calls` [EXTRACTED]
- [[ListDashboards — node key monitoring.dashboards.list (request kind, emits_audit=False)]] - `calls` [EXTRACTED]
- [[Node audit.events.emit]] - `calls` [EXTRACTED]
- [[UpdateDashboard — node key monitoring.dashboards.update (effect kind, emits_audit=True)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization