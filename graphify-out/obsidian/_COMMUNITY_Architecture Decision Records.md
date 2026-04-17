---
type: community
cohesion: 0.02
members: 128
---

# Architecture Decision Records

**Cohesion:** 0.02 - loosely connected
**Members:** 128 nodes

## Members
- [[ADR-002 NATS JetStream for Monitoring Ingestion]] - document - 03_docs/00_main/08_decisions/002_nats_for_streams.md
- [[ADR-003 Raw SQL with asyncpg — No ORM]] - document - 03_docs/00_main/08_decisions/003_raw_sql_no_orm.md
- [[ADR-005 ClickHouse as Optional Later Addition for High-Volume Analytics]] - document - 03_docs/00_main/08_decisions/005_clickhouse_later.md
- [[ADR-006 Database Schema Structure and Naming Conventions]] - document - 03_docs/00_main/08_decisions/006_database_conventions.md
- [[ADR-009b Change License from MIT to AGPL-3.0]] - document - 03_docs/00_main/08_decisions/009b_license_agpl3.md
- [[ADR-010 Alerting Engine Separated from Notification Delivery]] - document - 03_docs/00_main/08_decisions/010_alerting_notify_separation.md
- [[ADR-011 Monitoring Frontend Architecture]] - document - 03_docs/00_main/08_decisions/011_monitoring_ui_architecture.md
- [[ADR-015 Feature Module Gating — Single Container, Selective Activation]] - document - 03_docs/00_main/08_decisions/015_feature_gating.md
- [[ADR-017 Flow Execution Model]] - document - 03_docs/00_main/08_decisions/017_flow_execution_model.md
- [[ADR-018 Node Contract Model]] - document - 03_docs/00_main/08_decisions/018_node_contract_model.md
- [[ADR-019 Feature and Node Ownership]] - document - 03_docs/00_main/08_decisions/019_feature_node_ownership.md
- [[ADR-021 Gateway Compilation Boundary]] - document - 03_docs/00_main/08_decisions/021_gateway_compilation_boundary.md
- [[ADR-022 API Enhancement Model]] - document - 03_docs/00_main/08_decisions/022_api_enhancement_model.md
- [[ADR-023 React Flow (XY Flow) as the Visual Canvas Library]] - document - 03_docs/00_main/08_decisions/023_canvas_library.md
- [[ADR-024 MCP Integration Model — Generic Graph Tools]] - document - 03_docs/00_main/08_decisions/024_mcp_integration_model.md
- [[ADR-025 Multi-Tenant by Default, Single-Tenant via TENNETCTL_SINGLE_TENANT]] - document - 03_docs/00_main/08_decisions/025_multi_tenant_model.md
- [[ADR-026 Minimum Surface Principle — APIs and Nodes]] - document - 03_docs/00_main/08_decisions/026_minimum_surface_principle.md
- [[ADR-027 Node Catalog and Runner]] - document - 03_docs/00_main/08_decisions/027_node_catalog_and_runner.md
- [[ADR-028 vault envelope encryption rationale]] - document - 03_docs/00_main/08_decisions/028_vault_encryption.md
- [[ADR-029 Monitoring Query DSL]] - document - 03_docs/00_main/08_decisions/029_monitoring_query_dsl.md
- [[AES-256-GCM Envelope Encryption (DEK + root key)]] - concept - 03_docs/00_main/08_decisions/028_vault_foundation.md
- [[AGPL-3.0 License]] - concept - 03_docs/00_main/08_decisions/009b_license_agpl3.md
- [[API Key scopes (notifysend, notifyread, auditread)]] - code - frontend/src/app/(dashboard)/account/api-keys/page.tsx
- [[API Presets (public_api  internal_api  admin_api)]] - concept - 03_docs/00_main/08_decisions/022_api_enhancement_model.md
- [[APIs as Code-First, tennetctl as Enhancement Layer]] - concept - 03_docs/00_main/08_decisions/022_api_enhancement_model.md
- [[Account API Keys Page]] - code - frontend/src/app/(dashboard)/account/api-keys/page.tsx
- [[Account Security Page (TOTP + Passkeys)]] - code - frontend/src/app/(dashboard)/account/security/page.tsx
- [[AccountType string literal union (email_password, magic_link, google_oauth, github_oauth)]] - code - frontend/src/app/(dashboard)/iam/users/page.tsx
- [[Alert Notification Outbox (evt_alert_notifications)]] - concept - 03_docs/00_main/08_decisions/010_alerting_notify_separation.md
- [[Alert Silence (mutes notifications for matcher + time window)]] - code - frontend/src/app/(dashboard)/monitoring/alerts/silences/page.tsx
- [[Alert rule DSL condition (op, threshold, for_duration_seconds)]] - code - frontend/src/app/(dashboard)/monitoring/alerts/rules/page.tsx
- [[Alert rule pause (paused_until timestamp, not a boolean flag)]] - code - frontend/src/app/(dashboard)/monitoring/alerts/rules/page.tsx
- [[AlertList component]] - code - frontend/src/features/monitoring/_components/alert-list.tsx
- [[Apache APISIX as Gateway Execution Target]] - concept - 03_docs/00_main/08_decisions/021_gateway_compilation_boundary.md
- [[Audit Explorer Page]] - code - frontend/src/app/(dashboard)/audit/page.tsx
- [[Audit Live Tail (polling outbox cursor every 3s)]] - code - frontend/src/app/(dashboard)/audit/page.tsx
- [[ClickHouse (Optional Analytics Backend)]] - concept - 03_docs/00_main/08_decisions/005_clickhouse_later.md
- [[CreateFlagDialog — flag creation dialog]] - code - frontend/src/app/(dashboard)/feature-flags/page.tsx
- [[CreateOrgDialog component]] - code - frontend/src/features/iam-orgs/create-org-dialog.tsx
- [[DB ReadWrite Split — views for reads, tables for writes]] - concept - 03_docs/00_main/08_decisions/006_database_conventions.md
- [[Dashboard Panel with DSL-backed visualization types]] - code - frontend/src/app/(dashboard)/monitoring/dashboards/[id]/page.tsx
- [[DashboardGrid component]] - code - frontend/src/features/monitoring/_components/dashboard-grid.tsx
- [[EvaluatePage — flag evaluation sandbox]] - code - frontend/src/app/(dashboard)/feature-flags/evaluate/page.tsx
- [[EvaluateRequest — flag evaluation input]] - code - frontend/src/types/api.ts
- [[EvaluateResponse — flag resolution result + trace]] - code - frontend/src/types/api.ts
- [[Event-Driven Notify Subscription (audit event → fan-out)]] - concept - 03_docs/00_main/09_guides/notify-examples/order-confirmation.md
- [[EventDetailDrawer component (audit)]] - code - frontend/src/features/audit-analytics/_components/event-detail-drawer.tsx
- [[EventsTable component (audit)]] - code - frontend/src/features/audit-analytics/_components/events-table.tsx
- [[FilterBar component (audit)]] - code - frontend/src/features/audit-analytics/_components/filter-bar.tsx
- [[Flag — feature flag type]] - code - frontend/src/types/api.ts
- [[FlagDetailPage — flag detail with environmentsrulesoverridespermissions tabs]] - code - frontend/src/app/(dashboard)/feature-flags/[flagId]/page.tsx
- [[FlagEnvironmentsPanel — per-env toggle management]] - code - frontend/src/app/(dashboard)/feature-flags/[flagId]/page.tsx
- [[FlagOverridesPanel — per-entity override management]] - code - frontend/src/app/(dashboard)/feature-flags/[flagId]/page.tsx
- [[FlagPermissionsPanel — role-based flag permissions]] - code - frontend/src/app/(dashboard)/feature-flags/[flagId]/page.tsx
- [[FlagRulesPanel — targeting rules management]] - code - frontend/src/app/(dashboard)/feature-flags/[flagId]/page.tsx
- [[FlagsListPage — feature flags list with scope filter]] - code - frontend/src/app/(dashboard)/feature-flags/page.tsx
- [[Flow Edge Types (nextsuccessfailuretruefalse)]] - concept - 03_docs/00_main/08_decisions/017_flow_execution_model.md
- [[Flow as DAG of Typed Node Invocations]] - concept - 03_docs/00_main/08_decisions/017_flow_execution_model.md
- [[FunnelBuilder component (audit analytics)]] - code - frontend/src/features/audit-analytics/_components/funnel-builder.tsx
- [[Gateway vs Backend Runtime Compilation Boundary]] - concept - 03_docs/00_main/08_decisions/021_gateway_compilation_boundary.md
- [[Guide Order Confirmation — Event-Driven Subscription Example]] - document - 03_docs/00_main/09_guides/notify-examples/order-confirmation.md
- [[IAM Memberships Page]] - code - frontend/src/app/(dashboard)/iam/memberships/page.tsx
- [[IAM Orgs Page]] - code - frontend/src/app/(dashboard)/iam/orgs/page.tsx
- [[IAM Users Page]] - code - frontend/src/app/(dashboard)/iam/users/page.tsx
- [[IAM Workspaces Page]] - code - frontend/src/app/(dashboard)/iam/workspaces/page.tsx
- [[MCP 5 Generic Graph Tools (inspectsearchscaffoldvalidaterun)]] - concept - 03_docs/00_main/08_decisions/024_mcp_integration_model.md
- [[MetricPicker component]] - code - frontend/src/features/monitoring/_components/metric-picker.tsx
- [[MetricStore  EventStore Abstract Interface]] - concept - 03_docs/00_main/08_decisions/005_clickhouse_later.md
- [[MetricsChart component]] - code - frontend/src/features/monitoring/_components/metrics-chart.tsx
- [[Minimum Surface Principle — fewer APIsnodes, max configurability]] - concept - 03_docs/00_main/08_decisions/026_minimum_surface_principle.md
- [[Module Gating via TENNETCTL_MODULES]] - concept - 03_docs/00_main/08_decisions/015_feature_gating.md
- [[Monitoring Alert Detail Page]] - code - frontend/src/app/(dashboard)/monitoring/alerts/[id]/page.tsx
- [[Monitoring Alert Rules Page]] - code - frontend/src/app/(dashboard)/monitoring/alerts/rules/page.tsx
- [[Monitoring Alerts Page]] - code - frontend/src/app/(dashboard)/monitoring/alerts/page.tsx
- [[Monitoring Dashboard Detail Page]] - code - frontend/src/app/(dashboard)/monitoring/dashboards/[id]/page.tsx
- [[Monitoring Dashboards Page]] - code - frontend/src/app/(dashboard)/monitoring/dashboards/page.tsx
- [[Monitoring Metrics Page]] - code - frontend/src/app/(dashboard)/monitoring/metrics/page.tsx
- [[Monitoring Overview Page]] - code - frontend/src/app/(dashboard)/monitoring/page.tsx
- [[Monitoring Query DSL (logsmetricstraces target union)]] - code - frontend/src/app/(dashboard)/monitoring/page.tsx
- [[Monitoring Silences Page]] - code - frontend/src/app/(dashboard)/monitoring/alerts/silences/page.tsx
- [[Monitoring Trace Detail Page]] - code - frontend/src/app/(dashboard)/monitoring/traces/[traceId]/page.tsx
- [[Monitoring Traces Page]] - code - frontend/src/app/(dashboard)/monitoring/traces/page.tsx
- [[Multi-Tenant by Default, Single-Tenant via Flag]] - concept - 03_docs/00_main/08_decisions/025_multi_tenant_model.md
- [[NATS JetStream]] - concept - 03_docs/00_main/08_decisions/002_nats_for_streams.md
- [[Node Catalog Protocol v1 (NCP v1)]] - concept - 03_docs/00_main/08_decisions/027_node_catalog_and_runner.md
- [[Node Contract (key, kind, schemas, handler_ref)]] - concept - 03_docs/00_main/08_decisions/018_node_contract_model.md
- [[Node Kinds request  effect  control]] - concept - 03_docs/00_main/08_decisions/018_node_contract_model.md
- [[Node Ownership Rule — narrowest valid boundary, 3-feature promotion threshold]] - concept - 03_docs/00_main/08_decisions/019_feature_node_ownership.md
- [[NodeContext (user_id  session_id  org_id  workspace_id  trace_id)]] - concept - 03_docs/00_main/08_decisions/027_node_catalog_and_runner.md
- [[Notify Fallback Chain (in-app → email escalation)]] - concept - 03_docs/00_main/09_guides/notify-examples/order-confirmation.md
- [[OrgDetailDrawer component]] - code - frontend/src/features/iam-orgs/org-detail-drawer.tsx
- [[Postgres Transactional Outbox Pattern]] - concept - 03_docs/00_main/08_decisions/002_nats_for_streams.md
- [[React Flow  XY Flow Canvas Library]] - concept - 03_docs/00_main/08_decisions/023_canvas_library.md
- [[Repository Pattern]] - concept - 03_docs/00_main/08_decisions/003_raw_sql_no_orm.md
- [[RetentionGrid component (audit analytics)]] - code - frontend/src/features/audit-analytics/_components/retention-grid.tsx
- [[Role — IAM role type]] - code - frontend/src/types/api.ts
- [[RolesPage — IAM roles list with zodreact-hook-form]] - code - frontend/src/app/(dashboard)/iam/roles/page.tsx
- [[SavedViewsPanel component (audit analytics)]] - code - frontend/src/features/audit-analytics/_components/saved-views-panel.tsx
- [[Shared API types (api.ts)]] - code - frontend/src/types/api.ts
- [[SilenceDialog component]] - code - frontend/src/features/monitoring/_components/silence-dialog.tsx
- [[Soft Delete via deleted_at TIMESTAMP]] - concept - 03_docs/00_main/08_decisions/006_database_conventions.md
- [[StatsPanel component (audit)]] - code - frontend/src/features/audit-analytics/_components/stats-panel.tsx
- [[TanStack Query (React Query)]] - concept - 03_docs/00_main/08_decisions/011_monitoring_ui_architecture.md
- [[TimerangePicker component]] - code - frontend/src/features/monitoring/_components/timerange-picker.tsx
- [[TraceWaterfall component]] - code - frontend/src/features/monitoring/_components/trace-waterfall.tsx
- [[User emaildisplay_nameavatar stored as EAV attrs (not fct_ columns)]] - code - frontend/src/app/(dashboard)/iam/users/page.tsx
- [[VaultClient In-Process SWR Cache (60s)]] - concept - 03_docs/00_main/08_decisions/028_vault_foundation.md
- [[WebAuthn Passkey enrollment (browser navigator.credentials API)]] - code - frontend/src/app/(dashboard)/account/security/page.tsx
- [[asyncpg (Python Postgres Driver)]] - concept - 03_docs/00_main/08_decisions/003_raw_sql_no_orm.md
- [[feature.manifest.yaml — source of truth per feature]] - concept - 03_docs/00_main/08_decisions/027_node_catalog_and_runner.md
- [[lnk membership rows are immutable — revoke = delete]] - code - frontend/src/app/(dashboard)/iam/memberships/page.tsx
- [[run_node() — sole sanctioned cross-sub-feature call mechanism]] - concept - 03_docs/00_main/08_decisions/027_node_catalog_and_runner.md
- [[use-evaluate hook — flag evaluation mutation]] - code - frontend/src/app/(dashboard)/feature-flags/evaluate/page.tsx
- [[use-flags hooks — feature flag CRUD]] - code - frontend/src/app/(dashboard)/feature-flags/page.tsx
- [[use-orgs hook — org list]] - code - frontend/src/app/(dashboard)/feature-flags/page.tsx
- [[use-roles hooks — role CRUD]] - code - frontend/src/app/(dashboard)/iam/roles/page.tsx
- [[useAlertEvent  useSilences  useCreateSilence  useDeleteSilence hooks]] - code - frontend/src/features/monitoring/hooks/use-alerts.ts
- [[useAlertRules  useDeleteAlertRule  usePauseAlertRule  useUnpauseAlertRule hooks]] - code - frontend/src/features/monitoring/hooks/use-alert-rules.ts
- [[useApiKeys  useCreateApiKey  useRevokeApiKey hooks]] - code - frontend/src/features/auth/hooks/use-api-keys.ts
- [[useAuditEvents  useAuditEventStats  useAuditTailPoll  useLoadMore  useOutboxCursor hooks]] - code - frontend/src/features/audit-analytics/hooks/use-audit-events.ts
- [[useAuth hooks (TOTP + Passkey registrationmanagement)]] - code - frontend/src/features/auth/hooks/use-auth.ts
- [[useDashboards  useDashboard  useCreateDashboard  useDeleteDashboard  useCreatePanel  useUpdatePanel hooks]] - code - frontend/src/features/monitoring/hooks/use-dashboards.ts
- [[useLogsQuery hook]] - code - frontend/src/features/monitoring/hooks/use-logs-query.ts
- [[useMemberships hooks (org + workspace CRUD)]] - code - frontend/src/features/iam-memberships/hooks/use-memberships.ts
- [[useMetricsQuery hook]] - code - frontend/src/features/monitoring/hooks/use-metrics-query.ts
- [[useTracesQuery  useTraceDetail hooks]] - code - frontend/src/features/monitoring/hooks/use-traces-query.ts
- [[useUsers  useUser  useCreateUser  useUpdateUser  useDeleteUser hooks]] - code - frontend/src/features/iam-users/hooks/use-users.ts
- [[useWorkspaces  useWorkspace  useCreateWorkspace  useUpdateWorkspace  useDeleteWorkspace hooks]] - code - frontend/src/features/iam-workspaces/hooks/use-workspaces.ts

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Architecture_Decision_Records
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_API Keys Sub-feature]]
- 1 edge to [[_COMMUNITY_Error Types & Authorization]]

## Top bridge nodes
- [[ADR-028 vault envelope encryption rationale]] - degree 8, connects to 2 communities
- [[ADR-006 Database Schema Structure and Naming Conventions]] - degree 5, connects to 1 community