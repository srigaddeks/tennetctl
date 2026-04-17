---
source_file: "backend/02_features/05_monitoring/stores/postgres_resources_store.py"
type: "rationale"
community: "Monitoring Stores & Workers"
location: "L28"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Monitoring_Stores_&_Workers
---

# Hash-interned resource records. Idempotent upsert on (org_id, resource_hash).

## Connections
- [[PostgresResourcesStore]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Monitoring_Stores_&_Workers