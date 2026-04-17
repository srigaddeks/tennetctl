---
source_file: "03_docs/00_main/08_decisions/001_postgres_primary.md"
type: "document"
community: "Database Architecture Concepts"
tags:
  - graphify/document
  - graphify/EXTRACTED
  - community/Database_Architecture_Concepts
---

# ADR-001: Postgres as the Primary and Only Required Database

## Connections
- [[ADR-007 Valkey as Optional Caching and Rate-Limiting Backend]] - `references` [EXTRACTED]
- [[ClickHouse — optional backend for high-cardinality metrics (never required)]] - `references` [EXTRACTED]
- [[NATS JetStream — streaming buffer decoupling ingest rate from write rate]] - `references` [EXTRACTED]
- [[PostgreSQL 16 — only required external database for tennetctl]] - `references` [EXTRACTED]
- [[Postgres-specific features used RLS, advisory locks, CTEs, LISTENNOTIFY]] - `references` [EXTRACTED]
- [[Rationale Redis rejected — Postgres advisory locks + LISTENNOTIFY outbox covers use cases]] - `rationale_for` [EXTRACTED]
- [[Rationale SQLite rejected — lacks RLS, LISTENNOTIFY, uuid_generate_v7, advisory locks]] - `rationale_for` [EXTRACTED]
- [[Rationale single docker compose up with one Postgres instance for local dev]] - `rationale_for` [EXTRACTED]

#graphify/document #graphify/EXTRACTED #community/Database_Architecture_Concepts