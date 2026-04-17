---
type: community
cohesion: 0.33
members: 6
---

# Postgres Logs Store

**Cohesion:** 0.33 - loosely connected
**Members:** 6 nodes

## Members
- [[.__init__()_2]] - code - backend/02_features/05_monitoring/stores/postgres_logs_store.py
- [[.insert_batch()_1]] - code - backend/02_features/05_monitoring/stores/postgres_logs_store.py
- [[.query()_1]] - code - backend/02_features/05_monitoring/stores/postgres_logs_store.py
- [[Postgres implementation of LogsStore — batch insert + cursor pagination.]] - rationale - backend/02_features/05_monitoring/stores/postgres_logs_store.py
- [[PostgresLogsStore]] - code - backend/02_features/05_monitoring/stores/postgres_logs_store.py
- [[postgres_logs_store.py]] - code - backend/02_features/05_monitoring/stores/postgres_logs_store.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Postgres_Logs_Store
SORT file.name ASC
```
