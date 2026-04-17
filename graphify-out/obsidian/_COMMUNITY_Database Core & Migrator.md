---
type: community
cohesion: 0.40
members: 5
---

# Database Core & Migrator

**Cohesion:** 0.40 - moderately connected
**Members:** 5 nodes

## Members
- [[DB schema 00_schema_migrations (applied_migrations, applied_seeds tracking)]] - code - backend/01_migrator/runner.py
- [[Migration file layout (03_docsfeatures{nn}05_sub_features{nn}09_sql_migrations)]] - document - backend/01_migrator/runner.py
- [[SQL Migrator runner (applyrollbackseedstatushistorynew)]] - code - backend/01_migrator/runner.py
- [[asyncpg JSONB codec (auto encodedecode Python dicts — no json.dumps needed)]] - code - backend/01_core/database.py
- [[core database (asyncpg pool + JSONB codec)]] - code - backend/01_core/database.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Database_Core_&_Migrator
SORT file.name ASC
```
