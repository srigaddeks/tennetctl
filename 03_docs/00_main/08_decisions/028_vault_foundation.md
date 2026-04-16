# ADR-028: Vault Foundation — AES-256-GCM Envelope Encryption

**Status:** Accepted
**Date:** 2026-04-17
**Related:** ADR-018 (node contract), ADR-019 (feature ownership), ADR-026 (minimum surface), ADR-027 (node catalog + runner)

---

## Context

Every feature beyond IAM needs secrets: OAuth client IDs/secrets, session signing keys,
Argon2 pepper, SMTP credentials, third-party API tokens. Today those secrets live in
env vars, which is:

- unsafe — any shell/ps output leaks them
- undifferentiated — the operator cannot tell a "real" secret from a tuning knob
- unrotatable — rotating a signing key requires a restart + human coordination
- unauditable — no record of who read what, when, or why

We need a first-class vault that every other feature reads from, not from env.

Three non-options we need to rule out:

1. **Keep using env vars.** Fails on every axis above. Also contaminates `TENNETCTL_*`
   with dozens of unrelated vars that operators will mis-set.
2. **External KMS (AWS/GCP/HashiCorp).** Great in prod; wrong for a self-hostable platform.
   A developer cloning the repo should be able to `docker compose up` without signing up
   for a cloud KMS.
3. **Plaintext-in-DB.** Meets the "in the DB" goal; fails the security bar the minute
   a backup leaks.

We need a mechanism that is (a) secure without external dependencies, (b) rotatable at
the per-secret level, (c) auditable on every access, (d) usable by every in-process call
without a network hop.

---

## Decision

Adopt **AES-256-GCM envelope encryption** with a single **root key** held in env, and a
per-secret **data encryption key (DEK)** wrapped by the root key.

Three components:

### 1. Envelope encryption (PyCA `cryptography` library)

- Each secret gets its own random 32-byte DEK.
- The DEK encrypts the plaintext using AES-256-GCM with a fresh 12-byte nonce.
- The root key encrypts the DEK using AES-256-GCM with its own fresh 12-byte nonce.
- `fct_vault_entries.wrapped_dek` stores `wrap_nonce || AESGCM(root_key).encrypt(dek)`.
- GCM's auth tag covers ciphertext + nonce; any bit flip raises `InvalidTag` on decrypt.

No rolling-our-own. Every primitive comes from `cryptography.hazmat.primitives.ciphers.aead.AESGCM`.

### 2. Single root key in env (`TENNETCTL_VAULT_ROOT_KEY`)

- 32 raw bytes, base64-encoded (44 chars). Validated at startup.
- Generate via `python -c 'import os,base64; print(base64.b64encode(os.urandom(32)).decode())'`.
- Rotation = redeploy with a new root key + a migration script that re-wraps every DEK.
  Not automated in v0.2; scheduled for v0.3 hardening.

### 3. `VaultClient` in-process API with 60s SWR cache

Every backend feature reads secrets through `request.app.state.vault.get("auth.argon2.pepper")`.
The client holds a process-local cache keyed by secret name; entries expire after 60s or on
explicit `invalidate(key)` from the rotate/delete service paths.

The in-process path does **not** audit per-read — auditing every OAuth secret read for every
request would drown the audit log. HTTP `GET /v1/vault/{key}` **does** audit every access, for
operator visibility. This split is deliberate (see AC-5 of plan 07-01).

### Storage layout

`02_vault` schema, Pure-EAV compliant (matches ADR-019 + `.claude/rules/common/database.md`):

| Table | Purpose |
|-------|---------|
| `01_dim_entity_types` | One row: `secret` |
| `20_dtl_attr_defs` | One row: `description` (text) |
| `21_dtl_attrs` | Free-text description values (joined by `v_vault_entries`) |
| `10_fct_vault_entries` | Ciphertext + wrapped DEK + nonce + version + structural cols only |

Description lives in `dtl_attrs` — matching how IAM stores `display_name` and role/group/application
descriptions. No business columns on `fct_*`.

---

## Env-var contract

`backend/01_core/config.py` enforces an allowlist on boot. Any `TENNETCTL_*` var outside
the allowlist that matches `(SECRET|TOKEN|PASSWORD|PRIVATE_KEY|API_KEY)$` fails startup with
a message pointing the operator at the vault.

Allowlist:
- `TENNETCTL_VAULT_ROOT_KEY`
- `TENNETCTL_MODULES`
- `TENNETCTL_SINGLE_TENANT`
- `TENNETCTL_APP_PORT`
- `TENNETCTL_ALLOW_UNAUTHENTICATED_VAULT` (v0.2 only; removed after phase 8)

Secrets belong in the vault. Env is for infrastructure.

---

## Pre-auth gap (v0.2 only)

Phase 8 (auth) is not yet implemented. Until then, vault routes are gated behind
`TENNETCTL_ALLOW_UNAUTHENTICATED_VAULT=true`. Boot logs a WARNING reminding the operator
to remove the flag once auth lands. The flag and the warning both disappear in phase 8.

## Bootstrap secrets

On first boot after vault schema is migrated, the lifespan ensures two keys exist:

- `auth.argon2.pepper` — 32 random bytes base64
- `auth.session.signing_key_v1` — 32 random bytes base64 (Ed25519 seed in phase 8)

Created with `created_by='sys'`, audit metadata `{source: bootstrap}`. Idempotent — re-running
against a populated vault is a no-op.

---

## Non-goals for v0.2

- **Per-org vaults.** Single global vault. Multi-tenancy in vault arrives in v0.3 alongside
  `org_id` on `fct_vault_entries` + RLS.
- **KMS/HSM integration.** Root key in env is deliberately simple for self-host. Adapters
  for AWS/GCP/HashiCorp arrive when a cloud-deployed customer needs them.
- **Automated key rotation ceremony.** Rotation = redeploy + re-wrap script for v0.2.
- **External secret backends.** No sync-from-Vault, no sync-from-Doppler. The point is to be
  the single backend, not a cache.
- **Test-mode secrets.** `is_test` column exists for schema parity but is always false in v0.2.

## Consequences

### Positive
- Every feature has a uniform, auditable way to read secrets.
- Env surface shrinks from "anything" to a 5-var allowlist — operators can't accidentally
  mis-set secrets.
- AES-256-GCM + PyCA is the industry baseline; security review has a small blast radius.
- In-process SWR cache keeps latency near-zero for hot secrets (Argon2 pepper, session keys).

### Negative
- Root key loss = vault loss. Mitigation: backup root key out-of-band (password manager,
  printed + sealed, KMS in v0.3).
- 60s SWR cache means rotation is not instant across a distributed deployment; acceptable
  for v0.2 single-instance.
- Pre-auth gap flag is a footgun — operators might forget to remove it after phase 8.
  Mitigation: boot log WARNING every start; plan 08 removes the flag entirely.

---

## References

- NIST SP 800-38D — GCM mode recommendations (12-byte nonce, 128-bit auth tag)
- OWASP Cryptographic Storage Cheat Sheet
- PyCA `cryptography` — AESGCM primitive
- `.claude/rules/common/database.md` — Pure EAV rule (no business columns on `fct_*`)
- ADR-019 — feature-local vs shared node ownership
- ADR-026 — minimum surface principle (5 allowed env vars, not 50)
