---
source_file: "backend/01_catalog/cli.py"
type: "code"
community: "Backend Bootstrap & Catalog"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Backend_Bootstrap_&_Catalog
---

# 01_catalog/cli.py — CLI for catalog: lint (import checks) + upsert (boot against live DB)

## Connections
- [[01_catalogloader.py — upsert_all() discover → parse → filter modules → resolve handlers → topsort → upsert → deprecation sweep]] - `calls` [EXTRACTED]
- [[01_catalogrunner.py — run_node() dispatcher lookup → authz → resolve handler → validate → tx → retry]] - `conceptually_related_to` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/Backend_Bootstrap_&_Catalog