---
type: community
cohesion: 0.02
members: 131
---

# Core Infrastructure

**Cohesion:** 0.02 - loosely connected
**Members:** 131 nodes

## Members
- [[.__init__()_20]] - code - backend/02_features/02_vault/client.py
- [[._fetch()]] - code - backend/02_features/02_vault/client.py
- [[.get()]] - code - backend/02_features/02_vault/client.py
- [[.get_with_version()]] - code - backend/02_features/02_vault/client.py
- [[.invalidate()]] - code - backend/02_features/02_vault/client.py
- [[.run()_65]] - code - backend/02_features/04_audit/sub_features/01_events/nodes/query_events.py
- [[AES-256-GCM envelope encryption for vault secrets.  Every secret has its own 32-]] - rationale - backend/02_features/02_vault/crypto.py
- [[App lifespan — create DB pool on startup, close on shutdown.]] - rationale - backend/main.py
- [[Apply a seed file (insert rows into the target table).     Returns the number of]] - rationale - backend/01_migrator/runner.py
- [[Apply a single migration's UP section and move it to 01_migrated.     Returns d]] - rationale - backend/01_migrator/runner.py
- [[Apply all pending migrations discovered under root_dir.      Returns {applied]] - rationale - backend/01_migrator/runner.py
- [[Apply all pending seed files discovered under root_dir.      Seed files already]] - rationale - backend/01_migrator/runner.py
- [[Build error envelope dict.]] - rationale - backend/01_core/response.py
- [[Catalog CLI — lint + upsert commands.  Usage   python -m backend.01_catalog.cli]] - rationale - backend/01_catalog/cli.py
- [[Close the connection pool.]] - rationale - backend/01_core/database.py
- [[Connect to NATS with 3x exponential backoff. Idempotent.]] - rationale - backend/01_core/nats.py
- [[Create and return an asyncpg connection pool with JSONB codec.]] - rationale - backend/01_core/database.py
- [[Create or update all monitoring streams idempotently.]] - rationale - backend/02_features/05_monitoring/bootstrap/jetstream.py
- [[Cross-import linter — enforces NCP v1 §10.  Sub-features cannot import from othe]] - rationale - backend/01_catalog/linter.py
- [[Database pool management — asyncpg only.  Pool lifecycle create on app startup,]] - rationale - backend/01_core/database.py
- [[Drop a key from the cache. Called by rotatedelete service paths.]] - rationale - backend/02_features/02_vault/client.py
- [[Ensure each bootstrap key exists in the vault. Returns the count of secrets]] - rationale - backend/02_features/02_vault/bootstrap.py
- [[Ensure tracking schema and tables exist. Upgrades old schema if needed.]] - rationale - backend/01_migrator/runner.py
- [[Envelope]] - code - backend/02_features/02_vault/crypto.py
- [[Envelope-encrypt TOTP secret using vault root key. Returns (ciphertext_b64, dek_]] - rationale - backend/02_features/03_iam/sub_features/12_otp/service.py
- [[Envelope-encrypt a plaintext string. Fresh DEK + fresh nonce per call.]] - rationale - backend/02_features/02_vault/crypto.py
- [[Flush + drain + close. No-op if not connected.]] - rationale - backend/01_core/nats.py
- [[Get the current OS username for tracking.]] - rationale - backend/01_migrator/runner.py
- [[Health check endpoint.]] - rationale - backend/main.py
- [[If `call` is an `import_module(...)` or equivalent with a string literal arg,]] - rationale - backend/01_catalog/linter.py
- [[Input_62]] - code - backend/02_features/04_audit/sub_features/01_events/nodes/query_events.py
- [[Is this import permitted from `owner` sub-feature]] - rationale - backend/01_catalog/linter.py
- [[JetStream stream bootstrap for monitoring.  Streams - MONITORING_LOGS   — workq]] - rationale - backend/02_features/05_monitoring/bootstrap/jetstream.py
- [[Mount routers only for enabled modules.]] - rationale - backend/main.py
- [[Move a rolled-back migration from 01_migrated back to 02_in_progress.]] - rationale - backend/01_migrator/runner.py
- [[Move an applied migration from 02_in_progress to 01_migrated.]] - rationale - backend/01_migrator/runner.py
- [[NATS  JetStream core client — module-level singletons.  Public surface - conne]] - rationale - backend/01_core/nats.py
- [[Output_62]] - code - backend/02_features/04_audit/sub_features/01_events/nodes/query_events.py
- [[Parse a migration file into UP and DOWN sections.     Returns {up str, down]] - rationale - backend/01_migrator/runner.py
- [[Parse a seed file (YAML or JSON).      Expected shape       schema 03_iam]] - rationale - backend/01_migrator/runner.py
- [[Persisted shape for an encrypted secret — these three go into fct_vault_entries.]] - rationale - backend/02_features/02_vault/crypto.py
- [[QueryAuditEvents]] - code - backend/02_features/04_audit/sub_features/01_events/nodes/query_events.py
- [[Raised when VaultClient.get is called with a key that does not exist.]] - rationale - backend/02_features/02_vault/client.py
- [[Read + validate TENNETCTL_VAULT_ROOT_KEY. Raises RuntimeError if missingmalform]] - rationale - backend/02_features/02_vault/crypto.py
- [[Recursively find all .sql files in 09_sql_migrations01_migrated     directorie]] - rationale - backend/01_migrator/runner.py
- [[Recursively find all .sql files in 09_sql_migrations02_in_progress     directo]] - rationale - backend/01_migrator/runner.py
- [[Recursively find all seed files (.yaml, .json) in     09_sql_migrationsseeds]] - rationale - backend/01_migrator/runner.py
- [[Register type codecs on every new pool connection.]] - rationale - backend/01_core/database.py
- [[Return (feature_dir, sub_dir) if path lives under a sub-feature, else None.]] - rationale - backend/01_catalog/linter.py
- [[Return complete migration history including rollbacks.]] - rationale - backend/01_migrator/runner.py
- [[Return the latest non-deleted plaintext for `key`. Raises VaultSecretNotFound.]] - rationale - backend/02_features/02_vault/client.py
- [[Return violations for a single file.]] - rationale - backend/01_catalog/linter.py
- [[Return {filename info} for all actively applied migrations.]] - rationale - backend/01_migrator/runner.py
- [[Return {filename info} for all applied seeds.]] - rationale - backend/01_migrator/runner.py
- [[Reverse of encrypt. Raises cryptography.exceptions.InvalidTag on any tamper.]] - rationale - backend/02_features/02_vault/crypto.py
- [[Roll back migrations (reads files from 01_migrated, moves them back to     02_i]] - rationale - backend/01_migrator/runner.py
- [[SHA256 hex digest of full file content.]] - rationale - backend/01_migrator/runner.py
- [[Same as get() but also returns the version number.]] - rationale - backend/02_features/02_vault/client.py
- [[Scaffold a new migration file in the appropriate sub-feature directory.      Pat]] - rationale - backend/01_migrator/runner.py
- [[Show full migration history including rollbacks.]] - rationale - backend/01_migrator/runner.py
- [[Show migration status applied (in 01_migrated) vs pending (in 02_in_progress)]] - rationale - backend/01_migrator/runner.py
- [[TennetCTL — FastAPI application entry point.  Start cd tennetctl && .venvbinp]] - rationale - backend/main.py
- [[Vault boot-time bootstrap.  On first start after migrations, ensures the auth su]] - rationale - backend/02_features/02_vault/bootstrap.py
- [[VaultClient]] - code - backend/02_features/02_vault/client.py
- [[VaultClient — app-singleton in-process reader for vault secrets.  Every backend]] - rationale - backend/02_features/02_vault/client.py
- [[VaultSecretNotFound]] - code - backend/02_features/02_vault/client.py
- [[Violation]] - code - backend/01_catalog/linter.py
- [[Walk `root` and return all violations across .py files.]] - rationale - backend/01_catalog/linter.py
- [[_decrypt_secret()]] - code - backend/02_features/03_iam/sub_features/12_otp/service.py
- [[_encrypt_secret()]] - code - backend/02_features/03_iam/sub_features/12_otp/service.py
- [[_generate_secret()]] - code - backend/02_features/02_vault/bootstrap.py
- [[_import_module_target()]] - code - backend/01_catalog/linter.py
- [[_init_conn()]] - code - backend/01_core/database.py
- [[_is_allowed()]] - code - backend/01_catalog/linter.py
- [[_mount_module_routers()]] - code - backend/main.py
- [[_owner_of()]] - code - backend/01_catalog/linter.py
- [[_project_root()]] - code - backend/01_catalog/cli.py
- [[_reset_for_tests()_1]] - code - backend/01_core/nats.py
- [[_run_upsert()]] - code - backend/01_catalog/cli.py
- [[apply_seed()]] - code - backend/01_migrator/runner.py
- [[apply_single()]] - code - backend/01_migrator/runner.py
- [[audit.events.query — control node.  Read-only cross-sub-feature lookup over the]] - rationale - backend/02_features/04_audit/sub_features/01_events/nodes/query_events.py
- [[bootstrap()]] - code - backend/01_migrator/runner.py
- [[bootstrap.py]] - code - backend/02_features/02_vault/bootstrap.py
- [[bootstrap_monitoring_jetstream()]] - code - backend/02_features/05_monitoring/bootstrap/jetstream.py
- [[check_file()]] - code - backend/01_catalog/linter.py
- [[check_tree()]] - code - backend/01_catalog/linter.py
- [[cli.py]] - code - backend/01_catalog/cli.py
- [[client.py]] - code - backend/02_features/02_vault/client.py
- [[close()]] - code - backend/01_core/nats.py
- [[close_pool()]] - code - backend/01_core/database.py
- [[cmd_lint()]] - code - backend/01_catalog/cli.py
- [[cmd_upsert()]] - code - backend/01_catalog/cli.py
- [[compute_checksum()]] - code - backend/01_migrator/runner.py
- [[connect()]] - code - backend/01_core/nats.py
- [[create_pool()]] - code - backend/01_core/database.py
- [[crypto.py]] - code - backend/02_features/02_vault/crypto.py
- [[database.py]] - code - backend/01_core/database.py
- [[decrypt()]] - code - backend/02_features/02_vault/crypto.py
- [[discover_migrated()]] - code - backend/01_migrator/runner.py
- [[discover_pending()]] - code - backend/01_migrator/runner.py
- [[discover_seeds()]] - code - backend/01_migrator/runner.py
- [[encrypt()]] - code - backend/02_features/02_vault/crypto.py
- [[ensure_bootstrap_secrets()]] - code - backend/02_features/02_vault/bootstrap.py
- [[error()]] - code - backend/01_core/response.py
- [[get_applied()]] - code - backend/01_migrator/runner.py
- [[get_applied_seeds()]] - code - backend/01_migrator/runner.py
- [[get_current_user()]] - code - backend/01_migrator/runner.py
- [[get_full_history()]] - code - backend/01_migrator/runner.py
- [[get_nats()]] - code - backend/01_core/nats.py
- [[health()]] - code - backend/main.py
- [[jetstream.py]] - code - backend/02_features/05_monitoring/bootstrap/jetstream.py
- [[lifespan()]] - code - backend/main.py
- [[linter.py]] - code - backend/01_catalog/linter.py
- [[load_root_key()]] - code - backend/02_features/02_vault/crypto.py
- [[main()]] - code - backend/01_catalog/cli.py
- [[main()_1]] - code - backend/01_migrator/runner.py
- [[main.py]] - code - backend/main.py
- [[move_to_in_progress()]] - code - backend/01_migrator/runner.py
- [[move_to_migrated()]] - code - backend/01_migrator/runner.py
- [[nats.py]] - code - backend/01_core/nats.py
- [[parse_migration()]] - code - backend/01_migrator/runner.py
- [[parse_seed()]] - code - backend/01_migrator/runner.py
- [[query_events.py]] - code - backend/02_features/04_audit/sub_features/01_events/nodes/query_events.py
- [[run_apply()]] - code - backend/01_migrator/runner.py
- [[run_history()]] - code - backend/01_migrator/runner.py
- [[run_new()]] - code - backend/01_migrator/runner.py
- [[run_rollback()]] - code - backend/01_migrator/runner.py
- [[run_seed()]] - code - backend/01_migrator/runner.py
- [[run_status()]] - code - backend/01_migrator/runner.py
- [[runner.py_2]] - code - backend/01_migrator/runner.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Core_Infrastructure
SORT file.name ASC
```

## Connections to other communities
- 12 edges to [[_COMMUNITY_Service & Repository Layer]]
- 9 edges to [[_COMMUNITY_Audit Emit Pipeline]]
- 7 edges to [[_COMMUNITY_Admin Routes & DLQ]]
- 5 edges to [[_COMMUNITY_Monitoring Stores & Workers]]
- 5 edges to [[_COMMUNITY_API Routes & Response Handling]]
- 4 edges to [[_COMMUNITY_Notify Templates & Email Delivery]]
- 3 edges to [[_COMMUNITY_Auth & Error Handling]]
- 2 edges to [[_COMMUNITY_Node Catalog & Feature Implementations]]
- 2 edges to [[_COMMUNITY_Session Auth & Middleware]]
- 1 edge to [[_COMMUNITY_Monitoring Query DSL]]
- 1 edge to [[_COMMUNITY_Alert Evaluator Worker]]
- 1 edge to [[_COMMUNITY_Audit Events & Saved Views]]

## Top bridge nodes
- [[lifespan()]] - degree 21, connects to 5 communities
- [[error()]] - degree 9, connects to 5 communities
- [[.run()_65]] - degree 8, connects to 4 communities
- [[_run_upsert()]] - degree 6, connects to 2 communities
- [[_encrypt_secret()]] - degree 4, connects to 2 communities