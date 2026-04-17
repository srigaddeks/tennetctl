---
source_file: "backend/02_features/02_vault/sub_features/02_configs/repository.py"
type: "code"
community: "Alert Rules & Evaluation"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Alert_Rules_&_Evaluation
---

# vault.configs asyncpg repository (reads v_vault_configs, writes fct_vault_configs)

## Connections
- [[DB table 02_vault.11_fct_vault_configs (plaintext typed configs)]] - `references` [EXTRACTED]
- [[DB view 02_vault.v_vault_configs (joins scope + value_type codes, pivots description)]] - `references` [EXTRACTED]
- [[vault.configs Pydantic schemas (ConfigCreate, ConfigUpdate, ConfigMeta)]] - `shares_data_with` [INFERRED]
- [[vault.configs service (createlistgetupdatedelete config)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Alert_Rules_&_Evaluation