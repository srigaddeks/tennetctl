---
source_file: "backend/01_core/config.py"
type: "code"
community: "API Keys Sub-feature"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/API_Keys_Sub-feature
---

# core config (frozen dataclass, env-var contract, ADR-028)

## Connections
- [[Env-var contract secrets belong in vault not env (ADR-028)]] - `implements` [EXTRACTED]
- [[Module gating (TENNETCTL_MODULES env var controls which features start)]] - `implements` [EXTRACTED]
- [[NATS JetStream (log publish target)]] - `references` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/API_Keys_Sub-feature