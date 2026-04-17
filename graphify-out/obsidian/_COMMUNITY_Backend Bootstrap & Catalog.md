---
type: community
cohesion: 0.20
members: 21
---

# Backend Bootstrap & Catalog

**Cohesion:** 0.20 - loosely connected
**Members:** 21 nodes

## Members
- [[01_catalogcli.py — CLI for catalog lint (import checks) + upsert (boot against live DB)]] - code - backend/01_catalog/cli.py
- [[01_catalogcontext.py — NodeContext frozen dataclass; carries usersessiontraceconn through run_node]] - code - backend/01_catalog/context.py
- [[01_catalogloader.py — upsert_all() discover → parse → filter modules → resolve handlers → topsort → upsert → deprecation sweep]] - code - backend/01_catalog/loader.py
- [[01_catalogmanifest.py — Pydantic models for feature.manifest.yaml; parse_manifest + discover_manifests]] - code - backend/01_catalog/manifest.py
- [[01_catalogrunner.py — run_node() dispatcher lookup → authz → resolve handler → validate → tx → retry]] - code - backend/01_catalog/runner.py
- [[ConfigRowActions — Edit + soft-delete row actions for vault config]] - code - frontend/src/features/vault/configs/_components/config-row-actions.tsx
- [[CreateConfigDialog — form dialog for creating a vault config entry]] - code - frontend/src/features/vault/configs/_components/create-config-dialog.tsx
- [[EditConfigDialog — patches value of an existing vault config (keyscopetype immutable)]] - code - frontend/src/features/vault/configs/_components/edit-config-dialog.tsx
- [[Modal — accessible dialog wrapper using native HTML dialog element]] - code - frontend/src/components/modal.tsx
- [[OrgScopedResourcePage — generic CRUD page for org-scoped resources (groups, applications)]] - code - frontend/src/components/org-scoped-resource-page.tsx
- [[PageHeader — reusable page heading with title, description, and action slot]] - code - frontend/src/components/page-header.tsx
- [[Sidebar — sub-feature navigation sidebar driven by active feature config]] - code - frontend/src/components/sidebar.tsx
- [[TopBar — top navigation bar with feature links, user info, notifications, sign-out]] - code - frontend/src/components/topbar.tsx
- [[api.ts — typed API client apiFetch, apiList, buildQuery, ApiClientError; envelope-aware]] - code - frontend/src/lib/api.ts
- [[backendmain.py — FastAPI app entry point; lifespan manages pool, catalog boot, vault, monitoring, notify workers]] - code - backend/main.py
- [[cn.ts — clsx-based className utility]] - code - frontend/src/lib/cn.ts
- [[providers.tsx — root client providers QueryClientProvider + ToastProvider]] - code - frontend/src/lib/providers.tsx
- [[toast.tsx — ToastProvider context + useToast hook for in-app notifications]] - code - frontend/src/components/toast.tsx
- [[ui.tsx — shared UI primitives Button, Input, Select, Textarea, Field, Badge, Table, Skeleton, EmptyState, ErrorState]] - code - frontend/src/components/ui.tsx
- [[use-configs.ts — TanStack Query hooks useConfigs, useCreateConfig, useUpdateConfig, useDeleteConfig]] - code - frontend/src/features/vault/configs/hooks/use-configs.ts
- [[vaultconfigsschema.ts — Zod schemas for config createupdate + parsestringify helpers]] - code - frontend/src/features/vault/configs/schema.ts

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Backend_Bootstrap_&_Catalog
SORT file.name ASC
```
