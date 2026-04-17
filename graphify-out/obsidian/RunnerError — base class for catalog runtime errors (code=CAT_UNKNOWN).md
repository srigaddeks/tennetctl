---
source_file: "backend/01_catalog/errors.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# RunnerError — base class for catalog runtime errors (code=CAT_UNKNOWN)

## Connections
- [[DomainError — CAT_DOMAIN, non-retryable domain failure]] - `implements` [EXTRACTED]
- [[NodeAuthDenied — CAT_AUTH_DENIED error]] - `implements` [EXTRACTED]
- [[NodeNotFound — CAT_NODE_NOT_FOUND error]] - `implements` [EXTRACTED]
- [[NodeTombstoned — CAT_NODE_TOMBSTONED error]] - `implements` [EXTRACTED]
- [[TransientError — CAT_TRANSIENT, only class that triggers runner retries]] - `implements` [EXTRACTED]
- [[backend.01_catalog.errors — Runner error hierarchy]] - `implements` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization