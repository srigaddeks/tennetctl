---
source_file: "03_docs/00_main/protocols/001_node_catalog_protocol_v1.md"
type: "document"
community: "Database Architecture Concepts"
tags:
  - graphify/document
  - graphify/EXTRACTED
  - community/Database_Architecture_Concepts
---

# NCP v1 — Node Catalog Protocol (tennetctl/v1)

## Connections
- [[ADR-016 Node-First Architecture]] - `references` [EXTRACTED]
- [[Core Rule Sub-features communicate only via run_node(key, ctx, inputs), never direct imports]] - `references` [EXTRACTED]
- [[NCP §1 Entity Identity — key grammar for ModuleFeatureSub-featureNodeFlow]] - `references` [EXTRACTED]
- [[NCP §10 Cross-Import Rule — validator blocks sub-feature→sub-feature imports; enforced at pre-commit]] - `references` [EXTRACTED]
- [[NCP §11 Boot Sequence — parse modules, discover manifests, validate, filter, resolve handlers, upsert catalog]] - `references` [EXTRACTED]
- [[NCP §12 Lifecycle — undeclared → active → deprecated (180d) → tombstoned → key_reusable (365d)]] - `references` [EXTRACTED]
- [[NCP §13 Versioning — integer version, separate keys for parallel versions, deprecated_at + replaced_by]] - `references` [EXTRACTED]
- [[NCP §14 Error Codes — CAT_MANIFEST_INVALID, CAT_NODE_NOT_FOUND, CAT_NODE_TOMBSTONED, CAT_AUTH_DENIED, etc.]] - `references` [EXTRACTED]
- [[NCP §15 Out of Scope — declarative flow execution, React Flow canvas, APISIX gateway sync, MCP server]] - `references` [EXTRACTED]
- [[NCP §2 Folder Structure — feature.manifest.yaml + 5-file sub-feature shape + nodes]] - `references` [EXTRACTED]
- [[NCP §3 Feature Manifest Grammar — apiVersion tennetctlv1, kind Feature, spec with nodesroutesui_pages]] - `references` [EXTRACTED]
- [[NCP §4 Node Contract (Python) — Node class with InputOutput BaseModel + async run(ctx, inputs)]] - `references` [EXTRACTED]
- [[NCP §5 Catalog DB Schema — schema 01_catalog with dim_modules, fct_features, fct_nodes, dtl_attrs]] - `references` [EXTRACTED]
- [[NCP §6 NodeContext — frozen dataclass carrying user_id, session_id, org_id, trace_id, span_id, conn]] - `references` [EXTRACTED]
- [[NCP §7 Node Runner — run_node(key, ctx, inputs) catalog lookup, authz, resolve handler, execute]] - `references` [EXTRACTED]
- [[NCP §8 Execution Policy — timeout_ms, retries (TransientError only), tx modes (callerownnone)]] - `references` [EXTRACTED]
- [[NCP §9 Authorization Hook — authz.check_call(ctx, node_meta), pluggable via register_checker()]] - `references` [EXTRACTED]

#graphify/document #graphify/EXTRACTED #community/Database_Architecture_Concepts