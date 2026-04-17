---
source_file: "backend/02_features/03_iam/sub_features/15_api_keys/repository.py"
type: "code"
community: "API Keys Sub-feature"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/API_Keys_Sub-feature
---

# iam.api_keys repository (v_iam_api_keys view + fct)

## Connections
- [[DB table 03_iam.28_fct_iam_api_keys]] - `references` [EXTRACTED]
- [[DB view 03_iam.v_iam_api_keys]] - `references` [EXTRACTED]
- [[iam.api_keys service (mintrevokevalidate machine tokens)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/API_Keys_Sub-feature