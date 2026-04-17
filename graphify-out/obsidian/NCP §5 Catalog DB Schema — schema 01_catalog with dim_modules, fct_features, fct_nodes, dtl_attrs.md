---
source_file: "03_docs/00_main/protocols/001_node_catalog_protocol_v1.md"
type: "document"
community: "Database Architecture Concepts"
tags:
  - graphify/document
  - graphify/EXTRACTED
  - community/Database_Architecture_Concepts
---

# NCP §5 Catalog DB Schema — schema 01_catalog with dim_modules, fct_features, fct_nodes, dtl_attrs

## Connections
- [[NCP v1 — Node Catalog Protocol (tennetctlv1)]] - `references` [EXTRACTED]
- [[NCP §11 Boot Sequence — parse modules, discover manifests, validate, filter, resolve handlers, upsert catalog]] - `calls` [EXTRACTED]
- [[NCP §7 Node Runner — run_node(key, ctx, inputs) catalog lookup, authz, resolve handler, execute]] - `calls` [EXTRACTED]
- [[PostgreSQL 16 — only required external database for tennetctl]] - `references` [INFERRED]

#graphify/document #graphify/EXTRACTED #community/Database_Architecture_Concepts