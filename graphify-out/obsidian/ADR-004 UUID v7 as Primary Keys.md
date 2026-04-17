---
source_file: "03_docs/00_main/08_decisions/004_uuid7.md"
type: "document"
community: "Database Architecture Concepts"
tags:
  - graphify/document
  - graphify/EXTRACTED
  - community/Database_Architecture_Concepts
---

# ADR-004: UUID v7 as Primary Keys

## Connections
- [[01_coreid.py — centralised UUID v7 generation (new_id())]] - `references` [EXTRACTED]
- [[PostgreSQL 16 — only required external database for tennetctl]] - `conceptually_related_to` [INFERRED]
- [[Rationale BIGSERIAL rejected — sequential integers in URLs leak entity counts]] - `rationale_for` [EXTRACTED]
- [[Rationale ULID rejected — UUID is native Postgres type; ULID requires text storage]] - `rationale_for` [EXTRACTED]
- [[Rationale UUID in URLs is safe — no sequential enumeration, no business intelligence leak]] - `rationale_for` [EXTRACTED]
- [[Rationale time-ordered keys prevent B-tree index fragmentation vs UUID v4]] - `rationale_for` [EXTRACTED]
- [[UUID v7 — time-ordered 128-bit identifier, monotonically increasing (RFC 9562, 2024)]] - `references` [EXTRACTED]
- [[uuid-utils Python library — generates UUID v7 via uuid_utils.uuid7()]] - `references` [EXTRACTED]

#graphify/document #graphify/EXTRACTED #community/Database_Architecture_Concepts