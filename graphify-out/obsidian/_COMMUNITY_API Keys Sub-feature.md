---
type: community
cohesion: 0.03
members: 82
---

# API Keys Sub-feature

**Cohesion:** 0.03 - loosely connected
**Members:** 82 nodes

## Members
- [[5-file sub-feature structure (__init__, schemas, repository, service, routes)]] - document - 02_contributing_guidelines/05_backend_api_standards.md
- [[API key token format nk_key_id.secret (argon2id-hashed)]] - code - backend/02_features/03_iam/sub_features/15_api_keys/service.py
- [[AlertEvaluatorWorker_1]] - code - backend/02_features/05_monitoring/workers/alert_evaluator_worker.py
- [[Backend API Standards (5-file module, response envelope, URL conventions, audit events)]] - document - 02_contributing_guidelines/05_backend_api_standards.md
- [[CLAUDE.md — TennetCTL project guide (architecture, tech stack, rules, ADRs)]] - document - CLAUDE.md
- [[Concept API key Bearer authentication (nk_ prefix, argon2id, session-only mint)]] - document - backend/02_features/03_iam/sub_features/15_api_keys/service.py
- [[Concept EAV attribute pattern (dtl_attrs + dtl_attr_defs per entity_type)]] - document - backend/02_features/03_iam/
- [[Concept Org - Workspace - Application tenancy hierarchy]] - document - backend/02_features/03_iam/
- [[CounterHandle_1]] - code - backend/02_features/05_monitoring/sdk/metrics.py
- [[DB table 03_iam.03_dim_scopes]] - code - backend/02_features/03_iam/sub_features/06_applications/repository.py
- [[DB table 03_iam.10_fct_orgs]] - code - backend/02_features/03_iam/sub_features/01_orgs/repository.py
- [[DB table 03_iam.11_fct_workspaces]] - code - backend/02_features/03_iam/sub_features/02_workspaces/repository.py
- [[DB table 03_iam.15_fct_applications]] - code - backend/02_features/03_iam/sub_features/06_applications/repository.py
- [[DB table 03_iam.20_dtl_attr_defs (attribute definitions)]] - code - backend/02_features/03_iam/sub_features/01_orgs/repository.py
- [[DB table 03_iam.21_dtl_attrs (EAV attribute store)]] - code - backend/02_features/03_iam/sub_features/01_orgs/repository.py
- [[DB table 03_iam.28_fct_iam_api_keys]] - code - backend/02_features/03_iam/sub_features/15_api_keys/repository.py
- [[DB table 03_iam.45_lnk_application_scopes (many-to-many)]] - code - backend/02_features/03_iam/sub_features/06_applications/repository.py
- [[DB table 10_fct_audit_saved_views]] - code - backend/02_features/04_audit/sub_features/02_saved_views/repository.py
- [[DB table 10_fct_flags]] - code - backend/02_features/09_featureflags/sub_features/01_flags/repository.py
- [[DB table 11_fct_flag_states]] - code - backend/02_features/09_featureflags/sub_features/01_flags/repository.py
- [[DB table 20_dtl_audit_saved_view_details]] - code - backend/02_features/04_audit/sub_features/02_saved_views/repository.py
- [[DB view 03_iam.v_applications]] - code - backend/02_features/03_iam/sub_features/06_applications/repository.py
- [[DB view 03_iam.v_iam_api_keys]] - code - backend/02_features/03_iam/sub_features/15_api_keys/repository.py
- [[DB view 03_iam.v_orgs]] - code - backend/02_features/03_iam/sub_features/01_orgs/repository.py
- [[DB view 03_iam.v_workspaces]] - code - backend/02_features/03_iam/sub_features/02_workspaces/repository.py
- [[DB view v_audit_saved_views]] - code - backend/02_features/04_audit/sub_features/02_saved_views/repository.py
- [[DB view v_flag_states]] - code - backend/02_features/09_featureflags/sub_features/01_flags/repository.py
- [[DB view v_flags]] - code - backend/02_features/09_featureflags/sub_features/01_flags/repository.py
- [[DB view v_monitoring_alert_rules]] - code - backend/02_features/05_monitoring/workers/alert_evaluator_worker.py
- [[Env-var contract secrets belong in vault not env (ADR-028)]] - document - backend/01_core/config.py
- [[FlagCreate schema]] - code - backend/02_features/09_featureflags/sub_features/01_flags/schemas.py
- [[FlagRead schema]] - code - backend/02_features/09_featureflags/sub_features/01_flags/schemas.py
- [[FlagStateRead schema]] - code - backend/02_features/09_featureflags/sub_features/01_flags/schemas.py
- [[GaugeHandle_1]] - code - backend/02_features/05_monitoring/sdk/metrics.py
- [[HistogramHandle_1]] - code - backend/02_features/05_monitoring/sdk/metrics.py
- [[IAM API keys service (validate_token)]] - code - backend/01_core/middleware.py
- [[Module gating (TENNETCTL_MODULES env var controls which features start)]] - document - CLAUDE.md
- [[Node audit.events.emit (audit event sink)]] - code - backend/02_features/04_audit/
- [[Node iam.orgs.create (effect, fct+dtl+audit atomic write)]] - code - backend/02_features/03_iam/sub_features/01_orgs/nodes/iam_orgs_create.py
- [[Node iam.orgs.get (control, read-only tenant scope validation)]] - code - backend/02_features/03_iam/sub_features/01_orgs/nodes/iam_orgs_get.py
- [[Node iam.workspaces.create (effect, validate org + create workspace)]] - code - backend/02_features/03_iam/sub_features/02_workspaces/nodes/iam_workspaces_create.py
- [[Node iam.workspaces.get (control, read-only cross-sub-feature lookup)]] - code - backend/02_features/03_iam/sub_features/02_workspaces/nodes/iam_workspaces_get.py
- [[NodeContract (key, kind, config_schema, input_schema, output_schema, handler)]] - code - backend/01_core/node_registry.py
- [[Response envelope pattern ({ok, data}  {ok, error {code, message}})]] - document - 02_contributing_guidelines/05_backend_api_standards.md
- [[SessionMiddleware dual-auth API key (nk_ prefix) + session token]] - code - backend/01_core/middleware.py
- [[SyntheticRunner_1]] - code - backend/02_features/05_monitoring/workers/synthetic_runner.py
- [[WorkspaceCreate schema (org_id, slug, display_name)]] - code - backend/02_features/03_iam/sub_features/02_workspaces/schemas.py
- [[audit.saved_views repository]] - code - backend/02_features/04_audit/sub_features/02_saved_views/repository.py
- [[audit.saved_views routes]] - code - backend/02_features/04_audit/sub_features/02_saved_views/routes.py
- [[backend.01_catalog.run_node (cross-sub-feature node dispatch)]] - code - backend/01_catalog/__init__.py
- [[backend.01_core.middleware (Bearer token validation)]] - code - backend/01_core/middleware.py
- [[core config (frozen dataclass, env-var contract, ADR-028)]] - code - backend/01_core/config.py
- [[core errors (AppError hierarchy NotFound, Validation, Conflict, Forbidden, Unauthorized)]] - code - backend/01_core/errors.py
- [[core id (uuid7 generator)]] - code - backend/01_core/id.py
- [[core node_registry (in-memory NodeContract registry)]] - code - backend/01_core/node_registry.py
- [[core response (successerrorpaginated envelope helpers)]] - code - backend/01_core/response.py
- [[featureflags feature router]] - code - backend/02_features/09_featureflags/routes.py
- [[featureflags.flags repository]] - code - backend/02_features/09_featureflags/sub_features/01_flags/repository.py
- [[featureflags.flags routes]] - code - backend/02_features/09_featureflags/sub_features/01_flags/routes.py
- [[featureflags.flags schemas]] - code - backend/02_features/09_featureflags/sub_features/01_flags/schemas.py
- [[featureflags.flags service]] - code - backend/02_features/09_featureflags/sub_features/01_flags/service.py
- [[iam.api_keys repository (v_iam_api_keys view + fct)]] - code - backend/02_features/03_iam/sub_features/15_api_keys/repository.py
- [[iam.api_keys routes (v1api-keys)]] - code - backend/02_features/03_iam/sub_features/15_api_keys/routes.py
- [[iam.api_keys schemas]] - code - backend/02_features/03_iam/sub_features/15_api_keys/schemas.py
- [[iam.api_keys service (mintrevokevalidate machine tokens)]] - code - backend/02_features/03_iam/sub_features/15_api_keys/service.py
- [[iam.applications repository (v_applications + lnk_application_scopes)]] - code - backend/02_features/03_iam/sub_features/06_applications/repository.py
- [[iam.applications service (org-scoped, per-org code uniqueness)]] - code - backend/02_features/03_iam/sub_features/06_applications/service.py
- [[iam.credentials service (argon2id hashverify helper)]] - code - backend/02_features/03_iam/sub_features/08_credentials/service.py
- [[iam.orgs repository (v_orgs view + fct)]] - code - backend/02_features/03_iam/sub_features/01_orgs/repository.py
- [[iam.orgs routes (v1orgs)]] - code - backend/02_features/03_iam/sub_features/01_orgs/routes.py
- [[iam.orgs schemas]] - code - backend/02_features/03_iam/sub_features/01_orgs/schemas.py
- [[iam.orgs service (creategetlistupdatedelete)]] - code - backend/02_features/03_iam/sub_features/01_orgs/service.py
- [[iam.workspaces repository (v_workspaces view + fct)]] - code - backend/02_features/03_iam/sub_features/02_workspaces/repository.py
- [[iam.workspaces routes (v1workspaces)]] - code - backend/02_features/03_iam/sub_features/02_workspaces/routes.py
- [[iam.workspaces schemas]] - code - backend/02_features/03_iam/sub_features/02_workspaces/schemas.py
- [[iam.workspaces service (creategetlistupdatedelete)]] - code - backend/02_features/03_iam/sub_features/02_workspaces/service.py
- [[node iam.applications.get]] - code - backend/02_features/09_featureflags/sub_features/01_flags/service.py
- [[node monitoring.metrics.increment]] - code - backend/02_features/05_monitoring/sdk/metrics.py
- [[node monitoring.metrics.observe_histogram]] - code - backend/02_features/05_monitoring/sdk/metrics.py
- [[node monitoring.metrics.register]] - code - backend/02_features/05_monitoring/sdk/metrics.py
- [[node monitoring.metrics.set_gauge]] - code - backend/02_features/05_monitoring/sdk/metrics.py
- [[node notify.send.transactional]] - code - backend/02_features/05_monitoring/workers/alert_evaluator_worker.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/API_Keys_Sub-feature
SORT file.name ASC
```

## Connections to other communities
- 3 edges to [[_COMMUNITY_Alert Rules & Evaluation]]
- 2 edges to [[_COMMUNITY_Architecture Decision Records]]
- 2 edges to [[_COMMUNITY_Observability Instrumentation]]
- 1 edge to [[_COMMUNITY_Error Types & Authorization]]
- 1 edge to [[_COMMUNITY_Documentation & Guides]]

## Top bridge nodes
- [[backend.01_catalog.run_node (cross-sub-feature node dispatch)]] - degree 10, connects to 1 community
- [[Concept EAV attribute pattern (dtl_attrs + dtl_attr_defs per entity_type)]] - degree 7, connects to 1 community
- [[backend.01_core.middleware (Bearer token validation)]] - degree 7, connects to 1 community
- [[AlertEvaluatorWorker_1]] - degree 5, connects to 1 community
- [[SyntheticRunner_1]] - degree 4, connects to 1 community