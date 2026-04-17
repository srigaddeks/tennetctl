---
source_file: "backend/01_catalog/context.py"
type: "code"
community: "Backend Bootstrap & Catalog"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Backend_Bootstrap_&_Catalog
---

# 01_catalog/context.py — NodeContext frozen dataclass; carries user/session/trace/conn through run_node

## Connections
- [[01_catalogloader.py — upsert_all() discover → parse → filter modules → resolve handlers → topsort → upsert → deprecation sweep]] - `conceptually_related_to` [INFERRED]
- [[01_catalogrunner.py — run_node() dispatcher lookup → authz → resolve handler → validate → tx → retry]] - `references` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Backend_Bootstrap_&_Catalog