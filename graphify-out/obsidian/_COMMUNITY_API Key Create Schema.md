---
type: community
cohesion: 1.00
members: 2
---

# API Key Create Schema

**Cohesion:** 1.00 - tightly connected
**Members:** 2 nodes

## Members
- [[ApiKeyCreate schema (label, scopes, expires_at)]] - code - backend/02_features/03_iam/sub_features/15_api_keys/schemas.py
- [[ApiKeyCreatedResponse schema (one-time token reveal)]] - code - backend/02_features/03_iam/sub_features/15_api_keys/schemas.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/API_Key_Create_Schema
SORT file.name ASC
```
