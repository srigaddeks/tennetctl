---
source_file: "backend/02_features/05_monitoring/workers/apisix_scraper.py"
type: "rationale"
community: "Alert Evaluator Worker"
location: "L107"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Alert_Evaluator_Worker
---

# Single scrape. Returns number of samples written. Never raises.

## Connections
- [[.scrape_once()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Alert_Evaluator_Worker