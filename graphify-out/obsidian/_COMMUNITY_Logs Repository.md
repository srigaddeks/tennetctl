---
type: community
cohesion: 1.00
members: 1
---

# Logs Repository

**Cohesion:** 1.00 - tightly connected
**Members:** 1 nodes

## Members
- [[monitoring.logs repository (intentionally empty — writes handled by JetStream consumer)]] - code - backend/02_features/05_monitoring/sub_features/01_logs/repository.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Logs_Repository
SORT file.name ASC
```
