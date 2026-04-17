---
source_file: "backend/02_features/02_vault/crypto.py"
type: "rationale"
community: "Core Infrastructure"
location: "L78"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Core_Infrastructure
---

# Reverse of encrypt. Raises cryptography.exceptions.InvalidTag on any tamper.

## Connections
- [[decrypt()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Core_Infrastructure