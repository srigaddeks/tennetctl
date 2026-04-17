---
source_file: "backend/01_catalog/runner.py"
type: "code"
community: "Backend Bootstrap & Catalog"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Backend_Bootstrap_&_Catalog
---

# 01_catalog/runner.py — run_node() dispatcher: lookup → authz → resolve handler → validate → tx → retry

## Connections
- [[01_catalogcli.py — CLI for catalog lint (import checks) + upsert (boot against live DB)]] - `conceptually_related_to` [INFERRED]
- [[01_catalogcontext.py — NodeContext frozen dataclass; carries usersessiontraceconn through run_node]] - `references` [EXTRACTED]
- [[01_catalogloader.py — upsert_all() discover → parse → filter modules → resolve handlers → topsort → upsert → deprecation sweep]] - `calls` [EXTRACTED]
- [[01_catalogmanifest.py — Pydantic models for feature.manifest.yaml; parse_manifest + discover_manifests]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Backend_Bootstrap_&_Catalog