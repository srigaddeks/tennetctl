---
source_file: "backend/01_catalog/manifest.py"
type: "code"
community: "Backend Bootstrap & Catalog"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Backend_Bootstrap_&_Catalog
---

# 01_catalog/manifest.py — Pydantic models for feature.manifest.yaml; parse_manifest + discover_manifests

## Connections
- [[01_catalogloader.py — upsert_all() discover → parse → filter modules → resolve handlers → topsort → upsert → deprecation sweep]] - `calls` [EXTRACTED]
- [[01_catalogrunner.py — run_node() dispatcher lookup → authz → resolve handler → validate → tx → retry]] - `calls` [EXTRACTED]
- [[backendmain.py — FastAPI app entry point; lifespan manages pool, catalog boot, vault, monitoring, notify workers]] - `references` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/Backend_Bootstrap_&_Catalog