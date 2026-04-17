---
type: community
cohesion: 0.29
members: 7
---

# Vault Config UI Concepts

**Cohesion:** 0.29 - loosely connected
**Members:** 7 nodes

## Members
- [[Config scope hierarchy (global  org  workspace)]] - code - frontend/src/app/(dashboard)/vault/configs/page.tsx
- [[ConfigRowActions component]] - code - frontend/src/features/vault/configs/_components/config-row-actions.tsx
- [[CreateConfigDialog component]] - code - frontend/src/features/vault/configs/_components/create-config-dialog.tsx
- [[Vault Configs Page]] - code - frontend/src/app/(dashboard)/vault/configs/page.tsx
- [[Vault Index Page (redirects to vaultsecrets)]] - code - frontend/src/app/(dashboard)/vault/page.tsx
- [[stringifyValue utility (vault configs schema)]] - code - frontend/src/features/vault/configs/schema.ts
- [[useConfigs hook]] - code - frontend/src/features/vault/configs/hooks/use-configs.ts

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Vault_Config_UI_Concepts
SORT file.name ASC
```
