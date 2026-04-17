---
type: community
cohesion: 0.02
members: 139
---

# Audit Emit Pipeline

**Cohesion:** 0.02 - loosely connected
**Members:** 139 nodes

## Members
- [[.__init__()_1]] - code - backend/01_catalog/errors.py
- [[.__init__()]] - code - backend/01_catalog/manifest.py
- [[.__str__()_1]] - code - backend/01_catalog/errors.py
- [[.__str__()]] - code - backend/01_catalog/manifest.py
- [[.run()_64]] - code - backend/02_features/04_audit/sub_features/01_events/nodes/audit_emit.py
- [[.run()_60]] - code - backend/02_features/02_vault/sub_features/02_configs/nodes/vault_configs_create.py
- [[Application error hierarchy.  All application errors extend AppError. Each subcl]] - rationale - backend/01_core/errors.py
- [[Base application error.]] - rationale - backend/01_core/errors.py
- [[Base class for catalog errors. Every subclass carries a stable error code.]] - rationale - backend/01_catalog/manifest.py
- [[Boot loader — executes NCP v1 §11 sequence   discover → parse → filter by TENNE]] - rationale - backend/01_catalog/loader.py
- [[CatalogError]] - code - backend/01_catalog/manifest.py
- [[Coerce + validate handler output against Output class. Returns dict.]] - rationale - backend/01_catalog/runner.py
- [[ConfigCreate]] - code - backend/02_features/02_vault/sub_features/02_configs/schemas.py
- [[ConfigUpdate]] - code - backend/02_features/02_vault/sub_features/02_configs/schemas.py
- [[DomainError]] - code - backend/01_catalog/errors.py
- [[EmitAudit]] - code - backend/02_features/04_audit/sub_features/01_events/nodes/audit_emit.py
- [[Enforce declared type. JSON accepts anything; number accepts int or float.]] - rationale - backend/02_features/02_vault/sub_features/02_configs/schemas.py
- [[ExecutionPolicy]] - code - backend/01_catalog/manifest.py
- [[FeatureManifest]] - code - backend/01_catalog/manifest.py
- [[FeatureMetadata]] - code - backend/01_catalog/manifest.py
- [[FeatureSpec]] - code - backend/01_catalog/manifest.py
- [[Fetch node metadata joined with kind + tx mode codes. Returns dict or None.]] - rationale - backend/01_catalog/runner.py
- [[Find every feature.manifest.yaml under     - {root}backend02_featuresfeatu]] - rationale - backend/01_catalog/manifest.py
- [[For any row in `table` whose key is NOT in keys_present AND deprecated_at IS NUL]] - rationale - backend/01_catalog/repository.py
- [[Handler class must expose `key` and `kind` attributes matching the manifest.]] - rationale - backend/01_catalog/loader.py
- [[HandlerContractMismatch]] - code - backend/01_catalog/manifest.py
- [[HandlerUnresolved]] - code - backend/01_catalog/manifest.py
- [[IdempotencyRequired]] - code - backend/01_catalog/errors.py
- [[Import the module containing the handler and return the handler class (or raise)]] - rationale - backend/01_catalog/loader.py
- [[IncrementResponse]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/schemas.py
- [[Input_61]] - code - backend/02_features/04_audit/sub_features/01_events/nodes/audit_emit.py
- [[Input_57]] - code - backend/02_features/02_vault/sub_features/02_configs/nodes/vault_configs_create.py
- [[Kahn's algorithm over depends_on_modules. Cycle → CatalogError.]] - rationale - backend/01_catalog/loader.py
- [[KeyConflict]] - code - backend/01_catalog/manifest.py
- [[Load + validate a single feature.manifest.yaml file.]] - rationale - backend/01_catalog/manifest.py
- [[LoaderReport]] - code - backend/01_catalog/loader.py
- [[Manifest parser + Pydantic models — the NCP v1 §3 grammar.  Pydantic models ARE]] - rationale - backend/01_catalog/manifest.py
- [[ManifestInvalid]] - code - backend/01_catalog/manifest.py
- [[Map a node's handler path (relative inside the feature) to a fully qualified Pyt]] - rationale - backend/01_catalog/loader.py
- [[MetricResponse]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/schemas.py
- [[NodeAuthDenied]] - code - backend/01_catalog/errors.py
- [[NodeManifest]] - code - backend/01_catalog/manifest.py
- [[NodeNotFound]] - code - backend/01_catalog/errors.py
- [[NodeTimeout]] - code - backend/01_catalog/errors.py
- [[NodeTombstoned]] - code - backend/01_catalog/errors.py
- [[Non-retryable domain failure. Runner never retries this class.]] - rationale - backend/01_catalog/errors.py
- [[OTel resource identity — interned in fct_monitoring_resources.]] - rationale - backend/02_features/05_monitoring/sub_features/02_metrics/schemas.py
- [[Output_61]] - code - backend/02_features/04_audit/sub_features/01_events/nodes/audit_emit.py
- [[Output_57]] - code - backend/02_features/02_vault/sub_features/02_configs/nodes/vault_configs_create.py
- [[OwnsBlock]] - code - backend/01_catalog/manifest.py
- [[PATCH body. Only `value` + `description` + `is_active` are mutable.     `value_t]] - rationale - backend/02_features/02_vault/sub_features/02_configs/schemas.py
- [[ParentMissing]] - code - backend/01_catalog/manifest.py
- [[Per-node execution policy (NCP v1 §8).]] - rationale - backend/01_catalog/manifest.py
- [[Raises ValueError if sql_template fails safelist checks (save-time validation).]] - rationale - backend/02_features/06_notify/sub_features/03_templates/nodes/safelist.py
- [[ResourceIdentity]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/schemas.py
- [[Retryable failure. Subclass in user code for domain-specific transients.]] - rationale - backend/01_catalog/errors.py
- [[Return True iff the exception is retryable per NCP §8.]] - rationale - backend/01_catalog/runner.py
- [[Route entry — kept loose for v1 (not upserted into catalog this plan).]] - rationale - backend/01_catalog/manifest.py
- [[RouteManifest]] - code - backend/01_catalog/manifest.py
- [[Run one attempt of the handler under a timeout. Raises NodeTimeout on expiry.]] - rationale - backend/01_catalog/runner.py
- [[Run the full NCP §11 boot sequence. Strict mode.]] - rationale - backend/01_catalog/loader.py
- [[RunnerError]] - code - backend/01_catalog/errors.py
- [[Single node entry in a sub-feature's `nodes` list.]] - rationale - backend/01_catalog/manifest.py
- [[Sub-feature entry under `spec.sub_features`.]] - rationale - backend/01_catalog/manifest.py
- [[SubFeatureManifest]] - code - backend/01_catalog/manifest.py
- [[SubscriptionCreate]] - code - backend/02_features/06_notify/sub_features/05_subscriptions/schemas.py
- [[SubscriptionUpdate]] - code - backend/02_features/06_notify/sub_features/05_subscriptions/schemas.py
- [[TennetCTL SQL Migrator  Enterprise-grade sequential SQL migration runner using a]] - rationale - backend/01_migrator/runner.py
- [[Top-level feature manifest — whole YAML file.]] - rationale - backend/01_catalog/manifest.py
- [[TransientError]] - code - backend/01_catalog/errors.py
- [[UI page entry — kept loose for v1.]] - rationale - backend/01_catalog/manifest.py
- [[UIPageManifest]] - code - backend/01_catalog/manifest.py
- [[Upsert by key without burning the SMALLINT sequence on conflicts.]] - rationale - backend/01_catalog/repository.py
- [[Upsert by key without burning the SMALLINT sequence on conflicts._1]] - rationale - backend/01_catalog/repository.py
- [[Upsert by key without burning the SMALLINT sequence on conflicts.      Uses SELE]] - rationale - backend/01_catalog/repository.py
- [[Use the loader's shared handler path resolution logic by walking manifests.]] - rationale - backend/01_catalog/runner.py
- [[Validate that `ctx` is allowed to call `node_meta`.      node_meta fields used]] - rationale - backend/01_catalog/authz.py
- [[ValueError]] - code
- [[VaultConfigsCreate]] - code - backend/02_features/02_vault/sub_features/02_configs/nodes/vault_configs_create.py
- [[What a sub-feature owns in terms of DB objects + seeds.]] - rationale - backend/01_catalog/manifest.py
- [[_buckets_match_kind()]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/schemas.py
- [[_effect_must_emit_audit()]] - code - backend/01_catalog/manifest.py
- [[_event_key_shape()]] - code - backend/02_features/04_audit/sub_features/01_events/nodes/audit_emit.py
- [[_handler_import_path()]] - code - backend/01_catalog/loader.py
- [[_invoke_once()]] - code - backend/01_catalog/runner.py
- [[_is_transient()]] - code - backend/01_catalog/runner.py
- [[_key_matches_module_in_v1()]] - code - backend/01_catalog/manifest.py
- [[_key_shape()]] - code - backend/01_catalog/manifest.py
- [[_key_shape()_1]] - code - backend/02_features/02_vault/sub_features/02_configs/schemas.py
- [[_label_keys_unique_nonempty()]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/schemas.py
- [[_load_dim()]] - code - backend/01_catalog/repository.py
- [[_lookup_node()]] - code - backend/01_catalog/runner.py
- [[_node_keys_belong_to_this_sub_feature()]] - code - backend/01_catalog/manifest.py
- [[_project_root()_1]] - code - backend/01_catalog/loader.py
- [[_resolve_handler()_1]] - code - backend/01_catalog/loader.py
- [[_resolve_handler()]] - code - backend/01_catalog/runner.py
- [[_scope_shape()]] - code - backend/02_features/02_vault/sub_features/02_configs/nodes/vault_configs_create.py
- [[_shape()]] - code - backend/02_features/02_vault/sub_features/02_configs/schemas.py
- [[_sub_feature_keys_belong_to_feature()]] - code - backend/01_catalog/manifest.py
- [[_topsort()]] - code - backend/01_catalog/loader.py
- [[_unwrap_jsonb()]] - code - backend/02_features/02_vault/sub_features/02_configs/schemas.py
- [[_valid_mode()]] - code - backend/02_features/06_notify/sub_features/05_subscriptions/schemas.py
- [[_validate_dynamic_if_sql()]] - code - backend/02_features/06_notify/sub_features/04_variables/schemas.py
- [[_validate_key()]] - code - backend/02_features/02_vault/sub_features/02_configs/schemas.py
- [[_validate_output()]] - code - backend/01_catalog/runner.py
- [[_validate_scope_shape()]] - code - backend/02_features/02_vault/sub_features/02_configs/schemas.py
- [[_validate_type_fields()]] - code - backend/02_features/06_notify/sub_features/04_variables/schemas.py
- [[_validate_value_matches_type()]] - code - backend/02_features/02_vault/sub_features/02_configs/schemas.py
- [[_verify_contract()]] - code - backend/01_catalog/loader.py
- [[audit.emit — the canonical audit emitter.  Every effect node in the platform cal]] - rationale - backend/02_features/04_audit/sub_features/01_events/nodes/audit_emit.py
- [[audit_emit.py]] - code - backend/02_features/04_audit/sub_features/01_events/nodes/audit_emit.py
- [[check_call()]] - code - backend/01_catalog/authz.py
- [[discover_manifests()]] - code - backend/01_catalog/manifest.py
- [[errors.py]] - code - backend/01_catalog/errors.py
- [[get_module_id()]] - code - backend/01_catalog/repository.py
- [[get_node_kind_id()]] - code - backend/01_catalog/repository.py
- [[get_tx_mode_id()]] - code - backend/01_catalog/repository.py
- [[id_to_kind()]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/schemas.py
- [[kind_to_id()]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/schemas.py
- [[loader.py]] - code - backend/01_catalog/loader.py
- [[manifest.py]] - code - backend/01_catalog/manifest.py
- [[mark_absent_deprecated()]] - code - backend/01_catalog/repository.py
- [[notify.templates.nodes.safelist — SQL safelist validator for dynamic_sql variabl]] - rationale - backend/02_features/06_notify/sub_features/03_templates/nodes/safelist.py
- [[ok()]] - code - backend/01_catalog/loader.py
- [[parse_manifest()]] - code - backend/01_catalog/manifest.py
- [[repository.py]] - code - backend/01_catalog/repository.py
- [[runner.py]] - code - backend/01_catalog/runner.py
- [[safelist.py]] - code - backend/02_features/06_notify/sub_features/03_templates/nodes/safelist.py
- [[schemas.py_36]] - code - backend/02_features/02_vault/sub_features/02_configs/schemas.py
- [[schemas.py_24]] - code - backend/02_features/05_monitoring/sub_features/02_metrics/schemas.py
- [[schemas.py_9]] - code - backend/02_features/06_notify/sub_features/05_subscriptions/schemas.py
- [[upsert_all()]] - code - backend/01_catalog/loader.py
- [[upsert_feature()]] - code - backend/01_catalog/repository.py
- [[upsert_node()]] - code - backend/01_catalog/repository.py
- [[upsert_sub_feature()]] - code - backend/01_catalog/repository.py
- [[validate_dynamic_sql()]] - code - backend/02_features/06_notify/sub_features/03_templates/nodes/safelist.py
- [[validate_pattern()]] - code - backend/02_features/06_notify/sub_features/05_subscriptions/schemas.py
- [[vault.configs.create — effect node. Create a plaintext typed config value.]] - rationale - backend/02_features/02_vault/sub_features/02_configs/nodes/vault_configs_create.py
- [[vault_configs_create.py]] - code - backend/02_features/02_vault/sub_features/02_configs/nodes/vault_configs_create.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Audit_Emit_Pipeline
SORT file.name ASC
```

## Connections to other communities
- 36 edges to [[_COMMUNITY_Node Catalog & Feature Implementations]]
- 16 edges to [[_COMMUNITY_Service & Repository Layer]]
- 9 edges to [[_COMMUNITY_Core Infrastructure]]
- 8 edges to [[_COMMUNITY_Alert Evaluator Worker]]
- 5 edges to [[_COMMUNITY_Monitoring Query DSL]]
- 5 edges to [[_COMMUNITY_Notify Templates & Email Delivery]]
- 4 edges to [[_COMMUNITY_API Routes & Response Handling]]
- 3 edges to [[_COMMUNITY_Auth & Error Handling]]
- 2 edges to [[_COMMUNITY_Audit Events & Saved Views]]
- 1 edge to [[_COMMUNITY_Monitoring Stores & Workers]]
- 1 edge to [[_COMMUNITY_Audit Outbox]]
- 1 edge to [[_COMMUNITY_Frontend API Client]]

## Top bridge nodes
- [[ValueError]] - degree 44, connects to 8 communities
- [[schemas.py_24]] - degree 13, connects to 3 communities
- [[upsert_all()]] - degree 21, connects to 2 communities
- [[schemas.py_36]] - degree 11, connects to 2 communities
- [[repository.py]] - degree 10, connects to 2 communities