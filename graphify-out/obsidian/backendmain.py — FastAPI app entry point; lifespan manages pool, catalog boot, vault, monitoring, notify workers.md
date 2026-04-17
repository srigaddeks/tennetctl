---
source_file: "backend/main.py"
type: "code"
community: "Backend Bootstrap & Catalog"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Backend_Bootstrap_&_Catalog
---

# backend/main.py — FastAPI app entry point; lifespan manages pool, catalog boot, vault, monitoring, notify workers

## Connections
- [[01_catalogloader.py — upsert_all() discover → parse → filter modules → resolve handlers → topsort → upsert → deprecation sweep]] - `rationale_for` [EXTRACTED]
- [[01_catalogmanifest.py — Pydantic models for feature.manifest.yaml; parse_manifest + discover_manifests]] - `references` [INFERRED]
- [[api.ts — typed API client apiFetch, apiList, buildQuery, ApiClientError; envelope-aware]] - `conceptually_related_to` [INFERRED]

#graphify/code #graphify/INFERRED #community/Backend_Bootstrap_&_Catalog