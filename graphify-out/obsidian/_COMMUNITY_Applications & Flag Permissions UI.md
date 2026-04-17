---
type: community
cohesion: 0.09
members: 24
---

# Applications & Flag Permissions UI

**Cohesion:** 0.09 - loosely connected
**Members:** 24 nodes

## Members
- [[Application  ApplicationCreateBody  ApplicationUpdateBody (types)]] - code - frontend/src/types/api.ts
- [[CreateFlagDialog]] - code - frontend/src/features/featureflags/create-flag-dialog.tsx
- [[Flag (type)]] - code - frontend/src/types/api.ts
- [[Flag environment (dev  staging  prod  test)]] - document - frontend/src/features/featureflags/flag-environments-panel.tsx
- [[Flag permission hierarchy (view  toggle  write  admin)]] - document - frontend/src/features/featureflags/flag-permissions-panel.tsx
- [[Flag scope (global  org  application)]] - document - frontend/src/features/featureflags/create-flag-dialog.tsx
- [[FlagEnvironmentsPanel]] - code - frontend/src/features/featureflags/flag-environments-panel.tsx
- [[FlagOverride  FlagOverrideCreateBody (types)]] - code - frontend/src/types/api.ts
- [[FlagOverridesPanel]] - code - frontend/src/features/featureflags/flag-overrides-panel.tsx
- [[FlagPermissionsPanel]] - code - frontend/src/features/featureflags/flag-permissions-panel.tsx
- [[FlagRule  FlagRuleCreateBody  FlagRuleUpdateBody (types)]] - code - frontend/src/types/api.ts
- [[FlagRulesPanel]] - code - frontend/src/features/featureflags/flag-rules-panel.tsx
- [[FlagState (type)]] - code - frontend/src/types/api.ts
- [[GETPATCH v1flag-states]] - code - frontend/src/features/featureflags/hooks/use-flags.ts
- [[GETPOSTDELETE v1flag-overrides]] - code - frontend/src/features/featureflags/hooks/use-rules-overrides.ts
- [[GETPOSTDELETE v1flag-permissions]] - code - frontend/src/features/featureflags/hooks/use-permissions.ts
- [[GETPOSTPATCHDELETE v1applications]] - code - frontend/src/features/iam-applications/hooks/use-applications.ts
- [[GETPOSTPATCHDELETE v1flag-rules]] - code - frontend/src/features/featureflags/hooks/use-rules-overrides.ts
- [[GETPOSTPATCHDELETE v1flags]] - code - frontend/src/features/featureflags/hooks/use-flags.ts
- [[RoleFlagPermission  RoleFlagPermissionCreateBody (types)]] - code - frontend/src/types/api.ts
- [[use-applications (hook module)]] - code - frontend/src/features/iam-applications/hooks/use-applications.ts
- [[use-flags (hook module)]] - code - frontend/src/features/featureflags/hooks/use-flags.ts
- [[use-permissions (hook module)]] - code - frontend/src/features/featureflags/hooks/use-permissions.ts
- [[use-rules-overrides (hook module)]] - code - frontend/src/features/featureflags/hooks/use-rules-overrides.ts

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Applications_&_Flag_Permissions_UI
SORT file.name ASC
```
