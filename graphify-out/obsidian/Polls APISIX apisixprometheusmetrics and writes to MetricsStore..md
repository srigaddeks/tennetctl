---
source_file: "backend/02_features/05_monitoring/workers/apisix_scraper.py"
type: "rationale"
community: "Alert Evaluator Worker"
location: "L36"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Alert_Evaluator_Worker
---

# Polls APISIX /apisix/prometheus/metrics and writes to MetricsStore.

## Connections
- [[ApisixScraper]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Alert_Evaluator_Worker