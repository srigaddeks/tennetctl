---
source_file: "backend/02_features/03_iam/sub_features/10_auth/service.py"
type: "rationale"
community: "Service & Repository Layer"
location: "L387"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Service_&_Repository_Layer
---

# Exchange code -> upsert user (google_oauth/github_oauth account_type) -> mint se

## Connections
- [[oauth_signin()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Service_&_Repository_Layer