---
source_file: "backend/01_catalog/loader.py"
type: "code"
community: "Backend Bootstrap & Catalog"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Backend_Bootstrap_&_Catalog
---

# 01_catalog/loader.py — upsert_all(): discover → parse → filter modules → resolve handlers → topsort → upsert → deprecation sweep

## Connections
- [[01_catalogcli.py — CLI for catalog lint (import checks) + upsert (boot against live DB)]] - `calls` [EXTRACTED]
- [[01_catalogcontext.py — NodeContext frozen dataclass; carries usersessiontraceconn through run_node]] - `conceptually_related_to` [INFERRED]
- [[01_catalogmanifest.py — Pydantic models for feature.manifest.yaml; parse_manifest + discover_manifests]] - `calls` [EXTRACTED]
- [[01_catalogrunner.py — run_node() dispatcher lookup → authz → resolve handler → validate → tx → retry]] - `calls` [EXTRACTED]
- [[backendmain.py — FastAPI app entry point; lifespan manages pool, catalog boot, vault, monitoring, notify workers]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Backend_Bootstrap_&_Catalog