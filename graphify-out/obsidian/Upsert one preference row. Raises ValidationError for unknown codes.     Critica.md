---
source_file: "backend/02_features/06_notify/sub_features/09_preferences/service.py"
type: "rationale"
community: "Auth & Error Handling"
location: "L97"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Auth_&_Error_Handling
---

# Upsert one preference row. Raises ValidationError for unknown codes.     Critica

## Connections
- [[upsert_preference()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Auth_&_Error_Handling