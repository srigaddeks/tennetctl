---
type: community
cohesion: 0.47
members: 6
---

# WebAuthn Passkeys

**Cohesion:** 0.47 - moderately connected
**Members:** 6 nodes

## Members
- [[Concept WebAuthn passkey registerauth flow (challenge-response, sign_count replay protection)]] - document - backend/02_features/03_iam/sub_features/13_passkeys/
- [[DB table 03_iam.25_fct_iam_passkey_challenges]] - code - backend/02_features/03_iam/sub_features/13_passkeys/repository.py
- [[DB table 03_iam.26_fct_iam_passkey_credentials]] - code - backend/02_features/03_iam/sub_features/13_passkeys/repository.py
- [[iam.passkeys repository (challenges + credentials)]] - code - backend/02_features/03_iam/sub_features/13_passkeys/repository.py
- [[iam.passkeys routes (v1authpasskeys)]] - code - backend/02_features/03_iam/sub_features/13_passkeys/routes.py
- [[iam.passkeys schemas (WebAuthn)]] - code - backend/02_features/03_iam/sub_features/13_passkeys/schemas.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/WebAuthn_Passkeys
SORT file.name ASC
```
