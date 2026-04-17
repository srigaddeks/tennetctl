---
source_file: "03_docs/00_main/08_decisions/007_valkey_optional_cache.md"
type: "document"
community: "Database Architecture Concepts"
tags:
  - graphify/document
  - graphify/EXTRACTED
  - community/Database_Architecture_Concepts
---

# ADR-007: Valkey as Optional Caching and Rate-Limiting Backend

## Connections
- [[ADR-001 Postgres as the Primary and Only Required Database]] - `references` [EXTRACTED]
- [[Cache invalidation on iam.role.assigned, iam.permission.updated, iam.group.membership.changed]] - `references` [EXTRACTED]
- [[CacheBackend Protocol — abstract cache interface with getsetdeleteset_if_not_exists]] - `references` [EXTRACTED]
- [[Idempotency keys — Valkey SET NX EX or Postgres table + cleanup job]] - `references` [EXTRACTED]
- [[Permission caching — Valkey TTL cache (default 60s) for recursive CTE permission queries]] - `references` [EXTRACTED]
- [[RateLimiter Protocol — abstract rate limiter with check_and_increment]] - `references` [EXTRACTED]
- [[Rationale No durable state in Valkey — loss must be safe, system recovers in one request]] - `rationale_for` [EXTRACTED]
- [[Rationale Redis 2024 SSPL license incompatible with open-source projects; Valkey is BSD 3-Clause]] - `rationale_for` [EXTRACTED]
- [[Valkey — BSD 3-Clause community fork of Redis 7.2 (Linux Foundation)]] - `references` [EXTRACTED]

#graphify/document #graphify/EXTRACTED #community/Database_Architecture_Concepts