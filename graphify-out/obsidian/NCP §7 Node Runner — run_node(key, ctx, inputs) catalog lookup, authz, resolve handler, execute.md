---
source_file: "03_docs/00_main/protocols/001_node_catalog_protocol_v1.md"
type: "document"
community: "Database Architecture Concepts"
tags:
  - graphify/document
  - graphify/EXTRACTED
  - community/Database_Architecture_Concepts
---

# NCP §7 Node Runner — run_node(key, ctx, inputs): catalog lookup, authz, resolve handler, execute

## Connections
- [[Core Rule Sub-features communicate only via run_node(key, ctx, inputs), never direct imports]] - `implements` [EXTRACTED]
- [[NCP v1 — Node Catalog Protocol (tennetctlv1)]] - `references` [EXTRACTED]
- [[NCP §5 Catalog DB Schema — schema 01_catalog with dim_modules, fct_features, fct_nodes, dtl_attrs]] - `calls` [EXTRACTED]
- [[NCP §6 NodeContext — frozen dataclass carrying user_id, session_id, org_id, trace_id, span_id, conn]] - `references` [EXTRACTED]
- [[NCP §8 Execution Policy — timeout_ms, retries (TransientError only), tx modes (callerownnone)]] - `implements` [EXTRACTED]
- [[NCP §9 Authorization Hook — authz.check_call(ctx, node_meta), pluggable via register_checker()]] - `calls` [EXTRACTED]

#graphify/document #graphify/EXTRACTED #community/Database_Architecture_Concepts