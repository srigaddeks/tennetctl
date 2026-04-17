---
type: community
cohesion: 0.02
members: 136
---

# Error Types & Authorization

**Cohesion:** 0.02 - loosely connected
**Members:** 136 nodes

## Members
- [[Concept EAV pattern for role attributes (code, label, description) in dtl_attrs]] - code - backend/02_features/03_iam/sub_features/04_roles/repository.py
- [[Concept Email OTP auth (6-digit, SHA-256 hash, 5-min TTL, 3 max attempts)]] - document - backend/02_features/03_iam/sub_features/12_otp/service.py
- [[Concept FOR UPDATE SKIP LOCKED atomic claim pattern for email delivery worker]] - code - backend/02_features/06_notify/sub_features/07_email/repository.py
- [[Concept HMAC-SHA256 signed tokens for magic-link security (no raw token stored)]] - code - backend/02_features/03_iam/sub_features/11_magic_link/service.py
- [[Concept OAuth signin (Google + GitHub code exchange, user upsert)]] - document - backend/02_features/03_iam/sub_features/10_auth/service.py
- [[Concept Org membership (user-org lnk, immutable, hard-delete on revoke)]] - document - backend/02_features/03_iam/sub_features/07_memberships/service.py
- [[Concept Single-tenant default org auto-attach on signupsignin]] - document - backend/02_features/03_iam/sub_features/10_auth/service.py
- [[Concept TOTP auth (RFC 6238, pyotp, 30s window, vault-encrypted secret)]] - document - backend/02_features/03_iam/sub_features/12_otp/service.py
- [[Concept TOTP secret envelope-encrypted via vault root key (DEK + nonce)]] - document - backend/02_features/03_iam/sub_features/12_otp/service.py
- [[Concept User EAV attributes (email, display_name, avatar_url in dtl_attrs)]] - document - backend/02_features/03_iam/sub_features/03_users/repository.py
- [[Concept WebAuthn two-phase ceremony (begin challenge → complete verification)]] - code - backend/02_features/03_iam/sub_features/13_passkeys/service.py
- [[Concept Workspace membership (user-workspace lnk, org_id auto-derived, immutable)]] - document - backend/02_features/03_iam/sub_features/07_memberships/service.py
- [[Concept critical notification category cannot be opted out]] - code - backend/02_features/06_notify/sub_features/09_preferences/service.py
- [[Concept event_key wildcard pattern matching (exact, prefix., )]] - code - backend/02_features/06_notify/sub_features/05_subscriptions/service.py
- [[Concept no user enumeration — magic_link returns 'sent' regardless of user existence]] - code - backend/02_features/03_iam/sub_features/11_magic_link/service.py
- [[CreateDashboard — node key monitoring.dashboards.create (effect kind, emits_audit=True)]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/create_dashboard.py
- [[DB Table 05_monitoring.10_fct_monitoring_dashboards]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/repository.py
- [[DB Table 05_monitoring.11_fct_monitoring_panels]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/repository.py
- [[DB View 05_monitoring.v_monitoring_dashboards]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/repository.py
- [[DB View 05_monitoring.v_monitoring_panels]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/repository.py
- [[DB table 02_vault.10_fct_vault_entries (encrypted secrets rows)]] - document - backend/02_features/02_vault/client.py
- [[DB table 03_iam.02_dim_account_types]] - code - backend/02_features/03_iam/sub_features/03_users/repository.py
- [[DB table 03_iam.12_fct_users]] - code - backend/02_features/03_iam/sub_features/03_users/repository.py
- [[DB table 03_iam.13_fct_roles]] - code - backend/02_features/03_iam/sub_features/04_roles/repository.py
- [[DB table 03_iam.19_fct_iam_magic_link_tokens]] - code - backend/02_features/03_iam/sub_features/11_magic_link/repository.py
- [[DB table 03_iam.21_dtl_attrs (EAV user attributes)]] - code - backend/02_features/03_iam/sub_features/03_users/repository.py
- [[DB table 03_iam.23_fct_iam_otp_codes]] - code - backend/02_features/03_iam/sub_features/12_otp/repository.py
- [[DB table 03_iam.24_fct_iam_totp_credentials]] - code - backend/02_features/03_iam/sub_features/12_otp/repository.py
- [[DB table 03_iam.40_lnk_user_orgs (org memberships)]] - code - backend/02_features/03_iam/sub_features/07_memberships/repository.py
- [[DB table 03_iam.41_lnk_user_workspaces (workspace memberships)]] - code - backend/02_features/03_iam/sub_features/07_memberships/repository.py
- [[DB table 06_notify.14_fct_notify_subscriptions]] - code - backend/02_features/06_notify/sub_features/05_subscriptions/repository.py
- [[DB table 06_notify.15_fct_notify_deliveries_1]] - code - backend/02_features/06_notify/sub_features/07_email/repository.py
- [[DB table 06_notify.17_fct_notify_user_preferences]] - code - backend/02_features/06_notify/sub_features/09_preferences/repository.py
- [[DB view 03_iam.v_users]] - code - backend/02_features/03_iam/sub_features/03_users/repository.py
- [[DB 01_catalog.10_fct_features]] - code - backend/01_catalog/repository.py
- [[DB 01_catalog.11_fct_sub_features]] - code - backend/01_catalog/repository.py
- [[DB 01_catalog.12_fct_nodes]] - code - backend/01_catalog/repository.py
- [[DB 06_notify.11_fct_notify_template_groups]] - code - backend/02_features/06_notify/sub_features/02_template_groups/repository.py
- [[DB 06_notify.16_fct_notify_webpush_subscriptions]] - code - backend/02_features/06_notify/sub_features/08_webpush/repository.py
- [[DB 06_notify.17_fct_notify_suppressions]] - code - backend/02_features/06_notify/sub_features/16_suppression/repository.py
- [[DB 06_notify.v_notify_template_groups]] - code - backend/02_features/06_notify/sub_features/02_template_groups/repository.py
- [[Dashboards Repository — raw SQL against 10_fct_monitoring_dashboards + 11_fct_monitoring_panels]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/repository.py
- [[Dashboards Routes — full CRUD v1monitoringdashboards + nested panels]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/routes.py
- [[Dashboards Schemas — Pydantic models DashboardCreateUpdateResponse, PanelCreateUpdateResponse, GridPos]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/schemas.py
- [[Dashboards Service — CRUD for dashboards + panels, emits audit via catalog]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/service.py
- [[DeleteDashboard — node key monitoring.dashboards.delete (effect kind, emits_audit=True)]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/delete_dashboard.py
- [[DomainError — CAT_DOMAIN, non-retryable domain failure]] - code - backend/01_catalog/errors.py
- [[Envelope dataclass (ciphertext, wrapped_dek, nonce)]] - code - backend/02_features/02_vault/crypto.py
- [[GetDashboard — node key monitoring.dashboards.get (request kind, emits_audit=False)]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/get_dashboard.py
- [[IAM feature router — aggregates all sub-feature routers]] - code - backend/02_features/03_iam/routes.py
- [[ListDashboards — node key monitoring.dashboards.list (request kind, emits_audit=False)]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/list_dashboards.py
- [[Node catalog — run_node dispatcher for audit.events.emit, notify.send.transactional]] - code - backend/01_catalog/__init__.py
- [[Node — base class for all node handlers (NCP v1 §4)]] - code - backend/01_catalog/node.py
- [[Node audit.events.emit]] - code - backend/02_features/03_iam/sub_features/07_memberships/service.py
- [[Node iam.memberships.org.assign (effect)]] - code - backend/02_features/03_iam/sub_features/07_memberships/nodes/iam_memberships_org_assign.py
- [[Node iam.memberships.org.revoke (effect)]] - code - backend/02_features/03_iam/sub_features/07_memberships/nodes/iam_memberships_org_revoke.py
- [[Node iam.memberships.workspace.assign (effect)]] - code - backend/02_features/03_iam/sub_features/07_memberships/nodes/iam_memberships_workspace_assign.py
- [[Node iam.memberships.workspace.revoke (effect)]] - code - backend/02_features/03_iam/sub_features/07_memberships/nodes/iam_memberships_workspace_revoke.py
- [[Node iam.users.create (effect)]] - code - backend/02_features/03_iam/sub_features/03_users/nodes/iam_users_create.py
- [[Node iam.users.get (control)]] - code - backend/02_features/03_iam/sub_features/03_users/nodes/iam_users_get.py
- [[NodeAuthDenied — CAT_AUTH_DENIED error]] - code - backend/01_catalog/errors.py
- [[NodeContext — audit + tracing context passed to node run() handlers]] - code - backend/01_catalog/authz.py
- [[NodeNotFound — CAT_NODE_NOT_FOUND error]] - code - backend/01_catalog/errors.py
- [[NodeTombstoned — CAT_NODE_TOMBSTONED error]] - code - backend/01_catalog/errors.py
- [[RunnerError — base class for catalog runtime errors (code=CAT_UNKNOWN)]] - code - backend/01_catalog/errors.py
- [[TransientError — CAT_TRANSIENT, only class that triggers runner retries]] - code - backend/01_catalog/errors.py
- [[UpdateDashboard — node key monitoring.dashboards.update (effect kind, emits_audit=True)]] - code - backend/02_features/05_monitoring/sub_features/05_dashboards/nodes/update_dashboard.py
- [[backend.01_catalog.authz — Authorization hook for node runner (NCP v1 §9)]] - code - backend/01_catalog/authz.py
- [[backend.01_catalog.errors — Runner error hierarchy]] - code - backend/01_catalog/errors.py
- [[backend.01_catalog.linter — Cross-import linter, enforces NCP v1 §10]] - code - backend/01_catalog/linter.py
- [[backend.01_catalog.repository — raw asyncpg upserts into 01_catalog fct tables]] - code - backend/01_catalog/repository.py
- [[backend.01_catalog.routes — Read-only HTTP surface for live node registry (v1catalog)]] - code - backend/01_catalog/routes.py
- [[backend.02_features.02_vault.crypto (Envelope encryptdecrypt)]] - code - backend/02_features/03_iam/sub_features/12_otp/service.py
- [[iam.auth service layer (signupsigninsignoutOAuth)]] - code - backend/02_features/03_iam/sub_features/10_auth/service.py
- [[iam.magic_link repository — 19_fct_iam_magic_link_tokens]] - code - backend/02_features/03_iam/sub_features/11_magic_link/repository.py
- [[iam.magic_link routes — v1authmagic-linkrequest + consume]] - code - backend/02_features/03_iam/sub_features/11_magic_link/routes.py
- [[iam.magic_link schemas — MagicLinkRequestConsumeRequestResponse]] - code - backend/02_features/03_iam/sub_features/11_magic_link/schemas.py
- [[iam.magic_link service — request + consume flow with HMAC tokens]] - code - backend/02_features/03_iam/sub_features/11_magic_link/service.py
- [[iam.memberships FastAPI routes]] - code - backend/02_features/03_iam/sub_features/07_memberships/routes.py
- [[iam.memberships Pydantic schemas]] - code - backend/02_features/03_iam/sub_features/07_memberships/schemas.py
- [[iam.memberships asyncpg repository]] - code - backend/02_features/03_iam/sub_features/07_memberships/repository.py
- [[iam.memberships service layer]] - code - backend/02_features/03_iam/sub_features/07_memberships/service.py
- [[iam.otp FastAPI routes (v1authotp, v1authtotp)]] - code - backend/02_features/03_iam/sub_features/12_otp/routes.py
- [[iam.otp Pydantic schemas]] - code - backend/02_features/03_iam/sub_features/12_otp/schemas.py
- [[iam.otp asyncpg repository]] - code - backend/02_features/03_iam/sub_features/12_otp/repository.py
- [[iam.otp service layer (email OTP + TOTP)]] - code - backend/02_features/03_iam/sub_features/12_otp/service.py
- [[iam.passkeys service — WebAuthn FIDO2 registration + authentication]] - code - backend/02_features/03_iam/sub_features/13_passkeys/service.py
- [[iam.roles repository — EAV attrs, v_roles, 13_fct_roles]] - code - backend/02_features/03_iam/sub_features/04_roles/repository.py
- [[iam.roles routes — v1roles 5-endpoint CRUD]] - code - backend/02_features/03_iam/sub_features/04_roles/routes.py
- [[iam.roles schemas — RoleCreateUpdateRead]] - code - backend/02_features/03_iam/sub_features/04_roles/schemas.py
- [[iam.roles service — CRUD with EAV attributes]] - code - backend/02_features/03_iam/sub_features/04_roles/service.py
- [[iam.roles.create — effect node (catalog)]] - code - backend/02_features/03_iam/sub_features/04_roles/nodes/iam_roles_create.py
- [[iam.roles.get — control node (catalog)]] - code - backend/02_features/03_iam/sub_features/04_roles/nodes/iam_roles_get.py
- [[iam.sessions service — mint_session (shared by magic_link + passkeys)]] - code - backend/02_features/03_iam/sub_features/09_sessions/service.py
- [[iam.users FastAPI routes]] - code - backend/02_features/03_iam/sub_features/03_users/routes.py
- [[iam.users Pydantic schemas]] - code - backend/02_features/03_iam/sub_features/03_users/schemas.py
- [[iam.users repository — get_by_id used by magic_link + passkeys]] - code - backend/02_features/03_iam/sub_features/03_users/repository.py
- [[iam.users service layer]] - code - backend/02_features/03_iam/sub_features/03_users/service.py
- [[notify.deliveries.repository — mark_retryable_error, backoff_seconds_for_attempt (used by webpush)]] - code - backend/02_features/06_notify/sub_features/06_deliveries/repository.py
- [[notify.deliveries.service — create_delivery]] - code - backend/02_features/06_notify/sub_features/06_deliveries/service.py
- [[notify.email repository — poll_and_claim_email_deliveries]] - code - backend/02_features/06_notify/sub_features/07_email/repository.py
- [[notify.email routes — openclick tracking, bounce webhook]] - code - backend/02_features/06_notify/sub_features/07_email/routes.py
- [[notify.preferences repository — upsertget_opt_in, 17_fct_notify_user_preferences]] - code - backend/02_features/06_notify/sub_features/09_preferences/repository.py
- [[notify.preferences routes — GETPATCH v1notifypreferences]] - code - backend/02_features/06_notify/sub_features/09_preferences/routes.py
- [[notify.preferences schemas — PreferencePatchBodyPreferenceRow]] - code - backend/02_features/06_notify/sub_features/09_preferences/schemas.py
- [[notify.preferences.service — is_opted_in (channel+category opt-out check)]] - code - backend/02_features/06_notify/sub_features/09_preferences/service.py
- [[notify.routes — Feature router aggregating all notify sub-feature routers]] - code - backend/02_features/06_notify/routes.py
- [[notify.send.transactional — node key for programmatic sends]] - code - frontend/src/app/(dashboard)/notify/send/page.tsx
- [[notify.subscriptions repository — asyncpg raw SQL, v_notify_subscriptions]] - code - backend/02_features/06_notify/sub_features/05_subscriptions/repository.py
- [[notify.subscriptions routes — v1notifysubscriptions CRUD]] - code - backend/02_features/06_notify/sub_features/05_subscriptions/routes.py
- [[notify.subscriptions schemas — SubscriptionCreateUpdateRow]] - code - backend/02_features/06_notify/sub_features/05_subscriptions/schemas.py
- [[notify.subscriptions.service — list_active_for_worker, matches_pattern]] - code - backend/02_features/06_notify/sub_features/05_subscriptions/service.py
- [[notify.suppression.repository — asyncpg CRUD on 06_notify.17_fct_notify_suppressions]] - code - backend/02_features/06_notify/sub_features/16_suppression/repository.py
- [[notify.suppression.routes — v1notifysuppressions (admin) + v1notifyunsubscribe (public RFC 8058)]] - code - backend/02_features/06_notify/sub_features/16_suppression/routes.py
- [[notify.suppression.schemas — SuppressionAdd  SuppressionRow (ReasonCode hard_bounce, complaint, manual, unsubscribe)]] - code - backend/02_features/06_notify/sub_features/16_suppression/schemas.py
- [[notify.suppression.service — HMAC-signed unsubscribe tokens + suppression CRUD]] - code - backend/02_features/06_notify/sub_features/16_suppression/service.py
- [[notify.template_groups.repository — asyncpg CRUD on 06_notify.11_fct_notify_template_groups]] - code - backend/02_features/06_notify/sub_features/02_template_groups/repository.py
- [[notify.template_groups.routes — REST API v1notifytemplate-groups]] - code - backend/02_features/06_notify/sub_features/02_template_groups/routes.py
- [[notify.template_groups.schemas — TemplateGroupCreate  TemplateGroupUpdate  TemplateGroupRow]] - code - backend/02_features/06_notify/sub_features/02_template_groups/schemas.py
- [[notify.template_groups.service — CRUD + audit emission for template groups]] - code - backend/02_features/06_notify/sub_features/02_template_groups/service.py
- [[notify.templates.nodes.safelist — validate_dynamic_sql (called from variables schema validator)]] - code - backend/02_features/06_notify/sub_features/03_templates/nodes/safelist.py
- [[notify.templates.repository — get_template (used by worker to resolve template)]] - code - backend/02_features/06_notify/sub_features/03_templates/repository.py
- [[notify.variables.repository — resolve_variables (used by worker to render template vars)]] - code - backend/02_features/06_notify/sub_features/04_variables/repository.py
- [[notify.variables.schemas — TemplateVariableCreate  TemplateVariableUpdate  ResolveRequest  TemplateVariableRow]] - code - backend/02_features/06_notify/sub_features/04_variables/schemas.py
- [[notify.variables.service — CRUD + resolve_variables for template variables]] - code - backend/02_features/06_notify/sub_features/04_variables/service.py
- [[notify.webpush.repository — asyncpg CRUD on 06_notify.16_fct_notify_webpush_subscriptions]] - code - backend/02_features/06_notify/sub_features/08_webpush/repository.py
- [[notify.webpush.routes — v1notifywebpushvapid-public-key + v1notifywebpushsubscriptions]] - code - backend/02_features/06_notify/sub_features/08_webpush/routes.py
- [[notify.webpush.schemas — WebpushSubscriptionCreate  WebpushSubscriptionOut  VapidPublicKeyOut]] - code - backend/02_features/06_notify/sub_features/08_webpush/schemas.py
- [[notify.webpush.service — VAPID key bootstrap + pywebpush sending + delivery poller]] - code - backend/02_features/06_notify/sub_features/08_webpush/service.py
- [[notify.worker — Subscription worker polls audit outbox, matches subscriptions, enqueues deliveries]] - code - backend/02_features/06_notify/worker.py
- [[vault bootstrap (ensure_bootstrap_secrets)]] - code - backend/02_features/02_vault/bootstrap.py
- [[vault crypto (AES-256-GCM envelope encryptdecrypt)]] - code - backend/02_features/02_vault/crypto.py
- [[vault.client — VaultClient, VaultSecretNotFound (used by suppression + webpush for signing keys)]] - code - backend/02_features/02_vault/client.py
- [[vault.secrets repository (get_metadata_by_scope_key used by bootstrap)]] - code - backend/02_features/02_vault/sub_features/01_secrets/repository.py
- [[vault.secrets service (create_secret used by bootstrap)]] - code - backend/02_features/02_vault/sub_features/01_secrets/service.py
- [[vault.secrets.service — create_secret (used to bootstrap VAPID + suppression signing keys)]] - code - backend/02_features/02_vault/sub_features/01_secrets/service.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Error_Types_&_Authorization
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_API Endpoint Type Catalog]]
- 1 edge to [[_COMMUNITY_Alert Rules & Evaluation]]
- 1 edge to [[_COMMUNITY_API Keys Sub-feature]]
- 1 edge to [[_COMMUNITY_Architecture Decision Records]]

## Top bridge nodes
- [[notify.worker — Subscription worker polls audit outbox, matches subscriptions, enqueues deliveries]] - degree 6, connects to 1 community
- [[iam.sessions service — mint_session (shared by magic_link + passkeys)]] - degree 5, connects to 1 community
- [[notify.send.transactional — node key for programmatic sends]] - degree 4, connects to 1 community
- [[vault crypto (AES-256-GCM envelope encryptdecrypt)]] - degree 4, connects to 1 community