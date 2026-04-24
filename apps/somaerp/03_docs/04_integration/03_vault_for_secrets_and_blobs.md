# Vault for Secrets and Blobs

> Per the project's `project_vault_for_config` memory, every runtime secret and tenant-specific config lives in tennetctl vault. somaerp owns no secret-storage code. This doc also resolves the forward reference from ADR-005 about QC/delivery photo blob storage.

## Tenant-specific secrets — keyspace

somaerp stores tenant-scoped secrets under a deterministic keyspace in tennetctl vault:

```text
somaerp.tenants.{workspace_id}.{logical_key}
```

Scope: `workspace` (tennetctl vault's per-workspace scope). Tenant isolation is enforced by vault scope, not by app-layer checks.

### Known tenant secret keys (Soma Delights)

| Key | Purpose | When written |
| --- | --- | --- |
| `somaerp.tenants.{ws}.fssai_license_number` | FSSAI license number for labels + compliance audits | Tenant bootstrap |
| `somaerp.tenants.{ws}.fssai_license_expiry` | Expiry date; checked by compliance hook | Tenant bootstrap + renewal |
| `somaerp.tenants.{ws}.business_address` | Legal business address for labels | Tenant bootstrap |
| `somaerp.tenants.{ws}.gstin` | GST registration number for invoices (when billing ships) | Tenant bootstrap |
| `somaerp.tenants.{ws}.smtp_host` / `.smtp_username` / `.smtp_password` | Tenant's SMTP relay for notify (if the tenant wires their own domain) | Optional; falls back to platform SMTP |
| `somaerp.tenants.{ws}.whatsapp_business_token` | WhatsApp Business API token (future notify channel) | When the tenant signs up for WhatsApp notify — deferred |
| `somaerp.tenants.{ws}.trademark_registration` | Filed trademark ID, for legal reference | Tenant bootstrap |

### Known platform-wide (org-scoped) secret keys

| Key | Purpose |
| --- | --- |
| `somaerp.platform.service_api_key` | The somaerp→tennetctl service API key (stored for rotation reference, read from disk at boot) |
| `somaerp.platform.default_smtp_*` | Platform-default SMTP for tenants without their own |
| `somaerp.platform.default_currency_rates` | Stored manually; refreshed quarterly (no external FX API dependency) |

### Operator secret keys (per user, rarely used)

| Key | Purpose |
| --- | --- |
| `somaerp.users.{user_id}.preferences` | Per-user UI preferences stored in vault when they contain anything sensitive (rare) |

## Vault access pattern (service layer)

Per `00_tennetctl_proxy_pattern.md`, the proxy client exposes:

```text
await client.vault_put({"key": "somaerp.tenants.<ws>.fssai_license_number",
                        "scope": "workspace",
                        "value": "12345678901234",
                        "workspace_id": ws})

secret = await client.vault_reveal("somaerp.tenants.<ws>.fssai_license_number",
                                   scope="workspace",
                                   workspace_id=ws)
```

Vault reads and writes emit audit events (tennetctl side). No somaerp code stores a secret on disk, in an env var, or in Postgres.

### Boot-time discovery

At boot, somaerp reads the service API key from a file path (`SOMAERP_TENNETCTL_KEY_FILE`), NOT from vault. Chicken-and-egg avoidance: you need the key to talk to vault. Once the client is up, every subsequent secret read is through vault.

## Photo blob storage — resolving the ADR-005 forward reference

ADR-005 records that QC check photos and delivery stop photos reference `photo_vault_key`. ADR-005 flags but does not resolve the question "does tennetctl vault support blobs?" This doc resolves it for v0.9.0.

### Blob storage survey

At v0.9.0, tennetctl vault is a key-value secret store. It does not have a native large-blob (file-upload) primitive. A blob primitive is tentatively scheduled for v0.10 (not committed; out of this phase's scope).

### Two options considered

**Option (a) — Stopgap: store photos as base64-encoded values in vault's existing k/v shape.**

- Photo uploads: client uploads to somaerp route; route base64-encodes and writes a vault entry with the encoded bytes.
- Key shape: `somaerp.tenants.{ws}.photos.qc.{batch_id}.{checkpoint_id}.{photo_uuid}` and `somaerp.tenants.{ws}.photos.delivery.{delivery_run_id}.{stop_id}.{photo_uuid}`.
- Retrieval: somaerp route calls `vault_reveal`, decodes, streams.
- Pros: works today with zero new tennetctl primitives; honors the empire-thesis "no external storage provider" constraint.
- Cons: vault is not optimized for large values; retrieval is an HTTP hop to tennetctl then a base64 decode. Acceptable for Soma Delights volumes (maybe a few thousand photos/month). Limits: per-value size enforcement in tennetctl vault (≤ 1 MB recommended — photos compressed client-side to JPEG ≤ 500 KB).

**Option (b) — Future: a tennetctl vault blob extension primitive.**

- tennetctl adds a `blobs` sub-feature offering `POST /v1/vault/blobs` (multipart upload) and `GET /v1/vault/blobs/{blob_id}` (streamed download).
- Stored on the same Postgres via `LARGE OBJECT` or filesystem-backed storage on the tennetctl host.
- Same scope / auth / audit model as vault secrets.
- Deferred to v0.10.

### Decision for v0.9.0

**Pick (a) — base64 in vault — with an explicit "stopgap" flag.** Documentation on every call site notes:

> This is a stopgap. When tennetctl ships the vault blob primitive (v0.10), somaerp migrates these values to the blob API. The `photo_vault_key` column shape on `evt_qc_checks` and `evt_delivery_stops` is stable across the migration; only the read/write helper changes.

The `photo_vault_key` value stored in `evt_qc_checks.photo_vault_key` and `evt_delivery_stops.photo_vault_key` is opaque to the database — just a vault key string. Today that string looks like `somaerp.tenants.{ws}.photos.qc.{batch}.{checkpoint}.{uuid}`; post-migration it may look like `blob:abc123`. The schema does not change.

### Client-side compression (non-negotiable)

Because vault values are small-value-optimized, the somaerp frontend MUST compress photos before upload:

- Max edge: 1600 px.
- JPEG quality: 0.8.
- Target size: ≤ 300 KB per photo.

This is enforced in the frontend upload hook (ships in the production and delivery plans, 56-09 and 56-11). Server-side rejects anything > 750 KB.

### Writing a QC photo (service-layer pseudocode)

```text
service.record_qc_check(conn, ctx, batch_id, checkpoint_id, result, notes, photo_bytes):
    photo_key = None
    if photo_bytes is not None:
        photo_uuid = uuid7()
        photo_key = f"somaerp.tenants.{ctx.workspace_id}.photos.qc.{batch_id}.{checkpoint_id}.{photo_uuid}"
        await client.vault_put({
            "key": photo_key,
            "scope": "workspace",
            "value": base64.b64encode(photo_bytes).decode(),
            "workspace_id": ctx.workspace_id,
        })
    await repo.insert_qc_check(conn, ...columns..., photo_vault_key=photo_key)
    await client.emit_audit(
        event_key="somaerp.quality.checks.recorded",
        outcome="success",
        metadata={"category": "compliance", "batch_id": str(batch_id), "photo_present": photo_key is not None},
        actor_user_id=ctx.user_id, org_id=ctx.org_id, workspace_id=ctx.workspace_id,
    )
```

### Reading a QC photo

```text
service.fetch_qc_photo(ctx, photo_vault_key) -> bytes:
    encoded = await client.vault_reveal(photo_vault_key, scope="workspace", workspace_id=ctx.workspace_id)
    return base64.b64decode(encoded)
```

The read is scoped to the same workspace. A request from workspace A for a photo key starting `somaerp.tenants.{B}.photos...` will be rejected by vault's scope check — app-layer belt-and-suspenders is an additional check in the service layer.

## Vault rotation

tennetctl vault supports rotation via `POST /v1/vault/{key}/rotate`. somaerp secrets (SMTP credentials, FSSAI license renewal) rotate through the tenant admin UI (ships in a future plan). Photos don't rotate — they are immutable like the event row that references them.

## Vault deletion

When a customer requests DSAR deletion (per `../03_scaling/03_data_residency_compliance.md`):

- Photos attached to delivery stops for that customer: delete the vault entries; the `photo_vault_key` on `evt_delivery_stops` stays (append-only) but resolves to a "this photo has been deleted per privacy request" tombstone.
- Photos attached to QC checks are NOT deleted — they carry no customer identity; they document the batch, which is FSSAI-protected.

## Operational safeguards

- Vault writes of values > 750 KB are blocked at the somaerp service layer (belt before vault-side enforcement).
- Vault reveal calls are cached per-request (same key read twice in one request hits vault once). Across requests there is no caching — every reveal is a fresh audited call.
- A failed vault write aborts the parent mutation (unlike audit, which is best-effort). A QC check cannot persist without its referenced photo existing in vault.

## Related documents

- `00_tennetctl_proxy_pattern.md` — proxy client vault method signatures
- `02_audit_emission.md` — vault reads/writes audit (category=`operational`; DSAR-related vault deletes audit as `privacy`)
- `../00_main/08_decisions/005_qc_checkpoint_model.md` — declares `photo_vault_key` on `evt_qc_checks`
- `../01_data_model/04_quality.md` (forward reference — Task 2) — carries the photo_vault_key column
- `../01_data_model/09_delivery.md` (forward reference — Task 2) — carries the photo_vault_key column on `evt_delivery_stops`
- Memory: `project_vault_for_config.md`
