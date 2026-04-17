---
source_file: "backend/02_features/02_vault/sub_features/02_configs/service.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# vault.configs service (create/list/get/update/delete config)

## Connections
- [[backend.01_catalog.run_node (cross-sub-feature node dispatch)]] - `calls` [EXTRACTED]
- [[node audit.events.emit (effect node — canonical audit writer to 60_evt_audit)]] - `calls` [EXTRACTED]
- [[node vault.configs.create (effect node — create plaintext typed config)]] - `calls` [EXTRACTED]
- [[node vault.configs.delete (effect node — soft-delete config by id)]] - `calls` [EXTRACTED]
- [[node vault.configs.get (control node — cross-sub-feature config lookup)]] - `calls` [EXTRACTED]
- [[node vault.configs.update (effect node — PATCH valuedescriptionis_active)]] - `calls` [EXTRACTED]
- [[vault.configs FastAPI routes (v1vault-configs, 5 endpoints)]] - `calls` [EXTRACTED]
- [[vault.configs Pydantic schemas (ConfigCreate, ConfigUpdate, ConfigMeta)]] - `references` [EXTRACTED]
- [[vault.configs asyncpg repository (reads v_vault_configs, writes fct_vault_configs)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation