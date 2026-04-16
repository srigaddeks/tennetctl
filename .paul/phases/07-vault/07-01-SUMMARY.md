---
phase: 07-vault
plan: 01
subsystem: backend
tags: [vault, crypto, aes-256-gcm, envelope-encryption, eav, pure-eav, audit, bootstrap-secrets, env-var-contract, nodes, run_node]

requires:
  - phase: 02-catalog-foundation
    provides: NCP v1 — manifest, loader, runner, NodeContext, run_node, authz
  - phase: 03-iam-audit
    provides: "04_audit" schema + audit.events.emit node + scope CHECK (setup-bypass lets v0.2 vault writes land)
  - phase: 04-orgs-workspaces
    provides: Canonical 5-file sub-feature layout + Pure-EAV pattern (reference: dtl_attrs description for roles/groups)
provides:
  - 02_vault schema with Pure-EAV foundation (dim_entity_types, dtl_attr_defs, dtl_attrs, fct_vault_entries) + v_vault_entries flat read view
  - crypto module — AES-256-GCM envelope encryption via PyCA `cryptography` (load_root_key / encrypt / decrypt / Envelope dataclass)
  - VaultClient — app-singleton with 60s SWR cache; get / get_with_version / invalidate / invalidate_all
  - 4 catalog-registered nodes — vault.secrets.put/rotate/delete (effect, emits audit) + vault.secrets.get (request, hot-path, no audit)
  - 5 FastAPI endpoints under /v1/vault (list / create / get-plaintext / rotate / delete); item path uses {key} not {id}
  - Env-var contract enforcement — _enforce_env_contract() blocks startup if any TENNETCTL_* secret-named var is outside the 5-item allowlist
  - Bootstrap secrets — auth.argon2.pepper + auth.session.signing_key_v1 seeded on first boot; idempotent
  - ADR-028 — documents the envelope-encryption design, env-var contract, pre-auth gap, non-goals
  - 25 pytest tests — 9 crypto unit tests + 16 integration tests covering CRUD + audit + cache + plaintext-grep + at-rest-binary
affects: [Phase 7 Plan 02 (Vault UI), Phase 8 (auth — will read bootstrap pepper + signing key from vault), all future features needing secrets]

tech-stack:
  added:
    - cryptography>=43 (already installed via requirements.txt transitive; no new requirement line needed)
  patterns:
    - "Pure-EAV option B enforced — description lives in 02_vault.21_dtl_attrs via dim_attr_defs, not as a column on fct_vault_entries. Matches how IAM handles display_name/description for roles/groups/applications."
    - "Per-schema EAV stack — each feature schema owns its own dim_entity_types/dtl_attr_defs/dtl_attrs. Vault doesn't reuse IAM's EAV tables."
    - "Service takes (pool, conn, ctx, *, vault_client) for mutations so the in-process SWR cache can be invalidated atomically with the DB write + audit emit."
    - "NodeContext.extras carries both 'pool' (inherited from phase 4 pattern) and 'vault' (new for this phase)."
    - "Item path keyed on stable user-supplied identifier, not UUID — /v1/vault/{key} rather than /{id}. Documented deviation from the default 5-endpoint shape."
    - "Audit split between HTTP and node paths: HTTP GET /v1/vault/{key} always audits, vault.secrets.get node never does (hot-path). Deliberate, documented in AC-5 + ADR-028."
    - "Seed filenames must be globally unique — discovery is by filename across features, so vault seeds use 02vault_* prefix to avoid colliding with IAM's 01_dim_entity_types.yaml / 20_dtl_attr_defs.yaml."

key-files:
  created:
    - 03_docs/00_main/08_decisions/028_vault_foundation.md
    - 03_docs/features/02_vault/00_bootstrap/09_sql_migrations/02_in_progress/20260417_009_vault-module-register.sql
    - 03_docs/features/02_vault/00_bootstrap/09_sql_migrations/02_in_progress/20260417_010_vault-schema.sql
    - 03_docs/features/02_vault/00_bootstrap/09_sql_migrations/seeds/02vault_01_dim_entity_types.yaml
    - 03_docs/features/02_vault/00_bootstrap/09_sql_migrations/seeds/02vault_20_dtl_attr_defs.yaml
    - backend/02_features/02_vault/__init__.py
    - backend/02_features/02_vault/crypto.py
    - backend/02_features/02_vault/client.py
    - backend/02_features/02_vault/bootstrap.py
    - backend/02_features/02_vault/routes.py
    - backend/02_features/02_vault/feature.manifest.yaml
    - backend/02_features/02_vault/sub_features/__init__.py
    - backend/02_features/02_vault/sub_features/01_secrets/__init__.py
    - backend/02_features/02_vault/sub_features/01_secrets/schemas.py
    - backend/02_features/02_vault/sub_features/01_secrets/repository.py
    - backend/02_features/02_vault/sub_features/01_secrets/service.py
    - backend/02_features/02_vault/sub_features/01_secrets/routes.py
    - backend/02_features/02_vault/sub_features/01_secrets/nodes/__init__.py
    - backend/02_features/02_vault/sub_features/01_secrets/nodes/vault_secrets_put.py
    - backend/02_features/02_vault/sub_features/01_secrets/nodes/vault_secrets_get.py
    - backend/02_features/02_vault/sub_features/01_secrets/nodes/vault_secrets_rotate.py
    - backend/02_features/02_vault/sub_features/01_secrets/nodes/vault_secrets_delete.py
    - tests/test_vault_crypto.py
    - tests/test_vault_api.py
  modified:
    - .env.example
    - backend/01_core/config.py
    - backend/main.py

key-decisions:
  - "Option B for description storage (PATH: pure-EAV) — chosen over A (drop field) and C (fct deviation). Keeps Pure-EAV rule intact; matches existing IAM precedent for role/group/application descriptions. Trade-off: ~1 extra dtl_attrs write per mutation, v_vault_entries view joins in dtl_attrs, one extra dim_entity_types + dim_attr_defs entry in 02_vault schema."
  - "Item path uses {key} not {id} — secrets are identified by their user-supplied key, not a UUID. Documented deviation from the 5-endpoint default shape. Rationale: operator UX + backend code both reference secrets by name, and key is guaranteed unique per key_shape regex."
  - "Audit split between HTTP and node — HTTP GET /v1/vault/{key} emits vault.secrets.read every call; vault.secrets.get node does not. The node runs in the hot path (OAuth secret / session signing / Argon2 pepper reads), auditing each would drown evt_audit. Enterprise-grade visibility comes from the HTTP admin route."
  - "Key recycling refused in v0.2 — POST a key that was previously POSTed + DELETEd returns 409. Prevents a rotated-then-deleted-then-recreated key silently reappearing with new meaning. v0.3 adds tombstone state + admin-only forced recycle."
  - "Single root key in env (TENNETCTL_VAULT_ROOT_KEY) — 32 bytes base64. Rotation = redeploy + re-wrap script (not automated). Deliberate baseline; KMS/HSM/multi-key deferred to v0.3."
  - "Pre-auth gate via TENNETCTL_ALLOW_UNAUTHENTICATED_VAULT=true — lets v0.2 vault routes serve without auth until phase 8 ships. Boot WARNING logs every start as a removal reminder. Flag disappears entirely in phase 8."
  - "Seed filename prefix '02vault_' — global seed tracking keys by filename only, so vault seeds must not collide with IAM's 01_dim_entity_types.yaml / 20_dtl_attr_defs.yaml."

patterns-established:
  - "Envelope encryption via PyCA cryptography — never roll your own primitives. Per-secret DEK + 12-byte nonces + GCM auth tag covers ciphertext + nonce."
  - "In-process SWR cache for secret reads — backend features never re-read from DB on every request. Cache keyed by secret name; rotate/delete service paths call vault.invalidate(key) inside the same tx."
  - "Env-var allowlist enforcement at startup — config.py._enforce_env_contract() blocks boot if a stray TENNETCTL_*_SECRET / TOKEN / PASSWORD / KEY is present. Allowlist is 5 items."
  - "Bootstrap secrets helper in feature package — backend/02_features/02_vault/bootstrap.py.ensure_bootstrap_secrets(pool, vault_client) is idempotent. Runs from lifespan after catalog upsert."

duration: ~55min
started: 2026-04-16T15:05:00Z
completed: 2026-04-16T16:00:00Z
---

# Phase 7 Plan 01: Vault Backend — Summary

**Enterprise-grade secret storage ships: AES-256-GCM envelope encryption, per-secret DEKs wrapped by a root key, SWR-cached VaultClient, 4 catalog nodes, 5 routes under /v1/vault, auto-seeded bootstrap secrets for phase 8 auth, env-var allowlist that refuses secrets-in-env at startup, and Pure-EAV storage for secret descriptions.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~55min |
| Tasks | 6 (5 apply + 1 UNIFY) |
| Files created | 23 (20 code/config + 2 migrations + 2 seeds + 1 ADR) |
| Files modified | 3 (.env.example, config.py, main.py) |
| New code lines | ~1830 (crypto 93 + client 80 + bootstrap 75 + service 230 + routes 160 + schemas 75 + repo 150 + nodes 190 + tests 532 + ADR 130 + migration 150 + manifest 80) |
| Nodes registered | 4 new (vault.secrets.put/get/rotate/delete) — catalog total goes from 17 → 21 |
| HTTP routes mounted | 5 under /v1/vault |
| Pytest | 129/129 green (25 new vault tests + 104 prior ex-migrator-drift); migrator 11 pre-existing failures unchanged |

## Acceptance Criteria Results

| Criterion | Status | Evidence |
|-----------|--------|----------|
| AC-1: Migrations reversible (module-register + schema) | Pass | `apply` creates `02_vault` schema + 4 tables + view + 5 dim_modules row; `rollback --to 20260417_009` drops everything cleanly. Re-apply idempotent. |
| AC-2: Crypto round-trip + tamper + wrong-key failures | Pass | `test_vault_crypto.py` 9 tests — round-trip, tamper-ciphertext (InvalidTag), tamper-wrapped-dek (InvalidTag), wrong-root-key (InvalidTag), two-encrypts-differ (fresh nonce+DEK per call), empty-plaintext-rejected, missing-root-key, wrong-length-root-key, non-base64-root-key. |
| AC-3: 5 routes round-trip a secret | Pass | `test_crud_round_trip` + live curl POST → list (no value) → GET (value) → rotate → GET new value → DELETE → 404. Metadata rows only in list; audit fires on every mutation. |
| AC-4: VaultClient cache behaviour | Pass | `test_cache_refresh_on_rotate` + `test_cache_ttl_expiry` — second call within TTL hits cache; rotate busts; TTL expiry forces re-fetch. _fetch_count counter verifies no DB hit on cache hit. |
| AC-5: 4 nodes register + execute via run_node | Pass | Catalog upsert log: `19 → 21 nodes` on first boot. `test_nodes_via_runner` exercises put/get/rotate/delete via run_node; get emits no audit (kind=request), effect nodes emit correct audit rows. |
| AC-6: Env-var contract enforced at startup | Pass | Smoke: `TENNETCTL_GOOGLE_CLIENT_SECRET=abc ... load_config()` raises RuntimeError pointing at vault docs. Missing root key, wrong-length key, non-base64 key — all three fail with clear messages. |
| AC-7: Bootstrap secrets on first boot | Pass | Live boot logs 2 `vault.secrets.created` events with `metadata.source='bootstrap'`; v_vault_entries shows auth.argon2.pepper + auth.session.signing_key_v1 at version=1, created_by='sys'. Second boot: 0 new inserts (idempotent). |
| AC-8: No plaintext anywhere it shouldn't be | Pass | `test_plaintext_never_logged` greps caplog for a sentinel across POST/GET/rotate/DELETE and finds zero matches. `test_ciphertext_is_binary` confirms sentinel bytes NOT present in stored ciphertext; psql ciphertext::text dump fails with "invalid UTF-8 byte 0xa1" (confirms binary). `test_crud_round_trip` asserts list payload contains neither value/ciphertext/wrapped_dek/nonce. |
| AC-9: Tests + catalog both green | Pass | 25 new vault tests pass; 104 prior tests still pass (129 total ex-migrator); `/v1/catalog/nodes` lists all 4 vault.secrets.* nodes. |

## Accomplishments

- **Envelope encryption working end-to-end** — live smoke curl exercised full CRUD; stored ciphertext is binary noise (invalid UTF-8), no plaintext ever in the DB.
- **Audit trail on every mutation + HTTP read** — 5 audit events per full lifecycle (created, read, rotated, read, deleted); all landed in `04_audit.60_evt_audit` with correct metadata.key.
- **Bootstrap secrets auto-seeded** — both auth.argon2.pepper and auth.session.signing_key_v1 created on first boot with `created_by='sys'`, `audit_category='setup'`, `metadata.source='bootstrap'`. Phase 8 can `request.app.state.vault.get("auth.argon2.pepper")` immediately.
- **Env-var allowlist locks the surface** — operators can no longer put `TENNETCTL_GOOGLE_CLIENT_SECRET` in the env. App refuses to boot until they move it to the vault via POST /v1/vault.
- **Pure-EAV preserved** — no business columns on `fct_vault_entries`. Description lives in `02_vault.21_dtl_attrs` via `dim_attr_defs` entry. Memory-pinned rule honored.
- **In-process SWR cache** — backend features read secrets at near-zero latency; rotate/delete invalidate atomically inside the same transaction.

## Files Created/Modified

### Created (23)

| File | Purpose |
|------|---------|
| `03_docs/00_main/08_decisions/028_vault_foundation.md` | ADR documenting envelope encryption, env-var contract, non-goals, pre-auth gap |
| `03_docs/features/02_vault/00_bootstrap/09_sql_migrations/02_in_progress/20260417_009_vault-module-register.sql` | Register `vault` in dim_modules (reversible) |
| `03_docs/features/02_vault/00_bootstrap/09_sql_migrations/02_in_progress/20260417_010_vault-schema.sql` | Create 02_vault schema, 4 tables, v_vault_entries view, all comments + constraints |
| `03_docs/features/02_vault/00_bootstrap/09_sql_migrations/seeds/02vault_01_dim_entity_types.yaml` | Seed `secret` entity type |
| `03_docs/features/02_vault/00_bootstrap/09_sql_migrations/seeds/02vault_20_dtl_attr_defs.yaml` | Seed `description` attr def |
| `backend/02_features/02_vault/crypto.py` | AES-256-GCM primitives — load_root_key, encrypt, decrypt, Envelope |
| `backend/02_features/02_vault/client.py` | VaultClient singleton — 60s SWR cache, invalidate, fetch_count metric |
| `backend/02_features/02_vault/bootstrap.py` | ensure_bootstrap_secrets(pool, vault_client) — idempotent auto-seeder |
| `backend/02_features/02_vault/routes.py` | Feature-level router aggregator |
| `backend/02_features/02_vault/feature.manifest.yaml` | 4 nodes + 5 routes declared |
| `backend/02_features/02_vault/sub_features/01_secrets/schemas.py` | SecretCreate / SecretRotate / SecretMeta / SecretValue Pydantic v2 |
| `backend/02_features/02_vault/sub_features/01_secrets/repository.py` | asyncpg raw SQL — reads v_vault_entries, writes fct + dtl_attrs |
| `backend/02_features/02_vault/sub_features/01_secrets/service.py` | create/read/rotate/delete with audit emission + cache invalidation |
| `backend/02_features/02_vault/sub_features/01_secrets/routes.py` | 5-endpoint APIRouter; item path uses {key}; pre-auth gate |
| `backend/02_features/02_vault/sub_features/01_secrets/nodes/vault_secrets_put.py` | Effect node — create via run_node |
| `backend/02_features/02_vault/sub_features/01_secrets/nodes/vault_secrets_get.py` | Request node — read via VaultClient (no audit) |
| `backend/02_features/02_vault/sub_features/01_secrets/nodes/vault_secrets_rotate.py` | Effect node — rotate via run_node |
| `backend/02_features/02_vault/sub_features/01_secrets/nodes/vault_secrets_delete.py` | Effect node — delete via run_node |
| `tests/test_vault_crypto.py` | 9 unit tests (AC-2 + extras) |
| `tests/test_vault_api.py` | 16 integration tests (AC-3/4/5/6/7/8) |
| (plus 4 `__init__.py` namespace markers) | |

### Modified (3)

| File | Change |
|------|--------|
| `.env.example` | Documented 5-item TENNETCTL_* allowlist + root key + pre-auth flag |
| `backend/01_core/config.py` | Added `_enforce_env_contract()`, `allow_unauthenticated_vault` field, `vault` in default modules |
| `backend/main.py` | Added `"vault"` to MODULE_ROUTERS; vault lifespan block — loads root key, instantiates VaultClient on `app.state.vault`, runs `ensure_bootstrap_secrets`, requires pre-auth gate flag, logs WARNING while active |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Option B for `description` (EAV dtl_attrs) | Memory-pinned Pure-EAV rule; IAM precedent (roles/groups/applications use dtl_attrs for description) | +1 dim_entity_types row + 1 dim_attr_defs row + dtl_attrs join in view. Service writes one extra row per mutation when description provided. |
| Item path `/v1/vault/{key}` not `/{id}` | Secrets are identified by stable user-supplied key in operator UX + backend code; regex-validated shape guarantees URL-safety | Slight deviation from 5-endpoint default; documented in ADR-028 |
| Audit HTTP-reads but not node-reads | Node path is hot (OAuth secrets, session signing, Argon2 pepper); auditing each drowns evt_audit. HTTP is admin-observability | Enterprise-grade visibility via HTTP admin surface; node path stays fast |
| Key recycling refused in v0.2 | Prevents silent-reappearance footgun after delete | v0.3 will add tombstone state + admin forced recycle |
| Per-schema EAV stack (vault owns its own dim_entity_types etc.) | Matches IAM+featureflags pattern — feature schema is self-contained | `02_vault.01_dim_entity_types` has one row (secret) and starts fresh from id=1 |
| Seed filename prefix `02vault_` | Global seed tracking keys by filename alone; `01_dim_entity_types.yaml` collides with IAM's | Convention to flag for future features: seed filenames must be globally unique |
| Pre-auth gate required | v0.2 has no auth; open vault would be a footgun by default | Requires explicit TENNETCTL_ALLOW_UNAUTHENTICATED_VAULT=true; boot WARNING as removal reminder |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 2 | Seed filename collision with IAM (renamed vault seeds); plan used numeric NNN 009+010 but those already taken by featureflags — file names still work because date prefix 20260417 > 20260416 |
| Scope additions | 3 | Added `TENNETCTL_APP_PORT` as env-var fallback in config.py (plan listed it in allowlist but didn't say read it); added `bootstrap.py` as a separate module rather than inline in main.py (plan suggested either, separate is testable); added 5 extra crypto unit tests beyond AC-2 (load_root_key edge cases + empty plaintext) |
| Deferred | 0 | None |

**Total impact:** Minor. All AC assertions pass. No functional deviations.

### Auto-fixed Issues

**1. Seed filename collision with IAM seeds**
- **Found during:** Task 1 verify (`.venv/bin/python -m backend.01_migrator.runner seed`)
- **Issue:** Vault's `01_dim_entity_types.yaml` had the same filename as IAM's; seeder's `applied_seeds` tracks by filename alone, causing vault seed to be skipped with "checksum mismatch" warning.
- **Fix:** Renamed vault seeds to `02vault_01_dim_entity_types.yaml` + `02vault_20_dtl_attr_defs.yaml`.
- **Verification:** Re-ran `seed`, both rows inserted correctly; confirmed no regression in existing IAM seeds.

**2. Seed tracking survives schema rollback**
- **Found during:** Task 1 rollback test (verified DOWN is clean)
- **Issue:** Seed tracking rows live in `00_schema_migrations.applied_seeds` schema, which survives a DROP SCHEMA "02_vault" CASCADE. After rollback + reapply, seeder thinks seeds are still applied and skips — leaving the newly-recreated schema empty.
- **Fix (this run):** Manual `DELETE FROM applied_seeds WHERE filename LIKE '02vault_%'` then re-seed. Not a code change; pre-existing migrator quirk.
- **Noted:** Added to deferred gaps — future "migrator hardening" plan should make DOWN migrations also remove applied_seeds rows.

### Scope Additions

**1. `TENNETCTL_APP_PORT` env fallback in config.py**
- Plan listed it in the allowlist but didn't specify config.py reads it. I made it a fallback after APP_PORT so operators can use the prefixed name if preferred. Zero behavioral impact when unset.

**2. `bootstrap.py` as a separate module**
- Plan said "helper in main.py or a new file — prefer the separate file for testability". Went with separate file. Clean import path; testable in isolation if future tests need it.

**3. Extra crypto tests**
- Plan specified 5 tests for AC-2; I wrote 9 (added load_root_key edge cases + empty-plaintext rejection). Zero scope risk; proves three defensive paths.

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| Seed filename collision (above) | Renamed vault seeds with `02vault_` prefix. Filed observation: seed discovery's global filename-uniqueness is non-obvious; document in contributing guidelines. |
| Rollback + reapply seed state drift (above) | Manual DELETE on applied_seeds. Noted as deferred migrator-hardening item. |
| pyright `reportInvalidTypeForm` on importlib-bound schemas + `Unused "_pool"` on test fixtures | Pre-existing project convention — Phase 2 decision "Any typing for dynamically-imported modules". Ignored per pattern. |
| `migrator` tests 11/20 failing | Pre-existing from Phase 1 refactor drift (API names `discover_migrations` → `discover_pending`). Not caused by this plan; noted as deferred gap. |

## Next Phase Readiness

**Ready:**
- Phase 7 Plan 02 (Vault UI + Robot/Playwright E2E) — API is stable, reveal-once semantics hold (list never returns value, POST response carries metadata only). Frontend can hit /v1/vault directly.
- Phase 8 (Auth) — bootstrap secrets `auth.argon2.pepper` + `auth.session.signing_key_v1` already seeded. Phase 8 services read them via `request.app.state.vault.get(...)`.
- Future features needing OAuth client secrets, SMTP creds, third-party API keys — all go through the same vault.

**Concerns:**
- Rollback+reapply seed drift (noted above) is a general migrator quirk, not specific to vault. Low priority: manual DELETE is one line.
- `vault.secrets.get` node bypasses audit deliberately (documented), but operators should know reads via HTTP `/v1/vault/{key}` DO audit. UI docs + admin runbook should reinforce this.
- Root key rotation in v0.2 requires a redeploy + re-wrap script that doesn't exist yet. Non-urgent; deferred to v0.3 hardening milestone. Operators should keep the root key in a password manager + sealed backup.

**Blockers:**
- None. Ready for Plan 07-02 (Vault UI + E2E tests).

---
*Phase: 07-vault, Plan: 01*
*Completed: 2026-04-16*
